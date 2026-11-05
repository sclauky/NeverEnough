
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.recipe_step import RecipeStep
from app.models.user import User
from app.schemas.recipe import RecipeCreate, RecipeDetail


router = APIRouter(prefix="/recipes", tags=["Recipes"])


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

    return RecipeDetail.model_validate(recipe)