from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "496883bd4388"
down_revision: Union[str, Sequence[str], None] = "0c402d87241b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_budgets",
        sa.Column(
            "people_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )

    op.create_check_constraint(
        "ck_user_budgets_people_count_positive",
        "user_budgets",
        "people_count > 0",
    )

    op.alter_column(
        "user_budgets",
        "people_count",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_user_budgets_people_count_positive",
        "user_budgets",
        type_="check",
    )

    op.drop_column("user_budgets", "people_count")