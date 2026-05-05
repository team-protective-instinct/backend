"""add rag playbook tables

Revision ID: 3c4f1b8d9a2e
Revises: f9613daf678a
Create Date: 2026-05-05 09:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


class Vector(sa.types.UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **kwargs: object) -> str:
        return f"VECTOR({self.dimensions})"


# revision identifiers, used by Alembic.
revision: str = "3c4f1b8d9a2e"
down_revision: Union[str, Sequence[str], None] = "f9613daf678a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "rag_playbooks",
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("tactic", sa.String(length=100), nullable=False),
        sa.Column("source_file", sa.String(length=500), nullable=False),
        sa.Column("recommended_action_hints", sa.JSON(), nullable=False),
        sa.Column("source_refs", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("idx"),
        sa.UniqueConstraint("source_file"),
    )
    op.create_index(op.f("ix_rag_playbooks_idx"), "rag_playbooks", ["idx"], unique=False)
    op.create_index(op.f("ix_rag_playbooks_source_file"), "rag_playbooks", ["source_file"], unique=False)
    op.create_index(op.f("ix_rag_playbooks_tactic"), "rag_playbooks", ["tactic"], unique=False)

    op.create_table(
        "rag_playbook_chunks",
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("playbook_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.String(length=255), nullable=False),
        sa.Column("section", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["playbook_id"], ["rag_playbooks.idx"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("idx"),
        sa.UniqueConstraint("chunk_id"),
    )
    op.create_index(op.f("ix_rag_playbook_chunks_chunk_id"), "rag_playbook_chunks", ["chunk_id"], unique=False)
    op.create_index(op.f("ix_rag_playbook_chunks_idx"), "rag_playbook_chunks", ["idx"], unique=False)
    op.create_index(op.f("ix_rag_playbook_chunks_playbook_id"), "rag_playbook_chunks", ["playbook_id"], unique=False)
    op.create_index(op.f("ix_rag_playbook_chunks_section"), "rag_playbook_chunks", ["section"], unique=False)
    op.create_index(
        "ix_rag_playbook_chunks_embedding_cosine",
        "rag_playbook_chunks",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"lists": 100},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_rag_playbook_chunks_embedding_cosine", table_name="rag_playbook_chunks")
    op.drop_index(op.f("ix_rag_playbook_chunks_section"), table_name="rag_playbook_chunks")
    op.drop_index(op.f("ix_rag_playbook_chunks_playbook_id"), table_name="rag_playbook_chunks")
    op.drop_index(op.f("ix_rag_playbook_chunks_idx"), table_name="rag_playbook_chunks")
    op.drop_index(op.f("ix_rag_playbook_chunks_chunk_id"), table_name="rag_playbook_chunks")
    op.drop_table("rag_playbook_chunks")

    op.drop_index(op.f("ix_rag_playbooks_tactic"), table_name="rag_playbooks")
    op.drop_index(op.f("ix_rag_playbooks_source_file"), table_name="rag_playbooks")
    op.drop_index(op.f("ix_rag_playbooks_idx"), table_name="rag_playbooks")
    op.drop_table("rag_playbooks")
