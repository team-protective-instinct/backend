"""drop evidence logs from incident raw logs

Revision ID: d3b7a9e5c1f4
Revises: a4e6c1b9d2f8
Create Date: 2026-06-02 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d3b7a9e5c1f4"
down_revision: Union[str, Sequence[str], None] = "a4e6c1b9d2f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("incident_raw_logs", "evidence_logs")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "incident_raw_logs",
        sa.Column("evidence_logs", sa.Text(), nullable=False, server_default=""),
    )
