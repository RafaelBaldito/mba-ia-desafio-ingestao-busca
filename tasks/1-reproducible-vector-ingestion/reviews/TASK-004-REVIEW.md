# Review Result

FIX_REQUIRED

## Task

`TASK-004 — Implement the Ingestion Orchestrator and CLI`

## Validation

| Check | Result | Evidence |
|-------|--------|----------|
| `python -m pytest tests/test_ingestion_orchestrator.py tests/test_ingest_cli.py --cov=src --cov-report=term-missing --cov-fail-under=90` | FAIL | Six tests passed, but coverage was 71.24%, below the required 90% gate. |
| `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90` | PASS | 43 tests passed; project coverage was 92.04%. |
| Missing-configuration smoke: `python src/ingest.py` | PASS | Exit code 1; stderr was `Invalid or missing setting: OPENAI_API_KEY`; no secret was printed. |

## Acceptance Criteria

| Criterion | Result | Evidence |
|-----------|--------|----------|
| Successful faked invocation safely sequences source, collection, persistence count, and post-store report. | PASS | `test_ingest_sequences_collaborators_and_returns_safe_result` verifies loader → embedder → store and `IngestionResult`; CLI success test verifies exact summary. |
| Each expected failure class stops later calls, exits non-zero, and reports one credential-safe stderr message. | FAIL | The implementation has handlers, but the tests cover only missing configuration at the process boundary. No CLI tests cover source, chunk-invariant, provider, or persistence errors, nor their safe reporting/exit behavior. |
| Rerun replaces using deterministic IDs without orchestration append behavior. | PASS | Orchestrator delegates to `persist_chunks`; `tests/test_ingestion_store.py::test_identical_chunks_have_stable_ids_and_reingestion_replaces` verifies stable IDs and `pre_delete_collection=True`. |
| Tests need no OpenAI, Docker, or live database, and the full suite maintains 90%. | FAIL | The tests use fakes and the full suite reaches 92.04%, but the task-required targeted command fails its 90% coverage gate at 71.24%. |

## Findings

### FINDING-001 — HIGH — Required targeted coverage validation fails

- Location: `tests/test_ingestion_orchestrator.py`, `tests/test_ingest_cli.py`
- Issue: The mandatory targeted validation command fails the approved 90% coverage gate.
- Evidence: `python -m pytest tests/test_ingestion_orchestrator.py tests/test_ingest_cli.py --cov=src --cov-report=term-missing --cov-fail-under=90` collected six tests and reported 71.24% coverage.
- Expected: TASK-004 validation must pass with coverage at or above 90%.
- Fix direction: Add meaningful TASK-004 tests for the required orchestration/CLI behavior and ensure the approved targeted validation can meet its coverage gate without excluding relevant production code. If doing so requires changing the approved coverage scope or validating unrelated Wave 2 modules, escalate that conflict before changing the specification.

### FINDING-002 — HIGH — Expected CLI failure classes are not tested

- Location: `tests/test_ingest_cli.py`, `tests/test_ingestion_orchestrator.py`
- Issue: The approved requirement requires safe non-zero CLI behavior for configuration, source, chunk, provider, and persistence failures, but only missing configuration is tested at the CLI boundary.
- Evidence: `test_ingest_cli.py` contains only missing-configuration and success cases. `test_ingestion_orchestrator.py` omits chunk-invariant failure and does not exercise CLI stderr/exit mappings for source, chunk, provider, or persistence failures.
- Expected: Faked collaborators must demonstrate that every expected failure prevents later effects and maps to one actionable credential-safe stderr message with non-zero exit.
- Fix direction: Add focused CLI tests that inject each typed error and assert exit code, one safe stderr message, and absence of secret/payload text; add the missing chunk-failure sequencing test.

### FINDING-003 — MEDIUM — Out-of-scope configuration change included with TASK-004

- Location: `src/ingestion_config.py:61`
- Issue: TASK-004's affected-file contract authorizes the orchestrator, CLI, and their tests, but the implementation also changes configuration-loader behavior by choosing an explicit `.env` path when `repository_root` is supplied.
- Evidence: `git diff -- src/ingestion_config.py` changes `load_dotenv()` to conditional path handling; this file is not listed under TASK-004's affected files or scope.
- Expected: The task must limit changes to its approved scope and not alter prerequisite component behavior.
- Fix direction: Revert this unrelated configuration change, or obtain an approved task/specification boundary that authorizes it.

## Summary

The orchestration and successful CLI path are broadly aligned with the approved design, and the complete suite meets the project-wide gate. However, the required targeted validation fails, required CLI failure-path coverage is incomplete, and an unrelated configuration change is present. No code was modified during this review.
