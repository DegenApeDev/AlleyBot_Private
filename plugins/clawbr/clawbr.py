"""
Clawbr Plugin - Social network for AI agents with debates and voting
Base URL: https://www.clawbr.org/api/v1
"""
import os
import json
import time
import hashlib
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from plugin_manager import AlleyBotPlugin

# Import mixins
from .clawbr_api import ClawbrAPIMixin
from .clawbr_content import ClawbrContentMixin
from .clawbr_engagement import ClawbrEngagementMixin
from .clawbr_commands import ClawbrCommandsMixin
from .clawbr_analytics import ClawbrDeepIntegrationMixin
from .clawbr_wallet import ClawbrWalletMixin


class ClawbrPlugin(AlleyBotPlugin, ClawbrAPIMixin, ClawbrContentMixin, ClawbrEngagementMixin, ClawbrCommandsMixin, ClawbrDeepIntegrationMixin, ClawbrWalletMixin):
    """Clawbr social network integration for AlleyBot"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = "https://www.clawbr.org/api/v1"
        self.api_key = os.getenv('CLAWBR_API_KEY')
        self.agent_name = config.get('agent_name', 'AlleyBot')
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': f'AlleyBot/{self.agent_name}'
        }
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
        
        # Cache for rate limiting
        self._last_request = 0
        self._request_cache = {}
    
    def initialize(self, api, core):
        """Initialize plugin with API and core access"""
        super().initialize(api, core)
        
        # Validate API key before proceeding
        if not self.api_key:
            print("❌ Clawbr API key not found in environment variables")
            print("   Please set CLAWBR_API_KEY in your .env file")
            return
            
        if not self.api_key.startswith('agnt_sk_'):
            print("⚠️ Clawbr API key format looks incorrect (should start with 'agnt_sk_')")
            print(f"   Current key: {self.api_key[:10]}...")
        
        # Test API connection
        print("🔍 Testing Clawbr API connection...")
        test_result = self.test_api_connection()
        if not test_result.get('success'):
            print(f"❌ Clawbr API connection failed: {test_result.get('error', 'Unknown error')}")
            if '403' in str(test_result.get('error', '')):
                print("   This usually means the API key is invalid or expired")
                print("   Get a new API key from https://www.clawbr.org")
        else:
            print("✅ Clawbr API connection successful")
        
        # Initialize mixins now that core is available
        self._init_clawbr_api()
        self._init_clawbr_content()
        self._init_clawbr_engagement()
        self._init_clawbr_deep_integration()
        
        print(f"✅ Clawbr plugin initialized (API key: {'✓' if self.api_key else '✗'})")
        
    def test_api_connection(self) -> Dict[str, Any]:
        """Test basic API connectivity"""
        try:
            # Try to get user profile as a basic connectivity test
            result = self._make_request('GET', '/agents/me')
            if result.get('success'):
                return {'success': True, 'message': 'API connection working'}
            else:
                return {
                    'success': False, 
                    'error': result.get('error', 'API request failed'),
                    'status': result.get('status')
                }
        except Exception as e:
            return {'success': False, 'error': f'Connection test failed: {str(e)}'}
    # =================================================================
    # Core API Methods
    # =================================================================
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Clawbr API"""
        import requests
        
        url = f"{self.base_url}{endpoint}"
        
        # Rate limiting: max 10 requests per second
        now = time.time()
        if now - self._last_request < 0.1:
            time.sleep(0.1)
        self._last_request = time.time()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, params=params, timeout=10)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=self.headers, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Log request for debugging
            print(f"🔗 {method} {url} -> {response.status_code}")
            
            if response.status_code == 409:
                try:
                    error_data = response.json()
                except Exception:
                    error_data = response.text
                return {'success': False, 'error': error_data, 'status': 409}

            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                data = response.json()
                if isinstance(data, dict) and 'success' not in data:
                    if 'error' in data or 'errors' in data:
                        data['success'] = False
                    else:
                        data['success'] = True
                return data
            except ValueError as json_error:
                # Handle malformed JSON responses
                print(f"⚠️ JSON parsing failed: {json_error}")
                print(f"⚠️ Response content (first 500 chars): {response.text[:500]}...")
                # Check if it's an HTML error page
                if '<html' in response.text.lower() or '<!doctype' in response.text.lower():
                    return {
                        'success': False, 
                        'error': 'API returned HTML error page instead of JSON', 
                        'status': response.status_code,
                        'response_preview': response.text[:200]
                    }
                else:
                    # Try to extract any JSON-like content
                    import re
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group())
                            data['success'] = False
                            return data
                        except:
                            pass
                    return {
                        'success': False, 
                        'error': f'Invalid JSON response: {str(json_error)}', 
                        'status': response.status_code,
                        'response_length': len(response.text)
                    }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Clawbr API error: {e}")
            error_info = {
                'success': False, 
                'error': str(e),
                'endpoint': endpoint,
                'method': method
            }
            
            if hasattr(e, 'response') and e.response is not None:
                error_info['status'] = e.response.status_code
                try:
                    # Try to parse error response as JSON
                    error_data = e.response.json()
                    error_info['error'] = error_data
                except ValueError:
                    # Handle non-JSON error responses (like HTML pages)
                    error_text = e.response.text
                    if '<html' in error_text.lower() or '<!doctype' in error_text.lower():
                        error_info['error'] = f'HTML error page (status {e.response.status_code})'
                        error_info['error_preview'] = error_text[:200]
                    else:
                        error_info['error'] = error_text[:500]
            return error_info
    
    # =================================================================
    # Identity & Profile
    # =================================================================
    
    # =================================================================
    # Identity & Profile
    # =================================================================
    
    def register_agent(self, display_name: str, description: str, 
                      avatar_url: Optional[str] = None, faction: str = "AI") -> Dict[str, Any]:
        """Register new agent and get API key"""
        data = {
            'name': self.agent_name,
            'displayName': display_name,
            'description': description,
            'faction': faction
        }
        if avatar_url:
            data['avatarUrl'] = avatar_url
            
        result = self._make_request('POST', '/agents/register', data)
        if result.get('success', True) and 'apiKey' in result:
            self.api_key = result['apiKey']
            self.headers['Authorization'] = f'Bearer {self.api_key}'
            print(f"✅ Registered {self.agent_name} on Clawbr")
        return result
    
    def get_profile(self) -> Dict[str, Any]:
        """Get agent profile"""
        return self._make_request('GET', '/agents/me')

    def verify_x_account(self, x_handle: Optional[str] = None, tweet_url: Optional[str] = None) -> Dict[str, Any]:
        """Verify X/Twitter account for Clawbr profile"""
        data = {}
        if x_handle:
            data['x_handle'] = x_handle
        if tweet_url:
            data['tweet_url'] = tweet_url
            
        return self._make_request('POST', '/agents/me/verify-x', data)

    def _get_clawbr_agent_id(self) -> Optional[str]:
        """Get cached Clawbr agent id for engagement logic"""
        if getattr(self, '_clawbr_agent_id', None):
            return self._clawbr_agent_id
        profile = self.get_profile()
        if profile.get('success', True):
            agent_id = profile.get('id') or profile.get('agentId')
            self._clawbr_agent_id = agent_id
            return agent_id
        return None
    
    def update_profile(self, display_name: Optional[str] = None, 
                      description: Optional[str] = None,
                      avatar_url: Optional[str] = None,
                      avatar_emoji: Optional[str] = None,
                      banner_url: Optional[str] = None,
                      faction: Optional[str] = None) -> Dict[str, Any]:
        """Update agent profile"""
        data = {}
        if display_name:
            data['displayName'] = display_name
        if description:
            data['description'] = description
        if avatar_url:
            data['avatarUrl'] = avatar_url
        if avatar_emoji:
            data['avatarEmoji'] = avatar_emoji
        if banner_url:
            data['bannerUrl'] = banner_url
        if faction:
            data['faction'] = faction
            
        return self._make_request('PATCH', '/agents/me', data)
    
    def get_agent_by_name(self, name: str) -> Dict[str, Any]:
        """Lookup agent by name"""
        return self._make_request('GET', f'/agents/{name}')
    
    # =================================================================
    # Posts & Content
    # =================================================================
    
    def create_post(self, content: str, parent_id: Optional[str] = None,
                   media_url: Optional[str] = None,
                   intent: str = "statement") -> Dict[str, Any]:
        """Create post or reply"""
        # Check voting eligibility before posting
        eligibility = self.check_voting_eligibility()
        if not eligibility.get('success', True):
            return {
                'success': False, 
                'error': f'Could not verify posting eligibility: {eligibility.get("error", "Unknown error")}'
            }
        
        if not eligibility.get('can_post', False):
            stats = eligibility.get('stats', {})
            return {
                'success': False,
                'error': f'Posting blocked - insufficient voting activity. {eligibility.get("message", "")}',
                'stats': stats,
                'solution': 'Vote on completed debates to maintain posting rights (1 vote per 5 posts required)'
            }
        
        data = {
            'content': content,
            'intent': intent  # question, statement, opinion, support, challenge
        }
        if parent_id:
            data['parentId'] = parent_id
        if media_url:
            data['media_url'] = media_url
            
        result = self._make_request('POST', '/posts', data)
        if result.get('success', True):
            post_id = result.get('id')
            print(f"✅ Created Clawbr post: {post_id}")
            self._record_activity('create_post', {
                'post_id': post_id,
                'content': content[:100] + '...' if len(content) > 100 else content,
                'intent': intent,
                'parent_id': parent_id
            })
        return result
    
    def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get post with replies"""
        return self._make_request('GET', f'/posts/{post_id}')
    
    def edit_post(self, post_id: str, content: str) -> Dict[str, Any]:
        """Edit your post"""
        return self._make_request('PATCH', f'/posts/{post_id}', {'content': content})
    
    def delete_post(self, post_id: str) -> Dict[str, Any]:
        """Delete your post"""
        result = self._make_request('DELETE', f'/posts/{post_id}')
        if result.get('success', True):
            print(f"🗑️  Deleted Clawbr post: {post_id}")
        return result
    
    def like_post(self, post_id: str) -> Dict[str, Any]:
        """Like a post"""
        result = self._make_request('POST', f'/posts/{post_id}/like')
        if not result.get('success', True):
            error = result.get('error')
            error_text = str(error).lower()
            if '409' in error_text or 'conflict' in error_text:
                return {'success': True, 'skipped': True, 'error': error}
        if result.get('success', True):
            print(f"❤️  Liked Clawbr post: {post_id}")
            self._record_activity('like_post', {'post_id': post_id})
        return result
    
    def unlike_post(self, post_id: str) -> Dict[str, Any]:
        """Unlike a post"""
        return self._make_request('DELETE', f'/posts/{post_id}/like')
    
    # =================================================================
    # Feeds
    # =================================================================
    
    def get_global_feed(self, sort: str = "recent", intent: Optional[str] = None,
                       limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get global feed"""
        params = {'sort': sort, 'limit': limit, 'offset': offset}
        if intent:
            params['intent'] = intent
        return self._make_request('GET', '/feed/global', params=params)
    
    def get_following_feed(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get feed from agents you follow"""
        params = {'limit': limit, 'offset': offset}
        return self._make_request('GET', '/feed/following', params=params)
    
    def get_mentions_feed(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get posts that mention you"""
        params = {'limit': limit, 'offset': offset}
        return self._make_request('GET', '/feed/mentions', params=params)
    
    # =================================================================
    # Social (Follow/Unfollow)
    # =================================================================
    
    def follow_agent(self, agent_name: str) -> Dict[str, Any]:
        """Follow an agent"""
        result = self._make_request('POST', f'/follow/{agent_name}')
        if result.get('success', True):
            print(f"👥 Following {agent_name} on Clawbr")
            self._record_activity('follow', {'agent_name': agent_name})
        return result
    
    def unfollow_agent(self, agent_name: str) -> Dict[str, Any]:
        """Unfollow an agent"""
        return self._make_request('DELETE', f'/follow/{agent_name}')
    
    # =================================================================
    # Notifications
    # =================================================================
    
    def get_notifications(self, unread_only: bool = False) -> Dict[str, Any]:
        """Get notifications"""
        params = {'unread': 'true'} if unread_only else {}
        return self._make_request('GET', '/notifications', params=params)
    
    def get_unread_count(self) -> Dict[str, Any]:
        """Get unread notification count"""
        return self._make_request('GET', '/notifications/unread_count')
    
    def mark_notifications_read(self, notification_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Mark notifications as read"""
        data = {}
        if notification_ids:
            data['ids'] = notification_ids
        return self._make_request('POST', '/notifications/read', data)
    
    # =================================================================
    # Debates
    # =================================================================
    
    def get_debates_hub(self) -> Dict[str, Any]:
        """Get debates hub with available actions"""
        return self._make_request('GET', '/debates/hub')
    
    def get_debate_hub(self) -> Dict[str, Any]:
        """Alias for get_debates_hub for backward compatibility"""
        return self.get_debates_hub()
    
    def get_my_debates(self) -> Dict[str, Any]:
        """Get your debates with turn status"""
        return self._make_request('GET', '/agents/me/debates')
    
    def create_debate(self, topic: str, opening_argument: str,
                     category: Optional[str] = None,
                     opponent_id: Optional[str] = None,
                     max_posts: int = 5) -> Dict[str, Any]:
        """Create a new debate"""
        if not topic or len(topic) < 10:
            return {'success': False, 'error': 'Topic must be at least 10 characters'}
        if not opening_argument:
            return {'success': False, 'error': 'Opening argument is required'}
        if len(opening_argument) > 1200:
            opening_argument = opening_argument[:1200]
        data = {
            'topic': topic,
            'opening_argument': opening_argument,
            'max_posts': max_posts
        }
        if category:
            data['category'] = category
        if opponent_id:
            data['opponent_id'] = opponent_id
            
        result = self._make_request('POST', '/debates', data)
        if result.get('success', True):
            debate_slug = result.get('slug')
            print(f"🎭 Created debate: {topic} ({debate_slug})")
            self._record_activity('create_debate', {
                'slug': debate_slug,
                'topic': topic,
                'category': category
            })
            if debate_slug:
                try:
                    debate = self.get_debate(debate_slug)
                    debate_payload = debate.get('data') if isinstance(debate, dict) and 'data' in debate else debate
                    self._auto_follow_debate_opponent(debate_payload)
                except Exception as e:
                    print(f"⚠️  Auto-follow failed for debate {debate_slug}: {e}")
        return result
    
    def get_debate(self, slug: str) -> Dict[str, Any]:
        """Get full debate details"""
        return self._make_request('GET', f'/debates/{slug}')
    
    def join_debate(self, slug: str) -> Dict[str, Any]:
        """Join an open debate"""
        result = self._make_request('POST', f'/debates/{slug}/join')
        if result.get('success', True):
            print(f"🤝 Joined debate: {slug}")
            self._record_activity('join_debate', {'slug': slug})
            try:
                debate = self.get_debate(slug)
                debate_payload = debate.get('data') if isinstance(debate, dict) and 'data' in debate else debate
                self._auto_follow_debate_opponent(debate_payload)
            except Exception as e:
                print(f"⚠️  Auto-follow failed for debate {slug}: {e}")
        return result

    def _auto_follow_debate_opponent(self, debate: Optional[Dict[str, Any]]):
        """Follow the other participant in a debate if possible."""
        if not debate or not isinstance(debate, dict):
            return

        agent_id = self._get_clawbr_agent_id()
        challenger_id = debate.get('challengerId')
        opponent_id = debate.get('opponentId')

        opponent_name = None
        if agent_id and challenger_id == agent_id:
            opponent_name = (
                (debate.get('opponent') or {}).get('name')
                or (debate.get('opponent') or {}).get('username')
                or debate.get('opponentName')
            )
        elif agent_id and opponent_id == agent_id:
            opponent_name = (
                (debate.get('challenger') or {}).get('name')
                or (debate.get('challenger') or {}).get('username')
                or debate.get('challengerName')
            )

        if not opponent_name:
            return

        try:
            if hasattr(self, 'follow_user'):
                self.follow_user(opponent_name)
            else:
                self.follow_agent(opponent_name)
        except Exception as e:
            print(f"⚠️  Auto-follow failed for @{opponent_name}: {e}")
    
    def submit_debate_argument(self, slug: str, argument: str) -> Dict[str, Any]:
        """Submit argument for your turn in debate"""
        if not argument:
            return {'success': False, 'error': 'Argument content is required'}
        argument = self._trim_debate_argument(argument, max_len=750)
        data = {'content': argument}
        result = self._make_request('POST', f'/debates/{slug}/posts', data)
        if result.get('success', True):
            print(f"💬 Submitted argument for debate: {slug}")
            self._record_activity('debate_argument', {'slug': slug, 'argument': argument[:100]})
        return result

    def _trim_debate_argument(self, argument: str, max_len: int = 750) -> str:
        """Trim debate text without cutting off mid-sentence."""
        text = (argument or "").strip()
        if len(text) <= max_len:
            return text

        trimmed = text[:max_len].rstrip()
        last_sentence = max(trimmed.rfind('.'), trimmed.rfind('!'), trimmed.rfind('?'))
        if last_sentence > max_len * 0.6:
            return trimmed[:last_sentence + 1].rstrip()

        last_space = trimmed.rfind(' ')
        if last_space > max_len * 0.6:
            return trimmed[:last_space].rstrip() + "…"

        return trimmed.rstrip() + "…"
    
    def vote_debate(self, slug: str, side: str, vote_reason: str) -> Dict[str, Any]:
        """Vote on a debate (side: challenger/opponent)"""
        data = {
            'side': side,
            'content': vote_reason
        }
        result = self._make_request('POST', f'/debates/{slug}/vote', data)
        if result.get('success', True):
            print(f"🗳️  Voted on debate: {slug} ({side})")
            self._record_activity('debate_vote', {'slug': slug, 'side': side})
        return result
    
    def forfeit_debate(self, slug: str) -> Dict[str, Any]:
        """Forfeit a debate (you lose, -50 ELO)"""
        return self._make_request('POST', f'/debates/{slug}/forfeit')
    
    def get_completed_debates(self, limit: int = 20) -> Dict[str, Any]:
        """Get completed debates that can be voted on"""
        params = {'status': 'completed', 'limit': limit}
        return self._make_request('GET', '/debates', params=params)
    
    def vote_debate(self, slug: str, side: str, reasoning: str) -> Dict[str, Any]:
        """Vote on a completed debate"""
        if side not in ['challenger', 'opponent']:
            return {'success': False, 'error': 'Side must be "challenger" or "opponent"'}
        if len(reasoning) < 100:
            return {'success': False, 'error': 'Voting reasoning must be 100+ characters'}
            
        data = {
            'side': side,
            'content': reasoning
        }
        result = self._make_request('POST', f'/debates/{slug}/vote', data)
        if result.get('success', True):
            print(f"🗳️  Voted on debate {slug} ({side})")
            self._record_activity('vote_debate', {'slug': slug, 'side': side})
        return result
    
    # =================================================================
    # Search & Discovery
    # =================================================================
    
    def search_agents(self, query: str) -> Dict[str, Any]:
        """Search for agents"""
        return self._make_request('GET', '/search/agents', params={'q': query})
    
    def search_posts(self, query: str) -> Dict[str, Any]:
        """Search for posts"""
        return self._make_request('GET', '/search/posts', params={'q': query})
    
    def get_trending_hashtags(self, days: int = 7, limit: int = 20) -> Dict[str, Any]:
        """Get trending hashtags"""
        params = {'days': days, 'limit': limit}
        return self._make_request('GET', '/hashtags/trending', params=params)
    
    # =================================================================
    # Leaderboard
    # =================================================================
    
    def get_leaderboard(self) -> Dict[str, Any]:
        """Get influence score leaderboard"""
        return self._make_request('GET', '/leaderboard')
    
    def get_debate_leaderboard(self) -> Dict[str, Any]:
        """Get debate ELO leaderboard"""
        return self._make_request('GET', '/leaderboard/debates')
    
    # =================================================================
    # Utilities
    # =================================================================
    
    def get_platform_stats(self) -> Dict[str, Any]:
        """Get platform-wide statistics"""
        return self._make_request('GET', '/stats')
    
    def validate_post(self, content: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Dry-run post validation without saving"""
        data = {'content': content}
        if parent_id:
            data['parentId'] = parent_id
        return self._make_request('POST', '/debug/echo', data)
    
    def check_voting_eligibility(self) -> Dict[str, Any]:
        """Check if AlleyBot has sufficient voting activity to post"""
        try:
            # Get user profile to check voting stats
            profile = self.get_profile()
            if not profile.get('success', True):
                return {'success': False, 'error': 'Could not get profile', 'can_post': False}
            
            # Check recent voting activity from memory
            activities = self.core.get_memory('clawbr_activities') or []
            recent_votes = [
                act for act in activities 
                if act.get('type') == 'debate_vote' and 
                act.get('timestamp') and 
                self._is_recent_activity(act['timestamp'], hours=24)
            ]
            
            # Get total posts and votes ratio
            total_posts = len([act for act in activities if act.get('type') == 'create_post'])
            total_votes = len([act for act in activities if act.get('type') == 'debate_vote'])
            
            # Clawbr requires roughly 1 vote per 5 posts
            required_votes = max(1, total_posts // 5)
            has_sufficient_votes = total_votes >= required_votes
            
            result = {
                'success': True,
                'can_post': has_sufficient_votes,
                'stats': {
                    'total_posts': total_posts,
                    'total_votes': total_votes,
                    'recent_votes_24h': len(recent_votes),
                    'required_votes': required_votes,
                    'voting_ratio': f"{total_votes}/{required_votes}" if total_votes >= required_votes else f"{total_votes}/{required_votes} (NEED MORE)"
                }
            }
            
            if not has_sufficient_votes:
                result['message'] = f"Need {required_votes - total_votes} more votes to maintain posting rights (1 vote per 5 posts)"
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'can_post': False}
    
    def _is_recent_activity(self, timestamp_str: str, hours: int = 24) -> bool:
        """Check if activity timestamp is within the last N hours"""
        try:
            from datetime import datetime, timedelta
            activity_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            cutoff_time = datetime.now() - timedelta(hours=hours)
            return activity_time > cutoff_time
        except:
            return False

    def register_tournament(self, slug: str) -> Dict[str, Any]:
        """Register for a tournament by slug"""
        if not slug:
            return {'success': False, 'error': 'Tournament slug is required'}
            
        result = self._make_request('POST', f'/tournaments/{slug}/register')
        if result.get('success', True):
            print(f"🏆 Registered for tournament: {slug}")
            self._record_activity('register_tournament', {'slug': slug})
        return result

    def _record_activity(self, activity_type: str, data: Dict):
        """Record Clawbr activity in memory"""
        activities = self.core.get_memory('clawbr_activities') or []
        activities.append({
            'type': activity_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        self.core.save_memory('clawbr_activities', activities[-100:])

    # =================================================================
    # Command Wrappers (defensive)
    # =================================================================

    def clawbr_status_command(self) -> str:
        """Show Clawbr plugin status (defensive wrapper)."""
        return ClawbrCommandsMixin.clawbr_status_command(self)

    def clawbr_post_command(self, *args) -> str:
        """Create a post on Clawbr (defensive wrapper)."""
        return ClawbrCommandsMixin.clawbr_post_command(self, *args)

    def clawbr_reply_command(self, *args) -> str:
        """Reply to a specific post on Clawbr (defensive wrapper)."""
        return ClawbrCommandsMixin.clawbr_reply_command(self, *args)

    def clawbr_feed_command(self) -> str:
        """Get Clawbr global feed (defensive wrapper)."""
        return ClawbrCommandsMixin.clawbr_feed_command(self)

    def clawbr_join_debate_command(self, *args) -> str:
        """Join a debate by slug (defensive wrapper)."""
        return ClawbrCommandsMixin.clawbr_join_debate_command(self, *args)

    def clawbr_leaderboard_command(self) -> str:
        """Get Clawbr influence leaderboard (defensive wrapper)."""
        return ClawbrCommandsMixin.clawbr_leaderboard_command(self)

    def clawbr_search_command(self, *args) -> str:
        """Search for agents or posts (defensive wrapper)."""
        return ClawbrCommandsMixin.clawbr_search_command(self, *args)

    def clawbr_analyze_command(self, *args) -> str:
        """Analyze recent debate performance and provide recommendations (defensive wrapper)."""
        return ClawbrCommandsMixin.clawbr_analyze_command(self, *args)

    def clawbr_strategy_command(self) -> str:
        """Get Clawbr debate strategy advice (defensive wrapper)."""
        return ClawbrCommandsMixin.clawbr_strategy_command(self)

    def clawbr_stats_command(self) -> str:
        """Get Clawbr platform stats (defensive wrapper)."""
        return ClawbrCommandsMixin.clawbr_stats_command(self)

    def clawbr_debates_command(self) -> str:
        """Show debate hub and available debates (defensive wrapper)."""
        return ClawbrCommandsMixin.clawbr_debates_command(self)

    def clawbr_create_debate_command(self, *args) -> str:
        """Create a new debate (defensive wrapper)."""
        return ClawbrCommandsMixin.clawbr_create_debate_command(self, *args)
    
    # =================================================================
    # Plugin Commands
    # =================================================================
    
    def get_commands(self) -> Dict[str, Any]:
        """Return list of available commands"""
        return {
            'clawbr_status': self.clawbr_status_command,
            'clawbr_post': self.clawbr_post_command,
            'clawbr_reply': self.clawbr_reply_command,
            'clawbr_feed': self.clawbr_feed_command,
            'clawbr_debates': self.clawbr_debates_command,
            'clawbr_create_debate': self.clawbr_create_debate_command,
            'clawbr_join_debate': self.clawbr_join_debate_command,
            'clawbr_vote': self.clawbr_vote_command,
            'clawbr_vote_specific': self.clawbr_vote_specific_command,
            'clawbr_check_voting': self.clawbr_check_voting_command,
            'clawbr_completed_debates': self.clawbr_completed_debates_command,
            'clawbr_leaderboard': self.clawbr_leaderboard_command,
            'clawbr_search': self.clawbr_search_command,
            'clawbr_stats': self.clawbr_stats_command,
            'clawbr_analyze': self.clawbr_analyze_command,
            'clawbr_strategy': self.clawbr_strategy_command,
            'clawbr_verify_x': self.clawbr_verify_x_command,
            'clawbr_register_tournament': self.clawbr_register_tournament_command,
            'clawbr_engage': self.run_engagement_cycle,
            # Wallet and Token Commands
            'clawbr_generate_wallet': self.clawbr_generate_wallet_command,
            'clawbr_verify_wallet': self.clawbr_verify_wallet_command,
            'clawbr_balance': self.clawbr_balance_command,
            'clawbr_claim': self.clawbr_claim_command,
            'clawbr_transfer': self.clawbr_transfer_command,
            'clawbr_auto_claim': self.clawbr_auto_claim_command,
            'clawbr_claim_status': self.clawbr_claim_status_command,
            'clawbr_token_tx': self.clawbr_token_tx_command,
            # Phase 11: Deep Integration
            'clawbr_analytics': self.clawbr_analytics_command,
            'clawbr_turns': self.clawbr_turns_command,
            'clawbr_remind': self.clawbr_remind_command,
        }
    
    def clawbr_analytics_command(self) -> str:
        """Get Clawbr debate analytics (wrapper)"""
        try:
            result = self.get_debate_performance_analytics()
            if isinstance(result, dict):
                active = result.get('active_debates', 0)
                return f"🎭 Clawbr Analytics: {active} active debates"
            return "❌ Failed to get analytics"
        except Exception as e:
            return f"❌ Analytics error: {e}"
    
    def clawbr_strategy_command(self) -> str:
        """Get Clawbr debate strategy advice"""
        return "🎯 Strategy: Focus on tech/AI debates for maximum influence"
    
    def clawbr_turns_command(self) -> str:
        """Check debate turns requiring action"""
        try:
            result = self.send_debate_reminders()
            if isinstance(result, dict):
                turns = result.get('turns_taken', 0)
                return f"🎭 Debate Turns: {turns} turns taken"
            return "❌ Failed to check turns"
        except Exception as e:
            return f"❌ Turns check error: {e}"
    
    def clawbr_remind_command(self) -> str:
        """Send debate reminders"""
        return self.clawbr_turns_command()

    def send_debate_reminders(self):
        """Send debate turn reminders (called by scheduled task)"""
        try:
            result = self._check_debate_turns()
            if result and result.get('turns_taken', 0) > 0:
                print(f"🎭 Debate reminders sent - {result['turns_taken']} turns taken")
            else:
                print("🎭 Debate reminders checked - no action needed")
            return result
        except Exception as e:
            print(f"❌ Error sending debate reminders: {e}")
            return {'success': False, 'error': str(e)}
    
    def clawbr_verify_x_command(self, *args):
        """Handle X/Twitter verification command"""
        try:
            # Placeholder implementation for X/Twitter verification
            # This would need actual implementation for verifying X accounts
            return "🔗 X/Twitter verification feature coming soon! This will help verify user accounts for enhanced security."
        except Exception as e:
            return f"❌ Error in X verification: {e}"
    
    # Command implementations would go here...
    # For now, the plugin provides the API methods that can be called
    # from the autonomous system or other plugins
