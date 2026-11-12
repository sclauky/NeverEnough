from fastapi import FastAPI

from app.api.routes.recipes import router as recipes_router
from app.api.routes.users import router as users_router
from app.api.routes.ingredients import router as ingredients_router
from app.api.routes.recipe_reviews import router as recipe_reviews_router
from app.api.routes.meal_plans import (
    entries_router as meal_plan_entries_router,
)
from app.api.routes.meal_plans import router as meal_plans_router
from app.api.routes.shopping_lists import router as shopping_lists_router
from app.api.routes.budgets import router as budgets_router
from app.api.routes.recipe_cost import router as recipe_cost_router
from app.api.routes.stores import router as stores_router
from app.api.routes.products import router as products_router

app = FastAPI(
    title="Never Enough API",
    description="API commune au site web et aux applications mobiles.",
    version="0.1.0",
)

app.include_router(users_router)
app.include_router(recipes_router)
app.include_router(ingredients_router)
app.include_router(recipe_reviews_router)
app.include_router(meal_plans_router)
app.include_router(meal_plan_entries_router)
app.include_router(shopping_lists_router)
app.include_router(budgets_router)
app.include_router(recipe_cost_router)
app.include_router(stores_router)
app.include_router(products_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}