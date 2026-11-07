from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecipeReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class RecipeReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class RecipeReviewPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recipe_id: UUID
    username: str
    rating: int
    comment: str | None
    created_at: datetime
    updated_at: datetime


class RecipeReviewList(BaseModel):
    average_rating: float
    review_count: int
    reviews: list[RecipeReviewPublic]