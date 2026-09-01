"""Grounded answer orchestration for Wave 2 chat."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_openai import ChatOpenAI

from src.chat_config import APPROVED_CHAT_MODEL, ChatConfigurationError, ChatSettings, load_settings
from src.search import FALLBACK_ANSWER, RetrievalError, RetrievedChunk, build_prompt, retrieve


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


class _PreparedAnswerOperation:
    """Answer operation with its replaceable collaborators assembled once."""

    def __init__(
        self,
        retrieval_operation: Callable[[str, ChatSettings], tuple[RetrievedChunk, ...]],
        prompt_renderer: Callable[[str, tuple[RetrievedChunk, ...]], str],
        chat_model: Any,
    ) -> None:
        self._retrieval_operation = retrieval_operation
        self._prompt_renderer = prompt_renderer
        self._chat_model = chat_model

    def __call__(self, question: str, settings: ChatSettings) -> str:
        chunks = self._retrieval_operation(question, settings)
        prompt = self._prompt_renderer(question, chunks)

        try:
            response = self._chat_model.invoke(prompt)
            content = response.content
            if not isinstance(content, str):
                raise TypeError("Chat model returned non-text content")
        except Exception:
            raise ChatModelError(
                "Chat model failed; verify the configured OpenAI service"
            ) from None

        return content.strip() or FALLBACK_ANSWER


def prepare_answer_operation(
    settings: ChatSettings,
    *,
    retrieval_operation: Callable[[str, ChatSettings], tuple[RetrievedChunk, ...]] = retrieve,
    prompt_renderer: Callable[[str, tuple[RetrievedChunk, ...]], str] = build_prompt,
    chat_model_factory: Callable[..., Any] = ChatOpenAI,
) -> Callable[[str, ChatSettings], str]:
    """Assemble the replaceable retrieval and model collaborators for the CLI."""

    chat_model = chat_model_factory(
        model=APPROVED_CHAT_MODEL,
        api_key=settings.openai_api_key,
    )
    return _PreparedAnswerOperation(retrieval_operation, prompt_renderer, chat_model)


_EXPECTED_FAILURE_MESSAGE = (
    "Não foi possível responder à pergunta. Verifique a disponibilidade do banco e da "
    "OpenAI e tente novamente."
)
_UNEXPECTED_FAILURE_MESSAGE = "Não foi possível iniciar ou continuar o chat."


def _safe_error_output(
    error_output: Callable[[str], None],
    message: str,
) -> None:
    """Avoid escaping the CLI boundary when the error stream also fails."""

    try:
        error_output(message)
    except Exception:
        pass


def _safe_output(
    output: Callable[[str], None],
    error_output: Callable[[str], None],
    message: str,
) -> bool:
    """Keep terminal-write failures inside the CLI boundary."""

    try:
        output(message)
    except Exception:
        _safe_error_output(error_output, _UNEXPECTED_FAILURE_MESSAGE)
        return False
    return True


def main(
    *,
    input_function: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
    error_output: Callable[[str], None] | None = None,
    settings_loader: Callable[[], ChatSettings] = load_settings,
    answer_operation: Callable[[str, ChatSettings], str] | None = None,
    retrieval_operation: Callable[[str, ChatSettings], tuple[RetrievedChunk, ...]] = retrieve,
    prompt_renderer: Callable[[str, tuple[RetrievedChunk, ...]], str] = build_prompt,
    chat_model_factory: Callable[..., Any] = ChatOpenAI,
) -> int:
    """Run independent grounded questions through a safe, injectable terminal loop."""

    if error_output is None:
        error_output = lambda message: print(message, file=sys.stderr)

    try:
        settings = settings_loader()
        if answer_operation is None:
            answer_operation = prepare_answer_operation(
                settings,
                retrieval_operation=retrieval_operation,
                prompt_renderer=prompt_renderer,
                chat_model_factory=chat_model_factory,
            )
    except ChatConfigurationError as error:
        _safe_error_output(error_output, str(error))
        return 1
    except Exception:
        _safe_error_output(error_output, _UNEXPECTED_FAILURE_MESSAGE)
        return 1

    if not _safe_output(output, error_output, "Faça sua pergunta:"):
        return 1

    while True:
        try:
            question = input_function("PERGUNTA: ")
        except (EOFError, KeyboardInterrupt):
            if not _safe_output(output, error_output, ""):
                return 1
            if not _safe_output(output, error_output, "Chat encerrado."):
                return 1
            return 0
        except Exception:
            _safe_error_output(error_output, _UNEXPECTED_FAILURE_MESSAGE)
            continue

        try:
            normalized_question = question.strip().lower()
        except Exception:
            _safe_error_output(error_output, _UNEXPECTED_FAILURE_MESSAGE)
            continue

        if normalized_question in {"sair", "exit", "quit"}:
            if not _safe_output(output, error_output, "Chat encerrado."):
                return 1
            return 0
        if not normalized_question:
            _safe_output(output, error_output, "Informe uma pergunta não vazia.")
            continue

        try:
            response = answer_operation(question, settings)
        except (RetrievalError, ChatModelError):
            _safe_error_output(error_output, _EXPECTED_FAILURE_MESSAGE)
            continue
        except Exception:
            _safe_error_output(error_output, _UNEXPECTED_FAILURE_MESSAGE)
            continue

        _safe_output(output, error_output, f"RESPOSTA: {response}")


if __name__ == "__main__":
    raise SystemExit(main())
