"""add push tokens table

Revision ID: e2f4a6b8c9d1
Revises: d3b7a9e5c1f4
Create Date: 2026-06-04 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e2f4a6b8c9d1"
down_revision: Union[str, Sequence[str], None] = "d3b7a9e5c1f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("push_tokens"):
        return

    op.create_table(
        "push_tokens",
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("platform", sa.String(length=30), nullable=False),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("idx"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(op.f("ix_push_tokens_idx"), "push_tokens", ["idx"], unique=False)
    op.create_index(
        op.f("ix_push_tokens_token"), "push_tokens", ["token"], unique=False
    )
    op.create_index(
        op.f("ix_push_tokens_platform"), "push_tokens", ["platform"], unique=False
    )
    op.create_index(
        op.f("ix_push_tokens_is_active"), "push_tokens", ["is_active"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("push_tokens"):
        return

    op.drop_index(op.f("ix_push_tokens_is_active"), table_name="push_tokens")
    op.drop_index(op.f("ix_push_tokens_platform"), table_name="push_tokens")
    op.drop_index(op.f("ix_push_tokens_token"), table_name="push_tokens")
    op.drop_index(op.f("ix_push_tokens_idx"), table_name="push_tokens")
    op.drop_table("push_tokens")
