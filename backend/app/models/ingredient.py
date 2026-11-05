import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
    )

    category: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True,
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ingredients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    parent: Mapped["Ingredient | None"] = relationship(
        back_populates="variants",
        remote_side="Ingredient.id",
    )

    variants: Mapped[list["Ingredient"]] = relationship(
        back_populates="parent",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )