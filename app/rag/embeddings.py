from collections.abc import Iterable

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import SecretStr

from app.core.config import settings
from app.schemas import PlaybookChunk, PlaybookIndexError


DEFAULT_EMBEDDING_MODEL = settings.RAG_EMBEDDING_MODEL
DEFAULT_EMBEDDING_DIMENSIONS = 1536
DOCUMENT_TASK_TYPE = "RETRIEVAL_DOCUMENT"
QUERY_TASK_TYPE = "RETRIEVAL_QUERY"


def embed_chunks(
    chunks: list[PlaybookChunk],
    model: str,
    batch_size: int,
) -> list[list[float]]:
    embedder = create_embedder(model)
    embeddings: list[list[float]] = []
    for batch in iter_batches(chunks, batch_size):
        embeddings.extend(
            embedder.embed_documents(
                [chunk.content for chunk in batch],
                task_type=DOCUMENT_TASK_TYPE,
                output_dimensionality=DEFAULT_EMBEDDING_DIMENSIONS,
            )
        )
    return embeddings


def embed_query(query: str, model: str = DEFAULT_EMBEDDING_MODEL) -> list[float]:
    stripped_query = query.strip()
    if not stripped_query:
        raise PlaybookIndexError("Query text is required for playbook retrieval")
    return create_embedder(model).embed_query(
        stripped_query,
        task_type=QUERY_TASK_TYPE,
        output_dimensionality=DEFAULT_EMBEDDING_DIMENSIONS,
    )


def create_embedder(model: str) -> GoogleGenerativeAIEmbeddings:
    if settings.GOOGLE_API_KEY is None or not settings.GOOGLE_API_KEY.strip():
        raise PlaybookIndexError(
            "GOOGLE_API_KEY is required for playbook embedding generation"
        )
    return GoogleGenerativeAIEmbeddings(
        model=model,
        api_key=SecretStr(settings.GOOGLE_API_KEY),
        output_dimensionality=DEFAULT_EMBEDDING_DIMENSIONS,
    )


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
