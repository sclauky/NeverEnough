import asyncio

from sqlalchemy import select

from app.db.session import get_engine, get_session_factory
from app.models.ingredient import Ingredient


INGREDIENTS = {
    "Fruits et légumes": [
        "Tomate",
        "Oignon",
        "Ail",
        "Pomme de terre",
        "Carotte",
        "Courgette",
        "Aubergine",
        "Poivron",
        "Concombre",
        "Salade",
        "Épinards",
        "Brocoli",
        "Chou-fleur",
        "Champignon",
        "Poireau",
        "Haricot vert",
        "Maïs",
        "Avocat",
        "Citron",
        "Pomme",
        "Banane",
        "Orange",
        "Poire",
        "Fraise",
        "Courge",
    ],
    "Viandes et poissons": [
        "Poulet",
        "Dinde",
        "Bœuf",
        "Porc",
        "Jambon",
        "Lardons",
        "Steak haché",
        "Saucisse",
        "Saumon",
        "Thon",
        "Cabillaud",
        "Crevette",
        "Sardine",
    ],
    "Produits laitiers et œufs": [
        "Lait",
        "Beurre",
        "Crème fraîche",
        "Crème liquide",
        "Yaourt nature",
        "Fromage râpé",
        "Emmental",
        "Mozzarella",
        "Parmesan",
        "Chèvre",
        "Œuf",
        "Fromage blanc",
    ],
    "Féculents et céréales": [
        "Riz",
        "Pâtes",
        "Spaghetti",
        "Macaroni",
        "Farine",
        "Semoule",
        "Couscous",
        "Quinoa",
        "Boulgour",
        "Flocons d'avoine",
        "Pain",
        "Pain de mie",
        "Tortilla",
        "Nouilles",
    ],
    "Légumineuses": [
        "Lentilles",
        "Pois chiches",
        "Haricots rouges",
        "Haricots blancs",
        "Pois cassés",
        "Petits pois",
    ],
    "Épices et condiments": [
        "Sel",
        "Poivre",
        "Paprika",
        "Curry",
        "Cumin",
        "Cannelle",
        "Herbes de Provence",
        "Persil",
        "Basilic",
        "Thym",
        "Moutarde",
        "Mayonnaise",
        "Ketchup",
        "Vinaigre",
        "Sauce soja",
    ],
    "Huiles et matières grasses": [
        "Huile d'olive",
        "Huile de tournesol",
        "Huile de colza",
    ],
    "Conserves et autres": [
        "Tomates pelées",
        "Concentré de tomate",
        "Lait de coco",
        "Bouillon de légumes",
        "Bouillon de volaille",
        "Sucre",
        "Miel",
        "Chocolat noir",
        "Levure chimique",
        "Levure boulangère",
        "Noix",
        "Amandes",
        "Raisins secs",
    ],
}


async def main() -> None:
    session_factory = get_session_factory()

    try:
        async with session_factory() as session:
            result = await session.execute(select(Ingredient.name))
            existing_names = set(result.scalars().all())

            new_ingredients = [
                Ingredient(name=name, category=category)
                for category, names in INGREDIENTS.items()
                for name in names
                if name not in existing_names
            ]

            session.add_all(new_ingredients)
            await session.commit()

            print(f"{len(new_ingredients)} ingredients added.")
            print(f"{len(existing_names) + len(new_ingredients)} ingredients available.")

    finally:
        await get_engine().dispose()


if __name__ == "__main__":
    asyncio.run(main())