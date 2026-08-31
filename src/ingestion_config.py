"""Validated, credential-safe configuration for the ingestion boundary."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

APPROVED_EMBEDDING_MODEL = "text-embedding-3-small"
_COLLECTION_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


class IngestionConfigurationError(ValueError):
    """Raised when a required ingestion setting is missing or unsafe."""


@dataclass(frozen=True)
class IngestionSettings:
    """The settings passed to the Wave 1 ingestion components."""

    openai_api_key: str
    openai_embedding_model: str
    database_url: str
    collection_name: str
    pdf_path: Path

    def __repr__(self) -> str:
        return (
            "IngestionSettings(openai_api_key='[REDACTED]', "
            f"openai_embedding_model={self.openai_embedding_model!r}, "
            "database_url='[REDACTED]', "
            f"collection_name={self.collection_name!r}, pdf_path={str(self.pdf_path)!r})"
        )


def _value(environment: dict[str, str], name: str) -> str:
    value = environment.get(name)
    if value is None or not value.strip():
        raise IngestionConfigurationError(f"Invalid or missing setting: {name}")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise IngestionConfigurationError(f"Invalid or unsafe setting: {name}")
    return value.strip()


def _database_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"postgresql", "postgres", "postgresql+psycopg"} or not parsed.hostname:
        raise IngestionConfigurationError("Invalid or unsafe setting: DATABASE_URL")
    return value


def load_settings(
    *, environment: dict[str, str] | None = None, repository_root: Path | None = None
) -> IngestionSettings:
    """Load ``.env`` and validate the five approved ingestion settings."""

    if repository_root is None:
        load_dotenv()
    else:
        load_dotenv(Path(repository_root) / ".env")
    values = os.environ if environment is None else environment
    api_key = _value(values, "OPENAI_API_KEY")
    model = _value(values, "OPENAI_EMBEDDING_MODEL")
    if model != APPROVED_EMBEDDING_MODEL:
        raise IngestionConfigurationError(
            "Invalid setting: OPENAI_EMBEDDING_MODEL must be text-embedding-3-small"
        )
    database_url = _database_url(_value(values, "DATABASE_URL"))
    collection_name = _value(values, "PG_VECTOR_COLLECTION_NAME")
    if not _COLLECTION_NAME.fullmatch(collection_name):
        raise IngestionConfigurationError(
            "Invalid or unsafe setting: PG_VECTOR_COLLECTION_NAME"
        )
    pdf_value = _value(values, "PDF_PATH")
    root = Path.cwd() if repository_root is None else Path(repository_root)
    pdf_path = Path(pdf_value)
    if not pdf_path.is_absolute():
        pdf_path = root / pdf_path
    return IngestionSettings(
        openai_api_key=api_key,
        openai_embedding_model=model,
        database_url=database_url,
        collection_name=collection_name,
        pdf_path=pdf_path.resolve(),
    )
