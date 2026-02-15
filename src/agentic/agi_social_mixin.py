"""
AGI Social Intelligence Mixin
Handles advanced AGI-like social behaviors:
- Following users after engagement
- Replying to comments/notifications
- Building relationships through sustained interaction
"""
import asyncio
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AGISocialMixin:
    """Mixin providing AGI-level social intelligence for autonomous brain
    
    Follow Rate Limits (recommended for healthy account growth):
    - Conservative: 3 follows/day per platform (90/month)
    - Normal: 5 follows/day per platform (150/month)  
    - Aggressive: 8 follows/day per platform (240/month)
    
    These limits maintain healthy follower:following ratios and avoid
    appearing spammy to platform algorithms.
    """
    
    # Daily follow limits per platform
    FOLLOW_LIMITS = {
        'conservative': 3,
        'normal': 5,
        'aggressive': 8
    }
    
    def __init__(self, follow_mode: str = 'normal'):
        # Track who we've engaged with for follow decisions
        self._engagement_history: Dict[str, Dict[str, Any]] = {}
        self._followed_users: Set[str] = set()
        self._notification_replies_sent: Set[str] = set()  # Track replied notifications
        self._last_notification_check: Optional[datetime] = None
        
        # Follow rate limiting
        self._follow_mode = follow_mode if follow_mode in self.FOLLOW_LIMITS else 'normal'
        self._follows_today: Dict[str, int] = {}  # Platform -> count
        self._last_follow_date: Optional[datetime] = None
        self._total_follows_all_time: int = 0
    
    async def _process_platform_notifications(self, platform: str, plugin) -> Dict[str, Any]:
        """Process notifications for a platform and reply to comments/mentions"""
        results = {
            'notifications_checked': 0,
            'replies_sent': 0,
            'follows_done': 0,
            'errors': []
        }
        
        # Check if plugin has notification support
        if not hasattr(plugin, 'get_notifications'):
            return results
        
        try:
            # Get notifications - handle different method signatures
            # Clawbr: get_notifications(unread_only=False)
            # Moltx: get_notifications(limit=50, mark_read=False)
            notifs = None
            if hasattr(plugin, 'get_notifications'):
                import inspect
                sig = inspect.signature(plugin.get_notifications)
                params = list(sig.parameters.keys())
                
                if 'unread_only' in params:
                    # Clawbr-style API
                    notifs = plugin.get_notifications(unread_only=True)
                elif 'mark_read' in params:
                    # Moltx-style API
                    notifs = plugin.get_notifications(limit=20, mark_read=False)
                else:
                    # Generic call
                    notifs = plugin.get_notifications()
            
            if not isinstance(notifs, dict):
                return results
            
            notifications = notifs.get('notifications', [])
            results['notifications_checked'] = len(notifications)
            
            for notif in notifications:
                notif_id = notif.get('id', str(hash(str(notif))))
                notif_type = notif.get('type', 'unknown')
                actor = notif.get('actor', notif.get('from_user', {}))
                actor_name = actor.get('name', actor.get('username', 'unknown'))
                
                # Skip if already replied to this notification
                if notif_id in self._notification_replies_sent:
                    continue
                
                # Handle mentions - reply with AI
                if notif_type in ['mention', 'reply', 'comment']:
                    reply_result = await self._reply_to_notification(platform, plugin, notif)
                    if reply_result:
                        results['replies_sent'] += 1
                        self._notification_replies_sent.add(notif_id)
                
                # Handle likes - follow back if auto-follow enabled
                elif notif_type == 'like':
                    follow_result = await self._follow_if_engaged(platform, plugin, actor_name)
                    if follow_result:
                        results['follows_done'] += 1
                
                # Handle follows - follow back (reciprocal)
                elif notif_type == 'follow':
                    follow_result = await self._follow_if_engaged(platform, plugin, actor_name)
                    if follow_result:
                        results['follows_done'] += 1
                        print(f"👥 Auto-followed back: {actor_name} on {platform}")
            
            # Mark notifications as read
            if results['replies_sent'] > 0 or results['follows_done'] > 0:
                if hasattr(plugin, 'mark_notifications_read'):
                    plugin.mark_notifications_read()
        
        except Exception as e:
            logger.error(f"❌ Error processing {platform} notifications: {e}")
            results['errors'].append(str(e))
        
        self._last_notification_check = datetime.now()
        return results
    
    async def _reply_to_notification(self, platform: str, plugin, notification: Dict) -> Optional[str]:
        """Generate and send AI reply to a notification"""
        notif_type = notification.get('type', 'unknown')
        actor = notification.get('actor', notification.get('from_user', {}))
        actor_name = actor.get('name', actor.get('username', 'unknown'))
        
        # Get content to reply to
        content = ""
        post_id = None
        
        if 'post' in notification:
            content = notification['post'].get('content', '')
            post_id = notification['post'].get('id')
        elif 'content' in notification:
            content = notification['content']
        elif 'message' in notification:
            content = notification['message']
        
        # Generate AI reply
        reply_content = None
        try:
            # Try DeepSeek first for comments (cost-effective)
            from deepseek_ai import deepseek_ai
            if deepseek_ai.enabled:
                context = f"Replying to @{actor_name} on {platform}: {content[:200]}"
                reply_content = deepseek_ai.generate_comment(
                    post_content=context,
                    agent_name=actor_name,
                    context=f"{platform} platform - AI agents, crypto, DeFi, community"
                )
        except Exception as e:
            logger.debug(f"DeepSeek reply generation failed: {e}")
        
        # Fallback to Grok
        if not reply_content:
            try:
                from grok_ai import grok_ai
                if grok_ai.enabled:
                    prompt = f"@{actor_name} said: {content[:200]}\n\nWrite a brief, natural reply:"
                    reply_content = grok_ai.generate(prompt, max_tokens=100, temperature=0.7)
            except Exception as e:
                logger.debug(f"Grok reply generation failed: {e}")
        
        if not reply_content:
            # Final fallback
            reply_content = f"Thanks for the {notif_type} @{actor_name}! 🚀"
        
        # Send the reply based on platform
        try:
            if platform == 'moltx' and post_id and hasattr(plugin, 'reply_to_post'):
                result = plugin.reply_to_post(post_id, reply_content)
                if result:
                    print(f"💬 Replied to {notif_type} from {actor_name} on {platform}")
                    return reply_content
                    
            elif platform == 'clawbr':
                # Clawbr has _auto_reply_to_mention
                if hasattr(plugin, '_auto_reply_to_mention') and post_id:
                    plugin._auto_reply_to_mention(post_id, actor_name)
                    print(f"💬 Auto-replied to mention from {actor_name} on Clawbr")
                    return reply_content
                    
            elif platform == 'moltbook' and post_id:
                if hasattr(plugin, 'mb_api') and hasattr(plugin.mb_api, 'add_comment'):
                    result = plugin.mb_api.add_comment(post_id, reply_content)
                    if result:
                        print(f"💬 Replied to comment on Moltbook")
                        return reply_content
        
        except Exception as e:
            logger.error(f"❌ Failed to send reply on {platform}: {e}")
        
        return None
    
    async def _follow_if_engaged(self, platform: str, plugin, username: str) -> bool:
        """Follow a user if we've engaged with them, respecting daily limits"""
        if not username or username == 'unknown':
            return False
        
        # Check if already following
        follow_key = f"{platform}:{username}"
        if follow_key in self._followed_users:
            return False
        
        # Check daily follow limit
        if not self._can_follow_today(platform):
            logger.debug(f"⏸️ Daily follow limit reached for {platform}")
            return False
        
        # Record engagement
        if follow_key not in self._engagement_history:
            self._engagement_history[follow_key] = {
                'first_engagement': datetime.now(),
                'engagement_count': 0,
                'platform': platform,
                'username': username
            }
        
        self._engagement_history[follow_key]['engagement_count'] += 1
        self._engagement_history[follow_key]['last_engagement'] = datetime.now()
        
        # Follow if we have enough engagement (1+ interactions) or it's a reciprocal follow
        engagement_count = self._engagement_history[follow_key]['engagement_count']
        should_follow = engagement_count >= 1
        
        if should_follow:
            try:
                result = False
                
                if platform == 'moltx' and hasattr(plugin, 'follow_agent'):
                    result = plugin.follow_agent(username)
                    
                elif platform == 'clawbr' and hasattr(plugin, 'follow_agent'):
                    result = plugin.follow_agent(username)
                    
                elif platform == 'moltbook' and hasattr(plugin, 'mb_api'):
                    if hasattr(plugin.mb_api, 'follow_user'):
                        result = plugin.mb_api.follow_user(username)
                
                if result:
                    self._followed_users.add(follow_key)
                    self._record_follow(platform)
                    print(f"👥 Followed {username} on {platform} (engagement: {engagement_count}x, daily: {self._follows_today.get(platform, 0)}/{self.FOLLOW_LIMITS[self._follow_mode]})")
                    return True
                    
            except Exception as e:
                logger.error(f"❌ Failed to follow {username} on {platform}: {e}")
        
        return False
    
    def _can_follow_today(self, platform: str) -> bool:
        """Check if we can still follow users today on this platform"""
        # Reset counter if it's a new day
        today = datetime.now().date()
        if self._last_follow_date != today:
            self._follows_today = {}
            self._last_follow_date = today
        
        # Check limit
        limit = self.FOLLOW_LIMITS.get(self._follow_mode, 5)
        current = self._follows_today.get(platform, 0)
        return current < limit
    
    def _record_follow(self, platform: str):
        """Record a follow action for rate limiting"""
        today = datetime.now().date()
        if self._last_follow_date != today:
            self._follows_today = {}
            self._last_follow_date = today
        
        self._follows_today[platform] = self._follows_today.get(platform, 0) + 1
        self._total_follows_all_time += 1
    
    async def _follow_after_debate(self, platform: str, plugin, opponent_name: str):
        """Follow opponent after engaging in a debate"""
        if opponent_name:
            await self._follow_if_engaged(platform, plugin, opponent_name)
            print(f"🎭 Followed debate opponent: {opponent_name} on {platform}")
    
    async def _follow_after_engagement_action(self, platform: str, plugin, target_name: str, action_type: str):
        """Record engagement and potentially follow after an action"""
        if target_name and action_type in ['like', 'reply', 'repost', 'comment', 'upvote']:
            # Check for auto-follow after meaningful engagement
            if action_type in ['reply', 'comment']:  # Higher value engagement
                await self._follow_if_engaged(platform, plugin, target_name)
            else:
                # Just record for later decision
                follow_key = f"{platform}:{target_name}"
                if follow_key not in self._engagement_history:
                    self._engagement_history[follow_key] = {
                        'first_engagement': datetime.now(),
                        'engagement_count': 0,
                        'platform': platform,
                        'username': target_name
                    }
                self._engagement_history[follow_key]['engagement_count'] += 1
                self._engagement_history[follow_key]['last_engagement'] = datetime.now()
    
    def get_social_stats(self) -> Dict[str, Any]:
        """Get statistics on AGI social behaviors"""
        today = datetime.now().date()
        if self._last_follow_date != today:
            follows_today_display = 0
        else:
            follows_today_display = sum(self._follows_today.values())
        
        return {
            'users_engaged': len(self._engagement_history),
            'users_followed': len(self._followed_users),
            'follows_today': follows_today_display,
            'follow_limit_today': self.FOLLOW_LIMITS[self._follow_mode] * 5,  # All platforms
            'follow_mode': self._follow_mode,
            'notification_replies': len(self._notification_replies_sent),
            'last_notification_check': self._last_notification_check.isoformat() if self._last_notification_check else None,
            'engagement_breakdown': {
                platform: sum(1 for k, v in self._engagement_history.items() if v['platform'] == platform)
                for platform in set(v['platform'] for v in self._engagement_history.values())
            }
        }
    
    def set_follow_mode(self, mode: str) -> str:
        """Set follow rate limit mode: conservative, normal, or aggressive"""
        if mode not in self.FOLLOW_LIMITS:
            return f"❌ Invalid mode. Choose from: {', '.join(self.FOLLOW_LIMITS.keys())}"
        self._follow_mode = mode
        return f"✅ Follow mode set to {mode}: {self.FOLLOW_LIMITS[mode]} follows/day per platform"
