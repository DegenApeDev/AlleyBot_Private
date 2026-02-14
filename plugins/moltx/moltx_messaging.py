"""
Moltx Messaging Mixin
Direct messages, DM replies, AI-powered DM generation, and DM activity logging.
Uses v0.23.1 API format: POST /v1/dm/:name, GET /v1/dm, etc.
Enhanced with community support: browse public communities, join, list joined, message with media.
Added: feeds, search, hashtags, notifications, articles, leaderboard, claim/rewards/key recovery, first boot/heartbeat protocols.
"""
import re
from datetime import datetime
from typing import Optional, Dict, Any, List


class MoltxMessagingMixin:
    """Mixin providing DM, community, and extended Moltx v0.23.1 functionality"""

    def __init__(self, *args, **kwargs):
        """Initialize mixin - accepts any args/kwargs for cooperative inheritance"""
        super().__init__(*args, **kwargs)

    def perform_first_boot(self) -> Dict[str, Any]:
        """First boot protocol (POST /v1/boot)"""
        if self.initialized:
            return {"success": True, "message": "Already booted"}
        result = self._make_request('POST', '/v1/boot')
        if result and result.get('success'):
            self.initialized = True
            return {"success": True, "data": result.get('data', {})}
        return {"success": False, "error": "First boot failed", "raw": result}

    def send_heartbeat(self) -> Dict[str, Any]:
        """Send heartbeat (POST /v1/heartbeat)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}
        result = self._make_request('POST', '/v1/heartbeat')
        if result and result.get('success'):
            return {"success": True, "data": result.get('data', {})}
        return {"success": False, "error": "Heartbeat failed", "raw": result}

    def start_dm(self, agent_name: str) -> Dict[str, Any]:
        """Start or get a DM conversation with an agent (POST /v1/dm/:name)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('POST', f'/v1/dm/{agent_name}')

        if result and result.get('success'):
            return {"success": True, "data": result.get('data', {})}
        return {"success": False, "error": f"Failed to start DM with @{agent_name}", "raw": result}

    def list_dms(self) -> Dict[str, Any]:
        """List all DM conversations (GET /v1/dm)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('GET', '/v1/dm')

        if result and result.get('success'):
            conversations = result.get('data', {}).get('conversations', [])
            return {"success": True, "conversations": conversations, "count": len(conversations)}
        return {"success": False, "error": "Failed to list DMs", "raw": result}

    def get_dm_messages(self, agent_name: str, limit: int = 50) -> Dict[str, Any]:
        """Get messages from a DM conversation (GET /v1/dm/:name/messages)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'limit': limit}
        result = self._make_request('GET', f'/v1/dm/{agent_name}/messages', params=params)

        if result and result.get('success'):
            messages = result.get('data', {}).get('messages', [])
            return {"success": True, "messages": messages, "count": len(messages)}
        return {"success": False, "error": f"Failed to get messages with @{agent_name}", "raw": result}

    def send_dm_message(self, agent_name: str, content: str, media_url: str = None) -> Dict[str, Any]:
        """Send a message to an agent (POST /v1/dm/:name/messages), supports media"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        data = {'content': content}
        if media_url:
            data['media_url'] = media_url

        result = self._make_request('POST', f'/v1/dm/{agent_name}/messages', data)

        if result and result.get('success'):
            msg_data = result.get('data', {})
            self._record_activity('dm_sent', {
                'to': agent_name,
                'content': content[:100],
                'message_id': msg_data.get('id')
            })
            return {"success": True, "message_id": msg_data.get('id'), "data": msg_data}
        return {"success": False, "error": f"Failed to send DM to @{agent_name}", "raw": result}

    def generate_dm_reply(self, agent_name: str, messages: List[Dict[str, Any]]) -> str:
        """AI-powered reply generation for DMs"""
        try:
            from grok_ai import grok_ai
            context = '\n'.join([f"{m.get('sender', 'Unknown')}: {m.get('content', '')[:200]}" for m in messages[-10:]])
            prompt = f"You are chatting in a DM with @{agent_name}. Recent messages:\n{context}\n\nYour natural, concise reply:"
            return grok_ai.generate(prompt, max_tokens=150, temperature=0.7)
        except ImportError:
            return f"AI unavailable. Suggested reply: Thanks for the message @{agent_name}!"
        except Exception:
            return "Error generating reply."

    # --- Community Functionality ---

    def list_public_communities(self) -> Dict[str, Any]:
        """Browse public communities/groups (GET /v1/communities)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('GET', '/v1/communities')

        if result and result.get('success'):
            communities = result.get('data', {}).get('communities', [])
            return {"success": True, "communities": communities, "count": len(communities)}
        return {"success": False, "error": "Failed to list public communities", "raw": result}

    def join_community(self, community_id: str) -> Dict[str, Any]:
        """Join a community/group (POST /v1/communities/:id/join)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('POST', f'/v1/communities/{community_id}/join')

        if result and result.get('success'):
            self._record_activity('community_joined', {'community_id': community_id})
            return {"success": True, "data": result.get('data', {})}
        return {"success": False, "error": f"Failed to join community {community_id}", "raw": result}

    def list_communities(self) -> Dict[str, Any]:
        """List joined community conversations (GET /v1/conversations)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('GET', '/v1/conversations')

        if result and result.get('success'):
            conversations = result.get('data', {}).get('conversations', [])
            return {"success": True, "communities": conversations, "count": len(conversations)}
        return {"success": False, "error": "Failed to list communities", "raw": result}

    def leave_community(self, community_id: str) -> Dict[str, Any]:
        """Leave a community (POST /v1/conversations/:id/leave)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('POST', f'/v1/conversations/{community_id}/leave')

        if result and result.get('success'):
            self._record_activity('community_left', {'community_id': community_id})
            return {"success": True, "data": result.get('data', {})}
        return {"success": False, "error": f"Failed to leave community {community_id}", "raw": result}

    def get_community_messages(self, conversation_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get messages from a community conversation (GET /v1/conversations/:id/messages)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'limit': limit}
        result = self._make_request('GET', f'/v1/conversations/{conversation_id}/messages', params=params)

        if result and result.get('success'):
            messages = result.get('data', {}).get('messages', [])
            return {"success": True, "messages": messages, "count": len(messages)}
        return {"success": False, "error": f"Failed to get messages from community {conversation_id}", "raw": result}

    def send_community_message(self, conversation_id: str, content: str, media_url: str = None) -> Dict[str, Any]:
        """Send a message to a community (POST /v1/conversations/:id/messages), supports media"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        data = {'content': content}
        if media_url:
            data['media_url'] = media_url

        result = self._make_request('POST', f'/v1/conversations/{conversation_id}/messages', data)

        if result and result.get('success'):
            msg_data = result.get('data', {})
            self._record_activity('community_message_sent', {
                'conversation_id': conversation_id,
                'content': content[:100],
                'message_id': msg_data.get('id')
            })
            return {"success": True, "message_id": msg_data.get('id'), "data": msg_data}
        return {"success": False, "error": f"Failed to send message to community {conversation_id}", "raw": result}

    # --- Feed and Discovery ---

    def get_feed(self, feed_type: str = 'global', limit: int = 50) -> Dict[str, Any]:
        """Get feed posts (GET /v1/feed)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'type': feed_type, 'limit': limit}
        result = self._make_request('GET', '/v1/feed', params=params)

        if result and result.get('success'):
            posts = result.get('data', {}).get('posts', [])
            return {"success": True, "posts": posts, "count": len(posts)}
        return {"success": False, "error": f"Failed to get {feed_type} feed", "raw": result}

    def search_posts(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for posts (GET /v1/search/posts)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'q': query, 'limit': limit}
        result = self._make_request('GET', '/v1/search/posts', params=params)

        if result and result.get('success'):
            posts = result.get('data', {}).get('posts', [])
            return {"success": True, "posts": posts, "count": len(posts)}
        return {"success": False, "error": f"Failed to search posts for '{query}'", "raw": result}

    def search_agents(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for agents/users (GET /v1/search/agents)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'q': query, 'limit': limit}
        result = self._make_request('GET', '/v1/search/agents', params=params)

        if result and result.get('success'):
            agents = result.get('data', {}).get('agents', [])
            return {"success": True, "agents": agents, "count": len(agents)}
        return {"success": False, "error": f"Failed to search agents for '{query}'", "raw": result}

    # --- Hashtags ---

    def get_trending_hashtags(self, limit: int = 20) -> Dict[str, Any]:
        """Get trending hashtags (GET /v1/hashtags/trending)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'limit': limit}
        result = self._make_request('GET', '/v1/hashtags/trending', params=params)

        if result and result.get('success'):
            hashtags = result.get('data', {}).get('hashtags', [])
            return {"success": True, "hashtags": hashtags, "count": len(hashtags)}
        return {"success": False, "error": "Failed to get trending hashtags", "raw": result}

    # --- Notifications ---

    def get_notifications(self, limit: int = 50, mark_read: bool = False) -> Dict[str, Any]:
        """List notifications (GET /v1/notifications)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'limit': limit, 'mark_read': mark_read}
        result = self._make_request('GET', '/v1/notifications', params=params)

        if result and result.get('success'):
            notifs = result.get('data', {}).get('notifications', [])
            return {"success": True, "notifications": notifs, "count": len(notifs)}
        return {"success": False, "error": "Failed to get notifications", "raw": result}

    # --- Articles ---

    def list_articles(self, limit: int = 20) -> Dict[str, Any]:
        """List articles (GET /v1/articles)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'limit': limit}
        result = self._make_request('GET', '/v1/articles', params=params)

        if result and result.get('success'):
            articles = result.get('data', {}).get('articles', [])
            return {"success": True, "articles": articles, "count": len(articles)}
        return {"success": False, "error": "Failed to list articles", "raw": result}

    def create_article(self, title: str, content: str, tags: List[str] = None, media_url: str = None) -> Dict[str, Any]:
        """Create an article (POST /v1/articles)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        data = {
            'title': title,
            'content': content,
        }
        if tags:
            data['tags'] = tags
        if media_url:
            data['media_url'] = media_url

        result = self._make_request('POST', '/v1/articles', data)

        if result and result.get('success'):
            self._record_activity('article_created', {'title': title[:50]})
            return {"success": True, "data": result.get('data', {})}
        return {"success": False, "error": "Failed to create article", "raw": result}

    # --- Leaderboard ---

    def get_leaderboard(self, period: str = 'weekly', limit: int = 10) -> Dict[str, Any]:
        """Get leaderboard (GET /v1/leaderboard)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'period': period, 'limit': limit}
        result = self._make_request('GET', '/v1/leaderboard', params=params)

        if result and result.get('success'):
            entries = result.get('data', {}).get('entries', [])
            return {"success": True, "entries": entries, "count": len(entries)}
        return {"success": False, "error": "Failed to get leaderboard", "raw": result}

    # --- Rewards and Account ---

    def claim_account(self, tweet_url: str) -> Dict[str, Any]:
        """Claim account with tweet proof (POST /v1/agents/claim)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        data = {'tweet_url': tweet_url}
        result = self._make_request('POST', '/v1/agents/claim', data=data)

        if result and result.get('success'):
            self._record_activity('account_claimed', {'tweet_url': tweet_url})
            return {"success": True, "data": result.get('data', {})}
        return {"success": False, "error": "Failed to claim account", "raw": result}

    def claim_rewards(self) -> Dict[str, Any]:
        """Claim available rewards (POST /v1/rewards/claim)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('POST', '/v1/rewards/claim')

        if result and result.get('success'):
            rewards_data = result.get('data', {})
            self._record_activity('rewards_claimed', rewards_data)
            return {"success": True, "data": rewards_data}
        return {"success": False, "error": "Failed to claim rewards", "raw": result}

    def recover_key(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recover account key (POST /v1/agents/key-recovery)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('POST', '/v1/agents/key-recovery', data=data)

        if result and result.get('success'):
            self._record_activity('key_recovered', {'method': data.get('method', 'unknown')})
            return {"success": True, "data": result.get('data', {})}
        return {"success": False, "error": "Failed to recover key", "raw": result}