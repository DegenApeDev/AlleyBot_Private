"""
World State Mixin - Integrates World State with Brain decision engine

Provides persistent environment memory for AGI decision-making.
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Add src/autonomy to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'autonomy'))

from world_state import WorldStateManager, Entity, Fact, Relationship, Event, create_world_state_manager


class WorldStateMixin:
    """
    Mixin that adds World State capabilities to Brain plugin.
    
    Enables the Brain to maintain persistent memory of:
    - Entities in the environment (users, agents, posts, topics)
    - Facts about entities over time
    - Relationships between entities
    - Events that have occurred
    """
    
    def _init_world_state(self):
        """Initialize World State Manager"""
        try:
            if hasattr(self, 'core') and self.core:
                data_dir = getattr(self.core, 'data_dir', 'data')
            else:
                data_dir = 'data'
            
            self.world_state = WorldStateManager(db_path=f"{data_dir}/world_state.db")
            
            # Initialize default platform entities if none exist
            stats = self.world_state.get_stats()
            if stats['entities'] == 0:
                self._seed_default_entities()
            
            print("🌍 World State integrated with Brain")
        except Exception as e:
            print(f"⚠️ World State init failed: {e}")
            self.world_state = None
    
    def _seed_default_entities(self):
        """Seed initial platform entities"""
        platforms = [
            Entity(id="platform_moltx", type="platform", name="Moltx", display_name="Moltx"),
            Entity(id="platform_clawbr", type="platform", name="Clawbr", display_name="Clawbr"),
            Entity(id="platform_telegram", type="platform", name="Telegram", display_name="Telegram"),
            Entity(id="platform_moltbook", type="platform", name="Moltbook", display_name="Moltbook"),
        ]
        
        for platform in platforms:
            self.world_state.add_entity(platform)
        
        print(f"🌱 Seeded {len(platforms)} platform entities")
    
    def record_platform_interaction(self, platform: str, interaction_type: str, data: Dict):
        """
        Record an interaction from a platform into World State
        
        Examples:
        - Post created
        - Reply received
        - Mention detected
        - Engagement recorded
        """
        if not self.world_state:
            return
        
        timestamp = datetime.now().isoformat()
        
        # Create event
        event = Event(
            event_type=interaction_type,
            platform=platform,
            timestamp=timestamp,
            data=data
        )
        
        # Add actor if present
        if 'actor_id' in data:
            event.actor_id = data['actor_id']
            
            # Ensure actor entity exists
            actor = self.world_state.get_entity(data['actor_id'])
            if not actor:
                actor = Entity(
                    id=data['actor_id'],
                    type=data.get('actor_type', 'agent'),
                    name=data.get('actor_name'),
                    display_name=data.get('actor_display_name')
                )
                self.world_state.add_entity(actor)
        
        # Add target if present
        if 'target_id' in data:
            event.target_id = data['target_id']
        
        self.world_state.add_event(event)
        
        # Record facts if present
        if 'facts' in data and event.actor_id:
            for attr, value in data['facts'].items():
                value_type = 'string'
                if isinstance(value, int):
                    value_type = 'int'
                elif isinstance(value, float):
                    value_type = 'float'
                elif isinstance(value, bool):
                    value_type = 'bool'
                elif isinstance(value, dict):
                    value_type = 'json'
                    value = json.dumps(value)
                
                fact = Fact(
                    entity_id=event.actor_id,
                    attribute=attr,
                    value=str(value),
                    value_type=value_type,
                    timestamp=timestamp,
                    source=f"{platform}_{interaction_type}",
                    confidence=data.get('confidence', 1.0)
                )
                self.world_state.add_fact(fact)
    
    def record_relationship(self, from_entity: str, to_entity: str, relation_type: str, 
                           strength: float = 0.5, context: Dict = None):
        """Record a relationship between two entities"""
        if not self.world_state:
            return
        
        relationship = Relationship(
            from_entity=from_entity,
            to_entity=to_entity,
            relation_type=relation_type,
            strength=strength,
            context=context
        )
        
        self.world_state.add_relationship(relationship)
    
    def get_world_context(self, entity_id: str = None, depth: int = 1) -> Dict[str, Any]:
        """
        Get rich context about an entity and its relationships
        
        Used by Brain to make informed decisions
        """
        if not self.world_state:
            return {}
        
        context = {
            'entity': None,
            'facts': {},
            'relationships': {},
            'recent_events': [],
            'related_entities': {}
        }
        
        # Get entity
        if entity_id:
            entity_data = self.world_state.get_entity_with_facts(entity_id)
            if entity_data:
                context['entity'] = entity_data['entity']
                
                # Get latest value for each attribute
                for fact in entity_data['facts']:
                    if fact.attribute not in context['facts']:
                        context['facts'][fact.attribute] = {
                            'value': fact.get_typed_value(),
                            'timestamp': fact.timestamp,
                            'confidence': fact.confidence
                        }
                
                # Get relationships
                relationships = self.world_state.get_relationships(entity_id)
                for rel in relationships:
                    rel_type = rel.relation_type
                    if rel_type not in context['relationships']:
                        context['relationships'][rel_type] = []
                    
                    other_id = rel.to_entity if rel.from_entity == entity_id else rel.from_entity
                    context['relationships'][rel_type].append({
                        'entity_id': other_id,
                        'strength': rel.strength,
                        'timestamp': rel.timestamp
                    })
                
                # Get related entity details
                for rel_type, rels in context['relationships'].items():
                    for rel in rels:
                        other_id = rel['entity_id']
                        if other_id not in context['related_entities']:
                            other = self.world_state.get_entity(other_id)
                            if other:
                                context['related_entities'][other_id] = other
        
        # Get recent events
        recent = self.world_state.get_events(since=(datetime.now() - timedelta(hours=24)).isoformat(), limit=50)
        context['recent_events'] = [
            {
                'type': e.event_type,
                'actor': e.actor_id,
                'target': e.target_id,
                'platform': e.platform,
                'timestamp': e.timestamp,
                'data': e.data
            }
            for e in recent
        ]
        
        return context
    
    def get_trending_topics(self, hours: int = 24) -> List[Dict]:
        """
        Analyze recent events to find trending topics
        
        Returns topics with frequency counts
        """
        if not self.world_state:
            return []
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        events = self.world_state.get_events(since=since)
        
        # Extract topics from event data
        topic_counts = {}
        for event in events:
            if event.data and 'topic' in event.data:
                topic = event.data['topic']
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            if event.data and 'hashtags' in event.data:
                for tag in event.data['hashtags']:
                    topic_counts[tag] = topic_counts.get(tag, 0) + 1
        
        # Sort by frequency
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'topic': topic, 'count': count, 'trending': count > 3}
            for topic, count in sorted_topics[:10]
        ]
    
    def get_entity_activity_summary(self, entity_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get activity summary for an entity over time period"""
        if not self.world_state:
            return {}
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        # Get events involving this entity
        all_events = self.world_state.get_events(since=since)
        
        entity_events = [
            e for e in all_events
            if e.actor_id == entity_id or e.target_id == entity_id
        ]
        
        # Count by type
        event_counts = {}
        for e in entity_events:
            event_counts[e.event_type] = event_counts.get(e.event_type, 0) + 1
        
        # Get recent facts
        facts = self.world_state.get_facts(entity_id, since=since)
        
        return {
            'entity_id': entity_id,
            'period_hours': hours,
            'total_events': len(entity_events),
            'event_breakdown': event_counts,
            'new_facts': len(facts),
            'most_recent_activity': entity_events[0].timestamp if entity_events else None
        }
    
    def world_status_command(self, *args) -> str:
        """CLI command: Show World State statistics"""
        if not self.world_state:
            return "❌ World State not available"
        
        stats = self.world_state.get_stats()
        breakdown = self.world_state.get_entity_type_breakdown()
        
        output = "🌍 World State Status\n\n"
        output += f"  📊 Entities: {stats['entities']}\n"
        output += f"  📝 Facts: {stats['facts']}\n"
        output += f"  🔗 Relationships: {stats['relationships']}\n"
        output += f"  📅 Events: {stats['events']} ({stats['unprocessed_events']} unprocessed)\n\n"
        
        if breakdown:
            output += "  Entity Types:\n"
            for etype, count in breakdown.items():
                output += f"    • {etype}: {count}\n"
        
        return output
    
    def world_entity_command(self, entity_id: str) -> str:
        """CLI command: Show entity details"""
        if not self.world_state:
            return "❌ World State not available"
        
        data = self.world_state.get_entity_with_facts(entity_id)
        if not data:
            return f"❌ Entity not found: {entity_id}"
        
        entity = data['entity']
        facts = data['facts']
        
        output = f"👤 Entity: {entity.id}\n"
        output += f"  Type: {entity.type}\n"
        output += f"  Name: {entity.name or 'N/A'}\n"
        output += f"  Display: {entity.display_name or 'N/A'}\n"
        output += f"  Confidence: {entity.confidence:.2f}\n"
        output += f"  Created: {entity.created_at[:16] if entity.created_at else 'N/A'}\n"
        output += f"  Updated: {entity.updated_at[:16] if entity.updated_at else 'N/A'}\n\n"
        
        if entity.attributes:
            output += "  Attributes:\n"
            for key, value in entity.attributes.items():
                output += f"    • {key}: {value}\n"
            output += "\n"
        
        # Show latest fact for each attribute
        latest_facts = {}
        for fact in facts:
            if fact.attribute not in latest_facts:
                latest_facts[fact.attribute] = fact
        
        if latest_facts:
            output += f"  Latest Facts ({len(latest_facts)} attributes):\n"
            for attr, fact in sorted(latest_facts.items()):
                value = fact.get_typed_value()
                if isinstance(value, str) and len(value) > 40:
                    value = value[:40] + "..."
                output += f"    • {attr}: {value} (conf: {fact.confidence:.2f})\n"
        
        return output
    
    def world_facts_command(self, entity_id: str, attribute: str = None) -> str:
        """CLI command: Show fact history"""
        if not self.world_state:
            return "❌ World State not available"
        
        facts = self.world_state.get_facts(entity_id, attribute=attribute, limit=20)
        
        if not facts:
            return f"📭 No facts found for {entity_id}"
        
        output = f"📝 Facts for {entity_id}\n\n"
        
        for fact in facts:
            value = fact.get_typed_value()
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            output += f"  • {fact.attribute} = {value}\n"
            output += f"    Time: {fact.timestamp[:16] if fact.timestamp else 'N/A'}"
            output += f" | Source: {fact.source or 'N/A'}"
            output += f" | Conf: {fact.confidence:.2f}\n\n"
        
        return output
    
    def world_relations_command(self, entity_id: str) -> str:
        """CLI command: Show entity relationships"""
        if not self.world_state:
            return "❌ World State not available"
        
        relationships = self.world_state.get_relationships(entity_id)
        
        if not relationships:
            return f"📭 No relationships found for {entity_id}"
        
        output = f"🔗 Relationships for {entity_id}\n\n"
        
        outgoing = [r for r in relationships if r.from_entity == entity_id]
        incoming = [r for r in relationships if r.to_entity == entity_id]
        
        if outgoing:
            output += "  Outgoing:\n"
            for rel in outgoing[:10]:
                output += f"    → {rel.to_entity}: {rel.relation_type} (strength: {rel.strength:.2f})\n"
            output += "\n"
        
        if incoming:
            output += "  Incoming:\n"
            for rel in incoming[:10]:
                output += f"    ← {rel.from_entity}: {rel.relation_type} (strength: {rel.strength:.2f})\n"
            output += "\n"
        
        return output
    
    def world_search_command(self, *args) -> str:
        """CLI command: Search entities"""
        if not self.world_state:
            return "❌ World State not available"
        
        query = args[0] if args else ""
        entity_type = args[1] if len(args) > 1 else None
        
        entities = self.world_state.search_entities(query=query or None, entity_type=entity_type, limit=15)
        
        if not entities:
            return f"🔍 No entities found for '{query}'"
        
        output = f"🔍 Search Results ({len(entities)} found):\n\n"
        
        for entity in entities:
            name = entity.display_name or entity.name or entity.id
            output += f"  • {entity.id} ({entity.type})\n"
            output += f"    Name: {name}\n"
            output += f"    Updated: {entity.updated_at[:16] if entity.updated_at else 'N/A'}\n\n"
        
        return output
    
    def world_events_command(self, *args) -> str:
        """CLI command: Show recent events"""
        if not self.world_state:
            return "❌ World State not available"
        
        event_type = args[0] if args else None
        
        events = self.world_state.get_events(event_type=event_type, limit=20)
        
        if not events:
            return "📭 No events found"
        
        output = f"📅 Recent Events ({len(events)}):\n\n"
        
        for event in events:
            output += f"  • {event.event_type}\n"
            output += f"    Platform: {event.platform or 'N/A'}\n"
            output += f"    Actor: {event.actor_id or 'N/A'}\n"
            output += f"    Target: {event.target_id or 'N/A'}\n"
            output += f"    Time: {event.timestamp[:16] if event.timestamp else 'N/A'}\n"
            output += f"    Processed: {'✅' if event.processed else '⏳'}\n\n"
        
        return output
    
    def world_trends_command(self, *args) -> str:
        """CLI command: Show trending topics"""
        if not self.world_state:
            return "❌ World State not available"
        
        hours = int(args[0]) if args and args[0].isdigit() else 24
        
        trends = self.get_trending_topics(hours=hours)
        
        if not trends:
            return "📭 No trending topics found"
        
        output = f"📈 Trending Topics (last {hours}h):\n\n"
        
        for trend in trends:
            emoji = "🔥" if trend['trending'] else "📊"
            output += f"  {emoji} {trend['topic']}: {trend['count']} mentions\n"
        
        return output
    
    def world_cleanup_command(self, *args) -> str:
        """CLI command: Cleanup expired data"""
        if not self.world_state:
            return "❌ World State not available"
        
        deleted = self.world_state.cleanup_expired_facts()
        
        if deleted > 0:
            return f"🧹 Cleaned up {deleted} expired facts"
        return "✅ No expired facts to clean up"
    
    def _cleanup_expired_world_state(self):
        """Periodic cleanup task"""
        if self.world_state:
            count = self.world_state.cleanup_expired_facts()
            if count > 0:
                print(f"🧹 World State cleanup: {count} expired facts removed")
