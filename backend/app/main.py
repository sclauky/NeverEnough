from fastapi import FastAPI

from app.api.routes.recipes import router as recipes_router
from app.api.routes.users import router as users_router
from app.api.routes.ingredients import router as ingredients_router
from app.api.routes.recipe_reviews import router as recipe_reviews_router


app = FastAPI(
    title="Never Enough API",
    description="API commune au site web et aux applications mobiles.",
    version="0.1.0",
)

app.include_router(users_router)
app.include_router(recipes_router)
app.include_router(ingredients_router)
app.include_router(recipe_reviews_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}