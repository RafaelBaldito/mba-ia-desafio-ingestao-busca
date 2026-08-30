# TASK-002 — Implement Deterministic PDF Loading and Chunking

## Objective

Implement the isolated PDF/chunk service that converts the one configured PDF
into validated deterministic LangChain `Document` chunks before any persistence
operation.

## Scope

- Add a focused `src/ingestion_document.py` service and typed source/chunk
  errors.
- Add deterministic unit tests using a controlled loader double; no network,
  Docker, or live database is permitted.

## Context

### Required

- `docs/waves/1-reproducible-vector-ingestion/TECHSPEC.md` — §§4.1–4.2, §6, §7
- `src/ingestion_config.py` and its tests from TASK-001
- `src/ingest.py`

### Optional

- `docs/ARCHITECTURE.md` — §§6–8

## Requirements

- Validate the resolved source as a readable regular `.pdf` file before
  constructing or invoking the LangChain `PyPDFLoader`.
- Load pages with `PyPDFLoader`, concatenate page content in document order
  using one newline boundary, and create one source document whose `source`
  metadata is `document.pdf`. Fail for malformed/loading failures or when the
  resulting text has no non-whitespace content.
- Use `RecursiveCharacterTextSplitter` with `separators=[""]`,
  `chunk_size=1000`, `chunk_overlap=150`, `length_function=len`, and
  `strip_whitespace=False`.
- Assert before persistence that every non-final chunk is exactly 1,000
  characters, adjacent full chunks share exactly 150 characters, and a final
  remainder is 1–1,000 characters. Do not trim or silently discard chunks.
- Add operational metadata to every chunk only: source, zero-based
  `chunk_index`, `embedding_model`, `chunk_size`, and `chunk_overlap`. The
  source and model values must follow the approved configuration contract.

## Constraints

- Keep loader construction injectable so tests require no actual PDF file
  parser beyond targeted source-file validation tests.
- Do not create stable IDs, embeddings, vector stores, replacement behavior,
  CLI presentation, or Wave 2 retrieval logic here.

## Acceptance Criteria

- Controlled multi-page content yields page-ordered text and deterministic
  1,000-character/150-character-overlap chunks, including a correctly sized
  final remainder and unmodified whitespace.
- Chunk metadata is ordered and contains exactly the approved operational
  fields and values; no sensitive setting is copied to metadata.
- Missing, unreadable, non-PDF, loader-failure, textless, and invariant-failure
  paths produce typed errors before persistence can be attempted.
- Unit tests prove these outcomes without OpenAI, Docker, or PostgreSQL.

## Validation

- `python -m pytest tests/test_ingestion_document.py --cov=src --cov-report=term-missing --cov-fail-under=90`
- `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`

Record targeted and full-suite results, including coverage. If the full-suite
gate cannot yet pass solely because dependent production modules are not
implemented, record that fact accurately for the next task; do not exclude
them from coverage.

## Dependencies

- TASK-001 — configuration object, typed configuration boundary, and test
  command foundation.

## Affected Files

- `src/ingestion_document.py` (new)
- `tests/test_ingestion_document.py` (new)
- directly affected test fixtures under `tests/`

## Out of Scope

- Provider/store construction, collection replacement, CLI error mapping, and
  integration or smoke validation.
