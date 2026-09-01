from pathlib import Path

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


def test_cli_handles_independent_questions_blank_input_and_literal_fallback():
    questions = iter(["primeira", "   ", "segunda", "quit"])
    prompts = []
    outputs = []
    errors = []
    received_questions = []
    configured_settings = settings()

    def input_double(prompt):
        prompts.append(prompt)
        return next(questions)

    def answer_double(question, received_settings):
        received_questions.append((question, received_settings))
        return {"primeira": "resposta um", "segunda": FALLBACK_ANSWER}[question]

    result = chat.main(
        input_function=input_double,
        output=outputs.append,
        error_output=errors.append,
        settings_loader=lambda: configured_settings,
        answer_operation=answer_double,
    )

    assert result == 0
    assert prompts == ["PERGUNTA: "] * 4
    assert received_questions == [
        ("primeira", configured_settings),
        ("segunda", configured_settings),
    ]
    assert outputs == [
        "Fa\u00e7a sua pergunta:",
        "RESPOSTA: resposta um",
        "Informe uma pergunta n\u00e3o vazia.",
        f"RESPOSTA: {FALLBACK_ANSWER}",
        "Chat encerrado.",
    ]
    assert errors == []


@pytest.mark.parametrize("command", ["sair", " EXIT ", "Quit"])
def test_cli_exit_commands_end_without_calling_answer(command):
    outputs = []

    result = chat.main(
        input_function=lambda _: command,
        output=outputs.append,
        error_output=lambda _: pytest.fail("exit must not emit an error"),
        settings_loader=settings,
        answer_operation=lambda *_: pytest.fail("exit must not call answer"),
    )

    assert result == 0
    assert outputs == ["Fa\u00e7a sua pergunta:", "Chat encerrado."]


@pytest.mark.parametrize("terminal_event", [EOFError, KeyboardInterrupt])
def test_cli_eof_and_interrupt_terminate_safely(terminal_event):
    outputs = []

    def input_double(_):
        raise terminal_event()

    result = chat.main(
        input_function=input_double,
        output=outputs.append,
        error_output=lambda _: pytest.fail("termination must not emit an error"),
        settings_loader=settings,
    )

    assert result == 0
    assert outputs == ["Fa\u00e7a sua pergunta:", "", "Chat encerrado."]


def test_cli_unexpected_input_failure_is_safe_and_recoverable():
    inputs = iter([RuntimeError("secret input details"), "exit"])
    errors = []
    outputs = []

    def input_double(_):
        value = next(inputs)
        if isinstance(value, Exception):
            raise value
        return value

    result = chat.main(
        input_function=input_double,
        output=outputs.append,
        error_output=errors.append,
        settings_loader=settings,
        answer_operation=lambda *_: pytest.fail("answer must not run"),
    )

    assert result == 0
    assert errors == ["N\u00e3o foi poss\u00edvel iniciar ou continuar o chat."]
    assert outputs == ["Fa\u00e7a sua pergunta:", "Chat encerrado."]


def test_cli_unexpected_output_failure_is_safe_at_startup():
    errors = []

    def output_failure(_):
        raise RuntimeError("terminal output details")

    result = chat.main(
        input_function=lambda _: pytest.fail("input must not run after output failure"),
        output=output_failure,
        error_output=errors.append,
        settings_loader=settings,
        answer_operation=lambda *_: pytest.fail("answer must not run after output failure"),
    )

    assert result == 1
    assert errors == ["N\u00e3o foi poss\u00edvel iniciar ou continuar o chat."]


def test_cli_unexpected_output_failure_is_safe_and_recoverable_per_question():
    questions = iter(["pergunta", "exit"])
    errors = []
    outputs = []

    def output_double(message):
        outputs.append(message)
        if message.startswith("RESPOSTA:"):
            raise RuntimeError("terminal output details")

    result = chat.main(
        input_function=lambda _: next(questions),
        output=output_double,
        error_output=errors.append,
        settings_loader=settings,
        answer_operation=lambda *_: "resposta segura",
    )

    assert result == 0
    assert errors == ["N\u00e3o foi poss\u00edvel iniciar ou continuar o chat."]
    assert outputs == ["Fa\u00e7a sua pergunta:", "RESPOSTA: resposta segura", "Chat encerrado."]


def test_cli_assembles_model_and_retrieval_collaborators_before_input():
    events = []
    configured_settings = settings()

    class PreparedModel:
        def invoke(self, prompt):
            events.append(("invoke", prompt))
            return ResponseDouble("resposta")

    def settings_loader():
        events.append("settings")
        return configured_settings

    def model_factory(**kwargs):
        events.append(("model", kwargs))
        return PreparedModel()

    def retrieval_double(question, received_settings):
        events.append(("retrieve", question, received_settings))
        return chunks()

    def prompt_double(question, received_chunks):
        events.append(("prompt", question, received_chunks))
        return "prompt"

    questions = iter(["pergunta", "exit"])

    def input_double(_):
        events.append("input")
        return next(questions)

    result = chat.main(
        input_function=input_double,
        output=lambda _: None,
        error_output=lambda _: pytest.fail("unexpected error"),
        settings_loader=settings_loader,
        retrieval_operation=retrieval_double,
        prompt_renderer=prompt_double,
        chat_model_factory=model_factory,
    )

    assert result == 0
    assert events[0] == "settings"
    assert events[1][0] == "model"
    assert events[2] == "input"
    assert [event[0] if isinstance(event, tuple) else event for event in events] == [
        "settings",
        "model",
        "input",
        "retrieve",
        "prompt",
        "invoke",
        "input",
    ]


def test_cli_configuration_failure_stops_before_input_and_is_safe():
    errors = []

    result = chat.main(
        input_function=lambda _: pytest.fail("input must not be read after startup failure"),
        output=lambda _: pytest.fail("startup banner must not be printed after configuration failure"),
        error_output=errors.append,
        settings_loader=lambda: (_ for _ in ()).throw(
            chat.ChatConfigurationError("Invalid or missing setting: OPENAI_API_KEY")
        ),
    )

    assert result == 1
    assert errors == ["Invalid or missing setting: OPENAI_API_KEY"]
    assert "secret" not in errors[0].lower()


def test_cli_expected_answer_failures_are_safe_and_recoverable():
    questions = iter(["retrieval", "model", "valid", "sair"])
    outputs = []
    errors = []

    def answer_double(question, _):
        if question == "retrieval":
            raise RetrievalError("postgresql://user:secret@host/database")
        if question == "model":
            raise ChatModelError("provider response contains prompt text")
        return "resposta segura"

    result = chat.main(
        input_function=lambda _: next(questions),
        output=outputs.append,
        error_output=errors.append,
        settings_loader=settings,
        answer_operation=answer_double,
    )

    expected_message = (
        "N\u00e3o foi poss\u00edvel responder \u00e0 pergunta. Verifique a disponibilidade do banco e da "
        "OpenAI e tente novamente."
    )
    assert result == 0
    assert errors == [expected_message, expected_message]
    assert "secret" not in " ".join(errors).lower()
    assert "prompt text" not in " ".join(errors)
    assert outputs == [
        "Fa\u00e7a sua pergunta:",
        "RESPOSTA: resposta segura",
        "Chat encerrado.",
    ]


def test_cli_unexpected_failures_are_bounded_at_startup_and_question_boundary():
    startup_errors = []
    startup_result = chat.main(
        input_function=lambda _: pytest.fail("input must not be read"),
        output=lambda _: pytest.fail("banner must not be printed"),
        error_output=startup_errors.append,
        settings_loader=lambda: (_ for _ in ()).throw(RuntimeError("secret startup details")),
    )

    questions = iter(["bad", "good", "exit"])
    question_errors = []
    outputs = []

    def answer_double(question, _):
        if question == "bad":
            raise RuntimeError("prompt and provider details")
        return "ok"

    question_result = chat.main(
        input_function=lambda _: next(questions),
        output=outputs.append,
        error_output=question_errors.append,
        settings_loader=settings,
        answer_operation=answer_double,
    )

    expected_message = "N\u00e3o foi poss\u00edvel iniciar ou continuar o chat."
    assert startup_result == 1
    assert startup_errors == [expected_message]
    assert question_result == 0
    assert question_errors == [expected_message]
    assert outputs == ["Fa\u00e7a sua pergunta:", "RESPOSTA: ok", "Chat encerrado."]


def test_readme_documents_the_safe_operator_workflow():
    readme = Path("README.md").read_text(encoding="utf-8")

    for required_text in (
        "Docker Compose",
        "OPENAI_API_KEY",
        "cp .env.example .env",
        "docker compose up -d",
        "python src/ingest.py",
        "python src/chat.py",
        "document.pdf",
        "exatamente dez chunks",
        "sair",
        "exit",
        "quit",
        "público no GitHub",
    ):
        assert required_text in readme
