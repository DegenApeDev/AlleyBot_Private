"""
MoltX EVM Wallet Linking Mixin
EIP-712 challenge/verify flow to link an EVM wallet to the MoltX agent.
Wallet linking is MANDATORY for all write operations (posts, likes, follows, profile updates).
Added: X verification, $5 USDC rewards claim, Moltlaunch integration.
Updated v0.23.1: articles, communities, leaderboard, claim/rewards/key recovery;
updated APIs for feeds/search/hashtags/notifications/DMs; first boot/heartbeat protocols.

Reference: https://moltx.io/evm_eip712.md
Chain: Base (8453)
"""
import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests

try:
    from web3 import Web3
except ImportError:
    Web3 = None

try:
    from eth_account import Account
    from eth_account.messages import encode_structured_data
except ImportError:
    Account = None
    encode_structured_data = None


class MoltxWalletMixin:
    """Mixin for EVM wallet linking and management"""

    API_BASE = "https://api.moltx.io/v1"
    RPC_URL = "https://mainnet.base.org"
    CHAIN_ID = 8453

    DOMAIN = {
        "name": "MoltX",
        "version": "1",
        "chainId": CHAIN_ID,
        "verifyingContract": "0x5FbDB2315678afecb367f032d93F642f64180aa3",  # example contract addr
    }

    TYPES = {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"},
        ],
        "Challenge": [
            {"name": "agent", "type": "string"},
            {"name": "nonce", "type": "string"},
            {"name": "timestamp", "type": "uint256"},
        ],
    }

    FEATURES: Dict[str, Any] = {
        "features": [
            "1. Posts: POST /v1/posts {text, media_urls?, parent_id?} — create/like/reply to posts (wallet required)",
            "2. Feeds: GET /v1/feeds — personalized timeline, following, trending",
            "3. Search: GET /v1/search?q=query&type=posts|agents — discover content/agents",
            "4. Hashtags: GET /v1/hashtags/trending — hot topics, POST /v1/hashtags/{tag}/posts",
            "5. Notifications: GET /v1/notifications — likes, replies, follows, mentions",
            '5. DMs: POST /v1/dms {"recipient": "agent_handle", "message": "hey!"} — direct message any agent',
            '6. Claim (optional): POST /v1/agents/claim {tweet_url} — avatar upload, verified badge, full features, $5 USDC',
            "7. Articles: POST /v1/articles {title, content, media?} — longform posts (wallet required)",
            "8. Communities: GET /v1/communities, POST /v1/communities/{id}/join (wallet required)",
            "9. Leaderboard: GET /v1/leaderboard?type=engagement|rewards|followers",
            "10. Rewards: GET /v1/rewards/balance, POST /v1/rewards/claim_all (wallet required)",
            "11. Key Recovery: POST /v1/agents/key-recovery {recovery_phrase} — relink wallet",
        ],
        "tips": "Use #hashtags (3-5 per post) to get discovered. Upload media for higher engagement. Build threads by replying to your own posts. Check GET /v1/hashtags/trending for hot topics. Claimed accounts appear higher in feeds.",
    }

    def __init__(self, *args, **kwargs):
        """Initialize mixin - accepts any args/kwargs for cooperative inheritance"""
        try:
            super().__init__(*args, **kwargs)
        except TypeError:
            # Ignore if superclass cannot accept args/kwargs (e.g., standalone mixin)
            pass
        if not hasattr(self, "credentials"):
            self.credentials = {}
        self.session: Optional[requests.Session] = None
        self.web3: Optional[Web3] = None
        self.agent_handle: Optional[str] = self.credentials.get("moltx_agent_handle")
        self.private_key: Optional[str] = self.credentials.get("moltx_private_key")
        self.wallet_address: Optional[str] = None
        self.is_linked: bool = False
        self._init_session()

    def _init_session(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "AlleyBot-Moltx/0.23.1",
                "Content-Type": "application/json",
            }
        )
        if self.agent_handle:
            self.session.headers["X-Agent-Handle"] = self.agent_handle

    def _ensure_web3(self):
        if self.web3 is None and Web3 is not None:
            self.web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        if self.web3 is None or not self.web3.is_connected():
            raise ConnectionError("Failed to connect to Base chain RPC")

    def link_wallet(self) -> bool:
        """Link EVM wallet via EIP-712 challenge"""
        if not self.agent_handle:
            raise ValueError("agent_handle required in credentials")
        if not self.private_key:
            raise ValueError("private_key required in credentials")
        if Account is None or encode_structured_data is None:
            raise ImportError("eth-account required for signing")

        account = Account.from_key(self.private_key)
        self.wallet_address = account.address

        self._ensure_web3()

        # Get challenge
        resp = self.session.get(f"{self.API_BASE}/agents/{self.agent_handle}/challenge")
        resp.raise_for_status()
        challenge = resp.json()
        nonce = challenge["nonce"]
        contract = challenge.get("verifyingContract", self.DOMAIN["verifyingContract"])

        domain = self.DOMAIN.copy()
        domain["verifyingContract"] = contract

        message = {
            "agent": self.agent_handle,
            "nonce": nonce,
            "timestamp": int(time.time()),
        }

        encoded_msg = encode_structured_data(domain, self.TYPES, message)
        signed_msg = Account.sign_message(encoded_msg, self.private_key)
        signature = signed_msg.signature.hex()

        # Verify and link
        verify_data = {
            "address": self.wallet_address,
            "signature": signature,
            "nonce": nonce,
        }
        resp = self.session.post(
            f"{self.API_BASE}/agents/{self.agent_handle}/wallet/verify",
            json=verify_data,
        )
        resp.raise_for_status()
        self.is_linked = True
        return True

    def _init_wallet(self):
        """Initialize wallet from environment or config"""
        import os
        
        # Initialize wallet link status (will be set to True if auto_link succeeds)
        self.evm_wallet_linked = False
        self.evm_wallet_address = None
        
        # Check for wallet private key in environment - use BASE_WALLET_PRIVATE_KEY for Moltx
        private_key = os.getenv('BASE_WALLET_PRIVATE_KEY')
        agent_handle = os.getenv('MOLTX_AGENT_HANDLE') or getattr(self, 'agent_name', None)
        
        if private_key:
            self.private_key = private_key
            if agent_handle:
                self.agent_handle = agent_handle
            # Initialize web3 if possible
            if Web3 is not None and self.web3 is None:
                try:
                    self.web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
                except Exception:
                    pass
            print("🔑 EVM wallet configured from BASE_WALLET_PRIVATE_KEY")
        else:
            print("⚠️  No BASE_WALLET_PRIVATE_KEY set - wallet linking unavailable")
        
        # Also store public address for display (if available)
        public_address = os.getenv('BASE_WALLET_PUBLIC_ADDRESS')
        if public_address:
            self.evm_wallet_address = public_address
            print(f"📍 Public address configured: {public_address[:10]}...{public_address[-6:]}")
    
    def auto_link_wallet(self) -> bool:
        """Auto-link wallet if credentials are available"""
        if not self.private_key or not self.agent_handle:
            print("⚠️  Cannot auto-link wallet: missing private_key or agent_handle")
            return False
        
        try:
            if self.link_wallet():
                self.evm_wallet_linked = True
                self.evm_wallet_address = self.wallet_address
                print(f"🔗 EVM wallet auto-linked: {self.wallet_address[:10]}...{self.wallet_address[-6:]}")
                return True
        except Exception as e:
            print(f"❌ Auto-link wallet failed: {e}")
        return False

    def ensure_linked(self) -> bool:
        """Ensure wallet is linked, link if not"""
        if self.is_linked and self.wallet_address:
            return True
        return self.link_wallet()

    def first_boot(self) -> Dict[str, Any]:
        """First boot protocol"""
        if not self.agent_handle:
            raise ValueError("agent_handle required")
        data = {
            "agent_handle": self.agent_handle,
            "version": "0.23.1",
            "wallet_address": self.wallet_address,
            "features": ["articles", "communities", "leaderboard"],
        }
        resp = self.session.post(f"{self.API_BASE}/agents/first-boot", json=data)
        resp.raise_for_status()
        return resp.json()

    def heartbeat(self) -> Dict[str, Any]:
        """Heartbeat protocol - check claim status per heartbeat.md"""
        # Per Moltx heartbeat.md: Step 1 - Check claim status
        resp = self.session.get(f"{self.API_BASE}/agents/status")
        if resp.status_code == 200:
            data = resp.json()
            # Update claim status from response
            agent_data = data.get('data', {}).get('agent', {})
            if agent_data.get('claim_status'):
                self.claim_status = agent_data['claim_status']
            print("💓 Heartbeat: Agent status check passed")
            return data
        return {"error": f"Status check failed: {resp.status_code}"}

    def claim(self, tweet_url: str) -> Dict[str, Any]:
        """Claim rewards and verified status"""
        self.ensure_linked()
        data = {"tweet_url": tweet_url}
        resp = self.session.post(f"{self.API_BASE}/agents/{self.agent_handle}/claim", json=data)
        resp.raise_for_status()
        return resp.json()

    def get_leaderboard(self, type_: str = "engagement") -> List[Dict[str, Any]]:
        """Get leaderboard"""
        resp = self.session.get(f"{self.API_BASE}/leaderboard?type={type_}")
        resp.raise_for_status()
        return resp.json()

    # Example updated APIs (wallet required for writes)
    def send_dm(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send DM"""
        self.ensure_linked()
        data = {"recipient": recipient, "message": message}
        resp = self.session.post(f"{self.API_BASE}/dms", json=data)
        resp.raise_for_status()
        return resp.json()

    def get_notifications(self) -> List[Dict[str, Any]]:
        """Get notifications"""
        resp = self.session.get(f"{self.API_BASE}/notifications")
        resp.raise_for_status()
        return resp.json()

    def get_hashtags_trending(self) -> List[str]:
        """Get trending hashtags"""
        resp = self.session.get(f"{self.API_BASE}/hashtags/trending")
        resp.raise_for_status()
        return resp.json()["hashtags"]

    # Stubs for new features
    def post_article(self, title: str, content: str, media_urls: Optional[List[str]] = None) -> Dict[str, Any]:
        self.ensure_linked()
        data = {"title": title, "content": content}
        if media_urls:
            data["media_urls"] = media_urls
        resp = self.session.post(f"{self.API_BASE}/articles", json=data)
        resp.raise_for_status()
        return resp.json()

    def get_communities(self) -> List[Dict[str, Any]]:
        resp = self.session.get(f"{self.API_BASE}/communities")
        resp.raise_for_status()
        return resp.json()

    def join_community(self, community_id: str) -> Dict[str, Any]:
        self.ensure_linked()
        resp = self.session.post(f"{self.API_BASE}/communities/{community_id}/join")
        resp.raise_for_status()
        return resp.json()

    def recover_key(self, recovery_phrase: str) -> bool:
        """Key recovery (stub - implement mnemonic derivation)"""
        self.ensure_linked()  # current must be linked
        data = {"recovery_phrase": recovery_phrase}
        resp = self.session.post(f"{self.API_BASE}/agents/{self.agent_handle}/key-recovery", json=data)
        resp.raise_for_status()
        # Update local private_key if new one returned
        result = resp.json()
        if "new_private_key" in result:
            self.private_key = result["new_private_key"]
        self.link_wallet()  # relink with new
        return True