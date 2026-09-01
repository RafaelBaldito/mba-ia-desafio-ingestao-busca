# TASK-004 — Deliver the Repeatable Chat CLI and Operator Guide

## Objective

Expose the approved answer service through a safe repeatable terminal loop and
document the complete reproducible operator workflow.

## Scope

- Complete `python src/chat.py` startup/bootstrap and injectable CLI loop.
- Extend the chat unit tests for terminal behavior.
- Replace the README placeholder with the Wave 2 setup, ingest, chat, and
  exit guidance.

## Context

### Required

- `docs/waves/2-grounded-semantic-chat/TECHSPEC.md` — §§4.1, 4.6, 5–7
- `src/chat.py` and `tests/test_chat.py` from TASK-003
- `README.md`, `.env.example`, and `src/ingest.py`

### Optional

- `docs/ARCHITECTURE.md` — §§3–4, 8–9
- `docs/PRD.md` — FR-005, FR-011, NFR-005, CON-001–CON-003, CON-006

## Requirements

- Use the direct-script import bootstrap pattern established by `src/ingest.py`
  so `python src/chat.py` works from the repository root without installation.
- At startup, load settings and construct replaceable collaborators before
  reading input. Invalid configuration emits one actionable credential-safe
  stderr message and exits non-zero.
- Implement the exact prompt/output protocol in TECHSPEC §4.6: start banner,
  `PERGUNTA: ` input prompt, blank-question message, `RESPOSTA: {texto}` for
  each successful independent question, and safe termination for `sair`,
  `exit`, `quit`, EOF, and `KeyboardInterrupt`.
- Map expected retrieval/model failures to the exact safe retry message on
  stderr and continue with the next question. Catch unexpected exceptions only
  at the CLI boundary using the specified safe startup/per-question behavior.
- Document Python/Docker Compose/OpenAI prerequisites; copying `.env.example`;
  Docker startup/readiness; ingestion; chat execution; one grounded and one
  fallback interaction; exit commands; required prior ingestion of
  `document.pdf`; and the release-time requirement that the repository be
  public on GitHub.

## Constraints

- No session/history, external knowledge, web/API/UI channel, automatic retry,
  reingestion, Docker change, or external GitHub publication action.
- Never print a key, credential-bearing URL, prompt, retrieved text, raw
  provider exception, or traceback.
- README must not imply that an unavailable collection with fewer than ten
  chunks can produce an answer.

## Acceptance Criteria

- Injectable input/output tests demonstrate multiple successive independent
  questions, success, display of the literal fallback, blank input, all exit
  commands, EOF, and interrupt behavior without real external services.
- Startup configuration failure terminates before input; expected per-question
  retrieval/model failures print only the prescribed safe stderr message and
  continue; unexpected failures remain bounded at the CLI boundary.
- `python src/chat.py` is importable/executable from the repository root under
  the established direct-script pattern.
- README gives a reproducible Docker → ingest → chat sequence and all required
  chat/operator information; `.env.example` remains the safe configuration
  template established in TASK-001.

## Validation

- `python -m pytest tests/test_chat.py`
- `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`
- `python -c "import src.search; import src.chat"`
- `docker compose config`

**Validation amendment approval:** 2026-09-01 — explicit human approval.
The targeted CLI test and project-wide coverage commands above replace the
previous incoherent targeted-coverage command.

Run only applicable commands and record actual outcomes. Do not perform the
credentialed manual smoke test as a substitute for automated validation.

## Dependencies

- TASK-001 — startup configuration and `.env.example` contract.
- TASK-002 — retrieval/prompt boundary.
- TASK-003 — answer operation and typed failures.

## Affected Files

- `src/chat.py`
- `tests/test_chat.py`
- `README.md`

## Out of Scope

- pgVector integration test implementation, real-provider smoke execution,
  public-repository publication, and changes to Wave 1 ingestion or Compose.
