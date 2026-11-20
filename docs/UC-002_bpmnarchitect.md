# UC-002: 2. Standard Taxonomy & Rules

## Use Case Identification
| Field | Value |
|---|---|
| **UC ID** | UC-002 |
| **Title** | 2. Standard Taxonomy & Rules |
| **Skill** | BPMNArchitect |
| **Version** | 2.0.0 |
| **Status** | Draft (Auto-Generated) |
| **Created** | 2026-08-27 |
| **Generator** | DirectAssetGenerator v2.1 |

## Goal
Enable the `BPMNArchitect` skill to support **2. Standard Taxonomy & Rules** operations within the Antigravity platform.

## Scope
In-scope: All `2. Standard Taxonomy & Rules` operations executed by the `BPMNArchitect` skill.
Out-of-scope: External system configuration; hardware provisioning.

## Level
User Goal

## Description
BPMNArchitect: 2. Standard Taxonomy & Rules

## Actors
| Actor | Type | Description |
|---|---|---|
| **Operator** | Primary | The developer or agent invoking the skill |
| **System** | Supporting | The Antigravity platform runtime |
| **LLM Provider** | External | AI model backend (Gemini/OpenAI/Claude) |

## Preconditions
1. The Antigravity platform is running
2. The skill `BPMNArchitect` is installed and registered
3. Required dependencies are available
4. Caller has appropriate permissions

## Main Success Flow
1. ST-xxx (Happy Path Steps): ST-001, ST-002, ... ST-037 (Sequential 3-digit zero-padded IDs).
2. EX-xxx (Unhappy Exception Branches): EX-001 to EX-007 (Auto-heal recovery loops & escalations).
3. GW-xxx (Decision Gateways): GW-001 to GW-004 (Conditional decision gateways).
4. RF-xxx (Reflection Circles): RF-001 (30s micro), RF-002 (1m meso), RF-003 (3m macro).
5. 🔵 [CORE] Universal Path (#0f172a container / #38bdf8 border): Baseline path followed by all work types (General Vibe Working, Research, Documents, Ops, Strategy, and Harness Nodes).
6. 🟣 [CODE] Technical Vibe Coding (#3b0764 container / #c084fc border): Deep engineering sub-task hops for Vibe Coding (AST 3-Way Merges, DB Schema Migrations, SAST Scans, Fast-Forward Git PR Merges, Infrastructure Deploy).
7. 🔴 [EX] Exception Auto-Heal (#450a0a container / #ef4444 border): Unhappy exception recovery loops (EX-001 to EX-007).
8. 🟠 [GW] Decision & Quality Gateways (#fb923c border): Gateways and 4-tier Quality Gates (GW-001 to GW-004).
9. Subtask Quality Gate (ST-018 / RF-001): Micro-timebox sandbox quality validation (2m subtask level).
10. Task Quality Gate (GW-003 / ST-025 / RF-002): Meso-timebox staging quality validation ($\text{EAI} \ge 0.98$).


## Success Guarantee
The operation completes and results are persisted to the designated output path.

## Minimum Guarantee
Execution is logged with status and error details, even on failure.

## Alternate Flows
- **AF-1: Invalid Input** — System validates inputs and returns a structured error with field-level guidance. Gherkin: `@TC-UC-002-S02`
- **AF-2: Dependency Unavailable** — System retries up to 3 times with exponential backoff, then falls back. Gherkin: `@TC-UC-002-S03`
- **AF-3: Timeout** — System terminates execution after configured timeout and reports partial results. Gherkin: `@TC-UC-002-S04`

## Postconditions
1. Skill execution is logged with duration and status
2. Results are available to the caller at the designated path
3. No system state corruption on failure

## Business Rules
- BR-1: Skill must complete within configured timeout (default: 300s)
- BR-2: All outputs must be written to the designated directory under `skill_path`
- BR-3: Errors must be propagated with actionable, human-readable messages
- BR-4: No silent failures — all exceptions must be caught and logged

## Use-Case Slices
| Slice | Scenario | TC Reference | Priority |
|---|---|---|---|
| Slice-1 | Happy Path — 2. Standard Taxonomy & Rules | `@TC-UC-002-S01` | Must-Pass |
| Slice-2 | Invalid Input | `@TC-UC-002-S02` | Must-Pass |
| Slice-3 | Dependency Failure | `@TC-UC-002-S03` | Should-Pass |
| Slice-4 | Graceful Degradation | `@TC-UC-002-ERR01` | Should-Pass |

## Related Scripts
- `bpmn_process_compiler.py`

## Traceability
- **Gherkin**: `tests/features/TC-UC-002_bpmnarchitect.feature`
- **Test Data**: `tests/data/TC-UC-002_data.json`
- **Functional Requirements**: `docs/functional_requirements.md`

## Revision History
| Version | Date | Author | Change |
|---|---|---|---|
| 0.1.0 | 2026-08-27 | DirectAssetGenerator | Auto-generated scaffold |
