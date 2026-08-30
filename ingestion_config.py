"""Root-level import bridge for the ingestion configuration module."""

from src.ingestion_config import (
    APPROVED_EMBEDDING_MODEL,
    IngestionConfigurationError,
    IngestionSettings,
    load_settings,
)

__all__ = [
    "APPROVED_EMBEDDING_MODEL",
    "IngestionConfigurationError",
    "IngestionSettings",
    "load_settings",
]
