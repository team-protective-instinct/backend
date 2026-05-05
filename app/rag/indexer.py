from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.database import Database
from app.rag.embeddings import DEFAULT_EMBEDDING_MODEL, embed_chunks
from app.rag.loader import load_playbooks
from app.services.rag_service import replace_chunks, upsert_playbook
from app.rag.splitter import split_playbook
from app.schemas import PlaybookChunk, PlaybookIndexError, RawPlaybook


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150


@dataclass(frozen=True)
class IndexPlaybooksOptions:
    playbooks_dir: Path
    dry_run: bool
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    batch_size: int = 32
    limit: int | None = None
    embedding_model: str = DEFAULT_EMBEDDING_MODEL


def index_playbooks(options: IndexPlaybooksOptions) -> int:
    validate_options(options)
    playbooks = load_playbooks(options.playbooks_dir)
    chunks_by_source = split_all_playbooks(playbooks, options)

    print_plan(playbooks, chunks_by_source)
    if options.dry_run:
        print("Dry run enabled. Skipping embedding generation and DB writes.")
        return 0

    db_manager = Database(settings)
    db_manager.create_database()
    indexed_chunks = 0
    with db_manager.session() as db:
        for playbook in playbooks:
            chunks = chunks_by_source[playbook.source_file]
            embeddings = embed_chunks(
                chunks, options.embedding_model, options.batch_size
            )
            indexed_playbook = upsert_playbook(db, playbook)
            replace_chunks(db, indexed_playbook.idx, chunks, embeddings)
            indexed_chunks += len(chunks)
        db.commit()

    print(f"Indexed playbooks: {len(playbooks)}")
    print(f"Indexed chunks: {indexed_chunks}")
    return 0


def validate_options(options: IndexPlaybooksOptions) -> None:
    if options.chunk_size < 1:
        raise PlaybookIndexError("--chunk-size must be greater than or equal to 1")
    if options.chunk_overlap < 0:
        raise PlaybookIndexError("--chunk-overlap must be greater than or equal to 0")
    if options.chunk_overlap >= options.chunk_size:
        raise PlaybookIndexError("--chunk-overlap must be smaller than --chunk-size")
    if options.batch_size < 1:
        raise PlaybookIndexError("--batch-size must be greater than or equal to 1")
    if options.limit is not None and options.limit < 0:
        raise PlaybookIndexError("--limit must be greater than or equal to 0")


def split_all_playbooks(
    playbooks: list[RawPlaybook],
    options: IndexPlaybooksOptions,
) -> dict[str, list[PlaybookChunk]]:
    chunks_by_source = {
        playbook.source_file: split_playbook(
            playbook,
            options.chunk_size,
            options.chunk_overlap,
        )
        for playbook in playbooks
    }
    if options.limit is None:
        return chunks_by_source

    remaining = options.limit
    limited: dict[str, list[PlaybookChunk]] = {}
    for playbook in playbooks:
        chunks = chunks_by_source[playbook.source_file][:remaining]
        limited[playbook.source_file] = chunks
        remaining = max(remaining - len(chunks), 0)
    return limited


def print_plan(
    playbooks: list[RawPlaybook],
    chunks_by_source: dict[str, list[PlaybookChunk]],
) -> None:
    print(f"Loaded playbooks: {len(playbooks)}")
    print(
        f"Generated chunks: {sum(len(chunks) for chunks in chunks_by_source.values())}"
    )
    for playbook in playbooks:
        print(
            "- "
            f"source_file={playbook.source_file}; "
            f"tactic={playbook.tactic}; "
            f"title={playbook.title}; "
            f"chunks={len(chunks_by_source[playbook.source_file])}"
        )
