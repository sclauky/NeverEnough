from collections.abc import Sequence
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.ingredient import Ingredient
from app.models.meal_plan import MealPlan
from app.models.meal_plan_entry import MealPlanEntry
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.shopping_list import ShoppingList
from app.models.shopping_list_item import ShoppingListItem
from app.models.user import User
from app.schemas.shopping_list import (
    ShoppingListCreate,
    ShoppingListDetail,
    ShoppingListPublic,
)
from app.schemas.shopping_list_item import (
    ShoppingListItemCreate,
    ShoppingListItemPublic,
    ShoppingListItemUpdate,
)


router = APIRouter(
    prefix="/shopping-lists",
    tags=["Shopping Lists"],
)


async def get_owned_shopping_list(
    shopping_list_id: UUID,
    session: AsyncSession,
    current_user: User,
) -> ShoppingList:
    shopping_list = await session.scalar(
        select(ShoppingList).where(
            ShoppingList.id == shopping_list_id,
            ShoppingList.user_id == current_user.id,
        )
    )

    if shopping_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found.",
        )

    return shopping_list


async def get_shopping_list_detail(
    shopping_list: ShoppingList,
    session: AsyncSession,
) -> ShoppingListDetail:
    result = await session.execute(
        select(ShoppingListItem)
        .where(
            ShoppingListItem.shopping_list_id == shopping_list.id,
        )
        .order_by(
            ShoppingListItem.position,
            ShoppingListItem.created_at,
        )
    )

    items = [
        ShoppingListItemPublic.model_validate(item)
        for item in result.scalars().all()
    ]

    return ShoppingListDetail(
        **ShoppingListPublic.model_validate(shopping_list).model_dump(),
        items=items,
    )


@router.post(
    "",
    response_model=ShoppingListPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_shopping_list(
    list_data: ShoppingListCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ShoppingListPublic:
    if list_data.meal_plan_id is not None:
        meal_plan = await session.scalar(
            select(MealPlan).where(
                MealPlan.id == list_data.meal_plan_id,
                MealPlan.user_id == current_user.id,
            )
        )

        if meal_plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found.",
            )

    shopping_list = ShoppingList(
        **list_data.model_dump(),
        user_id=current_user.id,
    )

    session.add(shopping_list)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The shopping list could not be created.",
        )

    await session.refresh(shopping_list)

    return ShoppingListPublic.model_validate(shopping_list)


@router.get("", response_model=list[ShoppingListPublic])
async def get_shopping_lists(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ShoppingListPublic]:
    result = await session.execute(
        select(ShoppingList)
        .where(ShoppingList.user_id == current_user.id)
        .order_by(ShoppingList.created_at.desc())
    )

    return [
        ShoppingListPublic.model_validate(shopping_list)
        for shopping_list in result.scalars().all()
    ]


@router.post(
    "/from-meal-plan/{meal_plan_id}",
    response_model=ShoppingListDetail,
    status_code=status.HTTP_201_CREATED,
)
async def generate_shopping_list(
    meal_plan_id: UUID,
    title: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ShoppingListDetail:
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

    result = await session.execute(
        select(
            MealPlanEntry,
            Recipe,
            RecipeIngredient,
            Ingredient,
        )
        .join(
            Recipe,
            Recipe.id == MealPlanEntry.recipe_id,
        )
        .join(
            RecipeIngredient,
            RecipeIngredient.recipe_id == Recipe.id,
        )
        .join(
            Ingredient,
            Ingredient.id == RecipeIngredient.ingredient_id,
        )
        .where(
            MealPlanEntry.meal_plan_id == meal_plan_id,
        )
        .order_by(
            MealPlanEntry.scheduled_date,
            MealPlanEntry.meal_type,
            RecipeIngredient.position,
        )
    )

    rows: Sequence = result.all()

    grouped_items: dict[
        tuple[UUID, str | None],
        dict,
    ] = {}

    generated_items: list[dict] = []

    for entry, recipe, recipe_ingredient, ingredient in rows:
        if not recipe.is_public and recipe.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One of the planned recipes is no longer accessible.",
            )

        unit = (
            recipe_ingredient.unit.strip()
            if recipe_ingredient.unit
            else None
        )

        normalized_unit = unit.casefold() if unit else None

        if recipe_ingredient.quantity is None:
            generated_items.append(
                {
                    "ingredient_id": ingredient.id,
                    "name": ingredient.name,
                    "quantity": None,
                    "unit": unit,
                }
            )
            continue

        scale = Decimal(entry.servings) / Decimal(recipe.servings)

        quantity = (
            recipe_ingredient.quantity * scale
        ).quantize(
            Decimal("0.001"),
            rounding=ROUND_HALF_UP,
        )

        if quantity <= 0:
            quantity = Decimal("0.001")

        key = (
            ingredient.id,
            normalized_unit,
        )

        if key not in grouped_items:
            grouped_items[key] = {
                "ingredient_id": ingredient.id,
                "name": ingredient.name,
                "quantity": quantity,
                "unit": unit,
            }
        else:
            grouped_items[key]["quantity"] += quantity

    generated_items.extend(grouped_items.values())

    shopping_list = ShoppingList(
        user_id=current_user.id,
        meal_plan_id=meal_plan.id,
        title=title or (
            meal_plan.title
            or "Liste de courses"
        ),
    )

    session.add(shopping_list)

    try:
        await session.flush()

        for position, item_data in enumerate(generated_items):
            session.add(
                ShoppingListItem(
                    shopping_list_id=shopping_list.id,
                    position=position,
                    **item_data,
                )
            )

        await session.commit()

    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The shopping list could not be generated.",
        )

    await session.refresh(shopping_list)

    return await get_shopping_list_detail(
        shopping_list,
        session,
    )


@router.get(
    "/{shopping_list_id}",
    response_model=ShoppingListDetail,
)
async def get_shopping_list(
    shopping_list_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ShoppingListDetail:
    shopping_list = await get_owned_shopping_list(
        shopping_list_id,
        session,
        current_user,
    )

    return await get_shopping_list_detail(
        shopping_list,
        session,
    )


@router.post(
    "/{shopping_list_id}/items",
    response_model=ShoppingListItemPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_shopping_list_item(
    shopping_list_id: UUID,
    item_data: ShoppingListItemCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ShoppingListItemPublic:
    shopping_list = await get_owned_shopping_list(
        shopping_list_id,
        session,
        current_user,
    )

    if item_data.ingredient_id is not None:
        ingredient = await session.scalar(
            select(Ingredient.id).where(
                Ingredient.id == item_data.ingredient_id,
            )
        )

        if ingredient is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Ingredient not found.",
            )

    item = ShoppingListItem(
        shopping_list_id=shopping_list.id,
        **item_data.model_dump(),
    )

    session.add(item)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The shopping list item could not be created.",
        )

    await session.refresh(item)

    return ShoppingListItemPublic.model_validate(item)


@router.patch(
    "/{shopping_list_id}/items/{item_id}",
    response_model=ShoppingListItemPublic,
)
async def update_shopping_list_item(
    shopping_list_id: UUID,
    item_id: UUID,
    item_data: ShoppingListItemUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ShoppingListItemPublic:
    shopping_list = await get_owned_shopping_list(
        shopping_list_id,
        session,
        current_user,
    )

    item = await session.scalar(
        select(ShoppingListItem).where(
            ShoppingListItem.id == item_id,
            ShoppingListItem.shopping_list_id == shopping_list.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list item not found.",
        )

    update_data = item_data.model_dump(exclude_unset=True)

    for field in ("name", "is_purchased", "position"):
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null.",
            )

    if update_data.get("ingredient_id") is not None:
        ingredient = await session.scalar(
            select(Ingredient.id).where(
                Ingredient.id == update_data["ingredient_id"],
            )
        )

        if ingredient is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Ingredient not found.",
            )

    for field, value in update_data.items():
        setattr(item, field, value)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The shopping list item could not be updated.",
        )

    await session.refresh(item)

    return ShoppingListItemPublic.model_validate(item)


@router.delete(
    "/{shopping_list_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_shopping_list_item(
    shopping_list_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    shopping_list = await get_owned_shopping_list(
        shopping_list_id,
        session,
        current_user,
    )

    item = await session.scalar(
        select(ShoppingListItem).where(
            ShoppingListItem.id == item_id,
            ShoppingListItem.shopping_list_id == shopping_list.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list item not found.",
        )

    await session.delete(item)
    await session.commit()


@router.delete(
    "/{shopping_list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_shopping_list(
    shopping_list_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    shopping_list = await get_owned_shopping_list(
        shopping_list_id,
        session,
        current_user,
    )

    await session.delete(shopping_list)
    await session.commit()