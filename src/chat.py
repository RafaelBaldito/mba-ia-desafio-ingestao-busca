"""Grounded answer orchestration for Wave 2 chat."""

from __future__ import annotations

from typing import Any, Callable

from langchain_openai import ChatOpenAI

try:  # Support both ``import src.chat`` and direct-script imports.
    from .chat_config import APPROVED_CHAT_MODEL, ChatSettings
    from .search import FALLBACK_ANSWER, RetrievedChunk, build_prompt, retrieve, search_prompt
except ImportError:  # pragma: no cover - exercised by the future CLI entry point.
    from chat_config import APPROVED_CHAT_MODEL, ChatSettings
    from search import FALLBACK_ANSWER, RetrievedChunk, build_prompt, retrieve, search_prompt


class ChatModelError(RuntimeError):
    """Raised when the configured chat model cannot return safe answer text."""


def answer(
    question: str,
    settings: ChatSettings,
    *,
    retrieval_operation: Callable[[str, ChatSettings], tuple[RetrievedChunk, ...]] = retrieve,
    prompt_renderer: Callable[[str, tuple[RetrievedChunk, ...]], str] = build_prompt,
    chat_model_factory: Callable[..., Any] = ChatOpenAI,
) -> str:
    """Answer one question using only the retrieved mandatory prompt context."""

    chunks = retrieval_operation(question, settings)
    prompt = prompt_renderer(question, chunks)

    try:
        model = chat_model_factory(
            model=APPROVED_CHAT_MODEL,
            api_key=settings.openai_api_key,
        )
        response = model.invoke(prompt)
        content = response.content
        if not isinstance(content, str):
            raise TypeError("Chat model returned non-text content")
    except Exception:
        model_failed = True
    else:
        model_failed = False

    if model_failed:
        raise ChatModelError("Chat model failed; verify the configured OpenAI service")

    return content.strip() or FALLBACK_ANSWER


__all__ = ["ChatModelError", "answer"]


def main() -> None:
    """Preserve the pre-Wave-2 entry-point scaffold until TASK-004 owns the CLI."""

    if not search_prompt():
        print("N\u00e3o foi poss\u00edvel iniciar o chat. Verifique os erros de inicializa\u00e7\u00e3o.")


if __name__ == "__main__":
    main()
