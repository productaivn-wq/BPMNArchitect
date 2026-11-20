# Functional Requirements — BPMNArchitect

| Field | Value |
|---|---|
| **Skill** | BPMNArchitect |
| **UC Coverage** | UC-001, UC-002, UC-003 |
| **Generated** | 2026-08-27 |
| **Standard** | UC 3.0 / RequirementsTraceKit |

## FR Catalog

| FR-ID | Requirement (The system SHALL...) | Type | UC | Priority |
|---|---|---|---|---|
| FR-001 | The system SHALL Generic BPMN 2.0 Business Process Modeling, Auditing, and Visualization skill. Models, validates, and renders formal BPMN 2.0 activity diagrams (PlantUML .puml) and interactive Mermaid.js viewers (.html). Incorporates Unified ID Taxonomy (ST-xxx, EX-xxx, GW-xxx, RF-xxx), Dead-End Elimination (EX-001. | Mandatory | UC-001 | High |
| FR-002 | The system SHALL Generic & Reusable: BPMNArchitect contains instructions for process modeling in general. System-specific process specifications (such as the Universal Working Harness 37-step model) live in project context directories (docs/diagrams/UNIVERSAL_WORKING_HARNESS_BPMN_SPEC.md). | Mandatory | UC-001 | High |
| FR-003 | The system SHALL PlantUML & Mermaid Native: OMG BPMN XML and bpmn-js are deprecated. All process models MUST be rendered using PlantUML Activity Diagrams (.puml) and Interactive Mermaid.js HTML Viewers (.html). | Mandatory | UC-001 | High |
| FR-004 | The system SHALL Start Event Flexibility: A valid process MUST have at least one Start Event ($\ge 1$). Multiple Start Events with distinct triggers (Message, Timer, Signal, None) are explicitly allowed. | Mandatory | UC-001 | High |
| FR-005 | The system SHALL ST-xxx (Happy Path Steps): ST-001, ST-002, ... ST-037 (Sequential 3-digit zero-padded IDs). | Mandatory | UC-002 | High |
| FR-006 | The system SHALL EX-xxx (Unhappy Exception Branches): EX-001 to EX-007 (Auto-heal recovery loops & escalations). | Mandatory | UC-002 | High |
| FR-007 | The system SHALL GW-xxx (Decision Gateways): GW-001 to GW-004 (Conditional decision gateways). | Mandatory | UC-002 | High |
| FR-008 | The system SHALL RF-xxx (Reflection Circles): RF-001 (30s micro), RF-002 (1m meso), RF-003 (3m macro). | Mandatory | UC-002 | High |
| FR-009 | The system SHALL Maps BPMN Node ID $\to$ DAGNodeID $\to$ CAP-xxx $\to$ UTOPTrace. | Mandatory | UC-003 | High |
| FR-010 | The system SHALL Enforces 100% diagram traceability coverage score ($\text{CoverageScore}_{\text{BPMN}} = 1.0$). | Mandatory | UC-003 | High |

## Non-Functional Requirements

| NFR-ID | Requirement | Category |
|---|---|---|
| NFR-001 | The system SHALL complete within the configured timeout. | Performance |
| NFR-002 | The system SHALL log all execution events for auditability. | Observability |
| NFR-003 | The system SHALL NOT modify state without explicit user approval where required. | Safety |
| NFR-004 | The system SHALL degrade gracefully when dependencies are unavailable. | Resilience |
| NFR-005 | The system SHALL implement strict validation on all input payloads. | Security |

## Verification
- Each FR maps to at least one Gherkin scenario in the corresponding `.feature` file
- UC distribution: UC-001, UC-002, UC-003
- Priority: High = must-have, Medium = should-have, Low = nice-to-have
