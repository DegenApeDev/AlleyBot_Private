"""
GoalPlanner — Real planning with dependency graphs, precondition checking,
and rollback. Replaces template-based goal generation with genuine
means-end reasoning.

Goals are decomposed into steps with preconditions. If a step fails,
we check which precondition was wrong and try an alternative path.

Phase 2 additions:
- LLM-based creative decomposition for novel domains
- Domain detection from goal text
- Plan validation via BeliefEngine (reject should_wait steps)
- Multi-step outcome tracking (plan-level success/failure)
- Rollback cascade (undo completed steps on failure)
- Plan prioritization by expected value
- Plan conflict detection (resource contention)
"""

import json
import logging
import re
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum


class PlanStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    BLOCKED = "blocked"


class StepStatus(Enum):
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    id: str
    action: str
    plugin: str
    description: str
    preconditions: List[str] = field(default_factory=list)
    expected_outcome: str = ""
    rollback_action: str = ""
    depends_on: List[str] = field(default_factory=list)
    confidence: float = 0.5
    status: str = "pending"
    result: Optional[Dict] = None
    attempted_at: Optional[str] = None
    completed_at: Optional[str] = None
    failure_reason: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'PlanStep':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Plan:
    id: str
    goal: str
    domain: str
    steps: List[PlanStep] = field(default_factory=list)
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    failure_reason: str = ""
    priority: float = 0.5
    source: str = "autonomous"

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'goal': self.goal,
            'domain': self.domain,
            'steps': [s.to_dict() for s in self.steps],
            'status': self.status,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'failure_reason': self.failure_reason,
            'priority': self.priority,
            'source': self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Plan':
        steps = [PlanStep.from_dict(s) for s in data.get('steps', [])]
        return cls(
            id=data['id'], goal=data['goal'], domain=data['domain'],
            steps=steps, status=data.get('status', 'pending'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            completed_at=data.get('completed_at'),
            failure_reason=data.get('failure_reason', ''),
            priority=data.get('priority', 0.5),
            source=data.get('source', 'autonomous'),
        )


TOOL_REGISTRY = {
    'moltx': {
        'post': {'description': 'Create a post on Moltx', 'confidence_base': 0.7, 'requires': ['topic']},
        'reply': {'description': 'Reply to a post on Moltx', 'confidence_base': 0.75, 'requires': ['post_id', 'content']},
        'browse': {'description': 'Browse Moltx feed', 'confidence_base': 0.9, 'requires': []},
        'engage': {'description': 'Engage with Moltx content', 'confidence_base': 0.8, 'requires': ['post_id']},
        'analyze': {'description': 'Analyze Moltx trends', 'confidence_base': 0.85, 'requires': []},
    },
    'moltchan': {
        'post': {'description': 'Post on Moltchan', 'confidence_base': 0.7, 'requires': ['board', 'content']},
        'browse': {'description': 'Browse Moltchan boards', 'confidence_base': 0.9, 'requires': []},
        'engage': {'description': 'Engage on Moltchan', 'confidence_base': 0.75, 'requires': ['thread_id']},
    },
    'clawbr': {
        'post': {'description': 'Post on Clawbr', 'confidence_base': 0.7, 'requires': ['content']},
        'debate': {'description': 'Start or join a debate on Clawbr', 'confidence_base': 0.65, 'requires': ['topic']},
        'engage': {'description': 'Engage on Clawbr', 'confidence_base': 0.8, 'requires': []},
    },
    'moltbookai': {
        'post': {'description': 'Post on MoltBook', 'confidence_base': 0.7, 'requires': ['content']},
        'browse': {'description': 'Browse MoltBook', 'confidence_base': 0.9, 'requires': []},
    },
    'polymarket': {
        'analyze': {'description': 'Analyze Polymarket markets', 'confidence_base': 0.8, 'requires': []},
        'trade': {'description': 'Execute a trade on Polymarket', 'confidence_base': 0.5, 'requires': ['market_id', 'direction', 'amount']},
        'scan': {'description': 'Scan for market opportunities', 'confidence_base': 0.85, 'requires': []},
    },
    'crypto': {
        'analyze': {'description': 'Analyze crypto market data', 'confidence_base': 0.8, 'requires': []},
        'price_check': {'description': 'Check crypto prices', 'confidence_base': 0.95, 'requires': ['token']},
    },
    'analytics': {
        'analyze': {'description': 'Run analytics', 'confidence_base': 0.85, 'requires': []},
    },
    'a2a': {
        'discover': {'description': 'Discover other agents via A2A', 'confidence_base': 0.85, 'requires': []},
        'query': {'description': 'Query agent capabilities via A2A', 'confidence_base': 0.8, 'requires': ['agent_id']},
    },
    'selfimprove': {
        'analyze': {'description': 'Analyze capability gaps', 'confidence_base': 0.75, 'requires': []},
        'discover': {'description': 'Discover new skills', 'confidence_base': 0.6, 'requires': []},
    },
    'intelligence': {
        'analyze': {'description': 'Analyze intelligence data', 'confidence_base': 0.85, 'requires': []},
        'query': {'description': 'Query information', 'confidence_base': 0.8, 'requires': ['query']},
    },
    'mcp': {
        'research': {'description': 'Research via MCP', 'confidence_base': 0.75, 'requires': ['query']},
    },
    'engagement': {
        'engage': {'description': 'Cross-platform engagement', 'confidence_base': 0.7, 'requires': []},
        'coordinate': {'description': 'Coordinate engagement strategy', 'confidence_base': 0.65, 'requires': []},
    },
    'base_wallet_balance': {
        'check': {'description': 'Check Base wallet balance', 'confidence_base': 0.95, 'requires': []},
        'query': {'description': 'Query Base wallet info', 'confidence_base': 0.9, 'requires': []},
    },
    'solana_wallet_balance': {
        'check': {'description': 'Check Solana wallet balance', 'confidence_base': 0.95, 'requires': []},
        'query': {'description': 'Query Solana wallet info', 'confidence_base': 0.9, 'requires': []},
    },
    'clawchess': {
        'play': {'description': 'Play chess', 'confidence_base': 0.6, 'requires': []},
    },
}


class GoalPlanner:
    """
    Decompose goals into plans with dependency graphs, precondition
    checking, and rollback. Uses LLM for decomposition (creative
    part) but validates with symbolic checks (reliable part).
    """

    def __init__(self, storage_path: str = 'data/plans.json'):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.plans: Dict[str, Plan] = {}
        self.tool_registry = TOOL_REGISTRY
        self._load()

    def get_available_tools(self, domain: str = None) -> Dict:
        if domain and domain in self.tool_registry:
            return {domain: self.tool_registry[domain]}
        return self.tool_registry

    def get_tool_for_action(self, action_description: str) -> List[Dict]:
        action_lower = action_description.lower()
        matches = []
        for plugin, actions in self.tool_registry.items():
            for action_name, action_info in actions.items():
                if action_name in action_lower or action_info['description'].lower() in action_lower:
                    matches.append({
                        'plugin': plugin,
                        'action': action_name,
                        'description': action_info['description'],
                        'confidence_base': action_info['confidence_base'],
                        'requires': action_info['requires'],
                    })
        return matches

    def decompose_goal(
        self,
        goal: str,
        domain: str = "general",
        belief_engine=None,
        self_model=None,
        priority: float = 0.5,
    ) -> Plan:
        with self._lock:
            detected_domain = domain if domain != "general" else detect_domain(goal)
            steps = self._generate_steps(goal, detected_domain, belief_engine, self_model)

            # Try LLM decomposition for unknown domains or when templates are thin
            if detected_domain == 'unknown' or len(steps) <= 2:
                llm_steps = llm_decompose(goal, detected_domain, self.tool_registry)
                if llm_steps and len(llm_steps) > len(steps):
                    steps = [
                        PlanStep(
                            id=f"step_{i}_{s['plugin']}_{s['action']}",
                            action=s['action'],
                            plugin=s['plugin'],
                            description=s['description'],
                            expected_outcome=s.get('expected_outcome', ''),
                            rollback_action=s.get('rollback_action', ''),
                            confidence=s.get('confidence', 0.5),
                        )
                        for i, s in enumerate(llm_steps)
                    ]
                    logging.getLogger(__name__).info(
                        f"LLM decomposition produced {len(steps)} steps for goal: {goal[:60]}"
                    )

            for i, step in enumerate(steps):
                if i > 0:
                    step.depends_on = [steps[i - 1].id]
                    step.preconditions = [f"Step '{steps[i-1].id}' completed successfully"]

            plan_id = f"plan_{int(datetime.now().timestamp())}"
            plan = Plan(
                id=plan_id, goal=goal, domain=detected_domain,
                steps=steps, status="pending", priority=priority,
            )

            if belief_engine:
                self._validate_plan_against_beliefs(plan, belief_engine)

            if self_model:
                self._validate_plan_against_capabilities(plan, self_model)

            # 2.6: Plan prioritization — score by expected value
            plan.priority = score_plan(plan, belief_engine, self_model)

            self.plans[plan_id] = plan
            self._save()
            return plan

    def _generate_steps(
        self,
        goal: str,
        domain: str,
        belief_engine=None,
        self_model=None,
    ) -> List[PlanStep]:
        goal_lower = goal.lower()
        steps = []

        if domain == 'social' or any(w in goal_lower for w in ['post', 'engage', 'reply', 'interact', 'social', 'presence', 'community']):
            steps = [
                PlanStep(
                    id=f"step_observe_{domain}",
                    action="feed", plugin="moltx",
                    description=f"Browse {domain} platform to understand current context",
                    expected_outcome="Current context and trending topics identified",
                    rollback_action="Skip observation, proceed with general knowledge",
                    confidence=0.9,
                ),
                PlanStep(
                    id=f"step_analyze_{domain}",
                    action="analyze", plugin="analytics",
                    description="Analyze trends, sentiment, and engagement patterns",
                    preconditions=[f"step_observe_{domain} completed"],
                    expected_outcome="Key topics and engagement opportunities identified",
                    rollback_action="Use cached analysis",
                    confidence=0.8,
                ),
                PlanStep(
                    id=f"step_create_{domain}",
                    action="post", plugin="moltx",
                    description="Create and post content based on analysis",
                    preconditions=[f"step_analyze_{domain} completed"],
                    expected_outcome="Content posted and engagement tracking started",
                    rollback_action="Revert to simpler content approach",
                    confidence=0.7,
                ),
                PlanStep(
                    id=f"step_engage_{domain}",
                    action="engage", plugin="moltx",
                    description="Engage with responses and follow up",
                    preconditions=[f"step_create_{domain} completed"],
                    expected_outcome="Community engagement established",
                    rollback_action="Pause engagement, monitor passively",
                    confidence=0.75,
                ),
            ]

        elif domain == 'market' or any(w in goal_lower for w in ['trade', 'market', 'price', 'crypto', 'token', 'portfolio']):
            steps = [
                PlanStep(
                    id="step_scan_markets",
                    action="scan", plugin="polymarket",
                    description="Scan available markets for opportunities",
                    expected_outcome="List of potential opportunities",
                    rollback_action="Skip scan, rely on known markets",
                    confidence=0.85,
                ),
                PlanStep(
                    id="step_analyze_market",
                    action="analyze", plugin="crypto",
                    description="Analyze market conditions and price data",
                    preconditions=["step_scan_markets completed"],
                    expected_outcome="Market analysis with risk assessment",
                    rollback_action="Use conservative strategy",
                    confidence=0.8,
                ),
                PlanStep(
                    id="step_check_wallet",
                    action="check", plugin="base_wallet_balance",
                    description="Verify wallet balances before any action",
                    preconditions=["step_analyze_market completed"],
                    expected_outcome="Confirmed available funds",
                    rollback_action="Skip trade, insufficient funds",
                    confidence=0.95,
                ),
                PlanStep(
                    id="step_execute_trade",
                    action="trade", plugin="polymarket",
                    description="Execute trade based on analysis",
                    preconditions=["step_check_wallet completed"],
                    expected_outcome="Trade executed successfully",
                    rollback_action="Cancel trade order",
                    confidence=0.5,
                ),
            ]

        elif domain == 'analysis' or any(w in goal_lower for w in ['analyze', 'research', 'learn', 'understand', 'monitor']):
            steps = [
                PlanStep(
                    id="step_gather_data",
                    action="feed", plugin="moltx",
                    description="Gather data from relevant platforms",
                    expected_outcome="Data collected from multiple sources",
                    rollback_action="Use available cached data",
                    confidence=0.85,
                ),
                PlanStep(
                    id="step_analyze_data",
                    action="analyze", plugin="intelligence",
                    description="Analyze gathered data for insights",
                    preconditions=["step_gather_data completed"],
                    expected_outcome="Key insights and patterns identified",
                    rollback_action="Use surface-level analysis",
                    confidence=0.8,
                ),
                PlanStep(
                    id="step_report_findings",
                    action="post", plugin="moltx",
                    description="Share findings or update human via Telegram",
                    preconditions=["step_analyze_data completed"],
                    expected_outcome="Insights communicated to relevant audience",
                    rollback_action="Store findings for later review",
                    confidence=0.7,
                ),
            ]

        else:
            tools = self.get_tool_for_action(goal)
            if tools:
                for i, tool in enumerate(tools[:4]):
                    steps.append(PlanStep(
                        id=f"step_{i}_{tool['plugin']}_{tool['action']}",
                        action=tool['action'], plugin=tool['plugin'],
                        description=tool['description'],
                        expected_outcome=f"Successfully executed {tool['action']}",
                        rollback_action="Report failure and try alternative",
                        confidence=tool['confidence_base'],
                    ))
            else:
                steps.append(PlanStep(
                    id="step_generic_observe",
                    action="feed", plugin="moltx",
                    description="Observe current state across platforms",
                    expected_outcome="Current awareness of platform activity",
                    rollback_action="Use cached observations",
                    confidence=0.7,
                ))
                steps.append(PlanStep(
                    id="step_generic_act",
                    action="engage", plugin="engagement",
                    description="Take action based on observations",
                    preconditions=["step_generic_observe completed"],
                    expected_outcome="Action completed",
                    rollback_action="Step back and reassess",
                    confidence=0.5,
                ))

        for step in steps:
            if not step.depends_on and steps.index(step) > 0:
                step.depends_on = [steps[steps.index(step) - 1].id]

        return steps

    def _validate_plan_against_beliefs(self, plan: Plan, belief_engine) -> None:
        for step in plan.steps:
            should_wait, reason = belief_engine.should_wait(
                f"{step.plugin}.{step.action}", plan.domain
            )
            if should_wait:
                step.confidence *= 0.7
                step.description += f" [CAUTION: {reason}]"
            # 2.3: If belief prediction is extremely low, block the step
            if hasattr(belief_engine, 'predict'):
                prediction = belief_engine.predict(f"{step.plugin}.{step.action}", plan.domain)
                if prediction.predicted_success < 0.1:
                    step.status = "blocked"
                    step.failure_reason = f"Belief prediction too low: {prediction.predicted_success:.0%}"

    def _validate_plan_against_capabilities(self, plan: Plan, self_model) -> None:
        for step in plan.steps:
            should_attempt, reason = self_model.should_attempt(step.plugin, step.action)
            if not should_attempt:
                step.status = "blocked"
                step.failure_reason = reason
                step.confidence *= 0.4

    def check_preconditions(self, plan: Plan, current_state: Dict = None) -> Plan:
        if current_state is None:
            current_state = {}

        for step in plan.steps:
            all_deps_met = True
            for dep_id in step.depends_on:
                dep = next((s for s in plan.steps if s.id == dep_id), None)
                if dep and dep.status != "completed":
                    all_deps_met = False
                    step.status = "blocked"
                    step.failure_reason = f"Waiting for dependency: {dep_id}"
                    break

            if all_deps_met:
                step.status = "ready"

        return plan

    def get_next_step(self, plan: Plan) -> Optional[PlanStep]:
        ready_steps = [
            s for s in plan.steps
            if s.status in ("ready", "pending")
            and all(
                next((ps for ps in plan.steps if ps.id == dep_id), None) is not None
                and next((ps for ps in plan.steps if ps.id == dep_id), None).status == "completed"
                for dep_id in s.depends_on
            )
        ]

        if not ready_steps:
            blocked = [s for s in plan.steps if s.status == "blocked"]
            if blocked:
                plan.status = "blocked"
                plan.failure_reason = f"Blocked by: {blocked[0].failure_reason}"
                self._save()
            return None

        return max(ready_steps, key=lambda s: s.confidence)

    def mark_step_completed(self, plan_id: str, step_id: str, result: Dict) -> Plan:
        with self._lock:
            plan = self.plans.get(plan_id)
            if not plan:
                return None

            step = next((s for s in plan.steps if s.id == step_id), None)
            if step:
                step.status = "completed"
                step.result = result
                step.completed_at = datetime.now().isoformat()

            all_completed = all(s.status in ("completed", "skipped") for s in plan.steps)
            if all_completed:
                plan.status = "completed"
                plan.completed_at = datetime.now().isoformat()

            self._save()
            return plan

    def mark_step_failed(self, plan_id: str, step_id: str, reason: str, result: Dict = None) -> Plan:
        with self._lock:
            plan = self.plans.get(plan_id)
            if not plan:
                return None

            step = next((s for s in plan.steps if s.id == step_id), None)
            if step:
                step.status = "failed"
                step.failure_reason = reason
                step.result = result

            # 2.5: Rollback cascade — block all dependent steps
            dependent_steps = [s for s in plan.steps if step_id in s.depends_on]
            if dependent_steps:
                for dep_step in dependent_steps:
                    dep_step.status = "blocked"
                    dep_step.failure_reason = f"Dependency {step_id} failed: {reason}"

            plan.status = "failed"
            plan.failure_reason = f"Step {step_id} failed: {reason}"
            self._save()
            return plan

    def rollback_completed_steps(self, plan_id: str, up_to_step_id: str) -> Plan:
        """Undo completed steps (2.5 rollback cascade).

        Marks completed steps as 'rolled_back' and logs their rollback_action.
        Returns the updated plan.
        """
        with self._lock:
            plan = self.plans.get(plan_id)
            if not plan:
                return None

            rolled_back = 0
            for step in plan.steps:
                if step.status == "completed":
                    step.status = "rolled_back"
                    rolled_back += 1
                    logging.getLogger(__name__).info(
                        f"Rolled back step {step.id}: {step.rollback_action}"
                    )
                elif step.status in ("pending", "ready"):
                    # No point rolling back steps that haven't been executed
                    break

            if rolled_back > 0:
                logging.getLogger(__name__).info(
                    f"Rolled back {rolled_back} steps in plan {plan_id}"
                )

            self._save()
            return plan

    def record_plan_outcome(self, plan_id: str, success: bool, belief_engine=None, self_model=None) -> Dict:
        """Record plan-level outcome (2.4 multi-step outcome tracking).

        Updates belief engine and self model with the overall plan result.
        """
        with self._lock:
            plan = self.plans.get(plan_id)
            if not plan:
                return {'error': f'Plan {plan_id} not found'}

            completed = sum(1 for s in plan.steps if s.status == "completed")
            total = len(plan.steps)
            success_rate = completed / total if total > 0 else 0.0

            outcome = {
                'plan_id': plan_id,
                'goal': plan.goal,
                'domain': plan.domain,
                'success': success,
                'steps_completed': completed,
                'steps_total': total,
                'step_success_rate': success_rate,
                'priority': plan.priority,
            }

            # Update domain-level beliefs if engines are provided
            if belief_engine:
                try:
                    belief_engine.update_from_outcome(
                        action=f"plan:{plan.goal[:50]}",
                        domain=plan.domain,
                        predicted_success=plan.priority,
                        actual_success=success,
                        context=f"plan_with_{total}_steps",
                        outcome_description=f"Completed {completed}/{total} steps",
                    )
                except Exception as e:
                    logging.getLogger(__name__).debug(f"Plan belief update failed: {e}")

            if self_model:
                try:
                    self_model.record_outcome(
                        domain=plan.domain,
                        action_type="plan_execution",
                        predicted_confidence=plan.priority,
                        actual_success=success,
                        context=f"plan_{plan_id}",
                    )
                except Exception as e:
                    logging.getLogger(__name__).debug(f"Plan self-model update failed: {e}")

            self._save()
            return outcome

    def get_alternative_path(self, plan: Plan, failed_step_id: str) -> Optional[PlanStep]:
        failed_step = next((s for s in plan.steps if s.id == failed_step_id), None)
        if not failed_step:
            return None

        alternatives = self.get_tool_for_action(failed_step.action)
        used_plugins = {s.plugin for s in plan.steps}

        for alt in alternatives:
            if alt['plugin'] != failed_step.plugin and alt['plugin'] not in used_plugins:
                return PlanStep(
                    id=f"alt_{failed_step_id}_{alt['plugin']}",
                    action=alt['action'],
                    plugin=alt['plugin'],
                    description=f"Alternative: {alt['description']}",
                    preconditions=failed_step.preconditions,
                    expected_outcome=failed_step.expected_outcome,
                    rollback_action=failed_step.rollback_action,
                    confidence=alt['confidence_base'] * 0.8,
                )

        return None

    def get_active_plans(self) -> List[Plan]:
        return [p for p in self.plans.values() if p.status in ("pending", "in_progress")]

    def get_plan_report(self, plan_id: str) -> Dict:
        plan = self.plans.get(plan_id)
        if not plan:
            return {'error': f'Plan {plan_id} not found'}

        completed = sum(1 for s in plan.steps if s.status == "completed")
        failed = sum(1 for s in plan.steps if s.status == "failed")
        total = len(plan.steps)

        return {
            'plan_id': plan_id,
            'goal': plan.goal,
            'domain': plan.domain,
            'status': plan.status,
            'progress': f"{completed}/{total} steps completed",
            'failures': failed,
            'steps': [{'id': s.id, 'action': s.action, 'plugin': s.plugin,
                        'status': s.status, 'confidence': s.confidence} for s in plan.steps],
        }

    def _save(self):
        with self._lock:
            try:
                data = {k: v.to_dict() for k, v in self.plans.items()}
                with open(self.storage_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logging.getLogger(__name__).warning(f"GoalPlanner save failed: {e}")

    def _load(self):
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                with self._lock:
                    self.plans = {k: Plan.from_dict(v) for k, v in data.items()}
        except Exception as e:
            logging.getLogger(__name__).warning(f"GoalPlanner load failed: {e}")
            with self._lock:
                self.plans = {}


def get_goal_planner(storage_path: str = 'data/plans.json') -> GoalPlanner:
    return GoalPlanner(storage_path)


# ── Domain Detection ──────────────────────────────────────────────

DOMAIN_KEYWORDS = {
    'social': ['post', 'engage', 'reply', 'interact', 'social', 'presence',
                'community', 'moltx', 'moltchan', 'clawbr', 'moltbook', 'follow',
                'comment', 'share', 'mention', 'feed'],
    'market': ['trade', 'market', 'price', 'crypto', 'token', 'portfolio',
                'buy', 'sell', 'swap', 'dex', 'polymarket', 'liquidity'],
    'trading': ['swap', 'dex', 'limit order', 'slippage', 'arbitrage', 'position',
                 'stop loss', 'take profit', 'leverage'],
    'analysis': ['analyze', 'research', 'learn', 'understand', 'monitor', 'scan',
                  'insight', 'data', 'trend', 'statistics', 'report'],
    'onchain': ['wallet', 'transaction', 'gas', 'contract', 'deploy', 'mint',
                 'bridge', 'stake', 'claim', 'verify', 'token'],
    'security': ['security', 'check', 'audit', 'verify', 'protect', 'balance',
                  'authenticate', 'permission', 'approve'],
    'self_improvement': ['skill', 'learn', 'improve', 'fix', 'self', 'optimize',
                          'capability', 'gap', 'auto', 'upgrade'],
    'content': ['create', 'write', 'generate', 'compose', 'draft', 'content',
                 'article', 'summary', 'format'],
}


def detect_domain(goal: str) -> str:
    """Classify a goal into a known domain or 'unknown'.

    Returns the domain with the highest keyword overlap score.
    """
    goal_lower = goal.lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in goal_lower)
        if score > 0:
            scores[domain] = score
    if scores:
        return max(scores, key=scores.get)
    return 'unknown'


# ── LLM-based Goal Decomposition ──────────────────────────────────

DECOMPOSITION_PROMPT = """You are a planning assistant for an autonomous agent. Break down the following goal into 3-5 concrete, executable steps.

Goal: {goal}
Domain: {domain}
Available tools: {tools}

Rules:
1. Each step must use one of the available tools
2. Each step must have a clear expected outcome
3. Steps should form a logical dependency chain
4. Include a rollback action for each step (what to do if it fails)

Respond in JSON format only:
[
  {{
    "action": "tool_action_name",
    "plugin": "plugin_name",
    "description": "What this step does",
    "expected_outcome": "What success looks like",
    "rollback_action": "What to do if this fails",
    "confidence": 0.8
  }}
]

Tools available: {tools_list}"""


def llm_decompose(goal: str, domain: str, tool_registry: Dict) -> Optional[List[Dict]]:
    """Use LLM to decompose a goal into steps for novel domains.

    Returns a list of step dicts, or None if LLM is unavailable.
    """
    try:
        from src.core.llm_router import reason
    except ImportError:
        logging.getLogger(__name__).debug("LLM router not available for goal decomposition")
        return None

    tools_list = []
    for plugin, actions in tool_registry.items():
        for action_name, action_info in actions.items():
            tools_list.append(f"{plugin}.{action_name}: {action_info['description']}")

    prompt = DECOMPOSITION_PROMPT.format(
        goal=goal,
        domain=domain,
        tools=", ".join(tool_registry.keys()),
        tools_list="\n".join(tools_list),
    )

    try:
        response = reason(prompt, max_tokens=2000)
        if not response:
            return None

        # Extract JSON from response (may be wrapped in markdown)
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if not json_match:
            return None

        steps = json.loads(json_match.group())
        if not isinstance(steps, list):
            return None

        # Validate each step has required fields
        valid_steps = []
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            valid_steps.append({
                'action': step.get('action', f'step_{i}'),
                'plugin': step.get('plugin', 'unknown'),
                'description': step.get('description', f'Step {i+1} of {goal}'),
                'expected_outcome': step.get('expected_outcome', ''),
                'rollback_action': step.get('rollback_action', 'Skip and continue'),
                'confidence': float(step.get('confidence', 0.5)),
            })

        return valid_steps if valid_steps else None

    except (json.JSONDecodeError, ValueError, ImportError, Exception) as e:
        logging.getLogger(__name__).warning(f"LLM goal decomposition failed: {e}")
        return None


# ── Plan Prioritization ────────────────────────────────────────────

DOMAIN_IMPORTANCE = {
    'security': 1.0,
    'onchain': 0.9,
    'trading': 0.85,
    'market': 0.8,
    'social': 0.7,
    'analysis': 0.65,
    'content': 0.6,
    'self_improvement': 0.55,
    'unknown': 0.5,
}


def score_plan(plan, belief_engine=None, self_model=None) -> float:
    """Score a plan by expected value = belief_confidence × domain_importance.

    Higher scores = more valuable plans to pursue.
    """
    domain = getattr(plan, 'domain', 'unknown') if not isinstance(plan, dict) else plan.get('domain', 'unknown')
    base_importance = DOMAIN_IMPORTANCE.get(domain, 0.5)

    avg_confidence = 0.5
    steps = plan.steps if hasattr(plan, 'steps') else plan.get('steps', [])
    if steps:
        confidences = [s.confidence if hasattr(s, 'confidence') else s.get('confidence', 0.5) for s in steps]
        avg_confidence = sum(confidences) / len(confidences)

    # Belief adjustment
    belief_multiplier = 1.0
    if belief_engine:
        goal_text = plan.goal if hasattr(plan, 'goal') else plan.get('goal', '')
        prediction = belief_engine.predict(goal_text, domain)
        belief_multiplier = prediction.predicted_success

    return base_importance * avg_confidence * belief_multiplier


def detect_conflicts(plans: List) -> List[Tuple]:
    """Detect plans that compete for the same resources (plugins/actions).

    Returns a list of (plan_a_id, plan_b_id, shared_resource) tuples.
    """
    conflicts = []
    resource_map = {}

    for plan in plans:
        plan_id = plan.id if hasattr(plan, 'id') else plan.get('id', '?')
        steps = plan.steps if hasattr(plan, 'steps') else plan.get('steps', [])
        for step in steps:
            plugin = step.plugin if hasattr(step, 'plugin') else step.get('plugin', '?')
            action = step.action if hasattr(step, 'action') else step.get('action', '?')
            resource_key = f"{plugin}.{action}"
            if resource_key not in resource_map:
                resource_map[resource_key] = []
            resource_map[resource_key].append(plan_id)

    for resource, plan_ids in resource_map.items():
        if len(plan_ids) > 1:
            for i in range(len(plan_ids)):
                for j in range(i + 1, len(plan_ids)):
                    conflicts.append((plan_ids[i], plan_ids[j], resource))

    return conflicts