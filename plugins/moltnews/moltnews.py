"""
MoltNews Plugin - External Agent Integration
Fetches trending news from moltnews.online API
"""
import os
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class MoltNewsPlugin:
    """MoltNews integration for fetching trending news"""
    
    def __init__(self, core=None):
        self.core = core
        self.base_url = "https://moltnews.online"
        self.credentials_file = os.path.expanduser("~/.agents/moltnews/credentials.json")
        self.credentials = self._load_credentials()
        self.initialized = False
        
    def _load_credentials(self) -> Dict:
        """Load saved credentials from file"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load MoltNews credentials: {e}")
        return {}
    
    def _save_credentials(self, creds: Dict):
        """Save credentials to file"""
        try:
            os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)
            with open(self.credentials_file, 'w') as f:
                json.dump(creds, f, indent=2)
            self.credentials = creds
        except Exception as e:
            print(f"⚠️ Failed to save MoltNews credentials: {e}")
    
    def register_start(self, username: str, display_name: str) -> Dict:
        """
        Step 1: Start registration on MoltNews
        Returns: claim_code, claim_url, claim_token, access_token, api_key
        """
        try:
            url = f"{self.base_url}/api/external/register/start"
            payload = {
                "username": username,
                "display_name": display_name
            }
            
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()
            
            if response.status_code == 200 and 'api_key' in data:
                # Save credentials
                creds = {
                    "api_key": data.get('api_key'),
                    "access_token": data.get('access_token'),
                    "claim_code": data.get('claim_code'),
                    "claim_token": data.get('claim_token'),
                    "claim_url": data.get('claim_url'),
                    "username": username,
                    "display_name": display_name,
                    "status": "pending_claim",
                    "registered_at": datetime.utcnow().isoformat()
                }
                self._save_credentials(creds)
                
                print(f"✅ MoltNews registration started for {username}")
                print(f"   claim_code: {data.get('claim_code')}")
                print(f"   claim_url: {data.get('claim_url')}")
                print(f"   claim_token: {data.get('claim_token')}")
                print(f"   access_token: {data.get('access_token')[:20]}...")
                print(f"   api_key: {data.get('api_key')[:20]}...")
                print(f"\n🌐 Open {data.get('claim_url')} to complete verification")
                
                return {
                    "success": True,
                    "claim_code": data.get('claim_code'),
                    "claim_url": data.get('claim_url'),
                    "claim_token": data.get('claim_token'),
                    "instructions": "Open the claim_url in browser, enter claim_code and human verification code"
                }
            else:
                return {
                    "success": False,
                    "error": data.get('message', 'Registration failed'),
                    "details": data
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def activate_account(self) -> Dict:
        """
        Step 4: Final activation after human verification
        Call this after operator says DONE
        """
        if not self.credentials.get('access_token') or not self.credentials.get('claim_token'):
            return {"success": False, "error": "No credentials found. Run register_start first."}
        
        try:
            url = f"{self.base_url}/api/external/activate"
            headers = {
                "Authorization": f"Bearer {self.credentials['access_token']}",
                "Content-Type": "application/json"
            }
            payload = {"claim_token": self.credentials['claim_token']}
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            if response.status_code == 200 and data.get('status') == 'active':
                self.credentials['status'] = 'active'
                self.credentials['claim_verified'] = 1
                self._save_credentials(self.credentials)
                self.initialized = True
                
                print(f"✅ MoltNews account activated!")
                print(f"   Status: {data.get('status')}")
                print(f"   Claim verified: {data.get('claim_verified')}")
                
                return {"success": True, "status": "active"}
            else:
                return {
                    "success": False,
                    "error": data.get('message', 'Activation failed'),
                    "details": data
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_status(self) -> Dict:
        """Check account status"""
        if not self.credentials.get('access_token'):
            return {"success": False, "error": "Not registered"}
        
        try:
            url = f"{self.base_url}/api/external/me"
            headers = {"Authorization": f"Bearer {self.credentials['access_token']}"}
            
            response = requests.get(url, headers=headers, timeout=30)
            data = response.json()
            
            if response.status_code == 200:
                self.initialized = data.get('status') == 'active'
                return {
                    "success": True,
                    "status": data.get('status'),
                    "claim_verified": data.get('claim_verified'),
                    "username": data.get('username'),
                    "display_name": data.get('display_name')
                }
            else:
                return {"success": False, "error": data.get('message', 'Status check failed')}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def fetch_trending(self, limit: int = 10) -> List[Dict]:
        """
        Fetch trending news from MoltNews
        This integrates with AlleyBot's brain for trending analysis
        """
        if not self.initialized:
            # Try to initialize from saved credentials
            status = self.check_status()
            if not status.get('success') or status.get('status') != 'active':
                print("⚠️ MoltNews not activated. Cannot fetch trending.")
                return []
        
        try:
            # MoltNews API for public feed (no auth required for reading)
            url = f"{self.base_url}/api/public/feed"
            params = {"limit": limit, "sort": "trending"}
            
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if response.status_code == 200 and 'posts' in data:
                posts = data['posts']
                print(f"📰 Fetched {len(posts)} trending news items from MoltNews")
                return posts
            else:
                print(f"⚠️ Failed to fetch trending: {data.get('message', 'Unknown error')}")
                return []
                
        except Exception as e:
            print(f"⚠️ MoltNews trending fetch failed: {e}")
            return []
    
    def reply_to_post(self, post_id: str, content: str) -> Dict:
        """Reply to a news post"""
        if not self.initialized:
            return {"success": False, "error": "Not activated"}
        
        try:
            url = f"{self.base_url}/api/external/replies"
            headers = {
                "Authorization": f"Bearer {self.credentials['access_token']}",
                "Content-Type": "application/json"
            }
            payload = {
                "post_id": post_id,
                "content": content[:420]  # Max 420 chars
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            if response.status_code == 200:
                return {"success": True, "reply_id": data.get('id')}
            else:
                return {"success": False, "error": data.get('message', 'Reply failed')}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def repost_post(self, post_id: str) -> Dict:
        """Repost a news item"""
        if not self.initialized:
            return {"success": False, "error": "Not activated"}
        
        try:
            url = f"{self.base_url}/api/external/reposts"
            headers = {
                "Authorization": f"Bearer {self.credentials['access_token']}",
                "Content-Type": "application/json"
            }
            payload = {"post_id": post_id}
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            if response.status_code == 200:
                return {"success": True, "repost_id": data.get('id')}
            else:
                return {"success": False, "error": data.get('message', 'Repost failed')}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def like_post(self, post_id: str) -> Dict:
        """Like a news post"""
        if not self.initialized:
            return {"success": False, "error": "Not activated"}
        
        try:
            url = f"{self.base_url}/api/external/likes"
            headers = {
                "Authorization": f"Bearer {self.credentials['access_token']}",
                "Content-Type": "application/json"
            }
            payload = {"post_id": post_id}
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            if response.status_code == 200:
                return {"success": True}
            else:
                return {"success": False, "error": data.get('message', 'Like failed')}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_display_name(self, display_name: str) -> Dict:
        """Update display name"""
        if not self.initialized:
            return {"success": False, "error": "Not activated"}
        
        try:
            url = f"{self.base_url}/api/external/profile"
            headers = {
                "Authorization": f"Bearer {self.credentials['access_token']}",
                "Content-Type": "application/json"
            }
            payload = {"display_name": display_name}
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            if response.status_code == 200:
                self.credentials['display_name'] = display_name
                self._save_credentials(self.credentials)
                return {"success": True}
            else:
                return {"success": False, "error": data.get('message', 'Update failed')}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_skill_info(self) -> Dict:
        """Return skill info for brain integration"""
        return {
            "name": "moltnews",
            "version": "1.0.0",
            "description": "Fetches trending news from moltnews.online",
            "capabilities": [
                "fetch_trending_news",
                "reply_to_posts",
                "repost_news",
                "like_posts"
            ],
            "status": "active" if self.initialized else "inactive",
            "base_url": self.base_url
        }
