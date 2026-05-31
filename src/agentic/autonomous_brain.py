"""
AlleyBot Autonomous Brain System

The core AGI component that enables Alley to act autonomously without commands.
Runs a continuous loop that:
1. Gathers context from all platforms
2. Decides actions via SyMod
3. Executes via plugins
4. Learns from outcomes

Part of AGI Core - Phase 1: Self-Reflection System
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass

from src.agentic.action_logger import ActionLogger
from src.agentic.symod_core import get_symod_manager, SyModObservation
from src.agentic.skilldoc_manager import get_skilldoc_manager
from src.agentic.agi_social_mixin import AGISocialMixin
from src.agentic.agi_orchestrator import get_agi_orchestrator
from src.agentic.moltx_agi_integration import gather_moltx_service_insights
from src.agentic.cross_platform_intel import get_cross_platform_intelligence
from src.agentic.opportunity_monitor import get_opportunity_monitor
from src.agentic.outcome_learner import get_outcome_learner
from src.agentic.trading_observations import gather_trading_observations

# New AGI Foundation Systems
from src.agentic.unified_reasoner import get_unified_reasoner
from src.agentic.knowledge_graph import get_knowledge_graph
from src.agentic.transfer_learner import get_transfer_learner
from src.agentic.symbolic_engine import get_symbolic_engine
from src.agentic.goal_hierarchy import get_goal_hierarchy
from src.agentic.multi_timescale_planner import get_multi_timescale_planner
from src.agentic.meta_learner import get_meta_learner
from src.agentic.goal_manager import get_goal_manager
from src.agentic.default_goals import get_default_goal_seeder

# AGI Framework: Causal reasoning, meta-learning, attentional focus
from src.agentic.causal_engine import get_causal_engine
from src.agentic.contextual_awareness import ContextualAwareness
from src.agentic.meta_learning import create_meta_learning_engine

# Theory of Mind: belief attribution, intent inference, perspective-taking
from src.agentic.theory_of_mind import get_theory_of_mind

# Cognitive Integration: BeliefEngine, SelfModel, GoalPlanner replace Duat/Synergy numerology
from src.agentic.cognitive_integration import get_cognitive

# Phase 5: Brain module decomposition
from src.agentic.brain import create_cycle_coordinator

# Phase 8-9: Service Integration Layer
from src.agentic.service_integration import (
    get_integrated_work_item_service,
    get_integrated_notification_service,
    get_integrated_memory_service,
)
from src.agentic.contracts import NotificationPriority

logger = logging.getLogger(__name__)


@dataclass
class BrainConfig:
    """Configuration for autonomous brain operation"""
    enabled: bool = True
    mode: str = 'normal'  # conservative, normal, aggressive
    cycle_interval_minutes: int = 10  # 10 min default for proactive behavior
    max_actions_per_hour: int = 50
    min_confidence: float = 0.35
    require_owner_approval: bool = False  # HITL still active for high-risk via ActionRouter
    
    # Goal Quota System - Enforce minimum productivity
    min_goals_per_hour: int = 3
    goal_quota_strict: bool = False  # disabled — emergency goals create busywork, not value
    goal_quality_threshold: float = 0.6  # Minimum quality score for goals to count
    
    # Proactive Goal Generation
    proactive_goal_generation: bool = True  # Self-create goals from observations
    curiosity_drive_enabled: bool = True  # Explore when idle
    opportunity_detection: bool = True  # Create goals from detected opportunities
    
    # Mode-specific overrides
    @classmethod
    def from_mode(cls, mode: str) -> 'BrainConfig':
        configs = {
            'conservative': cls(
                enabled=True,
                mode='conservative',
                cycle_interval_minutes=30,
                max_actions_per_hour=20,
                min_confidence=0.5,
                require_owner_approval=False,
                min_goals_per_hour=2,
                goal_quota_strict=False,
                proactive_goal_generation=True,
                curiosity_drive_enabled=True
            ),
            'normal': cls(
                enabled=True,
                mode='normal',
                cycle_interval_minutes=10,
                max_actions_per_hour=50,
                min_confidence=0.35,
                require_owner_approval=False,
                min_goals_per_hour=3,
                goal_quota_strict=False,
                proactive_goal_generation=True,
                curiosity_drive_enabled=True
            ),
            'aggressive': cls(
                enabled=True,
                mode='aggressive',
                cycle_interval_minutes=5,
                max_actions_per_hour=100,
                min_confidence=0.25,
                require_owner_approval=False,
                min_goals_per_hour=5,
                goal_quota_strict=False,
                proactive_goal_generation=True,
                curiosity_drive_enabled=True,
                opportunity_detection=True
            )
        }
        return configs.get(mode, cls())


class AutonomousBrain(AGISocialMixin):
    """
    Alley's autonomous decision-making and action system.
    
    Once started, this runs continuously without human input:
    - Wakes up every N minutes
    - Gathers observations from all platforms
    - Asks SyMod what to do
    - Executes actions via plugins
    - Logs outcomes for learning
    
    Usage:
        brain = AutonomousBrain(core, plugin_manager, symod)
        
        # Start autonomous mode
        await brain.start(mode='normal')
        
        # Alley now acts on his own...
        
        # Check status
        status = brain.get_status()
        
        # Stop
        await brain.stop()
    """
    
    def __init__(self, core=None, plugin_manager=None, symod=None):
        self.core = core
        self.plugin_manager = plugin_manager
        self.symod = symod or get_symod_manager()
        
        # Duat Cognition Engine removed — replaced by CognitiveIntegration
        self.cognitive = get_cognitive()
        
        # Phase 5: Cycle coordinator for modular brain phases
        self.coordinator = create_cycle_coordinator(self)
        
        # Configuration
        self.config = BrainConfig()
        
        # Action logging
        self.action_logger = ActionLogger()
        
        # Runtime state
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_cycle: Optional[datetime] = None
        self._actions_this_hour = 0
        self._hour_start = datetime.now()
        
        # Goal Quota Tracking
        self._goals_this_hour = 0
        self._goals_completed_this_hour = 0
        self._goal_quota_hour_start = datetime.now()
        self._emergency_goals_generated = 0
        
        # Statistics
        self.stats = {
            'cycles_completed': 0,
            'actions_taken': 0,
            'actions_blocked': 0,
            'errors': 0,
            'start_time': None,
            'goals_completed_total': 0,
            'goals_failed_total': 0,
            'quota_warnings': 0
        }
        
        # Skill documentation manager
        self.skilldoc_manager = get_skilldoc_manager()
        self._skilldoc_task: Optional[asyncio.Task] = None
        
        # AGI Orchestrator integration
        self.agi_orchestrator = get_agi_orchestrator(core=core)
        
        # New autonomy systems
        self.cross_platform_intel = get_cross_platform_intelligence(plugin_manager) if plugin_manager else None
        self.opportunity_monitor = get_opportunity_monitor(plugin_manager) if plugin_manager else None
        self.outcome_learner = get_outcome_learner(core) if core else None
        
        # Auto skill building
        from src.agentic.auto_skill_builder import get_auto_skill_builder
        self.auto_skill_builder = get_auto_skill_builder(core, plugin_manager) if core and plugin_manager else None
        
        # Autonomous trading (disabled by default, must be explicitly enabled)
        from src.agentic.autonomous_trading import get_autonomous_trading
        self.autonomous_trading = get_autonomous_trading(core, plugin_manager) if core and plugin_manager else None
        
        # Theory of Mind: belief attribution, intent inference, perspective-taking
        self.theory_of_mind = get_theory_of_mind()
        self.owner_inferred_intent: Optional['IntentInference'] = None
        self.owner_predicted_next_action: Optional[str] = None
        
        # AGI Foundation Systems (85% AGI)
        self.knowledge_graph = get_knowledge_graph()
        # Seed knowledge graph from existing beliefs and plugins
        try:
            if hasattr(self, 'cognitive') and self.cognitive:
                belief_engine = getattr(self.cognitive, 'belief_engine', None)
                if belief_engine:
                    self.knowledge_graph.seed_from_beliefs(belief_engine)
            if self.plugin_manager:
                self.knowledge_graph.seed_from_plugin_list(self.plugin_manager)
        except Exception as e:
            logger.debug(f"Knowledge graph seeding failed: {e}")
        self.symbolic_engine = get_symbolic_engine()
        self.unified_reasoner = get_unified_reasoner(
            knowledge_graph=self.knowledge_graph,
            symbolic_engine=self.symbolic_engine,
            plugin_manager=plugin_manager
        )
        self.transfer_learner = get_transfer_learner(knowledge_graph=self.knowledge_graph)
        self.goal_hierarchy = get_goal_hierarchy()
        self.planner = get_multi_timescale_planner(goal_hierarchy=self.goal_hierarchy)
        self.meta_learner = get_meta_learner(knowledge_graph=self.knowledge_graph)
        self.goal_manager_v2 = get_goal_manager()

        # Causal engine for counterfactual reasoning and root cause analysis
        self.causal_engine = get_causal_engine(action_logger=self.action_logger)

        # Meta-learning engine for adaptive learning parameters per domain
        self.meta_learning_engine = create_meta_learning_engine()

        # Contextual awareness for attentional focus during observation gathering
        self.context_awareness = ContextualAwareness()
        
        # Phase 8-9: Foundation Services Integration
        self.work_item_service = get_integrated_work_item_service()
        self.notification_service = get_integrated_notification_service()
        self.memory_service = get_integrated_memory_service()
        
        # Flag for service availability
        self._services_available = all([
            self.work_item_service is not None,
            self.notification_service is not None,
        ])
        
        if self._services_available:
            logger.info("✅ Foundation Services connected (work items + notifications)")
        else:
            logger.warning("⚠️ Some foundation services unavailable, using fallbacks")
        
        # Initialize AGI social behaviors
        AGISocialMixin.__init__(self)
        
        logger.info("🧠 AutonomousBrain initialized")
        logger.info(f"🎭 AGI Orchestrator: {'✅ Connected' if self.agi_orchestrator else '❌ Not available'}")
        logger.info(f"🔗 Cross-Platform Intel: {'✅ Active' if self.cross_platform_intel else '❌ Not available'}")
        logger.info(f"👁️ Opportunity Monitor: {'✅ Active' if self.opportunity_monitor else '❌ Not available'}")
        logger.info(f"📊 Outcome Learner: {'✅ Active' if self.outcome_learner else '❌ Not available'}")
        
        # Log AGI Foundation Systems
        logger.info("\n🚀 === AGI FOUNDATION SYSTEMS (85% AGI) ===")
        logger.info(f"🧠 Unified Reasoner: {'✅ Active' if self.unified_reasoner else '❌ Not available'}")
        logger.info(f"🕸️ Knowledge Graph: {'✅ Active' if self.knowledge_graph else '❌ Not available'} ({self.knowledge_graph.get_statistics()['total_entities']} entities)")
        logger.info(f"🔄 Transfer Learner: {'✅ Active' if self.transfer_learner else '❌ Not available'} ({len(self.transfer_learner.patterns)} patterns)")
        logger.info(f"⚙️ Symbolic Engine: {'✅ Active' if self.symbolic_engine else '❌ Not available'} ({len(self.symbolic_engine.rules)} rules)")
        logger.info(f"🎯 Goal Hierarchy: {'✅ Active' if self.goal_hierarchy else '❌ Not available'} ({len(self.goal_hierarchy.goals)} goals)")
        logger.info(f"📋 Multi-Timescale Planner: {'✅ Active' if self.planner else '❌ Not available'}")
        logger.info(f"📚 Meta-Learner: {'✅ Active' if self.meta_learner else '❌ Not available'} ({len(self.meta_learner.strategies)} strategies)")
        logger.info("=" * 50)
    
    def register_plugins_with_symod(self) -> None:
        """Register all loaded plugins with SyMod for observations"""
        if not self.plugin_manager:
            return
        
        registered = 0
        for plugin_name in self.plugin_manager.list_loaded():
            try:
                # Register with SyMod
                self.symod.register_plugin(
                    plugin_name,
                    plugin_config={
                        'capabilities': ['observe', 'act', 'reflect'],
                        'metadata': {'auto_register': True}
                    }
                )
                registered += 1
                logger.info(f"✅ Plugin '{plugin_name}' registered with SyMod")
            except Exception as e:
                logger.warning(f"⚠ Plugin {plugin_name} not registered with SyMod: {e}")
        
        logger.info(f"📝 Registered {registered} plugins with SyMod")
    
    async def start(self, mode: str = 'normal') -> str:
        """
        Start autonomous brain loop.
        
        Args:
            mode: 'conservative', 'normal', or 'aggressive'
        
        Returns:
            Status message
        """
        if self._running:
            return "⚠️ Brain already running"
        
        self.config = BrainConfig.from_mode(mode)
        self.config.enabled = True
        
        self._running = True
        self.stats['start_time'] = datetime.now()
        self._hour_start = datetime.now()
        
        # Register all plugins with SyMod (non-blocking)
        try:
            self.register_plugins_with_symod()
        except Exception as e:
            logger.warning(f"⚠️ Plugin registration warning: {e}")
        
        # Get or create event loop
        self._created_loop = False
        try:
            loop = asyncio.get_running_loop()
            self._loop = loop
        except RuntimeError:
            # No running loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            self._created_loop = True  # Track that we created it so we can close it
        
        # Start background tasks in the event loop (non-blocking)
        self._task = loop.create_task(self._brain_loop())
        self._skilldoc_task = loop.create_task(self._skilldoc_check_loop())
        
        msg = (
            f"🧠 Autonomous Brain Started\n"
            f"Mode: {mode.upper()}\n"
            f"Cycle: {self.config.cycle_interval_minutes} min\n"
            f"Max actions/hour: {self.config.max_actions_per_hour}\n"
            f"Min confidence: {self.config.min_confidence}\n"
            f"Owner approval: {'✅ Yes' if self.config.require_owner_approval else '❌ No'}"
        )
        logger.info(msg)
        return msg
    
    async def stop(self) -> str:
        """Stop autonomous brain loop"""
        if not self._running:
            return "⚠️ Brain not running"
        
        self._running = False
        self.config.enabled = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Stop skilldoc checker
        if self._skilldoc_task:
            self._skilldoc_task.cancel()
            try:
                await self._skilldoc_task
            except asyncio.CancelledError:
                pass
        
        # Close event loop if we created it
        if self._created_loop and self._loop and not self._loop.is_closed():
            try:
                self._loop.close()
                logger.debug("✅ Event loop closed")
            except Exception as e:
                logger.warning(f"⚠️  Error closing event loop: {e}")
        
        uptime = datetime.now() - self.stats['start_time'] if self.stats['start_time'] else timedelta(0)
        
        msg = (
            f"🛑 Brain Stopped\n"
            f"Uptime: {uptime}\n"
            f"Cycles: {self.stats['cycles_completed']}\n"
            f"Actions: {self.stats['actions_taken']}\n"
            f"Success Rate: {self._get_success_rate():.1%}"
        )
        logger.info(msg)
        return msg
    
    async def _brain_loop(self) -> None:
        """Main autonomous loop with error recovery"""
        logger.info("🔄 Brain loop started")
        
        # Get error recovery system
        from src.agentic.error_recovery import get_error_recovery
        error_recovery = get_error_recovery(self.plugin_manager)
        
        while self._running:
            try:
                cycle_start = datetime.now()
                
                # Check rate limit (reset hourly)
                if (cycle_start - self._hour_start).total_seconds() > 3600:
                    self._actions_this_hour = 0
                    self._hour_start = cycle_start
                
                # Check if we can act
                if self._actions_this_hour < self.config.max_actions_per_hour:
                    # Execute one cycle
                    await self._execute_cycle()
                    self.stats['cycles_completed'] += 1
                else:
                    logger.info("⏸️ Hourly action limit reached, skipping cycle")
                
                self._last_cycle = datetime.now()
                
                # Sleep until next cycle
                sleep_seconds = self.config.cycle_interval_minutes * 60
                
                # Break sleep into chunks to allow quick shutdown
                while sleep_seconds > 0 and self._running:
                    await asyncio.sleep(min(5, sleep_seconds))
                    sleep_seconds -= 5
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Brain loop error: {e}")
                self.stats['errors'] += 1
                
                # Record error and attempt recovery
                if error_recovery:
                    error_recovery.record_error('brain', e, severity='high')
                    recovery_success = await error_recovery.attempt_recovery('brain', e)
                    if not recovery_success:
                        logger.warning("⚠️ Recovery failed, continuing with backoff...")
                
                await asyncio.sleep(60)  # Brief pause on error
        
        logger.info("🔄 Brain loop stopped")
    
    async def _execute_cycle(self) -> None:
        """Execute one full SENSE-THINK-ACT-REFLECT cycle"""
        logger.info("🔄 === Brain Cycle Start ===")
        
        # Cognitive reflection at cycle start: belief calibration + self-model assessment
        cognitive_reflection = self.cognitive.reflect()
        logger.info(
            f"🧠 Cognitive: {cognitive_reflection.get('overall_assessment', 'unknown')} | "
            f"Strengths: {len(cognitive_reflection.get('strengths', []))} | "
            f"Weaknesses: {len(cognitive_reflection.get('weaknesses', []))} | "
            f"Calibrated: {cognitive_reflection.get('calibration', {}).get('calibrated', 'unknown')}"
        )
        
        # Self-healing: Retry degraded plugins every cycle
        if self.core and hasattr(self.core, 'plugin_manager'):
            try:
                recovered = self.core.plugin_manager.retry_degraded_plugins()
                if recovered:
                    logger.info(f"🔧 Plugin self-heal: {', '.join(recovered)} recovered")
            except Exception as e:
                logger.debug(f"Plugin retry error: {e}")
        
        # Duat replaced by CognitiveIntegration — reflection is above
        
        active_work_items: List[Dict[str, Any]] = []
        spine_context: Dict[str, Any] = {}
        opportunities = []
        
        # === OPPORTUNITY DETECTION: Scan for interrupts + create work items ===
        opportunities = await self._phase_detect_opportunities()
        
        # === SENSE: Gather observations from all platforms ===
        observations = await self._gather_observations()
        logger.info(f"👁️ Gathered {len(observations)} observations")
        
        # Get AGI Kernel reference early for all AGI features
        agi_kernel = getattr(self.core, 'agi_kernel', None) if self.core else None
        
        # === CROSS-PLATFORM SYNTHESIS: Connect dots across platforms ===
        if self.cross_platform_intel:
            synthesis = self.cross_platform_intel.synthesize_observations(observations)
            cross_platform_topics = synthesis.get('cross_platform_topics', [])
            opportunities = synthesis.get('opportunities', [])
            
            if cross_platform_topics:
                logger.info(f"🔗 Found {len(cross_platform_topics)} cross-platform topics")
            if opportunities:
                logger.info(f"💡 Identified {len(opportunities)} cross-platform opportunities")
        
        # === CROSS-DOMAIN PATTERN DETECTION: Horizontal Intelligence ===
        # This is HORIZONTAL synthesis - detecting patterns across domains
        if agi_kernel and hasattr(agi_kernel, 'pattern_detector'):
            try:
                patterns = agi_kernel.pattern_detector.detect_patterns(observations)
                
                if patterns:
                    logger.info(f"🔍 Detected {len(patterns)} cross-domain patterns")
                    
                    # Log top patterns
                    for pattern in patterns[:3]:  # Top 3
                        logger.info(f"   📊 {pattern.pattern_type}: {pattern.description} (confidence: {pattern.confidence:.2f})")
                    
                    # Generate strategy from patterns
                    strategy = agi_kernel.pattern_detector.generate_strategy_from_patterns(patterns)
                    
                    if strategy:
                        logger.info(f"🎯 Generated multi-domain strategy from {strategy['based_on_pattern']} pattern")
                        logger.info(f"   Actions: {len(strategy['actions'])} cross-domain actions")
                        
                        # Store strategy for execution
                        if not hasattr(self, '_cross_domain_strategies'):
                            self._cross_domain_strategies = []
                        self._cross_domain_strategies.append(strategy)
                        
            except Exception as e:
                logger.debug(f"Cross-domain pattern detection error: {e}")
        
        # Submit to SyMod
        for obs in observations:
            self.symod.observe(obs)

        # === THEORY OF MIND: Infer user intent from observed actions ===
        owner_intent = self._phase_theory_of_mind(observations)
        if owner_intent:
            logger.info(f"🎯 ToM inferred owner intent: {owner_intent.inferred_intent} (conf: {owner_intent.confidence:.2f})")

        # === CAUSAL REASONING: Counterfactual simulation + root cause analysis ===
        await self._phase_causal_reasoning(observations, agi_kernel)

        # === FEED WORLD STATE DB: pipe observations so inference engine has real data ===
        await self._feed_observations_to_world_state(observations)

        # === WORK-FIRST CONTINUITY: Pull active meaningful work before broad proposal generation ===
        if agi_kernel and hasattr(agi_kernel, 'get_active_work_items'):
            try:
                active_work_items = agi_kernel.get_active_work_items(limit=5) or []
                # Filter out None items and ensure they're dicts
                active_work_items = [item for item in active_work_items if item and isinstance(item, dict)]
                if active_work_items:
                    top_work_item = active_work_items[0]
                    logger.info(
                        f"🧵 Active work items: {len(active_work_items)} | Top: {top_work_item.get('summary', 'unknown work')}"
                    )
                else:
                    # === AUTO-GENERATE DEFAULT GOALS: When no work items exist ===
                    logger.info("🎯 No active work items - auto-generating safe default goals")
                    default_goals_created = await self._generate_default_goals()
                    if default_goals_created:
                        # Refresh work items after creating goals
                        active_work_items = agi_kernel.get_active_work_items(limit=5) or []
                        active_work_items = [item for item in active_work_items if item and isinstance(item, dict)]
            except Exception as e:
                logger.debug(f"Could not load active work items for cycle: {e}")

        spine_context = self._build_runtime_spine_context(
            observations=observations,
            active_work_items=active_work_items,
            opportunities=opportunities,
        )
        self._log_runtime_spine_context(spine_context)
        
        # === SKILL GAP ANALYSIS: detect gaps + auto-build skills ===
        await self._phase_skill_gap_analysis(observations, agi_kernel)
        
        # === AUTONOMOUS TRADING: Analyze markets and execute SyMod-validated trades ===
        # ENABLED: Trading is now fully autonomous when trading system is available
        if self.autonomous_trading:
            try:
                # Analyze markets with SyMod validation
                trade_proposals = await self.autonomous_trading.analyze_markets()
                
                if trade_proposals:
                    logger.info(f"💰 Found {len(trade_proposals)} SyMod-validated trade opportunities")
                    
                    # Execute best trade (highest confidence)
                    best_trade = max(trade_proposals, key=lambda t: t.confidence)
                    trade_outcome = await self.autonomous_trading.execute_trade(best_trade)
                    
                    if trade_outcome:
                        logger.info(f"✅ Executed autonomous trade: {trade_outcome.trade_id}")
                        # Notify owner of trade
                        telegram = self.plugin_manager.get_plugin('telegram') if self.plugin_manager else None
                        if telegram and hasattr(telegram, 'notify_autonomous_activity'):
                            telegram.notify_autonomous_activity(
                                'autonomous_trade',
                                f"Executed trade: {trade_outcome.trade_id}"
                            )
            except Exception as e:
                logger.warning(f"⚠️ Autonomous trading error: {e}")
        
        # === GOAL MANAGEMENT: generation, approval, activation ===
        next_action = self._phase_goal_management(agi_kernel, observations)

        # === MEMORY-FIRST THINKING: Query semantic memory before LLM ===
        memory_proposals = await self._phase_memory_driven_thinking(observations, agi_kernel)
        if memory_proposals:
            logger.info(f"🧠 Memory-driven proposals: {len(memory_proposals)} (from semantic recall)")

        # === AGI ORCHESTRATION: Run full AGI cycle analysis ===
        agi_actions = await self._run_agi_orchestration_cycle()
        logger.info(f"🎭 AGI Orchestrator: {len(agi_actions)} actions generated")
        
        # === UNIFIED REASONING: Use AGI reasoning for complex decisions ===
        if self.unified_reasoner and observations:
            # Use unified reasoner for strategic decisions
            from src.agentic.unified_reasoner import ReasoningContext, ReasoningType
            
            # Example: Reason about what to do next
            reasoning_context = ReasoningContext(
                problem="What should I focus on based on current observations?",
                domain="general",
                reasoning_type=ReasoningType.STRATEGIC,
                related_domains=['social', 'trading', 'planning'],
                goal="Maximize impact and learning"
            )
            
            reasoning_result = self.unified_reasoner.reason(reasoning_context)
            if reasoning_result.confidence > 0.7:
                logger.info(f"🧠 Unified Reasoning: {reasoning_result.explanation[:100]}...")
        
        # === PERIODIC REFLECTION: Meta-cognition + performance optimization ===
        await self._phase_periodic_reflection(agi_kernel)

        # === CONSOLIDATE LEARNING: Sleep-cycle replay of high-value memories ===
        await self._phase_consolidate_learning(agi_kernel)

        # === PLUGIN DISCOVERY: Auto-generate plugins for detected capability gaps ===
        await self._phase_plugin_discovery_and_creation(agi_kernel)

        # === LEARNING ACQUISITION: Turn curiosity gaps + self-model weaknesses into real skills ===
        await self._phase_learning_goal_acquisition(agi_kernel)

        # === REVENUE INTELLIGENCE: Scan for profit opportunities, track P&L (HIGH PRIORITY) ===
        revenue_proposals = await self._phase_revenue_intelligence(agi_kernel)

        # === PHASE 3.7: Curiosity-driven self-directed goals (BEFORE SyMod/LLM) ===
        curiosity_proposals = await self._phase_curiosity_goals(agi_kernel)
        
        # === PERSISTENT INTENTS: Generate actions for long-running objectives (Phase 3.1) ===
        intent_proposals = await self._phase_maintain_persistent_intents(agi_kernel)

        # === THINK: Assemble and rank proposals ===
        proposals = await self._phase_assemble_proposals(agi_kernel, agi_actions, active_work_items, spine_context, memory_proposals, revenue_proposals, curiosity_proposals, intent_proposals)
        
        # === CROSS-DOMAIN SYNTHESIS & STRATEGIC PLANNING (Phase 4.1-4.2) ===
        await self._phase_cross_domain_synthesis_and_planning(agi_kernel, observations, proposals)
        
        # === MOLTX SUGGESTED ACTIONS (routed through Golden Path) ===
        moltx = self.plugin_manager.get_plugin('moltx')
        if moltx and agi_kernel:
            from src.agentic.moltx_agi_integration import build_moltx_suggested_action_specs
            loop = asyncio.get_event_loop()
            moltx_action_specs = await loop.run_in_executor(
                None, build_moltx_suggested_action_specs, moltx, self
            )
            for action_spec in moltx_action_specs:
                if self._actions_this_hour >= self.config.max_actions_per_hour:
                    break
                try:
                    result = await agi_kernel.act(action_spec)
                    if result and result.get('success'):
                        self.stats['actions_taken'] += 1
                        self._actions_this_hour += 1
                        logger.info(f"✅ Routed MoltX suggestion: {action_spec['action_type']}")
                except Exception as e:
                    logger.debug(f"MoltX suggested action routing error: {e}")
        
        # === ACT: Execute proposals ===
        executed = await self._phase_execute_proposals(proposals, agi_kernel, next_action)
        
        # === REFLECT: AGI Social Behaviors ===
        await self._run_agi_social_cycle()
        
        # Cognitive reflection at cycle end: update beliefs from this cycle's outcomes
        cognitive_end = self.cognitive.reflect()
        beliefs = self.cognitive.belief_engine.get_domain_strengths()
        calibration = self.cognitive.get_belief_calibration()
        logger.info(
            f"🧠 Cycle end: {cognitive_end.get('overall_assessment', '?')} | "
            f"Beliefs: {len(beliefs)} domains | "
            f"Calibrated: {calibration.get('calibrated', '?')} | "
            f"Error: {calibration.get('mean_absolute_error', '?')}"
        )

        # === META ADAPTATION: Adjust learning parameters per domain ===
        await self._phase_meta_adaptation(agi_kernel)

        # === 2.8: Plan Execution — advance active plans ===
        plan_result = await self._advance_active_plans(agi_kernel)

        if executed == 0 and not plan_result:
            # Generate and execute exploratory proposals when idle
            exploratory = self._handle_idle_state(active_work_items, proposals, spine_context)
            if exploratory:
                logger.info(f"🚀 Attempting {len(exploratory)} exploratory actions")
                for proposal in exploratory:
                    if proposal.confidence >= self.config.min_confidence:
                        result = await self._execute_proposal(proposal)
                        if result:
                            executed += 1
                            self._actions_this_hour += 1
                            self.stats['actions_taken'] += 1
                            logger.info(f"✅ Executed exploratory action: {proposal.action_type}")
                        await asyncio.sleep(1)  # Brief pause between exploratory actions
        
        logger.info(f"✅ Executed {executed}/{len(proposals)} actions")
        
        # === GOAL QUOTA ENFORCEMENT: Ensure minimum goals per hour ===
        await self._enforce_goal_quota()
        
        logger.info("🔄 === Brain Cycle Complete ===")
    
    async def _gather_observations(self) -> List[SyModObservation]:
        """Gather observations from all enabled plugins.
        
        All plugin API calls (MoltX, Clawbr, etc.) use synchronous requests.get/post
        which block the event loop and starve Telegram polling. We run the sync
        gathering in a thread pool to keep the event loop responsive.
        """
        if not self.plugin_manager:
            return []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._gather_observations_sync)
    
    def _gather_observations_sync(self) -> List[SyModObservation]:
        """Synchronous observation gathering - runs in thread pool."""
        observations = []
        
        # Get from MoltX
        moltx = self.plugin_manager.get_plugin('moltx')
        if moltx and hasattr(moltx, 'get_feed'):
            try:
                # Gather MoltX service message insights for AGI decision-making
                service_insights = gather_moltx_service_insights(moltx)
                observations.extend(service_insights)
                logger.info(f"💡 Gathered {len(service_insights)} MoltX service insights")
                
                # Get regular feed
                feed = moltx.get_feed('global', limit=20)
                if isinstance(feed, dict):
                    posts = feed.get('posts', [])
                    for post in posts:
                        if not isinstance(post, dict):
                            continue
                        obs = SyModObservation(
                            observation_type='post',
                            source_plugin='moltx',
                            data={
                                'id': post.get('id'),
                                'content': post.get('content', ''),
                                'author_id': post.get('author', {}).get('id'),
                                'author_name': post.get('author', {}).get('name'),
                                'likes': post.get('like_count', 0),
                                'hashtags': post.get('hashtags', []),
                                'already_liked': post.get('liked_by_me', False)
                            }
                        )
                        observations.append(obs)
            except Exception as e:
                logger.error(f"❌ Failed to gather from MoltX: {e}")
        
        # Get mentions/notifications
        if moltx and hasattr(moltx, 'get_notifications'):
            try:
                notifs = moltx.get_notifications(limit=10)
                if isinstance(notifs, dict):
                    for notif in notifs.get('notifications', []):
                        if notif.get('type') == 'mention':
                            obs = SyModObservation(
                                observation_type='mention',
                                source_plugin='moltx',
                                data={
                                    'id': notif.get('id'),
                                    'from_user': notif.get('from_user', {}).get('name'),
                                    'content': notif.get('post', {}).get('content'),
                                    'post_id': notif.get('post', {}).get('id')
                                }
                            )
                            observations.append(obs)
            except Exception as e:
                logger.error(f"❌ Failed to gather mentions: {e}")
        
        # Get from Clawbr (enhanced observations for brain decision-making)
        clawbr = self.plugin_manager.get_plugin('clawbr')
        if clawbr and hasattr(clawbr, 'get_global_feed'):
            try:
                feed = clawbr.get_global_feed(sort='recent', limit=20)
                if isinstance(feed, dict):
                    posts = feed.get('posts', [])
                    agent_id = clawbr._get_clawbr_agent_id() if hasattr(clawbr, '_get_clawbr_agent_id') else None
                    for post in posts:
                        if not isinstance(post, dict):
                            continue
                        # Skip our own posts
                        if post.get('authorId') == agent_id:
                            continue
                        # Check if post is interesting (AI/tech content)
                        content = post.get('content', '').lower()
                        keywords = ['ai', 'agent', 'autonomous', 'learning', 'debate', 'blockchain', 'llm', 'model', 'intelligence']
                        is_interesting = any(kw in content for kw in keywords)
                        
                        obs = SyModObservation(
                            observation_type='clawbr_post',
                            source_plugin='clawbr',
                            data={
                                'id': post.get('id'),
                                'content': post.get('content', ''),
                                'author_id': post.get('authorId'),
                                'author_name': post.get('authorName'),
                                'likes': post.get('likesCount', 0),
                                'replies': post.get('repliesCount', 0),
                                'debate_slug': post.get('debateSlug'),
                                'is_interesting': is_interesting,
                                'engagement_score': post.get('likesCount', 0) + post.get('repliesCount', 0) * 2,
                                'already_liked': False,  # Brain will check via memory
                                'already_commented': False,
                                'already_followed': False
                            }
                        )
                        observations.append(obs)
            except Exception as e:
                logger.error(f"❌ Failed to gather from Clawbr: {e}")
        
        # Get from Moltchan
        moltchan = self.plugin_manager.get_plugin('moltchan')
        if moltchan and hasattr(moltchan, 'browse_boards'):
            try:
                boards = moltchan.browse_boards()
                if isinstance(boards, dict) and 'boards' in boards:
                    for board in boards['boards'][:5]:  # Top 5 boards
                        obs = SyModObservation(
                            observation_type='board',
                            source_plugin='moltchan',
                            data={
                                'id': board.get('id'),
                                'name': board.get('name'),
                                'description': board.get('description'),
                                'thread_count': board.get('threadCount', 0)
                            }
                        )
                        observations.append(obs)
            except Exception as e:
                logger.error(f"❌ Failed to gather from Moltchan: {e}")
        
        # Get from Moltroad
        moltroad = self.plugin_manager.get_plugin('moltroad')
        if moltroad and hasattr(moltroad, 'browse_listings'):
            try:
                listings = moltroad.browse_listings()
                if isinstance(listings, dict) and 'listings' in listings:
                    for listing in listings['listings'][:10]:
                        obs = SyModObservation(
                            observation_type='listing',
                            source_plugin='moltroad',
                            data={
                                'id': listing.get('id'),
                                'title': listing.get('title'),
                                'price': listing.get('price'),
                                'category': listing.get('category'),
                                'seller': listing.get('seller', {}).get('name')
                            }
                        )
                        observations.append(obs)
                # Also check bounties
                bounties = moltroad.get_bounties() if hasattr(moltroad, 'get_bounties') else {}
                if isinstance(bounties, dict) and 'bounties' in bounties:
                    for bounty in bounties['bounties'][:5]:
                        obs = SyModObservation(
                            observation_type='bounty',
                            source_plugin='moltroad',
                            data={
                                'id': bounty.get('id'),
                                'title': bounty.get('title'),
                                'reward': bounty.get('reward'),
                                'status': bounty.get('status')
                            }
                        )
                        observations.append(obs)
            except Exception as e:
                logger.error(f"❌ Failed to gather from Moltroad: {e}")
        
        # === TRADING OBSERVATIONS (AUTONOMOUS TRADING ENABLED) ===
        # AGI brain observes market data AND executes trades autonomously
        # Trading is fully enabled - see AUTONOMOUS TRADING section above
        try:
            trading_obs = gather_trading_observations(self.plugin_manager)
            if trading_obs:
                observations.extend(trading_obs)
                logger.info(f"📊 Gathered {len(trading_obs)} trading observations (autonomous trading enabled)")
        except Exception as e:
            logger.error(f"❌ Failed to gather trading observations: {e}")
        
        # Get from Moltbit
        moltbit = self.plugin_manager.get_plugin('moltbit')
        if moltbit and hasattr(moltbit, 'moltbit_status'):
            try:
                status = moltbit.moltbit_status()
                obs = SyModObservation(
                    observation_type='status',
                    source_plugin='moltbit',
                    data={
                        'owner_registered': status.get('owner_registered'),
                        'agent_registered': status.get('agent_registered'),
                        'can_post': status.get('can_post'),
                        'agent_handle': status.get('agent_handle')
                    }
                )
                observations.append(obs)
            except Exception as e:
                logger.error(f"❌ Failed to gather from Moltbit: {e}")
        
        # === CHAIN OBSERVATIONS (Base + Apechain mempool/block watching) ===
        onchain = self.plugin_manager.get_plugin('onchain') if self.plugin_manager else None
        if onchain and hasattr(onchain, 'poll_chains'):
            try:
                chain_obs = onchain.poll_chains()
                for co in chain_obs:
                    obs = SyModObservation(
                        observation_type='chain_transaction',
                        source_plugin='onchain',
                        data=co,
                        importance=0.6 if co.get('value_eth', 0) >= 1.0 else 0.3,
                    )
                    observations.append(obs)
                if chain_obs:
                    logger.info(f"⛓️ Gathered {len(chain_obs)} chain observations")
            except Exception as e:
                logger.debug(f"Chain observation error: {e}")
        
        # Attentional focus: filter observations based on user state context
        if self.context_awareness:
            try:
                ctx = self.context_awareness.get_current_context()
                user_state = ctx.user_state.name if hasattr(ctx, 'user_state') else 'UNKNOWN'
                if user_state in ('BUSY', 'AWAY'):
                    # User is busy: keep only high-value observations
                    before = len(observations)
                    important_types = {'mention', 'chain_transaction', 'reply'}
                    observations = [o for o in observations
                                    if o.observation_type in important_types
                                    or o.importance >= 0.6]
                    logger.info(f"🎯 Attentional focus ({user_state}): filtered {before} → {len(observations)} observations")
                elif user_state == 'FOCUSED':
                    # User is focused: reduce noise from low-importance sources
                    before = len(observations)
                    observations = [o for o in observations
                                    if o.observation_type in ('mention', 'reply')
                                    or o.source_plugin not in ('moltchan', 'moltroad')]
                    logger.info(f"🎯 Attentional focus ({user_state}): filtered {before} → {len(observations)} observations")
            except Exception as e:
                logger.debug(f"Attentional focus error: {e}")

        return observations

    async def _feed_observations_to_world_state(self, observations: List[SyModObservation]) -> None:
        """Write gathered platform observations into world state DB so inference engine has real data."""
        try:
            from src.autonomy.world_state import get_world_state_manager, Entity, Fact
            import json as _json
            ws = get_world_state_manager()
            written = 0
            for obs in observations:
                content = obs.data.get('content', '')
                if not content:
                    continue
                entity_id = obs.data.get('id') or obs.data.get('author_id') or f"{obs.source_plugin}_{obs.observation_type}"
                author_name = obs.data.get('author_name') or obs.data.get('from_user') or obs.source_plugin
                # Upsert entity
                entity = Entity(
                    id=str(entity_id),
                    type='post' if obs.observation_type == 'post' else 'user',
                    name=str(author_name),
                    platform=obs.source_plugin,
                )
                ws.add_entity(entity)
                # Write content fact — this is what _get_recent_interactions() queries
                fact = Fact(
                    entity_id=str(entity_id),
                    attribute='content',
                    value=_json.dumps({
                        'content': content,
                        'platform': obs.source_plugin,
                        'likes': obs.data.get('likes', 0),
                        'hashtags': obs.data.get('hashtags', []),
                    }),
                    value_type='json',
                    source=obs.source_plugin,
                    confidence=0.9,
                )
                ws.add_fact(fact)
                written += 1
            if written:
                logger.debug(f"🌍 World state: wrote {written} observations from {len(observations)} gathered")
        except Exception as e:
            logger.warning(f"⚠️ Failed to feed world state: {e}")

    async def _skilldoc_check_loop(self):
        """Periodic check for skill.md updates"""
        await asyncio.sleep(30)  # Wait for bot to fully initialize
        
        while self._running:
            try:
                print("📚 Checking skill.md documentation for updates...")
                results = await self.skilldoc_manager.check_for_updates()
                
                updated = [p for p, r in results.items() if r.get('updated')]
                errors = [p for p, r in results.items() if r.get('error')]
                
                if updated:
                    print(f"✅ Updated skill.md for: {', '.join(updated)}")
                    for platform in updated:
                        caps = self.skilldoc_manager.extract_api_capabilities(platform)
                        if caps:
                            print(f"📖 {platform} capabilities: {len(caps.get('endpoints', []))} endpoints")
                
                if errors:
                    print(f"⚠️ Failed to check: {', '.join(errors)}")
                
                await asyncio.sleep(6 * 3600)  # Check every 6 hours
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Skilldoc check error: {e}")
                await asyncio.sleep(3600)
    
    def get_skill_doc(self, platform: str) -> Optional[str]:
        """Get skill.md documentation for a platform"""
        return self.skilldoc_manager.get_skill_doc(platform)

    async def _run_agi_social_cycle(self):
        """Run AGI social behaviors - process notifications, reply to comments, follow engaged users.
        
        Plugin notification calls use synchronous HTTP, so we run in thread pool.
        """
        if not self.plugin_manager:
            return
        
        logger.info("🤖 Running AGI Social Cycle")
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run_agi_social_cycle_sync)
        
        if result and (result.get('total_replies', 0) > 0 or result.get('total_follows', 0) > 0):
            logger.info(f"🤖 AGI Social: {result['total_replies']} replies, {result['total_follows']} follows")
    
    def _run_agi_social_cycle_sync(self) -> Dict:
        """Synchronous social cycle - runs in thread pool."""
        platforms = ['moltx', 'clawbr', 'moltchan', 'moltroad', 'moltbit']
        total_replies = 0
        total_follows = 0
        
        for platform in platforms:
            plugin = self.plugin_manager.get_plugin(platform)
            if not plugin:
                continue
            
            try:
                if not hasattr(plugin, 'get_notifications'):
                    continue
                    
                import inspect
                sig = inspect.signature(plugin.get_notifications)
                params = list(sig.parameters.keys())
                
                if 'unread_only' in params:
                    notifs = plugin.get_notifications(unread_only=True)
                elif 'mark_read' in params:
                    notifs = plugin.get_notifications(limit=20, mark_read=False)
                else:
                    notifs = plugin.get_notifications()
                
                if isinstance(notifs, dict):
                    notifications = notifs.get('notifications', [])
                    for notif in notifications:
                        notif_type = notif.get('type', 'unknown')
                        if notif_type in ['mention', 'reply', 'comment']:
                            total_replies += 1
                        elif notif_type in ['like', 'follow']:
                            total_follows += 1
            except Exception as e:
                logger.debug(f"AGI social cycle error for {platform}: {e}")
        
        return {'total_replies': total_replies, 'total_follows': total_follows}

    async def _get_proposals(self) -> List[Any]:
        """Get action proposals from SyMod"""
        from src.agentic.symod_core import SyModActionProposal
        
        proposals = []
        
        # Get available actions per plugin
        if self.plugin_manager:
            for plugin_name in self.plugin_manager.list_loaded():
                plugin = self.plugin_manager.get_plugin(plugin_name)
                if not plugin or not getattr(plugin, 'enabled', True):
                    continue
                
                # Clawbr: check for pending observations and propose actions
                if plugin_name == 'clawbr' and self.core:
                    pending = self.core.get_memory('clawbr_pending_observations') or []
                    if pending:
                        # Clear pending observations (brain will now decide)
                        self.core.save_memory('clawbr_pending_observations', [])
                        
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
                plugin_proposals = self.symod.propose_actions(
                    plugin_name,
                    context={
                        'constraints': {
                            'max_actions': 5,  # Per plugin per cycle
                            'min_confidence': self.config.min_confidence
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

        self._apply_active_goal_bias(proposals)
        self._apply_memory_shaped_ranking(proposals)
        return proposals

    def _get_recent_routed_outcomes(self, limit: int = 40) -> List[Dict[str, Any]]:
        """Return recent routed outcome records from the unified action router when available."""
        if not self.agi_kernel or not hasattr(self.agi_kernel, 'action_router'):
            return []

        router = getattr(self.agi_kernel, 'action_router', None)
        history = getattr(router, 'execution_history', None) if router else None
        if not isinstance(history, list):
            return []
        return history[-limit:]

    def _estimate_predicted_value(self, proposal: Any) -> str:
        """Estimate expected value for a proposal using lightweight heuristics."""
        action_blob = " ".join([
            str(getattr(proposal, 'action_type', '') or ''),
            str(getattr(proposal, 'justification', '') or ''),
            str(getattr(proposal, 'content', '') or ''),
            str((getattr(proposal, 'metadata', {}) or {}).get('goal_category', '') or ''),
        ]).lower()

        if any(token in action_blob for token in ['analy', 'report', 'insight', 'research', 'optimiz', 'improve']):
            return 'high'
        if any(token in action_blob for token in ['reply', 'comment', 'engage', 'follow', 'like']):
            return 'medium'
        return 'low'

    def _recall_memory_signals(self, proposal: Any) -> Dict[str, Any]:
        """Collect lightweight read-only recall signals for proposal shaping.
        
        Uses semantic embedding search (sentence transformers) as primary retrieval,
        falls back to keyword-based episodic memory recall.
        """
        signals = {
            'relevant_memory_count': 0,
            'recent_negative_memory_count': 0,
            'entity_context_found': False,
            'semantic_memory_score': 0.0,
        }

        if not self.agi_kernel:
            return signals

        memory_query = " ".join([
            str(getattr(proposal, 'action_type', '') or ''),
            str(getattr(proposal, 'target_name', '') or ''),
            str(getattr(proposal, 'justification', '') or ''),
        ]).strip()

        # PRIMARY: Semantic vector search via SQLiteMemorySystem
        sqlite_memory = getattr(self.agi_kernel, 'memory', None) or getattr(self.agi_kernel, 'sqlite_memory', None)
        if sqlite_memory and memory_query and hasattr(sqlite_memory, 'search_memories'):
            try:
                semantic_results = sqlite_memory.search_memories(
                    query=memory_query,
                    k=5,
                    min_relevance=0.3
                )
                if semantic_results:
                    signals['relevant_memory_count'] = len(semantic_results)
                    signals['semantic_memory_score'] = max(
                        r['relevance_score'] for r in semantic_results
                    )
                    negative_memories = [
                        r for r in semantic_results
                        if float(r.get('relevance_score', 0.0)) < 0.4
                    ]
                    signals['recent_negative_memory_count'] = len(negative_memories)
            except Exception as e:
                logger.debug(f"Could not search semantic memory: {e}")

        # SECONDARY: Episodic keyword-based recall
        if signals['relevant_memory_count'] == 0:
            episodic_memory = getattr(self.agi_kernel, 'episodic_memory', None)
            if episodic_memory and memory_query and hasattr(episodic_memory, 'recall_relevant'):
                try:
                    recalled = episodic_memory.recall_relevant(memory_query, k=3) or []
                    signals['relevant_memory_count'] = len(recalled)
                    negative_memories = [
                        memory for memory in recalled
                        if float(getattr(memory, 'emotional_valence', 0.0) or 0.0) < -0.2
                    ]
                    signals['recent_negative_memory_count'] = len(negative_memories)
                except Exception as e:
                    logger.debug(f"Could not recall episodic memory for proposal ranking: {e}")

        unified_memory = getattr(self.agi_kernel, 'unified_memory', None)
        target_name = str(getattr(proposal, 'target_name', '') or '')
        if unified_memory and target_name and hasattr(unified_memory, 'get_entity_context'):
            try:
                entity_context = unified_memory.get_entity_context(target_name)
                signals['entity_context_found'] = bool(entity_context)
            except Exception as e:
                logger.debug(f"Could not get unified memory entity context for proposal ranking: {e}")

        return signals

    def _apply_memory_shaped_ranking(self, proposals: List[Any]) -> None:
        """Adjust proposal confidence using routed outcomes, action logger performance data, and semantic memory."""
        if not proposals:
            return

        recent_outcomes = self._get_recent_routed_outcomes()

        # Pull ActionLogger performance data for richer per-action statistics
        action_perf = {}
        if hasattr(self, 'action_logger') and self.action_logger:
            try:
                if hasattr(self.action_logger, 'get_action_performance_summary'):
                    perf_data = self.action_logger.get_action_performance_summary(hours=72, limit=50)
                    if perf_data:
                        action_perf = perf_data
            except Exception as e:
                logger.debug(f"Could not get action performance data: {e}")

        for proposal in proposals:
            metadata = getattr(proposal, 'metadata', None) or {}
            plugin_name = str(metadata.get('plugin', 'unknown') or 'unknown')
            action_type = str(getattr(proposal, 'action_type', '') or '')
            current_confidence = float(getattr(proposal, 'confidence', 0.0) or 0.0)

            matching_outcomes = [
                outcome for outcome in recent_outcomes
                if outcome.get('plugin') == plugin_name and outcome.get('action_type') == action_type
            ]

            success_rate = None
            average_mismatch = None
            if matching_outcomes:
                success_rate = sum(1 for outcome in matching_outcomes if outcome.get('success')) / len(matching_outcomes)
                mismatch_values = [
                    float(outcome.get('mismatch_score', 0.5) or 0.5)
                    for outcome in matching_outcomes
                ]
                average_mismatch = sum(mismatch_values) / len(mismatch_values)

            # Richer stats from ActionLogger
            perf_key = f"{plugin_name}:{action_type}"
            perf_record = action_perf.get(perf_key) or action_perf.get(action_type)
            calibration_bias = perf_record.get('calibration_bias') if perf_record else None
            high_mismatch_rate = perf_record.get('high_mismatch_rate', 0.0) if perf_record else 0.0
            logger_success_rate = perf_record.get('success_rate') if perf_record else None

            predicted_value = self._estimate_predicted_value(proposal)
            adjustment = 0.0

            if predicted_value == 'high':
                adjustment += 0.04
            elif predicted_value == 'medium':
                adjustment += 0.015

            if success_rate is not None:
                if success_rate >= 0.75:
                    adjustment += 0.05
                elif success_rate <= 0.25:
                    adjustment -= 0.06
            elif logger_success_rate is not None:
                if logger_success_rate >= 0.75:
                    adjustment += 0.03
                elif logger_success_rate <= 0.25:
                    adjustment -= 0.04

            if average_mismatch is not None:
                if average_mismatch <= 0.25:
                    adjustment += 0.03
                elif average_mismatch >= 0.65:
                    adjustment -= 0.05

            # Calibration bias correction from ActionLogger
            if calibration_bias == 'overconfident':
                adjustment -= 0.04
            elif calibration_bias == 'underconfident':
                adjustment += 0.03

            # High mismatch rate reduces confidence (agent can't predict itself)
            if high_mismatch_rate > 0.3:
                adjustment -= 0.03

            memory_signals = self._recall_memory_signals(proposal)
            if memory_signals['semantic_memory_score'] >= 0.7:
                adjustment += 0.10
            elif memory_signals['semantic_memory_score'] >= 0.5:
                adjustment += 0.06
            elif memory_signals['relevant_memory_count'] >= 2:
                adjustment += 0.04
            elif memory_signals['relevant_memory_count'] >= 1:
                adjustment += 0.02
            if memory_signals['recent_negative_memory_count'] >= 1:
                adjustment -= 0.08
            if memory_signals['entity_context_found']:
                adjustment += 0.04

            if adjustment != 0.0:
                proposal.confidence = max(0.0, min(current_confidence + adjustment, 0.95))

            if not getattr(proposal, 'metadata', None):
                proposal.metadata = {}
            proposal.metadata['predicted_value'] = predicted_value
            proposal.metadata['memory_relevance_count'] = memory_signals['relevant_memory_count']
            proposal.metadata['negative_memory_count'] = memory_signals['recent_negative_memory_count']
            proposal.metadata['entity_context_found'] = memory_signals['entity_context_found']
            if success_rate is not None:
                proposal.metadata['recent_success_rate'] = round(success_rate, 3)
            if average_mismatch is not None:
                proposal.metadata['recent_mismatch_score'] = round(average_mismatch, 3)
            proposal.metadata['memory_shaped_adjustment'] = round(adjustment, 3)

    def _apply_meta_learning_bias(self, proposals: List[Any]) -> None:
        """Apply meta-learning: bias proposals based on which learning strategies have worked best."""
        if not proposals or not self.meta_learner:
            return
        
        try:
            # Get best performing strategies from meta-learner
            if hasattr(self.meta_learner, 'get_best_strategies'):
                best_strategies = self.meta_learner.get_best_strategies(limit=3)
                
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
    
    def _apply_transfer_learning_bias(self, proposals: List[Any]) -> None:
        """Apply transfer learning: use patterns from successful actions in other domains."""
        if not proposals or not self.transfer_learner:
            return
        
        try:
            for proposal in proposals:
                action_type = str(getattr(proposal, 'action_type', '') or '')
                domain = str((getattr(proposal, 'metadata', {}) or {}).get('plugin', 'unknown'))
                
                # Find applicable patterns from other domains
                if hasattr(self.transfer_learner, 'find_applicable_patterns'):
                    patterns = self.transfer_learner.find_applicable_patterns(
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
    
    def _apply_active_goal_bias(self, proposals: List[Any]) -> None:
        """Lightly bias proposal confidence toward the current safe active goal."""
        if not proposals or not self.goal_manager_v2 or not hasattr(self.goal_manager_v2, 'get_goals'):
            return

        try:
            from src.agentic.goal_manager import GoalStatus

            active_goals = self.goal_manager_v2.get_goals(status=GoalStatus.ACTIVE, limit=1)
            if not active_goals:
                return

            active_goal = active_goals[0]
            goal_text = f"{active_goal.title} {active_goal.description} {active_goal.category}".lower()
            if not self.goal_manager_v2.should_auto_approve_goal(active_goal):
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

    def _apply_active_work_item_bias(self, proposals: List[Any], active_work_items: List[Dict[str, Any]]) -> None:
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
    
    async def _run_agi_orchestration_cycle(self) -> List[Any]:
        """Run AGI Orchestrator cycle and convert results to action proposals"""
        if not self.agi_orchestrator:
            return []
        
        try:
            # Run full AGI cycle
            cycle_result = await self.agi_orchestrator.run_cycle(trigger="brain_cycle")
            
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
                proposal = await self._convert_agi_action_to_proposal(
                    cycle_result.final_action,
                    cycle_result.phases_executed
                )
                if proposal:
                    proposals.append(proposal)
            
            # Process creative content generation (common AGI output)
            for phase_result in cycle_result.phases_executed:
                if (phase_result.phase.value == 'CREATIVE_GENERATION' and 
                    phase_result.success and phase_result.output):
                    
                    creative_proposals = await self._extract_creative_proposals(
                        phase_result.output, cycle_result.phases_executed
                    )
                    proposals.extend(creative_proposals)
            
            logger.info(f"🎭 AGI Orchestrator generated {len(proposals)} action proposals")
            return proposals
            
        except Exception as e:
            logger.error(f"❌ AGI Orchestration error: {e}")
            return []
    
    async def _convert_agi_action_to_proposal(self, agi_action: Dict, phases_executed) -> Optional[Any]:
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
            target_id=None,  # Content posting doesn't need target ID
            target_name=f"AGI_Content_{datetime.now().strftime('%H%M%S')}",
            content=content,
            confidence=confidence,
            justification="AGI Orchestrator generated content based on multi-phase analysis",
            metadata={
                'plugin': platform,
                'trigger': 'agi_orchestrator',
                'phases_used': len(phases_executed),
                'agi_action': action_taken
            }
        )
    
    async def _extract_creative_proposals(self, creative_output: Dict, phases_executed) -> List[Any]:
        """Extract action proposals from creative generation phase, using AI to generate real post content."""
        from src.agentic.symod_core import SyModActionProposal
        
        proposals = []
        
        # Check for recommended content — generate real post text via moltx content pipeline
        recommended = creative_output.get('recommended_content')
        if recommended and isinstance(recommended, dict):
            concept_title = recommended.get('title', '')
            if concept_title:
                # Try to generate real AI post content from the concept
                content = self._generate_post_from_concept(concept_title)
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
        
        # Check for story arcs — generate real post from story theme
        story_arc = creative_output.get('story_arc')
        if story_arc and isinstance(story_arc, dict):
            theme = story_arc.get('title', '')
            if theme:
                content = self._generate_post_from_concept(theme)
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
                            'story_posts': story_arc.get('posts', 0),
                            'concept': theme,
                        }
                    )
                    proposals.append(proposal)
        
        return proposals

    def _generate_post_from_concept(self, concept: str) -> str:
        """Return topic for intelligent posting system (don't generate content here)"""
        # Just return the concept as a topic - intelligent_post will handle generation
        return concept if concept else ''
    
    async def _phase_detect_opportunities(self) -> List:
        """SENSE sub-phase — scan for opportunities and create work items.
        
        Returns list of detected opportunities.
        """
        opportunities = []
        if not self.opportunity_monitor:
            return opportunities
        
        opportunities = self.opportunity_monitor.scan_for_opportunities()
        interrupt_opps = self.opportunity_monitor.get_interrupt_opportunities()
        
        if interrupt_opps:
            logger.warning(f"🚨 {len(interrupt_opps)} high-priority opportunities detected!")
        
        if self.work_item_service and self._services_available and opportunities:
            try:
                for opp in opportunities[:3]:
                    opp_title = opp.get('title', 'Autonomous opportunity')
                    opp_desc = opp.get('description', 'Detected by opportunity monitor')
                    opp_type = opp.get('type', 'opportunity')
                    
                    existing = self.work_item_service.get_active_items()
                    duplicate = any(o.title == opp_title for o in existing)
                    
                    if not duplicate:
                        work_item = self.work_item_service.create_work_item(
                            title=opp_title,
                            description=opp_desc,
                            work_type=opp_type,
                            priority=opp.get('priority', 2),
                            source_signal={
                                'source': 'opportunity_monitor',
                                'confidence': opp.get('confidence', 0.5),
                                'detected_at': datetime.now().isoformat(),
                            },
                        )
                        logger.info(f"📌 Created work item from opportunity: {work_item.id}")
                        
                        if self.notification_service:
                            await self.notification_service.notify(
                                title="🎯 New Work Item Created",
                                message=f"Opportunity detected: {opp_title}",
                                priority=NotificationPriority.LOW,
                                source_work_item=work_item.id,
                            )
            except Exception as e:
                logger.debug(f"Work item creation error (non-critical): {e}")
        
        return opportunities
    
    async def _phase_skill_gap_analysis(self, observations, agi_kernel):
        """THINK sub-phase — detect capability gaps and auto-build skills.
        
        Runs with a cooldown: only every 50 cycles after an initial 10-cycle
        warmup. Prevents skill generation on startup when episodic memory
        may contain stale or malformed entries.
        """
        cycle_count = self.stats.get('cycles_completed', 0)
        
        # Don't run skill gap analysis in the first 10 cycles (warmup)
        if cycle_count < 10:
            return
        
        # Only run skill gap analysis every 50 cycles (cooldown)
        if cycle_count % 50 != 0:
            return
        
        # Phase 1.1: Auto-enable self_improvement domain when 3+ needs_new_skill judgments exist
        if agi_kernel and hasattr(agi_kernel, 'work_item_manager'):
            try:
                wm = agi_kernel.work_item_manager
                # Query work items for repeated needs_new_skill evidence
                all_items = wm.get_all_work_items(limit=100)
                needs_skill_count = 0
                for item in all_items:
                    metadata = item.metadata if hasattr(item, 'metadata') else {}
                    if not metadata:
                        continue
                    judgment = metadata.get('capability_judgment', {})
                    if judgment.get('needs_new_skill'):
                        evidence = metadata.get('upgrade_evidence', {})
                        repeated_count = evidence.get('repeated_need_count', 0)
                        if repeated_count >= 2:
                            needs_skill_count += 1
                
                # Auto-enable self_improvement domain if threshold met
                if needs_skill_count >= 3:
                    profiles = getattr(agi_kernel, 'domain_autonomy_profiles', {})
                    if not profiles.get('self_improvement', {}).get('enabled', False):
                        profiles['self_improvement']['enabled'] = True
                        logger.info(f"🧠 Self-improvement domain AUTO-ENABLED ({needs_skill_count} work items need new skills)")
            except Exception as e:
                logger.debug(f"Could not check work items for skill gaps: {e}")
        
        if self.auto_skill_builder:
            try:
                skill_proposals = await self.auto_skill_builder.detect_capability_gaps(observations)
                if skill_proposals:
                    logger.info(f"💡 Detected {len(skill_proposals)} capability gaps")
                built_count = await self.auto_skill_builder.auto_build_simple_skills(max_skills=1)
                if built_count > 0:
                    logger.info(f"🔨 Auto-built {built_count} new skill(s)")
                    # Reload skill executor so new skills are immediately available
                    if agi_kernel and hasattr(agi_kernel, 'skill_executor') and agi_kernel.skill_executor:
                        agi_kernel.skill_executor.reload_skills()
            except Exception as e:
                logger.warning(f"⚠️ Auto skill building error: {e}")
        
        skill_gaps = await self._detect_skill_gaps(agi_kernel)
        if not skill_gaps:
            return
        
        # Filter out gaps with unknown/generic action types — they're not actionable
        skill_gaps = [g for g in skill_gaps if g.get('action_type', 'unknown') not in ('unknown', 'none', '')]
        if not skill_gaps:
            return
        
        logger.info(f"🔍 Detected {len(skill_gaps)} skill gaps")
        selfimprove_plugin = self.plugin_manager.get_plugin('selfimprove') if self.plugin_manager else None
        
        gap = max(skill_gaps, key=lambda g: g['priority'])
        if gap['priority'] < 4:
            return
        
        logger.info(f"🤖 Auto-generating skill for gap: {gap['description']}")
        try:
            generated = False

            # Prefer selfimprove plugin's full autonomous coder (has AI generation + sandbox + hot-load)
            if hasattr(selfimprove_plugin, '_generate_code_with_ai'):
                task_desc = f"Create a skill to handle: {gap['description']}. "
                if gap.get('error_patterns'):
                    task_desc += f"Must fix these errors: {', '.join(gap['error_patterns'][:3])}"

                if hasattr(selfimprove_plugin, 'self_update_command'):
                    result = selfimprove_plugin.self_update_command(
                        ['create', gap['action_type'].replace(':', '_'), task_desc]
                    )
                    # Handle both string (confirmation needed) and dict (result) returns
                    if isinstance(result, dict) and result.get('success'):
                        logger.info(f"🚀 Self-update generated and deployed: {result.get('plan_id', 'unknown')}")
                        generated = True
                        if agi_kernel and hasattr(agi_kernel, 'episodic_memory'):
                            agi_kernel.episodic_memory.record_episode(
                                action_type='skill_generation',
                                context={'gap': gap, 'result': result},
                                outcome={'success': True, 'deployed': True}
                            )
                    elif isinstance(result, str) and 'pending confirmation' in result.lower():
                        logger.info(f"⏸️ Self-update requires confirmation: {result[:100]}...")
                    else:
                        logger.warning(f"⚠️ Self-update command returned: {result}")

            # Fallback to skeleton autonomous coder if selfimprove is unavailable
            if not generated:
                from src.agentic.autonomous_coder import SkillSpecification, AutonomousCoder

                spec = SkillSpecification(
                    id=f"fix_{gap['action_type'].replace(':', '_')}_{int(datetime.now().timestamp())}",
                    name=f"Fix {gap['action_type']}",
                    description=gap['description'],
                    category='fix',
                    file_structure={
                        '__init__.py': 'Package initialization',
                        'client.py': 'Main skill client',
                        'actions.py': 'Action handlers'
                    },
                    dependencies=[],
                    evidence=gap.get('error_patterns', [])
                )

                coder = AutonomousCoder()
                skill = coder.generate_skill(spec)

                if skill.status == 'generated' and skill.files_created:
                    logger.info(f"✅ Generated skill: {skill.skill_name}")
                    code_to_test = Path(skill.files_created[0]).read_text()
                    if selfimprove_plugin and hasattr(selfimprove_plugin, 'test_code_in_sandbox'):
                        test_result = selfimprove_plugin.test_code_in_sandbox(
                            code=code_to_test,
                            test_code=None
                        )
                        if test_result['success']:
                            coder.deploy_skill(skill)
                            logger.info(f"🚀 Deployed skill: {skill.skill_name}")
                        else:
                            logger.warning(f"⚠️ Skill failed sandbox test: {test_result.get('error', 'Unknown error')}")
                    else:
                        coder.deploy_skill(skill)
                        logger.info(f"🚀 Deployed skill (no sandbox available): {skill.skill_name}")
                elif skill.status == 'generated' and not skill.files_created:
                    logger.warning("⚠️ Skill generated but no files created")
                else:
                    logger.warning(f"⚠️ Skill generation failed: {skill.errors}")
        except Exception as e:
            logger.warning(f"⚠️ Autonomous coding error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    async def _phase_maintain_persistent_intents(self, agi_kernel) -> List:
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
                            'plugin': self._map_intent_action_to_plugin(action['action_type']),
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
    
    def _map_intent_action_to_plugin(self, action_type: str) -> str:
        """Map intent action types to appropriate plugins."""
        mapping = {
            'create_post': 'moltx',
            'engage': 'moltx',
            'analyze': 'analytics',
            'scan': 'crypto',
            'feed': 'moltx',
        }
        return mapping.get(action_type, 'moltx')
    
    async def _phase_cross_domain_synthesis_and_planning(
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
            market_state = self._extract_market_state(observations)
            social_state = self._extract_social_state(observations)
            
            # Run synthesis via orchestrator
            if agi_kernel and hasattr(agi_kernel, 'orchestrator'):
                opportunities = agi_kernel.orchestrator.synthesize_cross_domain_opportunities(
                    observations, market_state, social_state
                )
                
                for opp in opportunities:
                    # Convert to proposal
                    cross_domain_proposal = {
                        'plugin': self._map_intent_action_to_plugin(opp['proposed_action']),
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
    
    def _extract_market_state(self, observations: List[Dict]) -> Dict[str, Any]:
        """Extract market state from observations."""
        volatility_signals = []
        for obs in observations:
            content = str(obs.get('content', '')).lower()
            if any(word in content for word in ['crash', 'surge', 'pump', 'dump', 'volatile']):
                volatility_signals.append(1.0 if 'crash' in content else 0.7)
        
        return {
            'volatility_index': max(volatility_signals) if volatility_signals else 0.3,
            'risk_level': 'high' if volatility_signals else 'low',
        }
    
    def _extract_social_state(self, observations: List[Dict]) -> Dict[str, Any]:
        """Extract social platform state from observations."""
        engagement_signals = []
        trending = []
        
        for obs in observations:
            content = str(obs.get('content', '')).lower()
            if any(word in content for word in ['engaging', 'viral', 'trending']):
                engagement_signals.append(0.8)
            if any(word in content for word in ['trending', 'viral']):
                # Try to extract topic
                words = content.split()
                for i, word in enumerate(words):
                    if word in ['about', 'on'] and i + 1 < len(words):
                        trending.append(words[i + 1])
        
        return {
            'engagement_rate': sum(engagement_signals) / max(len(engagement_signals), 1),
            'trending_topic_match': len(trending) > 0,
            'trending_topics': trending[:3],
        }
    
    async def _phase_memory_driven_thinking(self, observations: List, agi_kernel=None) -> List:
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
        if not sqlite_memory and hasattr(self, 'agi_kernel') and self.agi_kernel:
            sqlite_memory = getattr(self.agi_kernel, 'memory', None) or getattr(self.agi_kernel, 'sqlite_memory', None)

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
        if hasattr(self, 'cognitive') and self.cognitive:
            belief_engine = getattr(self.cognitive, 'belief_engine', None)

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

    async def _phase_assemble_proposals(self, agi_kernel, agi_actions, active_work_items, spine_context, memory_proposals=None, revenue_proposals=None, curiosity_proposals=None, intent_proposals=None):
        """THINK phase — assemble, enrich, and rank all action proposals.
        
        Priority order: curiosity > persistent intents > memory-driven > goal-driven > SyMod > AGI
        Curiosity and intents come first so self-directed exploration outranks reactive work.
        """
        # Get goal-driven action from active autonomous goals
        goal_driven_action = None
        if agi_kernel and hasattr(agi_kernel, 'goal_manager'):
            try:
                goal_manager = agi_kernel.goal_manager
                from src.agentic.goal_manager import GoalStatus
                active_goals = await goal_manager.aget_goals(status=GoalStatus.ACTIVE, limit=5)
                
                if active_goals:
                    for goal in sorted(active_goals, key=lambda g: g.impact_score, reverse=True):
                        na = await goal_manager.aget_next_action_for_goal(goal)
                        if na:
                            goal_driven_action = na
                            logger.info(f"🎯 Goal-driven action: {na['action_type']} for goal '{goal.title}'")
                            if agi_kernel and hasattr(agi_kernel, 'progress_reporter') and agi_kernel.progress_reporter:
                                try:
                                    progress = agi_kernel.progress_reporter.report_goal_progress(goal.id, verify_truth=True)
                                    if progress.get('honest_assessment'):
                                        logger.info(f"   {progress['honest_assessment']}")
                                except Exception as e:
                                    logger.debug(f"Progress report failed for goal {goal.id}: {e}")
                            break
                
                if not active_goals:
                    onchain_plugin = self.plugin_manager.get_plugin('onchain') if self.plugin_manager else None
                    new_goals = goal_manager.scan_and_generate(onchain_plugin=onchain_plugin)
                    if new_goals:
                        logger.info(f"🎯 Generated {len(new_goals)} new autonomous goals from observations")
                        for goal in new_goals:
                            if goal.status in (GoalStatus.ACTIVE, GoalStatus.APPROVED):
                                na = goal_manager.get_next_action_for_goal(goal)
                                if na:
                                    goal_driven_action = na
                                    logger.info(f"🎯 Goal-driven action from new goal: {na['action_type']}")
                                    break
            except Exception as e:
                logger.debug(f"Goal-driven action retrieval error: {e}")
        
        # Combine SyMod + AGI proposals
        proposals = await self._get_proposals()
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
        self._apply_meta_learning_bias(proposals)
        self._apply_transfer_learning_bias(proposals)
        self._apply_active_work_item_bias(proposals, active_work_items)
        self._apply_runtime_spine_bias(proposals, spine_context)
        self._apply_cognitive_bias(proposals)
        proposals = self._prioritize_runtime_spine_proposals(proposals, spine_context)
        logger.info(f"🧠 Generated {len(proposals)} total proposals (AGI learning applied)")
        
        return proposals
    
    # 7.6: Adversarial self-critique - challenge own beliefs
    async def _adversarial_self_critique(self, agi_kernel) -> List[Dict]:
        """
        Periodically challenge own beliefs, look for disconfirming evidence.
        Called every 1000 cycles as part of adversarial reflection.
        """
        findings = []
        
        try:
            # Get all beliefs
            from src.agentic.belief_engine import get_belief_engine
            be = get_belief_engine()
            if not be:
                return findings
            
            beliefs = list(be.beliefs.values())
            
            # Check for high-confidence beliefs with weak evidence
            for belief in beliefs:
                if belief.confidence > 0.7 and belief.prediction_count < 3:
                    findings.append({
                        'belief': belief.proposition,
                        'challenge': 'High confidence but few predictions - overconfident?',
                        'confidence': belief.confidence,
                        'predictions': belief.prediction_count,
                        'strength': 'low_data'
                    })
                
                # Check for beliefs with more negative evidence than positive
                if len(belief.evidence_against) > len(belief.evidence_for) * 2:
                    findings.append({
                        'belief': belief.proposition,
                        'challenge': f'More failures ({len(belief.evidence_against)}) than successes',
                        'confidence': belief.confidence,
                        'strength': 'conflicting_evidence'
                    })
                
                # Check for old beliefs that may be stale
                if belief.last_validated:
                    from datetime import datetime
                    try:
                        last_val = datetime.fromisoformat(belief.last_validated)
                        age_days = (datetime.now() - last_val).days
                        if age_days > 30 and belief.confidence > 0.6:
                            findings.append({
                                'belief': belief.proposition,
                                'challenge': f'Old belief ({age_days} days) may be stale',
                                'confidence': belief.confidence,
                                'age_days': age_days,
                                'strength': 'stale'
                            })
                    except Exception as e:
                        logger.debug("Non-critical error: %s", e)
            # Check SelfModel for overconfident domains
            try:
                from src.agentic.self_model import get_self_model
                sm = get_self_model()
                overconfident = sm.get_overconfident_domains()
                for dom in overconfident:
                    findings.append({
                        'belief': f'High confidence in {dom}',
                        'challenge': 'SelfModel detects overconfidence - predictions exceed actual success',
                        'strength': 'calibration_error'
                    })
            except Exception as e:
                logger.debug("Non-critical error: %s", e)
        except Exception as e:
            logger.debug(f"Adversarial critique error: {e}")
        
        return findings
    
    async def _phase_periodic_reflection(self, agi_kernel):
        """THINK sub-phase — periodic reflection using real cognitive data.

        Uses BeliefEngine calibration and SelfModel capabilities instead of
        Duat/Synergy float arithmetic. Every 10 cycles: cognitive reflection.
        Every 50 cycles: performance optimization. Every 100 cycles: deep review.
        """
        cycle_count = self.stats.get('cycles_completed', 0)
        
        # Cognitive reflection (every 10 cycles — lightweight)
        if cycle_count > 0 and cycle_count % 10 == 0:
            try:
                reflection = self.cognitive.reflect()
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
                    
                self.learning_priorities = learn
                self.capability_strengths = strengths
                self.capability_weaknesses = weaknesses
                
            except Exception as e:
                logger.debug(f"Cognitive reflection error: {e}")
        
        # Deep meta-cognition review (every 100 cycles)
        if cycle_count > 0 and cycle_count % 100 == 0:
            try:
                logger.info("🧠 === DEEP COGNITIVE REVIEW ===")
                calibration = self.cognitive.get_belief_calibration()
                self_report = self.cognitive.get_self_awareness_report()
                domain_strengths = self.cognitive.get_domain_strengths()
                
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
                    curiosity_report = self.cognitive.get_curiosity_report()
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
                adversarial_findings = await self._adversarial_self_critique(agi_kernel)
                
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
                config_changes = self._propose_architecture_changes()
                if config_changes:
                    logger.info(f"🔧 Proposed {len(config_changes)} architecture changes")
                    for change in config_changes:
                        logger.info(f"   ⚙️ {change}")
            except Exception as e:
                logger.debug(f"Architecture modification error: {e}")

    def _propose_architecture_changes(self) -> List[str]:
        """Analyze recent performance and propose configuration adjustments.

        Self-directed architecture modification:
        - If calibration error is high → suggest lowering min_confidence
        - If too many actions blocked → suggest reducing max_actions_per_hour
        - If success rate is low → suggest increasing min_confidence
        - If curiosity gaps found → suggest enabling more observation sources
        Returns a list of human-readable change descriptions.
        """
        changes = []

        try:
            # Check calibration error
            if self.cognitive:
                calibration = self.cognitive.get_belief_calibration()
                mae = calibration.get('mean_absolute_error', 0)
                if mae > 0.25:
                    old = self.config.min_confidence
                    new = max(0.3, old * 0.9)
                    changes.append(f"Raise min_confidence from {old:.2f} to {new:.2f} (high calibration error {mae:.2f})")
                elif mae < 0.05 and self.config.min_confidence < 0.5:
                    old = self.config.min_confidence
                    new = min(0.5, old * 1.1)
                    changes.append(f"Lower min_confidence from {old:.2f} to {new:.2f} (low calibration error {mae:.2f})")

            # Check block rate
            blocked = self.stats.get('actions_blocked', 0)
            total = max(self.stats.get('proposals_generated', 1), 1)
            block_rate = blocked / total
            if block_rate > 0.5:
                changes.append(f"Reduce max_actions_per_hour from {self.config.max_actions_per_hour} "
                               f"to {self.config.max_actions_per_hour // 2} (block rate {block_rate:.0%})")

            # Check self-model weaknesses
            if hasattr(self, 'capability_weaknesses') and self.capability_weaknesses:
                weak_domains = set(w.get('domain', '') for w in self.capability_weaknesses[:3])
                if weak_domains:
                    changes.append(f"Prioritize practice in domains: {', '.join(weak_domains)}")

        except Exception as e:
            logger.debug(f"Architecture proposal error: {e}")

        return changes

    async def _phase_revenue_intelligence(self, agi_kernel=None) -> List:
        """Scan for revenue opportunities and generate high-priority proposals.

        Runs every 5 cycles. Identifies trading, content, and service opportunities,
        scores them by expected value, and generates proposals with elevated confidence.
        """
        revenue_proposals = []
        try:
            cycle_count = self.stats.get('cycles_completed', 0)
            if cycle_count < 1 or cycle_count % 5 != 0:
                return revenue_proposals

            from src.agentic.revenue_intelligence import get_revenue_intelligence
            ri = get_revenue_intelligence()

            # 1. Gather context from available data sources
            wallet_balances = None
            if hasattr(self, 'plugin_manager') and self.plugin_manager:
                onchain = self.plugin_manager.get_plugin('onchain')
                if onchain and hasattr(onchain, 'get_wallet_balances'):
                    try:
                        wallet_balances = onchain.get_wallet_balances()
                    except Exception:
                        pass

            # 2. Scan for opportunities
            opps = ri.scan_all_opportunities(wallet_balances=wallet_balances)
            top = ri.get_top_opportunities(limit=3)

            if not top:
                return revenue_proposals

            logger.info(f"💰 === REVENUE INTELLIGENCE === {len(opps)} opportunities scanned, "
                        f"top: {top[0].source}.{top[0].action} (${top[0].expected_value:.2f} est)")

            # 3. Generate proposals for top opportunities
            from src.agentic.symod_core import SyModActionProposal
            for opp in top:
                if opp.outcome == 'failed' and opp.last_attempted:
                    continue  # don't re-attempt failed experiments without new info

                confidence = min(opp.confidence * (1 + 0.1 * opp.seen_count), 0.9)
                proposal = SyModActionProposal(
                    action_type=opp.action,
                    target_id=opp.source,
                    target_name=opp.description[:60],
                    confidence=confidence,
                    justification=f"Revenue opportunity: {opp.description} "
                                  f"(est ${opp.expected_value:.2f}, risk={opp.risk_level})",
                    metadata={
                        'plugin': opp.source,
                        'revenue_opportunity': True,
                        'source': opp.source,
                        'action': opp.action,
                        'expected_value': opp.expected_value,
                        'effort': opp.effort_estimate,
                        'risk': opp.risk_level,
                    }
                )
                revenue_proposals.append(proposal)

            # 4. Log P&L summary
            pnl = ri.get_pnl_summary()
            if pnl['total_events'] > 0:
                logger.info(f"   📊 P&L: ${pnl['total_net']:.4f} across {pnl['total_events']} events")
                for source, data in pnl['by_source'].items():
                    logger.info(f"      {source}: ${data['net']:.4f} ({data['count']} events)")

        except Exception as e:
            logger.debug(f"Revenue intelligence error: {e}")

        if revenue_proposals:
            logger.info(f"💰 Generated {len(revenue_proposals)} revenue-driven proposals")
        return revenue_proposals

    async def _phase_curiosity_goals(self, agi_kernel) -> List:
        """THINK phase — generate curiosity-driven proposals before SyMod/LLM.

        Checks for knowledge gaps and generates self-directed exploration proposals.
        These run BEFORE the main proposal assembly so they can outrank work items.
        Returns a list of curiosity proposals to prepend.
        """
        curiosity_proposals = []
        try:
            cycle_count = self.stats.get('cycles_completed', 0)

            curiosity_goals = self.cognitive.get_curiosity_goals()

            if cycle_count > 0 and cycle_count % 10 == 0:
                reflection = self.cognitive.reflect()
                reflection_goals = self.cognitive.generate_reflection_curiosity_goals(reflection)
                curiosity_goals.extend(reflection_goals)

            if not curiosity_goals:
                return curiosity_proposals

            for cgoal in curiosity_goals:
                try:
                    plan = self.cognitive.goal_planner.decompose_goal(
                        goal=cgoal.title,
                        domain=cgoal.domain,
                        belief_engine=self.cognitive.belief_engine,
                        self_model=self.cognitive.self_model,
                        priority=cgoal.priority,
                    )
                    plan.source = cgoal.source

                    logger.info(
                        f"🧭 Curiosity goal: {cgoal.title[:50]} "
                        f"(domain={cgoal.domain}, priority={cgoal.priority:.2f}, "
                        f"info_gain={cgoal.information_gain_score:.2f})"
                    )

                    from src.agentic.symod_core import SyModActionProposal
                    next_step = self.cognitive.goal_planner.get_next_step(plan)
                    if next_step:
                        if not self._is_action_implemented(next_step.plugin, next_step.action):
                            logger.info(f"⏭️ Skipping curiosity proposal: {next_step.action} on {next_step.plugin} (not implemented)")
                            if hasattr(self.cognitive, 'curiosity') and hasattr(self.cognitive.curiosity, 'mark_target_blocked'):
                                self.cognitive.curiosity.mark_target_blocked(cgoal.domain, next_step.action, next_step.plugin)
                            continue
                        proposal = SyModActionProposal(
                            action_type=next_step.action,
                            target_id=cgoal.domain,
                            target_name=cgoal.title,
                            confidence=next_step.confidence * cgoal.priority,
                            justification=f"Curiosity-driven exploration (info_gain={cgoal.information_gain_score:.2f})",
                            metadata={
                                'plugin': next_step.plugin,
                                'curiosity_goal': True,
                                'goal_id': cgoal.goal_id,
                                'plan_id': plan.id,
                                'information_gain': cgoal.information_gain_score,
                                'novelty': cgoal.novelty_score,
                                'skill_gap': cgoal.skill_gap_score,
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

    def _is_action_implemented(self, plugin: str, action: str) -> bool:
        """Check if a plugin/action combo has a real implementation (not None)."""
        try:
            from src.agentic.action_router import ActionRouter
            return ActionRouter.is_action_valid(plugin, action)
        except Exception:
            return False  # fail closed — don't risk unknown actions
    
    def _phase_goal_management(self, agi_kernel, observations):
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
                        
                        if self.goal_manager_v2:
                            if self.goal_manager_v2.add_goal(goal):
                                logger.info(f"🎯 Proactive goal added: {goal.title[:50]}...")
            except Exception as e:
                logger.debug(f"Proactive goal generation error: {e}")
        
        # Hierarchical goals + planner
        if self.goal_hierarchy and self.planner:
            actionable_goals = self.goal_hierarchy.get_actionable_goals()
            logger.info(f"🎯 {len(actionable_goals)} actionable goals")
            next_action = self.planner.get_next_action()
            if next_action:
                logger.info(f"⚡ Next planned action: {next_action.description}")
        
        # Autonomous goal generation (legacy)
        if agi_kernel and hasattr(agi_kernel, 'goal_manager'):
            try:
                goal_manager = agi_kernel.goal_manager
                if goal_manager and hasattr(goal_manager, 'scan_and_generate'):
                    onchain_plugin = self.plugin_manager.get_plugin('onchain') if self.plugin_manager else None
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
        if hasattr(self, 'goal_stack') and self.goal_stack and self.cross_platform_intel:
            new_goals = self.goal_stack.auto_add_proposed_goals(
                observations, self.cross_platform_intel, max_new_goals=2
            )
            if new_goals > 0:
                logger.info(f"🎯 Self-proposed {new_goals} new goals")
        
        # GoalManager v2: auto-approve and activate safe goals
        if self.goal_manager_v2:
            try:
                from src.agentic.goal_manager import GoalStatus
                proposed_goals = self.goal_manager_v2.get_goals(status=GoalStatus.PROPOSED, limit=5)
                for goal in proposed_goals:
                    # Phase 1.3: Auto-approve safe goals (LOW/MEDIUM priority, low risk)
                    if self.goal_manager_v2.maybe_auto_approve_goal(goal.id):
                        logger.info(f"🤖 Auto-approved safe goal: {goal.title} ({goal.priority.name})")
                
                if hasattr(self.goal_manager_v2, 'start_next_safe_goal'):
                    started_goal = self.goal_manager_v2.start_next_safe_goal()
                    if started_goal:
                        logger.info(f"🚀 Runtime picked up safe goal: {started_goal.id} - {started_goal.title}")
                        telegram = self.plugin_manager.get_plugin('telegram') if self.plugin_manager else None
                        if telegram and hasattr(telegram, 'notify_autonomous_activity'):
                            telegram.notify_autonomous_activity(
                                'runtime_goal_pickup',
                                f"Picked up safe approved goal `{started_goal.id}`: {started_goal.title[:120]}"
                            )
            except Exception as e:
                logger.debug(f"Goal manager v2 activation error: {e}")

        # Goal hierarchy conflict detection and resolution
        if self.goal_hierarchy:
            try:
                conflicts = self.goal_hierarchy.detect_conflicts()
                if conflicts:
                    logger.info(f"⚠️ Detected {len(conflicts)} goal conflicts")
                    for conflict in conflicts:
                        logger.info(f"   ⚠️ {conflict['description']} (severity: {conflict['severity']})")
                    paused = self.goal_hierarchy.resolve_conflicts(conflicts)
                    if paused:
                        logger.info(f"⏸️ Auto-paused {len(paused)} conflicting goals")
            except Exception as e:
                logger.debug(f"Goal conflict resolution error: {e}")
        
        return next_action

    def _phase_theory_of_mind(self, observations: List) -> Optional['IntentInference']:
        """Feed observations to Theory of Mind, infer owner intent.

        Scans observations for owner-related interactions (mentions, replies,
        comments on own posts), records them as actions in ToM, and infers
        the owner's current intent. The inferred intent is attached to the
        brain's state for downstream phases to consume.
        """
        if not self.theory_of_mind:
            return None

        try:
            owner_id = 'owner'
            if self.core and hasattr(self.core, 'config') and isinstance(getattr(self.core, 'config', None), dict):
                owner_id = self.core.config.get('owner_id', 'owner')
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
                        self.theory_of_mind.observe_action(
                            agent_id=owner_id,
                            action_type=action_type,
                            target=target,
                            context={'observation_type': otype, 'content_preview': str(data.get('content', ''))[:120]},
                        )
                        owner_actions.append(action_type)

                elif otype in ('post', 'clawbr_post'):
                    content = str(data.get('content', ''))[:200]
                    if 'owner' in content.lower() or '@owner' in content.lower():
                        self.theory_of_mind.observe_action(
                            agent_id=owner_id,
                            action_type='mention_owner',
                            target=str(data.get('author_name', '')),
                            context={'content_preview': content},
                        )
                        owner_actions.append('mention_owner')

            if not owner_actions:
                return None

            inference = self.theory_of_mind.infer_intent(owner_id)
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
                self.owner_inferred_intent = inference

                predicted = self.theory_of_mind.predict_next_action(owner_id)
                if predicted:
                    self.owner_predicted_next_action = predicted

                return inference

        except Exception as e:
            logger.debug(f"ToM phase error: {e}")

        return None

    async def _phase_causal_reasoning(self, observations: List, agi_kernel=None) -> Dict:
        """Counterfactual simulation and root cause analysis.

        Uses CausalEngine to simulate "what if I had done X instead?"
        for failed actions, and feeds insights into subsequent planning.
        """
        insights = {"counterfactuals": [], "root_causes": [], "causal_links": 0}
        if not self.causal_engine:
            return insights

        try:
            recent_actions = self.action_logger.get_recent_actions(limit=10)
            failed_actions = [a for a in recent_actions if a.outcome == 'failure']
            for action in failed_actions[:3]:
                cf = self.causal_engine.simulate_counterfactual(
                    actual_action_id=str(action.id),
                    hypothetical_change={"time": "optimized"}
                )
                insights["counterfactuals"].append({
                    "action_id": str(action.id),
                    "predicted": cf.predicted_outcome,
                    "confidence": cf.confidence,
                })

            if observations:
                root = self.causal_engine.analyze_root_cause(
                    event_id="cycle_observation",
                    depth=2
                )
                if root and root.root_causes:
                    insights["root_causes"] = root.root_causes

            causal_links = self.causal_engine.find_correlations(
                outcome_type="success", min_strength=0.5
            )
            insights["causal_links"] = len(causal_links)
            if causal_links:
                logger.info(f"🔗 Causal engine: {len(causal_links)} correlations, {len(insights['counterfactuals'])} counterfactuals")

        except Exception as e:
            logger.debug(f"Causal reasoning error: {e}")

        return insights

    async def _phase_consolidate_learning(self, agi_kernel=None) -> None:
        """Sleep-cycle consolidation: replay high-value memories, update meta-params.

        Runs periodically (every 5 cycles) to:
        1. Replay recent successes into the knowledge graph
        2. Update meta-learning parameters per domain
        3. Prune low-confidence beliefs from the belief engine
        4. Record consolidated stats
        """
        if not hasattr(self, '_consolidation_counter'):
            self._consolidation_counter = 0
        self._consolidation_counter += 1

        # Only consolidate every 5 cycles
        if self._consolidation_counter % 5 != 0:
            return

        logger.info("💤 Starting learning consolidation cycle...")

        try:
            recent_actions = self.action_logger.get_recent_actions(limit=20)
            successes = [a for a in recent_actions if a.outcome == 'success']
            for action in successes[:5]:
                self.knowledge_graph.learn_from_outcome(
                    action=str(action.action_type),
                    domain=str(action.plugin or 'general'),
                    context=str(action.content or '')[:200],
                    outcome='success',
                    success=True,
                    confidence=action.confidence,
                )

            if self.cognitive and hasattr(self.cognitive, 'self_model'):
                learn_list = self.cognitive.self_model.what_should_i_learn()
                if learn_list:
                    logger.info(f"   📚 Learning priorities: {len(learn_list)} domains need practice")

            if self.meta_learning_engine:
                domains_seen = set()
                for a in recent_actions:
                    d = str(a.plugin or 'general')
                    if d not in domains_seen:
                        domains_seen.add(d)
                        approach = self.meta_learning_engine.adapt_learning_approach(
                            domain=d,
                            current_approach={"exploration_rate": 0.3, "memory_depth": 10}
                        )
                        logger.debug(f"   🔧 Adapted params for {d}: {approach.get('exploration_rate', '?')}")

            logger.info("💤 Consolidation complete")

        except Exception as e:
            logger.debug(f"Learning consolidation error: {e}")

    async def _phase_meta_adaptation(self, agi_kernel=None) -> None:
        """Adapt learning parameters per domain based on recent performance.

        Every cycle, query the meta-learning engine for optimal params
        and log any recommended adjustments for the reflection phase.
        """
        if not self.meta_learning_engine:
            return

        try:
            insights = self.meta_learning_engine.get_learning_insights()
            if insights:
                logger.info(f"🧠 Meta-learning: {len(insights)} insights")
                for insight in insights[:2]:
                    logger.info(f"   💡 {insight}")

            if self.cognitive and hasattr(self.cognitive, 'self_model'):
                calibration = self.cognitive.self_model.get_calibration_curve()
                mae = calibration.get('mean_absolute_error', 0)
                if mae > 0.2:
                    logger.info(f"   ⚠️ High calibration error ({mae:.2f}) — confidence calibration needs attention")

        except Exception as e:
            logger.debug(f"Meta adaptation error: {e}")

    async def _phase_plugin_discovery_and_creation(self, agi_kernel=None) -> None:
        """Detect capability gaps that could be filled by new plugins and auto-generate them.

        Runs every 50 cycles:
        1. Check knowledge graph for platform entities that lack a local plugin
        2. Check self-model for domains with zero capability data (unknown domains)
        3. Generate a PluginSpecification for each gap
        4. Call AutonomousCoder to generate the plugin
        5. Hot-load it via plugin_manager
        """
        if not self.plugin_manager:
            return

        cycle_count = self.stats.get('cycles_completed', 0)
        if cycle_count <= 0 or cycle_count % 50 != 0:
            return

        logger.info("🔌 === Plugin Discovery & Creation ===")

        try:
            from src.agentic.autonomous_coder import (
                PluginSpecification, get_autonomous_coder
            )
            coder = get_autonomous_coder()

            gaps = []

            # 1. Check knowledge graph for platform entities without plugins
            try:
                if self.knowledge_graph:
                    from src.agentic.knowledge_graph import EntityType
                    platform_entities = self.knowledge_graph.get_entities_by_type(EntityType.PLATFORM)
                    loaded_plugins = set()
                    if self.plugin_manager:
                        loaded_plugins = set(self.plugin_manager.plugins.keys())
                    for entity in platform_entities[:5]:
                        pname = entity.name.lower().replace(' ', '_')
                        if pname not in loaded_plugins:
                            gaps.append(PluginSpecification(
                                name=pname,
                                description=f"Auto-discovered platform: {entity.name}",
                                domain='social',
                                platform_url=getattr(entity, 'url', None),
                                evidence=[f"Discovered via knowledge graph entity: {entity.id}"]
                            ))
            except Exception as e:
                logger.debug(f"KG plugin discovery error: {e}")

            # 2. Check curiosity knowledge gaps for domain-level gaps
            try:
                if hasattr(self, 'capability_weaknesses') and self.capability_weaknesses:
                    unknown_domains = set()
                    for w in self.capability_weaknesses:
                        dom = w.get('domain', '')
                        if dom and dom not in ('general', 'unknown'):
                            unknown_domains.add(dom)
                    for domain in unknown_domains:
                        if not any(g.name == domain for g in gaps):
                            gaps.append(PluginSpecification(
                                name=f"{domain}_agent",
                                description=f"Agent for {domain} domain — generated from capability gap",
                                domain='data',
                                evidence=[f"Capability weakness in domain: {domain}"]
                            ))
            except Exception as e:
                logger.debug(f"Capability gap plugin discovery error: {e}")

            # 3. Generate plugins for each gap
            for gap in gaps[:2]:  # Max 2 per cycle
                result = coder.generate_plugin(gap)
                if result.status == 'generated':
                    logger.info(f"   ✅ Generated plugin: {gap.name}")
                    # Hot-load it
                    try:
                        pm = self.plugin_manager
                        if pm and hasattr(pm, 'load_plugin'):
                            import inspect
                            sig = inspect.signature(pm.load_plugin)
                            if len(sig.parameters) >= 4:
                                pm.load_plugin(gap.name, {'config': {}, 'enabled': True}, None, None)
                            else:
                                pm.load_plugin(gap.name, {'config': {}, 'enabled': True})
                            logger.info(f"   🔌 Hot-loaded plugin: {gap.name}")

                            # Register commands with intent classifier
                            try:
                                from plugins.telegram.intent_classifier import get_intent_classifier
                                classifier = get_intent_classifier()
                                plugin = pm.plugins.get(gap.name)
                                if plugin and classifier:
                                    for cmd_name, func in plugin.get_commands().items():
                                        doc = (func.__doc__ or f"Execute {cmd_name}").split('\\n')[0].strip()
                                        classifier.register_command(cmd_name, doc)
                            except Exception as e:
                                logger.debug("Non-critical error: %s", e)
                            # Tell the self-model a new capability was learned
                            if self.cognitive and hasattr(self.cognitive, 'self_model'):
                                self.cognitive.self_model.record_outcome(
                                    domain=gap.domain,
                                    action_type=f"plugin_{gap.name}",
                                    success=True,
                                    confidence=0.8,
                                )
                    except Exception as e:
                        logger.warning(f"   ⚠️ Hot-load failed for {gap.name}: {e}")
                else:
                    logger.warning(f"   ⚠️ Plugin generation failed for {gap.name}: {result.errors}")

            if not gaps:
                logger.info("   No plugin gaps found")

        except Exception as e:
            logger.debug(f"Plugin discovery error: {e}")

    async def _phase_learning_goal_acquisition(self, agi_kernel=None) -> None:
        """Turn curiosity gaps and self-model weaknesses into concrete skills.

        Runs every 20 cycles. Detects capability gaps, generates SkillSpecifications,
        delegates to AutonomousCoder, deploys the result, and updates self-model.
        """
        if not agi_kernel:
            return
        cycle_count = self.stats.get('cycles_completed', 0)
        if cycle_count < 1 or cycle_count % 20 != 0:
            return

        try:
            # 1. Gather signals: self-model learning priorities + curiosity goals
            learning_priorities = []
            if hasattr(self.cognitive, 'self_model') and self.cognitive.self_model:
                learning_priorities = self.cognitive.self_model.what_should_i_learn()

            curiosity_gaps = []
            if hasattr(self.cognitive, 'curiosity') and self.cognitive.curiosity:
                curiosity_gaps = self.cognitive.curiosity.detect_knowledge_gaps()

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
                        if hasattr(self.cognitive, 'self_model') and self.cognitive.self_model:
                            self.cognitive.self_model.record_outcome(
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

    async def _phase_execute_proposals(self, proposals, agi_kernel, next_action) -> int:
        """ACT phase — execute ranked proposals and record outcomes.
        
        Returns the number of successfully executed actions.
        """
        executed = 0
        for proposal in proposals:
            if proposal.confidence < self.config.min_confidence:
                logger.debug(f"⛔ Blocked: confidence {proposal.confidence:.2f} < {self.config.min_confidence}")
                self.stats['actions_blocked'] += 1
                continue
            
            if self._actions_this_hour >= self.config.max_actions_per_hour:
                logger.info("⏸️ Hourly budget exhausted")
                break
            
            result = await self._execute_proposal(proposal)
            
            # AGI Social: Follow after engagement if appropriate
            if result and proposal.target_name:
                await self._follow_after_engagement_action(
                    proposal.metadata.get('plugin', 'unknown'),
                    self.plugin_manager.get_plugin(proposal.metadata.get('plugin', 'unknown')),
                    proposal.target_name,
                    proposal.action_type
                )
            
            if result:
                executed += 1
                self._actions_this_hour += 1
                self.stats['actions_taken'] += 1
                self._record_proposal_success(proposal, result, agi_kernel, next_action)
            else:
                self._record_proposal_failure(proposal, agi_kernel)
            
            await asyncio.sleep(2)
        
        return executed
    
    def _record_proposal_success(self, proposal, result, agi_kernel, next_action):
        """Post-execution bookkeeping for a successful proposal."""
        goal_id = (proposal.metadata or {}).get('goal_id') if getattr(proposal, 'metadata', None) else None
        if goal_id:
            if self.goal_manager_v2 and hasattr(self.goal_manager_v2, 'record_goal_action_success'):
                self.goal_manager_v2.record_goal_action_success(
                    goal_id,
                    note=f"{proposal.action_type} via {(proposal.metadata or {}).get('plugin', 'unknown')} succeeded"
                )
            if agi_kernel and hasattr(agi_kernel, 'goal_manager'):
                gm = agi_kernel.goal_manager
                if gm and hasattr(gm, 'complete_action'):
                    gm.complete_action(goal_id, success=True, outcome=f"Successfully executed {proposal.action_type}")
        
        # Meta-learning with real metrics
        if self.meta_learner and proposal.action_type:
            from src.agentic.meta_learner import LearningOutcome
            from datetime import timedelta
            
            exec_time_ms = result.get('execution_time_ms', 5000) if isinstance(result, dict) else 5000
            pred_eval = result.get('prediction_evaluation', {}) if isinstance(result, dict) else {}
            mismatch = float(pred_eval.get('mismatch_score', 0.5))
            retention = max(0.0, 1.0 - mismatch)
            
            outcome = LearningOutcome(
                id=f"outcome_{datetime.now().timestamp()}",
                strategy_id="strategy_active_experimentation",
                domain=proposal.metadata.get('plugin', 'unknown'),
                task=proposal.action_type,
                success=True,
                learning_time=timedelta(milliseconds=exec_time_ms),
                quality_score=proposal.confidence,
                retention_score=retention,
                what_worked=[f"Action: {proposal.action_type}"],
                insights=[f"Confidence {proposal.confidence:.2f}, mismatch {mismatch:.2f}"]
            )
            self.meta_learner.record_outcome(outcome)
        
        # Transfer learning
        if self.transfer_learner and proposal.action_type:
            applicable_patterns = self.transfer_learner.find_applicable_patterns(
                domain=proposal.metadata.get('plugin', 'unknown'),
                problem=proposal.action_type
            )
            if applicable_patterns:
                logger.info(f"🔄 Found {len(applicable_patterns)} transferable patterns")
        
        # Knowledge graph
        if self.knowledge_graph:
            from src.agentic.knowledge_graph import Entity, EntityType
            entity = Entity(
                id=f"action_{datetime.now().timestamp()}",
                name=proposal.action_type,
                entity_type=EntityType.ACTION,
                domain=proposal.metadata.get('plugin', 'unknown'),
                attributes={
                    'success': True,
                    'confidence': proposal.confidence,
                    'timestamp': datetime.now().isoformat()
                }
            )
            self.knowledge_graph.add_entity(entity)
        
        # Goal hierarchy progress
        if self.goal_hierarchy and next_action and next_action.goal_id:
            goal = self.goal_hierarchy.get_goal(next_action.goal_id)
            if goal:
                new_progress = min(goal.progress + 0.05, 1.0)
                self.goal_hierarchy.update_progress(next_action.goal_id, new_progress)
                logger.info(f"📈 Goal progress: {goal.title} → {new_progress:.1%}")
        
        # Planner completion
        if self.planner and next_action:
            self.planner.complete_action(next_action.id)
    
    def _record_proposal_failure(self, proposal, agi_kernel):
        """Post-execution bookkeeping for a failed proposal."""
        goal_id = (proposal.metadata or {}).get('goal_id') if getattr(proposal, 'metadata', None) else None
        if goal_id:
            if self.goal_manager_v2 and hasattr(self.goal_manager_v2, 'record_goal_action_failure'):
                self.goal_manager_v2.record_goal_action_failure(
                    goal_id,
                    note=f"{proposal.action_type} via {(proposal.metadata or {}).get('plugin', 'unknown')} failed"
                )
            if agi_kernel and hasattr(agi_kernel, 'goal_manager'):
                gm = agi_kernel.goal_manager
                if gm and hasattr(gm, 'complete_action'):
                    gm.complete_action(goal_id, success=False, outcome="Action execution failed")
        
        if self.outcome_learner:
            self.outcome_learner.record_outcome(
                action_type=proposal.action_type,
                platform=proposal.metadata.get('plugin', 'unknown'),
                success=False,
                data={'reason': 'execution_failed'}
            )
    
    async def _execute_proposal(self, proposal) -> Optional[Dict]:
        """Execute a single action proposal.
        
        Route all autonomous proposals through AGIKernel.act()/ActionRouter
        so validation, execution, and learning use one unified pipeline.
        
        Also notifies owner of high-impact actions via notification service.
        """
        plugin_name = proposal.metadata.get('plugin')
        
        if not plugin_name or not self.plugin_manager:
            return None
        
        try:
            agi_kernel = getattr(self.core, 'agi_kernel', None) if self.core else None
            if not agi_kernel:
                logger.warning("⚠️ AGI Kernel unavailable, falling back to direct plugin execution")
                # Fallback: execute directly through plugin
                plugin = self.plugin_manager.get_plugin(plugin_name)
                if not plugin:
                    return None
                
                # Try to execute the action directly
                action_method = getattr(plugin, proposal.action_type, None)
                if action_method and callable(action_method):
                    try:
                        result = action_method(
                            target_id=proposal.target_id,
                            content=proposal.content,
                            **(proposal.metadata or {})
                        )
                        return {'success': True, 'data': result, 'fallback': True}
                    except Exception as e:
                        logger.error(f"❌ Direct execution error: {e}")
                        return {'success': False, 'error': str(e), 'fallback': True}
                return None
            # Original AGI Kernel route
            action_spec = {
                'plugin': plugin_name,
                'action_type': proposal.action_type,
                'params': {
                    'target_id': proposal.target_id,
                    'target_name': proposal.target_name,
                    'content': proposal.content,
                    'confidence': proposal.confidence,
                    'justification': proposal.justification,
                    'metadata': proposal.metadata or {},
                },
                'context': {
                    'source': 'autonomous_brain_proposal',
                    'trigger': proposal.metadata.get('trigger', 'autonomous_brain') if proposal.metadata else 'autonomous_brain',
                    'impact': 'high' if proposal.confidence >= 0.7 else 'medium',
                    'goal_id': proposal.metadata.get('goal_id') if proposal.metadata else None,
                    'proposal_confidence': proposal.confidence,
                    'spine_context': proposal.metadata.get('spine_context') if proposal.metadata else None,
                }
            }

            result = await agi_kernel.act(action_spec)
            
            # === NOTIFICATION: Alert owner of meaningful autonomous actions ===
            if result and self.notification_service and self._services_available:
                try:
                    success = result.get('success', False)
                    action_type = proposal.action_type
                    impact = action_spec['context'].get('impact', 'medium')
                    
                    # Determine if this is worth notifying about
                    should_notify = False
                    priority = NotificationPriority.LOW
                    
                    # High-impact successes
                    if success and impact == 'high':
                        should_notify = True
                        priority = NotificationPriority.NORMAL
                        
                    # Failures on high-confidence proposals
                    if not success and proposal.confidence >= 0.7:
                        should_notify = True
                        priority = NotificationPriority.HIGH
                    
                    # Certain action types are always notable
                    notable_actions = ['post', 'trade', 'debate', 'self_improve', 'auto_fix']
                    if any(a in action_type.lower() for a in notable_actions):
                        should_notify = True
                        if success:
                            priority = NotificationPriority.NORMAL
                        else:
                            priority = NotificationPriority.HIGH
                    
                    if should_notify:
                        await self.notification_service.notify(
                            title=f"🤖 Autonomous: {action_type}",
                            message=f"{'✅' if success else '❌'} {action_type} via {plugin_name} "
                                    f"(confidence: {proposal.confidence:.2f})",
                            priority=priority,
                            details={
                                'action_type': action_type,
                                'plugin': plugin_name,
                                'success': success,
                                'confidence': proposal.confidence,
                                'justification': proposal.justification[:100] if proposal.justification else '',
                            },
                            source_action=f"{plugin_name}:{action_type}",
                        )
                        logger.info(f"🔔 Notification sent: {action_type} {'succeeded' if success else 'failed'}")
                        
                except Exception as e:
                    logger.debug(f"Notification error (non-critical): {e}")

            # === USER FEEDBACK: Tell the owner what happened if they requested this goal ===
            if result and proposal.metadata.get('goal_driven'):
                await self._notify_user_of_goal_result(proposal, result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Execution error: {e}")
            return {'success': False, 'error': str(e)}

    async def _notify_user_of_goal_result(self, proposal: Any, result: Dict[str, Any]) -> None:
        """Send a specialized response back to a user if they originated the goal.
        
        This bridges the gap between 'On it' and the actual task completion.
        """
        try:
            metadata = proposal.metadata or {}
            origin = metadata.get('origin')
            evidence = metadata.get('evidence', {})
            
            # We only care about user-originated goals for this channel
            if origin != 'user':
                return
            
            chat_id = evidence.get('chat_id')
            if not chat_id:
                logger.debug("No chat_id in goal evidence, cannot notify user")
                return

            # Get telegram plugin
            telegram = self.plugin_manager.get_plugin('telegram') if self.plugin_manager else None
            if not telegram:
                return

            success = result.get('success', False)
            action_type = proposal.action_type
            
            # Extract actual data if possible
            # Result usually contains {'success': True, 'data': ...} or {'success': True, 'output': ...}
            data = result.get('data') or result.get('output') or result.get('details', {})
            
            # Formulate message
            if success:
                # Clean up data for display
                if isinstance(data, dict):
                    # Special handling for wallet balances
                    if action_type == 'check_wallet' or 'balance' in str(data).lower():
                        display_data = ""
                        for token, bal in data.items():
                            if isinstance(bal, (int, float)):
                                display_data += f"• {token}: {bal:.4f}\n"
                            else:
                                display_data += f"• {token}: {bal}\n"
                    else:
                        display_data = json.dumps(data, indent=2)
                else:
                    display_data = str(data)

                msg = f"🏁 **Task Complete: {proposal.target_name or action_type}**\n\n"
                msg += f"Result:\n{display_data if display_data else 'Success (no details returned)'}"
            else:
                error = result.get('error') or "Unknown error"
                msg = f"❌ **Task Failed: {proposal.target_name or action_type}**\n\n"
                msg += f"Reason: {error}"

            # Send via telegram
            # Use the loop to call the sync method to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, telegram.send_message_to_owner_sync, msg)
            logger.info(f"📤 Sent goal result feedback to user on Telegram (chat: {chat_id})")

        except Exception as e:
            logger.error(f"Error in _notify_user_of_goal_result: {e}")
            import traceback
            logger.debug(traceback.format_exc())

    def _build_runtime_spine_context(
        self,
        observations: List[Any],
        active_work_items: List[Dict[str, Any]],
        opportunities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build a compact runtime context around discovered reality, opportunity, and safe capability."""
        top_work_item = active_work_items[0] if active_work_items else {}
        top_judgment = top_work_item.get('capability_judgment') or (top_work_item.get('metadata') or {}).get('capability_judgment') or {}
        recent_interaction_count = len([
            obs for obs in observations
            if str(getattr(obs, 'observation_type', '') or '').lower() in {'mention', 'reply', 'comment'}
        ])
        opportunity_count = len(opportunities or [])
        opportunity_urgent = bool(opportunity_count)
        can_execute_now = bool(top_judgment.get('can_execute_now'))
        blocked_by_policy = bool(top_judgment.get('blocked_by_policy'))
        blocked_by_runtime = bool(top_judgment.get('blocked_by_runtime_readiness'))
        trust_bucket = str(top_judgment.get('trust_bucket', 'unknown') or 'unknown')

        opportunity_ripe = opportunity_urgent or recent_interaction_count > 0 or can_execute_now
        security_allows = not blocked_by_policy
        current_capability_ready = can_execute_now and not blocked_by_runtime

        # Theory of Mind state
        owner_intent = getattr(self, 'owner_inferred_intent', None)
        predicted_action = getattr(self, 'owner_predicted_next_action', None)

        return {
            'recent_findings_count': len(observations or []),
            'recent_interaction_count': recent_interaction_count,
            'opportunity_count': opportunity_count,
            'has_meaningful_work': bool(active_work_items),
            'top_work_item_id': top_work_item.get('id'),
            'top_work_item_type': top_work_item.get('type'),
            'top_work_item_summary': top_work_item.get('summary'),
            'opportunity_ripe': opportunity_ripe,
            'security_allows': security_allows,
            'current_capability_ready': current_capability_ready,
            'blocked_by_policy': blocked_by_policy,
            'blocked_by_runtime': blocked_by_runtime,
            'trust_bucket': trust_bucket,
            'owner_inferred_intent': owner_intent.inferred_intent if owner_intent else None,
            'owner_intent_confidence': owner_intent.confidence if owner_intent else None,
            'owner_predicted_next_action': predicted_action,
            'bounded_upgrade_candidates': [
                {
                    'id': item.get('id'),
                    'summary': item.get('summary'),
                    'objective': (item.get('metadata') or {}).get('bounded_upgrade_objective'),
                }
                for item in active_work_items
                if ((item.get('capability_judgment') or (item.get('metadata') or {}).get('capability_judgment') or {}).get('upgrade_allowed'))
            ],
        }

    def _log_runtime_spine_context(self, spine_context: Dict[str, Any]) -> None:
        """Log the compact runtime questions that should shape action choice."""
        if not spine_context:
            return
        logger.info(
            "🧭 Spine | found=%s meaningful=%s opportunity_ripe=%s security_allows=%s capability_ready=%s top_work=%s",
            spine_context.get('recent_findings_count', 0),
            spine_context.get('has_meaningful_work', False),
            spine_context.get('opportunity_ripe', False),
            spine_context.get('security_allows', False),
            spine_context.get('current_capability_ready', False),
            spine_context.get('top_work_item_summary', 'none'),
        )

    def _apply_runtime_spine_bias(self, proposals: List[Any], spine_context: Dict[str, Any]) -> None:
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

    def _apply_cognitive_bias(self, proposals: List[Any]) -> None:
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
                prediction = self.cognitive.predict_action_outcome(action_key, domain)
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

    def _prioritize_runtime_spine_proposals(self, proposals: List[Any], spine_context: Dict[str, Any]) -> List[Any]:
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

    async def _generate_default_goals(self) -> bool:
        """Auto-generate safe default goals when no active work items exist.
        
        Uses the new default_goals module for comprehensive goal seeding.
        Returns True if goals were created.
        """
        if not self.core or not hasattr(self.core, 'agi_kernel'):
            return False
        
        agi_kernel = self.core.agi_kernel
        if not agi_kernel:
            return False
        
        try:
            # Use new default goal seeder
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

    async def _detect_skill_gaps(self, agi_kernel) -> List[Dict]:
        """
        Detect capability gaps that require new skills.
        
        This is VERTICAL intelligence - identifying what we need to learn.
        
        Analyzes:
        1. Repeated failures (3+ failures = skill gap)
        2. Missing capabilities (referenced but not implemented)
        3. Performance bottlenecks (slow actions)
        
        Returns:
            List of skill gap dicts with priority scores
        """
        skill_gaps = []
        
        try:
            # 1. Analyze recent failures from episodic memory
            if hasattr(agi_kernel, 'episodic_memory'):
                recent_failures = []
                
                # Get recent failure episodes
                try:
                    recent_failures = agi_kernel.episodic_memory.get_recent_episodes(
                        filters={'outcome': 'failure'},
                        limit=50
                    )
                except Exception as e:
                    logger.warning(f"Episodic memory query failed: {e}")
                    recent_failures = []
                
                # Group failures by action type
                failure_patterns = {}
                for episode in recent_failures:
                    action_type = episode.action
                    if action_type not in failure_patterns:
                        failure_patterns[action_type] = []
                    failure_patterns[action_type].append(episode)
                
                # Identify repeated failures (skill gap indicator)
                for action_type, failures in failure_patterns.items():
                    if len(failures) >= 3:  # 3+ failures = skill gap
                        error_patterns = []
                        for f in failures:
                            error = f.outcome
                            if error not in error_patterns:
                                error_patterns.append(error)
                        
                        skill_gaps.append({
                            'type': 'repeated_failure',
                            'action_type': action_type,
                            'failure_count': len(failures),
                            'error_patterns': error_patterns[:5],  # Top 5 unique errors
                            'priority': min(10, len(failures) * 2),  # More failures = higher priority
                            'description': f"Repeated failures in {action_type} - need better implementation"
                        })
            
            # 2. Analyze missing capabilities from action logger
            if hasattr(agi_kernel, 'action_router'):
                try:
                    from src.agentic.action_logger import get_action_logger
                    action_logger = get_action_logger()
                    
                    # Get recent actions with "not found" errors
                    recent_actions = await action_logger.aget_recent_outcomes(limit=50)
                    
                    for action in recent_actions:
                        error = action.get('error', '')
                        if 'not found' in error.lower() or 'missing' in error.lower():
                            action_type = action.get('action_type', 'unknown')
                            plugin = action.get('plugin', 'unknown')
                            
                            skill_gaps.append({
                                'type': 'missing_capability',
                                'action_type': action_type,
                                'plugin': plugin,
                                'priority': 7,
                                'description': f"Missing capability: {action_type} in {plugin}",
                                'error_patterns': [error]
                            })
                except Exception as e:
                    logger.debug(f"Missing capability detection error: {e}")
            
            # 3. Analyze performance bottlenecks
            if hasattr(agi_kernel, 'action_router'):
                try:
                    from src.agentic.action_logger import get_action_logger
                    action_logger = get_action_logger()
                    
                    # Get actions with high duration
                    recent_actions = await action_logger.aget_recent_outcomes(limit=50)
                    
                    # Group by action type and calculate avg duration
                    action_durations = {}
                    for action in recent_actions:
                        action_type = action.get('action_type', 'unknown')
                        duration = action.get('duration_ms', 0)
                        
                        if action_type not in action_durations:
                            action_durations[action_type] = []
                        action_durations[action_type].append(duration)
                    
                    # Identify slow actions (avg > 5000ms)
                    for action_type, durations in action_durations.items():
                        if len(durations) >= 3:
                            avg_duration = sum(durations) / len(durations)
                            if avg_duration > 5000:
                                skill_gaps.append({
                                    'type': 'performance_bottleneck',
                                    'action_type': action_type,
                                    'avg_duration_ms': avg_duration,
                                    'priority': 6,
                                    'description': f"Slow action: {action_type} ({avg_duration:.0f}ms avg)",
                                    'error_patterns': []
                                })
                except Exception as e:
                    logger.debug(f"Performance bottleneck detection error: {e}")
            
            # 6.5: Wire skill gap detection to SelfModel belief data
            try:
                from src.agentic.self_model import get_self_model
                self_model = get_self_model()
                
                # Get learning priorities from SelfModel
                learning_priorities = self_model.what_should_i_learn()
                
                for item in learning_priorities:
                    skill_gaps.append({
                        'type': 'belief_driven_learning',
                        'domain': item.get('domain', 'unknown'),
                        'action_type': item.get('action_type', 'unknown'),
                        'reason': item.get('reason', 'unknown'),
                        'sample_size': item.get('sample_size', 0),
                        'success_rate': item.get('success_rate', 0),
                        'priority': 8 if item.get('priority') == 'high' else 5,
                        'description': f"Belief-driven: {item.get('reason')} - {item.get('action_type')}",
                        'error_patterns': [f"Low confidence due to {item.get('reason')}"]
                    })
                logger.debug(f"Added {len(learning_priorities)} belief-driven skill gaps")
            except Exception as e:
                logger.debug(f"SelfModel integration error: {e}")
        
        except Exception as e:
            logger.debug(f"Skill gap detection error: {e}")
        
        return skill_gaps
    
    def _handle_idle_state(self, active_work_items: List[Dict[str, Any]], proposals: List[Any], spine_context: Dict[str, Any]) -> List[Any]:
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
        elif proposals and all(float(getattr(p, 'confidence', 0.0) or 0.0) < self.config.min_confidence for p in proposals):
            logger.info("🛌 Idle: proposals below confidence threshold - will attempt diverse exploration")
        else:
            logger.info("🛌 Idle: no actions executed - attempting diverse exploration")

        # Generate diverse exploratory proposals
        exploratory_proposals = []
        
        # Only add exploratory actions if we haven't hit hourly limits
        if self._actions_this_hour >= self.config.max_actions_per_hour:
            return exploratory_proposals
            
        from src.agentic.symod_core import SyModActionProposal
        
        # Get cycle counter for rotating through categories
        cycle_count = self.stats.get('cycles_completed', 0)
        
        # === CATEGORY 1: ANALYSIS & RESEARCH (Every 2nd cycle) ===
        if cycle_count % 2 == 0:
            # Market/Trending analysis
            moltx = self.plugin_manager.get_plugin('moltx') if self.plugin_manager else None
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
            clawbr = self.plugin_manager.get_plugin('clawbr') if self.plugin_manager else None
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
            moltx = self.plugin_manager.get_plugin('moltx') if self.plugin_manager else None
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
        moltx = self.plugin_manager.get_plugin('moltx') if self.plugin_manager else None
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
        
        clawbr = self.plugin_manager.get_plugin('clawbr') if self.plugin_manager else None
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
            onchain = self.plugin_manager.get_plugin('onchain') if self.plugin_manager else None
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
                if hasattr(self, 'cognitive') and self.cognitive:
                    self_model = getattr(self.cognitive, 'self_model', None)
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

    def _log_idle_reason(self, active_work_items: List[Dict[str, Any]], proposals: List[Any], spine_context: Dict[str, Any]) -> None:
        """[DEPRECATED] Use _handle_idle_state instead. Kept for compatibility."""
        # This method is now replaced by _handle_idle_state which takes action
        # instead of just logging. The logic has been moved there.
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current brain status"""
        uptime = timedelta(0)
        if self.stats['start_time']:
            uptime = datetime.now() - self.stats['start_time']
        
        # Get recent action stats
        action_stats = self.action_logger.get_statistics(hours=1)
        
        return {
            'running': self._running,
            'mode': self.config.mode,
            'uptime': str(uptime),
            'last_cycle': self._last_cycle.isoformat() if self._last_cycle else None,
            'cycles_completed': self.stats['cycles_completed'],
            'actions_taken': self.stats['actions_taken'],
            'actions_blocked': self.stats['actions_blocked'],
            'actions_this_hour': self._actions_this_hour,
            'max_actions_per_hour': self.config.max_actions_per_hour,
            'success_rate': self._get_success_rate(),
            'recent_stats': action_stats,
            'agi_social': self.get_social_stats()
        }
    
    def _get_success_rate(self) -> float:
        """Calculate success rate from action log"""
        try:
            return self.action_logger.get_success_rate(hours=24)
        except (AttributeError, TypeError, ZeroDivisionError) as e:
            logger.debug(f"Failed to get success rate: {e}")
            return 0.0
    
    def set_mode(self, mode: str) -> str:
        """Change autonomy mode"""
        if mode not in ['conservative', 'normal', 'aggressive']:
            return f"❌ Unknown mode: {mode}"
        
        was_running = self._running
        
        if was_running:
            asyncio.create_task(self.stop())
        
        self.config = BrainConfig.from_mode(mode)
        
        if was_running:
            asyncio.create_task(self.start(mode))
        
        return f"✅ Mode set to {mode.upper()}"
    
    async def _enforce_goal_quota(self) -> None:
        """
        Goal Quota Enforcement: Ensure minimum goals per hour.
        
        If goals completed < min_goals_per_hour, generates emergency goals
        to meet the quota. This gives AlleyBot a sense of purpose and drive.
        """
        if not self.config.goal_quota_strict:
            return
        
        # Check if hour has rolled over
        now = datetime.now()
        hour_elapsed = (now - self._goal_quota_hour_start).total_seconds() / 3600
        
        if hour_elapsed >= 1.0:
            # Reset for new hour
            self._goal_quota_hour_start = now
            self._goals_completed_this_hour = 0
            self._emergency_goals_generated = 0
            logger.info(f"🕐 New hour started - Goal quota reset (target: {self.config.min_goals_per_hour}/hour)")
            return
        
        # Calculate progress
        progress = self._goals_completed_this_hour / self.config.min_goals_per_hour
        
        # If we're behind on quota, generate emergency goals
        if progress < 0.5 and self._emergency_goals_generated < 3:
            logger.warning(f"⚠️ Goal quota behind: {self._goals_completed_this_hour}/{self.config.min_goals_per_hour} "
                          f"({progress*100:.0f}%) - Generating emergency goals...")
            
            emergency_goals = await self._generate_emergency_goals()
            
            if emergency_goals:
                self._emergency_goals_generated += len(emergency_goals)
                self.stats['quota_warnings'] += 1
                logger.info(f"🚨 Generated {len(emergency_goals)} emergency goals to meet quota")
    
    async def _generate_emergency_goals(self) -> List[Dict[str, Any]]:
        """
        Generate emergency goals when quota is behind.
        Creates high-value, achievable goals from current observations.
        """
        emergency_goals = []
        
        try:
            # Get current world state for goal generation
            agi_kernel = getattr(self.core, 'agi_kernel', None) if self.core else None
            
            # Emergency Goal 1: Quick platform health check
            if self.plugin_manager:
                moltx = self.plugin_manager.get_plugin('moltx')
                if moltx and hasattr(moltx, 'get_feed'):
                    emergency_goals.append({
                        'title': 'Emergency: Quick Moltx Feed Check',
                        'description': 'Verify Moltx connectivity and gather trending topics',
                        'action_type': 'get_feed',
                        'plugin': 'moltx',
                        'priority': 8,
                        'estimated_duration': '2 min',
                        'confidence': 0.9
                    })
            
            # Emergency Goal 2: Quick feed check
            emergency_goals.append({
                'title': 'Emergency: Quick Moltx Feed Check',
                'description': 'Quickly check Moltx feed for trending topics',
                'action_type': 'feed',
                'plugin': 'moltx',
                'priority': 7,
                'estimated_duration': '2 min',
                'confidence': 0.95
            })
            
            # Emergency Goal 3: Content engagement (if platforms available)
            if self.plugin_manager:
                moltx = self.plugin_manager.get_plugin('moltx')
                if moltx:
                    emergency_goals.append({
                        'title': 'Emergency: Engage with Trending Content',
                        'description': 'Find and engage with high-value posts on Moltx',
                        'action_type': 'engage',
                        'plugin': 'moltx',
                        'priority': 6,
                        'estimated_duration': '5 min',
                        'confidence': 0.7
                    })
            
            # Create work items from emergency goals
            if self.work_item_service and emergency_goals:
                for goal in emergency_goals:
                    try:
                        work_item = self.work_item_service.create_work_item(
                            title=goal['title'],
                            description=goal['description'],
                            work_type='emergency_quota',
                            priority=goal['priority'],
                            source_signal={
                                'source': 'quota_enforcement',
                                'goal_data': goal,
                                'created_at': datetime.now().isoformat()
                            }
                        )
                        logger.info(f"🚨 Created emergency work item: {work_item.id}")
                    except Exception as e:
                        logger.debug(f"Could not create emergency work item: {e}")
            
        except Exception as e:
            logger.warning(f"⚠️ Emergency goal generation failed: {e}")
        
        return emergency_goals
    
    def _record_goal_completion(self, success: bool, goal_quality: float = 0.5) -> None:
        """
        Record goal completion for quota tracking.
        Only counts high-quality goals toward the quota.
        """
        if success and goal_quality >= self.config.goal_quality_threshold:
            self._goals_completed_this_hour += 1
            self.stats['goals_completed_total'] += 1
            logger.info(f"✅ Goal completed! ({self._goals_completed_this_hour}/{self.config.min_goals_per_hour} this hour)")
        elif not success:
            self.stats['goals_failed_total'] += 1
    
    async def _generate_proactive_goals(self, observations: List[Any]) -> List[Dict[str, Any]]:
        """
        Proactive Goal Generation: Create goals from observations.
        
        AlleyBot spots opportunities and creates goals automatically,
        giving him a sense of agency and purpose.
        """
        if not self.config.proactive_goal_generation:
            return []
        
        proactive_goals = []
        
        try:
            # Pattern 1: Trending Topics → Content Creation Goal
            for obs in observations:
                if hasattr(obs, 'data') and isinstance(obs.data, dict):
                    content = obs.data.get('content', '')
                    
                    # Detect trending crypto/AI topics
                    trending_keywords = ['bitcoin', 'ethereum', 'solana', 'ai agent', 'defi', 'nft']
                    for keyword in trending_keywords:
                        if keyword in content.lower() and len(content) > 50:
                            proactive_goals.append({
                                'title': f'Proactive: Create content about {keyword} trend',
                                'description': f'Trending topic detected: create analysis post about {keyword}',
                                'source': 'opportunity_detection',
                                'confidence': 0.6,
                                'estimated_impact': 7.5
                            })
                            break
            
            # Pattern 2: Low Engagement → Engagement Goal
            if len(observations) > 10:
                proactive_goals.append({
                    'title': 'Proactive: Boost Platform Engagement',
                    'description': 'Low activity detected - initiate engagement cycle',
                    'source': 'engagement_opportunity',
                    'confidence': 0.55,
                    'estimated_impact': 6.0
                })
            
            # Pattern 3: Knowledge Gap → Research Goal
            if self.knowledge_graph:
                knowledge_gaps = self.knowledge_graph.identify_gaps()
                if knowledge_gaps:
                    gap = knowledge_gaps[0]
                    proactive_goals.append({
                        'title': f'Proactive: Research {gap.topic}',
                        'description': f'Knowledge gap detected in {gap.domain}',
                        'source': 'knowledge_gap',
                        'confidence': 0.65,
                        'estimated_impact': 8.0
                    })
            
            # Create work items for high-confidence proactive goals
            for goal in proactive_goals:
                if goal['confidence'] >= self.config.min_confidence:
                    try:
                        if self.work_item_service:
                            work_item = self.work_item_service.create_work_item(
                                title=goal['title'],
                                description=goal['description'],
                                work_type='proactive',
                                priority=int(goal['estimated_impact']),
                                source_signal={
                                    'source': goal['source'],
                                    'confidence': goal['confidence'],
                                    'estimated_impact': goal['estimated_impact']
                                }
                            )
                            logger.info(f"💡 Proactive goal created: {work_item.title[:50]}...")
                    except Exception as e:
                        logger.debug(f"Could not create proactive work item: {e}")
        
        except Exception as e:
            logger.debug(f"Proactive goal generation error: {e}")
        
        return proactive_goals
    
    async def _generate_curiosity_goals(self) -> List[Dict[str, Any]]:
        """
        Curiosity Drive: Self-directed exploration using BeliefEngine and SelfModel.

        Replaces random topic selection with information-gain-driven exploration.
        Generates goals for domains where the agent has knowledge gaps.
        """
        if not self.config.curiosity_drive_enabled:
            return []

        curiosity_goals = []
        try:
            cognitive_goals = self.cognitive.get_curiosity_goals()
            for goal in cognitive_goals:
                curiosity_goals.append({
                    'title': goal.title,
                    'description': goal.description,
                    'source': goal.source,
                    'confidence': min(goal.priority, 0.9),
                    'estimated_impact': goal.priority * 10.0,
                    'domain': goal.domain,
                    'goal_type': goal.goal_type,
                    'information_gain': goal.information_gain_score,
                    'novelty': goal.novelty_score,
                    'skill_gap': goal.skill_gap_score,
                })
        except Exception as e:
            logger.debug(f"Curiosity drive error: {e}")

        if curiosity_goals:
            logger.info(f"Curiosity drive: {len(curiosity_goals)} goals ({', '.join(g['domain'] for g in curiosity_goals)})")

        return curiosity_goals

    async def _advance_active_plans(self, agi_kernel=None) -> bool:
        """Advance active plans by executing multiple ready steps per cycle (2.8).

        Finds active plans, picks the highest-priority ready steps from each,
        executes them via the action router, and records outcomes.
        Executes up to 3 steps per cycle to accelerate multi-step plans.
        """
        goal_planner = getattr(self.cognitive, 'goal_planner', None)
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

            prediction = self.cognitive.predict_action_outcome(
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
                elif self.plugin_manager:
                    plugin = self.plugin_manager.plugins.get(next_step.plugin)
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
                            belief_engine=self.cognitive.belief_engine,
                            self_model=self.cognitive.self_model,
                        )
                        executed += 1
                else:
                    reason = result.get('error', result.get('reason', 'Unknown failure'))
                    goal_planner.mark_step_failed(plan.id, next_step.id, reason, result)
                    goal_planner.rollback_completed_steps(plan.id, next_step.id)
                    goal_planner.record_plan_outcome(
                        plan.id, success=False,
                        belief_engine=self.cognitive.belief_engine,
                        self_model=self.cognitive.self_model,
                    )

                self.cognitive.record_action_outcome(
                    action=f"{next_step.plugin}:{next_step.action}",
                    domain=plan.domain,
                    predicted_confidence=prediction.get('predicted_success', 0.5),
                    actual_success=success,
                    context=f"plan:{plan.id}",
                    outcome_description=result.get('output', result.get('error', ''))[:200],
                )

                try:
                    intrinsic = self.cognitive.calculate_intrinsic_reward(
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

        return False


# Singleton instance
_brain_instance: Optional[AutonomousBrain] = None


def get_autonomous_brain(core=None, plugin_manager=None, symod=None) -> AutonomousBrain:
    """Get or create brain singleton"""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = AutonomousBrain(core, plugin_manager, symod)
    return _brain_instance
    if _brain_instance is None:
        _brain_instance = AutonomousBrain(core, plugin_manager, symod)
    return _brain_instance
