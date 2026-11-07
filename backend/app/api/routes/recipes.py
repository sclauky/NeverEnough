
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.recipe_step import RecipeStep
from app.models.user import User
from app.schemas.recipe import (
    RecipeCreate,
    RecipeDetail,
    RecipePublic,
    RecipeUpdate,
)


router = APIRouter(prefix="/recipes", tags=["Recipes"])


async def get_recipe_or_404(
    recipe_id: UUID,
    session: AsyncSession,
    current_user: User,
) -> Recipe:
    result = await session.execute(
        select(Recipe)
        .options(
            selectinload(Recipe.ingredients),
            selectinload(Recipe.steps),
        )
        .where(Recipe.id == recipe_id)
    )

    recipe = result.scalar_one_or_none()

    if recipe is None or recipe.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found.",
        )

    return recipe


@router.post(
    "",
    response_model=RecipeDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_recipe(
    recipe_data: RecipeCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RecipeDetail:
    if not recipe_data.ingredients:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A recipe must contain at least one ingredient.",
        )

    if not recipe_data.steps:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A recipe must contain at least one preparation step.",
        )

    ingredient_ids = {
        item.ingredient_id for item in recipe_data.ingredients
    }

    result = await session.execute(
        select(Ingredient.id).where(Ingredient.id.in_(ingredient_ids))
    )
    existing_ingredient_ids = set(result.scalars().all())

    if ingredient_ids != existing_ingredient_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more ingredients do not exist.",
        )

    recipe = Recipe(
        **recipe_data.model_dump(exclude={"ingredients", "steps"}),
        author_id=current_user.id,
        ingredients=[
            RecipeIngredient(
                ingredient_id=item.ingredient_id,
                quantity=item.quantity,
                unit=item.unit,
                position=index,
            )
            for index, item in enumerate(recipe_data.ingredients)
        ],
        steps=[
            RecipeStep(
                instruction=item.instruction,
                position=index,
            )
            for index, item in enumerate(recipe_data.steps)
        ],
    )

    session.add(recipe)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The recipe could not be saved.",
        )

    result = await session.execute(
        select(Recipe)
        .options(
            selectinload(Recipe.ingredients),
            selectinload(Recipe.steps),
        )
        .where(Recipe.id == recipe.id)
    )

    return RecipeDetail.model_validate(result.scalar_one())


@router.get("", response_model=list[RecipePublic])
async def get_recipes(
    search: str | None = Query(default=None, min_length=1, max_length=120),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[RecipePublic]:
    query = select(Recipe).where(Recipe.is_public.is_(True))

    if search:
        query = query.where(
            Recipe.title.ilike(f"%{search.strip()}%")
        )

    query = (
        query
        .order_by(Recipe.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(query)

    return [
        RecipePublic.model_validate(recipe)
        for recipe in result.scalars().all()
    ]


@router.get("/me", response_model=list[RecipePublic])
async def get_my_recipes(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[RecipePublic]:
    query = (
        select(Recipe)
        .where(Recipe.author_id == current_user.id)
        .order_by(Recipe.created_at.desc())
    )

    result = await session.execute(query)

    return [
        RecipePublic.model_validate(recipe)
        for recipe in result.scalars().all()
    ]


@router.get("/{recipe_id}", response_model=RecipeDetail)
async def get_recipe(
    recipe_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RecipeDetail:
    result = await session.execute(
        select(Recipe)
        .options(
            selectinload(Recipe.ingredients),
            selectinload(Recipe.steps),
        )
        .where(Recipe.id == recipe_id)
    )

    recipe = result.scalar_one_or_none()

    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found.",
        )

    if not recipe.is_public and recipe.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found.",
        )

    return RecipeDetail.model_validate(recipe)


@router.patch("/{recipe_id}", response_model=RecipeDetail)
async def update_recipe(
    recipe_id: UUID,
    recipe_data: RecipeUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RecipeDetail:
    recipe = await get_recipe_or_404(
        recipe_id,
        session,
        current_user,
    )

    update_data = recipe_data.model_dump(
        exclude_unset=True,
        exclude={"ingredients", "steps"},
    )

    if "title" in update_data and update_data["title"] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Recipe title cannot be null.",
        )

    for field, value in update_data.items():
        setattr(recipe, field, value)

    if "ingredients" in recipe_data.model_fields_set:
        if not recipe_data.ingredients:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A recipe must contain at least one ingredient.",
            )

        ingredient_ids = {
            item.ingredient_id for item in recipe_data.ingredients
        }

        result = await session.execute(
            select(Ingredient.id).where(Ingredient.id.in_(ingredient_ids))
        )
        existing_ids = set(result.scalars().all())

        if ingredient_ids != existing_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="One or more ingredients do not exist.",
            )

        recipe.ingredients = [
            RecipeIngredient(
                ingredient_id=item.ingredient_id,
                quantity=item.quantity,
                unit=item.unit,
                position=index,
            )
            for index, item in enumerate(recipe_data.ingredients)
        ]

    if "steps" in recipe_data.model_fields_set:
        if not recipe_data.steps:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A recipe must contain at least one preparation step.",
            )

        recipe.steps = [
            RecipeStep(
                instruction=item.instruction,
                position=index,
            )
            for index, item in enumerate(recipe_data.steps)
        ]

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The recipe could not be updated.",
        )

    result = await session.execute(
        select(Recipe)
        .options(
            selectinload(Recipe.ingredients),
            selectinload(Recipe.steps),
        )
        .where(Recipe.id == recipe_id)
    )

    return RecipeDetail.model_validate(result.scalar_one())


@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_recipe(
    recipe_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    recipe = await get_recipe_or_404(
        recipe_id,
        session,
        current_user,
    )

    await session.delete(recipe)
    await session.commit()