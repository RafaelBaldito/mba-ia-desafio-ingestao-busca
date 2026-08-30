# TASK-001 — Establish Ingestion Configuration and Test Foundation

## Objective

Create the validated, secret-safe Wave 1 ingestion configuration boundary and
the repository test/coverage foundation required before any external
collaborator can be constructed.

## Scope

- Add `pytest` and `pytest-cov` as development test dependencies and configure
  the repository-native command `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`.
- Replace obsolete Google/Gemini configuration and dependencies with the
  approved OpenAI-only Wave 1 configuration.
- Implement a focused configuration loader/settings object and typed
  configuration error in a new `src/ingestion_config.py` module.
- Add unit tests for valid configuration and all specified invalid/unsafe
  configuration paths.

## Context

### Required

- `docs/waves/1-reproducible-vector-ingestion/TECHSPEC.md` — §§3, 4.1, 5–7
- `docs/ARCHITECTURE.md` — §4 and §8
- `.env.example`, `requirements.txt`, and `src/ingest.py`

### Optional

- `docker-compose.yml` — verify that application configuration does not adopt
  Compose connection literals

## Requirements

- Load `.env` at process startup and validate `OPENAI_API_KEY`,
  `OPENAI_EMBEDDING_MODEL`, `DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME`, and
  `PDF_PATH` before constructing a loader, provider, or store.
- Require non-empty values; require the model to equal
  `text-embedding-3-small`; reject unsafe configuration needed to uphold the
  approved configuration contract. Resolve a relative PDF path against the
  repository working directory, while file-kind/readability checks remain for
  the PDF service.
- Configuration failures must identify only the affected setting and never
  include secret values or credential-bearing database URLs.
- Update `.env.example` to contain only the five approved Wave 1 settings with
  placeholders or safe local examples. Remove Google/Gemini packages and
  entries that contradict the approved provider boundary; retain required
  LangChain/OpenAI/Postgres/PDF runtime dependencies.
- Establish a `tests/` layout and tests that exercise configuration behavior
  without OpenAI, Docker, or PostgreSQL.

## Constraints

- Do not add a chat-model setting, retrieval settings, Gemini compatibility,
  or any Wave 2 behavior.
- Do not embed, print, or commit a real secret or credential-bearing URL.
- Do not exclude relevant `src` production modules from coverage.

## Acceptance Criteria

- A valid environment produces a settings object containing the approved
  embedding model, configured collection, database connection, and resolved
  PDF path without exposing secrets in its normal representation or errors.
- Missing/empty required settings and a non-approved embedding model raise a
  typed configuration error before any external collaborator is constructed.
- `.env.example` contains exactly the approved Wave 1 setting categories and
  no Google/Gemini setting.
- The declared pytest command is runnable and enforces project coverage of at
  least 90% without coverage exclusions for production behavior.

## Validation

- `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`
- `python -c "import ingest; import ingestion_config"`

Record the executed command output and coverage percentage as task evidence;
do not claim Docker, OpenAI, or database validation in this task.

## Dependencies

- None.

## Affected Files

- `requirements.txt`
- `.env.example`
- `src/ingestion_config.py` (new)
- test-runner configuration, if needed by the chosen repository-native setup
- `tests/test_ingestion_config.py` (new)

## Out of Scope

- PDF extraction and chunking, vector persistence, CLI orchestration,
  integration tests, and every Wave 2 component.
