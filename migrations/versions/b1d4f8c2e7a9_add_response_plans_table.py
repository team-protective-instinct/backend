"""add response plans table

Revision ID: b1d4f8c2e7a9
Revises: 3c4f1b8d9a2e
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1d4f8c2e7a9"
down_revision: Union[str, Sequence[str], None] = "3c4f1b8d9a2e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "response_plans",
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("incident_idx", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("plan_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("denied_at", sa.DateTime(), nullable=True),
        sa.Column("denied_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["incident_idx"], ["incidents.idx"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("idx"),
    )
    op.create_index(op.f("ix_response_plans_idx"), "response_plans", ["idx"], unique=False)
    op.create_index(
        op.f("ix_response_plans_incident_idx"),
        "response_plans",
        ["incident_idx"],
        unique=False,
    )
    op.create_index(
        op.f("ix_response_plans_thread_id"),
        "response_plans",
        ["thread_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_response_plans_status"),
        "response_plans",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_response_plans_status"), table_name="response_plans")
    op.drop_index(op.f("ix_response_plans_thread_id"), table_name="response_plans")
    op.drop_index(op.f("ix_response_plans_incident_idx"), table_name="response_plans")
    op.drop_index(op.f("ix_response_plans_idx"), table_name="response_plans")
    op.drop_table("response_plans")
