# Function List — BPMNArchitect

| ID | Function Name | File Path | Description |
|---|---|---|---|
| FL-001 | `build_canonical_37_step_process` | `src/bpmn_process_compiler.py` | Public function |
| FL-002 | `BpmnarchitectRequestSchema` | `domain_contract_adapter.py` | Immutable typed input schema for BPMNArchitect capability invocations. |
| FL-003 | `BpmnarchitectResultSchema` | `domain_contract_adapter.py` | Immutable typed output schema for BPMNArchitect execution results. |
| FL-004 | `AbstractBpmnarchitectAdapter` | `domain_contract_adapter.py` | Abstract protocol interface enforcing Liskov Substitution and Dependency Inversi |
| FL-005 | `BpmnarchitectDomainAdapter` | `domain_contract_adapter.py` | Concrete polymorphic adapter for BPMNArchitect. |
| FL-006 | `NotionBackupManager` | `modules/DiagramKit/core/backup_to_notion/notion_backup.py` | Public symbol |
| FL-007 | `C4DiagramGenerator` | `modules/DiagramKit/core/c4-author/generator.py` | Generates C4 Architecture diagrams and PlantUML models from structured definitio |
| FL-008 | `EAComponent` | `modules/DiagramKit/core/ea-gap/gap_analyzer.py` | Public symbol |
| FL-009 | `SyncRuleResult` | `modules/DiagramKit/core/ea-gap/gap_analyzer.py` | Public symbol |
| FL-010 | `StandaloneSyncEngine` | `modules/DiagramKit/core/ea-gap/gap_analyzer.py` | Standalone engine for EA artifact syncing, validation, and gap analysis. |
| FL-011 | `PlantUMLConfig` | `modules/DiagramKit/core/puml-render/config.py` | Public symbol |
| FL-012 | `encode_plantuml` | `modules/DiagramKit/core/puml-render/puml_engine.py` | Encodes PlantUML string using deflate compression + PlantUML 64-bit encoding. |
| FL-013 | `PlantUMLRenderEngine` | `modules/DiagramKit/core/puml-render/puml_engine.py` | PlantUML Rendering Engine with sanitization and verification. |
| FL-014 | `DiagramkitRequestSchema` | `modules/DiagramKit/domain_contract_adapter.py` | Immutable typed input schema for DiagramKit capability invocations. |
| FL-015 | `DiagramkitResultSchema` | `modules/DiagramKit/domain_contract_adapter.py` | Immutable typed output schema for DiagramKit execution results. |
| FL-016 | `AbstractDiagramkitAdapter` | `modules/DiagramKit/domain_contract_adapter.py` | Abstract protocol interface enforcing Liskov Substitution and Dependency Inversi |
| FL-017 | `DiagramkitDomainAdapter` | `modules/DiagramKit/domain_contract_adapter.py` | Concrete polymorphic adapter for DiagramKit. |
| FL-018 | `NodeType` | `src/bpmn_process_compiler.py` | Public symbol |
| FL-019 | `GatewayType` | `src/bpmn_process_compiler.py` | Public symbol |
| FL-020 | `BPMNActivity` | `src/bpmn_process_compiler.py` | Public symbol |
| FL-021 | `BPMNGateway` | `src/bpmn_process_compiler.py` | Public symbol |
| FL-022 | `BPMNExceptionLoop` | `src/bpmn_process_compiler.py` | Public symbol |
| FL-023 | `BPMNPhase` | `src/bpmn_process_compiler.py` | Public symbol |
| FL-024 | `BPMNProcess` | `src/bpmn_process_compiler.py` | Represents a full BPMN 2.0 Process specification (e.g. 53.REF.07, 53.REF.08). |

*Generated on 2026-08-27*
