from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    ingredient_id: UUID

    name: str = Field(
        min_length=1,
        max_length=200,
    )

    brand: str | None = Field(
        default=None,
        max_length=120,
    )

    barcode: str | None = Field(
        default=None,
        max_length=32,
        pattern=r"^[0-9]+$",
    )

    package_quantity: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=3,
    )

    package_unit: str = Field(
        min_length=1,
        max_length=20,
    )


class ProductPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingredient_id: UUID
    name: str
    brand: str | None
    barcode: str | None
    package_quantity: Decimal
    package_unit: str
    created_at: datetime