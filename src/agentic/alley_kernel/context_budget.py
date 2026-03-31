"""
Enhanced ContextWindow with Auto-Compact thresholds

Smart context window management with token budgets and circuit breakers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum


class TokenThreshold(Enum):
    """Token usage threshold levels."""
    NORMAL = "normal"
    WARNING = "warning"
    ERROR = "error"
    AUTO_COMPACT = "auto_compact"
    BLOCKING = "blocking"


@dataclass
class ContextBudget:
    """
    Token budget configuration for context management.
    
    Based on Claude Code's buffer thresholds with circuit breaker protection.
    """
    context_window: int = 200_000  # Total available context
    
    # Buffer zones (from Claude Code patterns)
    AUTOCOMPACT_BUFFER: int = 13_000
    WARNING_BUFFER: int = 20_000
    ERROR_BUFFER: int = 20_000
    MANUAL_COMPACT_BUFFER: int = 3_000
    
    # Circuit breaker settings
    MAX_CONSECUTIVE_FAILURES: int = 3
    
    # Reserved tokens for output
    MAX_OUTPUT_TOKENS: int = 20_000
    
    def get_effective_window(self) -> int:
        """Get effective context window after reservations."""
        return self.context_window - self.MAX_OUTPUT_TOKENS
    
    def get_auto_compact_threshold(self) -> int:
        """Threshold where auto-compact triggers."""
        return self.get_effective_window() - self.AUTOCOMPACT_BUFFER
    
    def get_warning_threshold(self) -> int:
        """Threshold for warning level."""
        return self.get_effective_window() - self.WARNING_BUFFER
    
    def get_error_threshold(self) -> int:
        """Threshold for error level."""
        return self.get_effective_window() - self.ERROR_BUFFER
    
    def get_blocking_threshold(self) -> int:
        """Threshold where operations should block."""
        return self.get_effective_window() - self.MANUAL_COMPACT_BUFFER


@dataclass
class CompactionResult:
    """Result of a compaction operation."""
    success: bool
    original_entries: int
    compacted_entries: int
    tokens_saved: int
    summary: str


@dataclass
class EnhancedContextWindow:
    """
    Enhanced context window with auto-compact and threshold management.
    
    Features:
    - Automatic compaction at configurable thresholds
    - Circuit breaker for compaction failures
    - Token usage tracking and warnings
    - Multiple compaction strategies
    """
    entries: list[dict[str, Any]] = field(default_factory=list)
    budget: ContextBudget = field(default_factory=ContextBudget)
    
    # Token estimation function (injected dependency)
    _token_counter: Callable[[str], int] = field(
        default_factory=lambda: lambda text: len(text) // 4,  # Rough: 4 chars ~ 1 token
        repr=False
    )
    
    # State tracking
    current_tokens: int = 0
    compaction_count: int = 0
    consecutive_failures: int = 0
    flushed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Hooks
    _on_compaction: list[Callable[[CompactionResult], None]] = field(
        default_factory=list, repr=False
    )
    _on_threshold: dict[TokenThreshold, list[Callable[[int], None]]] = field(
        default_factory=dict, repr=False
    )

    def append(self, entry: str, metadata: dict[str, Any] | None = None) -> None:
        """
        Add an entry to the context window with auto-compact check.
        
        Args:
            entry: Text content to add
            metadata: Optional metadata about the entry
        """
        entry_data = {
            "content": entry,
            "metadata": metadata or {},
            "timestamp": __import__('datetime').datetime.now().isoformat(),
        }
        
        self.entries.append(entry_data)
        self.current_tokens += self._token_counter(entry)
        self.flushed = False
        
        # Check thresholds and auto-compact if needed
        self._check_thresholds()

    def _check_thresholds(self) -> None:
        """Check token thresholds and trigger appropriate actions."""
        state = self.get_threshold_state()
        
        # Trigger threshold callbacks
        if state["is_above_auto_compact_threshold"]:
            self._trigger_threshold_callbacks(TokenThreshold.AUTO_COMPACT)
            
            # Attempt auto-compact if circuit breaker allows
            if self.consecutive_failures < self.budget.MAX_CONSECUTIVE_FAILURES:
                result = self.compact()
                if not result.success:
                    self.consecutive_failures += 1
                else:
                    self.consecutive_failures = 0
        
        if state["is_above_warning_threshold"]:
            self._trigger_threshold_callbacks(TokenThreshold.WARNING)
        
        if state["is_above_error_threshold"]:
            self._trigger_threshold_callbacks(TokenThreshold.ERROR)
        
        if state["is_at_blocking_limit"]:
            self._trigger_threshold_callbacks(TokenThreshold.BLOCKING)

    def get_threshold_state(self) -> dict[str, Any]:
        """
        Get current threshold state.
        
        Returns:
            Dictionary with threshold flags and percent remaining
        """
        effective = self.budget.get_effective_window()
        
        percent_left = max(0, round(((effective - self.current_tokens) / effective) * 100))
        
        warning_threshold = self.budget.get_warning_threshold()
        error_threshold = self.budget.get_error_threshold()
        auto_compact_threshold = self.budget.get_auto_compact_threshold()
        blocking_threshold = self.budget.get_blocking_threshold()
        
        return {
            "current_tokens": self.current_tokens,
            "effective_window": effective,
            "percent_left": percent_left,
            "is_above_warning_threshold": self.current_tokens >= warning_threshold,
            "is_above_error_threshold": self.current_tokens >= error_threshold,
            "is_above_auto_compact_threshold": self.current_tokens >= auto_compact_threshold,
            "is_at_blocking_limit": self.current_tokens >= blocking_threshold,
            "compactions": self.compaction_count,
            "consecutive_failures": self.consecutive_failures,
        }

    def compact(self, strategy: str = "summary", keep_recent: int = 10) -> CompactionResult:
        """
        Compact the context window using specified strategy.
        
        Strategies:
        - "summary": Replace old entries with summary marker
        - "semantic": Group related entries
        - "extractive": Keep only most important sentences
        
        Args:
            strategy: Compaction strategy to use
            keep_recent: Number of recent entries to preserve
        """
        original_count = len(self.entries)
        
        if original_count <= keep_recent:
            return CompactionResult(
                success=True,
                original_entries=original_count,
                compacted_entries=original_count,
                tokens_saved=0,
                summary="No compaction needed",
            )
        
        # Calculate tokens before compaction
        tokens_before = self.current_tokens
        
        if strategy == "summary":
            result = self._compact_summary(keep_recent)
        elif strategy == "semantic":
            result = self._compact_semantic(keep_recent)
        else:
            result = self._compact_extractive(keep_recent)
        
        # Recalculate tokens
        self.current_tokens = sum(
            self._token_counter(e["content"]) 
            for e in self.entries
        )
        
        tokens_saved = tokens_before - self.current_tokens
        self.compaction_count += 1
        
        compaction_result = CompactionResult(
            success=result,
            original_entries=original_count,
            compacted_entries=len(self.entries),
            tokens_saved=tokens_saved,
            summary=f"Compacted from {original_count} to {len(self.entries)} entries using {strategy} strategy",
        )
        
        # Trigger callbacks
        for callback in self._on_compaction:
            callback(compaction_result)
        
        return compaction_result

    def _compact_summary(self, keep_recent: int) -> bool:
        """Compact by replacing old entries with a summary marker."""
        preserved = self.entries[-keep_recent:]
        old_count = len(self.entries) - keep_recent
        
        summary_entry = {
            "content": f"[... {old_count} earlier entries compacted ...]",
            "metadata": {"compaction_marker": True, "original_count": old_count},
            "timestamp": self.entries[0]["timestamp"] if self.entries else "",
        }
        
        self.entries = [summary_entry] + preserved
        return True

    def _compact_semantic(self, keep_recent: int) -> bool:
        """Compact by grouping semantically similar entries."""
        # For now, fall back to summary strategy
        # TODO: Implement semantic grouping with embeddings
        return self._compact_summary(keep_recent)

    def _compact_extractive(self, keep_recent: int) -> bool:
        """Compact by extracting key sentences from old entries."""
        # For now, fall back to summary strategy
        # TODO: Implement extractive summarization
        return self._compact_summary(keep_recent)

    def replay(self) -> tuple[dict[str, Any], ...]:
        """Replay all entries."""
        return tuple(self.entries)

    def get_recent(self, n: int = 5) -> list[dict[str, Any]]:
        """Get n most recent entries."""
        return self.entries[-n:] if n < len(self.entries) else self.entries.copy()

    def search(self, query: str) -> list[tuple[int, dict[str, Any]]]:
        """Search for entries containing query."""
        matches: list[tuple[int, dict[str, Any]]] = []
        query_lower = query.lower()
        
        for i, entry in enumerate(self.entries):
            if query_lower in entry["content"].lower():
                matches.append((i, entry))
        
        return matches

    def flush(self) -> None:
        """Mark as flushed (persisted)."""
        self.flushed = True

    def clear(self) -> None:
        """Clear all entries."""
        self.entries.clear()
        self.current_tokens = 0
        self.flushed = False
        self.compaction_count = 0
        self.consecutive_failures = 0

    def on_compaction(self, callback: Callable[[CompactionResult], None]) -> None:
        """Register compaction callback."""
        self._on_compaction.append(callback)

    def on_threshold(
        self, 
        threshold: TokenThreshold, 
        callback: Callable[[int], None]
    ) -> None:
        """Register threshold callback."""
        if threshold not in self._on_threshold:
            self._on_threshold[threshold] = []
        self._on_threshold[threshold].append(callback)

    def _trigger_threshold_callbacks(self, threshold: TokenThreshold) -> None:
        """Trigger callbacks for a threshold level."""
        for callback in self._on_threshold.get(threshold, []):
            try:
                callback(self.current_tokens)
            except Exception:
                pass  # Don't let callbacks break the flow

    def get_summary(self) -> str:
        """Get human-readable summary."""
        state = self.get_threshold_state()
        
        lines = [
            f"Entries: {len(self.entries)}",
            f"Current tokens: {self.current_tokens:,}",
            f"Effective window: {state['effective_window']:,}",
            f"Percent left: {state['percent_left']}%",
            f"Compactions: {self.compaction_count}",
            f"Flushed: {self.flushed}",
        ]
        
        if state["is_above_auto_compact_threshold"]:
            lines.append("⚠️ Above auto-compact threshold")
        if state["is_at_blocking_limit"]:
            lines.append("🚫 At blocking limit")
        
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "entries": self.entries,
            "current_tokens": self.current_tokens,
            "budget": {
                "context_window": self.budget.context_window,
                "autocompact_buffer": self.budget.AUTOCOMPACT_BUFFER,
            },
            "compaction_count": self.compaction_count,
            "flushed": self.flushed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnhancedContextWindow:
        """Deserialize from dictionary."""
        window = cls(
            entries=list(data.get("entries", [])),
            budget=ContextBudget(
                context_window=data.get("budget", {}).get("context_window", 200_000)
            ),
        )
        window.current_tokens = data.get("current_tokens", 0)
        window.compaction_count = data.get("compaction_count", 0)
        window.flushed = data.get("flushed", False)
        return window
