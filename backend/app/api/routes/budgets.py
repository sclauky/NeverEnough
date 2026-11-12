from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.models.user_budget import UserBudget
from app.schemas.user_budget import (
    UserBudgetCreate,
    UserBudgetPublic,
    UserBudgetUpdate,
)


router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"],
)


@router.post(
    "",
    response_model=UserBudgetPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_budget(
    budget_data: UserBudgetCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserBudget:
    existing_budget = await session.scalar(
        select(UserBudget).where(
            UserBudget.user_id == current_user.id,
        )
    )

    if existing_budget is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A budget already exists for this user.",
        )

    budget = UserBudget(
        user_id=current_user.id,
        **budget_data.model_dump(),
    )

    session.add(budget)
    await session.commit()
    await session.refresh(budget)

    return budget


@router.get(
    "/me",
    response_model=UserBudgetPublic,
)
async def get_my_budget(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserBudget:
    budget = await session.scalar(
        select(UserBudget).where(
            UserBudget.user_id == current_user.id,
        )
    )

    if budget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No budget found for this user.",
        )

    return budget


@router.patch(
    "/me",
    response_model=UserBudgetPublic,
)
async def update_my_budget(
    budget_data: UserBudgetUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserBudget:
    budget = await session.scalar(
        select(UserBudget).where(
            UserBudget.user_id == current_user.id,
        )
    )

    if budget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No budget found for this user.",
        )

    update_data = budget_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )

    for field, value in update_data.items():
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null.",
            )
        setattr(budget, field, value)

    await session.commit()
    await session.refresh(budget)

    return budget


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_my_budget(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    budget = await session.scalar(
        select(UserBudget).where(
            UserBudget.user_id == current_user.id,
        )
    )

    if budget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No budget found for this user.",
        )

    await session.delete(budget)
    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)