# TASK-005 — Verify pgVector Retrieval Integration and Release Quality Gate

## Objective

Extend the isolated pgVector test to validate the real Wave 2 retrieval
adapter, then record the complete repository quality gate for the finished
Wave 2 scope.

## Scope

- Extend the existing opt-in disposable pgVector integration suite to seed and
  retrieve a Wave 2-compatible collection without OpenAI credentials.
- Run and record the required project-wide automated validation; update only
  directly affected integration-test documentation/evidence if needed.

## Context

### Required

- `docs/waves/2-grounded-semantic-chat/TECHSPEC.md` — §§1.1, 4.3, 6–7
- `src/search.py` and `src/chat_config.py`
- `tests/integration/test_pgvector_persistence.py` and `tests/integration/compose.yaml`

### Optional

- `docs/ARCHITECTURE.md` — §§5, 7–8
- `tests/integration/README.md` and `tests/integration/EVIDENCE.md`

## Requirements

- Reuse the isolated disposable Compose project/fixture. Seed at least ten
  text documents with a deterministic local 1536-dimensional embedding
  implementation in one unique collection; do not require an OpenAI key.
- Exercise the Wave 2 retrieval adapter against that collection and verify ten
  ordered text records are returned under its `k=10`, cosine, and
  1536-dimension contract.
- Preserve fixture cleanup and isolation: do not access the persistent local
  `postgres_data` volume, user corpus, or real provider credentials.
- Run the repository-wide coverage command without production-code exclusions;
  it must meet at least 90% coverage across `src`, including existing
  ingestion tests. Run the opt-in integration test only with its documented
  environment flag and record whether Docker made it executable.

## Constraints

- This task validates the approved retrieval contract; it must not change
  persistence schema, create a new vector backend, alter chunking/reingestion,
  or add a live OpenAI smoke test.
- Never treat a skipped opt-in Docker test as a successful integration run.
- Do not claim a manual credentialed smoke or public-GitHub verification unless
  it is actually performed under its separate release-time authority.

## Acceptance Criteria

- The isolated integration test seeds at least ten 1536-dimensional documents
  and proves the Wave 2 adapter returns exactly ten relevance-ordered text
  values from its unique pgVector collection.
- The integration suite remains opt-in, disposable, credential-free for
  OpenAI, and unable to touch persistent local data.
- The full project test command passes with coverage at or above 90%, with no
  relevant production module omitted; actual command output is recorded as
  task evidence.
- Any directly affected integration instructions accurately state the opt-in
  Docker prerequisite and command.

## Validation

- `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`
- `$env:RUN_PGVECTOR_INTEGRATION='1'; python -m pytest tests/integration/test_pgvector_persistence.py -m pgvect_integration`
- `python -c "import src.search; import src.chat"`

Record results, including an honest skipped/blocked Docker outcome when the
required local service is unavailable.

## Dependencies

- TASK-002 — implemented PGVector retrieval adapter.
- TASK-003 — complete grounded answer path included in coverage.
- TASK-004 — final CLI/documentation production changes included in coverage.

## Affected Files

- `tests/integration/test_pgvector_persistence.py`
- `tests/integration/README.md` and/or `tests/integration/EVIDENCE.md` only if
  their existing instructions/evidence require direct update

## Out of Scope

- Production implementation changes, README rewrite, live OpenAI/manual smoke,
  publication to GitHub, and all future-wave work.
