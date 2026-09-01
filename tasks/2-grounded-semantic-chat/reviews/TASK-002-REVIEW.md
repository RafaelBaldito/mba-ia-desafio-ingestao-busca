## Review Result

FIX_REQUIRED

## Task

`TASK-002 — Implement Ten-Chunk Retrieval and Mandatory Prompt`

## Validation

| Check | Result | Evidence |
|-------|--------|----------|
| `python -m pytest tests/test_search.py --cov=src.search --cov-report=term-missing --cov-fail-under=90` | PASS | 17 passed; `src.search` coverage 94.29% (66/70 statements). |
| `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90` | PASS | 91 passed, 1 skipped; repository coverage 98.56% (342/347 statements). |
| `python -c "import src.search"` | PASS | Module import completed successfully. |
| Prompt contract inspection | PASS | The UTF-8 fallback code points match the approved literal; the template has exactly the two permitted placeholders, four fallback occurrences, and the required final heading. |
| `git diff --check` | PASS | No whitespace errors reported. |

## Acceptance Criteria

| Criterion | Result | Evidence |
|-----------|--------|----------|
| Exact approved embedding/store configuration, literal `k=10`, query handoff, preserved adapter order, immutable ten-item return | FAIL | The adapter configuration, literal `k=10`, order preservation, and tuple return are correct, but `retrieve` forwards an untrimmed question to the semantic search. |
| Blank questions, adapter exceptions, invalid pairs, non-numeric scores, blank/non-text chunks, and result counts other than ten produce a typed safe failure | PASS | `src/search.py:84-101, 113-134` validates result shape/content/count and converts unexpected failures to safe `RetrievalError`; targeted tests cover the required failure boundary. |
| Ten known chunks render unchanged, ordered, double-newline-separated context and the complete mandatory prompt/fallback content | PASS | `src/search.py:23-49, 137-154` joins only `page_content` values in tuple order; `tests/test_search.py:152-198` locks the full literal prompt. |
| Invalid question or chunk count/content cannot render a prompt | PASS | `src/search.py:140-152` rejects blank questions, non-tuples, non-ten counts, invalid chunk text, and invalid scores; targeted tests pass. |

## Findings

### FINDING-001 — MEDIUM — Retrieval does not trim the validated question

- Location: `src/search.py:113-128`; `tests/test_search.py:61, 71`
- Issue: `retrieve` uses `question.strip()` only to decide whether the input is blank, then sends the original untrimmed value to `similarity_search_with_score`.
- Evidence: The test invokes `retrieve("  minha pergunta  ", ...)` and asserts that the store receives the same whitespace-padded string. The implementation at line 128 likewise passes `question`, not a stripped value.
- Expected: TASK-002 and TECHSPEC §4.3 require trimming and validating the question before constructing dependencies and performing retrieval. The embedding/search query must be the trimmed question.
- Fix direction: Normalize the question once after type validation, use that normalized value for the store query, and adjust/add the handoff assertion so leading/trailing whitespace cannot regress.

## Non-Blocking Notes

- The previously recorded mandatory-prompt defect is resolved: the rendered final heading includes its closing quote and the test now asserts a fixed full expected prompt.

## Summary

The retrieval configuration, exact-ten invariant, safe errors, prompt contract, tests, and coverage gates pass. TASK-002 remains `FIX_REQUIRED` because it does not satisfy the approved trimmed-question retrieval contract. No production code, tests, or specifications were changed during this review.

---

## Re-review Result — 2026-08-31

## Review Result

FIX_REQUIRED

## Task

`TASK-002 — Implement Ten-Chunk Retrieval and Mandatory Prompt`

## Validation

| Check | Result | Evidence |
|-------|--------|----------|
| `python -m pytest tests/test_search.py --cov=src.search --cov-report=term-missing --cov-fail-under=90` | PASS | 17 passed; `src.search` coverage 94.37% (67/71 statements). |
| `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90` | PASS | 91 passed, 1 skipped; repository coverage 98.56% (343/348 statements). |
| Originally approved direct-task command: `python -m pytest tests/test_search.py --cov=src --cov-report=term-missing --cov-fail-under=90` | FAIL | 17 tests passed, but coverage was 25.86%, below the required 90%. |
| `python -c "import src.search"` | PASS | Module import completed successfully. |
| TECHSPEC §4.4 prompt comparison | PASS | Rendered prompt matched the approved UTF-8 template byte-for-byte after only its two permitted substitutions. |
| `git diff --check` | PASS | No whitespace errors reported. |

## Acceptance Criteria

| Criterion | Result | Evidence |
|-----------|--------|----------|
| Exact approved embedding/store configuration, literal `k=10`, query handoff, preserved adapter order, immutable ten-item return | PASS | `src/search.py:113-130` validates and trims the question, constructs the approved adapters with cosine/1536, and calls the literal count; `tests/test_search.py:47-71` verifies the seam and order. |
| Blank questions, adapter exceptions, invalid pairs, non-numeric scores, blank/non-text chunk content, and result counts other than ten produce a typed safe failure | PASS | `src/search.py:84-101, 113-135` enforces the boundary without retaining provider exceptions; `tests/test_search.py:74-117` covers invalid questions, count, malformed pairs, and safe errors. |
| Ten known chunks render unchanged, ordered, double-newline-separated context and the complete mandatory prompt/fallback content | PASS | `src/search.py:23-49, 138-155` and `tests/test_search.py:152-198`; independent comparison against TECHSPEC §4.4 passed. |
| Invalid question or chunk count/content cannot render a prompt | PASS | `src/search.py:141-153`; `tests/test_search.py:130-141` passes. |

## Findings

### FINDING-002 — HIGH — Approved task validation was changed without approval and its original gate fails

- Location: `tasks/2-grounded-semantic-chat/TASK-002.md:69`; `tasks/2-grounded-semantic-chat/TASKS.md:19`
- Issue: The implementation changed TASK-002's approved direct-test command from `--cov=src` to `--cov=src.search`. This changes the approved validation contract and narrows its coverage surface, although `TASK-002.md` lists only `src/search.py` and `tests/test_search.py` as affected files.
- Evidence: `git diff` shows the validation-command replacement. Executing the original command collected 17 passing tests but failed `--cov-fail-under=90` at 25.86%; the altered command instead passed at 94.37% for `src.search` alone.
- Expected: The approved task contract must remain unchanged unless explicit human approval records its amendment. Required validation must be satisfied under that approved contract; lower-level implementation work must not redefine it.
- Fix direction: Restore the approved task content and make its mandated validation pass within approved scope, or obtain and record explicit human approval for a corrected validation contract before re-review. Do not silently retain the narrowed command.

## Summary

The current retrieval and prompt implementation satisfies the functional acceptance criteria, and both the current targeted and repository-wide suites pass. TASK-002 cannot receive acceptance because its implementation modified the approved validation contract and the original required direct-task command fails. No production code, tests, or approved specifications were changed by this re-review.

---

## Human Resolution Record — 2026-08-31

- `FINDING-002`: resolved by explicit human approval of a task-contract
  amendment.
- The task-targeted gate is now `python -m pytest tests/test_search.py`.
- The project-wide 90% coverage gate remains
  `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`.
- This approval resolves the specification conflict but does not grant review
  `PASS`; TASK-002 returns to `IMPLEMENTED` and requires independent re-review.

---

## Re-review Result — 2026-08-31

## Review Result

FIX_REQUIRED

## Task

`TASK-002 — Implement Ten-Chunk Retrieval and Mandatory Prompt`

## Previous Findings

| Finding | Status | Evidence |
| --- | --- | --- |
| `FINDING-001` — Retrieval does not trim the validated question | RESOLVED | `src/search.py:115-116, 128` now normalizes the question before search; `tests/test_search.py:47-71` asserts the store receives `"minha pergunta"`. |
| `FINDING-002` — Approved task validation was changed without approval | RESOLVED | `TASK-002.md:3-6, 74` contains the explicit approved amendment; the amended direct-task command passed. |

## Validation

| Check | Result | Evidence |
| --- | --- | --- |
| `python -m pytest tests/test_search.py` | PASS | 17 passed in 9.53s. |
| `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90` | PASS | 91 passed, 1 skipped; repository coverage 99% (343/348 statements), above the 90% gate. |
| `python -c "import src.search"` | PASS | Import completed successfully. |
| Mandatory-prompt structural inspection | PASS | Four fallback-literal occurrences, exactly one `{contexto}` placeholder, exactly one `{pergunta}` placeholder, and final newline; `tests/test_search.py:152-198` also asserts the complete rendered prompt. |
| `git diff --check` | PASS | No whitespace errors reported. |
| Pinned `langchain-postgres` adapter inspection | FAIL | Installed `langchain-postgres==0.0.15` exposes `PGVector(..., create_extension=True)` by default; its `__post_init__` calls `create_vector_extension`, `create_tables_if_not_exists`, and `create_collection`, which uses `get_or_create`. |

## Acceptance Criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Exact approved embedding/store configuration, literal `k=10`, query handoff, preserved adapter order, and immutable ten-item return | FAIL | The model, API-key handoff, cosine distance, 1536 dimensions, literal count, normalized query, order, and tuple invariant are correct in `src/search.py:113-135`; however the production `PGVector` constructor is invoked without disabling its mutating initialization path. |
| Blank questions, adapter exceptions, invalid pairs, non-numeric scores, blank/non-text chunks, and result counts other than ten produce a typed safe failure | PASS | `src/search.py:84-101, 113-135` validates the boundary and suppresses provider details; `tests/test_search.py:74-117` exercises the safe typed-failure paths. |
| Ten known chunks render unchanged, ordered, double-newline-separated context and the complete mandatory prompt/fallback content | PASS | `src/search.py:23-50, 138-155` only joins `page_content` in input order; the full exact expected rendering in `tests/test_search.py:152-198` passes. |
| Invalid question or chunk count/content cannot render a prompt | PASS | `src/search.py:141-153` rejects invalid question, count, tuple, text, and score; `tests/test_search.py:130-151` passes. |

## Findings

### FINDING-003 — HIGH — Retrieval construction can mutate the persisted collection

- Location: `src/search.py:122-128` (`PGVector` construction)
- Issue: The default production `PGVector` construction leaves `create_extension=True` and invokes the library initializer that can create the vector extension, tables, and configured collection. This is a write-capable initialization path, rather than an adapter restricted to reading the existing collection.
- Evidence: The installed pinned `langchain-postgres==0.0.15` signature sets `create_extension=True`. Its `PGVector.__post_init__` calls `create_vector_extension()`, `create_tables_if_not_exists()`, and `create_collection()`; `create_collection()` calls `CollectionStore.get_or_create(...)`. `src/search.py:122-128` passes none of the relevant controls, and `tests/test_search.py:47-71` does not assert a non-mutating initialization contract.
- Expected: TASK-002 Constraints and TECHSPEC §§3, 4.1, and 4.3 require retrieval to read the existing configured collection and never create, delete, replace, migrate, or reingest it. A missing/wrong collection must surface as a safe `RetrievalError`, not be created.
- Fix direction: Use a retrieval initialization path that cannot issue extension/table/collection creation or `get_or_create` operations against the configured collection, while retaining the approved `PGVector` retrieval contract; extend the injection-double tests to prove the non-mutating initialization and safe missing-collection failure. Do not change the approved task or TECHSPEC unless such a path proves unavailable.
- Review provenance: `MISSED_IN_PREVIOUS_REVIEW: yes`; `REGRESSION_FROM_FIX: no`.

## Summary

The two previous findings are resolved, and the complete acceptance matrix was repeated without detecting a regression from their remediation. Functional retrieval/prompt behavior and all approved test/coverage gates pass. TASK-002 remains `FIX_REQUIRED` because its default pgVector initialization can mutate the persisted collection, violating a core approved boundary. No production code, tests, or approved contracts were changed during this review.
