"""remove auth users table

Revision ID: 8f0c2a4d7b31
Revises: e7fc6e9c12f9
Create Date: 2026-05-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f0c2a4d7b31"
down_revision: Union[str, Sequence[str], None] = "e7fc6e9c12f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP TABLE IF EXISTS users")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "users",
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("idx"),
    )
    op.create_index(op.f("ix_users_idx"), "users", ["idx"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
