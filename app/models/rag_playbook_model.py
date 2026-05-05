from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import UserDefinedType

from app.core.database import Base


class RagPlaybook(Base):
    __tablename__: str = "rag_playbooks"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    tactic: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_file: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True, index=True
    )
    recommended_action_hints: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    source_refs: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    chunks: Mapped[list["RagPlaybookChunk"]] = relationship(
        back_populates="playbook",
        cascade="all, delete-orphan",
    )


class Vector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **kwargs: object) -> str:
        return f"VECTOR({self.dimensions})"


class RagPlaybookChunk(Base):
    __tablename__: str = "rag_playbook_chunks"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    playbook_id: Mapped[int] = mapped_column(
        ForeignKey("rag_playbooks.idx", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    section: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    chunk_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    playbook: Mapped[RagPlaybook] = relationship(back_populates="chunks")
