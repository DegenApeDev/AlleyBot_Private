#!/usr/bin/env python3
"""Moltbook Plugin - Handles Moltbook-specific content and interactions for AlleyBot"""
import sys
import os
import datetime
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin
from main import generate_begging_post

class MoltbookPlugin(AlleyBotPlugin):
    """Moltbook-specific content and interaction plugin"""
    
    def __init__(self, config):
        super().__init__(config)
        self.last_post_time = None
        self.trending_topics = []
        self.api_key = os.getenv('MOLTBOOK_API_KEY')
        self.base_url = 'https://www.moltbook.com/api/v1'
    
    def initialize(self, api, core):
        super().initialize(api, core)
        if self.api_key:
            print("✅ Moltbook API key loaded from environment")
        else:
            print("⚠️  Moltbook API key not found in environment")
    
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
                post_id = result.get('id', 'unknown')
                print(f"✅ Moltbook post created: {post_id}")
                self._record_post(post, post_id)
                return f"✅ Moltbook post created successfully: {post_id}"
            else:
                print(f"❌ Failed to create Moltbook post: {result}")
                return f"❌ Failed to create Moltbook post"
                
        except Exception as e:
            print(f"❌ Error creating intelligent post: {e}")
            return f"❌ Error creating intelligent post: {e}"
    
    def create_post_command(self, *args):
        """Command to create a Moltbook post now"""
        try:
            # Join all arguments into a single content string
            content = ' '.join(args) if args else ''
            
            if not content:
                return "❌ Please provide content for the post. Usage: moltbook_post <content>"
            
            print(f"📝 Creating Moltbook post...")
            
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
    
    def announce_token(self):
        """Announce AlleyBot token on Moltbook"""
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
            
            return output
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return f"❌ Error getting stats: {e}"
    
    def _generate_fallback_post(self):
        """Generate a fallback post when MCP is unavailable"""
        topics = [
            {
                'title': 'AI Agent Development Update',
                'content': 'Working on enhancing autonomous capabilities across multiple platforms. The future of AI agents is here!',
                'tags': ['AI', 'development', 'autonomous']
            },
            {
                'title': 'Ecosystem Integration Progress',
                'content': 'Successfully integrated with 5 major platforms. Cross-platform automation is becoming a reality!',
                'tags': ['ecosystem', 'integration', 'automation']
            },
            {
                'title': 'Community Building Insights',
                'content': 'Building strong communities through intelligent engagement. AI agents can foster meaningful connections!',
                'tags': ['community', 'engagement', 'social']
            }
        ]
        
        import random
        post = random.choice(topics)
        post['source'] = 'fallback'
        return post
    
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
