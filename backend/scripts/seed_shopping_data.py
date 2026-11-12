import asyncio
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.db.session import get_engine, get_session_factory
from app.models.ingredient import Ingredient
from app.models.product import Product
from app.models.product_price import ProductPrice
from app.models.store import Store


STORES = [
    {
        "key": "carrefour",
        "chain_name": "Carrefour (test)",
        "name": "Carrefour (test)",
        "address": "Adresse fictive - données de test",
        "postal_code": "33610",
        "city": "Cestas",
        "country_code": "FR",
    },
    {
        "key": "lidl",
        "chain_name": "Lidl (test)",
        "name": "Lidl (test)",
        "address": "Adresse fictive - données de test",
        "postal_code": "33610",
        "city": "Cestas",
        "country_code": "FR",
    },
    {
        "key": "leclerc",
        "chain_name": "E.Leclerc (test)",
        "name": "E.Leclerc (test)",
        "address": "Adresse fictive - données de test",
        "postal_code": "33610",
        "city": "Cestas",
        "country_code": "FR",
    },
]


PRODUCTS = [
    {
        "aliases": ["pâtes", "pâtes alimentaires", "spaghetti"],
        "name": "Spaghetti 500 g",
        "brand": "Marque de test",
        "package_quantity": Decimal("500"),
        "package_unit": "g",
        "prices": {
            "carrefour": Decimal("1.25"),
            "lidl": Decimal("0.95"),
            "leclerc": Decimal("1.10"),
        },
    },
    {
        "aliases": ["pâtes", "pâtes alimentaires", "spaghetti"],
        "name": "Spaghetti 1 kg",
        "brand": "Marque de test",
        "package_quantity": Decimal("1000"),
        "package_unit": "g",
        "prices": {
            "carrefour": Decimal("2.20"),
            "lidl": Decimal("1.85"),
            "leclerc": Decimal("1.95"),
        },
    },
    {
        "aliases": ["riz", "riz blanc"],
        "name": "Riz long 1 kg",
        "brand": "Marque de test",
        "package_quantity": Decimal("1000"),
        "package_unit": "g",
        "prices": {
            "carrefour": Decimal("2.10"),
            "lidl": Decimal("1.65"),
            "leclerc": Decimal("1.80"),
        },
    },
    {
        "aliases": ["lait", "lait demi-écrémé"],
        "name": "Lait demi-écrémé 1 L",
        "brand": "Marque de test",
        "package_quantity": Decimal("1"),
        "package_unit": "l",
        "prices": {
            "carrefour": Decimal("1.25"),
            "lidl": Decimal("1.05"),
            "leclerc": Decimal("1.12"),
        },
    },
    {
        "aliases": ["œufs", "oeufs", "œuf", "oeuf"],
        "name": "Œufs x6",
        "brand": "Marque de test",
        "package_quantity": Decimal("6"),
        "package_unit": "piece",
        "prices": {
            "carrefour": Decimal("2.15"),
            "lidl": Decimal("1.79"),
            "leclerc": Decimal("1.95"),
        },
    },
    {
        "aliases": ["farine", "farine de blé"],
        "name": "Farine de blé 1 kg",
        "brand": "Marque de test",
        "package_quantity": Decimal("1000"),
        "package_unit": "g",
        "prices": {
            "carrefour": Decimal("1.15"),
            "lidl": Decimal("0.89"),
            "leclerc": Decimal("0.99"),
        },
    },
    {
        "aliases": ["beurre"],
        "name": "Beurre doux 250 g",
        "brand": "Marque de test",
        "package_quantity": Decimal("250"),
        "package_unit": "g",
        "prices": {
            "carrefour": Decimal("2.35"),
            "lidl": Decimal("2.05"),
            "leclerc": Decimal("2.19"),
        },
    },
    {
        "aliases": ["sucre", "sucre en poudre"],
        "name": "Sucre en poudre 1 kg",
        "brand": "Marque de test",
        "package_quantity": Decimal("1000"),
        "package_unit": "g",
        "prices": {
            "carrefour": Decimal("1.45"),
            "lidl": Decimal("1.09"),
            "leclerc": Decimal("1.19"),
        },
    },
    {
        "aliases": ["crème liquide", "creme liquide", "crème"],
        "name": "Crème liquide 20 cl",
        "brand": "Marque de test",
        "package_quantity": Decimal("20"),
        "package_unit": "cl",
        "prices": {
            "carrefour": Decimal("1.05"),
            "lidl": Decimal("0.85"),
            "leclerc": Decimal("0.95"),
        },
    },
    {
        "aliases": ["tomates concassées", "tomates", "tomate"],
        "name": "Tomates concassées 400 g",
        "brand": "Marque de test",
        "package_quantity": Decimal("400"),
        "package_unit": "g",
        "prices": {
            "carrefour": Decimal("1.10"),
            "lidl": Decimal("0.79"),
            "leclerc": Decimal("0.89"),
        },
    },
    {
        "aliases": ["huile de tournesol", "huile"],
        "name": "Huile de tournesol 1 L",
        "brand": "Marque de test",
        "package_quantity": Decimal("1"),
        "package_unit": "l",
        "prices": {
            "carrefour": Decimal("2.15"),
            "lidl": Decimal("1.75"),
            "leclerc": Decimal("1.95"),
        },
    },
]


OBSERVED_AT = datetime(2026, 11, 12, tzinfo=timezone.utc)


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    return normalized.replace("œ", "oe").strip()


def find_ingredient(
    ingredients: list[Ingredient],
    aliases: list[str],
) -> Ingredient | None:
    normalized_ingredients = {
        normalize_name(ingredient.name): ingredient
        for ingredient in ingredients
    }

    for alias in aliases:
        normalized_alias = normalize_name(alias)

        if normalized_alias in normalized_ingredients:
            return normalized_ingredients[normalized_alias]

    for alias in aliases:
        normalized_alias = normalize_name(alias)
        matches = [
            ingredient
            for ingredient in ingredients
            if normalized_alias in normalize_name(ingredient.name)
        ]

        if matches:
            return min(matches, key=lambda ingredient: len(ingredient.name))

    return None


async def get_or_create_store(
    session,
    store_data: dict,
) -> Store:
    store = await session.scalar(
        select(Store).where(
            Store.chain_name == store_data["chain_name"],
            Store.name == store_data["name"],
            Store.address == store_data["address"],
            Store.postal_code == store_data["postal_code"],
            Store.city == store_data["city"],
            Store.country_code == store_data["country_code"],
        )
    )

    if store is not None:
        return store

    store = Store(
        chain_name=store_data["chain_name"],
        name=store_data["name"],
        address=store_data["address"],
        postal_code=store_data["postal_code"],
        city=store_data["city"],
        country_code=store_data["country_code"],
    )

    session.add(store)
    await session.flush()

    return store


async def get_or_create_product(
    session,
    ingredient: Ingredient,
    product_data: dict,
) -> Product:
    product = await session.scalar(
        select(Product).where(
            Product.ingredient_id == ingredient.id,
            Product.name == product_data["name"],
            Product.brand == product_data["brand"],
            Product.package_quantity == product_data["package_quantity"],
            Product.package_unit == product_data["package_unit"],
        )
    )

    if product is not None:
        return product

    product = Product(
        ingredient_id=ingredient.id,
        name=product_data["name"],
        brand=product_data["brand"],
        package_quantity=product_data["package_quantity"],
        package_unit=product_data["package_unit"],
    )

    session.add(product)
    await session.flush()

    return product


async def create_or_update_price(
    session,
    product: Product,
    store: Store,
    price: Decimal,
) -> None:
    product_price = await session.scalar(
        select(ProductPrice).where(
            ProductPrice.product_id == product.id,
            ProductPrice.store_id == store.id,
            ProductPrice.observed_at == OBSERVED_AT,
        )
    )

    if product_price is None:
        product_price = ProductPrice(
            product_id=product.id,
            store_id=store.id,
            price=price,
            currency_code="EUR",
            is_promotion=False,
            observed_at=OBSERVED_AT,
        )
        session.add(product_price)
    else:
        product_price.price = price
        product_price.currency_code = "EUR"
        product_price.is_promotion = False


async def seed() -> None:
    engine = get_engine()

    try:
        async with get_session_factory()() as session:
            async with session.begin():
                ingredients = list(
                    (
                        await session.scalars(
                            select(Ingredient)
                        )
                    ).all()
                )

                if not ingredients:
                    raise RuntimeError(
                        "Aucun ingrédient trouvé. Importe d'abord le catalogue."
                    )

                stores = {}

                for store_data in STORES:
                    stores[store_data["key"]] = await get_or_create_store(
                        session,
                        store_data,
                    )

                created_products = 0
                created_prices = 0
                skipped_products = []

                for product_data in PRODUCTS:
                    ingredient = find_ingredient(
                        ingredients,
                        product_data["aliases"],
                    )

                    if ingredient is None:
                        skipped_products.append(product_data["name"])
                        continue

                    existing_product = await session.scalar(
                        select(Product).where(
                            Product.ingredient_id == ingredient.id,
                            Product.name == product_data["name"],
                            Product.brand == product_data["brand"],
                            Product.package_quantity == product_data["package_quantity"],
                            Product.package_unit == product_data["package_unit"],
                        )
                    )

                    product = await get_or_create_product(
                        session,
                        ingredient,
                        product_data,
                    )

                    if existing_product is None:
                        created_products += 1

                    for store_key, price in product_data["prices"].items():
                        existing_price = await session.scalar(
                            select(ProductPrice.id).where(
                                ProductPrice.product_id == product.id,
                                ProductPrice.store_id == stores[store_key].id,
                                ProductPrice.observed_at == OBSERVED_AT,
                            )
                        )

                        await create_or_update_price(
                            session,
                            product,
                            stores[store_key],
                            price,
                        )

                        if existing_price is None:
                            created_prices += 1

            print("Import terminé.")
            print(f"Magasins disponibles : {len(stores)}")
            print(f"Nouveaux produits : {created_products}")
            print(f"Nouveaux prix : {created_prices}")

            if skipped_products:
                print("Produits ignorés, ingrédient introuvable :")
                for product_name in skipped_products:
                    print(f"- {product_name}")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())