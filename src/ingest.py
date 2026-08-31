"""Safe command-line entry point for Wave 1 ingestion."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion_config import IngestionConfigurationError, load_settings
from src.ingestion_document import IngestionChunkError, IngestionSourceError
from src.ingestion_orchestrator import ingest
from src.ingestion_store import EmbeddingProviderError, VectorPersistenceError


def main() -> int:
    """Run ingestion and report only safe operational outcomes."""

    try:
        settings = load_settings()
        result = ingest(settings)
    except IngestionConfigurationError as error:
        print(str(error), file=sys.stderr)
        return 1
    except IngestionSourceError as error:
        print(str(error), file=sys.stderr)
        return 1
    except IngestionChunkError:
        print("Ingestion chunk contract validation failed", file=sys.stderr)
        return 1
    except EmbeddingProviderError:
        print("Embedding provider failure", file=sys.stderr)
        return 1
    except VectorPersistenceError:
        print(
            "PostgreSQL/pgVector persistence failed; a failed replacement may require rerun",
            file=sys.stderr,
        )
        return 1
    except Exception:
        print("Ingestion failed unexpectedly", file=sys.stderr)
        return 1

    print(
        f"Ingested {result.source_name} into {result.collection_name} "
        f"({result.chunk_count} chunks)"
    )
    return 0


def ingest_pdf() -> None:
    """Backward-compatible scaffold symbol; command execution uses ``main``."""
    return None


if __name__ == "__main__":
    raise SystemExit(main())
