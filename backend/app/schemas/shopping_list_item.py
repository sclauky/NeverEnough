from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ShoppingListItemCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    ingredient_id: UUID | None = None

    name: str = Field(
        min_length=1,
        max_length=120,
    )

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


class ShoppingListItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shopping_list_id: UUID
    ingredient_id: UUID | None
    name: str
    quantity: Decimal | None
    unit: str | None
    is_purchased: bool
    position: int
    created_at: datetime