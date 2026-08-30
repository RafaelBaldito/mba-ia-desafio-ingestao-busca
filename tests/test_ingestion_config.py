from pathlib import Path

import pytest

import chat
import src.ingest as ingest
import search
from src.ingestion_config import (
    APPROVED_EMBEDDING_MODEL,
    IngestionConfigurationError,
    IngestionSettings,
    load_settings,
)


def valid_environment():
    return {
        "OPENAI_API_KEY": "test-key",
        "OPENAI_EMBEDDING_MODEL": APPROVED_EMBEDDING_MODEL,
        "DATABASE_URL": "postgresql://user:password@localhost:5432/app",
        "PG_VECTOR_COLLECTION_NAME": "document_chunks",
        "PDF_PATH": "document.pdf",
    }


def test_loads_valid_settings_and_resolves_relative_pdf(tmp_path):
    settings = load_settings(environment=valid_environment(), repository_root=tmp_path)
    assert isinstance(settings, IngestionSettings)
    assert settings.openai_embedding_model == APPROVED_EMBEDDING_MODEL
    assert settings.collection_name == "document_chunks"
    assert settings.pdf_path == (tmp_path / "document.pdf").resolve()
    assert "test-key" not in repr(settings)
    assert "password" not in repr(settings)


@pytest.mark.parametrize(
    "name",
    ["OPENAI_API_KEY", "OPENAI_EMBEDDING_MODEL", "DATABASE_URL", "PG_VECTOR_COLLECTION_NAME", "PDF_PATH"],
)
def test_missing_or_empty_setting_is_rejected(name):
    values = valid_environment()
    values[name] = " "
    with pytest.raises(IngestionConfigurationError, match=name):
        load_settings(environment=values)


def test_non_approved_model_is_rejected():
    values = valid_environment()
    values["OPENAI_EMBEDDING_MODEL"] = "text-embedding-ada-002"
    with pytest.raises(IngestionConfigurationError, match="OPENAI_EMBEDDING_MODEL"):
        load_settings(environment=values)


@pytest.mark.parametrize("name", ["DATABASE_URL", "PG_VECTOR_COLLECTION_NAME"])
def test_unsafe_values_are_rejected_without_echoing_secret(name):
    values = valid_environment()
    values[name] = "postgresql://user:secret@localhost/db\n" if name == "DATABASE_URL" else "chunks;drop"
    with pytest.raises(IngestionConfigurationError) as error:
        load_settings(environment=values)
    assert "secret" not in str(error.value)
    assert values[name] not in str(error.value)


def test_database_url_must_be_postgresql():
    values = valid_environment()
    values["DATABASE_URL"] = "sqlite:///unsafe.db"
    with pytest.raises(IngestionConfigurationError, match="DATABASE_URL"):
        load_settings(environment=values)


def test_absolute_pdf_path_is_preserved(tmp_path):
    absolute_path = tmp_path / "input.pdf"
    values = valid_environment()
    values["PDF_PATH"] = str(absolute_path)
    assert load_settings(environment=values, repository_root=Path("ignored")).pdf_path == absolute_path


def test_dotenv_is_loaded_at_process_boundary(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=dotenv-key\nOPENAI_EMBEDDING_MODEL=text-embedding-3-small\n"
        "DATABASE_URL=postgresql://localhost/app\nPG_VECTOR_COLLECTION_NAME=dotenv_collection\n"
        "PDF_PATH=document.pdf\n"
    )
    for name in valid_environment():
        monkeypatch.delenv(name, raising=False)
    settings = load_settings(repository_root=tmp_path)
    assert settings.collection_name == "dotenv_collection"
    assert settings.pdf_path == (tmp_path / "document.pdf").resolve()


def test_existing_ingest_entrypoint_scaffold_is_importable():
    assert ingest.ingest_pdf() is None


def test_search_placeholder_preserves_wave_two_boundary():
    assert search.search_prompt() is None
    assert search.search_prompt("question") is None


def test_chat_reports_unavailable_search(monkeypatch, capsys):
    monkeypatch.setattr(chat, "search_prompt", lambda: None)
    chat.main()
    assert "Não foi possível iniciar o chat" in capsys.readouterr().out
