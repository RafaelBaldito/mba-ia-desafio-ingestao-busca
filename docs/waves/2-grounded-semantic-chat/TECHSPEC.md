# Technical Specification — Wave 2: Grounded Semantic Chat

**Status:** APPROVED  
**Approval record:** 2026-08-31 — explicit human approval; amended
2026-09-01 — explicit human approval
**Scope:** Wave 2 only. This specification implements the retrieval, grounded
answering, and terminal-chat side of the contracts in
[`docs/ARCHITECTURE.md`](../../ARCHITECTURE.md). It neither changes the Wave 1
ingestion/persistence design nor designs subsequent work.

## 1. Scope and prerequisites

Wave 2 delivers the end-to-end terminal flow: receive a question, retrieve the
ten most relevant persisted chunks, concatenate their text into the mandated
prompt, invoke OpenAI `gpt-5.4-mini`, and show a grounded answer or the exact
fallback sentence.

Included requirements are FR-004 through FR-011, NFR-005, NFR-006, CON-005,
CON-006, and the CLI-facing completion of CON-001 through CON-004. In
particular, `src/search.py` owns retrieval and `src/chat.py` owns the terminal
interface; `README.md` and `.env.example` complete the reproducible operator
flow. The existing required repository structure remains intact.

Excluded are PDF ingestion/reingestion behavior, another corpus or provider,
web/API/UI channels, sessions/history, authentication, direct external search,
availability/scaling guarantees, and any change to the Docker database,
collection schema, or Wave 1 chunking contract.

### 1.1 Verified entry conditions

This design relies on the approved Wave 1 handoff and records the evidence
checked before its creation:

| Prerequisite | Evidence | Result |
| --- | --- | --- |
| Product requirements approved | `docs/PRD.md` is `APPROVED`, with explicit human approval dated 2026-08-30. | Satisfied |
| Delivery strategy and selected scope approved | `docs/DELIVERY-PLAN.md` is `APPROVED`, uses `WAVES`, and assigns this scope to Wave 2. | Satisfied |
| Shared architecture available | `docs/ARCHITECTURE.md` is `APPROVED` for Wave 2 planning. | Satisfied |
| Vector corpus available | The healthy `postgres_rag` pgVector service contains collection `wave1_smoke` with 54 persisted chunk records. | Satisfied |
| Corpus compatible with retrieval | Collection metadata identifies `text-embedding-3-small`, `document.pdf`, chunk size 1000 and overlap 150; all stored embeddings are 1536-dimensional. The active configuration names the same collection and embedding model. | Satisfied |

The runtime still validates its configured dependencies for each invocation; the
table above is planning evidence, not a substitute for operational checks.

## 2. Requirements traceability

| Requirement | Wave 2 design response |
| --- | --- |
| FR-004, FR-006, CON-004 | `src/search.py` embeds the question through the OpenAI/LangChain adapter and calls pgVector similarity search with the literal, non-configurable `k=10`. It returns the relevance-ordered ten chunks or a typed retrieval failure. |
| FR-005; CLI portions of CON-001 | `src/chat.py` is the directly executable, repeatable terminal interface and delegates all retrieval/model work to injected collaborators. |
| FR-007 | The answer service concatenates only the ten returned `Document.page_content` values, in retrieval order, separated by two newlines. |
| FR-008, CON-005 | The rendered prompt preserves the brief's mandatory headings, rules, three examples, user-question section, and exact fallback literal. It is the sole input to the chat model. |
| FR-009 | No answer path bypasses retrieval or adds memory, web results, metadata, scores, or application knowledge to the context/prompt. The chat model receives the approved prompt only. |
| FR-010 | The prompt requires the exact fallback sentence whenever the required information is not explicit in context; that literal is also the only application fallback for an empty normalized model answer. |
| FR-011, NFR-005, CON-002, CON-006 | README documents the reproducible Docker → ingest → chat sequence and configuration; `.env.example` documents safe placeholders, including the chat-model setting. Release verification confirms the repository is public. |
| NFR-006 | Deterministic unit and isolated pgVector integration tests cover the changed behavior; the repository-wide `src` coverage gate remains at least 90%. |

## 3. Current-state and Wave 1 handoff

`src/search.py` currently contains the required prompt text but has an empty
entry function. `src/chat.py` is a placeholder. Wave 1 provides a configurable
PostgreSQL/pgVector collection of LangChain documents whose text, cosine
similarity configuration, `text-embedding-3-small` embeddings, and 1536
dimensions are the retrieval contract. `pytest` and `pytest-cov` are already
listed in `requirements.txt`, and `pytest.ini` establishes `tests/` and the
`src` import path.

Wave 2 shall consume the same `DATABASE_URL`,
`PG_VECTOR_COLLECTION_NAME`, and `OPENAI_EMBEDDING_MODEL` as Wave 1. It shall
not create, delete, replace, migrate, or reingest the collection. A configured
collection with fewer than ten results is not a valid answer context for this
Wave: it is a safe retrieval failure, not an opportunity to silently use fewer
chunks or to ask the model without retrieval.

## 4. Technical design

### 4.1 Components and responsibilities

| Component | Responsibility | Must not do |
| --- | --- | --- |
| `src/chat_config.py` | Load and validate only chat/retrieval runtime settings, without exposing secrets. | Load PDFs, query pgVector, run the terminal loop, or generate answers. |
| `src/search.py` | Construct the OpenAI embedding and pgVector retrieval adapters; retrieve exactly ten ordered chunks; render the mandatory prompt from supplied chunks and question. | Print/read terminal I/O, mutate the collection, or invoke the chat model. |
| `src/chat.py` | Orchestrate one question through retrieval → prompt → chat model and provide the repeatable CLI loop. | Directly access pgVector or add external knowledge. |
| Chat-model adapter | Invoke LangChain `ChatOpenAI` with `gpt-5.4-mini` and return normalized text. | Construct context, decide search `k`, or use tools/memory. |

Small helper modules are permitted only when they preserve these boundaries and
test seams. `src/chat.py` must include the same direct-script import bootstrap
pattern as `src/ingest.py`, so `python src/chat.py` works from the repository
root without requiring an installation step.

### 4.2 Runtime configuration

Create an immutable `ChatSettings` value loaded before creating an embedding,
store, or chat model. It validates required non-empty values and rejects
control characters. Error messages may name a setting or dependency but never
include a key, password, credential-bearing URL, provider payload, prompt, or
retrieved text.

| Variable | Required rule |
| --- | --- |
| `OPENAI_API_KEY` | Required secret; supplied to LangChain/OpenAI only. |
| `OPENAI_EMBEDDING_MODEL` | Required and exactly `text-embedding-3-small`. |
| `OPENAI_CHAT_MODEL` | Required and exactly `gpt-5.4-mini`. |
| `DATABASE_URL` | Required valid PostgreSQL/psycopg URL; never print it. |
| `PG_VECTOR_COLLECTION_NAME` | Required non-empty safe logical identifier; it must be the Wave 1 collection. |

The chat configuration intentionally does not require `PDF_PATH`: Wave 2
queries the already persisted corpus. It may share the existing approved
embedding-model constant, but does not alter Wave 1 validation semantics.

### 4.3 Retrieval interface: exactly ten chunks

`src/search.py` shall expose one testable logical operation equivalent to:

```text
retrieve(question: str, settings: ChatSettings) -> tuple[RetrievedChunk, ...]
```

`RetrievedChunk` contains the original `Document.page_content` and its numeric
similarity score for internal ordering/diagnostics; scores and metadata are not
included in the answer context. The operation contract is:

1. Trim and validate that `question` is non-empty before provider or database
   construction.
2. Construct `OpenAIEmbeddings` with only the approved embedding model and
   supplied API key.
3. Connect a LangChain `PGVector` adapter to the configured existing
   collection using cosine distance and `embedding_length=1536`, matching the
   Wave 1 persistence invariant.
4. Invoke `similarity_search_with_score(question, k=10)`. This operation
   produces the question vector through the configured embedding adapter and
   performs the pgVector search.
5. Preserve the adapter's returned relevance order exactly. Require ten pairs,
   a text `Document`, non-empty `page_content`, and a numeric score for every
   pair; return an immutable tuple of ten `RetrievedChunk` values.

Any configuration, embedding construction, connection, provider, result-shape,
or database failure raises a typed `RetrievalError` with a credential-safe
message. A result count other than ten is also `RetrievalError`; the caller
must not call the model in that case. This enforces the approved `k=10`
contract rather than treating it as a library default.

### 4.4 Context and mandatory prompt

`build_prompt(question, chunks)` accepts only a validated non-empty question
and exactly ten `RetrievedChunk` values. It joins their `page_content` in the
same relevance order with `\n\n`. It does not trim, summarize, rank again,
deduplicate, add scores, add source metadata, or add unseen text.

The resulting prompt is normative and must be byte-for-byte equivalent in
content (apart from replacement of the two placeholders) to this UTF-8 text:

```text
CONTEXTO:
{resultados concatenados do banco de dados}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta do usuário}

RESPONDA A "PERGUNTA DO USUÁRIO"
```

The literal fallback constant is:

```text
Não tenho informações necessárias para responder sua pergunta.
```

The application sends the complete rendered prompt as the sole chat-model
input. It does not add a system prompt, conversation history, function/tool
calls, web-search results, or a second corpus. The context is the only source
of answerable factual content.

### 4.5 Answer orchestration and model invocation

The answer operation is logically:

```text
answer(question, settings) -> str
  = retrieve(question, settings)
  -> build_prompt(question, ten chunks)
  -> ChatOpenAI(model="gpt-5.4-mini").invoke(rendered prompt)
  -> normalized answer text
```

The model is constructed with `ChatOpenAI`, the validated OpenAI key, and the
validated literal model identifier `gpt-5.4-mini`. The implementation must not
substitute another model, silently fall back to another provider, or use a
model-side tool. The adapter accepts only a textual completion. A blank or
whitespace-only completion is normalized to the literal fallback above; a
non-text completion, an invocation exception, or an invalid provider response
is a typed `ChatModelError` and is not presented as a grounded answer.

The requirement for a context-grounded answer is enforced by the mandatory
prompt and the absence of every other answer input. No relevance score
threshold or answer-rewriting heuristic is introduced: neither is approved,
and a heuristic could reject information that is explicit in the retrieved
context. The model must therefore emit the literal fallback whenever the
necessary information is not explicit in those ten chunks.

### 4.6 CLI behavior

`python src/chat.py` loads `ChatSettings`, constructs replaceable retrieval and
model collaborators, and then runs this terminal loop:

1. Print `Faça sua pergunta:` when the chat starts.
2. Read a line at the `PERGUNTA: ` prompt.
3. A trimmed, case-insensitive `sair`, `exit`, or `quit` ends the loop, prints
   `Chat encerrado.`, and returns exit status 0. EOF and `KeyboardInterrupt`
   have the same safe termination behavior (with a preceding newline when
   necessary).
4. For blank input, print `Informe uma pergunta não vazia.` and continue; do
   not perform retrieval or call the model.
5. For a valid question, call the answer operation and print exactly
   `RESPOSTA: {texto}`. The loop then accepts the next question; no prior
   question or answer is sent with it.
6. For an expected retrieval or chat-model failure, print the safe message
   `Não foi possível responder à pergunta. Verifique a disponibilidade do banco e da OpenAI e tente novamente.` to stderr and continue to the next question. Do not print the prompt, chunk text, stack trace, or secret.

If configuration is invalid at startup, print one actionable credential-safe
message to stderr and terminate non-zero before reading input. An unexpected
exception is caught only at this CLI boundary, emits
`Não foi possível iniciar ou continuar o chat.`, and follows the same safe
startup/per-question rule. Per-question failure continues; startup failure
terminates. The literal absence-of-information fallback is a successful answer,
not an operational error.

## 5. Documentation and deliverable updates

Implementation in this wave updates only the directly affected documentation:

- `.env.example` adds `OPENAI_CHAT_MODEL='gpt-5.4-mini'`, retains only
  placeholders/safe non-secret examples, and documents the existing OpenAI,
  database, collection, and PDF settings consistently. This is an approved
  Wave 2 extension of the shared template, not a change to Wave 1's five
  `IngestionSettings` values or validation semantics. It must not add Gemini
  settings.
- `README.md` documents prerequisites (Python environment, Docker Compose,
  OpenAI key), copying `.env.example` to `.env`, `docker compose up -d`,
  waiting for the database/extension readiness, `python src/ingest.py`, and
  `python src/chat.py`. It gives one grounded and one fallback interaction,
  names the exit commands, and explains that the supplied PDF must be ingested
  before chat.
- The README states that the delivery repository must be public on GitHub.
  This is a release/operator verification item; Wave 2 does not attempt an
  external publication action.

No dependency change is required by this design: the established LangChain,
LangChain OpenAI, LangChain Postgres, psycopg, dotenv, pytest, and pytest-cov
dependencies are sufficient.

## 6. Error handling, security, and operations

| Condition | Required behavior |
| --- | --- |
| Missing/invalid runtime setting | Stop at startup with non-zero status and a safe message that names the setting only. |
| pgVector unavailable, wrong collection, incompatible vector dimension, embedding failure, or fewer/malformed search results | Raise `RetrievalError`; do not invoke the chat model; CLI emits the safe retry message and continues. |
| OpenAI chat authentication, quota, network, provider, or invalid-response failure | Raise `ChatModelError`; do not fabricate an answer or use another provider; CLI emits the safe retry message and continues. |
| Model returns empty text | Emit the exact fallback literal as a successful answer. |
| Question lacks an explicit answer in valid context | The prompt requires the exact fallback literal as a successful answer. |

Secrets stay in environment variables and are redacted from data-class
representations, errors, logs, and CLI output. The implementation must not log
the API key, `DATABASE_URL`, retrieved document content, complete prompt, or
raw provider exception. It must also not retry automatically: a retry can hide
quota/authentication failures and makes terminal behavior less predictable.

## 7. Validation strategy

All new/modified production behavior requires meaningful automated tests. The
repository-native gate is:

```bash
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90
```

It covers the complete `src` package; no relevant production module may be
omitted to inflate coverage. Implementations must run the command using the
project's configured Python environment and record its successful result before
task review. Existing ingestion tests remain part of the project-wide gate.

| Test layer | Required behavior and seams |
| --- | --- |
| Unit — configuration | Required/malformed chat settings, exact model identifiers, safe representations, and failure before factory creation. |
| Unit — retrieval | Fake embedding/store factories prove query handoff, cosine/1536/store configuration, literal `k=10`, order preservation, exactly-ten validation, and secret-safe typed failures. |
| Unit — prompt | Ten known chunks produce ordered concatenated context and every mandatory rule/example/question section; invalid count or blank text cannot render a prompt. |
| Unit — answer adapter | Fake `ChatOpenAI` receives only the rendered prompt and `gpt-5.4-mini`; textual output is returned, blank output uses the exact fallback, and provider/shape failures are typed. |
| Unit — CLI | Injectable input/output and answer service cover multiple successive questions, successful answer, exact fallback display, blank input, each exit mode, EOF/interrupt, startup configuration failure, and recoverable per-question failures without secret/prompt leakage. |
| Integration — pgVector | Extend the existing isolated disposable Compose test to seed at least ten 1536-dimensional documents in one collection, retrieve with the Wave 2 adapter, and verify ten ordered text records are returned. It must not touch the persistent local `postgres_data` volume or require OpenAI credentials. |
| Manual opt-in smoke | With valid operator credentials and the persisted `document.pdf` corpus, run the README sequence, ask one PDF-grounded question and one out-of-context/opinion question, verify ten-chunk retrieval and the exact fallback, then terminate normally. This supplements, never replaces, automated tests. |

Run applicable direct import validation for `src.search` and `src.chat`, and
`docker compose config` if documentation/configuration changes require checking
the Compose invocation. No linter or type checker is currently configured; do
not claim either until the repository establishes it.

## 8. Risks, assumptions, and open technical questions

### Risks and assumptions

- The deployed OpenAI account must have access to `gpt-5.4-mini`; configuration
  validation cannot prove entitlement, so invocation failures remain safe and
  recoverable in the CLI.
- The configured collection is assumed to remain the Wave 1 collection with at
  least ten non-empty chunks and 1536-dimensional
  `text-embedding-3-small` vectors. A changed collection/configuration fails
  safely rather than mixing embedding spaces.
- Prompting constrains the model and the application supplies no external
  context, but groundedness quality still depends on semantic retrieval and
  provider compliance. The tests verify the enforced input boundary and exact
  fallback contract, not a claim that any model can prove factual entailment.
- The static one-PDF corpus is trusted project input. This wave does not add a
  general prompt-injection mitigation layer or a source-content policy beyond
  the approved prompt, because such a new policy would alter the defined
  prompt behavior.
- Public GitHub availability is outside local code execution and must be
  checked at release time.

### Open technical questions

No question blocks task decomposition. The following decisions are deliberately
bounded for this Wave:

| Question | Wave 2 decision |
| --- | --- |
| OQ-001/OQ-005: invalid credentials or provider/database failure | Safe startup failure for invalid settings; safe, recoverable per-question failure for retrieval/model operations, with no automatic retry or secret disclosure. |
| OQ-002: context sufficiency | Do not invent a score threshold. The exact mandatory prompt directs `gpt-5.4-mini` to emit the literal fallback unless the answer is explicit in the ten-chunk context. |
| OQ-003: repeated questions and termination | The loop accepts independent successive questions; `sair`, `exit`, `quit`, EOF, and interrupt terminate safely as specified in §4.6. |
| OQ-004: reingestion | Remains wholly owned by Wave 1 and is not modified by this scope. |

## 9. Implementation boundaries and context surface

Downstream implementation tasks should need this TECHSPEC; Architecture
sections 3–8; PRD FR-004–FR-011, NFR-005–NFR-006 and CON-001–CON-006; the
current `src/search.py`, `src/chat.py`, `src/ingestion_config.py`, and
`src/ingestion_store.py`; `.env.example`, `README.md`, `pytest.ini`; and their
direct tests. They must not redesign ingestion, compose infrastructure,
collection persistence, or a future delivery scope.

The scope has a bounded context surface: retrieval, prompt/model orchestration,
CLI, configuration, and directly affected documentation/tests are cohesive
within the single user-visible Wave 2 outcome. No implementation tasks, code,
or future-wave design are created by this specification.
