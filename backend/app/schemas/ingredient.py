
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IngredientPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    category: str | None
    created_at: datetime
