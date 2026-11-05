
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.ingredient import Ingredient
from app.schemas.ingredient import IngredientPublic


router = APIRouter(prefix="/ingredients", tags=["Ingredients"])


@router.get("", response_model=list[IngredientPublic])
async def get_ingredients(
    search: str | None = Query(default=None, min_length=1, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[IngredientPublic]:
    query = select(Ingredient).order_by(Ingredient.name.asc())

    if search:
        query = query.where(Ingredient.name.ilike(f"%{search.strip()}%"))

    query = query.limit(limit).offset(offset)

    result = await session.execute(query)

    return [IngredientPublic.model_validate(ingredient) for ingredient in result.scalars().all()]