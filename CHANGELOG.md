# Changelog: BPMNArchitect

All notable changes to this skill are documented here.

## [2026-09-09] - v2.0.0
### Initial
- Skill baseline registration.

## [2026-11-20] - v2.1.0
### Added
- First-party 2-Layer JSON IR -> Camunda Modeler 5.20+ BPMN 2.0 XML compiler with Collaboration Pools, Swimlanes, Gutter Detour routing, and zero-collision BPMNDI (`src/bpmn_process_compiler.py`).
- Deterministic P=1 verifiers (`verify_semantic_invariants`, `verify_layout`, `check_arrow_overlaps`).
- Self-contained interactive `bpmn-js` Camunda Studio (`.html`) with drag-and-drop modeling, SVG/BPMN export, UTOP Step Matrix, and PlantUML/Mermaid/XML tabs.
- Canonical SOP models for `53.REF.07` (37-Step Coding) and `53.REF.08` (18-Step Working), plus Layer-2 CLI actions (`export-suite`, `verify-bpmn`).
