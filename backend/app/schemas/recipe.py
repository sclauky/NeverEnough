
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.recipe_ingredient import RecipeIngredientCreate, RecipeIngredientPublic
from app.schemas.recipe_step import RecipeStepCreate, RecipeStepPublic


class RecipeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = None
    servings: int = Field(default=2, ge=1)
    prep_time_minutes: int | None = Field(default=None, ge=0)
    cook_time_minutes: int | None = Field(default=None, ge=0)
    is_public: bool = False
    ingredients: list[RecipeIngredientCreate] = Field(default_factory=list)
    steps: list[RecipeStepCreate] = Field(default_factory=list)

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class RecipeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    servings: int | None = Field(default=None, ge=1)
    prep_time_minutes: int | None = Field(default=None, ge=0)
    cook_time_minutes: int | None = Field(default=None, ge=0)
    is_public: bool | None = None
    ingredients: list[RecipeIngredientCreate] | None = None
    steps: list[RecipeStepCreate] | None = None

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.strip()
        return value


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


class RecipeDetail(RecipePublic):
    ingredients: list[RecipeIngredientPublic]
    steps: list[RecipeStepPublic]