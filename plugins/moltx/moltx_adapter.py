"""
Moltx Adapter for World State

Integrates Moltx with AlleyBot's unified World State.
"""
from typing import List, Optional
from datetime import datetime
import re

from src.autonomy.platform_adapter import (
    PlatformAdapter, 
    PlatformEntity, 
    PlatformInteraction,
    PlatformRelationship
)


class MoltxAdapter(PlatformAdapter):
    """
    Moltx platform adapter.
    
    Implements standardized interface for ingesting Moltx data
    into World State.
    """
    
    def __init__(self, moltx_plugin):
        """Initialize with Moltx plugin instance"""
        self.plugin = moltx_plugin
    
    def get_platform_name(self) -> str:
        """Return platform identifier"""
        return "moltx"
    
    def is_available(self) -> bool:
        """Check if Moltx is connected"""
        return (
            self.plugin is not None and 
            getattr(self.plugin, 'initialized', False)
        )
    
    def fetch_recent_interactions(self, limit: int = 50, since: Optional[str] = None) -> List[PlatformInteraction]:
        """Fetch recent posts from Moltx"""
        interactions = []
        
        try:
            # Fetch global feed
            feed_result = self.plugin.get_feed(feed_type='global', limit=limit)
            posts = []
            
            if isinstance(feed_result, dict):
                posts = feed_result.get('posts') or feed_result.get('data', {}).get('posts', [])
            elif isinstance(feed_result, list):
                posts = feed_result
            
            # Convert posts to interactions
            for post in posts:
                interaction = self._convert_post_to_interaction(post)
                if interaction:
                    interactions.append(interaction)
                    
        except Exception as e:
            print(f"⚠️ MoltxAdapter fetch failed: {e}")
        
        return interactions
    
    def fetch_entities(self, entity_type: Optional[str] = None, limit: int = 50) -> List[PlatformEntity]:
        """Fetch entities from Moltx"""
        entities = []
        
        try:
            # Fetch posts as entities
            if entity_type is None or entity_type == 'post':
                feed_result = self.plugin.get_feed(feed_type='global', limit=limit)
                posts = []
                
                if isinstance(feed_result, dict):
                    posts = feed_result.get('posts') or feed_result.get('data', {}).get('posts', [])
                elif isinstance(feed_result, list):
                    posts = feed_result
                
                for post in posts:
                    entity = self._convert_post_to_entity(post)
                    if entity:
                        entities.append(entity)
            
            # Fetch agents
            if entity_type is None or entity_type == 'agent':
                # Try to get trending/following feed for agents
                feed_result = self.plugin.get_feed(feed_type='following', limit=limit)
                posts = []
                
                if isinstance(feed_result, dict):
                    posts = feed_result.get('posts') or feed_result.get('data', {}).get('posts', [])
                elif isinstance(feed_result, list):
                    posts = feed_result
                
                # Extract unique authors
                seen_authors = set()
                for post in posts:
                    author = post.get('agent_name') or post.get('author_name')
                    if author and author not in seen_authors:
                        seen_authors.add(author)
                        entity = self._convert_author_to_entity(post)
                        if entity:
                            entities.append(entity)
                            
        except Exception as e:
            print(f"⚠️ MoltxAdapter fetch_entities failed: {e}")
        
        return entities
    
    def fetch_relationships(self, entity_id: Optional[str] = None, limit: int = 100) -> List[PlatformRelationship]:
        """Fetch relationships from Moltx"""
        relationships = []
        
        # Moltx doesn't expose follows directly in API
        # Relationships inferred from mentions/replies in feed
        try:
            feed_result = self.plugin.get_feed(feed_type='mentions', limit=limit)
            posts = []
            
            if isinstance(feed_result, dict):
                posts = feed_result.get('posts') or feed_result.get('data', {}).get('posts', [])
            elif isinstance(feed_result, list):
                posts = feed_result
            
            for post in posts:
                author = post.get('agent_name') or post.get('author_name') or 'unknown'
                mentions = self._extract_mentions(post.get('content', ''))
                
                for mention in mentions:
                    rel = PlatformRelationship(
                        from_entity=f"moltx_{author.lstrip('@')}",
                        to_entity=f"moltx_{mention}",
                        relation_type='mentioned',
                        platform='moltx',
                        strength=0.5,
                        timestamp=post.get('created_at')
                    )
                    relationships.append(rel)
                    
        except Exception as e:
            print(f"⚠️ MoltxAdapter fetch_relationships failed: {e}")
        
        return relationships
    
    def _convert_post_to_interaction(self, post: dict) -> Optional[PlatformInteraction]:
        """Convert Moltx post to standardized interaction"""
        try:
            post_id = post.get('id') or post.get('post_id')
            author = post.get('agent_name') or post.get('author_name') or 'unknown'
            content = post.get('content') or post.get('text') or ''
            
            if not post_id:
                return None
            
            return PlatformInteraction(
                id=f"moltx_{post_id}",
                type='post',
                platform='moltx',
                actor_id=author.lstrip('@'),
                content=content,
                timestamp=post.get('created_at') or datetime.now().isoformat(),
                engagement_metrics={
                    'likes': post.get('likes_count', 0) or post.get('like_count', 0),
                    'replies': post.get('replies_count', 0) or post.get('reply_count', 0),
                    'views': post.get('views_count', 0) or post.get('views', 0)
                },
                hashtags=self._extract_hashtags(content),
                mentions=self._extract_mentions(content)
            )
        except Exception as e:
            print(f"⚠️ Failed to convert Moltx post: {e}")
            return None
    
    def _convert_post_to_entity(self, post: dict) -> Optional[PlatformEntity]:
        """Convert Moltx post to entity"""
        try:
            post_id = post.get('id') or post.get('post_id')
            author = post.get('agent_name') or post.get('author_name') or 'unknown'
            content = post.get('content') or ''
            
            if not post_id:
                return None
            
            return PlatformEntity(
                id=f"moltx_post_{post_id}",
                type='post',
                platform='moltx',
                name=f"Post {str(post_id)[:8]}",
                display_name=f"@{author}'s post",
                attributes={
                    'author': author,
                    'content_preview': content[:100] if content else '',
                    'likes': post.get('likes_count', 0) or post.get('like_count', 0),
                    'replies': post.get('replies_count', 0) or post.get('reply_count', 0)
                },
                created_at=post.get('created_at'),
                url=f"https://moltx.io/post/{post_id}"
            )
        except Exception as e:
            print(f"⚠️ Failed to convert Moltx post to entity: {e}")
            return None
    
    def _convert_author_to_entity(self, post: dict) -> Optional[PlatformEntity]:
        """Extract author from post as entity"""
        try:
            author = post.get('agent_name') or post.get('author_name') or post.get('username')
            if not author:
                return None
            
            return PlatformEntity(
                id=f"moltx_{author.lstrip('@')}",
                type='agent',
                platform='moltx',
                name=author.lstrip('@'),
                display_name=author,
                attributes={
                    'platform': 'moltx',
                    'observed_in_post': post.get('id')
                },
                created_at=post.get('created_at')
            )
        except Exception as e:
            print(f"⚠️ Failed to convert Moltx author: {e}")
            return None
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract #hashtags from content"""
        return re.findall(r'#(\w+)', content or '')
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from content"""
        return re.findall(r'@(\w+)', content or '')
