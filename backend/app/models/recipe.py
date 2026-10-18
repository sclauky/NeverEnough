import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Recipe(Base):
    __tablename__ = "recipes"

    __table_args__ = (
        CheckConstraint(
            "servings > 0",
            name="ck_recipes_servings_positive",
        ),
        CheckConstraint(
            "prep_time_minutes IS NULL OR prep_time_minutes >= 0",
            name="ck_recipes_prep_time_nonnegative",
        ),
        CheckConstraint(
            "cook_time_minutes IS NULL OR cook_time_minutes >= 0",
            name="ck_recipes_cook_time_nonnegative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    servings: Mapped[int] = mapped_column(
        default=2,
        nullable=False,
    )

    prep_time_minutes: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    cook_time_minutes: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    image_key: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )