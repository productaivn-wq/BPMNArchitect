# BPMNArchitect

> Generic OMG BPMN 2.0 Business Process Modeling, Auditing, and Visualization skill & compiler. Compiles structured processes and 2-Layer Business JSON IR (`*.ir.json`) into standard **Camunda Modeler 5.20+ XML (`.bpmn`)**, an **interactive `bpmn-js` drag-and-drop Studio (`.html`)**, **PlantUML (`.puml`)**, and **Mermaid (`.mermaid`)** with deterministic layout and arrow-overlap verification.

**Version:** 2.1.0 | **Updated:** 2026-11-20

---

## Key Capabilities

1. **2-Layer JSON IR -> Camunda 5.20+ Compiler (`src/bpmn_process_compiler.py`)**:
   - Models `BPMNProcess` with Collaboration Pools (`<bpmn:collaboration>`), Swimlanes (`<bpmn:laneSet>`), Unified ID Taxonomy (`ST-xxx`, `GW-xxx`, `EX-xxx`, `RF-xxx`), and Dead-End Eliminated recovery loops.
   - Serializes and restores clean business IR (`*.ir.json`) via `to_ir_dict()` / `from_ir_dict()` — separate business logic from pixel/waypoint math.
2. **Deterministic Semantic & Geometric Verification**:
   - `verify_semantic_invariants()`: Enforces graph reachability from `StartEvent_1`, reverse-reachability to `EndEvent_1` (zero dead-ends), gateway branching ($\ge 2$ distinct targets with labels), and optional source coverage.
   - `verify_layout()`: Verifies `0` node bounding-box collisions, `0` line-box cuts, and Camunda Modeler header/label clearances.
   - `check_arrow_overlaps()`: Enforces strict orthogonal segment disjointness (`0` collinear arrow overlaps).
3. **Interactive `bpmn-js` Camunda 5.20+ Studio (`examples/order_approval_camunda_studio.html`)**:
   - Open directly in any browser for **drag-and-drop editing** (`bpmn-modeler.production.min.js`), multi-process switching, Zoom/Fit controls, **Download `.bpmn`**, **Export `.svg`**, **Save File** (File System Access API), **Step Execution Matrix**, and **Mermaid / PlantUML / Raw XML** inspection.
   - Note: The interactive drag-and-drop canvas loads `bpmn-js@17.11.1` from `unpkg.com` CDN; the Step Matrix, Mermaid, PlantUML, and Raw XML tabs remain usable offline.

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
# 1. Compile any 2-layer *.ir.json process file into .bpmn + HTML Studio + .puml + .mermaid
python scripts/cli.py --action export-suite --ir examples/order_approval.ir.json --target-dir out_bpmn

# 2. Verify semantic reachability, zero box collisions, and zero arrow overlaps
python scripts/cli.py --action verify-bpmn --ir examples/order_approval.ir.json

# 3. Run automated test suite
python -m pytest tests/ -v
```

---

## 2-Layer JSON IR Schema (`*.ir.json`)

Author processes as pure business JSON (`process`, `lanes`, `phases`, `activities`, `gateways`, `exception_loops`, `transitions`) and let `BPMNArchitect` compute collision-free BPMNDI coordinates automatically:

```json
{
  "process": {
    "id": "order_approval",
    "name": "Order Approval Workflow",
    "version": "1.0.0",
    "protocol_type": "CORE"
  },
  "lanes": [
    { "lane_id": "Lane_CUSTOMER", "name": "Customer / Requester", "node_type": "HumanNode" },
    { "lane_id": "Lane_REVIEW", "name": "Finance & Operations", "node_type": "AgentNode" },
    { "lane_id": "Lane_SYSTEM", "name": "Order Engine (Automated)", "node_type": "CodeNode" }
  ],
  "phases": [
    { "phase_id": 1, "name": "Intake & Validation", "governance_gates": ["GW-001"] }
  ],
  "activities": [
    { "activity_id": "ST-001", "name": "Submit Order Request", "phase_id": 1, "assigned_node_type": "HumanNode", "lane_id": "Lane_CUSTOMER", "rule_ref": "Order Intake" },
    { "activity_id": "ST-002", "name": "Validate Inventory & Credit", "phase_id": 1, "assigned_node_type": "CodeNode", "lane_id": "Lane_SYSTEM", "rule_ref": "Stock + Credit Check" }
  ],
  "gateways": [
    { "gateway_id": "GW-001", "name": "Inventory & Credit Valid?", "gateway_type": "XOR", "condition_expression": "in_stock and credit_ok", "true_target": "ST-002", "false_target": "EX-001", "lane_id": "Lane_SYSTEM", "phase_id": 1 }
  ],
  "exception_loops": [
    { "loop_id": "EX-001", "source_activity_id": "GW-001", "recovery_activity_id": "ST-001", "trigger_error_code": "INVALID_OR_OOS", "max_retries": 3, "lane_id": "Lane_CUSTOMER" }
  ],
  "transitions": [
    { "source": "ST-001", "target": "ST-002" }
  ]
}
```

Compile it immediately:

```bash
python scripts/cli.py --action export-suite --ir examples/order_approval.ir.json --target-dir ./out
```

---

## Directory Structure

```text
BPMNArchitect/
├── SKILL.md                             # Skill rules & Camunda 5.20 layout invariants
├── README.md                            # Quickstart & 2-Layer JSON IR schema
├── core/
│   └── b_p_m_n_architect_det_harness.py # Deterministic harness & metrics
├── scripts/
│   └── cli.py                           # Click CLI (--action export-suite / verify-bpmn / --ir)
├── src/
│   └── bpmn_process_compiler.py         # BPMN 2.0 compiler, verifiers & Camunda Studio generator
├── examples/                            # Generic Order Approval demo (.bpmn, .ir.json, .puml, .mermaid & HTML Studio)
├── modules/DiagramKit/                  # Optional C4 / PlantUML rendering utilities
└── tests/                               # Pytest & unittest verification suite
```
