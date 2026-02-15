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

logger = logging.getLogger(__name__)


@dataclass
class BrainConfig:
    """Configuration for autonomous brain"""
    enabled: bool = False
    mode: str = 'normal'  # 'conservative', 'normal', 'aggressive'
    cycle_interval_minutes: int = 30
    max_actions_per_hour: int = 50
    min_confidence: float = 0.6
    require_owner_approval: bool = False
    
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
                require_owner_approval=True
            ),
            'normal': cls(
                enabled=True,
                mode='normal',
                cycle_interval_minutes=30,
                max_actions_per_hour=50,
                min_confidence=0.6,
                require_owner_approval=False
            ),
            'aggressive': cls(
                enabled=True,
                mode='aggressive',
                cycle_interval_minutes=15,
                max_actions_per_hour=100,
                min_confidence=0.4,
                require_owner_approval=False
            )
        }
        return configs.get(mode, cls())


class AutonomousBrain:
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
        
        logger.info("🧠 AutonomousBrain initialized")
    
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
        
        # Register all plugins with SyMod
        self.register_plugins_with_symod()
        
        # Start background task
        self._task = asyncio.create_task(self._brain_loop())
        
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
        """Main autonomous loop"""
        logger.info("🔄 Brain loop started")
        
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
                await asyncio.sleep(60)  # Brief pause on error
        
        logger.info("🔄 Brain loop stopped")
    
    async def _execute_cycle(self) -> None:
        """Execute one full SENSE-THINK-ACT-REFLECT cycle"""
        logger.info("🔄 === Brain Cycle Start ===")
        
        # === SENSE: Gather observations from all platforms ===
        observations = await self._gather_observations()
        logger.info(f"👁️ Gathered {len(observations)} observations")
        
        # Submit to SyMod
        for obs in observations:
            self.symod.observe(obs)
        
        # === THINK: Get action proposals ===
        proposals = await self._get_proposals()
        logger.info(f"🧠 Generated {len(proposals)} proposals")
        
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
            
            if result:
                executed += 1
                self._actions_this_hour += 1
                self.stats['actions_taken'] += 1
                
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
                
                # Log outcome
                self.action_logger.log_outcome(
                    record.id,
                    'success' if result.get('success') else 'failure',
                    result
                )
            
            # Brief pause between actions
            await asyncio.sleep(2)
        
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
        
        # TODO: Add other platforms (MoltBook, Clawbr, etc.)
        
        return observations
    
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
                
                # Get plugin proposals
                plugin_proposals = self.symod.propose_actions(
                    plugin_name,
                    context={
                        'constraints': {
                            'max_actions': 5,  # Per plugin per cycle
                            'min_confidence': self.config.min_confidence
                        }
                    },
                    available_actions=['like', 'reply', 'repost', 'follow', 'post']
                )
                
                # Tag with plugin name
                for p in plugin_proposals:
                    if not p.metadata:
                        p.metadata = {}
                    p.metadata['plugin'] = plugin_name
                
                proposals.extend(plugin_proposals)
        
        # Sort by confidence
        proposals.sort(key=lambda p: p.confidence, reverse=True)
        
        return proposals
    
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
            
            # Execute
            # This would call the plugin's execute_action method
            # For now, log what we would do
            logger.info(
                f"🎯 Would execute: {proposal.action_type} on {proposal.target_name} "
                f"via {plugin_name} (conf: {proposal.confidence:.2f})"
            )
            
            # TODO: Actually execute via plugin interface
            # result = await plugin.execute_action(proposal)
            
            return {'success': True, 'action': proposal.action_type}
            
        except Exception as e:
            logger.error(f"❌ Execution error: {e}")
            return {'success': False, 'error': str(e)}
    
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
            'recent_stats': action_stats
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
