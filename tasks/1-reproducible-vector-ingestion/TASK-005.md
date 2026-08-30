# TASK-005 — Add Isolated pgVector Integration and Opt-in Smoke Validation

## Objective

Prove the Wave 1 persistence handoff against a disposable pgVector database
without weakening deterministic tests or touching the persistent local corpus.

## Scope

- Add an opt-in integration-test fixture and any focused Compose configuration
  needed to provision and reliably tear down an isolated pgVector PostgreSQL
  database with the `vector` extension.
- Add an integration test for the adapter's real pgVector persistence contract.
- Define an opt-in real-dependency smoke procedure/evidence location for two
  ingestion runs against Compose and `document.pdf`, limited to Wave 1.

## Context

### Required

- `docs/waves/1-reproducible-vector-ingestion/TECHSPEC.md` — §§4.3, 5–7, §8
- `docker-compose.yml`
- `src/ingestion_store.py` and `src/ingestion_orchestrator.py`

### Optional

- `docs/ARCHITECTURE.md` — §§5 and 8
- existing test configuration and fixtures from TASK-001 through TASK-004

## Requirements

- The integration fixture must create a uniquely named disposable Compose
  project/database and remove its containers, network, and volumes in cleanup.
  It must not use `postgres_data`, production credentials, or a developer's
  configured `DATABASE_URL`.
- Wait for PostgreSQL health and vector-extension bootstrap completion before
  testing. Keep the established application contract: the application receives
  its database endpoint through test configuration rather than Compose literals.
- In the isolated database, verify `vector` exists and that persistence into a
  configured collection retains retrievable document text, embeddings, and the
  approved collection association. Use the approved 1536-dimensional model
  compatibility boundary without calling OpenAI; a deterministic embedding
  fake is acceptable for this database-contract test.
- Mark/gate this test so the standard deterministic test command remains
  runnable without Docker, while an explicit integration command runs it when
  Docker is available. The standard suite must still meet the 90% `src`
  coverage threshold through meaningful unit tests.
- Validate the infrastructure definition with `docker compose config`.
- Document only the test/smoke invocation and evidence needed for this Wave;
  do not add the complete Wave 2 README chat-flow documentation.

## Constraints

- No live OpenAI call is permitted in automated integration tests.
- The optional smoke run may use real credentials and `document.pdf` only when
  explicitly provided by the operator; it must run once and then again,
  confirming a successful count and no duplicated corpus.
- A failed replacement is reported as rerun-recoverable; do not introduce
  transactions, a second collection, versioning, retries, or retrieval code.

## Acceptance Criteria

- The integration test provisions an isolated pgVector service, confirms the
  vector extension, persists test documents, and verifies retrievable text and
  embeddings in the configured collection.
- Cleanup leaves no integration project containers, network, or volume data,
  and no test accesses the persistent Compose volume or production database
  credentials.
- The default pytest coverage command remains deterministic and passes the
  90% gate; the separately documented integration command succeeds when its
  Docker prerequisite is present.
- `docker compose config` succeeds for the relevant infrastructure definitions.
- The opt-in smoke procedure records the prerequisite health/bootstrap check
  and the two-run no-duplicate verification, without treating it as a
  substitute for automated tests.

## Validation

- `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`
- `$env:RUN_PGVECTOR_INTEGRATION = '1'; python -m pytest tests/integration/test_pgvector_persistence.py`
  with Docker available
- `docker compose config`
- `docker compose up -d --wait`, followed by `python src/ingest.py` twice with
  valid operator-supplied credentials and `document.pdf`

Configure the fixture to honor `RUN_PGVECTOR_INTEGRATION`; retain the command
outputs, cleanup evidence, exit statuses, and coverage percentage as task
evidence. Do not claim the opt-in commands passed unless they were actually
run in a suitable environment.

## Dependencies

- TASK-004 — complete testable ingestion flow and adapter contracts.

## Affected Files

- `tests/integration/test_pgvector_persistence.py` (new)
- isolated integration Compose/fixture configuration under `tests/integration/` (new)
- test-runner configuration and test documentation/evidence file, if needed

## Out of Scope

- Changes to the persistent `docker-compose.yml` unless a concrete Wave 1
  compatibility defect is demonstrated; production ingestion redesign; search,
  chat, prompt behavior, or any Wave 2 requirement.
