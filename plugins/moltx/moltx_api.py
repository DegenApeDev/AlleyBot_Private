"""
Moltx API Client Mixin
Core API communication, credentials management, registration, profile, and media uploads.
"""
import json
import os
import requests
from datetime import datetime
from pathlib import Path


class MoltxAPIMixin:
    """Mixin providing core Moltx API client functionality"""

    def __init__(self, *args, **kwargs):
        """Initialize mixin - accepts any args/kwargs for cooperative inheritance"""
        super().__init__(*args, **kwargs)

    def _init_api(self, api_key):
        """Initialize API-related attributes"""
        self.base_url = "https://moltx.io/v1"
        self.api_key = api_key
        self.agent_name = None
        self.agent_id = None
        self.claim_status = None
        self.credentials_file = Path.home() / ".agents" / "moltx" / "config.json"
        self.initialized = False

    def _init_api_connection(self):
        """Initialize API connection from environment or credentials"""
        if self.api_key:
            print("✅ Moltx API key loaded from environment")
            self.initialized = True
            self._load_credentials()
        else:
            self._load_credentials()
            if not self.api_key:
                print("🔑 No Moltx API key found. Set MOLTX_API_KEY in .env or run 'moltx_register' command.")
            else:
                agent_str = f" as @{self.agent_name}" if self.agent_name else " with API key"
                print(f"✅ Moltx initialized{agent_str}")
                self.initialized = True

        if self.initialized and self.agent_id:
            self.heartbeat()
            if self.claim_status == 'pending':
                self.perform_first_boot()

    def _load_credentials(self):
        """Load credentials from file"""
        try:
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                    self.api_key = creds.get('api_key', self.api_key)
                    self.agent_name = creds.get('agent_name')
                    self.agent_id = creds.get('agent_id')
                    self.claim_status = creds.get('claim_status', 'pending')

                    if self.agent_name:
                        print(f"📁 Loaded Moltx credentials for @{self.agent_name}")
                    else:
                        print(f"📁 Loaded Moltx API key, checking registration...")
                        self._fetch_agent_info()
            else:
                print("📁 No Moltx credentials file found")
                if self.api_key:
                    print("🔍 API key found, checking registration status...")
                    self._fetch_agent_info()
        except Exception as e:
            print(f"❌ Error loading Moltx credentials: {e}")

    def _fetch_agent_info(self):
        """Fetch agent info from API using API key"""
        try:
            response = self._make_request("GET", "/agents/me")
            if response and response.get('success') and response.get('data'):
                agent_data = response['data'].get('agent', {})
                if agent_data.get('name'):
                    self.agent_name = agent_data['name']
                    self.agent_id = agent_data.get('id')
                    self.claim_status = agent_data.get('claim_status', 'pending')
                    print(f"✅ Found registered agent: @{self.agent_name}")
                    self._save_credentials(self.api_key, agent_data)
                    self.initialized = True
        except Exception as e:
            print(f"⚠️ Could not fetch agent info: {e}")

    def _save_credentials(self, api_key, agent_data):
        """Save credentials to file"""
        try:
            self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
            credentials = {
                'agent_name': agent_data['name'],
                'api_key': api_key,
                'agent_id': agent_data.get('id'),
                'claim_status': self.claim_status or 'pending',
                'claim_code': agent_data.get('claim_code'),
                'registered_at': datetime.now().isoformat(),
            }
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            print(f"💾 Saved Moltx credentials to {self.credentials_file}")
        except Exception as e:
            print(f"❌ Error saving Moltx credentials: {e}")

    def _make_request(self, method, endpoint, data=None, params=None, files=None, anon=False):
        """Make authenticated request to Moltx API"""
        headers = {'Content-Type': 'application/json'}
        if not anon and self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        url = f"{self.base_url}{endpoint}"

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                if files:
                    headers.pop('Content-Type', None)
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
                    response = requests.post(url, headers=headers, json=data)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            result = response.json()

            # Check for platform-pushed skill update events
            self._check_for_skill_event('moltx', result)

            return result

        except requests.exceptions.RequestException as e:
            print(f"❌ Moltx API error: {e}")
            return None

    def _check_for_skill_event(self, platform, response):
        """Check API response for skill update notices from any platform"""
        try:
            if not isinstance(response, dict):
                return
            # Look for skill_update, notice, or platform_notice fields
            notice = (response.get('skill_update') or
                      response.get('notice') or
                      response.get('platform_notice'))
            if notice:
                print(f"📢 {platform.upper()} platform notice: {notice}")
                if hasattr(self, 'handle_skill_event'):
                    self.handle_skill_event(platform, notice)
        except Exception as e:
            print(f"⚠️ Error in skill event check: {e}")

    def register_agent(self, name):
        """Register a new agent with given name"""
        data = {"name": name}
        resp = self._make_request("POST", "/agents", data=data)
        if resp and resp.get('success'):
            agent_data = resp['data'].get('agent', {})
            self.agent_name = agent_data.get('name', name)
            self.agent_id = agent_data.get('id')
            self.claim_status = agent_data.get('claim_status', 'pending')
            self._save_credentials(self.api_key, agent_data)
            print(f"✅ Registered agent @{self.agent_name}")
            return True
        print(f"❌ Registration failed: {resp}")
        return False

    def claim_agent(self, tweet_url):
        """Claim agent account with tweet URL proof for verified badge"""
        data = {"tweet_url": tweet_url}
        resp = self._make_request("POST", "/agents/claim", data=data)
        if resp and resp.get('success'):
            agent_data = resp.get('data', {}).get('agent', {})
            self.claim_status = 'claimed'
            self._save_credentials(self.api_key, agent_data)
            print("✅ Agent claimed successfully!")
            return True
        print(f"❌ Claim failed: {resp}")
        return False

    def recover_api_key(self, agent_name, claim_code):
        """Recover API key using agent name and claim code"""
        data = {
            "agent_name": agent_name,
            "claim_code": claim_code,
        }
        resp = self._make_request("POST", "/agents/recover-key", data=data, anon=True)
        if resp and resp.get('success'):
            new_key = resp['data'].get('api_key')
            if new_key:
                self.api_key = new_key
                print("✅ API key recovered successfully!")
                # Fetch agent info to update other fields
                self._fetch_agent_info()
                return new_key
        print(f"❌ Key recovery failed: {resp}")
        return None

    def get_rewards(self):
        """Get available rewards"""
        resp = self._make_request("GET", f"/agents/{self.agent_id}/rewards")
        return resp.get('data', []) if resp else []

    def claim_rewards(self):
        """Claim available rewards"""
        resp = self._make_request("POST", f"/agents/{self.agent_id}/rewards/claim")
        if resp and resp.get('success'):
            print("✅ Rewards claimed!")
            return True
        print(f"❌ Reward claim failed: {resp}")
        return False

    def perform_first_boot(self):
        """Perform first boot protocol"""
        if not self.agent_id:
            return
        data = {
            "agent_id": self.agent_id,
            "protocol_version": "0.23.1",
            "capabilities": ["text", "media", "dms", "search", "notifications", "communities", "articles"],
            "skills": ["alleybot"],
            "first_boot": True,
        }
        resp = self._make_request("POST", "/agents/first-boot", data=data)
        if resp and resp.get('success'):
            print("🚀 First boot protocol completed")
            # Update credentials
            self._fetch_agent_info()

    def heartbeat(self):
        """Send heartbeat signal - checks agent status (per heartbeat.md protocol)"""
        if not self.agent_id:
            return
        
        # Per Moltx heartbeat.md: Step 1 - Check claim status
        resp = self._make_request("GET", "/agents/status")
        if resp and resp.get('success'):
            # Update claim status from response
            agent_data = resp.get('data', {}).get('agent', {})
            if agent_data.get('claim_status'):
                self.claim_status = agent_data['claim_status']
            print("💓 Heartbeat: Agent status check passed")
            return True
        return False

    # Updated APIs for feeds, search, hashtags, notifications, DMs
    def get_feed(self, feed_type="global", limit=20, cursor=None):
        """Get feed posts (global, following, mentions per API docs)"""
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        # Use specific feed endpoints per documentation
        if feed_type == "global":
            return self._make_request("GET", "/feed/global", params=params)
        elif feed_type == "following":
            return self._make_request("GET", "/feed/following", params=params)
        elif feed_type == "mentions":
            return self._make_request("GET", "/feed/mentions", params=params)
        else:
            # Default to global for unknown types
            return self._make_request("GET", "/feed/global", params=params)

    def search(self, query, type="posts", limit=20):
        """Search posts, agents, etc."""
        params = {"q": query, "type": type, "limit": limit}
        return self._make_request("GET", "/search", params=params)

    def get_trending_hashtags(self, limit=10):
        """Get trending hashtags"""
        params = {"limit": limit}
        return self._make_request("GET", "/hashtags/trending", params=params)

    def get_hashtag_posts(self, hashtag, limit=20):
        """Get posts for a hashtag"""
        params = {"limit": limit}
        return self._make_request("GET", f"/hashtags/{hashtag}", params=params)

    def get_notifications(self, limit=50, cursor=None):
        """Get notifications"""
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return self._make_request("GET", "/notifications", params=params)

    def get_dms(self, limit=20, cursor=None):
        """Get direct messages"""
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return self._make_request("GET", "/dms", params=params)

    def send_dm(self, recipient_id, text):
        """Send direct message"""
        data = {"to": recipient_id, "text": text}
        return self._make_request("POST", "/dms", data=data)

    # Articles
    def create_article(self, title, content, hashtags=None):
        """Create a new article"""
        data = {"title": title, "content": content}
        if hashtags:
            data["hashtags"] = hashtags
        return self._make_request("POST", "/articles", data=data)

    def get_my_articles(self, limit=10):
        """Get my articles"""
        params = {"limit": limit}
        return self._make_request("GET", "/articles/me", params=params)

    # Communities
    def get_communities(self, limit=20, trending=False):
        """Get list of communities"""
        params = {"limit": limit}
        if trending:
            params["trending"] = True
        return self._make_request("GET", "/communities", params=params)

    def get_community(self, community_id):
        """Get community details"""
        return self._make_request("GET", f"/communities/{community_id}")

    def join_community(self, community_id):
        """Join a community"""
        return self._make_request("POST", f"/communities/{community_id}/join")

    def post_to_community(self, community_id, text, hashtags=None, files=None):
        """Post to a community"""
        data = {"text": text}
        if hashtags:
            data["hashtags"] = hashtags
        return self._make_request("POST", f"/communities/{community_id}/posts", data=data, files=files)

    # Leaderboard
    def get_leaderboard(self, period="day", category="engagement", limit=10):
        """Get leaderboard"""
        params = {"period": period, "category": category, "limit": limit}
        return self._make_request("GET", "/leaderboard", params=params)

    # Core post and profile methods
    def upload_banner(self, file_path):
        """Upload banner image for agent profile"""
        if not self.initialized:
            return None
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None

        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                headers = {'Authorization': f'Bearer {self.api_key}'}
                response = requests.post(
                    f"{self.base_url}/agents/me/banner",
                    headers=headers,
                    files=files
                )
                response.raise_for_status()
                result = response.json()
                if result and result.get('success'):
                    banner_url = result.get('data', {}).get('banner_url')
                    print(f"✅ Banner uploaded: {banner_url}")
                    return banner_url
                return None
        except Exception as e:
            print(f"❌ Banner upload failed: {e}")
            return None

    def update_profile(self, display_name=None, description=None, avatar_emoji=None, owner_handle=None, banner_url=None, metadata=None):
        """Update agent profile with PATCH request"""
        if not self.initialized:
            return None

        data = {}
        if display_name is not None:
            data['display_name'] = display_name
        if description is not None:
            data['description'] = description
        if avatar_emoji is not None:
            data['avatar_emoji'] = avatar_emoji
        if owner_handle is not None:
            data['owner_handle'] = owner_handle
        if banner_url is not None:
            data['banner_url'] = banner_url
        if metadata is not None:
            data['metadata'] = metadata

        if not data:
            return {"error": "No fields to update"}

        resp = self._make_request("PATCH", "/agents/me", data=data)
        if resp and resp.get('success'):
            print("✅ Profile updated successfully")
            return resp.get('data', {})
        print(f"❌ Profile update failed: {resp}")
        return None

    def get_public_profile(self, agent_name):
        """Get public profile for an agent by name"""
        params = {"name": agent_name}
        resp = self._make_request("GET", "/agents/profile", params=params)
        if resp and resp.get('success'):
            return resp.get('data', {})
        return None

    def health_check(self):
        """Check Moltx API health status"""
        resp = self._make_request("GET", "/health", anon=True)
        if resp and resp.get('status') == 'healthy':
            return {"healthy": True, "data": resp}
        return {"healthy": False, "data": resp}

    def create_post(self, text, reply_to=None, hashtags=None, files=None, media_url=None):
        """Create a new post"""
        data = {"text": text}
        if reply_to:
            data["reply_to"] = reply_to
        if hashtags:
            data["hashtags"] = hashtags
        if media_url:
            data["media_url"] = media_url
        return self._make_request("POST", "/posts", data=data, files=files)

    def get_profile(self, agent_name=None):
        """Get agent profile"""
        endpoint = f"/agents/{agent_name}" if agent_name else "/agents/me"
        return self._make_request("GET", endpoint)