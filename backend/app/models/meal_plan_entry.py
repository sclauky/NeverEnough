import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MealPlanEntry(Base):
    __tablename__ = "meal_plan_entries"

    __table_args__ = (
        CheckConstraint(
            "servings > 0",
            name="ck_meal_plan_entries_servings_positive",
        ),
        CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="ck_meal_plan_entries_valid_meal_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    meal_plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("meal_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recipes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    meal_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    servings: Mapped[int] = mapped_column(
        Integer,
        default=2,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )