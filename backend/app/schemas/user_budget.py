from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserBudgetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

    period_type: Literal["week", "month"]


class UserBudgetPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: Decimal
    period_type: Literal["week", "month"]
    created_at: datetime
    updated_at: datetime