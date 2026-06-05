import json
from typing import cast

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.models import RagPlaybook
from app.rag.embeddings import vector_text
from app.schemas import (
    PlaybookChunk,
    PlaybookIndexError,
    PlaybookRetrievalResult,
    RawPlaybook,
)


def upsert_playbook(db: Session, playbook: RawPlaybook) -> RagPlaybook:
    existing = (
        db.query(RagPlaybook)
        .filter(RagPlaybook.source_file == playbook.source_file)
        .one_or_none()
    )
    if existing is None:
        existing = RagPlaybook(
            title=playbook.title,
            tactic=playbook.tactic,
            source_file=playbook.source_file,
            recommended_action_hints=playbook.recommended_action_hints,
            source_refs=playbook.source_refs,
            is_active=True,
        )
        db.add(existing)
    else:
        existing.title = playbook.title
        existing.tactic = playbook.tactic
        existing.recommended_action_hints = playbook.recommended_action_hints
        existing.source_refs = playbook.source_refs
        existing.is_active = True
    db.flush()
    return existing


def replace_chunks(
    db: Session,
    playbook_id: int,
    chunks: list[PlaybookChunk],
    embeddings: list[list[float]],
) -> None:
    db.execute(
        text("DELETE FROM rag_playbook_chunks WHERE playbook_id = :playbook_id"),
        {"playbook_id": playbook_id},
    )
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        db.execute(
            text(
                """
                INSERT INTO rag_playbook_chunks (
                    playbook_id, chunk_id, section, content, embedding, metadata, created_at, modified_at
                ) VALUES (
                    :playbook_id,
                    :chunk_id,
                    :section,
                    :content,
                    CAST(:embedding AS VECTOR),
                    CAST(:metadata AS JSON),
                    NOW(),
                    NOW()
                )
                """
            ),
            {
                "playbook_id": playbook_id,
                "chunk_id": chunk.chunk_id,
                "section": chunk.section,
                "content": chunk.content,
                "embedding": vector_text(embedding),
                "metadata": json.dumps(chunk.metadata, ensure_ascii=False),
            },
        )


def retrieve_playbook_chunks(
    db: Session,
    query_embedding: list[float],
    limit: int = 5,
    tactic: str | None = None,
) -> list[PlaybookRetrievalResult]:
    if limit < 1:
        raise PlaybookIndexError("limit must be greater than or equal to 1")

    where_clause = "WHERE p.is_active = TRUE"
    params: dict[str, object] = {
        "embedding": vector_text(query_embedding),
        "limit": limit,
    }
    if tactic is not None:
        where_clause += " AND p.tactic = :tactic"
        params["tactic"] = tactic

    rows = db.execute(
        text(
            f"""
            SELECT
                c.idx AS chunk_idx,
                c.chunk_id AS chunk_id,
                c.section AS section,
                c.content AS content,
                c.metadata AS chunk_metadata,
                p.idx AS playbook_id,
                p.title AS title,
                p.tactic AS tactic,
                p.source_file AS source_file,
                p.recommended_action_hints AS recommended_action_hints,
                p.source_refs AS source_refs,
                c.embedding <=> CAST(:embedding AS VECTOR) AS distance,
                1 - (c.embedding <=> CAST(:embedding AS VECTOR)) AS similarity
            FROM rag_playbook_chunks c
            JOIN rag_playbooks p ON p.idx = c.playbook_id
            {where_clause}
            ORDER BY c.embedding <=> CAST(:embedding AS VECTOR)
            LIMIT :limit
            """
        ),
        params,
    ).mappings()

    return [retrieval_result_from_row(row) for row in rows]


def retrieval_result_from_row(row: RowMapping) -> PlaybookRetrievalResult:
    section = row["section"]
    return PlaybookRetrievalResult(
        playbook_id=int(row["playbook_id"]),
        title=str(row["title"]),
        tactic=str(row["tactic"]),
        source_file=str(row["source_file"]),
        chunk_idx=int(row["chunk_idx"]),
        chunk_id=str(row["chunk_id"]),
        section=str(section) if section is not None else None,
        content=str(row["content"]),
        metadata=cast(dict[str, object], row["chunk_metadata"]),
        recommended_action_hints=cast(
            list[str], row["recommended_action_hints"]
        ),
        source_refs=cast(list[dict[str, object]], row["source_refs"]),
        distance=float(row["distance"]),
        similarity=float(row["similarity"]),
    )
