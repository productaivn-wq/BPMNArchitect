---
name: DiagramKit
status: active
version: 0.1.0
changed_at: 2026-06-25
description: Generate C4 architecture diagrams, enterprise architecture gap analysis,
  and PlantUML rendering with Notion backup.
capabilities:
- c4-architecture-authoring
- enterprise-architecture-gap-analysis
- plantuml-rendering
- notion-backup
- landscape-conversion
risk_class: TIER_1
approval_checkpoints:
- scope_confirmation
- security_confirmation
domain_adapter_contract:
  version: 3.1.0
  boundary: deterministic_p1_and_agentic_bdi
  mece_demarcation: Canonical owner of DiagramKit domain operations within the Antigravity
    9-stage enterprise lifecycle.
  validation: pydantic_or_dataclass_schema
---

# DiagramKit Skill Catalog

## Overview
DiagramKit provides automated diagram generation and architecture visualization capabilities. It encompasses three sub-modules: C4 architecture authoring, enterprise architecture gap analysis, and PlantUML rendering.

## Capabilities

- **C4 Architecture Authoring**: Generates C4 model diagrams (Context, Container, Component, Code) from structured input via the `c4-author/` module, including landscape parsing and product view generation.
- **Enterprise Architecture Gap Analysis**: Ingests EA artifacts, syncs them to a database, analyzes gaps between current and target architectures, and converts findings into dashboard-ready formats (`ea-gap/` module).
- **PlantUML Rendering**: Sanitizes and renders PlantUML `.puml` files via a local server (`puml-render/` module).
- **Notion Backup**: Backs up generated diagrams and architecture artifacts to Notion via the `backup_to_notion` module.
- **Landscape Conversion**: Parses and converts architecture landscape definitions into structured diagram templates.

## Artifacts
- `docs/UC-001_diagramkit.md`: Core Use Case specifications.
- `docs/function_rules.md`: Function rules.
- `docs/traceability_matrix.md`: Traceability matrix.

## Usage
Add this skill to your dynamic routing catalog to enable runtime diagram generation.

---

## When to Activate (Goal & Intent Triggers)

- **Trigger Condition**: Activate when the task requires `DiagramKit` domain capabilities or `diagramkit-execution`.
- **Preconditions**: Input payload adheres to the validated domain contract schema; workspace confinement (`GW-FS-ISOLATION-01`) verified.

## BDI Workflow & Deterministic Execution Pipeline

1. **Phase 1 (Belief & Schema Check)**: Parse input arguments and validate deterministic preconditions via `domain_contract.py` CLI/tool interface.
2. **Phase 2 (Desire & Contract Lock)**: Bind execution targets to measurable `DoD` quality gates.
3. **Phase 3 (Intention & Tool Dispatch)**: Execute discrete domain adapter actions (`diagramkit-execution`).
4. **Phase 4 (Verification & Feedback Loop)**: Assert output invariants ($P=1$) and emit structured audit telemetry.

## MECE Boundary & DRY Delegation Contract (`mece_demarcation_contract`)

- **Scope Demarcation**: Canonical owner of DiagramKit domain operations within the Antigravity 9-stage enterprise lifecycle.
- **DRY SSOT Invariant**: Zero duplicate business logic; shared persistence and telemetry delegate to `TaskManager` and `QualityGate`.
