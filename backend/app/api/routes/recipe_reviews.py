from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.recipe import Recipe
from app.models.recipe_review import RecipeReview
from app.models.user import User
from app.schemas.recipe_review import (
    RecipeReviewCreate,
    RecipeReviewList,
    RecipeReviewPublic,
    RecipeReviewUpdate,
)


router = APIRouter(prefix="/recipes", tags=["Recipe Reviews"])


async def get_review_or_404(
    review_id: UUID,
    session: AsyncSession,
    current_user: User,
) -> RecipeReview:
    result = await session.execute(
        select(RecipeReview).where(
            RecipeReview.id == review_id,
            RecipeReview.user_id == current_user.id,
        )
    )

    review = result.scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    return review


@router.get(
    "/{recipe_id}/reviews",
    response_model=RecipeReviewList,
)
async def get_recipe_reviews(
    recipe_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> RecipeReviewList:
    result = await session.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.is_public.is_(True),
        )
    )

    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found.",
        )

    result = await session.execute(
        select(
            func.avg(RecipeReview.rating),
            func.count(RecipeReview.id),
        ).where(RecipeReview.recipe_id == recipe_id)
    )

    average_rating, review_count = result.one()

    result = await session.execute(
        select(RecipeReview, User.username)
        .join(User, User.id == RecipeReview.user_id)
        .where(RecipeReview.recipe_id == recipe_id)
        .order_by(RecipeReview.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    reviews = [
        RecipeReviewPublic(
            id=review.id,
            recipe_id=review.recipe_id,
            username=username,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
        for review, username in result.all()
    ]

    return RecipeReviewList(
        average_rating=round(float(average_rating or 0), 2),
        review_count=review_count,
        reviews=reviews,
    )


@router.post(
    "/{recipe_id}/reviews",
    response_model=RecipeReviewPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_recipe_review(
    recipe_id: UUID,
    review_data: RecipeReviewCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RecipeReviewPublic:
    result = await session.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.is_public.is_(True),
        )
    )

    recipe = result.scalar_one_or_none()

    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found.",
        )

    if recipe.author_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot review your own recipe.",
        )

    review = RecipeReview(
        user_id=current_user.id,
        recipe_id=recipe_id,
        rating=review_data.rating,
        comment=review_data.comment,
    )

    session.add(review)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this recipe.",
        )

    await session.refresh(review)

    return RecipeReviewPublic(
        id=review.id,
        recipe_id=review.recipe_id,
        username=current_user.username,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.patch(
    "/reviews/{review_id}",
    response_model=RecipeReviewPublic,
)
async def update_recipe_review(
    review_id: UUID,
    review_data: RecipeReviewUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RecipeReviewPublic:
    review = await get_review_or_404(
        review_id,
        session,
        current_user,
    )

    update_data = review_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one field must be provided.",
        )

    for field, value in update_data.items():
        setattr(review, field, value)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The review could not be updated.",
        )

    await session.refresh(review)

    return RecipeReviewPublic(
        id=review.id,
        recipe_id=review.recipe_id,
        username=current_user.username,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_recipe_review(
    review_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    review = await get_review_or_404(
        review_id,
        session,
        current_user,
    )

    await session.delete(review)
    await session.commit()