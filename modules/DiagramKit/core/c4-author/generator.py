"""
C4 Architecture Diagram Generator for DiagramKit.
Implements: UC-001
"""

from typing import Any, Dict, List, Optional


class C4DiagramGenerator:
    """Generates C4 Architecture diagrams and PlantUML models from structured definitions."""

    def __init__(self, title: str = "", level: str = "Context"):
        self.title = title
        self.level = level
        self.elements: List[Dict[str, Any]] = []
        self.relationships: List[Dict[str, Any]] = []

    def add_element(
        self,
        element_id: str,
        name: str,
        element_type: str = "System",
        description: str = "",
        technology: str = "",
    ) -> None:
        """Add a C4 element (Person, System, Container, Component)."""
        self.elements.append(
            {
                "id": element_id,
                "name": name,
                "type": element_type,
                "description": description,
                "technology": technology,
            }
        )

    def add_relationship(
        self,
        from_id: str,
        to_id: str,
        description: str = "",
        technology: str = "",
    ) -> None:
        """Add a directed relationship between C4 elements."""
        self.relationships.append(
            {
                "from": from_id,
                "to": to_id,
                "description": description,
                "technology": technology,
            }
        )

    def parse_landscape_definition(self, landscape: Dict[str, Any]) -> None:
        """Parse structured landscape dictionary into diagram elements and relationships."""
        self.title = landscape.get("title", self.title)
        self.level = landscape.get("level", self.level)
        self.elements = []
        self.relationships = []

        for elem in landscape.get("elements", []):
            self.add_element(
                element_id=elem.get("id", ""),
                name=elem.get("name", ""),
                element_type=elem.get("type", "System"),
                description=elem.get("description", ""),
                technology=elem.get("technology", ""),
            )

        for rel in landscape.get("relationships", []):
            self.add_relationship(
                from_id=rel.get("from", ""),
                to_id=rel.get("to", ""),
                description=rel.get("description", ""),
                technology=rel.get("technology", ""),
            )

    def generate_plantuml(self) -> str:
        """Generate PlantUML C4 markup."""
        lines = [
            "@startuml",
            f"!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_{self.level}.puml",
        ]
        if self.title:
            lines.append(f"title {self.title}")
        lines.append("")

        for elem in self.elements:
            etype = elem["type"]
            eid = elem["id"]
            ename = elem["name"]
            edesc = elem["description"]
            etech = elem.get("technology", "")

            if etype == "Person":
                lines.append(f'Person({eid}, "{ename}", "{edesc}")')
            elif etype == "Container":
                if etech:
                    lines.append(f'Container({eid}, "{ename}", "{etech}", "{edesc}")')
                else:
                    lines.append(f'Container({eid}, "{ename}", "{edesc}")')
            elif etype == "Component":
                if etech:
                    lines.append(f'Component({eid}, "{ename}", "{etech}", "{edesc}")')
                else:
                    lines.append(f'Component({eid}, "{ename}", "{edesc}")')
            else:  # System
                lines.append(f'System({eid}, "{ename}", "{edesc}")')

        lines.append("")
        for rel in self.relationships:
            r_from = rel["from"]
            r_to = rel["to"]
            r_desc = rel["description"]
            r_tech = rel.get("technology", "")
            if r_tech:
                lines.append(f'Rel({r_from}, {r_to}, "{r_desc}", "{r_tech}")')
            else:
                lines.append(f'Rel({r_from}, {r_to}, "{r_desc}")')

        lines.append("@enduml")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Export diagram metadata as dictionary."""
        return {
            "title": self.title,
            "level": self.level,
            "elements": self.elements,
            "relationships": self.relationships,
        }


def main():
    print("C4 Diagram Generator module ready.")


if __name__ == "__main__":
    main()
