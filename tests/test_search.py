from dataclasses import replace

import pytest
from langchain_core.documents import Document
from sqlalchemy import create_engine

from src.chat_config import APPROVED_EMBEDDING_MODEL, APPROVED_CHAT_MODEL, ChatSettings
from src.search import (
    FALLBACK_ANSWER,
    RETRIEVAL_COUNT,
    RetrievedChunk,
    RetrievalError,
    _ReadOnlyPGVector,
    build_prompt,
    retrieve,
)


def settings():
    return ChatSettings(
        openai_api_key="secret-key",
        openai_embedding_model=APPROVED_EMBEDDING_MODEL,
        openai_chat_model=APPROVED_CHAT_MODEL,
        database_url="postgresql://user:password@localhost/db",
        collection_name="chunks",
    )


def documents(count=10):
    return [(Document(page_content=f"chunk-{i}"), i / 10) for i in range(count)]


class EmbeddingDouble:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class StoreDouble:
    def __init__(self, results, **kwargs):
        self.results = results
        self.kwargs = kwargs
        self.calls = []

    def similarity_search_with_score(self, question, *, k):
        self.calls.append((question, k))
        return self.results


def test_retrieve_uses_approved_adapters_and_preserves_order():
    captured = {}
    results = list(reversed(documents()))

    def embedding_factory(**kwargs):
        captured["embedding"] = kwargs
        return "embedding"

    def store_factory(**kwargs):
        captured["store"] = kwargs
        store = StoreDouble(results, **kwargs)
        captured["instance"] = store
        return store

    found = retrieve("  minha pergunta  ", settings(), embedding_factory=embedding_factory, store_factory=store_factory)

    assert isinstance(found, tuple)
    assert len(found) == RETRIEVAL_COUNT
    assert [chunk.page_content for chunk in found] == [d.page_content for d, _ in results]
    assert captured["embedding"] == {"model": APPROVED_EMBEDDING_MODEL, "api_key": "secret-key"}
    assert captured["store"]["connection"] == settings().database_url
    assert captured["store"]["collection_name"] == "chunks"
    assert captured["store"]["embedding_length"] == 1536
    assert captured["store"]["distance_strategy"].value == "cosine"
    assert captured["store"]["create_extension"] is False
    assert captured["store"]["pre_delete_collection"] is False
    assert captured["instance"].calls == [("minha pergunta", 10)]


def test_blank_question_fails_before_factories():
    called = []

    with pytest.raises(RetrievalError):
        retrieve(" \t", settings(), embedding_factory=lambda **_: called.append(1), store_factory=lambda **_: called.append(2))

    assert called == []


@pytest.mark.parametrize("count", [0, 9, 11])
def test_result_count_must_be_exactly_ten(count):
    with pytest.raises(RetrievalError):
        retrieve("question", settings(), store_factory=lambda **_: StoreDouble(documents(count)))


@pytest.mark.parametrize(
    "pair",
    [
        ("not a document", 1),
        (Document(page_content=""), 1),
        (Document(page_content="ok"), "score"),
        (Document(page_content="ok"), True),
        (Document(page_content="ok"),),
    ],
)
def test_malformed_result_is_a_safe_typed_failure(pair):
    malformed = documents()[:-1] + [pair]
    with pytest.raises(RetrievalError) as error:
        retrieve("question", settings(), store_factory=lambda **_: StoreDouble(malformed))
    assert "secret-key" not in str(error.value)
    assert "ok" not in str(error.value)


def test_adapter_failure_is_safe():
    def failing_store(**_):
        raise RuntimeError("secret-key and retrieved text")

    with pytest.raises(RetrievalError) as error:
        retrieve("question", settings(), store_factory=failing_store)
    assert str(error.value) == "Retrieval failed; verify the configured services"
    assert "secret-key" not in str(error.value)
    assert error.value.__cause__ is None
    assert error.value.__context__ is None


def test_read_only_pgvector_initialization_does_not_create_resources(monkeypatch):
    embedding_store = object()
    collection_store = object()
    monkeypatch.setattr(
        "src.search._get_embedding_collection_store",
        lambda embedding_length: (embedding_store, collection_store),
    )

    store = _ReadOnlyPGVector(
        EmbeddingDouble(),
        connection=create_engine("sqlite://"),
        embedding_length=1536,
        create_extension=False,
    )

    assert store.EmbeddingStore is embedding_store
    assert store.CollectionStore is collection_store


def test_missing_collection_is_a_safe_failure():
    class MissingCollectionStore:
        def similarity_search_with_score(self, question, *, k):
            raise ValueError("Collection not found: chunks")

    with pytest.raises(RetrievalError) as error:
        retrieve(
            "question",
            settings(),
            store_factory=lambda **_: MissingCollectionStore(),
        )

    assert str(error.value) == "Retrieval failed; verify the configured services"
    assert "chunks" not in str(error.value)


def test_prompt_is_exactly_ordered_and_contains_mandatory_content():
    chunks = tuple(RetrievedChunk(f"text-{i}", i) for i in range(10))
    prompt = build_prompt("pergunta original", chunks)

    assert "CONTEXTO:\n" + "\n\n".join(f"text-{i}" for i in range(10)) in prompt
    assert "PERGUNTA DO USUÁRIO:\npergunta original" in prompt
    assert prompt.count(FALLBACK_ANSWER) == 4
    assert "EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:" in prompt
    assert "Nunca invente ou use conhecimento externo." in prompt


@pytest.mark.parametrize("chunks", [(), tuple(RetrievedChunk("x", 1) for _ in range(9))])
def test_prompt_rejects_incomplete_context(chunks):
    with pytest.raises(RetrievalError):
        build_prompt("question", chunks)


def test_prompt_rejects_invalid_question_and_chunk():
    chunks = tuple(RetrievedChunk(f"x-{i}", 1) for i in range(10))
    with pytest.raises(RetrievalError):
        build_prompt(" ", chunks)
    with pytest.raises(RetrievalError):
        build_prompt("question", chunks[:-1] + (RetrievedChunk(" ", 1),))


def test_settings_failure_does_not_construct_dependencies():
    called = []
    invalid = replace(settings(), openai_embedding_model="other")
    with pytest.raises(RetrievalError):
        retrieve("question", invalid, embedding_factory=lambda **_: called.append(1))
    assert called == []


def test_prompt_is_exact_rendering_of_the_normative_template():
    chunks = tuple(RetrievedChunk(f"text-{i}", i) for i in range(10))
    expected = """CONTEXTO:
text-0

text-1

text-2

text-3

text-4

text-5

text-6

text-7

text-8

text-9

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
pergunta original

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

    assert build_prompt("pergunta original", chunks) == expected
