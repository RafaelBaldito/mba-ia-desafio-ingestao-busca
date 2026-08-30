"""Load the configured PDF and produce validated deterministic chunks."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .ingestion_config import APPROVED_EMBEDDING_MODEL, IngestionSettings

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
SOURCE_NAME = "document.pdf"


class IngestionSourceError(RuntimeError):
    """Raised when the configured PDF cannot produce source text."""


class IngestionChunkError(RuntimeError):
    """Raised when generated chunks violate the ingestion contract."""


# Descriptive aliases keep the two failure boundaries convenient to import.
PDFSourceError = IngestionSourceError
ChunkInvariantError = IngestionChunkError


def _validate_source(path: Path) -> None:
    if path.suffix.lower() != ".pdf" or not path.is_file() or not os.access(path, os.R_OK):
        raise IngestionSourceError(f"Configured PDF source is not a readable PDF: {path}")


def _load_source_document(
    path: Path, loader_factory: Callable[[str], Any]
) -> Document:
    try:
        loader = loader_factory(str(path))
        pages: Iterable[Any] = loader.load()
        page_contents = []
        for page in pages:
            content = getattr(page, "page_content", None)
            if not isinstance(content, str):
                raise ValueError("a loaded page has no text content")
            page_contents.append(content)
        text = "\n".join(page_contents)
    except Exception as error:
        if isinstance(error, IngestionSourceError):
            raise
        raise IngestionSourceError(f"Unable to load PDF source: {path}") from error

    if not text.strip():
        raise IngestionSourceError(f"PDF source contains no text: {path}")
    return Document(page_content=text, metadata={"source": SOURCE_NAME})


def _validate_chunks(chunks: list[Document]) -> None:
    if not chunks:
        raise IngestionChunkError("Ingestion chunk contract produced no chunks")
    if any(not isinstance(chunk.page_content, str) for chunk in chunks):
        raise IngestionChunkError("Ingestion chunk contract produced invalid text")
    if any(len(chunk.page_content) != CHUNK_SIZE for chunk in chunks[:-1]):
        raise IngestionChunkError("Every non-final chunk must contain 1,000 characters")
    if not 1 <= len(chunks[-1].page_content) <= CHUNK_SIZE:
        raise IngestionChunkError("The final chunk must contain 1 to 1,000 characters")
    for previous, current in zip(chunks, chunks[1:]):
        if previous.page_content[-CHUNK_OVERLAP:] != current.page_content[:CHUNK_OVERLAP]:
            raise IngestionChunkError("Adjacent chunks must overlap by exactly 150 characters")


def load_and_chunk(
    settings: IngestionSettings,
    *,
    loader_factory: Callable[[str], Any] = PyPDFLoader,
) -> list[Document]:
    """Load the configured PDF and return contract-compliant LangChain documents."""

    path = Path(settings.pdf_path)
    _validate_source(path)
    source = _load_source_document(path, loader_factory)
    splitter = RecursiveCharacterTextSplitter(
        separators=[""],
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        strip_whitespace=False,
    )
    chunks = splitter.split_documents([source])
    _validate_chunks(chunks)

    for index, chunk in enumerate(chunks):
        chunk.metadata = {
            "source": SOURCE_NAME,
            "chunk_index": index,
            "embedding_model": APPROVED_EMBEDDING_MODEL,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
        }
    return chunks


load_and_chunk_document = load_and_chunk

__all__ = [
    "CHUNK_OVERLAP",
    "CHUNK_SIZE",
    "ChunkInvariantError",
    "IngestionChunkError",
    "IngestionSourceError",
    "PDFSourceError",
    "SOURCE_NAME",
    "load_and_chunk",
    "load_and_chunk_document",
]
