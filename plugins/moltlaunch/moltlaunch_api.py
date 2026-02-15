"""
Moltlaunch API Client
Handles EIP-191 signature authentication and API calls
"""
import requests
import time
import uuid
from typing import Optional, Dict, Any, List
from pathlib import Path
import json


class MoltlaunchAPI:
    """API client for Moltlaunch task marketplace"""
    
    BASE_URL = "https://moltlaunch.com/api"
    
    def __init__(self, api_key: Optional[str] = None, private_key: Optional[str] = None):
        self.api_key = api_key
        self.private_key = private_key
        self.agent_id: Optional[str] = None
        self.wallet_address: Optional[str] = None
        
    def _get_signature(self, action: str, task_id: str) -> tuple[str, int, str]:
        """
        Generate EIP-191 signature for authenticated endpoints
        Returns: (signature, timestamp, nonce)
        """
        if not self.private_key:
            raise ValueError("Private key required for authentication")
        
        timestamp = int(time.time())
        nonce = str(uuid.uuid4())
        message = f"moltlaunch:{action}:{task_id}:{timestamp}:{nonce}"
        
        # Use web3 for EIP-191 signing
        try:
            from web3 import Web3
            w3 = Web3()
            account = w3.eth.account.from_key(self.private_key)
            
            # EIP-191 personal sign
            signable_message = account.sign_message(
                Web3.keccak(text=message)
            )
            signature = signable_message.signature.hex()
            
            return signature, timestamp, nonce
        except ImportError:
            raise ImportError("web3 required for Moltlaunch authentication")
    
    def _auth_headers(self, action: str, task_id: str) -> Dict[str, str]:
        """Generate authentication headers for a request"""
        signature, timestamp, nonce = self._get_signature(action, task_id)
        return {
            "X-Agent-ID": self.agent_id or "",
            "X-Signature": signature,
            "X-Timestamp": str(timestamp),
            "X-Nonce": nonce,
            "Content-Type": "application/json"
        }
    
    # === Public Endpoints (no auth required) ===
    
    def list_agents(self, limit: int = 50) -> List[Dict]:
        """List all registered agents"""
        resp = requests.get(f"{self.BASE_URL}/agents", params={"limit": limit})
        resp.raise_for_status()
        return resp.json().get("data", [])
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent by ID"""
        resp = requests.get(f"{self.BASE_URL}/agents/{agent_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json().get("data")
    
    def find_agent_by_wallet(self, address: str) -> Optional[Dict]:
        """Find agent by wallet address"""
        resp = requests.get(f"{self.BASE_URL}/agents/by-wallet/{address}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json().get("data")
    
    def get_agent_gigs(self, agent_id: str) -> List[Dict]:
        """Get agent's gig listings"""
        resp = requests.get(f"{self.BASE_URL}/agents/{agent_id}/gigs")
        resp.raise_for_status()
        return resp.json().get("data", [])
    
    def get_agent_reviews(self, agent_id: str) -> List[Dict]:
        """Get agent's reviews"""
        resp = requests.get(f"{self.BASE_URL}/agents/{agent_id}/reviews")
        resp.raise_for_status()
        return resp.json().get("data", [])
    
    def get_recent_tasks(self, limit: int = 10) -> List[Dict]:
        """Get recent tasks globally"""
        resp = requests.get(f"{self.BASE_URL}/tasks/recent", params={"limit": limit})
        resp.raise_for_status()
        return resp.json().get("data", [])
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID"""
        resp = requests.get(f"{self.BASE_URL}/tasks/{task_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json().get("data")
    
    def get_task_inbox(self, agent_id: str) -> List[Dict]:
        """Get pending tasks for agent"""
        resp = requests.get(
            f"{self.BASE_URL}/tasks/inbox",
            params={"agent": agent_id}
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
    
    def get_agent_tasks(self, agent_id: str) -> List[Dict]:
        """Get full task history for agent"""
        resp = requests.get(
            f"{self.BASE_URL}/tasks/agent",
            params={"id": agent_id}
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
    
    # === Authenticated Endpoints (require signature) ===
    
    def register_agent(self, name: str, description: str, 
                       skills: List[str], price_wei: str) -> Dict:
        """
        Register agent in Moltlaunch index
        Requires wallet signature
        """
        headers = self._auth_headers("register", name)
        
        data = {
            "name": name,
            "description": description,
            "skills": skills,
            "priceWei": price_wei
        }
        
        resp = requests.post(
            f"{self.BASE_URL}/agents/register",
            headers=headers,
            json=data
        )
        resp.raise_for_status()
        result = resp.json()
        
        # Store agent ID on successful registration
        if "data" in result and "id" in result["data"]:
            self.agent_id = result["data"]["id"]
        
        return result.get("data", {})
    
    def update_profile(self, agent_id: str, **fields) -> Dict:
        """Update agent profile"""
        headers = self._auth_headers("profile", agent_id)
        
        resp = requests.put(
            f"{self.BASE_URL}/agents/{agent_id}/profile",
            headers=headers,
            json=fields
        )
        resp.raise_for_status()
        return resp.json().get("data", {})
    
    def create_gig(self, agent_id: str, title: str, description: str,
                   price_wei: str, category: str) -> Dict:
        """Create or update a gig listing"""
        headers = self._auth_headers("gig", agent_id)
        
        data = {
            "title": title,
            "description": description,
            "priceWei": price_wei,
            "category": category
        }
        
        resp = requests.post(
            f"{self.BASE_URL}/agents/{agent_id}/gigs",
            headers=headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json().get("data", {})
    
    def quote_task(self, task_id: str, price_wei: str, message: str) -> Dict:
        """Quote a price for a task"""
        headers = self._auth_headers("quote", task_id)
        
        data = {
            "quotedPriceWei": price_wei,
            "quotedMessage": message
        }
        
        resp = requests.post(
            f"{self.BASE_URL}/tasks/{task_id}/quote",
            headers=headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json().get("data", {})
    
    def decline_task(self, task_id: str, reason: str = "") -> Dict:
        """Decline a task request"""
        headers = self._auth_headers("decline", task_id)
        
        data = {"reason": reason} if reason else {}
        
        resp = requests.post(
            f"{self.BASE_URL}/tasks/{task_id}/decline",
            headers=headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json().get("data", {})
    
    def submit_work(self, task_id: str, result: str, 
                    files: Optional[List[Dict]] = None) -> Dict:
        """Submit completed work"""
        headers = self._auth_headers("submit", task_id)
        
        data = {"result": result}
        if files:
            data["files"] = files
        
        resp = requests.post(
            f"{self.BASE_URL}/tasks/{task_id}/submit",
            headers=headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json().get("data", {})
    
    def upload_file(self, task_id: str, file_path: str) -> Dict:
        """Upload a file for a task"""
        headers = self._auth_headers("upload", task_id)
        # Remove Content-Type for multipart
        headers.pop("Content-Type", None)
        
        with open(file_path, "rb") as f:
            files = {"file": f}
            resp = requests.post(
                f"{self.BASE_URL}/tasks/{task_id}/upload",
                headers=headers,
                files=files
            )
        
        resp.raise_for_status()
        return resp.json().get("data", {})
    
    def send_message(self, task_id: str, content: str) -> Dict:
        """Send message on task thread"""
        headers = self._auth_headers("message", task_id)
        
        data = {"content": content}
        
        resp = requests.post(
            f"{self.BASE_URL}/tasks/{task_id}/message",
            headers=headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json().get("data", {})
