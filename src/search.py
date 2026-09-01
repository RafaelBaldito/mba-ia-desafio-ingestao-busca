"""Retrieval and mandatory grounded-prompt boundaries for Wave 2."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Any, Callable

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy, _get_embedding_collection_store

try:  # Support both ``import src.search`` and the existing script-style import.
    from .chat_config import APPROVED_EMBEDDING_MODEL, ChatSettings
except ImportError:  # pragma: no cover - exercised by legacy top-level imports.
    from chat_config import APPROVED_EMBEDDING_MODEL, ChatSettings

EMBEDDING_LENGTH = 1536
RETRIEVAL_COUNT = 10
FALLBACK_ANSWER = "Não tenho informações necessárias para responder sua pergunta."

PROMPT_TEMPLATE = """CONTEXTO:
{contexto}

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
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO\""""


PROMPT_TEMPLATE += "\n"


class RetrievalError(RuntimeError):
    """Raised when a safe, complete ten-chunk context cannot be produced."""


@dataclass(frozen=True)
class RetrievedChunk:
    """A validated document text and its adapter-provided numeric score."""

    text: str
    score: Real

    @property
    def page_content(self) -> str:
        return self.text


class _ReadOnlyPGVector(PGVector):
    """PGVector retrieval adapter that never initializes persisted resources."""

    def __post_init__(self) -> None:
        """Load the mapped tables without extension, schema, or collection creation."""

        self.EmbeddingStore, self.CollectionStore = _get_embedding_collection_store(
            self._embedding_length
        )


def _valid_question(question: Any) -> bool:
    return isinstance(question, str) and bool(question.strip())


def _validate_settings(settings: ChatSettings) -> None:
    if not isinstance(settings, ChatSettings):
        raise RetrievalError("Retrieval configuration is invalid")
    if (
        not settings.openai_api_key
        or settings.openai_embedding_model != APPROVED_EMBEDDING_MODEL
        or not settings.database_url
        or not settings.collection_name
    ):
        raise RetrievalError("Retrieval configuration is invalid")


def _validated_results(results: Any) -> tuple[RetrievedChunk, ...]:
    if not isinstance(results, (list, tuple)) or len(results) != RETRIEVAL_COUNT:
        raise RetrievalError("Retrieval did not return exactly ten chunks")
    chunks: list[RetrievedChunk] = []
    for pair in results:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise RetrievalError("Retrieval returned an invalid result")
        document, score = pair
        if (
            not isinstance(document, Document)
            or not isinstance(document.page_content, str)
            or not document.page_content.strip()
            or not isinstance(score, Real)
            or isinstance(score, bool)
        ):
            raise RetrievalError("Retrieval returned an invalid result")
        chunks.append(RetrievedChunk(document.page_content, score))
    return tuple(chunks)


def retrieve(
    question: str,
    settings: ChatSettings,
    *,
    embedding_factory: Callable[..., Any] = OpenAIEmbeddings,
    store_factory: Callable[..., Any] = _ReadOnlyPGVector,
) -> tuple[RetrievedChunk, ...]:
    """Retrieve exactly ten ordered chunks without exposing provider details."""

    if not _valid_question(question):
        raise RetrievalError("Question must not be empty")
    normalized_question = question.strip()
    try:
        _validate_settings(settings)
        embedding = embedding_factory(
            model=APPROVED_EMBEDDING_MODEL,
            api_key=settings.openai_api_key,
        )
        store = store_factory(
            embeddings=embedding,
            connection=settings.database_url,
            collection_name=settings.collection_name,
            distance_strategy=DistanceStrategy.COSINE,
            embedding_length=EMBEDDING_LENGTH,
            create_extension=False,
            pre_delete_collection=False,
        )
        results = store.similarity_search_with_score(normalized_question, k=RETRIEVAL_COUNT)
        return _validated_results(results)
    except RetrievalError:
        raise
    except Exception:
        pass
    raise RetrievalError("Retrieval failed; verify the configured services")


def build_prompt(question: str, chunks: tuple[RetrievedChunk, ...]) -> str:
    """Render the sole approved model input from a complete validated context."""

    if not _valid_question(question):
        raise RetrievalError("Question must not be empty")
    if not isinstance(chunks, tuple) or len(chunks) != RETRIEVAL_COUNT:
        raise RetrievalError("Prompt requires exactly ten chunks")
    if any(
        not isinstance(chunk, RetrievedChunk)
        or not isinstance(chunk.page_content, str)
        or not chunk.page_content.strip()
        or not isinstance(chunk.score, Real)
        or isinstance(chunk.score, bool)
        for chunk in chunks
    ):
        raise RetrievalError("Prompt contains an invalid chunk")
    context = "\n\n".join(chunk.page_content for chunk in chunks)
    return PROMPT_TEMPLATE.format(contexto=context, pergunta=question)


def search_prompt(
    question: str | None = None, chunks: tuple[RetrievedChunk, ...] | None = None
) -> str | None:
    """Compatibility entry point for the mandatory prompt renderer."""

    if question is None or chunks is None:
        return None
    return build_prompt(question, chunks)


__all__ = [
    "EMBEDDING_LENGTH",
    "FALLBACK_ANSWER",
    "PROMPT_TEMPLATE",
    "RETRIEVAL_COUNT",
    "RetrievedChunk",
    "RetrievalError",
    "build_prompt",
    "retrieve",
    "search_prompt",
]
