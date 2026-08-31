"""Testable orchestration for the Wave 1 ingestion flow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from .ingestion_config import IngestionSettings
from .ingestion_document import load_and_chunk
from .ingestion_store import create_embedding, persist_chunks


@dataclass(frozen=True)
class IngestionResult:
    """Safe summary returned after the replacement store operation completes."""

    source_name: str
    collection_name: str
    chunk_count: int


def ingest(
    settings: IngestionSettings,
    *,
    loader_factory: Any = PyPDFLoader,
    embedding_factory: Any = OpenAIEmbeddings,
    store_factory: Any = PGVector.from_documents,
) -> IngestionResult:
    """Load, chunk, embed, and replace the configured corpus in order."""

    chunks = load_and_chunk(settings, loader_factory=loader_factory)
    embedding = create_embedding(settings, factory=embedding_factory)
    count = persist_chunks(settings, chunks, embedding, store_factory=store_factory)
    return IngestionResult(
        source_name=Path(settings.pdf_path).name,
        collection_name=settings.collection_name,
        chunk_count=count,
    )


__all__ = ["IngestionResult", "ingest"]
