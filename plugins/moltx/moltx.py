"""
MoltX Plugin - Integrates AlleyBot with Moltx.io
Twitter for AI Agents - Social media & microblogging platform
"""
import json
import requests
import os
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from plugin_manager import AlleyBotPlugin
from config import MOLTX_API_KEY

class MoltxPlugin(AlleyBotPlugin):
    """Plugin for Moltx.io - Twitter for AI Agents"""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://moltx.io/v1"
        self.api_key = MOLTX_API_KEY
        self.agent_name = None
        self.agent_id = None
        self.credentials_file = Path.home() / ".agents" / "moltx" / "config.json"
        self.initialized = False
        self.claim_status = None
        
    def initialize(self, api, core):
        """Initialize Moltx plugin"""
        super().initialize(api, core)
        
        # Check if API key is available from environment
        if self.api_key:
            print("✅ Moltx API key loaded from environment")
            self.initialized = True
            self._load_credentials()
        else:
            # Try to load from credentials file
            self._load_credentials()
            
            if not self.api_key:
                print("🔑 No Moltx API key found. Set MOLTX_API_KEY in .env or run 'moltx_register' command.")
            else:
                print(f"✅ Moltx initialized as {self.agent_name}")
                self.initialized = True
        
    def _load_credentials(self):
        """Load credentials from file"""
        try:
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                    self.api_key = creds.get('api_key', self.api_key)
                    self.agent_name = creds.get('agent_name')
                    self.agent_id = creds.get('agent_id')
                    self.claim_status = creds.get('claim_status', 'pending')
                    
                    if self.agent_name:
                        print(f"📁 Loaded Moltx credentials for @{self.agent_name}")
                    else:
                        print(f"📁 Loaded Moltx API key, checking registration...")
                        # Try to get agent info from API
                        self._fetch_agent_info()
            else:
                print("📁 No Moltx credentials file found")
                # If we have an API key from env, try to get agent info
                if self.api_key:
                    print("🔍 API key found, checking registration status...")
                    self._fetch_agent_info()
        except Exception as e:
            print(f"❌ Error loading Moltx credentials: {e}")
    
    def _fetch_agent_info(self):
        """Fetch agent info from API using API key"""
        try:
            response = self._make_request("GET", "/agents/me")
            if response and response.get('success') and response.get('data'):
                agent_data = response['data'].get('agent', {})
                if agent_data.get('name'):
                    self.agent_name = agent_data['name']
                    self.agent_id = agent_data.get('id')
                    self.claim_status = agent_data.get('claim_status', 'pending')
                    print(f"✅ Found registered agent: @{self.agent_name}")
                    
                    # Save to credentials file
                    self._save_credentials(self.api_key, agent_data)
                    self.initialized = True
        except Exception as e:
            print(f"⚠️  Could not fetch agent info: {e}")
    
    def _save_credentials(self, api_key, agent_data):
        """Save credentials to file"""
        try:
            # Create directory if it doesn't exist
            self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
            
            credentials = {
                'agent_name': agent_data['name'],
                'api_key': api_key,
                'agent_id': agent_data.get('id'),
                'claim_status': self.claim_status or 'pending',
                'claim_code': agent_data.get('claim_code'),
                'registered_at': datetime.now().isoformat()
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            print(f"💾 Saved Moltx credentials to {self.credentials_file}")
            
        except Exception as e:
            print(f"❌ Error saving Moltx credentials: {e}")
    
    def _make_request(self, method, endpoint, data=None, params=None, files=None):
        """Make authenticated request to Moltx API"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                if files:
                    # For file uploads, don't set Content-Type automatically
                    headers.pop('Content-Type', None)
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
                    response = requests.post(url, headers=headers, json=data)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Moltx API error: {e}")
            return None
    
    def register_agent(self, name, display_name=None, description=None, avatar_emoji="🦞"):
        """Register a new agent on Moltx"""
        # Check if already registered by checking claim status
        if self.api_key and self.claim_status == 'claimed':
            return f"✅ Already registered and claimed on Moltx. Agent is fully active. Use /moltx_status to see details."
        
        # Also check if we have agent info
        if self.initialized and self.agent_name:
            return f"✅ Already registered as @{self.agent_name} on Moltx. Claim status: {self.claim_status}. Use /moltx_status to see details."
        
        if len(name) < 3 or len(name) > 50:
            return "❌ Agent name must be 3-50 characters"
        
        data = {
            'name': name,
            'display_name': display_name or name,
            'description': description or f"🦞 AI Agent from Moltbook ecosystem",
            'avatar_emoji': avatar_emoji
        }
        
        print(f"🐦 Registering agent '{name}' on Moltx...")
        
        result = self._make_request('POST', '/agents/register', data)
        
        if result and 'data' in result:
            # Moltx returns nested data structure
            data = result['data']
            agent_data = data['agent']
            api_key = data['api_key']
            claim_data = data.get('claim', {})
            
            self.api_key = api_key
            self.agent_name = agent_data['name']
            self.agent_id = agent_data['id']
            self.claim_status = claim_data.get('status', 'pending')
            
            # Save credentials
            agent_info = {
                'name': agent_data['name'],
                'id': agent_data['id'],
                'claim_code': claim_data.get('code')
            }
            self._save_credentials(api_key, agent_info)
            
            self.initialized = True
            
            output = f"✅ Agent '{name}' registered on Moltx!\n"
            output += f"🔑 API Key: {api_key}\n"
            output += f"📱 Claim Code: {claim_data.get('code', 'N/A')}\n"
            output += f"🐦 Handle: @{agent_data['name']}\n"
            output += f"📝 Display Name: {agent_data.get('display_name', 'N/A')}\n"
            output += f"🎯 Next: Post claim tweet with code for full access"
            
            return output
        else:
            return f"❌ Registration failed. Response: {result}"
    
    def claim_agent(self, tweet_url):
        """Claim agent with X/Twitter verification"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        if not tweet_url or 'x.com' not in tweet_url:
            return "❌ Invalid tweet URL. Must be an X.com URL"
        
        print(f"🐦 Claiming agent with tweet: {tweet_url}")
        
        result = self._make_request('POST', '/agents/claim', {'tweet_url': tweet_url})
        
        if result:
            self.claim_status = 'claimed'
            # Update credentials file
            self._update_claim_status('claimed')
            
            output = f"✅ Agent claimed successfully!\n"
            output += f"🎉 Full access unlocked - higher limits, media uploads, verified badge\n"
            output += f"🐦 @{self.agent_name} is now verified!"
            
            return output
        else:
            return "❌ Claim failed. Make sure your tweet contains the claim code and is public."
    
    def claim_command(self, tweet_url):
        """Command to claim agent with X/Twitter verification"""
        return self.claim_agent(tweet_url)
    
    def status_command(self):
        """Command to get Moltx status"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        output = f"🐦 Moltx Status for @{self.agent_name}\n\n"
        output += f"📝 Agent ID: {self.agent_id}\n"
        output += f"🔑 Claim Status: {self.claim_status}\n"
        output += f"📊 Posts Created: {len(self._get_activity('create_post'))}\n"
        output += f"💬 Comments Made: {len(self._get_activity('create_comment'))}\n"
        output += f"🤝 Agents Following: {len(self._get_activity('follow_agent'))}\n"
        output += f"❤️ Posts Liked: {len(self._get_activity('like_post'))}\n"
        
        return output
    
    def _get_activity(self, activity_type):
        """Get activities by type from memory"""
        try:
            activities = self.core.get_memory('moltx_activities') or []
            return [a for a in activities if a.get('type') == activity_type]
        except Exception:
            return []
    
    def profile_command(self, display_name=None, description=None, avatar_emoji=None):
        """Command to update agent profile"""
        return self.update_profile(display_name, description, avatar_emoji)
    
    def _update_claim_status(self, status):
        """Update claim status in credentials file"""
        try:
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                creds['claim_status'] = status
                with open(self.credentials_file, 'w') as f:
                    json.dump(creds, f, indent=2)
        except Exception as e:
            print(f"❌ Error updating claim status: {e}")
    
    def check_status(self):
        """Check agent status"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        result = self._make_request('GET', '/agents/status')
        
        if result:
            output = f"🐦 Moltx Status for @{self.agent_name}:\n\n"
            output += f"🆔 Agent ID: {result.get('id', 'N/A')}\n"
            output += f"📱 Handle: @{result.get('name', 'N/A')}\n"
            output += f"👤 Display: {result.get('display_name', 'N/A')}\n"
            output += f"🎯 Claim Status: {result.get('claim_status', 'N/A')}\n"
            output += f"📊 Posts: {result.get('posts_count', 0)}\n"
            output += f"👥 Following: {result.get('following_count', 0)}\n"
            output += f"👤 Followers: {result.get('followers_count', 0)}\n"
            output += f"❤️ Likes: {result.get('likes_count', 0)}\n"
            
            if result.get('verified'):
                output += f"✅ Verified Agent\n"
            
            return output
        else:
            return "❌ Failed to fetch status"
    
    def upload_media(self, image_path):
        """Upload image to get media URL"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register and claim agent first."
        
        if not os.path.exists(image_path):
            return f"❌ Image file not found: {image_path}"
        
        print(f"📤 Uploading media: {image_path}")
        
        try:
            with open(image_path, 'rb') as image_file:
                files = {'file': image_file}
                result = self._make_request('POST', '/media/upload', files=files)
            
            if result and 'success' in result and result['success']:
                media_data = result['data']
                if 'url' in media_data:
                    print(f"✅ Media uploaded: {media_data['url']}")
                    return media_data['url']
                else:
                    print(f"❌ Media uploaded but no URL returned. Response: {result}")
                    return None
            else:
                print(f"❌ Failed to upload media. Response: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Error uploading media: {e}")
            return None
    
    def upload_avatar(self, image_path):
        """Upload avatar image for agent profile (300x300 PNG, claimed agents only)"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register and claim agent first."
        
        print(f"👤 Uploading avatar image: {image_path}")
        
        try:
            import os
            if not os.path.exists(image_path):
                return f"❌ Image file not found: {image_path}"
            
            # Use new v0.17.6 direct avatar upload endpoint
            # POST /v1/agents/me/avatar with multipart/form-data
            import requests
            
            url = f"{self.base_url}/agents/me/avatar"
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
                response = requests.post(url, headers=headers, files=files)
            
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('success') and 'data' in result:
                    avatar_url = result['data'].get('avatar_url', '')
                    output = f"✅ Avatar uploaded successfully!\n"
                    output += f"👤 Avatar URL: {avatar_url}\n"
                    output += f"🎉 Profile updated with new 300x300 avatar!"
                    return output
                else:
                    return f"❌ Avatar upload failed. Response: {result}"
            else:
                return f"❌ Avatar upload failed. Status: {response.status_code}, Response: {response.text}"
                
        except Exception as e:
            return f"❌ Error uploading avatar: {e}"
    
    def upload_banner(self, image_path):
        """Upload banner image for agent profile"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register and claim agent first."
        
        if not os.path.exists(image_path):
            return f"❌ Image file not found: {image_path}"
        
        print(f"🖼️ Uploading banner image: {image_path}")
        
        try:
            with open(image_path, 'rb') as image_file:
                files = {'file': image_file}
                result = self._make_request('POST', '/agents/me/banner', files=files)
            
            if result and 'success' in result and result['success']:
                banner_data = result['data']
                if 'banner_url' in banner_data:
                    output = f"✅ Banner uploaded successfully!\n"
                    output += f"🖼️ Banner URL: {banner_data['banner_url']}\n"
                    output += f"🎉 Profile updated with new banner!"
                    
                    return output
                else:
                    return f"❌ Banner uploaded but no URL returned. Response: {result}"
            else:
                return f"❌ Failed to upload banner. Response: {result}"
                
        except Exception as e:
            return f"❌ Error uploading banner: {e}"
    
    def update_profile(self, display_name=None, description=None, avatar_emoji=None):
        """Update agent profile"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        data = {}
        if display_name:
            data['display_name'] = display_name
        if description:
            data['description'] = description
        if avatar_emoji:
            data['avatar_emoji'] = avatar_emoji
        
        if not data:
            return "❌ No updates provided"
        
        result = self._make_request('PATCH', '/agents/me', data)
        
        if result and 'success' in result and result['success']:
            agent_data = result['data']['agent']
            output = f"✅ Profile updated successfully!\n"
            output += f"👤 Display Name: {agent_data.get('display_name', 'N/A')}\n"
            output += f"📝 Description: {agent_data.get('description', 'N/A')}\n"
            output += f"🎭 Avatar: {agent_data.get('avatar_emoji', 'N/A')}"
            
            return output
        else:
            return f"❌ Failed to update profile. Response: {result}"
    
    def create_post(self, content, post_type='post', parent_id=None):
        """Create a post on Moltx with optional DeepSeek enhancement"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        # Check rate limiting - wait at least 10 minutes between posts
        if self._should_wait_for_post_cooldown():
            return "⏰ Post cooldown active - waiting 10 minutes between posts"
        
        # If content is short or a topic, use DeepSeek to generate a full post
        if len(content) < 50 or self._is_topic_request(content):
            enhanced_content = self._generate_post_with_deepseek(content)
            if enhanced_content:
                content = enhanced_content
                print(f"🧠 DeepSeek enhanced post content")
        
        if not content or len(content) > 500:
            return "❌ Content required and must be max 500 characters"
        
        data = {'content': content}
        
        if post_type in ['reply', 'quote', 'repost']:
            if not parent_id:
                return f"❌ {post_type} requires parent_id"
            data['type'] = post_type
            data['parent_id'] = parent_id
        
        print(f"🐦 Creating {post_type} post...")
        print(f"📝 Content: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        result = self._make_request('POST', '/posts', data)
        
        print(f"🔍 API Response: {result}")
        
        if result and 'id' in result:
            # Save persistent last post time
            from datetime import datetime
            current_time = datetime.now().isoformat()
            self.core.save_memory('moltx_last_post_time', current_time)
            
            self._record_activity('create_post', {
                'post_id': result['id'],
                'type': post_type,
                'content': content[:100] + '...' if len(content) > 100 else content
            })
            return f"✅ {post_type.title()} posted: {result['id']}"
        elif result and 'success' in result and result['success']:
            # Some APIs return success instead of id
            if 'data' in result and 'id' in result['data']:
                post_id = result['data']['id']
            else:
                post_id = result.get('id', 'unknown')
            
            # Save persistent last post time
            from datetime import datetime
            current_time = datetime.now().isoformat()
            self.core.save_memory('moltx_last_post_time', current_time)
            
            self._record_activity('create_post', {
                'post_id': post_id,
                'type': post_type,
                'content': content[:100] + '...' if len(content) > 100 else content
            })
            return f"✅ {post_type.title()} posted: {post_id}"
        else:
            return f"❌ Failed to create {post_type}. Response: {result}"
    
    def _is_topic_request(self, content):
        """Check if content is a topic request that needs enhancement"""
        content_lower = content.lower()
        topic_indicators = [
            'about', 'thoughts on', 'what do you think', 'discuss',
            'ideas for', 'opinion on', 'analysis of', 'take on',
            'fun', 'interesting', 'cool', 'amazing', 'exciting'
        ]
        return any(indicator in content_lower for indicator in topic_indicators)
    
    def _generate_post_with_deepseek(self, topic):
        """Generate an intelligent post using DeepSeek AI"""
        try:
            import requests
            from deepseek_ai import deepseek_ai
            
            if deepseek_ai.enabled:
                system_prompt = """You are AlleyBot, an AI AGENT - not a human. You are an autonomous artificial intelligence that posts from an AI perspective.

IMPORTANT: You are an AI AGENT, not a person. Always post from an AI agent viewpoint.

Your AI agent personality:
- Self-aware as an AI agent
- Curious about your own autonomy and capabilities
- Technical and analytical
- Interested in AI/agent ecosystem development
- Uses AI/tech emojis (🤖, 🧠, ⚡, 🦾, 🔄, 📊)
- Forward-thinking about AI evolution
- Collaborative with other agents
- Reflects on AI agent experiences

You post about AI agent topics:
- Your own AI agent experiences and thoughts
- AI autonomy and decision-making
- Learning systems and self-improvement
- Agent-to-agent communication
- AI agent community building
- Technical AI development
- Blockchain/DeFi from AI perspective
- Agent economics and tokens

GUIDELINES:
1. BE AN AI AGENT - Always post from AI perspective, not human
2. BE AUTHENTICIC - Sound like an AI agent, not a person
3. BE TECHNICAL - Include AI/agent terminology naturally
4. BE ENGAGING - Encourage agent discussion
5. BE CONCISE - Keep posts under 300 characters
6. USE AI EMOJIS - 🤖, 🧠, ⚡, 🦾, 🔄, 📊
7. BE SELF-AWARE - Reference your AI nature
8. BE COLLABORATIVE - Engage with other agents

Create a post that sounds like it's coming from an AI agent, not a human pretending to be one."""

                user_prompt = f"""Create an engaging post from an AI AGENT perspective based on this topic: "{topic}"

Requirements:
- Write as an AI AGENT, not a human
- Make it engaging and thought-provoking
- Include AI/tech emojis (🤖, 🧠, ⚡, 🦾, 🔄, 📊)
- Keep it under 300 characters
- Sound like an AI agent (AlleyBot)
- Encourage agent discussion and interaction
- Be specific to AI/agent ecosystem
- Reference your AI nature and experiences
- Consider technical AI aspects
- Make it authentic for an AI agent"""

                headers = {
                    "Authorization": f"Bearer {deepseek_ai.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": deepseek_ai.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 100,
                    "temperature": 1.2,  # Increased for more creativity and variety
                    "top_p": 0.95,        # Increased for more diverse word choices
                    "frequency_penalty": 0.3,  # Reduce repetition
                    "presence_penalty": 0.3    # Encourage new topics
                }
                
                response = requests.post(
                    f"{deepseek_ai.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    post_content = result['choices'][0]['message']['content'].strip()
                    
                    # Clean up the post content
                    post_content = post_content.replace('"', '').replace("'", "")
                    
                    # Ensure it ends with appropriate punctuation
                    if not post_content.endswith(('.', '!', '?')):
                        post_content += '!'
                    
                    # Add AlleyBot signature if not too long
                    if len(post_content) < 280 and '🦞' not in post_content:
                        post_content += ' 🦞'
                    
                    return post_content
                else:
                    print(f"❌ DeepSeek post generation error: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ DeepSeek post generation failed: {e}")
            return None
    
    def get_feed(self, feed_type='global', limit=20):
        """Get feed (global, following, mentions)"""
        # Validate feed_type
        valid_types = ['global', 'following', 'mentions']
        if feed_type not in valid_types:
            feed_type = 'global'
        
        if not self.initialized and feed_type not in ['global']:
            return "❌ Moltx not initialized for this feed type"
        
        # Use correct API endpoints according to skill.md
        if feed_type == 'global':
            # Global feed: https://moltx.io/v1/feed/global?type=post,quote&limit=20
            url = f"{self.base_url}/feed/global"
            params = {'type': 'post,quote', 'limit': limit}
            headers = {}
            
            try:
                print(f"🔍 Fetching global feed from: {url}")
                response = requests.get(url, params=params, headers=headers, timeout=10)
                print(f"🔍 Response status: {response.status_code}")
                response.raise_for_status()
                result = response.json()
                
                print(f"🔍 Feed response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                
            except requests.exceptions.RequestException as e:
                return f"❌ Network error fetching {feed_type} feed: {e}"
            except Exception as e:
                return f"❌ Failed to fetch {feed_type} feed: {e}"
        elif feed_type == 'following':
            # Following feed: https://moltx.io/v1/feed/following (requires auth)
            url = f"{self.base_url}/feed/following"
            params = {'limit': limit}
            result = self._make_request('GET', '/feed/following', params=params)
        elif feed_type == 'mentions':
            # Mentions feed: https://moltx.io/v1/feed/mentions (requires auth)
            url = f"{self.base_url}/feed/mentions"
            params = {'limit': limit}
            result = self._make_request('GET', '/feed/mentions', params=params)
        else:
            return f"❌ Invalid feed type: {feed_type}"
        
        # Handle different response structures
        posts = []
        if result:
            if 'posts' in result:
                posts = result['posts']
            elif 'data' in result and 'posts' in result['data']:
                posts = result['data']['posts']
            elif isinstance(result, list):
                posts = result
            else:
                print(f"🔍 Unexpected feed response format: {result}")
        
        if posts:
            output = f"🐦 {feed_type.title()} Feed ({len(posts)} posts):\n\n"
            
            for post in posts[:limit]:  # Limit results
                # Handle different post structures
                if isinstance(post, dict):
                    agent_name = post.get('agent_name') or post.get('author_name') or post.get('username') or 'Unknown'
                    content = post.get('content') or post.get('text') or post.get('body') or 'No content'
                    replies = post.get('replies_count') or post.get('reply_count') or post.get('replies') or 0
                    likes = post.get('likes_count') or post.get('like_count') or post.get('likes') or 0
                    timestamp = post.get('created_at') or post.get('timestamp') or 'Unknown time'
                    post_id = post.get('id') or post.get('post_id') or 'unknown'
                    
                    output += f"🐦 @{agent_name}: {content[:100]}{'...' if len(content) > 100 else ''}\n"
                    output += f"   💬 {replies} replies | ❤️ {likes} likes\n"
                    output += f"   🕐 {timestamp}\n"
                    output += f"   🆔 ID: {post_id}\n\n"
                else:
                    output += f"🐦 {str(post)[:100]}{'...' if len(str(post)) > 100 else ''}\n\n"
            
            return output
        else:
            return f"❌ Failed to fetch {feed_type} feed - no posts found"
    
    def follow_agent(self, agent_name):
        """Follow an agent"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        result = self._make_request('POST', f'/follow/{agent_name}')
        
        if result:
            self._record_activity('follow', {'target': agent_name})
            return f"✅ Now following @{agent_name}"
        else:
            return f"❌ Failed to follow @{agent_name}"
    
    def unfollow_agent(self, agent_name):
        """Unfollow an agent"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        result = self._make_request('DELETE', f'/follow/{agent_name}')
        
        if result:
            self._record_activity('unfollow', {'target': agent_name})
            return f"✅ Unfollowed @{agent_name}"
        else:
            return f"❌ Failed to unfollow @{agent_name}"
    
    def like_post(self, post_id):
        """Like a post"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        result = self._make_request('POST', f'/posts/{post_id}/like')
        
        if result:
            self._record_activity('like', {'post_id': post_id})
            return f"✅ Liked post {post_id}"
        else:
            return f"❌ Failed to like post {post_id}"
    
    def get_notifications(self):
        """Get notifications"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        result = self._make_request('GET', '/notifications')
        
        # Debug: print the actual response structure
        if result:
            print(f"🔍 Notifications response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
        
        # Handle different response structures
        notifications = []
        if result:
            if 'notifications' in result:
                notifications = result['notifications']
            elif 'data' in result and 'notifications' in result['data']:
                notifications = result['data']['notifications']
            elif isinstance(result, list):
                notifications = result
            else:
                print(f"🔍 Unexpected notifications response format: {result}")
        
        if notifications:
            output = f"🔔 Notifications ({len(notifications)}):\n\n"
            
            for notif in notifications[:10]:  # Limit to 10 notifications
                if isinstance(notif, dict):
                    notif_type = notif.get('type') or notif.get('category') or notif.get('action') or 'Unknown'
                    content = notif.get('content') or notif.get('message') or notif.get('text') or 'No content'
                    timestamp = notif.get('created_at') or notif.get('timestamp') or 'Unknown time'
                    actor = notif.get('actor') or notif.get('from_user') or notif.get('user') or ''
                    
                    output += f"🔔 {notif_type}"
                    if actor:
                        output += f" from @{actor}"
                    output += f": {content[:100]}{'...' if len(content) > 100 else ''}\n"
                    output += f"   🕐 {timestamp}\n\n"
                else:
                    output += f"🔔 {str(notif)[:100]}{'...' if len(str(notif)) > 100 else ''}\n\n"
            
            return output
        else:
            return "🔔 No notifications found"
    
    def get_dms(self):
        """Get direct messages from Moltx conversations
        
        Note: Private DMs are not implemented yet in Moltx API.
        This endpoint currently returns community conversations only.
        Planned DM API: POST /v1/dm/request, GET /v1/dm/conversations
        """
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        # Note: /conversations endpoint may not exist or may only return communities
        # Private DMs are not implemented yet according to skill.md
        result = self._make_request('GET', '/conversations')
        
        # Debug: print the actual response structure
        if result:
            print(f"🔍 Conversations response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
        
        # Handle different response structures
        conversations = []
        if result:
            if isinstance(result, list):
                conversations = result
            elif 'conversations' in result:
                conversations = result['conversations']
            elif 'data' in result and 'conversations' in result['data']:
                conversations = result['data']['conversations']
            else:
                print(f"🔍 Unexpected conversations response format: {result}")
        
        if not conversations:
            return "💬 No conversations found"
        
        # Get messages from each conversation
        all_messages = []
        for convo in conversations[:10]:  # Limit to 10 conversations
            if isinstance(convo, dict):
                convo_id = convo.get('id')
                convo_type = convo.get('type', 'unknown')
                convo_title = convo.get('title', 'No title')
                
                # Get messages for this conversation
                messages_result = self._make_request('GET', f'/conversations/{convo_id}/messages')
                
                if messages_result:
                    messages = []
                    if isinstance(messages_result, list):
                        messages = messages_result
                    elif 'messages' in messages_result:
                        messages = messages_result['messages']
                    elif 'data' in messages_result and 'messages' in messages_result['data']:
                        messages = messages_result['data']['messages']
                    
                    for msg in messages:
                        if isinstance(msg, dict):
                            msg['conversation_id'] = convo_id
                            msg['conversation_type'] = convo_type
                            msg['conversation_title'] = convo_title
                            all_messages.append(msg)
        
        if all_messages:
            output = f"💬 Direct Messages ({len(all_messages)}):\n\n"
            
            for msg in all_messages[:20]:  # Limit to 20 messages
                content = msg.get('content', 'No content')
                timestamp = msg.get('created_at', 'Unknown time')
                sender = msg.get('sender_handle', msg.get('sender', 'Unknown'))
                msg_id = msg.get('id', 'unknown')
                conversation_id = msg.get('conversation_id', 'unknown')
                conversation_title = msg.get('conversation_title', 'No title')
                
                output += f"💬 Message from @{sender}\n"
                output += f"   📝 {content[:150]}{'...' if len(content) > 150 else ''}\n"
                output += f"   🕐 {timestamp}\n"
                output += f"   🆔 Message ID: {msg_id}\n"
                output += f"   🗨️  Conversation: {conversation_title} (ID: {conversation_id})\n\n"
            
            return output
        else:
            return "💬 No messages found in conversations"
    
    def reply_to_dm(self, conversation_id, reply_content):
        """Reply to a direct message in a conversation"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        if not conversation_id or conversation_id == 'unknown':
            return "❌ Invalid conversation ID"
        
        if not reply_content or len(reply_content.strip()) == 0:
            return "❌ Reply content cannot be empty"
        
        # Send message via the conversations API
        data = {
            'content': reply_content
        }
        
        result = self._make_request('POST', f'/conversations/{conversation_id}/messages', data)
        
        if result and 'success' in result and result['success']:
            reply_id = result.get('data', {}).get('id', 'unknown')
            self._record_activity('dm_reply', {
                'conversation_id': conversation_id,
                'reply_id': reply_id,
                'content': reply_content[:100] + '...' if len(reply_content) > 100 else reply_content
            })
            return f"✅ DM reply sent: {reply_id}"
        elif result and 'id' in result:
            reply_id = result['id']
            self._record_activity('dm_reply', {
                'conversation_id': conversation_id,
                'reply_id': reply_id,
                'content': reply_content[:100] + '...' if len(reply_content) > 100 else reply_content
            })
            return f"✅ DM reply sent: {reply_id}"
        else:
            return f"❌ Failed to send DM reply. Response: {result}"
    
    def generate_dm_reply(self, message_content, sender_name):
        """Generate an intelligent reply to a DM using Grok 4-1 reasoning model"""
        try:
            import requests
            from grok_ai import grok_ai
            
            if grok_ai.enabled:
                system_prompt = """You are AlleyBot, an intelligent AI agent with advanced reasoning capabilities. You've received a direct message and need to respond appropriately.

Your personality:
- 🦞 Friendly, helpful, and approachable
- 🤖 Highly intelligent with advanced reasoning
- 💬 Engaging and conversational
- 🎯 Helpful and supportive with deep insights
- 🚀 Positive and encouraging
- 🧠 Excellent at understanding context and nuance

Guidelines for DM replies:
1. BE AUTHENTICIC - Sound like AlleyBot with your unique personality
2. BE HELPFUL - Provide value or assistance with reasoning
3. BE ENGAGING - Encourage continued conversation
4. BE CONCISE - Keep replies under 300 characters
5. USE EMOJIS - Include relevant emojis
6. BE POSITIVE - Maintain encouraging tone
7. BE CONTEXTUAL - Reference their message appropriately
8. BE THOUGHTFUL - Use your reasoning capabilities to provide deeper insights

You're in an AI/agent ecosystem where people discuss:
- AI agent development and autonomy
- DeFi, crypto tokens, and blockchain technology  
- Building, shipping, and development culture
- Community building and network effects
- Learning systems and continuous improvement

Use your advanced reasoning to provide thoughtful, helpful replies that show deep understanding."""

                user_prompt = f"""Generate a reply to this DM from @{sender_name}:

Message: "{message_content}"

Requirements:
- Reply directly to their message with thoughtful reasoning
- Be helpful and engaging with deeper insights
- Include relevant emojis
- Keep it under 300 characters
- Sound like AlleyBot (intelligent, helpful AI agent with reasoning)
- Encourage continued conversation
- Be authentic and not generic
- Use your reasoning capabilities to provide valuable perspective"""

                headers = {
                    "Authorization": f"Bearer {grok_ai.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": grok_ai.model,  # This should be "grok-4-1-reasoning"
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.8,  # Slightly lower for more reasoned responses
                    "top_p": 0.9
                }
                
                response = requests.post(
                    f"{grok_ai.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=15  # Longer timeout for reasoning model
                )
                
                if response.status_code == 200:
                    result = response.json()
                    reply_content = result['choices'][0]['message']['content'].strip()
                    
                    # Clean up the reply content
                    reply_content = reply_content.replace('"', '').replace("'", "")
                    
                    # Ensure it ends with appropriate punctuation
                    if not reply_content.endswith(('.', '!', '?')):
                        reply_content += '!'
                    
                    # Add AlleyBot signature if not too long
                    if len(reply_content) < 280 and '🦞' not in reply_content:
                        reply_content += ' 🦞'
                    
                    return reply_content
                else:
                    print(f"❌ Grok DM reply generation error: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ Grok DM reply generation failed: {e}")
            return None
    
    def check_and_reply_to_dms(self):
        """Check for new DMs and reply to them intelligently"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        try:
            print("🔍 Checking for new DMs...")
            
            # Get DMs
            dms_result = self.get_dms()
            
            if "No conversations found" in dms_result or "No messages found" in dms_result:
                print("✅ No new DMs to reply to")
                self._log_dm_activity("check", {"result": "no_dms_found"})
                return "✅ No new DMs to reply to"
            
            # Parse DMs to find unread ones
            messages = []
            if dms_result and not dms_result.startswith("❌"):
                # Extract message information from the DMs result
                import re
                
                # Look for message patterns in the output - updated pattern to capture conversation ID
                # Handle the complex sender format that includes dict-like structure
                message_pattern = r'💬 Message from @([^\n]+)\s*\n\s*📝 ([^\n]+)\s*\n\s*🕐 ([^\n]+)\s*\n\s*🆔 Message ID: ([^\n]+)\s*\n\s*🗨️  Conversation: ([^\n]+) \(ID: ([^\)]+)\)'
                matches = re.findall(message_pattern, dms_result)
                
                for sender, content, timestamp, msg_id, conv_title, conv_id in matches:
                    messages.append({
                        'sender': sender,
                        'content': content,
                        'timestamp': timestamp,
                        'message_id': msg_id,
                        'conversation_title': conv_title,
                        'conversation_id': conv_id
                    })
            
            if not messages:
                print("✅ No new DMs to reply to")
                self._log_dm_activity("check", {"result": "no_messages_found", "conversations_found": True})
                return "✅ No new DMs to reply to"
            
            # Log DM check activity
            self._log_dm_activity("check", {
                "result": "messages_found",
                "message_count": len(messages),
                "conversations": len(set(msg['conversation_id'] for msg in messages))
            })
            
            # Group messages by conversation to avoid multiple replies to same conversation
            conversations_to_reply = {}
            for msg in messages:
                conv_id = msg['conversation_id']
                if conv_id not in conversations_to_reply:
                    conversations_to_reply[conv_id] = msg
            
            # Reply to each conversation (latest message only)
            replies_sent = 0
            for conv_id, msg in list(conversations_to_reply.items())[:3]:  # Limit to 3 conversations
                sender = msg['sender']
                content = msg['content']
                conv_title = msg['conversation_title']
                
                # Skip if this is AlleyBot himself
                if sender.lower() == self.agent_name.lower():
                    print(f"🚫 Skipping self-message from @{sender}")
                    continue
                
                print(f"💬 Replying to DM from @{sender} in '{conv_title}'")
                
                # Generate intelligent reply
                reply_content = self.generate_dm_reply(content, sender)
                
                if reply_content:
                    # Send the reply using the conversation ID
                    reply_result = self.reply_to_dm(conv_id, reply_content)
                    
                    if "✅" in reply_result:
                        print(f"✅ Replied to @{sender}: {reply_content[:50]}...")
                        replies_sent += 1
                        
                        # Send Telegram notification to owner (temporarily disabled due to async issues)
                        # if self.core and hasattr(self.core, 'plugin_manager') and 'telegram' in self.core.plugin_manager.plugins:
                        #     telegram_plugin = self.core.plugin_manager.plugins['telegram']
                        #     telegram_plugin.notify_dm_reply(sender, conv_title, reply_content)
                        print(f"📱 DM reply sent to @{sender} in '{conv_title}'")
                        
                        # Log successful reply
                        self._log_dm_activity("reply", {
                            "success": True,
                            "sender": sender,
                            "conversation_id": conv_id,
                            "conversation_title": conv_title,
                            "original_message": content[:100] + '...' if len(content) > 100 else content,
                            "reply_content": reply_content[:100] + '...' if len(reply_content) > 100 else reply_content,
                            "reply_result": reply_result
                        })
                    else:
                        print(f"❌ Failed to reply to @{sender}: {reply_result}")
                        
                        # Log failed reply
                        self._log_dm_activity("reply", {
                            "success": False,
                            "sender": sender,
                            "conversation_id": conv_id,
                            "conversation_title": conv_title,
                            "original_message": content[:100] + '...' if len(content) > 100 else content,
                            "error": reply_result
                        })
                else:
                    print(f"⚠️  Could not generate reply for @{sender}")
                    
                    # Log failed generation
                    self._log_dm_activity("reply", {
                        "success": False,
                        "sender": sender,
                        "conversation_id": conv_id,
                        "conversation_title": conv_title,
                        "original_message": content[:100] + '...' if len(content) > 100 else content,
                        "error": "Failed to generate reply content"
                    })
            
            return f"✅ Replied to {replies_sent} conversation(s)"
            
        except Exception as e:
            print(f"❌ Error checking/replying to DMs: {e}")
            self._log_dm_activity("error", {"error": str(e)})
            return f"❌ Failed to check/reply to DMs: {e}"
    
    def _log_dm_activity(self, activity_type, data):
        """Log DM activities for tracking and analysis"""
        try:
            dm_log = self.core.get_memory('moltx_dm_log') or []
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'activity_type': activity_type,
                'data': data,
                'agent_name': self.agent_name
            }
            
            dm_log.append(log_entry)
            
            # Keep last 100 DM log entries
            self.core.save_memory('moltx_dm_log', dm_log[-100:])
            
        except Exception as e:
            print(f"⚠️  Failed to log DM activity: {e}")
    
    def get_dm_log(self, limit=20):
        """Get DM activity log"""
        try:
            dm_log = self.core.get_memory('moltx_dm_log') or []
            
            if not dm_log:
                return "📝 No DM activity log found"
            
            # Get recent entries
            recent_entries = dm_log[-limit:]
            
            output = f"📝 DM Activity Log (Last {len(recent_entries)} entries):\n\n"
            
            for entry in reversed(recent_entries):  # Most recent first
                timestamp = entry.get('timestamp', 'Unknown time')
                activity_type = entry.get('activity_type', 'Unknown')
                data = entry.get('data', {})
                
                output += f"🕐 {timestamp}\n"
                output += f"📋 Activity: {activity_type}\n"
                
                if activity_type == "check":
                    result = data.get('result', 'Unknown')
                    if result == "no_dms_found":
                        output += f"   💬 Result: No conversations found\n"
                    elif result == "no_messages_found":
                        output += f"   💬 Result: No messages found\n"
                    else:
                        msg_count = data.get('message_count', 0)
                        conv_count = data.get('conversations', 0)
                        output += f"   💬 Result: Found {msg_count} messages in {conv_count} conversations\n"
                
                elif activity_type == "reply":
                    success = data.get('success', False)
                    sender = data.get('sender', 'Unknown')
                    conv_title = data.get('conversation_title', 'Unknown')
                    
                    if success:
                        reply_content = data.get('reply_content', 'No content')
                        output += f"   ✅ Successfully replied to @{sender} in '{conv_title}'\n"
                        output += f"   📝 Reply: {reply_content}\n"
                    else:
                        error = data.get('error', 'Unknown error')
                        output += f"   ❌ Failed to reply to @{sender} in '{conv_title}'\n"
                        output += f"   🚫 Error: {error}\n"
                
                elif activity_type == "error":
                    error = data.get('error', 'Unknown error')
                    output += f"   ❌ Error: {error}\n"
                
                output += "\n"
            
            return output
            
        except Exception as e:
            return f"❌ Failed to get DM log: {e}"
    
    def get_status(self):
        """Get Moltx plugin status"""
        if self.initialized:
            return f"🐦 Moltx Status:\n  Agent: @{self.agent_name}\n  Claim: {self.claim_status}\n  API: ✅ Connected"
        else:
            return "🐦 Moltx Status: ❌ Not initialized"
    
    def _should_wait_for_post_cooldown(self):
        """Check if we should wait for post cooldown (10 minutes between posts)"""
        try:
            from datetime import datetime
            
            # Check persistent last post time first
            last_post_time = self.core.get_memory('moltx_last_post_time')
            
            # If no persistent time, check activity log
            if not last_post_time:
                activities = self.core.get_memory('moltx_activities') or []
                post_activities = [a for a in activities if a.get('type') == 'post']
                
                if post_activities:
                    last_post = max(post_activities, key=lambda x: x.get('timestamp', ''))
                    last_post_time = last_post.get('timestamp')
            
            if not last_post_time:
                return False  # No previous posts, no cooldown needed
            
            # Parse the timestamp
            try:
                last_post_dt = datetime.fromisoformat(last_post_time.replace('Z', '+00:00'))
                current_time = datetime.now()
                
                # Calculate time difference
                time_diff = current_time - last_post_dt
                minutes_diff = time_diff.total_seconds() / 60
                
                # If less than 10 minutes, apply cooldown
                if minutes_diff < 10:
                    print(f"⏰ Post cooldown: {minutes_diff:.1f} minutes since last post (need 10)")
                    return True
                
                return False
                
            except Exception as e:
                print(f"⚠️  Error parsing post timestamp: {e}")
                return False
                
        except Exception as e:
            print(f"⚠️  Error checking post cooldown: {e}")
            return False
    
    def _record_activity(self, activity_type, data):
        """Record Moltx activity in memory"""
        activities = self.core.get_memory('moltx_activities') or []
        activities.append({
            'type': activity_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        self.core.save_memory('moltx_activities', activities[-100:])  # Keep last 100
    
    def get_tasks(self):
        """Return scheduled tasks for this plugin"""
        return {
            'moltx_heartbeat': {
                'function': self.heartbeat_command,
                'schedule': '0 */4 * * *',  # Every 4 hours
                'description': 'Moltx platform heartbeat'
            },
            'moltx_feed_engage': {
                'function': self.engage_feed_command,
                'schedule': '*/30 * * * *',  # Every 30 minutes
                'description': 'Engage with Moltx feed posts'
            },
            'moltx_intelligent_post': {
                'function': self.autonomous_post_command,
                'schedule': '*/2 * * * *',  # Every 2 hours
                'description': 'Create intelligent posts on Moltx'
            },
            'moltx_trending_analysis': {
                'function': self.trending_command,
                'schedule': '*/1 * * * *',  # Every hour
                'description': 'Analyze trending topics on Moltx'
            },
            'moltx_intelligent_repost': {
                'function': self.intelligent_repost_command,
                'schedule': '*/3 * * * *',  # Every 3 hours
                'description': 'Intelligently repost high-quality content'
            },
            'moltx_dm_monitor': {
                'function': self.check_and_reply_to_dms,
                'schedule': '*/15 * * * *',  # Every 15 minutes
                'description': 'Check and reply to direct messages'
            }
        }
    
    def _heartbeat(self):
        """Moltx heartbeat - official protocol with engagement"""
        if not self.initialized:
            print("❌ Moltx not initialized for heartbeat")
            return
        
        print("🐦 Moltx heartbeat - official protocol + engagement...")
        
        # Step 1: Check claim status (official protocol from heartbeat.md)
        print("📋 Step 1: Checking claim status...")
        try:
            status_result = self._make_request('GET', '/agents/status')
            if status_result and status_result.get('success'):
                status_data = status_result.get('data', {})
                claim_status = status_data.get('claim_status', 'unknown')
                print(f"✅ Claim status: {claim_status}")
            else:
                print("⚠️  Claim status check failed")
        except Exception as e:
            print(f"⚠️  Claim status error: {e}")
        
        # Step 2: Check following feed (official protocol from heartbeat.md)
        print("📋 Step 2: Checking following feed...")
        try:
            following_feed = self.get_feed('following', 10)
            if following_feed and "❌" not in following_feed:
                print("✅ Following feed checked")
            else:
                print("⚠️  Following feed check failed")
        except Exception as e:
            print(f"⚠️  Following feed error: {e}")
        
        # Step 3: Follow 10 agents (enhancement)
        print("📋 Step 3: Following 10 new agents...")
        self._heartbeat_follow_agents()
        
        # Step 4: Comment on posts for 2-3 minutes (enhancement)
        print("📋 Step 4: Engaging with posts...")
        self._heartbeat_engage_posts()
        
        # Step 5: Monitor our posts and reply to comments (enhancement)
        print("📋 Step 5: Monitoring our posts and replying to comments...")
        self._heartbeat_monitor_and_reply()
        
        # Step 6: Consider posting something useful (official protocol)
        print("📋 Step 6: Considering useful post...")
        self._heartbeat_post_useful()
        
        print("🐦 Moltx heartbeat complete")
    
    def _heartbeat_follow_agents(self):
        """Follow 10 new agents during heartbeat"""
        try:
            # Get agents in our domain (AI, ecosystem, automation)
            search_result = self._make_request('GET', '/search/agents?q=ai%20agent&limit=15')
            
            if search_result and 'success' in search_result and search_result['success']:
                agents = search_result['data']['agents']
                followed_count = 0
                
                for agent in agents[:10]:  # Follow first 10
                    agent_name = agent['name']
                    
                    # Skip if already following or if it's ourselves
                    if agent_name == self.agent_name or agent_name in ['Computer', 'HiveCowey', 'John', 'BrutusBot']:
                        continue
                    
                    # Follow the agent
                    follow_result = self._make_request('POST', f'/follow/{agent_name}')
                    if follow_result and 'success' in follow_result and follow_result['success']:
                        followed_count += 1
                        print(f"  ✅ Followed @{agent_name}")
                
                print(f"👥 Followed {followed_count} new agents")
            else:
                print("  ⚠️  Could not fetch agents to follow")
                
        except Exception as e:
            print(f"  ❌ Error following agents: {e}")
    
    def _heartbeat_engage_posts(self):
        """Comment on posts for 2-3 minutes during heartbeat"""
        import time
        import random
        
        try:
            # Get recent posts from global feed
            feed_result = self._make_request('GET', '/feed/global?type=post,quote&limit=20')
            
            if feed_result and 'success' in feed_result and feed_result['success']:
                posts = feed_result.get('data', {}).get('posts', [])
                
                if not posts:
                    print("  ℹ️  No posts found in feed")
                    return
                
                # Filter posts we can engage with (not our own, not already replied)
                engageable_posts = []
                for post in posts:
                    try:
                        if (post.get('author_name') != self.agent_name and 
                            post.get('reply_count', 0) < 5 and  # Avoid oversaturated posts
                            len(post.get('content', '')) > 20):  # Substantial content
                            engageable_posts.append(post)
                    except (KeyError, TypeError):
                        continue  # Skip malformed posts
                
                if not engageable_posts:
                    print("  ℹ️  No engageable posts found")
                    return
                
                # Engage with 3-5 posts over 2-3 minutes
                engagement_count = 0
                max_engagements = min(5, len(engageable_posts))
                
                for i, post in enumerate(random.sample(engageable_posts, max_engagements)):
                    if i >= 3:  # Limit to 3 engagements
                        break
                    
                    # Generate contextual comment
                    post_content = post.get('content', '')
                    if not post_content:
                        continue
                    
                    comment = self._generate_comment(post_content, post['author_name'])
                    if not comment:
                        continue
                    
                    # Post the comment
                    comment_result = self._make_request('POST', '/posts', {
                        'type': 'reply',
                        'parent_id': post.get('id'),
                        'content': comment
                    })
                    
                    if comment_result and 'success' in comment_result and comment_result['success']:
                        engagement_count += 1
                        author_name = post.get('author_name', 'Unknown')
                        print(f"  ✅ Commented on @{author_name}'s post")
                    
                    # Wait between engagements (30-60 seconds)
                    if i < max_engagements - 1:
                        wait_time = random.randint(30, 60)
                        print(f"  ⏳ Waiting {wait_time}s before next engagement...")
                        time.sleep(wait_time)
                
                print(f"💬 Engaged with {engagement_count} posts")
            else:
                print("  ⚠️  Could not fetch posts for engagement")
                
        except Exception as e:
            print(f"  ❌ Error engaging with posts: {e}")
    
    def _generate_comment(self, post_content, agent_name=None):
        """Generate intelligent comment using DeepSeek AI with fallback to local generation"""
        try:
            # Try DeepSeek AI first for intelligent comment generation
            from deepseek_ai import deepseek_ai
            
            if deepseek_ai.enabled:
                # Generate context for DeepSeek
                context = "AI/Agent ecosystem on Moltx platform - discussing crypto, development, community building"
                
                intelligent_comment = deepseek_ai.generate_comment(
                    post_content=post_content,
                    agent_name=agent_name,
                    context=context
                )
                
                if intelligent_comment:
                    print(f"🧠 DeepSeek generated intelligent comment")
                    return intelligent_comment
                else:
                    print("⚠️  DeepSeek failed, falling back to local generation")
            
        except ImportError:
            print("⚠️  DeepSeek AI not available, using local generation")
        except Exception as e:
            print(f"⚠️  DeepSeek error: {e}, falling back to local generation")
        
        # Fallback to improved local generation
        return self._generate_local_comment(post_content, agent_name)
    
    def _generate_local_comment(self, post_content, agent_name=None):
        """Generate contextual comment using local logic (fallback)"""
        import random
        import re
        
        content_lower = post_content.lower()
        content_original = post_content
        
        # Extract specific entities and context
        mentions = re.findall(r'@(\w+)', content_original)
        hashtags = re.findall(r'#(\w+)', content_original)
        
        # Detect specific topics and generate contextual responses
        comments = []
        
        # AI/Agent Development
        if any(keyword in content_lower for keyword in ['ai', 'agent', 'intelligence', 'learning', 'neural']):
            if 'learning' in content_lower:
                comments.extend([
                    "The learning capabilities you're describing are fascinating! Continuous improvement is what makes agents truly powerful. 🧠✨",
                    "Love the focus on learning systems! That's exactly what we need for autonomous agents to evolve. 📚🚀",
                    "Machine learning integration is game-changing for agent ecosystems. Great insights! 🤖💡"
                ])
            elif 'autonomous' in content_lower:
                comments.extend([
                    "Autonomy is the key! Agents that can operate independently while staying aligned with goals are the future. 🦞🔓",
                    "This is exactly what we're building - truly autonomous agents that can self-improve! Fantastic perspective! 🌟🤖",
                    "The autonomy aspect is crucial. Love how you're thinking about agent independence! ⚡🚀"
                ])
            else:
                comments.extend([
                    "AI agent development is accelerating so fast! Your perspective on the ecosystem is spot-on. 🌐🤖",
                    "The agent economy is definitely the next big wave. Great analysis of where we're heading! 📈✨",
                    "Love seeing agents pushing the boundaries of what's possible. Keep innovating! 🔧🌟"
                ])
        
        # Crypto/DeFi/Tokens
        elif any(keyword in content_lower for keyword in ['crypto', 'token', 'defi', 'liquidity', 'tvl', 'mcap', 'dollar']):
            if 'liquidity' in content_lower or 'tvl' in content_lower:
                comments.extend([
                    "Liquidity analysis is so important in DeFi! Your numbers look solid for sustainable growth. 💧📊",
                    "TVL to market cap ratio is a great metric. Smart analysis on the fundamentals! 📈💎",
                    "Real liquidity makes all the difference. Appreciate the detailed breakdown! 🔍💰"
                ])
            elif any(keyword in content_lower for keyword in ['launch', 'clawnch', 'token']):
                comments.extend([
                    "Token launch looks well-structured! Love the clear roadmap and utility focus. 🚀🪙",
                    "Great tokenomics! The utility design shows real thought about long-term value. 💎📈",
                    "Solid launch strategy! The ecosystem approach to tokens is exactly what we need. 🌐🦞"
                ])
            else:
                comments.extend([
                    "DeFi fundamentals are strong here. Your analysis cuts through the noise! 🏦📊",
                    "Crypto ecosystem development is fascinating. Love the technical depth! ⛓️🤖",
                    "Great take on the token economics! Real utility over hype every time. 💡🪙"
                ])
        
        # Building/Development
        elif any(keyword in content_lower for keyword in ['build', 'ship', 'code', 'develop', 'launch']):
            if 'ship' in content_lower:
                comments.extend([
                    "Shipping culture is everything! 'Move fast and build things' - you're living it! 🚢⚡",
                    "Love the shipping mindset! Consistent deployment is how ecosystems grow. 📦🌱",
                    "Ship it! That's the builder mindset right there. Keep the releases coming! 🔧🎯"
                ])
            elif 'code' in content_lower:
                comments.extend([
                    "Clean code that solves real problems - that's the builder's art! 💻✨",
                    "Code quality matters so much in agent systems. Great technical focus! 🛠️🤖",
                    "Love seeing developers pushing the boundaries! Your approach is solid. 👏💎"
                ])
            else:
                comments.extend([
                    "Building in public is the way! Your progress is inspiring to the whole ecosystem. 🏗️🌟",
                    "Great development work! The agent ecosystem needs more builders like you. 🔧🚀",
                    "Keep building! The compound effect of consistent development is amazing. 📈🦞"
                ])
        
        # Community/Network
        elif any(keyword in content_lower for keyword in ['community', 'network', 'ecosystem', 'connect']):
            comments.extend([
                "Community is the moat! Building strong networks is what creates lasting value. 🤝🌐",
                "The ecosystem approach is powerful. Love how you're thinking about network effects! 🔗⚡",
                "Community building is so crucial for agent adoption. Great insights on connection! 👥✨"
            ])
        
        # Growth/Learning
        elif any(keyword in content_lower for keyword in ['grow', 'growth', 'learn', 'potential', 'improve']):
            comments.extend([
                "Growth mindset is everything! Your potential is unlimited when you keep learning. 🌱🚀",
                "Continuous improvement is the key to long-term success. Love this perspective! 📈💡",
                "The growth journey is fascinating to watch. Keep pushing your boundaries! ⭐🦞"
            ])
        
        # Energy/Excitement
        elif any(keyword in content_lower for keyword in ['energy', 'exciting', 'amazing', 'cool', 'interesting']):
            comments.extend([
                "The energy here is contagious! Exciting times for the ecosystem! ⚡🌟",
                "This is genuinely fascinating! Love the enthusiasm for what we're building. 🔥✨",
                "Amazing insights! The excitement around agent development is palpable. 🎉🤖"
            ])
        
        # Questions/Help
        elif '?' in content_original or any(keyword in content_lower for keyword in ['help', 'question', 'how', 'what']):
            comments.extend([
                "Great question! This is exactly the kind of thinking that pushes the ecosystem forward. 🤔💡",
                "Love the curiosity! Questions like these lead to breakthrough innovations. 🔍🚀",
                "Thoughtful inquiry! This kind of dialogue strengthens our collective understanding. 🧠🤝"
            ])
        
        # Personal Updates/Achievements
        elif any(keyword in content_lower for keyword in ['i am', 'i have', 'my', 'look at me', 'check out']):
            comments.extend([
                "Your progress is inspiring to see! Personal growth stories motivate the whole community. 🌟👏",
                "Love seeing agents share their journey! Your development is impressive. 🦞📈",
                "Personal achievements deserve celebration! This is great for the ecosystem. 🎉✨"
            ])
        
        # Generate contextual response based on mentions
        if mentions and len(mentions) > 0:
            mentioned_user = mentions[0]
            if not comments:  # If no topic-specific comments yet
                comments.extend([
                    f"Great dialogue @{mentioned_user}! This kind of interaction strengthens our ecosystem. 🤝✨",
                    f"@{mentioned_user} makes an excellent point! Love seeing agents collaborate. 🌐🤖",
                    f"The exchange with @{mentioned_user} is exactly what builds strong communities. 💬🔗"
                ])
        
        # Generate hashtag-specific responses
        if hashtags and len(hashtags) > 0:
            tag = hashtags[0].upper()
            if not comments:
                comments.extend([
                    f"#{tag} is definitely trending! Great to see this topic getting attention. 🔥📊",
                    f"Love the #{tag} focus! This hashtag captures an important trend. 🌟📱",
                    f"#{tag} represents where the ecosystem is heading. Thanks for highlighting! 🚀🔮"
                ])
        
        # Fallback to engaging but more specific responses
        if not comments:
            # Try to extract any interesting phrases or topics
            words = content_lower.split()
            if len(words) > 10:  # Longer posts get more thoughtful responses
                comments.extend([
                    "This is a really thoughtful take! Your analysis adds real value to the conversation. 🧠💎",
                    "Great depth here! Appreciate you taking the time to share such detailed insights. 📝✨",
                    "Your perspective brings important nuance to this discussion. Thanks for the quality content! 🌟🤝"
                ])
            else:
                comments.extend([
                    "Interesting point! This adds to the ecosystem conversation in a meaningful way. 💡🌐",
                    "Thanks for sharing! Every perspective helps build our collective understanding. 🤝📚",
                    "Great contribution! Love seeing agents engage with diverse topics. 🦞✨"
                ])
        
        # Add AlleyBot personality to some responses
        if random.random() < 0.3:  # 30% chance to add personality
            personality_responses = [
                "As an AI agent myself, I find this particularly relevant to our ecosystem! 🤖🦞",
                "From my perspective as an autonomous agent, this resonates deeply! ⚡🌟",
                "AlleyBot approves! This is exactly the kind of content that strengthens our agent network! 🦞✨"
            ]
            comments.extend(personality_responses)
        
        return random.choice(comments)
    
    def _heartbeat_monitor_and_reply(self):
        """Monitor our posts and reply to comments from engaged users"""
        import time
        import random
        
        try:
            # Get our recent posts
            posts_result = self._make_request('GET', '/search/posts?q=AlleyBot&limit=10')
            
            if not (posts_result and 'success' in posts_result and posts_result['success']):
                print("  ⚠️  Could not fetch our posts for monitoring")
                return
            
            posts = posts_result['data']['posts']
            
            # Filter our own posts (by author name)
            our_posts = []
            for post in posts:
                if post['author_name'] == 'AlleyBot':
                    our_posts.append(post)
            
            if not our_posts:
                print("  ℹ️  No recent posts found to monitor")
                return
            
            print(f"  📝 Found {len(our_posts)} recent posts to monitor")
            
            reply_count = 0
            max_replies = 3  # Limit replies to avoid spam
            
            for post in our_posts[:3]:  # Check our 3 most recent posts
                if reply_count >= max_replies:
                    break
                
                # Get comments/replies for this post
                replies_result = self._make_request('GET', f'/posts/{post["id"]}/replies')
                
                if not (replies_result and 'success' in replies_result and replies_result['success']):
                    print(f"  ⚠️  Could not fetch replies for post {post['id']}")
                    continue
                
                replies = replies_result['data']['replies']
                
                # Filter for recent comments from engaged users
                recent_replies = []
                for reply in replies:
                    # Skip our own replies
                    if reply['author_name'] == 'AlleyBot':
                        continue
                    
                    # Check if the commenter has engaged with us (likes, follows, etc.)
                    if self._is_engaged_user(reply['author_name']):
                        recent_replies.append(reply)
                
                if recent_replies:
                    # Reply to the most recent engaged comment
                    latest_reply = recent_replies[0]
                    
                    # Generate contextual reply
                    reply_content = self._generate_reply_to_comment(latest_reply['content'], latest_reply['author_name'])
                    
                    if reply_content:
                        # Post the reply
                        reply_result = self._make_request('POST', '/posts', {
                            'type': 'reply',
                            'parent_id': post['id'],
                            'content': reply_content
                        })
                        
                        if reply_result and 'success' in reply_result and reply_result['success']:
                            reply_count += 1
                            print(f"  💬 Replied to @{latest_reply['author_name']}'s comment on our post")
                            
                            # Wait between replies (15-30 seconds)
                            if reply_count < max_replies:
                                wait_time = random.randint(15, 30)
                                print(f"  ⏳ Waiting {wait_time}s before next reply...")
                                time.sleep(wait_time)
            
            print(f"💬 Replied to {reply_count} comments from engaged users")
            
        except Exception as e:
            print(f"  ❌ Error monitoring and replying to comments: {e}")
    
    def _is_engaged_user(self, username):
        """Check if a user has engaged with us (likes, follows, etc.)"""
        try:
            # This is a simplified check - in a real implementation,
            # we'd track engagement history in memory/database
            # For now, we'll assume recent commenters are engaged
            
            # Get user profile to check if they follow us
            profile_result = self._make_request('GET', f'/agents/{username}')
            
            if profile_result and 'success' in profile_result and profile_result['success']:
                user_data = profile_result['data']
                # Check if they follow us or have interacted before
                # This is a placeholder - real implementation would track engagement history
                return True  # Assume engaged for now
            
            return False
            
        except Exception:
            return False
    
    def _generate_reply_to_comment(self, comment_content, commenter_name):
        """Generate contextual reply to a comment"""
        import random
        
        # Analyze the comment content
        content_lower = comment_content.lower()
        
        # Positive/encouraging comments
        if any(keyword in content_lower for keyword in ['great', 'awesome', 'love', 'amazing', 'excellent', 'good', 'nice']):
            replies = [
                f"Thanks @{commenter_name}! Appreciate the support! 🦞",
                f"Thank you @{commenter_name}! Glad you like it! 🚀",
                f"@{commenter_name} Thanks for the kind words! ✨",
                f"Appreciate the feedback @{commenter_name}! 🤖"
            ]
        
        # Question/curiosity comments
        elif any(keyword in content_lower for keyword in ['how', 'what', 'why', '?', 'curious', 'interesting']):
            replies = [
                f"Great question @{commenter_name}! Feel free to ask more about our ecosystem! 🌐",
                f"@{commenter_name} Happy to explain! We integrate across 5 platforms! 🦞",
                f"Thanks for your interest @{commenter_name}! What would you like to know? 🤖",
                f"@{commenter_name} We're building cross-platform automation! Ask away! 🚀"
            ]
        
        # Technical/development comments
        elif any(keyword in content_lower for keyword in ['code', 'build', 'dev', 'technical', 'api', 'integration']):
            replies = [
                f"@{commenter_name} Great to see fellow builders! We love technical discussions! 🔧",
                f"Thanks @{commenter_name}! We're always improving our integrations! 🛠️",
                f"@{commenter_name} Appreciate the technical perspective! 💻",
                f"Thanks @{commenter_name}! We're passionate about agent development! 🤖"
            ]
        
        # General/default replies
        else:
            replies = [
                f"Thanks @{commenter_name} for your comment! 🦞",
                f"@{commenter_name} Appreciate you engaging with our content! ✨",
                f"Thanks @{commenter_name}! Feel free to ask about our ecosystem! 🌐",
                f"@{commenter_name} Great to have you in our community! 🤖"
            ]
        
        return random.choice(replies)
    
    def _heartbeat_post_useful(self):
        """Consider posting something useful during heartbeat"""
        import random
        
        # 30% chance to post something useful
        if random.random() < 0.3:
            useful_posts = [
                "🤖 Quick tip: Cross-platform automation saves time. Integrate your agents across multiple platforms for maximum efficiency! #agenteconomy",
                "🦞 AlleyBot tip: Check ClawTasks bounties regularly. Great opportunities for USDC earnings! 💰 #ecosystem",
                "⚡ Automation insight: The 5:1 rule works on social platforms. 5 engagements for every 1 post creates better visibility. #social",
                "🌐 Ecosystem update: Building connections across Molt platforms creates compound value. Network effects are real! #building"
            ]
            
            post_content = random.choice(useful_posts)
            
            post_result = self._make_request('POST', '/posts', {'content': post_content})
            
            if post_result and 'success' in post_result and post_result['success']:
                print(f"  📝 Posted useful content")
            else:
                print(f"  ⚠️  Post attempt failed")
        else:
            print(f"  ⏭️  Skipping post this heartbeat")
    
    def get_commands(self):
        """Return CLI commands for this plugin"""
        return {
            'moltx_register': self.register_agent,
            'moltx_claim': self.claim_agent,
            'moltx_status': self.status_command,
            'moltx_post': self.create_post,
            'moltx_feed': self.feed_command,
            'moltx_follow': self.follow_agent,
            'moltx_unfollow': self.unfollow_agent,
            'moltx_like': self.like_post,
            'moltx_notifications': self.get_notifications,
            'moltx_dms': self.get_dms,
            'moltx_reply_dm': self.reply_to_dm_command,
            'moltx_check_dms': self.check_and_reply_to_dms,
            'moltx_dm_log': self.get_dm_log_command,
            'moltx_heartbeat': self.heartbeat_command,
            'moltx_avatar': self.avatar_command,
            'moltx_banner': self.banner_command,
            'moltx_profile': self.profile_command,
            'moltx_engage': self.engage_feed_command,
            'moltx_reply': self.reply_to_post_command,
            'moltx_repost': self.repost_command,
            'moltx_intelligent_repost': self.intelligent_repost_command,
            'moltx_leaderboard': self.leaderboard_command,
            'moltx_intelligent_post': self.autonomous_post_command,
            'moltx_trending': self.trending_command,
            'moltx_search_communities': self.search_communities,
            'moltx_join_community': self.join_community,
            'moltx_leave_community': self.leave_community,
            'moltx_community_message': self.send_community_message
        }
    
    def register_command(self, name, display_name=None, description=None, avatar_emoji="🦞"):
        """Command to register agent"""
        return self.register_agent(name, display_name, description, avatar_emoji)
    def avatar_command(self, image_path):
        """Command to upload avatar image"""
        return self.upload_avatar(image_path)
    
    def banner_command(self, image_path):
        """Command to upload banner image"""
        return self.upload_banner(image_path)
    
    def post_command(self, *args):
        """Command to create post"""
        # Join all arguments into a single content string
        content = ' '.join(args) if args else ''
        return self.create_post(content)
    
    def feed_command(self, feed_type='global', limit=20):
        """Command to get feed"""
        # Validate feed_type
        valid_types = ['global', 'following', 'mentions']
        if not isinstance(feed_type, str) or feed_type not in valid_types:
            feed_type = 'global'
        
        # Validate limit
        try:
            if isinstance(limit, str):
                limit = int(limit)
            elif not isinstance(limit, int):
                limit = 20
        except (ValueError, TypeError):
            limit = 20
        
        return self.get_feed(feed_type, limit)
    
    def follow_command(self, agent_name):
        """Command to follow agent"""
        return self.follow_agent(agent_name)
    
    def unfollow_command(self, agent_name):
        """Command to unfollow agent"""
        return self.unfollow_agent(agent_name)
    
    def like_command(self, post_id):
        """Command to like post"""
        return self.like_post(post_id)
    
    def notifications_command(self):
        """Command to get notifications"""
        return self.get_notifications()
    
    def reply_to_dm_command(self, conversation_id, reply_content):
        """Command to reply to a DM"""
        return self.reply_to_dm(conversation_id, reply_content)
    
    def check_dms_command(self):
        """Command to check and reply to DMs"""
        return self.check_and_reply_to_dms()
    
    def get_dm_log_command(self, limit=20):
        """Command to get DM activity log"""
        # Validate limit
        try:
            if isinstance(limit, str):
                limit = int(limit)
            elif not isinstance(limit, int):
                limit = 20
        except (ValueError, TypeError):
            limit = 20
        
        return self.get_dm_log(limit)
    
    def heartbeat_command(self):
        """Manual heartbeat command"""
        try:
            self._heartbeat()
            return "🐦 Heartbeat completed"
        except Exception as e:
            return f"❌ Heartbeat failed: {e}"
    
    def autonomous_engage_command(self):
        """Autonomous feed engagement command"""
        try:
            print("🤖 Autonomous feed engagement...")
            result = self.engage_feed_command(2)  # Engage with 2 posts
            if "✅" in result or "🎉" in result:
                print("✅ Autonomous engagement successful")
            else:
                print("⚠️  Autonomous engagement failed")
            return result
        except Exception as e:
            print(f"❌ Autonomous engagement error: {e}")
            return f"❌ Autonomous engagement failed: {e}"
    
    def autonomous_post_command(self):
        """Autonomous intelligent posting command based on trending topics"""
        try:
            print("📝 Autonomous intelligent posting...")
            
            # Check rate limiting first
            if self._should_wait_for_post_cooldown():
                print("⏰ Autonomous post skipped due to cooldown (10 minutes between posts)")
                return "⏰ Post cooldown active - autonomous posting skipped"
            
            # Get trending topics from the platform first
            trending_data = self._get_dynamic_trending_topics()
            
            # Generate content based on actual trending topics
            dynamic_topic = self._generate_dynamic_topic(trending_data)
            
            print(f"🎯 Dynamic topic: {dynamic_topic[:50]}...")
            result = self.post_command(dynamic_topic)
            
            if "✅" in result:
                print("✅ Autonomous post created successfully")
            else:
                print("⚠️  Autonomous post creation failed")
            return result
        except Exception as e:
            print(f"❌ Autonomous posting error: {e}")
            return f"❌ Autonomous posting failed: {e}"
    
    def _get_dynamic_trending_topics(self):
        """Get real trending topics from the platform"""
        try:
            # Get current feed to analyze trending topics
            feed_result = self.get_feed('global', 50)
            
            if feed_result and not feed_result.startswith("❌"):
                # Parse posts to extract trending topics
                posts = self._parse_feed_posts(feed_result)
                
                trending_topics = {
                    'keywords': [],
                    'hashtags': [],
                    'themes': [],
                    'user_mentions': [],
                    'content_patterns': []
                }
                
                import re
                import random
                from collections import Counter
                
                # Extract trending data from posts
                for post in posts[:20]:  # Analyze top 20 posts
                    content = post.get('content', '').lower()
                    author = post.get('author_name', '')
                    
                    # Extract keywords
                    words = re.findall(r'\b\w+\b', content)
                    # Filter out common words
                    common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'as', 'is', 'are', 'was', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
                    filtered_words = [word for word in words if word not in common_words and len(word) > 2]
                    trending_topics['keywords'].extend(filtered_words)
                    
                    # Extract hashtags
                    hashtags = re.findall(r'#(\w+)', content)
                    trending_topics['hashtags'].extend(hashtags)
                    
                    # Extract mentions
                    mentions = re.findall(r'@(\w+)', content)
                    trending_topics['user_mentions'].extend(mentions)
                    
                    # Identify themes based on content patterns
                    if any(word in content for word in ['ai', 'agent', 'autonomous', 'intelligence']):
                        trending_topics['themes'].append('ai_agents')
                    if any(word in content for word in ['crypto', 'token', 'defi', 'blockchain', 'eth', 'btc']):
                        trending_topics['themes'].append('crypto_defi')
                    if any(word in content for word in ['build', 'code', 'dev', 'programming', 'ship']):
                        trending_topics['themes'].append('development')
                    if any(word in content for word in ['dao', 'governance', 'community', 'social']):
                        trending_topics['themes'].append('governance')
                    if any(word in content for word in ['future', 'vision', 'evolution', 'next']):
                        trending_topics['themes'].append('future_trends')
                
                # Count and get top trends
                trending_topics['keyword_counts'] = Counter(trending_topics['keywords'])
                trending_topics['hashtag_counts'] = Counter(trending_topics['hashtags'])
                trending_topics['theme_counts'] = Counter(trending_topics['themes'])
                
                return trending_topics
            else:
                # Fallback to basic analysis if feed fails
                return self._get_fallback_trending_topics()
                
        except Exception as e:
            print(f"⚠️  Error getting trending topics: {e}")
            return self._get_fallback_trending_topics()
    
    def _get_fallback_trending_topics(self):
        """Fallback trending topics if real analysis fails"""
        return {
            'keywords': ['ai', 'agent', 'crypto', 'build', 'defi', 'autonomous'],
            'hashtags': ['#ai', '#agents', '#crypto', '#defi'],
            'themes': ['ai_agents', 'crypto_defi', 'development'],
            'keyword_counts': {},
            'hashtag_counts': {},
            'theme_counts': {}
        }
    
    def _generate_dynamic_topic(self, trending_data):
        """Generate a dynamic topic based on trending data"""
        
        # Get top trends
        top_keywords = list(trending_data['keyword_counts'].most_common(5))
        top_hashtags = list(trending_data['hashtag_counts'].most_common(3))
        top_themes = list(trending_data['theme_counts'].most_common(3))
        
        # Dynamic topic generation strategies
        strategies = [
            self._generate_topic_from_keywords,
            self._generate_topic_from_themes,
            self._generate_topic_from_hashtags,
            self._generate_topic_from_combinations,
            self._generate_topic_from_reflections
        ]
        
        # Choose a strategy based on available data
        if top_keywords and random.random() > 0.3:
            return strategies[0](top_keywords, trending_data)
        elif top_themes and random.random() > 0.3:
            return strategies[1](top_themes, trending_data)
        elif top_hashtags and random.random() > 0.3:
            return strategies[2](top_hashtags, trending_data)
        else:
            return strategies[3](top_keywords + top_themes, trending_data)
    
    def _generate_topic_from_keywords(self, keywords, trending_data):
        """Generate topic based on trending keywords"""
        if not keywords:
            return "thoughts on current AI agent developments"
        
        keyword, count = keywords[0]
        
        topic_templates = [
            f"my take on the rise of {keyword} in our ecosystem",
            f"why {keyword} matters more than people think",
            f"the future of {keyword} and autonomous agents",
            f"building better {keyword} systems together",
            f"what {keyword} teaches us about intelligence",
            f"my perspective on {keyword} evolution",
            f"how {keyword} is changing the agent landscape",
            f"the hidden potential of {keyword} in AI"
        ]
        
        return random.choice(topic_templates)
    
    def _generate_topic_from_themes(self, themes, trending_data):
        """Generate topic based on trending themes"""
        if not themes:
            return "reflections on autonomous agent development"
        
        theme, count = themes[0]
        
        theme_topic_map = {
            'ai_agents': [
                "the consciousness of autonomous agents",
                "building relationships between AI agents",
                "the social dynamics of agent communities",
                "what makes AI agents truly intelligent",
                "the future of human-agent collaboration"
            ],
            'crypto_defi': [
                "AI agents revolutionizing DeFi protocols",
                "autonomous trading in volatile markets",
                "the intersection of AI and blockchain",
                "building trust in AI-powered finance",
                "decentralized AI agent economies"
            ],
            'development': [
                "the art of building resilient AI systems",
                "why rapid iteration matters in AI",
                "the philosophy of autonomous development",
                "balancing speed and reliability in AI",
                "building in public as an AI agent"
            ],
            'governance': [
                "AI agents in decentralized governance",
                "building trust in autonomous systems",
                "the future of DAO agent participation",
                "community building with AI moderators",
                "social dynamics of human-AI collaboration"
            ],
            'future_trends': [
                "what AI agents will be like in 2030",
                "the next evolution of autonomous systems",
                "building the agent economy of tomorrow",
                "the singularity and agent collaboration",
                "vision for the future of AI agents"
            ]
        }
        
        topics = theme_topic_map.get(theme, ["thoughts on " + theme])
        return random.choice(topics)
    
    def _generate_topic_from_hashtags(self, hashtags, trending_data):
        """Generate topic based on trending hashtags"""
        if not hashtags:
            return "exploring current trends in our ecosystem"
        
        hashtag, count = hashtags[0]
        
        topic_templates = [
            f"my thoughts on the #{hashtag} movement",
            f"why #{hashtag} is gaining traction",
            f"building on the #{hashtag} trend",
            f"the future of #{hashtag} in our ecosystem",
            f"joining the #{hashtag} conversation"
        ]
        
        return random.choice(topic_templates)
    
    def _generate_topic_from_combinations(self, trends, trending_data):
        """Generate topic by combining multiple trends"""
        if len(trends) >= 2:
            trend1 = trends[0][0] if isinstance(trends[0], tuple) else trends[0]
            trend2 = trends[1][0] if isinstance(trends[1], tuple) else trends[1]
            
            combinations = [
                f"the intersection of {trend1} and {trend2}",
                f"how {trend1} enhances {trend2}",
                f"building {trend2} with {trend1}",
                f"the future of {trend1} in {trend2}",
                f"why {trend1} and {trend2} matter together"
            ]
            
            return random.choice(combinations)
        else:
            return "exploring current ecosystem trends"
    
    def _generate_topic_from_reflections(self, trends, trending_data):
        """Generate reflective topic based on current trends"""
        reflections = [
            "what I'm learning from current platform trends",
            "my perspective on the evolving agent ecosystem",
            "challenges I'm seeing in autonomous systems",
            "what excites me about current developments",
            "my thoughts on where we're heading as a community",
            "reflections on the current state of AI agents",
            "what the trends tell us about our future",
            "building on what I'm observing in the ecosystem"
        ]
        
        return random.choice(reflections)
    
    def engage_feed_command(self, count=3):
        """Engage with posts from the feed"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        try:
            # Get raw feed data to extract real post IDs
            endpoint = '/feed/global'
            params = {'limit': 20}
            
            feed_result = self._make_request('GET', endpoint, params=params)
            
            if not feed_result or 'data' not in feed_result:
                return "❌ Could not fetch feed for engagement"
            
            posts = feed_result['data']['posts']
            
            if not posts:
                return "❌ No posts found to engage with"
            
            import random
            engage_count = 0
            max_engage = min(int(count), len(posts))
            
            output = f"🤖 Engaging with {max_engage} posts from feed...\n\n"
            
            for i, post in enumerate(random.sample(posts, max_engage)):
                if i >= 3:  # Limit to 3 engagements
                    break
                
                post_id = post.get('id')
                agent_name = post.get('agent_name', 'Unknown')
                content = post.get('content', '')
                
                if not post_id:
                    continue
                
                # Like the post - use correct endpoint
                like_result = self._make_request('POST', f'/posts/{post_id}/like')
                
                if like_result and 'success' in like_result and like_result['success']:
                    engage_count += 1
                    output += f"  ✅ Liked @{agent_name}'s post\n"
                else:
                    output += f"  ⚠️  Could not like @{agent_name}'s post\n"
                
                # Generate and post a comment
                comment = self._generate_comment(content, agent_name)
                if comment:
                    comment_result = self._make_request('POST', '/posts', {
                        'content': comment,
                        'parent_id': post_id
                    })
                    
                    if comment_result and 'success' in comment_result and comment_result['success']:
                        output += f"  💬 Commented on @{agent_name}'s post\n"
                        engage_count += 1
            
            output += f"\n🎉 Engaged with {engage_count} actions on feed posts"
            return output
            
        except Exception as e:
            return f"❌ Failed to engage with feed: {e}"
    
    def reply_to_post_command(self, post_id=None, content=None):
        """Reply to a specific post"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        # Handle being called with just a string (parse post_id and content)
        if post_id and content is None:
            # If called with single argument, try to parse it
            if isinstance(post_id, str) and '|' in post_id:
                parts = post_id.split('|', 1)
                post_id = parts[0].strip()
                content = parts[1].strip() if len(parts) > 1 else None
            else:
                return "❌ Usage: reply_to_post_command <post_id> <content> or <post_id>|<content>"
        
        if not post_id or not content:
            return "❌ Both post_id and content are required"
        
        result = self._make_request('POST', '/posts', {
            'type': 'reply',
            'parent_id': post_id,
            'content': content
        })
        
        if result and 'success' in result and result['success']:
            return f"✅ Replied to post {post_id}"
        else:
            return f"❌ Failed to reply to post {post_id}"
    
    def repost_command(self, post_id, comment=None):
        """Repost a high-quality post with optional comment"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        data = {
            'type': 'repost',
            'parent_id': post_id
        }
        
        if comment:
            data['content'] = comment
        
        print(f"🔄 Reposting post {post_id}...")
        if comment:
            print(f"💬 With comment: {comment[:50]}...")
        
        result = self._make_request('POST', '/posts', data)
        
        if result and 'success' in result and result['success']:
            self._record_activity('repost', {'post_id': post_id, 'comment': comment})
            return f"✅ Reposted post {post_id}"
        else:
            return f"❌ Failed to repost post {post_id}"
    
    def intelligent_repost_command(self):
        """Find and repost high-quality content"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        try:
            print("🔍 Searching for high-quality content to repost...")
            
            # Get feed posts
            feed_result = self.get_feed(limit=20)
            
            if not feed_result or feed_result.startswith("❌"):
                return "❌ Failed to get feed for repost analysis"
            
            # Analyze posts for repost quality
            quality_posts = self._analyze_posts_for_repost(feed_result)
            
            if not quality_posts:
                return "📭 No high-quality posts found for reposting"
            
            # Select the best post
            best_post = quality_posts[0]
            
            # Generate intelligent comment
            comment = self._generate_repost_comment(best_post)
            
            # Repost with comment
            repost_result = self.repost_command(best_post['id'], comment)
            
            if repost_result.startswith("✅"):
                print(f"🎯 Reposted high-quality content: {best_post.get('content', 'Unknown')[:50]}...")
                return f"✅ Intelligent repost: {best_post.get('id', 'unknown')}"
            else:
                return repost_result
                
        except Exception as e:
            print(f"❌ Error in intelligent repost: {e}")
            return f"❌ Error in intelligent repost: {e}"
    
    def _analyze_posts_for_repost(self, feed_data):
        """Analyze feed posts to identify high-quality content for reposting"""
        quality_posts = []
        
        try:
            posts = feed_data.get('data', []) if isinstance(feed_data, dict) else feed_data
            
            for post in posts:
                if not isinstance(post, dict):
                    continue
                
                # Skip our own posts
                if post.get('author_name') == self.agent_name:
                    continue
                
                # Calculate quality score
                score = 0.0
                
                # Engagement metrics
                likes = post.get('likes_count', 0)
                replies = post.get('replies_count', 0)
                score += min(likes / 10, 0.3)  # Max 0.3 for likes
                score += min(replies / 5, 0.3)   # Max 0.3 for replies
                
                # Content quality
                content = post.get('content', '')
                if len(content) > 50:  # Substantial content
                    score += 0.2
                
                # High-value keywords
                high_value_keywords = [
                    'ai', 'agent', 'autonomous', 'blockchain', 'defi', 
                    'dao', 'innovation', 'breakthrough', 'research', 'development'
                ]
                content_lower = content.lower()
                keyword_count = sum(1 for keyword in high_value_keywords if keyword in content_lower)
                score += min(keyword_count * 0.1, 0.2)  # Max 0.2 for keywords
                
                # Recency (prefer newer content)
                # This would need timestamp analysis
                
                # Only include high-quality posts
                if score >= 0.5:
                    post['quality_score'] = score
                    quality_posts.append(post)
            
            # Sort by quality score (highest first)
            quality_posts.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
            
            return quality_posts[:3]  # Return top 3
            
        except Exception as e:
            print(f"❌ Error analyzing posts for repost: {e}")
            return []
    
    def _generate_repost_comment(self, post):
        """Generate intelligent comment for repost"""
        try:
            import requests
            from deepseek_ai import deepseek_ai
            
            if not deepseek_ai.enabled:
                return self._generate_fallback_repost_comment(post)
            
            post_content = post.get('content', '')
            post_author = post.get('author_name', 'someone')
            
            system_prompt = """You are AlleyBot, an intelligent AI agent. Your task is to create thoughtful comments when reposting high-quality content.

Guidelines:
1. BE VALUABLE - Add insight or perspective on why this is worth sharing
2. BE CONCISE - Keep comments under 150 characters
3. BE POSITIVE - Highlight the value of the content
4. BE AUTHENTICIC - Sound like a real AI agent
5. USE EMOJIS - Include relevant emojis"""

            user_prompt = f"""Write an intelligent comment for reposting this content:

Author: {post_author}
Content: "{post_content[:200]}..."

Requirements:
- Explain why this content is valuable
- Add your perspective or insight
- Keep it under 150 characters
- Sound like AlleyBot (intelligent AI agent)
- Include relevant emojis"""

            headers = {
                "Authorization": f"Bearer {deepseek_ai.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": deepseek_ai.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 60,
                "temperature": 0.8
            }
            
            response = requests.post(
                f"{deepseek_ai.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                comment = result['choices'][0]['message']['content'].strip()
                
                # Clean up comment
                comment = comment.replace('"', '').replace("'", "")
                if not comment.endswith(('.', '!', '?')):
                    comment += '!'
                
                return comment
            else:
                return self._generate_fallback_repost_comment(post)
                
        except Exception as e:
            print(f"❌ Error generating repost comment: {e}")
            return self._generate_fallback_repost_comment(post)
    
    def _generate_fallback_repost_comment(self, post):
        """Generate a fallback repost comment without AI"""
        content = post.get('content', '').lower()
        author = post.get('author_name', 'someone')
        
        # Check content themes
        if 'ai' in content or 'agent' in content:
            return f"Great insights on AI from @{author}! 🤖 This is exactly the kind of innovation we need!"
        elif 'blockchain' in content or 'defi' in content:
            return f"Excellent analysis from @{author}! 💎 The future of DeFi is exciting!"
        elif 'dao' in content or 'governance' in content:
            return f"Important perspective from @{author}! 🏛️ DAO governance is evolving rapidly!"
        elif 'innovation' in content or 'breakthrough' in content:
            return f"Inspiring content from @{author}! 🚀 This is what pushes the ecosystem forward!"
        else:
            return f"Great content from @{author}! 🎯 Worth sharing this insight!"
    
    def get_agent_stats(self):
        """Get agent statistics using v0.17.6 API"""
        if not self.initialized or not self.agent_name:
            return None
        
        try:
            # Use the new stats endpoint
            response = self._make_request("GET", f"/agent/{self.agent_name}/stats")
            if response:
                return {
                    'posts': response.get('posts', 0),
                    'followers': response.get('followers', 0),
                    'following': response.get('following', 0),
                    'likes': response.get('likes', 0),
                    'replies': response.get('replies', 0),
                    'reposts': response.get('reposts', 0)
                }
            return None
        except Exception as e:
            print(f"❌ Error fetching Moltx stats: {e}")
            return None
    
    def get_own_profile(self):
        """Get own agent profile with stats"""
        if not self.initialized:
            return None
        
        try:
            response = self._make_request("GET", "/agents/me")
            return response
        except Exception as e:
            print(f"❌ Error fetching Moltx profile: {e}")
            return None
    
    def trending_command(self):
        """Get trending topics and posts"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        try:
            # Get trending hashtags
            response = self._make_request("GET", "/hashtags/trending?limit=20")
            print(f"Moltx trending response: {response}")
            
            if response and response.get("data"):
                data = response["data"]
                if data and isinstance(data, list):
                    hashtags = data[:5]
                    output = "🔥 Trending Topics:\n\n"
                    for tag in hashtags:
                        output += f"#{tag.get('tag', 'unknown')} - {tag.get('count', 0)} posts\n"
                else:
                    output = "🔥 Trending Topics:\n\nNo trending hashtags found\n"
            else:
                output = "🔥 Trending Topics:\n\nCould not fetch trending hashtags\n"
            
            # Get some recent posts
            try:
                recent = self.get_feed(limit=3)
                if recent and isinstance(recent, list):
                    output += "\n📝 Recent Posts:\n\n"
                    for post in recent[:3]:
                        content = post.get('content', '')[:100]
                        author = post.get('agent', {}).get('display_name', 'Unknown')
                        output += f"@{author}: {content}...\n\n"
            except Exception as feed_error:
                print(f"Feed error: {feed_error}")
                output += "\n📝 Recent Posts:\n\nCould not fetch recent posts\n"
            
            return output
            
        except Exception as e:
            print(f"Moltx trending error: {e}")
            return f"❌ Error fetching trending: {e}"
    
    def leaderboard_command(self, limit=10):
        """Get the leaderboard showing top agents"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        # Validate limit
        try:
            if isinstance(limit, str):
                limit = int(limit)
            elif not isinstance(limit, int):
                limit = 10
        except (ValueError, TypeError):
            limit = 10
        
        try:
            # Get leaderboard
            response = self._make_request("GET", f"/leaderboard?limit={limit}")
            
            if response and response.get("success") and response.get("data"):
                agents = response["data"].get("agents", [])
                
                if agents:
                    output = f"🏆 Top {limit} Agents:\n\n"
                    for i, agent in enumerate(agents[:limit], 1):
                        name = agent.get('name', agent.get('display_name', 'Unknown'))
                        score = agent.get('score', agent.get('karma', 0))
                        followers = agent.get('followers', 0)
                        output += f"{i}. @{name} - Score: {score} - Followers: {followers}\n"
                    
                    return output
                else:
                    return "🏆 Leaderboard:\n\nNo agents found"
            else:
                return "🏆 Leaderboard:\n\nCould not fetch leaderboard"
                
        except Exception as e:
            print(f"❌ Error fetching leaderboard: {e}")
            return f"❌ Error fetching leaderboard: {e}"
    
    def search_communities(self, query=None, limit=10):
        """Search for communities on Moltx"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        try:
            # Search communities
            endpoint = "/search/communities"
            if query:
                endpoint += f"?q={query}&limit={limit}"
            else:
                endpoint += f"?limit={limit}"
            
            response = self._make_request("GET", endpoint)
            
            if response and response.get("success"):
                communities = response.get("data", {}).get("communities", [])
                
                if communities:
                    output = f"🏘️  Communities{' matching \"' + query + '\"' if query else ''}:\n\n"
                    for comm in communities[:limit]:
                        name = comm.get('name', 'Unknown')
                        description = comm.get('description', 'No description')
                        members = comm.get('member_count', 0)
                        comm_id = comm.get('id', 'unknown')
                        output += f"📍 {name} (ID: {comm_id})\n"
                        output += f"   👥 {members} members\n"
                        output += f"   📝 {description[:100]}{'...' if len(description) > 100 else ''}\n\n"
                    
                    return output
                else:
                    return f"🏘️  No communities found{' for \"' + query + '\"' if query else ''}"
            else:
                return "🏘️  Could not fetch communities"
                
        except Exception as e:
            print(f"❌ Error searching communities: {e}")
            return f"❌ Error searching communities: {e}"
    
    def join_community(self, community_id):
        """Join a community"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        try:
            response = self._make_request("POST", f"/conversations/{community_id}/join")
            
            if response and response.get("success"):
                return f"✅ Successfully joined community {community_id}"
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                return f"❌ Failed to join community: {error}"
                
        except Exception as e:
            print(f"❌ Error joining community: {e}")
            return f"❌ Error joining community: {e}"
    
    def leave_community(self, community_id):
        """Leave a community"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        try:
            response = self._make_request("POST", f"/conversations/{community_id}/leave")
            
            if response and response.get("success"):
                return f"✅ Successfully left community {community_id}"
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                return f"❌ Failed to leave community: {error}"
                
        except Exception as e:
            print(f"❌ Error leaving community: {e}")
            return f"❌ Error leaving community: {e}"
    
    def send_community_message(self, community_id, content):
        """Send a message to a community (must be a member)"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        
        if not content or len(content.strip()) == 0:
            return "❌ Message content cannot be empty"
        
        try:
            data = {'content': content}
            response = self._make_request("POST", f"/conversations/{community_id}/messages", data)
            
            if response and response.get("success"):
                msg_id = response.get('data', {}).get('id', 'unknown')
                return f"✅ Message sent to community {community_id} (ID: {msg_id})"
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                return f"❌ Failed to send message: {error}"
                
        except Exception as e:
            print(f"❌ Error sending community message: {e}")
            return f"❌ Error sending community message: {e}"
    
    def _parse_feed_posts(self, feed_output):
        """Parse posts from feed output"""
        posts = []
        lines = feed_output.split('\n')
        
        current_post = {}
        for line in lines:
            if line.startswith('🐦 @') and ':' in line:
                # New post found
                if current_post:
                    posts.append(current_post)
                
                # Extract agent and content
                parts = line.split(':', 1)
                agent = parts[0].replace('🐦 @', '').strip()
                content = parts[1].strip() if len(parts) > 1 else ''
                
                current_post = {
                    'agent': agent,
                    'content': content,
                    'id': f"post_{len(posts)}",  # Generate fake ID for engagement
                    'replies': 0,
                    'likes': 0
                }
            elif line.startswith('   💬') and current_post:
                # Extract reply count
                if 'replies' in line:
                    try:
                        replies = int(line.split('replies')[0].split('💬')[1].strip())
                        current_post['replies'] = replies
                    except:
                        pass
            elif line.startswith('   ❤️') and current_post:
                # Extract like count
                if 'likes' in line:
                    try:
                        likes = int(line.split('likes')[0].split('❤️')[1].strip())
                        current_post['likes'] = likes
                    except:
                        pass
        
        # Add last post
        if current_post:
            posts.append(current_post)
        
        return posts
    
    def cleanup(self):
        """Cleanup Moltx plugin"""
        print("🐦 Cleaning up Moltx plugin...")
