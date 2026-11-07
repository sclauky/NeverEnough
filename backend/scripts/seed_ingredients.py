import asyncio
import json
import unicodedata
from pathlib import Path

from sqlalchemy import select

from app.db.session import get_engine, get_session_factory
from app.models.ingredient import Ingredient


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "ingredients.json"


def normalize_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name.casefold().strip())
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


def load_catalogue() -> list[dict]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Catalogue introuvable : {DATA_FILE}"
        )

    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    categories = data.get("categories")

    if not isinstance(categories, list):
        raise ValueError("Le catalogue doit contenir une liste 'categories'.")

    seen_names = set()

    for category in categories:
        category_name = category.get("name")
        ingredients = category.get("ingredients")

        if not isinstance(category_name, str) or not category_name.strip():
            raise ValueError("Une catégorie possède un nom invalide.")

        if len(category_name) > 60:
            raise ValueError(
                f"Nom de catégorie trop long : {category_name}"
            )

        if not isinstance(ingredients, list):
            raise ValueError(
                f"La catégorie '{category_name}' possède une liste invalide."
            )

        for ingredient in ingredients:
            names = [ingredient.get("name")]
            names.extend(ingredient.get("variants", []))

            for name in names:
                if not isinstance(name, str) or not name.strip():
                    raise ValueError(
                        f"Nom d'ingrédient invalide dans '{category_name}'."
                    )

                if len(name) > 120:
                    raise ValueError(
                        f"Nom d'ingrédient trop long : {name}"
                    )

                normalized = normalize_name(name)

                if normalized in seen_names:
                    raise ValueError(
                        f"Doublon détecté dans le catalogue : {name}"
                    )

                seen_names.add(normalized)

    return categories


async def seed_ingredients() -> None:
    categories = load_catalogue()

    engine = get_engine()
    session_factory = get_session_factory()

    generic_created = 0
    generic_existing = 0
    variants_created = 0
    variants_existing = 0

    try:
        async with session_factory() as session:
            async with session.begin():
                result = await session.scalars(select(Ingredient))
                existing_ingredients = result.all()

                ingredients_by_name = {
                    normalize_name(ingredient.name): ingredient
                    for ingredient in existing_ingredients
                }

                for category in categories:
                    category_name = category["name"]

                    for item in category["ingredients"]:
                        generic_name = item["name"]
                        generic_key = normalize_name(generic_name)

                        generic = ingredients_by_name.get(generic_key)

                        if generic is None:
                            generic = Ingredient(
                                name=generic_name,
                                category=category_name,
                                parent_id=None,
                            )
                            session.add(generic)
                            await session.flush()

                            ingredients_by_name[generic_key] = generic
                            generic_created += 1
                        else:
                            generic.category = category_name
                            generic.parent_id = None
                            generic_existing += 1

                        for variant_name in item.get("variants", []):
                            variant_key = normalize_name(variant_name)

                            variant = ingredients_by_name.get(variant_key)

                            if variant is None:
                                variant = Ingredient(
                                    name=variant_name,
                                    category=category_name,
                                    parent_id=generic.id,
                                )
                                session.add(variant)

                                ingredients_by_name[variant_key] = variant
                                variants_created += 1
                            else:
                                variant.category = category_name
                                variant.parent_id = generic.id
                                variants_existing += 1

    finally:
        await engine.dispose()

    print("\nImportation terminée.")
    print(f"Ingrédients génériques créés : {generic_created}")
    print(f"Ingrédients génériques existants : {generic_existing}")
    print(f"Variantes créées : {variants_created}")
    print(f"Variantes existantes : {variants_existing}")
    print(
        f"Total dans le catalogue : "
        f"{generic_created + generic_existing + variants_created + variants_existing}"
    )


if __name__ == "__main__":
    asyncio.run(seed_ingredients())