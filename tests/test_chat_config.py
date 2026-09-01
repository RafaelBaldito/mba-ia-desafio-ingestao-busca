from pathlib import Path

import pytest

from src.chat_config import (
    APPROVED_CHAT_MODEL,
    APPROVED_EMBEDDING_MODEL,
    ChatConfigurationError,
    ChatSettings,
    load_settings,
)


def valid_environment():
    return {
        "OPENAI_API_KEY": "test-key",
        "OPENAI_EMBEDDING_MODEL": APPROVED_EMBEDDING_MODEL,
        "OPENAI_CHAT_MODEL": APPROVED_CHAT_MODEL,
        "DATABASE_URL": "postgresql+psycopg://user:password@localhost:5432/app",
        "PG_VECTOR_COLLECTION_NAME": "document_chunks",
    }


def test_loads_valid_immutable_settings_without_pdf_requirement():
    settings = load_settings(environment=valid_environment(), repository_root=Path("unused"))

    assert isinstance(settings, ChatSettings)
    assert settings.openai_embedding_model == APPROVED_EMBEDDING_MODEL
    assert settings.openai_chat_model == APPROVED_CHAT_MODEL
    assert settings.database_url == valid_environment()["DATABASE_URL"]
    assert settings.collection_name == "document_chunks"
    assert "test-key" not in repr(settings)
    assert "password" not in repr(settings)
    with pytest.raises(AttributeError):
        settings.openai_chat_model = "other-model"


@pytest.mark.parametrize(
    "name",
    [
        "OPENAI_API_KEY",
        "OPENAI_EMBEDDING_MODEL",
        "OPENAI_CHAT_MODEL",
        "DATABASE_URL",
        "PG_VECTOR_COLLECTION_NAME",
    ],
)
def test_missing_or_blank_setting_is_rejected(name):
    values = valid_environment()
    values[name] = " "

    with pytest.raises(ChatConfigurationError, match=name):
        load_settings(environment=values)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"),
        ("OPENAI_CHAT_MODEL", "gpt-4o"),
    ],
)
def test_only_approved_models_are_accepted(name, value):
    values = valid_environment()
    values[name] = value

    with pytest.raises(ChatConfigurationError, match=name):
        load_settings(environment=values)


@pytest.mark.parametrize(
    "name",
    [
        "OPENAI_API_KEY",
        "OPENAI_EMBEDDING_MODEL",
        "OPENAI_CHAT_MODEL",
        "DATABASE_URL",
        "PG_VECTOR_COLLECTION_NAME",
    ],
)
def test_control_characters_are_rejected_without_echoing_values(name):
    values = valid_environment()
    secret_value = "secret-value\n"
    values[name] = secret_value

    with pytest.raises(ChatConfigurationError) as error:
        load_settings(environment=values)

    assert name in str(error.value)
    assert secret_value not in str(error.value)


@pytest.mark.parametrize(
    "url",
    [
        "sqlite:///unsafe.db",
        "postgresql://",
        "postgresql://[invalid",
        "postgresql+psycopg://localhost:not-a-port/app",
        "postgresql://localhost:0/app",
        "postgresql+psycopg://localhost:65536/app",
        "not-a-url",
    ],
)
def test_database_url_must_be_a_postgresql_url(url):
    values = valid_environment()
    values["DATABASE_URL"] = url

    with pytest.raises(ChatConfigurationError, match="DATABASE_URL") as error:
        load_settings(environment=values)

    assert url not in str(error.value)


@pytest.mark.parametrize("collection", ["chunks;drop", "-chunks", "chunks with spaces"])
def test_collection_name_must_be_a_safe_logical_identifier(collection):
    values = valid_environment()
    values["PG_VECTOR_COLLECTION_NAME"] = collection

    with pytest.raises(ChatConfigurationError, match="PG_VECTOR_COLLECTION_NAME"):
        load_settings(environment=values)


def test_dotenv_is_loaded_at_process_boundary(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=dotenv-key\n"
        "OPENAI_EMBEDDING_MODEL=text-embedding-3-small\n"
        "OPENAI_CHAT_MODEL=gpt-5.4-mini\n"
        "DATABASE_URL=postgresql://localhost/app\n"
        "PG_VECTOR_COLLECTION_NAME=dotenv_collection\n"
    )
    for name in valid_environment():
        monkeypatch.delenv(name, raising=False)

    settings = load_settings(repository_root=tmp_path)

    assert settings.collection_name == "dotenv_collection"
    assert settings.openai_chat_model == APPROVED_CHAT_MODEL
