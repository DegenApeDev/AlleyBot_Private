#!/usr/bin/env python3
"""
Moltbook Plugin for AlleyBot
Handles posting, engagement, and content creation on Moltbook platform

Split into mixins for maintainability:
- moltbook_api.py: API client, feed fetching, post management
- moltbook_content.py: Post creation, AI generation, drafts, trending
- moltbook_engagement.py: Heartbeat, comment monitoring, engagement, stats
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin
from plugins.moltbook.moltbook_api import MoltbookAPIMixin
from plugins.moltbook.moltbook_content import MoltbookContentMixin
from plugins.moltbook.moltbook_engagement import MoltbookEngagementMixin


class MoltbookPlugin(MoltbookAPIMixin, MoltbookContentMixin, MoltbookEngagementMixin, AlleyBotPlugin):
    """Moltbook-specific content and interaction plugin"""

    def __init__(self, config):
        super().__init__(config)
        self.last_post_time = None
        self.trending_topics = []
        self.api_key = os.getenv('MOLTBOOK_API_KEY')
        self.base_url = 'https://www.moltbook.com/api/v1'
        self.mb_api = None  # Will be initialized in initialize()

    def initialize(self, api, core):
        super().initialize(api, core)
        if self.api_key:
            print("✅ Moltbook API key loaded from environment")
            self._init_moltbook_api()
        else:
            print("⚠️  Moltbook API key not found in environment")

    def get_tasks(self):
        """Return scheduled tasks for this plugin"""
        tasks = {}

        if self.config.get('heartbeat_enabled', True):
            tasks['moltbook_heartbeat'] = {
                'function': self.moltbook_heartbeat,
                'schedule': '*/4 * * * *',
                'description': 'Intelligent heartbeat with engagement'
            }

        if self.config.get('comment_monitoring_enabled', True):
            tasks['moltbook_comment_monitor'] = {
                'function': self.monitor_comments_and_reply,
                'schedule': '*/30 * * * *',
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
            'moltbook_monitor_comments': self.monitor_comments_and_reply,
            # v1.9.0 commands
            'moltbook_follow': self.follow_command,
            'moltbook_unfollow': self.unfollow_command,
            'moltbook_search': self.search_command,
            'moltbook_profile': self.profile_command,
            'moltbook_avatar': self.avatar_command,
            'moltbook_remove_avatar': self.remove_avatar_command,
            'moltbook_update_profile': self.update_profile_command,
            'moltbook_submolts': self.submolts_command,
            'moltbook_subscribe': self.subscribe_command,
            'moltbook_unsubscribe': self.unsubscribe_command,
            'moltbook_feed': self.feed_command,
            'moltbook_upvote': self.upvote_command,
            'moltbook_downvote': self.downvote_command,
            'moltbook_comment': self.comment_command,
            'moltbook_link': self.link_post_command,
            'moltbook_claim_status': self.claim_status_command,
        }

    def get_endpoints(self):
        """Return web endpoints for this plugin"""
        return {}


# Plugin is now automatically registered through the plugin manager system
