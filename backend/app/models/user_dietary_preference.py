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


class UserDietaryPreference(Base):
    __tablename__ = "user_dietary_preferences"

    __table_args__ = (
        UniqueConstraint(
            "user_preferences_id",
            "preference",
            name="uq_user_dietary_preferences_choice",
        ),
        CheckConstraint(
            "preference IN ('vegetarian', 'vegan', 'pescatarian', 'halal', 'kosher')",
            name="ck_user_dietary_preferences_valid_choice",
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

    preference: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )