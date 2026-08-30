# TASK-003 — Implement Embedding and pgVector Persistence Adapters

## Objective

Implement injectable LangChain adapters that create the approved embedding and
pgVector collection configuration, then replace and persist the validated
chunk corpus with stable IDs.

## Scope

- Add a focused `src/ingestion_store.py` adapter module, typed provider and
  persistence errors, and factory/protocol seams.
- Add deterministic unit tests that inspect adapter inputs via fakes rather
  than contacting OpenAI or PostgreSQL.

## Context

### Required

- `docs/waves/1-reproducible-vector-ingestion/TECHSPEC.md` — §§4.1–4.3, §5–7
- `src/ingestion_config.py` and `src/ingestion_document.py`
- `requirements.txt`

### Optional

- `docs/ARCHITECTURE.md` — §§5–8

## Requirements

- Construct `langchain_openai.OpenAIEmbeddings` using only the validated
  `text-embedding-3-small` model and provider configuration; surface a typed,
  credential-safe provider failure.
- Construct `langchain_postgres.PGVector` for the configured database URL and
  collection with cosine distance, `embedding_length=1536`, and collection
  metadata containing the approved model, source, chunk size, and overlap.
- Persist all supplied chunk documents through the store with
  `pre_delete_collection=True`, so a successful reingestion replaces instead
  of appending to the single configured collection.
- Generate stable IDs exclusively from source plus zero-based chunk index, and
  preserve each document's page content and approved metadata through the
  store handoff. Return the persisted count.
- Verify the selected installed `langchain-postgres` API supports the approved
  replacement and compatibility arguments before finalizing the adapter;
  adapt only call syntax, not the approved semantics.

## Constraints

- The adapter must not implement search, call `search.py` or `chat.py`, use a
  second collection, support alternate embedding models, or attempt atomic
  recovery/versioning.
- Do not log or expose provider payloads, API keys, passwords, or complete
  credential-bearing connection URLs.
- Keep provider/store factories replaceable so orchestration tests remain
  network- and Docker-free.

## Acceptance Criteria

- Fakes show the approved model, cosine distance, 1536-dimension guard,
  configured collection/database connection, collection metadata, replacement
  request, and complete document/ID handoff reach the appropriate LangChain
  seam.
- A rerun request uses replacement semantics rather than an append operation.
- Stable IDs and persisted count are deterministic for identical source chunks.
- Provider and persistence failures remain typed and secret-safe for the CLI
  layer to handle later.

## Validation

- `python -m pytest tests/test_ingestion_store.py --cov=src --cov-report=term-missing --cov-fail-under=90`
- `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`
- `python -c "import ingestion_store"`

Record the inspected package/API version and test evidence. Do not use a real
OpenAI key or a live database in this task.

## Dependencies

- TASK-001 — validated settings and test foundation.
- TASK-002 — validated chunks and metadata contract.

## Affected Files

- `src/ingestion_store.py` (new)
- `tests/test_ingestion_store.py` (new)
- directly affected test fixtures under `tests/`

## Out of Scope

- PDF parsing/chunk-policy changes, command-line presentation, actual database
  integration, retry/recovery behavior, retrieval, and chat.
