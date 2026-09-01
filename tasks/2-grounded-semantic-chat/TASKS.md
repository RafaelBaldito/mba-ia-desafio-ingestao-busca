# Tasks — Wave 2: Grounded Semantic Chat

**Status:** APPROVED
**Approval record:** 2026-08-31 — explicit human approval

## Scope

Implement only the approved Wave 2 terminal flow: validated chat settings,
pgVector retrieval of exactly ten chunks, the mandatory grounded prompt, the
OpenAI chat response path, the repeatable CLI, operator documentation, and
the required automated validation. This task set neither changes the Wave 1
ingestion/persistence contract nor adds a future delivery scope.

## Execution Order

| Task | Title | Depends On | Status |
| --- | --- | --- | --- |
| TASK-001 | Establish Secure Chat Configuration | — | PASS |
| TASK-002 | Implement Ten-Chunk Retrieval and Mandatory Prompt | TASK-001 | PASS |
| TASK-003 | Implement Grounded Answer Orchestration | TASK-001, TASK-002 | PASS |
| TASK-004 | Deliver the Repeatable Chat CLI and Operator Guide | TASK-001, TASK-002, TASK-003 | PASS |
| TASK-005 | Verify pgVector Retrieval Integration and Release Quality Gate | TASK-002, TASK-003, TASK-004 | PASS |

## Coverage

- TECHSPEC §2; §4.1–§4.2; §6; §7 configuration tests → TASK-001
- TECHSPEC §2; §3; §4.3–§4.4; §6; §7 retrieval/prompt tests → TASK-002
- TECHSPEC §2; §4.1; §4.5; §6; §7 answer-adapter tests → TASK-003
- TECHSPEC §2; §4.1; §4.6; §5; §6; §7 CLI/documentation tests → TASK-004
- TECHSPEC §1.1; §4.3; §5; §7 integration, import/Compose, and project coverage validation → TASK-005
- PRD FR-004–FR-011, NFR-005–NFR-006, CON-001–CON-006 (applicable Wave 2 portions) → TASK-001 through TASK-005
- Delivery Plan §6 Wave 2 and §7 cross-cutting constraints → TASK-001 through TASK-005

## Execution Notes

- Execute exactly one task at a time with `execute-task`; this index is not
  authorization to implement the next task automatically.
- TASK-002 owns the literal `k=10` and the byte-equivalent mandatory prompt;
  callers must not reimplement either contract.
- TASK-005 uses only the existing isolated disposable pgVector Compose test
  environment. It must never use the local persistent `postgres_data` volume,
  production credentials, or real OpenAI access.
- The repository-wide coverage gate is `python -m pytest --cov=src
  --cov-report=term-missing --cov-fail-under=90`. Earlier tasks must preserve
  it; TASK-005 records the final result for this Wave.
