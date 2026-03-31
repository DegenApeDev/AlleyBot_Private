"""
SessionStore - Persistent session management

Handles save/load of cognitive sessions for continuity across restarts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class StoredSession:
    """A persisted cognitive session."""
    session_id: str
    messages: tuple[str, ...]
    input_tokens: int = 0
    output_tokens: int = 0
    timestamp: str = field(default_factory=lambda: __import__('datetime').datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionStore:
    """
    Manages persistent storage of cognitive sessions.
    
    Sessions survive process restarts and can be resumed.
    """
    storage_dir: Path = field(default_factory=lambda: Path.home() / ".alleybot" / "sessions")
    
    def __post_init__(self):
        """Ensure storage directory exists."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session: StoredSession) -> Path:
        """
        Save a session to storage.
        
        Returns:
            Path to saved session file
        """
        filepath = self.storage_dir / f"{session.session_id}.json"
        
        data = {
            "session_id": session.session_id,
            "messages": list(session.messages),
            "input_tokens": session.input_tokens,
            "output_tokens": session.output_tokens,
            "timestamp": session.timestamp,
            "metadata": session.metadata,
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        return filepath

    def load(self, session_id: str) -> StoredSession:
        """
        Load a session from storage.
        
        Raises:
            FileNotFoundError: If session doesn't exist
        """
        filepath = self.storage_dir / f"{session_id}.json"
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        return StoredSession(
            session_id=data["session_id"],
            messages=tuple(data.get("messages", [])),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            timestamp=data.get("timestamp", ""),
            metadata=data.get("metadata", {}),
        )

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all available sessions with metadata."""
        sessions: list[dict[str, Any]] = []
        
        for filepath in self.storage_dir.glob("*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data.get("session_id", filepath.stem),
                    "timestamp": data.get("timestamp", ""),
                    "message_count": len(data.get("messages", [])),
                    "tokens": data.get("input_tokens", 0) + data.get("output_tokens", 0),
                    "filepath": str(filepath),
                })
            except (json.JSONDecodeError, IOError):
                continue  # Skip corrupted files
        
        # Sort by timestamp descending
        sessions.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
        return sessions

    def delete(self, session_id: str) -> bool:
        """
        Delete a session from storage.
        
        Returns:
            True if deleted, False if not found
        """
        filepath = self.storage_dir / f"{session_id}.json"
        
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return (self.storage_dir / f"{session_id}.json").exists()

    def get_storage_path(self, session_id: str) -> Path:
        """Get the storage path for a session."""
        return self.storage_dir / f"{session_id}.json"

    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """
        Remove sessions older than specified days.
        
        Returns:
            Number of sessions removed
        """
        from datetime import datetime, timedelta
        
        cutoff = datetime.now() - timedelta(days=max_age_days)
        removed = 0
        
        for filepath in self.storage_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mtime < cutoff:
                    filepath.unlink()
                    removed += 1
            except (OSError, IOError):
                continue
        
        return removed

    def get_summary(self) -> str:
        """Get human-readable storage summary."""
        sessions = self.list_sessions()
        total_size = sum(
            f.stat().st_size 
            for f in self.storage_dir.glob("*.json")
        )
        
        lines = [
            f"Storage: {self.storage_dir}",
            f"Sessions: {len(sessions)}",
            f"Total size: {total_size / 1024:.1f} KB",
        ]
        return "\n".join(lines)
