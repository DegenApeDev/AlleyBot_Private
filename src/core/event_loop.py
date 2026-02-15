"""
AlleyBot Central Event Loop

The EventLoop is the heart of the new architecture. It:
1. Receives events from all platforms (via platform-specific adapters)
2. Normalizes events to PluginEvent format
3. Routes events to PluginManager for distribution
4. Coordinates with Planner for action decisions

See SOP.md for architecture invariants.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from queue import PriorityQueue
import threading

logger = logging.getLogger(__name__)


@dataclass
class QueuedEvent:
    """Event with priority for queue processing"""
    priority: int           # Lower = higher priority (0=urgent, 5=normal, 10=low)
    timestamp: datetime
    event_type: str
    channel: str
    payload: Dict[str, Any]
    
    def __lt__(self, other):
        # Priority queue uses __lt__ - lower priority first, then earlier timestamp
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.timestamp < other.timestamp


class EventLoop:
    """
    Central event processing loop for AlleyBot.
    
    This is the ONLY event loop in the system. All platform events
    enter through here. Plugins do NOT implement their own loops.
    
    Architecture:
        Platform APIs → Platform Adapters → EventLoop → PluginManager → Plugins
                                                    ↓
                                                Planner (decides actions)
                                                    ↓
                                              PluginManager (executes)
    
    Usage:
        loop = EventLoop(plugin_manager, planner)
        
        # Start processing
        await loop.start()
        
        # Submit events from platform adapters
        await loop.submit_event('post', 'moltx', {'content': '...'})
        
        # Stop
        await loop.stop()
    """
    
    # Priority levels
    PRIORITY_URGENT = 0     # System errors, security alerts
    PRIORITY_HIGH = 2       # DMs, mentions, urgent platform events
    PRIORITY_NORMAL = 5     # Regular posts, updates
    PRIORITY_LOW = 10       # Background syncs, analytics
    
    def __init__(self, plugin_manager=None, planner=None, symod=None):
        """
        Initialize event loop.
        
        Args:
            plugin_manager: PluginManager instance for routing
            planner: Planner instance for decision-making
            symod: SyMod core manager
        """
        self.plugin_manager = plugin_manager
        self.planner = planner
        self.symod = symod
        
        # Event queue
        self._queue: asyncio.Queue = asyncio.Queue()
        
        # Processing state
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # Event handlers (for direct routing bypassing queue)
        self._handlers: Dict[str, List[Callable]] = {}
        
        # Statistics
        self._stats = {
            'events_processed': 0,
            'events_by_channel': {},
            'events_by_type': {},
            'errors': 0,
            'start_time': None
        }
        
        logger.info("🔄 EventLoop initialized")
    
    async def start(self) -> None:
        """Start the event processing loop"""
        if self._running:
            logger.warning("⚠️ EventLoop already running")
            return
        
        self._running = True
        self._stats['start_time'] = datetime.now()
        self._task = asyncio.create_task(self._process_loop())
        
        logger.info("🔄 EventLoop started")
    
    async def stop(self) -> None:
        """Stop the event processing loop"""
        if not self._running:
            return
        
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Process remaining events
        remaining = []
        while not self._queue.empty():
            try:
                remaining.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        
        if remaining:
            logger.info(f"⏳ Processing {len(remaining)} remaining events...")
            for event in remaining:
                await self._process_single_event(event)
        
        logger.info("🛑 EventLoop stopped")
    
    async def submit_event(self, 
                          event_type: str, 
                          channel: str, 
                          payload: Dict[str, Any],
                          priority: int = PRIORITY_NORMAL) -> bool:
        """
        Submit an event to be processed.
        
        Called by platform adapters when they receive data.
        
        Args:
            event_type: Type of event (post, message, transaction, etc.)
            channel: Source channel (moltx, telegram, onchain, etc.)
            payload: Event data
            priority: Processing priority (0=urgent, 5=normal, 10=low)
        
        Returns:
            True if queued successfully
        """
        if not self._running:
            logger.warning("⚠️ EventLoop not running, event dropped")
            return False
        
        event = QueuedEvent(
            priority=priority,
            timestamp=datetime.now(),
            event_type=event_type,
            channel=channel,
            payload=payload
        )
        
        await self._queue.put(event)
        logger.debug(f"📥 Queued event: {event_type} from {channel} (p={priority})")
        return True
    
    async def _process_loop(self) -> None:
        """Main processing loop"""
        while self._running:
            try:
                # Get event with timeout to allow checking _running
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._process_single_event(event)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ EventLoop error: {e}")
                self._stats['errors'] += 1
    
    async def _process_single_event(self, event: QueuedEvent) -> None:
        """Process a single event through the pipeline"""
        try:
            logger.debug(f"🔍 Processing {event.event_type} from {event.channel}")
            
            # 1. Route to plugins for observation
            if self.plugin_manager:
                await self.plugin_manager.route_event(
                    event.event_type,
                    event.channel,
                    event.payload
                )
            
            # 2. Update statistics
            self._stats['events_processed'] += 1
            self._stats['events_by_channel'][event.channel] = \
                self._stats['events_by_channel'].get(event.channel, 0) + 1
            self._stats['events_by_type'][event.event_type] = \
                self._stats['events_by_type'].get(event.event_type, 0) + 1
            
            # 3. If this is an observation-worthy event, let planner decide actions
            if self.planner and self._should_plan_actions(event):
                await self.planner.process_observations(event.channel)
            
            # 4. Call direct handlers
            await self._call_handlers(event)
            
        except Exception as e:
            logger.error(f"❌ Error processing event: {e}")
            self._stats['errors'] += 1
    
    def _should_plan_actions(self, event: QueuedEvent) -> bool:
        """Determine if this event should trigger planning"""
        # Only plan for certain event types to avoid spam
        plan_triggers = ['post', 'mention', 'message', 'transaction', 'price_alert']
        return event.event_type in plan_triggers
    
    def register_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register a direct handler for an event type.
        
        Handlers are called after plugin routing. Use sparingly.
        
        Args:
            event_type: Event type to handle
            handler: Async callable(event_type, channel, payload)
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"🎯 Registered handler for {event_type}")
    
    def unregister_handler(self, event_type: str, handler: Callable) -> None:
        """Unregister a handler"""
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
    
    async def _call_handlers(self, event: QueuedEvent) -> None:
        """Call registered handlers for an event"""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event.event_type, event.channel, event.payload)
                else:
                    handler(event.event_type, event.channel, event.payload)
            except Exception as e:
                logger.error(f"❌ Handler error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        uptime = None
        if self._stats['start_time']:
            uptime = (datetime.now() - self._stats['start_time']).total_seconds()
        
        return {
            **self._stats,
            'running': self._running,
            'queue_size': self._queue.qsize(),
            'uptime_seconds': uptime
        }
    
    def is_running(self) -> bool:
        """Check if event loop is running"""
        return self._running


class Planner:
    """
    Central planner that queries SyMod and executes actions.
    
    The planner is called by EventLoop when observations warrant action.
    It:
    1. Collects observations from plugins
    2. Asks SyMod for action proposals
    3. Validates and executes actions via PluginManager
    
    See WORLD_MODEL.md for SyMod integration details.
    """
    
    def __init__(self, plugin_manager=None, symod=None):
        """
        Initialize planner.
        
        Args:
            plugin_manager: For action execution
            symod: For decision-making
        """
        self.plugin_manager = plugin_manager
        self.symod = symod
        
        # Cycle tracking
        self._last_plan_time: Optional[datetime] = None
        self._plan_interval = 30  # Seconds between planning cycles
        
        # Statistics
        self._stats = {
            'planning_cycles': 0,
            'actions_proposed': 0,
            'actions_executed': 0,
            'actions_failed': 0
        }
        
        logger.info("🧠 Planner initialized")
    
    async def process_observations(self, channel: str) -> Dict[str, Any]:
        """
        Process observations from a channel and execute actions.
        
        Called by EventLoop when new observations arrive.
        
        Args:
            channel: Source channel
        
        Returns:
            Execution results
        """
        # Rate limit planning
        now = datetime.now()
        if self._last_plan_time:
            elapsed = (now - self._last_plan_time).total_seconds()
            if elapsed < self._plan_interval:
                return {'skipped': True, 'reason': 'rate_limited'}
        
        self._last_plan_time = now
        self._stats['planning_cycles'] += 1
        
        results = {
            'channel': channel,
            'proposals': 0,
            'executed': 0,
            'failed': 0,
            'actions': []
        }
        
        try:
            # Get plugins for this channel
            plugins = self.plugin_manager.get_plugins_by_channel(channel) if self.plugin_manager else []
            
            for plugin in plugins:
                if not plugin.enabled:
                    continue
                
                # Get available actions for this plugin
                available_actions = self._get_plugin_actions(plugin)
                
                # Get context (would come from plugin's recent observations)
                context = {
                    'channel': channel,
                    'plugin': plugin.name,
                    'constraints': {
                        'max_actions': 5,  # Per cycle limit
                        'min_confidence': 0.6
                    }
                }
                
                # Ask SyMod for proposals
                if self.symod:
                    proposals = self.symod.propose_actions(
                        plugin.name,
                        context,
                        available_actions
                    )
                    
                    results['proposals'] += len(proposals)
                    self._stats['actions_proposed'] += len(proposals)
                    
                    # Execute proposals
                    for proposal in proposals:
                        if not proposal.valid:
                            continue
                        
                        # Validate
                        is_valid, reason = self.symod.validate_action(plugin.name, proposal)
                        if not is_valid:
                            logger.debug(f"⛔ Action blocked: {reason}")
                            continue
                        
                        # Execute
                        exec_result = await self.plugin_manager.execute_action(
                            plugin.name,
                            proposal.action_type,
                            proposal.target_id,
                            proposal.content,
                            proposal.metadata
                        )
                        
                        if exec_result.get('success'):
                            results['executed'] += 1
                            self._stats['actions_executed'] += 1
                        else:
                            results['failed'] += 1
                            self._stats['actions_failed'] += 1
                        
                        results['actions'].append({
                            'plugin': plugin.name,
                            'action': proposal.action_type,
                            'success': exec_result.get('success'),
                            'error': exec_result.get('error')
                        })
                        
                        # Reflect outcome
                        from src.agentic.symod_core import SyModActionOutcome
                        outcome = SyModActionOutcome(
                            action_type=proposal.action_type,
                            success=exec_result.get('success', False),
                            target_id=proposal.target_id,
                            error_message=exec_result.get('error')
                        )
                        self.symod.reflect(plugin.name, proposal, outcome)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Planning error: {e}")
            return {'error': str(e)}
    
    def _get_plugin_actions(self, plugin) -> List[str]:
        """Get list of actions a plugin supports"""
        # This would come from plugin metadata or inspection
        # Default common actions
        common_actions = ['like', 'reply', 'post', 'follow']
        
        # Could be extended based on plugin capabilities
        return common_actions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get planning statistics"""
        return self._stats.copy()
    
    def set_plan_interval(self, seconds: int) -> None:
        """Set minimum seconds between planning cycles"""
        self._plan_interval = seconds
        logger.info(f"⏱️ Plan interval set to {seconds}s")
