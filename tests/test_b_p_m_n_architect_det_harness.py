"""Tests for deterministic harness BPMNArchitect."""
from pathlib import Path
import sys

_SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from core.b_p_m_n_architect_det_harness import (
    batch_dispatch_b_p_m_n_architect,
    execute_b_p_m_n_architect_step,
    health_check_b_p_m_n_architect,
    summarize_b_p_m_n_architect_metrics,
)


def test_b_p_m_n_architect_deterministic_execution() -> None:
    res = execute_b_p_m_n_architect_step("health-check", {"check_id": "CHK-01"})
    assert res["status"] == "OK" and res["p1_deterministic"] is True


def test_b_p_m_n_architect_batch_and_summary() -> None:
    res = batch_dispatch_b_p_m_n_architect(["audit", "summary"], {"env": "test"})
    assert len(res) == 2 and summarize_b_p_m_n_architect_metrics(res)["p1_conservation_pass"] is True


def test_b_p_m_n_architect_health_check() -> None:
    assert health_check_b_p_m_n_architect()["healthy"] is True
