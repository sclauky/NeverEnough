from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecipeIngredientCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    ingredient_id: UUID

    quantity: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=3,
    )

    unit: str | None = Field(
        default=None,
        max_length=30,
    )

    position: int = Field(
        default=0,
        ge=0,
    )


class RecipeIngredientPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingredient_id: UUID
    quantity: Decimal | None
    unit: str | None
    position: int