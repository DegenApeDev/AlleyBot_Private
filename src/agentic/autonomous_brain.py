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
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import os

from src.agentic.action_logger import ActionLogger, ActionRecord
from src.agentic.symod_core import get_symod_manager, SyModObservation
from src.agentic.skilldoc_manager import get_skilldoc_manager
from src.agentic.agi_social_mixin import AGISocialMixin
from src.agentic.agi_orchestrator import get_agi_orchestrator
from src.agentic.moltx_agi_integration import gather_moltx_service_insights, execute_moltx_suggested_actions
from src.agentic.cross_platform_intel import get_cross_platform_intelligence
from src.agentic.opportunity_monitor import get_opportunity_monitor
from src.agentic.outcome_learner import get_outcome_learner
from src.agentic.trading_observations import gather_trading_observations, get_trading_summary

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
from src.agentic.duat_cognition import get_duat_engine

# Phase 8-9: Service Integration Layer
from src.agentic.service_integration import (
    get_integrated_work_item_service,
    get_integrated_notification_service,
    get_integrated_memory_service,
)
from src.agentic.contracts import WorkItemState, NotificationPriority

logger = logging.getLogger(__name__)


@dataclass
class BrainConfig:
    """Configuration for autonomous brain operation"""
    enabled: bool = True
    mode: str = 'normal'  # conservative, normal, aggressive
    cycle_interval_minutes: int = 30
    max_actions_per_hour: int = 50
    min_confidence: float = 0.35
    require_owner_approval: bool = False  # Always False - AlleyBot decides autonomously
    
    # Mode-specific overrides
    @classmethod
    def from_mode(cls, mode: str) -> 'BrainConfig':
        configs = {
            'conservative': cls(
                enabled=True,
                mode='conservative',
                cycle_interval_minutes=60,
                max_actions_per_hour=20,
                min_confidence=0.5,
                require_owner_approval=False  # Moderate confidence threshold
            ),
            'normal': cls(
                enabled=True,
                mode='normal',
                cycle_interval_minutes=30,
                max_actions_per_hour=50,
                min_confidence=0.35,
                require_owner_approval=False  # Balanced autonomous operation
            ),
            'aggressive': cls(
                enabled=True,
                mode='aggressive',
                cycle_interval_minutes=15,
                max_actions_per_hour=100,
                min_confidence=0.25,
                require_owner_approval=False  # Maximum autonomy and experimentation
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
        
        # Duat Cognition Engine - consciousness state tracking
        self.duat = get_duat_engine()
        
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
        
        # Statistics
        self.stats = {
            'cycles_completed': 0,
            'actions_taken': 0,
            'actions_blocked': 0,
            'errors': 0,
            'start_time': None
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
        
        # AGI Foundation Systems (85% AGI)
        self.knowledge_graph = get_knowledge_graph()
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
        
        # Duat Cognition: Perform reflection at cycle start
        duat_reflection = self.duat.reflection()
        logger.info(f"🜂 Duat State: awareness={duat_reflection['awareness']:.2f}, distortion={duat_reflection['distortion']:.2f}")
        
        active_work_items: List[Dict[str, Any]] = []
        spine_context: Dict[str, Any] = {}
        opportunities = []
        
        # === OPPORTUNITY DETECTION: Check for interrupts ===
        if self.opportunity_monitor:
            opportunities = self.opportunity_monitor.scan_for_opportunities()
            interrupt_opps = self.opportunity_monitor.get_interrupt_opportunities()
            
            if interrupt_opps:
                logger.warning(f"🚨 {len(interrupt_opps)} high-priority opportunities detected!")
                # Handle interrupts (could expand this to actually interrupt)
            
            # === WORK ITEM CREATION: Create durable work from opportunities ===
            if self.work_item_service and self._services_available and opportunities:
                try:
                    for opp in opportunities[:3]:  # Top 3 opportunities
                        opp_title = opp.get('title', 'Autonomous opportunity')
                        opp_desc = opp.get('description', 'Detected by opportunity monitor')
                        opp_type = opp.get('type', 'opportunity')
                        
                        # Check if similar work item already exists
                        existing = self.work_item_service.get_active_items()
                        duplicate = any(
                            o.title == opp_title for o in existing
                        )
                        
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
                            
                            # Notify owner of new opportunity-based work
                            if self.notification_service:
                                await self.notification_service.notify(
                                    title="🎯 New Work Item Created",
                                    message=f"Opportunity detected: {opp_title}",
                                    priority=NotificationPriority.LOW,
                                    source_work_item=work_item.id,
                                )
                except Exception as e:
                    logger.debug(f"Work item creation error (non-critical): {e}")
        
        # === SENSE: Gather observations from all platforms ===
        observations = await self._gather_observations()
        logger.info(f"👁️ Gathered {len(observations)} observations")
        
        # === CROSS-PLATFORM SYNTHESIS: Connect dots across platforms ===
        if self.cross_platform_intel:
            synthesis = self.cross_platform_intel.synthesize_observations(observations)
            cross_platform_topics = synthesis.get('cross_platform_topics', [])
            opportunities = synthesis.get('opportunities', [])
            
            if cross_platform_topics:
                logger.info(f"🔗 Found {len(cross_platform_topics)} cross-platform topics")
            if opportunities:
                logger.info(f"💡 Identified {len(opportunities)} cross-platform opportunities")
        
        # Submit to SyMod
        for obs in observations:
            self.symod.observe(obs)
        
        # === FEED WORLD STATE DB: pipe observations so inference engine has real data ===
        await self._feed_observations_to_world_state(observations)

        # === WORK-FIRST CONTINUITY: Pull active meaningful work before broad proposal generation ===
        agi_kernel = getattr(self.core, 'agi_kernel', None) if self.core else None
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
        
        # === AUTO SKILL BUILDING: Detect capability gaps and build new skills ===
        if self.auto_skill_builder:
            try:
                # Detect gaps from observations
                skill_proposals = await self.auto_skill_builder.detect_capability_gaps(observations)
                if skill_proposals:
                    logger.info(f"💡 Detected {len(skill_proposals)} capability gaps")
                
                # Auto-build simple skills (max 1 per cycle to avoid overload)
                built_count = await self.auto_skill_builder.auto_build_simple_skills(max_skills=1)
                if built_count > 0:
                    logger.info(f"🔨 Auto-built {built_count} new skill(s)")
            except Exception as e:
                logger.warning(f"⚠️ Auto skill building error: {e}")
        
        # === AUTONOMOUS CODING: Detect skill gaps and generate code ===
        # This is VERTICAL intelligence - self-improvement through code generation
        skill_gaps = await self._detect_skill_gaps(agi_kernel)
        
        if skill_gaps:
            logger.info(f"🔍 Detected {len(skill_gaps)} skill gaps")
            
            # Get self-improvement plugin
            selfimprove_plugin = self.plugin_manager.get_plugin('selfimprove') if self.plugin_manager else None
            
            if selfimprove_plugin:
                # Process highest priority gap
                gap = max(skill_gaps, key=lambda g: g['priority'])
                
                # Check if we should auto-generate code for this gap
                if gap['priority'] >= 7 and gap['type'] == 'repeated_failure':
                    logger.info(f"🤖 Auto-generating skill for gap: {gap['description']}")
                    
                    try:
                        # Generate skill specification
                        from src.agentic.autonomous_coder import SkillSpecification
                        
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
                        
                        # Generate code using autonomous coder
                        from src.agentic.autonomous_coder import AutonomousCoder
                        coder = AutonomousCoder()
                        
                        skill = coder.generate_skill(spec)
                        
                        if skill.status == 'generated':
                            logger.info(f"✅ Generated skill: {skill.skill_name}")
                            
                            # Test in sandbox
                            test_result = selfimprove_plugin.test_code_in_sandbox(
                                code=open(skill.files_created[0]).read() if skill.files_created else "",
                                test_code=None
                            )
                            
                            if test_result['success']:
                                # Deploy if safe
                                coder.deploy_skill(skill)
                                logger.info(f"🚀 Deployed skill: {skill.skill_name}")
                                
                                # Record in episodic memory
                                if agi_kernel and hasattr(agi_kernel, 'episodic_memory'):
                                    agi_kernel.episodic_memory.record_episode(
                                        action_type='skill_generation',
                                        context={'gap': gap, 'skill': skill.skill_name},
                                        outcome={'success': True, 'deployed': True}
                                    )
                            else:
                                logger.warning(f"⚠️ Skill failed sandbox test: {test_result.get('error', 'Unknown error')}")
                        else:
                            logger.warning(f"⚠️ Skill generation failed: {skill.errors}")
                    except Exception as e:
                        logger.warning(f"⚠️ Autonomous coding error: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
        
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
        
        # === HIERARCHICAL GOALS: Get actionable goals and plan next actions ===
        if self.goal_hierarchy and self.planner:
            actionable_goals = self.goal_hierarchy.get_actionable_goals()
            logger.info(f"🎯 {len(actionable_goals)} actionable goals")
            
            # Get next immediate action from planner
            next_action = self.planner.get_next_action()
            if next_action:
                logger.info(f"⚡ Next planned action: {next_action.description}")
        
        # === AUTONOMOUS GOAL GENERATION: Scan observations for opportunities ===
        # This is the core AGI behavior - AlleyBot detects opportunities and creates goals
        if agi_kernel and hasattr(agi_kernel, 'goal_manager'):
            try:
                # Scan for opportunities using autonomous goal system
                goal_manager = agi_kernel.goal_manager
                if goal_manager and hasattr(goal_manager, 'scan_and_generate'):
                    # Get onchain plugin for opportunity detection
                    onchain_plugin = self.plugin_manager.get_plugin('onchain') if self.plugin_manager else None
                    
                    # Generate goals from observations and opportunities
                    new_autonomous_goals = goal_manager.scan_and_generate(onchain_plugin=onchain_plugin)
                    
                    if new_autonomous_goals:
                        logger.info(f"🎯 Generated {len(new_autonomous_goals)} autonomous goals from observations")
                        
                        # Auto-activate high-priority goals (priority >= 8.0)
                        for goal in new_autonomous_goals:
                            if goal.priority_score >= 8.0:
                                goal_manager.approve_goal(goal.id)
                                logger.info(f"✅ Auto-activated high-priority goal: {goal.description}")
            except Exception as e:
                logger.debug(f"Autonomous goal generation error: {e}")
        
        # === SELF-DIRECTED GOALS: Propose new goals based on observations ===
        if hasattr(self, 'goal_stack') and self.goal_stack and self.cross_platform_intel:
            new_goals = self.goal_stack.auto_add_proposed_goals(
                observations, 
                self.cross_platform_intel,
                max_new_goals=2
            )
            if new_goals > 0:
                logger.info(f"🎯 Self-proposed {new_goals} new goals")

        # === GOAL MANAGER V2: Auto-approve and activate safe goals ===
        if self.goal_manager_v2:
            try:
                # Auto-approve safe goals that meet criteria
                from src.agentic.goal_manager import GoalStatus
                proposed_goals = self.goal_manager_v2.get_goals(status=GoalStatus.PROPOSED, limit=5)
                
                for goal in proposed_goals:
                    if self.goal_manager_v2.should_auto_approve_goal(goal):
                        self.goal_manager_v2.approve_goal(goal.id)
                        logger.info(f"✅ Auto-approved safe goal: {goal.title}")
                
                # Start the next approved goal if idle
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
        
        # === GOAL-DRIVEN ACTIONS: Get next action from active autonomous goals ===
        goal_driven_action = None
        if agi_kernel and hasattr(agi_kernel, 'goal_manager'):
            try:
                goal_manager = agi_kernel.goal_manager
                
                # Get active goals
                from src.agentic.goal_manager import GoalStatus
                active_goals = goal_manager.get_goals(status=GoalStatus.ACTIVE, limit=5)
                
                if active_goals:
                    # Get next action for highest priority goal
                    for goal in sorted(active_goals, key=lambda g: g.impact_score, reverse=True):
                        next_action = goal_manager.get_next_action_for_goal(goal)
                        if next_action:
                            goal_driven_action = next_action
                            logger.info(f"🎯 Goal-driven action: {next_action['action_type']} for goal '{goal.title}'")
                            break
                
                # If no active goals, scan for new opportunities
                if not active_goals:
                    onchain_plugin = self.plugin_manager.get_plugin('onchain') if self.plugin_manager else None
                    new_goals = goal_manager.scan_and_generate(onchain_plugin=onchain_plugin)
                    if new_goals:
                        logger.info(f"🎯 Generated {len(new_goals)} new autonomous goals from observations")
                        # Try to get action from newly created goals
                        for goal in new_goals:
                            if goal.status == GoalStatus.ACTIVE or goal.status == GoalStatus.APPROVED:
                                next_action = goal_manager.get_next_action_for_goal(goal)
                                if next_action:
                                    goal_driven_action = next_action
                                    logger.info(f"🎯 Goal-driven action from new goal: {next_action['action_type']}")
                                    break
            except Exception as e:
                logger.debug(f"Goal-driven action retrieval error: {e}")
        
        # === THINK: Get action proposals from both SyMod and AGI ===
        proposals = await self._get_proposals()
        proposals.extend(agi_actions)  # Add AGI-generated actions
        
        # Add goal-driven action as high-priority proposal if available
        if goal_driven_action:
            from src.agentic.symod_core import SyModActionProposal
            goal_proposal = SyModActionProposal(
                action_type=goal_driven_action.get('action_type', 'unknown'),
                target_id=goal_driven_action.get('params', {}).get('target_id'),
                target_name=goal_driven_action.get('goal_description', 'Goal-driven action'),
                confidence=0.85,  # High confidence for goal-driven actions
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
            proposals.insert(0, goal_proposal)  # Add at front for priority
            logger.info("🎯 Goal-driven action added to proposals with high priority")
        
        # Apply AGI learning systems to proposal ranking
        self._apply_meta_learning_bias(proposals)  # Use learned strategies
        self._apply_transfer_learning_bias(proposals)  # Apply cross-domain patterns
        self._apply_active_work_item_bias(proposals, active_work_items)
        self._apply_runtime_spine_bias(proposals, spine_context)
        proposals = self._prioritize_runtime_spine_proposals(proposals, spine_context)
        logger.info(f"🧠 Generated {len(proposals)} total proposals (AGI learning applied)")
        
        # === EXECUTE MOLTX SUGGESTED ACTIONS ===
        # Execute actions suggested by MoltX service messages (quote posts, trending checks, etc.)
        # Run in thread pool to avoid blocking event loop (sync HTTP calls)
        moltx = self.plugin_manager.get_plugin('moltx')
        if moltx:
            loop = asyncio.get_event_loop()
            moltx_results = await loop.run_in_executor(
                None, execute_moltx_suggested_actions, moltx, self
            )
            if moltx_results:
                logger.info(f"✅ Executed {len(moltx_results)} MoltX-suggested actions")
                for result in moltx_results:
                    if result.get('success'):
                        self.stats['actions_taken'] += 1
                        self._actions_this_hour += 1
        
        # === ACT: Execute proposals ===
        executed = 0
        for proposal in proposals:
            # Check confidence threshold
            if proposal.confidence < self.config.min_confidence:
                logger.debug(f"⛔ Blocked: confidence {proposal.confidence:.2f} < {self.config.min_confidence}")
                self.stats['actions_blocked'] += 1
                continue
            
            # Check if we have budget
            if self._actions_this_hour >= self.config.max_actions_per_hour:
                logger.info("⏸️ Hourly budget exhausted")
                break
            
            # Execute
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

                # Update goal progress for both goal systems
                goal_id = (proposal.metadata or {}).get('goal_id') if getattr(proposal, 'metadata', None) else None
                if goal_id:
                    # Update GoalManager v2 if applicable
                    if self.goal_manager_v2 and hasattr(self.goal_manager_v2, 'record_goal_action_success'):
                        self.goal_manager_v2.record_goal_action_success(
                            goal_id,
                            note=f"{proposal.action_type} via {(proposal.metadata or {}).get('plugin', 'unknown')} succeeded"
                        )
                    
                    # Update AutonomousGoalManager if applicable
                    if agi_kernel and hasattr(agi_kernel, 'goal_manager'):
                        goal_manager = agi_kernel.goal_manager
                        if goal_manager and hasattr(goal_manager, 'complete_action'):
                            goal_manager.complete_action(
                                goal_id,
                                success=True,
                                outcome=f"Successfully executed {proposal.action_type}"
                            )
                
                # === META-LEARNING: Record learning outcome ===
                if self.meta_learner and proposal.action_type:
                    from src.agentic.meta_learner import LearningOutcome
                    from datetime import timedelta
                    
                    outcome = LearningOutcome(
                        id=f"outcome_{datetime.now().timestamp()}",
                        strategy_id="strategy_active_experimentation",  # Default strategy
                        domain=proposal.metadata.get('plugin', 'unknown'),
                        task=proposal.action_type,
                        success=True,
                        learning_time=timedelta(seconds=5),  # Approximate
                        quality_score=proposal.confidence,
                        retention_score=0.8,  # Will be updated later
                        what_worked=[f"Action: {proposal.action_type}"],
                        insights=[f"Confidence {proposal.confidence:.2f} led to success"]
                    )
                    self.meta_learner.record_outcome(outcome)
                
                # === TRANSFER LEARNING: Check for pattern transfer opportunities ===
                if self.transfer_learner and proposal.action_type:
                    # Find applicable patterns from other domains
                    applicable_patterns = self.transfer_learner.find_applicable_patterns(
                        domain=proposal.metadata.get('plugin', 'unknown'),
                        problem=proposal.action_type
                    )
                    if applicable_patterns:
                        logger.info(f"🔄 Found {len(applicable_patterns)} transferable patterns")
                
                # === KNOWLEDGE GRAPH: Add knowledge from successful action ===
                if self.knowledge_graph:
                    from src.agentic.knowledge_graph import Entity, EntityType
                    
                    # Add successful action as knowledge
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
                
                # === GOAL PROGRESS: Update goal progress ===
                if self.goal_hierarchy and next_action and next_action.goal_id:
                    goal = self.goal_hierarchy.get_goal(next_action.goal_id)
                    if goal:
                        new_progress = min(goal.progress + 0.05, 1.0)
                        self.goal_hierarchy.update_progress(next_action.goal_id, new_progress)
                        logger.info(f"📈 Goal progress: {goal.title} → {new_progress:.1%}")
                
                # === PLANNER: Mark action as complete ===
                if self.planner and next_action:
                    self.planner.complete_action(next_action.id)
            else:
                # Record failure for both goal systems
                goal_id = (proposal.metadata or {}).get('goal_id') if getattr(proposal, 'metadata', None) else None
                if goal_id:
                    # Update GoalManager v2 if applicable
                    if self.goal_manager_v2 and hasattr(self.goal_manager_v2, 'record_goal_action_failure'):
                        self.goal_manager_v2.record_goal_action_failure(
                            goal_id,
                            note=f"{proposal.action_type} via {(proposal.metadata or {}).get('plugin', 'unknown')} failed"
                        )
                    
                    # Update AutonomousGoalManager if applicable
                    if agi_kernel and hasattr(agi_kernel, 'goal_manager'):
                        goal_manager = agi_kernel.goal_manager
                        if goal_manager and hasattr(goal_manager, 'complete_action'):
                            goal_manager.complete_action(
                                goal_id,
                                success=False,
                                outcome="Action execution failed"
                            )

                # === OUTCOME LEARNING: Record failure ===
                if self.outcome_learner:
                    self.outcome_learner.record_outcome(
                        action_type=proposal.action_type,
                        platform=proposal.metadata.get('plugin', 'unknown'),
                        success=False,
                        data={'reason': 'execution_failed'}
                    )
            
            # Brief pause between actions
            await asyncio.sleep(2)
        
        # === REFLECT: AGI Social Behaviors ===
        await self._run_agi_social_cycle()
        
        # Duat Cognition: Purification and renewal at cycle end
        duat_purification = self.duat.purification()
        duat_renewal = self.duat.renewal()
        self.duat.advance_time()
        self.duat.save_state()
        logger.info(f"🜂 Duat Purification: truth={duat_purification['truth']:.2f}, coherence={duat_renewal['coherence']:.2f}")

        if executed == 0:
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
        """Collect lightweight read-only recall signals for proposal shaping."""
        signals = {
            'relevant_memory_count': 0,
            'recent_negative_memory_count': 0,
            'entity_context_found': False,
        }

        if not self.agi_kernel:
            return signals

        memory_query = " ".join([
            str(getattr(proposal, 'action_type', '') or ''),
            str(getattr(proposal, 'target_name', '') or ''),
            str(getattr(proposal, 'justification', '') or ''),
        ]).strip()

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
        """Lightly adjust proposal confidence using recent routed outcomes and expected value."""
        if not proposals:
            return

        recent_outcomes = self._get_recent_routed_outcomes()

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

            if average_mismatch is not None:
                if average_mismatch <= 0.25:
                    adjustment += 0.03
                elif average_mismatch >= 0.65:
                    adjustment -= 0.05

            memory_signals = self._recall_memory_signals(proposal)
            if memory_signals['relevant_memory_count'] >= 2:
                adjustment += 0.02
            if memory_signals['recent_negative_memory_count'] >= 1:
                adjustment -= 0.04
            if memory_signals['entity_context_found']:
                adjustment += 0.015

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
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Execution error: {e}")
            return {'success': False, 'error': str(e)}

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

        synergy_ripe = opportunity_urgent or recent_interaction_count > 0 or can_execute_now
        security_allows = not blocked_by_policy
        current_capability_ready = can_execute_now and not blocked_by_runtime

        return {
            'recent_findings_count': len(observations or []),
            'recent_interaction_count': recent_interaction_count,
            'opportunity_count': opportunity_count,
            'has_meaningful_work': bool(active_work_items),
            'top_work_item_id': top_work_item.get('id'),
            'top_work_item_type': top_work_item.get('type'),
            'top_work_item_summary': top_work_item.get('summary'),
            'synergy_ripe': synergy_ripe,
            'security_allows': security_allows,
            'current_capability_ready': current_capability_ready,
            'blocked_by_policy': blocked_by_policy,
            'blocked_by_runtime': blocked_by_runtime,
            'trust_bucket': trust_bucket,
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
            "🧭 Spine | found=%s meaningful=%s synergy_ripe=%s security_allows=%s capability_ready=%s top_work=%s",
            spine_context.get('recent_findings_count', 0),
            spine_context.get('has_meaningful_work', False),
            spine_context.get('synergy_ripe', False),
            spine_context.get('security_allows', False),
            spine_context.get('current_capability_ready', False),
            spine_context.get('top_work_item_summary', 'none'),
        )

    def _apply_runtime_spine_bias(self, proposals: List[Any], spine_context: Dict[str, Any]) -> None:
        """Bias proposals toward opportunity-driven and executable meaningful work before idle exploration."""
        if not proposals or not spine_context:
            return

        meaningful_work = bool(spine_context.get('has_meaningful_work'))
        synergy_ripe = bool(spine_context.get('synergy_ripe'))
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
            if synergy_ripe and any(token in blob for token in ['engage', 'reply', 'analy', 'post']):
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
                
                # Get recent episodes
                try:
                    episodes = agi_kernel.episodic_memory.get_recent_episodes(
                        filters={'outcome': 'failure'},
                        limit=50
                    )
                    recent_failures = episodes if episodes else []
                except:
                    # Fallback: try alternative method
                    if hasattr(agi_kernel.episodic_memory, 'episodes'):
                        all_episodes = agi_kernel.episodic_memory.episodes[-50:]
                        recent_failures = [e for e in all_episodes if e.outcome.get('success') == False]
                
                # Group failures by action type
                failure_patterns = {}
                for episode in recent_failures:
                    action_type = episode.context.get('action_type', 'unknown')
                    if action_type not in failure_patterns:
                        failure_patterns[action_type] = []
                    failure_patterns[action_type].append(episode)
                
                # Identify repeated failures (skill gap indicator)
                for action_type, failures in failure_patterns.items():
                    if len(failures) >= 3:  # 3+ failures = skill gap
                        error_patterns = []
                        for f in failures:
                            error = f.outcome.get('error', 'Unknown error')
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
                    recent_actions = action_logger.get_recent_outcomes(limit=50)
                    
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
                    recent_actions = action_logger.get_recent_outcomes(limit=50)
                    
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
        
        # === CATEGORY 6: SELF-IMPROVEMENT (Only if bounded evidence exists) ===
        # Skip internal plugin actions - no 'internal' plugin exists
        # These require capability_gap evidence from work items
        
        # Skip world_state_refresh - no 'internal' plugin exists
        # Brain handles its own state refresh internally
        
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
        except:
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


# Singleton instance
_brain_instance: Optional[AutonomousBrain] = None


def get_autonomous_brain(core=None, plugin_manager=None, symod=None) -> AutonomousBrain:
    """Get or create brain singleton"""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = AutonomousBrain(core, plugin_manager, symod)
    return _brain_instance
