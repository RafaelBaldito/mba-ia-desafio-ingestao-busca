# Delivery Plan

**Status:** APPROVED
**Approval record:** 2026-08-30 — explicit human approval

## 1. Delivery Summary

This plan delivers the approved command-line PDF ingestion and grounded
semantic-search experience. The repository already provides the required
Docker Compose database definition, dependency list, environment template, and
the three required Python entry points, but the application entry points are
currently skeletal. Delivery therefore covers completing and validating the
approved behavior rather than replacing the project structure.

## 2. Delivery Mode

**WAVES**

## 3. Decision Rationale

Two incremental delivery waves are appropriate. Vector ingestion and grounded
interactive answering are distinct user-visible capabilities with a strict
dependency: answering cannot be meaningfully demonstrated until a correctly
chunked, embedded corpus is persisted and retrievable. Separating them keeps
each future TECHSPEC focused, isolates integration and external-service risk,
and permits meaningful automated validation of the ingestion contract before
the LLM and CLI behavior are added.

The waves are vertical product slices, not a split by technical layer. Wave 1
delivers a reproducible, searchable corpus; Wave 2 delivers the complete user
question-and-answer flow using that corpus.

## 4. Requirement Coverage

| Approved requirement | Delivery destination |
| --- | --- |
| FR-001 to FR-003 | Wave 1 |
| FR-004 to FR-010 | Wave 2 |
| FR-011 | Wave 2 |
| NFR-001 to NFR-004 | Wave 1, with continued compliance in Wave 2 |
| NFR-005 | Wave 2 |
| NFR-006 | Both waves |
| CON-001 to CON-004 | Wave 1, except the user-facing entry-point completion in Wave 2 |
| CON-005 | Wave 2 |
| CON-006 | Wave 2 |

## 5. Architecture Overview Need

**Recommended.** Before the first detailed TECHSPEC, create a concise global
architecture overview that fixes only the stable shared boundaries: environment
configuration, PostgreSQL/pgVector collection and connection contract,
LangChain/OpenAI provider integration, the handoff from ingestion to retrieval,
and test seams for external services. It must not design either wave in detail.

## 6. Delivery Scopes

### Wave 1 — Reproducible Vector Ingestion

- **Objective:** Make `document.pdf` ingestible into the configured
  PostgreSQL/pgVector service as correctly split, embedded chunks.
- **Included requirements:** FR-001, FR-002, FR-003; NFR-001 to NFR-004;
  applicable structural and configuration portions of CON-001 to CON-004;
  NFR-006 for this scope.
- **Dependencies:** Available Docker/Docker Compose runtime, operational
  PostgreSQL with pgVector, a valid OpenAI API key and embedding configuration,
  and the required `document.pdf`.
- **Boundary:** Does not provide interactive questions, answer generation, or
  README instructions for the complete chat flow.
- **Demonstrable outcome:** After the database is started, running
  `python src/ingest.py` reads the configured PDF, splits it into 1,000-character
  chunks with 150-character overlap, and persists their embeddings so the
  corpus is available for retrieval.

### Wave 2 — Grounded Semantic Chat

- **Objective:** Deliver the end-to-end terminal experience that retrieves the
  relevant corpus content and answers only from that context.
- **Included requirements:** FR-004 to FR-011; NFR-005; CON-005 and CON-006;
  completion of the applicable CLI-facing portions of CON-001 to CON-004; and
  NFR-006 for this scope and the overall project.
- **Dependencies:** Wave 1's persisted vector corpus and shared configuration;
  valid OpenAI chat-model access; an operational pgVector database.
- **Boundary:** Does not add new document sources, UI/API channels, sessions,
  authentication, scalability guarantees, or external knowledge responses.
- **Demonstrable outcome:** A user can follow the README to start the database,
  ingest the PDF, run `python src/chat.py`, ask questions, retrieve exactly ten
  relevant chunks, and receive either a context-grounded answer or the exact
  required absence-of-information message.

## 7. Cross-Cutting Constraints

- Use Python, LangChain, PostgreSQL with pgVector, Docker, Docker Compose,
  `text-embedding-3-small`, and `gpt-5.4-mini` as approved.
- Preserve the mandated prompt rules and exact fallback response:
  `Não tenho informações necessárias para responder sua pergunta.`
- Keep secrets out of the repository; use documented environment configuration.
- Add meaningful automated tests for modified production behavior and maintain
  at least 90% project coverage, alongside applicable repository-native checks.
- Preserve the required repository artifacts, including `docker-compose.yml`,
  `requirements.txt`, `.env.example`, the three `src/` entry points,
  `document.pdf`, and `README.md`.

## 8. Delivery Risks and Dependencies

- Docker, PostgreSQL/pgVector, and OpenAI availability, credentials, quotas,
  and model access are operational dependencies for the corresponding flows.
- Retrieval quality is limited by the source PDF and the semantic relevance of
  its chunks; Wave 2 must validate the required grounded-response behavior
  without treating unsupported inference as an answer.
- The external-service boundaries need test doubles or equivalent isolation so
  the required coverage and behavior tests remain reproducible.
- Reingestion behavior and user-facing error/termination behavior are purposely
  not decided by the approved PRD and must not be silently expanded during
  delivery.

## 9. Open Delivery Questions

The PRD's open questions OQ-001 through OQ-005 remain unresolved. They do not
prevent sequencing the two waves, but must be resolved or explicitly bounded
in the relevant future TECHSPEC before implementation where they affect the
contract: invalid OpenAI credentials, context-sufficiency evaluation, CLI loop
and termination, repeated ingestion, and operational failure behavior.

## 10. Next Planning Boundary

After explicit approval of this plan, the next planning work is the recommended
concise architecture overview, followed by a TECHSPEC for Wave 1 only. No
TECHSPEC, implementation task, or production code is created by this plan.
