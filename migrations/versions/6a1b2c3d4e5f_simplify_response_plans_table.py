"""simplify response plans table

Revision ID: 6a1b2c3d4e5f
Revises: 5d9a7c1e4f23
Create Date: 2026-05-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6a1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "5d9a7c1e4f23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("response_plans", "approved_at")
    op.drop_column("response_plans", "denied_at")
    op.drop_column("response_plans", "plan_text")
    op.drop_column("response_plans", "rationale")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("response_plans", sa.Column("rationale", sa.Text(), nullable=True))
    op.add_column(
        "response_plans",
        sa.Column("plan_text", sa.Text(), nullable=False, server_default=""),
    )
    op.alter_column("response_plans", "plan_text", server_default=None)
    op.add_column("response_plans", sa.Column("denied_at", sa.DateTime(), nullable=True))
    op.add_column("response_plans", sa.Column("approved_at", sa.DateTime(), nullable=True))
