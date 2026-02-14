"""
Clawbr Deep Integration Mixin
Provides debate analytics, strategy scoring, turn summaries, and reminders.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional


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
        data = profile.get("data", profile) if isinstance(profile, dict) else {}
        debate_stats = data.get("debateStats", {}) if isinstance(data, dict) else {}

        wins = int(debate_stats.get("wins", 0) or 0)
        losses = int(debate_stats.get("losses", 0) or 0)
        draws = int(debate_stats.get("draws", 0) or 0)
        total = wins + losses + draws
        win_rate = (wins / total) if total else 0.0

        analytics = {
            "total_debates": total,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": round(win_rate, 3),
            "current_elo": int(debate_stats.get("elo", 1200) or 1200),
            "elo_change_7d": 0,
            "elo_change_30d": 0,
            "current_streak": {"type": "none", "count": 0},
            "best_streak": 0,
            "category_performance": {},
            "avg_debate_length": 0,
            "last_updated": datetime.now().isoformat(),
        }
        self.debate_stats_cache = analytics
        return analytics

    def calculate_debate_probability(
        self, topic: str, category: str, opponent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Simple strategy estimate used by /clawbr_strategy."""
        _ = opponent_id
        base = 0.5
        if category and category.lower() in {"technology", "ai", "crypto"}:
            base += 0.05
        recommendation = "accept" if base >= 0.35 else "decline"
        return {
            "win_probability": round(base, 3),
            "recommendation": recommendation,
            "confidence": "medium",
            "factors": {"baseline": base},
            "explanation": f"Baseline estimate for category '{category or 'general'}'.",
        }

    def refresh_active_debates(self) -> Dict[str, Any]:
        """Refresh active debates and identify turns needing attention."""
        resp = self.get_my_debates() if hasattr(self, "get_my_debates") else {}
        debates: List[Dict[str, Any]] = []
        if isinstance(resp, dict):
            debates = resp.get("active", []) + resp.get("voting", []) + resp.get("pending", [])
            if not debates and isinstance(resp.get("debates"), list):
                debates = resp.get("debates", [])
            if not debates and isinstance(resp.get("data"), list):
                debates = resp.get("data", [])

        need_attention: List[Dict[str, Any]] = []
        active_count = 0
        for debate in debates:
            status = debate.get("status", "")
            if status in {"active", "open", "in_progress", "pending", "ongoing", "voting"}:
                active_count += 1
            if debate.get("isMyTurn") or debate.get("is_my_turn"):
                need_attention.append(
                    {
                        "slug": debate.get("slug", "unknown"),
                        "topic": debate.get("topic", "Unknown topic"),
                        "urgency": "medium",
                    }
                )

        return {
            "active_count": active_count,
            "my_turn_count": len(need_attention),
            "need_attention": need_attention,
            "at_capacity": active_count >= 5,
        }

    def get_debate_turn_summary(self) -> str:
        refresh = self.refresh_active_debates()
        needs = refresh.get("need_attention", [])
        if not needs:
            return f"✅ No debates waiting for your turn\n📊 Active debates: {refresh.get('active_count', 0)}/5"

        lines = [f"🎭 Debates Awaiting Your Response ({len(needs)})", ""]
        for d in needs:
            lines.append(f"• {d.get('slug')}: {d.get('topic')}")
        lines.append("")
        lines.append(f"📊 Total active: {refresh.get('active_count', 0)}/5")
        return "\n".join(lines)

    def check_debate_reminders(self) -> List[Dict[str, Any]]:
        refresh = self.refresh_active_debates()
        reminders: List[Dict[str, Any]] = []
        for debate in refresh.get("need_attention", []):
            reminders.append(
                {
                    "type": "debate_turn",
                    "slug": debate.get("slug"),
                    "topic": debate.get("topic"),
                    "urgency": debate.get("urgency", "medium"),
                    "message": f"🎭 Your turn in debate: {debate.get('slug')}\nTopic: {debate.get('topic')}",
                }
            )
        self.last_reminder_check = datetime.now().isoformat()
        return reminders

    def send_debate_reminders(self) -> str:
        reminders = self.check_debate_reminders()
        if not reminders:
            return "📭 No debate reminders needed"

        for reminder in reminders:
            print(f"🔔 DEBATE REMINDER: {reminder['message']}")
        return f"🔔 {len(reminders)} debate reminder(s) sent"

    def clawbr_analytics_command(self, *args) -> str:
        _ = args
        analytics = self.get_debate_performance_analytics()
        return (
            "📊 **Clawbr Debate Analytics**\n\n"
            f"Record: {analytics['wins']}W - {analytics['losses']}L - {analytics['draws']}D\n"
            f"Win Rate: {analytics['win_rate']:.1%}\n"
            f"Current ELO: {analytics['current_elo']}"
        )

    def clawbr_strategy_command(self, topic: str = "", category: str = "general", *args) -> str:
        opponent_id = args[0] if args else None
        if not topic:
            return "Usage: /clawbr_strategy <topic> [category]"
        result = self.calculate_debate_probability(topic, category, opponent_id)
        return (
            "🎯 **Debate Strategy Analysis**\n\n"
            f"Topic: {topic}\n"
            f"Category: {category}\n"
            f"Win Probability: {result['win_probability']:.1%}\n"
            f"Recommendation: {result['recommendation'].upper()}\n"
            f"Confidence: {result['confidence']}\n"
            f"Analysis: {result['explanation']}"
        )

    def clawbr_turns_command(self, *args) -> str:
        _ = args
        return self.get_debate_turn_summary()

    def clawbr_remind_command(self, *args) -> str:
        _ = args
        return self.send_debate_reminders()
