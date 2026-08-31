import subprocess
import sys
import os

import pytest

from src.ingestion_config import IngestionConfigurationError
from src.ingestion_document import IngestionChunkError, IngestionSourceError
from src.ingestion_store import EmbeddingProviderError, VectorPersistenceError


def test_cli_missing_configuration_is_nonzero_and_safe():
    environment = os.environ.copy()
    for name in ("OPENAI_API_KEY", "OPENAI_EMBEDDING_MODEL", "DATABASE_URL", "PG_VECTOR_COLLECTION_NAME", "PDF_PATH"):
        environment.pop(name, None)
    result = subprocess.run(
        [sys.executable, "src/ingest.py"],
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode != 0
    assert "OPENAI_API_KEY" in result.stderr
    assert "password" not in result.stderr.lower()
    assert "postgresql://" not in result.stderr.lower()


def test_cli_success_prints_only_summary(monkeypatch, capsys):
    from src import ingest as cli
    from src.ingestion_config import APPROVED_EMBEDDING_MODEL, IngestionSettings
    from src.ingestion_orchestrator import IngestionResult

    settings = IngestionSettings("secret", APPROVED_EMBEDDING_MODEL, "postgresql://u:p@h/db", "docs", "document.pdf")
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr(cli, "ingest", lambda value: IngestionResult("document.pdf", "docs", 2))
    assert cli.main() == 0
    output = capsys.readouterr()
    assert output.out == "Ingested document.pdf into docs (2 chunks)\n"
    assert output.err == ""


@pytest.mark.parametrize(
    ("failure", "expected_message"),
    [
        (
            IngestionConfigurationError("Invalid or missing setting: PDF_PATH"),
            "Invalid or missing setting: PDF_PATH",
        ),
        (
            IngestionSourceError("Configured PDF source is not a readable PDF: input.pdf"),
            "Configured PDF source is not a readable PDF: input.pdf",
        ),
        (IngestionChunkError("chunk contents must not be printed"), "Ingestion chunk contract validation failed"),
        (EmbeddingProviderError("provider payload must not be printed"), "Embedding provider failure"),
        (
            VectorPersistenceError("postgresql://user:password@host/database"),
            "PostgreSQL/pgVector persistence failed; a failed replacement may require rerun",
        ),
    ],
    ids=["configuration", "source", "chunk", "provider", "persistence"],
)
def test_cli_expected_failures_are_nonzero_actionable_and_safe(
    monkeypatch, capsys, failure, expected_message
):
    from src import ingest as cli

    ingest_called = False

    def fail_load_settings():
        if isinstance(failure, IngestionConfigurationError):
            raise failure
        return object()

    def fail_ingest(settings):
        nonlocal ingest_called
        ingest_called = True
        raise failure

    monkeypatch.setattr(cli, "load_settings", fail_load_settings)
    monkeypatch.setattr(cli, "ingest", fail_ingest)

    assert cli.main() == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == f"{expected_message}\n"
    assert "password" not in output.err.lower()
    assert "postgresql://" not in output.err.lower()
    assert "payload" not in output.err.lower()
    assert ingest_called is not isinstance(failure, IngestionConfigurationError)


def test_cli_unexpected_failure_is_safe_and_nonzero(monkeypatch, capsys):
    from src import ingest as cli

    monkeypatch.setattr(cli, "load_settings", lambda: object())
    monkeypatch.setattr(cli, "ingest", lambda settings: (_ for _ in ()).throw(RuntimeError("secret payload")))
    assert cli.main() == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "Ingestion failed unexpectedly\n"
