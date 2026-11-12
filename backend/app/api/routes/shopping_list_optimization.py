from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.shopping_list_optimization import (
    ShoppingListOptimizationPublic,
)
from app.services.shopping_list_optimization import (
    calculate_shopping_list_optimization,
)


router = APIRouter(
    prefix="/shopping-lists",
    tags=["Shopping List Optimization"],
)


@router.get(
    "/{shopping_list_id}/optimization",
    response_model=ShoppingListOptimizationPublic,
)
async def optimize_shopping_list(
    shopping_list_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await calculate_shopping_list_optimization(
            session=session,
            shopping_list_id=shopping_list_id,
            user_id=current_user.id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error