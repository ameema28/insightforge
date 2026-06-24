"""
InsightForge Session Memory

Lightweight JSON-file persistence for Streamlit sessions.
In production, swap for Firestore or Redis.
"""

import json
import os
from typing import Any, Dict


class MemoryBank:
    """Simple file-based memory store for agent sessions."""

    def __init__(self, storage_dir: str = ".memory"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _file_path(self, session_id: str) -> str:
        safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
        return os.path.join(self.storage_dir, f"{safe_id}.json")

    def get(self, session_id: str) -> Dict[str, Any]:
        """Retrieve memory for a session."""
        path = self._file_path(session_id)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def set(self, session_id: str, key: str, value: Any):
        """Store a key-value pair for a session."""
        data = self.get(session_id)
        data[key] = value
        self._save(session_id, data)

    def _save(self, session_id: str, data: Dict[str, Any]):
        path = self._file_path(session_id)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def clear(self, session_id: str):
        """Clear memory for a session."""
        path = self._file_path(session_id)
        if os.path.exists(path):
            os.remove(path)


# Global instance
memory_bank = MemoryBank()