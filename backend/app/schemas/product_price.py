from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductPriceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    store_id: UUID

    price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

    currency_code: str = Field(
        default="EUR",
        pattern=r"^[A-Z]{3}$",
    )

    is_promotion: bool = False

    observed_at: datetime


class ProductPricePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    store_id: UUID
    price: Decimal
    currency_code: str
    is_promotion: bool
    observed_at: datetime
    created_at: datetime