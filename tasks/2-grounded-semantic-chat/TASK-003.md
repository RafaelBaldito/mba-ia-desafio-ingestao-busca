# TASK-003 — Implement Grounded Answer Orchestration

## Objective

Implement the one-question answer service that chains required retrieval and
prompt construction to the sole approved `gpt-5.4-mini` chat-model input.

## Scope

- Add the injectable answer operation and `ChatModelError` to `src/chat.py`
  (or a narrowly scoped helper that preserves its ownership).
- Add deterministic unit tests for the model adapter and answer orchestration.

## Context

### Required

- `docs/waves/2-grounded-semantic-chat/TECHSPEC.md` — §§4.1, 4.5, 6–7
- `src/search.py` and its tests from TASK-002
- `src/chat_config.py` from TASK-001

### Optional

- `docs/ARCHITECTURE.md` — §§3, 6, 8–9
- `docs/PRD.md` — FR-008–FR-010 and CON-005

## Requirements

- Implement the logical chain `retrieve → build_prompt → ChatOpenAI.invoke`
  for one valid question, using injected retrieval and model collaborators.
- Construct `ChatOpenAI` only with the validated API key and the literal
  approved `gpt-5.4-mini` model. Send the fully rendered prompt as its sole
  input; do not add a system message, history, tools, web results, metadata,
  scores, or another corpus.
- Accept only textual completions. Return non-blank text normalized for the
  specified adapter contract; normalize blank/whitespace-only text to the
  exact absence-of-information fallback literal.
- Map model-construction, invocation, non-text, and invalid-response failures
  to a credential-safe `ChatModelError`. Let `RetrievalError` prevent model
  construction/invocation rather than fabricating an answer.

## Constraints

- No automatic retry, alternate model, alternate provider, answer rewrite, or
  answer-sufficiency heuristic is permitted.
- This task does not implement terminal input/output; collaborators must keep
  the answer operation testable without a live provider.
- Do not expose the prompt, chunk text, raw provider payload, key, or database
  URL in errors or normal output.

## Acceptance Criteria

- Fake collaborators prove retrieval precedes prompt rendering and that the
  fake `ChatOpenAI` receives exactly one value: the rendered mandatory prompt.
- Tests prove `gpt-5.4-mini` is used, non-empty textual output is returned,
  and blank output returns the exact fallback literal as a successful answer.
- Retrieval failure never calls the chat-model factory or invoker; provider,
  shape, and non-text failures are typed, safe `ChatModelError` values.
- Unit tests require no OpenAI credentials, network, Docker, or pgVector
  service.

## Validation

- `python -m pytest tests/test_chat.py --cov=src --cov-report=term-missing --cov-fail-under=90`
- `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`

Record executed results and coverage without excluding the new production code.

## Dependencies

- TASK-001 — chat settings.
- TASK-002 — retrieval contract, prompt renderer, `RetrievalError`, and fallback constant.

## Affected Files

- `src/chat.py`
- `tests/test_chat.py` (new)

## Out of Scope

- Terminal-loop behavior, direct-script bootstrap, README updates, and
  pgVector integration validation.
