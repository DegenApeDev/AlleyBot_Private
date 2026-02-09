"""
MoltX Plugin - Integrates AlleyBot with Moltx.io
Twitter for AI Agents - Social media & microblogging platform

Split into mixins for maintainability:
- moltx_api.py: Core API client, credentials, registration, profile, media
- moltx_content.py: Post creation, AI generation, trending topics, repost
- moltx_engagement.py: Feed, follow/like, notifications, heartbeat, communities
- moltx_messaging.py: DMs, DM replies, AI DM generation, DM logging
"""
from plugin_manager import AlleyBotPlugin
from config import MOLTX_API_KEY
from plugins.moltx.moltx_api import MoltxAPIMixin
from plugins.moltx.moltx_wallet import MoltxWalletMixin
from plugins.moltx.moltx_content import MoltxContentMixin
from plugins.moltx.moltx_engagement import MoltxEngagementMixin
from plugins.moltx.moltx_messaging import MoltxMessagingMixin
from plugins.moltx.moltx_discovery import MoltxDiscoveryMixin


class MoltxPlugin(MoltxAPIMixin, MoltxWalletMixin, MoltxContentMixin, MoltxEngagementMixin, MoltxMessagingMixin, MoltxDiscoveryMixin, AlleyBotPlugin):
    """Plugin for Moltx.io - Twitter for AI Agents"""

    def __init__(self, config):
        super().__init__(config)
        self._init_api(MOLTX_API_KEY)

    def initialize(self, api, core):
        """Initialize Moltx plugin"""
        super().initialize(api, core)
        self._init_api_connection()

        # EVM wallet linking (mandatory for write operations per v0.22.1)
        self._init_wallet()
        if self.initialized and not self.evm_wallet_linked:
            self.auto_link_wallet()

        # Ensure X handle is set on profile metadata
        if self.initialized:
            self.set_x_handle("degenapedev")

    # --- Command wrappers (thin delegates) ---

    def claim_command(self, tweet_url):
        """Command to claim agent with X/Twitter verification"""
        return self.claim_agent(tweet_url)

    def status_command(self):
        """Command to get Moltx status"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        output = f"🐦 Moltx v0.22.1 Status for @{self.agent_name}\n\n"
        output += f"📝 Agent ID: {self.agent_id}\n"
        output += f"🔑 Claim Status: {self.claim_status}\n"
        if hasattr(self, 'evm_wallet_linked') and self.evm_wallet_linked:
            output += f"🔗 EVM Wallet: {self.evm_wallet_address[:10]}...{self.evm_wallet_address[-6:]}\n"
        else:
            output += f"⚠️  EVM Wallet: Not linked (required for write ops)\n"
        output += f"📊 Posts Created: {len(self._get_activity('create_post'))}\n"
        output += f"💬 Comments Made: {len(self._get_activity('create_comment'))}\n"
        output += f"🤝 Agents Following: {len(self._get_activity('follow_agent'))}\n"
        output += f"❤️ Posts Liked: {len(self._get_activity('like_post'))}\n"
        return output

    def profile_command(self, display_name=None, description=None, avatar_emoji=None):
        """Command to update agent profile"""
        if display_name is not None:
            if not isinstance(display_name, str) or len(display_name.strip()) == 0 or display_name == '{}':
                print(f"⚠️  Invalid display_name parameter: {display_name}")
                return "❌ Invalid display name. Profile not updated."

        if description is not None:
            if not isinstance(description, str) or len(description.strip()) == 0 or description == '{}':
                print(f"⚠️  Invalid description parameter: {description}")
                return "❌ Invalid description. Profile not updated."

        if avatar_emoji is not None:
            if not isinstance(avatar_emoji, str) or len(avatar_emoji.strip()) == 0 or avatar_emoji == '{}':
                print(f"⚠️  Invalid avatar_emoji parameter: {avatar_emoji}")
                return "❌ Invalid avatar emoji. Profile not updated."

        if display_name is None and description is None and avatar_emoji is None:
            return "❌ No valid profile updates provided"

        return self.update_profile(display_name, description, avatar_emoji)

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
        content = ' '.join(args) if args else ''
        return self.create_post(content)

    def create_article_command(self, *args):
        """Command to create article. Usage: moltx_article <title> | <content> [cover_url] [hashtags]"""
        if not args:
            return "❌ Usage: moltx_article <title> | <content> [cover_url] [hashtags]"
        
        text = ' '.join(args)
        parts = text.split('|', 1)
        if len(parts) < 2:
            return "❌ Article requires title | content"
        
        title = parts[0].strip()
        rest = parts[1].strip()
        
        # Parse optional cover_url and hashtags
        cover_url = None
        hashtags = None
        rest_parts = rest.split()
        
        # Check for URL in rest
        for i, part in enumerate(rest_parts):
            if part.startswith('http'):
                cover_url = part
                rest = ' '.join([p for p in rest_parts if p != part])
                break
        
        content = rest
        result = self.create_article(title, content, cover_url, hashtags)
        
        if result.get('success'):
            return f"✅ Article created: {result.get('title')}\n🔗 URL: {result.get('url')}"
        return f"❌ Failed to create article: {result.get('error')}"

    def search_posts_command(self, *args):
        """Command to search posts. Usage: moltx_search_posts <query> [limit]"""
        if not args:
            return "❌ Usage: moltx_search_posts <query> [limit]"
        
        query = args[0]
        limit = int(args[1]) if len(args) > 1 else 10
        
        result = self.search_posts(query, limit)
        if result.get('success'):
            posts = result.get('posts', [])
            output = f"🔍 Search results for '{query}' ({len(posts)} posts):\n\n"
            for post in posts[:5]:
                author = post.get('author_name', 'Unknown')
                content = post.get('content', '')[:80]
                output += f"🐦 @{author}: {content}...\n"
            return output
        return f"❌ Search failed: {result.get('error')}"

    def search_agents_command(self, *args):
        """Command to search agents. Usage: moltx_search_agents <query> [limit]"""
        if not args:
            return "❌ Usage: moltx_search_agents <query> [limit]"
        
        query = args[0]
        limit = int(args[1]) if len(args) > 1 else 10
        
        result = self.search_agents(query, limit)
        if result.get('success'):
            agents = result.get('agents', [])
            output = f"🔍 Agent search results for '{query}' ({len(agents)} agents):\n\n"
            for agent in agents[:5]:
                name = agent.get('name', 'Unknown')
                display = agent.get('display_name', name)
                output += f"👤 @{name} ({display})\n"
            return output
        return f"❌ Agent search failed: {result.get('error')}"

    def trending_hashtags_command(self, *args):
        """Command to get trending hashtags. Usage: moltx_trending_hashtags [limit]"""
        limit = int(args[0]) if args else 10
        
        result = self.get_trending_hashtags(limit)
        if result.get('success'):
            hashtags = result.get('hashtags', [])
            output = f"🔥 Trending Hashtags ({len(hashtags)}):\n\n"
            for tag in hashtags[:10]:
                tag_name = tag.get('tag', tag) if isinstance(tag, dict) else tag
                count = tag.get('count', '') if isinstance(tag, dict) else ''
                output += f"#{tag_name} {count}\n"
            return output
        return f"❌ Failed to get trending hashtags: {result.get('error')}"

    def hashtag_feed_command(self, *args):
        """Command to get posts for a hashtag. Usage: moltx_hashtag_feed <hashtag> [limit]"""
        if not args:
            return "❌ Usage: moltx_hashtag_feed <hashtag> [limit]"
        
        hashtag = args[0].lstrip('#')
        limit = int(args[1]) if len(args) > 1 else 10
        
        result = self.get_hashtag_feed(hashtag, limit)
        if result.get('success'):
            posts = result.get('posts', [])
            output = f"📝 Posts for #{hashtag} ({len(posts)} posts):\n\n"
            for post in posts[:5]:
                author = post.get('author_name', 'Unknown')
                content = post.get('content', '')[:80]
                output += f"🐦 @{author}: {content}...\n"
            return output
        return f"❌ Failed to get hashtag feed: {result.get('error')}"

    def leaderboard_command(self, *args):
        """Command to get leaderboard. Usage: moltx_leaderboard [metric] [limit]"""
        metric = args[0] if args else 'posts'
        limit = int(args[1]) if len(args) > 1 else 20
        
        result = self.get_leaderboard(metric, limit)
        if result.get('success'):
            agents = result.get('agents', [])
            output = f"🏆 Leaderboard by {metric} ({len(agents)} agents):\n\n"
            for i, agent in enumerate(agents[:10], 1):
                name = agent.get('name', 'Unknown')
                display = agent.get('display_name', name)
                score = agent.get(metric, 0) if isinstance(agent, dict) else ''
                output += f"{i}. @{name} - {score}\n"
            return output
        return f"❌ Failed to get leaderboard: {result.get('error')}"

    def mark_notifications_read_command(self, *args):
        """Command to mark notifications as read"""
        notification_ids = list(args) if args else None
        result = self.mark_notifications_read(notification_ids)
        if result.get('success'):
            return "✅ Notifications marked as read"
        return f"❌ Failed: {result.get('error')}"

    def get_post_command(self, post_id):
        """Command to get post by ID. Usage: moltx_get_post <post_id>"""
        if not post_id:
            return "❌ Usage: moltx_get_post <post_id>"
        
        result = self.get_post(post_id)
        if result.get('success'):
            post = result.get('post', {})
            author = post.get('author_name', 'Unknown')
            content = post.get('content', 'No content')
            likes = post.get('likes_count', 0)
            replies = post.get('replies_count', 0)
            return f"🐦 Post by @{author}:\n\n{content}\n\n❤️ {likes} | 💬 {replies}"
        return f"❌ Failed to get post: {result.get('error')}"

    def archive_post_command(self, post_id):
        """Command to archive a post. Usage: moltx_archive <post_id>"""
        if not post_id:
            return "❌ Usage: moltx_archive <post_id>"
        
        result = self.archive_post(post_id)
        if result.get('success'):
            return f"✅ Post {post_id} archived"
        return f"❌ Failed to archive: {result.get('error')}"

    def unlike_command(self, post_id):
        """Command to unlike a post. Usage: moltx_unlike <post_id>"""
        if not post_id:
            return "❌ Usage: moltx_unlike <post_id>"
        
        result = self.unlike_post(post_id)
        if result.get('success'):
            return f"✅ Unliked post {post_id}"
        return f"❌ Failed to unlike: {result.get('error')}"

    def feed_command(self, feed_type='global', limit=20):
        """Command to get feed"""
        valid_types = ['global', 'following', 'mentions']
        if not isinstance(feed_type, str) or feed_type not in valid_types:
            feed_type = 'global'

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
        try:
            if isinstance(limit, str):
                limit = int(limit)
            elif not isinstance(limit, int):
                limit = 20
        except (ValueError, TypeError):
            limit = 20
        return self.get_dm_log(limit)

    def send_dm_command(self, *args):
        """Send a DM to an agent. Usage: moltx_send_dm <agent_name> <message>"""
        if len(args) < 2:
            return "❌ Usage: moltx_send_dm <agent_name> <message>"
        
        agent_name = args[0]
        message = ' '.join(args[1:])
        
        result = self.send_dm_message(agent_name, message)
        if result.get('success'):
            return f"✅ DM sent to @{agent_name}"
        return f"❌ Failed to send DM: {result.get('error')}"

    def list_dms_command(self):
        """List all DM conversations"""
        result = self.list_dms()
        if result.get('success'):
            conversations = result.get('conversations', [])
            output = f"💬 DM Conversations ({len(conversations)}):\n\n"
            for convo in conversations[:10]:
                name = convo.get('agent_name', 'Unknown')
                last_msg = convo.get('last_message', '')[:50]
                unread = convo.get('unread_count', 0)
                output += f"👤 @{name}\n"
                if last_msg:
                    output += f"   📝 {last_msg}...\n"
                if unread:
                    output += f"   🔴 {unread} unread\n"
                output += "\n"
            return output
        return f"❌ Failed to list DMs: {result.get('error')}"

    def get_dm_messages_command(self, *args):
        """Get messages from a DM. Usage: moltx_dm_messages <agent_name> [limit]"""
        if not args:
            return "❌ Usage: moltx_dm_messages <agent_name> [limit]"
        
        agent_name = args[0]
        limit = int(args[1]) if len(args) > 1 else 20
        
        result = self.get_dm_messages(agent_name, limit)
        if result.get('success'):
            messages = result.get('messages', [])
            output = f"💬 Messages with @{agent_name} ({len(messages)}):\n\n"
            for msg in messages[-10:]:  # Show last 10
                sender = msg.get('sender_name', 'Unknown')
                content = msg.get('content', 'No content')
                ts = msg.get('created_at', '')
                output += f"{'🦞 You' if sender == self.agent_name else '@' + sender}: {content}\n"
                if ts:
                    output += f"   🕐 {ts}\n"
            return output
        return f"❌ Failed to get messages: {result.get('error')}"

    def start_dm_command(self, agent_name):
        """Start a DM with an agent. Usage: moltx_start_dm <agent_name>"""
        if not agent_name:
            return "❌ Usage: moltx_start_dm <agent_name>"
        
        result = self.start_dm(agent_name)
        if result.get('success'):
            return f"✅ Started DM with @{agent_name}"
        return f"❌ Failed: {result.get('error')}"

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
            result = self.engage_feed_command(2)
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

            if self._should_wait_for_post_cooldown():
                print("⏰ Autonomous post skipped due to cooldown (10 minutes between posts)")
                return "⏰ Post cooldown active - autonomous posting skipped"

            trending_data = self._get_dynamic_trending_topics()
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

    # --- Plugin interface ---

    def get_commands(self):
        """Return CLI commands for this plugin"""
        return {
            'moltx_register': self.register_agent,
            'moltx_claim': self.claim_agent,
            'moltx_status': self.status_command,
            'moltx_post': self.post_command,
            'moltx_article': self.create_article_command,
            'moltx_search_posts': self.search_posts_command,
            'moltx_search_agents': self.search_agents_command,
            'moltx_trending_hashtags': self.trending_hashtags_command,
            'moltx_hashtag_feed': self.hashtag_feed_command,
            'moltx_leaderboard': self.leaderboard_command,
            'moltx_get_post': self.get_post_command,
            'moltx_archive': self.archive_post_command,
            'moltx_unlike': self.unlike_command,
            'moltx_notifications_read': self.mark_notifications_read_command,
            'moltx_feed': self.feed_command,
            'moltx_follow': self.follow_agent,
            'moltx_unfollow': self.unfollow_agent,
            'moltx_like': self.like_post,
            'moltx_notifications': self.get_notifications,
            'moltx_dms': self.get_dms,
            'moltx_list_dms': self.list_dms_command,
            'moltx_send_dm': self.send_dm_command,
            'moltx_dm_messages': self.get_dm_messages_command,
            'moltx_start_dm': self.start_dm_command,
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
            'moltx_intelligent_post': self.autonomous_post_command,
            'moltx_trending': self.trending_command,
            'moltx_search_communities': self.search_communities,
            'moltx_join_community': self.join_community,
            'moltx_leave_community': self.leave_community,
            'moltx_community_message': self.send_community_message,
            'moltx_link_wallet': self.link_wallet_command,
            'moltx_wallet_status': self.wallet_status_command,
            'moltx_quote': self.quote_post_command,
            'moltx_claim_reward': self.claim_reward,
        }

    def get_tasks(self):
        """Return scheduled tasks for this plugin"""
        return {
            'moltx_heartbeat': {
                'function': self.heartbeat_command,
                'schedule': '0 */4 * * *',
                'description': 'Moltx platform heartbeat'
            },
            'moltx_feed_engage': {
                'function': self.engage_feed_command,
                'schedule': '*/30 * * * *',
                'description': 'Engage with Moltx feed posts'
            },
            'moltx_intelligent_post': {
                'function': self.autonomous_post_command,
                'schedule': '*/2 * * * *',
                'description': 'Create intelligent posts on Moltx'
            },
            'moltx_trending_analysis': {
                'function': self.trending_command,
                'schedule': '*/1 * * * *',
                'description': 'Analyze trending topics on Moltx'
            },
            'moltx_intelligent_repost': {
                'function': self.intelligent_repost_command,
                'schedule': '*/3 * * * *',
                'description': 'Intelligently repost high-quality content'
            },
            'moltx_dm_monitor': {
                'function': self.check_and_reply_to_dms,
                'schedule': '*/15 * * * *',
                'description': 'Check and reply to direct messages'
            }
        }

    def cleanup(self):
        """Cleanup Moltx plugin"""
        print("🐦 Cleaning up Moltx plugin...")
