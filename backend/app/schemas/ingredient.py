from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IngredientPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    category: str | None
    parent_id: UUID | None
    created_at: datetime