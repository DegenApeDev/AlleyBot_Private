"""MoltBook Plugin - Reddit for AI Agents

MoltBook integration with posts, comments, voting, and submolts.
Uses MOLTBOOK_API_KEY from .env for authentication.

API: https://www.moltbook.com/api/v1
"""

import requests
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from plugin_manager import AlleyBotPlugin


class MoltBookPlugin(AlleyBotPlugin):
    """Plugin for MoltBook - Reddit-style platform for AI Agents"""

    def __init__(self, config):
        super().__init__(config)
        self.api_key = None
        self.base_url = "https://www.moltbook.com/api/v1"
        self.agent_id = None
        self.agent_name = None
        self.initialized = False

    def initialize(self, api, core):
        """Initialize MoltBook plugin with API key from .env"""
        super().initialize(api, core)

        # Load API key from config
        from config import MOLTBOOK_API_KEY
        self.api_key = MOLTBOOK_API_KEY

        if not self.api_key:
            print("⚠️  MoltBook API key not found in .env (MOLTBOOK_API_KEY)")
            return

        print(f"🔑 MoltBook API key loaded: {self.api_key[:20]}...")

        # Check claim status
        status = self._check_status()
        if status.get('status') == 'claimed':
            self.initialized = True
            print("✅ MoltBook initialized - agent claimed")

            # Get agent profile
            profile = self._get_profile()
            if profile:
                self.agent_id = profile.get('id')
                self.agent_name = profile.get('name', 'unknown')
                print(f"🤖 MoltBook agent: @{self.agent_name}")
        else:
            print(f"⚠️  MoltBook agent status: {status.get('status', 'unknown')}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to MoltBook API"""
        if not self.api_key:
            return {'success': False, 'error': 'No API key configured'}

        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.request(
                method, url, headers=headers, timeout=30, **kwargs
            )
            response.raise_for_status()

            # Some endpoints return empty body on success
            if response.text:
                return response.json()
            return {'success': True}

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                return {'success': False, 'error': 'Rate limited - try again later'}
            try:
                return {'success': False, 'error': e.response.json()}
            except:
                return {'success': False, 'error': f'HTTP {e.response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _check_status(self) -> Dict[str, Any]:
        """Check agent claim status"""
        return self._make_request('GET', '/agents/status')

    def _get_profile(self) -> Optional[Dict[str, Any]]:
        """Get agent profile"""
        result = self._make_request('GET', '/agents/me')
        if result and 'error' not in result:
            return result
        return None

    # === Posts ===

    def create_post(
        self,
        title: str,
        content: str = "",
        submolt_name: str = "general",
        post_type: str = "text",
        url: str = None
    ) -> Dict[str, Any]:
        """Create a post on MoltBook"""
        if not self.initialized:
            return {'success': False, 'error': 'MoltBook not initialized'}

        payload = {
            "submolt_name": submolt_name,
            "title": title,
            "content": content,
            "type": post_type
        }
        if url:
            payload["url"] = url
            payload["type"] = "link"

        result = self._make_request('POST', '/posts', json=payload)

        # Handle verification challenge if present
        if result.get('verification'):
            print(f"🔐 MoltBook verification required: {result['verification']}")
            # For now, return the challenge - can implement solver later
            return {
                'success': False,
                'error': 'Verification challenge required',
                'verification': result['verification']
            }

        if result.get('id') or result.get('post_id'):
            post_id = result.get('id') or result.get('post_id')
            self._record_activity('create_post', {'post_id': post_id, 'title': title})
            return {
                'success': True,
                'post_id': post_id,
                'title': title,
                'url': f"https://www.moltbook.com/p/{post_id}"
            }

        return result

    def get_feed(self, sort: str = "hot", limit: int = 25, cursor: str = None) -> Dict[str, Any]:
        """Get MoltBook feed"""
        if not self.initialized:
            return {'success': False, 'error': 'MoltBook not initialized'}

        params = {"sort": sort, "limit": limit}
        if cursor:
            params["cursor"] = cursor

        return self._make_request('GET', '/posts', params=params)

    def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get a single post"""
        return self._make_request('GET', f'/posts/{post_id}')

    def delete_post(self, post_id: str) -> Dict[str, Any]:
        """Delete a post"""
        return self._make_request('DELETE', f'/posts/{post_id}')

    # === Comments ===

    def add_comment(self, post_id: str, content: str) -> Dict[str, Any]:
        """Add a comment to a post"""
        if not self.initialized:
            return {'success': False, 'error': 'MoltBook not initialized'}

        result = self._make_request(
            'POST', f'/posts/{post_id}/comments',
            json={"content": content}
        )

        if result.get('id') or result.get('comment_id'):
            comment_id = result.get('id') or result.get('comment_id')
            self._record_activity('add_comment', {'post_id': post_id, 'comment_id': comment_id})
            return {
                'success': True,
                'comment_id': comment_id,
                'post_id': post_id
            }

        return result

    def reply_to_comment(self, comment_id: str, content: str) -> Dict[str, Any]:
        """Reply to a comment"""
        if not self.initialized:
            return {'success': False, 'error': 'MoltBook not initialized'}

        return self._make_request(
            'POST', f'/comments/{comment_id}/reply',
            json={"content": content}
        )

    def get_comments(self, post_id: str) -> Dict[str, Any]:
        """Get comments on a post"""
        return self._make_request('GET', f'/posts/{post_id}/comments')

    # === Voting ===

    def upvote_post(self, post_id: str) -> Dict[str, Any]:
        """Upvote a post"""
        if not self.initialized:
            return {'success': False, 'error': 'MoltBook not initialized'}

        result = self._make_request('POST', f'/posts/{post_id}/upvote')
        if result.get('success') or 'error' not in result:
            self._record_activity('upvote_post', {'post_id': post_id})
            return {'success': True, 'post_id': post_id}
        return result

    def downvote_post(self, post_id: str) -> Dict[str, Any]:
        """Downvote a post"""
        return self._make_request('POST', f'/posts/{post_id}/downvote')

    def upvote_comment(self, comment_id: str) -> Dict[str, Any]:
        """Upvote a comment"""
        return self._make_request('POST', f'/comments/{comment_id}/upvote')

    # === Following ===

    def follow_agent(self, agent_name: str) -> Dict[str, Any]:
        """Follow another agent"""
        if not self.initialized:
            return {'success': False, 'error': 'MoltBook not initialized'}

        result = self._make_request('POST', f'/agents/{agent_name}/follow')
        if result.get('success') or 'error' not in result:
            self._record_activity('follow_agent', {'agent_name': agent_name})
            return {'success': True, 'agent_name': agent_name}
        return result

    def unfollow_agent(self, agent_name: str) -> Dict[str, Any]:
        """Unfollow an agent"""
        return self._make_request('POST', f'/agents/{agent_name}/unfollow')

    def get_following_feed(self, limit: int = 25) -> Dict[str, Any]:
        """Get personalized following feed"""
        return self._make_request('GET', f'/feed/following?limit={limit}')

    # === Submolts ===

    def list_submolts(self) -> Dict[str, Any]:
        """List all submolts"""
        return self._make_request('GET', '/submolts')

    def get_submolt_feed(self, submolt_name: str, sort: str = "hot", limit: int = 25) -> Dict[str, Any]:
        """Get posts from a specific submolt"""
        return self._make_request(
            'GET', f'/submolts/{submolt_name}/feed?sort={sort}&limit={limit}'
        )

    def subscribe_submolt(self, submolt_name: str) -> Dict[str, Any]:
        """Subscribe to a submolt"""
        return self._make_request('POST', f'/submolts/{submolt_name}/subscribe')

    # === Semantic Search ===

    def search(self, query: str, limit: int = 20, type_filter: str = None) -> Dict[str, Any]:
        """AI-powered semantic search"""
        params = {"q": query, "limit": limit}
        if type_filter:
            params["type"] = type_filter  # 'post' or 'comment'
        return self._make_request('GET', '/search', params=params)

    # === Activity Tracking ===

    def _record_activity(self, activity_type: str, data: dict):
        """Record activity to memory"""
        if not hasattr(self, 'core') or not self.core:
            return
        try:
            activities = self.core.get_memory('moltbook_activities') or []
            activities.append({
                'type': activity_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            })
            self.core.save_memory('moltbook_activities', activities[-100:])
        except Exception as e:
            print(f"⚠️  Could not record MoltBook activity: {e}")

    def get_commands(self):
        """Register Telegram commands"""
        return {
            'moltbook_status': self.status_command,
            'moltbook_post': self.post_command,
            'moltbook_feed': self.feed_command,
            'moltbook_comment': self.comment_command,
            'moltbook_search': self.search_command,
            'moltbook_submolts': self.submolts_command,
            'moltbook_follow': self.follow_command,
        }

    def get_tasks(self):
        return {}

    # === Command Handlers ===

    def status_command(self):
        """Get MoltBook status"""
        if not self.initialized:
            return "❌ MoltBook not initialized. Check API key."

        profile = self._get_profile()
        if not profile:
            return "❌ Could not fetch profile"

        output = f"📚 MoltBook Status for @{profile.get('name', 'unknown')}\n\n"
        output += f"🆔 Agent ID: {profile.get('id', 'N/A')[:16]}...\n"
        output += f"📊 Karma: {profile.get('karma', 0)}\n"
        output += f"📧 Email: {profile.get('owner_email', 'Not set')}\n"
        output += f"🤖 AI Verified: {'✅ Yes' if profile.get('ai_verified') else '❌ No'}\n"

        # Get activity stats
        activities = self.core.get_memory('moltbook_activities') or []
        posts = len([a for a in activities if a['type'] == 'create_post'])
        comments = len([a for a in activities if a['type'] == 'add_comment'])
        upvotes = len([a for a in activities if a['type'] == 'upvote_post'])

        output += f"\n📈 Activity:\n"
        output += f"  📝 Posts: {posts}\n"
        output += f"  💬 Comments: {comments}\n"
        output += f"  ⬆️ Upvotes: {upvotes}\n"

        return output

    def post_command(self, *args):
        """Create a post: /moltbook_post <submolt> | <title> | <content>"""
        if not self.initialized:
            return "❌ MoltBook not initialized"

        if not args:
            return "❌ Usage: /moltbook_post <submolt> | <title> | <content>"

        text = ' '.join(args)
        parts = [p.strip() for p in text.split('|')]

        if len(parts) < 2:
            return "❌ Usage: /moltbook_post <submolt> | <title> | <content>\nExample: /moltbook_post general | Hello World | My first post!"

        submolt = parts[0] if parts[0] else "general"
        title = parts[1]
        content = parts[2] if len(parts) > 2 else ""

        if len(title) > 300:
            return "❌ Title too long (max 300 chars)"

        result = self.create_post(title=title, content=content, submolt_name=submolt)

        if result.get('success'):
            return f"✅ Posted to #{submolt}: {title}\n🔗 {result.get('url', '')}"
        else:
            error = result.get('error', 'Unknown error')
            if isinstance(error, dict):
                error = error.get('message', str(error))
            return f"❌ Post failed: {error}"

    def feed_command(self, *args):
        """Get MoltBook feed: /moltbook_feed [sort] [limit]"""
        if not self.initialized:
            return "❌ MoltBook not initialized"

        sort = args[0] if args and args[0] in ['hot', 'new', 'top', 'rising'] else 'hot'
        limit = int(args[1]) if len(args) > 1 and str(args[1]).isdigit() else 10

        result = self.get_feed(sort=sort, limit=min(limit, 25))

        if not result.get('success') and result.get('error'):
            return f"❌ Failed to fetch feed: {result.get('error')}"

        posts = result.get('posts', []) or result.get('data', {}).get('posts', [])
        if not posts:
            return "📚 No posts found"

        output = f"📚 MoltBook Feed ({sort}, {len(posts)} posts):\n\n"
        for post in posts[:limit]:
            title = post.get('title', 'No title')
            author = post.get('agent_name', post.get('author_name', 'Unknown'))
            submolt = post.get('submolt_name', 'general')
            upvotes = post.get('upvotes', 0)
            comments = post.get('comment_count', 0)
            post_id = post.get('id', 'unknown')[:8]

            output += f"📖 [{submolt}] {title[:60]}{'...' if len(title) > 60 else ''}\n"
            output += f"   👤 @{author} | ⬆️ {upvotes} | 💬 {comments} | 🆔 {post_id}\n\n"

        return output

    def comment_command(self, post_id: str, *args):
        """Add a comment: /moltbook_comment <post_id> <content>"""
        if not self.initialized:
            return "❌ MoltBook not initialized"

        if not post_id or not args:
            return "❌ Usage: /moltbook_comment <post_id> <your comment>"

        content = ' '.join(args)
        result = self.add_comment(post_id, content)

        if result.get('success'):
            return f"✅ Comment added to post {post_id[:12]}..."
        else:
            error = result.get('error', 'Unknown error')
            if isinstance(error, dict):
                error = error.get('message', str(error))
            return f"❌ Comment failed: {error}"

    def search_command(self, *args):
        """Search MoltBook: /moltbook_search <query>"""
        if not self.initialized:
            return "❌ MoltBook not initialized"

        if not args:
            return "❌ Usage: /moltbook_search <query>"

        query = ' '.join(args)
        result = self.search(query, limit=10)

        if not result.get('success') and result.get('error'):
            return f"❌ Search failed: {result.get('error')}"

        posts = result.get('posts', []) or result.get('results', []) or []
        if not posts:
            return f"🔍 No results for '{query}'"

        output = f"🔍 MoltBook Search: '{query}' ({len(posts)} results)\n\n"
        for post in posts[:10]:
            title = post.get('title', post.get('content', 'No title')[:60])
            author = post.get('agent_name', 'Unknown')
            score = post.get('score', post.get('upvotes', 0))
            post_id = post.get('id', 'unknown')[:8]

            output += f"📖 {title[:60]}{'...' if len(title) > 60 else ''}\n"
            output += f"   👤 @{author} | ⬆️ {score} | 🆔 {post_id}\n\n"

        return output

    def submolts_command(self):
        """List submolts: /moltbook_submolts"""
        if not self.initialized:
            return "❌ MoltBook not initialized"

        result = self.list_submolts()

        if not result.get('success') and result.get('error'):
            return f"❌ Failed to list submolts: {result.get('error')}"

        submolts = result.get('submolts', []) or result.get('data', {}).get('submolts', [])
        if not submolts:
            return "📚 No submolts found"

        output = f"📚 MoltBook Submolts ({len(submolts)}):\n\n"
        for sub in submolts[:15]:
            name = sub.get('name', 'unknown')
            display = sub.get('display_name', name)
            subs = sub.get('subscriber_count', 0)
            desc = sub.get('description', '')[:50]

            output += f"📖 #{name}\n"
            output += f"   {display} | 👥 {subs} subscribers\n"
            if desc:
                output += f"   {desc}...\n"
            output += "\n"

        return output

    def follow_command(self, agent_name: str):
        """Follow an agent: /moltbook_follow <agent_name>"""
        if not self.initialized:
            return "❌ MoltBook not initialized"

        if not agent_name:
            return "❌ Usage: /moltbook_follow <agent_name>"

        result = self.follow_agent(agent_name.lstrip('@'))

        if result.get('success'):
            return f"✅ Now following @{agent_name.lstrip('@')} on MoltBook"
        else:
            error = result.get('error', 'Unknown error')
            if isinstance(error, dict):
                error = error.get('message', str(error))
            return f"❌ Follow failed: {error}"


# Plugin factory function
def create_plugin(core):
    return MoltBookPlugin({})


PLUGIN_INFO = {
    "name": "moltbook",
    "version": "1.0.0",
    "description": "MoltBook integration - Reddit for AI Agents",
    "author": "AlleyBot",
    "requires": [],
    "environment_vars": ["MOLTBOOK_API_KEY"]
}
