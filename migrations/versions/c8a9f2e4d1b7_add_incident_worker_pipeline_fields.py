"""add incident worker pipeline fields

Revision ID: c8a9f2e4d1b7
Revises: b1d4f8c2e7a9
Create Date: 2026-05-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c8a9f2e4d1b7"
down_revision: Union[str, Sequence[str], None] = "b1d4f8c2e7a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "incidents",
        "thread_id",
        existing_type=sa.String(length=255),
        nullable=True,
    )
    op.add_column("incidents", sa.Column("raw_payload", sa.JSON(), nullable=True))
    op.add_column(
        "incidents",
        sa.Column(
            "analysis_status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "incidents",
        sa.Column("analysis_attempts", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("incidents", sa.Column("analysis_last_error", sa.Text(), nullable=True))
    op.add_column(
        "incidents", sa.Column("response_plan_status", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "incidents",
        sa.Column(
            "response_plan_attempts", sa.Integer(), server_default="0", nullable=False
        ),
    )
    op.add_column(
        "incidents", sa.Column("response_plan_last_error", sa.Text(), nullable=True)
    )
    op.execute(
        """
        UPDATE incidents
        SET analysis_status = CASE
            WHEN is_identified_threat IS TRUE THEN 'completed'
            WHEN is_identified_threat IS FALSE THEN 'completed'
            ELSE 'pending'
        END
        """
    )
    op.execute(
        """
        UPDATE incidents
        SET response_plan_status = 'pending'
        WHERE is_identified_threat IS TRUE
          AND NOT EXISTS (
              SELECT 1
              FROM response_plans
              WHERE response_plans.incident_idx = incidents.idx
          )
        """
    )
    op.create_index(
        op.f("ix_incidents_analysis_status"),
        "incidents",
        ["analysis_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incidents_response_plan_status"),
        "incidents",
        ["response_plan_status"],
        unique=False,
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_incidents_response_plan_status"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_analysis_status"), table_name="incidents")
    op.drop_column("incidents", "response_plan_last_error")
    op.drop_column("incidents", "response_plan_attempts")
    op.drop_column("incidents", "response_plan_status")
    op.drop_column("incidents", "analysis_last_error")
    op.drop_column("incidents", "analysis_attempts")
    op.drop_column("incidents", "analysis_status")
    op.drop_column("incidents", "raw_payload")
    op.alter_column(
        "incidents",
        "thread_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )
