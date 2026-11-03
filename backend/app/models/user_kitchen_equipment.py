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


class UserKitchenEquipment(Base):
    __tablename__ = "user_kitchen_equipment"

    __table_args__ = (
        UniqueConstraint(
            "user_preferences_id",
            "equipment",
            name="uq_user_kitchen_equipment_choice",
        ),
        CheckConstraint(
            "equipment IN ('oven', 'microwave', 'air_fryer', 'stovetop', 'kettle', 'toaster', 'blender', 'food_processor', 'rice_cooker')",
            name="ck_user_kitchen_equipment_valid_choice",
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

    equipment: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )