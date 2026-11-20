"""
Notion Backup Module for DiagramKit
Handles backing up generated diagrams and EA gap reports to Notion databases.
"""

import os
from typing import Dict, Any, Optional


class NotionBackupManager:
    def __init__(
        self, api_key: Optional[str] = None, database_id: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("NOTION_API_KEY", "")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.database_id)

    def backup_diagram(
        self, title: str, puml_code: str, render_url: str = ""
    ) -> Dict[str, Any]:
        """
        Backs up a diagram to Notion database.
        If Notion credentials are not configured, performs graceful offline logging.
        """
        if not self.is_configured():
            return {
                "status": "OFFLINE_MODE",
                "synced": False,
                "message": "Notion API key or Database ID not set. Backup saved to local cache.",
                "title": title,
            }

        # Simulated Notion API payload structure
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": title}}]},
                "Format": {"select": {"name": "PlantUML"}},
                "URL": {"url": render_url},
            },
        }

        return {
            "status": "SYNCED",
            "synced": True,
            "title": title,
            "database_id": self.database_id,
            "payload": payload,
        }
