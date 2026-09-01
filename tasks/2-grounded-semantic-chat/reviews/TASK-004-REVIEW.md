# Review — TASK-004: Deliver the Repeatable Chat CLI and Operator Guide

## Review Result

FIX_REQUIRED

## Review Context

- Task: `tasks/2-grounded-semantic-chat/TASK-004.md`
- Approved contract: `docs/waves/2-grounded-semantic-chat/TECHSPEC.md` §§4.1, 4.6, 5–7
- Repository rules: `AGENTS.md`
- Previous review: none; this is the initial independent review.
- Inspected implementation scope: `src/chat.py`, `tests/test_chat.py`, `README.md`, and the related compatibility-test update in `tests/test_ingestion_config.py`.

## Validation

| Check | Result | Evidence |
| --- | --- | --- |
| `python -m pytest tests/test_chat.py` | PASS | 17 passed in 2.17s. |
| `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90` | PASS | 109 passed, 2 skipped; total coverage 98.77% (threshold: 90%). |
| `python -c "import src.search; import src.chat"` | PASS | Exit code 0. |
| `docker compose config` | PASS | Exit code 0; Compose configuration rendered successfully. |
| `python src/chat.py` with invalid local configuration | PASS | Exited 1 before reading input and emitted only `Invalid or missing setting: OPENAI_CHAT_MODEL`. |
| Injected unexpected input failure at `main()` boundary | FAIL | A `RuntimeError` from `input_function` escaped at `src/chat.py:87` and produced a traceback instead of the prescribed safe CLI behavior. |
| `git diff --check` | PASS | Exit code 0; only CRLF conversion warnings from Git. |

No lint or type-check command is configured by this repository (TECHSPEC §7).

## Acceptance Criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Injectable terminal tests cover independent questions, success, literal fallback, blank input, all exits, EOF, and interrupt without external services. | PASS | `tests/test_chat.py:136-207` covers successive questions, blank input, fallback, `sair`/`exit`/`quit`, EOF, and `KeyboardInterrupt`; targeted tests passed. |
| Startup failure stops before input; expected retrieval/model errors retry safely; unexpected failures are bounded at the CLI boundary. | FAIL | Startup and answer-operation paths are covered at `tests/test_chat.py:210-293`, but an unexpected input exception escapes `main()` at `src/chat.py:86-90`, producing a traceback. |
| `python src/chat.py` is importable/executable from the repository root using the direct-script pattern. | PASS | `src/chat.py:5-15` mirrors the root-path bootstrap in `src/ingest.py`; direct execution reached safe startup validation with exit 1 rather than an import error. |
| README provides the reproducible Docker → ingest → chat workflow and `.env.example` remains the safe template. | PASS | `README.md:3-85` contains prerequisites, copy/setup, Compose readiness, ingestion, chat, grounded/fallback examples, exits, ten-chunk prerequisite, and public-GitHub release check. `.env.example` retains safe placeholders and `OPENAI_CHAT_MODEL='gpt-5.4-mini'`. |

## Findings

### FINDING-001 — HIGH — Unexpected input failures escape the safe CLI boundary

- Location: `src/chat.py:86-90`
- Issue: The per-question `try` handles only `EOFError` and `KeyboardInterrupt` around `input_function`. Any other unexpected input/read failure propagates out of `main()`.
- Evidence: Calling `main()` with valid injected settings and an `input_function` that raises `RuntimeError("input failure")` produced an uncaught traceback whose first application frame is `src/chat.py:87`; no safe CLI message was emitted.
- Expected: TECHSPEC §4.6 requires unexpected exceptions to be caught at the CLI boundary, to emit exactly `Não foi possível iniciar ou continuar o chat.`, and to follow the safe per-question behavior. The task also prohibits traceback output.
- Fix direction: Extend the per-question CLI boundary so unexpected failures while obtaining or processing a question emit the prescribed safe message and preserve the defined EOF/interrupt termination behavior. Add an injectable regression test that proves no traceback escapes.
- Review provenance: `MISSED_IN_PREVIOUS_REVIEW: no`; `REGRESSION_FROM_FIX: no`.

### FINDING-002 — MEDIUM — Startup does not construct the required replaceable collaborators before input

- Location: `src/chat.py:62-101`; `src/chat.py:22-40`
- Issue: `main()` loads settings and immediately displays/reads the prompt. Retrieval and the `ChatOpenAI` collaborator are only selected/constructed within `answer()` after a valid question is entered; no startup assembly occurs before the first input.
- Evidence: After `settings = settings_loader()` at line 76, the next observable operation is `output()` at line 84 and `input_function()` at line 87. `ChatOpenAI` construction is deferred to `answer()` lines 35-40, invoked only at line 101.
- Expected: TASK-004 Requirements and TECHSPEC §4.6 require startup to load settings **and construct replaceable retrieval and model collaborators before reading input**.
- Fix direction: Assemble the injected answer/retrieval/model collaboration during startup after configuration validation, pass the prepared operation into the loop, and retain the existing test seams and safe error handling.
- Review provenance: `MISSED_IN_PREVIOUS_REVIEW: no`; `REGRESSION_FROM_FIX: no`.

## Scope and Quality Notes

- No previous review handoff existed, so no prior findings require re-review disposition.
- The implementation stays within the task-owned CLI, tests, and README scope. The skipped legacy scaffold test in `tests/test_ingestion_config.py` is a directly related compatibility update, not an unrelated production change.
- No specification contradiction was identified; both findings are correctable within TASK-004 and do not require upstream contract changes.

## Summary

The CLI protocol, documentation, direct-script bootstrap, test suite, coverage gate, imports, and Compose validation are otherwise satisfactory. `FIX_REQUIRED` because the CLI can emit an unbounded traceback for an unexpected input failure and does not meet the approved startup collaborator-construction order.

## Re-review Update — 2026-09-01

The human explicitly approved the TASK-004 validation amendment on 2026-09-01.
The current approved validation contract is the targeted CLI test command plus the
project-wide coverage command recorded in `TASK-004.md`.

### Previous Findings Disposition

| Finding | Disposition | Evidence |
| --- | --- | --- |
| FINDING-001 | RESOLVED | `src/chat.py:142-150` catches unexpected input failures, emits only the safe unexpected-failure message, and continues. `tests/test_chat.py:210-231` provides the regression test. |
| FINDING-002 | RESOLVED | `main()` invokes `prepare_answer_operation()` before its first input read; `tests/test_chat.py:234-287` proves model assembly precedes input. |

### Current Active Finding

#### FINDING-003 — HIGH — Output failures escape the safe CLI boundary

- Location: `src/chat.py:140`, and the other unguarded `output()` calls in the loop.
- Issue: A failure while writing terminal output propagates from `main()` without
  emitting the prescribed safe message.
- Evidence: With valid injected settings and an injected `output` function that
  raises `RuntimeError`, the startup-banner call escaped `main()` and
  `error_output` received no message.
- Expected: TECHSPEC §4.6 requires unexpected exceptions at the CLI boundary to
  remain bounded and emit `Não foi possível iniciar ou continuar o chat.` where
  output remains available. No traceback may escape.
- Fix direction: Bound terminal-output operations at the CLI boundary, preserving
  the existing expected-failure and EOF/interrupt behavior; add an injectable
  regression test.
- Review provenance: `MISSED_IN_PREVIOUS_REVIEW: yes`;
  `REGRESSION_FROM_FIX: no`.

### Current Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Injectable terminal tests cover independent questions, success, literal fallback, blank input, all exits, EOF, and interrupt without external services. | PASS | `python -m pytest tests/test_chat.py` passed: 19 tests. |
| Startup failure stops before input; expected retrieval/model errors retry safely; unexpected failures are bounded at the CLI boundary. | FAIL | Unexpected `output()` failure escapes at the startup banner. |
| `python src/chat.py` is importable/executable from the repository root using the direct-script pattern. | PASS | Direct import passed; invalid configuration exited safely with code 1 before input. |
| README provides the reproducible Docker → ingest → chat workflow and `.env.example` remains the safe template. | PASS | README and `.env.example` satisfy the approved operator content. |

### Current Validation Evidence

| Check | Result | Evidence |
| --- | --- | --- |
| `python -m pytest tests/test_chat.py` | PASS | 19 passed. |
| `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90` | PASS | 111 passed, 2 skipped; total coverage 97.47%. |
| `python -c "import src.search; import src.chat"` | PASS | Exit code 0. |
| `docker compose config` | PASS | Exit code 0. |

Only FINDING-003 is active for `fix-task`; the earlier findings are retained
above as review history and must not be reimplemented.
