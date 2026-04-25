"""
CognitiveIntegration — Wires BeliefEngine, SelfModel, GoalPlanner, and
ToolAwareness into the autonomous brain cycle and action router.

This replaces Duat/Synergy float arithmetic with real cognitive architecture:
- BeliefEngine: predict-compare-update for every action
- SelfModel: calibrated capability tracking
- GoalPlanner: dependency-graph plans with rollback
- ToolAwareness: agent knows its available tools

Also wires Telegram notifications for goal completion and permission requests.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.agentic.belief_engine import BeliefEngine, get_belief_engine
from src.agentic.self_model import SelfModel, get_self_model
from src.agentic.goal_planner import GoalPlanner, get_goal_planner

logger = logging.getLogger(__name__)


class CognitiveIntegration:
    """
    The glue between the new cognitive components and the existing
    autonomous brain / action router loop.

    This is the single integration point. All the new cognitive
    capabilities flow through here.
    """

    def __init__(self, telegram_plugin=None):
        self.belief_engine = get_belief_engine()
        self.self_model = get_self_model()
        self.goal_planner = get_goal_planner()
        self.telegram_plugin = telegram_plugin
        self._cycle_count = 0

    def set_telegram(self, telegram_plugin):
        self.telegram_plugin = telegram_plugin

    # ── Called BEFORE an action is executed ──────────────────────────

    def predict_action_outcome(self, action: str, domain: str) -> Dict:
        prediction = self.belief_engine.predict(action, domain)

        capability_confidence = self.self_model.get_confidence_for(domain, action)

        should_attempt, reason = self.self_model.should_attempt(domain, action)
        should_wait, wait_reason = self.belief_engine.should_wait(action, domain)

        combined_confidence = (
            prediction.predicted_success * 0.6 +
            capability_confidence * 0.4
        )

        if not should_attempt:
            combined_confidence *= 0.3
        if should_wait:
            combined_confidence *= 0.6

        return {
            'predicted_success': combined_confidence,
            'belief_prediction': prediction.predicted_success,
            'capability_confidence': capability_confidence,
            'should_attempt': should_attempt,
            'attempt_reason': reason,
            'should_wait': should_wait,
            'wait_reason': wait_reason,
            'relevant_beliefs': prediction.relevant_beliefs[:3],
            'predicted_outcome': prediction.predicted_outcome,
        }

    # ── Called AFTER an action completes ────────────────────────────

    def record_action_outcome(
        self,
        action: str,
        domain: str,
        predicted_confidence: float,
        actual_success: bool,
        context: str = "",
        outcome_description: str = "",
    ) -> Dict:
        belief_result = self.belief_engine.update_from_outcome(
            action=action,
            domain=domain,
            predicted_success=predicted_confidence,
            actual_success=actual_success,
            context=context,
            outcome_description=outcome_description,
        )

        cap_result = self.self_model.record_outcome(
            domain=domain,
            action_type=action,
            predicted_confidence=predicted_confidence,
            actual_success=actual_success,
            context=context,
        )

        if actual_success and self._should_notify_completion(action, domain):
            self.notify_completion(action, domain, outcome_description)

        if not actual_success and self._should_notify_failure(action, domain, cap_result):
            self.notify_failure(action, domain, outcome_description, belief_result)

        return {
            'belief_update': belief_result,
            'capability_update': cap_result,
        }

    # ── Goal Planning ────────────────────────────────────────────────

    def plan_goal(self, goal: str, domain: str = "general") -> Dict:
        plan = self.goal_planner.decompose_goal(
            goal=goal,
            domain=domain,
            belief_engine=self.belief_engine,
            self_model=self.self_model,
        )

        next_step = self.goal_planner.get_next_step(plan)

        return {
            'plan_id': plan.id,
            'goal': goal,
            'domain': domain,
            'steps': [{'id': s.id, 'action': s.action, 'plugin': s.plugin,
                        'confidence': s.confidence, 'status': s.status} for s in plan.steps],
            'next_step': {'id': next_step.id, 'action': next_step.action,
                          'plugin': next_step.plugin, 'confidence': next_step.confidence} if next_step else None,
            'status': plan.status,
        }

    def get_available_tools(self, domain: str = None) -> Dict:
        return self.goal_planner.get_available_tools(domain)

    def get_self_awareness_report(self) -> Dict:
        return self.self_model.generate_self_awareness_report()

    def get_belief_calibration(self) -> Dict:
        return self.belief_engine.get_calibration_report()

    def get_domain_strengths(self) -> Dict:
        return self.belief_engine.get_domain_strengths()

    # ── Periodic Reflection (replaces MetaCognitionEngine) ──────────

    def reflect(self) -> Dict:
        self._cycle_count += 1

        beliefs = self.belief_engine.get_domain_strengths()
        calibration = self.belief_engine.get_calibration_report()
        self_report = self.self_model.generate_self_awareness_report()

        strengths = self_report.get('strengths', [])
        weaknesses = self_report.get('weaknesses', [])
        learn_priorities = self_report.get('learning_priorities', [])

        reflection = {
            'cycle': self._cycle_count,
            'timestamp': datetime.now().isoformat(),
            'beliefs': beliefs,
            'calibration': calibration,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'learning_priorities': learn_priorities,
            'recommendation': self_report.get('recommendation', 'Continue standard operations'),
            'overall_assessment': self._compute_overall_assessment(calibration, strengths, weaknesses),
        }

        if self._cycle_count % 10 == 0:
            self.send_periodic_digest(reflection)

        return reflection

    def _compute_overall_assessment(self, calibration, strengths, weaknesses):
        n_strengths = len(strengths)
        n_weaknesses = len(weaknesses)
        cal_error = calibration.get('mean_absolute_error', 0.5)

        if n_strengths > n_weaknesses and cal_error < 0.15:
            return "strong_and_calibrated"
        elif n_strengths > n_weaknesses and cal_error >= 0.15:
            return "strong_but_overconfident"
        elif n_weaknesses > n_strengths and cal_error < 0.15:
            return "weak_but_learning"
        elif n_weaknesses > n_strengths:
            return "struggling_refocus"
        else:
            return "moderate_progress"

    # ── Plan Execution ───────────────────────────────────────────────

    def execute_plan_step(self, plan_id: str, step_id: str, result: Dict, success: bool):
        if success:
            plan = self.goal_planner.mark_step_completed(plan_id, step_id, result)
            if plan and plan.status == "completed":
                self.notify_goal_completion(plan.goal, plan.domain, plan.id)
        else:
            reason = result.get('error', result.get('message', 'Unknown failure'))
            plan = self.goal_planner.mark_step_failed(plan_id, step_id, reason, result)

            alt = self.goal_planner.get_alternative_path(plan, step_id) if plan else None
            if alt:
                logger.info(f"Alternative path available for {step_id}: {alt.plugin}.{alt.action}")
            else:
                self.notify_plan_failure(plan_id, step_id, reason)

    # ── Telegram Notifications ───────────────────────────────────────

    def notify_completion(self, action: str, domain: str, details: str):
        if not self.telegram_plugin:
            return
        try:
            msg = f"✅ Completed: {domain}/{action}\n{details[:200]}"
            if hasattr(self.telegram_plugin, 'notify_autonomous_accomplishment'):
                self.telegram_plugin.notify_autonomous_accomplishment(
                    title=f"{domain}/{action} completed",
                    summary=details[:200],
                    reward_signal="Progress made",
                )
            elif hasattr(self.telegram_plugin, 'send_message_to_owner_sync'):
                self.telegram_plugin.send_message_to_owner_sync(msg)
        except Exception as e:
            logger.debug(f"Telegram completion notification failed: {e}")

    def notify_failure(self, action: str, domain: str, details: str, belief_result: Dict):
        if not self.telegram_plugin:
            return
        try:
            explanations = self.belief_engine.explain_failure(action, domain)
            explanation_text = "; ".join(explanations[:2])
            msg = f"⚠️ Failed: {domain}/{action}\n{details[:100]}\nAnalysis: {explanation_text}"
            if hasattr(self.telegram_plugin, 'notify_error'):
                self.telegram_plugin.notify_error(
                    error_type=f"{domain}/{action}_failure",
                    error_message=msg,
                )
            elif hasattr(self.telegram_plugin, 'send_message_to_owner_sync'):
                self.telegram_plugin.send_message_to_owner_sync(msg)
        except Exception as e:
            logger.debug(f"Telegram failure notification failed: {e}")

    def notify_goal_completion(self, goal: str, domain: str, plan_id: str):
        if not self.telegram_plugin:
            return
        try:
            report = self.goal_planner.get_plan_report(plan_id)
            progress = report.get('progress', 'unknown')
            msg = f"🎯 Goal completed: {goal}\nDomain: {domain}\nProgress: {progress}"

            if hasattr(self.telegram_plugin, 'notify_autonomous_accomplishment'):
                self.telegram_plugin.notify_autonomous_accomplishment(
                    title=f"Goal achieved: {goal}",
                    summary=msg,
                    reward_signal="Goal completed autonomously",
                )
            elif hasattr(self.telegram_plugin, 'send_message_to_owner_sync'):
                self.telegram_plugin.send_message_to_owner_sync(msg)
        except Exception as e:
            logger.debug(f"Telegram goal notification failed: {e}")

    def notify_plan_failure(self, plan_id: str, step_id: str, reason: str):
        if not self.telegram_plugin:
            return
        try:
            msg = f"❌ Plan {plan_id} failed at {step_id}: {reason}"
            if hasattr(self.telegram_plugin, 'notify_error'):
                self.telegram_plugin.notify_error(
                    error_type="plan_failure",
                    error_message=msg,
                )
            elif hasattr(self.telegram_plugin, 'send_message_to_owner_sync'):
                self.telegram_plugin.send_message_to_owner_sync(msg)
        except Exception as e:
            logger.debug(f"Telegram plan failure notification failed: {e}")

    def send_periodic_digest(self, reflection: Dict):
        if not self.telegram_plugin:
            return
        try:
            assessment = reflection.get('overall_assessment', 'unknown')
            strengths = reflection.get('strengths', [])
            weaknesses = reflection.get('weaknesses', [])
            learn = reflection.get('learning_priorities', [])
            rec = reflection.get('recommendation', '')

            lines = [
                f"🧠 AlleyBot Self-Reflection (Cycle {reflection.get('cycle', '?')}):",
                f"Status: {assessment}",
                f"Recommendation: {rec}",
            ]
            if strengths:
                lines.append(f"Strong: {', '.join(s['domain'] for s in strengths[:3])}")
            if weaknesses:
                lines.append(f"Avoid: {', '.join(w['domain'] for w in weaknesses[:3])}")
            if learn:
                lines.append(f"Learn: {', '.join(l['domain'] for l in learn[:3])}")

            msg = "\n".join(lines)

            if hasattr(self.telegram_plugin, 'maybe_send_autonomous_digest'):
                self.telegram_plugin.maybe_send_autonomous_digest(hours=1)
            elif hasattr(self.telegram_plugin, 'send_message_to_owner_sync'):
                self.telegram_plugin.send_message_to_owner_sync(msg)
        except Exception as e:
            logger.debug(f"Telegram digest notification failed: {e}")

    def request_permission(self, action: str, domain: str, reason: str) -> bool:
        if not self.telegram_plugin:
            return True

        try:
            msg = (
                f"🔐 Permission Request\n"
                f"Action: {domain}/{action}\n"
                f"Reason: {reason}\n"
                f"Reply /approve or /deny"
            )
            if hasattr(self.telegram_plugin, 'send_message_to_owner_sync'):
                self.telegram_plugin.send_message_to_owner_sync(msg)
                return False

            if hasattr(self.telegram_plugin, 'notify_error'):
                self.telegram_plugin.notify_error(
                    error_type="permission_request",
                    error_message=msg,
                )
                return False

            return True
        except Exception as e:
            logger.debug(f"Telegram permission request failed: {e}")
            return True

    # ── Internal helpers ──────────────────────────────────────────────

    def _should_notify_completion(self, action: str, domain: str) -> bool:
        notify_actions = {'post', 'trade', 'create', 'deploy', 'launch', 'send'}
        notify_domains = {'market', 'trading', 'onchain'}

        action_root = action.split(':')[-1] if ':' in action else action
        return action_root in notify_actions or domain in notify_domains

    def _should_notify_failure(self, action: str, domain: str, cap_result: Dict) -> bool:
        cap = self.self_model.capabilities.get(f"{domain}:{action}")
        if not cap:
            return True
        return cap.consecutive_failures >= 2


# Singleton
_cognitive: Optional[CognitiveIntegration] = None


def get_cognitive(telegram_plugin=None) -> CognitiveIntegration:
    global _cognitive
    if _cognitive is None:
        _cognitive = CognitiveIntegration(telegram_plugin)
    elif telegram_plugin and not _cognitive.telegram_plugin:
        _cognitive.set_telegram(telegram_plugin)
    return _cognitive