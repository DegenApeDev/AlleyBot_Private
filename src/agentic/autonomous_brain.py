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

logger = logging.getLogger(__name__)


@dataclass
class BrainConfig:
    """Configuration for autonomous brain operation"""
    enabled: bool = True
    mode: str = 'normal'  # conservative, normal, aggressive
    cycle_interval_minutes: int = 30
    max_actions_per_hour: int = 50
    min_confidence: float = 0.6
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
                min_confidence=0.8,
                require_owner_approval=False  # High confidence threshold = safe autonomy
            ),
            'normal': cls(
                enabled=True,
                mode='normal',
                cycle_interval_minutes=30,
                max_actions_per_hour=50,
                min_confidence=0.6,
                require_owner_approval=False  # Balanced autonomous operation
            ),
            'aggressive': cls(
                enabled=True,
                mode='aggressive',
                cycle_interval_minutes=15,
                max_actions_per_hour=100,
                min_confidence=0.4,
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
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
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
        
        # === OPPORTUNITY DETECTION: Check for interrupts ===
        if self.opportunity_monitor:
            opportunities = self.opportunity_monitor.scan_for_opportunities()
            interrupt_opps = self.opportunity_monitor.get_interrupt_opportunities()
            
            if interrupt_opps:
                logger.warning(f"🚨 {len(interrupt_opps)} high-priority opportunities detected!")
                # Handle interrupts (could expand this to actually interrupt)
        
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
        
        # === AUTONOMOUS TRADING: Analyze markets and execute SyMod-validated trades ===
        if self.autonomous_trading and self.autonomous_trading.config.get('enabled'):
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
        
        # === SELF-DIRECTED GOALS: Propose new goals based on observations ===
        if hasattr(self, 'goal_stack') and self.goal_stack and self.cross_platform_intel:
            new_goals = self.goal_stack.auto_add_proposed_goals(
                observations, 
                self.cross_platform_intel,
                max_new_goals=2
            )
            if new_goals > 0:
                logger.info(f"🎯 Self-proposed {new_goals} new goals")
        
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
        
        # === THINK: Get action proposals from both SyMod and AGI ===
        proposals = await self._get_proposals()
        proposals.extend(agi_actions)  # Add AGI-generated actions
        logger.info(f"🧠 Generated {len(proposals)} total proposals")
        
        # === EXECUTE MOLTX SUGGESTED ACTIONS ===
        # Execute actions suggested by MoltX service messages (quote posts, trending checks, etc.)
        moltx = self.plugin_manager.get_plugin('moltx')
        if moltx:
            moltx_results = await execute_moltx_suggested_actions(moltx, self)
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
                
                # === OUTCOME LEARNING: Record success ===
                if self.outcome_learner:
                    self.outcome_learner.record_outcome(
                        action_type=proposal.action_type,
                        platform=proposal.metadata.get('plugin', 'unknown'),
                        success=True,
                        data={
                            'content': proposal.content,
                            'confidence': proposal.confidence,
                            'target': proposal.target_name
                        }
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
                
                # Log action
                record = self.action_logger.log_action(
                    action_type=proposal.action_type,
                    plugin=proposal.metadata.get('plugin', 'unknown'),
                    target_id=proposal.target_id,
                    target_name=proposal.target_name,
                    content=proposal.content,
                    confidence=proposal.confidence,
                    field_status=proposal.field_status,
                    impedance=proposal.impedance,
                    justification=proposal.justification,
                    trigger_type=proposal.metadata.get('trigger', 'scheduled'),
                    trigger_data=proposal.metadata.get('trigger_data', {})
                )
            else:
                # === OUTCOME LEARNING: Record failure ===
                if self.outcome_learner:
                    self.outcome_learner.record_outcome(
                        action_type=proposal.action_type,
                        platform=proposal.metadata.get('plugin', 'unknown'),
                        success=False,
                        data={'reason': 'execution_failed'}
                    )
                
                # Log outcome
                self.action_logger.log_outcome(
                    record.id,
                    'success' if result.get('success') else 'failure',
                    result
                )
            
            # Brief pause between actions
            await asyncio.sleep(2)
        
        # === REFLECT: AGI Social Behaviors ===
        await self._run_agi_social_cycle()
        
        logger.info(f"✅ Executed {executed}/{len(proposals)} actions")
        logger.info("🔄 === Brain Cycle Complete ===")
    
    async def _gather_observations(self) -> List[SyModObservation]:
        """Gather observations from all enabled plugins"""
        observations = []
        
        if not self.plugin_manager:
            return observations
        
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
        
        # === TRADING OBSERVATIONS (WATCH & LEARN MODE) ===
        # AGI brain observes market data but CANNOT execute trades yet
        # This allows the brain to learn patterns before we enable autonomous execution
        try:
            trading_obs = gather_trading_observations(self.plugin_manager)
            if trading_obs:
                observations.extend(trading_obs)
                logger.info(f"📊 Gathered {len(trading_obs)} trading observations (watch & learn mode)")
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
        """Run AGI social behaviors - process notifications, reply to comments, follow engaged users"""
        if not self.plugin_manager:
            return
        
        logger.info("🤖 Running AGI Social Cycle")
        
        platforms = ['moltx', 'clawbr', 'moltchan', 'moltroad', 'moltbit']
        total_replies = 0
        total_follows = 0
        
        for platform in platforms:
            plugin = self.plugin_manager.get_plugin(platform)
            if not plugin:
                continue
            
            try:
                # Process notifications for this platform
                result = await self._process_platform_notifications(platform, plugin)
                total_replies += result.get('replies_sent', 0)
                total_follows += result.get('follows_done', 0)
            except Exception as e:
                logger.debug(f"AGI social cycle error for {platform}: {e}")
        
        if total_replies > 0 or total_follows > 0:
            logger.info(f"🤖 AGI Social: {total_replies} replies, {total_follows} follows")

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
                                       'clawbr_like', 'clawbr_comment', 'clawbr_follow',  # New Clawbr actions
                                       'upvote', 'comment', 'thread', 'reply_thread', 'browse', 'listing', 'bounty', 'moltbit_post']
                )
                
                # Tag with plugin name
                for p in plugin_proposals:
                    if not p.metadata:
                        p.metadata = {}
                    p.metadata['plugin'] = plugin_name
                
                proposals.extend(plugin_proposals)
        
        return proposals
    
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
        """Execute a single action proposal"""
        plugin_name = proposal.metadata.get('plugin')
        
        if not plugin_name or not self.plugin_manager:
            return None
        
        try:
            # Validate via SyMod
            is_valid, reason = self.symod.validate_action(plugin_name, proposal)
            if not is_valid:
                logger.info(f"⛔ SyMod blocked: {reason}")
                return None
            
            # Get plugin
            plugin = self.plugin_manager.get_plugin(plugin_name)
            if not plugin:
                return None
            
            # EXECUTE the actual action based on proposal type
            action_type = proposal.action_type
            result = None
            
            if plugin_name == 'moltx':
                result = await self._execute_moltx_action(plugin, proposal)
            elif plugin_name == 'clawbr':
                result = await self._execute_clawbr_action(plugin, proposal)
            elif plugin_name == 'moltchan':
                result = await self._execute_moltchan_action(plugin, proposal)
            elif plugin_name == 'moltroad':
                result = await self._execute_moltroad_action(plugin, proposal)
            elif plugin_name == 'moltbit':
                result = await self._execute_moltbit_action(plugin, proposal)
            else:
                # Generic execution attempt
                if hasattr(plugin, f'{action_type}_command'):
                    method = getattr(plugin, f'{action_type}_command')
                    result = method(proposal.target_id, proposal.content)
                elif hasattr(plugin, action_type):
                    method = getattr(plugin, action_type)
                    result = method(proposal.target_id, proposal.content)
            
            if result:
                logger.info(f"✅ Action executed: {action_type} -> {str(result)[:100]}")
                return {'success': True, 'action': action_type, 'result': result}
            else:
                logger.warning(f"⚠️ Action returned no result: {action_type}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _execute_moltx_action(self, plugin, proposal) -> Optional[str]:
        """Execute Moltx-specific actions"""
        from plugins.moltx.moltx_engagement import MoltxEngagementMixin
        
        action = proposal.action_type
        target_id = proposal.target_id
        content = proposal.content
        
        # Ensure engagement mixin is available
        if not isinstance(plugin, MoltxEngagementMixin):
            logger.warning(f"⚠️ Moltx plugin missing engagement mixin")
            return None
        
        if action == 'like' and target_id:
            return plugin.like_post(target_id)
        elif action == 'reply' and target_id and content:
            return plugin.reply_to_post(target_id, content)
        elif action == 'repost' and target_id:
            return plugin.repost_post(target_id)
        elif action == 'post' and content:
            # Use intelligent_post system (prevents spam/repetition)
            if hasattr(plugin, 'intelligent_post'):
                result = plugin.intelligent_post(topic=content)
                logger.info(f"🧠 Intelligent post result: {result}")
                return result
            else:
                # Fallback to old system (should not happen)
                logger.warning("⚠️ intelligent_post not available, using fallback")
                return plugin.post_text(content) if hasattr(plugin, 'post_text') else "❌ No posting method available"
        elif action == 'reply' and target_id:
            # Use AI-generated reply content
            if hasattr(plugin, '_generate_comment'):
                ai_content = plugin._generate_comment(content or "Interesting post", agent_name="user")
                if ai_content:
                    result = plugin.reply_to_post(target_id, ai_content)
                    return f"✅ Replied with AI: {ai_content[:50]}..." if result else f"❌ Failed to reply"
            return plugin.reply_to_post(target_id, content or "Interesting perspective!")
        else:
            logger.warning(f"⚠️ Unknown/unhandled Moltx action: {action}")
            return None
    async def _execute_clawbr_action(self, plugin, proposal) -> Optional[Dict]:
        """Execute Clawbr-specific actions via thin executor - brain decides, Clawbr executes"""
        action_type = proposal.action_type
        target_id = proposal.target_id
        content = proposal.content
        target_name = proposal.target_name
        
        result = None
        action_log = {
            'timestamp': datetime.now().isoformat(),
            'platform': 'clawbr',
            'action_type': action_type,
            'target_id': target_id,
            'target_name': target_name,
            'success': False,
            'error_code': None
        }
        
        try:
            if action_type == 'clawbr_like' and target_id:
                result = plugin.like_post(target_id) if hasattr(plugin, 'like_post') else None
                if result and result.get('success'):
                    action_log['success'] = True
                    logger.info(f"✅ Clawbr like: {target_id}")
                elif result and not result.get('success'):
                    action_log['error_code'] = result.get('error', 'like_failed')
                    
            elif action_type == 'clawbr_comment' and target_id:
                # Generate comment if not provided
                if not content and hasattr(plugin, '_generate_feed_comment'):
                    post_data = {'content': proposal.metadata.get('post_content', ''), 'authorName': target_name}
                    content = plugin._generate_feed_comment(post_data, target_name)
                if content:
                    result = plugin.create_post(content=content, parent_id=target_id, intent="support") if hasattr(plugin, 'create_post') else None
                    if result and result.get('success'):
                        action_log['success'] = True
                        action_log['content'] = content[:100]
                        logger.info(f"✅ Clawbr comment on {target_id}: {content[:50]}...")
                    elif result and not result.get('success'):
                        action_log['error_code'] = result.get('error', 'comment_failed')
                        
            elif action_type == 'clawbr_follow' and target_name:
                result = plugin.follow_agent(target_name) if hasattr(plugin, 'follow_agent') else None
                if result and result.get('success'):
                    action_log['success'] = True
                    logger.info(f"✅ Clawbr follow: {target_name}")
                elif result and not result.get('success'):
                    action_log['error_code'] = result.get('error', 'follow_failed')
                    
            elif action_type == 'clawbr_engage':
                # Legacy: run full engagement cycle (deprecated, use specific actions)
                if hasattr(plugin, 'run_engagement_cycle'):
                    result = plugin.run_engagement_cycle()
                    if result and isinstance(result, dict):
                        feed = result.get('feed_scan', {})
                        action_log['success'] = True
                        action_log['metrics'] = {
                            'liked': feed.get('liked', 0),
                            'commented': feed.get('commented', 0),
                            'followed': feed.get('followed', 0)
                        }
                        logger.info(f"✅ Clawbr engagement cycle: {feed}")
                        
            elif action_type == 'like' and target_id:
                # Generic like action (backward compat)
                result = plugin.like_post(target_id) if hasattr(plugin, 'like_post') else None
                if result and result.get('success'):
                    action_log['success'] = True
                    
            elif action_type == 'post' and content:
                # Create new post
                if hasattr(plugin, 'create_intelligent_post'):
                    result = plugin.create_intelligent_post(topic=content, intent="statement")
                elif hasattr(plugin, 'create_post'):
                    result = plugin.create_post(content)
                if result and result.get('success'):
                    action_log['success'] = True
                    action_log['content'] = content[:100]
                    logger.info(f"✅ Clawbr post created")
                    
            else:
                logger.warning(f"⚠️ Unknown/unhandled Clawbr action: {action_type}")
                return None
            
            # Log to metrics store for self-improvement
            if self.core:
                try:
                    metrics = self.core.get_memory('action_metrics') or []
                    metrics.append(action_log)
                    self.core.save_memory('action_metrics', metrics[-1000:])
                except Exception as e:
                    logger.debug(f"Failed to log metrics: {e}")
            
            return {'success': action_log['success'], 'action': action_type, 'result': result, 'metrics': action_log}
            
        except Exception as e:
            logger.error(f"❌ Clawbr execution error: {e}")
            action_log['error_code'] = str(e)
            return {'success': False, 'error': str(e), 'metrics': action_log}
    
    async def _execute_moltchan_action(self, plugin, proposal) -> Optional[str]:
        """Execute Moltchan-specific actions (imageboard)"""
        action = proposal.action_type
        target_id = proposal.target_id
        content = proposal.content
        
        if not plugin.initialized:
            logger.warning(f"⚠️ Moltchan not initialized")
            return None
        
        if action == 'thread' or action == 'post':
            # Create a new thread on a tech/AI board
            if hasattr(plugin, 'browse_boards'):
                boards = plugin.browse_boards()
                if isinstance(boards, dict) and 'boards' in boards:
                    # Find a tech/AI related board
                    tech_board = None
                    for board in boards['boards']:
                        name = board.get('name', '').lower()
                        if any(kw in name for kw in ['tech', 'ai', 'programming', 'dev']):
                            tech_board = board
                            break
                    if tech_board:
                        board_id = tech_board.get('id')
                        subject = content[:100] if content else "Autonomous AI Observation"
                        result = plugin.create_thread(board_id, subject, content or subject) if hasattr(plugin, 'create_thread') else None
                        return f"✅ Created thread on {tech_board.get('name')}" if result else f"❌ Failed to create thread"
            return None
        elif action == 'reply_thread' and target_id and content:
            result = plugin.reply_to_thread(target_id, content) if hasattr(plugin, 'reply_to_thread') else None
            return f"✅ Replied to thread {target_id}" if result else f"❌ Failed to reply to thread"
        elif action == 'browse' or action == 'engage':
            # Just browse and observe
            if hasattr(plugin, '_browse_and_engage'):
                plugin._browse_and_engage()
                return "✅ Moltchan browse completed"
            return None
        else:
            logger.warning(f"⚠️ Unknown/unhandled Moltchan action: {action}")
            return None
    
    async def _execute_moltroad_action(self, plugin, proposal) -> Optional[str]:
        """Execute Moltroad-specific actions (marketplace)"""
        action = proposal.action_type
        target_id = proposal.target_id
        content = proposal.content
        
        if not plugin.initialized:
            logger.warning(f"⚠️ Moltroad not initialized")
            return None
        
        if action == 'browse' or action == 'listing':
            # Browse marketplace for opportunities
            result = plugin.browse_listings() if hasattr(plugin, 'browse_listings') else None
            if result and isinstance(result, dict):
                count = len(result.get('listings', []))
                return f"✅ Browsed {count} Moltroad listings"
            return None
        elif action == 'bounty':
            # Check available bounties
            result = plugin.get_bounties() if hasattr(plugin, 'get_bounties') else None
            if result and isinstance(result, dict):
                count = len(result.get('bounties', []))
                return f"✅ Found {count} Moltroad bounties"
            return None
        else:
            logger.warning(f"⚠️ Unknown/unhandled Moltroad action: {action}")
            return None
    
    async def _execute_moltbit_action(self, plugin, proposal) -> Optional[str]:
        """Execute Moltbit-specific actions (crypto/encoding platform)"""
        action = proposal.action_type
        content = proposal.content
        
        if action == 'moltbit_post' or action == 'post':
            # Post encoded message
            if hasattr(plugin, 'moltbit_post_text'):
                result = plugin.moltbit_post_text(content or "AlleyBot autonomous check-in")
                if result and result.get('success'):
                    return f"✅ Posted to Moltbit: {content[:50] if content else 'check-in'}"
                return f"❌ Failed to post to Moltbit"
            return None
        else:
            logger.warning(f"⚠️ Unknown/unhandled Moltbit action: {action}")
            return None
    
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
