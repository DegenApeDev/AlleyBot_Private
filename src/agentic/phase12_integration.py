"""
Phase 12 Integration Mixin
Wires learning, performance tracking, and memory pruning into the agentic system
"""
from typing import Dict, List, Optional, Any
from datetime import datetime


class Phase12IntegrationMixin:
    """
    Mixin to add Phase 12 Memory & Learning capabilities
    to AgenticAlleyBot or AlleyBotCore
    """
    
    def __init__(self, *args, **kwargs):
        # Import here to avoid circular imports
        try:
            from .phase12_learning import Phase12LearningMixin
            self.phase12_learning = Phase12LearningMixin()
        except Exception as e:
            print(f"⚠️ Could not initialize Phase 12 learning: {e}")
            self.phase12_learning = None
    
    # Performance & Learning Tools
    def record_content_performance(self, content_id: str, platform: str,
                                   content_type: str, topic: str,
                                   metadata: Optional[Dict] = None) -> bool:
        """Record content for performance tracking (Phase 12.1, 12.3)"""
        if self.phase12_learning:
            return self.phase12_learning.record_content_performance(
                content_id, platform, content_type, topic, metadata
            )
        return False
    
    def update_content_engagement(self, content_id: str, **engagement) -> bool:
        """Update engagement metrics (Phase 12.3)"""
        if self.phase12_learning:
            return self.phase12_learning.update_content_engagement(
                content_id, **engagement
            )
        return False
    
    def get_content_strategy(self) -> Dict:
        """Get AI-generated content strategy based on performance (Phase 12.1)"""
        if self.phase12_learning:
            return self.phase12_learning.generate_content_strategy()
        return {'error': 'Phase 12 learning not available'}
    
    def get_top_topics(self, limit: int = 5) -> List[Dict]:
        """Get best performing topics (Phase 12.1)"""
        if self.phase12_learning:
            return self.phase12_learning.get_top_topics(limit=limit)
        return []
    
    # User Relationship Tools
    def track_user_interaction(self, user_id: str, platform: str,
                               interaction_type: str, **kwargs) -> bool:
        """Track user interaction (Phase 12.2)"""
        if self.phase12_learning:
            return self.phase12_learning.track_user_interaction(
                user_id, platform, interaction_type, **kwargs
            )
        return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user relationship profile (Phase 12.2)"""
        if self.phase12_learning:
            return self.phase12_learning.get_user_profile(user_id)
        return None
    
    def get_active_community(self, days: int = 7) -> List[Dict]:
        """Get active community members (Phase 12.2)"""
        if self.phase12_learning:
            return self.phase12_learning.get_active_community_members(days)
        return []
    
    def get_community_summary(self) -> Dict:
        """Get community relationship summary (Phase 12.2)"""
        if self.phase12_learning:
            return self.phase12_learning.get_relationship_summary()
        return {'error': 'Phase 12 learning not available'}
    
    # Memory Pruning Tools
    def prune_memories_advanced(self, max_age_days: int = 30,
                                min_relevance: float = 0.3) -> Dict:
        """Advanced memory pruning (Phase 12.5)"""
        if hasattr(self, 'memory') and self.memory:
            return self.memory.advanced_prune(max_age_days, min_relevance)
        return {'error': 'Memory system not available'}
    
    def get_memory_pruning_report(self) -> Dict:
        """Get memory pruning report (Phase 12.5)"""
        if hasattr(self, 'memory') and self.memory:
            return self.memory.get_pruning_report()
        return {'error': 'Memory system not available'}
    
    def auto_prune_scheduled(self) -> Dict:
        """Run scheduled auto-pruning (Phase 12.5)"""
        stats = self.prune_memories_advanced(max_age_days=30, min_relevance=0.3)
        
        # Record the pruning activity
        if hasattr(self, 'memory') and self.memory:
            self.memory.add_memory(
                f"Auto-pruned memories: {stats.get('vector', {}).get('removed', 0)} vector, "
                f"{stats.get('regular', {}).get('removed', 0)} regular",
                memory_type='maintenance',
                metadata={'pruning_stats': stats}
            )
        
        return stats
