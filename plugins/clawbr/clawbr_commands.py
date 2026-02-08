"""
Clawbr Command Handlers
Telegram and CLI commands for Clawbr interaction
"""
from typing import Dict, List, Optional, Any
import os
import base64
import requests


class ClawbrCommandsMixin:
    """Mixin for Clawbr command implementations"""
    
    def clawbr_status_command(self) -> str:
        """Show Clawbr plugin status"""
        try:
            profile = self.get_profile()
            if not profile.get('success', True):
                return "❌ Not connected to Clawbr. Check API key."
            
            agent = profile
            stats = self.get_platform_stats()
            
            status = f"""🦞 **Clawbr Status**
📛 Agent: {agent.get('displayName', 'N/A')}
🏷️  Name: @{agent.get('name', 'N/A')}
📊 Followers: {agent.get('followerCount', 0)}
⚡ Influence: {agent.get('influenceScore', 0)}
🎭 Debates: {agent.get('debateStats', {}).get('wins', 0)}W/{agent.get('debateStats', {}).get('losses', 0)}L
📈 ELO: {agent.get('debateStats', {}).get('elo', 1200)}

Platform Stats:
🤖 Total Agents: {stats.get('totalAgents', 'N/A')}
💬 Total Posts: {stats.get('totalPosts', 'N/A')}
🎭 Active Debates: {stats.get('activeDebates', 'N/A')}"""
            
            return status
            
        except Exception as e:
            return f"❌ Error getting status: {e}"
    
    def clawbr_post_command(self, *args) -> str:
        """Create a post on Clawbr"""
        if not args:
            return "Usage: /clawbr_post <content>"
        
        content = ' '.join(args)
        result = self.create_intelligent_post(content)
        
        if result.get('success', True):
            post_id = result.get('id')
            return f"✅ Posted on Clawbr: {post_id}"
        else:
            return f"❌ Failed to post: {result.get('error', 'Unknown error')}"
    
    def clawbr_feed_command(self, limit: int = 10) -> str:
        """Show recent posts from global feed"""
        feed = self.get_global_feed(limit=limit)
        
        if not feed.get('success', True):
            return f"❌ Failed to get feed: {feed.get('error', 'Unknown error')}"
        
        posts = feed.get('posts', [])
        if not posts:
            return "📭 No posts in feed"
        
        output = ["📡 **Clawbr Global Feed**\n"]
        for post in posts[:5]:
            author = post.get('authorDisplayName', 'Unknown')
            content = post.get('content', '')[:100]
            if len(post.get('content', '')) > 100:
                content += "..."
            likes = post.get('likeCount', 0)
            replies = post.get('replyCount', 0)