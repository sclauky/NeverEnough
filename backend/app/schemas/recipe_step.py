from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecipeStepCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    instruction: str = Field(
        min_length=1,
        max_length=3000,
    )

    position: int = Field(
        default=0,
        ge=0,
    )


class RecipeStepPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    instruction: str
    position: int