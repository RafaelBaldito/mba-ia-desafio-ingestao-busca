"""Root-level import bridge for the repository's ``src`` entry point."""

from src.ingest import ingest_pdf

__all__ = ["ingest_pdf"]
