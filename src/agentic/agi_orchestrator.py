"""
AlleyBot AGI Orchestrator - The Meta-Brain

Integrates all 14 AGI phases into a coherent, emergent intelligence.
Each phase feeds into others, creating compound intelligence effects.

Phase Flow:
1. World State Intelligence detects patterns
2. Causal Understanding finds why things happen
3. Autonomous Research investigates gaps
4. Creative Generation produces novel solutions
5. Social Intelligence predicts reactions
6. Metacognition validates confidence
7. Multi-Step Planning breaks into actionable steps
8. Goal Management queues the work
9. Execution happens via appropriate plugins
10. Self-Reflection learns from outcomes
11. Strategy Evolution improves approaches
12. Theory of Mind updates agent models
13. Knowledge Synthesis connects learnings
14. Confidence Calibration tunes future decisions

Usage:
    orchestrator = AGIOrchestrator()
    
    # Run full AGI cycle
    result = orchestrator.run_cycle()
    
    # Or trigger specific phase cascade
    orchestrator.cascade_from_detection(trend_detected)
"""

import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

# Import all 14 phases
from src.autonomy.inference_engine import get_inference_engine
from src.agentic.causal_engine import get_causal_engine
from src.agentic.research_engine import get_research_engine
from src.agentic.creative_engine import get_creative_engine
from src.agentic.social_intelligence import get_social_intelligence
from src.agentic.metacognition import get_metacognition
from src.agentic.planning import get_plan_manager
from src.agentic.goal_manager import get_goal_manager
from src.agentic.action_logger import get_action_logger
from src.agentic.strategy_evolver import get_strategy_evolver
from src.autonomy.world_state import get_world_state_manager
from src.agentic.multi_platform_engine import get_multi_platform_engine, Platform

logger = logging.getLogger(__name__)


class Phase(Enum):
    """The 14 AGI phases"""
    WORLD_STATE_INTELLIGENCE = 7
    CAUSAL_UNDERSTANDING = 10
    AUTONOMOUS_RESEARCH = 11
    CREATIVE_GENERATION = 13
    SOCIAL_INTELLIGENCE = 12
    METACOGNITION = 14
    MULTI_STEP_PLANNING = 9
    GOAL_MANAGEMENT = 2
    EXECUTION = 0
    SELF_REFLECTION = 1
    STRATEGY_EVOLUTION = 1  # Same as reflection
    THEORY_OF_MIND = 12  # Same as social
    KNOWLEDGE_SYNTHESIS = 11  # Same as research
    CONFIDENCE_CALIBRATION = 14  # Same as metacognition


@dataclass
class PhaseResult:
    """Result from running a phase"""
    phase: Phase
    success: bool
    output: Any
    confidence: float
    duration_seconds: float
    triggered_phases: List[Phase]


@dataclass
class AGICycleResult:
    """Result of a complete AGI cycle"""
    cycle_id: str
    triggered_by: str
    phases_executed: List[PhaseResult]
    final_action: Optional[Dict[str, Any]]
    learnings: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class AGIOrchestrator:
    """
    The Meta-Brain - Orchestrates all 14 AGI phases.
    
    This is the emergent layer where individual capabilities combine
    into coherent, intelligent behavior.
    
    Key cascades:
    - Detection → Causal → Research → Creative → Social → Meta → Plan → Execute → Learn
    - Anomaly → Causal → Research → Creative → Plan → Execute → Reflect
    - Goal → Plan → Research → Creative → Social → Execute → Reflect → Evolve
    """
    
    def __init__(self, core=None):
        # Initialize all phase engines
        self.inference = get_inference_engine()
        self.causal = get_causal_engine()
        self.research = get_research_engine()
        self.creative = get_creative_engine()
        self.social = get_social_intelligence()
        self.metacognition = get_metacognition()
        self.planning = get_plan_manager()
        self.goals = get_goal_manager()
        self.action_logger = get_action_logger()
        self.strategy_evolver = get_strategy_evolver()
        self.world_state = get_world_state_manager()
        
        # Multi-platform execution engine
        self.multi_platform = get_multi_platform_engine(core=core)
        
        # Core reference for plugin access
        self.core = core
        
        # Safety controls
        self.last_post_time: Optional[datetime] = None
        self.min_post_interval_minutes = 30  # Don't post more than every 30 min
        self.daily_post_count = 0
        self.max_daily_posts = 10
        self.last_post_date = datetime.now().date()
        
        # Cross-phase memory
        self.recent_insights: List[Dict] = []
        self.active_cascades: Dict[str, Any] = {}
        self.learning_accumulator: Dict[str, Any] = {}
        
        logger.info("🧠 AGI Orchestrator initialized - 14 phases ready")
        logger.info(f"🌐 Multi-Platform Engine: {len([p for p, a in self.multi_platform.available_platforms.items() if a])} platforms available")
    
    def run_cycle(self, trigger: str = "scheduled") -> AGICycleResult:
        """
        Run a complete AGI cycle through all relevant phases.
        
        Args:
            trigger: What triggered this cycle ('scheduled', 'anomaly', 'goal', 'user')
            
        Returns:
            AGICycleResult with full trace of execution
        """
        cycle_id = f"agi_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        phases_executed = []
        learnings = []
        
        logger.info(f"🚀 Starting AGI cycle {cycle_id} (trigger: {trigger})")
        
        # Phase 7: Detect patterns in world state
        detection_result = self._run_phase_7_detection()
        phases_executed.append(detection_result)
        
        if not detection_result.success or not detection_result.output:
            logger.info("📭 No patterns detected, cycle complete")
            return AGICycleResult(
                cycle_id=cycle_id,
                triggered_by=trigger,
                phases_executed=phases_executed,
                final_action=None,
                learnings=["no_patterns_detected"]
            )
        
        # Phase 10: Understand causality of detected patterns
        causal_result = self._run_phase_10_causal(detection_result.output)
        phases_executed.append(causal_result)
        
        # Phase 11: Research knowledge gaps
        research_result = self._run_phase_11_research(
            detection_result.output, 
            causal_result.output
        )
        phases_executed.append(research_result)
        
        # Phase 13: Generate creative solutions
        creative_result = self._run_phase_13_creative(
            detection_result.output,
            research_result.output
        )
        phases_executed.append(creative_result)
        
        # Phase 12: Predict social dynamics
        social_result = self._run_phase_12_social(creative_result.output)
        phases_executed.append(social_result)
        
        # Phase 14: Metacognitive check
        meta_result = self._run_phase_14_metacognition(
            creative_result.output,
            social_result.output
        )
        phases_executed.append(meta_result)
        
        if not meta_result.output.get('proceed', False):
            logger.info("🛑 Metacognition blocked action (low confidence)")
            learnings.append("blocked_low_confidence")
            return AGICycleResult(
                cycle_id=cycle_id,
                triggered_by=trigger,
                phases_executed=phases_executed,
                final_action=None,
                learnings=learnings
            )
        
        # Phase 9: Plan execution
        plan_result = self._run_phase_9_planning(
            creative_result.output,
            meta_result.output
        )
        phases_executed.append(plan_result)
        
        # Execute the plan
        execution_result = self._execute_plan(plan_result.output)
        
        # Phase 1 & 8: Learn from execution
        learning_result = self._run_phase_1_learning(execution_result)
        phases_executed.append(learning_result)
        
        learnings.extend(learning_result.output.get('learnings', []))
        
        logger.info(f"✅ AGI cycle {cycle_id} complete - {len(phases_executed)} phases")
        
        return AGICycleResult(
            cycle_id=cycle_id,
            triggered_by=trigger,
            phases_executed=phases_executed,
            final_action=execution_result,
            learnings=learnings
        )
    
    def _run_phase_7_detection(self) -> PhaseResult:
        """Phase 7: World State Intelligence - Detect patterns"""
        start = datetime.now()
        
        try:
            # Detect trends
            trends = self.inference.detect_trends(hours=24, top_n=3)
            
            # Detect anomalies
            anomalies = self.inference.detect_anomalies(hours=6)
            
            # Find cross-platform patterns
            patterns = self.inference.find_cross_platform_patterns(hours=48)
            
            output = {
                'trends': [{'topic': t.topic, 'strength': t.strength} for t in trends],
                'anomalies': [{'type': a.anomaly_type, 'severity': a.severity} for a in anomalies],
                'patterns': [{'type': p.pattern_type, 'platforms': p.platforms} for p in patterns],
                'has_detection': bool(trends or anomalies or patterns)
            }
            
            # Determine what to trigger next
            triggered = []
            if anomalies:
                triggered.append(Phase.CAUSAL_UNDERSTANDING)
            if trends:
                triggered.append(Phase.CAUSAL_UNDERSTANDING)
            
            return PhaseResult(
                phase=Phase.WORLD_STATE_INTELLIGENCE,
                success=True,
                output=output,
                confidence=0.8 if output['has_detection'] else 0.5,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=triggered
            )
        
        except Exception as e:
            logger.error(f"Phase 7 failed: {e}")
            return PhaseResult(
                phase=Phase.WORLD_STATE_INTELLIGENCE,
                success=False,
                output={'error': str(e)},
                confidence=0.0,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[]
            )
    
    def _run_phase_10_causal(self, detection_output: Dict) -> PhaseResult:
        """Phase 10: Causal Understanding - Understand why"""
        start = datetime.now()
        
        try:
            insights = []
            
            # Analyze causes for top trends
            for trend in detection_output.get('trends', []):
                # Find correlations for trend topic
                correlations = self.causal.find_correlations(trend['topic'])
                if correlations:
                    insights.append({
                        'topic': trend['topic'],
                        'likely_causes': [{'factor': c.cause_type, 'strength': c.strength} 
                                         for c in correlations[:3]]
                    })
            
            # Get attribution for recent engagement
            attribution = self.causal.get_impact_attribution('engagement', time_window_hours=24)
            
            output = {
                'insights': insights,
                'attribution': attribution,
                'confidence': 0.7 if insights else 0.5
            }
            
            return PhaseResult(
                phase=Phase.CAUSAL_UNDERSTANDING,
                success=True,
                output=output,
                confidence=output['confidence'],
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[Phase.AUTONOMOUS_RESEARCH] if insights else []
            )
        
        except Exception as e:
            logger.error(f"Phase 10 failed: {e}")
            return PhaseResult(
                phase=Phase.CAUSAL_UNDERSTANDING,
                success=False,
                output={'error': str(e)},
                confidence=0.0,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[]
            )
    
    def _run_phase_11_research(self, detection: Dict, causal: Dict) -> PhaseResult:
        """Phase 11: Autonomous Research - Investigate gaps"""
        start = datetime.now()
        
        try:
            # Detect knowledge gaps from patterns
            gaps = self.research.detect_gaps_from_failures(self.action_logger)
            
            # Research top trend topics
            findings = []
            for trend in detection.get('trends', [])[:2]:
                topic_findings = self.research.research_topic(trend['topic'])
                findings.extend([{'topic': trend['topic'], 'source': f.source} 
                                for f in topic_findings[:3]])
            
            # Synthesize knowledge
            synthesis = {}
            if detection.get('trends'):
                synthesis = self.research.synthesize_knowledge(detection['trends'][0]['topic'])
            
            output = {
                'gaps_found': len(gaps),
                'findings': findings,
                'synthesis': synthesis,
                'questions_to_investigate': self.research.generate_research_questions(
                    detection.get('trends', [{}])[0].get('topic', 'AI'), 
                    num_questions=3
                ) if detection.get('trends') else []
            }
            
            return PhaseResult(
                phase=Phase.AUTONOMOUS_RESEARCH,
                success=True,
                output=output,
                confidence=0.75 if findings else 0.5,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[Phase.CREATIVE_GENERATION]
            )
        
        except Exception as e:
            logger.error(f"Phase 11 failed: {e}")
            return PhaseResult(
                phase=Phase.AUTONOMOUS_RESEARCH,
                success=False,
                output={'error': str(e)},
                confidence=0.0,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[]
            )
    
    def _run_phase_13_creative(self, detection: Dict, research: Dict) -> PhaseResult:
        """Phase 13: Creative Generation - Generate solutions"""
        start = datetime.now()
        
        try:
            concepts = []
            
            # Generate concepts based on trends
            for trend in detection.get('trends', [])[:2]:
                concept = self.creative.generate_concept(
                    'meme', 
                    topic=trend['topic']
                )
                concepts.append({
                    'title': concept.title,
                    'novelty': concept.novelty_score,
                    'estimated_impact': concept.estimated_impact
                })
            
            # Cross-domain inspiration
            inspired = self.creative.cross_domain_inspire('gaming', 'finance')
            
            # Build story arc if multiple concepts
            story = None
            if len(concepts) >= 2:
                story = self.creative.build_story_arc(
                    theme=concepts[0]['title'], 
                    posts=min(3, len(concepts))
                )
            
            output = {
                'concepts': concepts,
                'cross_domain_inspiration': {
                    'title': inspired.title,
                    'description': inspired.description
                },
                'story_arc': {
                    'title': story.title,
                    'posts': len(story.posts)
                } if story else None,
                'recommended_content': concepts[0] if concepts else None
            }
            
            return PhaseResult(
                phase=Phase.CREATIVE_GENERATION,
                success=True,
                output=output,
                confidence=0.8 if concepts else 0.5,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[Phase.SOCIAL_INTELLIGENCE]
            )
        
        except Exception as e:
            logger.error(f"Phase 13 failed: {e}")
            return PhaseResult(
                phase=Phase.CREATIVE_GENERATION,
                success=False,
                output={'error': str(e)},
                confidence=0.0,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[]
            )
    
    def _run_phase_12_social(self, creative_output: Dict) -> PhaseResult:
        """Phase 12: Social Intelligence - Predict reactions"""
        start = datetime.now()
        
        try:
            if not isinstance(creative_output, dict):
                creative_output = {}

            # Predict community reaction to proposed content
            recommended_content = creative_output.get('recommended_content') or {}
            if not isinstance(recommended_content, dict):
                recommended_content = {}

            content = recommended_content.get('title') or recommended_content.get('content') or ''
            
            if not content:
                # No content to analyze
                return PhaseResult(
                    phase=Phase.SOCIAL_INTELLIGENCE,
                    success=True,
                    output={
                        'predicted_reaction': {},
                        'risk_assessment': 'unknown',
                        'entities_tracked': 0,
                        'proceed_recommended': False
                    },
                    confidence=0.5,
                    duration_seconds=(datetime.now() - start).total_seconds(),
                    triggered_phases=[Phase.METACOGNITION]
                )
            
            reaction = self.social.simulate_community_reaction(content)
            if not isinstance(reaction, dict):
                reaction = {}
            
            # Check for high-risk deception patterns in recent interactions
            social_summary = self.social.get_social_summary() or {}
            if not isinstance(social_summary, dict):
                social_summary = {}

            predicted_sentiment = reaction.get('predicted_sentiment')
            reaction_confidence = reaction.get('confidence', 0)
            
            if reaction:
                output = {
                    'predicted_reaction': reaction,
                    'risk_assessment': 'low' if predicted_sentiment == 'positive' else 'medium',
                    'entities_tracked': social_summary.get('entities_modeled', 0),
                    'proceed_recommended': predicted_sentiment in ['positive', 'neutral']
                }
            else:
                output = {
                    'predicted_reaction': {},
                    'risk_assessment': 'medium',
                    'entities_tracked': social_summary.get('entities_modeled', 0),
                    'proceed_recommended': True  # Proceed with caution
                }
            
            return PhaseResult(
                phase=Phase.SOCIAL_INTELLIGENCE,
                success=True,
                output=output,
                confidence=0.75 if reaction_confidence > 0.6 else 0.5,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[Phase.METACOGNITION]
            )
        
        except Exception as e:
            logger.error(f"Phase 12 failed: {e}")
            return PhaseResult(
                phase=Phase.SOCIAL_INTELLIGENCE,
                success=False,
                output={'error': str(e)},
                confidence=0.0,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[]
            )
    
    def _run_phase_14_metacognition(self, creative: Dict, social: Dict) -> PhaseResult:
        """Phase 14: Metacognition - Validate confidence"""
        start = datetime.now()
        
        try:
            # Check resource constraints
            constraints = self.metacognition.check_resource_constraints()
            
            # Assess overall capability for this task
            task = "content_generation"
            calibrated_confidence = self.metacognition.calibrate_confidence(
                task, 
                context={'novel': True, 'complexity': 0.6}
            )
            
            # Get metacognitive summary
            meta_summary = self.metacognition.get_metacognitive_summary()
            
            # Decide whether to proceed
            proceed = (
                calibrated_confidence > 0.6 and
                constraints.get('can_continue', True) and
                social.get('proceed_recommended', True)
            )
            
            output = {
                'proceed': proceed,
                'confidence': calibrated_confidence,
                'constraints': constraints,
                'capabilities_known': meta_summary.get('capabilities_known', 0),
                'rationale': f"Confidence: {calibrated_confidence:.0%}, "
                            f"Constraints: {len(constraints.get('constraints', []))}, "
                            f"Social: {social.get('predicted_reaction', {}).get('predicted_sentiment')}"
            }
            
            return PhaseResult(
                phase=Phase.METACOGNITION,
                success=True,
                output=output,
                confidence=calibrated_confidence,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[Phase.MULTI_STEP_PLANNING] if proceed else []
            )
        
        except Exception as e:
            logger.error(f"Phase 14 failed: {e}")
            return PhaseResult(
                phase=Phase.METACOGNITION,
                success=False,
                output={'error': str(e), 'proceed': False},
                confidence=0.0,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[]
            )
    
    def _run_phase_9_planning(self, creative: Dict, meta: Dict) -> PhaseResult:
        """Phase 9: Multi-Step Planning - Create execution plan"""
        start = datetime.now()
        
        try:
            # Simple plan structure based on creative output
            content = creative.get('recommended_content', {})
            
            plan_steps = [
                {'step': 1, 'action': 'prepare_content', 'details': content},
                {'step': 2, 'action': 'review_and_confirm', 'details': {'auto': True}},
                {'step': 3, 'action': 'execute_post', 'details': {'platform': 'moltx'}}
            ]
            
            # Design A/B test if multiple concepts
            ab_test = None
            if len(creative.get('concepts', [])) >= 2:
                ab_test = self.creative.design_ab_test(
                    hypothesis="Concept A vs Concept B engagement"
                )
            
            output = {
                'plan_steps': plan_steps,
                'estimated_duration': len(plan_steps) * 5,  # 5 min per step
                'ab_test': {'id': ab_test.id} if ab_test else None,
                'ready_to_execute': True
            }
            
            return PhaseResult(
                phase=Phase.MULTI_STEP_PLANNING,
                success=True,
                output=output,
                confidence=meta.get('confidence', 0.7),
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[Phase.EXECUTION]
            )
        
        except Exception as e:
            logger.error(f"Phase 9 failed: {e}")
            return PhaseResult(
                phase=Phase.MULTI_STEP_PLANNING,
                success=False,
                output={'error': str(e)},
                confidence=0.0,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[]
            )
    
    def _check_safety_limits(self) -> Dict[str, Any]:
        """Check if it's safe to post (rate limits, daily caps)"""
        now = datetime.now()
        current_date = now.date()
        
        # Reset daily count if it's a new day
        if current_date != self.last_post_date:
            self.daily_post_count = 0
            self.last_post_date = current_date
        
        # Check daily cap
        if self.daily_post_count >= self.max_daily_posts:
            return {'safe': False, 'reason': f'Daily post cap reached ({self.max_daily_posts})'}
        
        # Check rate limit
        if self.last_post_time:
            minutes_since_last = (now - self.last_post_time).total_seconds() / 60
            if minutes_since_last < self.min_post_interval_minutes:
                return {
                    'safe': False, 
                    'reason': f'Rate limit: {self.min_post_interval_minutes - minutes_since_last:.0f} min remaining'
                }
        
        return {'safe': True, 'reason': 'Within limits'}
    
    def _execute_plan(self, plan: Dict) -> Dict[str, Any]:
        """Execute the generated plan - ACTUALLY posts to platforms"""
        execution = {
            'executed_at': datetime.now().isoformat(),
            'steps_completed': 0,
            'action_taken': None,
            'result': None,
            'platform_response': None
        }
        
        # Check safety limits first
        safety = self._check_safety_limits()
        if not safety['safe']:
            execution['action_taken'] = 'blocked_by_safety'
            execution['result'] = 'safety_blocked'
            execution['reason'] = safety['reason']
            logger.warning(f"🚫 AGI execution blocked: {safety['reason']}")
            return execution
        
        # Get content to post
        content = plan.get('plan_steps', [{}])[0].get('details', {})
        content_text = content.get('title', '') or content.get('content', '')
        
        if not content_text:
            execution['action_taken'] = 'no_content'
            execution['result'] = 'failed'
            return execution
        
        # Try to post to Moltx if available
        if self.core and 'moltx' in getattr(self.core, 'plugins', {}):
            try:
                moltx = self.core.plugins['moltx']
                
                # Generate full content using creative engine
                styled_content = self.creative.transfer_style(
                    content_text, 
                    target_style='casual'
                )
                final_text = styled_content.get('transformed', content_text)
                
                # Actually post
                result = moltx.create_post(final_text)
                
                if result and result.get('success'):
                    execution['action_taken'] = 'posted_to_moltx'
                    execution['result'] = 'success'
                    execution['platform_response'] = result.get('data', {})
                    execution['content_posted'] = final_text[:100]
                    
                    # Update safety tracking
                    self.last_post_time = datetime.now()
                    self.daily_post_count += 1
                    
                    logger.info(f"✅ AGI posted to Moltx: {final_text[:50]}...")
                else:
                    execution['action_taken'] = 'moltx_post_failed'
                    execution['result'] = 'failed'
                    execution['error'] = result.get('error', 'Unknown error')
                    logger.error(f"❌ Moltx post failed: {result}")
                    
            except Exception as e:
                execution['action_taken'] = 'exception'
                execution['result'] = 'failed'
                execution['error'] = str(e)
                logger.error(f"❌ Error posting to Moltx: {e}")
        else:
            # No Moltx available, just prepare
            execution['action_taken'] = 'prepared_only'
            execution['result'] = 'no_platform'
            execution['content_preview'] = content_text[:100]
            logger.info(f"🔧 Prepared content (no platform): {content_text[:50]}...")
        
        execution['steps_completed'] = len(plan.get('plan_steps', []))
        
        return execution
    
    def _run_phase_1_learning(self, execution: Dict) -> PhaseResult:
        """Phase 1 & 8: Self-Reflection and Strategy Evolution - Learn"""
        start = datetime.now()
        
        try:
            learnings = []
            
            # Record action outcome
            action_id = f"action_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Log to action logger
            self.action_logger.log_action(
                action_type='agi_cycle',
                plugin='agi_orchestrator',
                content=execution.get('content_preview', ''),
                confidence=0.8,
                trigger_type='autonomous'
            )
            
            # Run strategy evolution periodically
            try:
                report = self.strategy_evolver.evolve()
                learnings.append(f"Evolved {report.strategies_evaluated} strategies")
            except Exception as e:
                logger.warning(f"Strategy evolution skipped: {e}")
            
            # Update metacognition
            self.metacognition.record_strategy_outcome(
                strategy='agi_cycle',
                context_type='autonomous',
                success=execution.get('result') == 'success',
                confidence=0.8
            )
            
            output = {
                'learnings': learnings,
                'action_id': action_id,
                'improvements': ['strategy_fitness_updated']
            }
            
            return PhaseResult(
                phase=Phase.SELF_REFLECTION,
                success=True,
                output=output,
                confidence=0.85,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[]
            )
        
        except Exception as e:
            logger.error(f"Phase 1 learning failed: {e}")
            return PhaseResult(
                phase=Phase.SELF_REFLECTION,
                success=False,
                output={'error': str(e)},
                confidence=0.0,
                duration_seconds=(datetime.now() - start).total_seconds(),
                triggered_phases=[]
            )
    
    def get_orchestrator_summary(self) -> Dict[str, Any]:
        """Get summary of orchestrator state"""
        return {
            'phases_available': 14,
            'recent_insights': len(self.recent_insights),
            'active_cascades': len(self.active_cascades),
            'inference_summary': self.inference.get_intelligence_summary(),
            'research_summary': self.research.get_research_summary(),
            'social_summary': self.social.get_social_summary(),
            'creative_summary': self.creative.get_creative_summary(),
            'meta_summary': self.metacognition.get_metacognitive_summary(),
            'multi_platform_summary': self.multi_platform.get_engine_summary()
        }
    
    def run_multi_platform_cycle(self, topic: str = None, platforms: List[str] = None) -> Dict[str, Any]:
        """
        Run a multi-platform content cycle using the unified engine.
        
        Detects cross-platform trends, creates content for multiple platforms, and executes.
        """
        logger.info(f"🌐 Starting multi-platform cycle for topic: {topic}")
        
        # Step 1: Detect cross-platform trends
        cross_trends = self.multi_platform.detect_cross_platform_trends(hours=24)
        
        # Use detected trend if no topic provided
        if not topic and cross_trends:
            topic = cross_trends[0].topic
            logger.info(f"   Using trending topic: {topic}")
        elif not topic:
            topic = "AI and blockchain convergence"
        
        # Step 2: Check on-chain signals
        on_chain_signals = self.multi_platform.check_on_chain_signals()
        
        # Step 3: Determine target platforms
        if platforms:
            target_platforms = [Platform(p) for p in platforms if hasattr(Platform, p.upper())]
        else:
            # Use available platforms
            target_platforms = [p for p, available in self.multi_platform.available_platforms.items() if available]
        
        if not target_platforms:
            return {'success': False, 'error': 'No platforms available'}
        
        # Step 4: Create multi-platform campaign
        campaign = self.multi_platform.create_multi_platform_content(
            topic=topic,
            platforms=target_platforms,
            include_image=True
        )
        
        # Step 5: Execute campaign
        results = self.multi_platform.execute_campaign(campaign, a2a_coordination=False)
        
        # Step 6: Trigger ERC-8004 evolution if successful
        self.multi_platform.trigger_erc8004_evolution(results)
        
        # Log the cycle
        successful_posts = sum(1 for r in results.values() if r.get('success'))
        
        return {
            'success': successful_posts > 0,
            'topic': topic,
            'campaign_id': campaign.id,
            'platforms_targeted': len(target_platforms),
            'platforms_succeeded': successful_posts,
            'cross_trends_detected': len(cross_trends),
            'on_chain_signals': len(on_chain_signals),
            'platform_results': {p.value: r for p, r in results.items()}
        }


# Singleton
_orchestrator_instance: Optional[AGIOrchestrator] = None


def get_agi_orchestrator(core=None) -> AGIOrchestrator:
    """Get or create AGI Orchestrator singleton"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AGIOrchestrator(core=core)
    elif core is not None:
        # Update core reference if provided
        _orchestrator_instance.core = core
    return _orchestrator_instance
