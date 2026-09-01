# Technical Specification — Wave 1: Reproducible Vector Ingestion

**Status:** APPROVED
**Approval record:** 2026-08-30 — explicit human approval; amended
2026-09-01 — explicit human approval
**Scope:** Wave 1 only. This specification implements the ingestion side of
the shared contracts in [Architecture Overview sections 4–8](../../ARCHITECTURE.md).
It does not redefine those contracts or design Wave 2.

## 1. Scope and exclusions

Running `python src/ingest.py` shall load the configured `document.pdf`, create
deterministic character chunks, obtain an OpenAI embedding for every chunk
through LangChain, and replace the configured pgVector collection with the
resulting retrievable corpus.

Included: FR-001 to FR-003; NFR-001 to NFR-004; NFR-006 for Wave 1; and the
infrastructure/configuration portions of CON-001 to CON-004.

Excluded: semantic search, question embeddings, enforcement of retrieval
`k=10`, chat CLI, prompt construction, answer generation, complete README
chat-flow documentation, and all Wave 2 requirements. This artifact creates no
tasks, code, or tests.

## 2. Requirement traceability

| Requirement | Wave 1 design response |
| --- | --- |
| FR-001 / CON-001, CON-003 | `src/ingest.py` remains the executable entry point and loads the one configured PDF, whose delivered value is `document.pdf`. |
| FR-002 | A LangChain character splitter uses `chunk_size=1000`, `chunk_overlap=150`, character length, and no whitespace stripping. |
| FR-003 / NFR-002, NFR-003 | LangChain's OpenAI embedding adapter and `langchain-postgres` persist text and vectors in PostgreSQL with pgVector. |
| NFR-001 / CON-001 | The implementation and tests are Python; the required project structure remains intact. |
| NFR-004 / CON-002 | Docker Compose remains the local PostgreSQL/pgVector mechanism; the application uses configured `DATABASE_URL`, never Compose literals. |
| NFR-006 | Deterministic unit tests, a disposable database integration test, and a 90% project coverage gate are specified below. |
| CON-004 (configuration portion) | The single configured collection is made compatible with later retrieval. `k=10` is explicitly deferred to the Wave 2 retrieval boundary. |

## 3. Current-state context

`src/ingest.py` presently loads dotenv and defines `PDF_PATH`, but its flow is
empty. `search.py` and `chat.py` are Wave 2 placeholders and are not changed by
this scope. `.env.example` contains the required category of settings but also
obsolete Google/Gemini entries. `docker-compose.yml` starts pgVector PostgreSQL
17 and a one-shot `vector` extension bootstrap. `requirements.txt` already has
the runtime LangChain, OpenAI, Postgres, psycopg, pypdf, and dotenv packages;
it has no established test tooling. There are no repository tests.

## 4. Technical design

### 4.1 Components and responsibilities

The Wave 1 implementation may place small helpers beside `ingest.py` or in
focused `src/` modules, but shall maintain these testable boundaries:

| Component | Responsibility |
| --- | --- |
| Configuration loader | Load `.env` at process startup; validate and return the ingestion settings without exposing secrets. |
| PDF/chunk service | Load the configured PDF and produce validated LangChain `Document` chunks. |
| Embedding provider | Construct `langchain_openai.OpenAIEmbeddings` for the approved model. |
| Vector-store adapter | Construct and operate `langchain_postgres.PGVector` for the configured connection and collection. |
| Ingestion orchestrator | Sequence validation, loading, chunking, replacement persistence, and safe command reporting. |
| `ingest.py` | Thin CLI entry point: invoke the orchestrator, print a success summary, and map expected failures to a non-zero exit. |

Provider/store construction belongs behind injected factories or protocols. The
orchestrator must accept replaceable loader, embedder, and store collaborators;
tests must not need OpenAI, Docker, or a live database.

### 4.2 Data flow

1. Load configuration, validate it, resolve `PDF_PATH`, and confirm it is a
   readable regular `.pdf` file before contacting OpenAI or PostgreSQL.
2. Use LangChain `PyPDFLoader` to extract the PDF pages. Concatenate extracted
   page content in document order with a single newline page boundary, producing
   one source document with source metadata `document.pdf`. Fail if the result
   has no non-whitespace text.
3. Split that document with `RecursiveCharacterTextSplitter` configured with
   `separators=[""]`, `chunk_size=1000`, `chunk_overlap=150`,
   `length_function=len`, and `strip_whitespace=False`. This is a character
   window contract: every chunk except a possible final remainder is exactly
   1,000 characters, adjacent full chunks share exactly 150 characters, and
   the final remainder is 1–1,000 characters. Assert these invariants before
   persistence. Chunks must not be silently dropped or trimmed.
4. Attach only non-sensitive operational metadata to every chunk:
   `source` (`document.pdf`), zero-based `chunk_index`,
   `embedding_model` (`text-embedding-3-small`), `chunk_size` (1000), and
   `chunk_overlap` (150). Use stable IDs derived from source plus chunk index.
5. Create the LangChain OpenAI embedder with model
   `text-embedding-3-small`. Create the PGVector store for the configured
   collection, cosine distance, `embedding_length=1536`, and the same
   collection metadata (`embedding_model`, source, chunk parameters). Persist
   all chunk documents through that store, which obtains their embeddings.
6. On success, report the source basename, collection name, and persisted chunk
   count only. The persisted text, vectors, source association, and collection
   name constitute the Wave 1 to Wave 2 handoff.

`embedding_length=1536` is the default dimension of the approved model and is
an intentional compatibility guard. The configured model is not a provider
choice: configuration validation rejects a non-`text-embedding-3-small` value.
The database collection is therefore recreated with one known embedding
dimension and metadata rather than mixing incompatible embeddings.

### 4.3 Reingestion decision

Reingesting replaces, rather than appends to, the configured collection. After
all local configuration, PDF, and chunk-invariant checks pass, the vector-store
adapter uses LangChain PGVector's collection replacement capability
(`pre_delete_collection=True`) and inserts the complete new corpus. Thus a
successful rerun of unchanged input yields the same chunk IDs, metadata, and
single-source searchable corpus without duplicates.

Replacement is not atomic across OpenAI and PostgreSQL. A provider or database
failure after deletion can leave the collection empty or partially populated;
the command reports failure and the operator must correct the dependency and
rerun from the source PDF. This bounded operational decision is appropriate for
the one-document local corpus and does not introduce a second collection,
versioning, or a future product feature.

## 5. Interfaces, persistence, and configuration

The ingestion orchestrator has one logical operation: `ingest(settings) ->
IngestionResult`, where the result has source name, collection name, and chunk
count. It raises typed configuration, source, provider, or persistence errors;
the CLI owns presentation and exit status. The vector-store adapter accepts
validated documents plus the configured collection and returns the persisted
count. It must not implement search or call `chat.py`/`search.py`.

The configured collection is the sole persistent corpus. Its LangChain PGVector
records must preserve `Document.page_content` and its embedding; the metadata
above enables traceability but is not a user-facing citation feature. Wave 2
must connect with the same `DATABASE_URL`, collection name, model, cosine
distance, and compatible 1536-dimensional store, then retrieve from this
collection as defined by Architecture section 7.

Required environment variables and validation:

| Variable | Rule |
| --- | --- |
| `OPENAI_API_KEY` | Required, non-empty secret; pass only to the provider environment/configuration. |
| `OPENAI_EMBEDDING_MODEL` | Required and exactly `text-embedding-3-small`. |
| `DATABASE_URL` | Required non-empty PostgreSQL/psycopg URL; never print the value because it may contain credentials. |
| `PG_VECTOR_COLLECTION_NAME` | Required non-empty logical collection identifier; use unchanged for ingestion and later retrieval. |
| `PDF_PATH` | Required path to the delivered `document.pdf`; resolve relative to the repository working directory and validate before provider/store construction. |

Update `.env.example` to retain these five Wave 1
OpenAI/database/collection/PDF settings with placeholders or safe local
examples; remove Google/Gemini variables and dependencies because they
contradict the approved provider boundary. An explicitly approved downstream
Wave may add its own OpenAI model setting to the shared template, provided it
does not alter the five-setting `IngestionSettings` contract or introduce a
second provider. Retain the current Compose database and extension bootstrap
unless validation reveals a concrete incompatibility. The Wave 1 smoke
procedure requires Compose's PostgreSQL health check and extension bootstrap
to have completed before running ingestion.

## 6. Error and operational behavior

All expected failures terminate `python src/ingest.py` with a non-zero exit,
write one actionable message to stderr, and do not print API keys, passwords,
or credential-bearing URLs. No automatic retry is performed, avoiding unclear
replacement state.

| Failure class | Required behavior |
| --- | --- |
| Missing/invalid configuration | Stop before PDF, OpenAI, or database work; name only the missing/invalid setting. |
| Missing, unreadable, malformed, or textless PDF | Stop before collection replacement; identify the source path safely. |
| Chunk invariant failure | Stop before collection replacement; report an internal ingestion-contract failure. |
| OpenAI authentication, quota, or embedding failure | Stop and report the embedding provider failure without provider payloads or secrets. |
| Database unavailable, extension absent, or persistence failure | Stop and report that PostgreSQL/pgVector persistence failed; state that a failed replacement may require rerun. |

Unexpected exceptions are caught only at the entry point for safe reporting;
tests should preserve their underlying typed cause. Success is reported only
after the store operation completes.

## 7. Validation strategy

Introduce `pytest` and `pytest-cov` as development test dependencies and use a
`tests/` layout. Configure the repository-native test command as
`python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`.
Production `src` modules must be included; relevant code may not be omitted to
inflate coverage.

| Validation | Meaningful evidence |
| --- | --- |
| Unit: configuration | Missing/empty values, wrong embedding model, and unsafe values fail before collaborator construction. |
| Unit: PDF/chunk service | Controlled loader output produces 1,000/150 character windows, correct final remainder, ordered metadata, and failure for empty text. |
| Unit: orchestration | Fakes prove the configured source and collection reach collaborators; success count is reported; each failure avoids subsequent effects and maps to non-zero CLI behavior. |
| Unit: provider/store seams | Fakes verify the approved model, 1536 compatibility guard, cosine store setup, replacement request, stable IDs, and document text/metadata handoff without network calls. |
| Integration: pgVector | In an isolated disposable Compose database, confirm `vector` exists and persisted documents in the configured collection retain retrievable text and embeddings. It must not use production credentials or volume data. |
| Smoke (opt-in) | With real Compose, credentials, and `document.pdf`, run ingestion once and again; confirm no duplicated corpus and successful persisted count. This does not replace automated tests. |

Run applicable import validation after dependency changes and `docker compose
config` for infrastructure changes. There is no current linter or type checker;
do not claim either until one is explicitly configured.

## 8. Risks, assumptions, and implementation boundaries

**Risks/assumptions.** PDF extraction may not preserve visual layout; the
contract is extracted text in page order. OpenAI access, quotas, Docker, and
PostgreSQL/pgVector availability remain external dependencies. Replacement
recovery is rerun-based and can temporarily remove a previously usable corpus.
The current persistent Docker volume makes an isolated integration database
essential. The approved model's 1536 default dimension is assumed by the
configured store and must be verified in the selected LangChain package during
implementation.

**Open technical questions.** None block task decomposition for Wave 1. The
PRD's reingestion (OQ-004) and operational-failure (OQ-001/OQ-005) questions
are resolved locally above for the ingestion command only. CLI termination,
retrieval sufficiency, and question/answer failures remain Wave 2 questions.

**Bounded downstream context.** Tasks for this wave need this document plus
only: Architecture sections 4–8; PRD FR-001–003, NFR-001–004/NFR-006, and
CON-001–004; `src/ingest.py`; `.env.example`; `docker-compose.yml`;
`requirements.txt`; and their directly affected tests. They must not inspect or
implement `search.py`, `chat.py`, prompt policy, or any Wave 2 design.
