
from uuid import UUID

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
    category: str | None = Query(default=None, min_length=1, max_length=60),
    parent_id: UUID | None = Query(default=None),
    include_variants: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[IngredientPublic]:
    query = select(Ingredient)

    if parent_id is not None:
        query = query.where(Ingredient.parent_id == parent_id)
    elif not include_variants:
        query = query.where(Ingredient.parent_id.is_(None))

    if search:
        query = query.where(
            Ingredient.name.ilike(f"%{search.strip()}%")
        )

    if category:
        query = query.where(
            Ingredient.category.ilike(category.strip())
        )

    query = query.order_by(Ingredient.name.asc())
    query = query.limit(limit).offset(offset)

    result = await session.execute(query)

    return [
        IngredientPublic.model_validate(ingredient)
        for ingredient in result.scalars().all()
    ]