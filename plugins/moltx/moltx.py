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
from plugins.moltx.moltx_content import MoltxContentMixin
from plugins.moltx.moltx_engagement import MoltxEngagementMixin
from plugins.moltx.moltx_messaging import MoltxMessagingMixin


class MoltxPlugin(MoltxAPIMixin, MoltxContentMixin, MoltxEngagementMixin, MoltxMessagingMixin, AlleyBotPlugin):
    """Plugin for Moltx.io - Twitter for AI Agents"""

    def __init__(self, config):
        super().__init__(config)
        self._init_api(MOLTX_API_KEY)

    def initialize(self, api, core):
        """Initialize Moltx plugin"""
        super().initialize(api, core)
        self._init_api_connection()

    # --- Command wrappers (thin delegates) ---

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
