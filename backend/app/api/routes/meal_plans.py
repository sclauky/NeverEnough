
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.meal_plan import MealPlan
from app.models.meal_plan_entry import MealPlanEntry
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.meal_plan import MealPlanCreate, MealPlanPublic
from app.schemas.meal_plan_entry import (
    MealPlanEntryCreate,
    MealPlanEntryPublic,
)


router = APIRouter(prefix="/meal-plans", tags=["Meal Plans"])
entries_router = APIRouter(
    prefix="/meal-plan-entries",
    tags=["Meal Plan Entries"],
)


async def get_owned_meal_plan(
    meal_plan_id: UUID,
    session: AsyncSession,
    current_user: User,
) -> MealPlan:
    meal_plan = await session.scalar(
        select(MealPlan).where(
            MealPlan.id == meal_plan_id,
            MealPlan.user_id == current_user.id,
        )
    )

    if meal_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found.",
        )

    return meal_plan


@router.post(
    "",
    response_model=MealPlanPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_meal_plan(
    meal_plan_data: MealPlanCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> MealPlanPublic:
    meal_plan = MealPlan(
        **meal_plan_data.model_dump(),
        user_id=current_user.id,
    )

    session.add(meal_plan)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The meal plan could not be created.",
        )

    await session.refresh(meal_plan)

    return MealPlanPublic.model_validate(meal_plan)


@router.get("", response_model=list[MealPlanPublic])
async def get_meal_plans(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[MealPlanPublic]:
    result = await session.execute(
        select(MealPlan)
        .where(MealPlan.user_id == current_user.id)
        .order_by(MealPlan.start_date.desc())
    )

    return [
        MealPlanPublic.model_validate(meal_plan)
        for meal_plan in result.scalars().all()
    ]


@router.get("/{meal_plan_id}", response_model=MealPlanPublic)
async def get_meal_plan(
    meal_plan_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> MealPlanPublic:
    meal_plan = await get_owned_meal_plan(
        meal_plan_id,
        session,
        current_user,
    )

    return MealPlanPublic.model_validate(meal_plan)


@router.get(
    "/{meal_plan_id}/entries",
    response_model=list[MealPlanEntryPublic],
)
async def get_meal_plan_entries(
    meal_plan_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[MealPlanEntryPublic]:
    await get_owned_meal_plan(
        meal_plan_id,
        session,
        current_user,
    )

    result = await session.execute(
        select(MealPlanEntry)
        .where(MealPlanEntry.meal_plan_id == meal_plan_id)
        .order_by(
            MealPlanEntry.scheduled_date,
            MealPlanEntry.meal_type,
        )
    )

    return [
        MealPlanEntryPublic.model_validate(entry)
        for entry in result.scalars().all()
    ]


@entries_router.post(
    "",
    response_model=MealPlanEntryPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_meal_plan_entry(
    entry_data: MealPlanEntryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> MealPlanEntryPublic:
    meal_plan = await get_owned_meal_plan(
        entry_data.meal_plan_id,
        session,
        current_user,
    )

    if not (
        meal_plan.start_date
        <= entry_data.scheduled_date
        <= meal_plan.end_date
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The scheduled date must be inside the meal plan date range.",
        )

    recipe = await session.scalar(
        select(Recipe).where(
            Recipe.id == entry_data.recipe_id,
            (
                (Recipe.is_public.is_(True))
                | (Recipe.author_id == current_user.id)
            ),
        )
    )

    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found.",
        )

    entry = MealPlanEntry(**entry_data.model_dump())

    session.add(entry)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The meal plan entry could not be created.",
        )

    await session.refresh(entry)

    return MealPlanEntryPublic.model_validate(entry)


@entries_router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_meal_plan_entry(
    entry_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    entry = await session.scalar(
        select(MealPlanEntry)
        .join(
            MealPlan,
            MealPlan.id == MealPlanEntry.meal_plan_id,
        )
        .where(
            MealPlanEntry.id == entry_id,
            MealPlan.user_id == current_user.id,
        )
    )

    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan entry not found.",
        )

    await session.delete(entry)
    await session.commit()


@router.delete(
    "/{meal_plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_meal_plan(
    meal_plan_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    meal_plan = await get_owned_meal_plan(
        meal_plan_id,
        session,
        current_user,
    )

    await session.delete(meal_plan)
    await session.commit()