"""
Event Bus Integration - Wires existing engines to the CognitiveEventBus.

This module integrates existing horizontal engines (social_intelligence, 
research_engine, creative_engine, etc.) with the event bus without
rewriting them. Uses adapter pattern for clean integration.
"""

from typing import Dict, Any
from dataclasses import dataclass

from .event_bus import (
    EventBusMixin,
    EventType,
    EventPriority,
    CognitiveEvent,
)


class EngineEventAdapter(EventBusMixin):
    """
    Base adapter for connecting existing engines to the event bus.
    
    Usage:
        adapter = EngineEventAdapter(existing_engine, "social_intelligence")
        adapter.subscribe_to_core_events()
        
        # Now engine receives events from core and can publish back
    """
    
    def __init__(self, engine: Any, engine_name: str, agi_kernel=None):
        super().__init__(engine_name)
        self.engine = engine
        self.engine_name = engine_name
        self.agi_kernel = agi_kernel
        
    def subscribe_to_core_events(self) -> None:
        """Subscribe this engine to relevant core events."""
        # All engines get these base events
        self.subscribe(EventType.DECISION_MADE, self.on_decision)
        self.subscribe(EventType.ACTION_EXECUTED, self.on_action_executed)
        self.subscribe(EventType.ACTION_FAILED, self.on_action_failed)
        self.subscribe(EventType.GOAL_COMPLETED, self.on_goal_completed)
        
    def on_decision(self, event: CognitiveEvent) -> None:
        """Handle decision events from core."""
        # Route to engine's handle_decision method if it exists
        if hasattr(self.engine, 'handle_decision'):
            self.engine.handle_decision(event.data.get('action'))
    
    def on_action_executed(self, event: CognitiveEvent) -> None:
        """Handle successful action execution."""
        if hasattr(self.engine, 'on_action_success'):
            self.engine.on_action_success(
                event.data.get('action_spec'),
                event.data.get('result')
            )
    
    def on_action_failed(self, event: CognitiveEvent) -> None:
        """Handle failed action execution."""
        if hasattr(self.engine, 'on_action_failure'):
            self.engine.on_action_failure(
                event.data.get('action_spec'),
                event.data.get('result')
            )
    
    def on_goal_completed(self, event: CognitiveEvent) -> None:
        """Handle goal completion - engines may want to react."""
        if hasattr(self.engine, 'on_goal_completed'):
            self.engine.on_goal_completed(event.data.get('goal'))
    
    def inject_goal_to_core(self, goal_data: Dict[str, Any]) -> bool:
        """
        Inject a goal from this engine back to the core AGI system.
        
        This is the bidirectional path:
        Engine detects opportunity → Creates goal → Core executes it
        """
        if not self.agi_kernel:
            return False
            
        try:
            # Try to inject through goal_manager
            goal_manager = getattr(self.agi_kernel, 'goal_manager', None)
            if goal_manager and hasattr(goal_manager, 'create_goal'):
                goal_data['origin'] = f"engine:{self.engine_name}"
                goal_manager.create_goal(**goal_data)
                
                # Publish event
                self.publish(
                    EventType.GOAL_CREATED,
                    {"goal": goal_data, "source": self.engine_name},
                    priority=EventPriority.HIGH,
                )
                return True
                
        except Exception as e:
            print(f"⚠️ {self.engine_name} failed to inject goal: {e}")
            
        return False


class SocialIntelligenceAdapter(EngineEventAdapter):
    """Adapter for SocialIntelligence engine."""
    
    def __init__(self, social_engine: Any, agi_kernel=None):
        super().__init__(social_engine, "social_intelligence", agi_kernel)
        
    def subscribe_to_core_events(self) -> None:
        super().subscribe_to_core_events()
        # Social engine also cares about these
        self.subscribe(EventType.SOCIAL_MENTION, self.on_social_mention)
        self.subscribe(EventType.SOCIAL_REPLY, self.on_social_reply)
        self.subscribe(EventType.OPPORTUNITY_DETECTED, self.on_opportunity)
        
    def on_social_mention(self, event: CognitiveEvent) -> None:
        """React to social mentions."""
        if hasattr(self.engine, 'record_interaction'):
            self.engine.record_interaction(
                entity_id=event.data.get('user_id'),
                interaction_type='mention',
                content=event.data.get('content'),
                platform=event.data.get('platform'),
            )
    
    def on_social_reply(self, event: CognitiveEvent) -> None:
        """React to replies."""
        if hasattr(self.engine, 'record_interaction'):
            self.engine.record_interaction(
                entity_id=event.data.get('user_id'),
                interaction_type='reply',
                content=event.data.get('content'),
                platform=event.data.get('platform'),
            )
    
    def on_opportunity(self, event: CognitiveEvent) -> None:
        """When opportunity detected, social engine may want to engage."""
        opp_type = event.data.get('opportunity_type')
        
        if opp_type == 'trending_topic':
            # Create social engagement goal
            self.inject_goal_to_core({
                'description': f"Engage with trending topic: {event.data.get('topic')}",
                'priority_score': 7.0,
                'action_plan': ['monitor_topic', 'craft_response', 'post_engagement'],
            })


class ResearchEngineAdapter(EngineEventAdapter):
    """Adapter for ResearchEngine."""
    
    def __init__(self, research_engine: Any, agi_kernel=None):
        super().__init__(research_engine, "research_engine", agi_kernel)
        
    def subscribe_to_core_events(self) -> None:
        super().subscribe_to_core_events()
        self.subscribe(EventType.OBSERVATION, self.on_observation)
        self.subscribe(EventType.PATTERN_DETECTED, self.on_pattern)
        
    def on_observation(self, event: CognitiveEvent) -> None:
        """Research engine processes observations for insights."""
        obs_type = event.data.get('observation_type')
        
        if obs_type == 'knowledge_gap':
            # Create research goal
            self.inject_goal_to_core({
                'description': f"Research: {event.data.get('topic')}",
                'priority_score': 6.0,
                'action_plan': ['gather_sources', 'synthesize', 'store_findings'],
            })
            
    def on_pattern(self, event: CognitiveEvent) -> None:
        """When pattern detected, research engine may want to investigate."""
        if hasattr(self.engine, 'analyze_pattern'):
            self.engine.analyze_pattern(event.data)


class ContentIntelligenceAdapter(EngineEventAdapter):
    """Adapter for ContentIntelligence engine."""
    
    def __init__(self, content_engine: Any, agi_kernel=None):
        super().__init__(content_engine, "content_intelligence", agi_kernel)
        
    def subscribe_to_core_events(self) -> None:
        super().subscribe_to_core_events()
        self.subscribe(EventType.INSIGHT_GENERATED, self.on_insight)
        self.subscribe(EventType.CONTENT_PERFORMANCE, self.on_performance)
        
    def on_insight(self, event: CognitiveEvent) -> None:
        """Convert high-value insights into content."""
        insight = event.data
        
        # Check if insight is content-worthy
        if insight.get('value_score', 0) > 0.7:
            self.inject_goal_to_core({
                'description': f"Create content from insight: {insight.get('title', 'untitled')}",
                'priority_score': 7.0,
                'action_plan': ['draft_content', 'optimize', 'schedule_post'],
            })
    
    def on_performance(self, event: CognitiveEvent) -> None:
        """React to content performance metrics."""
        perf = event.data
        
        # Underperforming content → optimization goal
        if perf.get('engagement_rate', 1.0) < 0.03:
            self.inject_goal_to_core({
                'description': f"Optimize underperforming content: {perf.get('content_id')}",
                'priority_score': 5.0,
                'action_plan': ['analyze_metrics', 'identify_issues', 'revise_content'],
            })


class TradingEngineAdapter(EngineEventAdapter):
    """Adapter for autonomous_trading engine."""
    
    def __init__(self, trading_engine: Any, agi_kernel=None):
        super().__init__(trading_engine, "trading_engine", agi_kernel)
        
    def subscribe_to_core_events(self) -> None:
        super().subscribe_to_core_events()
        self.subscribe(EventType.MARKET_SIGNAL, self.on_market_signal)
        self.subscribe(EventType.ANOMALY_DETECTED, self.on_anomaly)
        
    def on_market_signal(self, event: CognitiveEvent) -> None:
        """React to market signals."""
        signal = event.data
        
        if signal.get('urgency') == 'high':
            self.inject_goal_to_core({
                'description': f"Act on market signal: {signal.get('symbol')} {signal.get('signal_type')}",
                'priority_score': 9.0,  # High priority
                'urgency': 9.0,
                'action_plan': ['validate_signal', 'check_positions', 'execute_if_valid'],
            })


class CreativeEngineAdapter(EngineEventAdapter):
    """Adapter for CreativeEngine."""
    
    def __init__(self, creative_engine: Any, agi_kernel=None):
        super().__init__(creative_engine, "creative_engine", agi_kernel)
        
    def subscribe_to_core_events(self) -> None:
        super().subscribe_to_core_events()
        self.subscribe(EventType.LEARNING_COMPLETED, self.on_learning)
        
    def on_learning(self, event: CognitiveEvent) -> None:
        """Creative engine may want to express learnings creatively."""
        learning = event.data
        
        if learning.get('significance') == 'major':
            self.inject_goal_to_core({
                'description': "Create creative expression of recent learning",
                'priority_score': 4.0,
                'action_plan': ['conceptualize', 'create_draft', 'refine'],
            })


@dataclass
class EngineIntegrationManager:
    """
    Manages all engine adapters and their lifecycle.
    
    Usage:
        manager = EngineIntegrationManager(agi_kernel)
        manager.register_all_engines()
        
        # All engines now connected to event bus
    """
    
    agi_kernel: Any
    adapters: Dict[str, EngineEventAdapter] = None
    
    def __post_init__(self):
        if self.adapters is None:
            self.adapters = {}
    
    def register_all_engines(self) -> None:
        """Find and register all available engines."""
        # Social Intelligence
        if hasattr(self.agi_kernel, 'social_intelligence') and self.agi_kernel.social_intelligence:
            adapter = SocialIntelligenceAdapter(
                self.agi_kernel.social_intelligence,
                self.agi_kernel
            )
            adapter.subscribe_to_core_events()
            self.adapters['social'] = adapter
            print("🔗 SocialIntelligence connected to event bus")
        
        # Research Engine
        if hasattr(self.agi_kernel, 'research_engine') and self.agi_kernel.research_engine:
            adapter = ResearchEngineAdapter(
                self.agi_kernel.research_engine,
                self.agi_kernel
            )
            adapter.subscribe_to_core_events()
            self.adapters['research'] = adapter
            print("🔗 ResearchEngine connected to event bus")
        
        # Content Intelligence
        if hasattr(self.agi_kernel, 'content_intelligence') and self.agi_kernel.content_intelligence:
            adapter = ContentIntelligenceAdapter(
                self.agi_kernel.content_intelligence,
                self.agi_kernel
            )
            adapter.subscribe_to_core_events()
            self.adapters['content'] = adapter
            print("🔗 ContentIntelligence connected to event bus")
        
        # Trading
        if hasattr(self.agi_kernel, 'trading_engine') and self.agi_kernel.trading_engine:
            adapter = TradingEngineAdapter(
                self.agi_kernel.trading_engine,
                self.agi_kernel
            )
            adapter.subscribe_to_core_events()
            self.adapters['trading'] = adapter
            print("🔗 TradingEngine connected to event bus")
        
        # Creative
        if hasattr(self.agi_kernel, 'creative_engine') and self.agi_kernel.creative_engine:
            adapter = CreativeEngineAdapter(
                self.agi_kernel.creative_engine,
                self.agi_kernel
            )
            adapter.subscribe_to_core_events()
            self.adapters['creative'] = adapter
            print("🔗 CreativeEngine connected to event bus")
        
        print(f"✅ {len(self.adapters)} horizontal engines connected")
    
    def disconnect_all(self) -> None:
        """Disconnect all engines."""
        for name, adapter in self.adapters.items():
            adapter.unsubscribe_all()
            print(f"🔌 {name} engine disconnected")
        self.adapters.clear()


def integrate_all_engines(agi_kernel) -> EngineIntegrationManager:
    """Convenience function to wire up all engines."""
    manager = EngineIntegrationManager(agi_kernel)
    manager.register_all_engines()
    return manager
