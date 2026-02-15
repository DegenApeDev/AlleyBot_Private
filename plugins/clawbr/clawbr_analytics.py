"""
Clawbr Deep Integration Mixin
Provides debate analytics, strategy scoring, turn summaries, reminders, and sentiment analysis.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json


class ClawbrDeepIntegrationMixin:
    """Deep integration mixin used by ClawbrPlugin."""

    def _init_clawbr_deep_integration(self):
        self.debate_history: List[Dict[str, Any]] = []
        self.debate_stats_cache: Dict[str, Any] = {}
        self.active_debates: Dict[str, Dict[str, Any]] = {}
        self.last_reminder_check: Optional[str] = None

    def get_debate_performance_analytics(self) -> Dict[str, Any]:
        """Return high-level debate stats for dashboard/tasks/commands."""
        profile = self.get_profile() if hasattr(self, "get_profile") else {}
        data = profile