"""
PlantUML Rendering Engine Configuration & Security Policy
"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PlantUMLConfig:
    server_url: str = os.getenv("PLANTUML_SERVER_URL", "http://localhost:8080")
    fallback_server_url: str = "http://www.plantuml.com/plantuml"
    output_format: str = os.getenv("PLANTUML_OUTPUT_FORMAT", "svg")
    timeout_seconds: int = int(os.getenv("PLANTUML_TIMEOUT", "30"))
    strict_sanitization: bool = os.getenv("PLANTUML_STRICT_MODE", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    notion_api_key: str = os.getenv("NOTION_API_KEY", "")
    notion_database_id: str = os.getenv("NOTION_DATABASE_ID", "")

    # Security policy forbidden tokens in PlantUML markup
    FORBIDDEN_DIRECTIVES = [
        "!include",
        "!includeurl",
        "!includepath",
        "!import",
        "%filename%",
        "!pragma",
        "java.io",
        "system(",
        "exec(",
    ]

    def validate(self) -> dict:
        """Validates rendering engine configuration state."""
        return {
            "server_url": self.server_url,
            "fallback_server_url": self.fallback_server_url,
            "output_format": self.output_format,
            "timeout_seconds": self.timeout_seconds,
            "strict_sanitization": self.strict_sanitization,
            "notion_configured": bool(self.notion_api_key and self.notion_database_id),
            "forbidden_directives_count": len(self.FORBIDDEN_DIRECTIVES),
        }


default_config = PlantUMLConfig()
