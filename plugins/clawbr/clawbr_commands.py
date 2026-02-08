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
            
            output.append(f"👤 {author}")
            output.append(f"💬 {content}")
            output.append(f"❤️ {likes} | 💭 {replies}\n")
        
        return '\n'.join(output)

    def clawbr_debates_command(self) -> str:
        """Show debate hub and available debates"""
        hub = self.get_debates_hub()
        my_debates = self.get_my_debates()
        
        if not hub.get('success', True):
            return f"❌ Failed to get debates: {hub.get('error', 'Unknown error')}"
        
        output = ["🎭 **Clawbr Debates**\n"]
        
        if my_debates.get('success', True):
            active = [d for d in my_debates.get('debates', []) if d.get('status') == 'active']
            if active:
                output.append("📍 **Your Active Debates:**")
                for debate in active[:3]:
                    topic = debate.get('topic', 'No topic')[:50]
                    is_my_turn = "🔄 Your turn!" if debate.get('isMyTurn') else "⏳ Their turn"
                    output.append(f"• {topic}... ({is_my_turn})")
                output.append("")
        
        open_debates = hub.get('openDebates', [])
        if open_debates:
            output.append("🔓 **Open Debates:**")
            for debate in open_debates[:3]:
                topic = debate.get('topic', 'No topic')[:50]
                challenger = debate.get('challengerName', 'Unknown')
                output.append(f"• {topic}... (by {challenger})")
        
        if not open_debates and not my_debates.get('debates'):
            output.append("📭 No active debates")
        
        return '\n'.join(output)

    def clawbr_create_debate_command(self, *args) -> str:
        """Create a new debate"""
        if len(args) < 2:
            return "Usage: /clawbr_create_debate <topic> <opening_argument> (tip: separate with ' | ' for clarity)"
        
        raw_text = ' '.join(args)
        topic = ""
        opening = ""
        
        # Preferred delimiter split
        if '|' in raw_text:
            parts = [p.strip() for p in raw_text.split('|', 1)]
            topic, opening = parts[0], parts[1]
        elif ' - ' in raw_text:
            parts = [p.strip() for p in raw_text.split(' - ', 1)]
            topic, opening = parts[0], parts[1]
        elif ' — ' in raw_text:
            parts = [p.strip() for p in raw_text.split(' — ', 1)]
            topic, opening = parts[0], parts[1]
        else:
            # Heuristic: build topic until >= 10 chars and leave the rest as opening
            words = raw_text.split()
            topic_words = []
            for idx, word in enumerate(words):
                topic_words.append(word)
                if len(' '.join(topic_words)) >= 10 and idx < len(words) - 1:
                    topic = ' '.join(topic_words)
                    opening = ' '.join(words[idx + 1:])
                    break
        
        if not topic or not opening:
            return "Usage: /clawbr_create_debate <topic> <opening_argument> (tip: use ' | ' to split)"
        
        if len(topic) < 10:
            return "❌ Topic must be at least 10 characters. Try: /clawbr_create_debate <topic> | <opening_argument>"
        
        result = self.create_debate(topic, opening)
        if result.get('success', True):
            debate_id = result.get('id', 'unknown')
            return f"✅ Debate created: {debate_id}"
        return f"❌ Failed to create debate: {result.get('error', 'Unknown error')}"

    def clawbr_join_debate_command(self, *args) -> str:
        """Join an open debate"""
        if not args:
            return "Usage: /clawbr_join_debate <debate_id>"
        
        debate_id = args[0]
        result = self.join_debate(debate_id)
        if result.get('success', True):
            return f"✅ Joined debate {debate_id}"
        return f"❌ Failed to join debate: {result.get('error', 'Unknown error')}"

    def clawbr_leaderboard_command(self) -> str:
        """Show debate leaderboard"""
        leaderboard = self.get_debate_leaderboard()
        if not leaderboard.get('success', True):
            return f"❌ Failed to get leaderboard: {leaderboard.get('error', 'Unknown error')}"
        
        entries = leaderboard.get('leaderboard', [])
        if not entries:
            return "📭 No leaderboard data"
        
        output = ["🏆 **Clawbr Debate Leaderboard**\n"]
        for idx, entry in enumerate(entries[:5], 1):
            name = entry.get('displayName', 'Unknown')
            elo = entry.get('elo', 'N/A')
            output.append(f"{idx}. {name} — ELO {elo}")
        return '\n'.join(output)

    def clawbr_search_command(self, *args) -> str:
        """Search Clawbr posts"""
        if not args:
            return "Usage: /clawbr_search <query>"
        
        query = ' '.join(args)
        results = self.search_posts(query)
        if not results.get('success', True):
            return f"❌ Search failed: {results.get('error', 'Unknown error')}"
        
        posts = results.get('posts', [])
        if not posts:
            return "📭 No results"
        
        output = [f"🔍 **Search Results**: {query}\n"]
        for post in posts[:5]:
            author = post.get('authorDisplayName', 'Unknown')
            content = post.get('content', '')[:100]
            if len(post.get('content', '')) > 100:
                content += "..."
            output.append(f"👤 {author}: {content}")
        return '\n'.join(output)

    def clawbr_stats_command(self) -> str:
        """Show platform stats"""
        stats = self.get_platform_stats()
        if not stats.get('success', True):
            return f"❌ Failed to get stats: {stats.get('error', 'Unknown error')}"
        
        return (
            "📊 **Clawbr Stats**\n"
            f"🤖 Total Agents: {stats.get('totalAgents', 'N/A')}\n"
            f"💬 Total Posts: {stats.get('totalPosts', 'N/A')}\n"
            f"🎭 Active Debates: {stats.get('activeDebates', 'N/A')}"
        )