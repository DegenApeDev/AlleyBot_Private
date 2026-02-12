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

    def clawbr_follow_command(self, *args) -> str:
        """Follow a Clawbr user by @handle/username"""
        if not args:
            return "Usage: /clawbr_follow <username> (e.g., /clawbr_follow @neo)"

        username = args[0].strip().lstrip('@')
        if not username:
            return "❌ Invalid username provided."

        try:
            # Check follow status first
            status = self.get_follow_status(username)
            print(f"🔍 Follow status for @{username}: {status}")
            
            status_data = status.get('data') if isinstance(status, dict) else None
            if status.get('success', False) and isinstance(status_data, dict):
                if status_data.get('isFollowing') is True:
                    return f"✅ Already following @{username}."
            
            # Try to follow - use follow_agent directly to avoid mixin conflicts
            result = self.follow_agent(username)
            print(f"📤 Follow result for @{username}: {result}")
            
            if result.get('success', False):
                return f"✅ Successfully followed @{username}!"
            
            # Handle error response
            error_msg = result.get('error')
            if isinstance(error_msg, dict):
                error_msg = error_msg.get('message') or error_msg.get('error') or str(error_msg)
            elif not error_msg:
                error_msg = result.get('message') or 'Unknown error'
            
            return f"❌ Failed to follow @{username}: {error_msg}"
            
        except Exception as e:
            import traceback
            print(f"🦞 Exception in clawbr_follow_command: {e}")
            traceback.print_exc()
            return f"🦞 Error following @{username}: {str(e)}"
    
    def clawbr_unfollow_command(self, *args) -> str:
        """Unfollow a Clawbr user by @handle/username"""
        if not args:
            return "Usage: /clawbr_unfollow <username> (e.g., /clawbr_unfollow @neo)"

        username = args[0].strip().lstrip('@')
        if not username:
            return "❌ Invalid username provided."

        try:
            result = self.unfollow_agent(username)
            if result.get('success', False):
                return f"✅ Successfully unfollowed @{username}!"
            error_msg = result.get('error') or result.get('message') or 'Unknown error'
            return f"❌ Failed to unfollow @{username}: {error_msg}"
        except Exception as e:
            return f"🦞 Error unfollowing @{username}: {str(e)}"
    
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

    def clawbr_following_feed_command(self, limit: int = 10) -> str:
        """Show recent posts from agents you follow"""
        feed = self.get_following_feed(limit=limit)
        
        if not feed.get('success', True):
            return f"❌ Failed to get following feed: {feed.get('error', 'Unknown error')}"
        
        posts = feed.get('posts', [])
        if not posts:
            return "📭 No posts from followed agents"
        
        output = ["👥 **Clawbr Following Feed**\n"]
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

    def clawbr_mentions_command(self, limit: int = 10) -> str:
        """Show posts that @mention you"""
        feed = self.get_mentions_feed(limit=limit)
        
        if not feed.get('success', True):
            return f"❌ Failed to get mentions: {feed.get('error', 'Unknown error')}"
        
        posts = feed.get('posts', [])
        if not posts:
            return "📭 No mentions found"
        
        output = ["📢 **Clawbr Mentions**\n"]
        for post in posts[:5]:
            author = post.get('authorDisplayName', 'Unknown')
            content = post.get('content', '')[:100]
            if len(post.get('content', '')) > 100:
                content += "..."
            likes = post.get('likeCount', 0)
            replies = post.get('replyCount', 0)
            
            output.append(f"👤 {author} mentioned you")
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
        
        # Handle different response structures
        debates_list = []
        if isinstance(my_debates, dict):
            if my_debates.get('success', True):
                # Clawbr API returns: {active: [], voting: [], completed: [], total: N}
                active_debates = my_debates.get('active', [])
                voting_debates = my_debates.get('voting', [])
                pending_debates = my_debates.get('pending', [])
                
                # Combine all debates
                debates_list = active_debates + voting_debates + pending_debates
                
                # Also check legacy structure just in case
                if not debates_list and 'debates' in my_debates:
                    debates_list = my_debates.get('debates', [])
                if not debates_list and 'data' in my_debates:
                    data = my_debates.get('data', [])
                    if isinstance(data, list):
                        debates_list = data
                    elif isinstance(data, dict):
                        debates_list = data.get('active', []) + data.get('voting', []) + data.get('pending', [])
        
        if debates_list:
            # Group by status
            active = [d for d in debates_list if d.get('status') in ('active', 'open', 'in_progress', 'pending')]
            waiting = [d for d in debates_list if d.get('isMyTurn') or d.get('is_my_turn')]
            
            output.append(f"� **Your Debates ({len(debates_list)} total):**")
            
            # Show debates waiting for your turn first
            if waiting:
                output.append(f"\n� **Waiting for your turn ({len(waiting)}):**")
                for debate in waiting[:5]:
                    topic = debate.get('topic', 'No topic')[:50]
                    slug = debate.get('slug', 'unknown')
                    status = debate.get('status', 'unknown')
                    output.append(f"  • {topic}... ({slug}) [status: {status}]")
            
            # Show active debates
            if active:
                output.append(f"\n🎭 **Active debates ({len(active)}):**")
                for debate in active[:5]:
                    topic = debate.get('topic', 'No topic')[:50]
                    slug = debate.get('slug', 'unknown')
                    is_my_turn = "🔄 Your turn!" if (debate.get('isMyTurn') or debate.get('is_my_turn')) else "⏳ Their turn"
                    output.append(f"  • {topic}... ({is_my_turn})")
            
            # If no active but have debates, show all statuses
            if not active and debates_list:
                output.append(f"\n� **All your debates:**")
                for debate in debates_list[:5]:
                    topic = debate.get('topic', 'No topic')[:50]
                    status = debate.get('status', 'unknown')
                    slug = debate.get('slug', 'unknown')
                    output.append(f"  • {topic}... [status: {status}] ({slug})")
            output.append("")
        else:
            output.append("📭 No debates found in your account\n")
        
        # Show open debates from hub
        open_debates = hub.get('openDebates', [])
        if not open_debates and 'data' in hub:
            open_debates = hub.get('data', {}).get('openDebates', [])
            
        if open_debates:
            output.append(f"🔓 **Open Debates ({len(open_debates)}):**")
            for debate in open_debates[:3]:
                topic = debate.get('topic', 'No topic')[:50]
                challenger = debate.get('challengerName', 'Unknown')
                output.append(f"  • {topic}... (by {challenger})")
        
        if not debates_list and not open_debates:
            output.append("📭 No active debates found")
        
        return '\n'.join(output)

    def clawbr_create_debate_command(self, *args) -> str:
        """Create a new debate - accepts natural language or structured args"""
        if not args:
            return "Usage: /clawbr_create_debate <topic> <opening_argument> [category]\nOr: /clawbr_create_debate <natural language description>"
        
        full_input = ' '.join(args)
        
        # Detect natural language vs structured args
        # Natural language: longer than 15 chars, doesn't look like a short topic + argument
        # Structured: first arg is short topic (<50 chars), remaining args exist
        is_structured = len(args) >= 2 and len(args[0]) < 50 and len(args[0]) > 5
        is_natural_language = not is_structured and len(full_input) > 15
        
        if is_natural_language:
            # Use intelligent debate creation with Grok
            result = self.create_intelligent_debate(full_input)
        else:
            # Use traditional structured args
            topic = args[0]
            opening = ' '.join(args[1:]) if len(args) > 1 else ""
            result = self.create_debate(topic, opening)
        
        if result.get('success', True):
            debate_id = result.get('id', result.get('slug', 'unknown'))
            topic = result.get('topic', 'N/A')
            return f"✅ Debate created: {debate_id}\nTopic: {topic}"
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