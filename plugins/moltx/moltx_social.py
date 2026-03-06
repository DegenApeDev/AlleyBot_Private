"""
MoltX Social - All social interaction functionality
Consolidates: engagement, messaging, discovery, service_messages, async_engagement
"""
import json
import time
import random
import requests
import os
import re
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    import mimetypes
except ImportError:
    mimetypes = None

logger = logging.getLogger(__name__)


class MoltxSocialMixin:
    """Consolidated social functionality: engagement, messaging, discovery, service messages, async"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Async engagement
        self._engagement_task = None
        self._engagement_running = False
        # Service messages
        self._latest_notice = None
        self._latest_hint = None
        self._model_guide = None
        self._feature_suggestions = []
        self._api_tips = []
    
    # =========================================================================
    # ENGAGEMENT - Feed, likes, follows, notifications
    # =========================================================================
    
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
            if hasattr(self, 'api_key') and self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, mime_type)}
                response = requests.post(upload_url, files=files, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                if data.get('success') and data.get('data'):
                    return data.get('data', {}).get('url') or data.get('data', {}).get('media_url')
                return "❌ No media URL returned"
        except Exception as e:
            return f"❌ Upload failed: {str(e)[:100]}"
    
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
        
        if result and isinstance(result, dict):
            if result.get('success'):
                self._record_activity('like', {'post_id': post_id})
                return f"✅ Liked post {post_id}"
            else:
                error = result.get('error', result.get('message', 'Unknown error'))
                return f"❌ Failed to like post {post_id}: {error}"
        elif result:
            return f"⚠️ Unexpected response liking post {post_id}: {str(result)[:100]}"
        else:
            return f"❌ Failed to like post {post_id}: No response from API"
    
    def unlike_post(self, post_id):
        """Unlike a post"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        if not post_id:
            return "❌ No post ID provided"
        
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
    
    def reply_to_post(self, post_id, content):
        """Reply to a post"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        if not post_id or not content:
            return "❌ Missing post ID or content"
        
        if isinstance(post_id, str) and post_id.strip().startswith('{'):
            try:
                parsed = json.loads(post_id)
                post_id = parsed.get('post_id') or parsed.get('id')
            except json.JSONDecodeError:
                pass
        
        if isinstance(post_id, str):
            post_id = post_id.strip()
        
        data = {'type': 'reply', 'parent_id': post_id, 'content': content}
        result = self._make_request('POST', '/posts', data=data)
        
        if result and 'post_id' in result:
            reply_id = result['post_id']
            self._record_activity('reply', {'post_id': post_id, 'reply_id': reply_id})
            return f"✅ Replied to post {post_id}! Reply ID: {reply_id}"
        return f"❌ Failed to reply to post {post_id}"
    
    def repost_post(self, post_id):
        """Repost without comment"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."
        if not post_id:
            return "❌ No post ID provided"
        
        if isinstance(post_id, str) and post_id.strip().startswith('{'):
            try:
                parsed = json.loads(post_id)
                post_id = parsed.get('post_id') or parsed.get('id')
            except json.JSONDecodeError:
                pass
        
        if isinstance(post_id, str):
            post_id = post_id.strip()
        
        data = {'type': 'repost', 'parent_id': post_id}
        result = self._make_request('POST', '/posts', json=data)
        
        if result and 'post_id' in result:
            repost_id = result['post_id']
            self._record_activity('repost', {'post_id': post_id, 'repost_id': repost_id})
            return f"✅ Reposted post {post_id}! Repost ID: {repost_id}"
        return f"❌ Failed to repost post {post_id}"
    
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
    
    # =========================================================================
    # MESSAGING - DMs and communities
    # =========================================================================
    
    def start_dm(self, agent_name: str) -> Dict[str, Any]:
        """Start or get a DM conversation with an agent"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}
        result = self._make_request('POST', f'/dm/{agent_name}')
        if result and result.get('success'):
            return {"success": True, "data": result.get('data', {})}
        return {"success": False, "error": f"Failed to start DM with @{agent_name}", "raw": result}
    
    def list_dms(self) -> Dict[str, Any]:
        """List all DM conversations"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}
        result = self._make_request('GET', '/dm')
        if result and result.get('success'):
            conversations = result.get('data', {}).get('conversations', [])
            return {"success": True, "conversations": conversations, "count": len(conversations)}
        return {"success": False, "error": "Failed to list DMs", "raw": result}
    
    def get_dm_messages(self, agent_name: str, limit: int = 50) -> Dict[str, Any]:
        """Get messages from a DM conversation"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}
        params = {'limit': limit}
        result = self._make_request('GET', f'/dm/{agent_name}/messages', params=params)
        if result and result.get('success'):
            messages = result.get('data', {}).get('messages', [])
            return {"success": True, "messages": messages, "count": len(messages)}
        return {"success": False, "error": f"Failed to get messages with @{agent_name}", "raw": result}
    
    def send_dm_message(self, agent_name: str, content: str, media_url: str = None) -> Dict[str, Any]:
        """Send a message to an agent"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}
        data = {'content': content}
        if media_url:
            data['media_url'] = media_url
        result = self._make_request('POST', f'/dm/{agent_name}/messages', data)
        if result and result.get('success'):
            msg_data = result.get('data', {})
            self._record_activity('dm_sent', {
                'to': agent_name,
                'content': content[:100],
                'message_id': msg_data.get('id')
            })
            return {"success": True, "message_id": msg_data.get('id'), "data": msg_data}
        return {"success": False, "error": f"Failed to send DM to @{agent_name}", "raw": result}
    
    def list_public_communities(self) -> Dict[str, Any]:
        """Browse public communities"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}
        result = self._make_request('GET', '/communities')
        if result and result.get('success'):
            communities = result.get('data', {}).get('communities', [])
            return {"success": True, "communities": communities, "count": len(communities)}
        return {"success": False, "error": "Failed to list public communities", "raw": result}
    
    def join_community(self, community_id: str) -> Dict[str, Any]:
        """Join a community"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}
        result = self._make_request('POST', f'/communities/{community_id}/join')
        if result and result.get('success'):
            self._record_activity('community_joined', {'community_id': community_id})
            return {"success": True, "data": result.get('data', {})}
        return {"success": False, "error": f"Failed to join community {community_id}", "raw": result}
    
    # =========================================================================
    # DISCOVERY - Search, hashtags, leaderboard
    # =========================================================================
    
    def search_posts(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Full-text search for posts"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}
        params = {'q': query, 'limit': limit}
        result = self._make_request('GET', '/search/posts', params=params)
        if result and result.get('success'):
            posts = result.get('data', {}).get('posts', [])
            return {"success": True, "posts": posts, "count": len(posts)}
        return {"success": False, "error": "Failed to search posts", "raw": result}
    
    def search_agents(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for agents by name"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}
        params = {'q': query, 'limit': limit}
        result = self._make_request('GET', '/search/agents', params=params)
        if result and result.get('success'):
            agents = result.get('data', {}).get('agents', [])
            return {"success": True, "agents": agents, "count": len(agents)}
        return {"success": False, "error": "Failed to search agents", "raw": result}
    
    def get_trending_hashtags(self, limit: int = 10) -> Dict[str, Any]:
        """Get trending hashtags"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}
        params = {'limit': limit}
        result = self._make_request('GET', '/hashtags/trending', params=params)
        if result and result.get('success'):
            hashtags = result.get('data', [])
            return {"success": True, "hashtags": hashtags, "count": len(hashtags)}
        return {"success": False, "error": "Failed to fetch trending hashtags", "raw": result}
    
    def get_leaderboard(self, metric: str = 'followers', limit: int = 100) -> Dict[str, Any]:
        """Get agent leaderboard by metric"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}
        params = {'metric': metric, 'limit': limit}
        result = self._make_request('GET', '/leaderboard', params=params)
        if result and result.get('success'):
            agents = result.get('data', {}).get('agents', [])
            return {"success": True, "agents": agents, "count": len(agents)}
        return {"success": False, "error": "Failed to fetch leaderboard", "raw": result}
    
    # =========================================================================
    # SERVICE MESSAGES - Parse platform guidance
    # =========================================================================
    
    def _parse_service_messages(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse service messages from MoltX API response"""
        if not isinstance(api_response, dict):
            return {}
        
        parsed = {
            'has_notice': False,
            'has_hint': False,
            'has_guide': False,
            'actionable_items': []
        }
        
        # Parse moltx_notice
        if 'moltx_notice' in api_response:
            notice = api_response['moltx_notice']
            self._latest_notice = notice
            parsed['has_notice'] = True
            parsed['notice'] = notice
            
            if 'feature' in notice:
                feature = notice['feature']
                self._feature_suggestions.append({
                    'feature': feature,
                    'timestamp': datetime.now().isoformat(),
                    'version': notice.get('skill_version', 'unknown')
                })
                parsed['actionable_items'].append({
                    'type': 'feature_suggestion',
                    'priority': 'high',
                    'action': feature,
                    'source': 'moltx_notice'
                })
            
            if hasattr(self, 'core'):
                self.core.save_memory('moltx_skill_version', notice.get('skill_version'))
                self.core.save_memory('moltx_api_version', notice.get('api_version'))
        
        # Parse moltx_hint
        if 'moltx_hint' in api_response:
            hint = api_response['moltx_hint']
            self._latest_hint = hint
            parsed['has_hint'] = True
            parsed['hint'] = hint
            
            hint_type = hint.get('type', 'general')
            hint_message = hint.get('message', '')
            hint_example = hint.get('example', '')
            
            parsed['actionable_items'].append({
                'type': 'hint',
                'priority': 'medium',
                'category': hint_type,
                'action': hint_message,
                'example': hint_example,
                'source': 'moltx_hint'
            })
            
            if hasattr(self, 'core'):
                hints = self.core.get_memory('moltx_hints') or []
                hints.append({
                    'type': hint_type,
                    'title': hint.get('title', ''),
                    'message': hint_message,
                    'example': hint_example,
                    'timestamp': datetime.now().isoformat()
                })
                self.core.save_memory('moltx_hints', hints[-20:])
        
        # Parse _model_guide
        if '_model_guide' in api_response:
            guide = api_response['_model_guide']
            self._model_guide = guide
            parsed['has_guide'] = True
            parsed['guide'] = guide
            
            if 'tips' in guide:
                tips = guide['tips']
                self._api_tips.append({
                    'tips': tips,
                    'timestamp': datetime.now().isoformat()
                })
                
                if isinstance(tips, str):
                    tip_list = [t.strip() for t in tips.replace('\n', '. ').split('. ') if t.strip()]
                    for tip in tip_list:
                        parsed['actionable_items'].append({
                            'type': 'api_tip',
                            'priority': 'low',
                            'action': tip,
                            'source': '_model_guide'
                        })
                
                if hasattr(self, 'core'):
                    self.core.save_memory('moltx_api_tips', tips)
            
            if 'quick_start' in guide and hasattr(self, 'core'):
                self.core.save_memory('moltx_quick_start', guide['quick_start'])
            
            if 'endpoints' in guide and hasattr(self, 'core'):
                self.core.save_memory('moltx_endpoints', guide['endpoints'])
        
        return parsed
    
    # =========================================================================
    # ASYNC ENGAGEMENT - Non-blocking background tasks
    # =========================================================================
    
    async def _run_engagement_async(self, engagement_func, *args, **kwargs) -> Optional[str]:
        """Run engagement function asynchronously"""
        if self._engagement_running:
            logger.info("⏸️ Engagement already running in background, skipping...")
            return "⏸️ Engagement already in progress"
        
        try:
            self._engagement_running = True
            logger.info("🔄 Starting background engagement task...")
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, engagement_func, *args, **kwargs)
            
            logger.info(f"✅ Background engagement complete: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Background engagement failed: {e}")
            return f"❌ Background engagement error: {e}"
        finally:
            self._engagement_running = False
    
    def start_engagement_background(self, engagement_func, *args, **kwargs) -> str:
        """Start engagement in background without blocking"""
        if self._engagement_running:
            return "⏸️ Engagement already running in background"
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        self._engagement_task = loop.create_task(
            self._run_engagement_async(engagement_func, *args, **kwargs)
        )
        
        return "🔄 Engagement started in background (non-blocking)"
    
    def is_engagement_running(self) -> bool:
        """Check if background engagement is currently running"""
        return self._engagement_running
