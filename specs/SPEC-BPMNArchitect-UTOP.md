# SPEC-BPMNArchitect-UTOP: BPMNArchitect Generic BPMN 2.0 Business Process Modeling & Visualization Engine

- Status: ACTIVE
- Traceability: `SKILL.md` <-> `specs/SPEC-BPMNArchitect-UTOP.md` <-> `tests/data/TC-BPMNArchitect_data.json`
- Invariant & Quality Gate: GW-QG-01, GW-TC-COUPLE-01, EAI >= 0.98

## 1. Functional Requirements (FR)
- FR-BPMNArchitect-01: BPMN 2.0 formal activity diagram modeling with Unified ID Taxonomy (ST-xxx, GW-xxx, EX-xxx, RF-xxx) and 2-Layer JSON IR compilation (`to_ir_dict` / `from_ir_dict`).
- FR-BPMNArchitect-02: Dead-End Elimination (`EX-001..EX-007`), dynamic polymorphic hops (`[CODE]` vs `[CORE]`), and deterministic semantic verification (`verify_semantic_invariants`).
- FR-BPMNArchitect-03: Standard Camunda Modeler 5.20+ `.bpmn` XML/BPMNDI generation with zero-collision layout (`verify_layout`, `check_arrow_overlaps`), interactive `bpmn-js` Modeler studio (`.html`), PlantUML (`.puml`), Mermaid (`.mermaid`), and UTOP Markdown Spec (`.md`).

## 2. Test Cases & Acceptance Criteria (Check #12 & GW-TC-COUPLE-01)
- Total Domain Vectors: 12 (7 ACCEPT + 5 REJECT adversarial cases) + compiler/layout verification suite.
- Primary Data Matrix: `tests/data/TC-BPMNArchitect_data.json`.
