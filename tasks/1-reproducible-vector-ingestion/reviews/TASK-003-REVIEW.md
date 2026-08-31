## Review Result

FIX_REQUIRED

## Task

`TASK-003 — Implement Embedding and pgVector Persistence Adapters`

## Validation

| Check | Result | Evidence |
|-------|--------|----------|
| `python -c "importlib.metadata...; inspect.signature(PGVector...)"` | PASS | Installed `langchain-postgres` is `0.0.15`; `PGVector.from_documents` accepts `pre_delete_collection` and forwards `**kwargs` to the store construction path, which accepts the required compatibility arguments. |
| `python -m pytest tests/test_ingestion_store.py --cov=src --cov-report=term-missing --cov-fail-under=90` | FAIL | All 9 tests passed, but the command exited with coverage 48.02% (`src/ingestion_store.py`: 88%), below the required 90%. |
| `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90` | FAIL | Coverage was 93.79%, but `tests/test_ingestion_config.py::test_dotenv_is_loaded_at_process_boundary` failed. `src/ingestion_config.py` and its failing test are unchanged from `HEAD`, so this is recorded as external validation evidence, not a TASK-003 code finding. |
| `python -c "import ingestion_store"` | FAIL | Exit code 1: `ModuleNotFoundError: No module named 'ingestion_store'` from the repository root. |
| Secret-safety probe with failing injected factories | FAIL | The public typed messages are redacted, but both exception `__cause__` values retained the injected API key/database URL. |

## Acceptance Criteria

| Criterion | Result | Evidence |
|-----------|--------|----------|
| Fakes reach the approved provider/store seam with model, cosine distance, 1536 guard, configured connection/collection, collection metadata, replacement request, and complete document/ID handoff. | PASS | `tests/test_ingestion_store.py::test_ingestion_handoff_uses_approved_provider_and_replacement_configuration` passed; inspected code passes `model`, `DistanceStrategy.COSINE`, `embedding_length=1536`, metadata, IDs, and `pre_delete_collection=True`. |
| A rerun uses replacement rather than append semantics. | PASS | `test_identical_chunks_have_stable_ids_and_reingestion_replaces` passed and verifies `pre_delete_collection=True` for both calls. |
| Stable IDs and persisted count are deterministic for identical source chunks. | PASS | Stable IDs are `source:chunk_index`; the reingestion test passed with counts `(2, 2)` and equal ID lists. |
| Provider and persistence failures are typed and secret-safe for the CLI layer. | FAIL | The adapter raises typed errors, but lines 69 and 109 chain the raw provider/database exception, whose message may contain the API key or credential-bearing URL. |

## Findings

### FINDING-001 — HIGH — Raw provider and database errors remain reachable through typed failures

- Location: `src/ingestion_store.py:67-69`, `src/ingestion_store.py:107-109`
- Issue: The typed errors use `raise ... from error`, retaining raw provider/driver exceptions as `__cause__`.
- Evidence: A deterministic injected-factory probe reported `provider_cause_exposes_secret=True` and `persistence_cause_exposes_secret=True` while the injected exceptions contained an API key and a credential-bearing PostgreSQL URL.
- Expected: Provider and persistence failures must be typed and credential-safe, without exposing provider payloads, API keys, passwords, or complete database URLs.
- Fix direction: Suppress or replace the raw cause with a credential-safe typed cause, and add tests that inspect chained/context exceptions as well as the top-level string.

### FINDING-002 — HIGH — Required import validation fails from the repository root

- Location: `src/ingestion_store.py:13-22`; repository root import path
- Issue: The task-required command `python -c "import ingestion_store"` cannot locate the new adapter from the repository root.
- Evidence: The executed command exited 1 with `ModuleNotFoundError: No module named 'ingestion_store'`. `pytest.ini` only adds `src` to pytest's import path, which does not apply to plain Python.
- Expected: The explicit task import-validation command must succeed in its repository-native execution context.
- Fix direction: Establish a repository-supported import path/package entry point for the adapter, or obtain an approved correction to the task validation command if its intended working directory is `src`.

### FINDING-003 — HIGH — TASK-003 tests do not meet the required coverage gate for generated adapter code

- Location: `tests/test_ingestion_store.py`; `src/ingestion_store.py:16-22,106`
- Issue: The adapter's own measured coverage is 88%, and the mandatory focused validation exits non-zero at 48.02% project coverage.
- Evidence: `python -m pytest tests/test_ingestion_store.py --cov=src --cov-report=term-missing --cov-fail-under=90` ran 9 passing tests but failed coverage. The report marks the direct-import fallback and the typed persistence re-raise as uncovered.
- Expected: Generated TASK-003 code must be covered above 90%, and the mandatory validation must pass without excluding relevant production code.
- Fix direction: Add meaningful tests for the uncovered adapter behavior and preserve the unexcluded project coverage gate; if the focused command is intended to enforce project-wide coverage while selecting one file, request an approved validation-command clarification rather than bypassing coverage.

## Non-Blocking Notes

- The installed `langchain-postgres` API version is `0.0.15`. Its `PGVector.from_documents` signature supports `pre_delete_collection`, and its `**kwargs` forwarding reaches the constructor path that supports `embedding_length` and `collection_metadata`.
- The full-suite failure in `test_dotenv_is_loaded_at_process_boundary` predates TASK-003's untracked files and is outside this review's implementation scope; it still prevents a clean repository-wide validation run.

## Summary

The adapter satisfies the functional fake-handoff, replacement, stable-ID, and API-compatibility checks, but it fails the approved credential-safety requirement and two mandatory task validation requirements. TASK-003 requires remediation and re-review. No production code or tests were modified during this review.
