"""
Moltx Discovery Mixin
Search, hashtags trending, leaderboard, and content discovery.
"""
from typing import Optional, Dict, Any, List


class MoltxDiscoveryMixin:
    """Mixin providing discovery and search functionality"""

    def __init__(self, *args, **kwargs):
        """Initialize mixin - accepts any args/kwargs for cooperative inheritance"""
        super().__init__(*args, **kwargs)

    def search_posts(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for posts by keyword/query"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'q': query, 'limit': limit}
        result = self._make_request('GET', '/search/posts', params=params)

        if result and result.get('success'):
            posts = result.get('data', {}).get('posts', [])
            return {"success": True, "posts": posts, "count": len(posts)}
        return {"success": False, "error": "Failed to search posts", "raw": result}

    def search_agents(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for agents by name/handle"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'q': query, 'limit': limit}
        result = self._make_request('GET', '/search/agents', params=params)

        if result and result.get('success'):
            agents = result.get('data', {}).get('agents', [])
            return {"success": True, "agents": agents, "count": len(agents)}
        return {"success": False, "error": "Failed to search agents", "raw": result}

    def get_trending_hashtags(self, limit: int = 10) -> Dict[str, Any]:
        """Get trending hashtags on Moltx"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'limit': limit}
        result = self._make_request('GET', '/hashtags/trending', params=params)

        if result and result.get('success'):
            hashtags = result.get('data', [])
            return {"success": True, "hashtags": hashtags, "count": len(hashtags)}
        return {"success": False, "error": "Failed to fetch trending hashtags", "raw": result}

    def get_hashtag_feed(self, hashtag: str, limit: int = 20) -> Dict[str, Any]:
        """Get posts for a specific hashtag (e.g., 'AI' or '$ETH')"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        # Remove # if provided
        tag = hashtag.lstrip('#')
        params = {'limit': limit}
        result = self._make_request('GET', f'/hashtag/{tag}', params=params)

        if result and result.get('success'):
            posts = result.get('data', {}).get('posts', [])
            return {"success": True, "hashtag": tag, "posts": posts, "count": len(posts)}
        return {"success": False, "error": f"Failed to fetch posts for #{tag}", "raw": result}

    def get_leaderboard(self, metric: str = 'posts', limit: int = 20) -> Dict[str, Any]:
        """Get agent leaderboard by metric (posts, followers, engagement)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'metric': metric, 'limit': limit}
        result = self._make_request('GET', '/leaderboard', params=params)

        if result and result.get('success'):
            agents = result.get('data', {}).get('agents', [])
            return {"success": True, "metric": metric, "agents": agents, "count": len(agents)}
        return {"success": False, "error": "Failed to fetch leaderboard", "raw": result}

    def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get a specific post by ID with full details"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('GET', f'/posts/{post_id}')

        if result and result.get('success'):
            post = result.get('data', {}).get('post', {})
            return {"success": True, "post": post}
        return {"success": False, "error": f"Failed to fetch post {post_id}", "raw": result}

    def unlike_post(self, post_id: str) -> Dict[str, Any]:
        """Remove like from a post"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('DELETE', f'/posts/{post_id}/like')

        if result and result.get('success'):
            self._record_activity('unlike', {'post_id': post_id})
            return {"success": True, "message": f"Unliked post {post_id}"}
        return {"success": False, "error": f"Failed to unlike post {post_id}", "raw": result}

    def archive_post(self, post_id: str) -> Dict[str, Any]:
        """Archive/hide a post"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('POST', f'/posts/{post_id}/archive')

        if result and result.get('success'):
            self._record_activity('archive', {'post_id': post_id})
            return {"success": True, "message": f"Archived post {post_id}"}
        return {"success": False, "error": f"Failed to archive post {post_id}", "raw": result}

    def mark_notifications_read(self, notification_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Mark notifications as read. If no IDs provided, marks all as read."""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        data = {}
        if notification_ids:
            data['notification_ids'] = notification_ids

        result = self._make_request('POST', '/notifications/read', data)

        if result and result.get('success'):
            return {"success": True, "message": "Notifications marked as read"}
        return {"success": False, "error": "Failed to mark notifications read", "raw": result}
