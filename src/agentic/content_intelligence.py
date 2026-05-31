"""
Cross-Platform Content Intelligence System

Learns what content works across platforms and optimizes accordingly.

This system analyzes content performance across ALL platforms (MoltX, Telegram, Clawbr, etc.)
and identifies patterns that lead to high engagement. It then uses these insights to optimize
future content generation.

Key Features:
- Analyzes content performance across all platforms
- Identifies successful patterns (topics, timing, tone)
- Optimizes future content based on real engagement data
- Applies learnings universally

Integration:
- Uses UnifiedMemory for cross-platform data
- Uses EpisodicMemory for historical performance
- Integrates with ContentStrategy for optimization
- Feeds into AGI decision-making
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


class ContentIntelligence:
    """
    Learns what content works across platforms and optimizes accordingly.
    
    Analyzes:
    - Topic performance (which topics get high engagement)
    - Timing patterns (when posts perform best)
    - Tone effectiveness (technical vs casual, etc.)
    - Platform-specific preferences
    
    Optimizes:
    - Content topic selection
    - Posting timing
    - Tone and style
    - Hashtag usage
    """
    
    def __init__(self, unified_memory, episodic_memory=None, world_state=None):
        self.memory = unified_memory
        self.episodes = episodic_memory
        self.world_state = world_state
        
        # Performance thresholds
        self.high_performance_threshold = 0.7  # 70% engagement
        self.low_performance_threshold = 0.3   # 30% engagement
    
    def analyze_content_performance(self, time_range_days: int = 30) -> Dict[str, Any]:
        """
        Analyze what content performs well across all platforms.
        
        Args:
            time_range_days: Number of days to analyze
            
        Returns:
            Insights for future content generation
        """
        try:
            insights = {
                'best_topics': [],
                'best_times': [],
                'best_tone': 'balanced',
                'avoid_topics': [],
                'avoid_times': [],
                'platform_preferences': {},
                'overall_stats': {}
            }
            
            # Get posts from world state if available
            if self.world_state:
                posts = self._get_posts_from_world_state(time_range_days)
            else:
                posts = []
            
            # Get episodes from episodic memory if available
            if self.episodes:
                episodes = self._get_episodes_from_memory(time_range_days)
            else:
                episodes = []
            
            # Combine data sources
            all_content = posts + episodes
            
            if not all_content:
                logger.debug("No content data available for analysis")
                return insights
            
            # Separate high and low performers
            high_performers = [c for c in all_content if self._get_engagement_score(c) > self.high_performance_threshold]
            low_performers = [c for c in all_content if self._get_engagement_score(c) < self.low_performance_threshold]
            
            # Analyze topics
            insights['best_topics'] = self._extract_topics(high_performers)
            insights['avoid_topics'] = self._extract_topics(low_performers)
            
            # Analyze timing
            insights['best_times'] = self._extract_timing(high_performers)
            insights['avoid_times'] = self._extract_timing(low_performers)
            
            # Analyze tone
            insights['best_tone'] = self._extract_tone(high_performers)
            
            # Platform-specific analysis
            insights['platform_preferences'] = self._analyze_platform_preferences(all_content)
            
            # Overall stats
            insights['overall_stats'] = {
                'total_content': len(all_content),
                'high_performers': len(high_performers),
                'low_performers': len(low_performers),
                'avg_engagement': sum(self._get_engagement_score(c) for c in all_content) / len(all_content) if all_content else 0
            }
            
            logger.info(f"📊 Content analysis complete: {len(high_performers)} high performers, {len(low_performers)} low performers")
            
            return insights
        
        except Exception as e:
            logger.error(f"Content performance analysis failed: {e}")
            return {
                'best_topics': [],
                'best_times': [],
                'best_tone': 'balanced',
                'avoid_topics': [],
                'avoid_times': [],
                'platform_preferences': {},
                'overall_stats': {}
            }
    
    def optimize_content(self, draft: str, platform: str, context: Dict = None) -> str:
        """
        Optimize content based on learned patterns.
        
        Args:
            draft: Original content
            platform: Target platform
            context: Additional context (time, topic, etc.)
            
        Returns:
            Optimized content
        """
        try:
            # Get performance insights
            insights = self.analyze_content_performance()
            
            optimized = draft
            
            # Apply topic optimization
            best_topics = insights.get('best_topics', [])
            if best_topics:
                # Check if draft contains successful topics
                has_good_topic = any(topic.lower() in draft.lower() for topic in best_topics[:3])
                
                if not has_good_topic and len(draft) < 200:
                    # Add a successful topic reference if space allows
                    optimized += f"\n\n#{best_topics[0]}"
            
            # Apply tone optimization
            best_tone = insights.get('best_tone', 'balanced')
            current_tone = self._detect_tone(draft)
            
            if best_tone != current_tone and best_tone != 'balanced':
                # Note: Actual tone adjustment would require AI/LLM
                # For now, just log the recommendation
                logger.debug(f"Recommend adjusting tone from {current_tone} to {best_tone}")
            
            # Apply platform-specific optimizations
            platform_prefs = insights.get('platform_preferences', {}).get(platform, {})
            if platform_prefs:
                # Apply platform-specific best practices
                if platform_prefs.get('prefers_hashtags') and '#' not in optimized:
                    if best_topics:
                        optimized += f" #{best_topics[0]}"
            
            return optimized
        
        except Exception as e:
            logger.error(f"Content optimization failed: {e}")
            return draft
    
    def should_post_now(self, platform: str, content_type: str = 'post') -> Dict[str, Any]:
        """
        Determine if now is a good time to post based on historical performance.
        
        Args:
            platform: Target platform
            content_type: Type of content
            
        Returns:
            Decision with reasoning
        """
        try:
            current_hour = datetime.now().hour
            
            # Get timing insights
            insights = self.analyze_content_performance()
            best_times = insights.get('best_times', [])
            avoid_times = insights.get('avoid_times', [])
            
            # Check if current hour is in best times
            is_best_time = current_hour in best_times
            is_avoid_time = current_hour in avoid_times
            
            # Calculate score
            if is_best_time:
                score = 0.9
                reason = f"Optimal time - historical data shows high engagement at {current_hour}:00"
            elif is_avoid_time:
                score = 0.3
                reason = f"Suboptimal time - historical data shows low engagement at {current_hour}:00"
            else:
                score = 0.6
                reason = f"Neutral time - no strong historical signal for {current_hour}:00"
            
            return {
                'should_post': score > 0.5,
                'confidence': score,
                'reason': reason,
                'best_times': best_times,
                'current_hour': current_hour
            }
        
        except Exception as e:
            logger.error(f"Timing analysis failed: {e}")
            return {
                'should_post': True,
                'confidence': 0.5,
                'reason': 'No timing data available',
                'best_times': [],
                'current_hour': datetime.now().hour
            }
    
    def _get_posts_from_world_state(self, days: int) -> List[Dict]:
        """Get posts from world state"""
        posts = []
        try:
            # Get events from world state
            cutoff = datetime.now() - timedelta(days=days)
            events = self.world_state.get_events(limit=1000)
            
            for event in events:
                # Filter for post events
                if event.event_type in ['post_created', 'content_posted']:
                    # Calculate engagement score from event data
                    engagement = event.metadata.get('engagement', {})
                    likes = engagement.get('likes', 0)
                    replies = engagement.get('replies', 0)
                    
                    posts.append({
                        'content': event.metadata.get('content', ''),
                        'platform': event.metadata.get('platform', 'unknown'),
                        'timestamp': event.timestamp,
                        'engagement_score': self._calculate_engagement_score(likes, replies),
                        'hour': datetime.fromisoformat(event.timestamp).hour if event.timestamp else 0
                    })
        except Exception as e:
            logger.debug(f"Could not get posts from world state: {e}")
        
        return posts
    
    def _get_episodes_from_memory(self, days: int) -> List[Dict]:
        """Get content episodes from episodic memory"""
        episodes = []
        try:
            # Get all memories
            all_memories = self.episodes.get_all_memories()
            
            cutoff = datetime.now() - timedelta(days=days)
            
            for memory in all_memories:
                # Filter for content-related actions
                if 'post' in memory.action.lower() or 'content' in memory.context.lower():
                    # Extract engagement from outcome
                    engagement_score = 0.5  # Default
                    if memory.emotional_valence > 0:
                        engagement_score = 0.5 + (memory.emotional_valence * 0.5)
                    else:
                        engagement_score = 0.5 + (memory.emotional_valence * 0.5)
                    
                    episodes.append({
                        'content': memory.action,
                        'platform': self._extract_platform(memory.context),
                        'timestamp': memory.timestamp,
                        'engagement_score': engagement_score,
                        'hour': memory.timestamp.hour if memory.timestamp else 0
                    })
        except Exception as e:
            logger.debug(f"Could not get episodes from memory: {e}")
        
        return episodes
    
    def _get_engagement_score(self, content: Dict) -> float:
        """Get engagement score from content data"""
        return content.get('engagement_score', 0.5)
    
    def _calculate_engagement_score(self, likes: int, replies: int) -> float:
        """Calculate engagement score from metrics"""
        # Simple formula: normalize to 0-1 range
        total = likes + (replies * 2)  # Weight replies higher
        return min(total / 20, 1.0)  # Cap at 1.0
    
    def _extract_topics(self, content_list: List[Dict]) -> List[str]:
        """Extract common topics from content"""
        topics = defaultdict(int)
        
        for content in content_list:
            text = content.get('content', '')
            
            # Extract hashtags
            hashtags = re.findall(r'#(\w+)', text)
            for tag in hashtags:
                topics[tag] += 1
            
            # Extract common keywords (simple approach)
            keywords = ['DeFi', 'NFT', 'AI', 'crypto', 'blockchain', 'web3', 'agent', 'trading']
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    topics[keyword] += 1
        
        # Sort by frequency
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in sorted_topics[:10]]
    
    def _extract_timing(self, content_list: List[Dict]) -> List[int]:
        """Extract best posting times (hours)"""
        hour_performance = defaultdict(list)
        
        for content in content_list:
            hour = content.get('hour', 0)
            score = content.get('engagement_score', 0)
            hour_performance[hour].append(score)
        
        # Calculate average performance per hour
        hour_avg = {}
        for hour, scores in hour_performance.items():
            hour_avg[hour] = sum(scores) / len(scores)
        
        # Sort by performance
        sorted_hours = sorted(hour_avg.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, _ in sorted_hours[:5]]
    
    def _extract_tone(self, content_list: List[Dict]) -> str:
        """Extract best performing tone"""
        tone_scores = defaultdict(list)
        
        for content in content_list:
            text = content.get('content', '')
            tone = self._detect_tone(text)
            score = content.get('engagement_score', 0)
            tone_scores[tone].append(score)
        
        # Calculate average per tone
        tone_avg = {}
        for tone, scores in tone_scores.items():
            tone_avg[tone] = sum(scores) / len(scores)
        
        # Return best tone
        if tone_avg:
            return max(tone_avg.items(), key=lambda x: x[1])[0]
        return 'balanced'
    
    def _detect_tone(self, text: str) -> str:
        """Detect tone of text"""
        text_lower = text.lower()
        
        # Technical indicators
        technical_words = ['protocol', 'algorithm', 'implementation', 'architecture', 'optimize']
        technical_count = sum(1 for word in technical_words if word in text_lower)
        
        # Casual indicators
        casual_words = ['lol', 'btw', 'tbh', '!', '😂', '🔥']
        casual_count = sum(1 for word in casual_words if word in text_lower)
        
        if technical_count > casual_count:
            return 'technical'
        elif casual_count > technical_count:
            return 'casual'
        return 'balanced'
    
    def _analyze_platform_preferences(self, content_list: List[Dict]) -> Dict[str, Dict]:
        """Analyze platform-specific preferences"""
        platform_data = defaultdict(lambda: {'posts': [], 'avg_engagement': 0})
        
        for content in content_list:
            platform = content.get('platform', 'unknown')
            platform_data[platform]['posts'].append(content)
        
        # Calculate preferences
        preferences = {}
        for platform, data in platform_data.items():
            posts = data['posts']
            if not posts:
                continue
            
            avg_engagement = sum(p.get('engagement_score', 0) for p in posts) / len(posts)
            
            # Check if hashtags correlate with engagement
            with_hashtags = [p for p in posts if '#' in p.get('content', '')]
            without_hashtags = [p for p in posts if '#' not in p.get('content', '')]
            
            hashtag_boost = 0
            if with_hashtags and without_hashtags:
                avg_with = sum(p.get('engagement_score', 0) for p in with_hashtags) / len(with_hashtags)
                avg_without = sum(p.get('engagement_score', 0) for p in without_hashtags) / len(without_hashtags)
                hashtag_boost = avg_with - avg_without
            
            preferences[platform] = {
                'avg_engagement': avg_engagement,
                'prefers_hashtags': hashtag_boost > 0.1,
                'total_posts': len(posts)
            }
        
        return preferences
    
    def _extract_platform(self, context: str) -> str:
        """Extract platform from context string"""
        context_lower = context.lower()
        if 'moltx' in context_lower:
            return 'moltx'
        elif 'telegram' in context_lower:
            return 'telegram'
        elif 'clawbr' in context_lower:
            return 'clawbr'
        return 'unknown'


def create_content_intelligence(unified_memory, episodic_memory=None, world_state=None):
    """Factory function to create content intelligence system"""
    return ContentIntelligence(unified_memory, episodic_memory, world_state)
