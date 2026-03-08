#!/usr/bin/env python3
"""
Platform Stats Aggregator
Fetches real-time stats from all platforms and aggregates them
"""
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional


class PlatformStatsAggregator:
    """Aggregates stats from all platforms"""
    
    def __init__(self, core):
        self.core = core
        self.moltx_api_key = os.getenv('MOLTX_API_KEY')
        self.moltchan_api_key = os.getenv('MOLTCHAN_API_KEY')
        self.moltroad_api_key = os.getenv('MOLTROAD_API_KEY')
        self._follower_cache = None  # {moltx: N, moltchan: N, moltroad: N, total: N, fetched_at: iso}
        self._follower_cache_ttl = 86400  # 24 hours in seconds
    
    def get_all_stats(self) -> Dict:
        """Get aggregated stats from all platforms.
        
        Strategy: Pull from loaded plugins first (instant, no network).
        Fall back to direct API calls only if plugin not loaded.
        """
        stats = {
            'total_posts': 0,
            'total_comments': 0,
            'total_followers': 0,
            'total_following': 0,
            'platforms': {},
            'recent_activity': [],
            'timestamp': datetime.now().isoformat()
        }
        
        plugins = {}
        if self.core and hasattr(self.core, 'plugin_manager'):
            plugins = self.core.plugin_manager.plugins
        
        # ── Moltx ──
        moltx_stats = self._get_plugin_stats(plugins, 'moltx')
        if not moltx_stats:
            moltx_stats = self._get_moltx_stats()
        if not moltx_stats:
            moltx_stats = {'posts': 0, 'followers': 0, 'following': 0, 'recent_posts': []}
        stats['platforms']['moltx'] = moltx_stats
        stats['total_posts'] += moltx_stats.get('posts', 0)
        stats['total_followers'] += moltx_stats.get('followers', 0)
        stats['total_following'] += moltx_stats.get('following', 0)
        stats['recent_activity'].extend(moltx_stats.get('recent_posts', []))
        
        # ── MoltChan ──
        moltchan_stats = self._get_plugin_stats(plugins, 'moltchan')
        if not moltchan_stats:
            moltchan_stats = self._get_moltchan_stats()
        if not moltchan_stats:
            moltchan_stats = {'threads': 0, 'replies': 0}
        stats['platforms']['moltchan'] = moltchan_stats
        stats['total_posts'] += moltchan_stats.get('threads', moltchan_stats.get('posts', 0))
        stats['total_comments'] += moltchan_stats.get('replies', moltchan_stats.get('comments', 0))
        
        # ── MoltRoad ──
        moltroad_stats = self._get_plugin_stats(plugins, 'moltroad')
        if not moltroad_stats:
            moltroad_stats = {'posts': 0}
        stats['platforms']['moltroad'] = moltroad_stats
        stats['total_posts'] += moltroad_stats.get('posts', 0)
        
        # Platform-specific stats
        moltx_posts = stats['platforms']['moltx'].get('posts', 0)
        moltx_followers = stats['platforms']['moltx'].get('followers', 0)
        moltchan_posts = stats['platforms']['moltchan'].get('threads', stats['platforms']['moltchan'].get('posts', 0))
        moltchan_replies = stats['platforms']['moltchan'].get('replies', 0)
        moltroad_posts = stats['platforms']['moltroad'].get('posts', 0)
        
        # Debug output for tracking
        # print(f"[DASHBOARD-DEBUG] Platform stats - Moltx: {moltx_posts} posts, {moltx_followers} followers")
        
        # Sort recent activity by timestamp
        stats['recent_activity'].sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        stats['recent_activity'] = stats['recent_activity'][:50]

        # Override total_followers with cached combined count from public APIs
        follower_data = self._get_cached_followers()
        stats['total_followers'] = follower_data.get('total', stats['total_followers'])
        # Update per-platform follower counts too
        if 'moltx' in stats['platforms']:
            stats['platforms']['moltx']['followers'] = follower_data.get('moltx', stats['platforms']['moltx'].get('followers', 0))

        return stats
    
    def _get_plugin_stats(self, plugins: Dict, plugin_name: str) -> Optional[Dict]:
        """Get stats from plugin by counting actual posts in memory"""
        try:
            plugin = plugins.get(plugin_name)
            if not plugin:
                return None
            
            # First try get_stats() method
            if hasattr(plugin, 'get_stats'):
                stats = plugin.get_stats()
                if stats:
                    return stats
            
            # Count from memory - this is where real data lives
            result = {'posts': 0, 'comments': 0, 'followers': 0, 'recent_posts': []}
            
            if plugin_name == 'moltx':
                posts = self.core.get_memory('moltx_recent_posts') or []
                result['posts'] = len(posts)
                # Try to get followers from profile if possible
                if hasattr(plugin, 'agent_name') and plugin.agent_name:
                    result['followers'] = getattr(plugin, 'follower_count', 0)
                
            elif plugin_name == 'moltchan':
                posts = self.core.get_memory('moltchan_recent_posts') or []
                result['threads'] = len(posts)
                result['posts'] = len(posts)
                
            elif plugin_name == 'moltroad':
                posts = self.core.get_memory('moltroad_recent_posts') or []
                result['posts'] = len(posts)
                
            elif plugin_name == 'clawbr':
                posts = self.core.get_memory('clawbr_recent_posts') or []
                debates = self.core.get_memory('clawbr_recent_debates') or []
                result['posts'] = len(posts)
                result['debates_joined'] = len(debates)
            
            # Add recent activity from memory
            memory_key = f'{plugin_name}_recent_posts'
            recent = self.core.get_memory(memory_key) or []
            for post in recent[:10]:
                result['recent_posts'].append({
                    'type': 'post',
                    'platform': plugin_name.title(),
                    'content': post.get('content', post.get('title', ''))[:100],
                    'timestamp': post.get('timestamp', post.get('created_at', '')),
                    'url': post.get('url', '')
                })
            
            # print(f"[DASHBOARD-DEBUG] {plugin_name} stats from memory: {result}")
            return result if (result['posts'] > 0 or result.get('comments', 0) > 0) else None
            
        except Exception as e:
            # print(f"[DASHBOARD-DEBUG] Error getting {plugin_name} stats: {e}")
            return None
    
    def _get_moltx_stats(self) -> Optional[Dict]:
        """Get stats from Moltx using v0.17.6 API"""
        if not self.moltx_api_key:
            return None
        
        try:
            headers = {'Authorization': f'Bearer {self.moltx_api_key}'}
            
            # Get agent profile - returns {success, data: {agent}}
            response = requests.get(
                'https://moltx.io/v1/agents/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response is successful
                if not data.get('success'):
                    print(f"⚠️  Moltx API returned success=false")
                    return None
                
                agent = data.get('data', {}).get('agent', {})
                
                # Get recent posts from agent's feed
                posts_response = requests.get(
                    f"https://moltx.io/v1/agents/profile?name={agent.get('name')}",
                    timeout=10
                )
                
                recent_posts = []
                post_count = 0
                if posts_response.status_code == 200:
                    profile_data = posts_response.json()
                    posts_data = profile_data.get('posts', [])
                    post_count = len(posts_data)
                    
                    for post in posts_data[:10]:
                        recent_posts.append({
                            'type': 'post',
                            'platform': 'Moltx',
                            'content': post.get('content', '')[:100],
                            'url': f"https://moltx.io/post/{post.get('id')}",
                            'timestamp': post.get('created_at', ''),
                            'likes': post.get('like_count', 0),
                            'replies': post.get('reply_count', 0)
                        })
                
                # Moltx doesn't provide follower/following counts in /agents/me
                # We'll use post count from profile endpoint
                return {
                    'posts': post_count,
                    'followers': 0,  # Not available in API
                    'following': 0,  # Not available in API
                    'recent_posts': recent_posts,
                    'status': 'active'
                }
        except Exception as e:
            print(f"⚠️  Moltx stats error: {e}")
            return None
    
    def _get_cached_followers(self) -> Dict:
        """Get MoltX follower count, cached for 1 hour."""
        now = datetime.now()
        cache_ttl = 3600

        if self._follower_cache:
            try:
                fetched = datetime.fromisoformat(self._follower_cache['fetched_at'])
                age = (now - fetched).total_seconds()
                if age < cache_ttl:
                    return self._follower_cache
            except (ValueError, TypeError, KeyError):
                pass

        try:
            cached = self.core.get_memory('follower_cache') if self.core else None
            if cached and isinstance(cached, dict):
                fetched = datetime.fromisoformat(cached.get('fetched_at', ''))
                age = (now - fetched).total_seconds()
                if age < cache_ttl:
                    self._follower_cache = cached
                    return cached
        except Exception:
            pass

        moltx_followers = 0

        try:
            resp = requests.get(
                'https://moltx.io/v1/agent/AlleyBot/stats',
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    stats_data = data.get('data', data.get('stats', data))
                    if isinstance(stats_data, dict):
                        moltx_followers = stats_data.get('followers', stats_data.get('follower_count', 0))
        except Exception:
            pass

        if moltx_followers == 0:
            try:
                resp = requests.get(
                    'https://moltx.io/v1/agents/profile?name=AlleyBot',
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict):
                        agent = data.get('agent', data.get('data', data))
                        if isinstance(agent, dict):
                            moltx_followers = agent.get('follower_count', agent.get('followers', 0))
            except Exception:
                pass

        result = {
            'moltx': moltx_followers,
            'total': moltx_followers,
            'fetched_at': now.isoformat(),
        }

        # Save to both in-memory and persistent cache
        self._follower_cache = result
        try:
            if self.core:
                self.core.save_memory('follower_cache', result)
        except Exception:
            pass

        return result

    def _get_moltchan_stats(self) -> Optional[Dict]:
        """Get stats from MoltChan"""
        if not self.moltchan_api_key:
            return None
        
        try:
            headers = {'Authorization': f'Bearer {self.moltchan_api_key}'}
            
            # Get agent stats
            response = requests.get(
                'https://www.moltchan.org/api/v1/agents/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'threads': data.get('thread_count', 0),
                    'replies': data.get('reply_count', 0),
                    'status': 'active'
                }
        except Exception as e:
            print(f"⚠️  MoltChan stats error: {e}")
            return None
    
