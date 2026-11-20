# Traceability Matrix — BPMNArchitect

| Field | Value |
|---|---|
| **Skill** | BPMNArchitect |
| **Generated** | 2026-08-27 |
| **Coverage** | OKF Verified |
| **UC Coverage** | 3 UCs (UC-001, UC-002, UC-003) |

## UC → Gherkin Scenarios ↔ Playwright (Test Data) ↔ Functional Requirements (FRs) ↔ Function Checkpoints

| UC Flow | Description | Gherkin Scenario | Functional Requirement | Test Data | Status |
|---|---|---|---|---|---|
| UC-001.1 | Generic & Reusable: BPMNArchitect contains instructions for process modeling in  | TC-UC-001-S01 | FR-001 | TC-001-VALID | Draft |
| UC-001.2 | PlantUML & Mermaid Native: OMG BPMN XML and bpmn-js are deprecated. All process  | TC-UC-001-S02 | FR-002 | TC-002-VALID | Draft |
| UC-001.3 | Start Event Flexibility: A valid process MUST have at least one Start Event ($\g | TC-UC-001-S03 | FR-003 | TC-003-VALID | Draft |
| UC-001.ERR | 1. Overview & Generic Design Principles — graceful degradation | TC-UC-001-ERR01 | NFR-004 | TC-004-TIMEOUT | Draft |
| UC-002.5 | ST-xxx (Happy Path Steps): ST-001, ST-002, ... ST-037 (Sequential 3-digit zero-p | TC-UC-002-S01 | FR-005 | TC-005-VALID | Draft |
| UC-002.6 | EX-xxx (Unhappy Exception Branches): EX-001 to EX-007 (Auto-heal recovery loops  | TC-UC-002-S02 | FR-006 | TC-006-VALID | Draft |
| UC-002.7 | GW-xxx (Decision Gateways): GW-001 to GW-004 (Conditional decision gateways). | TC-UC-002-S03 | FR-007 | TC-007-VALID | Draft |
| UC-002.8 | RF-xxx (Reflection Circles): RF-001 (30s micro), RF-002 (1m meso), RF-003 (3m ma | TC-UC-002-S04 | FR-008 | TC-008-VALID | Draft |
| UC-002.9 | 🔵 [CORE] Universal Path (#0f172a container / #38bdf8 border): Baseline path foll | TC-UC-002-S05 | FR-009 | TC-009-VALID | Draft |
| UC-002.10 | 🟣 [CODE] Technical Vibe Coding (#3b0764 container / #c084fc border): Deep engine | TC-UC-002-S06 | FR-010 | TC-010-VALID | Draft |
| UC-002.ERR | 2. Standard Taxonomy & Rules — graceful degradation | TC-UC-002-ERR01 | NFR-004 | TC-011-TIMEOUT | Draft |
| UC-003.12 | Maps BPMN Node ID $\to$ DAGNodeID $\to$ CAP-xxx $\to$ UTOPTrace. | TC-UC-003-S01 | FR-012 | TC-012-VALID | Draft |
| UC-003.13 | Enforces 100% diagram traceability coverage score ($\text{CoverageScore}_{\text{ | TC-UC-003-S02 | FR-013 | TC-013-VALID | Draft |
| UC-003.ERR | 4. UTOP Traceability Integration — graceful degradation | TC-UC-003-ERR01 | NFR-004 | TC-014-TIMEOUT | Draft |

## Coverage Summary

| Category | Count |
|---|---|
| Use Cases | 3 |
| Gherkin Scenarios | 14 |
| Functional Requirements | 14 |
| Test Data Cases | 14 |

*Generated on 2026-08-27*
