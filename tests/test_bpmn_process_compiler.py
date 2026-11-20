"""Tests for BPMNProcessCompiler & Multi-Format Camunda BPMN 2.0 Studio."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bpmn_process_compiler import (
    BPMNActivity,
    BPMNExceptionLoop,
    BPMNGateway,
    BPMNLane,
    BPMNProcess,
    GatewayType,
    NodeType,
    build_canonical_18_step_process,
    build_canonical_37_step_process,
    check_arrow_overlaps,
    verify_layout,
)


class TestBPMNProcessCompiler(unittest.TestCase):
    def test_canonical_37_step_build(self):
        p = build_canonical_37_step_process()
        self.assertEqual(p.process_id, "53.REF.07")
        self.assertEqual(len(p.phases), 7)
        self.assertEqual(len(p.activities), 37)
        self.assertEqual(len(p.gateways), 4)
        self.assertEqual(len(p.exception_loops), 4)

    def test_canonical_18_step_build(self):
        p = build_canonical_18_step_process()
        self.assertEqual(p.process_id, "53.REF.08")
        self.assertEqual(p.protocol_type, "CORE")
        self.assertEqual(len(p.phases), 7)
        self.assertEqual(len(p.activities), 18)
        self.assertEqual(len(p.gateways), 3)
        self.assertEqual(len(p.exception_loops), 3)

    def test_kahn_dag_compilation(self):
        p = build_canonical_37_step_process()
        dag = p.to_execution_dag()
        self.assertTrue(dag["is_acyclic"])
        self.assertEqual(dag["total_activities"], 37)
        self.assertGreater(len(dag["kahn_waves"]), 0)

    def test_langgraph_export(self):
        p = build_canonical_37_step_process()
        lg = p.to_langgraph_dict()
        self.assertEqual(len(lg["nodes"]), 37)
        self.assertEqual(len(lg["conditional_edges"]), 4)
        self.assertEqual(len(lg["exception_loops"]), 4)

    def test_camunda_xml_pools_lanes_labels_and_loops(self):
        for builder in (build_canonical_37_step_process, build_canonical_18_step_process):
            p = builder()
            xml_str = p.to_camunda_bpmn_xml()
            root = ET.fromstring(xml_str)
            ns = {
                "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
                "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
            }
            self.assertEqual(len(root.findall(".//bpmn:collaboration", ns)), 1)
            self.assertEqual(len(root.findall(".//bpmn:participant", ns)), 1)
            self.assertEqual(len(root.findall(".//bpmn:lane", ns)), 3)
            self.assertIn("&#10;", xml_str)
            for gw_id in p.gateways:
                shape = root.find(f".//bpmndi:BPMNShape[@bpmnElement='{gw_id}']", ns)
                self.assertIsNotNone(shape)
                self.assertEqual(shape.attrib.get("isMarkerVisible"), "true")
                self.assertIsNotNone(shape.find("bpmndi:BPMNLabel", ns))
            for ex_id in p.exception_loops:
                self.assertIsNotNone(root.find(f".//*[@id='{ex_id}']", ns))

    def test_semantic_layout_and_arrow_overlap_verifiers(self):
        for builder in (build_canonical_37_step_process, build_canonical_18_step_process):
            p = builder()
            sem = p.verify_semantic_invariants()
            self.assertTrue(sem["ok"], msg=f"Semantic errors: {sem['errors']}")
            self.assertEqual(sem["unreachable"], [])
            self.assertEqual(sem["dead_ends"], [])

            xml_str = p.to_camunda_bpmn_xml()
            lay = verify_layout(xml_str)
            self.assertTrue(lay["ok"], msg=f"Layout issues: {lay}")
            self.assertEqual(lay["shape_collisions"], 0)
            self.assertEqual(lay["box_intersections"], 0)
            self.assertEqual(lay["ergonomic_violations"], [])

            ov = check_arrow_overlaps(xml_str)
            self.assertTrue(ov["ok"], msg=f"Arrow overlaps: {ov}")
            self.assertEqual(ov["overlap_count"], 0)
            self.assertEqual(ov["diagonal_segments"], [])

    def test_semantic_verifier_rejects_broken_gateway(self):
        p = BPMNProcess("BAD.01", "Broken Gateway Process")
        p.add_phase(1, "Only")
        p.add_activity(BPMNActivity("ST-001", "Start Step", 1, NodeType.HUMAN_NODE))
        p.add_activity(BPMNActivity("ST-002", "End Step", 1, NodeType.CODE_NODE))
        p.add_transition("ST-001", "ST-002")
        p.add_gateway(
            BPMNGateway("GW-001", "Collapsed Gate", GatewayType.EXCLUSIVE, "x == 1", "ST-002", "ST-002")
        )
        sem = p.verify_semantic_invariants()
        self.assertFalse(sem["ok"])

    def test_ir_round_trip(self):
        orig = build_canonical_18_step_process()
        ir = orig.to_ir_dict()
        restored = BPMNProcess.from_ir_dict(ir)
        self.assertEqual(restored.process_id, orig.process_id)
        self.assertEqual(len(restored.activities), len(orig.activities))
        self.assertEqual(len(restored.gateways), len(orig.gateways))
        self.assertEqual(len(restored.exception_loops), len(orig.exception_loops))
        self.assertEqual(restored.to_camunda_bpmn_xml(), orig.to_camunda_bpmn_xml())

    def test_multiformat_exporters_and_deliverable_package(self):
        p37 = build_canonical_37_step_process()
        p18 = build_canonical_18_step_process()

        puml = p37.to_plantuml()
        self.assertIn("@startuml", puml)
        self.assertIn("@enduml", puml)
        self.assertIn("GW-001", puml)

        mmd = p18.to_mermaid()
        self.assertIn("flowchart TD", mmd)
        self.assertIn("GW_001", mmd)

        spec_md = p37.to_utop_markdown_spec()
        self.assertIn("Step-by-Step Execution Matrix", spec_md)
        self.assertIn("ST-037", spec_md)

        studio_html = p37.to_interactive_html_viewer(additional_processes=[p18])
        self.assertIn("bpmn-modeler.production.min.js", studio_html)
        self.assertIn("53.REF.07", studio_html)
        self.assertIn("53.REF.08", studio_html)

        with tempfile.TemporaryDirectory() as tmpdir:
            res = p37.export_deliverable_package(tmpdir, additional_processes=[p18])
            self.assertEqual(res["status"], "OK")
            out = Path(tmpdir)
            for fname in (
                "53_REF_07.bpmn",
                "53_REF_07.ir.json",
                "53_REF_07.puml",
                "53_REF_07.mermaid",
                "53_REF_07_SPEC.md",
                "53_REF_08.bpmn",
                "53_REF_07_camunda_studio.html",
            ):
                self.assertTrue((out / fname).is_file(), msg=f"Missing exported file {fname}")
            loaded_ir = json.loads((out / "53_REF_07.ir.json").read_text(encoding="utf-8"))
            self.assertEqual(loaded_ir["process"]["id"], "53.REF.07")


if __name__ == "__main__":
    unittest.main()
