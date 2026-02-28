"""
World State Bridge for AGI Kernel

Lightweight integration layer that connects AGI Kernel to the existing
WorldStateManager in src/autonomy/world_state.py.

This bridge:
- Provides AGI Kernel access to world state data
- Connects world state to goal generation
- Enables content strategy to use world context
- Tracks cross-platform entity relationships
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add src/autonomy to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'autonomy'))

from world_state import WorldStateManager, Entity, Fact, Relationship, Event


class WorldStateBridge:
    """
    Bridge between AGI Kernel and World State Manager.
    
    Provides high-level interface for:
    - Querying world context for decisions
    - Recording platform interactions
    - Analyzing trends across platforms
    - Tracking entity relationships
    """
    
    def __init__(self, agi_kernel, db_path: str = None):
        self.agi = agi_kernel
        self.core = agi_kernel.core if hasattr(agi_kernel, 'core') else None
        
        # Initialize world state manager
        if db_path is None:
            data_dir = getattr(self.core, 'data_dir', 'data') if self.core else 'data'
            db_path = f"{data_dir}/world_state.db"
        
        self.world_state = WorldStateManager(db_path=db_path)
        
        # Initialize platform entities if needed
        stats = self.world_state.get_stats()
        if stats['entities'] == 0:
            self._seed_platforms()
        
        print(f"🌍 WorldStateBridge initialized ({stats['entities']} entities, {stats['facts']} facts)")
    
    def _seed_platforms(self):
        """Seed initial platform entities"""
        platforms = [
            Entity(id="platform_moltx", type="platform", name="Moltx", display_name="Moltx"),
            Entity(id="platform_clawbr", type="platform", name="Clawbr", display_name="Clawbr"),
            Entity(id="platform_telegram", type="platform", name="Telegram", display_name="Telegram"),
            Entity(id="platform_moltbook", type="platform", name="Moltbook", display_name="Moltbook"),
            Entity(id="platform_moltroad", type="platform", name="Moltroad", display_name="Moltroad"),
            Entity(id="platform_clawchess", type="platform", name="ClawChess", display_name="ClawChess"),
        ]
        
        for platform in platforms:
            self.world_state.add_entity(platform)
        
        print(f"🌱 Seeded {len(platforms)} platform entities")
    
    # =========================================================================
    # Context Queries for Decision Making
    # =========================================================================
    
    def get_world_context_for_decision(self, scope: str = 'recent') -> Dict[str, Any]:
        """
        Get world context for AGI decision making.
        
        Args:
            scope: 'recent' (24h), 'week', 'all'
            
        Returns:
            Rich context including entities, trends, relationships
        """
        if scope == 'recent':
            hours = 24
        elif scope == 'week':
            hours = 168
        else:
            hours = None
        
        context = {
            'stats': self.world_state.get_stats(),
            'entity_breakdown': self.world_state.get_entity_type_breakdown(),
            'recent_events': [],
            'trending_topics': [],
            'active_entities': [],
        }
        
        # Get recent events
        if hours:
            since = (datetime.now() - timedelta(hours=hours)).isoformat()
            events = self.world_state.get_events(since=since, limit=100)
            context['recent_events'] = [
                {
                    'type': e.event_type,
                    'platform': e.platform,
                    'actor': e.actor_id,
                    'timestamp': e.timestamp,
                }
                for e in events[:20]  # Limit for context size
            ]
        
        # Get trending topics
        context['trending_topics'] = self.get_trending_topics(hours=hours or 24)
        
        # Get most active entities
        context['active_entities'] = self._get_active_entities(hours=hours or 24)
        
        return context
    
    def get_entity_context(self, entity_id: str) -> Dict[str, Any]:
        """
        Get detailed context about a specific entity.
        
        Used for personalized interactions and relationship building.
        """
        data = self.world_state.get_entity_with_facts(entity_id)
        if not data:
            return {}
        
        entity = data['entity']
        facts = data['facts']
        
        # Get latest value for each attribute
        latest_facts = {}
        for fact in facts:
            if fact.attribute not in latest_facts:
                latest_facts[fact.attribute] = {
                    'value': fact.get_typed_value(),
                    'timestamp': fact.timestamp,
                    'confidence': fact.confidence,
                }
        
        # Get relationships
        relationships = self.world_state.get_relationships(entity_id)
        rel_summary = {}
        for rel in relationships:
            rel_type = rel.relation_type
            if rel_type not in rel_summary:
                rel_summary[rel_type] = []
            
            other_id = rel.to_entity if rel.from_entity == entity_id else rel.from_entity
            rel_summary[rel_type].append({
                'entity_id': other_id,
                'strength': rel.strength,
            })
        
        return {
            'entity': {
                'id': entity.id,
                'type': entity.type,
                'name': entity.name,
                'display_name': entity.display_name,
                'platform': entity.platform,
            },
            'facts': latest_facts,
            'relationships': rel_summary,
        }
    
    # =========================================================================
    # Trend Analysis
    # =========================================================================
    
    def get_trending_topics(self, hours: int = 24) -> List[Dict]:
        """
        Analyze recent events to find trending topics.
        
        Returns topics with frequency counts and platforms.
        """
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        events = self.world_state.get_events(since=since)
        
        # Extract topics from event data
        topic_data = {}
        for event in events:
            if event.data:
                # Extract hashtags
                if 'hashtags' in event.data:
                    for tag in event.data['hashtags']:
                        if tag not in topic_data:
                            topic_data[tag] = {'count': 0, 'platforms': set()}
                        topic_data[tag]['count'] += 1
                        if event.platform:
                            topic_data[tag]['platforms'].add(event.platform)
                
                # Extract topics
                if 'topic' in event.data:
                    topic = event.data['topic']
                    if topic not in topic_data:
                        topic_data[topic] = {'count': 0, 'platforms': set()}
                    topic_data[topic]['count'] += 1
                    if event.platform:
                        topic_data[topic]['platforms'].add(event.platform)
        
        # Sort by frequency
        sorted_topics = sorted(topic_data.items(), key=lambda x: x[1]['count'], reverse=True)
        
        return [
            {
                'topic': topic,
                'count': data['count'],
                'platforms': list(data['platforms']),
                'trending': data['count'] > 3,
                'cross_platform': len(data['platforms']) > 1,
            }
            for topic, data in sorted_topics[:15]
        ]
    
    def get_platform_activity_summary(self, platform: str, hours: int = 24) -> Dict[str, Any]:
        """Get activity summary for a specific platform"""
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        events = self.world_state.get_events(since=since)
        
        platform_events = [e for e in events if e.platform == platform]
        
        # Count by event type
        event_counts = {}
        for e in platform_events:
            event_counts[e.event_type] = event_counts.get(e.event_type, 0) + 1
        
        # Get unique actors
        actors = set(e.actor_id for e in platform_events if e.actor_id)
        
        return {
            'platform': platform,
            'period_hours': hours,
            'total_events': len(platform_events),
            'event_breakdown': event_counts,
            'unique_actors': len(actors),
            'most_common_event': max(event_counts.items(), key=lambda x: x[1])[0] if event_counts else None,
        }
    
    def _get_active_entities(self, hours: int = 24) -> List[Dict]:
        """Get most active entities in time period"""
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        events = self.world_state.get_events(since=since)
        
        # Count activity per entity
        entity_activity = {}
        for event in events:
            if event.actor_id:
                entity_activity[event.actor_id] = entity_activity.get(event.actor_id, 0) + 1
        
        # Sort by activity
        sorted_entities = sorted(entity_activity.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'entity_id': entity_id, 'activity_count': count}
            for entity_id, count in sorted_entities[:10]
        ]
    
    # =========================================================================
    # Recording Platform Interactions
    # =========================================================================
    
    def record_interaction(self, platform: str, interaction_type: str, 
                          actor_id: str = None, target_id: str = None,
                          data: Dict = None):
        """
        Record a platform interaction into world state.
        
        Examples:
        - Post created
        - Reply received
        - Mention detected
        - Engagement recorded
        """
        event = Event(
            event_type=interaction_type,
            platform=platform,
            timestamp=datetime.now().isoformat(),
            actor_id=actor_id,
            target_id=target_id,
            data=data or {}
        )
        
        self.world_state.add_event(event)
        
        # Ensure actor entity exists
        if actor_id:
            actor = self.world_state.get_entity(actor_id)
            if not actor and data:
                actor = Entity(
                    id=actor_id,
                    type=data.get('actor_type', 'agent'),
                    name=data.get('actor_name'),
                    display_name=data.get('actor_display_name'),
                    platform=platform,
                )
                self.world_state.add_entity(actor)
    
    def record_relationship(self, from_entity: str, to_entity: str, 
                           relation_type: str, strength: float = 0.5):
        """Record a relationship between entities"""
        relationship = Relationship(
            from_entity=from_entity,
            to_entity=to_entity,
            relation_type=relation_type,
            strength=strength,
        )
        
        self.world_state.add_relationship(relationship)
    
    def record_fact(self, entity_id: str, attribute: str, value: Any,
                   source: str = None, confidence: float = 1.0):
        """Record a fact about an entity"""
        # Determine value type
        value_type = 'string'
        if isinstance(value, int):
            value_type = 'int'
        elif isinstance(value, float):
            value_type = 'float'
        elif isinstance(value, bool):
            value_type = 'bool'
        elif isinstance(value, dict):
            value_type = 'json'
            import json
            value = json.dumps(value)
        
        fact = Fact(
            entity_id=entity_id,
            attribute=attribute,
            value=str(value),
            value_type=value_type,
            timestamp=datetime.now().isoformat(),
            source=source,
            confidence=confidence,
        )
        
        self.world_state.add_fact(fact)
    
    # =========================================================================
    # Integration with Goal Generator
    # =========================================================================
    
    def get_world_state_for_goals(self) -> Dict[str, Any]:
        """
        Get world state summary for goal generation.
        
        Provides context about:
        - Platform activity levels
        - Trending topics
        - Relationship opportunities
        - Resource availability
        """
        context = self.get_world_context_for_decision(scope='recent')
        
        # Add platform-specific summaries
        platform_summaries = {}
        for platform in ['moltx', 'clawbr', 'telegram']:
            platform_summaries[platform] = self.get_platform_activity_summary(platform, hours=24)
        
        context['platform_summaries'] = platform_summaries
        
        return context
    
    # =========================================================================
    # Statistics and Monitoring
    # =========================================================================
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of world state status"""
        stats = self.world_state.get_stats()
        breakdown = self.world_state.get_entity_type_breakdown()
        
        return {
            'total_entities': stats['entities'],
            'total_facts': stats['facts'],
            'total_relationships': stats['relationships'],
            'total_events': stats['events'],
            'unprocessed_events': stats['unprocessed_events'],
            'entity_breakdown': breakdown,
        }
    
    def cleanup_expired_data(self, days: int = 30) -> int:
        """Cleanup old data from world state"""
        return self.world_state.cleanup_expired_facts(days=days)


def create_world_state_bridge(agi_kernel) -> WorldStateBridge:
    """Factory function to create world state bridge"""
    return WorldStateBridge(agi_kernel)
