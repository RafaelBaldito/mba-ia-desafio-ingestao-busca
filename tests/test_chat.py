import pytest

import src.chat as chat
from src.chat import ChatModelError, answer
from src.chat_config import APPROVED_CHAT_MODEL, APPROVED_EMBEDDING_MODEL, ChatSettings
from src.search import FALLBACK_ANSWER, RetrievalError, RetrievedChunk


def settings():
    return ChatSettings(
        openai_api_key="secret-key",
        openai_embedding_model=APPROVED_EMBEDDING_MODEL,
        openai_chat_model=APPROVED_CHAT_MODEL,
        database_url="postgresql://user:password@localhost/db",
        collection_name="chunks",
    )


def chunks():
    return tuple(RetrievedChunk(f"chunk-{index}", index) for index in range(10))


class ModelDouble:
    def __init__(self, response):
        self.response = response
        self.inputs = []

    def invoke(self, prompt):
        self.inputs.append(prompt)
        return self.response


class FailingModelDouble:
    def invoke(self, prompt):
        raise RuntimeError("prompt text")


class ResponseDouble:
    def __init__(self, content):
        self.content = content


def test_answer_retrieves_then_renders_then_invokes_only_rendered_prompt():
    calls = []
    model = ModelDouble(ResponseDouble(" resposta grounded "))
    captured = {}

    def retrieve_double(question, received_settings):
        calls.append(("retrieve", question, received_settings))
        return chunks()

    def prompt_double(question, received_chunks):
        calls.append(("prompt", question, received_chunks))
        return "mandatory rendered prompt"

    def model_factory(**kwargs):
        calls.append(("factory", kwargs))
        captured["kwargs"] = kwargs
        return model

    result = answer(
        "pergunta",
        settings(),
        retrieval_operation=retrieve_double,
        prompt_renderer=prompt_double,
        chat_model_factory=model_factory,
    )

    assert result == "resposta grounded"
    assert [call[0] for call in calls] == ["retrieve", "prompt", "factory"]
    assert captured["kwargs"] == {"model": APPROVED_CHAT_MODEL, "api_key": "secret-key"}
    assert model.inputs == ["mandatory rendered prompt"]


def test_blank_text_completion_returns_exact_fallback_as_successful_answer():
    model = ModelDouble(ResponseDouble(" \t\n "))

    result = answer(
        "pergunta",
        settings(),
        retrieval_operation=lambda *_: chunks(),
        prompt_renderer=lambda *_: "rendered prompt",
        chat_model_factory=lambda **_: model,
    )

    assert result == FALLBACK_ANSWER


@pytest.mark.parametrize(
    "factory",
    [
        lambda **_: (_ for _ in ()).throw(RuntimeError("secret-key")),
        lambda **_: FailingModelDouble(),
        lambda **_: ModelDouble(object()),
        lambda **_: ModelDouble(ResponseDouble([{"text": "not accepted"}])),
    ],
)
def test_model_failures_are_safe_typed_errors(factory):
    with pytest.raises(ChatModelError) as error:
        answer(
            "pergunta",
            settings(),
            retrieval_operation=lambda *_: chunks(),
            prompt_renderer=lambda *_: "rendered prompt",
            chat_model_factory=factory,
        )

    assert str(error.value) == "Chat model failed; verify the configured OpenAI service"
    assert "secret-key" not in str(error.value)
    assert "prompt text" not in str(error.value)
    assert error.value.__cause__ is None
    assert error.value.__context__ is None


def test_retrieval_error_prevents_prompt_model_factory_and_invocation():
    calls = []

    def retrieval_failure(*_):
        calls.append("retrieve")
        raise RetrievalError("safe retrieval failure")

    with pytest.raises(RetrievalError):
        answer(
            "pergunta",
            settings(),
            retrieval_operation=retrieval_failure,
            prompt_renderer=lambda *_: calls.append("prompt"),
            chat_model_factory=lambda **_: calls.append("factory"),
        )

    assert calls == ["retrieve"]


def test_legacy_entrypoint_reports_unavailable_search(monkeypatch, capsys):
    monkeypatch.setattr(chat, "search_prompt", lambda: None)

    chat.main()

    assert "N\u00e3o foi poss\u00edvel iniciar o chat" in capsys.readouterr().out
