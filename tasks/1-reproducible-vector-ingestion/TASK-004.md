# TASK-004 — Implement the Ingestion Orchestrator and CLI

## Objective

> **Validation amendment (2026-09-01):** explicit human approval. Targeted
> tests demonstrate task-owned behavior; the 90% project coverage gate is
> evaluated only by the full-suite command below.

Connect the approved configuration, document, and persistence components into
a testable `ingest(settings) -> IngestionResult` operation and the required
safe `python src/ingest.py` command.

## Scope

- Add `src/ingestion_orchestrator.py` containing the typed ingestion result
  and collaborator-injected orchestration flow.
- Replace the current skeletal `src/ingest.py` with the thin CLI entry point.
- Add unit tests for successful sequencing, no-effect failure paths, and
  command exit/reporting behavior with all collaborators faked.

## Context

### Required

- `docs/waves/1-reproducible-vector-ingestion/TECHSPEC.md` — §§4.1–4.3, §5–7
- `src/ingestion_config.py`, `src/ingestion_document.py`, and `src/ingestion_store.py`
- `src/ingest.py`

### Optional

- `docs/ARCHITECTURE.md` — §§3, 6, and 8

## Requirements

- Implement the logical operation `ingest(settings) -> IngestionResult`, where
  the result contains only the source basename, collection name, and persisted
  chunk count.
- Sequence configuration validation, source validation/loading, chunk
  validation, adapter construction, and replacement persistence so each early
  failure prevents subsequent effects. The orchestrator must accept replaceable
  loader, embedder, and store collaborators/factories.
- Keep `ingest.py` a thin entry point: load configuration, invoke the
  orchestrator, print the success summary only after persistence completes,
  and map expected configuration/source/chunk/provider/persistence failures to
  one actionable stderr message and a non-zero process exit.
- For database failure, state that PostgreSQL/pgVector persistence failed and
  a failed replacement may require rerun. For provider failure, report only a
  safe provider failure. Catch unexpected exceptions only at the entry point
  and report them safely.
- Never print chunk text, vectors, API keys, passwords, database URLs, or
  provider payloads. Do not retry automatically.

## Constraints

- Preserve `src/ingest.py` as the executable entry point and do not change
  `src/search.py` or `src/chat.py`.
- Do not add retrieval `k=10`, question embedding, semantic search, prompt
  construction, answer generation, multiple sources, atomic replacement, or
  versioning.

## Acceptance Criteria

- With faked collaborators, a successful invocation passes the configured PDF
  and collection through the approved sequence and reports exactly the safe
  source, collection, and persisted-count summary after store completion.
- Each expected failure class stops later collaborator calls, exits non-zero,
  and writes one actionable, credential-safe stderr message.
- An unchanged successful rerun reaches store replacement with deterministic
  chunk IDs and does not add an orchestration-level append path.
- CLI and orchestrator tests require no OpenAI access, Docker runtime, or live
  database, and the full suite maintains the 90% gate.

## Validation

- `python -m pytest tests/test_ingestion_orchestrator.py tests/test_ingest_cli.py`
- `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`
- `python src/ingest.py` with deliberately missing required configuration,
  verifying a non-zero exit and no secret exposure

Record command outputs, exit status, and coverage. The final command is a
local negative-path smoke check only; it must not contact external services.

## Dependencies

- TASK-001 — configuration/test foundation.
- TASK-002 — PDF/chunk service.
- TASK-003 — provider and persistence adapter seams.

## Affected Files

- `src/ingestion_orchestrator.py` (new)
- `src/ingest.py`
- `tests/test_ingestion_orchestrator.py` (new)
- `tests/test_ingest_cli.py` (new)

## Out of Scope

- Disposable database provisioning, real OpenAI smoke execution, retrieval,
  chat, README chat-flow documentation, and all Wave 2 code.
