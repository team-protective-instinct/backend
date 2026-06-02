"""add source type to incident raw logs

Revision ID: a4e6c1b9d2f8
Revises: 636dd064cec7
Create Date: 2026-06-02 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a4e6c1b9d2f8"
down_revision: Union[str, Sequence[str], None] = "636dd064cec7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "incident_raw_logs",
        sa.Column(
            "source_type",
            sa.String(length=50),
            server_default="webhook",
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_incident_raw_logs_source_type"),
        "incident_raw_logs",
        ["source_type"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_incident_raw_logs_source_type"), table_name="incident_raw_logs"
    )
    op.drop_column("incident_raw_logs", "source_type")
