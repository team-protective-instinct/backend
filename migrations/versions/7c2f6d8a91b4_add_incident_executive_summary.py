"""add incident executive summary

Revision ID: 7c2f6d8a91b4
Revises: 2ab90dd1fb4b
Create Date: 2026-04-28 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c2f6d8a91b4"
down_revision: Union[str, Sequence[str], None] = "2ab90dd1fb4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("incidents", sa.Column("executive_summary", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("incidents", "executive_summary")
