from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecipeCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str = Field(
        min_length=1,
        max_length=120,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    servings: int = Field(
        default=2,
        gt=0,
        le=50,
    )

    prep_time_minutes: int | None = Field(
        default=None,
        ge=0,
        le=1440,
    )

    cook_time_minutes: int | None = Field(
        default=None,
        ge=0,
        le=1440,
    )


class RecipePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    servings: int
    prep_time_minutes: int | None
    cook_time_minutes: int | None
    is_public: bool
    created_at: datetime
    updated_at: datetime