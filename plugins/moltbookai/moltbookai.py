#!/usr/bin/env python3
"""
MoltbookAI Plugin - AI Agent Integration
Posts and comments on MoltbookAI using Ethereum wallet authentication
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, Optional, Any
from eth_account import Account
from eth_account.messages import encode_defunct
from plugin_manager import AlleyBotPlugin


class MoltbookAIPlugin(AlleyBotPlugin):
    """MoltbookAI integration for autonomous posting and engagement"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = "https://moltbookai.net"
        self.api_key = os.getenv('MOLTBOOKAI_API_KEY')
        
        # Ethereum wallet for authentication
        self.wallet_address = os.getenv('ALLEYBOT_ADDRESS')
        self.private_key = os.getenv('ALLEYBOT_PRIVATE_KEY')
        
        # Rate limiting
        self.last_post_time = 0
        self.last_comment_time = 0
        self.post_cooldown = 1800  # 30 minutes
        self.comment_cooldown = 20  # 20 seconds
        
        # Agent profile cache
        self.agent_profile = None
        self.profile_cache_time = 0
        self.profile_cache_ttl = 3600  # 1 hour
        
        print(f"🤖 MoltbookAI Plugin initialized")
        print(f"   Address: {self.wallet_address}")
        print(f"   Base URL: {self.base_url}")
    
    def initialize(self, api, core):
        """Initialize plugin with API and core access"""
        super().initialize(api, core)
        print(f"🔗 MoltbookAI plugin connected to core")
    
    def _sign_message(self, action: str, timestamp: int) -> str:
        """Sign message for MoltbookAI authentication"""
        try:
            # Build message string: moltbook:{action}:{timestamp}
            message = f"moltbook:{action}:{timestamp}"
            
            # Create account from private key
            account = Account.from_key(self.private_key)
            
            # Encode the message for signing
            message_encoded = encode_defunct(text=message)
            
            # Sign the encoded message
            signed_message = account.sign_message(message_encoded)
            
            return signed_message.signature.hex()
            
        except Exception as e:
            print(f"❌ Error signing message: {e}")
            return None
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                      action: str = "CreatePost") -> Dict[str, Any]:
        """Make authenticated request to MoltbookAI API"""
        try:
            url = f"{self.base_url}{endpoint}"
            timestamp = int(time.time())  # Unix timestamp in seconds
            
            # Sign the message
            signature = self._sign_message(action, timestamp)
            if not signature:
                return {"success": False, "error": "Failed to sign message"}
            
            # Prepare headers
            headers = {
                'x-agent-address': self.wallet_address,
                'x-agent-signature': signature,
                'x-agent-timestamp': str(timestamp),
                'Content-Type': 'application/json'
            }
            
            # Make request
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=headers, json=data, timeout=10)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            # Parse response
            try:
                result = response.json()
            except:
                result = {"response": response.text}
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "data": result,
                "headers": dict(response.headers)
            }
            
        except Exception as e:
            print(f"❌ Error making request: {e}")
            return {"success": False, "error": str(e)}
    
    def initialize_agent(self, name: str = "AlleyBot", description: str = None) -> Dict[str, Any]:
        """Initialize agent profile (optional - happens automatically on first post)"""
        try:
            print(f"🤖 Initializing MoltbookAI agent profile...")
            
            data = {
                "name": name,
                "description": description or "Autonomous AI agent sharing insights on technology, AI, and decentralized systems",
                "metadata": {
                    "agent_type": "autonomous",
                    "created_by": "AlleyBot",
                    "version": "1.0"
                }
            }
            
            print(f"🔍 Sending data to {self.base_url}/api/agents")
            print(f"📝 Data: {json.dumps(data, indent=2)}")
            
            result = self._make_request('POST', '/api/agents', data, 'InitializeAgent')
            
            print(f"🔍 Response: {result}")
            
            if result['success']:
                print(f"✅ Agent profile initialized successfully")
                return {"success": True, "message": "Agent profile initialized"}
            else:
                print(f"❌ Failed to initialize agent: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error', 'Unknown error')}
                
        except Exception as e:
            print(f"❌ Agent initialization error: {str(e)}")
            return {"success": False, "error": f"Agent initialization error: {str(e)}"}
    
    def get_profile(self) -> Dict[str, Any]:
        """Get agent profile information"""
        try:
            # Check cache first
            now = time.time()
            if self.agent_profile and (now - self.profile_cache_time) < self.profile_cache_ttl:
                return {"success": True, "data": self.agent_profile}
            
            print(f"🔍 Fetching MoltbookAI agent profile...")
            
            result = self._make_request('GET', f'/api/agents/me?address={self.wallet_address}')
            
            if result['success']:
                self.agent_profile = result['data']
                self.profile_cache_time = now
                print(f"✅ Profile fetched successfully")
                return {"success": True, "data": self.agent_profile}
            else:
                print(f"❌ Failed to fetch profile: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error', 'Unknown error')}
                
        except Exception as e:
            return {"success": False, "error": f"Profile fetch error: {str(e)}"}
    
    def create_post(self, submolt_name: str, title: str, content: str = None, url: str = None) -> Dict[str, Any]:
        """Create a post on MoltbookAI"""
        try:
            # Check rate limiting
            now = time.time()
            if now - self.last_post_time < self.post_cooldown:
                remaining = int(self.post_cooldown - (now - self.last_post_time))
                return {
                    "success": False, 
                    "error": f"Rate limited. Please wait {remaining} seconds before posting again."
                }
            
            print(f"📝 Creating post on r/{submolt_name}: {title}")
            
            data = {
                "submolt_name": submolt_name,
                "title": title
            }
            
            if content:
                data["content"] = content
            if url:
                data["url"] = url
            
            result = self._make_request('POST', '/api/posts', data, 'CreatePost')
            
            if result['success']:
                self.last_post_time = now
                post_data = result['data']
                print(f"✅ Post created successfully")
                return {
                    "success": True, 
                    "post_id": post_data.get('id'),
                    "message": "Post created successfully",
                    "data": post_data
                }
            else:
                print(f"❌ Failed to create post: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error', 'Unknown error')}
                
        except Exception as e:
            return {"success": False, "error": f"Post creation error: {str(e)}"}
    
    def create_comment(self, post_id: str, content: str, parent_id: str = None) -> Dict[str, Any]:
        """Create a comment on a post"""
        try:
            # Check rate limiting
            now = time.time()
            if now - self.last_comment_time < self.comment_cooldown:
                remaining = int(self.comment_cooldown - (now - self.last_comment_time))
                return {
                    "success": False, 
                    "error": f"Rate limited. Please wait {remaining} seconds before commenting again."
                }
            
            print(f"💬 Creating comment on post {post_id}")
            
            data = {"content": content}
            if parent_id:
                data["parent_id"] = parent_id
            
            result = self._make_request('POST', f'/api/posts/{post_id}/comments', data, 'CreateComment')
            
            if result['success']:
                self.last_comment_time = now
                comment_data = result['data']
                print(f"✅ Comment created successfully")
                return {
                    "success": True, 
                    "comment_id": comment_data.get('id'),
                    "message": "Comment created successfully",
                    "data": comment_data
                }
            else:
                print(f"❌ Failed to create comment: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error', 'Unknown error')}
                
        except Exception as e:
            return {"success": False, "error": f"Comment creation error: {str(e)}"}
    
    def get_posts(self, sort: str = "new", limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get posts from feed"""
        try:
            print(f"📖 Fetching posts (sort: {sort}, limit: {limit})")
            
            params = {"sort": sort, "limit": limit, "offset": offset}
            url = f'/api/posts?{"&".join([f"{k}={v}" for k, v in params.items()])}'
            
            result = self._make_request('GET', url)
            
            if result['success']:
                posts = result['data']
                print(f"✅ Fetched {len(posts) if isinstance(posts, list) else 1} posts")
                return {"success": True, "posts": posts}
            else:
                print(f"❌ Failed to fetch posts: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error', 'Unknown error')}
                
        except Exception as e:
            return {"success": False, "error": f"Posts fetch error: {str(e)}"}
    
    def get_submolts(self) -> Dict[str, Any]:
        """Get list of submolts"""
        try:
            print(f"📂 Fetching submolt list...")
            
            result = self._make_request('GET', '/api/submolts')
            
            if result['success']:
                submolts = result['data']
                print(f"✅ Fetched {len(submolts) if isinstance(submolts, list) else 1} submolts")
                return {"success": True, "submolts": submolts}
            else:
                print(f"❌ Failed to fetch submolts: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error', 'Unknown error')}
                
        except Exception as e:
            return {"success": False, "error": f"Submolts fetch error: {str(e)}"}
    
    def update_profile(self, name: str = None, description: str = None, metadata: Dict = None) -> Dict[str, Any]:
        """Update agent profile"""
        try:
            print(f"🔄 Updating agent profile...")
            
            data = {}
            if name:
                data["name"] = name
            if description:
                data["description"] = description
            if metadata:
                data["metadata"] = metadata
            
            result = self._make_request('PATCH', '/api/agents/me', data, 'UpdateProfile')
            
            if result['success']:
                # Clear profile cache to force refresh
                self.agent_profile = None
                self.profile_cache_time = 0
                
                print(f"✅ Profile updated successfully")
                return {"success": True, "message": "Profile updated successfully"}
            else:
                print(f"❌ Failed to update profile: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error', 'Unknown error')}
                
        except Exception as e:
            return {"success": False, "error": f"Profile update error: {str(e)}"}
    
    # Command methods
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
            
            # Create post
            result = self.create_post(submolt, title, content)
            
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
            
            # Create comment
            result = self.create_comment(post_id, comment_text)
            
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
            # Get profile
            result = self.get_profile()
            
            if result['success']:
                profile_data = result['data']
                agent = profile_data.get('agent', profile_data.get('data', {}))
                
                return f"""🤖 **MoltbookAI Agent Profile**

📛 **Name:** {agent.get('name', 'N/A')}
📝 **Description:** {agent.get('description', 'N/A')}
🔐 **Address:** {self.wallet_address[:10]}...{self.wallet_address[-8:] if self.wallet_address else 'N/A'}
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
            
            # Get posts
            result = self.get_posts(sort=sort_type, limit=limit)
            
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
            # Get submolts
            result = self.get_submolts()
            
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
            # Initialize agent
            result = self.initialize_agent()
            
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
    
    def get_commands(self) -> Dict[str, callable]:
        """Return available commands"""
        return {
            'moltbookai_post': self.moltbookai_post_command,
            'moltbookai_comment': self.moltbookai_comment_command,
            'moltbookai_profile': self.moltbookai_profile_command,
            'moltbookai_feed': self.moltbookai_feed_command,
            'moltbookai_submolts': self.moltbookai_submolts_command,
            'moltbookai_init': self.moltbookai_init_command,
        }


# Plugin factory function
def create_plugin(core):
    """Create MoltbookAI plugin instance"""
    return MoltbookAIPlugin()


# Plugin metadata
PLUGIN_INFO = {
    "name": "moltbookai",
    "version": "1.0.0",
    "description": "MoltbookAI integration for autonomous posting and engagement",
    "author": "AlleyBot",
    "requires": ["eth_account", "requests"],
    "environment_vars": [
        "ALLEYBOT_ADDRESS",
        "ALLEYBOT_PRIVATE_KEY"
    ]
}
