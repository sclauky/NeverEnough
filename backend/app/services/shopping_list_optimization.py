from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient
from app.models.product import Product
from app.models.product_price import ProductPrice
from app.models.shopping_list import ShoppingList
from app.models.shopping_list_item import ShoppingListItem
from app.models.store import Store
from app.services.recipe_cost import (
    BASE_UNITS,
    UNIT_CONVERSIONS,
    build_selection,
    convert_quantity,
    normalize_unit,
)


def build_shopping_selection(
    ingredient_totals: dict,
    products: dict,
    optimization: str,
) -> dict:
    selection = build_selection(
        ingredient_totals,
        products,
        optimization,
    )

    for item in selection["items"]:
        item["store_id"] = item.pop("_store_id")
        item["store_name"] = item.pop("_store_name")
        item["chain_name"] = item.pop("_chain_name")

    return selection


async def calculate_shopping_list_optimization(
    session: AsyncSession,
    shopping_list_id: UUID,
    user_id: UUID,
) -> dict:
    shopping_list = await session.scalar(
        select(ShoppingList).where(
            ShoppingList.id == shopping_list_id,
            ShoppingList.user_id == user_id,
        )
    )

    if shopping_list is None:
        raise ValueError("Shopping list not found.")

    list_items = (
        await session.scalars(
            select(ShoppingListItem)
            .where(
                ShoppingListItem.shopping_list_id == shopping_list_id,
                ShoppingListItem.is_purchased.is_(False),
            )
            .order_by(
                ShoppingListItem.position,
                ShoppingListItem.created_at,
            )
        )
    ).all()

    ingredient_totals = {}
    unpriced_items = []

    for list_item in list_items:
        if (
            list_item.ingredient_id is None
            or list_item.quantity is None
            or list_item.unit is None
        ):
            unpriced_items.append(
                {
                    "item_id": str(list_item.id),
                    "name": list_item.name,
                    "reason": "Missing ingredient, quantity or unit.",
                }
            )
            continue

        ingredient = await session.get(
            Ingredient,
            list_item.ingredient_id,
        )

        if ingredient is None:
            unpriced_items.append(
                {
                    "item_id": str(list_item.id),
                    "name": list_item.name,
                    "reason": "Ingredient not found.",
                }
            )
            continue

        unit_data = UNIT_CONVERSIONS.get(
            normalize_unit(list_item.unit)
        )

        if unit_data is None:
            unpriced_items.append(
                {
                    "item_id": str(list_item.id),
                    "name": list_item.name,
                    "reason": "Unsupported unit.",
                }
            )
            continue

        dimension, conversion_factor = unit_data

        if ingredient.id not in ingredient_totals:
            ingredient_totals[ingredient.id] = {
                "quantity": Decimal("0"),
                "dimension": dimension,
                "unit": BASE_UNITS[dimension],
                "name": ingredient.name,
            }

        total = ingredient_totals[ingredient.id]

        if total["dimension"] != dimension:
            unpriced_items.append(
                {
                    "item_id": str(list_item.id),
                    "name": list_item.name,
                    "reason": "Incompatible units for the same ingredient.",
                }
            )
            continue

        total["quantity"] += (
            list_item.quantity * conversion_factor
        )

    ingredient_ids = list(ingredient_totals)

    if not ingredient_ids:
        return {
            "shopping_list_id": shopping_list.id,
            "shopping_list_title": shopping_list.title,
            "stores": [],
            "multi_store_optimization": {
                "consumed_optimization": None,
                "purchase_optimization": None,
            },
            "unpriced_items": unpriced_items,
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
    all_products = defaultdict(list)
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

        candidate = {
            "product_id": product.id,
            "product_name": product.name,
            "brand": product.brand,
            "package_quantity": product.package_quantity,
            "package_unit": product.package_unit,
            "package_price": price,
            "currency_code": currency_code,
            "unit_price": unit_price,
            "package_base_quantity": package_quantity,
            "_store_id": str(store.id),
            "_store_name": store.name,
            "_chain_name": store.chain_name,
        }

        store_data[store.id] = store
        store_products[store.id][ingredient_id].append(candidate)
        all_products[ingredient_id].append(candidate)

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

        consumed_selection = build_shopping_selection(
            ingredient_totals,
            products,
            "consumed",
        )

        purchase_selection = build_shopping_selection(
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

    currencies = {
        item["currency_code"]
        for candidates in all_products.values()
        for item in candidates
    }

    if len(currencies) == 1:
        multi_store_consumed = build_shopping_selection(
            ingredient_totals,
            all_products,
            "consumed",
        )

        multi_store_purchase = build_shopping_selection(
            ingredient_totals,
            all_products,
            "purchase",
        )
    else:
        multi_store_consumed = None
        multi_store_purchase = None

    return {
        "shopping_list_id": shopping_list.id,
        "shopping_list_title": shopping_list.title,
        "stores": stores_result,
        "multi_store_optimization": {
            "consumed_optimization": multi_store_consumed,
            "purchase_optimization": multi_store_purchase,
        },
        "unpriced_items": unpriced_items,
    }