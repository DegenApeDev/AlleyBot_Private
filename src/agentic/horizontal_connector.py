"""
HorizontalEngineConnector - Wires all horizontal engines to the event bus.

This module connects the specialized engines (social, content, trading, research, coding)
to the cognitive event bus, enabling bidirectional communication with the core AGI systems.
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from .event_bus import (
    CognitiveEventBus,
    EventBusMixin,
    EventType,
    EventPriority,
    get_event_bus,
    CognitiveEvent,
)


@dataclass
class EngineSubscriptions:
    """Configuration for which events each engine subscribes to."""
    
    # Social Engine subscriptions
    SOCIAL_EVENTS = [
        EventType.GOAL_COMPLETED,
        EventType.ACTION_EXECUTED,
        EventType.CONTENT_PERFORMANCE,
        EventType.SOCIAL_MENTION,
        EventType.SOCIAL_REPLY,
        EventType.OPPORTUNITY_DETECTED,
    ]
    
    # Content Engine subscriptions
    CONTENT_EVENTS = [
        EventType.GOAL_COMPLETED,
        EventType.INSIGHT_GENERATED,
        EventType.OBSERVATION,
        EventType.PATTERN_DETECTED,
        EventType.TRENDING_TOPIC,
        EventType.MARKET_SIGNAL,
    ]
    
    # Trading Engine subscriptions
    TRADING_EVENTS = [
        EventType.MARKET_SIGNAL,
        EventType.OPPORTUNITY_DETECTED,
        EventType.ANOMALY_DETECTED,
        EventType.SYSTEM_HEALTH,
    ]
    
    # Research Engine subscriptions
    RESEARCH_EVENTS = [
        EventType.GOAL_CREATED,
        EventType.OBSERVATION,
        EventType.INSIGHT_GENERATED,
        EventType.PATTERN_DETECTED,
        EventType.LEARNING_COMPLETED,
    ]
    
    # Coding/Development Engine subscriptions
    CODING_EVENTS = [
        EventType.ACTION_FAILED,
        EventType.SYSTEM_ERROR,
        EventType.GOAL_COMPLETED,
        EventType.MEMORY_STORED,
    ]


class HorizontalEngineConnector(EventBusMixin):
    """
    Connects all horizontal engines to the event bus.
    
    This is the integration point that enables:
    - Core → Engines: Broadcasting decisions, actions, observations
    - Engines → Core: Injecting new goals, insights, opportunities
    """
    
    def __init__(self, agi_kernel=None):
        super().__init__("horizontal_connector")
        self.agi_kernel = agi_kernel
        self._engines: Dict[str, Any] = {}
        self._subscriptions: Dict[str, str] = {}
        
    def register_engine(self, name: str, engine: Any) -> None:
        """Register a horizontal engine."""
        self._engines[name] = engine
        
        # Subscribe engine to relevant events
        events = getattr(EngineSubscriptions, f"{name.upper()}_EVENTS", [])
        
        for event_type in events:
            handler_id = self.subscribe(
                event_type=event_type,
                callback=self._create_engine_handler(name, engine),
            )
            self._subscriptions[f"{name}:{event_type}"] = handler_id
        
        print(f"🔗 {name} engine connected to event bus ({len(events)} event types)")
    
    def _create_engine_handler(self, engine_name: str, engine: Any) -> Callable:
        """Create an event handler for a specific engine."""
        def handler(event: CognitiveEvent) -> None:
            # Route event to engine's on_event method if available
            if hasattr(engine, 'on_event'):
                engine.on_event(event)
            
            # Also try specific method name like on_goal_completed
            method_name = f"on_{event.type.replace('.', '_')}"
            if hasattr(engine, method_name):
                getattr(engine, method_name)(event)
        
        return handler
    
    def inject_goal_from_engine(self, engine_name: str, goal_data: Dict[str, Any]) -> bool:
        """
        Allow horizontal engines to inject goals into the core system.
        
        This is the key bidirectional path:
        Engine detects opportunity → Injects goal → Core executes
        """
        if not self.agi_kernel or not hasattr(self.agi_kernel, 'goal_manager'):
            return False
        
        try:
            goal_manager = self.agi_kernel.goal_manager
            
            # Create goal from engine data
            goal_data['origin'] = f"engine:{engine_name}"
            goal_data['status'] = 'proposed'
            
            # Inject into goal manager
            if hasattr(goal_manager, 'add_goal'):
                goal_manager.add_goal(**goal_data)
            elif hasattr(goal_manager, 'create_goal'):
                goal_manager.create_goal(**goal_data)
            
            # Publish goal created event
            self.publish(
                EventType.GOAL_CREATED,
                {"goal": goal_data, "source_engine": engine_name},
                priority=EventPriority.HIGH,
            )
            
            print(f"🎯 Goal injected by {engine_name}: {goal_data.get('description', 'unknown')[:60]}")
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to inject goal from {engine_name}: {e}")
            return False
    
    def publish_observation(self, source: str, observation_type: str, 
                           data: Dict[str, Any], priority: EventPriority = EventPriority.NORMAL) -> None:
        """Convenience method for engines to publish observations."""
        self.publish(
            EventType.OBSERVATION,
            {
                "observation_type": observation_type,
                "source": source,
                "data": data,
            },
            priority=priority,
        )
    
    def get_connected_engines(self) -> Dict[str, Any]:
        """Get all registered engines."""
        return self._engines.copy()
    
    def disconnect_all(self) -> None:
        """Disconnect all engines from the event bus."""
        self.unsubscribe_all()
        self._engines.clear()
        self._subscriptions.clear()
        print("🔌 All horizontal engines disconnected")


def create_horizontal_connector(agi_kernel=None) -> HorizontalEngineConnector:
    """Factory function to create and configure the connector."""
    return HorizontalEngineConnector(agi_kernel)


# Example integration for existing engines
class SocialEngineAdapter(EventBusMixin):
    """
    Adapter to connect existing social engine to event bus.
    
    Example of how to integrate existing engines without rewriting them.
    """
    
    def __init__(self, social_engine: Any):
        super().__init__("social_engine")
        self.engine = social_engine
        
        # Subscribe to relevant events
        self.subscribe(EventType.GOAL_COMPLETED, self.on_goal_completed)
        self.subscribe(EventType.CONTENT_PERFORMANCE, self.on_content_performance)
        self.subscribe(EventType.OPPORTUNITY_DETECTED, self.on_opportunity)
    
    def on_goal_completed(self, event: CognitiveEvent) -> None:
        """When a goal completes, maybe share success on social media."""
        goal_data = event.data.get('goal', {})
        
        # Check if goal is shareable
        if goal_data.get('is_shareable') or goal_data.get('origin') == 'user_command':
            if hasattr(self.engine, 'share_achievement'):
                self.engine.share_achievement(goal_data)
    
    def on_content_performance(self, event: CognitiveEvent) -> None:
        """React to content performance metrics."""
        performance = event.data
        
        # If content underperforms, create optimization goal
        if performance.get('engagement_rate', 1.0) < 0.05:
            # This would inject a goal back to core
            pass
    
    def on_opportunity(self, event: CognitiveEvent) -> None:
        """React to detected opportunities."""
        opportunity = event.data
        
        # Social engine might want to engage with trending topics
        if opportunity.get('type') == 'trending_topic':
            if hasattr(self.engine, 'engage_with_topic'):
                self.engine.engage_with_topic(opportunity)


class ContentEngineAdapter(EventBusMixin):
    """Adapter for content intelligence engine."""
    
    def __init__(self, content_engine: Any):
        super().__init__("content_engine")
        self.engine = content_engine
        
        self.subscribe(EventType.OBSERVATION, self.on_observation)
        self.subscribe(EventType.INSIGHT_GENERATED, self.on_insight)
    
    def on_observation(self, event: CognitiveEvent) -> None:
        """Process observations for content opportunities."""
        obs_type = event.data.get('observation_type')
        
        if obs_type == 'trending_topic':
            # Generate content goal
            pass
        elif obs_type == 'market_event':
            # Maybe create analysis content
            pass
    
    def on_insight(self, event: CognitiveEvent) -> None:
        """Convert insights into content."""
        insight = event.data
        
        # High-value insights become content
        if insight.get('value_score', 0) > 0.8:
            if hasattr(self.engine, 'create_content_from_insight'):
                self.engine.create_content_from_insight(insight)
