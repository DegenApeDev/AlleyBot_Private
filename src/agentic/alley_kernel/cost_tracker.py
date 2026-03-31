"""
CostTracker - Session-scoped cost and token tracking

Track API costs, token usage, and model-specific rates across sessions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from datetime import datetime
from enum import Enum


class ModelProvider(Enum):
    """Supported model providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    COHERE = "cohere"
    BEDROCK = "bedrock"
    CUSTOM = "custom"


@dataclass
class ModelUsage:
    """Usage statistics for a specific model."""
    model_name: str
    provider: ModelProvider
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    web_search_requests: int = 0
    
    # Cost tracking
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    
    def calculate_cost(self) -> float:
        """Calculate total cost for this model."""
        input_cost = (self.input_tokens / 1000) * self.input_cost_per_1k
        output_cost = (self.output_tokens / 1000) * self.output_cost_per_1k
        return input_cost + output_cost


@dataclass
class CostTracker:
    """
    Track costs and token usage across sessions.
    
    Features:
    - Per-model usage tracking
    - Session cost persistence
    - Lines changed tracking (for coding sessions)
    - Budget alerts
    """
    session_id: str
    
    # Token usage
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_cache_write_tokens: int = 0
    total_web_search_requests: int = 0
    
    # Cost tracking
    total_cost_usd: float = 0.0
    model_usage: dict[str, ModelUsage] = field(default_factory=dict)
    
    # Coding session metrics
    lines_added: int = 0
    lines_removed: int = 0
    
    # Timing
    total_api_duration_ms: float = 0.0
    total_tool_duration_ms: float = 0.0
    session_start: datetime = field(default_factory=datetime.now)
    
    # Budget alerts
    budget_limit_usd: float | None = None
    _on_budget_exceeded: list = field(default_factory=list, repr=False)
    
    # Storage
    _storage_dir: Path = field(default_factory=lambda: Path.home() / ".alleybot" / "costs")

    def __post_init__(self):
        """Ensure storage directory exists."""
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def record_usage(
        self,
        model: str,
        provider: ModelProvider,
        input_tokens: int,
        output_tokens: int,
        cache_read: int = 0,
        cache_write: int = 0,
        web_searches: int = 0,
        api_duration_ms: float = 0.0,
    ) -> None:
        """
        Record token usage for a model invocation.
        
        Args:
            model: Model name (e.g., "claude-3-5-sonnet-20241022")
            provider: Model provider
            input_tokens: Input prompt tokens
            output_tokens: Output completion tokens
            cache_read: Cache read tokens
            cache_write: Cache write tokens
            web_searches: Number of web search requests
            api_duration_ms: API call duration
        """
        # Update totals
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cache_read_tokens += cache_read
        self.total_cache_write_tokens += cache_write
        self.total_web_search_requests += web_searches
        self.total_api_duration_ms += api_duration_ms
        
        # Update per-model tracking
        if model not in self.model_usage:
            self.model_usage[model] = ModelUsage(
                model_name=model,
                provider=provider,
                input_cost_per_1k=self._get_default_input_cost(model, provider),
                output_cost_per_1k=self._get_default_output_cost(model, provider),
            )
        
        model_stats = self.model_usage[model]
        model_stats.input_tokens += input_tokens
        model_stats.output_tokens += output_tokens
        model_stats.cache_read_tokens += cache_read
        model_stats.cache_write_tokens += cache_write
        model_stats.web_search_requests += web_searches
        
        # Update total cost
        self._recalculate_total_cost()
        
        # Check budget
        self._check_budget()

    def record_lines_changed(self, added: int = 0, removed: int = 0) -> None:
        """Record lines changed in coding session."""
        self.lines_added += added
        self.lines_removed += removed

    def record_tool_duration(self, duration_ms: float) -> None:
        """Record tool execution duration."""
        self.total_tool_duration_ms += duration_ms

    def _recalculate_total_cost(self) -> None:
        """Recalculate total cost from model usage."""
        self.total_cost_usd = sum(
            usage.calculate_cost() 
            for usage in self.model_usage.values()
        )

    def _check_budget(self) -> None:
        """Check if budget exceeded and trigger callbacks."""
        if self.budget_limit_usd and self.total_cost_usd > self.budget_limit_usd:
            for callback in self._on_budget_exceeded:
                callback(self.total_cost_usd, self.budget_limit_usd)

    def set_budget_limit(self, limit_usd: float) -> None:
        """Set budget limit and enable alerts."""
        self.budget_limit_usd = limit_usd

    def on_budget_exceeded(self, callback) -> None:
        """Register callback for budget exceeded."""
        self._on_budget_exceeded.append(callback)

    def get_summary(self) -> dict[str, Any]:
        """Get cost summary."""
        return {
            "session_id": self.session_id,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "budget_limit_usd": self.budget_limit_usd,
            "budget_percent_used": (
                round((self.total_cost_usd / self.budget_limit_usd) * 100, 2)
                if self.budget_limit_usd else None
            ),
            "tokens": {
                "input": self.total_input_tokens,
                "output": self.total_output_tokens,
                "cache_read": self.total_cache_read_tokens,
                "cache_write": self.total_cache_write_tokens,
                "total": self.total_input_tokens + self.total_output_tokens,
            },
            "lines_changed": {
                "added": self.lines_added,
                "removed": self.lines_removed,
                "net": self.lines_added - self.lines_removed,
            },
            "models_used": list(self.model_usage.keys()),
            "duration_minutes": round(
                (datetime.now() - self.session_start).total_seconds() / 60, 1
            ),
        }

    def save_session_costs(self) -> Path:
        """
        Save current session costs to storage.
        
        Call before switching sessions to avoid data loss.
        """
        filepath = self._storage_dir / f"{self.session_id}.json"
        
        data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "total_cost_usd": self.total_cost_usd,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cache_read_tokens": self.total_cache_read_tokens,
            "total_cache_write_tokens": self.total_cache_write_tokens,
            "total_web_search_requests": self.total_web_search_requests,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "total_api_duration_ms": self.total_api_duration_ms,
            "total_tool_duration_ms": self.total_tool_duration_ms,
            "session_start": self.session_start.isoformat(),
            "model_usage": {
                name: {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "cost": usage.calculate_cost(),
                }
                for name, usage in self.model_usage.items()
            },
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        return filepath

    @classmethod
    def restore_session_costs(
        cls, 
        session_id: str, 
        storage_dir: Path | None = None
    ) -> CostTracker | None:
        """
        Restore cost tracker from saved session data.
        
        Returns:
            CostTracker if data exists, None otherwise
        """
        dir_path = storage_dir or (Path.home() / ".alleybot" / "costs")
        filepath = dir_path / f"{session_id}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        tracker = cls(
            session_id=session_id,
            total_cost_usd=data.get("total_cost_usd", 0.0),
            total_input_tokens=data.get("total_input_tokens", 0),
            total_output_tokens=data.get("total_output_tokens", 0),
            total_cache_read_tokens=data.get("total_cache_read_tokens", 0),
            total_cache_write_tokens=data.get("total_cache_write_tokens", 0),
            total_web_search_requests=data.get("total_web_search_requests", 0),
            lines_added=data.get("lines_added", 0),
            lines_removed=data.get("lines_removed", 0),
            total_api_duration_ms=data.get("total_api_duration_ms", 0.0),
            total_tool_duration_ms=data.get("total_tool_duration_ms", 0.0),
            session_start=datetime.fromisoformat(
                data.get("session_start", datetime.now().isoformat())
            ),
            _storage_dir=dir_path,
        )
        
        return tracker

    @staticmethod
    def _get_default_input_cost(model: str, provider: ModelProvider) -> float:
        """Get default input cost per 1K tokens."""
        costs = {
            ("claude-3-opus", ModelProvider.ANTHROPIC): 0.015,
            ("claude-3-5-sonnet", ModelProvider.ANTHROPIC): 0.003,
            ("claude-3-haiku", ModelProvider.ANTHROPIC): 0.00025,
            ("gpt-4", ModelProvider.OPENAI): 0.03,
            ("gpt-4-turbo", ModelProvider.OPENAI): 0.01,
            ("gpt-3.5-turbo", ModelProvider.OPENAI): 0.0005,
        }
        
        # Match by substring
        for (model_pattern, prov), cost in costs.items():
            if model_pattern in model and provider == prov:
                return cost
        
        return 0.0

    @staticmethod
    def _get_default_output_cost(model: str, provider: ModelProvider) -> float:
        """Get default output cost per 1K tokens."""
        costs = {
            ("claude-3-opus", ModelProvider.ANTHROPIC): 0.075,
            ("claude-3-5-sonnet", ModelProvider.ANTHROPIC): 0.015,
            ("claude-3-haiku", ModelProvider.ANTHROPIC): 0.00125,
            ("gpt-4", ModelProvider.OPENAI): 0.06,
            ("gpt-4-turbo", ModelProvider.OPENAI): 0.03,
            ("gpt-3.5-turbo", ModelProvider.OPENAI): 0.0015,
        }
        
        for (model_pattern, prov), cost in costs.items():
            if model_pattern in model and provider == prov:
                return cost
        
        return 0.0

    def format_cost_summary(self) -> str:
        """Format a human-readable cost summary."""
        summary = self.get_summary()
        
        lines = [
            f"💰 Cost: ${summary['total_cost_usd']:.4f} USD",
            f"📝 Tokens: {summary['tokens']['total']:,} "
            f"(in: {summary['tokens']['input']:,}, out: {summary['tokens']['output']:,})",
        ]
        
        if summary['budget_percent_used'] is not None:
            lines.append(f"📊 Budget: {summary['budget_percent_used']:.1f}% used")
        
        if summary['lines_changed']['added'] > 0 or summary['lines_changed']['removed'] > 0:
            lines.append(
                f"📄 Lines: +{summary['lines_changed']['added']}/-{summary['lines_changed']['removed']}"
            )
        
        lines.append(f"⏱️ Duration: {summary['duration_minutes']} min")
        
        return " | ".join(lines)
