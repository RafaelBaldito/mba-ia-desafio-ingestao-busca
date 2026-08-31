from pathlib import Path

import pytest
from langchain_core.documents import Document

from src.ingestion_config import APPROVED_EMBEDDING_MODEL, IngestionSettings
from src.ingestion_document import IngestionChunkError, IngestionSourceError
from src.ingestion_orchestrator import IngestionResult, ingest
from src.ingestion_store import EmbeddingProviderError, VectorPersistenceError


def make_settings(path: Path) -> IngestionSettings:
    return IngestionSettings("key", APPROVED_EMBEDDING_MODEL, "postgresql://u:p@h/db", "docs", path)


class Loader:
    def __init__(self, path, events):
        events.append(("load", path))

    def load(self):
        return [Document(page_content="x" * 1000)]


def test_ingest_sequences_collaborators_and_returns_safe_result(tmp_path):
    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"pdf")
    events = []

    def loader(path):
        return Loader(path, events)

    def embedder(**kwargs):
        events.append(("embed", kwargs))
        return "embedding"

    def store(documents, embedding, **kwargs):
        events.append(("store", embedding, kwargs["collection_name"]))

    result = ingest(make_settings(pdf), loader_factory=loader, embedding_factory=embedder, store_factory=store)
    assert result == IngestionResult("document.pdf", "docs", 1)
    assert [event[0] for event in events] == ["load", "embed", "store"]


@pytest.mark.parametrize(
    ("failure", "expected_calls", "expected_error"),
    [
        ("source", ["load"], IngestionSourceError),
        ("provider", ["load", "embed"], EmbeddingProviderError),
        ("store", ["load", "embed", "store"], VectorPersistenceError),
    ],
)
def test_ingest_stops_after_each_expected_failure(
    tmp_path, failure, expected_calls, expected_error
):
    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"pdf")
    calls = []

    def loader(path):
        calls.append("load")
        if failure == "source":
            raise IngestionSourceError("bad source")

        class SuccessfulLoader:
            def load(self):
                return [Document(page_content="x" * 1000)]

        return SuccessfulLoader()

    def embedder(**kwargs):
        calls.append("embed")
        if failure == "provider":
            raise RuntimeError("provider payload")
        return "embedding"

    def store(*args, **kwargs):
        calls.append("store")
        if failure == "store":
            raise RuntimeError("database secret")

    with pytest.raises(expected_error):
        ingest(make_settings(pdf), loader_factory=loader, embedding_factory=embedder, store_factory=store)
    assert calls == expected_calls


def test_ingest_chunk_failure_stops_before_provider_and_store(monkeypatch, tmp_path):
    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"pdf")
    calls = []

    def fail_chunking(*args, **kwargs):
        calls.append("load")
        raise IngestionChunkError("invalid chunk text must remain internal")

    def embedder(**kwargs):
        calls.append("embed")

    def store(*args, **kwargs):
        calls.append("store")

    monkeypatch.setattr("src.ingestion_orchestrator.load_and_chunk", fail_chunking)
    with pytest.raises(IngestionChunkError):
        ingest(make_settings(pdf), embedding_factory=embedder, store_factory=store)
    assert calls == ["load"]
