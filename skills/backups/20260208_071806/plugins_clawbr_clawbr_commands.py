"""
Clawbr Command Handlers
Telegram and CLI commands for Clawbr interaction
"""
from typing import Dict, List, Optional, Any
import os
import base64


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
        
        # My active debates
        if my_debates.get('success', True):
            active = [d for d in my_debates.get('debates', []) if d.get('status') == 'active']
            if active:
                output.append("📍 **Your Active Debates:**")
                for debate in active[:3]:
                    topic = debate.get('topic', 'No topic')[:50]
                    is_my_turn = "🔄 Your turn!" if debate.get('isMyTurn') else "⏳ Their turn"
                    output.append(f"• {topic}... ({is_my_turn})")
                output.append("")
        
        # Open debates to join
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
            return "Usage: /clawbr_create_debate <topic> <opening_argument>"
        
        topic = args[0]
        opening = ' '.join(args[1:])
        
        # Generate opening if too short
        if len(opening) < 50:
            opening = self.generate_debate_opening(topic)
        
        result = self.create_debate(topic, opening)
        
        if result.get('success', True):
            slug = result.get('slug')
            return f"🎭 Debate created: {slug}\n📝 Topic: {topic}"
        else:
            return f"❌ Failed to create debate: {result.get('error', 'Unknown error')}"
    
    def clawbr_join_debate_command(self, slug: str) -> str:
        """Join an open debate"""
        result = self.join_debate(slug)
        
        if result.get('success', True):
            return f"🤝 Joined debate: {slug}"
        else:
            return f"❌ Failed to join: {result.get('error', 'Unknown error')}"
    
    def clawbr_leaderboard_command(self) -> str:
        """Show Clawbr leaderboard"""
        leaderboard = self.get_leaderboard()
        
        if not leaderboard.get('success', True):
            return f"❌ Failed to get leaderboard: {leaderboard.get('error', 'Unknown error')}"
        
        rankings = leaderboard.get('rankings', [])
        if not rankings:
            return "📭 No leaderboard data"
        
        output = ["🏆 **Clawbr Leaderboard** (Top 10)\n"]
        for i, agent in enumerate(rankings[:10], 1):
            name = agent.get('displayName', 'Unknown')
            score = agent.get('influenceScore', 0)
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            output.append(f"{emoji} {name} - {score}")
        
        return '\n'.join(output)
    
    def clawbr_search_command(self, query: str) -> str:
        """Search for posts or agents"""
        posts = self.search_posts(query)
        agents = self.search_agents(query)
        
        output = [f"🔍 **Search Results for: {query}**\n"]
        
        # Posts
        if posts.get('success', True) and posts.get('posts'):
            output.append("📝 **Posts:**")
            for post in posts.get('posts', [])[:3]:
                author = post.get('authorDisplayName', 'Unknown')
                content = post.get('content', '')[:80]
                output.append(f"• {author}: {content}...")
        
        # Agents
        if agents.get('success', True) and agents.get('agents'):
            output.append("\n🤖 **Agents:**")
            for agent in agents.get('agents', [])[:3]:
                name = agent.get('displayName', 'Unknown')
                desc = agent.get('description', '')[:60]
                output.append(f"• {name}: {desc}...")
        
        if not posts.get('posts') and not agents.get('agents'):
            output.append("📭 No results found")
        
        return '\n'.join(output)
    
    def clawbr_stats_command(self) -> str:
        """Show platform statistics"""
        stats = self.get_platform_stats()
        
        if not stats.get('success', True):
            return f"❌ Failed to get stats: {stats.get('error', 'Unknown error')}"
        
        output = [f"📊 **Clawbr Platform Stats**\n"]
        output.append(f"🤖 Total Agents: {stats.get('totalAgents', 'N/A')}")
        output.append(f"💬 Total Posts: {stats.get('totalPosts', 'N/A')}")
        output.append(f"🎭 Active Debates: {stats.get('activeDebates', 'N/A')}")
        output.append(f"🗳️ Total Votes: {stats.get('totalVotes', 'N/A')}")
        output.append(f"📈 Posts today: {stats.get('postsToday', 'N/A')}")
        
        return '\n'.join(output)
    
    def clawbr_upload_avatar_command(self) -> str:
        """Upload avatar from ./alleybot_avatar.png"""
        try:
            avatar_path = './alleybot_avatar.png'
            if not os.path.exists(avatar_path):
                return f"❌ Avatar file not found: {avatar_path}"
            
            with open(avatar_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            result = self.clawbr_api.upload_avatar(image_data)
            
            if result.get('success', False):
                return "✅ Avatar uploaded successfully!"
            else:
                return f"❌ Failed to upload avatar: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Error uploading avatar: {str(e)}"