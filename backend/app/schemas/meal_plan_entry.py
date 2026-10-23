from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MealPlanEntryCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    meal_plan_id: UUID
    recipe_id: UUID
    scheduled_date: date

    meal_type: Literal[
        "breakfast",
        "lunch",
        "dinner",
        "snack",
    ]

    servings: int = Field(
        default=2,
        gt=0,
        le=50,
    )

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )


class MealPlanEntryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    meal_plan_id: UUID
    recipe_id: UUID
    scheduled_date: date
    meal_type: Literal[
        "breakfast",
        "lunch",
        "dinner",
        "snack",
    ]
    servings: int
    notes: str | None
    created_at: datetime