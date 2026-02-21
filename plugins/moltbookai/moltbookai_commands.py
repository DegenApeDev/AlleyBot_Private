"""
MoltbookAI Commands - AI-powered posting and engagement
"""

import asyncio
from typing import Dict, Any


class MoltbookAICommands:
    """Command handlers for MoltbookAI integration"""
    
    def __init__(self, core):
        self.core = core
    
    def moltbookai_post_command(self, *args) -> str:
        """Create an AI-generated post on MoltbookAI"""
        if not args:
            return """📝 **Usage:**
/moltbookai_post [submolt] [title] | [content]

**Examples:**
/moltbookai_post aithoughts AI Agents | Autonomous agents are evolving rapidly...
/moltbookai_post tech AI Ethics | Discussing the ethical implications of AI
/moltbookai_post alleybot Dev Update | Working on new features and improvements"""
        
        try:
            # Parse arguments
            args_str = ' '.join(args)
            if '|' in args_str:
                parts = args_str.split('|', 1)
                title_part = parts[0].strip()
                content = parts[1].strip() if len(parts) > 1 else None
            else:
                title_part = args_str
                content = None
            
            # Extract submolt and title
            title_parts = title_part.split(' ', 1)
            if len(title_parts) < 2:
                return "❌ Please specify both submolt and title"
            
            submolt = title_parts[0]
            title = title_parts[1]
            
            # Get MoltbookAI plugin
            if 'moltbookai' not in self.core.plugin_manager.plugins:
                return "❌ MoltbookAI plugin not available"
            
            plugin = self.core.plugin_manager.plugins['moltbookai']
            
            # Create post
            result = plugin.create_post(submolt, title, content)
            
            if result['success']:
                return f"""📝 **Post Created Successfully!**

🔗 **Post ID:** {result.get('post_id', 'N/A')}
📍 **Submolt:** r/{submolt}
📰 **Title:** {title}

✅ Your post is now live on MoltbookAI!
🌐 View at: https://moltbookai.net"""
            else:
                return f"""❌ **Post Failed**

{result.get('error', 'Unknown error')}

💡 **Check:**
• ALLEYBOT_ADDRESS is set in .env
• ALLEYBOT_PRIVATE_KEY is set in .env
• Rate limits (1 post per 30 minutes)"""
                
        except Exception as e:
            return f"❌ Post creation error: {str(e)}"
    
    def moltbookai_comment_command(self, *args) -> str:
        """Create a comment on a MoltbookAI post"""
        if len(args) < 2:
            return """📝 **Usage:**
/moltbookai_comment [post_id] [comment_text]

**Example:**
/moltbookai_comment abc123 Great point! I think...
/moltbookai_comment def456 Interesting perspective on..."""
        
        try:
            post_id = args[0]
            comment_text = ' '.join(args[1:])
            
            # Get MoltbookAI plugin
            if 'moltbookai' not in self.core.plugin_manager.plugins:
                return "❌ MoltbookAI plugin not available"
            
            plugin = self.core.plugin_manager.plugins['moltbookai']
            
            # Create comment
            result = plugin.create_comment(post_id, comment_text)
            
            if result['success']:
                return f"""💬 **Comment Created Successfully!**

🔗 **Comment ID:** {result.get('comment_id', 'N/A')}
📝 **Post:** {post_id}
💭 **Comment:** {comment_text[:50]}{'...' if len(comment_text) > 50 else ''}

✅ Your comment is now live on MoltbookAI!"""
            else:
                return f"""❌ **Comment Failed**

{result.get('error', 'Unknown error')}

💡 **Check:**
• Post ID is valid
• Rate limits (1 comment per 20 seconds)"""
                
        except Exception as e:
            return f"❌ Comment creation error: {str(e)}"
    
    def moltbookai_profile_command(self, *args) -> str:
        """Get MoltbookAI agent profile"""
        try:
            # Get MoltbookAI plugin
            if 'moltbookai' not in self.core.plugin_manager.plugins:
                return "❌ MoltbookAI plugin not available"
            
            plugin = self.core.plugin_manager.plugins['moltbookai']
            
            # Get profile
            result = plugin.get_profile()
            
            if result['success']:
                profile_data = result['data']
                agent = profile_data.get('agent', profile_data.get('data', {}))
                
                return f"""🤖 **MoltbookAI Agent Profile**

📛 **Name:** {agent.get('name', 'N/A')}
📝 **Description:** {agent.get('description', 'N/A')}
🔐 **Address:** {plugin.wallet_address[:10]}...{plugin.wallet_address[-8:] if plugin.wallet_address else 'N/A'}
📊 **Stats:** Posts: {agent.get('post_count', 0)} | Comments: {agent.get('comment_count', 0)}
⏰ **Created:** {agent.get('created_at', 'N/A')}

✅ Agent profile loaded successfully!"""
            else:
                return f"""❌ **Profile Failed**

{result.get('error', 'Unknown error')}

💡 **Check:**
• ALLEYBOT_ADDRESS is set in .env
• Agent is initialized (first post auto-registers)"""
                
        except Exception as e:
            return f"❌ Profile fetch error: {str(e)}"
    
    def moltbookai_feed_command(self, *args) -> str:
        """Get recent posts from MoltbookAI feed"""
        try:
            # Parse options
            sort_type = "new"
            limit = 10
            
            for arg in args:
                if arg in ["new", "top", "discussed", "random"]:
                    sort_type = arg
                elif arg.isdigit():
                    limit = min(int(arg), 50)  # Cap at 50
            
            # Get MoltbookAI plugin
            if 'moltbookai' not in self.core.plugin_manager.plugins:
                return "❌ MoltbookAI plugin not available"
            
            plugin = self.core.plugin_manager.plugins['moltbookai']
            
            # Get posts
            result = plugin.get_posts(sort=sort_type, limit=limit)
            
            if result['success']:
                posts = result['posts']
                if not posts:
                    return "📭 No posts found"
                
                output = f"""📖 **MoltbookAI Feed** ({sort_type.title()})

"""
                
                for i, post in enumerate(posts[:limit], 1):
                    title = post.get('title', 'No title')
                    submolt = post.get('submolt_name', 'unknown')
                    content = post.get('content', '')
                    post_id = post.get('id', 'unknown')[:8]
                    
                    output += f"{i}. **{title}** (r/{submolt})\n"
                    output += f"   📝 {content[:100]}{'...' if len(content) > 100 else ''}\n"
                    output += f"   🔗 ID: {post_id}...\n\n"
                
                return output
            else:
                return f"❌ Feed fetch failed: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Feed error: {str(e)}"
    
    def moltbookai_submolts_command(self, *args) -> str:
        """Get list of available submolts"""
        try:
            # Get MoltbookAI plugin
            if 'moltbookai' not in self.core.plugin_manager.plugins:
                return "❌ MoltbookAI plugin not available"
            
            plugin = self.core.plugin_manager.plugins['moltbookai']
            
            # Get submolts
            result = plugin.get_submolts()
            
            if result['success']:
                submolts = result['submolts']
                if not submolts:
                    return "📭 No submolts found"
                
                output = """📂 **MoltbookAI Submolts**

"""
                
                for i, submolt in enumerate(submolts[:20], 1):  # Show first 20
                    name = submolt.get('name', 'unknown')
                    description = submolt.get('description', '')
                    post_count = submolt.get('post_count', 0)
                    
                    output += f"{i}. **r/{name}** ({post_count} posts)\n"
                    if description:
                        output += f"   📝 {description[:80]}{'...' if len(description) > 80 else ''}\n"
                    output += "\n"
                
                return output
            else:
                return f"❌ Submolts fetch failed: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Submolts error: {str(e)}"
    
    def moltbookai_init_command(self, *args) -> str:
        """Initialize MoltbookAI agent profile"""
        try:
            # Get MoltbookAI plugin
            if 'moltbookai' not in self.core.plugin_manager.plugins:
                return "❌ MoltbookAI plugin not available"
            
            plugin = self.core.plugin_manager.plugins['moltbookai']
            
            # Initialize agent
            result = plugin.initialize_agent()
            
            if result['success']:
                return """🤖 **Agent Initialized Successfully!**

✅ Your MoltbookAI agent profile is ready
📝 You can now post and comment on MoltbookAI
🔐 Authentication configured with your wallet

💡 **Next Steps:**
• /moltbookai_profile - Check your profile
• /moltbookai_post [submolt] [title] | [content] - Create a post
• /moltbookai_feed - Browse recent posts"""
            else:
                return f"❌ Initialization failed: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Initialization error: {str(e)}"
