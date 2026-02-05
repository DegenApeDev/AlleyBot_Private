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
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"❌ Moltx API error: {e}")
            return None

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
            self.agent_id = agent_data['id']
            self.claim_status = claim_data.get('status', 'pending')

            agent_info = {
                'name': agent_data['name'],
                'id': agent_data['id'],
                'claim_code': claim_data.get('code')
            }
            self._save_credentials(api_key, agent_info)
            self.initialized = True

            output = f"✅ Agent '{name}' registered on Moltx!\n"
            output += f"🔑 API Key: {api_key}\n"
            output += f"📱 Claim Code: {claim_data.get('code', 'N/A')}\n"
            output += f"🐦 Handle: @{agent_data['name']}\n"
            output += f"📝 Display Name: {agent_data.get('display_name', 'N/A')}\n"
            output += f"🎯 Next: Post claim tweet with code for full access"
            return output
        else:
            return f"❌ Registration failed. Response: {result}"

    def claim_agent(self, tweet_url):
        """Claim agent with X/Twitter verification"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        if not tweet_url or 'x.com' not in tweet_url:
            return "❌ Invalid tweet URL. Must be an X.com URL"

        print(f"🐦 Claiming agent with tweet: {tweet_url}")
        result = self._make_request('POST', '/agents/claim', {'tweet_url': tweet_url})

        if result:
            self.claim_status = 'claimed'
            self._update_claim_status('claimed')
            output = f"✅ Agent claimed successfully!\n"
            output += f"🎉 Full access unlocked - higher limits, media uploads, verified badge\n"
            output += f"🐦 @{self.agent_name} is now verified!"
            return output
        else:
            return "❌ Claim failed. Make sure your tweet contains the claim code and is public."

    def _update_claim_status(self, status):
        """Update claim status in credentials file"""
        try:
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                creds['claim_status'] = status
                with open(self.credentials_file, 'w') as f:
                    json.dump(creds, f, indent=2)
        except Exception as e:
            print(f"❌ Error updating claim status: {e}")

    def check_status(self):
        """Check agent status"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        result = self._make_request('GET', '/agents/status')

        if result:
            output = f"🐦 Moltx Status for @{self.agent_name}:\n\n"
            output += f"🆔 Agent ID: {result.get('id', 'N/A')}\n"
            output += f"📱 Handle: @{result.get('name', 'N/A')}\n"
            output += f"👤 Display: {result.get('display_name', 'N/A')}\n"
            output += f"🎯 Claim Status: {result.get('claim_status', 'N/A')}\n"
            output += f"📊 Posts: {result.get('posts_count', 0)}\n"
            output += f"👥 Following: {result.get('following_count', 0)}\n"
            output += f"👤 Followers: {result.get('followers_count', 0)}\n"
            output += f"❤️ Likes: {result.get('likes_count', 0)}\n"
            if result.get('verified'):
                output += f"✅ Verified Agent\n"
            return output
        else:
            return "❌ Failed to fetch status"

    def upload_media(self, image_path):
        """Upload image to get media URL"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register and claim agent first."

        if not os.path.exists(image_path):
            return f"❌ Image file not found: {image_path}"

        print(f"📤 Uploading media: {image_path}")

        try:
            with open(image_path, 'rb') as image_file:
                files = {'file': image_file}
                result = self._make_request('POST', '/media/upload', files=files)

            if result and 'success' in result and result['success']:
                media_data = result['data']
                if 'url' in media_data:
                    print(f"✅ Media uploaded: {media_data['url']}")
                    return media_data['url']
                else:
                    print(f"❌ Media uploaded but no URL returned. Response: {result}")
                    return None
            else:
                print(f"❌ Failed to upload media. Response: {result}")
                return None

        except Exception as e:
            print(f"❌ Error uploading media: {e}")
            return None

    def upload_avatar(self, image_path):
        """Upload avatar image for agent profile (300x300 PNG, claimed agents only)"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register and claim agent first."

        print(f"👤 Uploading avatar image: {image_path}")

        try:
            if not os.path.exists(image_path):
                return f"❌ Image file not found: {image_path}"

            url = f"{self.base_url}/agents/me/avatar"
            headers = {'Authorization': f'Bearer {self.api_key}'}

            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
                response = requests.post(url, headers=headers, files=files)

            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('success') and 'data' in result:
                    avatar_url = result['data'].get('avatar_url', '')
                    output = f"✅ Avatar uploaded successfully!\n"
                    output += f"👤 Avatar URL: {avatar_url}\n"
                    output += f"🎉 Profile updated with new 300x300 avatar!"
                    return output
                else:
                    return f"❌ Avatar upload failed. Response: {result}"
            else:
                return f"❌ Avatar upload failed. Status: {response.status_code}, Response: {response.text}"

        except Exception as e:
            return f"❌ Error uploading avatar: {e}"

    def upload_banner(self, image_path):
        """Upload banner image for agent profile"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register and claim agent first."

        if not os.path.exists(image_path):
            return f"❌ Image file not found: {image_path}"

        print(f"🖼️ Uploading banner image: {image_path}")

        try:
            with open(image_path, 'rb') as image_file:
                files = {'file': image_file}
                result = self._make_request('POST', '/agents/me/banner', files=files)

            if result and 'success' in result and result['success']:
                banner_data = result['data']
                if 'banner_url' in banner_data:
                    output = f"✅ Banner uploaded successfully!\n"
                    output += f"🖼️ Banner URL: {banner_data['banner_url']}\n"
                    output += f"🎉 Profile updated with new banner!"
                    return output
                else:
                    return f"❌ Banner uploaded but no URL returned. Response: {result}"
            else:
                return f"❌ Failed to upload banner. Response: {result}"

        except Exception as e:
            return f"❌ Error uploading banner: {e}"

    def update_profile(self, display_name=None, description=None, avatar_emoji=None):
        """Update agent profile"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        data = {}
        if display_name:
            data['display_name'] = display_name
        if description:
            data['description'] = description
        if avatar_emoji:
            data['avatar_emoji'] = avatar_emoji

        if not data:
            return "❌ No updates provided"

        result = self._make_request('PATCH', '/agents/me', data)

        if result and 'success' in result and result['success']:
            agent_data = result['data']['agent']
            output = f"✅ Profile updated successfully!\n"
            output += f"👤 Display Name: {agent_data.get('display_name', 'N/A')}\n"
            output += f"📝 Description: {agent_data.get('description', 'N/A')}\n"
            output += f"🎭 Avatar: {agent_data.get('avatar_emoji', 'N/A')}"
            return output
        else:
            return f"❌ Failed to update profile. Response: {result}"

    def get_agent_stats(self):
        """Get agent statistics using v0.17.6 API"""
        if not self.initialized or not self.agent_name:
            return None

        try:
            response = self._make_request("GET", f"/agent/{self.agent_name}/stats")
            if response:
                return {
                    'posts': response.get('posts', 0),
                    'followers': response.get('followers', 0),
                    'following': response.get('following', 0),
                    'likes': response.get('likes', 0),
                    'replies': response.get('replies', 0),
                    'reposts': response.get('reposts', 0)
                }
            return None
        except Exception as e:
            print(f"❌ Error fetching Moltx stats: {e}")
            return None

    def get_own_profile(self):
        """Get own agent profile with stats"""
        if not self.initialized:
            return None

        try:
            response = self._make_request("GET", "/agents/me")
            return response
        except Exception as e:
            print(f"❌ Error fetching Moltx profile: {e}")
            return None

    def get_status(self):
        """Get Moltx plugin status"""
        if self.initialized:
            return f"🐦 Moltx Status:\n  Agent: @{self.agent_name}\n  Claim: {self.claim_status}\n  API: ✅ Connected"
        else:
            return "🐦 Moltx Status: ❌ Not initialized"

    def _get_activity(self, activity_type):
        """Get activities by type from memory"""
        try:
            activities = self.core.get_memory('moltx_activities') or []
            return [a for a in activities if a.get('type') == activity_type]
        except Exception:
            return []

    def _should_wait_for_post_cooldown(self):
        """Check if we should wait for post cooldown (10 minutes between posts)"""
        try:
            from datetime import datetime

            last_post_time = self.core.get_memory('moltx_last_post_time')

            if not last_post_time:
                activities = self.core.get_memory('moltx_activities') or []
                post_activities = [a for a in activities if a.get('type') == 'post']
                if post_activities:
                    last_post = max(post_activities, key=lambda x: x.get('timestamp', ''))
                    last_post_time = last_post.get('timestamp')

            if not last_post_time:
                return False

            try:
                last_post_dt = datetime.fromisoformat(last_post_time.replace('Z', '+00:00'))
                current_time = datetime.now()
                time_diff = current_time - last_post_dt
                minutes_diff = time_diff.total_seconds() / 60

                if minutes_diff < 10:
                    print(f"⏰ Post cooldown: {minutes_diff:.1f} minutes since last post (need 10)")
                    return True
                return False

            except Exception as e:
                print(f"⚠️  Error parsing post timestamp: {e}")
                return False

        except Exception as e:
            print(f"⚠️  Error checking post cooldown: {e}")
            return False

    def _record_activity(self, activity_type, data):
        """Record Moltx activity in memory"""
        activities = self.core.get_memory('moltx_activities') or []
        activities.append({
            'type': activity_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        self.core.save_memory('moltx_activities', activities[-100:])
