import pytest
from langchain_core.documents import Document

from src.ingestion_config import APPROVED_EMBEDDING_MODEL, IngestionSettings
from src.ingestion_store import (
    COLLECTION_METADATA,
    EMBEDDING_LENGTH,
    EmbeddingProviderError,
    VectorPersistenceError,
    ingest_chunks,
    persist_chunks,
    stable_chunk_id,
)


def settings():
    return IngestionSettings(
        openai_api_key="secret-key",
        openai_embedding_model=APPROVED_EMBEDDING_MODEL,
        database_url="postgresql://user:password@localhost/app",
        collection_name="document_chunks",
        pdf_path="document.pdf",
    )


def chunks():
    return [
        Document(page_content="first text", metadata={"source": "document.pdf", "chunk_index": 0, "safe": "kept"}),
        Document(page_content="second text", metadata={"source": "document.pdf", "chunk_index": 1}),
    ]


def test_ingestion_handoff_uses_approved_provider_and_replacement_configuration():
    provider_calls = []
    store_calls = []

    def embedding_factory(**kwargs):
        provider_calls.append(kwargs)
        return "fake-embedding"

    def store_factory(documents, embedding, **kwargs):
        store_calls.append((documents, embedding, kwargs))
        return object()

    count = ingest_chunks(settings(), chunks(), embedding_factory=embedding_factory, store_factory=store_factory)

    assert count == 2
    assert provider_calls == [{"model": APPROVED_EMBEDDING_MODEL, "api_key": "secret-key"}]
    documents, embedding, kwargs = store_calls[0]
    assert embedding == "fake-embedding"
    assert [document.page_content for document in documents] == ["first text", "second text"]
    assert [document.metadata for document in documents] == [chunks()[0].metadata, chunks()[1].metadata]
    assert kwargs["connection"] == settings().database_url
    assert kwargs["collection_name"] == settings().collection_name
    assert kwargs["distance_strategy"].value == "cosine"
    assert kwargs["embedding_length"] == EMBEDDING_LENGTH
    assert kwargs["collection_metadata"] == COLLECTION_METADATA
    assert kwargs["ids"] == ["document.pdf:0", "document.pdf:1"]
    assert kwargs["pre_delete_collection"] is True


def test_identical_chunks_have_stable_ids_and_reingestion_replaces():
    calls = []

    def store_factory(documents, embedding, **kwargs):
        calls.append(kwargs)

    first = persist_chunks(settings(), chunks(), "embedding", store_factory=store_factory)
    second = persist_chunks(settings(), chunks(), "embedding", store_factory=store_factory)

    assert (first, second) == (2, 2)
    assert calls[0]["ids"] == calls[1]["ids"]
    assert all(call["pre_delete_collection"] for call in calls)


def test_provider_failure_is_typed_and_does_not_expose_key():
    def failing_factory(**kwargs):
        raise RuntimeError("request payload secret-key")

    with pytest.raises(EmbeddingProviderError) as error:
        ingest_chunks(settings(), chunks(), embedding_factory=failing_factory, store_factory=lambda *a, **k: None)
    assert "secret-key" not in str(error.value)
    assert "payload" not in str(error.value)
    assert error.value.__cause__ is None
    assert error.value.__context__ is None


def test_invalid_model_is_rejected_before_provider_call():
    invalid = settings()
    object.__setattr__(invalid, "openai_embedding_model", "other-model")
    called = False

    def factory(**kwargs):
        nonlocal called
        called = True

    with pytest.raises(EmbeddingProviderError):
        ingest_chunks(invalid, chunks(), embedding_factory=factory, store_factory=lambda *a, **k: None)
    assert called is False


def test_persistence_failure_is_typed_and_secret_safe():
    def failing_store(*args, **kwargs):
        raise RuntimeError("postgresql://user:password@host/db")

    with pytest.raises(VectorPersistenceError) as error:
        persist_chunks(settings(), chunks(), "embedding", store_factory=failing_store)
    assert "password" not in str(error.value)
    assert "postgresql://" not in str(error.value)
    assert error.value.__cause__ is None
    assert error.value.__context__ is None


def test_invalid_chunk_identity_stops_before_store_factory():
    called = False

    def store_factory(*args, **kwargs):
        nonlocal called
        called = True

    invalid_chunk = Document(page_content="text", metadata={"source": "document.pdf"})
    with pytest.raises(VectorPersistenceError, match="valid source and index"):
        persist_chunks(settings(), [invalid_chunk], "embedding", store_factory=store_factory)
    assert called is False


@pytest.mark.parametrize(
    "metadata",
    [{"source": "document.pdf"}, {"source": "", "chunk_index": 0}, {"source": "document.pdf", "chunk_index": -1}],
)
def test_invalid_chunk_identity_is_typed(metadata):
    with pytest.raises(VectorPersistenceError):
        stable_chunk_id(Document(page_content="text", metadata=metadata))


def test_stable_id_requires_zero_based_integer_index():
    assert stable_chunk_id(Document(page_content="text", metadata={"source": "document.pdf", "chunk_index": 0})) == "document.pdf:0"
    with pytest.raises(VectorPersistenceError):
        stable_chunk_id(Document(page_content="text", metadata={"source": "document.pdf", "chunk_index": True}))
