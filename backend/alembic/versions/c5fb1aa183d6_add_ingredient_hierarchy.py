
"""add ingredient hierarchy"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c5fb1aa183d6"
down_revision: Union[str, Sequence[str], None] = "d1c9f5faecb7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ingredients",
        sa.Column("parent_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        "ix_ingredients_parent_id",
        "ingredients",
        ["parent_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_ingredients_parent_id_ingredients",
        "ingredients",
        "ingredients",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_ingredients_parent_id_ingredients",
        "ingredients",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_ingredients_parent_id",
        table_name="ingredients",
    )
    op.drop_column("ingredients", "parent_id")
