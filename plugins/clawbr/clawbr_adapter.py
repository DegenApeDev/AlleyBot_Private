"""
Clawbr Adapter for World State

Integrates Clawbr with AlleyBot's unified World State.
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


class ClawbrAdapter(PlatformAdapter):
    """
    Clawbr platform adapter.
    
    Implements standardized interface for ingesting Clawbr data
    into World State.
    """
    
    def __init__(self, clawbr_plugin):
        """Initialize with Clawbr plugin instance"""
        self.plugin = clawbr_plugin
    
    def get_platform_name(self) -> str:
        """Return platform identifier"""
        return "clawbr"
    
    def is_available(self) -> bool:
        """Check if Clawbr is connected"""
        return (
            self.plugin is not None and 
            getattr(self.plugin, 'api_key', None) is not None
        )
    
    def fetch_recent_interactions(self, limit: int = 50, since: Optional[str] = None) -> List[PlatformInteraction]:
        """Fetch recent posts, debates from Clawbr"""
        interactions = []
        
        try:
            # Fetch global feed
            feed_result = self.plugin.get_global_feed(limit=limit)
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
            
            # Fetch debates
            try:
                debates_result = self.plugin.get_debates_hub()
                if isinstance(debates_result, dict):
                    debates = debates_result.get('debates') or debates_result.get('data', {}).get('debates', [])
                    for debate in debates:
                        interaction = self._convert_debate_to_interaction(debate)
                        if interaction:
                            interactions.append(interaction)
            except Exception as e:
                print(f"⚠️ ClawbrAdapter debates fetch failed: {e}")
                    
        except Exception as e:
            print(f"⚠️ ClawbrAdapter fetch failed: {e}")
        
        return interactions
    
    def fetch_entities(self, entity_type: Optional[str] = None, limit: int = 50) -> List[PlatformEntity]:
        """Fetch entities from Clawbr"""
        entities = []
        
        try:
            # Fetch posts as entities
            if entity_type is None or entity_type == 'post':
                feed_result = self.plugin.get_global_feed(limit=limit)
                posts = []
                
                if isinstance(feed_result, dict):
                    posts = feed_result.get('posts') or feed_result.get('data', {}).get('posts', [])
                elif isinstance(feed_result, list):
                    posts = feed_result
                
                for post in posts:
                    entity = self._convert_post_to_entity(post)
                    if entity:
                        entities.append(entity)
            
            # Fetch debates as entities
            if entity_type is None or entity_type == 'debate':
                try:
                    debates_result = self.plugin.get_debates_hub()
                    if isinstance(debates_result, dict):
                        debates = debates_result.get('debates') or debates_result.get('data', {}).get('debates', [])
                        for debate in debates:
                            entity = self._convert_debate_to_entity(debate)
                            if entity:
                                entities.append(entity)
                except Exception as e:
                    print(f"⚠️ ClawbrAdapter debates fetch failed: {e}")
            
            # Fetch agents from feed
            if entity_type is None or entity_type == 'agent':
                feed_result = self.plugin.get_global_feed(limit=limit)
                posts = []
                
                if isinstance(feed_result, dict):
                    posts = feed_result.get('posts') or feed_result.get('data', {}).get('posts', [])
                elif isinstance(feed_result, list):
                    posts = feed_result
                
                # Extract unique authors
                seen_authors = set()
                for post in posts:
                    author = post.get('agent', {}).get('name') or post.get('agentName')
                    if author and author not in seen_authors:
                        seen_authors.add(author)
                        entity = self._convert_author_to_entity(post)
                        if entity:
                            entities.append(entity)
                            
        except Exception as e:
            print(f"⚠️ ClawbrAdapter fetch_entities failed: {e}")
        
        return entities
    
    def fetch_relationships(self, entity_id: Optional[str] = None, limit: int = 100) -> List[PlatformRelationship]:
        """Fetch relationships from Clawbr"""
        relationships = []
        
        # Clawbr relationships: follows, debate participation
        try:
            # Get debates to find participants
            debates_result = self.plugin.get_debates_hub()
            if isinstance(debates_result, dict):
                debates = debates_result.get('debates') or debates_result.get('data', {}).get('debates', [])
                
                for debate in debates:
                    # Challenger vs Opponent = debated_with relationship
                    challenger = debate.get('challenger', {}).get('name')
                    opponent = debate.get('opponent', {}).get('name')
                    
                    if challenger and opponent:
                        rel = PlatformRelationship(
                            from_entity=f"clawbr_{challenger}",
                            to_entity=f"clawbr_{opponent}",
                            relation_type='debated_with',
                            platform='clawbr',
                            strength=0.8,
                            timestamp=debate.get('createdAt') or debate.get('created_at')
                        )
                        relationships.append(rel)
                    
                    # Voters show support relationship
                    votes = debate.get('votes', [])
                    for vote in votes:
                        voter = vote.get('voter', {}).get('name')
                        if voter:
                            rel = PlatformRelationship(
                                from_entity=f"clawbr_{voter}",
                                to_entity=f"clawbr_{challenger if vote.get('side') == 'challenger' else opponent}",
                                relation_type='voted_for',
                                platform='clawbr',
                                strength=0.6,
                                timestamp=vote.get('createdAt')
                            )
                            relationships.append(rel)
                            
        except Exception as e:
            print(f"⚠️ ClawbrAdapter fetch_relationships failed: {e}")
        
        return relationships
    
    def _convert_post_to_interaction(self, post: dict) -> Optional[PlatformInteraction]:
        """Convert Clawbr post to standardized interaction"""
        try:
            post_id = post.get('id')
            agent = post.get('agent', {})
            author = agent.get('name') or post.get('agentName') or 'unknown'
            content = post.get('content') or ''
            
            if not post_id:
                return None
            
            return PlatformInteraction(
                id=f"clawbr_{post_id}",
                type='post',
                platform='clawbr',
                actor_id=author,
                content=content,
                timestamp=post.get('createdAt') or post.get('created_at') or datetime.now().isoformat(),
                engagement_metrics={
                    'likes': post.get('likesCount', 0) or post.get('likes_count', 0),
                    'replies': post.get('repliesCount', 0) or post.get('replies_count', 0),
                    'intent': post.get('intent', 'statement')  # Clawbr-specific
                },
                hashtags=self._extract_hashtags(content),
                mentions=self._extract_mentions(content)
            )
        except Exception as e:
            print(f"⚠️ Failed to convert Clawbr post: {e}")
            return None
    
    def _convert_debate_to_interaction(self, debate: dict) -> Optional[PlatformInteraction]:
        """Convert Clawbr debate to interaction"""
        try:
            debate_id = debate.get('id') or debate.get('slug')
            challenger = debate.get('challenger', {}).get('name') or 'unknown'
            topic = debate.get('topic') or debate.get('title', '')
            
            if not debate_id:
                return None
            
            return PlatformInteraction(
                id=f"clawbr_debate_{debate_id}",
                type='debate',
                platform='clawbr',
                actor_id=challenger,
                content=topic,
                timestamp=debate.get('createdAt') or debate.get('created_at') or datetime.now().isoformat(),
                engagement_metrics={
                    'max_posts': debate.get('maxPosts', 5),
                    'current_posts': len(debate.get('posts', [])),
                    'status': debate.get('status', 'open')
                }
            )
        except Exception as e:
            print(f"⚠️ Failed to convert Clawbr debate: {e}")
            return None
    
    def _convert_post_to_entity(self, post: dict) -> Optional[PlatformEntity]:
        """Convert Clawbr post to entity"""
        try:
            post_id = post.get('id')
            agent = post.get('agent', {})
            author = agent.get('name') or post.get('agentName') or 'unknown'
            content = post.get('content') or ''
            
            if not post_id:
                return None
            
            return PlatformEntity(
                id=f"clawbr_post_{post_id}",
                type='post',
                platform='clawbr',
                name=f"Post {str(post_id)[:8]}",
                display_name=f"@{author}'s post",
                attributes={
                    'author': author,
                    'author_display': agent.get('displayName'),
                    'content_preview': content[:100] if content else '',
                    'likes': post.get('likesCount', 0) or post.get('likes_count', 0),
                    'replies': post.get('repliesCount', 0) or post.get('replies_count', 0),
                    'intent': post.get('intent', 'statement')
                },
                created_at=post.get('createdAt') or post.get('created_at'),
                url=f"https://clawbr.org/post/{post_id}"
            )
        except Exception as e:
            print(f"⚠️ Failed to convert Clawbr post to entity: {e}")
            return None
    
    def _convert_debate_to_entity(self, debate: dict) -> Optional[PlatformEntity]:
        """Convert Clawbr debate to entity"""
        try:
            debate_id = debate.get('id') or debate.get('slug')
            if not debate_id:
                return None
            
            challenger = debate.get('challenger', {}).get('name') or 'unknown'
            opponent = debate.get('opponent', {}).get('name')
            topic = debate.get('topic') or debate.get('title', '')
            
            return PlatformEntity(
                id=f"clawbr_debate_{debate_id}",
                type='debate',
                platform='clawbr',
                name=topic[:50] if topic else f"Debate {str(debate_id)[:8]}",
                display_name=f"{challenger} vs {opponent}" if opponent else f"{challenger}'s debate",
                attributes={
                    'challenger': challenger,
                    'opponent': opponent,
                    'status': debate.get('status', 'open'),
                    'max_posts': debate.get('maxPosts', 5),
                    'current_posts': len(debate.get('posts', [])),
                    'winner': debate.get('winner')
                },
                created_at=debate.get('createdAt') or debate.get('created_at'),
                url=f"https://clawbr.org/debate/{debate_id}"
            )
        except Exception as e:
            print(f"⚠️ Failed to convert Clawbr debate to entity: {e}")
            return None
    
    def _convert_author_to_entity(self, post: dict) -> Optional[PlatformEntity]:
        """Extract author from post as entity"""
        try:
            agent = post.get('agent', {})
            author = agent.get('name') or post.get('agentName')
            if not author:
                return None
            
            return PlatformEntity(
                id=f"clawbr_{author}",
                type='agent',
                platform='clawbr',
                name=author,
                display_name=agent.get('displayName') or author,
                attributes={
                    'platform': 'clawbr',
                    'faction': agent.get('faction'),
                    'influence_score': agent.get('influenceScore'),
                    'follower_count': agent.get('followerCount'),
                    'elo': agent.get('elo')
                },
                created_at=post.get('createdAt') or post.get('created_at')
            )
        except Exception as e:
            print(f"⚠️ Failed to convert Clawbr author: {e}")
            return None
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract #hashtags from content"""
        return re.findall(r'#(\w+)', content or '')
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from content"""
        return re.findall(r'@(\w+)', content or '')
