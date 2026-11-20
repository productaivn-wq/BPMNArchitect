# UC-001: 1. Overview & Generic Design Principles

## Use Case Identification
| Field | Value |
|---|---|
| **UC ID** | UC-001 |
| **Title** | 1. Overview & Generic Design Principles |
| **Skill** | BPMNArchitect |
| **Version** | 2.1.0 |
| **Status** | Active |
| **Updated** | 2026-11-20 |

## Goal
Enable the `BPMNArchitect` skill to model, validate, and deliver standard OMG BPMN 2.0 workflows across Camunda Modeler 5.20+, interactive `bpmn-js` web studios, PlantUML, Mermaid, and UTOP specifications.

## Scope
In-scope: All domain-agnostic BPMN 2.0 modeling, 2-layer JSON IR compilation, deterministic layout/overlap verification, and multi-format export executed by `BPMNArchitect`.
Out-of-scope: External Camunda server deployment or infrastructure provisioning.

## Level
User Goal

## Description
BPMNArchitect: 1. Overview & Generic Design Principles

## Actors
| Actor | Type | Description |
|---|---|---|
| **Operator** | Primary | The BA, PM, developer, or agent invoking the skill |
| **System** | Supporting | The `bpmn_process_compiler.py` deterministic engine & CLI |
| **LLM Provider** | External | AI model backend synthesizing business process IR |

## Preconditions
1. Python 3.10+ is available
2. The skill `BPMNArchitect` is installed
3. Input process description, Use Case, or `*.ir.json` conforms to schema
4. Target output path is within authorized workspace boundaries

## Main Success Flow
1. Generic & Reusable: `BPMNArchitect` decouples business process intent (`*.ir.json`) from deterministic layout calculation (`src/bpmn_process_compiler.py`).
2. Multi-Format First-Class Delivery: Generates standard Camunda BPMN 2.0 XML (`.bpmn` with Collaboration Pools, Swimlanes, and full BPMNDI shapes/waypoints), interactive `bpmn-js` Modeler HTML Studio (`.html`), PlantUML (`.puml`), Native Mermaid (`.mermaid`), and UTOP Markdown Specs (`.md`).
3. Mathematical Verification ($P=1$): Enforces `verify_semantic_invariants()`, `verify_layout()` (0 shape collisions, 0 line-box cuts), and `check_arrow_overlaps()` (0 overlapping segments).

## Success Guarantee
The operation completes, passes all semantic/geometric checks, and persists verified artifacts to the designated output path.

## Minimum Guarantee
Execution is logged with status and deterministic error details on failure.

## Alternate Flows
- **AF-1: Invalid Input** — System validates inputs and returns a structured error with field-level guidance. Gherkin: `@TC-UC-001-S02`
- **AF-2: Dependency Unavailable** — System degrades gracefully (HTML Studio offline tabs remain usable without CDN). Gherkin: `@TC-UC-001-S03`
- **AF-3: Timeout** — System terminates execution cleanly and reports partial diagnostics. Gherkin: `@TC-UC-001-S04`

## Postconditions
1. Verified `.bpmn`, `.ir.json`, `.puml`, `.mermaid`, `_SPEC.md`, and `_camunda_studio.html` artifacts exist at the output path
2. `verify_layout()` reports `shape_collisions == 0` and `box_intersections == 0`
3. `check_arrow_overlaps()` reports `overlap_count == 0`

## Business Rules
- BR-1: Collaboration Pools & Swimlanes are mandatory for multi-role processes
- BR-2: Zero dead-end exception branches (`EX-xxx` loops back to recovery nodes)
- BR-3: Errors propagate with actionable, human-readable diagnostics
- BR-4: No silent failures — all exceptions must be caught and reported

## Use-Case Slices
| Slice | Scenario | TC Reference | Priority |
|---|---|---|---|
| Slice-1 | Happy Path — 1. Overview & Generic Design Principles | `@TC-UC-001-S01` | Must-Pass |
| Slice-2 | Invalid Input | `@TC-UC-001-S02` | Must-Pass |
| Slice-3 | Dependency Failure | `@TC-UC-001-S03` | Should-Pass |
| Slice-4 | Graceful Degradation | `@TC-UC-001-ERR01` | Should-Pass |

## Related Scripts
- `src/bpmn_process_compiler.py`
- `scripts/cli.py`

## Traceability
- **Gherkin**: `tests/features/TC-UC-001_bpmnarchitect.feature`
- **Test Data**: `tests/data/TC-UC-001_data.json`
- **Functional Requirements**: `docs/functional_requirements.md`
