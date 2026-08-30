## Review Result

FIX_REQUIRED

## Task

`TASK-001 — Establish Ingestion Configuration and Test Foundation`

## Validation

| Check | Result | Evidence |
|---|---|---|
| `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90` | FAIL | Active Python 3.14 has no `pytest` installed: `No module named pytest`. |
| `.venv\\Scripts\\python.exe -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90` | PASS | 13 tests passed; reported 98.21%, but only because `.coveragerc` omits production modules. |
| Coverage without exclusions | FAIL | `--cov-config=NUL` reports 80.88% (13 missed lines), below 90%. |
| `python -c "import ingest; import ingestion_config"` | FAIL | `ModuleNotFoundError: No module named 'ingest'` from repository root, including through `.venv`. |
| Google/Gemini runtime configuration/dependencies search | PASS | No remaining matches outside documentation/task artifacts. |
| `git diff --check` | PASS | No whitespace errors. |

## Acceptance Criteria

| Criterion | Result | Evidence |
|---|---|---|
| Valid environment yields safe resolved settings | PASS | `test_loads_valid_settings_and_resolves_relative_pdf` passes; `IngestionSettings.__repr__` redacts API key and database URL. |
| Invalid settings fail with typed, credential-safe error before collaborators | PASS | 13 unit tests cover missing/empty settings, wrong model, unsafe collection/database values, and dotenv loading. |
| `.env.example` has exactly five Wave 1 categories and no Google/Gemini setting | PASS | Contains only the five approved variables. |
| Declared pytest command runs and enforces ≥90% project coverage without production exclusions | FAIL | Exact command cannot run in the active environment; `.coveragerc` excludes `src/chat.py` and `src/search.py`, and unomitted coverage is 80.88%. |

## Findings

### FINDING-001 — HIGH — Coverage gate excludes production modules

- Location: `.coveragerc:2-4`
- Issue: `src/chat.py` and `src/search.py` are explicitly omitted from project coverage.
- Evidence: With the configured omission, coverage is 98.21%; without it, the same tests produce 80.88%, below the required 90%.
- Expected: The task requires project-wide `src` coverage with no exclusions for production behavior.
- Fix direction: Remove the exclusions and add meaningful coverage sufficient to meet the approved threshold, without expanding Wave 1 behavior.

### FINDING-002 — HIGH — Required import validation is not runnable from repository root

- Location: `pytest.ini:3`, `src/ingestion_config.py`
- Issue: Source imports are not configured for the required `python -c "import ingest; import ingestion_config"` command.
- Evidence: The command fails with `ModuleNotFoundError: No module named 'ingest'`, including when invoked through the repository `.venv`.
- Expected: The task's declared import-validation command must succeed.
- Fix direction: Establish the approved source import path for direct Python execution and verify the specified command succeeds.

## Summary

The configuration implementation and its focused tests are sound, but the task cannot pass because the mandated coverage gate is artificially satisfied through exclusions and the required import validation fails. No production code or tests were modified during review.
