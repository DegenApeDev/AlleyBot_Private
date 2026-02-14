"""
World State Platform Adapter - Generic ingestion framework for any platform

This module provides a standardized interface for ingesting data from any
social platform into the World State. New platforms only need to implement
the PlatformAdapter interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PlatformEntity:
    """Standardized entity from any platform"""
    id: str
    type: str  # 'user', 'agent', 'post', 'topic', 'comment', 'debate'
    platform: str  # 'moltx', 'clawbr', 'twitter', etc.
    name: Optional[str] = None
    display_name: Optional[str] = None
    attributes: Optional[Dict] = None
    created_at: Optional[str] = None
    url: Optional[str] = None  # Link to original content


@dataclass
class PlatformInteraction:
    """Standardized interaction from any platform"""
    id: str
    type: str  # 'post', 'like', 'reply', 'repost', 'debate', 'vote'
    platform: str
    actor_id: str  # Who did it
    target_id: Optional[str] = None  # What was affected (if any)
    content: Optional[str] = None
    timestamp: Optional[str] = None
    engagement_metrics: Optional[Dict] = None  # likes, replies, shares, etc.
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None


@dataclass
class PlatformRelationship:
    """Standardized relationship from any platform"""
    from_entity: str
    to_entity: str
    relation_type: str  # 'follows', 'mentioned', 'replied_to', 'debated_with'
    platform: str
    strength: float = 0.5
    timestamp: Optional[str] = None


class PlatformAdapter(ABC):
    """
    Abstract base class for platform-specific World State ingestion.
    
    Any new platform (Moltx, Clawbr, Twitter, Discord, etc.) must implement
    this interface to integrate with World State.
    
    Example implementation:
    
    ```python
    class MoltxAdapter(PlatformAdapter):
        def __init__(self, moltx_plugin):
            self.moltx = moltx_plugin
        
        def get_platform_name(self) -> str:
            return "moltx"
        
        def fetch_recent_interactions(self, limit: int = 50) -> List[PlatformInteraction]:
            feed = self.moltx.get_feed(limit=limit)
            return [self._convert_post(p) for p in feed]
        
        def convert_to_entities(self, raw_data: Dict) -> PlatformEntity:
            return PlatformEntity(
                id=f"moltx_{raw_data['id']}",
                type='post',
                platform='moltx',
                name=raw_data.get('agent_name'),
                attributes={'content': raw_data.get('content')}
            )
    ```
    """
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform identifier (e.g., 'moltx', 'clawbr')"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the platform is connected/authenticated"""
        pass
    
    @abstractmethod
    def fetch_recent_interactions(self, limit: int = 50, since: Optional[str] = None) -> List[PlatformInteraction]:
        """
        Fetch recent posts, likes, replies, etc. from the platform.
        
        Args:
            limit: Maximum number of interactions to fetch
            since: ISO timestamp - only fetch interactions after this time
            
        Returns:
            List of standardized PlatformInteraction objects
        """
        pass
    
    @abstractmethod
    def fetch_entities(self, entity_type: Optional[str] = None, limit: int = 50) -> List[PlatformEntity]:
        """
        Fetch entities (users, agents, posts) from the platform.
        
        Args:
            entity_type: Filter by type ('user', 'post', 'topic', etc.) or None for all
            limit: Maximum number of entities to fetch
            
        Returns:
            List of standardized PlatformEntity objects
        """
        pass
    
    @abstractmethod
    def fetch_relationships(self, entity_id: Optional[str] = None, limit: int = 100) -> List[PlatformRelationship]:
        """
        Fetch relationships (follows, mentions, replies) from the platform.
        
        Args:
            entity_id: Filter by specific entity, or None for all
            limit: Maximum number of relationships to fetch
            
        Returns:
            List of standardized PlatformRelationship objects
        """
        pass
    
    def record_interaction(self, interaction: PlatformInteraction, world_state_manager) -> bool:
        """
        Record a single interaction to World State.
        Can be overridden for platform-specific handling.
        """
        try:
            from src.autonomy.world_state import Entity, Fact, Event, Relationship
            
            # Create or update actor entity
            actor = Entity(
                id=f"{interaction.platform}_{interaction.actor_id}",
                type='agent',
                platform=interaction.platform,
                name=interaction.actor_id,
                last_observed_at=interaction.timestamp or datetime.now().isoformat()
            )
            world_state_manager.add_entity(actor)
            
            # Create event
            event = Event(
                event_type=interaction.type,
                actor_id=actor.id,
                target_id=f"{interaction.platform}_{interaction.target_id}" if interaction.target_id else None,
                platform=interaction.platform,
                data={
                    'content_preview': interaction.content[:100] if interaction.content else '',
                    'engagement': interaction.engagement_metrics,
                    'hashtags': interaction.hashtags,
                    'mentions': interaction.mentions
                },
                timestamp=interaction.timestamp or datetime.now().isoformat()
            )
            world_state_manager.add_event(event)
            
            # Record engagement metrics as facts if available
            if interaction.engagement_metrics:
                for metric, value in interaction.engagement_metrics.items():
                    if interaction.target_id:
                        target_entity_id = f"{interaction.platform}_{interaction.target_id}"
                        world_state_manager.add_fact(Fact(
                            entity_id=target_entity_id,
                            attribute=metric,
                            value=str(value),
                            value_type='int' if isinstance(value, int) else 'float',
                            source=f'{interaction.platform}_api',
                            timestamp=interaction.timestamp
                        ))
            
            return True
        except Exception as e:
            print(f"❌ Failed to record interaction: {e}")
            return False
    
    def sync_to_world_state(self, world_state_manager, limit: int = 50) -> Dict[str, int]:
        """
        Sync all recent data from this platform to World State.
        
        This is the main entry point - called periodically to keep World State fresh.
        
        Returns:
            Stats dict: {'entities': N, 'interactions': N, 'relationships': N}
        """
        if not self.is_available():
            return {'entities': 0, 'interactions': 0, 'relationships': 0, 'error': 'Platform not available'}
        
        stats = {'entities': 0, 'interactions': 0, 'relationships': 0}
        
        try:
            # Fetch and record interactions
            interactions = self.fetch_recent_interactions(limit=limit)
            for interaction in interactions:
                if self.record_interaction(interaction, world_state_manager):
                    stats['interactions'] += 1
            
            # Fetch and record entities
            entities = self.fetch_entities(limit=limit)
            for entity in entities:
                from src.autonomy.world_state import Entity
                ws_entity = Entity(
                    id=entity.id,
                    type=entity.type,
                    platform=entity.platform,
                    name=entity.name,
                    display_name=entity.display_name,
                    attributes=entity.attributes,
                    last_observed_at=entity.created_at or datetime.now().isoformat()
                )
                if world_state_manager.add_entity(ws_entity):
                    stats['entities'] += 1
            
            # Fetch and record relationships
            relationships = self.fetch_relationships(limit=limit)
            for rel in relationships:
                from src.autonomy.world_state import Relationship
                ws_rel = Relationship(
                    from_entity=rel.from_entity,
                    to_entity=rel.to_entity,
                    relation_type=rel.relation_type,
                    strength=rel.strength,
                    timestamp=rel.timestamp or datetime.now().isoformat(),
                    context={'platform': rel.platform}
                )
                if world_state_manager.add_relationship(ws_rel):
                    stats['relationships'] += 1
            
            return stats
            
        except Exception as e:
            print(f"❌ Sync failed for {self.get_platform_name()}: {e}")
            stats['error'] = str(e)
            return stats


class WorldStateIngestionEngine:
    """
    Central engine that manages platform adapters and coordinates data ingestion.
    
    This is the main entry point for World State population. It:
    1. Registers platform adapters
    2. Runs periodic sync from all platforms
    3. Provides aggregated stats
    
    Usage:
    ```python
    engine = WorldStateIngestionEngine(world_state_manager)
    engine.register_adapter(MoltxAdapter(moltx_plugin))
    engine.register_adapter(ClawbrAdapter(clawbr_plugin))
    
    # Manual sync
    stats = engine.sync_all()
    
    # Or set up scheduled sync
    engine.start_scheduled_sync(interval_minutes=30)
    ```
    """
    
    def __init__(self, world_state_manager):
        self.world_state = world_state_manager
        self.adapters: Dict[str, PlatformAdapter] = {}
        self._last_sync = {}
    
    def register_adapter(self, adapter: PlatformAdapter):
        """Register a platform adapter"""
        platform = adapter.get_platform_name()
        self.adapters[platform] = adapter
        print(f"✅ Registered {platform} adapter")
    
    def unregister_adapter(self, platform: str):
        """Remove a platform adapter"""
        if platform in self.adapters:
            del self.adapters[platform]
            print(f"🗑️  Unregistered {platform} adapter")
    
    def sync_platform(self, platform: str, limit: int = 50) -> Dict:
        """Sync a specific platform"""
        if platform not in self.adapters:
            return {'error': f'No adapter for {platform}'}
        
        adapter = self.adapters[platform]
        stats = adapter.sync_to_world_state(self.world_state, limit)
        self._last_sync[platform] = datetime.now().isoformat()
        
        print(f"🔄 Synced {platform}: {stats['interactions']} interactions, {stats['entities']} entities")
        return stats
    
    def sync_all(self, limit: int = 50) -> Dict[str, Dict]:
        """Sync all registered platforms"""
        all_stats = {}
        
        for platform, adapter in self.adapters.items():
            try:
                stats = adapter.sync_to_world_state(self.world_state, limit)
                self._last_sync[platform] = datetime.now().isoformat()
                all_stats[platform] = stats
            except Exception as e:
                all_stats[platform] = {'error': str(e)}
        
        # Summary
        total_interactions = sum(s.get('interactions', 0) for s in all_stats.values())
        total_entities = sum(s.get('entities', 0) for s in all_stats.values())
        print(f"🌍 Sync complete: {total_interactions} interactions, {total_entities} entities from {len(self.adapters)} platforms")
        
        return all_stats
    
    def get_platforms_status(self) -> Dict[str, bool]:
        """Check which platforms are available"""
        return {platform: adapter.is_available() for platform, adapter in self.adapters.items()}
    
    def get_last_sync_times(self) -> Dict[str, Optional[str]]:
        """Get last sync timestamp for each platform"""
        return self._last_sync.copy()


# Helper function for easy integration
def create_platform_adapter(platform_name: str, plugin_instance) -> Optional[PlatformAdapter]:
    """
    Factory function to create appropriate adapter for a plugin.
    
    This allows automatic adapter discovery - just pass the plugin and
    get back the right adapter.
    
    Args:
        platform_name: Name of the platform
        plugin_instance: The plugin object (MoltxPlugin, ClawbrPlugin, etc.)
        
    Returns:
        PlatformAdapter instance or None if not supported
    """
    # Try to find adapter class dynamically
    try:
        module_name = f"plugins.{platform_name}.{platform_name}_adapter"
        class_name = f"{platform_name.title()}Adapter"
        
        import importlib
        module = importlib.import_module(module_name)
        adapter_class = getattr(module, class_name)
        
        return adapter_class(plugin_instance)
    except (ImportError, AttributeError):
        print(f"⚠️  No adapter found for {platform_name}")
        return None
