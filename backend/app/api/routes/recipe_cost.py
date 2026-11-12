from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.recipe_cost import RecipeCostPublic
from app.services.recipe_cost import calculate_recipe_cost


router = APIRouter(
    prefix="/recipes",
    tags=["Recipe Costs"],
)


@router.get(
    "/{recipe_id}/cost",
    response_model=RecipeCostPublic,
)
async def get_recipe_cost(
    recipe_id: UUID,
    servings: int | None = Query(default=None, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    recipe = await session.scalar(
        select(Recipe).where(Recipe.id == recipe_id)
    )

    if recipe is None:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found.",
        )

    if not recipe.is_public and recipe.author_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access this recipe.",
        )

    try:
        return await calculate_recipe_cost(
            session=session,
            recipe_id=recipe_id,
            servings=servings,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc