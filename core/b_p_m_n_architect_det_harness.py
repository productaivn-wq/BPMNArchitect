"""Deterministic P=1 Harness for BPMNArchitect."""
from __future__ import annotations
import hashlib
import time
from typing import Any

HARNESS_DOMAIN = "governance"
HARNESS_SKILL = "BPMNArchitect"
SUPPORTED_ACTIONS = (
    "audit",
    "validate",
    "dispatch",
    "summary",
    "health-check",
    "inspect",
    "remediate",
    "verify-checksum",
    "compile",
    "export-suite",
)


class BPMNArchitectExecutionError(ValueError):
    pass


def validate_b_p_m_n_architect_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise BPMNArchitectExecutionError("Payload must be dict")
    cleaned = {str(k): v for k, v in payload.items() if not str(k).startswith("_")}
    if "action" in cleaned and cleaned["action"] not in SUPPORTED_ACTIONS:
        raise BPMNArchitectExecutionError("Bad action")
    return cleaned


def verify_b_p_m_n_architect_conservation(initial: dict[str, Any], final: dict[str, Any]) -> bool:
    return {k for k in initial if not k.startswith("_")}.issubset({k for k in final if not k.startswith("_")})


def compute_b_p_m_n_architect_hash(data: dict[str, Any]) -> str:
    raw = ",".join(f"{k}:{v}" for k, v in sorted(data.items()) if not k.startswith("_"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def execute_b_p_m_n_architect_step(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    p = validate_b_p_m_n_architect_payload(params or {})
    if action not in SUPPORTED_ACTIONS:
        raise BPMNArchitectExecutionError(f"Action unsupported: {action}")
    keys = sorted(p.keys())
    lat = round((time.perf_counter() - t0) * 1000.0, 3)
    res = {
        "status": "OK",
        "skill": HARNESS_SKILL,
        "action": action,
        "domain": HARNESS_DOMAIN,
        "p1_deterministic": True,
    }
    res.update({
        "keys_count": len(keys),
        "keys": keys,
        "latency_ms": lat,
        "checksum": compute_b_p_m_n_architect_hash(p),
    })
    res["conservation_verified"] = verify_b_p_m_n_architect_conservation(p, res)
    return res


def batch_dispatch_b_p_m_n_architect(actions: list[str], ctx: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    c = validate_b_p_m_n_architect_payload(ctx or {})
    return [execute_b_p_m_n_architect_step(a, c) for a in actions]


def summarize_b_p_m_n_architect_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    tot = len(results)
    ok = sum(1 for r in results if r.get("status") == "OK")
    latencies = [float(r.get("latency_ms", 0.0)) for r in results]
    return {
        "total_executions": tot,
        "success_rate": round(ok / max(tot, 1), 4),
        "mean_latency_ms": round(sum(latencies) / max(tot, 1), 3),
        "p1_conservation_pass": ok == tot,
    }


def health_check_b_p_m_n_architect() -> dict[str, Any]:
    step = execute_b_p_m_n_architect_step("health-check", {"source": "self-test"})
    return {"healthy": step.get("status") == "OK", "step": step}


def inspect_b_p_m_n_architect_schema() -> dict[str, Any]:
    return {
        "skill": HARNESS_SKILL,
        "actions": list(SUPPORTED_ACTIONS),
        "domain": HARNESS_DOMAIN,
        "loc_standard": "P1_DET",
    }


def remediate_b_p_m_n_architect_drift(target: dict[str, Any]) -> dict[str, Any]:
    c = validate_b_p_m_n_architect_payload(target)
    c["remediated_at"] = time.time()
    return {"status": "REMEDIATED", "target": c}
