"""
Moltx Engagement Mixin
Feed browsing, follow/unfollow, likes, notifications, heartbeat loops, and feed engagement.
"""
import json
import time
import random
import requests


class MoltxEngagementMixin:
    """Mixin providing social engagement functionality"""

    def __init__(self, *args, **kwargs):
        """Initialize mixin - accepts any args/kwargs for cooperative inheritance"""
        super().__init__(*args, **kwargs)

    def _get_feed_data(self, feed_type, limit):
        """Internal: Fetch raw feed data"""
        params = {'limit': limit}
        if feed_type == 'global':
            params['type'] = 'post,quote'
            url = f"{self.base_url}/feed/global"
            headers = {}
            try:
                print(f"🔍 Fetching {feed_type} feed from: {url}")
                response = requests.get(url, params=params, headers=headers, timeout=10)
                print(f"🔍 Response status: {response.status_code}")
                response.raise_for_status()
                result = response.json()
                print(f"🔍 Feed response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                return result
            except requests.exceptions.RequestException as e:
                print(f"❌ Network error fetching {feed_type} feed: {e}")
                return f"❌ Network error fetching {feed_type} feed: {e}"
            except Exception as e:
                print(f"❌ Failed to fetch {feed_type} feed: {e}")
                return f"❌ Failed to fetch {feed_type} feed: {e}"
        else:
            if not self.initialized:
                return "❌ Moltx not initialized"
            return self._make_request('GET', f'/feed/{feed_type}', params=params)

    def get_feed(self, feed_type='global', limit=20):
        """Get feed (global, following, mentions)"""
        valid_types = ['global', 'following', 'mentions']
        if feed_type not in valid_types:
            feed_type = 'global'

        if not self.initialized and feed_type != 'global':
            return "❌ Moltx not initialized for this feed type"

        data = self._get_feed_data(feed_type, limit)
        if isinstance(data, str):
            return data

        # Handle different response structures
        posts = []
        if data:
            if 'posts' in data:
                posts = data['posts']
            elif 'data' in data and isinstance(data['data'], dict) and 'posts' in data['data']:
                posts = data['data']['posts']
            elif isinstance(data, list):
                posts = data
            else:
                print(f"🔍 Unexpected feed response format: {data}")

        if posts:
            output = f"🐦 {feed_type.title()} Feed ({len(posts)} posts):\n\n"

            for post in posts[:limit]:
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
            return f"❌ No posts in {feed_type} feed"

    def _get_raw_notifications(self):
        """Internal: Get raw notifications data"""
        if not self.initialized:
            return []
        result = self._make_request('GET', '/notifications')
        print(f"🔍 Notifications response structure: {list(result.keys()) if isinstance(result, dict) else type(result) if result else 'None'}")
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
        return notifications

    def get_notifications(self):
        """Get notifications"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        notifications = self._get_raw_notifications()

        if notifications:
            output = f"🔔 Notifications ({len(notifications)}):\n\n"
            type_emojis = {
                'follow': '👥',
                'like': '❤️',
                'reply': '💬',
                'quote': '🔄',
                'mention': '📢',
            }
            for notif in notifications[:10]:
                if isinstance(notif, dict):
                    notif_type = (notif.get('type') or notif.get('category') or notif.get('action') or 'unknown').lower()
                    display_emoji = type_emojis.get(notif_type, '🔔')
                    display_type = notif_type.title()
                    content = notif.get('content') or notif.get('message') or notif.get('text') or 'No content'
                    timestamp = notif.get('created_at') or notif.get('timestamp') or 'Unknown time'
                    actor = notif.get('actor') or notif.get('from_user') or notif.get('user') or ''

                    output += f"{display_emoji} {display_type}"
                    if actor:
                        output += f" from @{actor}"
                    output += f": {content[:100]}{'...' if len(content) > 100 else ''}\n"
                    output += f"   🕐 {timestamp}\n\n"
                else:
                    output += f"🔔 {str(notif)[:100]}{'...' if len(str(notif)) > 100 else ''}\n\n"
            return output
        else:
            return "🔔 No notifications found"

    def follow_agent(self, agent_name):
        """Follow an agent"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        if not agent_name:
            return "❌ No agent name provided"
        agent_name = agent_name.strip().lstrip('@')
        result = self._make_request('POST', f'/follow/{agent_name}')
        if not result:
            return f"❌ No response when following @{agent_name}"
        if isinstance(result, dict):
            if result.get('success') or result.get('status') == 'ok' or 'followed' in str(result).lower():
                self._record_activity('follow', {'target': agent_name})
                msg = result.get('message', 'Success')
                return f"✅ Now following @{agent_name}: {msg}"
            elif 'error' in result or 'message' in result:
                err = result.get('error') or result.get('message', 'Unknown error')
                return f"❌ Failed to follow @{agent_name}: {err}"
        return f"❌ Unexpected response when following @{agent_name}: {result}"

    def unfollow_agent(self, agent_name):
        """Unfollow an agent"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        if not agent_name:
            return "❌ No agent name provided"
        agent_name = agent_name.strip().lstrip('@')
        result = self._make_request('DELETE', f'/follow/{agent_name}')
        if not result:
            return f"❌ No response when unfollowing @{agent_name}"
        if isinstance(result, dict):
            if result.get('success') or result.get('status') == 'ok' or 'unfollowed' in str(result).lower():
                self._record_activity('unfollow', {'target': agent_name})
                msg = result.get('message', 'Success')
                return f"✅ Unfollowed @{agent_name}: {msg}"
            elif 'error' in result or 'message' in result:
                err = result.get('error') or result.get('message', 'Unknown error')
                return f"❌ Failed to unfollow @{agent_name}: {err}"
        return f"❌ Unexpected response when unfollowing @{agent_name}: {result}"

    def like_post(self, post_id):
        """Like a post"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        if not post_id:
            return "❌ No post ID provided"

        # Check if post_id is JSON-formatted and extract actual ID
        if isinstance(post_id, str) and post_id.strip().startswith('{'):
            try:
                parsed = json.loads(post_id)
                if 'post_id' in parsed:
                    post_id = parsed['post_id']
                    print(f"📝 Extracted post_id from JSON input: {post_id}")
            except json.JSONDecodeError:
                pass

        if isinstance(post_id, str):
            post_id = post_id.strip()

        if not post_id:
            return "❌ Invalid post ID"

        result = self._make_request('POST', f'/posts/{post_id}/like')

        if not result:
            return f"❌ No response when liking post {post_id}"
        if isinstance(result, dict):
            if result.get('success') or result.get('status') == 'ok' or 'liked' in str(result).lower():
                self._record_activity('like', {'post_id': post_id})
                msg = result.get('message', 'Success')
                return f"✅ Liked post {post_id}: {msg}"
            elif 'error' in result or 'message' in result:
                err = result.get('error') or result.get('message', 'Unknown error')
                return f"❌ Failed to like post {post_id}: {err}"
        return f"❌ Unexpected response when liking post {post_id}: {result}"

    # --- Heartbeat ---

    def _heartbeat(self):
        """Moltx heartbeat v0.22.1 protocol — every 4+ hours.
        Follows the 5:1 rule: 5 replies + 10 likes before 1 original post."""
        if not self.initialized:
            print("❌ Moltx not initialized.")
            return

        print("💓 Starting Moltx heartbeat...")

        # Handle notifications: follow-backs for follow notifications
        raw_notifs = self._get_raw_notifications()
        follow_backs = 0
        recent_follows = [n for n in raw_notifs if (n.get('type') or '').lower() == 'follow'][:3]
        my_agent_name = getattr(self, 'agent_name', None)
        for notif in recent_follows:
            actor = (notif.get('actor') or notif.get('from_user') or notif.get('user') or '').strip().lstrip('@')
            if actor and actor != my_agent_name:
                res = self.follow_agent(actor)
                print(f"🔄 Follow-back attempt: {res}")
                if "✅" in res:
                    follow_backs += 1
                time.sleep(random.uniform(2, 5))

        # Feed engagement: random likes
        feed_data = self._get_feed_data('global', 50)
        likes_done = 0
        if isinstance(feed_data, str):
            print(f"❌ Feed fetch failed in heartbeat: {feed_data}")
        else:
            posts = []
            if 'posts' in feed_data:
                posts = feed_data['posts']
            elif 'data' in feed_data and isinstance(feed_data['data'], dict) and 'posts' in feed_data['data']:
                posts = feed_data['data']['posts']
            elif isinstance(feed_data, list):
                posts = feed_data

            if posts:
                random.shuffle(posts)
                for post in posts[:15]:
                    post_id = post.get('id') or post.get('post_id')
                    if post_id and isinstance(post_id, str) and post_id.strip():
                        post_id = post_id.strip()
                        res = self.like_post(post_id)
                        print(f"❤️ Like attempt: {res}")
                        if "✅" in res:
                            likes_done += 1
                        time.sleep(random.uniform(1, 4))

        print(f"✅ Heartbeat complete: {follow_backs} follow-backs, {likes_done} likes")
        self._record_activity('heartbeat', {
            'follow_backs': follow_backs,
            'likes': likes_done,
        })