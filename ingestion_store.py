"""Root-level import bridge for the vector-ingestion store adapter."""

from src.ingestion_store import (
    COLLECTION_METADATA,
    EMBEDDING_LENGTH,
    EmbeddingFactory,
    EmbeddingProviderError,
    StoreFactory,
    VectorPersistenceError,
    create_embedding,
    ingest_chunks,
    persist_chunks,
    stable_chunk_id,
)

__all__ = [
    "COLLECTION_METADATA",
    "EMBEDDING_LENGTH",
    "EmbeddingFactory",
    "EmbeddingProviderError",
    "StoreFactory",
    "VectorPersistenceError",
    "create_embedding",
    "ingest_chunks",
    "persist_chunks",
    "stable_chunk_id",
]
