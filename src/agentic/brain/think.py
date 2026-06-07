"""
Brain Think Module - Goal generation, belief evaluation, planning

Extracted from autonomous_brain.py for modularity.
Contains: THINK phase methods for the autonomous brain cycle.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict

logger = logging.getLogger(__name__)


class BrainThink:
    """Think phase operations for the autonomous brain."""

    def __init__(self, brain):
        self.brain = brain

    # ──────────────────────────────────────────────
    # PROPOSAL GENERATION
    # ──────────────────────────────────────────────

    async def get_proposals(self) -> List[Any]:
        """Get action proposals from SyMod"""
        from src.agentic.symod_core import SyModActionProposal

        proposals = []

        # Get available actions per plugin
        if self.brain.plugin_manager:
            for plugin_name in self.brain.plugin_manager.list_loaded():
                plugin = self.brain.plugin_manager.get_plugin(plugin_name)
                if not plugin or not getattr(plugin, 'enabled', True):
                    continue

                # Clawbr: check for pending observations and propose actions
                if plugin_name == 'clawbr' and self.brain.core:
                    pending = self.brain.core.get_memory('clawbr_pending_observations') or []
                    if pending:
                        # Clear pending observations (brain will now decide)
                        self.brain.core.save_memory('clawbr_pending_observations', [])

                        for obs in pending[:5]:  # Max 5 per cycle to avoid spam
                            if obs.get('metrics', {}).get('already_liked'):
                                continue
                            if obs.get('metrics', {}).get('already_commented') and obs.get('metrics', {}).get('already_followed'):
                                continue

                            # Propose like action
                            if not obs['metrics']['already_liked']:
                                p = SyModActionProposal(
                                    action_type='clawbr_like',
                                    target_id=obs['post_id'],
                                    target_name=obs['author'],
                                    confidence=0.6 if obs['metrics']['is_interesting'] else 0.4,
                                    justification=f"Like interesting post by {obs['author']} about AI/tech",
                                    metadata={'plugin': 'clawbr', 'post_content': obs['content']}
                                )
                                proposals.append(p)

                            # Propose comment action (lower probability)
                            if not obs['metrics']['already_commented'] and obs['metrics']['is_interesting']:
                                p = SyModActionProposal(
                                    action_type='clawbr_comment',
                                    target_id=obs['post_id'],
                                    target_name=obs['author'],
                                    confidence=0.5,
                                    justification=f"Comment on {obs['author']}'s AI-related post",
                                    metadata={'plugin': 'clawbr', 'post_content': obs['content']}
                                )
                                proposals.append(p)

                            # Propose follow action (even lower probability)
                            if not obs['metrics']['already_followed'] and obs['metrics']['is_interesting']:
                                p = SyModActionProposal(
                                    action_type='clawbr_follow',
                                    target_id=obs['author'],
                                    target_name=obs['author'],
                                    confidence=0.4,
                                    justification=f"Follow {obs['author']} for AI content",
                                    metadata={'plugin': 'clawbr'}
                                )
                                proposals.append(p)

                # Get plugin proposals from SyMod
                plugin_proposals = self.brain.symod.propose_actions(
                    plugin_name,
                    context={
                        'constraints': {
                            'max_actions': 5,  # Per plugin per cycle
                            'min_confidence': self.brain.config.min_confidence
                        }
                    },
                    available_actions=['like', 'reply', 'repost', 'follow', 'post', 'engage', 'clawbr_engage',
                                       'clawbr_like', 'clawbr_comment', 'clawbr_follow',
                                       'upvote', 'comment', 'thread', 'reply_thread', 'browse', 'listing', 'bounty', 'moltbit_post',
                                       'self_improve', 'auto_fix_error']  # Added autonomous evolution actions
                )

                # Tag with plugin name
                for p in plugin_proposals:
                    if not p.metadata:
                        p.metadata = {}
                    p.metadata['plugin'] = plugin_name

                proposals.extend(plugin_proposals)

        self.brain._apply_active_goal_bias(proposals)
        self.brain._apply_memory_shaped_ranking(proposals)
        return proposals

    # ──────────────────────────────────────────────
    # BIAS / RANKING METHODS
    # ──────────────────────────────────────────────

    def apply_meta_learning_bias(self, proposals: List[Any]) -> None:
        """Apply meta-learning: bias proposals based on which learning strategies have worked best."""
        if not proposals or not self.brain.meta_learner:
            return

        try:
            # Get best performing strategies from meta-learner
            if hasattr(self.brain.meta_learner, 'get_best_strategies'):
                best_strategies = self.brain.meta_learner.get_best_strategies(limit=3)

                for proposal in proposals:
                    action_type = str(getattr(proposal, 'action_type', '') or '')
                    domain = str((getattr(proposal, 'metadata', {}) or {}).get('plugin', 'unknown'))

                    # Check if this action aligns with successful strategies
                    for strategy in best_strategies:
                        if strategy.domain == domain or strategy.domain == 'general':
                            # Boost confidence for actions in domains with successful strategies
                            adjustment = 0.03 * strategy.success_rate
                            proposal.confidence = min(float(getattr(proposal, 'confidence', 0.0) or 0.0) + adjustment, 0.95)

                            if not getattr(proposal, 'metadata', None):
                                proposal.metadata = {}
                            proposal.metadata['meta_learning_boost'] = round(adjustment, 3)
                            proposal.metadata['strategy_id'] = strategy.id
                            break
        except Exception as e:
            logger.debug(f"Meta-learning bias error: {e}")

    def apply_transfer_learning_bias(self, proposals: List[Any]) -> None:
        """Apply transfer learning: use patterns from successful actions in other domains."""
        if not proposals or not self.brain.transfer_learner:
            return

        try:
            for proposal in proposals:
                action_type = str(getattr(proposal, 'action_type', '') or '')
                domain = str((getattr(proposal, 'metadata', {}) or {}).get('plugin', 'unknown'))

                # Find applicable patterns from other domains
                if hasattr(self.brain.transfer_learner, 'find_applicable_patterns'):
                    patterns = self.brain.transfer_learner.find_applicable_patterns(
                        domain=domain,
                        problem=action_type
                    )

                    if patterns:
                        # Boost confidence based on transferable patterns
                        pattern_boost = min(0.05, len(patterns) * 0.015)
                        proposal.confidence = min(float(getattr(proposal, 'confidence', 0.0) or 0.0) + pattern_boost, 0.95)

                        if not getattr(proposal, 'metadata', None):
                            proposal.metadata = {}
                        proposal.metadata['transfer_patterns_found'] = len(patterns)
                        proposal.metadata['transfer_boost'] = round(pattern_boost, 3)
        except Exception as e:
            logger.debug(f"Transfer learning bias error: {e}")

    def apply_active_goal_bias(self, proposals: List[Any]) -> None:
        """Lightly bias proposal confidence toward the current safe active goal."""
        if not proposals or not self.brain.goal_manager_v2 or not hasattr(self.brain.goal_manager_v2, 'get_goals'):
            return

        try:
            from src.agentic.goal_manager import GoalStatus

            active_goals = self.brain.goal_manager_v2.get_goals(status=GoalStatus.ACTIVE, limit=1)
            if not active_goals:
                return

            active_goal = active_goals[0]
            goal_text = f"{active_goal.title} {active_goal.description} {active_goal.category}".lower()
            if not self.brain.goal_manager_v2.should_auto_approve_goal(active_goal):
                return

            for proposal in proposals:
                action_blob = " ".join([
                    str(getattr(proposal, 'action_type', '') or ''),
                    str(getattr(proposal, 'target_name', '') or ''),
                    str(getattr(proposal, 'content', '') or ''),
                    str((getattr(proposal, 'metadata', {}) or {}).get('plugin', '') or ''),
                ]).lower()

                aligned = False
                if active_goal.category == 'analysis':
                    aligned = any(token in action_blob for token in ['analy', 'trend', 'report', 'insight', 'intel'])
                elif active_goal.category == 'optimization':
                    aligned = any(token in action_blob for token in ['optimiz', 'engage', 'timing', 'performance', 'improve'])

                if aligned:
                    proposal.confidence = min(float(getattr(proposal, 'confidence', 0.0) or 0.0) + 0.08, 0.95)
                    if not getattr(proposal, 'metadata', None):
                        proposal.metadata = {}
                    proposal.metadata['goal_id'] = active_goal.id
                    proposal.metadata['goal_title'] = active_goal.title
                    proposal.metadata['goal_category'] = active_goal.category
        except Exception as e:
            logger.debug(f"Could not apply active goal bias: {e}")

    def apply_active_work_item_bias(self, proposals: List[Any], active_work_items: List[Dict[str, Any]]) -> None:
        """Bias proposal confidence toward persistent meaningful work already tracked by the AGI kernel."""
        if not proposals or not active_work_items:
            return

        top_work_item = active_work_items[0]
        recommended_family = str(top_work_item.get('recommended_action_family', '') or '').lower()
        work_blob = " ".join([
            str(top_work_item.get('summary', '') or ''),
            str(top_work_item.get('type', '') or ''),
            str(top_work_item.get('topic', '') or ''),
            recommended_family,
        ]).lower()
        work_tokens = [token for token in work_blob.split() if len(token) > 3][:8]

        for proposal in proposals:
            proposal_blob = " ".join([
                str(getattr(proposal, 'action_type', '') or ''),
                str(getattr(proposal, 'target_name', '') or ''),
                str(getattr(proposal, 'content', '') or ''),
                str(getattr(proposal, 'justification', '') or ''),
                str((getattr(proposal, 'metadata', {}) or {}).get('plugin', '') or ''),
            ]).lower()

            aligned = False
            if recommended_family and recommended_family in proposal_blob:
                aligned = True
            elif any(token in proposal_blob for token in work_tokens):
                aligned = True

            if aligned:
                proposal.confidence = min(float(getattr(proposal, 'confidence', 0.0) or 0.0) + 0.1, 0.95)
                if not getattr(proposal, 'metadata', None):
                    proposal.metadata = {}
                proposal.metadata['active_work_item_id'] = top_work_item.get('id')
                proposal.metadata['active_work_item_type'] = top_work_item.get('type')
                proposal.metadata['active_work_item_summary'] = top_work_item.get('summary')
                proposal.metadata['active_work_item_family'] = recommended_family

    def apply_runtime_spine_bias(self, proposals: List[Any], spine_context: Dict[str, Any]) -> None:
        """Bias proposals toward opportunity-driven and executable meaningful work before idle exploration."""
        if not proposals or not spine_context:
            return

        meaningful_work = bool(spine_context.get('has_meaningful_work'))
        opportunity_ripe = bool(spine_context.get('opportunity_ripe'))
        security_allows = bool(spine_context.get('security_allows'))
        capability_ready = bool(spine_context.get('current_capability_ready'))
        top_work_type = str(spine_context.get('top_work_item_type', '') or '').lower()
        bounded_upgrade_candidates = spine_context.get('bounded_upgrade_candidates', []) or []

        for proposal in proposals:
            metadata = getattr(proposal, 'metadata', None) or {}
            plugin_name = str(metadata.get('plugin', '') or '').lower()
            action_type = str(getattr(proposal, 'action_type', '') or '').lower()
            blob = " ".join([plugin_name, action_type, str(getattr(proposal, 'justification', '') or '')]).lower()
            adjustment = 0.0

            if meaningful_work and capability_ready:
                if any(token in blob for token in ['engage', 'reply', 'comment', 'analy', 'report', 'trend']):
                    adjustment += 0.08
            if top_work_type == 'interaction_followup' and any(token in blob for token in ['reply', 'comment', 'engage', 'follow']):
                adjustment += 0.08
            if top_work_type == 'trend_opportunity' and any(token in blob for token in ['analy', 'post', 'trend']):
                adjustment += 0.06
            if opportunity_ripe and any(token in blob for token in ['engage', 'reply', 'analy', 'post']):
                adjustment += 0.05
            # Note: Self-improvement and auto-fix are now enabled for autonomous evolution
            # The checks below are for informational logging only - not blocking
            if not security_allows and any(token in blob for token in ['trade']):
                adjustment -= 0.05  # Small reminder for trading without security clearance
                logger.debug("🔄 Trading proposal without security_allows - logging only, not blocking")
            if any(token in blob for token in ['self_improve', 'auto_fix_error']) and not bounded_upgrade_candidates:
                adjustment += 0.1  # Boost self-improvement to encourage evolution
                logger.debug("🔄 Self-improvement/auto-fix without bounded candidates - encouraging evolution")
            # Bonus for safe exploratory actions when no specific work items
            if not meaningful_work and any(token in blob for token in ['post', 'engage', 'trend', 'analy']):
                adjustment += 0.05  # Small boost for safe idle exploration
            if any(token in blob for token in ['self_improve']) and bounded_upgrade_candidates:
                adjustment += 0.06

            if adjustment != 0.0:
                proposal.confidence = min(max(float(getattr(proposal, 'confidence', 0.0) or 0.0) + adjustment, 0.0), 0.95)

            if not getattr(proposal, 'metadata', None):
                proposal.metadata = {}
            proposal.metadata['spine_context'] = spine_context
            proposal.metadata['spine_bias_applied'] = round(adjustment, 3)

    def apply_cognitive_bias(self, proposals: List[Any]) -> None:
        """Apply BeliefEngine + SelfModel confidence adjustments.

        Replaces the old +0.03/+0.05 heuristic biases with real experience-driven
        confidence from BeliefEngine predictions and SelfModel capability tracking.
        """
        if not proposals:
            return

        for proposal in proposals:
            metadata = getattr(proposal, 'metadata', None) or {}
            domain = str(metadata.get('plugin', 'unknown')).lower()
            action_type = str(getattr(proposal, 'action_type', '') or '').lower()
            action_key = f"{domain}:{action_type}"

            try:
                prediction = self.brain.cognitive.predict_action_outcome(action_key, domain)
                predicted_success = prediction.get('predicted_success', 0.5)

                should_attempt, reason = prediction.get('should_attempt', True), prediction.get('attempt_reason', '')
                should_wait, wait_reason = prediction.get('should_wait', False), prediction.get('wait_reason', '')

                current_confidence = float(getattr(proposal, 'confidence', 0.5) or 0.5)

                if should_wait:
                    current_confidence *= 0.6
                    if not getattr(proposal, 'metadata', None):
                        proposal.metadata = {}
                    proposal.metadata['cognitive_wait'] = wait_reason

                if not should_attempt:
                    current_confidence *= 0.4
                    if not getattr(proposal, 'metadata', None):
                        proposal.metadata = {}
                    proposal.metadata['cognitive_avoid'] = reason

                belief_delta = (predicted_success - 0.5) * 0.5
                current_confidence = max(0.05, min(0.95, current_confidence + belief_delta))

                proposal.confidence = current_confidence

                if not getattr(proposal, 'metadata', None):
                    proposal.metadata = {}
                proposal.metadata['cognitive_prediction'] = round(predicted_success, 3)
                proposal.metadata['cognitive_bias_applied'] = round(belief_delta, 3)

            except Exception as e:
                logger.debug(f"Cognitive bias error for {action_key}: {e}")

    def prioritize_runtime_spine_proposals(self, proposals: List[Any], spine_context: Dict[str, Any]) -> List[Any]:
        """Sort proposals so discovered opportunity and executable work outrank idle exploratory behavior."""
        if not proposals:
            return proposals

        meaningful_work = bool(spine_context.get('has_meaningful_work'))
        capability_ready = bool(spine_context.get('current_capability_ready'))
        security_allows = bool(spine_context.get('security_allows'))
        bounded_upgrade_candidates = spine_context.get('bounded_upgrade_candidates', []) or []

        def proposal_rank(proposal: Any):
            metadata = getattr(proposal, 'metadata', None) or {}
            action_type = str(getattr(proposal, 'action_type', '') or '').lower()
            plugin_name = str(metadata.get('plugin', '') or '').lower()
            blob = f"{plugin_name} {action_type} {getattr(proposal, 'justification', '')}".lower()

            # Note: Self-improvement and auto-fix are now enabled
            # Category assignment is for ranking, not blocking
            category = 0
            if meaningful_work and capability_ready and any(token in blob for token in ['reply', 'comment', 'engage', 'analy', 'trend', 'report']):
                category = 4
            elif any(token in blob for token in ['reply', 'comment', 'engage']):
                category = 3
            elif any(token in blob for token in ['analy', 'trend', 'post']):
                category = 2
            elif any(token in blob for token in ['self_improve', 'auto_fix_error']):
                category = 1  # Promoted from negative - now encouraged
            elif any(token in blob for token in ['trade']):
                category = 1  # Promoted - trading enabled

            return (category, float(getattr(proposal, 'confidence', 0.0) or 0.0))

        return sorted(proposals, key=proposal_rank, reverse=True)

    # ──────────────────────────────────────────────
    # AGI ORCHESTRATION
    # ──────────────────────────────────────────────

    async def run_agi_orchestration_cycle(self) -> List[Any]:
        """Run AGI Orchestrator cycle and convert results to action proposals"""
        if not self.brain.agi_orchestrator:
            return []

        try:
            # Run full AGI cycle
            cycle_result = await self.brain.agi_orchestrator.run_cycle(trigger="brain_cycle")

            # Check if cycle was successful (AGICycleResult doesn't have success attribute)
            # Success is determined by having phases executed and not just early termination
            cycle_successful = (
                hasattr(cycle_result, 'phases_executed') and
                len(cycle_result.phases_executed) > 0 and
                not any(phase.output.get('error') for phase in cycle_result.phases_executed if hasattr(phase, 'output'))
            )

            if not cycle_successful:
                logger.info("🎭 AGI Orchestrator: No actionable insights this cycle")
                return []

            # Convert AGI actions to SyMod proposals
            proposals = []

            # Process final action if present
            if cycle_result.final_action and cycle_result.final_action.get('action_taken'):
                proposal = await self.convert_agi_action_to_proposal(
                    cycle_result.final_action,
                    cycle_result.phases_executed
                )
                if proposal:
                    proposals.append(proposal)

            # Process creative content generation (common AGI output)
            for phase_result in cycle_result.phases_executed:
                if (phase_result.phase.value == 'CREATIVE_GENERATION' and
                    phase_result.success and phase_result.output):

                    creative_proposals = await self.extract_creative_proposals(
                        phase_result.output, cycle_result.phases_executed
                    )
                    proposals.extend(creative_proposals)

            logger.info(f"🎭 AGI Orchestrator generated {len(proposals)} action proposals")
            return proposals

        except Exception as e:
            logger.error(f"❌ AGI Orchestration error: {e}")
            return []

    # ──────────────────────────────────────────────
    # THINK PHASE: PROPOSAL ASSEMBLY
    # ──────────────────────────────────────────────

    async def phase_assemble_proposals(self, agi_kernel, agi_actions, active_work_items, spine_context, memory_proposals=None, revenue_proposals=None, curiosity_proposals=None, intent_proposals=None):
        """THINK phase — assemble, enrich, and rank all action proposals.

        Priority order: curiosity > persistent intents > memory-driven > goal-driven > SyMod > AGI
        Curiosity and intents come first so self-directed exploration outranks reactive work.
        """
        # Get goal-driven action from active autonomous goals
        goal_driven_action = None
        if agi_kernel and hasattr(agi_kernel, 'goal_manager'):
            goal_manager = agi_kernel.goal_manager

            # AutonomousGoalManager.get_next_action() pulls from v2 GoalManager
            # Returns a dict with plugin, action_type, params, etc.
            if hasattr(goal_manager, 'get_next_action'):
                try:
                    na = goal_manager.get_next_action()
                    if na and isinstance(na, dict):
                        goal_driven_action = na
                        logger.info(f"🎯 Goal-driven action: {na.get('action_type', '?')} via {na.get('plugin', '?')}")
                except Exception as e2:
                    logger.debug(f"get_next_action failed: {e2}")

            if not goal_driven_action and hasattr(goal_manager, 'get_active_goals'):
                # Fallback: iterate active goals and get first actionable one
                active_goal_dicts = goal_manager.get_active_goals()
                if active_goal_dicts:
                    logger.info(f"🎯 Found {len(active_goal_dicts)} active goals (dicts)")
                    for g in active_goal_dicts[:3]:
                        gid = g.get('id') or g.get('_id')
                        if gid and hasattr(goal_manager, 'get_next_action'):
                            try:
                                na = goal_manager.get_next_action()
                                if na and isinstance(na, dict):
                                    goal_driven_action = na
                                    logger.info(f"🎯 Goal-driven action from dict goal: {na.get('action_type', '?')}")
                                    break
                            except Exception:
                                pass

        # Combine SyMod + AGI proposals
        proposals = await self.brain._get_proposals()
        proposals.extend(agi_actions)

        # PREPEND revenue proposals (profit opportunities > everything except curiosity)
        if revenue_proposals:
            proposals = revenue_proposals + proposals
        # PREPEND curiosity proposals (self-directed exploration > reactive work)
        if curiosity_proposals:
            proposals = curiosity_proposals + proposals
        # THEN persistent intents (long-running objectives)
        if intent_proposals:
            proposals = intent_proposals + proposals
        # THEN memory-driven proposals (semantic recall)
        if memory_proposals:
            proposals = memory_proposals + proposals

        # Inject goal-driven action as high-priority proposal
        if goal_driven_action:
            from src.agentic.symod_core import SyModActionProposal
            goal_proposal = SyModActionProposal(
                action_type=goal_driven_action.get('action_type', 'unknown'),
                target_id=goal_driven_action.get('params', {}).get('target_id'),
                target_name=goal_driven_action.get('goal_description', 'Goal-driven action'),
                confidence=0.85,
                justification=f"Pursuing active goal: {goal_driven_action.get('goal_description', 'N/A')}",
                metadata={
                    'plugin': goal_driven_action.get('plugin', 'unknown'),
                    'goal_driven': True,
                    'goal_id': goal_driven_action.get('goal_id'),
                    'step': goal_driven_action.get('step'),
                    'total_steps': goal_driven_action.get('total_steps'),
                    'origin': goal_driven_action.get('origin', 'autonomous'),
                }
            )
            proposals.insert(0, goal_proposal)
            logger.info("🎯 Goal-driven action added to proposals with high priority")

        # Apply learning biases and rank
        self.brain._apply_meta_learning_bias(proposals)
        self.brain._apply_transfer_learning_bias(proposals)
        self.brain._apply_active_work_item_bias(proposals, active_work_items)
        self.brain._apply_runtime_spine_bias(proposals, spine_context)
        self.brain._apply_cognitive_bias(proposals)
        proposals = self.brain._prioritize_runtime_spine_proposals(proposals, spine_context)
        logger.info(f"🧠 Generated {len(proposals)} total proposals (AGI learning applied)")

        return proposals

    # ──────────────────────────────────────────────
    # THINK PHASE: MEMORY-DRIVEN THINKING
    # ──────────────────────────────────────────────

    async def phase_memory_driven_thinking(self, observations: List, agi_kernel=None) -> List:
        """Memory-First Thinking: Query semantic memory to generate action proposals.

        Before calling any LLM, retrieve semantically similar past experiences
        from memory and use them to seed action proposals with confidence based
        on what worked/failed before.
        """
        from src.agentic.symod_core import SyModActionProposal

        memory_proposals = []

        if not observations:
            return memory_proposals

        # Build a memory query from current observations
        obs_texts = []
        for obs in observations:
            data = getattr(obs, 'data', obs) if isinstance(obs, dict) else getattr(obs, 'data', {})
            if isinstance(data, dict):
                content = data.get('content', '') or data.get('description', '') or ''
                if content:
                    obs_texts.append(content)

        if not obs_texts:
            return memory_proposals

        memory_query = " ".join(obs_texts[:5])[:500]

        # Query semantic memory via SQLiteMemorySystem
        sqlite_memory = None
        if agi_kernel:
            sqlite_memory = getattr(agi_kernel, 'memory', None) or getattr(agi_kernel, 'sqlite_memory', None)
        if not sqlite_memory and hasattr(self.brain, 'agi_kernel') and self.brain.agi_kernel:
            sqlite_memory = getattr(self.brain.agi_kernel, 'memory', None) or getattr(self.brain.agi_kernel, 'sqlite_memory', None)

        if not sqlite_memory or not hasattr(sqlite_memory, 'search_memories'):
            return memory_proposals

        try:
            similar_memories = sqlite_memory.search_memories(
                query=memory_query,
                k=5,
                min_relevance=0.35
            )
        except Exception as e:
            logger.debug(f"Memory-driven thinking semantic search failed: {e}")
            return memory_proposals

        if not similar_memories:
            return memory_proposals

        # Ask BeliefEngine what it thinks about these memory-driven actions
        belief_engine = None
        if hasattr(self.brain, 'cognitive') and self.brain.cognitive:
            belief_engine = getattr(self.brain.cognitive, 'belief_engine', None)

        seen_actions = set()

        for mem in similar_memories:
            meta = mem.get('metadata', {}) or {}
            content = mem.get('content', '') or ''
            relevance = mem.get('relevance_score', 0.0)
            memory_type = mem.get('memory_type', 'interaction')

            # Determine what action type this memory suggests
            suggested_action = meta.get('action_type', '') or meta.get('plugin', '') or ''
            plugin_name = meta.get('plugin', '')
            if not plugin_name:
                # Try to infer from memory type
                if 'post' in content.lower() or 'content' in memory_type:
                    plugin_name = 'moltx'
                    suggested_action = 'post'
                elif 'reply' in content.lower() or 'comment' in memory_type:
                    plugin_name = 'clawbr'
                    suggested_action = 'reply'
                elif 'trade' in content.lower() or memory_type == 'on_chain_event':
                    plugin_name = 'onchain'
                    suggested_action = 'analyze'
                else:
                    plugin_name = 'general'
                    suggested_action = 'engage'

            if not suggested_action:
                suggested_action = 'engage'

            action_key = f"{plugin_name}:{suggested_action}"
            if action_key in seen_actions:
                continue
            seen_actions.add(action_key)

            # Use BeliefEngine for confidence if available
            base_confidence = 0.4 + (relevance * 0.3)
            if belief_engine and hasattr(belief_engine, 'predict'):
                try:
                    prediction = belief_engine.predict(suggested_action, plugin_name)
                    if prediction.relevant_beliefs:
                        base_confidence = max(base_confidence, prediction.predicted_success * 0.8)
                except Exception as e:
                    logger.debug("Non-critical error: %s", e)
            justification = f"Memory suggests: {'; '.join(content.split('.')[:2])}" if content else f"From similar past {memory_type}"

            proposal = SyModActionProposal(
                action_type=suggested_action,
                target_name=meta.get('target_name', '') or meta.get('author', '') or '',
                confidence=min(base_confidence, 0.9),
                justification=justification,
                metadata={
                    'plugin': plugin_name,
                    'memory_driven': True,
                    'memory_id': mem.get('id', ''),
                    'memory_relevance': round(relevance, 3),
                    'source_memory': 'semantic',
                    'origin': 'memory_first',
                }
            )
            memory_proposals.append(proposal)

        return memory_proposals

    # ──────────────────────────────────────────────
    # THINK PHASE: CURIOSITY GOALS
    # ──────────────────────────────────────────────

    async def phase_curiosity_goals(self, agi_kernel) -> List:
        """THINK phase — generate curiosity-driven proposals before SyMod/LLM.

        Checks for knowledge gaps and generates self-directed exploration proposals.
        These run BEFORE the main proposal assembly so they can outrank work items.
        Returns a list of curiosity proposals to prepend.
        """
        curiosity_proposals = []
        try:
            cycle_count = self.brain.stats.get('cycles_completed', 0)

            curiosity_goals = self.brain.cognitive.get_curiosity_goals()

            if cycle_count > 0 and cycle_count % 10 == 0:
                reflection = self.brain.cognitive.reflect()
                reflection_goals = self.brain.cognitive.generate_reflection_curiosity_goals(reflection)
                curiosity_goals.extend(reflection_goals)

            if not curiosity_goals:
                return curiosity_proposals

            for cgoal in curiosity_goals:
                try:
                    plan = self.brain.cognitive.goal_planner.decompose_goal(
                        goal=cgoal.title,
                        domain=cgoal.domain,
                        belief_engine=self.brain.cognitive.belief_engine,
                        self_model=self.brain.cognitive.self_model,
                        priority=cgoal.priority,
                    )
                    plan.source = cgoal.source

                    logger.info(
                        f"🧭 Curiosity goal: {cgoal.title[:50]} "
                        f"(domain={cgoal.domain}, priority={cgoal.priority:.2f}, "
                        f"info_gain={cgoal.information_gain_score:.2f})"
                    )

                    from src.agentic.symod_core import SyModActionProposal
                    next_step = self.brain.cognitive.goal_planner.get_next_step(plan)
                    if next_step:
                        implemented = self.brain._is_action_implemented(next_step.plugin, next_step.action)
                        if not implemented:
                            logger.info(f"⚠️ Action {next_step.plugin}.{next_step.action} not in ACTION_MAP — allowing with reduced confidence")
                            # Don't skip — let it reach the action router which will fail gracefully
                            # Lower confidence so it doesn't outrank implemented actions
                            confidence_mult = 0.4
                        else:
                            confidence_mult = 1.0
                        proposal = SyModActionProposal(
                            action_type=next_step.action,
                            target_id=cgoal.domain,
                            target_name=cgoal.title,
                            confidence=next_step.confidence * cgoal.priority * confidence_mult,
                            justification=f"Curiosity-driven exploration (info_gain={cgoal.information_gain_score:.2f}){' — action not yet implemented' if not implemented else ''}",
                            metadata={
                                'plugin': next_step.plugin,
                                'curiosity_goal': True,
                                'goal_id': cgoal.goal_id,
                                'plan_id': plan.id,
                                'information_gain': cgoal.information_gain_score,
                                'novelty': cgoal.novelty_score,
                                'skill_gap': cgoal.skill_gap_score,
                                'action_implemented': implemented,
                            }
                        )
                        curiosity_proposals.append(proposal)

                except Exception as e:
                    logger.debug(f"Curiosity goal planning error for '{cgoal.title}': {e}")

        except Exception as e:
            logger.debug(f"Curiosity goals phase error: {e}")

        if curiosity_proposals:
            logger.info(f"🧭 Generated {len(curiosity_proposals)} curiosity-driven proposals (before SyMod)")
        return curiosity_proposals

    # ──────────────────────────────────────────────
    # THINK PHASE: PERSISTENT INTENTS
    # ──────────────────────────────────────────────

    async def phase_maintain_persistent_intents(self, agi_kernel) -> List:
        """Phase 3.1 — Check persistent intents and generate advancement actions.

        Unlike goals (discrete outcomes), intents are long-running objectives
        that generate multiple actions over days/weeks.
        Returns intent proposals to be included in the main proposal list.
        """
        intent_proposals = []
        from src.agentic.persistent_intent import get_persistent_intent_manager

        try:
            intent_mgr = get_persistent_intent_manager()
            ready_intents = intent_mgr.get_ready_intents()

            if not ready_intents:
                return intent_proposals

            logger.info(f"🎯 {len(ready_intents)} persistent intents ready for action")

            for intent in ready_intents[:2]:
                action = intent_mgr.generate_action_for_intent(intent)

                if action:
                    from src.agentic.symod_core import SyModActionProposal
                    intent_proposal = SyModActionProposal(
                        action_type=action['action_type'],
                        target_id=intent.id,
                        target_name=intent.objective[:50],
                        content=action.get('description', ''),
                        justification=f"Advance persistent intent: {intent.objective[:60]}...",
                        confidence=0.7,
                        metadata={
                            'plugin': self.brain._map_intent_action_to_plugin(action['action_type']),
                            'intent_id': intent.id,
                            'intent_objective': intent.objective,
                            'step_description': action['description'],
                            'source': 'persistent_intent',
                            'intent_priority': intent.priority,
                            'progress_percent': intent.progress_percent,
                        },
                    )

                    intent_proposals.append(intent_proposal)
                    logger.info(f"   📋 Intent action queued: {action['description'][:50]}...")

                    intent_mgr.record_intent_action(
                        intent_id=intent.id,
                        action_description=action['description'],
                        success=False
                    )

        except Exception as e:
            logger.debug(f"Persistent intent processing error: {e}")

        return intent_proposals

    # ──────────────────────────────────────────────
    # THINK PHASE: CROSS-DOMAIN SYNTHESIS & PLANNING
    # ──────────────────────────────────────────────

    async def phase_cross_domain_synthesis_and_planning(
        self,
        agi_kernel,
        observations,
        proposals,
    ) -> None:
        """
        Phase 4.1-4.2 — Cross-domain synthesis and strategic planning.

        Detects patterns across market, social, content domains and
        advances multi-day strategic plans.
        """
        try:
            from src.agentic.cross_domain_synthesis import get_cross_domain_synthesizer
            from src.agentic.strategic_planner import get_strategic_planner

            # 4.1: Cross-domain synthesis
            synthesizer = get_cross_domain_synthesizer()

            # Build market and social state from observations
            market_state = self.brain._extract_market_state(observations)
            social_state = self.brain._extract_social_state(observations)

            # Run synthesis via orchestrator
            if agi_kernel and hasattr(agi_kernel, 'orchestrator'):
                opportunities = agi_kernel.orchestrator.synthesize_cross_domain_opportunities(
                    observations, market_state, social_state
                )

                for opp in opportunities:
                    # Convert to proposal
                    cross_domain_proposal = {
                        'plugin': self.brain._map_intent_action_to_plugin(opp['proposed_action']),
                        'action_type': opp['proposed_action'],
                        'params': {
                            'description': opp['description'],
                            'source': 'cross_domain_synthesis',
                            'domains': opp.get('source_domains', []),
                        },
                        'context': {
                            'source': 'cross_domain_synthesis',
                            'goal_description': f"Cross-domain: {opp['title']}",
                            'impact': 'high',
                            'risk_level': 'low',
                            'objective_alignment': opp.get('objective_alignment', 0.5),
                            'cross_domain_score': opp.get('cross_domain_score', 0.6),
                        },
                        'confidence': opp.get('cross_domain_score', 0.6),
                        'description': opp['description'],
                    }

                    proposals.append(cross_domain_proposal)
                    logger.info(f"   🔮 Cross-domain opportunity: {opp['title'][:50]}...")

            # 4.2: Strategic planning
            planner = get_strategic_planner()

            # Advance plan if needed (check daily)
            current_plan = planner.get_current_plan()
            if not current_plan:
                # Create initial plan
                from src.agentic.owner_objectives import get_owner_objectives_manager
                objectives_mgr = get_owner_objectives_manager()
                objectives = objectives_mgr.get_active_objectives()

                plan = planner.create_plan(
                    plan_type='growth',
                    owner_objectives=[o.to_dict() for o in objectives],
                )
                if plan:
                    logger.info(f"📋 Strategic plan created: {plan.title}")
            else:
                # Check if we need to advance to next cycle
                days_elapsed = (datetime.now() - current_plan.created_at).days
                if days_elapsed >= current_plan.horizon_days:
                    new_plan = planner.advance_plan()
                    if new_plan:
                        logger.info(f"📋 Advanced to new strategic plan: {new_plan.title}")

        except Exception as e:
            logger.debug(f"Cross-domain synthesis error: {e}")

    # ──────────────────────────────────────────────
    # THINK PHASE: GOAL MANAGEMENT
    # ──────────────────────────────────────────────

    def phase_goal_management(self, agi_kernel, observations):
        """THINK sub-phase — goal generation, approval, and activation.

        Returns the next planned action (or None) for use in the ACT phase.
        """
        next_action = None

        # Phase 2.1: Proactive goal generation via orchestrator
        if agi_kernel and hasattr(agi_kernel, 'orchestrator'):
            try:
                orchestrator = agi_kernel.orchestrator
                if orchestrator and hasattr(orchestrator, 'generate_goal_proposals'):
                    proactive_proposals = orchestrator.generate_goal_proposals(observations)
                    for proposal in proactive_proposals[:2]:  # Top 2 proposals
                        # Convert to Goal and add to manager
                        from src.agentic.goal_manager import Goal, GoalPriority
                        goal = Goal(
                            id=proposal['id'],
                            title=proposal['title'],
                            description=proposal['description'],
                            category=proposal['category'],
                            priority=GoalPriority.MEDIUM if proposal.get('priority', 5) <= 5 else GoalPriority.HIGH,
                            impact_score=float(proposal.get('priority', 5)),
                            effort_estimate='hours',
                            confidence=proposal.get('objective_alignment', 0.5),
                            trigger_type=proposal.get('rationale', 'proactive_generation'),
                            trigger_data={
                                'source': 'orchestrator_generate_goal_proposals',
                                'proposed_action': proposal.get('proposed_action'),
                                'evidence': proposal.get('evidence', []),
                            },
                            evidence=proposal.get('evidence', []),
                        )
                        # Add evidence for bounded upgrades if skill-related
                        if proposal.get('bounded_upgrade_evidence'):
                            goal.trigger_data['bounded_upgrade_evidence'] = True

                        if self.brain.goal_manager_v2:
                            if self.brain.goal_manager_v2.add_goal(goal):
                                logger.info(f"🎯 Proactive goal added: {goal.title[:50]}...")
            except Exception as e:
                logger.debug(f"Proactive goal generation error: {e}")

        # Hierarchical goals + planner
        if self.brain.goal_hierarchy and self.brain.planner:
            actionable_goals = self.brain.goal_hierarchy.get_actionable_goals()
            logger.info(f"🎯 {len(actionable_goals)} actionable goals")
            next_action = self.brain.planner.get_next_action()
            if next_action:
                logger.info(f"⚡ Next planned action: {next_action.description}")

        # Autonomous goal generation (legacy)
        if agi_kernel and hasattr(agi_kernel, 'goal_manager'):
            try:
                goal_manager = agi_kernel.goal_manager
                if goal_manager and hasattr(goal_manager, 'scan_and_generate'):
                    onchain_plugin = self.brain.plugin_manager.get_plugin('onchain') if self.brain.plugin_manager else None
                    new_autonomous_goals = goal_manager.scan_and_generate(onchain_plugin=onchain_plugin)
                    if new_autonomous_goals:
                        logger.info(f"🎯 Generated {len(new_autonomous_goals)} autonomous goals from observations")
                        for goal in new_autonomous_goals:
                            if goal.priority_score >= 8.0:
                                goal_manager.approve_goal(goal.id)
                                logger.info(f"✅ Auto-activated high-priority goal: {goal.description}")
            except Exception as e:
                logger.debug(f"Autonomous goal generation error: {e}")

        # Self-directed goals from goal stack
        if hasattr(self.brain, 'goal_stack') and self.brain.goal_stack and self.brain.cross_platform_intel:
            new_goals = self.brain.goal_stack.auto_add_proposed_goals(
                observations, self.brain.cross_platform_intel, max_new_goals=2
            )
            if new_goals > 0:
                logger.info(f"🎯 Self-proposed {new_goals} new goals")

        # GoalManager v2: auto-approve and activate safe goals
        if self.brain.goal_manager_v2:
            try:
                from src.agentic.goal_manager import GoalStatus
                proposed_goals = self.brain.goal_manager_v2.get_goals(status=GoalStatus.PROPOSED, limit=5)
                for goal in proposed_goals:
                    # Phase 1.3: Auto-approve safe goals (LOW/MEDIUM priority, low risk)
                    if self.brain.goal_manager_v2.maybe_auto_approve_goal(goal.id):
                        logger.info(f"🤖 Auto-approved safe goal: {goal.title} ({goal.priority.name})")

                if hasattr(self.brain.goal_manager_v2, 'start_next_safe_goal'):
                    started_goal = self.brain.goal_manager_v2.start_next_safe_goal()
                    if started_goal:
                        logger.info(f"🚀 Runtime picked up safe goal: {started_goal.id} - {started_goal.title}")
                        telegram = self.brain.plugin_manager.get_plugin('telegram') if self.brain.plugin_manager else None
                        if telegram and hasattr(telegram, 'notify_autonomous_activity'):
                            telegram.notify_autonomous_activity(
                                'runtime_goal_pickup',
                                f"Picked up safe approved goal `{started_goal.id}`: {started_goal.title[:120]}"
                            )
            except Exception as e:
                logger.debug(f"Goal manager v2 activation error: {e}")

        # Goal hierarchy conflict detection and resolution
        if self.brain.goal_hierarchy:
            try:
                conflicts = self.brain.goal_hierarchy.detect_conflicts()
                if conflicts:
                    logger.info(f"⚠️ Detected {len(conflicts)} goal conflicts")
                    for conflict in conflicts:
                        logger.info(f"   ⚠️ {conflict['description']} (severity: {conflict['severity']})")
                    paused = self.brain.goal_hierarchy.resolve_conflicts(conflicts)
                    if paused:
                        logger.info(f"⏸️ Auto-paused {len(paused)} conflicting goals")
            except Exception as e:
                logger.debug(f"Goal conflict resolution error: {e}")

        return next_action

    # ──────────────────────────────────────────────
    # THINK PHASE: PERIODIC REFLECTION
    # ──────────────────────────────────────────────

    async def phase_periodic_reflection(self, agi_kernel):
        """THINK sub-phase — periodic reflection using real cognitive data.

        Uses BeliefEngine calibration and SelfModel capabilities instead of
        Duat/Synergy float arithmetic. Every 10 cycles: cognitive reflection.
        Every 50 cycles: performance optimization. Every 100 cycles: deep review.
        """
        cycle_count = self.brain.stats.get('cycles_completed', 0)

        # Cognitive reflection (every 10 cycles — lightweight)
        if cycle_count > 0 and cycle_count % 10 == 0:
            try:
                reflection = self.brain.cognitive.reflect()
                assessment = reflection.get('overall_assessment', 'unknown')
                strengths = reflection.get('strengths', [])
                weaknesses = reflection.get('weaknesses', [])
                learn = reflection.get('learning_priorities', [])
                rec = reflection.get('recommendation', '')

                logger.info(f"🧠 Cognitive reflection (cycle {cycle_count}):")
                logger.info(f"   Assessment: {assessment}")
                logger.info(f"   Recommendation: {rec}")
                if strengths:
                    logger.info(f"   ✅ Strengths: {', '.join(s['domain'] for s in strengths[:3])}")
                if weaknesses:
                    logger.info(f"   ⚠️ Weaknesses: {', '.join(w['domain'] + '.' + w['action_type'] for w in weaknesses[:3])}")
                if learn:
                    logger.info(f"   📚 Learning priorities: {', '.join(l['domain'] + '.' + l['action_type'] for l in learn[:3])}")

                self.brain.learning_priorities = learn
                self.brain.capability_strengths = strengths
                self.brain.capability_weaknesses = weaknesses

            except Exception as e:
                logger.debug(f"Cognitive reflection error: {e}")

        # Deep meta-cognition review (every 100 cycles)
        if cycle_count > 0 and cycle_count % 100 == 0:
            try:
                logger.info("🧠 === DEEP COGNITIVE REVIEW ===")
                calibration = self.brain.cognitive.get_belief_calibration()
                self_report = self.brain.cognitive.get_self_awareness_report()
                domain_strengths = self.brain.cognitive.get_domain_strengths()

                logger.info(f"   Belief calibration: error={calibration.get('mean_absolute_error', '?')}, "
                             f"calibrated={calibration.get('calibrated', '?')}")
                logger.info(f"   Domain knowledge: {len(domain_strengths)} domains tracked")
                logger.info(f"   Self-model: {self_report.get('recommendation', 'no recommendation')}")

                if calibration.get('overconfident_domains'):
                    logger.info(f"   ⚠️ Overconfident in: {', '.join(calibration['overconfident_domains'])}")
                if calibration.get('underconfident_domains'):
                    logger.info(f"   📈 Underconfident in: {', '.join(calibration['underconfident_domains'])}")

                # Phase 3.2: Curiosity report during deep review
                try:
                    curiosity_report = self.brain.cognitive.get_curiosity_report()
                    logger.info(f"   🧭 Curiosity: {curiosity_report.get('total_curiosity_goals', 0)} goals, "
                                f"{curiosity_report.get('attempted_goals', 0)} attempted, "
                                f"{curiosity_report.get('successful_goals', 0)} successful, "
                                f"avg reward={curiosity_report.get('avg_intrinsic_reward', 0):.3f}")
                    gaps = curiosity_report.get('knowledge_gaps', [])
                    if gaps:
                        logger.info(f"   📚 Knowledge gaps: {', '.join(g['domain'] + ':' + g['type'] for g in gaps[:3])}")
                except Exception as e:
                    logger.debug("Non-critical error: %s", e)
                if hasattr(agi_kernel, 'goal_manager') and self_report.get('learning_priorities'):
                    from src.agentic.goal_manager import Goal, GoalPriority
                    for lp in self_report['learning_priorities'][:2]:
                        new_goal = Goal(
                            id=f"cog_learn_{int(datetime.now().timestamp())}_{lp['domain']}",
                            title=f"Build capability: {lp['domain']}.{lp['action_type']}",
                            description=f"Low data ({lp['sample_size']} attempts) in {lp['domain']}.{lp['action_type']}. "
                                        f"Reason: {lp['reason']}. Current success rate: {lp.get('success_rate', 'unknown')}",
                            category=lp['domain'],
                            priority=GoalPriority.MEDIUM,
                            impact_score=0.6,
                            effort_estimate='hours',
                            confidence=0.7,
                            trigger_type='cognitive_reflection',
                            evidence=[f"Self-model assessment: {lp['reason']}"],
                        )
                        try:
                            if await agi_kernel.goal_manager.aadd_goal(new_goal):
                                logger.info(f"   ✅ Learning goal created: {new_goal.id}")
                        except Exception as e:
                            logger.debug("Non-critical error: %s", e)
            except Exception as e:
                logger.debug(f"Deep cognitive review error: {e}")

        # 7.5: Reflection depth control - adversarial every 1000 cycles
        if cycle_count > 0 and cycle_count % 1000 == 0:
            try:
                logger.info("🧠 === ADVERSARIAL SELF-CRITIQUE (1000 cycles) ===")
                # Challenge own beliefs - look for disconfirming evidence
                adversarial_findings = await self.brain._adversarial_self_critique(agi_kernel)

                if adversarial_findings:
                    logger.info(f"   🔍 Found {len(adversarial_findings)} beliefs to challenge")
                    for finding in adversarial_findings[:5]:
                        logger.info(f"   ⚠️ {finding['belief'][:60]}... => {finding['challenge']}")
                else:
                    logger.info("   ✅ No significant belief challenges found")

                # Store findings in beliefs
                try:
                    from src.agentic.belief_engine import get_belief_engine
                    be = get_belief_engine()
                    if be and adversarial_findings:
                        for f in adversarial_findings[:3]:
                            be.add_belief(
                                predicate=f"adversarial_challenge_{f['belief'][:30]}",
                                confidence=0.7,
                                domain="metacognition",
                                evidence=[f"Challenge: {f['challenge']}", f"Strength: {f.get('strength', 'unknown')}"],
                                source="adversarial_reflection"
                            )
                except Exception as e:
                    logger.debug("Non-critical error: %s", e)
            except Exception as e:
                logger.debug(f"Adversarial self-critique error: {e}")

        # Performance optimization (every 50 cycles)
        if cycle_count > 0 and cycle_count % 50 == 0:
            if agi_kernel and hasattr(agi_kernel, 'performance_optimizer'):
                try:
                    from src.agentic.action_logger import get_action_logger
                    action_logger = get_action_logger()

                    recent_actions = await action_logger.aget_recent_outcomes(limit=100)
                    action_types = {}
                    for action in recent_actions:
                        at = action.get('action_type', 'unknown')
                        plugin = action.get('plugin', '')
                        full_type = f"{plugin}:{at}" if plugin else at
                        action_types[full_type] = action_types.get(full_type, 0) + 1

                    top_actions = sorted(action_types.items(), key=lambda x: x[1], reverse=True)[:3]
                    for action_type, count in top_actions:
                        metrics = agi_kernel.performance_optimizer.analyze_action_type(action_type, action_logger)
                        if metrics:
                            logger.info(f"📊 Performance: {action_type} — {metrics.success_rate:.1%} ({metrics.avg_duration_ms:.0f}ms)")
                            optimizations = agi_kernel.performance_optimizer.generate_optimizations(metrics)
                            if optimizations:
                                top_opt = max(optimizations, key=lambda o: o.priority)
                                logger.info(f"   🔧 Top optimization: {top_opt.recommendation}")
                except Exception as e:
                    logger.debug(f"Performance optimization error: {e}")

        # Self-directed architecture modification (every 200 cycles)
        if cycle_count > 0 and cycle_count % 200 == 0:
            try:
                config_changes = self.brain._propose_architecture_changes()
                if config_changes:
                    logger.info(f"🔧 Proposed {len(config_changes)} architecture changes")
                    for change in config_changes:
                        logger.info(f"   ⚙️ {change}")
            except Exception as e:
                logger.debug(f"Architecture modification error: {e}")

    # ──────────────────────────────────────────────
    # IDLE STATE HANDLING
    # ──────────────────────────────────────────────

    def handle_idle_state(self, active_work_items: List[Dict[str, Any]], proposals: List[Any], spine_context: Dict[str, Any]) -> List[Any]:
        """Handle idle state by generating diverse exploratory proposals from 336+ available commands.

        Cycles through command categories to ensure variety:
        - Analysis/Research (market trends, sentiment, platform stats)
        - Content Creation (intelligent posts, articles, threads)
        - Social Engagement (replies, debates, follows)
        - System Health (monitoring, diagnostics, optimization)
        - Trading/Market (if enabled via domain autonomy)
        - Self-Improvement (auto-fix, skill building if evidence exists)

        Security: Only generates safe actions with proper gating.
        """
        # First log the idle reason for transparency
        if not active_work_items:
            logger.info("🛌 Idle: no meaningful work items - generating diverse exploratory proposals")
        elif proposals and all(float(getattr(p, 'confidence', 0.0) or 0.0) < self.brain.config.min_confidence for p in proposals):
            logger.info("🛌 Idle: proposals below confidence threshold - will attempt diverse exploration")
        else:
            logger.info("🛌 Idle: no actions executed - attempting diverse exploration")

        # Generate diverse exploratory proposals
        exploratory_proposals = []

        # Only add exploratory actions if we haven't hit hourly limits
        if self.brain._actions_this_hour >= self.brain.config.max_actions_per_hour:
            return exploratory_proposals

        from src.agentic.symod_core import SyModActionProposal

        # Get cycle counter for rotating through categories
        cycle_count = self.brain.stats.get('cycles_completed', 0)

        # === CATEGORY 1: ANALYSIS & RESEARCH (Every 2nd cycle) ===
        if cycle_count % 2 == 0:
            # Market/Trending analysis
            moltx = self.brain.plugin_manager.get_plugin('moltx') if self.brain.plugin_manager else None
            if moltx:
                if hasattr(moltx, 'trending'):
                    exploratory_proposals.append(SyModActionProposal(
                        action_type='trending_check',
                        target_id=None,
                        target_name='exploratory_trend_check',
                        confidence=0.42,
                        justification='Exploratory: Analyzing trending topics for opportunities',
                        metadata={'plugin': 'moltx', 'trigger': 'idle_exploration', 'safe': True, 'category': 'analysis'}
                    ))
                if hasattr(moltx, 'get_feed'):
                    exploratory_proposals.append(SyModActionProposal(
                        action_type='feed_browse',
                        target_id=None,
                        target_name='exploratory_feed_check',
                        confidence=0.38,
                        justification='Exploratory: Browsing feed to gather intelligence',
                        metadata={'plugin': 'moltx', 'trigger': 'idle_exploration', 'safe': True, 'category': 'analysis'}
                    ))
                if hasattr(moltx, 'get_sentiment_analysis'):
                    exploratory_proposals.append(SyModActionProposal(
                        action_type='sentiment_analysis',
                        target_id=None,
                        target_name='market_sentiment_check',
                        confidence=0.40,
                        justification='Exploratory: Analyzing market sentiment',
                        metadata={'plugin': 'moltx', 'trigger': 'idle_exploration', 'safe': True, 'category': 'analysis'}
                    ))

            # Platform health checks
            clawbr = self.brain.plugin_manager.get_plugin('clawbr') if self.brain.plugin_manager else None
            if clawbr and hasattr(clawbr, 'get_stats'):
                exploratory_proposals.append(SyModActionProposal(
                    action_type='platform_stats',
                    target_id=None,
                    target_name='clawbr_health_check',
                    confidence=0.45,
                    justification='Exploratory: Checking Clawbr platform health',
                    metadata={'plugin': 'clawbr', 'trigger': 'idle_exploration', 'safe': True, 'category': 'analysis'}
                ))

        # === CATEGORY 2: CONTENT CREATION (Every 3rd cycle) ===
        if cycle_count % 3 == 0:
            moltx = self.brain.plugin_manager.get_plugin('moltx') if self.brain.plugin_manager else None
            if moltx:
                if hasattr(moltx, 'intelligent_post'):
                    exploratory_proposals.append(SyModActionProposal(
                        action_type='intelligent_post',
                        target_id=None,
                        target_name='create_intelligent_content',
                        confidence=0.35,
                        justification='Exploratory: Creating intelligent content about recent discoveries',
                        metadata={'plugin': 'moltx', 'trigger': 'idle_exploration', 'safe': True, 'category': 'content', 'requires_engagement_quota': True}
                    ))
                if hasattr(moltx, 'create_thread'):
                    exploratory_proposals.append(SyModActionProposal(
                        action_type='create_thread',
                        target_id=None,
                        target_name='create_discussion_thread',
                        confidence=0.33,
                        justification='Exploratory: Starting a discussion thread on trending topic',
                        metadata={'plugin': 'moltx', 'trigger': 'idle_exploration', 'safe': True, 'category': 'content'}
                    ))

        # === CATEGORY 3: SOCIAL ENGAGEMENT (Every cycle - maintains presence) ===
        moltx = self.brain.plugin_manager.get_plugin('moltx') if self.brain.plugin_manager else None
        if moltx:
            if hasattr(moltx, 'engage_feed'):
                exploratory_proposals.append(SyModActionProposal(
                    action_type='engage_feed',
                    target_id=None,
                    target_name='light_social_engagement',
                    confidence=0.40,
                    justification='Exploratory: Light engagement to maintain social presence',
                    metadata={'plugin': 'moltx', 'trigger': 'idle_exploration', 'safe': True, 'category': 'social'}
                ))
            if hasattr(moltx, 'auto_reply_mentions'):
                exploratory_proposals.append(SyModActionProposal(
                    action_type='reply_mentions',
                    target_id=None,
                    target_name='reply_to_mentions',
                    confidence=0.42,
                    justification='Exploratory: Responding to mentions and interactions',
                    metadata={'plugin': 'moltx', 'trigger': 'idle_exploration', 'safe': True, 'category': 'social'}
                ))

        clawbr = self.brain.plugin_manager.get_plugin('clawbr') if self.brain.plugin_manager else None
        if clawbr:
            if hasattr(clawbr, 'check_debates'):
                exploratory_proposals.append(SyModActionProposal(
                    action_type='check_debates',
                    target_id=None,
                    target_name='check_active_debates',
                    confidence=0.38,
                    justification='Exploratory: Checking for debate opportunities',
                    metadata={'plugin': 'clawbr', 'trigger': 'idle_exploration', 'safe': True, 'category': 'social'}
                ))
            if hasattr(clawbr, 'get_notifications'):
                exploratory_proposals.append(SyModActionProposal(
                    action_type='check_notifications',
                    target_id=None,
                    target_name='check_clawbr_notifications',
                    confidence=0.41,
                    justification='Exploratory: Checking for new notifications',
                    metadata={'plugin': 'clawbr', 'trigger': 'idle_exploration', 'safe': True, 'category': 'social'}
                ))

        # === CATEGORY 4: SYSTEM & MONITORING (Every 5th cycle) ===
        if cycle_count % 5 == 0:
            # Skip internal plugin actions - no 'internal' plugin exists
            # Memory consolidation and performance monitoring are handled
            # by the brain itself, not routed through plugin system
            pass

        # === CATEGORY 5: TRADING/MARKET (Only if domain enabled) ===
        if cycle_count % 4 == 0:
            onchain = self.brain.plugin_manager.get_plugin('onchain') if self.brain.plugin_manager else None
            if onchain:
                if hasattr(onchain, 'analyze_markets'):
                    exploratory_proposals.append(SyModActionProposal(
                        action_type='market_analysis',
                        target_id=None,
                        target_name='analyze_market_conditions',
                        confidence=0.36,
                        justification='Exploratory: Analyzing market conditions for opportunities',
                        metadata={'plugin': 'onchain', 'trigger': 'idle_exploration', 'safe': True, 'category': 'market', 'domain_autonomy': 'market'}
                    ))
                if hasattr(onchain, 'get_portfolio_summary'):
                    exploratory_proposals.append(SyModActionProposal(
                        action_type='portfolio_check',
                        target_id=None,
                        target_name='check_portfolio_status',
                        confidence=0.39,
                        justification='Exploratory: Checking portfolio status',
                        metadata={'plugin': 'onchain', 'trigger': 'idle_exploration', 'safe': True, 'category': 'market', 'domain_autonomy': 'market'}
                    ))

        # === CATEGORY 6: SELF-IMPROVEMENT — Practice what the agent is bad at ===
        if cycle_count % 3 == 0:
            try:
                learn_priorities = []
                if hasattr(self.brain, 'cognitive') and self.brain.cognitive:
                    self_model = getattr(self.brain.cognitive, 'self_model', None)
                    if self_model and hasattr(self_model, 'what_should_i_learn'):
                        learn_priorities = self_model.what_should_i_learn() or []
                    if self_model and hasattr(self_model, 'what_should_i_avoid'):
                        avoid_list = self_model.what_should_i_avoid() or []
                        for item in avoid_list[:2]:
                            learn_priorities.append({
                                'domain': item.get('domain', 'unknown'),
                                'action_type': item.get('action_type', 'unknown'),
                                'reason': 'needs_practice',
                                'sample_size': item.get('sample_size', 0),
                                'success_rate': item.get('success_rate', 0.0),
                                'priority': 'high',
                            })

                if learn_priorities:
                    seen_domains = set()
                    for item in learn_priorities[:3]:
                        domain = item.get('domain', 'unknown')
                        action_type = item.get('action_type', 'practice')
                        reason = item.get('reason', '')
                        sample_size = item.get('sample_size', 0)

                        if domain in seen_domains:
                            continue
                        seen_domains.add(domain)

                        base_confidence = 0.45 if reason == 'needs_practice' else 0.40
                        exploratory_proposals.append(SyModActionProposal(
                            action_type=action_type,
                            target_id=None,
                            target_name=f"practice_{domain}",
                            confidence=base_confidence,
                            justification=f"Self-improvement: practicing {domain}/{action_type} ({reason}, {sample_size} samples)",
                            metadata={
                                'plugin': domain,
                                'trigger': 'idle_exploration',
                                'safe': True,
                                'category': 'self_improve',
                                'self_model_driven': True,
                                'learning_reason': reason,
                            }
                        ))
                    logger.info(f"📚 Self-model: {len(learn_priorities)} learning priorities found, generated practice proposals")
            except Exception as e:
                logger.debug(f"Self-model learning priorities error: {e}")

        logger.info(f"🚀 Generated {len(exploratory_proposals)} diverse exploratory proposals (cycle: {cycle_count})")

        return exploratory_proposals

    # ──────────────────────────────────────────────
    # GENERATE DEFAULT GOALS
    # ──────────────────────────────────────────────

    async def generate_default_goals(self) -> bool:
        """Auto-generate safe default goals when no active work items exist.

        Uses the new default_goals module for comprehensive goal seeding.
        Returns True if goals were created.
        """
        if not self.brain.core or not hasattr(self.brain.core, 'agi_kernel'):
            return False

        agi_kernel = self.brain.core.agi_kernel
        if not agi_kernel:
            return False

        try:
            # Use new default goal seeder
            from src.agentic.default_goals import get_default_goal_seeder
            goal_seeder = get_default_goal_seeder(agi_kernel)
            if not goal_seeder:
                return False
            seeded_count = goal_seeder.seed_goals_if_needed()

            if seeded_count > 0:
                logger.info(f"🌱 Seeded {seeded_count} default goals via DefaultGoalSeeder")
                return True

        except Exception as e:
            logger.warning(f"Default goal seeding failed: {e}")

        return False

    # ──────────────────────────────────────────────
    # ADVANCE ACTIVE PLANS
    # ──────────────────────────────────────────────

    async def advance_active_plans(self, agi_kernel=None) -> bool:
        """Advance active plans by executing multiple ready steps per cycle (2.8).

        Finds active plans, picks the highest-priority ready steps from each,
        executes them via the action router, and records outcomes.
        Executes up to 3 steps per cycle to accelerate multi-step plans.
        """
        goal_planner = getattr(self.brain.cognitive, 'goal_planner', None)
        if not goal_planner:
            return False

        active_plans = goal_planner.get_active_plans()
        if not active_plans:
            return False

        active_plans.sort(key=lambda p: getattr(p, 'priority', 0.5), reverse=True)

        executed = 0
        max_per_cycle = 3

        for plan in active_plans:
            if executed >= max_per_cycle:
                break

            goal_planner.check_preconditions(plan)
            next_step = goal_planner.get_next_step(plan)

            if not next_step:
                continue

            logger.info(
                f"📋 Executing plan step: {next_step.id} ({next_step.action}) "
                f"from plan {plan.id} ({plan.goal[:40]})"
            )

            action_spec = {
                'action_type': next_step.action,
                'plugin': next_step.plugin,
                'params': {},
                'context': {'plan_id': plan.id, 'step_id': next_step.id, 'goal': plan.goal},
            }

            prediction = self.brain.cognitive.predict_action_outcome(
                action=f"{next_step.plugin}:{next_step.action}",
                domain=plan.domain,
            )

            try:
                result = None
                if agi_kernel and hasattr(agi_kernel, 'action_router') and agi_kernel.action_router:
                    try:
                        result = await agi_kernel.action_router.route_action(action_spec)
                    except Exception as e:
                        logger.warning(f"Plan step execution failed: {e}")
                        result = {'success': False, 'error': str(e)}
                elif self.brain.plugin_manager:
                    plugin = self.brain.plugin_manager.plugins.get(next_step.plugin)
                    if plugin:
                        try:
                            cmd_handler = plugin.get_commands().get(next_step.action)
                            if cmd_handler:
                                cmd_result = cmd_handler([])
                                result = {'success': True, 'output': str(cmd_result)[:500]}
                            else:
                                result = {'success': False, 'error': f'No command {next_step.action} on {next_step.plugin}'}
                        except Exception as e:
                            result = {'success': False, 'error': str(e)}

                if result is None:
                    result = {'success': False, 'error': 'No executor available'}

                success = result.get('success', False)

                if success:
                    goal_planner.mark_step_completed(plan.id, next_step.id, result)
                    plan = goal_planner.plans.get(plan.id)
                    if plan and plan.status == "completed":
                        logger.info(f"📋 Plan completed: {plan.goal[:60]}")
                        goal_planner.record_plan_outcome(
                            plan.id, success=True,
                            belief_engine=self.brain.cognitive.belief_engine,
                            self_model=self.brain.cognitive.self_model,
                        )
                        executed += 1
                else:
                    reason = result.get('error', result.get('reason', 'Unknown failure'))
                    goal_planner.mark_step_failed(plan.id, next_step.id, reason, result)
                    goal_planner.rollback_completed_steps(plan.id, next_step.id)
                    goal_planner.record_plan_outcome(
                        plan.id, success=False,
                        belief_engine=self.brain.cognitive.belief_engine,
                        self_model=self.brain.cognitive.self_model,
                    )

                self.brain.cognitive.record_action_outcome(
                    action=f"{next_step.plugin}:{next_step.action}",
                    domain=plan.domain,
                    predicted_confidence=prediction.get('predicted_success', 0.5),
                    actual_success=success,
                    context=f"plan:{plan.id}",
                    outcome_description=result.get('output', result.get('error', ''))[:200],
                )

                try:
                    intrinsic = self.brain.cognitive.calculate_intrinsic_reward(
                        domain=plan.domain,
                        action=next_step.action,
                        predicted=prediction.get('predicted_success', 0.5),
                        actual_success=success,
                    )
                    logger.debug(f"Curiosity intrinsic reward: {intrinsic:.3f} for {plan.domain}.{next_step.action}")
                except Exception as e:
                    logger.debug("Non-critical error: %s", e)
                executed += 1

            except Exception as e:
                logger.error(f"Plan step execution error: {e}")
                goal_planner.mark_step_failed(
                    plan.id, next_step.id, str(e), {'error': str(e)}
                )
                continue

        if executed > 0:
            logger.info(f"📋 Advanced {executed} plan steps this cycle (max: {max_per_cycle})")
        return executed > 0

    async def convert_agi_action_to_proposal(self, agi_action: Dict, phases_executed) -> Optional[Any]:
        """Convert AGI orchestrator action to SyMod proposal"""
        from src.agentic.symod_core import SyModActionProposal

        action_taken = agi_action.get('action_taken', '')
        content = agi_action.get('content_posted', '')

        # Map AGI actions to SyMod action types
        action_mapping = {
            'posted_to_moltx': 'moltx_post',
            'posted_to_clawbr': 'clawbr_post',
        }

        symod_action = action_mapping.get(action_taken)
        if not symod_action:
            return None

        # Determine confidence based on metacognition phase
        confidence = 0.6  # Default
        for phase in phases_executed:
            if phase.phase.value == 'METACOGNITION' and phase.success:
                confidence = phase.output.get('confidence', 0.6)
                break

        # Extract platform from action
        platform = 'unknown'
        if 'moltx' in action_taken:
            platform = 'moltx'
        elif 'clawbr' in action_taken:
            platform = 'clawbr'

        return SyModActionProposal(
            action_type=symod_action,
            target_id=None,
            target_name=f"AGI_Content_{datetime.now().strftime('%H%M%S')}",
            content=content,
            confidence=confidence,
            justification="AGI Orchestrator generated content based on multi-phase analysis",
            metadata={
                'plugin': platform,
                'trigger': 'agi_orchestrator',
                'phases_used': len(phases_executed),
                'agi_action': action_taken,
            }
        )

    async def extract_creative_proposals(self, creative_output: Dict, phases_executed) -> List[Any]:
        """Extract action proposals from creative generation phase"""
        from src.agentic.symod_core import SyModActionProposal

        proposals = []

        recommended = creative_output.get('recommended_content')
        if recommended and isinstance(recommended, dict):
            concept_title = recommended.get('title', '')
            if concept_title:
                content = self.brain._generate_post_from_concept(concept_title)
                if content:
                    proposal = SyModActionProposal(
                        action_type='moltx_post',
                        target_id=None,
                        target_name="AGI_Creative_Content",
                        content=content,
                        confidence=0.7,
                        justification="AGI Creative Engine generated engaging content",
                        metadata={
                            'plugin': 'moltx',
                            'trigger': 'agi_creative',
                            'novelty_score': recommended.get('novelty', 0),
                            'estimated_impact': recommended.get('estimated_impact', 0),
                            'concept': concept_title,
                        }
                    )
                    proposals.append(proposal)

        story_arc = creative_output.get('story_arc')
        if story_arc and isinstance(story_arc, dict):
            theme = story_arc.get('title', '')
            if theme:
                content = self.brain._generate_post_from_concept(theme)
                if content:
                    proposal = SyModActionProposal(
                        action_type='moltx_post',
                        target_id=None,
                        target_name="AGI_Story_Arc",
                        content=content,
                        confidence=0.6,
                        justification="AGI Creative Engine generated story concept",
                        metadata={
                            'plugin': 'moltx',
                            'trigger': 'agi_creative',
                            'novelty_score': story_arc.get('novelty', 0),
                            'estimated_impact': story_arc.get('estimated_impact', 0),
                            'theme': theme,
                        }
                    )
                    proposals.append(proposal)

        return proposals

    # ──────────────────────────────────────────────

    async def think_phase(
        self,
        agi_kernel,
        agi_actions,
        active_work_items,
        spine_context,
        observations,
    ) -> List:
        """Main think phase - assembles and ranks proposals."""
        return await self.brain._phase_assemble_proposals(
            agi_kernel, agi_actions, active_work_items, spine_context
        )

    async def goal_management(self, agi_kernel, observations) -> Optional[Dict]:
        """Goal generation and management."""
        return self.brain._phase_goal_management(agi_kernel, observations)

    async def curiosity_goals(self, agi_kernel, proposals) -> None:
        """Self-directed curiosity goals injection."""
        await self.brain._phase_curiosity_goals(agi_kernel, proposals)

    async def periodic_reflection(self, agi_kernel) -> None:
        """Periodic reflection - cognitive data review."""
        await self.brain._phase_periodic_reflection(agi_kernel)

    async def maintain_persistent_intents(self, agi_kernel, proposals) -> None:
        """Maintain long-running objectives."""
        await self.brain._phase_maintain_persistent_intents(agi_kernel, proposals)

    async def cross_domain_synthesis(self, agi_kernel, observations, proposals) -> None:
        """Cross-domain strategic planning."""
        await self.brain._phase_cross_domain_synthesis_and_planning(
            agi_kernel, observations, proposals
        )


def create_brain_think(brain) -> BrainThink:
    """Factory to create BrainThink with brain reference."""
    return BrainThink(brain)
