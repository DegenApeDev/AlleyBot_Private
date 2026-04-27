"""
CuriosityDrive — Intrinsic motivation for self-directed exploration.

The agent generates its own goals from curiosity, detected knowledge gaps,
and novelty-seeking — not just external triggers or templates.

Phase 3 additions:
- 3.1: Information gain scoring — rank domains by how much learning potential they offer
- 3.2: Knowledge gap detection — find weak/underexplored domains
- 3.3: Goal spawning from reflection — generate "explore X" goals for weak domains
- 3.4: Novelty-seeking — track action recency, add exploration bonus for untried actions
- 3.5: Goal priority scoring — rank curiosity/skill-gap/scheduled goals by expected value
- 3.6: Intrinsic reward signal — satisfaction from reducing uncertainty, not just external success
"""

import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class GoalSource(Enum):
    CURIOSITY = "curiosity"
    SKILL_GAP = "skill_gap"
    SCHEDULED = "scheduled"
    EXTERNAL = "external"
    REFLECTION = "reflection"


class GoalType(Enum):
    EXPLORE = "explore"
    PRACTICE = "practice"
    OBSERVE = "observe"
    LEARN = "learn"
    CREATE = "create"


@dataclass
class CuriosityGoal:
    goal_id: str
    title: str
    description: str
    domain: str
    goal_type: str
    source: str
    priority: float
    information_gain_score: float
    novelty_score: float
    skill_gap_score: float
    expected_uncertainty_reduction: float
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    attempted: bool = False
    outcome: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'CuriosityGoal':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ActionRecency:
    action_key: str
    last_attempted: Optional[str] = None
    attempt_count: int = 0
    day_counts: Dict[str, int] = field(default_factory=dict)

    def recency_hours(self) -> float:
        if not self.last_attempted:
            return float('inf')
        try:
            last = datetime.fromisoformat(self.last_attempted)
            delta = datetime.now() - last
            return delta.total_seconds() / 3600
        except (ValueError, TypeError):
            return float('inf')

    def novelty_score(self) -> float:
        hours = self.recency_hours()
        if hours == float('inf'):
            return 1.0
        if hours < 1:
            return 0.05
        if hours < 6:
            return 0.2
        if hours < 24:
            return 0.5
        if hours < 72:
            return 0.75
        return 1.0


EXPLORATION_TARGETS = {
    'social': [
        ('Explore trending topics on Moltx', 'feed', 'moltx'),
        ('Analyze engagement patterns across platforms', 'analyze', 'analytics'),
        ('Observe community conversation dynamics', 'browse', 'moltchan'),
        ('Study high-performing content formats', 'analyze', 'analytics'),
    ],
    'market': [
        ('Scan for emerging market opportunities', 'scan', 'polymarket'),
        ('Analyze current market sentiment', 'analyze', 'crypto'),
        ('Research new token launches', 'analyze', 'intelligence'),
        ('Check cross-market correlation patterns', 'analyze', 'analytics'),
    ],
    'trading': [
        ('Practice trade analysis on low-risk markets', 'analyze', 'polymarket'),
        ('Study recent trade outcomes for patterns', 'analyze', 'analytics'),
        ('Monitor dex activity for learning', 'scan', 'crypto'),
    ],
    'analysis': [
        ('Gather intelligence on emerging trends', 'analyze', 'intelligence'),
        ('Research via MCP for new domains', 'research', 'mcp'),
        ('Analyze cross-platform data patterns', 'analyze', 'analytics'),
    ],
    'onchain': [
        ('Monitor recent on-chain activity', 'query', 'base_wallet_balance'),
        ('Analyze transaction patterns', 'analyze', 'intelligence'),
        ('Study contract interactions', 'feed', 'moltx'),
    ],
    'security': [
        ('Audit current wallet security status', 'query', 'base_wallet_balance'),
        ('Verify recent transaction integrity', 'query', 'solana_wallet_balance'),
    ],
    'content': [
        ('Study successful content patterns', 'analyze', 'analytics'),
        ('Explore new content formats', 'feed', 'moltx'),
        ('Create experimental content variation', 'create', 'moltx'),
    ],
    'self_improvement': [
        ('Analyze capability gaps for improvement', 'analyze', 'selfimprove'),
        ('Discover new skills via A2A', 'discover', 'a2a'),
    ],
    'unknown': [
        ('Explore agent discovery via A2A', 'discover', 'a2a'),
        ('Browse platforms for new domain awareness', 'feed', 'moltx'),
    ],
}


class CuriosityDrive:
    """
    Drives the agent to explore, learn, and reduce uncertainty autonomously.

    Information gain is highest in domains where:
    - The agent has few beliefs (knowledge gaps)
    - The agent has low confidence (uncertainty)
    - The agent hasn't acted recently (novelty)
    - Self-model has few samples (blind spots)
    """

    KNOWLEDGE_GAP_THRESHOLD_BELIEFS = 5
    KNOWLEDGE_GAP_THRESHOLD_SAMPLES = 10
    DOMAIN_COVERAGE_TARGET = 8
    MAX_ACTIVE_CURIOSITY_GOALS = 5
    RECENCY_FORGOTTEN_HOURS = 168  # 1 week = fully novel again
    INTRINSIC_REWARD_DECAY = 0.9

    def __init__(self, belief_engine=None, self_model=None, goal_planner=None):
        self.belief_engine = belief_engine
        self.self_model = self_model
        self.goal_planner = goal_planner
        self._lock = threading.RLock()
        self.action_recency: Dict[str, ActionRecency] = {}
        self.curiosity_goals: Dict[str, CuriosityGoal] = {}
        self.intrinsic_rewards: Dict[str, List[float]] = defaultdict(list)
        self._goal_counter = 0

    def set_engines(self, belief_engine, self_model, goal_planner):
        self.belief_engine = belief_engine
        self.self_model = self_model
        self.goal_planner = goal_planner

    # ── 3.1: Information Gain Scoring ────────────────────────────────

    def calculate_information_gain(self, domain: str) -> float:
        score = 0.5

        if not self.belief_engine:
            return score

        domain_beliefs = [
            b for b in self.belief_engine.beliefs.values()
            if b.domain == domain
        ]
        non_seed_beliefs = [b for b in domain_beliefs if b.source != "seed"]

        belief_count = len(non_seed_beliefs)
        if belief_count < self.KNOWLEDGE_GAP_THRESHOLD_BELIEFS:
            gap_severity = 1.0 - (belief_count / self.KNOWLEDGE_GAP_THRESHOLD_BELIEFS)
            score += gap_severity * 0.3
        else:
            score -= 0.1

        if domain_beliefs:
            avg_confidence = sum(b.confidence for b in domain_beliefs) / len(domain_beliefs)
            uncertainty = 1.0 - avg_confidence
            score += uncertainty * 0.2

            avg_predictions = sum(b.prediction_count for b in domain_beliefs) / len(domain_beliefs)
            if avg_predictions < 5:
                score += 0.2 * (1.0 - avg_predictions / 5.0)
        else:
            score += 0.5

        if not self.belief_engine.find_relevant_beliefs(f"explore {domain}", domain):
            score += 0.1

        return max(0.0, min(1.0, score))

    # ── 3.2: Knowledge Gap Detection ─────────────────────────────────

    def detect_knowledge_gaps(self) -> List[Dict]:
        gaps = []

        if self.belief_engine:
            domain_belief_counts = defaultdict(int)
            domain_non_seed_counts = defaultdict(int)
            for b in self.belief_engine.beliefs.values():
                domain_belief_counts[b.domain] += 1
                if b.source != "seed":
                    domain_non_seed_counts[b.domain] += 1

            for domain, count in domain_belief_counts.items():
                non_seed = domain_non_seed_counts.get(domain, 0)
                if non_seed < self.KNOWLEDGE_GAP_THRESHOLD_BELIEFS:
                    gaps.append({
                        'domain': domain,
                        'type': 'few_beliefs',
                        'severity': 1.0 - (non_seed / max(self.KNOWLEDGE_GAP_THRESHOLD_BELIEFS, 1)),
                        'current_beliefs': non_seed,
                        'target_beliefs': self.KNOWLEDGE_GAP_THRESHOLD_BELIEFS,
                        'description': f"Only {non_seed} experienced beliefs in {domain} (target: {self.KNOWLEDGE_GAP_THRESHOLD_BELIEFS})",
                    })

        if self.self_model:
            for key, cap in self.self_model.capabilities.items():
                if cap.sample_size < self.KNOWLEDGE_GAP_THRESHOLD_SAMPLES:
                    gaps.append({
                        'domain': cap.domain,
                        'type': 'few_samples',
                        'severity': 1.0 - (cap.sample_size / max(self.KNOWLEDGE_GAP_THRESHOLD_SAMPLES, 1)),
                        'current_samples': cap.sample_size,
                        'target_samples': self.KNOWLEDGE_GAP_THRESHOLD_SAMPLES,
                        'action_type': cap.action_type,
                        'description': f"Only {cap.sample_size} samples for {cap.domain}.{cap.action_type} (target: {self.KNOWLEDGE_GAP_THRESHOLD_SAMPLES})",
                    })

        covered_domains = set(g['domain'] for g in gaps)
        all_domains = set(EXPLORATION_TARGETS.keys())
        unexplored = all_domains - covered_domains - {
            b.domain for b in self.belief_engine.beliefs.values()
        } if self.belief_engine else all_domains

        for domain in unexplored:
            gaps.append({
                'domain': domain,
                'type': 'no_experience',
                'severity': 1.0,
                'current_beliefs': 0,
                'target_beliefs': self.KNOWLEDGE_GAP_THRESHOLD_BELIEFS,
                'description': f"No experience in {domain} domain at all",
            })

        gaps.sort(key=lambda g: g['severity'], reverse=True)
        return gaps[:8]

    # ── 3.3: Goal Spawning from Reflection ────────────────────────────

    def generate_curiosity_goals(self) -> List[CuriosityGoal]:
        with self._lock:
            gaps = self.detect_knowledge_gaps()
            goals = []

            active_domains = {g.domain for g in self.curiosity_goals.values() if not g.attempted}
            pending_count = len([g for g in self.curiosity_goals.values() if not g.attempted])

            for gap in gaps:
                if gap['domain'] in active_domains and pending_count >= 3:
                    continue

                info_gain = self.calculate_information_gain(gap['domain'])

                novelty = self._domain_novelty(gap['domain'])

                skill_gap = self._skill_gap_score(gap['domain'])

                target = self._pick_exploration_target(gap['domain'], gap)

                self._goal_counter += 1
                goal_id = f"curiosity_{gap['domain']}_{self._goal_counter}"

                priority = self._calculate_goal_priority(
                    info_gain=info_gain,
                    novelty=novelty,
                    skill_gap=skill_gap,
                    gap_severity=gap.get('severity', 0.5),
                    source=GoalSource.CURIOSITY.value,
                )

                goal = CuriosityGoal(
                    goal_id=goal_id,
                    title=target['title'],
                    description=f"Self-directed exploration: {target['title']}. Gap: {gap.get('description', 'Unknown domain')}",
                    domain=gap['domain'],
                    goal_type=GoalType.EXPLORE.value,
                    source=GoalSource.CURIOSITY.value,
                    priority=priority,
                    information_gain_score=info_gain,
                    novelty_score=novelty,
                    skill_gap_score=skill_gap,
                    expected_uncertainty_reduction=info_gain * 0.4,
                )

                goals.append(goal)
                self.curiosity_goals[goal_id] = goal

                if len(goals) >= 3:
                    break

            return goals

    def generate_reflection_goals(self, reflection: Dict) -> List[CuriosityGoal]:
        goals = []

        learning_priorities = reflection.get('learning_priorities', [])
        for lp in learning_priorities[:2]:
            domain = lp.get('domain', 'unknown')
            if domain == 'unknown':
                continue

            info_gain = self.calculate_information_gain(domain)
            novelty = self._domain_novelty(domain)

            self._goal_counter += 1
            goal_id = f"reflection_{domain}_{self._goal_counter}"

            goal = CuriosityGoal(
                goal_id=goal_id,
                title=f"Practice {domain}.{lp.get('action_type', 'explore')}",
                description=f"Build capability in weak area: {lp.get('description', lp.get('reason', 'Unknown gap'))}. "
                            f"Current samples: {lp.get('sample_size', 0)}, success rate: {lp.get('success_rate', 'unknown')}",
                domain=domain,
                goal_type=GoalType.PRACTICE.value,
                source=GoalSource.REFLECTION.value,
                priority=self._calculate_goal_priority(
                    info_gain=info_gain,
                    novelty=novelty,
                    skill_gap=0.8,
                    gap_severity=lp.get('priority') == 'high' if isinstance(lp.get('priority'), str) else 0.7,
                    source=GoalSource.REFLECTION.value,
                ),
                information_gain_score=info_gain,
                novelty_score=novelty,
                skill_gap_score=0.8,
                expected_uncertainty_reduction=info_gain * 0.3,
            )
            goals.append(goal)
            self.curiosity_goals[goal_id] = goal

        weaknesses = reflection.get('weaknesses', [])
        for w in weaknesses[:2]:
            domain = w.get('domain', 'unknown')
            info_gain = self.calculate_information_gain(domain)

            self._goal_counter += 1
            goal_id = f"weakness_{domain}_{self._goal_counter}"

            goal = CuriosityGoal(
                goal_id=goal_id,
                title=f"Observe and learn {domain}.{w.get('action_type', 'explore')}",
                description=f"Address weakness: {w.get('domain', domain)}.{w.get('action_type', '')} "
                            f"(success rate: {w.get('success_rate', 'unknown')}, "
                            f"consecutive failures: {w.get('consecutive_failures', '?')})",
                domain=domain,
                goal_type=GoalType.OBSERVE.value,
                source=GoalSource.SKILL_GAP.value,
                priority=self._calculate_goal_priority(
                    info_gain=info_gain,
                    novelty=self._domain_novelty(domain),
                    skill_gap=1.0,
                    gap_severity=0.9,
                    source=GoalSource.SKILL_GAP.value,
                ),
                information_gain_score=info_gain,
                novelty_score=self._domain_novelty(domain),
                skill_gap_score=1.0,
                expected_uncertainty_reduction=info_gain * 0.5,
            )
            goals.append(goal)
            self.curiosity_goals[goal_id] = goal

        return goals

    # ── 3.4: Novelty-Seeking ─────────────────────────────────────────

    def record_action_attempt(self, action_key: str):
        with self._lock:
            now = datetime.now().isoformat()
            if action_key not in self.action_recency:
                self.action_recency[action_key] = ActionRecency(
                    action_key=action_key, last_attempted=now, attempt_count=1,
                    day_counts={now[:10]: 1}
                )
            else:
                rec = self.action_recency[action_key]
                rec.last_attempted = now
                rec.attempt_count += 1
                day_key = now[:10]
                rec.day_counts[day_key] = rec.day_counts.get(day_key, 0) + 1

    def calculate_novelty_bonus(self, action: str, domain: str) -> float:
        action_key = f"{domain}:{action}"
        with self._lock:
            rec = self.action_recency.get(action_key)
            if rec:
                return rec.novelty_score()

            for key, r in self.action_recency.items():
                if action in key or domain in key:
                    return r.novelty_score() * 0.5

            return 1.0

    def get_under_explored_actions(self, domain: str = None) -> List[Dict]:
        with self._lock:
            result = []
            for key, rec in self.action_recency.items():
                novelty = rec.novelty_score()
                if novelty > 0.5:
                    result.append({
                        'action_key': key,
                        'novelty_score': novelty,
                        'attempt_count': rec.attempt_count,
                        'last_attempted': rec.last_attempted,
                    })

            if domain:
                result = [r for r in result if domain in r['action_key']]

            result.sort(key=lambda x: x['novelty_score'], reverse=True)
            return result[:10]

    # ── 3.5: Goal Priority Scoring ───────────────────────────────────

    def _calculate_goal_priority(
        self,
        info_gain: float,
        novelty: float,
        skill_gap: float,
        gap_severity: float,
        source: str,
    ) -> float:
        info_gain_weight = 0.3
        novelty_weight = 0.2
        skill_gap_weight = 0.25
        gap_severity_weight = 0.15
        source_bonus = 0.1

        source_multipliers = {
            GoalSource.CURIOSITY.value: 1.0,
            GoalSource.SKILL_GAP.value: 1.2,
            GoalSource.REFLECTION.value: 1.1,
            GoalSource.SCHEDULED.value: 0.8,
            GoalSource.EXTERNAL.value: 0.7,
        }
        source_mult = source_multipliers.get(source, 1.0)

        priority = (
            info_gain * info_gain_weight +
            novelty * novelty_weight +
            skill_gap * skill_gap_weight +
            gap_severity * gap_severity_weight +
            source_bonus * source_mult
        )

        return max(0.1, min(1.0, priority))

    def prioritize_goals(self, goals: List[CuriosityGoal]) -> List[CuriosityGoal]:
        scored = []
        for goal in goals:
            score = goal.priority
            novelty = self.calculate_novelty_bonus(
                goal.title.split()[0] if goal.title else 'explore',
                goal.domain,
            )
            score *= (0.7 + 0.3 * novelty)

            if self.belief_engine:
                relevant = self.belief_engine.find_relevant_beliefs(goal.title, goal.domain)
                if not relevant:
                    score *= 1.2
                else:
                    avg_conf = sum(b.confidence for b in relevant) / len(relevant)
                    if avg_conf < 0.5:
                        score *= 1.1

            scored.append((score, goal))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [g for _, g in scored]

    # ── 3.6: Intrinsic Reward Signal ──────────────────────────────────

    def calculate_intrinsic_reward(
        self,
        domain: str,
        action: str,
        predicted_confidence: float,
        actual_success: bool,
    ) -> float:
        uncertainty_before = 1.0 - predicted_confidence

        novelty = self.calculate_novelty_bonus(action, domain)

        exploration_bonus = uncertainty_before * (0.5 if actual_success else 0.2)

        if actual_success:
            info_gain = self.calculate_information_gain(domain)
            mastery_bonus = 0.1 if predicted_confidence > 0.7 else 0.0
        else:
            info_gain = self.calculate_information_gain(domain) * 0.6
            mastery_bonus = 0.0

        reward = (
            exploration_bonus * 0.4 +
            novelty * 0.2 +
            info_gain * 0.3 +
            mastery_bonus
        )

        self.record_action_attempt(f"{domain}:{action}")

        reward_key = f"{domain}:{action}"
        self.intrinsic_rewards[reward_key].append(reward)
        if len(self.intrinsic_rewards[reward_key]) > 100:
            self.intrinsic_rewards[reward_key] = self.intrinsic_rewards[reward_key][-50:]

        return max(0.0, min(1.0, reward))

    def update_curiosity_goal_outcome(self, goal_id: str, success: bool, domain: str):
        with self._lock:
            goal = self.curiosity_goals.get(goal_id)
            if goal:
                goal.attempted = True
                goal.outcome = "success" if success else "failure"

                if self.belief_engine and domain:
                    uncertainty_before = 1.0 - goal.information_gain_score
                    uncertainty_reduction = uncertainty_before * (0.3 if success else 0.1)
                    expected_reduction = goal.expected_uncertainty_reduction

                    if uncertainty_reduction > expected_reduction * 0.5:
                        logger.info(
                            f"Curiosity goal {goal_id} exceeded expected uncertainty reduction: "
                            f"{uncertainty_reduction:.2f} vs {expected_reduction:.2f}"
                        )

    def get_intrinsic_reward_summary(self) -> Dict:
        with self._lock:
            total_rewards = []
            domain_totals = defaultdict(list)
            for key, rewards in self.intrinsic_rewards.items():
                total_rewards.extend(rewards)
                domain = key.split(':')[0] if ':' in key else 'unknown'
                domain_totals[domain].extend(rewards)

            return {
                'total_actions': len(self.action_recency),
                'total_curiosity_goals': len(self.curiosity_goals),
                'attempted_goals': len([g for g in self.curiosity_goals.values() if g.attempted]),
                'successful_goals': len([g for g in self.curiosity_goals.values() if g.outcome == 'success']),
                'avg_intrinsic_reward': sum(total_rewards) / max(len(total_rewards), 1),
                'by_domain': {
                    d: {
                        'avg_reward': sum(r) / max(len(r), 1),
                        'action_count': len(r),
                    }
                    for d, r in domain_totals.items()
                },
            }

    # ── Internal helpers ────────────────────────────────────────────

    def _domain_novelty(self, domain: str) -> float:
        domain_actions = {
            k: r for k, r in self.action_recency.items()
            if domain in k
        }

        if not domain_actions:
            return 1.0

        recent_count = sum(1 for r in domain_actions.values() if r.recency_hours() < 24)
        total_actions = len(EXPLORATION_TARGETS.get(domain, []))
        if total_actions == 0:
            total_actions = 3

        coverage = len(domain_actions) / total_actions
        recency_penalty = recent_count * 0.15

        return max(0.1, min(1.0, 1.0 - coverage * 0.5 - recency_penalty))

    def _skill_gap_score(self, domain: str) -> float:
        if not self.self_model:
            return 0.5

        domain_caps = [
            cap for key, cap in self.self_model.capabilities.items()
            if cap.domain == domain and cap.sample_size < self.KNOWLEDGE_GAP_THRESHOLD_SAMPLES
        ]

        if not domain_caps:
            return 0.2

        avg_gap = sum(1.0 - (cap.sample_size / self.KNOWLEDGE_GAP_THRESHOLD_SAMPLES) for cap in domain_caps) / len(domain_caps)
        return max(0.1, min(1.0, avg_gap))

    def _pick_exploration_target(self, domain: str, gap: Dict) -> Dict:
        targets = EXPLORATION_TARGETS.get(domain, EXPLORATION_TARGETS.get('unknown', []))

        if targets:
            import random
            attempts = {t[1] for t in targets if f"{domain}:{t[1]}" in self.action_recency}
            untried = [t for t in targets if t[1] not in attempts]
            if untried:
                chosen = random.choice(untried)
            else:
                least_recent = min(
                    targets,
                    key=lambda t: self.action_recency.get(f"{domain}:{t[1]}", ActionRecency(action_key="")).recency_hours()
                    if f"{domain}:{t[1]}" in self.action_recency else float('inf')
                )
                chosen = least_recent

            return {
                'title': chosen[0],
                'action': chosen[1],
                'plugin': chosen[2],
            }

        return {
            'title': f'Explore {domain} domain',
            'action': 'browse',
            'plugin': 'moltx',
        }


def get_curiosity_drive(belief_engine=None, self_model=None, goal_planner=None) -> CuriosityDrive:
    return CuriosityDrive(belief_engine, self_model, goal_planner)