# AGENTS.md

## Project Overview

This repository is developed using a specification-driven AI-assisted
engineering workflow.

Product requirements, delivery boundaries, technical design,
implementation tasks, code, tests, and reviews must remain traceable and
consistent.

Agents must prefer correctness, bounded context, explicit scope, and
verifiable evidence over speculative implementation.

## Development Workflow

Use the following lifecycle when the corresponding artifacts are
required:

`PRD → Delivery Plan → TECHSPEC → Tasks → Execute → Review → Fix → Final Review`

Planning artifacts require explicit human approval before the next
planning stage begins.

For larger deliveries, work may be divided into Waves. Only the
currently approved Wave should receive detailed TECHSPECs and
implementation tasks.

Do not automatically advance to another workflow stage unless explicitly
requested.

## Repository Map

Default documentation conventions:

``` text
docs/
├── PRD.md
├── DELIVERY-PLAN.md
├── ARCHITECTURE.md
└── waves/
    └── <wave-id>-<short-name>/
        └── TECHSPEC.md

tasks/
├── TASKS.md                 # SINGLE delivery
├── TASK-XXX.md
└── <wave-id>-<short-name>/  # WAVES delivery
    ├── TASKS.md
    └── TASK-XXX.md

src/                         # Production code
tests/                       # Automated tests
```

For `SINGLE` delivery, the default TECHSPEC is:

`docs/TECHSPEC.md`

Respect an explicit repository convention when one already exists.

## Source of Truth

Use this authority order:

1.  current explicit user instruction;
2.  approved PRD;
3.  approved Delivery Plan;
4.  approved Architecture / ADRs;
5.  approved current-scope TECHSPEC;
6.  approved Task;
7.  repository engineering rules;
8.  existing implementation.

Lower-level artifacts must not silently redefine higher-level approved
decisions.

When artifacts conflict and the conflict cannot be resolved without
changing an approved decision, report:

`SPEC_CHANGE_REQUIRED`

Do not silently choose one conflicting interpretation.

## Coding Rules

-   Follow established repository patterns before introducing new ones.
-   Prefer simple, explicit implementations over speculative
    abstractions.
-   Keep changes within the selected task or approved scope.
-   Do not perform unrelated refactors.
-   Do not implement future tasks for convenience.
-   Add dependencies only when technically justified.
-   Never commit secrets, credentials, tokens, or private keys.
-   Update directly affected documentation when public behavior, setup,
    configuration, or usage changes.
-   Preserve approved architecture and contracts.
-   Tests are part of the implementation, not optional follow-up work.

## Quality Gates

All production changes must satisfy the repository quality gates.

### Automated Tests

-   New or modified production behavior MUST have appropriate automated
    tests.
-   Project automated test coverage MUST be at least **90%**.
-   Coverage MUST NOT be artificially increased by excluding relevant
    production code.
-   Tests MUST validate meaningful behavior rather than merely execute
    lines.
-   Relevant failure and boundary paths SHOULD be tested when
    applicable.

A task MUST NOT receive review `PASS` when applicable required tests
fail or when the required coverage gate is not satisfied.

The final project review MUST NOT receive `PASS` when project coverage
is below 90%.

### Additional Validation

When configured for the repository, the following checks are mandatory:

-   lint;
-   type checking;
-   build or import validation;
-   integration tests;
-   end-to-end or smoke tests for critical flows;
-   database or migration validation when applicable.

Never claim a validation passed unless the corresponding command was
actually executed successfully.

## Validation Commands

Use repository-native commands whenever they are defined.

For this repository, document confirmed commands here as tooling is
established:

``` bash
# Tests
python -m pytest

# Coverage
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90

# Lint
<project lint command>

# Type checking
<project type-check command>

# Other project validation
<project-specific command>
```

Do not invent tooling solely to fill this section. Update these commands
when the project establishes the corresponding tool.

Targeted task tests validate task-owned behavior. The 90% project coverage
gate must be evaluated with the project-wide test suite; do not combine a
narrow test selection with project-wide `--cov=src` unless the resulting
command is demonstrably coherent.

## Context Rules for Agents

Context is a budget.

Load the minimum information required to perform the current operation
safely.

For task execution, prefer this order:

1.  this `AGENTS.md`;
2.  selected task;
3.  task `Required Context`;
4.  directly affected source files and tests;
5.  task `Optional Context` only when necessary.

Do not load by default:

-   the entire PRD;
-   all TECHSPECs;
-   future Waves;
-   all tasks;
-   the entire source tree;
-   repository history.

Prefer references to specific document sections over complete documents.

A large Context Surface is a signal to reassess task or Wave boundaries,
not a reason to consume unlimited context.

## Scope and Change Control

Implementation agents must operate within explicit approved boundaries.

During `execute-task` and `fix-task`, approved PRDs, Delivery Plans,
Architecture/ADRs, TECHSPECs, and normative task content are immutable. A
required change to any of these artifacts must produce
`SPEC_CHANGE_REQUIRED`. Status-only updates remain permitted where the
repository convention requires them.

`execute-task`:

-   implements only the selected task;
-   does not redesign approved specifications;
-   does not start another task automatically.

`review-task`:

-   reviews only the selected task;
-   does not fix implementation while reviewing;
-   produces evidence-based acceptance or findings.

`fix-task`:

-   fixes only applicable review findings for the selected task;
-   does not perform unrelated improvements;
-   returns the task to a review-ready state.

`final-review`:

-   audits the complete approved release;
-   verifies traceability, integration, and project-level validation;
-   does not silently fix findings.

If implementation discovers that an approved requirement or design must
change, stop scope expansion and report `SPEC_CHANGE_REQUIRED`.

## Workflow States

Use these states consistently:

-   `AWAITING_HUMAN_APPROVAL` --- planning artifact is ready for
    explicit approval.
-   `COMPLETED` --- the requested execution/remediation operation
    completed.
-   `IMPLEMENTED` --- task implementation is ready for independent
    review.
-   `PASS` --- independent review accepted the task or release.
-   `FIX_REQUIRED` --- implementation defects must be corrected.
-   `SPEC_CHANGE_REQUIRED` --- approved upstream specification must be
    reconsidered.
-   `BLOCKED` --- required context, dependency, infrastructure, or
    decision is unavailable.

`COMPLETED` or `IMPLEMENTED` does not imply review `PASS`.

## Definition of Done

A delivered scope is done only when:

-   approved requirements assigned to the scope are implemented;
-   applicable automated tests pass;
-   required coverage is at least 90%;
-   applicable repository validation commands pass;
-   required integration behavior works;
-   directly affected documentation is current;
-   required task reviews have `PASS`;
-   no blocking review finding remains;
-   implementation remains consistent with approved specifications.

Project/release completion additionally requires successful
`final-review`.

## Skill Map

  -----------------------------------------------------------------------
  Skill                               Responsibility
  ----------------------------------- -----------------------------------
  `create-prd`                        Define product requirements and
                                      boundaries

  `plan-delivery`                     Choose delivery strategy and
                                      decompose delivery scope

  `create-techspec`                   Define technical design for one
                                      approved scope

  `create-tasks`                      Decompose one approved TECHSPEC
                                      into executable tasks

  `execute-task`                      Implement exactly one selected task

  `review-task`                       Independently review one
                                      implemented task

  `fix-task`                          Correct findings for one reviewed
                                      task

  `final-review`                      Audit complete release traceability
                                      and acceptance
  -----------------------------------------------------------------------

Skills define the workflow behavior. This file defines persistent
repository rules, quality gates, context policy, and validation
expectations.
