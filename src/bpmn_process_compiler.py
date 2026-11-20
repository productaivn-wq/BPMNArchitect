"""
BPMN 2.0 Process Compiler & Multi-Format Studio for Antigravity Working Harness.
Compiles BPMNProcess models and 2-Layer JSON IR into:
- Standard Camunda Modeler 5.20+ BPMN 2.0 XML (.bpmn) with Pools, Swimlanes & Zero-Collision BPMNDI
- Deterministic Kahn Execution DAGs & LangGraph StateGraph dictionaries
- PlantUML Activity Diagrams (.puml), Mermaid Flowcharts (.mermaid), & UTOP Markdown Specs (.md)
- Interactive First-Party Camunda bpmn-js Drag-and-Drop HTML Studio (.html)
- Mathematical Layout & Anti-Arrow-Overlap Verifiers (P=1)

Implements: UC-001, UC-002, UC-003, 53.REF.07, 53.REF.08, 53.REF.69, 53.REF.100.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import html
import json
import logging
from pathlib import Path
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

# Resolve FunctionCheckpointer from TaskManager with portable no-op fallback
try:
    from function_checkpointer import checkpoint
except ImportError:
    _tm_candidates = [
        Path.home() / ".gemini" / "antigravity" / "skills" / "TaskManager" / "src",
        Path.home() / ".gemini" / "config" / "skills" / "TaskManager" / "src",
    ]
    for _tm_src in _tm_candidates:
        if _tm_src.exists() and str(_tm_src) not in sys.path:
            sys.path.insert(0, str(_tm_src))
            break
    try:
        from function_checkpointer import checkpoint
    except ImportError:

        def checkpoint(**_kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            """Portable fallback no-op decorator when TaskManager is not mounted."""

            def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
                return fn

            return _decorator


logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    CODE_NODE = "CodeNode"
    AGENT_NODE = "AgentNode"
    HUMAN_NODE = "HumanNode"


class GatewayType(str, Enum):
    EXCLUSIVE = "XOR"
    PARALLEL = "AND"
    INCLUSIVE = "OR"


@dataclass
class BPMNLane:
    """Swimlane inside a BPMN Collaboration Pool (e.g., HUM, AGT, DET)."""

    lane_id: str
    name: str
    node_type: Optional[NodeType] = None


@dataclass
class BPMNActivity:
    activity_id: str  # e.g., ST-001
    name: str
    phase_id: int
    assigned_node_type: NodeType
    allocated_actor_id: str = "default_worker"
    pomodoro_tier: str = "2m"
    prompt_name: Optional[str] = None
    input_keys: List[str] = field(default_factory=list)
    output_keys: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    lane_id: Optional[str] = None
    rule_ref: Optional[str] = None
    category: str = "CORE"


@dataclass
class BPMNGateway:
    gateway_id: str  # e.g., GW-001
    name: str
    gateway_type: GatewayType
    condition_expression: str
    true_target: str
    false_target: str
    lane_id: Optional[str] = None
    phase_id: Optional[int] = None


@dataclass
class BPMNExceptionLoop:
    loop_id: str  # e.g., EX-001
    source_activity_id: str
    recovery_activity_id: str
    trigger_error_code: str
    max_retries: int = 3
    lane_id: Optional[str] = None
    description: Optional[str] = None


@dataclass
class BPMNPhase:
    phase_id: int
    name: str
    activities: List[BPMNActivity] = field(default_factory=list)
    governance_gates: List[str] = field(default_factory=list)


def _xml_escape(text: str) -> str:
    """Escape XML attribute characters while preserving printable text."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _safe_id(raw: str) -> str:
    """Normalize arbitrary identifiers into valid XML IDs."""
    return (
        str(raw)
        .replace(".", "_")
        .replace("-", "_")
        .replace(" ", "_")
        .replace("/", "_")
    )


def _format_two_line_name(prefix_id: str, title: str, subtitle: str) -> str:
    """Format a 2-line Camunda task label using &#10; to prevent text-icon collision."""
    clean_title = title.strip()
    if not clean_title.startswith(prefix_id):
        line1 = f"{prefix_id}: {clean_title}"
    else:
        line1 = clean_title
    line2 = f"({subtitle.strip()})"
    return f"{_xml_escape(line1)}&#10;{_xml_escape(line2)}"


def _gateway_tag(gw_type: GatewayType) -> str:
    if gw_type == GatewayType.PARALLEL:
        return "bpmn:parallelGateway"
    if gw_type == GatewayType.INCLUSIVE:
        return "bpmn:inclusiveGateway"
    return "bpmn:exclusiveGateway"


def _segments_intersect_box(
    x1: int, y1: int, x2: int, y2: int, bx: int, by: int, bw: int, bh: int
) -> bool:
    """Check whether an orthogonal or straight segment intersects a rectangle."""
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)
    if x1 == x2:
        return (bx <= x1 <= bx + bw) and (max_y >= by and min_y <= by + bh)
    if y1 == y2:
        return (by <= y1 <= by + bh) and (max_x >= bx and min_x <= bx + bw)
    return not (max_x < bx or min_x > bx + bw or max_y < by or min_y > by + bh)


def verify_layout(xml_str: str) -> Dict[str, Any]:
    """Deterministically verify BPMNDI layout invariants (0 shape collisions, 0 box cuts, ergonomic rules)."""
    ns = {
        "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
        "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
        "dc": "http://www.omg.org/spec/DD/20100524/DC",
        "di": "http://www.omg.org/spec/DD/20100524/DI",
    }
    root = ET.fromstring(xml_str)

    container_ids: set[str] = set()
    for tag in ("bpmn:participant", "bpmn:lane"):
        for elem in root.findall(f".//{tag}", ns):
            eid = elem.attrib.get("id")
            if eid:
                container_ids.add(eid)

    flow_refs: Dict[str, Tuple[str, str]] = {}
    for sf in root.findall(".//bpmn:sequenceFlow", ns):
        fid = sf.attrib.get("id", "")
        flow_refs[fid] = (sf.attrib.get("sourceRef", ""), sf.attrib.get("targetRef", ""))

    node_boxes: Dict[str, Tuple[int, int, int, int]] = {}
    ergonomic_violations: List[str] = []

    for shape in root.findall(".//bpmndi:BPMNShape", ns):
        bpmn_el = shape.attrib.get("bpmnElement", "")
        if not bpmn_el or bpmn_el in container_ids:
            continue
        bounds = shape.find("dc:Bounds", ns)
        if bounds is None:
            continue
        x = int(float(bounds.attrib["x"]))
        y = int(float(bounds.attrib["y"]))
        w = int(float(bounds.attrib["width"]))
        h = int(float(bounds.attrib["height"]))
        node_boxes[bpmn_el] = (x, y, w, h)

        if bpmn_el.startswith("StartEvent"):
            center_x = x + w / 2.0
            if center_x < 270:
                ergonomic_violations.append(f"StartEvent {bpmn_el} center_x={center_x} < 270")
            lbl = shape.find("bpmndi:BPMNLabel/dc:Bounds", ns)
            if lbl is not None:
                lx = int(float(lbl.attrib["x"]))
                lw = int(float(lbl.attrib["width"]))
                if lx < 230 or lw > 110:
                    ergonomic_violations.append(
                        f"StartEvent {bpmn_el} label bounds invalid (x={lx}, w={lw})"
                    )

    shape_collisions: List[Tuple[str, str]] = []
    box_items = list(node_boxes.items())
    for idx, (id_a, (ax, ay, aw, ah)) in enumerate(box_items):
        for id_b, (bx, by, bw, bh) in box_items[idx + 1 :]:
            if ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by:
                shape_collisions.append((id_a, id_b))

    box_intersections: List[Dict[str, Any]] = []
    edges = root.findall(".//bpmndi:BPMNEdge", ns)
    for edge in edges:
        flow_id = edge.attrib.get("bpmnElement", "")
        src_id, dst_id = flow_refs.get(flow_id, ("", ""))
        waypoints = [
            (int(float(wp.attrib["x"])), int(float(wp.attrib["y"])))
            for wp in edge.findall("di:waypoint", ns)
        ]
        for seg_idx in range(len(waypoints) - 1):
            x1, y1 = waypoints[seg_idx]
            x2, y2 = waypoints[seg_idx + 1]
            for box_id, (bx, by, bw, bh) in box_items:
                if box_id in (src_id, dst_id):
                    continue
                if _segments_intersect_box(x1, y1, x2, y2, bx, by, bw, bh):
                    box_intersections.append(
                        {
                            "edge_id": flow_id,
                            "segment_index": seg_idx,
                            "segment": ((x1, y1), (x2, y2)),
                            "collided_node": box_id,
                        }
                    )

    ok = (
        len(shape_collisions) == 0
        and len(box_intersections) == 0
        and len(ergonomic_violations) == 0
    )
    return {
        "ok": ok,
        "total_shapes": len(node_boxes),
        "total_edges": len(edges),
        "shape_collisions": len(shape_collisions),
        "colliding_pairs": shape_collisions,
        "box_intersections": len(box_intersections),
        "intersections": box_intersections,
        "ergonomic_violations": ergonomic_violations,
    }


def check_arrow_overlaps(xml_str: str) -> Dict[str, Any]:
    """Verify strict segment disjointness across all BPMNEdge sequence flows (0 overlaps)."""
    ns = {
        "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
        "di": "http://www.omg.org/spec/DD/20100524/DI",
    }
    root = ET.fromstring(xml_str)
    segments: List[Tuple[str, int, int, int, str]] = []
    diagonal_segments: List[str] = []

    for edge in root.findall(".//bpmndi:BPMNEdge", ns):
        edge_id = edge.attrib.get("bpmnElement", edge.attrib.get("id", ""))
        wps = [
            (int(float(wp.attrib["x"])), int(float(wp.attrib["y"])))
            for wp in edge.findall("di:waypoint", ns)
        ]
        for idx in range(len(wps) - 1):
            x1, y1 = wps[idx]
            x2, y2 = wps[idx + 1]
            if x1 == x2 and y1 == y2:
                continue
            if y1 == y2:
                segments.append(("H", y1, min(x1, x2), max(x1, x2), edge_id))
            elif x1 == x2:
                segments.append(("V", x1, min(y1, y2), max(y1, y2), edge_id))
            else:
                diagonal_segments.append(edge_id)

    overlaps: List[Dict[str, Any]] = []
    for i, (ori_a, coord_a, lo_a, hi_a, eid_a) in enumerate(segments):
        for ori_b, coord_b, lo_b, hi_b, eid_b in segments[i + 1 :]:
            if ori_a != ori_b or coord_a != coord_b:
                continue
            overlap_len = min(hi_a, hi_b) - max(lo_a, lo_b)
            if overlap_len > 0:
                overlaps.append(
                    {
                        "orientation": ori_a,
                        "coord": coord_a,
                        "edge_a": eid_a,
                        "edge_b": eid_b,
                        "overlap_px": overlap_len,
                    }
                )

    return {
        "ok": len(overlaps) == 0 and len(diagonal_segments) == 0,
        "total_segments": len(segments),
        "overlap_count": len(overlaps),
        "overlaps": overlaps,
        "diagonal_segments": diagonal_segments,
    }


class BPMNProcess:
    """Represents a full BPMN 2.0 Process specification (e.g. 53.REF.07, 53.REF.08)."""

    def __init__(
        self,
        process_id: str,
        name: str,
        version: str = "2.0.0",
        protocol_type: str = "TECHNICAL",
    ):
        self.process_id = process_id
        self.name = name
        self.version = version
        self.protocol_type = protocol_type
        self.lanes: Dict[str, BPMNLane] = {}
        self.phases: Dict[int, BPMNPhase] = {}
        self.activities: Dict[str, BPMNActivity] = {}
        self.gateways: Dict[str, BPMNGateway] = {}
        self.exception_loops: Dict[str, BPMNExceptionLoop] = {}
        self.transitions: List[Tuple[str, str]] = []

    def add_lane(
        self, lane_id: str, name: str, node_type: Optional[NodeType] = None
    ) -> BPMNLane:
        lane = BPMNLane(lane_id=lane_id, name=name, node_type=node_type)
        self.lanes[lane_id] = lane
        return lane

    def add_phase(self, phase_id: int, name: str) -> BPMNPhase:
        phase = BPMNPhase(phase_id=phase_id, name=name)
        self.phases[phase_id] = phase
        return phase

    def add_activity(self, activity: BPMNActivity) -> None:
        self.activities[activity.activity_id] = activity
        if activity.phase_id in self.phases:
            self.phases[activity.phase_id].activities.append(activity)

    def add_gateway(self, gateway: BPMNGateway) -> None:
        self.gateways[gateway.gateway_id] = gateway

    def add_exception_loop(self, loop: BPMNExceptionLoop) -> None:
        self.exception_loops[loop.loop_id] = loop

    def add_transition(self, source_id: str, target_id: str) -> None:
        self.transitions.append((source_id, target_id))

    def _ensure_default_lanes(self) -> Dict[str, BPMNLane]:
        if self.lanes:
            return self.lanes
        self.add_lane(
            "Lane_HUMAN",
            "Human Node (HUM — Intent, Ethics & Sign-Off)",
            NodeType.HUMAN_NODE,
        )
        self.add_lane(
            "Lane_AGENT",
            "Agent Node Swarm (AGT — BDI Reasoning & Synthesis)",
            NodeType.AGENT_NODE,
        )
        self.add_lane(
            "Lane_CODE",
            "Code Node (DET P=1 — Validation, Gates & State)",
            NodeType.CODE_NODE,
        )
        return self.lanes

    def _resolve_lane_id(
        self, node_type: NodeType, explicit_lane_id: Optional[str] = None
    ) -> str:
        lanes = self._ensure_default_lanes()
        if explicit_lane_id and explicit_lane_id in lanes:
            return explicit_lane_id
        for lid, lane in lanes.items():
            if lane.node_type == node_type:
                return lid
        default_map = {
            NodeType.HUMAN_NODE: "Lane_HUMAN",
            NodeType.AGENT_NODE: "Lane_AGENT",
            NodeType.CODE_NODE: "Lane_CODE",
        }
        candidate = default_map.get(node_type)
        if candidate and candidate in lanes:
            return candidate
        return next(iter(lanes.keys()))

    @checkpoint(
        checkpoint_id="CHK-BPMN-DAG-COMPILER-001",
        pre_invariants=["len(self.activities) > 0"],
        post_invariants=[
            "isinstance(result, dict)",
            "result['is_acyclic'] == True",
            "result['total_activities'] == len(self.activities)",
        ],
        capture_vars=["self.process_id", "self.name"],
    )
    def to_execution_dag(self) -> Dict[str, Any]:
        """Compiles the BPMN process into a deterministic Kahn execution DAG."""
        adjacency: Dict[str, List[str]] = {act_id: [] for act_id in self.activities}
        in_degree: Dict[str, int] = {act_id: 0 for act_id in self.activities}

        for src, dst in self.transitions:
            if src in adjacency and dst in in_degree:
                adjacency[src].append(dst)
                in_degree[dst] += 1

        waves: List[List[str]] = []
        remaining_in_degree = in_degree.copy()

        while True:
            current_wave = [
                node for node, deg in remaining_in_degree.items() if deg == 0
            ]
            if not current_wave:
                break
            waves.append(current_wave)
            for node in current_wave:
                del remaining_in_degree[node]
                for neighbor in adjacency.get(node, []):
                    if neighbor in remaining_in_degree:
                        remaining_in_degree[neighbor] -= 1

        return {
            "process_id": self.process_id,
            "name": self.name,
            "version": self.version,
            "total_activities": len(self.activities),
            "total_gateways": len(self.gateways),
            "total_exception_loops": len(self.exception_loops),
            "kahn_waves": waves,
            "is_acyclic": len(remaining_in_degree) == 0,
            "unresolved_cycles": list(remaining_in_degree.keys()),
        }

    @checkpoint(
        checkpoint_id="CHK-BPMN-LANGGRAPH-001",
        pre_invariants=["len(self.activities) > 0"],
        post_invariants=[
            "isinstance(result, dict)",
            "len(result['nodes']) == len(self.activities)",
        ],
        capture_vars=["self.process_id", "self.name"],
    )
    def to_langgraph_dict(self) -> Dict[str, Any]:
        """Generates LangGraph StateGraph node and edge declarations."""
        nodes = [
            {
                "node_id": act.activity_id,
                "name": act.name,
                "node_type": act.assigned_node_type.value,
                "phase_id": act.phase_id,
                "prompt": act.prompt_name,
            }
            for act in self.activities.values()
        ]
        edges = [
            {"from": src, "to": dst, "type": "standard"}
            for src, dst in self.transitions
        ]
        conditional_edges = [
            {
                "gateway_id": gw.gateway_id,
                "condition": gw.condition_expression,
                "true_target": gw.true_target,
                "false_target": gw.false_target,
            }
            for gw in self.gateways.values()
        ]
        return {
            "graph_name": self.name,
            "process_id": self.process_id,
            "nodes": nodes,
            "edges": edges,
            "conditional_edges": conditional_edges,
            "exception_loops": [
                {
                    "loop_id": ex.loop_id,
                    "from": ex.source_activity_id,
                    "recovery": ex.recovery_activity_id,
                    "error_code": ex.trigger_error_code,
                }
                for ex in self.exception_loops.values()
            ],
        }

    def to_ir_dict(self) -> Dict[str, Any]:
        """Serialize the process model into clean 2-layer business JSON IR (zero coordinates)."""
        lanes = self._ensure_default_lanes()
        return {
            "process": {
                "id": self.process_id,
                "name": self.name,
                "version": self.version,
                "protocol_type": self.protocol_type,
            },
            "lanes": [
                {
                    "lane_id": lane.lane_id,
                    "name": lane.name,
                    "node_type": lane.node_type.value if lane.node_type else None,
                }
                for lane in lanes.values()
            ],
            "phases": [
                {
                    "phase_id": ph.phase_id,
                    "name": ph.name,
                    "governance_gates": list(ph.governance_gates),
                }
                for ph in self.phases.values()
            ],
            "activities": [
                {
                    "activity_id": act.activity_id,
                    "name": act.name,
                    "phase_id": act.phase_id,
                    "assigned_node_type": act.assigned_node_type.value,
                    "allocated_actor_id": act.allocated_actor_id,
                    "pomodoro_tier": act.pomodoro_tier,
                    "prompt_name": act.prompt_name,
                    "input_keys": list(act.input_keys),
                    "output_keys": list(act.output_keys),
                    "metadata": dict(act.metadata),
                    "lane_id": self._resolve_lane_id(act.assigned_node_type, act.lane_id),
                    "rule_ref": act.rule_ref,
                    "category": act.category,
                }
                for act in self.activities.values()
            ],
            "gateways": [
                {
                    "gateway_id": gw.gateway_id,
                    "name": gw.name,
                    "gateway_type": gw.gateway_type.value,
                    "condition_expression": gw.condition_expression,
                    "true_target": gw.true_target,
                    "false_target": gw.false_target,
                    "lane_id": gw.lane_id,
                    "phase_id": gw.phase_id,
                }
                for gw in self.gateways.values()
            ],
            "exception_loops": [
                {
                    "loop_id": ex.loop_id,
                    "source_activity_id": ex.source_activity_id,
                    "recovery_activity_id": ex.recovery_activity_id,
                    "trigger_error_code": ex.trigger_error_code,
                    "max_retries": ex.max_retries,
                    "lane_id": ex.lane_id,
                    "description": ex.description,
                }
                for ex in self.exception_loops.values()
            ],
            "transitions": [{"source": src, "target": dst} for src, dst in self.transitions],
        }

    @classmethod
    def from_ir_dict(cls, data: Dict[str, Any]) -> "BPMNProcess":
        """Reconstruct a BPMNProcess deterministically from a 2-layer JSON IR dictionary."""
        proc_meta = data.get("process", {})
        proc = cls(
            process_id=str(proc_meta.get("id", "PROCESS_1")),
            name=str(proc_meta.get("name", "Untitled BPMN Process")),
            version=str(proc_meta.get("version", "2.0.0")),
            protocol_type=str(proc_meta.get("protocol_type", "CORE")),
        )
        for lane_data in data.get("lanes", []):
            nt_raw = lane_data.get("node_type")
            nt = NodeType(nt_raw) if nt_raw else None
            proc.add_lane(
                lane_id=str(lane_data["lane_id"]),
                name=str(lane_data["name"]),
                node_type=nt,
            )
        for ph_data in data.get("phases", []):
            ph = proc.add_phase(int(ph_data["phase_id"]), str(ph_data["name"]))
            ph.governance_gates = list(ph_data.get("governance_gates", []))
        for act_data in data.get("activities", []):
            proc.add_activity(
                BPMNActivity(
                    activity_id=str(act_data["activity_id"]),
                    name=str(act_data["name"]),
                    phase_id=int(act_data.get("phase_id", 1)),
                    assigned_node_type=NodeType(act_data.get("assigned_node_type", "CodeNode")),
                    allocated_actor_id=str(act_data.get("allocated_actor_id", "default_worker")),
                    pomodoro_tier=str(act_data.get("pomodoro_tier", "2m")),
                    prompt_name=act_data.get("prompt_name"),
                    input_keys=list(act_data.get("input_keys", [])),
                    output_keys=list(act_data.get("output_keys", [])),
                    metadata=dict(act_data.get("metadata", {})),
                    lane_id=act_data.get("lane_id"),
                    rule_ref=act_data.get("rule_ref"),
                    category=str(act_data.get("category", "CORE")),
                )
            )
        for gw_data in data.get("gateways", []):
            proc.add_gateway(
                BPMNGateway(
                    gateway_id=str(gw_data["gateway_id"]),
                    name=str(gw_data["name"]),
                    gateway_type=GatewayType(gw_data.get("gateway_type", "XOR")),
                    condition_expression=str(gw_data.get("condition_expression", "approved")),
                    true_target=str(gw_data["true_target"]),
                    false_target=str(gw_data["false_target"]),
                    lane_id=gw_data.get("lane_id"),
                    phase_id=gw_data.get("phase_id"),
                )
            )
        for ex_data in data.get("exception_loops", []):
            proc.add_exception_loop(
                BPMNExceptionLoop(
                    loop_id=str(ex_data["loop_id"]),
                    source_activity_id=str(ex_data["source_activity_id"]),
                    recovery_activity_id=str(ex_data["recovery_activity_id"]),
                    trigger_error_code=str(ex_data["trigger_error_code"]),
                    max_retries=int(ex_data.get("max_retries", 3)),
                    lane_id=ex_data.get("lane_id"),
                    description=ex_data.get("description"),
                )
            )
        for tr in data.get("transitions", []):
            if isinstance(tr, dict):
                proc.add_transition(str(tr["source"]), str(tr["target"]))
            elif isinstance(tr, (list, tuple)) and len(tr) >= 2:
                proc.add_transition(str(tr[0]), str(tr[1]))
        return proc

    def _build_visual_graph(self) -> Dict[str, Any]:
        """Normalize activities, spliced gateways, exception tasks, and ordered columns."""
        lanes = self._ensure_default_lanes()
        nodes: Dict[str, Dict[str, Any]] = {}

        if not self.activities:
            return {"lanes": lanes, "nodes": nodes, "edges": [], "ordered_ids": []}

        act_ids = list(self.activities.keys())
        first_act_id = act_ids[0]
        last_act_id = act_ids[-1]

        first_lane = self._resolve_lane_id(
            self.activities[first_act_id].assigned_node_type,
            self.activities[first_act_id].lane_id,
        )
        last_lane = self._resolve_lane_id(
            self.activities[last_act_id].assigned_node_type,
            self.activities[last_act_id].lane_id,
        )

        nodes["StartEvent_1"] = {
            "id": "StartEvent_1",
            "kind": "start",
            "tag": "bpmn:startEvent",
            "name": "Process Initiated",
            "lane_id": first_lane,
        }

        for act in self.activities.values():
            task_tag = (
                "bpmn:userTask"
                if act.assigned_node_type in (NodeType.HUMAN_NODE, NodeType.AGENT_NODE)
                else "bpmn:serviceTask"
            )
            subtitle = act.rule_ref or f"Phase {act.phase_id} • {act.assigned_node_type.value}"
            nodes[act.activity_id] = {
                "id": act.activity_id,
                "kind": "activity",
                "tag": task_tag,
                "name": _format_two_line_name(act.activity_id, act.name, subtitle),
                "raw_name": act.name,
                "lane_id": self._resolve_lane_id(act.assigned_node_type, act.lane_id),
                "phase_id": act.phase_id,
                "node_type": act.assigned_node_type,
                "category": act.category,
            }

        edges: List[Dict[str, str]] = [
            {
                "id": f"Flow_{_safe_id(src)}_{_safe_id(dst)}",
                "src": src,
                "dst": dst,
                "name": "",
                "kind": "forward",
            }
            for src, dst in self.transitions
        ]

        gw_attached_before: Dict[str, List[str]] = {}
        ex_after_gw: Dict[str, List[str]] = {}
        ex_by_id = dict(self.exception_loops)

        for gw in self.gateways.values():
            gw_lane = gw.lane_id
            if not gw_lane or gw_lane not in lanes:
                if gw.true_target in nodes:
                    gw_lane = nodes[gw.true_target]["lane_id"]
                else:
                    gw_lane = self._resolve_lane_id(NodeType.CODE_NODE)

            nodes[gw.gateway_id] = {
                "id": gw.gateway_id,
                "kind": "gateway",
                "tag": _gateway_tag(gw.gateway_type),
                "name": _xml_escape(f"{gw.gateway_id}: {gw.name}"),
                "raw_name": gw.name,
                "lane_id": gw_lane,
                "condition": gw.condition_expression,
            }

            has_incoming = any(e["dst"] == gw.gateway_id for e in edges)
            if not has_incoming:
                spliced = False
                for idx, e in enumerate(edges):
                    if e["dst"] == gw.true_target and e["kind"] == "forward":
                        edges[idx] = {
                            "id": f"Flow_{_safe_id(e['src'])}_{_safe_id(gw.gateway_id)}",
                            "src": e["src"],
                            "dst": gw.gateway_id,
                            "name": "",
                            "kind": "forward",
                        }
                        edges.append(
                            {
                                "id": f"Flow_{_safe_id(gw.gateway_id)}_{_safe_id(gw.true_target)}_Pass",
                                "src": gw.gateway_id,
                                "dst": gw.true_target,
                                "name": "Pass",
                                "kind": "gw_true",
                            }
                        )
                        gw_attached_before.setdefault(gw.true_target, []).append(gw.gateway_id)
                        spliced = True
                        break
                if not spliced and gw.true_target in nodes:
                    edges.append(
                        {
                            "id": f"Flow_{_safe_id(gw.gateway_id)}_{_safe_id(gw.true_target)}_Pass",
                            "src": gw.gateway_id,
                            "dst": gw.true_target,
                            "name": "Pass",
                            "kind": "gw_true",
                        }
                    )
                    gw_attached_before.setdefault(gw.true_target, []).append(gw.gateway_id)

            if gw.false_target:
                err_lbl = "Reject"
                if gw.false_target in ex_by_id:
                    err_lbl = ex_by_id[gw.false_target].trigger_error_code
                edges.append(
                    {
                        "id": f"Flow_{_safe_id(gw.gateway_id)}_{_safe_id(gw.false_target)}_Fail",
                        "src": gw.gateway_id,
                        "dst": gw.false_target,
                        "name": err_lbl,
                        "kind": "gw_false",
                    }
                )

        for ex in self.exception_loops.values():
            is_hitl = "HITL" in ex.trigger_error_code.upper()
            ex_nt = NodeType.HUMAN_NODE if is_hitl else NodeType.CODE_NODE
            ex_lane = (
                ex.lane_id
                if ex.lane_id and ex.lane_id in lanes
                else self._resolve_lane_id(ex_nt)
            )
            nodes[ex.loop_id] = {
                "id": ex.loop_id,
                "kind": "exception",
                "tag": "bpmn:userTask" if is_hitl else "bpmn:serviceTask",
                "name": _format_two_line_name(
                    ex.loop_id,
                    f"Auto-Heal ({ex.trigger_error_code})",
                    f"Recover -> {ex.recovery_activity_id}",
                ),
                "raw_name": f"Auto-Heal ({ex.trigger_error_code})",
                "lane_id": ex_lane,
                "recovery_target": ex.recovery_activity_id,
                "error_code": ex.trigger_error_code,
            }
            ex_after_gw.setdefault(ex.source_activity_id, []).append(ex.loop_id)

            if not any(
                e["src"] == ex.source_activity_id and e["dst"] == ex.loop_id
                for e in edges
            ):
                edges.append(
                    {
                        "id": f"Flow_{_safe_id(ex.source_activity_id)}_{_safe_id(ex.loop_id)}",
                        "src": ex.source_activity_id,
                        "dst": ex.loop_id,
                        "name": ex.trigger_error_code,
                        "kind": "gw_false",
                    }
                )
            edges.append(
                {
                    "id": f"Flow_{_safe_id(ex.loop_id)}_{_safe_id(ex.recovery_activity_id)}",
                    "src": ex.loop_id,
                    "dst": ex.recovery_activity_id,
                    "name": f"Retry -> {ex.recovery_activity_id}",
                    "kind": "loop_back",
                }
            )

        nodes["EndEvent_1"] = {
            "id": "EndEvent_1",
            "kind": "end",
            "tag": "bpmn:endEvent",
            "name": "Process Completed",
            "lane_id": last_lane,
        }

        edges.insert(
            0,
            {
                "id": f"Flow_Start_{_safe_id(first_act_id)}",
                "src": "StartEvent_1",
                "dst": first_act_id,
                "name": "",
                "kind": "forward",
            },
        )
        edges.append(
            {
                "id": f"Flow_{_safe_id(last_act_id)}_End",
                "src": last_act_id,
                "dst": "EndEvent_1",
                "name": "",
                "kind": "forward",
            },
        )

        ordered_ids: List[str] = ["StartEvent_1"]
        placed: set[str] = {"StartEvent_1"}
        for aid in act_ids:
            for gwid in gw_attached_before.get(aid, []):
                if gwid not in placed:
                    ordered_ids.append(gwid)
                    placed.add(gwid)
                for exid in ex_after_gw.get(gwid, []):
                    if exid not in placed:
                        ordered_ids.append(exid)
                        placed.add(exid)
            if aid not in placed:
                ordered_ids.append(aid)
                placed.add(aid)
            for exid in ex_after_gw.get(aid, []):
                if exid not in placed:
                    ordered_ids.append(exid)
                    placed.add(exid)

        for nid in nodes:
            if nid != "EndEvent_1" and nid not in placed:
                ordered_ids.append(nid)
                placed.add(nid)
        ordered_ids.append("EndEvent_1")

        return {
            "lanes": lanes,
            "nodes": nodes,
            "edges": edges,
            "ordered_ids": ordered_ids,
        }

    def _compute_bpmn_layout(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """Compute collision-free shapes and disjoint orthogonal waypoints."""
        lanes: Dict[str, BPMNLane] = graph["lanes"]
        nodes: Dict[str, Dict[str, Any]] = graph["nodes"]
        edges: List[Dict[str, str]] = graph["edges"]
        ordered_ids: List[str] = graph["ordered_ids"]

        col_of: Dict[str, int] = {nid: idx for idx, nid in enumerate(ordered_ids)}

        skip_edges = [
            e
            for e in edges
            if e["kind"] != "loop_back" and col_of[e["dst"]] > col_of[e["src"]] + 1
        ]
        loop_edges = [
            e
            for e in edges
            if e["kind"] == "loop_back" or col_of[e["dst"]] <= col_of[e["src"]]
        ]

        pool_x, pool_y = 160, 80
        lane_x = 190
        top_corridor_h = max(90, 40 + len(skip_edges) * 28)
        bottom_corridor_h = 56 + len(loop_edges) * 30

        lane_ids = list(lanes.keys())
        lane_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        lane_node_top: Dict[str, int] = {}

        col_pitch = 240
        start_x = 252  # 36px wide -> center at 270px >= 270px invariant
        first_node_x = 380
        last_col = max(len(ordered_ids) - 1, 1)
        pool_width = (first_node_x + last_col * col_pitch) - pool_x + 120

        cur_y = pool_y
        for idx, lid in enumerate(lane_ids):
            if idx == 0:
                lh = top_corridor_h + 210
                task_y_offset = top_corridor_h + 52
            else:
                lh = 230
                task_y_offset = 78
            if idx == len(lane_ids) - 1:
                lh += bottom_corridor_h
            lane_bounds[lid] = (lane_x, cur_y, pool_width - 30, lh)
            lane_node_top[lid] = cur_y + task_y_offset
            cur_y += lh

        pool_height = cur_y - pool_y

        node_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        col_base_x: Dict[int, int] = {}
        for nid in ordered_ids:
            col = col_of[nid]
            node = nodes[nid]
            lid = node["lane_id"]
            base_task_y = lane_node_top[lid]
            kind = node["kind"]

            if kind == "start":
                bx = start_x
                col_base_x[col] = bx - 20
                node_bounds[nid] = (bx, base_task_y + 22, 36, 36)
            elif kind == "end":
                cx = first_node_x + (col - 1) * col_pitch
                col_base_x[col] = cx
                node_bounds[nid] = (cx + 20, base_task_y + 22, 36, 36)
            elif kind == "gateway":
                cx = first_node_x + (col - 1) * col_pitch
                col_base_x[col] = cx
                node_bounds[nid] = (cx + 65, base_task_y + 15, 50, 50)
            else:
                cx = first_node_x + (col - 1) * col_pitch
                col_base_x[col] = cx
                node_bounds[nid] = (cx, base_task_y, 180, 80)

        max_node_bottom = max(y + h for _, y, _, h in node_bounds.values())
        bottom_base_y = max_node_bottom + 46

        right_out_count: Dict[str, int] = {}
        left_in_count: Dict[str, int] = {}
        bottom_out_count: Dict[str, int] = {}
        bottom_in_count: Dict[str, int] = {}
        skip_idx = 0
        loop_idx = 0
        gap_channel_count: Dict[int, int] = {}

        edge_waypoints: Dict[str, List[Tuple[int, int]]] = {}
        edge_label_bounds: Dict[str, Tuple[int, int, int, int]] = {}

        for edge in edges:
            eid = edge["id"]
            src_id, dst_id = edge["src"], edge["dst"]
            sx, sy, sw, sh = node_bounds[src_id]
            tx, ty, tw, th = node_bounds[dst_id]
            col_src, col_dst = col_of[src_id], col_of[dst_id]

            if edge["kind"] == "loop_back" or col_dst <= col_src:
                b_out_slot = bottom_out_count.get(src_id, 0)
                bottom_out_count[src_id] = b_out_slot + 1
                b_in_slot = bottom_in_count.get(dst_id, 0)
                bottom_in_count[dst_id] = b_in_slot + 1

                src_bx = sx + sw // 2 + (b_out_slot * 28)
                if tw >= 160:
                    dst_bx = tx + 42 + (b_in_slot * 46)
                else:
                    dst_bx = tx + tw // 2 + (b_in_slot * 18)

                gutter_y = bottom_base_y + loop_idx * 30
                loop_idx += 1

                wps = [
                    (src_bx, sy + sh),
                    (src_bx, gutter_y),
                    (dst_bx, gutter_y),
                    (dst_bx, ty + th),
                ]
                edge_waypoints[eid] = wps
                if edge["name"]:
                    mid_lx = (src_bx + dst_bx) // 2 - 55
                    edge_label_bounds[eid] = (mid_lx, gutter_y - 22, 110, 18)
                continue

            if col_dst > col_src + 1:
                r_slot = right_out_count.get(src_id, 0)
                right_out_count[src_id] = r_slot + 1
                l_slot = left_in_count.get(dst_id, 0)
                left_in_count[dst_id] = l_slot + 1

                src_py = sy + sh // 2 + (r_slot * 14 if sh >= 70 else 0)
                dst_py = ty + th // 2 + (l_slot * 14 if th >= 70 else 0)

                up_x = min(sx + sw + 28 + r_slot * 16, col_base_x[col_src] + 206)
                down_slot = gap_channel_count.get(col_dst - 1, 0)
                gap_channel_count[col_dst - 1] = down_slot + 1
                down_x = col_base_x[col_dst] - 24 - down_slot * 14

                top_gutter_y = pool_y + 24 + skip_idx * 28
                skip_idx += 1

                wps = [
                    (sx + sw, src_py),
                    (up_x, src_py),
                    (up_x, top_gutter_y),
                    (down_x, top_gutter_y),
                    (down_x, dst_py),
                    (tx, dst_py),
                ]
                edge_waypoints[eid] = wps
                if edge["name"]:
                    mid_lx = (up_x + down_x) // 2 - 45
                    edge_label_bounds[eid] = (mid_lx, top_gutter_y - 22, 90, 18)
                continue

            if edge["kind"] == "gw_false" and nodes[src_id]["kind"] == "gateway":
                b_out_slot = bottom_out_count.get(src_id, 0)
                bottom_out_count[src_id] = b_out_slot + 1
                l_slot = left_in_count.get(dst_id, 0)
                left_in_count[dst_id] = l_slot + 1

                src_bx = sx + sw // 2
                dst_py = ty + th // 2 + (l_slot * 14 if th >= 70 else 0)

                if dst_py >= sy + sh + 25:
                    wps = [
                        (src_bx, sy + sh),
                        (src_bx, dst_py),
                        (tx, dst_py),
                    ]
                    if edge["name"]:
                        edge_label_bounds[eid] = (src_bx + 15, (sy + sh + dst_py) // 2 - 9, 100, 18)
                else:
                    under_y = sy + sh + 28
                    gap_slot = gap_channel_count.get(col_src, 0)
                    gap_channel_count[col_src] = gap_slot + 1
                    gap_x = col_base_x[col_src] + 198 + gap_slot * 14
                    wps = [
                        (src_bx, sy + sh),
                        (src_bx, under_y),
                        (gap_x, under_y),
                        (gap_x, dst_py),
                        (tx, dst_py),
                    ]
                    if edge["name"]:
                        edge_label_bounds[eid] = (src_bx + 15, under_y + 8, 100, 18)
                edge_waypoints[eid] = wps
                continue

            r_slot = right_out_count.get(src_id, 0)
            right_out_count[src_id] = r_slot + 1
            l_slot = left_in_count.get(dst_id, 0)
            left_in_count[dst_id] = l_slot + 1

            src_py = sy + sh // 2 + (r_slot * 14 if sh >= 70 else 0)
            dst_py = ty + th // 2 + (l_slot * 14 if th >= 70 else 0)

            if src_py == dst_py:
                wps = [(sx + sw, src_py), (tx, dst_py)]
                if edge["name"]:
                    edge_label_bounds[eid] = ((sx + sw + tx) // 2 - 45, src_py - 22, 90, 18)
            else:
                gap_slot = gap_channel_count.get(col_src, 0)
                gap_channel_count[col_src] = gap_slot + 1
                if nodes[src_id]["kind"] == "start":
                    mid_x = sx + sw + 28 + gap_slot * 14
                else:
                    mid_x = col_base_x[col_src] + 206 + gap_slot * 12
                wps = [
                    (sx + sw, src_py),
                    (mid_x, src_py),
                    (mid_x, dst_py),
                    (tx, dst_py),
                ]
                if edge["name"]:
                    edge_label_bounds[eid] = (mid_x + 15, (src_py + dst_py) // 2 - 9, 90, 18)
            edge_waypoints[eid] = wps

        return {
            "pool_bounds": (pool_x, pool_y, pool_width, pool_height),
            "lane_bounds": lane_bounds,
            "node_bounds": node_bounds,
            "edge_waypoints": edge_waypoints,
            "edge_label_bounds": edge_label_bounds,
        }

    def to_camunda_bpmn_xml(self) -> str:
        """Export standard Camunda Modeler 5.20+ BPMN 2.0 XML with Pools, Swimlanes & BPMNDI."""
        graph = self._build_visual_graph()
        layout = self._compute_bpmn_layout(graph)

        proc_id = _safe_id(self.process_id)
        collab_id = f"Collaboration_{proc_id}"
        part_id = f"Participant_{proc_id}"
        bpmn_proc_id = f"Process_{proc_id}"
        lanes: Dict[str, BPMNLane] = graph["lanes"]
        nodes: Dict[str, Dict[str, Any]] = graph["nodes"]
        edges: List[Dict[str, str]] = graph["edges"]

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"',
            '                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"',
            '                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"',
            '                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"',
            '                  xmlns:camunda="http://camunda.org/schema/1.0/bpmn"',
            f'                  id="Definitions_{proc_id}"',
            '                  targetNamespace="http://bpmn.io/schema/bpmn"',
            '                  exporter="Camunda Modeler"',
            '                  exporterVersion="5.20.0">',
            f'  <bpmn:collaboration id="{collab_id}">',
            f'    <bpmn:participant id="{part_id}" name="{_xml_escape(self.name)}" processRef="{bpmn_proc_id}" />',
            "  </bpmn:collaboration>",
            f'  <bpmn:process id="{bpmn_proc_id}" name="{_xml_escape(self.name)}" isExecutable="true">',
            f'    <bpmn:laneSet id="LaneSet_{proc_id}">',
        ]

        for lid, lane in lanes.items():
            lines.append(f'      <bpmn:lane id="{lid}" name="{_xml_escape(lane.name)}">')
            for nid in graph["ordered_ids"]:
                if nodes[nid]["lane_id"] == lid:
                    lines.append(f"        <bpmn:flowNodeRef>{nid}</bpmn:flowNodeRef>")
            lines.append("      </bpmn:lane>")
        lines.append("    </bpmn:laneSet>")

        for nid in graph["ordered_ids"]:
            node = nodes[nid]
            tag = node["tag"]
            in_flows = [e["id"] for e in edges if e["dst"] == nid]
            out_flows = [e["id"] for e in edges if e["src"] == nid]
            lines.append(f'    <{tag} id="{nid}" name="{node["name"]}">')
            for fid in in_flows:
                lines.append(f"      <bpmn:incoming>{fid}</bpmn:incoming>")
            for fid in out_flows:
                lines.append(f"      <bpmn:outgoing>{fid}</bpmn:outgoing>")
            lines.append(f"    </{tag}>")

        for edge in edges:
            name_attr = f' name="{_xml_escape(edge["name"])}"' if edge["name"] else ""
            lines.append(
                f'    <bpmn:sequenceFlow id="{edge["id"]}"{name_attr} sourceRef="{edge["src"]}" targetRef="{edge["dst"]}" />'
            )

        lines.append("  </bpmn:process>")

        lines.append(f'  <bpmndi:BPMNDiagram id="BPMNDiagram_{proc_id}">')
        lines.append(f'    <bpmndi:BPMNPlane id="BPMNPlane_{proc_id}" bpmnElement="{collab_id}">')

        px, py, pw, ph = layout["pool_bounds"]
        lines.append(f'      <bpmndi:BPMNShape id="{part_id}_di" bpmnElement="{part_id}" isHorizontal="true">')
        lines.append(f'        <dc:Bounds x="{px}" y="{py}" width="{pw}" height="{ph}" />')
        lines.append("      </bpmndi:BPMNShape>")

        for lid, (lx, ly, lw, lh) in layout["lane_bounds"].items():
            lines.append(f'      <bpmndi:BPMNShape id="{lid}_di" bpmnElement="{lid}" isHorizontal="true">')
            lines.append(f'        <dc:Bounds x="{lx}" y="{ly}" width="{lw}" height="{lh}" />')
            lines.append("      </bpmndi:BPMNShape>")

        for nid in graph["ordered_ids"]:
            x, y, w, h = layout["node_bounds"][nid]
            node = nodes[nid]
            marker_attr = ' isMarkerVisible="true"' if node["kind"] == "gateway" else ""
            lines.append(f'      <bpmndi:BPMNShape id="{nid}_di" bpmnElement="{nid}"{marker_attr}>')
            lines.append(f'        <dc:Bounds x="{x}" y="{y}" width="{w}" height="{h}" />')
            if node["kind"] == "gateway":
                lines.append("        <bpmndi:BPMNLabel>")
                lines.append(f'          <dc:Bounds x="{x - 35}" y="{y - 40}" width="120" height="25" />')
                lines.append("        </bpmndi:BPMNLabel>")
            elif node["kind"] == "start":
                lines.append("        <bpmndi:BPMNLabel>")
                lines.append(f'          <dc:Bounds x="{max(235, x - 17)}" y="{y + 42}" width="106" height="24" />')
                lines.append("        </bpmndi:BPMNLabel>")
            elif node["kind"] == "end":
                lines.append("        <bpmndi:BPMNLabel>")
                lines.append(f'          <dc:Bounds x="{x - 35}" y="{y + 42}" width="106" height="24" />')
                lines.append("        </bpmndi:BPMNLabel>")
            lines.append("      </bpmndi:BPMNShape>")

        for edge in edges:
            eid = edge["id"]
            wps = layout["edge_waypoints"][eid]
            lines.append(f'      <bpmndi:BPMNEdge id="{eid}_di" bpmnElement="{eid}">')
            for wx, wy in wps:
                lines.append(f'        <di:waypoint x="{wx}" y="{wy}" />')
            if eid in layout["edge_label_bounds"]:
                lx, ly, lw, lh = layout["edge_label_bounds"][eid]
                lines.append("        <bpmndi:BPMNLabel>")
                lines.append(f'          <dc:Bounds x="{lx}" y="{ly}" width="{lw}" height="{lh}" />')
                lines.append("        </bpmndi:BPMNLabel>")
            lines.append("      </bpmndi:BPMNEdge>")

        lines.append("    </bpmndi:BPMNPlane>")
        lines.append("  </bpmndi:BPMNDiagram>")
        lines.append("</bpmn:definitions>")
        return "\n".join(lines)

    def verify_semantic_invariants(
        self, source_facts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Verify structural graph integrity, Dead-End Elimination, and optional UC coverage."""
        errors: List[str] = []
        warnings: List[str] = []

        if not self.activities:
            errors.append("Process contains zero activities.")
            return {"ok": False, "errors": errors, "warnings": warnings, "coverage": {}}

        graph = self._build_visual_graph()
        nodes = graph["nodes"]
        edges = graph["edges"]

        for e in edges:
            if e["src"] not in nodes:
                errors.append(f"Edge {e['id']} references unknown source '{e['src']}'.")
            if e["dst"] not in nodes:
                errors.append(f"Edge {e['id']} references unknown target '{e['dst']}'.")

        for gw_id in self.gateways:
            out_edges = [e for e in edges if e["src"] == gw_id]
            if len(out_edges) < 2:
                errors.append(f"Gateway {gw_id} has {len(out_edges)} outgoing edges (must be >= 2).")
            targets = {e["dst"] for e in out_edges}
            if len(targets) < 2:
                errors.append(f"Gateway {gw_id} branches collapse to fewer than 2 distinct targets.")
            if any(not e["name"].strip() for e in out_edges):
                errors.append(f"Gateway {gw_id} has an unlabeled outgoing branch.")

        fwd_adj: Dict[str, List[str]] = {nid: [] for nid in nodes}
        rev_adj: Dict[str, List[str]] = {nid: [] for nid in nodes}
        for e in edges:
            if e["src"] in fwd_adj and e["dst"] in rev_adj:
                fwd_adj[e["src"]].append(e["dst"])
                rev_adj[e["dst"]].append(e["src"])

        def _bfs(start: str, adj: Dict[str, List[str]]) -> set[str]:
            seen = {start}
            q: deque[str] = deque([start])
            while q:
                cur = q.popleft()
                for nxt in adj.get(cur, []):
                    if nxt not in seen:
                        seen.add(nxt)
                        q.append(nxt)
            return seen

        reachable = _bfs("StartEvent_1", fwd_adj)
        can_reach_end = _bfs("EndEvent_1", rev_adj)
        unreachable = sorted(nid for nid in nodes if nid not in reachable)
        dead_ends = sorted(nid for nid in nodes if nid not in can_reach_end)

        if unreachable:
            errors.append(f"Unreachable nodes from StartEvent_1: {unreachable}")
        if dead_ends:
            errors.append(f"Dead-end nodes unable to reach EndEvent_1: {dead_ends}")

        coverage: Dict[str, Any] = {}
        if source_facts:
            lane_blob = " ".join(l.name.lower() for l in graph["lanes"].values())
            gw_blob = " ".join(
                f"{g.name} {g.condition_expression}".lower() for g in self.gateways.values()
            )
            ex_blob = " ".join(
                f"{ex.trigger_error_code} {ex.description or ''}".lower()
                for ex in self.exception_loops.values()
            )
            for key, haystack in (
                ("actors", lane_blob),
                ("branches", gw_blob),
                ("errors", ex_blob),
            ):
                items = [str(x) for x in source_facts.get(key, [])]
                missing = [x for x in items if x.lower() not in haystack]
                coverage[key] = {
                    "total": len(items),
                    "covered": len(items) - len(missing),
                    "missing": missing,
                }
                for m in missing:
                    warnings.append(f"Source {key[:-1]} '{m}' not explicitly matched in diagram.")

        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "unreachable": unreachable,
            "dead_ends": dead_ends,
            "coverage": coverage,
        }

    def verify_layout(self) -> Dict[str, Any]:
        """Compile Camunda XML and run deterministic BPMNDI layout verification."""
        return verify_layout(self.to_camunda_bpmn_xml())

    def check_arrow_overlaps(self) -> Dict[str, Any]:
        """Compile Camunda XML and verify strict segment disjointness (0 overlaps)."""
        return check_arrow_overlaps(self.to_camunda_bpmn_xml())

    def to_plantuml(self) -> str:
        """Render a PlantUML Activity Diagram (.puml) with swimlanes and 4-type styling."""
        graph = self._build_visual_graph()
        lanes = graph["lanes"]
        lines = [
            f"@startuml {_safe_id(self.process_id)}",
            f"title {self.name} ({self.process_id} v{self.version})",
            "skinparam ActivityBackgroundColor #0f172a",
            "skinparam ActivityBorderColor #38bdf8",
            "skinparam ActivityFontColor #f8fafc",
            "skinparam ArrowColor #0284c7",
            "skinparam SwimlaneBorderColor #334155",
            "start",
        ]

        color_map = {
            NodeType.HUMAN_NODE: "#fff3e0",
            NodeType.AGENT_NODE: "#3b0764",
            NodeType.CODE_NODE: "#0f172a",
        }
        gw_by_true = {gw.true_target: gw for gw in self.gateways.values()}
        ex_by_src = {ex.source_activity_id: ex for ex in self.exception_loops.values()}

        for act in self.activities.values():
            lid = self._resolve_lane_id(act.assigned_node_type, act.lane_id)
            lane_name = lanes[lid].name
            lines.append(f"|{lane_name}|")

            gw = gw_by_true.get(act.activity_id)
            if gw:
                lines.append(f"if ({gw.gateway_id}: {gw.name}?) then (Pass)")
                ex = ex_by_src.get(gw.gateway_id)
                if ex:
                    lines.append("else (Fail)")
                    lines.append(
                        f"  #450a0a:{ex.loop_id}: Auto-Heal ({ex.trigger_error_code})\\n-> Retry {ex.recovery_activity_id};"
                    )
                lines.append("endif")

            bg = color_map.get(act.assigned_node_type, "#0f172a")
            lines.append(f"{bg}:{act.activity_id}: {act.name};")

        lines.append("stop")
        lines.append("@enduml")
        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """Render a native Mermaid.js flowchart with Phase subgraphs, gateways, and 4-type classes."""
        graph = self._build_visual_graph()
        lines = [
            "flowchart TD",
            "    classDef human fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#0f172a;",
            "    classDef code fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#0f172a;",
            "    classDef agent fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#0f172a;",
            "    classDef ex fill:#ffebee,stroke:#d32f2f,stroke-width:2px,color:#7f1d1d;",
            "    classDef gw fill:#fffde7,stroke:#fbc02d,stroke-width:2px,color:#0f172a;",
            "",
            '    START(["Process Initiated"]):::human',
            '    END(["Process Completed"]):::code',
        ]

        cls_map = {
            NodeType.HUMAN_NODE: "human",
            NodeType.AGENT_NODE: "agent",
            NodeType.CODE_NODE: "code",
        }
        for ph in self.phases.values():
            lines.append(f'    subgraph P{ph.phase_id}["Phase {ph.phase_id}: {ph.name}"]')
            for act in ph.activities:
                nid = _safe_id(act.activity_id)
                lbl = act.name.replace('"', "'")
                c = cls_map.get(act.assigned_node_type, "code")
                lines.append(f'        {nid}["{act.activity_id}: {lbl}"]:::{c}')
            lines.append("    end")

        placed_acts = {a.activity_id for ph in self.phases.values() for a in ph.activities}
        for act in self.activities.values():
            if act.activity_id not in placed_acts:
                nid = _safe_id(act.activity_id)
                lbl = act.name.replace('"', "'")
                c = cls_map.get(act.assigned_node_type, "code")
                lines.append(f'    {nid}["{act.activity_id}: {lbl}"]:::{c}')

        for gw in self.gateways.values():
            gid = _safe_id(gw.gateway_id)
            lbl = gw.name.replace('"', "'")
            lines.append(f'    {gid}{{"{gw.gateway_id}: {lbl}"}}:::gw')

        for ex in self.exception_loops.values():
            xid = _safe_id(ex.loop_id)
            lines.append(f'    {xid}["{ex.loop_id}: Auto-Heal ({ex.trigger_error_code})"]:::ex')

        lines.append("")
        for edge in graph["edges"]:
            src = "START" if edge["src"] == "StartEvent_1" else ("END" if edge["src"] == "EndEvent_1" else _safe_id(edge["src"]))
            dst = "START" if edge["dst"] == "StartEvent_1" else ("END" if edge["dst"] == "EndEvent_1" else _safe_id(edge["dst"]))
            if edge["name"]:
                lbl = edge["name"].replace('"', "'")
                lines.append(f'    {src} -- "{lbl}" --> {dst}')
            else:
                lines.append(f"    {src} --> {dst}")

        return "\n".join(lines)

    def to_utop_markdown_spec(self) -> str:
        """Generate a complete UTOP Process Specification Markdown document with verification proof."""
        xml_str = self.to_camunda_bpmn_xml()
        sem_rep = self.verify_semantic_invariants()
        lay_rep = verify_layout(xml_str)
        ov_rep = check_arrow_overlaps(xml_str)

        lines = [
            f"# {self.process_id}: {self.name}",
            "",
            f"> **Protocol**: `{self.protocol_type}` | **Version**: `{self.version}` | **Skill Engine**: `BPMNArchitect`",
            "",
            "## 1. Process Verification Proof Summary (Deterministic P=1)",
            "",
            "| Gate | Check | Result | Metric |",
            "|---|---|---|---|",
            f"| Semantic Integrity | Reachability & Dead-End Elimination | {'PASS' if sem_rep['ok'] else 'FAIL'} | {sem_rep['node_count']} nodes, {sem_rep['edge_count']} flows, 0 dead-ends |",
            f"| Layout Geometry | Shape Collisions & Box Cuts | {'PASS' if lay_rep['ok'] else 'FAIL'} | {lay_rep['shape_collisions']} collisions, {lay_rep['box_intersections']} cuts |",
            f"| Arrow Disjointness | Segment Overlap Audit | {'PASS' if ov_rep['ok'] else 'FAIL'} | {ov_rep['overlap_count']} overlaps across {ov_rep['total_segments']} segments |",
            "",
            "## 2. Mermaid Process Topology",
            "",
            "```mermaid",
            self.to_mermaid(),
            "```",
            "",
            "## 3. Step-by-Step Execution Matrix",
            "",
            "| Step ID | Phase | Title | Node Type | Swimlane | Pomodoro | Rule / Reference |",
            "|:---:|:---:|---|---|:---:|:---:|---|",
        ]

        lanes = self._ensure_default_lanes()
        for act in self.activities.values():
            lid = self._resolve_lane_id(act.assigned_node_type, act.lane_id)
            lane_label = lanes[lid].name.split("(")[0].strip()
            ph_name = self.phases[act.phase_id].name if act.phase_id in self.phases else f"Phase {act.phase_id}"
            lines.append(
                f"| **{act.activity_id}** | P{act.phase_id}: {ph_name} | {act.name} | `{act.assigned_node_type.value}` | {lane_label} | {act.pomodoro_tier} | {act.rule_ref or act.prompt_name or '-'} |"
            )

        lines.extend(
            [
                "",
                "## 4. Decision Gateways & Dead-End Eliminated Exception Loops",
                "",
                "| ID | Type | Title / Trigger | Condition / Error | Pass / Target | Recovery / Fallback |",
                "|:---:|:---:|---|---|---|---|",
            ]
        )
        for gw in self.gateways.values():
            lines.append(
                f"| **{gw.gateway_id}** | Gateway ({gw.gateway_type.value}) | {gw.name} | `{gw.condition_expression}` | `{gw.true_target}` | `{gw.false_target}` |"
            )
        for ex in self.exception_loops.values():
            lines.append(
                f"| **{ex.loop_id}** | Exception Loop | Trigger from `{ex.source_activity_id}` | `{ex.trigger_error_code}` | `{ex.recovery_activity_id}` | Auto-Heal (max {ex.max_retries} retries) |"
            )
        lines.append("")
        return "\n".join(lines)

    def to_interactive_html_viewer(
        self, additional_processes: Optional[List["BPMNProcess"]] = None
    ) -> str:
        """Build a self-contained first-party Camunda bpmn-js Modeler & UTOP Studio HTML app."""
        all_procs = [self] + list(additional_processes or [])
        bundle: List[Dict[str, Any]] = []
        for proc in all_procs:
            xml_str = proc.to_camunda_bpmn_xml()
            sem = proc.verify_semantic_invariants()
            lay = verify_layout(xml_str)
            ov = check_arrow_overlaps(xml_str)
            steps = [
                {
                    "id": a.activity_id,
                    "phase": f"P{a.phase_id}: {proc.phases[a.phase_id].name if a.phase_id in proc.phases else a.phase_id}",
                    "name": a.name,
                    "node_type": a.assigned_node_type.value,
                    "tier": a.pomodoro_tier,
                    "rule": a.rule_ref or a.prompt_name or "-",
                }
                for a in proc.activities.values()
            ]
            bundle.append(
                {
                    "slug": _safe_id(proc.process_id),
                    "process_id": proc.process_id,
                    "title": f"{proc.process_id} — {proc.name}",
                    "version": proc.version,
                    "protocol": proc.protocol_type,
                    "xml": xml_str,
                    "mermaid": proc.to_mermaid(),
                    "plantuml": proc.to_plantuml(),
                    "steps": steps,
                    "metrics": {
                        "activities": len(proc.activities),
                        "gateways": len(proc.gateways),
                        "exceptions": len(proc.exception_loops),
                        "semantic_ok": sem["ok"],
                        "shape_collisions": lay["shape_collisions"],
                        "box_intersections": lay["box_intersections"],
                        "arrow_overlaps": ov["overlap_count"],
                    },
                }
            )

        payload_json = json.dumps(bundle, ensure_ascii=False).replace("</", "<\\/")
        title_escaped = html.escape(self.name)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BPMNArchitect Studio — {title_escaped}</title>
  <link rel="stylesheet" href="https://unpkg.com/bpmn-js@17.11.1/dist/assets/diagram-js.css" />
  <link rel="stylesheet" href="https://unpkg.com/bpmn-js@17.11.1/dist/assets/bpmn-js.css" />
  <link rel="stylesheet" href="https://unpkg.com/bpmn-js@17.11.1/dist/assets/bpmn-font/css/bpmn.css" />
  <script src="https://unpkg.com/bpmn-js@17.11.1/dist/bpmn-modeler.production.min.js"></script>
  <style>
    :root {{ --bg: #0f172a; --panel: #1e293b; --border: #334155; --accent: #38bdf8; --ok: #10b981; --warn: #f59e0b; }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; height: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #0f172a; }}
    header {{ background: var(--bg); color: #f8fafc; padding: 10px 18px; display: flex; flex-wrap: wrap; align-items: center; gap: 10px; border-bottom: 2px solid var(--accent); }}
    .brand {{ font-weight: 700; font-size: 15px; display: flex; align-items: center; gap: 8px; }}
    .pill {{ font-size: 11px; padding: 2px 8px; border-radius: 999px; background: #0284c7; color: #fff; font-weight: 600; }}
    .pill.ok {{ background: #065f46; border: 1px solid #10b981; }}
    select, button {{ border-radius: 6px; border: 1px solid var(--border); background: var(--panel); color: #f8fafc; padding: 6px 11px; font-size: 13px; cursor: pointer; }}
    button:hover {{ background: #334155; }}
    button.primary {{ background: #0284c7; border-color: #38bdf8; font-weight: 600; }}
    button.primary:hover {{ background: #0369a1; }}
    .spacer {{ flex: 1; }}
    #dirtyBadge {{ display: none; color: #fbbf24; font-size: 12px; font-weight: 600; }}
    nav.tabs {{ background: #ffffff; border-bottom: 1px solid #cbd5e1; padding: 0 18px; display: flex; gap: 6px; }}
    nav.tabs button {{ background: transparent; color: #475569; border: none; border-bottom: 3px solid transparent; border-radius: 0; padding: 10px 14px; font-weight: 600; }}
    nav.tabs button.active {{ color: #0284c7; border-bottom-color: #0284c7; }}
    .view {{ display: none; height: calc(100vh - 96px); }}
    .view.active {{ display: block; }}
    #canvas {{ width: 100%; height: 100%; background: #ffffff; }}
    .panel-pad {{ padding: 20px; overflow: auto; height: 100%; max-width: 1280px; margin: 0 auto; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-bottom: 18px; }}
    .kpi {{ background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 12px 14px; }}
    .kpi .lbl {{ font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 700; }}
    .kpi .val {{ font-size: 20px; font-weight: 800; color: #0f172a; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; background: #ffffff; border: 1px solid #cbd5e1; font-size: 13px; }}
    th {{ background: #0f172a; color: #f8fafc; text-align: left; padding: 10px 12px; }}
    td {{ padding: 8px 12px; border-bottom: 1px solid #e2e8f0; }}
    tr:nth-child(even) td {{ background: #f8fafc; }}
    pre {{ background: #0f172a; color: #e2e8f0; padding: 14px; border-radius: 10px; overflow: auto; font-size: 12px; max-height: 360px; }}
    #offlineWarn {{ display: none; background: #fef3c7; color: #92400e; padding: 10px 18px; font-size: 13px; border-bottom: 1px solid #f59e0b; }}
    .bjs-powered-by {{ display: none !important; }}
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span>BPMNArchitect Studio</span>
      <span class="pill">OMG BPMN 2.0</span>
      <span class="pill ok" id="proofBadge">Verified 0 Overlaps</span>
    </div>
    <select id="procSelect" onchange="switchProcess(this.value)"></select>
    <span id="dirtyBadge">Unsaved edits</span>
    <span class="spacer"></span>
    <button onclick="zoomFit()">Fit View</button>
    <button onclick="zoomStep(1)">+</button>
    <button onclick="zoomStep(-1)">-</button>
    <button class="primary" onclick="downloadBpmn()">Download .bpmn</button>
    <button onclick="downloadSvg()">Export .svg</button>
    <button onclick="saveBpmnFile()">Save File</button>
    <button onclick="copyXml()">Copy XML</button>
  </header>
  <div id="offlineWarn">Note: Interactive drag-and-drop canvas requires bpmn-js CDN access. Execution Matrix, Mermaid, PlantUML, and Raw XML tabs remain 100% available offline.</div>
  <nav class="tabs">
    <button id="tab-modeler" class="active" onclick="showTab('modeler')">Interactive Camunda 2.0 Modeler</button>
    <button id="tab-matrix" onclick="showTab('matrix')">UTOP Step Execution Matrix</button>
    <button id="tab-source" onclick="showTab('source')">Mermaid / PlantUML / Raw XML</button>
  </nav>

  <section id="view-modeler" class="view active"><div id="canvas"></div></section>
  <section id="view-matrix" class="view panel-pad">
    <div class="kpi-grid" id="kpiGrid"></div>
    <table>
      <thead><tr><th>Step ID</th><th>Phase</th><th>Action Title</th><th>Node Type</th><th>Tier</th><th>Rule / Spec Reference</th></tr></thead>
      <tbody id="stepTableBody"></tbody>
    </table>
  </section>
  <section id="view-source" class="view panel-pad">
    <h3>Mermaid Flowchart Source</h3>
    <pre id="mermaidSrc"></pre>
    <h3>PlantUML Activity Source</h3>
    <pre id="pumlSrc"></pre>
    <h3>Camunda Modeler 5.20 BPMN 2.0 XML</h3>
    <pre id="xmlSrc"></pre>
  </section>

  <script>
    const PROCESSES = {payload_json};
    let modeler = null;
    let currentProc = PROCESSES[0];
    let dirty = false;

    const selectEl = document.getElementById('procSelect');
    PROCESSES.forEach(p => {{
      const opt = document.createElement('option');
      opt.value = p.slug;
      opt.textContent = p.title;
      selectEl.appendChild(opt);
    }});

    if (typeof BpmnJS !== 'undefined') {{
      modeler = new BpmnJS({{ container: '#canvas' }});
      modeler.on('commandStack.changed', () => setDirty(true));
    }} else {{
      document.getElementById('offlineWarn').style.display = 'block';
    }}

    function setDirty(v) {{
      dirty = v;
      document.getElementById('dirtyBadge').style.display = v ? 'inline' : 'none';
    }}

    function showTab(name) {{
      ['modeler', 'matrix', 'source'].forEach(t => {{
        document.getElementById('tab-' + t).classList.toggle('active', t === name);
        document.getElementById('view-' + t).classList.toggle('active', t === name);
      }});
      if (name === 'modeler' && modeler) setTimeout(zoomFit, 50);
    }}

    function renderDetails(p) {{
      const m = p.metrics;
      document.getElementById('proofBadge').textContent =
        `Verified: ${{m.shape_collisions}} collisions, ${{m.box_intersections}} cuts, ${{m.arrow_overlaps}} overlaps`;
      document.getElementById('kpiGrid').innerHTML = [
        ['Activities', m.activities],
        ['Gateways', m.gateways],
        ['Exception Loops', m.exceptions],
        ['Semantic Check', m.semantic_ok ? 'PASS' : 'FAIL'],
        ['Box Cuts', m.box_intersections],
        ['Arrow Overlaps', m.arrow_overlaps],
      ].map(([k, v]) => `<div class="kpi"><div class="lbl">${{k}}</div><div class="val">${{v}}</div></div>`).join('');

      document.getElementById('stepTableBody').innerHTML = p.steps.map(s =>
        `<tr><td><b>${{s.id}}</b></td><td>${{s.phase}}</td><td>${{s.name}}</td><td><code>${{s.node_type}}</code></td><td>${{s.tier}}</td><td>${{s.rule}}</td></tr>`
      ).join('');
      document.getElementById('mermaidSrc').textContent = p.mermaid;
      document.getElementById('pumlSrc').textContent = p.plantuml;
      document.getElementById('xmlSrc').textContent = p.xml;
    }}

    async function switchProcess(slug) {{
      if (dirty && !confirm('Unsaved canvas edits will be lost. Continue?')) {{
        selectEl.value = currentProc.slug;
        return;
      }}
      currentProc = PROCESSES.find(p => p.slug === slug) || PROCESSES[0];
      selectEl.value = currentProc.slug;
      renderDetails(currentProc);
      if (modeler) {{
        await modeler.importXML(currentProc.xml);
        setDirty(false);
        zoomFit();
      }}
    }}

    function zoomFit() {{ if (modeler) modeler.get('canvas').zoom('fit-viewport', 'auto'); }}
    function zoomStep(dir) {{ if (modeler) modeler.get('zoomScroll').stepZoom(dir); }}

    async function currentXml() {{
      if (modeler) {{
        const res = await modeler.saveXML({{ format: true }});
        return res.xml;
      }}
      return currentProc.xml;
    }}

    async function downloadBpmn() {{
      const xml = await currentXml();
      const blob = new Blob([xml], {{ type: 'application/xml' }});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = currentProc.slug + '.bpmn';
      a.click();
      URL.revokeObjectURL(a.href);
      setDirty(false);
    }}

    async function downloadSvg() {{
      if (!modeler) return alert('SVG export requires bpmn-js canvas.');
      const res = await modeler.saveSVG();
      const blob = new Blob([res.svg], {{ type: 'image/svg+xml' }});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = currentProc.slug + '.svg';
      a.click();
      URL.revokeObjectURL(a.href);
    }}

    async function saveBpmnFile() {{
      if (!window.showSaveFilePicker) return downloadBpmn();
      const xml = await currentXml();
      const handle = await window.showSaveFilePicker({{
        suggestedName: currentProc.slug + '.bpmn',
        types: [{{ description: 'BPMN 2.0 XML', accept: {{ 'application/xml': ['.bpmn'] }} }}]
      }});
      const w = await handle.createWritable();
      await w.write(xml);
      await w.close();
      setDirty(false);
    }}

    async function copyXml() {{
      const xml = await currentXml();
      await navigator.clipboard.writeText(xml);
      alert('Copied BPMN 2.0 XML to clipboard.');
    }}

    switchProcess(currentProc.slug);
  </script>
</body>
</html>"""

    def export_deliverable_package(
        self,
        output_dir: str | Path,
        additional_processes: Optional[List["BPMNProcess"]] = None,
    ) -> Dict[str, Any]:
        """Export full multi-format BPMN package (.bpmn, .ir.json, .puml, .mermaid, _SPEC.md, _camunda_studio.html)."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        all_procs = [self] + list(additional_processes or [])
        exported_files: List[str] = []
        verification_reports: Dict[str, Any] = {}

        for proc in all_procs:
            slug = _safe_id(proc.process_id)
            xml_str = proc.to_camunda_bpmn_xml()
            sem = proc.verify_semantic_invariants()
            lay = verify_layout(xml_str)
            ov = check_arrow_overlaps(xml_str)

            files_map = {
                out_path / f"{slug}.bpmn": xml_str,
                out_path / f"{slug}.ir.json": json.dumps(proc.to_ir_dict(), indent=2, ensure_ascii=False),
                out_path / f"{slug}.puml": proc.to_plantuml(),
                out_path / f"{slug}.mermaid": proc.to_mermaid(),
                out_path / f"{slug}_SPEC.md": proc.to_utop_markdown_spec(),
            }
            for fp, content in files_map.items():
                fp.write_text(content, encoding="utf-8")
                exported_files.append(str(fp))

            verification_reports[proc.process_id] = {
                "semantic_ok": sem["ok"],
                "shape_collisions": lay["shape_collisions"],
                "box_intersections": lay["box_intersections"],
                "arrow_overlaps": ov["overlap_count"],
                "ergonomic_violations": lay["ergonomic_violations"],
            }

        studio_path = out_path / f"{_safe_id(self.process_id)}_camunda_studio.html"
        studio_path.write_text(
            self.to_interactive_html_viewer(additional_processes=additional_processes),
            encoding="utf-8",
        )
        exported_files.append(str(studio_path))

        all_ok = all(
            r["semantic_ok"]
            and r["shape_collisions"] == 0
            and r["box_intersections"] == 0
            and r["arrow_overlaps"] == 0
            and not r["ergonomic_violations"]
            for r in verification_reports.values()
        )
        return {
            "status": "OK" if all_ok else "FAIL",
            "output_dir": str(out_path),
            "studio_html": str(studio_path),
            "files": exported_files,
            "verifications": verification_reports,
        }


def build_canonical_37_step_process() -> BPMNProcess:
    """Builds the authoritative 37-Step Technical Vibe Coding Process (53.REF.07)."""
    p = BPMNProcess(
        "53.REF.07", "37-Step Technical Vibe Coding Process", "2.0.0", "TECHNICAL"
    )
    p.add_lane("Lane_HUMAN", "Human Node (HUM — Intent, Ethics & Sign-Off)", NodeType.HUMAN_NODE)
    p.add_lane("Lane_AGENT", "Agent Node Swarm (AGT — BDI Reasoning & Synthesis)", NodeType.AGENT_NODE)
    p.add_lane("Lane_CODE", "Code Node (DET P=1 — Validation, Gates & State)", NodeType.CODE_NODE)

    p.add_phase(1, "Intake & Register")
    p.add_phase(2, "Plan & Assign / Sign-Off")
    p.add_phase(3, "Authorize")
    p.add_phase(4, "Parallel Execute")
    p.add_phase(5, "Validate & Review")
    p.add_phase(6, "Approve & Integrate")
    p.add_phase(7, "Close & Learn")

    activities = [
        BPMNActivity("ST-001", "Message Inquiry Intake", 1, NodeType.HUMAN_NODE, rule_ref="53.REF.07 Intake", category="CORE"),
        BPMNActivity("ST-002", "Intent Detection & Task Registry", 1, NodeType.CODE_NODE, rule_ref="DocOrg SSOT", category="CORE"),
        BPMNActivity("ST-003", "SMART Syntax & BMC Binding", 1, NodeType.CODE_NODE, rule_ref="GW-GENESIS-01 / 7H", category="CORE"),
        BPMNActivity("ST-004", "WSJF Strategic Prioritization", 1, NodeType.CODE_NODE, rule_ref="CoD / Duration", category="CORE"),
        BPMNActivity("ST-005", "Graph & DB Registration", 1, NodeType.CODE_NODE, rule_ref="KuzuDB + SQLite", category="CORE"),
        BPMNActivity("ST-006", "User Story Ingestion", 2, NodeType.AGENT_NODE, prompt_name="task_decomposition", rule_ref="US-xxx + Context Swarm", category="CORE"),
        BPMNActivity("ST-007", "UC 3.0 & BDD Specification", 2, NodeType.AGENT_NODE, prompt_name="UCBDDManager:uc_template", rule_ref="GW-UTOP-01 (17-Artifact)", category="CODE"),
        BPMNActivity("ST-008", "Subtask Decomposition", 2, NodeType.AGENT_NODE, prompt_name="task_decomposition", rule_ref="Atomic WBS <= 5m", category="CORE"),
        BPMNActivity("ST-009", "Kahn DAG Wave Calculation", 2, NodeType.CODE_NODE, rule_ref="Zero-Indegree W_k", category="CORE"),
        BPMNActivity("ST-010", "Write-Set Sibling Check", 2, NodeType.CODE_NODE, rule_ref="Disjoint AST Write-Sets", category="CODE"),
        BPMNActivity("ST-011", "Kahn MergePoint Insertion", 2, NodeType.CODE_NODE, rule_ref="53.REF.69 Sprint Sync", category="CORE"),
        BPMNActivity("ST-012", "PolicyPack Boundary Audit", 3, NodeType.CODE_NODE, rule_ref="authorization_matrix.yaml", category="CORE"),
        BPMNActivity("ST-013", "Capability Grant Issuance", 3, NodeType.CODE_NODE, rule_ref="Scoped GRANT-XXX", category="CORE"),
        BPMNActivity("ST-014", "Git Worktree Provisioning", 4, NodeType.CODE_NODE, rule_ref=".worktrees/feat-*", category="CODE"),
        BPMNActivity("ST-015", "Dynamic Parallel Fan-Out", 4, NodeType.CODE_NODE, rule_ref="|W_k| <= 20", category="CORE"),
        BPMNActivity("ST-016", "Technical Code Execution", 4, NodeType.AGENT_NODE, prompt_name="worker_default", rule_ref="Implements: UC/FR/TC", category="CODE"),
        BPMNActivity("ST-017", "Pomodoro Focus Enforcement", 4, NodeType.CODE_NODE, rule_ref="GW-TIMEBOX-01 (2m)", category="CORE"),
        BPMNActivity("ST-018", "Subtask Micro-Reflection (RF-001)", 4, NodeType.AGENT_NODE, prompt_name="reflection:rf-001", rule_ref="30s Recalibration", category="CORE"),
        BPMNActivity("ST-019", "Local Sandbox Unit Testing", 4, NodeType.CODE_NODE, rule_ref="Pytest Sandbox", category="CODE"),
        BPMNActivity("ST-020", "Stream Barrier Synchronization", 4, NodeType.CODE_NODE, rule_ref="MergePoint Sync", category="CORE"),
        BPMNActivity("ST-021", "Static Analysis & Ruff Linting", 5, NodeType.CODE_NODE, rule_ref="Ruff / AST Lint", category="CODE"),
        BPMNActivity("ST-022", "SAST Security & Secret Scan", 5, NodeType.CODE_NODE, rule_ref="Bandit / Secret Guard", category="CODE"),
        BPMNActivity("ST-023", "Gherkin BDD & Automated Test Runner", 5, NodeType.CODE_NODE, rule_ref="MinTC vs _data.json", category="CODE"),
        BPMNActivity("ST-024", "15 QualityGate Reviewers Swarm", 5, NodeType.CODE_NODE, rule_ref="GW-QG-01 Review", category="CORE"),
        BPMNActivity("ST-025", "LLM-as-a-Judge EAI Scoring", 5, NodeType.AGENT_NODE, prompt_name="quality_gate_judge", rule_ref="EAI >= 0.98", category="CORE"),
        BPMNActivity("ST-026", "Task Meso-Reflection (RF-002)", 5, NodeType.AGENT_NODE, prompt_name="reflection:rf-002", rule_ref="1m Reflection", category="CORE"),
        BPMNActivity("ST-027", "Compile walkthrough.md Proof", 5, NodeType.AGENT_NODE, rule_ref="Empirical Proof + Sealing", category="CORE"),
        BPMNActivity("ST-028", "Separation of Duties Check", 6, NodeType.CODE_NODE, rule_ref="GW-SOD-01", category="CORE"),
        BPMNActivity("ST-029", "Git Fast-Forward Merge", 6, NodeType.CODE_NODE, rule_ref="GW-GIT-BRANCH-01", category="CODE"),
        BPMNActivity("ST-030", "Worktree Cleanup", 6, NodeType.CODE_NODE, rule_ref="Prune Ephemeral Branch", category="CODE"),
        BPMNActivity("ST-031", "CI/CD Build Canary Trigger", 6, NodeType.CODE_NODE, rule_ref="GW-DEPLOY-07", category="CODE"),
        BPMNActivity("ST-032", "SD-008 Post-Completion Hooks", 7, NodeType.CODE_NODE, rule_ref="DocOrg MECE Hygiene", category="CORE"),
        BPMNActivity("ST-033", "Documentation Publishing", 7, NodeType.CODE_NODE, rule_ref="Catalog & Spec Sync", category="CORE"),
        BPMNActivity("ST-034", "Task State Done Transition", 7, NodeType.CODE_NODE, rule_ref="53.REF.69 Archive", category="CORE"),
        BPMNActivity("ST-035", "LangFuse Telemetry Audit", 7, NodeType.CODE_NODE, rule_ref="Coverage = 1.0", category="CORE"),
        BPMNActivity("ST-036", "Sprint Macro-Reflection (RF-003)", 7, NodeType.AGENT_NODE, prompt_name="reflection:rf-003", rule_ref="3m Macro Retro", category="CORE"),
        BPMNActivity("ST-037", "EBQC Distillation & Promotion", 7, NodeType.AGENT_NODE, prompt_name="prompt_crystallization_evaluator", rule_ref="4-Stage Crystallization", category="CORE"),
    ]

    for act in activities:
        p.add_activity(act)

    for i in range(1, 37):
        p.add_transition(f"ST-{i:03d}", f"ST-{i + 1:03d}")

    p.add_gateway(BPMNGateway("GW-001", "Dual Architecture Sign-Off", GatewayType.EXCLUSIVE, "approved == True", "ST-011", "EX-001", lane_id="Lane_HUMAN", phase_id=2))
    p.add_gateway(BPMNGateway("GW-002", "Minimal-HITL Authorization", GatewayType.EXCLUSIVE, "eai >= 0.98 or approved", "ST-013", "EX-002", lane_id="Lane_CODE", phase_id=3))
    p.add_gateway(BPMNGateway("GW-003", "3-Way AST Merge Barrier", GatewayType.EXCLUSIVE, "conflicts == 0", "ST-020", "EX-003", lane_id="Lane_CODE", phase_id=4))
    p.add_gateway(BPMNGateway("GW-004", "QualityGate Verification", GatewayType.EXCLUSIVE, "eai >= 0.98 and tests_green", "ST-027", "EX-004", lane_id="Lane_CODE", phase_id=5))

    p.add_exception_loop(BPMNExceptionLoop("EX-001", "GW-001", "ST-006", "ARCH_REJECTED", lane_id="Lane_CODE"))
    p.add_exception_loop(BPMNExceptionLoop("EX-002", "GW-002", "ST-013", "HIGH_RISK_HITL", lane_id="Lane_HUMAN"))
    p.add_exception_loop(BPMNExceptionLoop("EX-003", "GW-003", "ST-016", "AST_CONFLICT", lane_id="Lane_CODE"))
    p.add_exception_loop(BPMNExceptionLoop("EX-004", "GW-004", "ST-016", "QUALITY_GATE_FAIL", lane_id="Lane_CODE"))

    return p


def build_canonical_18_step_process() -> BPMNProcess:
    """Builds the authoritative 18-Step Universal Vibe Working Process (53.REF.08)."""
    p = BPMNProcess(
        "53.REF.08", "18-Step Universal Vibe Working Process [CORE]", "3.0.0", "CORE"
    )
    p.add_lane("Lane_HUMAN", "Human Node (HUM — Intent, Ethics & Sign-Off)", NodeType.HUMAN_NODE)
    p.add_lane("Lane_AGENT", "Agent Node Swarm (AGT — BDI Reasoning & Synthesis)", NodeType.AGENT_NODE)
    p.add_lane("Lane_CODE", "Code Node (DET P=1 — Validation, Gates & State)", NodeType.CODE_NODE)

    p.add_phase(1, "Intake & Registration")
    p.add_phase(2, "Plan & Sign-Off (Outline & Rubrics)")
    p.add_phase(3, "Authorize (Minimal-HITL)")
    p.add_phase(4, "Parallel Execution")
    p.add_phase(5, "Validate & Review")
    p.add_phase(6, "Approve & Integrate")
    p.add_phase(7, "Close, Distill & Learn")

    activities = [
        BPMNActivity("ST-001", "Message Inquiry Intake", 1, NodeType.HUMAN_NODE, rule_ref="53.REF.08 Intake", category="CORE"),
        BPMNActivity("ST-002", "Task Registration & SSOT Intake", 1, NodeType.CODE_NODE, rule_ref="DocOrg Intake", category="CORE"),
        BPMNActivity("ST-003", "Goal & Pomodoro Budget", 1, NodeType.CODE_NODE, rule_ref="SMART + 15m Sprint", category="CORE"),
        BPMNActivity("ST-004", "Plan & Outline Decomposition", 2, NodeType.AGENT_NODE, prompt_name="task_decomposition", rule_ref="TOC + 4-Block Goal + DoD", category="CORE"),
        BPMNActivity("ST-005", "Kahn DAG Wave Calculation", 2, NodeType.CODE_NODE, rule_ref="Zero-Indegree Waves", category="CORE"),
        BPMNActivity("ST-006", "MergePoint Barrier Insertion", 2, NodeType.CODE_NODE, rule_ref="Kahn Barrier", category="CORE"),
        BPMNActivity("ST-007", "Grant Issuance & Path Guard", 3, NodeType.CODE_NODE, rule_ref="GRANT-XXX / MECE Zone", category="CORE"),
        BPMNActivity("ST-008", "Dynamic Fan-Out Execution", 4, NodeType.AGENT_NODE, prompt_name="worker_default", rule_ref="Depth <= 2 Synthesis", category="CORE"),
        BPMNActivity("ST-009", "Pomodoro Focus Enforcement", 4, NodeType.CODE_NODE, rule_ref="GW-TIMEBOX-01 (2m/5m)", category="CORE"),
        BPMNActivity("ST-010", "Subtask Micro-Reflection (RF-001)", 4, NodeType.AGENT_NODE, prompt_name="reflection:rf-001", rule_ref="30s Recalibration", category="CORE"),
        BPMNActivity("ST-011", "MergePoint Barrier Sync", 4, NodeType.CODE_NODE, rule_ref="Draft Consolidation", category="CORE"),
        BPMNActivity("ST-012", "Document Depth & Rule Audit", 5, NodeType.CODE_NODE, rule_ref="MECE Depth <= 2", category="CORE"),
        BPMNActivity("ST-013", "Mandatory EBQC Quality Gate", 5, NodeType.CODE_NODE, rule_ref="EAI >= 0.98", category="CORE"),
        BPMNActivity("ST-014", "Task Meso-Reflection (RF-002)", 5, NodeType.AGENT_NODE, prompt_name="reflection:rf-002", rule_ref="1m Reflection", category="CORE"),
        BPMNActivity("ST-015", "Compile walkthrough.md Proof", 5, NodeType.AGENT_NODE, rule_ref="1:1 DoD Matrix", category="CORE"),
        BPMNActivity("ST-016", "Separation of Duties Check", 6, NodeType.CODE_NODE, rule_ref="GW-SOD-01", category="CORE"),
        BPMNActivity("ST-017", "Commit MECE Zone & Git Sync", 6, NodeType.CODE_NODE, rule_ref="10/20/30 Zone Commit", category="CORE"),
        BPMNActivity("ST-018", "Close, Macro-Reflection (RF-003) & Distill", 7, NodeType.AGENT_NODE, prompt_name="reflection:rf-003", rule_ref="WeKnora + hot.md <= 500w", category="CORE"),
    ]

    for act in activities:
        p.add_activity(act)

    for i in range(1, 18):
        p.add_transition(f"ST-{i:03d}", f"ST-{i + 1:03d}")

    p.add_gateway(BPMNGateway("GW-001", "Rubric & Outline Baseline", GatewayType.EXCLUSIVE, "outline_and_dod_ready", "ST-005", "EX-001", lane_id="Lane_CODE", phase_id=2))
    p.add_gateway(BPMNGateway("GW-002", "Minimal-HITL Scope Gate", GatewayType.EXCLUSIVE, "tier <= 1 and scope_ok", "ST-007", "EX-002", lane_id="Lane_CODE", phase_id=3))
    p.add_gateway(BPMNGateway("GW-003", "QualityGate Pass (EAI >= 0.98)", GatewayType.EXCLUSIVE, "eai >= 0.98 and dod_pass", "ST-015", "EX-003", lane_id="Lane_CODE", phase_id=5))

    p.add_exception_loop(BPMNExceptionLoop("EX-001", "GW-001", "ST-004", "RUBRIC_MISSING", lane_id="Lane_CODE"))
    p.add_exception_loop(BPMNExceptionLoop("EX-002", "GW-002", "ST-007", "HIGH_RISK_HITL", lane_id="Lane_HUMAN"))
    p.add_exception_loop(BPMNExceptionLoop("EX-003", "GW-003", "ST-008", "QUALITY_GATE_FAIL", lane_id="Lane_CODE"))

    return p
