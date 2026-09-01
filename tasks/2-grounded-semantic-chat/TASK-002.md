# TASK-002 — Implement Ten-Chunk Retrieval and Mandatory Prompt

## Objective

Implement the `src/search.py` retrieval boundary and deterministic prompt
renderer that together produce the only permitted model input.

## Scope

- Replace the placeholder search entry point with testable retrieval,
  `RetrievedChunk`, `RetrievalError`, and prompt-building operations.
- Add unit tests with embedding/store doubles for retrieval and prompt rules.

## Context

### Required

- `docs/waves/2-grounded-semantic-chat/TECHSPEC.md` — §§3, 4.3–4.4, 6–7
- `src/chat_config.py` and its tests from TASK-001
- `src/search.py` and `src/ingestion_store.py`

### Optional

- `docs/ARCHITECTURE.md` — §§5–8
- `docs/PRD.md` — FR-004, FR-006–FR-010 and CON-004–CON-005

## Requirements

- Validate a non-empty trimmed question before constructing an embedding or
  store. Construct OpenAI embeddings only with the validated API key and
  `text-embedding-3-small`; connect the existing configured PGVector
  collection with cosine distance and `embedding_length=1536`.
- Invoke `similarity_search_with_score(question, k=10)` with literal,
  non-configurable `k=10`. Preserve returned relevance order and return an
  immutable tuple of exactly ten chunks, each with text `page_content` and a
  numeric score.
- Convert configuration, provider, connection, result-shape, malformed text,
  and result-count failures into a credential-safe `RetrievalError`. Fewer or
  more than ten results must fail; no caller may receive a partial context.
- Render the normative UTF-8 prompt from exactly ten validated chunks. Join
  only `page_content` values in retrieval order using `\n\n`, replace only the
  context and question placeholders, and retain every required heading, rule,
  example, and exact fallback literal byte-for-byte in content.
- Do not trim, rank, summarize, deduplicate, expose scores/metadata, add
  unseen text, invoke a model, or perform terminal I/O.

## Constraints

- Keep OpenAI embedding and PGVector construction injectable so the unit suite
  makes no network, credential, or database call.
- Read but never create, delete, replace, migrate, or reingest the collection.
- Do not introduce a relevance threshold or substitute a library default for
  `k=10`.

## Acceptance Criteria

- Tests prove the exact approved embedding/store configuration, literal
  `k=10`, query handoff, preserved adapter order, and immutable ten-item
  return value.
- Blank questions, adapter exceptions, invalid pairs, non-numeric scores,
  blank/non-text chunk content, and result counts other than ten produce a
  typed safe failure without exposing credentials or retrieved text.
- Ten known chunks yield a prompt with their unchanged text in order, separated
  only by two newlines, and the complete mandatory prompt/fallback content.
- Invalid question or chunk count/content cannot render a prompt.

## Validation

- `python -m pytest tests/test_search.py --cov=src --cov-report=term-missing --cov-fail-under=90`
- `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`

Record executed results and coverage without adding coverage exclusions.

## Dependencies

- TASK-001 — validated `ChatSettings` and secret-safe configuration error
  boundary.

## Affected Files

- `src/search.py`
- `tests/test_search.py` (new)

## Out of Scope

- Chat completion invocation, CLI loop, README, and live pgVector integration.
