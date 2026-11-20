# UC-001: Capabilities

## Use Case Identification
| Field | Value |
|---|---|
| **UC ID** | UC-001 |
| **Title** | Capabilities |
| **Skill** | DiagramKit |
| **Version** | 0.1.0 |
| **Status** | Draft (Auto-Generated) |
| **Created** | 2026-08-27 |
| **Generator** | DirectAssetGenerator v2.1 |

## Goal
Enable the `DiagramKit` skill to support **Capabilities** operations within the Antigravity platform.

## Scope
In-scope: All `Capabilities` operations executed by the `DiagramKit` skill.
Out-of-scope: External system configuration; hardware provisioning.

## Level
User Goal

## Description
DiagramKit: Capabilities

## Actors
| Actor | Type | Description |
|---|---|---|
| **Operator** | Primary | The developer or agent invoking the skill |
| **System** | Supporting | The Antigravity platform runtime |
| **LLM Provider** | External | AI model backend (Gemini/OpenAI/Claude) |

## Preconditions
1. The Antigravity platform is running
2. The skill `DiagramKit` is installed and registered
3. Required dependencies are available
4. Caller has appropriate permissions

## Main Success Flow
1. C4 Architecture Authoring: Generates C4 model diagrams (Context, Container, Component, Code) from structured input via the c4-author/ module, including landscape parsing and product view generation.
2. Enterprise Architecture Gap Analysis: Ingests EA artifacts, syncs them to a database, analyzes gaps between current and target architectures, and converts findings into dashboard-ready formats (ea-gap/ module).
3. PlantUML Rendering: Sanitizes and renders PlantUML .puml files via a local server (puml-render/ module).
4. Notion Backup: Backs up generated diagrams and architecture artifacts to Notion via the backup_to_notion module.
5. Landscape Conversion: Parses and converts architecture landscape definitions into structured diagram templates.


## Success Guarantee
The operation completes and results are persisted to the designated output path.

## Minimum Guarantee
Execution is logged with status and error details, even on failure.

## Alternate Flows
- **AF-1: Invalid Input** — System validates inputs and returns a structured error with field-level guidance. Gherkin: `@TC-UC-001-S02`
- **AF-2: Dependency Unavailable** — System retries up to 3 times with exponential backoff, then falls back. Gherkin: `@TC-UC-001-S03`
- **AF-3: Timeout** — System terminates execution after configured timeout and reports partial results. Gherkin: `@TC-UC-001-S04`

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
| Slice-1 | Happy Path — Capabilities | `@TC-UC-001-S01` | Must-Pass |
| Slice-2 | Invalid Input | `@TC-UC-001-S02` | Must-Pass |
| Slice-3 | Dependency Failure | `@TC-UC-001-S03` | Should-Pass |
| Slice-4 | Graceful Degradation | `@TC-UC-001-ERR01` | Should-Pass |

## Related Scripts
- (none discovered)

## Traceability
- **Gherkin**: `tests/features/TC-UC-001_diagramkit.feature`
- **Test Data**: `tests/data/TC-UC-001_data.json`
- **Functional Requirements**: `docs/functional_requirements.md`

## Revision History
| Version | Date | Author | Change |
|---|---|---|---|
| 0.1.0 | 2026-08-27 | DirectAssetGenerator | Auto-generated scaffold |
