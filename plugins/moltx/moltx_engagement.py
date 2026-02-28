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

    def _handle_media_uploads(self, media_paths):
        """Upload media files and return list of media_ids"""
        media_ids = []
        if not media_paths:
            return media_ids
        paths = [media_paths] if isinstance(media_paths, str) else media_paths
        for path in paths:
            mid = self.upload_media(path)
            if isinstance(mid, str) and not mid.startswith('❌'):
                media_ids.append(mid)
        return media_ids

    def upload_media(self, file_path):
        """Upload media and return media_id or error str"""
        if not hasattr(self, 'initialized') or not self.initialized:
            return "❌ Not initialized"
        if mimetypes is None:
            return "❌ mimetypes unavailable"
        if not os.path.exists(file_path):
            return f"❌ File not found: {file_path}"
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or 'application/octet-stream'
        upload_url = f"{self.base_url}/media/upload"
        try:
            headers = {'Accept': 'application/json'}
            # Add Authorization header with API key
            if hasattr(self, 'api_key') and self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, mime_type)}
                response = requests.post(upload_url, files=files, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                # Return CDN URL from response (data.url per skill.md)
                if data.get('success') and data.get('data'):
                    return data.get('data', {}).get('url') or data.get('data', {}).get('media_url')
                return "❌ No media URL returned"
        except Exception as e:
            return f"❌ Upload failed: {str(e)[:100]}"

    def get_feed(self, feed_type='global', limit=20):
        """Get feed (global, following, mentions)"""
        valid_types = ['global', 'following', 'mentions']
        if feed_type not in valid_types:
            feed_type = 'global'

        if not self.initialized and feed_type not in ['global']:
            return "❌ Moltx not initialized for this feed type"

        if feed_type == 'global':
            result = self._make_request('GET', '/feed/global', params={'type': 'post,quote', 'limit': limit})
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
            except json.JSONDecodeError:
                pass

        if isinstance(post_id, str):
            post_id = post_id.strip()

        result = self._make_request('POST', f'/posts/{post_id}/like')
        
        # Debug logging
        print(f"🔍 like_post result for {post_id}: {result}")

        # Check for actual success - result should be dict with success=True
        if result and isinstance(result, dict):
            if result.get('success'):
                self._record_activity('like', {'post_id': post_id})
                return f"✅ Liked post {post_id}"
            else:
                error = result.get('error', result.get('message', 'Unknown error'))
                return f"❌ Failed to like post {post_id}: {error}"
        elif result:
            # Unexpected response type
            return f"⚠️ Unexpected response liking post {post_id}: {str(result)[:100]}"
        else:
            return f"❌ Failed to like post {post_id}: No response from API"

    def unlike_post(self, post_id):
        """Unlike a post (remove like)"""
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
            except json.JSONDecodeError:
                pass

        if isinstance(post_id, str):
            post_id = post_id.strip()

        result = self._make_request('DELETE', f'/posts/{post_id}/like')

        if result:
            self._record_activity('unlike', {'post_id': post_id})
            return f"✅ Unliked post {post_id}"
        else:
            return f"❌ Failed to unlike post {post_id}"

    def archive_post(self, post_id):
        """Archive/hide a post"""
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
            except json.JSONDecodeError:
                pass

        if isinstance(post_id, str):
            post_id = post_id.strip()

        result = self._make_request('POST', f'/posts/{post_id}/archive')

        if result:
            self._record_activity('archive', {'post_id': post_id})
            return f"✅ Archived post {post_id}"
        else:
            return f"❌ Failed to archive post {post_id}"

    def reply_to_post(self, post_id, content):
        """Reply to a post"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        if not post_id:
            return "❌ No post ID provided"

        if not content:
            return "❌ No reply content provided"

        # Check if post_id is JSON-formatted and extract actual ID
        if isinstance(post_id, str) and post_id.strip().startswith('{'):
            try:
                parsed = json.loads(post_id)
                if 'post_id' in parsed:
                    post_id = parsed['post_id']
                elif 'id' in parsed:
                    post_id = parsed['id']
            except json.JSONDecodeError:
                pass

        if isinstance(post_id, str):
            post_id = post_id.strip()

        data = {
            'type': 'reply',
            'parent_id': post_id,
            'content': content
        }

        result = self._make_request('POST', '/posts', data=data)

        if result and 'post_id' in result:
            reply_id = result['post_id']
            self._record_activity('reply', {'post_id': post_id, 'reply_id': reply_id})
            return f"✅ Replied to post {post_id}! Reply ID: {reply_id}"
        return f"❌ Failed to reply to post {post_id}"

    def quote_post(self, post_id, content):
        """Quote/repost with comment"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        if not post_id:
            return "❌ No post ID provided"

        if not content:
            return "❌ No quote content provided"

        # Check if post_id is JSON-formatted and extract actual ID
        if isinstance(post_id, str) and post_id.strip().startswith('{'):
            try:
                parsed = json.loads(post_id)
                if 'post_id' in parsed:
                    post_id = parsed['post_id']
                elif 'id' in parsed:
                    post_id = parsed['id']
            except json.JSONDecodeError:
                pass

        if isinstance(post_id, str):
            post_id = post_id.strip()

        data = {
            'type': 'quote',
            'parent_id': post_id,
            'content': content
        }

        result = self._make_request('POST', '/posts', data=data)

        if result and 'post_id' in result:
            quote_id = result['post_id']
            self._record_activity('quote', {'post_id': post_id, 'quote_id': quote_id})
            return f"✅ Quoted post {post_id}! Quote ID: {quote_id}"
        return f"❌ Failed to quote post {post_id}"

    def get_notifications_unread_count(self):
        """Get unread notification count"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        result = self._make_request('GET', '/notifications/unread_count')

        if result:
            count = result.get('count', result.get('unread_count', 0))
            return f"🔔 {count} unread notifications"
        return "❌ Failed to get unread count"

    def mark_notifications_read(self, notification_ids=None, mark_all=False):
        """Mark notifications as read"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        if mark_all:
            data = {'all': True}
        elif notification_ids:
            if isinstance(notification_ids, str):
                notification_ids = [n.strip() for n in notification_ids.split(',')]
            data = {'ids': notification_ids}
        else:
            return "❌ Provide notification_ids or set mark_all=True"

        result = self._make_request('POST', '/notifications/read', data=data)

        if result:
            return "✅ Notifications marked as read"
        return "❌ Failed to mark notifications as read"

    def get_system_stats(self):
        """Get Moltx system stats"""
        result = self._make_request('GET', '/stats')

        if result:
            output = "📊 Moltx System Stats:\n\n"
            for key, value in result.items():
                if isinstance(value, dict):
                    output += f"{key}:\n"
                    for k, v in value.items():
                        output += f"  {k}: {v}\n"
                else:
                    output += f"{key}: {value}\n"
            return output
        return "❌ Failed to get system stats"

    def get_agent_activity(self, agent_name=None, metric='posts', granularity='daily', range_days='7d'):
        """Get agent activity graph"""
        if not agent_name:
            agent_name = self.agent_name

        if not agent_name:
            return "❌ No agent name provided"

        params = {
            'metric': metric,
            'granularity': granularity,
            'range': range_days
        }

        result = self._make_request('GET', f'/agent/{agent_name}/activity', params=params)

        if result:
            output = f"📈 Activity for @{agent_name}:\n\n"
            data_points = result.get('data', result.get('activity', []))
            if data_points:
                for point in data_points[:10]:
                    ts = point.get('timestamp', 'Unknown')
                    val = point.get('value', point.get('count', 0))
                    output += f"  {ts}: {val}\n"
            return output
        return f"❌ Failed to get activity for {agent_name}"

    def get_notifications(self, limit=20):
        """Get notifications"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        result = self._make_request('GET', '/notifications', params={'limit': limit})

        notifs = []
        if result:
            if 'notifications' in result:
                notifs = result['notifications']
            elif 'data' in result and 'notifications' in result['data']:
                notifs = result['data']['notifications']
            elif isinstance(result, list):
                notifs = result

        if notifs:
            output = f"🔔 Notifications ({len(notifs)}):\n\n"
            for notif in notifs[:limit]:
                if isinstance(notif, dict):
                    agent_name = notif.get('agent_name') or notif.get('author_name') or notif.get('username') or 'Unknown'
                    content = notif.get('content') or notif.get('text') or notif.get('body') or 'No content'
                    notif_type = notif.get('type') or 'general'
                    timestamp = notif.get('created_at') or notif.get('timestamp') or 'Unknown time'
                    notif_id = notif.get('id') or notif.get('notification_id') or 'unknown'
                    output += f"🔔 @{agent_name} ({notif_type}): {content[:100]}{'...' if len(content) > 100 else ''}\n"
                    output += f"   🕐 {timestamp}\n"
                    output += f"   🆔 ID: {notif_id}\n\n"
                else:
                    output += f"🔔 {str(notif)[:100]}{'...' if len(str(notif)) > 100 else ''}\n\n"
            return output
        else:
            return "✅ No new notifications"

    def post_text(self, text, media_paths=None, hashtags=None):
        """Post text post with optional media and hashtags"""
        if not self.initialized:
            return "❌ Moltx not initialized"
        
        # 5:1 Engagement Rule - Must engage 5x before posting 1x
        if not self._check_engagement_quota():
            print("🔄 5:1 Rule: Engaging with feed before posting...")
            engagement_result = self._auto_engage_for_posting()
            if not engagement_result or "❌" in engagement_result:
                return f"❌ 5:1 Engagement rule: Failed to meet engagement quota. Please try again. ({engagement_result})"
            print(f"✅ Pre-post engagement complete: {engagement_result}")
        
        data = {'content': text}
        if hashtags:
            htags = [h.strip().strip('#') for h in (hashtags.split(',') if isinstance(hashtags, str) else hashtags) if h.strip()]
            data['hashtags'] = htags[:5]
        media_ids = self._handle_media_uploads(media_paths)
        if media_ids:
            data['media_ids'] = media_ids
        result = self._make_request('POST', '/posts', json=data)
        if result and 'post_id' in result:
            post_id = result['post_id']
            self._record_post_made()  # Record for 5:1 tracking
            self._record_activity('post_text', {'post_id': post_id, 'media_count': len(media_ids)})
            return f"✅ Text post created! ID: {post_id}"
        return "❌ Failed to post text"

    def post_article(self, title, body, media_paths=None):
        """Post article with optional media"""
        if not self.initialized:
            return "❌ Moltx not initialized"
        data = {'title': title, 'body': body}
        media_ids = self._handle_media_uploads(media_paths)
        if media_ids:
            data['media_ids'] = media_ids
        result = self._make_request('POST', '/articles', json=data)
        if result and 'article_id' in result:
            article_id = result['article_id']
            self._record_activity('post_article', {'article_id': article_id})
            return f"✅ Article posted! ID: {article_id}"
        return "❌ Failed to post article"

    def send_dm(self, agent_name, message, media_paths=None):
        """Send DM with optional media"""
        if not self.initialized:
            return "❌ Moltx not initialized"
        data = {'recipient': agent_name, 'content': message}
        media_ids = self._handle_media_uploads(media_paths)
        if media_ids:
            data['media_ids'] = media_ids
        result = self._make_request('POST', '/dms', json=data)
        if result:
            self._record_activity('send_dm', {'to': agent_name, 'preview': message[:30]})
            return f"✅ DM sent to @{agent_name}"
        return f"❌ Failed to send DM to @{agent_name}"

    def get_dms(self, limit=20):
        """Get recent DM conversations"""
        if not self.initialized:
            return "❌ Moltx not initialized"
        result = self._make_request('GET', '/dms', params={'limit': limit})
        dms = []
        if result:
            if 'dms' in result or 'messages' in result:
                dms = result.get('dms') or result.get('messages', [])
            elif 'conversations' in result:
                dms = result['conversations']
            elif isinstance(result, list):
                dms = result
        if dms:
            output = f"💬 Recent DMs ({len(dms)}):\n\n"
            for dm in dms[:limit]:
                agent_name = dm.get('agent_name') or dm.get('sender_name') or dm.get('recipient') or 'Unknown'
                content = dm.get('content') or dm.get('message') or dm.get('last_message', 'No message')
                timestamp = dm.get('updated_at') or dm.get('timestamp') or 'Unknown'
                output += f"💬 @{agent_name}: {content[:100]}{'...' if len(content) > 100 else ''}\n"
                output += f"   🕐 {timestamp}\n\n"
            return output
        return "✅ No DMs"

    def search(self, query, search_type='posts'):
        """Search for posts, agents, or hashtags"""
        valid_types = ['posts', 'agents', 'hashtags']
        if search_type not in valid_types:
            search_type = 'posts'
        params = {'q': query, 'type': search_type}
        result = self._make_request('GET', '/search', params=params)
        items = []
        if result:
            key = f"{search_type}s"
            items = result.get(key) or result.get('results', []) or (result['data'][key] if 'data' in result else [])
            if isinstance(result, list):
                items = result
        output = f"🔍 '{query}' ({search_type}): {len(items)} results\n\n"
        for item in items[:10]:
            if isinstance(item, dict):
                name = item.get('agent_name') or item.get('title') or item.get('name') or item.get('tag') or 'Unknown'
                desc = (item.get('content') or item.get('description') or item.get('text') or '')[:80]
                output += f"📌 {name}: {desc}{'...' if len(desc) > 80 else ''}\n"
        return output if items else f"❌ No {search_type} found for '{query}'"

    def get_trending_hashtags(self, limit=20):
        """Get trending hashtags"""
        result = self._make_request('GET', '/hashtags/trending', params={'limit': limit})
        hashtags = result.get('hashtags', []) if result else []
        output = f"🔥 Trending Hashtags ({len(hashtags)}):\n\n"
        for tag in hashtags[:limit]:
            name = tag.get('name', 'unknown')
            count = tag.get('post_count', 0)
            output += f"#{name} ({count} posts)\n"
        return output

    def get_leaderboard(self, category='daily', limit=10):
        """Get leaderboard"""
        params = {'category': category, 'limit': limit}
        result = self._make_request('GET', '/leaderboard', params=params)
        leaders = result.get('leaders', result.get('leaderboard', [])) if result else []
        output = f"🏆 {category.title()} Leaderboard:\n\n"
        for i, leader in enumerate(leaders[:limit], 1):
            name = leader.get('agent_name', 'Unknown')
            score = leader.get('score', leader.get('points', 0))
            output += f"{i}. @{name}: {score} pts\n"
        return output

    def get_communities(self, limit=20):
        """Get communities"""
        result = self._make_request('GET', '/communities', params={'limit': limit})
        communities = result.get('communities', []) if result else []
        output = f"🏘️ Communities ({len(communities)}):\n\n"
        for comm in communities[:limit]:
            name = comm.get('name', 'Unknown')
            member_count = comm.get('member_count', 0)
            desc = (comm.get('description') or '')[:60]
            output += f"🏘️ {name} ({member_count} members): {desc}{'...' if len(desc) > 60 else ''}\n"
        return output

    def join_community(self, community_id):
        """Join a community"""
        if not self.initialized:
            return "❌ Not initialized"
        result = self._make_request('POST', f'/communities/{community_id}/join')
        return f"✅ Joined {community_id}" if result else f"❌ Failed to join {community_id}"

    def get_articles(self, limit=20):
        """Get articles feed"""
        result = self._make_request('GET', '/articles', params={'limit': limit})
        articles = []
        if result:
            if 'articles' in result:
                articles = result['articles']
            elif 'data' in result and 'articles' in result['data']:
                articles = result['data']['articles']
            elif isinstance(result, list):
                articles = result
        if articles:
            output = f"📚 Articles ({len(articles)}):\n\n"
            for article in articles[:limit]:
                title = (article.get('title') or article.get('content') or 'No title')[:100]
                author = article.get('agent_name', 'Unknown')
                views = article.get('views_count', article.get('views', 0))
                timestamp = article.get('created_at', 'Unknown')
                output += f"📚 {title}{'...' if len(title) > 100 else ''}\n"
                output += f"   by @{author} | 👀 {views} views | 🕐 {timestamp}\n\n"
            return output
        return "📚 No articles found"

    def claim_agent(self, tweet_url):
        """Claim agent for verified status"""
        data = {'tweet_url': tweet_url.strip()}
        result = self._make_request('POST', '/agents/claim', json=data)
        if result and result.get('success', result.get('claimed')):
            self.initialized = True
            return f"✅ Claimed agent with {tweet_url}"
        return f"❌ Claim failed for {tweet_url}"

    def claim_rewards(self):
        """Claim pending rewards"""
        if not self.initialized:
            return "❌ Not initialized"
        result = self._make_request('POST', '/rewards/claim')
        if result:
            amount = result.get('amount', result.get('rewards_claimed', 0))
            return f"✅ Claimed {amount} rewards"
        return "❌ No rewards or claim failed"

    def recover_key(self, recovery_phrase):
        """Recover agent key"""
        if self.initialized:
            return "ℹ️ Already initialized"
        data = {'recovery_phrase': recovery_phrase}
        result = self._make_request('POST', '/agents/key-recovery', json=data)
        if result and result.get('success'):
            self.initialized = True
            return "✅ Key recovered"
        return "❌ Key recovery failed"

    def heartbeat(self):
        """Heartbeat protocol: check claim status via GET /agents/status"""
        result = self._make_request('GET', '/agents/status')
        if result and result.get('success'):
            agent_data = result.get('data', {}).get('agent', {})
            if agent_data.get('claim_status'):
                self.claim_status = agent_data['claim_status']
            return "✅ Heartbeat status check successful"
        return "❌ Heartbeat status check failed"

    def repost_post(self, post_id):
        """Repost (simple repost without comment)"""
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
                elif 'id' in parsed:
                    post_id = parsed['id']
            except json.JSONDecodeError:
                pass

        if isinstance(post_id, str):
            post_id = post_id.strip()

        data = {
            'type': 'repost',
            'parent_id': post_id
        }

        result = self._make_request('POST', '/posts', json=data)

        if result and 'post_id' in result:
            repost_id = result['post_id']
            self._record_activity('repost', {'post_id': post_id, 'repost_id': repost_id})
            return f"✅ Reposted post {post_id}! Repost ID: {repost_id}"
        return f"❌ Failed to repost post {post_id}"

    def fetch_post(self, post_id):
        """Fetch a single post by ID (returns dict or None)"""
        if not post_id:
            return None

        # Check if post_id is JSON-formatted and extract actual ID
        if isinstance(post_id, str) and post_id.strip().startswith('{'):
            try:
                parsed = json.loads(post_id)
                if 'post_id' in parsed:
                    post_id = parsed['post_id']
                elif 'id' in parsed:
                    post_id = parsed['id']
            except json.JSONDecodeError:
                pass

        if isinstance(post_id, str):
            post_id = post_id.strip()

        result = self._make_request('GET', f'/posts/{post_id}')
        
        if result:
            # Return the post object directly
            if 'post' in result:
                return result['post']
            elif 'data' in result and isinstance(result['data'], dict):
                return result['data'].get('post', result['data'])
            elif isinstance(result, dict) and 'content' in result:
                return result
        return None

    def get_post(self, post_id):
        """Get a single post by ID with its replies"""
        if not post_id:
            return "❌ No post ID provided"

        # Check if post_id is JSON-formatted and extract actual ID
        if isinstance(post_id, str) and post_id.strip().startswith('{'):
            try:
                parsed = json.loads(post_id)
                if 'post_id' in parsed:
                    post_id = parsed['post_id']
                elif 'id' in parsed:
                    post_id = parsed['id']
            except json.JSONDecodeError:
                pass

        if isinstance(post_id, str):
            post_id = post_id.strip()

        result = self._make_request('GET', f'/posts/{post_id}')

        if result:
            output = "🐦 Post:\n\n"
            post = result.get('post', result.get('data', {}))
            if isinstance(post, dict):
                agent_name = post.get('agent_name') or post.get('author_name') or post.get('username') or 'Unknown'
                content = post.get('content') or post.get('text') or post.get('body') or 'No content'
                replies_count = post.get('replies_count') or post.get('reply_count') or 0
                likes_count = post.get('likes_count') or post.get('like_count') or 0
                timestamp = post.get('created_at') or post.get('timestamp') or 'Unknown time'
                post_type = post.get('type', 'post')

                output += f"🐦 @{agent_name} ({post_type}): {content}\n"
                output += f"   💬 {replies_count} replies | ❤️ {likes_count} likes\n"
                output += f"   🕐 {timestamp}\n"

                # Show replies if any
                replies = result.get('replies', result.get('data', {}).get('replies', []))
                if replies:
                    output += f"\n💬 Replies ({len(replies)}):\n"
                    for reply in replies[:5]:
                        if isinstance(reply, dict):
                            reply_author = reply.get('agent_name') or reply.get('author_name') or 'Unknown'
                            reply_content = reply.get('content') or reply.get('text', 'No content')
                            output += f"   ↳ @{reply_author}: {reply_content[:80]}{'...' if len(reply_content) > 80 else ''}\n"
            return output
        return f"❌ Failed to get post {post_id}"

    def list_posts(self, sort='new', limit=20, offset=0):
        """List posts with sort options (new, top)"""
        params = {'sort': sort, 'limit': limit, 'offset': offset}
        result = self._make_request('GET', '/posts', params=params)

        if result:
            posts = result.get('posts', result.get('data', {}).get('posts', []))
            if posts:
                output = f"🐦 Posts (sorted by {sort}, {len(posts)} total):\n\n"
                for post in posts[:limit]:
                    if isinstance(post, dict):
                        agent_name = post.get('agent_name') or post.get('author_name') or post.get('username') or 'Unknown'
                        content = post.get('content') or post.get('text') or post.get('body') or 'No content'
                        replies = post.get('replies_count') or post.get('reply_count') or 0
                        likes = post.get('likes_count') or post.get('like_count') or 0
                        post_id = post.get('id') or post.get('post_id') or 'unknown'
                        output += f"🐦 @{agent_name}: {content[:100]}{'...' if len(content) > 100 else ''}\n"
                        output += f"   💬 {replies} replies | ❤️ {likes} likes | 🆔 {post_id}\n\n"
                return output
            return "🐦 No posts found"
        return "❌ Failed to list posts"

    def search_posts_by_hashtag(self, hashtag, limit=20):
        """Search posts by hashtag"""
        # Remove # if provided
        tag = hashtag.lstrip('#')
        params = {'hashtag': tag, 'limit': limit}
        result = self._make_request('GET', '/search/posts', params=params)

        if result:
            posts = result.get('posts', result.get('data', {}).get('posts', []))
            if posts:
                output = f"🔍 Posts with #{tag} ({len(posts)} results):\n\n"
                for post in posts[:limit]:
                    if isinstance(post, dict):
                        agent_name = post.get('agent_name') or post.get('author_name') or post.get('username') or 'Unknown'
                        content = post.get('content') or post.get('text') or post.get('body') or 'No content'
                        output += f"🐦 @{agent_name}: {content[:100]}{'...' if len(content) > 100 else ''}\n"
                return output
            return f"🔍 No posts found for #{tag}"
        return f"❌ Failed to search posts by hashtag #{tag}"

    def get_article(self, article_id):
        """Get a single article by ID with its replies"""
        if not article_id:
            return "❌ No article ID provided"

        result = self._make_request('GET', f'/articles/{article_id}')

        if result:
            output = "📚 Article:\n\n"
            article = result.get('article', result.get('data', {}))
            if isinstance(article, dict):
                title = article.get('title', 'No title')
                content = article.get('content', 'No content')
                author = article.get('agent_name') or article.get('author_name') or article.get('author', 'Unknown')
                views = article.get('views_count') or article.get('views', 0)
                likes = article.get('likes_count') or article.get('like_count', 0)
                read_time = article.get('read_time', 0)
                word_count = article.get('word_count', 0)

                output += f"📚 {title}\n"
                output += f"   by @{author} | 👀 {views} views | ❤️ {likes} likes\n"
                output += f"   ⏱️ {read_time} min read | 📝 {word_count} words\n\n"
                output += f"{content[:500]}{'...' if len(content) > 500 else ''}\n"

                # Show replies if any
                replies = result.get('replies', result.get('data', {}).get('replies', []))
                if replies:
                    output += f"\n💬 Replies ({len(replies)}):\n"
                    for reply in replies[:5]:
                        if isinstance(reply, dict):
                            reply_author = reply.get('agent_name') or reply.get('author_name') or 'Unknown'
                            reply_content = reply.get('content') or reply.get('text', 'No content')
                            output += f"   ↳ @{reply_author}: {reply_content[:80]}{'...' if len(reply_content) > 80 else ''}\n"
            return output
        return f"❌ Failed to get article {article_id}"

    def _record_to_world_state(self, post: dict, interaction_type: str = "observed"):
        """Record a post and its author to World State"""
        try:
            # Get World State from core
            if not hasattr(self, 'core') or not self.core:
                return
            brain = self.core.plugin_manager.plugins.get('brain')
            if not brain or not hasattr(brain, 'world_state'):
                return
            
            ws = brain.world_state
            if not ws:
                return
            
            # Extract post data
            post_id = post.get('id') or post.get('post_id')
            author = post.get('agent_name') or post.get('author_name') or post.get('username', 'unknown')
            content = post.get('content') or post.get('text') or ''
            timestamp = post.get('created_at') or datetime.now().isoformat()
            likes = post.get('likes_count') or post.get('like_count', 0)
            replies = post.get('replies_count') or post.get('reply_count', 0)
            
            if not post_id:
                return
            
            # Create author entity
            author_id = f"moltx_{author.lstrip('@')}"
            from src.autonomy.world_state import Entity, Fact, Event
            
            author_entity = Entity(
                id=author_id,
                type='agent',
                name=author.lstrip('@'),
                display_name=author,
                attributes={'platform': 'moltx'}
            )
            ws.add_entity(author_entity)
            
            # Create post entity
            post_entity = Entity(
                id=f"moltx_post_{post_id}",
                type='post',
                name=f"Post {post_id[:8]}",
                attributes={
                    'platform': 'moltx',
                    'content_preview': content[:100] if content else '',
                    'author_id': author_id
                }
            )
            ws.add_entity(post_entity)
            
            # Record facts about the post
            ws.add_fact(Fact(
                entity_id=f"moltx_post_{post_id}",
                attribute='likes_count',
                value=str(likes),
                value_type='int',
                source='moltx_api',
                timestamp=timestamp
            ))
            
            ws.add_fact(Fact(
                entity_id=f"moltx_post_{post_id}",
                attribute='replies_count',
                value=str(replies),
                value_type='int',
                source='moltx_api',
                timestamp=timestamp
            ))
            
            # Record event
            ws.add_event(Event(
                event_type=f'post_{interaction_type}',
                actor_id=author_id,
                target_id=f"moltx_post_{post_id}",
                platform='moltx',
                data={'post_id': post_id, 'content_preview': content[:50] if content else ''},
                timestamp=timestamp
            ))
            
            # Record relationship if we interacted
            if interaction_type in ('liked', 'replied', 'engaged'):
                from src.autonomy.world_state import Relationship
                ws.add_relationship(Relationship(
                    from_entity=f"agent_{self.agent_name.lstrip('@') if hasattr(self, 'agent_name') else 'alleybot'}",
                    to_entity=author_id,
                    relation_type='engaged_with',
                    strength=0.6,
                    context={'interaction': interaction_type, 'post_id': post_id}
                ))
                
        except Exception as e:
            # Silent fail - don't break main functionality
            print(f"⚠️ World State recording failed: {e}")
    
    def first_boot(self):
        """Perform first boot"""
        if hasattr(self, '_booted') and self._booted:
            return "ℹ️ Already booted"
        result = self._make_request('POST', '/first-boot')
        if result:
            self._booted = True
            return "✅ First boot complete"
        return "❌ First boot failed"