"""
Brain Learn Module — Reflection, metacognition, belief update

Extracted from autonomous_brain.py for modularity.
Contains: periodic reflection, consolidation, meta-adaptation,
causal reasoning, theory of mind, learning goal acquisition.
"""

import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime

from src.agentic.symod_core import SyModObservation

if TYPE_CHECKING:
    from src.agentic.theory_of_mind import IntentInference

logger = logging.getLogger(__name__)


class BrainLearn:
    """Learn phase operations for the autonomous brain."""

    def __init__(self, brain):
        self.brain = brain

    # ── Existing helper methods (preserved from original stubs) ──

    def cognitive_reflect(self) -> Dict:
        """Run cognitive reflection at cycle end."""
        return self.brain.cognitive.reflect()

    def cognitive_record_outcome(
        self,
        action: str,
        domain: str,
        predicted: float,
        actual: bool,
        context: str = "",
        outcome_desc: str = "",
    ) -> Dict:
        """Record action outcome to cognitive systems."""
        return self.brain.cognitive.record_action_outcome(
            action=action,
            domain=domain,
            predicted_confidence=predicted,
            actual_success=actual,
            context=context,
            outcome_description=outcome_desc,
        )

    def get_belief_calibration(self) -> Dict:
        """Get belief calibration report."""
        return self.brain.cognitive.get_belief_calibration()

    def get_domain_strengths(self) -> Dict:
        """Get domain strength summary."""
        return self.brain.cognitive.get_domain_strengths()

    # ── Phase methods extracted from autonomous_brain.py ──

    async def _phase_periodic_reflection(self, agi_kernel):
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

                logger.info(f"🧠 Cognitive reflection (cycle {cycle_count}):")
                logger.info(f"   Assessment: {assessment}")
                logger.info(f"   Recommendation: {reflection.get('recommendation', '')}")
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
                            trigger_data={},
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

    async def _phase_consolidate_learning(self, agi_kernel=None) -> None:
        """Sleep-cycle consolidation: replay high-value memories, update meta-params.

        Runs periodically (every 5 cycles) to:
        1. Replay recent successes into the knowledge graph
        2. Update meta-learning parameters per domain
        3. Prune low-confidence beliefs from the belief engine
        4. Record consolidated stats
        """
        if not hasattr(self.brain, '_consolidation_counter'):
            self.brain._consolidation_counter = 0
        self.brain._consolidation_counter += 1

        # Only consolidate every 5 cycles
        if self.brain._consolidation_counter % 5 != 0:
            return

        logger.info("💤 Starting learning consolidation cycle...")

        try:
            recent_actions = self.brain.action_logger.get_recent_actions(limit=20)
            successes = [a for a in recent_actions if a.outcome == 'success']
            for action in successes[:5]:
                self.brain.knowledge_graph.learn_from_outcome(
                    action=str(action.action_type),
                    domain=str(action.plugin or 'general'),
                    context=str(action.content or '')[:200],
                    outcome='success',
                    success=True,
                    confidence=action.confidence,
                )

            if self.brain.cognitive and hasattr(self.brain.cognitive, 'self_model'):
                learn_list = self.brain.cognitive.self_model.what_should_i_learn()
                if learn_list:
                    logger.info(f"   📚 Learning priorities: {len(learn_list)} domains need practice")

            if self.brain.meta_learning_engine:
                domains_seen = set()
                for a in recent_actions:
                    d = str(a.plugin or 'general')
                    if d not in domains_seen:
                        domains_seen.add(d)
                        approach = self.brain.meta_learning_engine.adapt_learning_approach(
                            domain=d,
                            current_approach={"exploration_rate": 0.3, "memory_depth": 10}
                        )
                        logger.debug(f"   🔧 Adapted params for {d}: {approach.get('exploration_rate', '?')}")

            # Memory consolidation pipeline: consolidate clusters every 25 cycles
            if self.brain._consolidation_counter % 25 == 0:
                try:
                    memory_system = getattr(self.brain, 'memory_system', None)
                    if memory_system is None and hasattr(self.brain, 'memory'):
                        memory_system = self.brain.memory
                    if memory_system and hasattr(memory_system, 'consolidate_memories'):
                        mem_stats = memory_system.consolidate_memories()
                        logger.info(f"   🧠 Memory consolidation: {mem_stats['clusters_found']} clusters, "
                                    f"{mem_stats['consolidated_created']} created, "
                                    f"{mem_stats['originals_expired']} expired")
                        # Also prune low-importance stale memories
                        if hasattr(memory_system, 'prune_by_importance'):
                            pruned = memory_system.prune_by_importance()
                            if pruned > 0:
                                logger.info(f"   🧹 Pruned {pruned} low-importance memories")
                except Exception as e:
                    logger.debug(f"Memory consolidation pipeline error: {e}")

            logger.info("💤 Consolidation complete")

        except Exception as e:
            logger.debug(f"Learning consolidation error: {e}")

    async def _phase_meta_adaptation(self, agi_kernel=None) -> None:
        """Adapt learning parameters per domain based on recent performance.

        Every cycle, query the meta-learning engine for optimal params
        and log any recommended adjustments for the reflection phase.
        """
        if not self.brain.meta_learning_engine:
            return

        try:
            insights = self.brain.meta_learning_engine.get_learning_insights()
            if insights:
                logger.info(f"🧠 Meta-learning: {len(insights)} insights")
                for insight in insights[:2]:
                    logger.info(f"   💡 {insight}")

            if self.brain.cognitive and hasattr(self.brain.cognitive, 'self_model'):
                calibration = self.brain.cognitive.self_model.get_calibration_curve()
                mae = calibration.get('mean_absolute_error', 0)
                if mae > 0.2:
                    logger.info(f"   ⚠️ High calibration error ({mae:.2f}) — confidence calibration needs attention")

        except Exception as e:
            logger.debug(f"Meta adaptation error: {e}")

    async def _phase_causal_reasoning(self, observations: List, agi_kernel=None) -> Dict:
        """Counterfactual simulation and root cause analysis.

        Uses CausalEngine to simulate "what if I had done X instead?"
        for failed actions, and feeds insights into subsequent planning.
        """
        insights = {"counterfactuals": [], "root_causes": [], "causal_links": 0}
        if not self.brain.causal_engine:
            return insights

        try:
            recent_actions = self.brain.action_logger.get_recent_actions(limit=10)
            failed_actions = [a for a in recent_actions if a.outcome == 'failure']
            for action in failed_actions[:3]:
                cf = self.brain.causal_engine.simulate_counterfactual(
                    actual_action_id=str(action.id),
                    hypothetical_change={"time": "optimized"}
                )
                insights["counterfactuals"].append({
                    "action_id": str(action.id),
                    "predicted": cf.predicted_outcome,
                    "confidence": cf.confidence,
                })

            if observations:
                root = self.brain.causal_engine.analyze_root_cause(
                    event_id="cycle_observation",
                    depth=2
                )
                if root and root.root_causes:
                    insights["root_causes"] = root.root_causes

            causal_links = self.brain.causal_engine.find_correlations(
                outcome_type="success", min_strength=0.5
            )
            insights["causal_links"] = len(causal_links)
            if causal_links:
                logger.info(f"🔗 Causal engine: {len(causal_links)} correlations, {len(insights['counterfactuals'])} counterfactuals")

        except Exception as e:
            logger.debug(f"Causal reasoning error: {e}")

        return insights

    def _phase_theory_of_mind(self, observations: List) -> Optional['IntentInference']:
        """Feed observations to Theory of Mind, infer owner intent.

        Scans observations for owner-related interactions (mentions, replies,
        comments on own posts), records them as actions in ToM, and infers
        the owner's current intent. The inferred intent is attached to the
        brain's state for downstream phases to consume.
        """
        if not self.brain.theory_of_mind:
            return None

        try:
            owner_id = 'owner'
            if self.brain.core and hasattr(self.brain.core, 'config') and isinstance(getattr(self.brain.core, 'config', None), dict):
                owner_id = self.brain.core.config.get('owner_id', 'owner')
            owner_actions = []

            for obs in observations:
                if not hasattr(obs, 'observation_type') or not hasattr(obs, 'data'):
                    continue
                otype = str(getattr(obs, 'observation_type', '') or '')
                data = getattr(obs, 'data', {}) or {}

                if otype in ('mention', 'reply', 'comment'):
                    action_type = otype
                    target = str(data.get('from_user', data.get('author_name', '')))
                    if target and target.lower() not in ('owner', 'alleybot', 'self'):
                        self.brain.theory_of_mind.observe_action(
                            agent_id=owner_id,
                            action_type=action_type,
                            target=target,
                            context={'observation_type': otype, 'content_preview': str(data.get('content', ''))[:120]},
                        )
                        owner_actions.append(action_type)

                elif otype in ('post', 'clawbr_post'):
                    content = str(data.get('content', ''))[:200]
                    if 'owner' in content.lower() or '@owner' in content.lower():
                        self.brain.theory_of_mind.observe_action(
                            agent_id=owner_id,
                            action_type='mention_owner',
                            target=str(data.get('author_name', '')),
                            context={'content_preview': content},
                        )
                        owner_actions.append('mention_owner')

            if not owner_actions:
                return None

            inference = self.brain.theory_of_mind.infer_intent(owner_id)
            if inference and inference.confidence >= 0.3:
                intent_obs = SyModObservation(
                    observation_type='inferred_owner_intent',
                    importance=0.7 + inference.confidence * 0.3,
                    source_plugin='theory_of_mind',
                    data={
                        'inferred_intent': inference.inferred_intent,
                        'confidence': inference.confidence,
                        'explanation': inference.explanation,
                        'supporting_actions': inference.supporting_actions,
                    },
                )
                observations.append(intent_obs)
                self.brain.owner_inferred_intent = inference

                predicted = self.brain.theory_of_mind.predict_next_action(owner_id)
                if predicted:
                    self.brain.owner_predicted_next_action = predicted

                return inference

        except Exception as e:
            logger.debug(f"ToM phase error: {e}")

        return None

    async def _phase_learning_goal_acquisition(self, agi_kernel=None) -> None:
        """Turn curiosity gaps and self-model weaknesses into concrete skills.

        Runs every 20 cycles. Detects capability gaps, generates SkillSpecifications,
        delegates to AutonomousCoder, deploys the result, and updates self-model.
        """
        if not agi_kernel:
            return
        cycle_count = self.brain.stats.get('cycles_completed', 0)
        if cycle_count < 1 or cycle_count % 20 != 0:
            return

        try:
            # 1. Gather signals: self-model learning priorities + curiosity goals
            learning_priorities = []
            if hasattr(self.brain.cognitive, 'self_model') and self.brain.cognitive.self_model:
                learning_priorities = self.brain.cognitive.self_model.what_should_i_learn()

            curiosity_gaps = []
            if hasattr(self.brain.cognitive, 'curiosity') and self.brain.cognitive.curiosity:
                curiosity_gaps = self.brain.cognitive.curiosity.detect_knowledge_gaps()

            if not learning_priorities and not curiosity_gaps:
                return

            logger.info(f"📚 === LEARNING ACQUISITION === "
                        f"({len(learning_priorities)} self-model gaps, "
                        f"{len(curiosity_gaps)} curiosity gaps)")

            # 2. Build candidates from self-model weaknesses
            candidates = []
            seen = set()
            for lp in learning_priorities[:3]:
                domain = lp.get('domain', 'general')
                if domain in seen:
                    continue
                seen.add(domain)
                candidates.append({
                    'domain': domain,
                    'action_type': lp.get('action_type', 'learn'),
                    'description': f"Build capability in {domain}: {lp.get('reason', 'low data')}",
                    'source': 'self_model',
                    'sample_size': lp.get('sample_size', 0),
                    'success_rate': lp.get('success_rate', 0),
                })

            for gap in curiosity_gaps[:2]:
                domain = gap.get('domain', 'general')
                if domain in seen:
                    continue
                seen.add(domain)
                candidates.append({
                    'domain': domain,
                    'action_type': gap.get('type', 'explore'),
                    'description': f"Explore {domain}: {gap.get('gap_description', 'knowledge gap')}",
                    'source': 'curiosity',
                    'sample_size': 0,
                    'success_rate': 0,
                })

            if not candidates:
                return

            # 3. Generate skills for each candidate
            from src.agentic.autonomous_coder import (
                SkillSpecification, get_best_coder, get_autonomous_coder
            )

            coder = get_autonomous_coder()
            plugin_manager = getattr(agi_kernel, 'plugin_manager', None)
            ai_coder = get_best_coder(plugin_manager) if plugin_manager else None

            for candidate in candidates:
                domain = candidate['domain']
                action = candidate['action_type']
                logger.info(f"   🎯 Building skill for {domain}.{action} ({candidate['source']})")

                spec = SkillSpecification(
                    id=f"learn_{domain}_{action}_{int(datetime.now().timestamp())}",
                    name=f"{domain}_{action}_skill",
                    description=candidate['description'],
                    category=domain,
                    file_structure={},
                    dependencies=[],
                    evidence=[f"Source: {candidate['source']}",
                              f"Sample size: {candidate['sample_size']}",
                              f"Success rate: {candidate['success_rate']}"],
                )

                skill = coder.generate_skill(spec)
                if skill.status == 'generated':
                    deployed = coder.deploy_skill(skill)
                    if deployed:
                        logger.info(f"   ✅ Deployed {skill.skill_name} ({skill.skill_path})")
                        # Update self-model with new capability
                        if hasattr(self.brain.cognitive, 'self_model') and self.brain.cognitive.self_model:
                            self.brain.cognitive.self_model.record_outcome(
                                domain=domain,
                                action_type=action,
                                predicted_confidence=0.5,
                                actual_success=1.0,
                                context=f"skill_deployed:{skill.skill_name}",
                            )
                    else:
                        logger.warning(f"   ⚠️  Deploy failed for {skill.skill_name}")
                else:
                    logger.warning(f"   ⚠️  Skill generation failed: {skill.errors}")

        except Exception as e:
            logger.debug(f"Learning acquisition error: {e}")


def create_brain_learn(brain) -> BrainLearn:
    """Factory to create BrainLearn with brain reference."""
    return BrainLearn(brain)
