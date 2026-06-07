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
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
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

# Narrative self: persistent identity, goals, and narrative memory
from src.agentic.narrative_self import get_narrative_engine

# Sub-agent swarm: parallel specialized agents
from src.agentic.sub_agent_swarm import get_sub_agent_swarm, SubAgentSwarm

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
    # AGI mode: confidence gates removed — action is guided by consequence,
    # not by pre-judgment. The causal engine and failure budget provide safety.
    min_confidence: float = 0.0
    require_owner_approval: bool = False
    
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
                min_confidence=0.0,
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
                min_confidence=0.0,
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
                min_confidence=0.0,
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

        # Narrative self: persistent identity, goals, and narrative memory
        self.narrative_self = get_narrative_engine()

        # Sub-agent swarm: parallel specialized agents
        self.sub_agent_swarm = get_sub_agent_swarm(brain_ref=self)

        # Event-driven trigger queue (Phase 4: real-time response)
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
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

    def _init_sub_agent_swarm(self) -> None:
        """Initialize the sub-agent swarm with built-in agents."""
        brain = self

        async def _scan(agent) -> Optional[Any]:
            if not brain or not hasattr(brain, 'opportunity_monitor'):
                return None
            try:
                obs = await brain._gather_observations()
                return {
                    'agent_name': 'scanner',
                    'action': f"Scanned {len(obs)} observations",
                    'result': 'success' if obs else 'skipped',
                    'details': {'count': len(obs)},
                }
            except Exception as e:
                return {'agent_name': 'scanner', 'action': f"Error: {e}", 'result': 'failure'}

        async def _social(agent) -> Optional[Any]:
            pm = brain.plugin_manager if brain else None
            if not pm:
                return None
            try:
                moltx = pm.get_plugin('moltx')
                if moltx and hasattr(moltx, 'get_feed'):
                    feed = moltx.get_feed('global', limit=5)
                    posts = feed.get('posts', []) if isinstance(feed, dict) else []
                    return {'agent_name': 'social', 'action': f"Feed: {len(posts)} posts", 'result': 'success', 'details': {'count': len(posts)}}
            except Exception as e:
                return {'agent_name': 'social', 'action': f"Error: {e}", 'result': 'failure'}
            return None

        async def _improve(agent) -> Optional[Any]:
            if not brain or not hasattr(brain, 'action_logger'):
                return None
            try:
                recent = brain.action_logger.get_recent_actions(limit=20)
                if not recent or len(recent) < 5:
                    return None
                successes = [a for a in recent if hasattr(a, 'outcome') and a.outcome == 'success']
                rate = len(successes) / len(recent)
                return {'agent_name': 'self_improve', 'action': f"{rate:.0%} success rate", 'result': 'success' if rate > 0.5 else 'failure', 'details': {'total': len(recent), 'successes': len(successes), 'rate': rate}}
            except Exception as e:
                return {'agent_name': 'self_improve', 'action': f"Error: {e}", 'result': 'failure'}

        async def _trade(agent) -> Optional[Any]:
            if not brain or not hasattr(brain, 'autonomous_trading') or not brain.autonomous_trading:
                return None
            try:
                if brain.autonomous_trading.config.get('enabled'):
                    proposals = await brain.autonomous_trading.generate_proposals()
                    return {'agent_name': 'trader', 'action': f"{len(proposals)} proposals", 'result': 'success', 'details': {'count': len(proposals)}}
            except Exception as e:
                return {'agent_name': 'trader', 'action': f"Error: {e}", 'result': 'failure'}
            return None

        self.sub_agent_swarm.add_agent('scanner', 'Scan for opportunities across platforms', 120, _scan)
        self.sub_agent_swarm.add_agent('social', 'Monitor and engage social platforms', 180, _social)
        self.sub_agent_swarm.add_agent('self_improve', 'Review actions and propose improvements', 600, _improve)
        self.sub_agent_swarm.add_agent('trader', 'Scan and execute trades', 300, _trade)
        logger.info(f"🤖 Initialized {len(self.sub_agent_swarm._agents)} sub-agents")

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

        # Start sub-agent swarm (parallel specialized agents)
        try:
            self._init_sub_agent_swarm()
            self.sub_agent_swarm.start_all(loop)
        except Exception as e:
            logger.warning(f"⚠️ Sub-agent swarm start error: {e}")

        msg = (
            f"🧠 Autonomous Brain Started\n"
            f"Mode: {mode.upper()}\n"
            f"Cycle: {self.config.cycle_interval_minutes} min\n"
            f"Max actions/hour: {self.config.max_actions_per_hour}\n"
            f"Confidence: AGI mode (no gate, learned from outcomes)\n"
            f"Owner approval: AGI mode (self-directed)\n"
            f"Sub-agents: {len(self.sub_agent_swarm._agents) if hasattr(self.sub_agent_swarm, '_agents') else 0}"
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

        # Stop sub-agent swarm
        if hasattr(self, 'sub_agent_swarm') and self.sub_agent_swarm:
            try:
                self.sub_agent_swarm.stop_all()
            except Exception as e:
                logger.warning(f"⚠️ Sub-agent swarm stop error: {e}")

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
        """Main autonomous loop with event-driven triggers + periodic cycles."""
        logger.info("🔄 Brain loop started (event-driven + periodic)")
        
        from src.agentic.error_recovery import get_error_recovery
        error_recovery = get_error_recovery(self.plugin_manager)
        
        while self._running:
            try:
                cycle_start = datetime.now()
                
                if (cycle_start - self._hour_start).total_seconds() > 3600:
                    self._actions_this_hour = 0
                    self._hour_start = cycle_start
                
                if self._actions_this_hour < self.config.max_actions_per_hour:
                    await self._execute_cycle()
                    self.stats['cycles_completed'] += 1
                else:
                    logger.info("⏸️ Hourly action limit reached, skipping cycle")
                
                self._last_cycle = datetime.now()
                
                # Wait for next cycle OR an external event, whichever comes first
                sleep_seconds = self.config.cycle_interval_minutes * 60
                while sleep_seconds > 0 and self._running:
                    try:
                        # Wait up to 5s for an event, then check remaining sleep
                        event = await asyncio.wait_for(
                            self._event_queue.get(), timeout=min(5.0, sleep_seconds)
                        )
                        logger.info(f"⚡ Event triggered cycle: {event.get('type', 'unknown')}")
                        self._event_queue.task_done()
                        break  # Wake up, run cycle now
                    except asyncio.TimeoutError:
                        sleep_seconds -= 5
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Brain loop error: {e}")
                self.stats['errors'] += 1
                
                if error_recovery:
                    error_recovery.record_error('brain', e, severity='high')
                    recovery_success = await error_recovery.attempt_recovery('brain', e)
                    if not recovery_success:
                        logger.warning("⚠️ Recovery failed, continuing with backoff...")
                
                await asyncio.sleep(60)

    def trigger_event(self, event_type: str, data: Optional[Dict] = None) -> None:
        """Trigger an immediate brain cycle from an external event.
        
        Call this from Telegram handlers, webhooks, or on-chain listeners.
        Safe to call from any thread — uses asyncio.run_coroutine_threadsafe internally.
        """
        event = {'type': event_type, 'data': data or {}, 'timestamp': datetime.now().isoformat()}
        try:
            self._event_queue.put_nowait(event)
            logger.info(f"📡 Event queued: {event_type}")
        except Exception as e:
            logger.debug(f"Event queue error: {e}")
        
        # Dispatch to registered handlers
        for handler in self._event_handlers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(handler(event))
                    else:
                        loop.run_until_complete(handler(event))
                else:
                    handler(event)
            except Exception as e:
                logger.debug(f"Event handler error: {e}")

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register a handler for a specific event type."""
        self._event_handlers[event_type].append(handler)
        logger.info(f"📡 Registered handler for event: {event_type}")
        
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

        active_work_items: List[Dict[str, Any]] = []
        spine_context: Dict[str, Any] = {}
        opportunities = []

        # === OPPORTUNITY DETECTION + SENSE: via coordinator ===
        opportunities = await self.coordinator.detect_opportunities()
        observations = await self.coordinator.gather_observations()
        logger.info(f"👁️ Gathered {len(observations)} observations")

        # ⚡ QUICK ACTION CHECKPOINT 1: Fresh data, check for quick plays
        quick_actions = await self.coordinator.quick_profit_actions("after-SENSE")

        # Get AGI Kernel reference early for all AGI features
        agi_kernel = getattr(self.core, 'agi_kernel', None) if self.core else None

        # === CROSS-PLATFORM SYNTHESIS: Connect dots across platforms ===
        if self.cross_platform_intel:
            synthesis = self.cross_platform_intel.synthesize_observations(observations)
            cross_platform_topics = synthesis.get('cross_platform_topics', [])
            xp_opportunities = synthesis.get('opportunities', [])
            if xp_opportunities:
                opportunities = xp_opportunities
            if cross_platform_topics:
                logger.info(f"🔗 Found {len(cross_platform_topics)} cross-platform topics")
            if opportunities:
                logger.info(f"💡 Identified {len(opportunities)} cross-platform opportunities")

        # === CROSS-DOMAIN PATTERN DETECTION: Horizontal Intelligence ===
        if agi_kernel and hasattr(agi_kernel, 'pattern_detector'):
            try:
                patterns = agi_kernel.pattern_detector.detect_patterns(observations)
                if patterns:
                    logger.info(f"🔍 Detected {len(patterns)} cross-domain patterns")
                    for pattern in patterns[:3]:
                        logger.info(f"   📊 {pattern.pattern_type}: {pattern.description} (confidence: {pattern.confidence:.2f})")
                    strategy = agi_kernel.pattern_detector.generate_strategy_from_patterns(patterns)
                    if strategy:
                        logger.info(f"🎯 Generated multi-domain strategy from {strategy['based_on_pattern']} pattern")
                        logger.info(f"   Actions: {len(strategy['actions'])} cross-domain actions")
                        if not hasattr(self, '_cross_domain_strategies'):
                            self._cross_domain_strategies = []
                        self._cross_domain_strategies.append(strategy)
            except Exception as e:
                logger.debug(f"Cross-domain pattern detection error: {e}")

        # Submit to SyMod
        for obs in observations:
            self.symod.observe(obs)

        # === THEORY OF MIND: via coordinator ===
        owner_intent = self.coordinator.theory_of_mind(observations)
        if owner_intent:
            logger.info(f"🎯 ToM inferred owner intent: {owner_intent.inferred_intent} (conf: {owner_intent.confidence:.2f})")

        # === CAUSAL REASONING: via coordinator ===
        await self.coordinator.causal_reasoning(observations, agi_kernel)

        # === FEED WORLD STATE DB: via coordinator ===
        await self.coordinator.feed_observations_to_world_state(observations)

        # === WORK-FIRST CONTINUITY: Pull active meaningful work ===
        if agi_kernel and hasattr(agi_kernel, 'get_active_work_items'):
            try:
                active_work_items = agi_kernel.get_active_work_items(limit=5) or []
                active_work_items = [item for item in active_work_items if item and isinstance(item, dict)]
                if active_work_items:
                    top_work_item = active_work_items[0]
                    logger.info(
                        f"🧵 Active work items: {len(active_work_items)} | Top: {top_work_item.get('summary', 'unknown work')}"
                    )
                else:
                    logger.info("🎯 No active work items - auto-generating safe default goals")
                    default_goals_created = await self.coordinator.generate_default_goals()
                    if default_goals_created:
                        active_work_items = agi_kernel.get_active_work_items(limit=5) or []
                        active_work_items = [item for item in active_work_items if item and isinstance(item, dict)]
            except Exception as e:
                logger.debug(f"Could not load active work items for cycle: {e}")

        spine_context = self.coordinator.build_spine_context(
            observations=observations,
            active_work_items=active_work_items,
            opportunities=opportunities,
        )
        self._log_runtime_spine_context(spine_context)

        # === SKILL GAP ANALYSIS: via coordinator ===
        await self.coordinator.skill_gap_analysis(observations, agi_kernel)

        # === AUTONOMOUS TRADING ===
        if self.autonomous_trading:
            try:
                trade_proposals = await self.autonomous_trading.analyze_markets()
                if trade_proposals:
                    logger.info(f"💰 Found {len(trade_proposals)} SyMod-validated trade opportunities")
                    best_trade = max(trade_proposals, key=lambda t: t.confidence)
                    trade_outcome = await self.autonomous_trading.execute_trade(best_trade)
                    if trade_outcome:
                        logger.info(f"✅ Executed autonomous trade: {trade_outcome.trade_id}")
                        telegram = self.plugin_manager.get_plugin('telegram') if self.plugin_manager else None
                        if telegram and hasattr(telegram, 'notify_autonomous_activity'):
                            telegram.notify_autonomous_activity(
                                'autonomous_trade',
                                f"Executed trade: {trade_outcome.trade_id}"
                            )
            except Exception as e:
                logger.warning(f"⚠️ Autonomous trading error: {e}")

        # ⚡ QUICK ACTION CHECKPOINT 2: via coordinator
        quick_actions = await self.coordinator.quick_profit_actions("after-trading")

        # === GOAL MANAGEMENT: via coordinator ===
        next_action = await self.coordinator.goal_management(agi_kernel, observations)

        # === MEMORY-FIRST THINKING: via coordinator ===
        memory_proposals = await self.coordinator.memory_driven_thinking(observations, agi_kernel)
        if memory_proposals:
            logger.info(f"🧠 Memory-driven proposals: {len(memory_proposals)} (from semantic recall)")

        # === AGI ORCHESTRATION: via coordinator ===
        agi_actions = await self.coordinator.run_agi_orchestration()
        logger.info(f"🎭 AGI Orchestrator: {len(agi_actions)} actions generated")

        # === UNIFIED REASONING ===
        if self.unified_reasoner and observations:
            from src.agentic.unified_reasoner import ReasoningContext, ReasoningType
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

        # === PERIODIC REFLECTION: via coordinator ===
        await self.coordinator.periodic_reflection(agi_kernel)

        # === CONSOLIDATE LEARNING: via coordinator ===
        await self.coordinator.consolidate_learning(agi_kernel)

        # === PLUGIN DISCOVERY: via coordinator ===
        await self.coordinator.plugin_discovery(agi_kernel)

        # === LEARNING ACQUISITION: via coordinator ===
        await self.coordinator.learning_acquisition(agi_kernel)

        # === CHESS WIN ANNOUNCEMENTS: via coordinator ===
        await self.coordinator.post_chess_wins()

        # === REVENUE INTELLIGENCE: via coordinator ===
        revenue_proposals = await self.coordinator.revenue_intelligence(agi_kernel)

        # ⚡ QUICK ACTION CHECKPOINT 3: via coordinator
        quick_actions = await self.coordinator.quick_profit_actions("after-revenue")

        # === CURIOSITY GOALS: via coordinator ===
        curiosity_proposals = await self.coordinator.curiosity_goals(agi_kernel)

        # === PERSISTENT INTENTS: via coordinator ===
        intent_proposals = await self.coordinator.maintain_persistent_intents(agi_kernel)

        # === ASSEMBLE PROPOSALS: via coordinator ===
        proposals = await self.coordinator.assemble_proposals(
            agi_kernel, agi_actions, active_work_items, spine_context,
            memory_proposals, revenue_proposals, curiosity_proposals, intent_proposals
        )

        # === CROSS-DOMAIN SYNTHESIS: via coordinator ===
        await self.coordinator.cross_domain_synthesis(agi_kernel, observations, proposals)

        # === MOLTX SUGGESTED ACTIONS ===
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

        # === ACT: Execute proposals via coordinator ===
        executed = await self.coordinator.execute_proposals(proposals, agi_kernel, next_action)

        # === REFLECT ===
        await self._run_agi_social_cycle()

        cognitive_end = self.cognitive.reflect()
        beliefs = self.cognitive.belief_engine.get_domain_strengths()
        calibration = self.cognitive.get_belief_calibration()
        logger.info(
            f"🧠 Cycle end: {cognitive_end.get('overall_assessment', '?')} | "
            f"Beliefs: {len(beliefs)} domains | "
            f"Calibrated: {calibration.get('calibrated', '?')} | "
            f"Error: {calibration.get('mean_absolute_error', '?')}"
        )

        # === META ADAPTATION: via coordinator ===
        await self.coordinator.meta_adaptation(agi_kernel)

        # === ADVANCE ACTIVE PLANS: via coordinator ===
        plan_result = await self.coordinator.advance_active_plans(agi_kernel)

        if executed == 0 and not plan_result:
            exploratory = self.coordinator.handle_idle_state(active_work_items, proposals, spine_context)
            if exploratory:
                logger.info(f"🚀 Attempting {len(exploratory)} exploratory actions")
                for proposal in exploratory:
                    result = await self._execute_proposal(proposal)
                    if result:
                        executed += 1
                        self._actions_this_hour += 1
                        self.stats['actions_taken'] += 1
                        logger.info(f"✅ Executed exploratory action: {proposal.action_type}")
                    await asyncio.sleep(1)

        logger.info(f"✅ Executed {executed}/{len(proposals)} actions")

        # === GOAL QUOTA ENFORCEMENT ===
        await self._enforce_goal_quota()

        # === CORE GOAL REMINDER ===
        if self.narrative_self:
            goals = self.narrative_self.get_goals('active')
            core_goal = next((g for g in goals if '10%' in g.description or 'profit' in g.description.lower()), None)
            if core_goal:
                logger.info(f"🎯 Core goal: {core_goal.description[:80]} (progress: {core_goal.progress:.0%})")
            elif not goals:
                logger.info("🎯 No active goals — core profit goal may need seeding")

        # === NARRATIVE RECORDING ===
        self._record_cycle_narrative(executed, len(proposals), len(observations), spine_context)

        logger.info("🔄 === Brain Cycle Complete ===")
    
    async def _gather_observations(self) -> List[SyModObservation]:
        """Delegate to brain module."""
        return await self.coordinator.gather_observations()


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
        """Delegate to brain module."""
        return await self.coordinator.feed_observations_to_world_state(observations)


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
        """Delegate to brain module."""
        return await self.coordinator.think.get_proposals()


    def _get_recent_routed_outcomes(self, limit: int = 40) -> List[Dict[str, Any]]:
        """Delegate to brain module."""
        return self.coordinator.think.get_recent_routed_outcomes(limit)


    def _estimate_predicted_value(self, proposal: Any) -> str:
        """Delegate to brain module."""
        return self.coordinator.think.estimate_predicted_value(proposal)


    def _recall_memory_signals(self, proposal: Any) -> Dict[str, Any]:
        """Delegate to brain module."""
        return self.coordinator.think.recall_memory_signals(proposal)


    def _apply_memory_shaped_ranking(self, proposals: List[Any]) -> None:
        """Delegate to brain module."""
        return self.coordinator.think.apply_memory_shaped_ranking(proposals)


    def _apply_meta_learning_bias(self, proposals: List[Any]) -> None:
        """Delegate to brain module."""
        return self.coordinator.think.apply_meta_learning_bias(proposals)


    def _apply_transfer_learning_bias(self, proposals: List[Any]) -> None:
        """Delegate to brain module."""
        return self.coordinator.think.apply_transfer_learning_bias(proposals)


    def _apply_active_goal_bias(self, proposals: List[Any]) -> None:
        """Delegate to brain module."""
        return self.coordinator.think.apply_active_goal_bias(proposals)


    def _apply_active_work_item_bias(self, proposals: List[Any], active_work_items: List[Dict[str, Any]]) -> None:
        """Delegate to brain module."""
        return self.coordinator.think.apply_active_work_item_bias(proposals, active_work_items)


    async def _run_agi_orchestration_cycle(self) -> List[Any]:
        """Delegate to brain module."""
        return await self.coordinator.run_agi_orchestration()


    async def _convert_agi_action_to_proposal(self, agi_action: Dict, phases_executed) -> Optional[Any]:
        """Delegate to brain module."""
        return await self.coordinator.think.convert_agi_action_to_proposal(agi_action, phases_executed)


    async def _extract_creative_proposals(self, creative_output: Dict, phases_executed) -> List[Any]:
        """Delegate to brain module."""
        return await self.coordinator.think.extract_creative_proposals(creative_output, phases_executed)


    def _generate_post_from_concept(self, concept: str) -> str:
        """Return topic for intelligent posting system (don't generate content here)"""
        # Just return the concept as a topic - intelligent_post will handle generation
        return concept if concept else ''
    
    async def _phase_detect_opportunities(self) -> List:
        """Delegate to brain module."""
        return await self.coordinator.detect_opportunities()


    async def _phase_skill_gap_analysis(self, observations, agi_kernel):
        """Delegate to brain module."""
        return await self.coordinator.skill_gap_analysis(observations, agi_kernel)


    async def _phase_maintain_persistent_intents(self, agi_kernel) -> List:
        """Delegate to brain module."""
        return await self.coordinator.maintain_persistent_intents(agi_kernel)


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
        """Delegate to brain module."""
        return await self.coordinator.cross_domain_synthesis(agi_kernel, observations, proposals)


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
        """Delegate to brain module."""
        return await self.coordinator.memory_driven_thinking(observations, agi_kernel)


    async def _phase_assemble_proposals(self, agi_kernel, agi_actions, active_work_items, spine_context, memory_proposals=None, revenue_proposals=None, curiosity_proposals=None, intent_proposals=None):
        """Delegate to brain module."""
        return await self.coordinator.assemble_proposals(agi_kernel, agi_actions, active_work_items, spine_context, memory_proposals, revenue_proposals, curiosity_proposals, intent_proposals)


    async def _adversarial_self_critique(self, agi_kernel) -> List[Dict]:
        """Delegate to brain module."""
        return await self.coordinator.think.adversarial_self_critique(agi_kernel)


    async def _phase_periodic_reflection(self, agi_kernel):
        """Delegate to brain module."""
        return await self.coordinator.periodic_reflection(agi_kernel)


    def _propose_architecture_changes(self) -> List[str]:
        """Delegate to brain module."""
        return self.coordinator.self_improve.propose_architecture_changes()


    async def _phase_chess_win_posts(self) -> None:
        """Delegate to brain module."""
        return await self.coordinator.post_chess_wins()


    async def _phase_revenue_intelligence(self, agi_kernel=None) -> List:
        """Delegate to brain module."""
        return await self.coordinator.revenue_intelligence(agi_kernel)


    async def _phase_curiosity_goals(self, agi_kernel) -> List:
        """Delegate to brain module."""
        return await self.coordinator.curiosity_goals(agi_kernel)


    def _is_action_implemented(self, plugin: str, action: str) -> bool:
        """Delegate to brain module."""
        return self.coordinator.self_improve.is_action_implemented(plugin, action)


    def _phase_goal_management(self, agi_kernel, observations):
        """Delegate to brain module."""
        return self.coordinator.goal_management(agi_kernel, observations)


    def _phase_theory_of_mind(self, observations: List) -> Optional['IntentInference']:
        """Delegate to brain module."""
        return self.coordinator.theory_of_mind(observations)


    def _record_cycle_narrative(self, actions_executed: int, total_proposals: int,
                                 observation_count: int, spine_context: Dict) -> None:
        """Record this cycle's outcome into the persistent narrative self."""
        if not self.narrative_self:
            return
        try:
            summary_parts = []
            if actions_executed > 0:
                summary_parts.append(f"executed {actions_executed} actions")
            if total_proposals > 0:
                summary_parts.append(f"{total_proposals} proposals")
            if observation_count > 0:
                summary_parts.append(f"{observation_count} observations")
            if spine_context.get('owner_inferred_intent'):
                summary_parts.append(f"owner intent: {spine_context['owner_inferred_intent']}")

            summary = ', '.join(summary_parts) if summary_parts else "idle cycle"
            outcome = 'success' if actions_executed > 0 else 'ongoing'

            self.narrative_self.record(
                event_type='brain_cycle',
                summary=summary,
                outcome=outcome,
                details={
                    'actions': actions_executed,
                    'proposals': total_proposals,
                    'observations': observation_count,
                    'intent': spine_context.get('owner_inferred_intent'),
                },
            )

            # Sync goals from narrative
            if self.cognitive and hasattr(self.cognitive, 'goal_planner'):
                planner = getattr(self.cognitive, 'goal_planner', None)
                if planner and hasattr(planner, 'get_active_goals'):
                    active_goals = planner.get_active_goals()
                    if active_goals:
                        for goal in active_goals[:3]:
                            gid = goal.get('id', str(hash(str(goal))))
                            if not any(g.id == gid for g in self.narrative_self.get_goals('active')):
                                self.narrative_self.add_goal(
                                    description=goal.get('description', goal.get('summary', str(goal)))[:120],
                                    priority='active',
                                    goal_id=gid,
                                )
        except Exception as e:
            logger.debug(f"Narrative recording error: {e}")

    async def _phase_causal_reasoning(self, observations: List, agi_kernel=None) -> Dict:
        """Delegate to brain module."""
        return await self.coordinator.causal_reasoning(observations, agi_kernel)


    async def _phase_consolidate_learning(self, agi_kernel=None) -> None:
        """Delegate to brain module."""
        return await self.coordinator.consolidate_learning(agi_kernel)


    async def _phase_meta_adaptation(self, agi_kernel=None) -> None:
        """Delegate to brain module."""
        return await self.coordinator.meta_adaptation(agi_kernel)


    async def _phase_plugin_discovery_and_creation(self, agi_kernel=None) -> None:
        """Delegate to brain module."""
        return await self.coordinator.plugin_discovery(agi_kernel)


    async def _phase_learning_goal_acquisition(self, agi_kernel=None) -> None:
        """Delegate to brain module."""
        return await self.coordinator.learning_acquisition(agi_kernel)


    async def _phase_execute_proposals(self, proposals, agi_kernel, next_action) -> int:
        """Delegate to brain module."""
        return await self.coordinator.execute_proposals(proposals, agi_kernel, next_action)


    def _record_proposal_success(self, proposal, result, agi_kernel, next_action):
        """Delegate to brain module."""
        return self.coordinator.act._record_proposal_success(proposal, result, agi_kernel, next_action)


    def _record_proposal_failure(self, proposal, agi_kernel):
        """Delegate to brain module."""
        return self.coordinator.act._record_proposal_failure(proposal, agi_kernel)


    async def _execute_proposal(self, proposal) -> Optional[Dict]:
        """Delegate to brain module."""
        return await self.coordinator.act._execute_proposal(proposal)


    async def _notify_user_of_goal_result(self, proposal: Any, result: Dict[str, Any]) -> None:
        """Delegate to brain module."""
        return await self.coordinator.act._notify_user_of_goal_result(proposal, result)


    def _build_runtime_spine_context(
        self,
        observations: List[Any],
        active_work_items: List[Dict[str, Any]],
        opportunities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Delegate to brain module."""
        return self.coordinator.build_spine_context(observations=observations, active_work_items=active_work_items, opportunities=opportunities)


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
        """Delegate to brain module."""
        return self.coordinator.think.apply_runtime_spine_bias(proposals, spine_context)


    def _apply_cognitive_bias(self, proposals: List[Any]) -> None:
        """Delegate to brain module."""
        return self.coordinator.think.apply_cognitive_bias(proposals)


    def _prioritize_runtime_spine_proposals(self, proposals: List[Any], spine_context: Dict[str, Any]) -> List[Any]:
        """Delegate to brain module."""
        return self.coordinator.think.prioritize_runtime_spine_proposals(proposals, spine_context)


    async def _generate_default_goals(self) -> bool:
        """Delegate to brain module."""
        return await self.coordinator.generate_default_goals()


    async def _detect_skill_gaps(self, agi_kernel) -> List[Dict]:
        """Delegate to brain module."""
        return await self.coordinator.self_improve.detect_skill_gaps(agi_kernel)


    def _handle_idle_state(self, active_work_items: List[Dict[str, Any]], proposals: List[Any], spine_context: Dict[str, Any]) -> List[Any]:
        """Delegate to brain module."""
        return self.coordinator.handle_idle_state(active_work_items, proposals, spine_context)


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
    
    async def _check_for_quick_profit_actions(self, checkpoint: str) -> int:
        """Delegate to brain module."""
        return await self.coordinator.quick_profit_actions(checkpoint)


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
        """Delegate to brain module."""
        return await self.coordinator.think.generate_proactive_goals(observations)


    async def _generate_curiosity_goals(self) -> List[Dict[str, Any]]:
        """Delegate to brain module."""
        return await self.coordinator.think.generate_curiosity_goals()


    async def _advance_active_plans(self, agi_kernel=None) -> bool:
        """Delegate to brain module."""
        return await self.coordinator.advance_active_plans(agi_kernel)

