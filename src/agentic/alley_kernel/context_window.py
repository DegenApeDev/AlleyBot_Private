"""
ContextWindow - Conversational context management with compaction

Prevents context window overflow through intelligent message compaction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextWindow:
    """
    Manages conversational context with automatic compaction.
    
    Similar to transcript store but with AlleyBot-native terminology.
    Prevents memory overflow in long-running sessions.
    """
    entries: list[str] = field(default_factory=list)
    flushed: bool = False
    max_size: int = 1000  # Maximum entries before forced compaction
    metadata: dict[str, Any] = field(default_factory=dict)

    def append(self, entry: str) -> None:
        """Add an entry to the context window."""
        self.entries.append(entry)
        self.flushed = False
        
        # Auto-compact if exceeding max size
        if len(self.entries) > self.max_size:
            self.compact(keep_last=self.max_size // 2)

    def extend(self, entries: list[str]) -> None:
        """Add multiple entries."""
        self.entries.extend(entries)
        self.flushed = False
        
        if len(self.entries) > self.max_size:
            self.compact(keep_last=self.max_size // 2)

    def compact(self, keep_last: int = 10) -> None:
        """
        Compact the context window to prevent overflow.
        
        Args:
            keep_last: Number of recent entries to preserve
        """
        if len(self.entries) > keep_last:
            # Preserve most recent entries
            preserved = self.entries[-keep_last:]
            
            # Create summary of compacted content
            compacted_count = len(self.entries) - keep_last
            summary = f"[... {compacted_count} earlier entries compacted ...]"
            
            # Update entries
            self.entries = [summary] + preserved
            
            # Track compaction in metadata
            self.metadata["compactions"] = self.metadata.get("compactions", 0) + 1
            self.metadata["total_compacted"] = self.metadata.get("total_compacted", 0) + compacted_count

    def replay(self) -> tuple[str, ...]:
        """Replay all entries as a tuple."""
        return tuple(self.entries)

    def get_recent(self, n: int = 5) -> list[str]:
        """Get the n most recent entries."""
        return self.entries[-n:] if n < len(self.entries) else self.entries.copy()

    def flush(self) -> None:
        """Mark as flushed (persisted to storage)."""
        self.flushed = True

    def clear(self) -> None:
        """Clear all entries."""
        self.entries.clear()
        self.flushed = False
        self.metadata.clear()

    def search(self, query: str) -> list[tuple[int, str]]:
        """Search for entries containing query."""
        matches: list[tuple[int, str]] = []
        query_lower = query.lower()
        
        for i, entry in enumerate(self.entries):
            if query_lower in entry.lower():
                matches.append((i, entry))
        
        return matches

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "entries": self.entries,
            "flushed": self.flushed,
            "size": len(self.entries),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextWindow:
        """Deserialize from dictionary."""
        return cls(
            entries=list(data.get("entries", [])),
            flushed=data.get("flushed", False),
            max_size=data.get("max_size", 1000),
            metadata=dict(data.get("metadata", {})),
        )

    def get_summary(self) -> str:
        """Get human-readable summary."""
        lines = [
            f"Entries: {len(self.entries)}",
            f"Flushed: {self.flushed}",
        ]
        if self.metadata.get("compactions"):
            lines.append(f"Compactions: {self.metadata['compactions']}")
        if self.metadata.get("total_compacted"):
            lines.append(f"Total compacted: {self.metadata['total_compacted']}")
        return "\n".join(lines)
