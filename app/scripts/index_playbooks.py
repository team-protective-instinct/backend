from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.rag.embeddings import DEFAULT_EMBEDDING_MODEL
from app.rag.indexer import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    IndexPlaybooksOptions,
    index_playbooks,
)
from app.schemas import PlaybookIndexError


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Index Markdown playbooks into the RAG VectorDB tables."
    )
    parser.add_argument(
        "--playbooks-dir",
        default="playbooks",
        help="Directory containing Markdown playbook files, relative to project root by default.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and split playbooks, but skip embedding generation and DB writes.",
    )
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--limit", type=int, default=None, help="Only index the first N chunks."
    )
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    return parser.parse_args(argv)


def resolve_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def options_from_args(args: argparse.Namespace) -> IndexPlaybooksOptions:
    return IndexPlaybooksOptions(
        playbooks_dir=resolve_path(args.playbooks_dir),
        dry_run=args.dry_run,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size,
        limit=args.limit,
        embedding_model=args.embedding_model,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        return index_playbooks(options_from_args(parse_args(argv)))
    except PlaybookIndexError as exc:
        print(f"Playbook indexing failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
