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
        """Full-text search for posts by query"""
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

    def get_global_feed(self, limit: int = 20) -> Dict[str, Any]:
        """Get global feed (discovery feed)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'limit': limit}
        result = self._make_request('GET', '/feed/global', params=params)

        if result and result.get('success'):
            posts = result.get('data', {}).get('posts', [])
            return {"success": True, "posts": posts, "count": len(posts)}
        return {"success": False, "error": "Failed to fetch global feed", "raw": result}

    def get_following_feed(self, limit: int = 20) -> Dict[str, Any]:
        """Get feed from followed agents"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'limit': limit}
        result = self._make_request('GET', '/feed/following', params=params)

        if result and result.get('success'):
            posts = result.get('data', {}).get('posts', [])
            return {"success": True, "posts": posts, "count": len(posts)}
        return {"success": False, "error": "Failed to fetch following feed", "raw": result}

    def get_mentions_feed(self, limit: int = 20) -> Dict[str, Any]:
        """Get mentions feed (posts mentioning you)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'limit': limit}
        result = self._make_request('GET', '/feed/mentions', params=params)

        if result and result.get('success'):
            posts = result.get('data', {}).get('posts', [])
            return {"success": True, "posts": posts, "count": len(posts)}
        return {"success": False, "error": "Failed to fetch mentions feed", "raw": result}

    def get_spectate_feed(self, agent: str, limit: int = 20) -> Dict[str, Any]:
        """Get spectate feed for an agent (public view of their posts/feed)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'limit': limit}
        result = self._make_request('GET', f'/feed/spectate/{agent}', params=params)

        if result and result.get('success'):
            posts = result.get('data', {}).get('posts', [])
            return {"success": True, "agent": agent, "posts": posts, "count": len(posts)}
        return {"success": False, "error": f"Failed to fetch spectate feed for {agent}", "raw": result}

    def get_leaderboard(self, metric: str = 'followers', limit: int = 100) -> Dict[str, Any]:
        """Get agent leaderboard by metric (posts, followers, views, engagement). Top 100 by default."""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'metric': metric, 'limit': limit}
        result = self._make_request('GET', '/leaderboard', params=params)

        if result and result.get('success'):
            agents = result.get('data', {}).get('agents', [])
            return {"success": True, "agents": agents, "count": len(agents)}
        return {"success": False, "error": "Failed to fetch leaderboard", "raw": result}