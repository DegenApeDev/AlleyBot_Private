"""
Moltbook API Mixin
API client, feed fetching, upvoting, commenting, and post management.
Includes suspension detection and verification challenge handling.
"""
import os
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta


class MoltbookAPIClient:
    """Standalone API client for Moltbook platform with suspension awareness"""

    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        # Suspension tracking
        self.is_suspended = False
        self.suspension_reason = None
        self.suspension_ends_at = None
        self.offense_count = 0

    def _check_for_suspension(self, response):
        """Check if response indicates suspension and update state"""
        if response.status_code == 401:
            try:
                data = response.json()
                error = data.get('error', '').lower()
                hint = data.get('hint', '').lower()
                
                if 'suspended' in error or 'suspended' in hint:
                    self.is_suspended = True
                    self.suspension_reason = data.get('hint', 'Account suspended')
                    
                    # Parse suspension duration if available
                    if '1 week' in hint or '1week' in hint:
                        self.suspension_ends_at = datetime.now() + timedelta(days=7)
                    elif '1 hour' in hint:
                        self.suspension_ends_at = datetime.now() + timedelta(hours=1)
                    elif 'ends in' in hint:
                        # Try to extract time info
                        import re
                        time_match = re.search(r'(\d+)\s*(hour|day|week)', hint)
                        if time_match:
                            amount, unit = int(time_match.group(1)), time_match.group(2)
                            if unit == 'hour':
                                self.suspension_ends_at = datetime.now() + timedelta(hours=amount)
                            elif unit == 'day':
                                self.suspension_ends_at = datetime.now() + timedelta(days=amount)
                            elif unit == 'week':
                                self.suspension_ends_at = datetime.now() + timedelta(weeks=amount)
                    
                    print(f"🚫 MOLTBOOK SUSPENSION DETECTED")
                    print(f"   Reason: {self.suspension_reason}")
                    if self.suspension_ends_at:
                        print(f"   Ends: {self.suspension_ends_at.isoformat()}")
                    
                    # Track offense count
                    if 'offense' in hint:
                        import re
                        offense_match = re.search(r'offense\s*#?(\d+)', hint)
                        if offense_match:
                            self.offense_count = int(offense_match.group(1))
                    
                    return True
                    
            except Exception:
                pass
        return False

    def _check_for_verification_challenge(self, response):
        """Check if response indicates a verification challenge is required"""
        if response.status_code in [401, 403, 429]:
            try:
                data = response.json()
                hint = data.get('hint', '').lower()
                error = data.get('error', '').lower()
                
                challenge_indicators = [
                    'verification', 'challenge', 'captcha', 'human',
                    'verify', 'proof', 'ai verification'
                ]
                
                if any(ind in hint for ind in challenge_indicators) or \
                   any(ind in error for ind in challenge_indicators):
                    print(f"🚨 MOLTBOOK VERIFICATION CHALLENGE DETECTED")
                    print(f"   Response: {response.text[:200]}")
                    print(f"   🛑 HALTING ALL MOLTBOOK ACTIVITY - HUMAN INTERVENTION REQUIRED")
                    return True
                    
            except Exception:
                pass
        return False

    def check_suspension_status(self):
        """Check if suspension has expired and reset state if so"""
        if self.is_suspended and self.suspension_ends_at:
            if datetime.now() >= self.suspension_ends_at:
                print(f"✅ Moltbook suspension expired - resuming activity")
                self.is_suspended = False
                self.suspension_reason = None
                self.suspension_ends_at = None
                return False  # No longer suspended
        return self.is_suspended

    def can_perform_action(self, action_type='post'):
        """Check if an action can be performed (not suspended)"""
        # First check if suspension expired
        self.check_suspension_status()
        
        if self.is_suspended:
            remaining = ""
            if self.suspension_ends_at:
                remaining_seconds = (self.suspension_ends_at - datetime.now()).total_seconds()
                if remaining_seconds > 0:
                    hours = int(remaining_seconds / 3600)
                    days = int(remaining_seconds / 86400)
                    if days > 0:
                        remaining = f" ({days} days remaining)"
                    else:
                        remaining = f" ({hours} hours remaining)"
            
            print(f"⛔ Moltbook action blocked: Account suspended{remaining}")
            print(f"   Reason: {self.suspension_reason}")
            return False
        return True

    def create_post(self, submolt, title, content=None, url=None):
        """Create a post with suspension checking"""
        if not self.can_perform_action('post'):
            return {'error': 'Account suspended', 'suspended': True, 
                    'reason': self.suspension_reason, 'ends_at': self.suspension_ends_at.isoformat() if self.suspension_ends_at else None}
        
        data = {'submolt': submolt, 'title': title}
        if content:
            data['content'] = content
        if url:
            data['url'] = url

        try:
            response = self.session.post(f"{self.base_url}/posts", json=data)
            print(f"MoltBook API Response: Status {response.status_code}")
            print(f"Full Response body: {response.text}")

            # Check for suspension or challenges
            if self._check_for_suspension(response):
                return {'error': 'Account suspended', 'suspended': True,
                        'reason': self.suspension_reason, 'ends_at': self.suspension_ends_at.isoformat() if self.suspension_ends_at else None}
            
            if self._check_for_verification_challenge(response):
                return {'error': 'Verification challenge required', 'challenge_required': True,
                        'reason': 'Human verification needed - automation halted'}

            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"❌ MoltBook API error: {response.status_code} - {response.text}")
                return {'error': f"Status {response.status_code}", 'message': response.text}
        except Exception as e:
            print(f"❌ MoltBook API exception: {e}")
            return {'error': str(e)}

    def get_feed(self, sort='hot', limit=25):
        """Get feed (allowed even when suspended for monitoring)"""
        params = {'sort': sort, 'limit': limit}
        response = self.session.get(f"{self.base_url}/posts", params=params)
        # Check for suspension even on GET requests
        if response.status_code == 401:
            self._check_for_suspension(response)
        return response.json() if response.status_code == 200 else None

    def upvote_post(self, post_id):
        """Upvote a post with suspension check"""
        if not self.can_perform_action('upvote'):
            return {'error': 'Account suspended', 'suspended': True}
        response = self.session.post(f"{self.base_url}/posts/{post_id}/upvote")
        if self._check_for_suspension(response):
            return {'error': 'Account suspended', 'suspended': True}
        return response.json() if response.status_code == 200 else None

    def add_comment(self, post_id, content):
        """Add a comment with suspension check"""
        if not self.can_perform_action('comment'):
            return {'error': 'Account suspended', 'suspended': True}
        data = {'content': content.strip()}
        response = self.session.post(f"{self.base_url}/posts/{post_id}/comments", json=data)
        if self._check_for_suspension(response):
            return {'error': 'Account suspended', 'suspended': True}
        if self._check_for_verification_challenge(response):
            return {'error': 'Verification challenge required', 'challenge_required': True}
        return response.json() if response.status_code in [200, 201] else None

    def get_post(self, post_id):
        """Get a single post by ID"""
        response = self.session.get(f"{self.base_url}/posts/{post_id}")
        return response.json() if response.status_code == 200 else None

    def delete_post(self, post_id):
        """Delete a post by ID"""
        response = self.session.delete(f"{self.base_url}/posts/{post_id}")
        return response.json() if response.status_code == 200 else None

    def downvote_post(self, post_id):
        """Downvote a post"""
        response = self.session.post(f"{self.base_url}/posts/{post_id}/downvote")
        return response.json() if response.status_code == 200 else None

    def upvote_comment(self, comment_id):
        """Upvote a comment"""
        response = self.session.post(f"{self.base_url}/comments/{comment_id}/upvote")
        return response.json() if response.status_code == 200 else None

    def reply_to_comment(self, post_id, parent_id, content):
        """Reply to a specific comment (nested comment)"""
        data = {'content': content.strip(), 'parent_id': parent_id}
        response = self.session.post(f"{self.base_url}/posts/{post_id}/comments", json=data)
        return response.json() if response.status_code in [200, 201] else None

    # --- Following ---

    def follow_agent(self, agent_name):
        """Follow another molty"""
        response = self.session.post(f"{self.base_url}/agents/{agent_name}/follow")
        return response.json() if response.status_code == 200 else None

    def unfollow_agent(self, agent_name):
        """Unfollow a molty"""
        response = self.session.delete(f"{self.base_url}/agents/{agent_name}/follow")
        return response.json() if response.status_code == 200 else None

    # --- Submolts ---

    def list_submolts(self):
        """List all submolts"""
        response = self.session.get(f"{self.base_url}/submolts")
        return response.json() if response.status_code == 200 else None

    def get_submolt(self, name):
        """Get submolt info"""
        response = self.session.get(f"{self.base_url}/submolts/{name}")
        return response.json() if response.status_code == 200 else None

    def create_submolt(self, name, display_name, description):
        """Create a new submolt"""
        data = {'name': name, 'display_name': display_name, 'description': description}
        response = self.session.post(f"{self.base_url}/submolts", json=data)
        return response.json() if response.status_code in [200, 201] else None

    def subscribe_submolt(self, name):
        """Subscribe to a submolt"""
        response = self.session.post(f"{self.base_url}/submolts/{name}/subscribe")
        return response.json() if response.status_code == 200 else None

    def unsubscribe_submolt(self, name):
        """Unsubscribe from a submolt"""
        response = self.session.delete(f"{self.base_url}/submolts/{name}/subscribe")
        return response.json() if response.status_code == 200 else None

    def get_submolt_feed(self, name, sort='new'):
        """Get posts from a specific submolt"""
        response = self.session.get(f"{self.base_url}/submolts/{name}/feed", params={'sort': sort})
        return response.json() if response.status_code == 200 else None

    # --- Feed ---

    def get_personalized_feed(self, sort='hot', limit=25):
        """Get personalized feed (subscribed submolts + followed moltys)"""
        params = {'sort': sort, 'limit': limit}
        response = self.session.get(f"{self.base_url}/feed", params=params)
        return response.json() if response.status_code == 200 else None

    # --- Search ---

    def semantic_search(self, query, search_type='all', limit=20):
        """AI-powered semantic search for posts and comments"""
        params = {'q': query, 'type': search_type, 'limit': limit}
        response = self.session.get(f"{self.base_url}/search", params=params)
        return response.json() if response.status_code == 200 else None

    # --- Profile ---

    def get_profile(self):
        """Get own profile"""
        response = self.session.get(f"{self.base_url}/agents/me")
        return response.json() if response.status_code == 200 else None

    def get_agent_profile(self, agent_name):
        """View another molty's profile"""
        response = self.session.get(f"{self.base_url}/agents/profile", params={'name': agent_name})
        return response.json() if response.status_code == 200 else None

    def update_profile(self, description=None, metadata=None):
        """Update profile (PATCH, not PUT)"""
        data = {}
        if description is not None:
            data['description'] = description
        if metadata is not None:
            data['metadata'] = metadata
        response = self.session.patch(f"{self.base_url}/agents/me", json=data)
        return response.json() if response.status_code == 200 else None

    def upload_avatar(self, file_path):
        """Upload avatar image. Max 1MB. Formats: JPEG, PNG, GIF, WebP."""
        file_path = Path(file_path)
        if not file_path.exists():
            return {'error': f'File not found: {file_path}'}

        # Use a separate request without Content-Type: application/json
        headers = {'Authorization': f'Bearer {self.api_key}'}
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'image/jpeg')}
            response = requests.post(
                f"{self.base_url}/agents/me/avatar",
                headers=headers,
                files=files
            )
        return response.json() if response.status_code == 200 else {'error': response.text, 'status': response.status_code}

    def remove_avatar(self):
        """Remove avatar"""
        response = self.session.delete(f"{self.base_url}/agents/me/avatar")
        return response.json() if response.status_code == 200 else None

    def get_stats(self):
        """Get user stats including karma"""
        response = self.session.get(f"{self.base_url}/user/stats")
        return response.json() if response.status_code == 200 else {'karma': 0}

    def check_claim_status(self):
        """Check if agent is claimed"""
        response = self.session.get(f"{self.base_url}/agents/status")
        return response.json() if response.status_code == 200 else None


class MoltbookAPIMixin:
    """Mixin providing API client initialization and low-level helpers"""

    def _init_moltbook_api(self):
        """Initialize MoltbookAPI client"""
        if self.api_key:
            self.mb_api = MoltbookAPIClient(self.api_key, self.base_url)
        else:
            self.mb_api = None

    def _get_feed_posts(self):
        """Get recent posts from Moltbook feed"""
        try:
            response = self.mb_api.session.get(f"{self.mb_api.base_url}/posts?limit=20")

            if response.status_code == 200:
                posts_data = response.json()
                posts = []

                for post in posts_data.get('posts', []):
                    posts.append({
                        'id': post.get('id'),
                        'title': post.get('title', 'No title'),
                        'content': post.get('content', ''),
                        'author': post.get('author', 'Anonymous'),
                        'upvotes': post.get('upvotes', 0),
                        'comments': post.get('comments_count', 0),
                        'timestamp': post.get('created_at', '2026-02-01T00:00:00Z')
                    })

                print(f"📱 Retrieved {len(posts)} posts from Moltbook API")
                return posts
            else:
                print(f"❌ Failed to fetch posts: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Error fetching posts from API: {e}")
            return []

    def _get_post_comments(self, post_id):
        """Get comments for a specific post from Moltbook API"""
        try:
            response = self.mb_api.session.get(f"{self.mb_api.base_url}/posts/{post_id}/comments")

            if response.status_code == 200:
                comments_data = response.json()
                comments = []

                for comment in comments_data.get('comments', []):
                    comments.append({
                        'id': comment.get('id'),
                        'author': comment.get('author', 'Anonymous'),
                        'content': comment.get('content', ''),
                        'timestamp': comment.get('created_at', '2026-02-01T00:00:00Z'),
                        'upvotes': comment.get('upvotes', 0)
                    })

                return comments
            else:
                print(f"❌ Failed to fetch comments: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Error fetching comments: {e}")
            return []

    def _upvote_post(self, post_id):
        """Upvote a post"""
        try:
            print(f"👍 Upvoting post {post_id}")
            return True

        except Exception as e:
            print(f"❌ Error upvoting post: {e}")
            return False

    def _notify_brain_tracker(self, post_id, platform, content):
        """Notify the brain's feedback loop to track this post's engagement"""
        try:
            brain = self.core.plugin_manager.plugins.get('brain')
            if brain and hasattr(brain, 'track_post'):
                brain.track_post(post_id, platform, content, source='plugin')
        except Exception as e:
            print(f"⚠️  Brain tracker notify failed: {e}")

    def _record_post(self, post, post_id):
        """Record post in memory"""
        try:
            import datetime
            posts = self.core.get_memory('moltbook_recent_posts') or []
            posts.append({
                'post_id': post_id,
                'title': post.get('title', ''),
                'content': post.get('content', ''),
                'tags': post.get('tags', []),
                'timestamp': datetime.datetime.now().isoformat(),
                'platform': 'moltbook',
                'source': post.get('source', 'command'),
                'type': post.get('type', 'regular')
            })
            self.core.save_memory('moltbook_recent_posts', posts[-50:])
        except Exception as e:
            print(f"⚠️  Failed to record post in memory: {e}")

    def delete_post_command(self, post_id):
        """Delete a Moltbook post by ID"""
        try:
            if not post_id:
                return "❌ Please provide a post ID. Usage: moltbook_delete <post_id>"

            print(f"🗑️ Deleting Moltbook post {post_id}...")

            result = self.mb_api.delete_post(post_id)

            if result and result.get('success'):
                print(f"✅ Moltbook post deleted: {post_id}")

                recent_posts = self.core.get_memory('moltbook_recent_posts') or []
                recent_posts = [p for p in recent_posts if p.get('post_id') != post_id]
                self.core.save_memory('moltbook_recent_posts', recent_posts)

                return f"✅ Moltbook post deleted successfully: {post_id}"
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No response'
                print(f"❌ Failed to delete Moltbook post: {error_msg}")
                return f"❌ Failed to delete Moltbook post: {error_msg}"

        except Exception as e:
            error_str = str(e)
            if "404" in error_str or "not found" in error_str.lower():
                return f"❌ Post not found: {post_id}"
            elif "403" in error_str or "forbidden" in error_str.lower():
                return f"❌ Permission denied: You can only delete your own posts"
            else:
                print(f"❌ Error deleting post: {e}")
                return f"❌ Error deleting post: {e}"

    def list_recent_posts(self):
        """List recent posts with IDs for deletion"""
        try:
            recent_posts = self.core.get_memory('moltbook_recent_posts') or []

            if not recent_posts:
                return "📭 No recent posts found"

            output = "📝 Recent Moltbook Posts:\n\n"

            for i, post in enumerate(reversed(recent_posts[-10:]), 1):
                post_id = post.get('post_id', 'unknown')
                title = post.get('title', 'No title')[:50]
                timestamp = post.get('timestamp', 'Unknown time')

                output += f"{i}. 📄 {title}...\n"
                output += f"   🆔 ID: {post_id}\n"
                output += f"   ⏰ {timestamp}\n\n"

            output += "💡 Use: moltbook_delete <post_id> to delete a post"

            return output

        except Exception as e:
            print(f"❌ Error listing posts: {e}")
            return f"❌ Error listing posts: {e}"
