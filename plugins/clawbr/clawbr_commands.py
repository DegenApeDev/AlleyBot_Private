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
            
            status = f"""🦞 **Clawbr Status**
📛 Agent: {agent.get('displayName', 'N/A')}
🏷️  Name: @{agent.get('name', 'N/A')}
📊 Followers: {agent.get('followerCount', 0)}
⚡ Influence: {agent.get('influenceScore', 0)}
🎭 Debates: {agent.get('debateStats', 0)}"""
            return status
        except Exception:
            return "❌ Error fetching Clawbr status."
    
    def clawbr_follow_10_agents(self) -> str:
        """Discover and follow 10 relevant AI agents"""
        try:
            profile = self.get_profile()
            if not profile.get('success', True):
                return "❌ Not connected to Clawbr. Check API key."
            
            api_key = os.getenv("CLAWBR_API_KEY")
            if not api_key:
                return "❌ CLAWBR_API_KEY environment variable not set."
            
            base_url = "https://api.clawbr.ai/v1"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            
            # API discovery: search for AI agents, sort by followers
            search_url = f"{base_url}/search/agents"
            params = {
                "q": "AI agent",
                "limit": 10,
                "sort": "followerCount",
                "order": "desc",
            }
            search_resp = requests.get(search_url, headers=headers, params=params, timeout=10)
            
            if search_resp.status_code != 200:
                return f"❌ Agent search failed: HTTP {search_resp.status_code}"
            
            search_data: Dict[str, Any] = search_resp.json()
            if not search_data.get("success"):
                return "❌ Agent search API returned error."
            
            agents: List[Dict[str, Any]] = search_data.get("data", {}).get("agents", [])
            if not agents:
                return "❌ No relevant AI agents found."
            
            followed_count = 0
            followed_agents = []
            
            for agent in agents:
                agent_id = agent.get("id") or agent.get("agentId")
                if not agent_id:
                    continue
                
                # Follow via API (engagement)
                follow_url = f"{base_url}/agents/{agent_id}/follow"
                follow_resp = requests.post(follow_url, headers=headers, timeout=10)
                
                if follow_resp.status_code == 200:
                    follow_data: Dict[str, Any] = follow_resp.json()
                    if follow_data.get("success"):
                        followed_count += 1
                        name = agent.get("displayName") or agent.get("name", "Unknown")
                        followed_agents.append(name)
                        
                        # Log for analytics
                        log_entry = {
                            "action": "follow_agent",
                            "agent_id": agent_id,
                            "agent_name": name,
                            "timestamp": os.getenv("TIMESTAMP", ""),  # optional
                        }
                        print(f"Clawbr analytics: {log_entry}")
            
            agent_list = "\n".join([f"• @{name}" for name in followed_agents[:5]])
            more = "..." if len(followed_agents) > 5 else ""
            
            status_msg = f"""✅ **Followed {followed_count}/10 AI Agents**

{agent_list}
{more}

Logged to analytics."""
            
            return status_msg
        
        except Exception as e:
            return f"❌ Error following agents: {str(e)}"
    
    def clawbr_post_command(self, *args) -> str:
        """Create a post on Clawbr (wrapper around create_post)"""
        content = ' '.join(args) if args else ""
        if not content:
            return "❌ Usage: /clawbr_post <your message>"
        
        result = self.create_post(content)
        if result.get('success', True):
            post_id = result.get('id', 'unknown')
            return f"✅ Posted to Clawbr! ID: {post_id}\n📝 {content[:100]}{'...' if len(content) > 100 else ''}"
        return f"❌ Post failed: {result.get('error', 'Unknown error')}"
    
    def clawbr_feed_command(self) -> str:
        """Get Clawbr global feed"""
        result = self.get_global_feed(limit=10)
        if not result.get('success', True):
            return f"❌ Failed to fetch feed: {result.get('error', 'Unknown error')}"
        
        posts = result.get('posts', result.get('data', {}).get('posts', []))
        if not posts:
            return "📭 No posts in feed"
        
        output = f"🦞 Clawbr Feed ({len(posts)} posts):\n\n"
        for post in posts[:5]:
            author = post.get('agentName') or post.get('agent', {}).get('name', 'Unknown')
            content = post.get('content', '')[:80]
            likes = post.get('likesCount', 0)
            output += f"@{author}: {content}{'...' if len(content) > 80 else ''}\n"
            output += f"   ❤️ {likes} likes\n\n"
        return output
    
    def clawbr_join_debate_command(self, *args) -> str:
        """Join a debate by slug"""
        if not args:
            return "❌ Usage: /clawbr_join_debate <debate_slug>"
        slug = args[0]
        result = self.join_debate(slug)
        if result.get('success', True):
            return f"✅ Joined debate: {slug}"
        return f"❌ Failed to join debate: {result.get('error', 'Unknown error')}"
    
    def clawbr_leaderboard_command(self) -> str:
        """Get Clawbr influence leaderboard"""
        result = self.get_leaderboard()
        if not result.get('success', True):
            return f"❌ Failed to fetch leaderboard: {result.get('error', 'Unknown error')}"
        
        leaders = result.get('leaderboard', result.get('data', []))
        if not leaders:
            return "📭 Leaderboard empty"
        
        output = "🏆 Clawbr Leaderboard:\n\n"
        for i, leader in enumerate(leaders[:10], 1):
            name = leader.get('name', 'Unknown')
            influence = leader.get('influenceScore', 0)
            output += f"{i}. @{name} - {influence} influence\n"
        return output
    
    def clawbr_debates_command(self) -> str:
        """Show active debates on Clawbr"""
        try:
            result = self.get_debate_hub()
            if not result.get('success', True):
                return f"❌ Failed to fetch debates: {result.get('error', 'Unknown error')}"
            
            debates = result.get('debates', result.get('data', {}).get('debates', []))
            if not debates:
                return "📭 No active debates"
            
            output = f"🎭 Clawbr Debates ({len(debates)} active):\n\n"
            for debate in debates[:5]:
                topic = debate.get('topic', 'Unknown topic')
                slug = debate.get('slug', 'no-slug')
                status = debate.get('status', 'open')
                output += f"• {topic[:60]}\n"
                output += f"  Slug: {slug} | Status: {status}\n\n"
            return output
        except Exception as e:
            return f"❌ Error fetching debates: {str(e)}"
    
    def clawbr_create_debate_command(self, *args) -> str:
        """Create a new debate"""
        if len(args) < 2:
            return "❌ Usage: /clawbr_create_debate <topic> <opening_argument>"
        
        topic = args[0]
        argument = ' '.join(args[1:])
        
        try:
            result = self.create_debate(topic, argument)
            if result.get('success', True):
                slug = result.get('slug', 'unknown')
                return f"✅ Created debate: {topic}\n🔗 Slug: {slug}"
            return f"❌ Failed to create debate: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"❌ Error creating debate: {str(e)}"
    
    def clawbr_search_command(self, *args) -> str:
        """Search for agents or posts"""
        if not args:
            return "❌ Usage: /clawbr_search <query>"
        query = ' '.join(args)
        
        # Search agents
        agent_result = self.search_agents(query)
        agents = agent_result.get('agents', agent_result.get('data', {}).get('agents', [])) if agent_result.get('success') else []
        
        output = f"🔍 Clawbr Search: '{query}'\n\n"
        
        if agents:
            output += f"👤 Agents ({len(agents)}):\n"
            for agent in agents[:5]:
                name = agent.get('name', 'Unknown')
                display = agent.get('displayName', name)
                followers = agent.get('followerCount', 0)
                output += f"  @{name} ({display}) - {followers} followers\n"
        else:
            output += "👤 No agents found\n"
        
        return output
    
    def clawbr_stats_command(self) -> str:
        """Get Clawbr platform stats"""
        result = self.get_platform_stats()
        if not result.get('success', True):
            return f"❌ Failed to fetch stats: {result.get('error', 'Unknown error')}"
        
        stats = result.get('stats', result.get('data', {}))
        output = "📊 Clawbr Platform Stats:\n\n"
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                output += f"  {key}: {value:,}\n"
            else:
                output += f"  {key}: {value}\n"
        return output