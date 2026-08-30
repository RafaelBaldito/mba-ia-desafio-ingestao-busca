# Architecture Overview

## 1. Purpose and Authority

This document defines the small set of stable architectural boundaries shared
by both approved delivery waves. It is a guide for future Wave TECHSPECs, not
an implementation design, task plan, or replacement for the approved PRD and
Delivery Plan.

Authority is applied in this order: explicit user direction, approved PRD,
approved Delivery Plan, this approved architecture overview, repository
constraints, and existing implementation as evidence of the starting point.
In particular, the application remains a Python command-line solution for one
`document.pdf`, using LangChain, PostgreSQL with pgVector, Docker Compose, and
OpenAI (`text-embedding-3-small` and `gpt-5.4-mini`). It does not gain a web
interface, another document source, Gemini support, external-knowledge answers,
or session features through this document.

## 2. Current-State Context

The repository already contains the required structural artifacts:

- `docker-compose.yml` starts a pgVector PostgreSQL 17 service and a one-shot
  extension bootstrap service;
- `.env.example` establishes environment-based configuration and includes
  database, collection, PDF-path, and OpenAI embedding settings;
- `requirements.txt` contains the relevant LangChain, LangChain OpenAI,
  LangChain Postgres, PostgreSQL driver, PDF, and dotenv libraries;
- `src/ingest.py`, `src/search.py`, and `src/chat.py` exist, but currently
  contain only the beginning of the intended interfaces or placeholders.

The existing Compose file and dependency list are starting-state evidence, not
architecture authority if a future Wave TECHSPEC finds them inconsistent with
an approved requirement. Existing Google-related entries are likewise not a
supported product integration: the approved provider boundary is OpenAI only.

## 3. System Boundary and Responsibilities

The product has four runtime roles. Future TECHSPECs may arrange code within
or beside the required entry-point files, but must preserve these boundaries.

| Role | Responsibility | Must not own |
| --- | --- | --- |
| Runtime configuration | Read, validate, and expose non-secret settings needed by a process. | Business flow, embedding, retrieval, or response generation. |
| Ingestion flow | Load the configured PDF, split content, obtain embeddings, and write retrievable chunk records. | User chat loop or answer policy. |
| Retrieval flow | Embed a question and return the ordered, relevant stored chunk content. | Interactive input/output or deciding the answer text. |
| Chat flow | Obtain a question, request retrieval with the mandated count, build the approved prompt, invoke the chat model, and present the result. | Direct database/vector-store details or external knowledge fallback. |

The PostgreSQL/pgVector service and OpenAI APIs are external infrastructure
boundaries. LangChain is the integration abstraction used at the application
side of both boundaries; it is not a substitute for the product's own
responsibility to enforce approved parameters and grounded-answer policy.

The expected high-level flow is:

```text
document.pdf -> ingestion -> chunks + embeddings -> PostgreSQL/pgVector

terminal question -> retrieval (k=10) -> retrieved text context
                  -> approved prompt + OpenAI chat model -> terminal answer
```

No direct path from a terminal question to the chat model may bypass retrieval
when producing a product answer. No answer flow may use a general external
search, an additional corpus, or a conversational-memory store.

## 4. Environment and Configuration Boundary

### 4.1 Configuration contract

Runtime configuration belongs at the process boundary. Each executable reads
configuration before constructing provider or storage integrations and passes
only the settings each downstream component needs. Production code must not
embed credentials, connection strings containing credentials, or developer
machine paths.

The stable configuration categories are:

| Category | Required contract | Current repository evidence |
| --- | --- | --- |
| OpenAI authentication | A secret API key is supplied only through the runtime environment. | `OPENAI_API_KEY` is templated in `.env.example`. |
| Embedding provider | The approved embedding model is `text-embedding-3-small`. | `OPENAI_EMBEDDING_MODEL` is templated with that value. |
| Chat provider | The answer-generation model is `gpt-5.4-mini`. | The PRD defines it; the current template does not yet expose a chat-model setting. |
| Database | A PostgreSQL connection location is supplied by configuration, not inferred from code. | `DATABASE_URL` is templated. |
| Vector namespace | The target logical collection is explicitly named in configuration. | `PG_VECTOR_COLLECTION_NAME` is templated. |
| Source document | The PDF input path is configurable; the approved delivered corpus is `document.pdf`. | `PDF_PATH` is templated and `document.pdf` is present at repository root. |

Future TECHSPECs may decide the exact settings object, validation library, and
whether model identifiers are read directly or given approved defaults. They
must keep the above semantic contract and document all required variables in
the README and `.env.example`. They must also reconcile obsolete Google/Gemini
configuration entries with the approved OpenAI-only scope rather than treating
them as a second provider option.

### 4.2 Configuration lifecycle and failures

Configuration loading is a startup concern. A missing, empty, or unusable
required setting must stop the affected command before external work begins and
report an actionable, credential-safe failure. It must never print a secret.
The exact wording, exception model, and recovery interaction remain local
decisions for the relevant Wave TECHSPEC because the PRD deliberately leaves
operational error behavior open.

`docker-compose.yml` owns local database-service configuration. Application
processes consume the database endpoint through the application configuration
contract; they do not rely on a container name, fixed local port, user, or
password embedded in application logic. Development defaults in Compose are
not production secrets.

## 5. PostgreSQL and pgVector Boundary

### 5.1 Connection and lifecycle contract

PostgreSQL with the `vector` extension is the sole persistent vector store for
the product. Docker Compose is the supported local mechanism for making that
service available. The database must be ready and the vector extension enabled
before an ingestion or retrieval operation uses the store. The existing
bootstrap service is consistent with this prerequisite, but its exact
operational implementation remains infrastructure detail for the Wave 1
TECHSPEC.

Application components connect through the configured database URL. They do
not create an alternate database backend or a separate local on-disk vector
index. Connection, transaction, pooling, and schema/collection initialization
mechanisms are intentionally deferred to the Wave TECHSPECs, provided the
following persistence contract holds.

### 5.2 Collection contract

One explicitly configured logical collection identifies the searchable corpus
for this initial product. Ingestion writes chunk records to that collection;
retrieval reads from the same configured collection. A stored record must
preserve, at minimum:

- the chunk text that can be supplied to the answer context;
- an embedding produced by the approved embedding provider;
- the association needed for vector similarity retrieval within the configured
  collection.

Optional document metadata (for example source filename, page, or chunk
ordinal) may be retained when it supports operational traceability. It is not
a new user-facing citation requirement. The storage representation, LangChain
collection schema, identifiers, and metadata fields are implementation choices
for Wave 1 as long as they remain compatible with Wave 2 retrieval.

The collection must be compatible with the configured embedding model's vector
dimension. The model and existing collection cannot be changed independently
without an intentional compatibility check. This is a persistence invariant,
not a request to support multiple embedding models.

The PRD does not define reingestion semantics. This overview therefore does
not choose append, replace, deduplicate, or versioned behavior. A future
Wave 1 TECHSPEC must explicitly surface and resolve or bound that behavior
before implementation; it must not silently alter the corpus contract.

## 6. LangChain and OpenAI Provider Boundary

LangChain provides the application-facing adapters for PDF loading/text
splitting, OpenAI embeddings, PostgreSQL/pgVector vector storage and retrieval,
and OpenAI chat invocation. Provider-specific construction and invocation must
be isolated from the CLI orchestration so that the latter remains testable
without network calls.

The stable provider contracts are:

- **Embedding adapter:** accepts text chunks or a query text and yields vectors
  using OpenAI's approved `text-embedding-3-small` model.
- **Vector-store adapter:** accepts chunks for persistence and accepts a query
  representation for similarity retrieval from the configured collection.
- **Chat-model adapter:** accepts the fully rendered approved prompt and yields
  answer text using OpenAI's approved `gpt-5.4-mini` model.

The mandatory prompt rules are an application policy, not a behavior delegated
to a model default. The prompt passed to the chat adapter must contain the
retrieved context and user question, preserve the PRD's mandatory instructions
and examples, and request the exact fallback sentence when the information is
not explicitly present. Model output must not be supplemented by application
knowledge, another model/provider, or a web search.

The specific LangChain class names, chain composition, synchronous/asynchronous
execution, retry configuration, and message representation are not global
architecture decisions. They belong in the smallest future TECHSPEC that needs
them.

## 7. Ingestion-to-Retrieval Handoff

The handoff is the persisted, searchable chunk corpus; ingestion does not call
the chat flow, and the chat flow does not need to know how the PDF was parsed.
The shared compatibility contract is:

1. Ingestion treats the configured PDF as the only source and creates text
   chunks using the approved 1,000-character size and 150-character overlap.
2. Each persisted chunk includes its retrievable text and approved-model
   embedding in the configured collection.
3. Retrieval receives a user question and queries that same collection using
   the question embedding.
4. Retrieval returns the ten most relevant chunk texts in relevance order for
   context construction. The exact `k=10` rule is owned and enforced at the
   retrieval boundary, rather than left to the caller or a library default.
5. Chat concatenates the returned chunk text as the context for the approved
   prompt; it must not introduce unseen content while constructing context.

This contract lets Wave 1 demonstrate a usable corpus without designing the
CLI, while Wave 2 can rely on a bounded retrieval interface without duplicating
ingestion or persistence logic. It does not prescribe public function names,
data classes, or a module layout beyond the required entry points.

## 8. Test Seams and Validation Boundaries

External effects must be behind replaceable boundaries. Future implementation
must make it possible to test orchestration with controlled doubles for:

| External effect | Required seam | Core behavior validated without the live service |
| --- | --- | --- |
| PDF read | Document-loading input | Configured-source handoff and chunking contract. |
| OpenAI embeddings | Embedding adapter | Text/query passed to the correct provider boundary. |
| pgVector persistence and search | Vector-store adapter | Writes use the configured collection; retrieval requests exactly `k=10`; returned order and context handoff. |
| OpenAI chat completion | Chat-model adapter | Mandatory prompt composition and terminal answer handling. |
| Terminal I/O | CLI input/output boundary | Question-loop behavior and displayed output. |

Unit tests should exercise approved behavior through these seams without real
OpenAI credentials, network access, or a user-managed database. Database
integration tests should separately verify the pgVector connection/collection
contract in an isolated, disposable environment when the repository's test
tooling establishes that capability. An end-to-end smoke flow may use the real
operational dependencies only when explicitly configured; it is not a
substitute for deterministic automated tests.

The repository requires meaningful tests and at least 90% project coverage.
The choice and configuration of test runner, coverage tool, fixtures, and
commands are intentionally a future TECHSPEC concern because none are currently
established. Future scopes must define them before implementation and must not
exclude relevant production behavior merely to meet the threshold.

## 9. Cross-Cutting Operational and Security Boundaries

- Secrets remain in environment configuration outside version control;
  `.env.example` contains placeholders only.
- Logs and user-facing failures may name a failing dependency or configuration
  key but must not expose API keys, passwords, or full credential-bearing URLs.
- The system is bounded to a local operator's configured PDF and database;
  it makes no availability, scaling, performance, multi-user, or session
  guarantee beyond the PRD.
- Failure messages, retry behavior, CLI termination, context-sufficiency
  heuristics, and reingestion semantics are not defined here. They are open
  product/technical decisions to be resolved only where the approved scope
  requires them.

## 10. Guidance for Future Wave TECHSPECs

Wave 1 should detail the ingestion and persistence side of Sections 4–7,
including the required chunking and the unresolved reingestion/error behavior.
Wave 2 should detail the retrieval, prompt, and CLI side while conforming to
the collection and retrieval contracts above. Neither scope may revise these
global boundaries or absorb requirements assigned to the other wave without an
approved upstream change.

This overview intentionally leaves implementation structure, library APIs,
schema specifics, command behavior, and task decomposition to just-in-time
Wave TECHSPECs.
