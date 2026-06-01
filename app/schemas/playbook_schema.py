from datetime import datetime

from pydantic import BaseModel, Field

from app.models import RagPlaybook, RagPlaybookChunk


class PlaybookListItemResponse(BaseModel):
    idx: int
    title: str
    tactic: str
    source_file: str
    recommended_action_hints: list[str]
    source_refs: list[dict[str, object]]
    is_active: bool
    created_at: datetime
    modified_at: datetime

    @classmethod
    def from_playbook(cls, playbook: RagPlaybook) -> "PlaybookListItemResponse":
        return cls(
            idx=playbook.idx,
            title=playbook.title,
            tactic=playbook.tactic,
            source_file=playbook.source_file,
            recommended_action_hints=playbook.recommended_action_hints,
            source_refs=playbook.source_refs,
            is_active=playbook.is_active,
            created_at=playbook.created_at,
            modified_at=playbook.modified_at,
        )


class PlaybookChunkResponse(BaseModel):
    idx: int
    playbook_id: int
    chunk_id: str
    section: str | None
    content: str
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    modified_at: datetime

    @classmethod
    def from_chunk(cls, chunk: RagPlaybookChunk) -> "PlaybookChunkResponse":
        return cls(
            idx=chunk.idx,
            playbook_id=chunk.playbook_id,
            chunk_id=chunk.chunk_id,
            section=chunk.section,
            content=chunk.content,
            metadata=chunk.chunk_metadata,
            created_at=chunk.created_at,
            modified_at=chunk.modified_at,
        )


class PlaybookDetailResponse(PlaybookListItemResponse):
    chunks: list[PlaybookChunkResponse]

    @classmethod
    def from_playbook(cls, playbook: RagPlaybook) -> "PlaybookDetailResponse":
        return cls(
            idx=playbook.idx,
            title=playbook.title,
            tactic=playbook.tactic,
            source_file=playbook.source_file,
            recommended_action_hints=playbook.recommended_action_hints,
            source_refs=playbook.source_refs,
            is_active=playbook.is_active,
            created_at=playbook.created_at,
            modified_at=playbook.modified_at,
            chunks=[
                PlaybookChunkResponse.from_chunk(chunk)
                for chunk in sorted(playbook.chunks, key=lambda item: item.idx)
            ],
        )
