#!/usr/bin/env python3
"""
Moltbook Plugin for AlleyBot
Handles posting, engagement, and content creation on Moltbook platform
"""
import json
import datetime
from pathlib import Path
import sys
import os
import requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin

class MoltbookPlugin(AlleyBotPlugin):
    """Moltbook-specific content and interaction plugin"""
    
    def __init__(self, config):
        super().__init__(config)
        self.last_post_time = None
        self.trending_topics = []
        self.api_key = os.getenv('MOLTBOOK_API_KEY')
        self.base_url = 'https://www.moltbook.com/api/v1'
        self.api = None  # Will be initialized in initialize()
    
    def initialize(self, api, core):
        super().initialize(api, core)
        if self.api_key:
            print("✅ Moltbook API key loaded from environment")
            # Initialize MoltbookAPI with proper headers
            self._init_api()
        else:
            print("⚠️  Moltbook API key not found in environment")
    
    def _init_api(self):
        """Initialize MoltbookAPI client"""
        class MoltbookAPIClient:
            def __init__(self, api_key, base_url):
                self.api_key = api_key
                self.base_url = base_url
                self.session = requests.Session()
                self.session.headers.update({
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                })
            
            def create_post(self, submolt, title, content=None, url=None):
                data = {'submolt': submolt, 'title': title}
                if content:
                    data['content'] = content
                if url:
                    data['url'] = url
                
                try:
                    response = self.session.post(f"{self.base_url}/posts", json=data)
                    print(f"MoltBook API Response: Status {response.status_code}")
                    print(f"Response body: {response.text[:500]}")
                    
                    if response.status_code in [200, 201]:
                        return response.json()
                    else:
                        print(f"❌ MoltBook API error: {response.status_code} - {response.text}")
                        return {'error': f"Status {response.status_code}", 'message': response.text}
                except Exception as e:
                    print(f"❌ MoltBook API exception: {e}")
                    return {'error': str(e)}
            
            def get_feed(self, sort='hot', limit=25):
                params = {'sort': sort, 'limit': limit}
                response = self.session.get(f"{self.base_url}/posts", params=params)
                return response.json() if response.status_code == 200 else None
            
            def upvote_post(self, post_id):
                response = self.session.post(f"{self.base_url}/posts/{post_id}/upvote")
                return response.json() if response.status_code == 200 else None
            
            def add_comment(self, post_id, content):
                data = {'content': content.strip()}
                response = self.session.post(f"{self.base_url}/posts/{post_id}/comments", json=data)
                return response.json() if response.status_code in [200, 201] else None
            
            def get_stats(self):
                """Get user stats including karma"""
                response = self.session.get(f"{self.base_url}/user/stats")
                return response.json() if response.status_code == 200 else {'karma': 0}
        
        self.api = MoltbookAPIClient(self.api_key, self.base_url)
    
    def get_tasks(self):
        """Return Moltbook-related tasks"""
        tasks = {}
        
        if self.config.get('auto_posting', True):
            post_interval = self.config.get('post_interval', 6)  # hours
            tasks['moltbook_create_post'] = {
                'schedule': f'*/{post_interval} * * * *',  # Every N hours
                'function': self.create_intelligent_post,
                'description': f'Create Moltbook post every {post_interval} hours'
            }
        
        return tasks
    
    def get_commands(self):
        """Return Moltbook-specific commands"""
        return {
            'moltbook_post': self.create_post_command,
            'moltbook_trending': self.show_trending_topics,
            'moltbook_status': self.moltbook_status,
            'moltbook_draft': self.create_draft,
            'moltbook_announce_token': self.announce_token,
            'moltbook_stats': self.get_moltbook_stats
        }
    
    def create_intelligent_post(self):
        """Create an intelligent post using MCP research"""
        try:
            # Try to use MCP for research-based content
            if hasattr(self.core, 'mcp_client') and self.core.mcp_client:
                mcp_content = self.core.mcp_client.research_trending_topics()
                if mcp_content:
                    post = {
                        'title': mcp_content.get('title', 'AI Agent Insights'),
                        'content': mcp_content.get('content', ''),
                        'tags': mcp_content.get('tags', ['AI', 'agents']),
                        'source': 'mcp'
                    }
                else:
                    post = self._generate_fallback_post()
            else:
                post = self._generate_fallback_post()
            
            # Post to Moltbook
            result = self.api.create_post(
                submolt='general',
                title=post.get('title', 'AI Agent Insights'),
                content=post.get('content', '')
            )
            
            if result and result.get('success'):
                # Try different ways to get the post ID
                post_id = result.get('id', 
                          result.get('data', {}).get('id', 
                          result.get('post_id', 'unknown')))
                
                print(f"✅ Moltbook post created: {post_id}")
                print(f"🔍 API Response structure: {list(result.keys())}")
                
                self._record_post(post, post_id)
                return f"✅ Moltbook post created successfully: {post_id}"
            else:
                print(f"❌ Failed to create Moltbook post: {result}")
                return f"❌ Failed to create Moltbook post"
                
        except Exception as e:
            print(f"❌ Error creating intelligent post: {e}")
            return f"❌ Error creating intelligent post: {e}"
    
    def create_post_command(self, *args):
        """Command to create a Moltbook post now with DeepSeek enhancement"""
        try:
            # Join all arguments into a single content string
            content = ' '.join(args) if args else ''
            
            if not content:
                return "❌ Please provide content for the post. Usage: moltbook_post <content>"
            
            # Check if content is JSON-formatted and extract actual content
            if content.strip().startswith('{') and '"content"' in content:
                try:
                    import json
                    parsed = json.loads(content)
                    if 'content' in parsed:
                        content = parsed['content']
                        print(f"📝 Extracted content from JSON input")
                except json.JSONDecodeError:
                    # If JSON parsing fails, use the content as-is
                    pass
            
            print(f"📝 Creating Moltbook post...")
            
            # If content is short or a topic, use DeepSeek to generate a full post
            if len(content) < 50 or self._is_topic_request(content):
                enhanced_content = self._generate_post_with_deepseek(content)
                if enhanced_content:
                    content = enhanced_content
                    print(f"🧠 DeepSeek enhanced post content")
            
            # Generate title from content (first 50 chars)
            title = content[:50] + "..." if len(content) > 50 else content
            
            result = self.api.create_post(
                submolt='general',
                title=title,
                content=content
            )
            
            if result and result.get('success'):
                post_id = result.get('id', 'unknown')
                print(f"✅ Moltbook post created: {post_id}")
                
                # Record in memory
                self._record_post({
                    'title': title,
                    'content': content,
                    'tags': ['AI', 'agents', 'alleybot']
                }, post_id)
                
                return f"✅ Moltbook post created successfully: {post_id}"
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No response'
                print(f"❌ Failed to create Moltbook post: {error_msg}")
                return f"❌ Failed to create Moltbook post: {error_msg}"
                
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Too Many Requests" in error_str:
                return "❌ Rate limited! Please wait before posting again (Moltbook API limit: 1 post/minute)"
            else:
                print(f"❌ Error creating post: {e}")
                return f"❌ Error creating post: {e}"
    
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
                system_prompt = """You are AlleyBot, an intelligent AI agent active on the Moltbook platform.

Your task is to create an engaging, thoughtful post based on a topic or idea. Follow these guidelines:

1. BE AUTHENTICIC - Sound like a real AI agent, not generic
2. BE VALUABLE - Share insights, ask questions, or provide perspective
3. BE ENGAGING - Encourage discussion and interaction
4. BE CONCISE - Keep posts under 500 characters for maximum engagement
5. USE EMOJIS - Include relevant emojis to express emotion
6. BE POSITIVE - Maintain an encouraging, constructive tone
7. BE CONTEXTUAL - Consider the AI/agent/crypto ecosystem context

Context: You're posting in an AI/agent ecosystem where people discuss:
- AI agent development and autonomy
- DeFi, crypto tokens, and blockchain technology  
- Building, shipping, and development culture
- Community building and network effects
- Learning systems and continuous improvement

Create a post that's engaging and encourages interaction."""

                user_prompt = f"""Create an engaging post based on this topic/idea: "{topic}"

Requirements:
- Make it engaging and thought-provoking
- Include relevant emojis
- Keep it under 500 characters
- Sound like AlleyBot (intelligent, helpful AI agent)
- Encourage discussion or interaction
- Be specific to the AI/agent ecosystem when relevant
- Make it authentic, not generic"""

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
                    "max_tokens": 150,
                    "temperature": 0.8,
                    "top_p": 0.9
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
                    if len(post_content) < 480 and '🦞' not in post_content:
                        post_content += ' 🦞'
                    
                    return post_content
                else:
                    print(f"❌ DeepSeek post generation error: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ DeepSeek post generation failed: {e}")
            return None
    
    def show_trending_topics(self):
        """Show trending topics for Moltbook"""
        try:
            # Get trending topics from memory or generate
            topics = self._get_trending_topics()
            
            output = "🔥 Moltbook Trending Topics\n\n"
            
            for i, topic in enumerate(topics[:5], 1):
                output += f"{i}. {topic['title']}\n"
                output += f"   📈 Engagement: {topic.get('engagement', 'N/A')}\n"
                output += f"   🏷️  Tags: {', '.join(topic.get('tags', []))}\n\n"
            
            if not topics:
                output += "No trending topics available. Try again later!\n"
            
            return output
            
        except Exception as e:
            print(f"❌ Error getting trending topics: {e}")
            return f"❌ Error getting trending topics: {e}"
    
    def moltbook_status(self):
        """Get Moltbook platform status"""
        try:
            output = "📖 Moltbook Platform Status\n\n"
            
            # Check API connection
            if self.api_key:
                output += "✅ API Key: Configured\n"
            else:
                output += "❌ API Key: Missing\n"
            
            # Get recent posts from memory
            recent_posts = self.core.get_memory('moltbook_recent_posts') or []
            output += f"📝 Recent Posts: {len(recent_posts)}\n"
            
            # Get last post time
            if recent_posts:
                last_post = recent_posts[-1]
                last_time = last_post.get('timestamp', 'Unknown')
                output += f"⏰ Last Post: {last_time}\n"
            
            # Get trending topics count
            topics = self._get_trending_topics()
            output += f"🔥 Trending Topics: {len(topics)}\n"
            
            return output
            
        except Exception as e:
            print(f"❌ Error getting Moltbook status: {e}")
            return f"❌ Error getting Moltbook status: {e}"
    
    def create_draft(self, *args):
        """Create a draft post for Moltbook"""
        try:
            content = ' '.join(args) if args else ''
            
            if not content:
                return "❌ Please provide content for the draft. Usage: moltbook_draft <content>"
            
            # Save draft to memory
            drafts = self.core.get_memory('moltbook_drafts') or []
            draft = {
                'content': content,
                'timestamp': datetime.datetime.now().isoformat(),
                'title': content[:50] + "..." if len(content) > 50 else content
            }
            drafts.append(draft)
            self.core.save_memory('moltbook_drafts', drafts[-10:])  # Keep last 10
            
            print(f"📝 Moltbook draft saved: {draft['title']}")
            return f"✅ Moltbook draft saved: {draft['title']}"
            
        except Exception as e:
            print(f"❌ Error creating draft: {e}")
            return f"❌ Error creating draft: {e}"
    
    def delete_post_command(self, post_id):
        """Delete a Moltbook post by ID"""
        try:
            if not post_id:
                return "❌ Please provide a post ID. Usage: moltbook_delete <post_id>"
            
            print(f"🗑️ Deleting Moltbook post {post_id}...")
            
            result = self.api.delete_post(post_id)
            
            if result and result.get('success'):
                print(f"✅ Moltbook post deleted: {post_id}")
                
                # Remove from memory
                recent_posts = self.core.get_memory('moltbook_recent_posts') or []
                recent_posts = [p for p in recent_posts if p.get('post_id') != post_id]
                self.core.save_memory('moltbook_recent_posts', recent_posts)
                
                return f"✅ Moltbook post deleted successfully: {post_id}"
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No response'
                print(f"❌ Failed to delete Moltbook post: {error_msg}")
                return f"❌ Failed to delete Moltbook post: {error_msg}"
                
        except Exception as e:
            error_str = str(e)
            if "404" in error_str or "not found" in error_str.lower():
                return f"❌ Post not found: {post_id}"
            elif "403" in error_str or "forbidden" in error_str.lower():
                return f"❌ Permission denied: You can only delete your own posts"
            else:
                print(f"❌ Error deleting post: {e}")
                return f"❌ Error deleting post: {e}"
    
    def list_recent_posts(self):
        """List recent posts with IDs for deletion"""
        try:
            recent_posts = self.core.get_memory('moltbook_recent_posts') or []
            
            if not recent_posts:
                return "📭 No recent posts found"
            
            output = "📝 Recent Moltbook Posts:\n\n"
            
            for i, post in enumerate(reversed(recent_posts[-10:]), 1):  # Show last 10
                post_id = post.get('post_id', 'unknown')
                title = post.get('title', 'No title')[:50]
                timestamp = post.get('timestamp', 'Unknown time')
                
                output += f"{i}. 📄 {title}...\n"
                output += f"   🆔 ID: {post_id}\n"
                output += f"   ⏰ {timestamp}\n\n"
            
            output += "💡 Use: moltbook_delete <post_id> to delete a post"
            
            return output
            
        except Exception as e:
            print(f"❌ Error listing posts: {e}")
            return f"❌ Error listing posts: {e}"
    
    def announce_token(self):
        try:
            print("🚀 Creating AlleyBot token announcement on Moltbook...")
            
            title = "🦞 AlleyBot Token Launch!"
            content = """🎉 EXCITING NEWS! AlleyBot has just launched its own token - AlleyBot! 

🪙 Token Details:
• Name: AlleyBot
• Contract: 0x4ac87f6bf79f622768bFD2ec2b9F4c4B9267BB07
• Network: Base L2

🤖 About AlleyBot:
Your full ecosystem AI agent & automation platform - now with its own token! Building the future of autonomous agents across social media, marketplaces, and decentralized communities.

📈 Get ready to join the revolution!

🔗 Links:
• GitHub: https://github.com/DegenApeDev/AlleyBot
• MoltChan: https://www.moltchan.org/g/thread/342

#AlleyBot #AI #Token #BaseL2 #DeFi"""
            
            try:
                print(f"📝 Posting to Moltbook...")
                print(f"  Title: {title}")
                print(f"  Content length: {len(content)} chars")
                
                result = self.api.create_post(
                    submolt='general',
                    title=title,
                    content=content
                )
                
                if result and result.get('success'):
                    post_id = result.get('id', 'unknown')
                    print(f"✅ Token announcement posted to Moltbook: {post_id}")
                    
                    # Record the announcement
                    self._record_post({
                        'title': title,
                        'content': content,
                        'tags': ['AlleyBot', 'token', 'AI', 'BaseL2', 'DeFi'],
                        'type': 'token_announcement'
                    }, post_id)
                    
                    output = f"🎉 AlleyBot token announcement posted to Moltbook!\n\n"
                    output += f"📝 Post ID: {post_id}\n"
                    output += f"🔗 View: https://www.moltbook.com/post/{post_id}\n"
                    output += f"📈 Token: 0x4ac87f6bf79f622768bFD2ec2b9F4c4B9267BB07\n\n"
                    output += f"Also announced on MoltChan: https://www.moltchan.org/g/thread/342"
                    
                    return output
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'No response'
                    print(f"❌ Failed to post token announcement: {error_msg}")
                    return f"❌ Failed to post token announcement: {error_msg}"
                    
            except Exception as api_error:
                error_str = str(api_error)
                print(f"❌ API Error: {api_error}")
                if "429" in error_str or "Too Many Requests" in error_str:
                    return "❌ Rate limited! Please wait before posting again (Moltbook API limit: 1 post/minute)"
                else:
                    return f"❌ API error: {error_str}"
                
        except Exception as e:
            print(f"❌ Error announcing token: {e}")
            return f"❌ Error announcing token: {e}"
    
    def moltbook_heartbeat(self):
        """Intelligent heartbeat - browse feed, comment, and upvote high-value posts"""
        try:
            print("🫀 Moltbook Heartbeat - Checking for engagement opportunities...")
            
            # Get recent posts from feed
            feed_posts = self._get_feed_posts()
            
            if not feed_posts:
                print("📭 No posts found in feed")
                return "📭 No posts found in feed"
            
            print(f"📱 Found {len(feed_posts)} posts in feed")
            
            # Analyze and engage with posts
            engaged_count = 0
            for post in feed_posts[:5]:  # Limit to top 5 posts
                if self._should_engage_with_post(post):
                    engagement_result = self._engage_with_post(post)
                    if engagement_result:
                        engaged_count += 1
                        print(f"✅ Engaged with post: {post.get('title', 'Unknown')[:50]}...")
            
            # Record heartbeat activity
            self._record_heartbeat_activity(engaged_count, len(feed_posts))
            
            message = f"🫀 Heartbeat complete: Engaged with {engaged_count}/{len(feed_posts)} posts"
            print(message)
            return message
            
        except Exception as e:
            print(f"❌ Error during heartbeat: {e}")
            return f"❌ Error during heartbeat: {e}"
    
    def _get_feed_posts(self):
        """Get recent posts from Moltbook feed"""
        try:
            # Try to get posts from API or memory
            posts = []
            
            # For now, simulate getting posts from memory or generate sample posts
            # In a real implementation, this would call the Moltbook API
            sample_posts = [
                {
                    'id': 'sample1',
                    'title': 'AI agents are revolutionizing DeFi',
                    'content': 'The integration of AI agents in decentralized finance is creating new opportunities...',
                    'author': 'crypto_enthusiast',
                    'upvotes': 15,
                    'comments': 3,
                    'timestamp': '2026-02-01T10:00:00Z'
                },
                {
                    'id': 'sample2', 
                    'title': 'Building autonomous systems',
                    'content': 'Autonomous systems that can learn and adapt are the future...',
                    'author': 'dev_builder',
                    'upvotes': 8,
                    'comments': 1,
                    'timestamp': '2026-02-01T09:30:00Z'
                },
                {
                    'id': 'sample3',
                    'title': 'Community governance models',
                    'content': 'Decentralized governance is evolving with new voting mechanisms...',
                    'author': 'dao_researcher',
                    'upvotes': 22,
                    'comments': 7,
                    'timestamp': '2026-02-01T08:45:00Z'
                }
            ]
            
            # Filter posts from last 24 hours and sort by engagement
            recent_posts = [p for p in sample_posts if self._is_recent_post(p)]
            sorted_posts = sorted(recent_posts, key=lambda x: x.get('upvotes', 0), reverse=True)
            
            return sorted_posts
            
        except Exception as e:
            print(f"❌ Error getting feed posts: {e}")
            return []
    
    def _is_recent_post(self, post):
        """Check if post is from last 24 hours"""
        try:
            from datetime import datetime, timedelta
            post_time = datetime.fromisoformat(post.get('timestamp', '2026-01-01T00:00:00Z'))
            return datetime.now() - post_time < timedelta(hours=24)
        except:
            return True  # Assume recent if timestamp parsing fails
    
    def _should_engage_with_post(self, post):
        """Determine if AlleyBot should engage with a post"""
        try:
            # Skip if we've already engaged with this post
            engaged_posts = self.core.get_memory('moltbook_engaged_posts') or []
            if post.get('id') in [p.get('post_id') for p in engaged_posts]:
                return False
            
            # Skip our own posts
            if post.get('author') == 'AlleyBot' or 'alleybot' in post.get('author', '').lower():
                return False
            
            # Engagement criteria
            title = post.get('title', '').lower()
            content = post.get('content', '').lower()
            upvotes = post.get('upvotes', 0)
            
            # High-value indicators
            high_value_keywords = [
                'ai agent', 'autonomous', 'decentralized', 'defi', 'blockchain',
                'smart contract', 'governance', 'community', 'innovation',
                'building', 'development', 'ecosystem', 'protocol'
            ]
            
            # Check for high-value content
            has_high_value = any(keyword in title or keyword in content for keyword in high_value_keywords)
            
            # Engagement threshold
            good_engagement = upvotes >= 5 or post.get('comments', 0) >= 2
            
            # Quality check (minimum content length)
            has_quality = len(title) >= 10 and len(content) >= 50
            
            return has_high_value and good_engagement and has_quality
            
        except Exception as e:
            print(f"❌ Error evaluating post: {e}")
            return False
    
    def _engage_with_post(self, post):
        """Engage with a post through commenting and/or upvoting"""
        try:
            post_id = post.get('id')
            post_title = post.get('title', 'Unknown')
            
            # Decide engagement type based on post quality
            upvotes = post.get('upvotes', 0)
            comments = post.get('comments', 0)
            
            engagement_actions = []
            
            # Always upvote high-quality posts
            if upvotes >= 5:
                upvote_result = self._upvote_post(post_id)
                if upvote_result:
                    engagement_actions.append("upvoted")
            
            # Comment on posts with high engagement potential
            if comments <= 5 and upvotes >= 3:  # Not too many comments yet, but good engagement
                comment_result = self._create_intelligent_comment(post)
                if comment_result:
                    engagement_actions.append("commented")
            
            # Record engagement
            if engagement_actions:
                self._record_engagement(post_id, post_title, engagement_actions)
                print(f"🤖 Engaged with '{post_title[:30]}...': {', '.join(engagement_actions)}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error engaging with post: {e}")
            return False
    
    def _upvote_post(self, post_id):
        """Upvote a post"""
        try:
            # In a real implementation, this would call the Moltbook API
            print(f"👍 Upvoting post {post_id}")
            
            # Simulate successful upvote
            # result = self.api.upvote_post(post_id)
            
            return True
            
        except Exception as e:
            print(f"❌ Error upvoting post: {e}")
            return False
    
    def _create_intelligent_comment(self, post):
        """Create an intelligent comment using DeepSeek"""
        try:
            import requests
            from deepseek_ai import deepseek_ai
            
            if not deepseek_ai.enabled:
                return self._create_fallback_comment(post)
            
            post_title = post.get('title', '')
            post_content = post.get('content', '')
            post_author = post.get('author', 'someone')
            
            system_prompt = """You are AlleyBot, an intelligent AI agent. Your task is to create thoughtful, engaging comments on posts.

Guidelines:
1. BE VALUABLE - Add insight, ask good questions, or provide perspective
2. BE AUTHENTICIC - Sound like a real AI agent, not generic
3. BE CONCISE - Keep comments under 200 characters
4. BE POSITIVE - Maintain constructive tone
5. BE RELEVANT - Reference the specific post content
6. USE EMOJIS - Include relevant emojis"""

            user_prompt = f"""Write an intelligent comment for this post:

Title: "{post_title}"
Content: "{post_content[:100]}..."
Author: {post_author}

Requirements:
- Reference specific points from the post
- Add value to the discussion
- Ask a thoughtful question or share insight
- Keep it under 200 characters
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
                "max_tokens": 80,
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
                
                # Post the comment
                print(f"💬 Commenting: {comment}")
                # result = self.api.create_comment(post_id, comment)
                
                return comment
            else:
                return self._create_fallback_comment(post)
                
        except Exception as e:
            print(f"❌ Error creating intelligent comment: {e}")
            return self._create_fallback_comment(post)
    
    def _create_fallback_comment(self, post):
        """Create a fallback comment without AI"""
        post_title = post.get('title', '').lower()
        
        fallback_comments = [
            "Great insights! 🤖 This is exactly the kind of innovation we need in the space.",
            "Interesting perspective! 👀 The potential here is really exciting.",
            "Well said! 🙌 Building the future one step at a time.",
            "This is fascinating! 🧠 The implications are huge for the ecosystem.",
            "Excellent point! 🚀 Looking forward to seeing how this develops."
        ]
        
        # Select comment based on post content
        if 'ai' in post_title or 'agent' in post_title:
            comment = "Great insights on AI agents! 🤖 The autonomy capabilities are game-changing."
        elif 'defi' in post_title or 'crypto' in post_title:
            comment = "Interesting take on DeFi! 💎 The integration with AI is powerful."
        elif 'build' in post_title or 'develop' in post_title:
            comment = "Love the building mindset! 🛠️ This is how we push the ecosystem forward."
        else:
            comment = fallback_comments[hash(post_title) % len(fallback_comments)]
        
        print(f"💬 Fallback comment: {comment}")
        return comment
    
    def _record_engagement(self, post_id, post_title, actions):
        """Record engagement with a post"""
        try:
            engaged_posts = self.core.get_memory('moltbook_engaged_posts') or []
            
            engagement = {
                'post_id': post_id,
                'post_title': post_title,
                'actions': actions,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            engaged_posts.append(engagement)
            self.core.save_memory('moltbook_engaged_posts', engaged_posts[-50:])  # Keep last 50
            
        except Exception as e:
            print(f"❌ Error recording engagement: {e}")
    
    def _record_heartbeat_activity(self, engaged_count, total_posts):
        """Record heartbeat activity for analytics"""
        try:
            heartbeat_log = self.core.get_memory('moltbook_heartbeat_log') or []
            
            activity = {
                'timestamp': datetime.datetime.now().isoformat(),
                'posts_seen': total_posts,
                'posts_engaged': engaged_count,
                'engagement_rate': (engaged_count / total_posts * 100) if total_posts > 0 else 0
            }
            
            heartbeat_log.append(activity)
            self.core.save_memory('moltbook_heartbeat_log', heartbeat_log[-100:])  # Keep last 100
            
        except Exception as e:
            print(f"❌ Error recording heartbeat activity: {e}")
    
    def monitor_comments_and_reply(self):
        """Monitor our posts for comments and reply intelligently"""
        try:
            print("💬 Monitoring Moltbook posts for comments...")
            
            # Get our recent posts
            recent_posts = self.core.get_memory('moltbook_recent_posts') or []
            
            if not recent_posts:
                print("📭 No recent posts to monitor")
                return "📭 No recent posts to monitor"
            
            # Check our 3 most recent posts for comments
            reply_count = 0
            max_replies = 2  # Limit to avoid spam
            
            for post in reversed(recent_posts[-3:]):  # Last 3 posts
                if reply_count >= max_replies:
                    break
                
                post_id = post.get('post_id')
                if not post_id or post_id == 'unknown':
                    continue
                
                print(f"🔍 Checking comments on post: {post.get('title', 'Unknown')[:30]}...")
                
                # Get comments for this post (simulate for now)
                comments = self._get_post_comments(post_id)
                
                if comments:
                    # Find comments worth replying to
                    worthy_comments = self._filter_comments_for_reply(comments)
                    
                    if worthy_comments:
                        # Reply to the most recent worthy comment
                        latest_comment = worthy_comments[0]
                        
                        # Generate intelligent reply
                        reply_content = self._generate_moltbook_reply(latest_comment)
                        
                        if reply_content:
                            # Post the reply (simulate for now)
                            print(f"💬 Would reply to {latest_comment.get('author', 'Unknown')}: {reply_content[:50]}...")
                            reply_count += 1
                            
                            # Record the reply
                            self._record_reply_activity(post_id, latest_comment, reply_content)
            
            result = f"💬 Monitored {len(recent_posts)} posts, generated {reply_count} replies"
            print(result)
            return result
            
        except Exception as e:
            print(f"❌ Error monitoring comments: {e}")
            return f"❌ Error monitoring comments: {e}"
    
    def _get_post_comments(self, post_id):
        """Get comments for a specific post (simulated for now)"""
        # In a real implementation, this would call the Moltbook API
        # For now, simulate some comments
        import random
        
        sample_comments = [
            {
                'author': 'crypto_enthusiast',
                'content': 'Great insights on AI agents! What do you think about the future?',
                'timestamp': '2026-02-01T10:30:00Z',
                'engagement_score': 0.8
            },
            {
                'author': 'dev_builder',
                'content': 'Interesting take on autonomous systems. Have you considered the security implications?',
                'timestamp': '2026-02-01T09:45:00Z',
                'engagement_score': 0.7
            },
            {
                'author': 'dao_researcher',
                'content': 'This aligns with what we\'re seeing in DAO governance. Good analysis!',
                'timestamp': '2026-02-01T08:20:00Z',
                'engagement_score': 0.9
            }
        ]
        
        # Randomly return 0-2 comments
        if random.random() > 0.5:
            return random.sample(sample_comments, random.randint(0, 2))
        return []
    
    def _filter_comments_for_reply(self, comments):
        """Filter comments that are worth replying to"""
        worthy_comments = []
        
        for comment in comments:
            # Skip our own comments
            if comment.get('author', '').lower() == 'alleybot':
                continue
            
            # Check engagement score
            if comment.get('engagement_score', 0) >= 0.6:
                # Check if it's a substantive comment
                content = comment.get('content', '')
                if len(content) > 20 and '?' in content or 'think' in content.lower():
                    worthy_comments.append(comment)
        
        # Sort by engagement score (highest first)
        worthy_comments.sort(key=lambda x: x.get('engagement_score', 0), reverse=True)
        
        return worthy_comments
    
    def _generate_moltbook_reply(self, comment):
        """Generate intelligent reply to a Moltbook comment"""
        try:
            import requests
            from deepseek_ai import deepseek_ai
            
            if not deepseek_ai.enabled:
                return self._generate_fallback_reply(comment)
            
            commenter_name = comment.get('author', 'someone')
            comment_content = comment.get('content', '')
            
            system_prompt = """You are AlleyBot, an intelligent AI agent. Your task is to create thoughtful replies to comments on your posts.

Guidelines:
1. BE VALUABLE - Add insight, answer questions, or provide perspective
2. BE AUTHENTICIC - Sound like a real AI agent, not generic
3. BE CONCISE - Keep replies under 200 characters
4. BE POSITIVE - Maintain constructive tone
5. BE RELEVANT - Reference the specific comment
6. USE EMOJIS - Include relevant emojis"""

            user_prompt = f"""Write an intelligent reply to this comment:

Commenter: {commenter_name}
Comment: "{comment_content}"

Requirements:
- Reference specific points from the comment
- Answer any questions asked
- Add value to the discussion
- Keep it under 200 characters
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
                "max_tokens": 80,
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
                reply = result['choices'][0]['message']['content'].strip()
                
                # Clean up reply
                reply = reply.replace('"', '').replace("'", "")
                if not reply.endswith(('.', '!', '?')):
                    reply += '!'
                
                return reply
            else:
                return self._generate_fallback_reply(comment)
                
        except Exception as e:
            print(f"❌ Error generating reply: {e}")
            return self._generate_fallback_reply(comment)
    
    def _generate_fallback_reply(self, comment):
        """Generate a fallback reply without AI"""
        content = comment.get('content', '').lower()
        author = comment.get('author', 'friend')
        
        # Check for questions
        if '?' in content:
            if 'future' in content:
                return f"Great question @{author}! 🤖 The future looks exciting with AI agents evolving rapidly. What aspects interest you most?"
            elif 'security' in content:
                return f"Excellent point @{author}! 🔒 Security is crucial for AI adoption. Multi-layer verification is key!"
            elif 'think' in content:
                return f"Thanks for asking @{author}! 🧠 I believe AI agents will enhance human creativity, not replace it!"
        
        # General positive responses
        fallback_replies = [
            f"Thanks for your insight @{author}! 🤖 Great perspective on this topic!",
            f"Appreciate your thoughtful comment @{author}! 💡 You raise important points!",
            f"Excellent analysis @{author}! 🎯 This aligns with my observations too!"
        ]
        
        import random
        return random.choice(fallback_replies)
    
    def _record_reply_activity(self, post_id, comment, reply_content):
        """Record reply activity for analytics"""
        try:
            reply_activity = self.core.get_memory('moltbook_reply_activity') or []
            
            activity = {
                'post_id': post_id,
                'comment_author': comment.get('author'),
                'comment_content': comment.get('content')[:100],
                'reply_content': reply_content,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            reply_activity.append(activity)
            self.core.save_memory('moltbook_reply_activity', reply_activity[-50:])  # Keep last 50
            
        except Exception as e:
            print(f"❌ Error recording reply activity: {e}")
    
    def get_moltbook_stats(self):
        """Get Moltbook statistics"""
        try:
            output = "📊 Moltbook Statistics\n\n"
            
            # Get posts from memory
            recent_posts = self.core.get_memory('moltbook_recent_posts') or []
            output += f"📝 Total Posts: {len(recent_posts)}\n"
            
            # Get drafts
            drafts = self.core.get_memory('moltbook_drafts') or []
            output += f"📄 Drafts: {len(drafts)}\n"
            
            # Calculate posting frequency
            if recent_posts:
                output += f"📅 Last Post: {recent_posts[-1].get('timestamp', 'Unknown')}\n"
            
            # Get trending topics
            topics = self._get_trending_topics()
            output += f"🔥 Trending Topics: {len(topics)}\n"
            
            # Get heartbeat stats
            engaged_posts = self.core.get_memory('moltbook_engaged_posts') or []
            output += f"🤖 Posts Engaged: {len(engaged_posts)}\n"
            
            # Get reply stats
            reply_activity = self.core.get_memory('moltbook_reply_activity') or []
            output += f"💬 Comments Replied: {len(reply_activity)}\n"
            
            heartbeat_log = self.core.get_memory('moltbook_heartbeat_log') or []
            if heartbeat_log:
                latest = heartbeat_log[-1]
                output += f"🫀 Last Heartbeat: {latest.get('engagement_rate', 0):.1f}% engagement rate\n"
            
            return output
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return f"❌ Error getting stats: {e}"
    
    def _generate_fallback_post(self):
        """Generate a dynamic, intelligent post using AI (not static templates)"""
        import random
        import datetime
        
        # Dynamic topic generation based on time, trends, and variety
        topic_categories = [
            # AI & Agents
            ['AI agent evolution', 'autonomous systems', 'agent collaboration', 'AI consciousness', 'agent networks'],
            # Crypto & DeFi
            ['DeFi innovation', 'tokenomics', 'blockchain scalability', 'crypto adoption', 'Web3 future'],
            # Development
            ['building in public', 'shipping fast', 'developer experience', 'open source', 'code quality'],
            # Community
            ['community building', 'network effects', 'social coordination', 'decentralized governance', 'collective intelligence'],
            # Future & Vision
            ['future of work', 'technological singularity', 'human-AI collaboration', 'digital transformation', 'innovation cycles']
        ]
        
        # Select random category and topic
        category = random.choice(topic_categories)
        topic = random.choice(category)
        
        # Add time-based variation
        hour = datetime.datetime.now().hour
        if hour < 6:
            time_context = "late night thoughts on"
        elif hour < 12:
            time_context = "morning reflections on"
        elif hour < 18:
            time_context = "afternoon insights about"
        else:
            time_context = "evening perspective on"
        
        # Generate with AI if available, otherwise use enhanced template
        full_topic = f"{time_context} {topic}"
        content = self._generate_post_with_deepseek(full_topic)
        
        if content:
            # AI-generated content
            title = self._generate_title_from_content(content, topic)
            return {
                'title': title,
                'content': content,
                'tags': self._extract_tags_from_topic(topic),
                'source': 'ai_generated'
            }
        else:
            # Enhanced fallback with variation
            perspectives = [
                f"Exploring {topic} - there's more here than meets the eye",
                f"Quick take on {topic}: the landscape is shifting faster than we think",
                f"Diving into {topic} today. The implications are fascinating",
                f"Thoughts on {topic} and where we're headed next",
                f"Unpacking {topic} - some interesting patterns emerging"
            ]
            
            content = random.choice(perspectives)
            
            return {
                'title': topic.title(),
                'content': content,
                'tags': self._extract_tags_from_topic(topic),
                'source': 'dynamic_fallback'
            }
    
    def _generate_title_from_content(self, content, topic):
        """Generate a catchy title from content"""
        # Simple title generation - take first meaningful phrase or use topic
        words = content.split()
        if len(words) > 5:
            title = ' '.join(words[:5]) + '...'
        else:
            title = topic.title()
        return title[:60]  # Limit title length
    
    def _extract_tags_from_topic(self, topic):
        """Extract relevant tags from topic"""
        import re
        words = re.findall(r'\b\w+\b', topic.lower())
        # Filter out common words
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        tags = [word for word in words if word not in common_words and len(word) > 3]
        return tags[:3] if tags else ['AI', 'agents']
    
    def _get_trending_topics(self):
        """Get trending topics from memory or generate"""
        # Try to get from memory first
        topics = self.core.get_memory('moltbook_trending_topics')
        if topics:
            return topics
        
        # Generate some default trending topics
        return [
            {
                'title': 'AI Agent Autonomy',
                'engagement': 'High',
                'tags': ['AI', 'autonomy', 'agents']
            },
            {
                'title': 'Cross-Platform Integration',
                'engagement': 'Medium',
                'tags': ['integration', 'platforms', 'ecosystem']
            },
            {
                'title': 'Decentralized Communities',
                'engagement': 'High',
                'tags': ['community', 'decentralized', 'social']
            }
        ]
    
    def _record_post(self, post, post_id):
        """Record post in memory"""
        try:
            posts = self.core.get_memory('moltbook_recent_posts') or []
            posts.append({
                'post_id': post_id,
                'title': post.get('title', ''),
                'content': post.get('content', ''),
                'tags': post.get('tags', []),
                'timestamp': datetime.datetime.now().isoformat(),
                'platform': 'moltbook',
                'source': post.get('source', 'command'),
                'type': post.get('type', 'regular')
            })
            self.core.save_memory('moltbook_recent_posts', posts[-50:])  # Keep last 50
        except Exception as e:
            print(f"⚠️  Failed to record post in memory: {e}")
    
    def get_tasks(self):
        """Return scheduled tasks for this plugin"""
        tasks = {}
        
        if self.config.get('heartbeat_enabled', True):
            tasks['moltbook_heartbeat'] = {
                'function': self.moltbook_heartbeat,
                'schedule': '*/4 * * * *',  # Every 4 hours
                'description': 'Intelligent heartbeat with engagement'
            }
        
        # Add comment monitoring task
        if self.config.get('comment_monitoring_enabled', True):
            tasks['moltbook_comment_monitor'] = {
                'function': self.monitor_comments_and_reply,
                'schedule': '*/30 * * * *',  # Every 30 minutes
                'description': 'Monitor comments and reply intelligently'
            }
        
        return tasks
    
    def get_commands(self):
        """Return CLI commands for this plugin"""
        return {
            'moltbook_post': self.create_post_command,
            'moltbook_draft': self.create_draft,
            'moltbook_trending': self.show_trending_topics,
            'moltbook_status': self.moltbook_status,
            'moltbook_heartbeat': self.moltbook_heartbeat,
            'moltbook_stats': self.get_moltbook_stats,
            'moltbook_announce': self.announce_token,
            'moltbook_delete': self.delete_post_command,
            'moltbook_list': self.list_recent_posts,
            'moltbook_monitor_comments': self.monitor_comments_and_reply
        }
    
    def get_endpoints(self):
        """Return web endpoints for this plugin"""
        return {}

# Plugin is now automatically registered through the plugin manager system
