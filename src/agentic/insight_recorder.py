"""
Insight Recorder for Cross-Platform Learning

Automatically records insights from platform interactions that can be
applied across all platforms. This enables true cross-platform learning.

Examples:
- "DeFi topics get 2x engagement on MoltX" → Apply to all platforms
- "Technical depth resonates with audience" → Adjust tone everywhere
- "Morning posts (10am-12pm) perform better" → Schedule optimization
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InsightRecorder:
    """
    Automatically records cross-platform insights from interactions.
    
    Integrates with:
    - UnifiedMemory (stores insights)
    - WorldState (tracks interaction patterns)
    - ContentStrategy (applies insights to content generation)
    """
    
    def __init__(self, agi_kernel):
        self.agi = agi_kernel
        self.unified_memory = agi_kernel.unified_memory if hasattr(agi_kernel, 'unified_memory') else None
        
    def analyze_and_record_insights(self, platform: str = None) -> List[Dict]:
        """
        Analyze recent platform data and record cross-platform insights.
        
        Called periodically by AGI cycle to learn from interactions.
        
        Args:
            platform: Specific platform to analyze, or None for all
            
        Returns:
            List of recorded insights
        """
        if not self.unified_memory:
            return []
        
        insights_recorded = []
        
        try:
            # Get cross-platform user profile
            profile = self.unified_memory.get_cross_platform_user_profile('global')
            
            # Analyze topic interests
            topic_insights = self._analyze_topic_preferences(profile)
            for insight in topic_insights:
                if self.unified_memory.record_cross_platform_insight(insight):
                    insights_recorded.append(insight)
            
            # Analyze engagement patterns
            engagement_insights = self._analyze_engagement_patterns(profile)
            for insight in engagement_insights:
                if self.unified_memory.record_cross_platform_insight(insight):
                    insights_recorded.append(insight)
            
            # Analyze platform-specific performance
            if hasattr(self.agi, 'world_state') and self.agi.world_state:
                performance_insights = self._analyze_platform_performance()
                for insight in performance_insights:
                    if self.unified_memory.record_cross_platform_insight(insight):
                        insights_recorded.append(insight)
            
            if insights_recorded:
                logger.info(f"💡 Recorded {len(insights_recorded)} cross-platform insights")
            
        except Exception as e:
            logger.warning(f"⚠️ Insight recording failed: {e}")
        
        return insights_recorded
    
    def _analyze_topic_preferences(self, profile: Dict) -> List[Dict]:
        """Analyze topic interests and generate insights"""
        insights = []
        
        topic_interests = profile.get('topic_interests', [])
        interaction_count = profile.get('interaction_count', 0)
        
        # Only record if we have sufficient data
        if interaction_count < 10:
            return insights
        
        # Top topics become insights
        for topic in topic_interests[:3]:
            insights.append({
                'description': f"Audience shows strong interest in {topic} topics",
                'platform': 'aggregate',
                'applies_to': 'all',
                'confidence': min(0.9, 0.5 + (interaction_count / 100)),
                'insight_type': 'topic',
                'data': {
                    'topic': topic,
                    'interaction_count': interaction_count,
                    'source': 'topic_analysis'
                }
            })
        
        return insights
    
    def _analyze_engagement_patterns(self, profile: Dict) -> List[Dict]:
        """Analyze engagement patterns across platforms"""
        insights = []
        
        platforms = profile.get('platforms', {})
        
        # Compare engagement across platforms
        platform_engagement = {}
        for platform_name, platform_data in platforms.items():
            if isinstance(platform_data, dict):
                platform_engagement[platform_name] = platform_data.get('interaction_count', 0)
        
        if not platform_engagement:
            return insights
        
        # Find best performing platform
        best_platform = max(platform_engagement.items(), key=lambda x: x[1])
        if best_platform[1] > 5:  # Minimum threshold
            insights.append({
                'description': f"{best_platform[0]} shows highest engagement ({best_platform[1]} interactions)",
                'platform': best_platform[0],
                'applies_to': 'all',
                'confidence': 0.7,
                'insight_type': 'engagement',
                'data': {
                    'platform': best_platform[0],
                    'interaction_count': best_platform[1],
                    'source': 'engagement_analysis'
                }
            })
        
        return insights
    
    def _analyze_platform_performance(self) -> List[Dict]:
        """Analyze platform-specific performance metrics"""
        insights = []
        
        try:
            # Get recent events from world state
            if not hasattr(self.agi, 'world_state') or not self.agi.world_state:
                return insights
            
            # Analyze trending topics
            trending = self.agi.world_state.get_trending_topics(limit=5)
            
            for topic_data in trending:
                topic = topic_data.get('topic')
                count = topic_data.get('count', 0)
                
                if count > 3:  # Minimum threshold
                    insights.append({
                        'description': f"Topic '{topic}' is trending with {count} mentions",
                        'platform': 'aggregate',
                        'applies_to': 'all',
                        'confidence': min(0.9, 0.6 + (count / 20)),
                        'insight_type': 'topic',
                        'data': {
                            'topic': topic,
                            'mention_count': count,
                            'source': 'trending_analysis'
                        }
                    })
        
        except Exception as e:
            logger.debug(f"Platform performance analysis failed: {e}")
        
        return insights
    
    def record_manual_insight(self, description: str, platform: str, 
                             applies_to: str = 'all', confidence: float = 0.8,
                             insight_type: str = 'manual') -> bool:
        """
        Manually record an insight (e.g., from user feedback or observation).
        
        Args:
            description: Human-readable insight description
            platform: Source platform
            applies_to: Target platforms ('all' or list)
            confidence: Confidence level (0-1)
            insight_type: Type of insight
            
        Returns:
            Success boolean
        """
        if not self.unified_memory:
            return False
        
        insight = {
            'description': description,
            'platform': platform,
            'applies_to': applies_to,
            'confidence': confidence,
            'insight_type': insight_type,
            'data': {
                'source': 'manual',
                'recorded_at': datetime.now().isoformat()
            }
        }
        
        return self.unified_memory.record_cross_platform_insight(insight)


def create_insight_recorder(agi_kernel):
    """Factory function to create insight recorder"""
    return InsightRecorder(agi_kernel)
