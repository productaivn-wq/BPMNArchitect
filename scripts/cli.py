"""[CANARY:AGENTS.md:GOVERNED] Layer-2 Click CLI for BPMNArchitect."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import click

_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))
_SRC = _SKILL_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core.b_p_m_n_architect_det_harness import (
    SUPPORTED_ACTIONS,
    execute_b_p_m_n_architect_step,
)
from bpmn_process_compiler import (
    BPMNProcess,
    build_canonical_18_step_process,
    build_canonical_37_step_process,
    check_arrow_overlaps,
    verify_layout,
)

CLI_ACTIONS = tuple(SUPPORTED_ACTIONS) + ("verify-bpmn",)


def _resolve_processes(ir_path: str = "", process_key: str = "both") -> list[BPMNProcess]:
    if ir_path:
        data = json.loads(Path(ir_path).read_text(encoding="utf-8"))
        return [BPMNProcess.from_ir_dict(data)]
    if process_key == "37":
        return [build_canonical_37_step_process()]
    if process_key == "18":
        return [build_canonical_18_step_process()]
    return [build_canonical_37_step_process(), build_canonical_18_step_process()]


@click.command(
    name="b_p_m_n_architect-cli",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option("--action", type=click.Choice(CLI_ACTIONS), default="summary")
@click.option("--params", type=str, default="{}")
@click.option("--json", "as_json", is_flag=True, default=True)
@click.option("--target-dir", default="")
@click.option("--ir", "ir_path", default="", help="Optional path to a 2-layer *.ir.json file.")
def main(
    action: str,
    params: str,
    as_json: bool,
    target_dir: str = "",
    ir_path: str = "",
) -> None:
    try:
        p = json.loads(params)
        if not isinstance(p, dict):
            p = {"raw": p}
    except Exception:
        p = {"raw": params}

    out_dir = target_dir or str(p.get("output_dir") or "")

    if action == "export-suite":
        procs = _resolve_processes(ir_path=ir_path or str(p.get("ir_path") or ""), process_key=str(p.get("process", "both")))
        dest = Path(out_dir) if out_dir else (_SKILL_ROOT / "examples")
        res = procs[0].export_deliverable_package(dest, additional_processes=procs[1:])
        click.echo(json.dumps(res, indent=2, ensure_ascii=False) if as_json else str(res))
        return

    if action == "verify-bpmn":
        bpmn_file = str(p.get("bpmn_path") or "")
        if bpmn_file:
            xml_str = Path(bpmn_file).read_text(encoding="utf-8")
            lay = verify_layout(xml_str)
            ov = check_arrow_overlaps(xml_str)
            res = {
                "status": "OK" if (lay["ok"] and ov["ok"]) else "FAIL",
                "bpmn_path": bpmn_file,
                "layout": lay,
                "arrow_overlaps": ov,
            }
        else:
            procs = _resolve_processes(ir_path=ir_path or str(p.get("ir_path") or ""), process_key=str(p.get("process", "both")))
            reports = {}
            all_ok = True
            for proc in procs:
                xml_str = proc.to_camunda_bpmn_xml()
                sem = proc.verify_semantic_invariants()
                lay = verify_layout(xml_str)
                ov = check_arrow_overlaps(xml_str)
                proc_ok = sem["ok"] and lay["ok"] and ov["ok"]
                all_ok = all_ok and proc_ok
                reports[proc.process_id] = {
                    "semantic_ok": sem["ok"],
                    "shape_collisions": lay["shape_collisions"],
                    "box_intersections": lay["box_intersections"],
                    "arrow_overlaps": ov["overlap_count"],
                    "ergonomic_violations": lay["ergonomic_violations"],
                }
            res = {"status": "OK" if all_ok else "FAIL", "verifications": reports}
        click.echo(json.dumps(res, indent=2, ensure_ascii=False) if as_json else str(res))
        return

    res = execute_b_p_m_n_architect_step(action, p)
    click.echo(json.dumps(res, indent=2, ensure_ascii=False) if as_json else str(res))


if __name__ == "__main__":
    main()
