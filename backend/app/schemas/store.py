from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StoreCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    chain_name: str = Field(
        min_length=1,
        max_length=120,
    )

    name: str = Field(
        min_length=1,
        max_length=120,
    )

    address: str = Field(
        min_length=1,
        max_length=255,
    )

    postal_code: str = Field(
        min_length=1,
        max_length=20,
    )

    city: str = Field(
        min_length=1,
        max_length=120,
    )

    country_code: str = Field(
        default="FR",
        pattern=r"^[A-Z]{2}$",
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )


class StorePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chain_name: str
    name: str
    address: str
    postal_code: str
    city: str
    country_code: str
    latitude: float | None
    longitude: float | None
    created_at: datetime