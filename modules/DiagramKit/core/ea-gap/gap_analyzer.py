"""
Enterprise Architecture Gap Analyzer & Sync Engine.
Implements: UC-001
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EAComponent:
    id: str
    name: str = ""
    capabilities: List[str] = field(default_factory=list)
    technology: str = ""
    dependencies: List[str] = field(default_factory=list)
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EAComponent":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            capabilities=list(data.get("capabilities", [])),
            technology=data.get("technology", ""),
            dependencies=list(data.get("dependencies", [])),
            description=data.get("description", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "capabilities": self.capabilities,
            "technology": self.technology,
            "dependencies": self.dependencies,
            "description": self.description,
        }


@dataclass
class SyncRuleResult:
    rule_id: str
    name: str
    passed: bool
    details: str
    affected_components: List[str] = field(default_factory=list)


class StandaloneSyncEngine:
    """Standalone engine for EA artifact syncing, validation, and gap analysis."""

    def __init__(self):
        self.states: Dict[str, Dict[str, EAComponent]] = {
            "current": {},
            "target": {},
        }

    def load_architecture_state(self, state_name: str, components: List[Any]) -> None:
        """Load components into a named architecture state ('current' or 'target')."""
        comp_map: Dict[str, EAComponent] = {}
        for c in components:
            if isinstance(c, EAComponent):
                comp_map[c.id] = c
            elif isinstance(c, dict):
                comp = EAComponent.from_dict(c)
                comp_map[comp.id] = comp
        self.states[state_name] = comp_map

    def audit_sync_rules(self) -> List[SyncRuleResult]:
        """Audit all architecture sync rules across loaded states."""
        results: List[SyncRuleResult] = []

        # SYNC-RULE-001: Unique Identification
        r1_passed = True
        r1_affected = []
        for state_name, comps in self.states.items():
            seen = set()
            for cid in comps:
                if cid in seen:
                    r1_passed = False
                    r1_affected.append(f"{state_name}:{cid}")
                seen.add(cid)
        results.append(
            SyncRuleResult(
                rule_id="SYNC-RULE-001",
                name="Unique Component Identification",
                passed=r1_passed,
                details="All component IDs must be unique within each state."
                if r1_passed
                else "Duplicate IDs found.",
                affected_components=r1_affected,
            )
        )

        # SYNC-RULE-002: Orphan Dependency Check
        target_comps = self.states.get("target", {})
        orphan_deps = []
        for cid, comp in target_comps.items():
            for dep in comp.dependencies:
                if dep not in target_comps:
                    orphan_deps.append(f"{cid} -> missing_dep:{dep}")

        r2_passed = len(orphan_deps) == 0
        results.append(
            SyncRuleResult(
                rule_id="SYNC-RULE-002",
                name="No Orphan Dependencies",
                passed=r2_passed,
                details="All dependencies in target state must resolve to known components."
                if r2_passed
                else f"Orphan dependencies found: {orphan_deps}",
                affected_components=orphan_deps,
            )
        )

        # SYNC-RULE-003: Non-empty Component Name
        empty_names = []
        for state_name, comps in self.states.items():
            for cid, comp in comps.items():
                if not comp.name:
                    empty_names.append(f"{state_name}:{cid}")
        r3_passed = len(empty_names) == 0
        results.append(
            SyncRuleResult(
                rule_id="SYNC-RULE-003",
                name="Valid Component Naming",
                passed=r3_passed,
                details="All components must have valid names."
                if r3_passed
                else f"Components with missing names: {empty_names}",
                affected_components=empty_names,
            )
        )

        return results

    def analyze_gaps(self) -> Dict[str, Any]:
        """Perform delta and gap analysis between current and target architectures."""
        current = self.states.get("current", {})
        target = self.states.get("target", {})

        current_ids = set(current.keys())
        target_ids = set(target.keys())

        added_ids = target_ids - current_ids
        removed_ids = current_ids - target_ids
        common_ids = current_ids & target_ids

        modified_ids = set()
        unchanged_ids = set()

        for cid in common_ids:
            c_curr = current[cid]
            c_targ = target[cid]
            if (
                c_curr.name != c_targ.name
                or set(c_curr.capabilities) != set(c_targ.capabilities)
                or c_curr.technology != c_targ.technology
                or set(c_curr.dependencies) != set(c_targ.dependencies)
            ):
                modified_ids.add(cid)
            else:
                unchanged_ids.add(cid)

        return {
            "summary": {
                "total_current": len(current),
                "total_target": len(target),
                "added": len(added_ids),
                "removed": len(removed_ids),
                "modified": len(modified_ids),
                "unchanged": len(unchanged_ids),
            },
            "added": [target[cid].to_dict() for cid in added_ids],
            "removed": [current[cid].to_dict() for cid in removed_ids],
            "modified": [
                {
                    "id": cid,
                    "current": current[cid].to_dict(),
                    "target": target[cid].to_dict(),
                }
                for cid in modified_ids
            ],
            "unchanged": [target[cid].to_dict() for cid in unchanged_ids],
        }


def main():
    print("EA Gap Analyzer Standalone Engine initialized.")


if __name__ == "__main__":
    main()
