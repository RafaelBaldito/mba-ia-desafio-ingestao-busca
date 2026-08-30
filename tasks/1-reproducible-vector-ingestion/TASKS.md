# Tasks — Wave 1: Reproducible Vector Ingestion

## Scope

Implement only the approved Wave 1 ingestion path: configuration validation,
deterministic PDF chunking, OpenAI embedding and pgVector replacement
persistence, a safe `python src/ingest.py` command, and its automated
validation. Retrieval, chat, prompt behavior, and all Wave 2 work remain
excluded.

## Execution Order

| Task | Title | Depends On | Status |
| --- | --- | --- | --- |
| TASK-001 | Establish Ingestion Configuration and Test Foundation | — | FIX_REQUIRED |
| TASK-002 | Implement Deterministic PDF Loading and Chunking | TASK-001 | PENDING |
| TASK-003 | Implement Embedding and pgVector Persistence Adapters | TASK-001, TASK-002 | PENDING |
| TASK-004 | Implement the Ingestion Orchestrator and CLI | TASK-001, TASK-002, TASK-003 | PENDING |
| TASK-005 | Add Isolated pgVector Integration and Opt-in Smoke Validation | TASK-004 | PENDING |

## Coverage

- TECHSPEC §1–2; FR-001 / CON-001, CON-003 → TASK-001, TASK-004
- TECHSPEC §2, §4.2 step 3; FR-002 → TASK-002
- TECHSPEC §2, §4.2 steps 4–6, §4.3; FR-003 / NFR-002, NFR-003 / CON-004 configuration portion → TASK-003, TASK-004, TASK-005
- TECHSPEC §5 configuration contract; NFR-001, NFR-004 / CON-001, CON-002 → TASK-001, TASK-005
- TECHSPEC §6 error and operational behavior → TASK-001 through TASK-004
- TECHSPEC §7 deterministic tests and 90% coverage → TASK-001 through TASK-005
- TECHSPEC §8 boundaries and external-service seams → TASK-002 through TASK-005

## Execution Notes

- Execute one task at a time with `execute-task`; no task authorizes Wave 2
  changes.
- `TASK-001` establishes the required pytest command and the project-wide 90%
  coverage gate. Later tasks must maintain it, not bypass it through exclusions.
- The integration validation in `TASK-005` must use an isolated disposable
  pgVector Compose project; it must never use production credentials or the
  persistent `postgres_data` volume.
