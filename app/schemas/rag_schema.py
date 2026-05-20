from dataclasses import dataclass


class PlaybookIndexError(Exception):
    pass


@dataclass(frozen=True)
class RawPlaybook:
    title: str
    tactic: str
    source_file: str
    content: str
    recommended_action_hints: list[str]
    source_refs: list[dict[str, object]]


@dataclass(frozen=True)
class PlaybookChunk:
    chunk_id: str
    section: str | None
    content: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class PlaybookRetrievalResult:
    playbook_id: int
    title: str
    tactic: str
    source_file: str
    chunk_idx: int
    chunk_id: str
    section: str | None
    content: str
    metadata: dict[str, object]
    recommended_action_hints: list[str]
    source_refs: list[dict[str, object]]
    distance: float
    similarity: float
