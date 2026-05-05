import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import RagPlaybook
from app.rag.embeddings import vector_text
from app.schemas import PlaybookChunk, RawPlaybook


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
