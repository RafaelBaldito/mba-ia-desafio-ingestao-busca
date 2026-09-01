"""Validated, credential-safe configuration for the Wave 2 chat boundary."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

APPROVED_EMBEDDING_MODEL = "text-embedding-3-small"
APPROVED_CHAT_MODEL = "gpt-5.4-mini"
_COLLECTION_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


class ChatConfigurationError(ValueError):
    """Raised when a required chat setting is missing or unsafe."""


@dataclass(frozen=True)
class ChatSettings:
    """The validated settings passed to Wave 2 retrieval and chat components."""

    openai_api_key: str
    openai_embedding_model: str
    openai_chat_model: str
    database_url: str
    collection_name: str

    def __repr__(self) -> str:
        return (
            "ChatSettings(openai_api_key='[REDACTED]', "
            f"openai_embedding_model={self.openai_embedding_model!r}, "
            f"openai_chat_model={self.openai_chat_model!r}, "
            "database_url='[REDACTED]', "
            f"collection_name={self.collection_name!r})"
        )


def _value(environment: dict[str, str], name: str) -> str:
    value = environment.get(name)
    if value is None or not value.strip():
        raise ChatConfigurationError(f"Invalid or missing setting: {name}")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ChatConfigurationError(f"Invalid or unsafe setting: {name}")
    return value.strip()


def _database_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise ChatConfigurationError("Invalid or unsafe setting: DATABASE_URL") from error
    if (
        parsed.scheme not in {"postgresql", "postgres", "postgresql+psycopg"}
        or not parsed.hostname
        or (port is not None and not 1 <= port <= 65535)
    ):
        raise ChatConfigurationError("Invalid or unsafe setting: DATABASE_URL")
    return value


def load_settings(
    *, environment: dict[str, str] | None = None, repository_root: Path | None = None
) -> ChatSettings:
    """Load ``.env`` and validate the settings required by Wave 2 chat."""

    if repository_root is None:
        load_dotenv()
    else:
        load_dotenv(Path(repository_root) / ".env")
    values = os.environ if environment is None else environment

    api_key = _value(values, "OPENAI_API_KEY")
    embedding_model = _value(values, "OPENAI_EMBEDDING_MODEL")
    if embedding_model != APPROVED_EMBEDDING_MODEL:
        raise ChatConfigurationError(
            "Invalid setting: OPENAI_EMBEDDING_MODEL must be text-embedding-3-small"
        )
    chat_model = _value(values, "OPENAI_CHAT_MODEL")
    if chat_model != APPROVED_CHAT_MODEL:
        raise ChatConfigurationError(
            "Invalid setting: OPENAI_CHAT_MODEL must be gpt-5.4-mini"
        )
    database_url = _database_url(_value(values, "DATABASE_URL"))
    collection_name = _value(values, "PG_VECTOR_COLLECTION_NAME")
    if not _COLLECTION_NAME.fullmatch(collection_name):
        raise ChatConfigurationError(
            "Invalid or unsafe setting: PG_VECTOR_COLLECTION_NAME"
        )

    return ChatSettings(
        openai_api_key=api_key,
        openai_embedding_model=embedding_model,
        openai_chat_model=chat_model,
        database_url=database_url,
        collection_name=collection_name,
    )


load_chat_settings = load_settings
