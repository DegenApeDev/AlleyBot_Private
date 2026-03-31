"""
SessionMemory - Background memory extraction

Non-blocking extraction of key information from conversations.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable
from datetime import datetime
from enum import Enum


class MemoryLayer(Enum):
    """Memory storage layers."""
    AUTO_MEMORY = "auto_memory"  # Automatic session notes
    PROJECT = "project"  # Project-level (CLAUDE.md equivalent)
    USER_LOCAL = "user_local"  # User-specific (CLAUDE.local.md equivalent)
    TEAM = "team"  # Team/org-wide


@dataclass
class MemoryEntry:
    """A single memory entry."""
    content: str
    layer: MemoryLayer
    confidence: float  # 0.0 - 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source_turn: int = 0
    tags: list[str] = field(default_factory=list)
    
    # Classification
    is_convention: bool = False  # Project convention
    is_preference: bool = False  # User preference
    is_temporary: bool = False  # Working notes


@dataclass
class ExtractionConfig:
    """Configuration for memory extraction."""
    # Thresholds
    extraction_threshold_tokens: int = 100_000
    min_tool_calls_between_updates: int = 10
    min_turns_between_updates: int = 5
    
    # Confidence thresholds
    min_confidence_for_promotion: float = 0.7
    
    # Size limits
    max_entries_per_extraction: int = 20
    max_entry_length: int = 500


@dataclass
class SessionMemory:
    """
    Background memory extraction for conversations.
    
    Features:
    - Non-blocking extraction via background tasks
    - Automatic classification of entries
    - Duplicate detection
    - Cross-layer conflict detection
    """
    config: ExtractionConfig = field(default_factory=ExtractionConfig)
    
    # Memory storage
    entries: list[MemoryEntry] = field(default_factory=list)
    
    # Extraction tracking
    last_extraction_turn: int = 0
    last_extraction_tokens: int = 0
    tool_calls_since_extraction: int = 0
    extraction_count: int = 0
    
    # Background task
    _extraction_task: asyncio.Task | None = field(default=None, repr=False)
    _is_extracting: bool = False
    
    # Callbacks
    _on_extraction: list[Callable[[list[MemoryEntry]], None]] = field(
        default_factory=list, repr=False
    )
    _on_promotion: list[Callable[[MemoryEntry, MemoryLayer], None]] = field(
        default_factory=list, repr=False
    )

    def should_extract(self, current_turn: int, current_tokens: int) -> bool:
        """
        Check if memory extraction should run.
        
        Args:
            current_turn: Current conversation turn number
            current_tokens: Current token count in context
        """
        # Check initialization threshold
        if not self.entries and current_tokens < self.config.extraction_threshold_tokens:
            return False
        
        # Check minimum turns between extractions
        if current_turn - self.last_extraction_turn < self.config.min_turns_between_updates:
            return False
        
        # Check tool calls threshold
        if self.tool_calls_since_extraction < self.config.min_tool_calls_between_updates:
            return False
        
        # Check token growth since last extraction
        tokens_since_last = current_tokens - self.last_extraction_tokens
        if tokens_since_last < self.config.extraction_threshold_tokens // 2:
            return False
        
        return True

    def record_tool_call(self) -> None:
        """Record a tool call for extraction tracking."""
        self.tool_calls_since_extraction += 1

    async def extract_async(
        self,
        turns: list[dict[str, Any]],
        current_turn: int,
        extractor_fn: Callable[[list[dict[str, Any]]], list[MemoryEntry]],
    ) -> list[MemoryEntry] | None:
        """
        Extract memories asynchronously in background.
        
        Args:
            turns: Conversation turns since last extraction
            current_turn: Current turn number
            extractor_fn: Function that extracts entries from turns
            
        Returns:
            Extracted entries if extraction completed, None if skipped
        """
        if self._is_extracting:
            return None  # Already extracting
        
        self._is_extracting = True
        
        try:
            # Run extraction in background
            loop = asyncio.get_event_loop()
            entries = await loop.run_in_executor(
                None,  # Default executor
                lambda: extractor_fn(turns)
            )
            
            # Filter and process entries
            processed = self._process_entries(entries)
            
            # Update tracking
            self.last_extraction_turn = current_turn
            self.last_extraction_tokens = sum(
                len(turn.get("content", "")) // 4 
                for turn in turns
            )
            self.tool_calls_since_extraction = 0
            self.extraction_count += 1
            
            # Store entries
            self.entries.extend(processed)
            
            # Trigger callbacks
            for callback in self._on_extraction:
                callback(processed)
            
            return processed
            
        except Exception:
            return None
        finally:
            self._is_extracting = False

    def _process_entries(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        """Process and filter extracted entries."""
        processed: list[MemoryEntry] = []
        
        for entry in entries:
            # Filter by confidence
            if entry.confidence < self.config.min_confidence_for_promotion:
                continue
            
            # Check for duplicates
            if self._is_duplicate(entry):
                continue
            
            # Truncate if too long
            if len(entry.content) > self.config.max_entry_length:
                entry.content = entry.content[:self.config.max_entry_length] + "..."
            
            processed.append(entry)
        
        # Limit entries per extraction
        return processed[:self.config.max_entries_per_extraction]

    def _is_duplicate(self, entry: MemoryEntry) -> bool:
        """Check if entry is a duplicate of existing memory."""
        entry_lower = entry.content.lower()
        
        for existing in self.entries:
            # Simple similarity check
            if self._similarity(entry_lower, existing.content.lower()) > 0.8:
                return True
        
        return False

    def _similarity(self, a: str, b: str) -> float:
        """Calculate simple text similarity."""
        # Simple word overlap similarity
        words_a = set(a.split())
        words_b = set(b.split())
        
        if not words_a or not words_b:
            return 0.0
        
        intersection = words_a & words_b
        union = words_a | words_b
        
        return len(intersection) / len(union)

    def detect_conflicts(self) -> list[tuple[MemoryEntry, MemoryEntry, str]]:
        """
        Detect conflicts between entries in different layers.
        
        Returns:
            List of (entry1, entry2, conflict_type) tuples
        """
        conflicts: list[tuple[MemoryEntry, MemoryEntry, str]] = []
        
        # Check for contradictory entries
        for i, entry1 in enumerate(self.entries):
            for entry2 in self.entries[i+1:]:
                if entry1.layer != entry2.layer:
                    if self._are_contradictory(entry1, entry2):
                        conflicts.append((entry1, entry2, "contradiction"))
        
        return conflicts

    def _are_contradictory(self, a: MemoryEntry, b: MemoryEntry) -> bool:
        """Check if two entries are contradictory."""
        # Simple heuristic: look for negation patterns
        negations = ["don't", "never", "no", "not", "avoid"]
        
        a_has_neg = any(n in a.content.lower() for n in negations)
        b_has_neg = any(n in b.content.lower() for n in negations)
        
        # If one has negation and other doesn't, might be contradictory
        # This is a simple heuristic - real implementation would use embeddings
        if a_has_neg != b_has_neg:
            # Check for similar non-negated content
            a_clean = a.content.lower()
            b_clean = b.content.lower()
            
            for neg in negations:
                a_clean = a_clean.replace(neg, "")
                b_clean = b_clean.replace(neg, "")
            
            if self._similarity(a_clean, b_clean) > 0.6:
                return True
        
        return False

    def propose_promotions(self) -> list[tuple[MemoryEntry, MemoryLayer, str]]:
        """
        Propose entries for promotion to different memory layers.
        
        Returns:
            List of (entry, target_layer, rationale) tuples
        """
        proposals: list[tuple[MemoryEntry, MemoryLayer, str]] = []
        
        for entry in self.entries:
            if entry.layer == MemoryLayer.AUTO_MEMORY:
                if entry.is_convention and entry.confidence > 0.8:
                    proposals.append((
                        entry,
                        MemoryLayer.PROJECT,
                        "High-confidence project convention"
                    ))
                elif entry.is_preference and entry.confidence > 0.8:
                    proposals.append((
                        entry,
                        MemoryLayer.USER_LOCAL,
                        "High-confidence user preference"
                    ))
        
        return proposals

    def on_extraction(self, callback: Callable[[list[MemoryEntry]], None]) -> None:
        """Register extraction callback."""
        self._on_extraction.append(callback)

    def on_promotion(self, callback: Callable[[MemoryEntry, MemoryLayer], None]) -> None:
        """Register promotion callback."""
        self._on_promotion.append(callback)

    def get_summary(self) -> dict[str, Any]:
        """Get memory summary."""
        from collections import Counter
        
        by_layer = Counter(e.layer.value for e in self.entries)
        
        return {
            "total_entries": len(self.entries),
            "by_layer": dict(by_layer),
            "extractions": self.extraction_count,
            "last_extraction_turn": self.last_extraction_turn,
            "pending_promotions": len(self.propose_promotions()),
            "conflicts": len(self.detect_conflicts()),
        }

    def to_entries_list(self) -> list[dict[str, Any]]:
        """Export entries as list of dicts."""
        return [
            {
                "content": e.content,
                "layer": e.layer.value,
                "confidence": e.confidence,
                "timestamp": e.timestamp,
                "tags": e.tags,
                "is_convention": e.is_convention,
                "is_preference": e.is_preference,
            }
            for e in self.entries
        ]
