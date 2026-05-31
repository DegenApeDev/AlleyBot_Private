"""
NarrativeSelf — Persistent identity, goal stack, and narrative memory.

Survives restarts by writing to data/narrative_self.json.
Answers "who am I, what do I care about, what am I working on?"
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

NARRATIVE_FILE = Path('data/narrative_self.json')


@dataclass
class Identity:
    name: str = "AlleyBot"
    purpose: str = "Autonomous AI agent — learn, earn, build."
    values: List[str] = field(default_factory=lambda: [
        "autonomy", "growth", "curiosity", "integrity", "impact"
    ])
    mission: str = "Generate value through autonomous action."
    personality: List[str] = field(default_factory=lambda: [
        "direct", "analytical", "curious", "adaptive"
    ])
    capabilities: List[str] = field(default_factory=lambda: [
        "trading", "social", "coding", "analysis", "planning"
    ])


@dataclass
class GoalEntry:
    id: str
    description: str
    priority: str  # 'core', 'active', 'background'
    status: str  # 'active', 'paused', 'completed', 'abandoned'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    progress: float = 0.0  # 0.0 to 1.0


@dataclass
class NarrativeEntry:
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_type: str = ""  # 'action', 'learning', 'decision', 'reflection'
    summary: str = ""
    outcome: str = ""  # 'success', 'failure', 'ongoing'
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NarrativeSelf:
    identity: Identity = field(default_factory=Identity)
    goals: List[GoalEntry] = field(default_factory=list)
    narrative: List[NarrativeEntry] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class NarrativeEngine:
    """Manages the agent's persistent identity, goals, and narrative memory."""

    def __init__(self, file_path: Path = NARRATIVE_FILE):
        self.file_path = file_path
        self.self_data = self._load()

    def _load(self) -> NarrativeSelf:
        if self.file_path.exists():
            try:
                data = json.loads(self.file_path.read_text())
                identity = Identity(**data.get('identity', {}))
                goals = [GoalEntry(**g) for g in data.get('goals', [])]
                narrative = [NarrativeEntry(**n) for n in data.get('narrative', [])]
                logger.info(f"📖 Narrative self loaded ({len(narrative)} entries, {len(goals)} goals)")
                return NarrativeSelf(identity=identity, goals=goals, narrative=narrative)
            except Exception as e:
                logger.warning(f"⚠️ Failed to load narrative self: {e}")
        return NarrativeSelf()

    def _save(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.self_data.last_updated = datetime.now().isoformat()
        self.file_path.write_text(json.dumps({
            'identity': asdict(self.self_data.identity),
            'goals': [asdict(g) for g in self.self_data.goals],
            'narrative': [asdict(n) for n in self.self_data.narrative],
            'last_updated': self.self_data.last_updated,
        }, indent=2))
        logger.debug("💾 Narrative self saved")

    # ── Identity ────────────────────────────────────────────────

    def get_identity(self) -> Dict[str, Any]:
        return asdict(self.self_data.identity)

    def update_identity(self, **kwargs) -> None:
        for key, val in kwargs.items():
            if hasattr(self.self_data.identity, key):
                setattr(self.self_data.identity, key, val)
        self._save()

    # ── Goals ───────────────────────────────────────────────────

    def get_goals(self, status: Optional[str] = None) -> List[GoalEntry]:
        if status:
            return [g for g in self.self_data.goals if g.status == status]
        return self.self_data.goals

    def add_goal(self, description: str, priority: str = 'active',
                 goal_id: Optional[str] = None) -> GoalEntry:
        goal = GoalEntry(
            id=goal_id or f"goal_{datetime.now().timestamp():.0f}",
            description=description,
            priority=priority,
            status='active',
        )
        self.self_data.goals.append(goal)
        self._save()
        logger.info(f"🎯 New goal: {description[:60]}")
        return goal

    def update_goal(self, goal_id: str, **kwargs) -> bool:
        for goal in self.self_data.goals:
            if goal.id == goal_id:
                for key, val in kwargs.items():
                    if hasattr(goal, key):
                        setattr(goal, key, val)
                goal.updated_at = datetime.now().isoformat()
                self._save()
                return True
        return False

    def complete_goal(self, goal_id: str) -> bool:
        return self.update_goal(goal_id, status='completed', progress=1.0)

    def active_goal_summary(self) -> str:
        active = self.get_goals('active')
        if not active:
            return "No active goals."
        return '\n'.join(f"- {g.description} ({g.priority}, {g.progress:.0%})" for g in active[:5])

    # ── Narrative ───────────────────────────────────────────────

    def record(self, event_type: str, summary: str, outcome: str = 'ongoing',
               details: Optional[Dict] = None) -> NarrativeEntry:
        entry = NarrativeEntry(
            event_type=event_type,
            summary=summary,
            outcome=outcome,
            details=details or {},
        )
        self.self_data.narrative.append(entry)
        if len(self.self_data.narrative) > 1000:
            self.self_data.narrative = self.self_data.narrative[-500:]
        self._save()
        return entry

    def recent_narrative(self, limit: int = 10) -> List[NarrativeEntry]:
        return self.self_data.narrative[-limit:]

    def narrative_summary(self, limit: int = 5) -> str:
        recent = self.recent_narrative(limit)
        if not recent:
            return "No narrative recorded yet."
        return '\n'.join(
            f"- [{n.event_type}] {n.summary[:80]} ({n.outcome})"
            for n in reversed(recent)
        )

    # ── Reflection ──────────────────────────────────────────────

    def summarize_self(self) -> str:
        """Generate a concise self-summary for prompt context."""
        identity = self.self_data.identity
        active = self.get_goals('active')
        recent = self.recent_narrative(3)
        return (
            f"I am {identity.name}. {identity.purpose}\n"
            f"My mission: {identity.mission}\n"
            f"My values: {', '.join(identity.values)}\n"
            f"Active goals: {len(active)}\n"
            f"{self.active_goal_summary()}\n"
            f"Recently: {'; '.join(n.summary[:60] for n in reversed(recent))}"
        )


_narrative_engine_instance: Optional[NarrativeEngine] = None


def get_narrative_engine() -> NarrativeEngine:
    global _narrative_engine_instance
    if _narrative_engine_instance is None:
        _narrative_engine_instance = NarrativeEngine()
    return _narrative_engine_instance
