# TASK-001 — Establish Secure Chat Configuration

## Objective

Create the immutable, credential-safe configuration boundary required before
Wave 2 constructs a retrieval adapter or chat model.

## Scope

- Add `src/chat_config.py` with `ChatSettings`, a typed configuration error,
  and a testable settings loader.
- Extend `.env.example` with the approved chat-model setting while preserving
  safe placeholders and the existing Wave 1 configuration categories.
- Add focused configuration unit tests.

## Context

### Required

- `docs/waves/2-grounded-semantic-chat/TECHSPEC.md` — §§4.1–4.2, 5–7
- `docs/ARCHITECTURE.md` — §§3–4, 8–9
- `src/ingestion_config.py`, `.env.example`, and `tests/test_ingestion_config.py`

### Optional

- `docs/PRD.md` — §§7–9
- `docs/DELIVERY-PLAN.md` — §§6–7

## Requirements

- Load and validate `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`,
  `OPENAI_CHAT_MODEL`, `DATABASE_URL`, and `PG_VECTOR_COLLECTION_NAME` before
  any provider or store factory is called.
- Require non-empty values, reject control characters, require respectively
  `text-embedding-3-small` and `gpt-5.4-mini`, validate a PostgreSQL/psycopg
  URL, and validate the collection logical identifier according to TECHSPEC
  §4.2.
- Make settings immutable and ensure representations and errors redact the API
  key and credential-bearing database URL. Configuration failures may name a
  setting but no secret value.
- Do not require `PDF_PATH` in `ChatSettings` and do not alter the Wave 1
  `IngestionSettings` validation contract.
- Add `OPENAI_CHAT_MODEL='gpt-5.4-mini'` to `.env.example`; retain only safe
  non-secret values and do not introduce Gemini settings.

## Constraints

- Configuration code owns no PDF, pgVector, terminal-loop, prompt-rendering,
  or model-invocation behavior.
- Do not change `requirements.txt`, Docker Compose, the collection schema, or
  persisted data.
- Do not log, print, serialize, or commit real credentials.

## Acceptance Criteria

- A valid supplied environment produces an immutable `ChatSettings` containing
  only the approved identifiers and configured database/collection values,
  with secrets redacted from its representation.
- Missing, blank, control-character-bearing, malformed, or unapproved setting
  values raise the typed error before any external factory can be constructed.
- `.env.example` documents the exact `gpt-5.4-mini` chat setting alongside
  consistent safe configuration placeholders and no Gemini option.
- Unit tests verify valid and invalid settings, exact model identifiers, and
  secret-safe representations/errors without OpenAI, Docker, or PostgreSQL.

## Validation

- `python -m pytest tests/test_chat_config.py --cov=src --cov-report=term-missing --cov-fail-under=90`
- `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`

Record commands actually run and coverage. If the whole-project gate is not
yet attainable solely because dependent Wave 2 modules are pending, report it
accurately without excluding production modules.

## Dependencies

- None.

## Affected Files

- `src/chat_config.py` (new)
- `.env.example`
- `tests/test_chat_config.py` (new)

## Out of Scope

- Retrieval, prompt composition, `ChatOpenAI` construction, CLI behavior,
  README changes, and pgVector integration testing.
