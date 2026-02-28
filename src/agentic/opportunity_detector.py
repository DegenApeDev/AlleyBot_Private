"""
Opportunity Detection System

Spots opportunities across platforms that user might miss.
This is a key component of JARVIS-style proactive intelligence.

Monitors:
- Trending topics
- Engagement spikes
- User mentions
- High-value interactions
- Community activity
- Market movements (if applicable)

Generates:
- Opportunity alerts
- Engagement suggestions
- Collaboration opportunities
- Content ideas

Integration:
- Uses WorldState for platform activity
- Uses ContentIntelligence for topic analysis
- Uses AdaptiveTiming for timing opportunities
- Feeds into PredictiveSuggestions
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Opportunity:
    """An detected opportunity"""
    opportunity_type: str  # 'trending', 'engagement', 'mention', 'collaboration'
    title: str
    description: str
    confidence: float
    potential_impact: str  # 'high', 'medium', 'low'
    action_suggestion: str
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


class OpportunityDetector:
    """
    Detects opportunities across platforms.
    
    JARVIS-like opportunity awareness:
    - Never miss important opportunities
    - Proactive opportunity alerts
    - Intelligent prioritization
    - Actionable suggestions
    """
    
    def __init__(self,
                 world_state=None,
                 content_intelligence=None,
                 adaptive_timing=None):
        """
        Initialize opportunity detector.
        
        Args:
            world_state: WorldState instance
            content_intelligence: ContentIntelligence instance
            adaptive_timing: AdaptiveTimingEngine instance
        """
        self.world_state = world_state
        self.content_intelligence = content_intelligence
        self.adaptive_timing = adaptive_timing
        
        # Tracking
        self.detected_opportunities = []
        self.notified_opportunities = set()
    
    def detect_opportunities(self) -> List[Opportunity]:
        """
        Detect all current opportunities.
        
        Returns:
            List of detected opportunities
        """
        opportunities = []
        
        # Trending topic opportunities
        trending = self.detect_trending_opportunities()
        opportunities.extend(trending)
        
        # Engagement opportunities
        engagement = self.detect_engagement_opportunities()
        opportunities.extend(engagement)
        
        # Mention opportunities
        mentions = self.detect_mention_opportunities()
        opportunities.extend(mentions)
        
        # Collaboration opportunities
        collabs = self.detect_collaboration_opportunities()
        opportunities.extend(collabs)
        
        # Timing opportunities
        timing = self.detect_timing_opportunities()
        opportunities.extend(timing)
        
        # Sort by impact and confidence
        opportunities.sort(
            key=lambda o: (
                {'high': 3, 'medium': 2, 'low': 1}.get(o.potential_impact, 0),
                o.confidence
            ),
            reverse=True
        )
        
        # Store for tracking
        self.detected_opportunities = opportunities
        
        return opportunities
    
    def detect_trending_opportunities(self) -> List[Opportunity]:
        """
        Find trending topics to capitalize on.
        
        Returns:
            List of trending opportunities
        """
        opportunities = []
        
        if not self.world_state:
            return opportunities
        
        try:
            # Get recent events
            events = self.world_state.get_events(limit=200)
            
            # Count topic mentions
            topic_counts = defaultdict(int)
            topic_timestamps = defaultdict(list)
            
            for event in events:
                # Extract topics from event
                content = event.metadata.get('content', '')
                topics = self._extract_topics(content)
                
                for topic in topics:
                    topic_counts[topic] += 1
                    topic_timestamps[topic].append(
                        datetime.fromisoformat(event.timestamp)
                    )
            
            # Find trending topics (high frequency in recent time)
            for topic, count in topic_counts.items():
                if count >= 5:  # Minimum threshold
                    # Check if trending (recent spike)
                    timestamps = topic_timestamps[topic]
                    recent = [t for t in timestamps if datetime.now() - t < timedelta(hours=2)]
                    
                    if len(recent) >= 3:  # Trending now
                        opportunities.append(Opportunity(
                            opportunity_type='trending',
                            title=f"Trending: {topic}",
                            description=f"{topic} is trending with {count} mentions ({len(recent)} in last 2 hours)",
                            confidence=min(len(recent) / 10, 1.0),
                            potential_impact='high' if len(recent) >= 5 else 'medium',
                            action_suggestion=f"Create content about {topic} to capitalize on trend",
                            expires_at=datetime.now() + timedelta(hours=4),
                            metadata={'topic': topic, 'mention_count': count}
                        ))
        
        except Exception as e:
            logger.debug(f"Could not detect trending opportunities: {e}")
        
        return opportunities
    
    def detect_engagement_opportunities(self) -> List[Opportunity]:
        """
        Find high-engagement posts to interact with.
        
        Returns:
            List of engagement opportunities
        """
        opportunities = []
        
        if not self.world_state:
            return opportunities
        
        try:
            # Get recent posts with high engagement
            events = self.world_state.get_events(limit=100)
            
            for event in events:
                if event.event_type in ['post_seen', 'content_discovered']:
                    engagement = event.metadata.get('engagement', {})
                    likes = engagement.get('likes', 0)
                    replies = engagement.get('replies', 0)
                    
                    # High engagement threshold
                    if likes >= 10 or replies >= 5:
                        post_id = event.metadata.get('post_id')
                        author = event.metadata.get('author', 'someone')
                        
                        opportunities.append(Opportunity(
                            opportunity_type='engagement',
                            title=f"High engagement post by {author}",
                            description=f"Post has {likes} likes and {replies} replies - good opportunity to engage",
                            confidence=0.8,
                            potential_impact='medium',
                            action_suggestion=f"Reply with thoughtful comment to engage with {author}",
                            expires_at=datetime.now() + timedelta(hours=6),
                            metadata={'post_id': post_id, 'author': author}
                        ))
        
        except Exception as e:
            logger.debug(f"Could not detect engagement opportunities: {e}")
        
        return opportunities
    
    def detect_mention_opportunities(self) -> List[Opportunity]:
        """
        Find mentions that need response.
        
        Returns:
            List of mention opportunities
        """
        opportunities = []
        
        if not self.world_state:
            return opportunities
        
        try:
            # Get recent events
            events = self.world_state.get_events(limit=100)
            
            for event in events:
                # Check for mentions
                if 'mention' in event.event_type.lower():
                    author = event.metadata.get('author', 'someone')
                    content = event.metadata.get('content', '')
                    
                    opportunities.append(Opportunity(
                        opportunity_type='mention',
                        title=f"Mentioned by {author}",
                        description=f"{author} mentioned you: {content[:100]}",
                        confidence=1.0,
                        potential_impact='high',
                        action_suggestion=f"Respond to {author}'s mention",
                        expires_at=datetime.now() + timedelta(hours=12),
                        metadata={'author': author, 'content': content}
                    ))
        
        except Exception as e:
            logger.debug(f"Could not detect mention opportunities: {e}")
        
        return opportunities
    
    def detect_collaboration_opportunities(self) -> List[Opportunity]:
        """
        Find potential collaboration opportunities.
        
        Returns:
            List of collaboration opportunities
        """
        opportunities = []
        
        if not self.world_state:
            return opportunities
        
        try:
            # Get recent interactions
            events = self.world_state.get_events(limit=200)
            
            # Track repeated interactions
            interaction_counts = defaultdict(int)
            
            for event in events:
                if event.event_type in ['reply_sent', 'engagement']:
                    target = event.metadata.get('target_user')
                    if target:
                        interaction_counts[target] += 1
            
            # Find users with multiple interactions
            for user, count in interaction_counts.items():
                if count >= 3:  # Multiple interactions
                    opportunities.append(Opportunity(
                        opportunity_type='collaboration',
                        title=f"Potential collaboration with {user}",
                        description=f"You've interacted with {user} {count} times - might be worth reaching out for collaboration",
                        confidence=0.6,
                        potential_impact='medium',
                        action_suggestion=f"Send DM to {user} to explore collaboration",
                        metadata={'user': user, 'interaction_count': count}
                    ))
        
        except Exception as e:
            logger.debug(f"Could not detect collaboration opportunities: {e}")
        
        return opportunities
    
    def detect_timing_opportunities(self) -> List[Opportunity]:
        """
        Find optimal timing windows.
        
        Returns:
            List of timing opportunities
        """
        opportunities = []
        
        if not self.adaptive_timing:
            return opportunities
        
        try:
            # Check if now is optimal time for posting
            timing = self.adaptive_timing.get_optimal_timing('create_post', 'moltx')
            
            if timing['should_act_now'] and timing['confidence'] > 0.7:
                opportunities.append(Opportunity(
                    opportunity_type='timing',
                    title="Optimal posting window",
                    description=f"Now is a good time to post (confidence: {timing['confidence']:.0%})",
                    confidence=timing['confidence'],
                    potential_impact='medium',
                    action_suggestion="Create and post content now for maximum engagement",
                    expires_at=datetime.now() + timedelta(hours=1),
                    metadata=timing
                ))
        
        except Exception as e:
            logger.debug(f"Could not detect timing opportunities: {e}")
        
        return opportunities
    
    def get_top_opportunities(self, limit: int = 5) -> List[Opportunity]:
        """
        Get top opportunities by impact and confidence.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            Top opportunities
        """
        all_opportunities = self.detect_opportunities()
        return all_opportunities[:limit]
    
    def get_new_opportunities(self) -> List[Opportunity]:
        """
        Get opportunities that haven't been notified yet.
        
        Returns:
            New opportunities
        """
        all_opportunities = self.detect_opportunities()
        
        new_opportunities = []
        for opp in all_opportunities:
            # Create unique ID for opportunity
            opp_id = f"{opp.opportunity_type}:{opp.title}"
            
            if opp_id not in self.notified_opportunities:
                new_opportunities.append(opp)
                self.notified_opportunities.add(opp_id)
        
        return new_opportunities
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text"""
        topics = []
        text_lower = text.lower()
        
        # Common topics
        topic_keywords = {
            'defi': ['defi', 'yield', 'farming', 'lending'],
            'nft': ['nft', 'nfts', 'collectible'],
            'ai': ['ai', 'artificial intelligence', 'agent', 'bot'],
            'crypto': ['crypto', 'bitcoin', 'ethereum'],
            'trading': ['trade', 'trading', 'buy', 'sell']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def get_opportunity_summary(self) -> str:
        """Get human-readable opportunity summary"""
        opportunities = self.detect_opportunities()
        
        if not opportunities:
            return "🔍 No opportunities detected at this time."
        
        lines = [f"🎯 {len(opportunities)} Opportunities Detected:"]
        
        for i, opp in enumerate(opportunities[:5], 1):
            impact_emoji = {'high': '🔥', 'medium': '⚡', 'low': '💡'}.get(opp.potential_impact, '•')
            lines.append(f"{i}. {impact_emoji} {opp.title} ({opp.confidence:.0%} confidence)")
            lines.append(f"   → {opp.action_suggestion}")
        
        return "\n".join(lines)


def create_opportunity_detector(world_state=None,
                                content_intelligence=None,
                                adaptive_timing=None):
    """Factory function to create opportunity detector"""
    return OpportunityDetector(world_state, content_intelligence, adaptive_timing)
