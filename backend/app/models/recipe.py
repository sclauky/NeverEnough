import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    Uuid,
    cast,
    func,
    select,
)
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.db.base import Base
from app.models.recipe_review import RecipeReview


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

    average_rating: Mapped[float] = column_property(
        select(
            cast(
                func.coalesce(
                    func.round(func.avg(RecipeReview.rating), 2),
                    0.0,
                ),
                Float,
            )
        )
        .where(RecipeReview.recipe_id == id)
        .correlate_except(RecipeReview)
        .scalar_subquery()
    )

    review_count: Mapped[int] = column_property(
        select(func.count(RecipeReview.id))
        .where(RecipeReview.recipe_id == id)
        .correlate_except(RecipeReview)
        .scalar_subquery()
    )

    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeIngredient.position",
    )

    steps: Mapped[list["RecipeStep"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeStep.position",
    )