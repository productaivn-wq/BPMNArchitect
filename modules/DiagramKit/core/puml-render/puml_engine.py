"""
PlantUML Rendering Engine Module
Handles PlantUML code sanitization, 64-bit URL encoding, local/remote server rendering, and engine verification.
"""

import zlib
import string
import urllib.request
import urllib.parse
from typing import Dict, Any, Tuple
from pathlib import Path
import sys

# Support relative import when run directly or imported
try:
    from .config import default_config, PlantUMLConfig
except ImportError:
    from config import default_config, PlantUMLConfig

# PlantUML custom 64-character alphabet for URL encoding
PLANTUML_ALPHABET = (
    string.ascii_uppercase + string.ascii_lowercase + string.digits + "-_"
)


def encode_plantuml(puml_text: str) -> str:
    """Encodes PlantUML string using deflate compression + PlantUML 64-bit encoding."""
    zlib_compress = zlib.compressobj(9, zlib.DEFLATED, -15)
    compressed = (
        zlib_compress.compress(puml_text.encode("utf-8")) + zlib_compress.flush()
    )

    res = []
    for i in range(0, len(compressed), 3):
        b1 = compressed[i]
        b2 = compressed[i + 1] if i + 1 < len(compressed) else 0
        b3 = compressed[i + 2] if i + 2 < len(compressed) else 0

        c1 = b1 >> 2
        c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
        c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
        c4 = b3 & 0x3F

        res.append(PLANTUML_ALPHABET[c1 & 0x3F])
        res.append(PLANTUML_ALPHABET[c2 & 0x3F])
        res.append(PLANTUML_ALPHABET[c3 & 0x3F])
        res.append(PLANTUML_ALPHABET[c4 & 0x3F])

    return "".join(res)


class PlantUMLRenderEngine:
    """PlantUML Rendering Engine with sanitization and verification."""

    def __init__(self, config: PlantUMLConfig = None):
        self.config = config or default_config

    def sanitize(self, puml_code: str) -> Tuple[str, bool, list]:
        """
        Sanitizes PlantUML source code by stripping or blocking forbidden directives.
        Returns: (sanitized_code, is_clean, list_of_violations)
        """
        violations = []
        clean_lines = []

        for line in puml_code.splitlines():
            line_str = line.strip()
            found_forbidden = False
            for directive in self.config.FORBIDDEN_DIRECTIVES:
                if directive.lower() in line_str.lower():
                    violations.append(
                        f"Forbidden directive '{directive}' found in line: '{line_str}'"
                    )
                    found_forbidden = True
                    break

            if not found_forbidden:
                clean_lines.append(line)
            else:
                if not self.config.strict_sanitization:
                    # In non-strict mode, comment out forbidden line
                    clean_lines.append(f"' REMOVED_BY_SANITIZER: {line}")

        is_clean = len(violations) == 0
        sanitized_code = "\n".join(clean_lines)
        return sanitized_code, is_clean, violations

    def verify_configuration(self) -> Dict[str, Any]:
        """Audits and verifies the rendering engine configuration and readiness."""
        cfg_status = self.config.validate()

        # Verify encoding capability
        test_puml = "@startuml\nBob -> Alice : hello\n@enduml"
        try:
            encoded = encode_plantuml(test_puml)
            encoding_ok = bool(encoded)
        except Exception as e:
            encoding_ok = False

        return {
            "status": "HEALTHY" if encoding_ok else "UNHEALTHY",
            "configuration": cfg_status,
            "encoding_functional": encoding_ok,
            "engine_version": "0.1.0",
        }

    def render(self, puml_code: str, output_format: str = None) -> Dict[str, Any]:
        """
        Renders PlantUML code to SVG/PNG URL or string representation.
        Includes full sanitization check and graceful error handling.
        """
        fmt = output_format or self.config.output_format
        sanitized_code, is_clean, violations = self.sanitize(puml_code)

        if not is_clean and self.config.strict_sanitization:
            return {
                "success": False,
                "error": "Sanitization failed due to forbidden directives.",
                "violations": violations,
                "output": None,
            }

        encoded = encode_plantuml(sanitized_code)
        primary_url = f"{self.config.server_url.rstrip('/')}/{fmt}/{encoded}"
        fallback_url = f"{self.config.fallback_server_url.rstrip('/')}/{fmt}/{encoded}"

        return {
            "success": True,
            "sanitized": is_clean,
            "violations": violations,
            "format": fmt,
            "render_url": primary_url,
            "fallback_url": fallback_url,
            "encoded_markup": encoded,
        }


def main():
    engine = PlantUMLRenderEngine()
    health = engine.verify_configuration()
    print("PlantUML Engine Health Check:", health)

    sample_puml = (
        "@startuml\nAlice -> Bob: Authentication Request\n!include secret.puml\n@enduml"
    )
    result = engine.render(sample_puml)
    print("Render Result:", result)


if __name__ == "__main__":
    main()
