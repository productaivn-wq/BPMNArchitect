# BPMNArchitect

> First-party, sovereign BPMN 2.0 Business Process Modeling, Auditing, and Visualization skill & compiler built on our UTOP & 7-Phase SOP standards (`53.REF.07`, `53.REF.08`, `53.REF.69`, `53.REF.100`). Compiles structured processes and 2-Layer JSON IR into standard **Camunda Modeler 5.20+ XML (`.bpmn`)**, **interactive `bpmn-js` drag-and-drop Studio (`.html`)**, **PlantUML (`.puml`)**, **Mermaid (`.mermaid`)**, and **UTOP Process Specs (`.md`)** with deterministic mathematical layout and arrow-overlap verification ($P=1$).

**Version:** 2.1.0 | **Updated:** 2026-11-20

---

## Key Capabilities

1. **2-Layer IR -> Camunda 5.20+ Compiler (`src/bpmn_process_compiler.py`)**:
   - Models `BPMNProcess` with Collaboration Pools (`<bpmn:collaboration>`), Three-Node Socio-Technical Swimlanes (`HUM`, `AGT`, `DET P=1`), Unified ID Taxonomy (`ST-xxx`, `GW-xxx`, `EX-xxx`, `RF-xxx`), and Dead-End Eliminated recovery loops.
   - Serializes and restores clean business IR (`*.ir.json`) via `to_ir_dict()` / `from_ir_dict()` — separate business logic from coordinate math.
2. **Deterministic Semantic & Geometric Verification ($P=1$)**:
   - `verify_semantic_invariants()`: Enforces graph reachability from `StartEvent_1`, reverse-reachability to `EndEvent_1` (zero dead-ends), gateway branching ($\ge 2$ distinct targets with labels), and optional UC source coverage.
   - `verify_layout()`: Verifies `0` node bounding-box collisions, `0` line-box cuts, and Camunda Modeler header/label clearances.
   - `check_arrow_overlaps()`: Enforces strict orthogonal segment disjointness (`0` collinear arrow overlaps).
3. **Interactive `bpmn-js` Camunda 5.20+ Studio (`examples/53_REF_07_camunda_studio.html`)**:
   - Open directly in any browser for **drag-and-drop editing** (`bpmn-modeler.production.min.js`), multi-process dropdown switching, Zoom/Fit controls, **Download `.bpmn`**, **Export `.svg`**, **Save File** (File System Access API), **UTOP Step Execution Matrix**, and **Mermaid / PlantUML / Raw XML** inspection.
   - Note: The interactive drag-and-drop canvas loads `bpmn-js@17.11.1` from `unpkg.com` CDN; the UTOP Step Matrix, Mermaid, PlantUML, and Raw XML tabs remain 100% available offline.
4. **Canonical SOP Models Included**:
   - **`53.REF.07`**: 37-Step Technical Vibe Coding Process `[CODE]`
   - **`53.REF.08`**: 18-Step Universal Vibe Working Process `[CORE]`

---

## 1-Command Installation

### Standalone Python CLI
```bash
git clone https://github.com/productaivn-wq/BPMNArchitect.git
cd BPMNArchitect
pip install click pytest
```

### Mount as an AI Agent Skill

- **Claude Code**:
  ```bash
  git clone https://github.com/productaivn-wq/BPMNArchitect.git ~/.claude/skills/BPMNArchitect
  ```
- **Google Antigravity**:
  ```bash
  git clone https://github.com/productaivn-wq/BPMNArchitect.git ~/.gemini/config/skills/BPMNArchitect
  ```
- **Codex**:
  ```bash
  git clone https://github.com/productaivn-wq/BPMNArchitect.git ~/.codex/skills/BPMNArchitect
  ```

*(On Windows PowerShell, replace `~` with `$HOME`.)*

---

## Quick Start

```bash
# 1. Export the canonical 37-step & 18-step SOP BPMN showcase package
python scripts/cli.py --action export-suite --target-dir examples

# 2. Compile any custom 2-layer *.ir.json process file into .bpmn + HTML Studio + .puml + .mermaid + _SPEC.md
python scripts/cli.py --action export-suite --ir examples/53_REF_08.ir.json --target-dir out_bpmn

# 3. Verify semantic reachability, zero box collisions, and zero arrow overlaps
python scripts/cli.py --action verify-bpmn

# 4. Run full automated test suite (27 tests)
python -m pytest tests/ -v
```

---

## 2-Layer JSON IR Schema (`*.ir.json`)

Author processes as pure business JSON (`process`, `lanes`, `phases`, `activities`, `gateways`, `exception_loops`, `transitions`) and let `BPMNArchitect` compute collision-free BPMNDI coordinates automatically:

```json
{
  "process": {
    "id": "ORDER.01",
    "name": "Order Approval Workflow",
    "version": "1.0.0",
    "protocol_type": "CORE"
  },
  "lanes": [
    { "lane_id": "Lane_HUMAN", "name": "Human Reviewer", "node_type": "HumanNode" },
    { "lane_id": "Lane_CODE", "name": "Automation Engine", "node_type": "CodeNode" }
  ],
  "phases": [
    { "phase_id": 1, "name": "Intake & Review", "governance_gates": ["GW-001"] }
  ],
  "activities": [
    { "activity_id": "ST-001", "name": "Submit Request", "phase_id": 1, "assigned_node_type": "HumanNode", "lane_id": "Lane_HUMAN", "rule_ref": "Order Intake" },
    { "activity_id": "ST-002", "name": "Validate & Fulfill", "phase_id": 1, "assigned_node_type": "CodeNode", "lane_id": "Lane_CODE", "rule_ref": "Auto-Dispatch" }
  ],
  "gateways": [
    { "gateway_id": "GW-001", "name": "Approval Gate", "gateway_type": "XOR", "condition_expression": "approved == True", "true_target": "ST-002", "false_target": "EX-001", "lane_id": "Lane_HUMAN", "phase_id": 1 }
  ],
  "exception_loops": [
    { "loop_id": "EX-001", "source_activity_id": "GW-001", "recovery_activity_id": "ST-001", "trigger_error_code": "REJECTED_REVISE", "max_retries": 3, "lane_id": "Lane_HUMAN" }
  ],
  "transitions": [
    { "source": "ST-001", "target": "ST-002" }
  ]
}
```

Compile it immediately:

```bash
python scripts/cli.py --action export-suite --ir my_process.ir.json --target-dir ./out
```

---

## Directory Structure

```text
BPMNArchitect/
├── SKILL.md                             # Canonical skill rules & Camunda 5.20 layout invariants
├── README.md                            # This file
├── core/
│   └── b_p_m_n_architect_det_harness.py # Deterministic P=1 harness & metrics
├── scripts/
│   └── cli.py                           # Click CLI (--action export-suite / verify-bpmn / --ir)
├── src/
│   └── bpmn_process_compiler.py         # BPMN 2.0 compiler, verifiers & Camunda Studio generator
├── specs/
│   └── SPEC-BPMNArchitect-UTOP.md       # UTOP requirements & verification spec
├── examples/                            # Ready-to-open Camunda .bpmn, .ir.json, .puml, .mermaid & HTML Studio
├── docs/                                # UC 3.0 narratives, FRs, traceability matrix & checkpoints
└── tests/                               # Pytest & unittest verification suite
```
