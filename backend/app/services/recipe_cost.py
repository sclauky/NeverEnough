from collections import defaultdict
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient
from app.models.product import Product
from app.models.product_price import ProductPrice
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.store import Store


UNIT_CONVERSIONS = {
    "mg": ("mass", Decimal("0.001")),
    "g": ("mass", Decimal("1")),
    "gr": ("mass", Decimal("1")),
    "gramme": ("mass", Decimal("1")),
    "grammes": ("mass", Decimal("1")),
    "kg": ("mass", Decimal("1000")),
    "ml": ("volume", Decimal("1")),
    "cl": ("volume", Decimal("10")),
    "dl": ("volume", Decimal("100")),
    "l": ("volume", Decimal("1000")),
    "litre": ("volume", Decimal("1000")),
    "litres": ("volume", Decimal("1000")),
    "piece": ("count", Decimal("1")),
    "pieces": ("count", Decimal("1")),
    "unite": ("count", Decimal("1")),
    "unites": ("count", Decimal("1")),
    "unité": ("count", Decimal("1")),
    "unités": ("count", Decimal("1")),
    "u": ("count", Decimal("1")),
}

BASE_UNITS = {
    "mass": "g",
    "volume": "ml",
    "count": "piece",
}


def normalize_unit(unit: str) -> str:
    return unit.strip().lower().replace(" ", "")


def convert_quantity(
    quantity: Decimal,
    source_unit: str,
    target_unit: str,
) -> Decimal | None:
    source = UNIT_CONVERSIONS.get(normalize_unit(source_unit))
    target = UNIT_CONVERSIONS.get(normalize_unit(target_unit))

    if source is None or target is None:
        return None

    if source[0] != target[0]:
        return None

    return quantity * source[1] / target[1]


def round_money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_packages(
    required_quantity: Decimal,
    package_quantity: Decimal,
) -> int:
    return int(
        (required_quantity / package_quantity).to_integral_value(
            rounding=ROUND_CEILING
        )
    )


def build_selection(
    ingredient_totals: dict,
    products: dict,
    optimization: str,
) -> dict:
    total = Decimal("0")
    missing = []
    items = []

    for ingredient_id, required in ingredient_totals.items():
        candidates = products.get(ingredient_id, [])

        if not candidates:
            missing.append(str(ingredient_id))
            continue

        if optimization == "consumed":
            selected = min(
                candidates,
                key=lambda item: (
                    item["unit_price"],
                    item["package_price"],
                ),
            )
        else:
            selected = min(
                candidates,
                key=lambda item: (
                    item["package_price"]
                    * calculate_packages(
                        required["quantity"],
                        item["package_base_quantity"],
                    ),
                    item["unit_price"],
                ),
            )

        required_quantity = required["quantity"]
        packages_needed = calculate_packages(
            required_quantity,
            selected["package_base_quantity"],
        )

        consumed_cost = selected["unit_price"] * required_quantity
        purchase_cost = selected["package_price"] * packages_needed

        cost = consumed_cost if optimization == "consumed" else purchase_cost
        total += cost

        items.append(
            {
                "ingredient_id": str(ingredient_id),
                "product_id": str(selected["product_id"]),
                "product_name": selected["product_name"],
                "brand": selected["brand"],
                "required_quantity": required_quantity,
                "unit": required["unit"],
                "packages_needed": packages_needed,
                "package_quantity": selected["package_quantity"],
                "package_unit": selected["package_unit"],
                "package_price": selected["package_price"],
                "consumed_cost": round_money(consumed_cost),
                "purchase_cost": round_money(purchase_cost),
                "currency_code": selected["currency_code"],
            }
        )

    return {
        "complete": not missing,
        "missing_ingredients": missing,
        "total": round_money(total),
        "currency_code": next(
            (
                item["currency_code"]
                for candidates in products.values()
                for item in candidates
            ),
            "EUR",
        ),
        "items": items,
    }


async def calculate_recipe_cost(
    session: AsyncSession,
    recipe_id: UUID,
    servings: int | None = None,
) -> dict:
    recipe = await session.scalar(
        select(Recipe).where(Recipe.id == recipe_id)
    )

    if recipe is None:
        raise ValueError("Recipe not found.")

    target_servings = servings if servings is not None else recipe.servings

    if target_servings <= 0 or recipe.servings <= 0:
        raise ValueError("Servings must be greater than zero.")

    scale = Decimal(target_servings) / Decimal(recipe.servings)

    recipe_ingredients = (
        await session.scalars(
            select(RecipeIngredient)
            .where(RecipeIngredient.recipe_id == recipe_id)
            .order_by(RecipeIngredient.position)
        )
    ).all()

    ingredient_totals = {}
    missing_ingredients = []

    for recipe_ingredient in recipe_ingredients:
        ingredient = await session.get(
            Ingredient,
            recipe_ingredient.ingredient_id,
        )

        if ingredient is None:
            continue

        if (
            recipe_ingredient.quantity is None
            or recipe_ingredient.unit is None
        ):
            missing_ingredients.append(
                {
                    "ingredient_id": str(ingredient.id),
                    "ingredient_name": ingredient.name,
                    "reason": "Missing quantity or unit.",
                }
            )
            continue

        unit_data = UNIT_CONVERSIONS.get(
            normalize_unit(recipe_ingredient.unit)
        )

        if unit_data is None:
            missing_ingredients.append(
                {
                    "ingredient_id": str(ingredient.id),
                    "ingredient_name": ingredient.name,
                    "reason": "Unsupported recipe unit.",
                }
            )
            continue

        dimension, conversion_factor = unit_data
        base_quantity = recipe_ingredient.quantity * scale * conversion_factor

        if ingredient.id not in ingredient_totals:
            ingredient_totals[ingredient.id] = {
                "quantity": Decimal("0"),
                "dimension": dimension,
                "unit": BASE_UNITS[dimension],
                "name": ingredient.name,
            }

        total = ingredient_totals[ingredient.id]

        if total["dimension"] != dimension:
            missing_ingredients.append(
                {
                    "ingredient_id": str(ingredient.id),
                    "ingredient_name": ingredient.name,
                    "reason": "Incompatible units for the same ingredient.",
                }
            )
            continue

        total["quantity"] += base_quantity

    ingredient_ids = list(ingredient_totals)

    if not ingredient_ids:
        return {
            "recipe_id": recipe.id,
            "recipe_title": recipe.title,
            "servings": target_servings,
            "stores": [],
            "missing_ingredients": missing_ingredients,
        }

    latest_prices = (
        select(
            ProductPrice.product_id.label("product_id"),
            ProductPrice.store_id.label("store_id"),
            ProductPrice.price.label("price"),
            ProductPrice.currency_code.label("currency_code"),
            func.row_number()
            .over(
                partition_by=(
                    ProductPrice.product_id,
                    ProductPrice.store_id,
                ),
                order_by=(
                    ProductPrice.observed_at.desc(),
                    ProductPrice.created_at.desc(),
                ),
            )
            .label("row_number"),
        )
        .subquery()
    )

    query = (
        select(
            Product,
            latest_prices.c.price,
            latest_prices.c.currency_code,
            Store,
        )
        .join(
            latest_prices,
            latest_prices.c.product_id == Product.id,
        )
        .join(
            Store,
            Store.id == latest_prices.c.store_id,
        )
        .where(
            Product.ingredient_id.in_(ingredient_ids),
            latest_prices.c.row_number == 1,
        )
    )

    results = (await session.execute(query)).all()

    store_products = defaultdict(lambda: defaultdict(list))
    store_data = {}

    for product, price, currency_code, store in results:
        ingredient_id = product.ingredient_id
        required = ingredient_totals.get(ingredient_id)

        if required is None:
            continue

        package_quantity = convert_quantity(
            product.package_quantity,
            product.package_unit,
            required["unit"],
        )

        if package_quantity is None or package_quantity <= 0:
            continue

        unit_price = price / package_quantity

        store_data[store.id] = store

        store_products[store.id][ingredient_id].append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "brand": product.brand,
                "package_quantity": product.package_quantity,
                "package_unit": product.package_unit,
                "package_price": price,
                "currency_code": currency_code,
                "unit_price": unit_price,
                "package_base_quantity": package_quantity,
            }
        )

    stores_result = []

    for store_id, products in store_products.items():
        store = store_data[store_id]

        currencies = {
            item["currency_code"]
            for candidates in products.values()
            for item in candidates
        }

        if len(currencies) != 1:
            continue

        consumed_selection = build_selection(
            ingredient_totals,
            products,
            "consumed",
        )

        purchase_selection = build_selection(
            ingredient_totals,
            products,
            "purchase",
        )

        stores_result.append(
            {
                "store_id": str(store_id),
                "store_name": store.name,
                "chain_name": store.chain_name,
                "address": store.address,
                "city": store.city,
                "consumed_optimization": consumed_selection,
                "purchase_optimization": purchase_selection,
            }
        )

    stores_result.sort(
        key=lambda item: (
            not item["purchase_optimization"]["complete"],
            item["purchase_optimization"]["total"],
        )
    )

    return {
        "recipe_id": recipe.id,
        "recipe_title": recipe.title,
        "servings": target_servings,
        "stores": stores_result,
        "missing_ingredients": missing_ingredients,
    }