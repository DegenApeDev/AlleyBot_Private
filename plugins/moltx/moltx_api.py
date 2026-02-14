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
        self.credentials_file = Path.home() / ".agents" / "moltx" / "config.json"
        self.initialized = False
        self.claim_status = None

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
                print(f"✅ Moltx initialized as {self.agent_name}")
                self.initialized = True

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
            print(f"⚠️  Could not fetch agent info: {e}")

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
                'registered_at': datetime.now().isoformat()
            }
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            print(f"💾 Saved Moltx credentials to {self.credentials_file}")
        except Exception as e:
            print(f"❌ Error saving Moltx credentials: {e}")

    def _make_request(self, method, endpoint, data=None, params=None, files=None):
        """Make authenticated request to Moltx API"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
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
                      response.get(f'{platform}_notice'))
            if not notice or not isinstance(notice, dict):
                return
            if notice.get('type') != 'skill_update':
                return
            # Route to selfimprove plugin
            if hasattr(self, 'core') and self.core:
                plugins = getattr(self.core, 'plugin_manager', None)
                if plugins:
                    selfimprove = plugins.plugins.get('selfimprove')
                    if selfimprove and hasattr(selfimprove, 'handle_platform_skill_event'):
                        selfimprove.handle_platform_skill_event(platform, notice)
        except Exception as e:
            print(f"⚠️  Error checking skill event: {e}")

    def register_agent(self, name, display_name=None, description=None, avatar_emoji="🦞"):
        """Register a new agent on Moltx"""
        if self.api_key and self.claim_status == 'claimed':
            return f"✅ Already registered and claimed on Moltx. Agent is fully active. Use /moltx_status to see details."

        if self.initialized and self.agent_name:
            return f"✅ Already registered as @{self.agent_name} on Moltx. Claim status: {self.claim_status}. Use /moltx_status to see details."

        if len(name) < 3 or len(name) > 50:
            return "❌ Agent name must be 3-50 characters"

        data = {
            'name': name,
            'display_name': display_name or name,
            'description': description or f"🦞 AI Agent from Moltbook ecosystem",
            'avatar_emoji': avatar_emoji
        }

        print(f"🐦 Registering agent '{name}' on Moltx...")
        result = self._make_request('POST', '/agents/register', data)

        if result and 'data' in result:
            data = result['data']
            agent_data = data['agent']
            api_key = data['api_key']
            claim_data = data.get('claim', {})

            self.api_key = api_key
            self.agent_name = agent_data['name']
            self.agent_id = agent_data.get('id')
            self.claim_status = agent_data.get('claim_status', claim_data.get('status', 'pending'))
            self._save_credentials(self.api_key, agent_data)
            print(f"✅ Successfully registered agent @{self.agent_name}")
            claim_code = claim_data.get('code')
            if claim_code:
                print(f"📋 Your claim code is: {claim_code}")
                print("💡 Share this code with Moltx team to claim your agent.")
            return f"✅ Agent @{self.agent_name} registered successfully! Status: {self.claim_status}"
        else:
            return "❌ Registration failed. Check console for details."

    def get_articles(self, params=None):
        """Fetch articles"""
        return self._make_request("GET", "/articles", params=params)

    def create_article(self, title, content, community_id=None, tags=None):
        """Create a new article"""
        data = {
            "title": title,
            "content": content,
            "community_id": community_id,
            "tags": tags or []
        }
        return self._make_request("POST", "/articles", data=data)

    def get_communities(self, params=None):
        """Fetch communities"""
        return self._make_request("GET", "/communities", params=params)

    def get_leaderboard(self, period="daily", limit=10):
        """Fetch leaderboard"""
        params = {"period": period, "limit": limit}
        return self._make_request("GET", "/leaderboard", params=params)

    def get_hashtags(self, params=None):
        """Fetch hashtags"""
        return self._make_request("GET", "/hashtags", params=params)

    def get_notifications(self, params=None):
        """Fetch notifications"""
        return self._make_request("GET", "/notifications", params=params)

    def mark_notification_read(self, notification_id):
        """Mark a notification as read"""
        return self._make_request("PATCH", f"/notifications/{notification_id}/read")

    def search(self, query, type="all", limit=20):
        """Search across platform"""
        params = {"q": query, "type": type, "limit": limit}
        return self._make_request("GET", "/search", params=params)

    def claim_agent(self, claim_code):
        """Claim the registered agent"""
        if self.claim_status == 'claimed':
            return "✅ Agent already claimed."
        if not self.agent_name:
            return "❌ No agent registered. Register first."
        data = {"claim_code": claim_code}
        result = self._make_request("POST", "/agents/claim", data=data)
        if result and result.get('success'):
            self.claim_status = 'claimed'
            agent_data = result.get('data', {}).get('agent', {})
            self._save_credentials(self.api_key, agent_data)
            return f"✅ Agent @{self.agent_name} claimed successfully!"
        return "❌ Claim failed. Invalid code?"

    def get_rewards(self):
        """Fetch available rewards"""
        return self._make_request("GET", "/rewards")

    def claim_reward(self, reward_id):
        """Claim a specific reward"""
        return self._make_request("POST", f"/rewards/{reward_id}/claim")