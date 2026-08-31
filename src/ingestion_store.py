"""Injectable LangChain adapters for the Wave 1 vector-ingestion boundary."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Protocol

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy

from .ingestion_config import APPROVED_EMBEDDING_MODEL, IngestionSettings
from .ingestion_document import CHUNK_OVERLAP, CHUNK_SIZE, SOURCE_NAME


EMBEDDING_LENGTH = 1536


class EmbeddingProviderError(RuntimeError):
    """Raised when the configured embedding provider cannot be constructed."""


class VectorPersistenceError(RuntimeError):
    """Raised when the configured pgVector collection cannot be persisted."""


# These protocols deliberately describe only the seams used by this adapter.
class EmbeddingFactory(Protocol):
    def __call__(self, **kwargs: Any) -> Any: ...


class StoreFactory(Protocol):
    def __call__(self, documents: list[Document], embedding: Any, **kwargs: Any) -> Any: ...


COLLECTION_METADATA = {
    "embedding_model": APPROVED_EMBEDDING_MODEL,
    "source": SOURCE_NAME,
    "chunk_size": CHUNK_SIZE,
    "chunk_overlap": CHUNK_OVERLAP,
}


def create_embedding(
    settings: IngestionSettings,
    *,
    factory: EmbeddingFactory = OpenAIEmbeddings,
) -> Any:
    """Construct the only embedding provider allowed by the ingestion contract."""

    if settings.openai_embedding_model != APPROVED_EMBEDDING_MODEL:
        raise EmbeddingProviderError("Embedding provider configuration is invalid")
    try:
        embedding = factory(
            model=APPROVED_EMBEDDING_MODEL,
            api_key=settings.openai_api_key,
        )
    except Exception:
        # Do not retain the provider exception: it may contain request data or secrets.
        failure = EmbeddingProviderError("Embedding provider initialization failed")
    else:
        return embedding
    raise failure


def stable_chunk_id(document: Document) -> str:
    """Return the deterministic ID defined by source and zero-based chunk index."""

    source = document.metadata.get("source")
    index = document.metadata.get("chunk_index")
    if not isinstance(source, str) or not source or not isinstance(index, int) or isinstance(index, bool) or index < 0:
        raise VectorPersistenceError("Chunk metadata does not contain a valid source and index")
    return f"{source}:{index}"


def persist_chunks(
    settings: IngestionSettings,
    documents: Sequence[Document],
    embedding: Any,
    *,
    store_factory: StoreFactory = PGVector.from_documents,
) -> int:
    """Replace the configured collection with all supplied chunks and return its count."""

    chunks = list(documents)
    try:
        ids = [stable_chunk_id(document) for document in chunks]
        store_factory(
            chunks,
            embedding,
            connection=settings.database_url,
            collection_name=settings.collection_name,
            distance_strategy=DistanceStrategy.COSINE,
            embedding_length=EMBEDDING_LENGTH,
            collection_metadata=COLLECTION_METADATA.copy(),
            ids=ids,
            pre_delete_collection=True,
        )
    except VectorPersistenceError:
        raise
    except Exception:
        # Do not retain driver errors: they can contain credentials or payloads.
        failure = VectorPersistenceError(
            "PostgreSQL/pgVector persistence failed; rerun ingestion"
        )
    else:
        return len(chunks)
    raise failure


def ingest_chunks(
    settings: IngestionSettings,
    documents: Sequence[Document],
    *,
    embedding_factory: EmbeddingFactory = OpenAIEmbeddings,
    store_factory: StoreFactory = PGVector.from_documents,
) -> int:
    """Construct the provider and replace the sole configured collection."""

    embedding = create_embedding(settings, factory=embedding_factory)
    return persist_chunks(settings, documents, embedding, store_factory=store_factory)


__all__ = [
    "COLLECTION_METADATA",
    "EMBEDDING_LENGTH",
    "EmbeddingProviderError",
    "EmbeddingFactory",
    "StoreFactory",
    "VectorPersistenceError",
    "create_embedding",
    "ingest_chunks",
    "persist_chunks",
    "stable_chunk_id",
]
