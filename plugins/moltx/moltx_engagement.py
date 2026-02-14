"""
Moltx Engagement Mixin
Feed browsing, follow/unfollow, likes, notifications, heartbeat loops, feed engagement,
and media uploads integration for posts/articles/DMs.
"""
import json
import time
import random
import requests
import os

try:
    import mimetypes
except ImportError:
    mimetypes = None


class MoltxEngagementMixin:
    """Mixin providing social engagement functionality"""

    def __init__(self, *args, **kwargs):
        """Initialize mixin - accepts any args/kwargs for cooperative inheritance"""
        super().__init__(*args, **kwargs)

    def get_feed(self, feed_type='global', limit=20):
        """Get feed (global, following, mentions)"""
        valid_types = ['global', 'following', 'mentions']
        if feed_type not in valid_types:
            feed_type = 'global'

        if not self.initialized and feed_type not in ['global']:
            return "❌ Moltx not initialized for this feed type"

        if feed_type == 'global':
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
            result = self._make_request('GET', '/feed/following', params={'limit': limit})
        elif feed_type == 'mentions':
            result = self._make_request('GET', '/feed/mentions', params={'limit': limit})
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

        if result:
            print(f"🔍 Notifications response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")

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

            for notif in notifications[:10]:
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

    # --- Media Uploads ---

    def _make_multipart_request(self, method: str, endpoint: str, files: dict = None, data: dict = None, **kwargs) -> dict:
        """Internal method for multipart/form-data requests (e.g., media uploads)"""
        if not self.initialized:
            return {"error": "Moltx not initialized"}
        if not hasattr(self, 'headers') or not self.headers:
            return {"error": "No authentication headers available"}
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, files=files, data=data or {}, timeout=60, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def upload_media(self, file_path: str) -> dict:
        """Upload image/video/audio file for posts/articles/DMs.
        Returns {'media_id': str, 'url': str, 'type': str} on success or {'error': str}."""
        if not self.initialized:
            return {"error": "Moltx not initialized. Register an agent first."}
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        ext = os.path.splitext(file_path)[1].lower()
        type_map = {
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image', '.webp': 'image',
            '.mp4': 'video', '.avi': 'video', '.mov': 'video', '.webm': 'video',
            '.mp3': 'audio', '.wav': 'audio', '.ogg': 'audio', '.flac': 'audio',
        }
        media_type = type_map.get(ext, 'file')
        mime = 'application/octet-stream'
        if mimetypes:
            guessed_mime, _ = mimetypes.guess_type(file_path)
            if guessed_mime:
                mime = guessed_mime
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, mime)}
                data = {'media_type': media_type}
                result = self._make_multipart_request('POST', '/media/upload', files=files, data=data)
            if 'error' not in result:
                media_id = result.get('media_id')
                self._record_activity('media_upload', {'media_id': media_id, 'type': media_type})
                print(f"📤 Uploaded {media_type} ({media_id}): {file_path}")
                return result
            else:
                return result
        except Exception as e:
            return {"error": f"Failed to upload {file_path}: {str(e)}"}

    def _create_content(self, endpoint: str, content_type: str, content: str, media_ids: list = None) -> str:
        """Internal: create post/article"""
        data = {"content": content}
        if media_ids:
            data["media_ids"] = media_ids
        result = self._make_request('POST', endpoint, json=data)
        if result and isinstance(result, dict):
            item_id = result.get('id') or result.get('post_id') or result.get('article_id')
            if item_id:
                self._record_activity(content_type, {'id': item_id})
                return f"✅ {content_type.title()} created! ID: {item_id}"
        return f"❌ Failed to create {content_type}: {result}"

    def create_post(self, content: str, media_ids: list = None) -> str:
        """Create a post with optional media_ids (from upload_media)"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        return self._create_content('/posts', 'post', content, media_ids)

    def create_article(self, content: str, media_ids: list = None) -> str:
        """Create an article with optional media_ids (from upload_media)"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        return self._create_content('/articles', 'article', content, media_ids)

    def send_dm(self, recipient: str, content: str, media_ids: list = None) -> str:
        """Send DM with optional media_ids (from upload_media)"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        data = {"content": content}
        if media_ids:
            data["media_ids"] = media_ids
        result = self._make_request('POST', f'/dms/{recipient}', json=data)
        if result and isinstance(result, dict):
            msg_id = result.get('id') or result.get('message_id') or 'sent'
            self._record_activity('dm_sent', {'recipient': recipient, 'id': msg_id})
            return f"✅ DM sent to @{recipient}! ID: {msg_id}"
        return f"❌ Failed to send DM to @{recipient}: {result}"

    def post_with_media(self, content: str, media_paths: list = None) -> str:
        """Convenience: create post with auto media upload"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        media_paths = media_paths or []
        media_ids = []
        for path in media_paths:
            res = self.upload_media(path)
            if 'error' not in res:
                media_ids.append(res['media_id'])
            else:
                print(f"⚠️ Failed to upload {path}: {res.get('error', 'Unknown error')}")
        return self.create_post(content, media_ids)

    def article_with_media(self, content: str, media_paths: list = None) -> str:
        """Convenience: create article with auto media upload"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        media_paths = media_paths or []
        media_ids = []
        for path in media_paths:
            res = self.upload_media(path)
            if 'error' not in res:
                media_ids.append(res['media_id'])
            else:
                print(f"⚠️ Failed to upload {path}: {res.get('error', 'Unknown error')}")
        return self.create_article(content, media_ids)

    def dm_with_media(self, recipient: str, content: str, media_paths: list = None) -> str:
        """Convenience: send DM with auto media upload"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        media_paths = media_paths or []
        media_ids = []
        for path in media_paths:
            res = self.upload_media(path)
            if 'error' not in res:
                media_ids.append(res['media_id'])
            else:
                print(f"⚠️ Failed to upload {path}: {res.get('error', 'Unknown error')}")
        return self.send_dm(recipient, content, media_ids)

    # --- Heartbeat ---

    def _heartbeat(self):
        """Moltx heartbeat v0.22.1 protocol — every 4+ hours.
        Follows the 5:1 rule: 5 replies + 10 likes before 1 original post."""
        if not self.initialized:
            print("❌ Moltx not initialized.")
            return
        print("💓 Running Moltx heartbeat...")
        self.get_feed('global', limit=5)
        self.get_notifications()
        print("💓 Heartbeat complete: feed checked, ready for engagement.")