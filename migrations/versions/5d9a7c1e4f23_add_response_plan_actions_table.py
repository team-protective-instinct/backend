"""add response plan actions table

Revision ID: 5d9a7c1e4f23
Revises: 8f0c2a4d7b31
Create Date: 2026-05-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5d9a7c1e4f23"
down_revision: Union[str, Sequence[str], None] = "8f0c2a4d7b31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "response_plan_actions",
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("response_plan_idx", sa.Integer(), nullable=False),
        sa.Column("execution_order", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["response_plan_idx"], ["response_plans.idx"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("idx"),
    )
    op.create_index(
        op.f("ix_response_plan_actions_idx"),
        "response_plan_actions",
        ["idx"],
        unique=False,
    )
    op.create_index(
        op.f("ix_response_plan_actions_response_plan_idx"),
        "response_plan_actions",
        ["response_plan_idx"],
        unique=False,
    )
    op.create_index(
        op.f("ix_response_plan_actions_status"),
        "response_plan_actions",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_response_plan_actions_tool_name"),
        "response_plan_actions",
        ["tool_name"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_response_plan_actions_tool_name"), table_name="response_plan_actions")
    op.drop_index(op.f("ix_response_plan_actions_status"), table_name="response_plan_actions")
    op.drop_index(
        op.f("ix_response_plan_actions_response_plan_idx"),
        table_name="response_plan_actions",
    )
    op.drop_index(op.f("ix_response_plan_actions_idx"), table_name="response_plan_actions")
    op.drop_table("response_plan_actions")
