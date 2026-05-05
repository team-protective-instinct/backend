from collections.abc import Iterable

from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from app.core.config import settings
from app.schemas import PlaybookChunk, PlaybookIndexError


DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSIONS = 1536


def embed_chunks(
    chunks: list[PlaybookChunk],
    model: str,
    batch_size: int,
) -> list[list[float]]:
    if settings.OPENAI_API_KEY is None or not settings.OPENAI_API_KEY.strip():
        raise PlaybookIndexError(
            "OPENAI_API_KEY is required for playbook embedding generation"
        )

    embedder = OpenAIEmbeddings(model=model, api_key=SecretStr(settings.OPENAI_API_KEY))
    embeddings: list[list[float]] = []
    for batch in iter_batches(chunks, batch_size):
        embeddings.extend(embedder.embed_documents([chunk.content for chunk in batch]))
    return embeddings


def iter_batches(
    items: list[PlaybookChunk], batch_size: int
) -> Iterable[list[PlaybookChunk]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def vector_text(embedding: list[float]) -> str:
    if len(embedding) != DEFAULT_EMBEDDING_DIMENSIONS:
        raise PlaybookIndexError(
            f"Embedding dimension mismatch: expected {DEFAULT_EMBEDDING_DIMENSIONS}, got {len(embedding)}"
        )
    return "[" + ",".join(format(float(value), ".12g") for value in embedding) + "]"
