from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ShoppingListCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    meal_plan_id: UUID | None = None


class ShoppingListPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    meal_plan_id: UUID | None
    title: str | None
    created_at: datetime
    updated_at: datetime