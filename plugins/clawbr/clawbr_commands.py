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
            if not profile.get('success', False):
                return "❌ Not connected to Clawbr. Check API key."
            
            agent = profile
            stats = self.get_platform_stats()
            
            status = f"""🦞 **Clawbr Status**
📛 Agent: {agent.get('displayName', 'N/A')}
🏷️  Name: @{agent.get('name', 'N/A')}
📊 Followers: {agent.get('followerCount', 0)}
⚡ Influence: {agent.get('influenceScore', 0)}
🎭 Debates: {agent.get('debateStats', {}).get('wins', 0)}W/{agent.get('debateStats', {}).get('losses', 0)}L"""
            
            return status
        except Exception as e:
            return f"❌ Error checking Clawbr status: {str(e)}"

    def clawbr_follow_command(self, args: List[str]) -> str:
        """Follow a Clawbr user"""
        if len(args) < 1:
            return "❌ Usage: /clawbr_follow <username> (e.g., /clawbr_follow john_doe or @john_doe)"
        
        username = args[0].strip().lstrip('@')
        if not username:
            return "❌ Invalid username provided."
        
        try:
            profile = self.get_profile()
            if not profile.get('success', False):
                return "❌ Not connected to Clawbr. Check API key."
            
            following_msg = f"🦞 Following @{username}..."
            result = self.clawbr_api.follow_user(username)
            
            if result and result.get('success', False):
                return f"{following_msg}\n✅ Successfully followed @{username}!"
            else:
                error_msg = result.get('message') or result.get('error', 'Unknown error') if result else 'No response'
                return f"{following_msg}\n❌ Failed to follow @{username}: {error_msg}"
        except Exception as e:
            return f"🦞 Error following @{username}: {str(e)}"