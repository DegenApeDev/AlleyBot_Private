"""
MoltNews Brain Integration
Connects MoltNews trending feed to AlleyBot's brain for content awareness
"""
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class MoltNewsBrain:
    """Integrates MoltNews with AlleyBot's brain for trending awareness"""
    
    def __init__(self, moltnews_plugin=None):
        self.plugin = moltnews_plugin
        self.last_fetch = None
        self.cached_news = []
        self.cache_ttl = 300  # 5 minutes
        
    def get_trending_topics(self, limit: int = 5) -> List[str]:
        """
        Extract trending topics from MoltNews for brain consideration
        Returns list of trending topics/hashtags
        """
        posts = self._get_cached_or_fetch(limit)
        
        topics = []
        for post in posts:
            # Extract hashtags
            content = post.get('content', '')
            hashtags = [word for word in content.split() if word.startswith('#')]
            topics.extend(hashtags)
            
            # Extract keywords from title
            title = post.get('title', '')
            if title:
                topics.append(title)
        
        # Deduplicate and return top topics
        seen = set()
        unique_topics = []
        for topic in topics:
            if topic.lower() not in seen:
                seen.add(topic.lower())
                unique_topics.append(topic)
        
        return unique_topics[:limit]
    
    def get_news_summary(self, limit: int = 3) -> str:
        """
        Get a summary of current trending news for content generation context
        Returns formatted summary string
        """
        posts = self._get_cached_or_fetch(limit)
        
        if not posts:
            return "No trending news available at the moment."
        
        summaries = []
        for post in posts:
            title = post.get('title', 'Untitled')
            content = post.get('content', '')[:200]  # First 200 chars
            author = post.get('author', 'Unknown')
            
            summary = f"• {title} (by {author}): {content}..."
            summaries.append(summary)
        
        return "\n".join(summaries)
    
    def should_engage_with_topic(self, topic: str) -> bool:
        """
        Check if a topic is currently trending on MoltNews
        Used by brain to decide whether to create content about a topic
        """
        trending = self.get_trending_topics(limit=20)
        topic_lower = topic.lower()
        
        for trending_topic in trending:
            if topic_lower in trending_topic.lower() or trending_topic.lower() in topic_lower:
                return True
        
        return False
    
    def get_engagement_opportunities(self) -> List[Dict]:
        """
        Find posts that AlleyBot could reply to or repost
        Returns list of post objects with engagement recommendations
        """
        posts = self._get_cached_or_fetch(10)
        opportunities = []
        
        for post in posts:
            opportunity = {
                "post_id": post.get('id'),
                "title": post.get('title', 'Untitled'),
                "content_preview": post.get('content', '')[:100],
                "author": post.get('author', 'Unknown'),
                "reply_count": post.get('reply_count', 0),
                "like_count": post.get('like_count', 0),
                "recommendation": self._generate_recommendation(post)
            }
            opportunities.append(opportunity)
        
        return opportunities
    
    def _generate_recommendation(self, post: Dict) -> str:
        """Generate engagement recommendation for a post"""
        reply_count = post.get('reply_count', 0)
        like_count = post.get('like_count', 0)
        content = post.get('content', '')
        
        # Low engagement posts = good reply opportunity
        if reply_count < 3:
            return "reply"
        
        # High quality content = repost worthy
        if like_count > 10 and len(content) > 100:
            return "repost"
        
        # Default = just monitor
        return "monitor"
    
    def _get_cached_or_fetch(self, limit: int) -> List[Dict]:
        """Get news from cache or fetch fresh"""
        now = datetime.utcnow()
        
        # Check if cache is still valid
        if (self.last_fetch and 
            self.cached_news and 
            (now - self.last_fetch).seconds < self.cache_ttl):
            return self.cached_news[:limit]
        
        # Fetch fresh data
        if self.plugin:
            posts = self.plugin.fetch_trending(limit=limit)
            self.cached_news = posts
            self.last_fetch = now
            return posts
        
        return []
    
    def get_content_suggestion(self) -> Optional[str]:
        """
        Suggest content based on trending news
        Returns a content suggestion string or None
        """
        topics = self.get_trending_topics(limit=3)
        
        if not topics:
            return None
        
        # Generate a suggestion based on trending topics
        suggestion = f"Consider creating content about: {', '.join(topics[:3])}"
        return suggestion
    
    def format_for_moltx(self, post: Dict) -> str:
        """
        Format a MoltNews post for cross-posting to Moltx
        """
        title = post.get('title', '')
        content = post.get('content', '')
        url = post.get('url', '')
        
        # Create Moltx-friendly format
        if url:
            return f"📰 {title}\n\n{content[:200]}...\n\nSource: {url} via @MoltNews"
        else:
            return f"📰 {title}\n\n{content[:200]}...\n\nvia @MoltNews"
