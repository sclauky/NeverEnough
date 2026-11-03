
import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    Uuid,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserAllergy(Base):
    __tablename__ = "user_allergies"

    __table_args__ = (
        UniqueConstraint(
            "user_preferences_id",
            "allergy",
            name="uq_user_allergies_choice",
        ),
        CheckConstraint(
            "allergy IN ('peanuts', 'tree_nuts', 'milk', 'eggs', 'soy', 'wheat', 'fish', 'shellfish', 'sesame')",
            name="ck_user_allergies_valid_choice",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_preferences_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_preferences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    allergy: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )