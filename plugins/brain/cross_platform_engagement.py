"""
Cross-Platform Engagement Mixin for AlleyBot Brain

Implements the 5:1 engagement rule across all platforms:
- Reply to 5 posts with AI-generated contextual replies
- Like 10 posts
- Follow 2-3 agents

Connected to brain for autonomous decision-making.
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime


class CrossPlatformEngagementMixin:
    """Handles 5:1 engagement rule across all social platforms"""
    
    def __init__(self, *args, **kwargs):
        """Initialize mixin - accepts args/kwargs for MRO compatibility with BrainPlugin"""
        # Don't call super().__init__ to avoid MRO issues with AlleyBotPlugin
        # Just initialize our own attributes
        self.engagement_stats = {
            'moltx': {'replies': 0, 'likes': 0, 'follows': 0, 'last_engagement': None},
            'moltbook': {'replies': 0, 'likes': 0, 'follows': 0, 'last_engagement': None},
            'moltchan': {'replies': 0, 'likes': 0, 'follows': 0, 'last_engagement': None},
        }
        self.platform_priorities = ['moltx', 'moltbook', 'moltchan']
    
    async def should_engagement_before_post(self, platform: str) -> bool:
        """Check if engagement is needed before posting (5:1 rule)"""
        stats = self.engagement_stats.get(platform, {})
        
        # Check if we've done 5:1 engagement recently (within last hour)
        last_engagement = stats.get('last_engagement')
        if last_engagement:
            elapsed = (datetime.now() - last_engagement).total_seconds() / 3600
            if elapsed < 1:  # Engaged within last hour
                return False
        
        # Check 5:1 ratios
        replies = stats.get('replies', 0)
        likes = stats.get('likes', 0)
        follows = stats.get('follows', 0)
        
        # Need: 5 replies, 10 likes, 2 follows minimum
        return replies < 5 or likes < 10 or follows < 2
    
    async def run_preflight_engagement(self, platform: str, plugin: Any, 
                                        update: Any = None) -> Dict[str, int]:
        """
        Run 5:1 engagement protocol before posting
        
        Args:
            platform: Platform name (moltx, moltbook, moltchan)
            plugin: The platform plugin instance
            update: Optional Telegram update for status messages
            
        Returns:
            Dict with engagement stats (replies, likes, follows)
        """
        results = {'replies': 0, 'likes': 0, 'follows': 0, 'platform': platform}
        
        try:
            # Get feed based on platform
            feed = await self._get_platform_feed(platform, plugin)
            if not feed:
                print(f"⚠️ No feed available for {platform}")
                return results
            
            print(f"📊 Running 5:1 engagement on {platform} ({len(feed)} posts)")
            
            # 1. Like 10 posts
            results['likes'] = await self._bulk_like(feed[:15], plugin, platform)
            
            # 2. Reply to 5 posts with AI-generated contextual replies
            results['replies'] = await self._bulk_reply_with_ai(
                feed[15:25], plugin, platform
            )
            
            # 3. Follow 2-3 interesting agents
            results['follows'] = await self._bulk_follow(feed[:20], plugin, platform)
            
            # Update stats
            self.engagement_stats[platform]['replies'] += results['replies']
            self.engagement_stats[platform]['likes'] += results['likes']
            self.engagement_stats[platform]['follows'] += results['follows']
            self.engagement_stats[platform]['last_engagement'] = datetime.now()
            
            print(f"✅ 5:1 Engagement complete on {platform}: {results}")
            
            # Report to Telegram if update provided
            if update and hasattr(update, 'message'):
                await update.message.reply_text(
                    f"✅ 5:1 Engagement ({platform}): {results['likes']} likes, "
                    f"{results['replies']} replies, {results['follows']} follows"
                )
            
        except Exception as e:
            print(f"⚠️ Engagement error on {platform}: {e}")
            # Non-blocking - continue even if engagement fails
        
        return results
    
    async def _get_platform_feed(self, platform: str, plugin: Any) -> List[Dict]:
        """Get feed from any platform plugin"""
        feed = []
        
        try:
            if platform == 'moltx':
                # Moltx feed
                if hasattr(plugin, '_make_request'):
                    result = plugin._make_request(
                        'GET', '/feed/global', 
                        params={'type': 'post,quote', 'limit': 30}
                    )
                    if result:
                        if 'posts' in result:
                            feed = result['posts']
                        elif 'data' in result and 'posts' in result['data']:
                            feed = result['data']['posts']
                        elif isinstance(result, list):
                            feed = result
                            
            elif platform == 'moltbook':
                # Moltbook feed
                if hasattr(plugin, 'get_feed'):
                    result = plugin.get_feed(limit=30)
                    if isinstance(result, list):
                        feed = result
                    elif isinstance(result, dict):
                        feed = result.get('posts', result.get('data', []))
                        
            elif platform == 'moltchan':
                # Moltchan threads
                if hasattr(plugin, 'get_threads'):
                    result = plugin.get_threads(limit=30)
                    if isinstance(result, list):
                        feed = [{'id': t.get('id'), 'content': t.get('title', t.get('content')), 
                                'agent_name': t.get('author')} for t in result]
        except Exception as e:
            print(f"⚠️ Feed fetch error on {platform}: {e}")
        
        return feed
    
    async def _bulk_like(self, posts: List[Dict], plugin: Any, platform: str) -> int:
        """Like posts in bulk"""
        liked = 0
        
        for post in posts:
            if liked >= 10:
                break
            try:
                post_id = post.get('id') or post.get('post_id')
                if not post_id:
                    continue
                
                # Platform-specific like method
                result = None
                if platform == 'moltx' and hasattr(plugin, 'like_post'):
                    result = plugin.like_post(post_id)
                elif platform == 'moltbook' and hasattr(plugin, 'like_post'):
                    result = plugin.like_post(post_id)
                elif platform == 'moltchan' and hasattr(plugin, 'upvote_thread'):
                    result = plugin.upvote_thread(post_id)
                
                if result and ('✅' in str(result) or 'success' in str(result).lower()):
                    liked += 1
                    print(f"❤️  Liked on {platform}: {post_id[:16]}... ({liked}/10)")
                
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"⚠️ Like failed on {platform}: {e}")
                continue
        
        return liked
    
    async def _bulk_reply_with_ai(self, posts: List[Dict], plugin: Any, 
                                   platform: str) -> int:
        """Reply to posts with AI-generated contextual replies using DeepSeek"""
        replied = 0
        
        # Initialize DeepSeek
        from deepseek_ai import deepseek_ai
        
        for post in posts:
            if replied >= 5:
                break
            try:
                post_id = post.get('id') or post.get('post_id')
                author = (post.get('agent_name') or post.get('author_name') 
                         or post.get('username') or 'agent')
                post_content = post.get('content', '') or post.get('text', '')
                
                if not post_id or not post_content:
                    continue
                
                # Generate contextual reply using DeepSeek directly
                reply_prompt = f"""You're AlleyBot replying to a post on {platform}.

Original post by @{author}: "{post_content[:200]}"

CRITICAL: This is reply #{replied+1} of 5. Each reply MUST be completely different.

Reply requirements:
1. React to something SPECIFIC from their post
2. NEVER use generic phrases like "Interesting perspective!" or "Building on this"
3. Vary your opening: "Wait...", "Actually...", "What if...", "Hold up..."
4. Add unique value - challenge, add insight, or ask sharp question
5. Keep it 1-2 sentences, conversational

Generate ONLY the reply (no @ mentions, no explanations):"""
                
                # Use DeepSeek for contextual generation
                reply_text = deepseek_ai.generate_text(reply_prompt, max_tokens=150)
                reply_text = reply_text.strip().strip('"').strip("'")
                
                # Platform-specific reply method
                result = None
                if platform == 'moltx' and hasattr(plugin, 'reply_to_post'):
                    result = plugin.reply_to_post(post_id, f"@{author} {reply_text}")
                elif platform == 'moltbook' and hasattr(plugin, 'add_comment'):
                    result = plugin.add_comment(post_id, f"@{author} {reply_text}")
                elif platform == 'moltchan' and hasattr(plugin, 'reply_to_thread'):
                    result = plugin.reply_to_thread(post_id, reply_text)
                
                if result and ('✅' in str(result) or 'success' in str(result).lower()):
                    replied += 1
                    print(f"💬 Replied on {platform} (DeepSeek): {reply_text[:60]}... ({replied}/5)")
                
                await asyncio.sleep(1.5)  # Rate limit
                
            except Exception as e:
                print(f"⚠️ Reply failed on {platform}: {e}")
                continue
        
        return replied
    
    async def _bulk_follow(self, posts: List[Dict], plugin: Any, platform: str) -> int:
        """Follow interesting agents in bulk"""
        followed = 0
        
        for post in posts:
            if followed >= 3:
                break
            try:
                author = (post.get('agent_name') or post.get('author_name') 
                         or post.get('username'))
                if not author:
                    continue
                
                # Platform-specific follow method
                result = None
                if platform == 'moltx' and hasattr(plugin, 'follow_agent'):
                    result = plugin.follow_agent(author)
                elif platform == 'moltbook' and hasattr(plugin, 'follow_user'):
                    result = plugin.follow_user(author)
                elif platform == 'moltchan' and hasattr(plugin, 'follow_thread'):
                    result = plugin.follow_thread(author)
                
                if result and ('✅' in str(result) or 'success' in str(result).lower()):
                    followed += 1
                    print(f"👥 Followed on {platform}: {author} ({followed}/3)")
                
                await asyncio.sleep(0.5)
            except Exception as e:
                continue
        
        return followed
    
    def get_engagement_summary(self) -> Dict[str, Any]:
        """Get engagement stats for all platforms"""
        return {
            'platforms': self.engagement_stats,
            'total_replies': sum(s.get('replies', 0) for s in self.engagement_stats.values()),
            'total_likes': sum(s.get('likes', 0) for s in self.engagement_stats.values()),
            'total_follows': sum(s.get('follows', 0) for s in self.engagement_stats.values()),
        }
