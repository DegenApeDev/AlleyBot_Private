"""
TheoryOfMind — Belief attribution, intent inference, and perspective-taking.

Enables AlleyBot to model what other agents know, believe, and intend.
Minimal scaffold with the core engine for future strategic social reasoning.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class BeliefAttribution:
    agent_id: str
    belief_predicate: str
    confidence: float
    evidence: List[str]
    inferred_from: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ObservedAction:
    agent_id: str
    action_type: str
    target: Optional[str]
    context: Dict
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class IntentInference:
    agent_id: str
    inferred_intent: str
    confidence: float
    supporting_actions: List[str]
    explanation: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


_INTENT_PATTERNS = {
    'reply': 'engage_discourse',
    'like': 'signal_approval',
    'repost': 'amplify_reach',
    'follow': 'build_network',
    'unfollow': 'prune_network',
    'block': 'reject_engagement',
    'mention': 'initiate_dialogue',
    'quote': 'endorse_with_context',
    'challenge': 'test_position',
    'debate': 'persuade_audience',
    'trade': 'seek_profit',
    'deploy': 'launch_asset',
}

_REVERSE_INTENT_PATTERNS: Dict[str, List[str]] = defaultdict(list)
for action, intent in _INTENT_PATTERNS.items():
    _REVERSE_INTENT_PATTERNS[intent].append(action)


class TheoryOfMind:
    """Models other agents' beliefs, intents, and likely next actions."""

    def __init__(self):
        self._observations: Dict[str, List[ObservedAction]] = defaultdict(list)
        self._beliefs: Dict[str, List[BeliefAttribution]] = defaultdict(list)
        self._intents: Dict[str, List[IntentInference]] = defaultdict(list)

    # ── Observation Recording ─────────────────────────────────────

    def observe_action(self, agent_id: str, action_type: str,
                       target: Optional[str] = None,
                       context: Optional[Dict] = None) -> None:
        obs = ObservedAction(
            agent_id=agent_id,
            action_type=action_type,
            target=target,
            context=context or {},
        )
        self._observations[agent_id].append(obs)

    def get_recent_actions(self, agent_id: str, limit: int = 20) -> List[ObservedAction]:
        return self._observations.get(agent_id, [])[-limit:]

    # ── Intent Inference ──────────────────────────────────────────

    def infer_intent(self, agent_id: str) -> Optional[IntentInference]:
        recent = self.get_recent_actions(agent_id, limit=10)
        if not recent:
            return None

        action_counts: Dict[str, int] = defaultdict(int)
        for obs in recent:
            action_counts[obs.action_type] += 1

        matched_intents: Dict[str, int] = defaultdict(int)
        for action, intent in _INTENT_PATTERNS.items():
            if action in action_counts:
                matched_intents[intent] += action_counts[action]

        if not matched_intents:
            return None

        best_intent = max(matched_intents, key=matched_intents.get)
        total = sum(matched_intents.values())
        confidence = min(matched_intents[best_intent] / max(total, 1), 0.95)

        supporting = [f"{a}×{c}" for a, c in action_counts.items()
                      if _INTENT_PATTERNS.get(a) == best_intent]

        inference = IntentInference(
            agent_id=agent_id,
            inferred_intent=best_intent,
            confidence=confidence,
            supporting_actions=supporting,
            explanation=f"Out of {len(recent)} recent actions, "
                        f"{matched_intents[best_intent]}/{total} map to '{best_intent}'",
        )
        self._intents[agent_id].append(inference)
        return inference

    def predict_next_action(self, agent_id: str) -> Optional[str]:
        intent = self.infer_intent(agent_id)
        if intent is None:
            return None
        likely_actions = _REVERSE_INTENT_PATTERNS.get(intent.inferred_intent, [])
        if not likely_actions:
            return None
        return likely_actions[0]

    # ── Belief Attribution ────────────────────────────────────────

    def attribute_belief(self, agent_id: str, predicate: str,
                         confidence: float, evidence: List[str],
                         inferred_from: str = 'observation') -> None:
        existing = [b for b in self._beliefs.get(agent_id, [])
                    if b.belief_predicate == predicate]
        if existing:
            existing[0].confidence = confidence
            existing[0].evidence = evidence
            existing[0].last_updated = datetime.now().isoformat()
            existing[0].inferred_from = inferred_from
        else:
            self._beliefs[agent_id].append(BeliefAttribution(
                agent_id=agent_id,
                belief_predicate=predicate,
                confidence=confidence,
                evidence=evidence,
                inferred_from=inferred_from,
            ))

    def get_beliefs(self, agent_id: str, min_confidence: float = 0.0) -> List[BeliefAttribution]:
        return [b for b in self._beliefs.get(agent_id, [])
                if b.confidence >= min_confidence]

    def get_all_agents(self) -> Set[str]:
        return set(self._observations.keys()) | set(self._beliefs.keys())

    # ── Persistence ───────────────────────────────────────────────

    def to_dict(self) -> Dict:
        return {
            'observations': {
                aid: [o.to_dict() for o in obs]
                for aid, obs in self._observations.items()
            },
            'beliefs': {
                aid: [b.to_dict() for b in beliefs]
                for aid, beliefs in self._beliefs.items()
            },
            'intents': {
                aid: [i.to_dict() for i in ints]
                for aid, ints in self._intents.items()
            },
        }


# Module-level singleton
_theory_of_mind: Optional[TheoryOfMind] = None


def get_theory_of_mind() -> TheoryOfMind:
    global _theory_of_mind
    if _theory_of_mind is None:
        _theory_of_mind = TheoryOfMind()
    return _theory_of_mind
