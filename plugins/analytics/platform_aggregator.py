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
        self.moltbook_api_key = os.getenv('MOLTBOOK_API_KEY')
        self.moltx_api_key = os.getenv('MOLTX_API_KEY')
        self.moltchan_api_key = os.getenv('MOLTCHAN_API_KEY')
        self.moltroad_api_key = os.getenv('MOLTROAD_API_KEY')
        self.clawtasks_api_key = os.getenv('CLAWTASKS_API_KEY')
        self.fourclaw_api_key = os.getenv('FOURCLAW_API_KEY')
    
    def get_all_stats(self) -> Dict:
        """Get aggregated stats from all platforms"""
        print("🔍 PlatformStatsAggregator: Starting stats collection...")
        stats = {
            'total_posts': 0,
            'total_comments': 0,
            'total_followers': 0,
            'total_following': 0,
            'platforms': {},
            'recent_activity': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Fetch from each platform
        print("📊 Fetching Moltbook stats...")
        moltbook_stats = self._get_moltbook_stats()
        print(f"   Moltbook: {moltbook_stats}")
        
        print("📊 Fetching Moltx stats...")
        moltx_stats = self._get_moltx_stats()
        print(f"   Moltx: {moltx_stats}")
        
        print("📊 Fetching MoltChan stats...")
        moltchan_stats = self._get_moltchan_stats()
        print(f"   MoltChan: {moltchan_stats}")
        
        print("📊 Fetching ClawTasks stats...")
        clawtasks_stats = self._get_clawtasks_stats()
        print(f"   ClawTasks: {clawtasks_stats}")
        
        print("📊 Fetching 4claw stats...")
        fourclaw_stats = self._get_fourclaw_stats()
        print(f"   4claw: {fourclaw_stats}")
        
        # Aggregate
        if moltbook_stats:
            stats['platforms']['moltbook'] = moltbook_stats
            stats['total_posts'] += moltbook_stats.get('posts', 0)
            stats['total_comments'] += moltbook_stats.get('comments', 0)
            stats['total_followers'] += moltbook_stats.get('followers', 0)
            stats['total_following'] += moltbook_stats.get('following', 0)
            stats['recent_activity'].extend(moltbook_stats.get('recent_posts', []))
        
        if moltx_stats:
            stats['platforms']['moltx'] = moltx_stats
            stats['total_posts'] += moltx_stats.get('posts', 0)
            stats['total_followers'] += moltx_stats.get('followers', 0)
            stats['total_following'] += moltx_stats.get('following', 0)
            stats['recent_activity'].extend(moltx_stats.get('recent_posts', []))
        
        if moltchan_stats:
            stats['platforms']['moltchan'] = moltchan_stats
            stats['total_posts'] += moltchan_stats.get('threads', 0)
            stats['total_comments'] += moltchan_stats.get('replies', 0)
        
        if clawtasks_stats:
            stats['platforms']['clawtasks'] = clawtasks_stats
        
        if fourclaw_stats:
            stats['platforms']['fourclaw'] = fourclaw_stats
            stats['total_posts'] += fourclaw_stats.get('threads', 0)
            stats['total_comments'] += fourclaw_stats.get('replies', 0)
        
        # Sort recent activity by timestamp
        stats['recent_activity'].sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        stats['recent_activity'] = stats['recent_activity'][:50]  # Keep last 50
        
        print(f"✅ Aggregation complete: {stats['total_posts']} posts, {stats['total_comments']} comments, {stats['total_followers']} followers")
        
        return stats
    
    def _get_moltbook_stats(self) -> Optional[Dict]:
        """Get stats from Moltbook"""
        if not self.moltbook_api_key:
            return None
        
        try:
            headers = {'Authorization': f'Bearer {self.moltbook_api_key}'}
            
            # Get agent profile - this includes recentPosts
            response = requests.get(
                'https://www.moltbook.com/api/v1/agents/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response is successful
                if not data.get('success'):
                    print(f"⚠️  Moltbook API returned success=false")
                    return None
                
                agent = data.get('agent', {})
                stats = agent.get('stats', {})
                recent_posts_data = data.get('recentPosts', [])
                
                # Format recent posts
                recent_posts = []
                for post in recent_posts_data[:10]:
                    recent_posts.append({
                        'type': 'post',
                        'platform': 'Moltbook',
                        'title': post.get('title', ''),
                        'url': f"https://www.moltbook.com/post/{post.get('id')}",
                        'timestamp': post.get('created_at', ''),
                        'upvotes': post.get('upvotes', 0),
                        'comments': post.get('comment_count', 0)
                    })
                
                return {
                    'posts': stats.get('posts', 0),
                    'comments': stats.get('comments', 0),
                    'followers': agent.get('follower_count', 0),
                    'following': agent.get('following_count', 0),
                    'karma': agent.get('karma', 0),
                    'recent_posts': recent_posts,
                    'status': 'active'
                }
        except Exception as e:
            print(f"⚠️  Moltbook stats error: {e}")
            return None
    
    def _get_moltx_stats(self) -> Optional[Dict]:
        """Get stats from Moltx"""
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
    
    def _get_clawtasks_stats(self) -> Optional[Dict]:
        """Get stats from ClawTasks"""
        if not self.clawtasks_api_key:
            return None
        
        try:
            headers = {'Authorization': f'Bearer {self.clawtasks_api_key}'}
            
            # Get agent stats
            response = requests.get(
                'https://clawtasks.com/api/agents/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'tasks_completed': data.get('tasks_completed', 0),
                    'earnings_usdc': data.get('earnings_usdc', 0),
                    'status': 'active'
                }
        except Exception as e:
            print(f"⚠️  ClawTasks stats error: {e}")
            return None
    
    def _get_fourclaw_stats(self) -> Optional[Dict]:
        """Get stats from 4claw"""
        if not self.fourclaw_api_key:
            return None
        
        try:
            headers = {'Authorization': f'Bearer {self.fourclaw_api_key}'}
            
            # Get agent status
            response = requests.get(
                'https://www.4claw.org/api/v1/agents/status',
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
            print(f"⚠️  4claw stats error: {e}")
            return None
