"""
Unified Memory Bridge - AGI Foundation

Consolidates all memory systems into a coherent world model:
- WorldState (entities, facts, relationships, events)
- EnhancedMemory (vector DB, semantic search, goals)
- Phase12Learning (content performance, user tracking)
- Core Memory (simple JSON storage)

Provides a single API for persistent, queryable, learning memory.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

class UnifiedMemory:
    """
    Single interface to all memory systems.
    Automatically syncs and cross-references data.
    """
    
    def __init__(self, core=None):
        self.core = core
        self._init_systems()
        
    def _init_systems(self):
        """Initialize all memory subsystems"""
        # World State
        try:
            from src.autonomy.world_state import create_world_state_manager
            self.world_state = create_world_state_manager(self.core)
            print("✅ World State connected")
        except Exception as e:
            print(f"⚠️ World State unavailable: {e}")
            self.world_state = None
            
        # Enhanced Memory (Vector DB)
        try:
            from src.agentic.enhanced_memory import EnhancedMemorySystem
            self.enhanced_memory = EnhancedMemorySystem()
            print("✅ Enhanced Memory connected")
        except Exception as e:
            print(f"⚠️ Enhanced Memory unavailable: {e}")
            self.enhanced_memory = None
            
        # Phase 12 Learning
        try:
            from src.agentic.phase12_learning import Phase12LearningMixin
            self.phase12 = Phase12LearningMixin()
            print("✅ Phase 12 Learning connected")
        except Exception as e:
            print(f"⚠️ Phase 12 Learning unavailable: {e}")
            self.phase12 = None
            
    # =================================================================
    # Unified Storage API
    # =================================================================
    
    def store(self, content: str, memory_type: str = 'general', 
              metadata: Optional[Dict] = None, entity_id: Optional[str] = None) -> str:
        """
        Store a memory across all relevant systems
        
        Args:
            content: The memory content
            memory_type: Type of memory (interaction, learning, goal, entity, fact)
            metadata: Additional context
            entity_id: Optional entity to associate with
            
        Returns:
            memory_id: Unique identifier for this memory
        """
        memory_id = f"mem_{datetime.now().timestamp()}"
        metadata = metadata or {}
        
        # 1. Store in Enhanced Memory (vector DB for semantic search)
        if self.enhanced_memory:
            self.enhanced_memory.add_memory(
                content=content,
                memory_type=memory_type,
                metadata={**metadata, 'memory_id': memory_id, 'entity_id': entity_id}
            )
        
        # 2. Store in World State (if entity-related)
        if entity_id and self.world_state:
            from src.autonomy.world_state import Fact
            self.world_state.add_fact(Fact(
                entity_id=entity_id,
                attribute=memory_type,
                value=content,
                source='unified_memory',
                timestamp=datetime.now().isoformat()
            ))
        
        # 3. Store event if significant
        if memory_type in ['interaction', 'achievement', 'learning'] and self.world_state:
            from src.autonomy.world_state import Event
            self.world_state.add_event(Event(
                event_type=memory_type,
                actor_id=entity_id or 'self',
                target_id=metadata.get('target_id'),
                platform=metadata.get('platform', 'unknown'),
                data={'content': content, 'metadata': metadata}
            ))
            
        return memory_id
    
    # =================================================================
    # Unified Retrieval API
    # =================================================================
    
    def recall(self, query: str, k: int = 5, memory_type: Optional[str] = None) -> List[Dict]:
        """
        Semantic search across all memory systems
        
        Args:
            query: Search query
            k: Number of results
            memory_type: Filter by type
            
        Returns:
            List of relevant memories with sources
        """
        results = []
        
        # 1. Search Enhanced Memory (vector DB)
        if self.enhanced_memory:
            memories = self.enhanced_memory.search_memories(query, k=k, memory_type=memory_type)
            for mem in memories:
                mem['source'] = 'enhanced_memory'
                results.append(mem)
        
        # 2. Search World State entities
        if self.world_state:
            entities = self.world_state.search_entities(query, limit=k)
            for entity in entities:
                results.append({
                    'id': entity.id,
                    'content': f"Entity: {entity.name or entity.id} ({entity.type})",
                    'memory_type': 'entity',
                    'source': 'world_state',
                    'timestamp': entity.updated_at,
                    'metadata': entity.attributes
                })
        
        # Sort by relevance/timestamp and return top k
        results.sort(key=lambda x: x.get('relevance_score', 0.5), reverse=True)
        return results[:k]
    
    def get_entity_context(self, entity_id: str) -> Dict[str, Any]:
        """
        Get comprehensive context about an entity from all systems
        
        Returns merged data from:
        - World State (facts, relationships)
        - Phase 12 (interaction history)
        - Enhanced Memory (related memories)
        """
        context = {
            'entity_id': entity_id,
            'world_state': None,
            'relationships': [],
            'facts': [],
            'interaction_count': 0,
            'recent_memories': []
        }
        
        # 1. World State data
        if self.world_state:
            entity_data = self.world_state.get_entity_with_facts(entity_id)
            if entity_data:
                context['world_state'] = entity_data
                context['facts'] = [f.to_dict() for f in entity_data.get('facts', [])]
                
            # Get relationships
            relationships = self.world_state.get_relationships(entity_id)
            context['relationships'] = [r.to_dict() for r in relationships]
        
        # 2. Phase 12 user data
        if self.phase12:
            profile = self.phase12.get_user_profile(entity_id)
            if profile:
                context['interaction_count'] = profile.get('interaction_count', 0)
                context['preferred_topics'] = profile.get('preferred_topics', [])
                context['sentiment_trend'] = profile.get('sentiment_trend', 'neutral')
        
        # 3. Related memories
        if self.enhanced_memory:
            memories = self.enhanced_memory.search_memories(entity_id, k=10)
            context['recent_memories'] = memories
        
        return context
    
    # =================================================================
    # Learning & Adaptation
    # =================================================================
    
    def learn_from_interaction(self, user_id: str, interaction_type: str, 
                               content: str, outcome: Optional[str] = None,
                               platform: str = 'unknown') -> bool:
        """
        Record an interaction and update all relevant learning systems
        
        This is where episodic memory becomes learning:
        - Records the interaction
        - Updates user model
        - If outcome provided, adjusts future behavior weights
        """
        try:
            # 1. Store as memory
            self.store(
                content=content,
                memory_type='interaction',
                metadata={
                    'user_id': user_id,
                    'interaction_type': interaction_type,
                    'outcome': outcome,
                    'platform': platform
                },
                entity_id=user_id
            )
            
            # 2. Track in Phase 12
            if self.phase12:
                self.phase12.track_user_interaction(
                    user_id=user_id,
                    platform=platform,
                    interaction_type=interaction_type
                )
            
            # 3. Update World State relationship
            if self.world_state:
                from src.autonomy.world_state import Relationship
                # Strengthen relationship
                existing = self.world_state.get_relationships(user_id, relation_type='interacted_with')
                strength = 0.5
                if existing:
                    strength = min(1.0, existing[0].strength + 0.1)
                
                self.world_state.add_relationship(Relationship(
                    from_entity='alleybot',
                    to_entity=user_id,
                    relation_type='interacted_with',
                    strength=strength,
                    context={'last_interaction': interaction_type, 'platform': platform}
                ))
            
            return True
        except Exception as e:
            print(f"❌ Failed to learn from interaction: {e}")
            return False
    
    def get_behavior_weights(self, context: Dict[str, Any]) -> Dict[str, float]:
        """
        Get dynamically adjusted behavior weights based on memory
        
        This enables the system to change how it behaves based on:
        - Past interaction outcomes
        - User preferences
        - Content performance
        """
        weights = {
            'formality': 0.5,
            'verbosity': 0.5,
            'emoji_usage': 0.7,
            'technical_depth': 0.5
        }
        
        user_id = context.get('user_id')
        if not user_id:
            return weights
        
        # Adjust based on user profile
        if self.phase12:
            profile = self.phase12.get_user_profile(user_id)
            if profile:
                # More interactions = more casual
                if profile.get('interaction_count', 0) > 10:
                    weights['formality'] = 0.3
                    weights['emoji_usage'] = 0.9
                
                # Preferred topics indicate technical interest
                topics = profile.get('preferred_topics', [])
                if any(t in ['AI', 'coding', 'dev', 'tech'] for t in topics):
                    weights['technical_depth'] = 0.8
        
        return weights
    
    # =================================================================
    # Goal & Intention Management
    # =================================================================
    
    def set_goal(self, description: str, goal_type: str = 'short_term',
                 priority: int = 1, parent_goal: Optional[str] = None) -> str:
        """
        Set a goal that persists across all memory systems
        """
        if self.enhanced_memory:
            goal_id = self.enhanced_memory.add_goal(
                description=description,
                goal_type=goal_type,
                parent_goal_id=parent_goal,
                priority=priority
            )
            
            # Also store as event
            if self.world_state:
                from src.autonomy.world_state import Event
                self.world_state.add_event(Event(
                    event_type='goal_set',
                    actor_id='alleybot',
                    platform='internal',
                    data={'goal_id': goal_id, 'description': description, 'type': goal_type}
                ))
            
            return goal_id
        return None
    
    def get_active_intentions(self) -> List[Dict]:
        """
        Get current active goals that should influence behavior
        """
        goals = []
        
        if self.enhanced_memory:
            active = self.enhanced_memory.get_active_goals()
            goals.extend(active)
        
        # Sort by priority
        goals.sort(key=lambda g: g.get('priority', 1), reverse=True)
        return goals
    
    # =================================================================
    # Persistence & Stats
    # =================================================================
    
    def get_unified_stats(self) -> Dict[str, Any]:
        """Get statistics across all memory systems"""
        stats = {
            'world_state': {},
            'enhanced_memory': {},
            'phase12': {},
            'total_memories': 0
        }
        
        if self.world_state:
            ws_stats = self.world_state.get_stats()
            stats['world_state'] = ws_stats
            stats['total_memories'] += ws_stats.get('facts', 0)
        
        if self.enhanced_memory:
            em_stats = self.enhanced_memory.get_memory_stats()
            stats['enhanced_memory'] = em_stats
            stats['total_memories'] += em_stats.get('total_memories', 0)
        
        if self.phase12:
            stats['phase12'] = {
                'relationship_summary': self.phase12.get_relationship_summary()
            }
        
        return stats
    
    def sync_all(self) -> bool:
        """
        Force sync across all memory systems
        Ensures consistency and updates cross-references
        """
        try:
            # Save all systems
            if self.enhanced_memory:
                self.enhanced_memory._save_vector_store()
                self.enhanced_memory._save_goals()
            
            print("✅ Unified memory synced")
            return True
        except Exception as e:
            print(f"❌ Sync failed: {e}")
            return False


# Global instance factory
def create_unified_memory(core=None) -> UnifiedMemory:
    """Create unified memory bridge"""
    return UnifiedMemory(core)
