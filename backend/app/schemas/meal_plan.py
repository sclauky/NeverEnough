from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MealPlanCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date < self.start_date:
            raise ValueError(
                "La date de fin doit être postérieure "
                "ou égale à la date de début."
            )
        return self


class MealPlanPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    start_date: date
    end_date: date
    created_at: datetime
    updated_at: datetime