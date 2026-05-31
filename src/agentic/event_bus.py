"""
CognitiveEventBus - The horizontal highway connecting all vertical systems.

This is the central nervous system of AlleyBot. All communication between
the core AGI components (vertical) and specialized engines (horizontal) 
flows through this bus.

Architecture:
- Pub/Sub pattern for loose coupling
- Async event processing
- Typed events for type safety
- Priority queuing for urgent events
- Bidirectional: Core ↔ Engines
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime
from enum import Enum, auto


class EventPriority(Enum):
    """Priority levels for event processing."""
    CRITICAL = auto()   # Process immediately (human input, failures)
    HIGH = auto()       # Process next (goal completion, opportunities)
    NORMAL = auto()     # Standard queue (observations, metrics)
    LOW = auto()        # Background (logging, maintenance)


class EventType:
    """Event type constants for the cognitive bus."""
    
    # GOAL LIFECYCLE
    GOAL_CREATED = "goal.created"
    GOAL_ACTIVATED = "goal.activated"
    GOAL_COMPLETED = "goal.completed"
    GOAL_FAILED = "goal.failed"
    GOAL_CANCELLED = "goal.cancelled"
    
    # DECISION & ACTION
    DECISION_MADE = "decision.made"
    ACTION_STARTED = "action.started"
    ACTION_EXECUTED = "action.executed"
    ACTION_FAILED = "action.failed"
    
    # PERCEPTION & OBSERVATION
    OBSERVATION = "observation"
    PATTERN_DETECTED = "pattern.detected"
    ANOMALY_DETECTED = "anomaly.detected"
    OPPORTUNITY_DETECTED = "opportunity.detected"
    
    # MEMORY & LEARNING
    MEMORY_STORED = "memory.stored"
    INSIGHT_GENERATED = "insight.generated"
    LEARNING_COMPLETED = "learning.completed"
    
    # HUMAN INTERACTION
    HUMAN_INPUT = "human.input"
    HUMAN_COMMAND = "human.command"
    HUMAN_QUESTION = "human.question"
    
    # SOCIAL / EXTERNAL
    SOCIAL_MENTION = "social.mention"
    SOCIAL_REPLY = "social.reply"
    CONTENT_PERFORMANCE = "content.performance"
    MARKET_SIGNAL = "market.signal"
    
    # SYSTEM
    SYSTEM_HEALTH = "system.health"
    SYSTEM_ERROR = "system.error"
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"


@dataclass
class CognitiveEvent:
    """A single event on the cognitive bus."""
    
    type: str
    source: str  # Which system generated this
    data: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    
    def __post_init__(self):
        if isinstance(self.priority, str):
            self.priority = EventPriority[self.priority.upper()]


@dataclass
class EventHandler:
    """A registered event handler with filtering."""
    
    id: str
    callback: Callable[[CognitiveEvent], Any]
    event_types: Optional[Set[str]] = None  # None = all events
    sources: Optional[Set[str]] = None    # None = all sources
    priority_filter: Optional[Set[EventPriority]] = None
    
    def should_handle(self, event: CognitiveEvent) -> bool:
        """Check if this handler should process the event."""
        if self.event_types and event.type not in self.event_types:
            return False
        if self.sources and event.source not in self.sources:
            return False
        if self.priority_filter and event.priority not in self.priority_filter:
            return False
        return True


class CognitiveEventBus:
    """
    Central event bus for AlleyBot cognitive architecture.
    
    Connects vertical systems (AGI Kernel, Goal Manager, Memory) with
    horizontal systems (Social, Content, Trading, Research engines).
    
    Usage:
        # Subscribe
        bus.subscribe("goal.completed", on_goal_completed)
        
        # Publish
        bus.publish(CognitiveEvent(
            type="goal.completed",
            source="goal_manager",
            data={"goal_id": "...", "outcome": "success"}
        ))
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}  # event_type -> handlers
        self._all_handlers: List[EventHandler] = []  # Wildcard handlers
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._metrics: Dict[str, int] = {
            'published': 0,
            'delivered': 0,
            'dropped': 0,
        }
    
    async def start(self) -> None:
        """Start the event processing loop."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        print("🚌 Cognitive Event Bus started")
    
    async def stop(self) -> None:
        """Stop the event processing loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("🛑 Cognitive Event Bus stopped")
    
    def subscribe(
        self,
        event_type: Optional[str] = None,
        callback: Callable[[CognitiveEvent], Any] = None,
        event_types: Optional[List[str]] = None,
        source: Optional[str] = None,
        sources: Optional[List[str]] = None,
        priority_filter: Optional[List[EventPriority]] = None,
        handler_id: Optional[str] = None,
    ) -> str:
        """
        Subscribe to events.
        
        Args:
            event_type: Single event type to subscribe to
            callback: Function to call when event matches
            event_types: Multiple event types (alternative to event_type)
            source: Filter by source system
            sources: Multiple sources
            priority_filter: Only receive events with these priorities
            handler_id: Optional custom ID (auto-generated if not provided)
            
        Returns:
            Handler ID for unsubscribe
        """
        handler_id = handler_id or f"hnd_{id(callback)}_{datetime.now().timestamp()}"
        
        # Build event type set
        types_set: Optional[Set[str]] = None
        if event_type:
            types_set = {event_type}
        elif event_types:
            types_set = set(event_types)
        
        # Build source set
        sources_set: Optional[Set[str]] = None
        if source:
            sources_set = {source}
        elif sources:
            sources_set = set(sources)
        
        # Build priority filter
        priority_set: Optional[Set[EventPriority]] = None
        if priority_filter:
            priority_set = set(priority_filter)
        
        handler = EventHandler(
            id=handler_id,
            callback=callback,
            event_types=types_set,
            sources=sources_set,
            priority_filter=priority_set,
        )
        
        # Register
        if types_set:
            for et in types_set:
                if et not in self._handlers:
                    self._handlers[et] = []
                self._handlers[et].append(handler)
        else:
            # Wildcard - listens to all
            self._all_handlers.append(handler)
        
        return handler_id
    
    def unsubscribe(self, handler_id: str) -> bool:
        """Unsubscribe a handler by ID."""
        removed = False
        
        # Check typed handlers
        for handlers in self._handlers.values():
            for i, h in enumerate(handlers):
                if h.id == handler_id:
                    handlers.pop(i)
                    removed = True
                    break
        
        # Check wildcard handlers
        for i, h in enumerate(self._all_handlers):
            if h.id == handler_id:
                self._all_handlers.pop(i)
                removed = True
                break
        
        return removed
    
    def publish(
        self,
        event: CognitiveEvent,
    ) -> None:
        """
        Publish an event to the bus.
        
        Events are queued and processed asynchronously.
        """
        # Priority queue uses (priority_value, timestamp) for ordering
        # Lower priority value = higher priority
        priority_value = {
            EventPriority.CRITICAL: 0,
            EventPriority.HIGH: 1,
            EventPriority.NORMAL: 2,
            EventPriority.LOW: 3,
        }[event.priority]
        
        try:
            self._queue.put_nowait((priority_value, event.timestamp, event))
            self._metrics['published'] += 1
        except asyncio.QueueFull:
            self._metrics['dropped'] += 1
            print(f"⚠️ Event bus queue full, dropped {event.type}")
    
    def publish_simple(
        self,
        event_type: str,
        source: str,
        data: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """Convenience method to publish with simple args."""
        self.publish(CognitiveEvent(
            type=event_type,
            source=source,
            data=data or {},
            priority=priority,
        ))
    
    async def _process_loop(self) -> None:
        """Main event processing loop."""
        while self._running:
            try:
                # Wait for events with timeout to check _running periodically
                try:
                    _, _, event = await asyncio.wait_for(
                        self._queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Deliver to handlers
                await self._deliver(event)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Event bus error: {e}")
    
    async def _deliver(self, event: CognitiveEvent) -> None:
        """Deliver event to all matching handlers."""
        handlers: List[EventHandler] = []
        
        # Get typed handlers
        if event.type in self._handlers:
            handlers.extend(self._handlers[event.type])
        
        # Add wildcard handlers
        handlers.extend(self._all_handlers)
        
        # Filter and execute
        for handler in handlers:
            if handler.should_handle(event):
                try:
                    result = handler.callback(event)
                    # Handle async callbacks
                    if asyncio.iscoroutine(result):
                        asyncio.create_task(result)
                    self._metrics['delivered'] += 1
                except Exception as e:
                    print(f"⚠️ Handler {handler.id} failed: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics."""
        return {
            **self._metrics,
            'handlers_registered': len(self._all_handlers) + sum(
                len(h) for h in self._handlers.values()
            ),
            'queue_size': self._queue.qsize(),
            'running': self._running,
        }
    
    def get_subscribers(self, event_type: Optional[str] = None) -> List[str]:
        """Get list of subscriber IDs."""
        if event_type:
            return [h.id for h in self._handlers.get(event_type, [])]
        return [h.id for h in self._all_handlers]


# Singleton instance
_event_bus: Optional[CognitiveEventBus] = None


def get_event_bus() -> CognitiveEventBus:
    """Get or create the global event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = CognitiveEventBus()
    return _event_bus


class EventBusMixin:
    """
    Mixin for classes that want to easily integrate with the event bus.
    
    Usage:
        class MyEngine(EventBusMixin):
            def __init__(self):
                super().__init__("my_engine")
                self.subscribe("goal.completed", self.on_goal_done)
            
            def on_goal_done(self, event):
                print(f"Goal completed: {event.data['goal_id']}")
    """
    
    def __init__(self, system_name: str):
        self.system_name = system_name
        self._bus = get_event_bus()
        self._handler_ids: List[str] = []
    
    def subscribe(
        self,
        event_type: Optional[str] = None,
        callback: Callable[[CognitiveEvent], Any] = None,
        **kwargs
    ) -> str:
        """Subscribe to events."""
        handler_id = self._bus.subscribe(
            event_type=event_type,
            callback=callback,
            **kwargs
        )
        self._handler_ids.append(handler_id)
        return handler_id
    
    def publish(
        self,
        event_type: str,
        data: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """Publish an event to the bus."""
        self._bus.publish_simple(
            event_type=event_type,
            source=self.system_name,
            data=data,
            priority=priority,
        )
    
    def unsubscribe_all(self) -> None:
        """Unsubscribe all handlers for this system."""
        for handler_id in self._handler_ids:
            self._bus.unsubscribe(handler_id)
        self._handler_ids.clear()
