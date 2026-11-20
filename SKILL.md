---
name: BPMNArchitect
description: Generic BPMN 2.0 Business Process Modeling, Auditing, and Visualization
  skill. Models, validates, and renders formal BPMN 2.0 activity diagrams (PlantUML
  .puml) and interactive Mermaid.js viewers (.html). Incorporates Unified ID Taxonomy
  (ST-xxx, EX-xxx, GW-xxx, RF-xxx), Dead-End Elimination (EX-001..007), Dynamic Polymorphic
  Technical Hops ([CODE] vs [CORE]), 4-Tier Quality Gates, and UTOP Graph Traceability.
version: 2.1.0
status: active
changed_at: 2026-11-20
capabilities:
- gutter-detour-invariant
risk_class: TIER_1
approval_checkpoints:
- scope_confirmation
- security_confirmation
domain_adapter_contract:
  version: 3.1.0
  boundary: deterministic_p1_and_agentic_bdi
  mece_demarcation: Canonical owner of BPMNArchitect domain operations within the
    Antigravity 9-stage enterprise lifecycle.
  validation: pydantic_or_dataclass_schema
---

# BPMNArchitect — Generic BPMN 2.0 Process Modeling & Visualization Skill

> **Expertise**: bpmn-2-0-modeling, plantuml-activity-diagrams, mermaid-workflow-graphs, process-auditing, exception-loop-design, utop-traceability-wiring  
> **Input Formats**: Plain Text Process Descriptions, SRS, Use Cases 3.0 (`UC-xxx.md`), User Stories (`US-xxx`), Architecture Specs  
> **Output Formats**: Standard Camunda BPMN 2.0 XML (`.bpmn` with full BPMNDI Shapes & Edge Waypoints), PlantUML Activity Diagrams (`.puml`), Native Mermaid.js (`.mermaid`), Interactive Camunda HTML Viewers (`.html`), Process Context Specs (`.md`)

---

## 1. Overview & Generic Design Principles

**`BPMNArchitect`** is the canonical, domain-agnostic process modeling skill. It can model, validate, audit, and render formal BPMN 2.0 workflows for **any business process**, whether software engineering, enterprise operations, research, financial planning, or document crafting.

### Core Architectural Axioms
1. **Generic & Reusable**: `BPMNArchitect` contains instructions for process modeling in general. System-specific process specifications (such as the Universal Working Harness 37-step model) live in project context directories (`docs/diagrams/UNIVERSAL_WORKING_HARNESS_BPMN_SPEC.md`).
2. **Camunda BPMN 2.0 & Multi-Format First-Class Standard**: All process models MUST be exportable as standard **Camunda BPMN 2.0 XML (`.bpmn`)** containing complete **Diagram Interchange (BPMNDI)** specifications: every node MUST have `<bpmndi:BPMNShape>` with precise bounds, and every sequence flow MUST have `<bpmndi:BPMNEdge>` with explicit `<di:waypoint>` coordinates so they render clean connecting arrows in Camunda Modeler without disconnected nodes. Models are also rendered using **Native Mermaid.js** and **PlantUML Activity Diagrams (`.puml`)**.
3. **Start Event Flexibility**: A valid process MUST have at least one Start Event ($\ge 1$). Multiple Start Events with distinct triggers (Message, Timer, Signal, None) are explicitly allowed.

---

## 2. Standard Taxonomy & Rules

### 2.1 Unified ID System
Every step, exception route, gateway, and reflection circle MUST have a standardized ID:
- **`ST-xxx` (Happy Path Steps)**: `ST-001`, `ST-002`, ... `ST-037` (Sequential 3-digit zero-padded IDs).
- **`EX-xxx` (Unhappy Exception Branches)**: `EX-001` to `EX-007` (Auto-heal recovery loops & escalations).
- **`GW-xxx` (Decision Gateways)**: `GW-001` to `GW-004` (Conditional decision gateways).
- **`RF-xxx` (Reflection Circles)**: `RF-001` (30s micro), `RF-002` (1m meso), `RF-003` (3m macro).

### 2.2 Strict 4-Type Color & Badge Taxonomy
- 🔵 **`[CORE]` Universal Path** (`#0f172a` container / `#38bdf8` border): Baseline path followed by all work types (General Vibe Working, Research, Documents, Ops, Strategy, and Harness Nodes).
- 🟣 **`[CODE]` Technical Vibe Coding** (`#3b0764` container / `#c084fc` border): Deep engineering sub-task hops for Vibe Coding (AST 3-Way Merges, DB Schema Migrations, SAST Scans, Fast-Forward Git PR Merges, Infrastructure Deploy).
- 🔴 **`[EX]` Exception Auto-Heal** (`#450a0a` container / `#ef4444` border): Unhappy exception recovery loops (`EX-001` to `EX-007`).
- 🟠 **`[GW]` Decision & Quality Gateways** (`#fb923c` border): Gateways and 4-tier Quality Gates (`GW-001` to `GW-004`).

### 2.3 Dead-End Elimination Rule
No exception or rejection branch may terminate in a silent "Halt" or un-noticed dead end. Every rejection path MUST emit an explicit EBQC friction signal (e.g. `ERR_ARCH_REJECTED`), notify responsible roles, and loop back to a valid recovery node or scope re-negotiation (`ST-003`).

### 2.4 4-Tier Quality Gate Rule
Quality validation is enforced across 4 granularity levels:
1. **Subtask Quality Gate (`ST-018` / `RF-001`)**: Micro-timebox sandbox quality validation (2m subtask level).
2. **Task Quality Gate (`GW-003` / `ST-025` / `RF-002`)**: Meso-timebox staging quality validation ($\text{EAI} \ge 0.98$).
3. **Epic Integration Quality Gate (`ST-022` / `GW-001`)**: Tier 3 inter-task & architectural contract validation via Dual Architecture Sign-Off Gate (`GW-001`).

4. **Sprint Quality Gate (`ST-032` / `ST-035` / `RF-003`)**: Macro-timebox release & retrospective quality validation (15m sprint level).

### 2.5 Unified Task Representation Principle
Planning, reviews, UTOP asset generation, QualityGate testing, and retrospective reflection circles are NOT out-of-band rituals. They are **normal, explicit tasks (Nodes)** decomposed directly from **Capability Gaps (`CAP-xxx`)** and initial user requests inside the Kahn DAG.

### 2.6 Camunda Modeler Ergonomics & Zero-Collision Layout Invariants
To ensure professional visual quality and eliminate any rendering overlap when opened in **Camunda Modeler 5.20+**:
1. **Mandatory Collaboration Pools & Swimlanes**: Every process model involving human roles and system engines MUST declare a `<bpmn:collaboration>` with a named `<bpmn:participant>` (Pool) and partitioned `<bpmn:laneSet>` with dedicated `<bpmn:lane>` elements. Processes without pools and lanes are strictly prohibited.
2. **Start Event Offset from Lane Headers**:
   - The Pool left boundary is at $x=160\text{px}$ and Lane headers occupy $x \in [160, 215]\text{px}$.
   - Every Start Event circle ($36 \times 36\text{px}$) MUST be placed with its center at $x \ge 270\text{px}$ (minimum $60\text{px}$ clearance from lane headers).
   - The Start Event's `<bpmndi:BPMNLabel>` MUST have $x \ge 230\text{px}$ and bounded width $\le 110\text{px}$ so text never collides with the vertical lane header line.
3. **Descriptive Step Names & Zero Text-Icon Overlap**:
   - Task boxes MUST use a minimum size of $180 \times 80\text{px}$ (or $190 \times 80\text{px}$ for longer titles).
   - Task `name` attributes MUST be formatted with an explicit newline entity (`&#10;`):
     - Line 1: Concise action name (e.g. `ST-001: Report Breakdown`).
     - Line 2: Rule / UC reference (e.g. `(UC-TYCRM-001 Intake)`).
   - This keeps the text centered and compact ($\approx 30\text{px}$ high), leaving the top $25\text{px}$ completely clear for the top-left task type icon (User/Service/Script marker), preventing any text-icon collision.
4. **Dedicated Gateway & Event Label Placement**:
   - Every Gateway diamond ($50 \times 50\text{px}$) MUST have `isMarkerVisible="true"` and an explicit `<bpmndi:BPMNLabel>` with `<dc:Bounds x="{gx-35}" y="{gy-40}" width="120" height="25" />` positioned $30\text{px}$ above the diamond in the lane's top gutter channel.
   - Gateway labels must never sit on top of gateway diamonds or sequence flows.
5. **Sequence Flow Label Offsets (Anti-Line Cutting Invariant)**:
   - Sequence flow condition labels MUST NEVER be drawn across waypoint line strokes.
   - For horizontal segments $(x_1, y) \to (x_2, y)$, `<bpmndi:BPMNLabel>` MUST be offset by $\Delta y = -22\text{px}$ (above) or $+8\text{px}$ (below the line).
   - For vertical segments $(x, y_1) \to (x, y_2)$, `<bpmndi:BPMNLabel>` MUST be placed to the right with $\Delta x \ge +15\text{px}$ (e.g. at $x + 15$), never straddling the vertical line.
   - Unconditional forward flows between tasks (e.g. `ST-001 -> ST-002`) MUST omit redundant text names to eliminate visual clutter.
6. **Zero Component Overlap & Gutter Detour Routing**:
   - Every task, gateway, and label must occupy a distinct, collision-free coordinate box $(x, y, w, h)$.
   - Sequential columns must maintain $\Delta x \ge 220\text{px}$ clearance.
   - **Gutter Detour Invariant**: Feedback, rework, and rejection loops (e.g. `EX-001`, `Reject -> Rework`) MUST NEVER traverse through the interior or boundary of intermediate task boxes. They must route through dedicated lane gutters (top gutter $y_{lane\_top} + 25\text{px}$ or bottom gutter $y_{lane\_bottom} - 25\text{px}$) with $\ge 25\text{px}$ clearance from all task boxes.
   - Diagrams MUST pass formal mathematical line-box intersection verification (`verify_layout()`).
7. **Anti-Arrow Overlap Invariant (Strict Segment Disjointness)**:
   - Sequence flow arrows and line segments MUST NEVER share identical or collinear overlapping coordinates ($\text{length}(\text{seg}_1 \cap \text{seg}_2) = 0$).
   - Multiple flows exiting the same gateway must branch from distinct gateway ports (e.g. top $(g_x + 25, g_y)$, right $(g_x + 50, g_y + 25)$, bottom $(g_x + 25, g_y + 50)$).
   - Parallel or adjacent return/rework loops must run in dedicated parallel gutter tracks spaced by $\Delta \ge 25\text{px}$ (e.g. track 1 at $y=475\text{px}$, track 2 at $y=505\text{px}$, or separate $x$-channels $\Delta x \ge 25\text{px}$).
   - All models MUST pass mathematical segment overlap verification (`check_arrow_overlaps.py` returns `0`).

---

## 3. Authoring Workflow

```
Step 1: Ingest Requirements / Use Cases / Process Facts
        │
        ▼
Step 2: Assign Swimlanes (Human Node, Code Node, Agent Node Swarm)
        │
        ▼
Step 3: Apply Unified ID System (ST-xxx, EX-xxx, GW-xxx, RF-xxx)
        │
        ▼
Step 4: Check Dead-End Elimination & 4-Tier Quality Gates
        │
        ▼
Step 5: Compile 2-Layer IR (`*.ir.json`) -> Verified Camunda `.bpmn` + Interactive `bpmn-js` Studio (`.html`) + `.puml` + `.mermaid` + `_SPEC.md`
```

### CLI & Python Engine Commands
- **Export Canonical SOP Suite (`53.REF.07` & `53.REF.08`)**:
  `python scripts/cli.py --action export-suite --target-dir examples`
- **Compile Custom 2-Layer Business IR (`*.ir.json`)**:
  `python scripts/cli.py --action export-suite --ir path/to/process.ir.json --target-dir out`
- **Verify Semantic Reachability, Zero Box Cuts & Zero Arrow Overlaps**:
  `python scripts/cli.py --action verify-bpmn`

---

## 4. UTOP Traceability Integration

`BPMNArchitect` links directly to KùzuDB graph database:
- Maps `BPMN Node ID` $\to$ `DAGNodeID` $\to$ `CAP-xxx` $\to$ `UTOPTrace`.
- Enforces 100% diagram traceability coverage score ($\text{CoverageScore}_{\text{BPMN}} = 1.0$).

---

## MECE Boundary & DRY Delegation Contract (`mece_demarcation_contract`)

- **Scope Demarcation**: Canonical owner of BPMNArchitect domain operations within the Antigravity 9-stage enterprise lifecycle.
- **DRY SSOT Invariant**: Zero duplicate business logic; shared persistence and telemetry delegate to `TaskManager` and `QualityGate`.
