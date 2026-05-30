"""
MoltX Integrations - Wallet linking and World State adapter
Consolidates: moltx_wallet.py, moltx_adapter.py
"""
import os
import json
import re
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from web3 import Web3
except ImportError:
    Web3 = None

try:
    from eth_account import Account
    from eth_account.messages import encode_typed_data
except ImportError:
    Account = None
    encode_typed_data = None

try:
    from src.autonomy.platform_adapter import (
        PlatformAdapter, 
        PlatformEntity, 
        PlatformInteraction,
        PlatformRelationship
    )
except ImportError:
    PlatformAdapter = None
    PlatformEntity = None
    PlatformInteraction = None
    PlatformRelationship = None


def _safe_json(response) -> dict:
    """Parse response.json() with NDJSON fallback."""
    try:
        return response.json()
    except json.JSONDecodeError:
        text = response.text.strip()
        if not text:
            return {}
        try:
            decoder = json.JSONDecoder()
            obj, _ = decoder.raw_decode(text)
            return obj if isinstance(obj, dict) else {}
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*?\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return {}


class MoltxIntegrationsMixin:
    """Wallet linking and World State integration for MoltX"""
    
    API_BASE = "https://moltx.io"
    RPC_URL = "https://mainnet.base.org"
    CHAIN_ID = 8453
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.web3 = None
        self.wallet_address = None
        self.evm_wallet_linked = False
        self.evm_wallet_address = None
    
    # =========================================================================
    # WALLET LINKING - EVM wallet via EIP-712
    # =========================================================================
    
    def _init_wallet(self):
        """Initialize wallet from environment or config"""
        self.evm_wallet_linked = False
        self.evm_wallet_address = None
        
        private_key = os.getenv('BASE_WALLET_PRIVATE_KEY')
        agent_handle = os.getenv('MOLTX_AGENT_HANDLE') or getattr(self, 'agent_name', None)
        
        if private_key:
            self.private_key = private_key
            if agent_handle:
                self.agent_handle = agent_handle
            if Web3 is not None and self.web3 is None:
                try:
                    self.web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
                except Exception:
                    pass
            print("🔑 EVM wallet configured from BASE_WALLET_PRIVATE_KEY")
        else:
            print("⚠️  No BASE_WALLET_PRIVATE_KEY set - wallet linking unavailable")
        
        public_address = os.getenv('BASE_WALLET_PUBLIC_ADDRESS')
        if public_address:
            self.evm_wallet_address = public_address
            print(f"📍 Public address configured: {public_address[:10]}...{public_address[-6:]}")
    
    def link_wallet(self) -> bool:
        """Link EVM wallet via EIP-712 challenge/verify flow"""
        if not hasattr(self, 'api_key') or not self.api_key:
            raise ValueError("api_key required for wallet linking")
        if not hasattr(self, 'private_key') or not self.private_key:
            raise ValueError("private_key required for wallet linking")
        if Account is None or encode_typed_data is None:
            raise ImportError("eth-account package required: pip install eth-account")
        
        account = Account.from_key(self.private_key)
        self.wallet_address = account.address
        print(f"🔑 Using wallet: {self.wallet_address[:10]}...{self.wallet_address[-6:]}")
        
        # Request challenge
        challenge_res = requests.post(
            f"{self.API_BASE}/v1/agents/me/evm/challenge",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "address": account.address,
                "chain_id": self.CHAIN_ID
            }
        )
        
        if challenge_res.status_code != 200:
            raise Exception(f"Challenge failed: {challenge_res.status_code}")
        
        challenge = _safe_json(challenge_res)
        if not challenge.get("success"):
            raise Exception(f"Challenge error: {challenge.get('error')}")
        
        nonce = challenge["data"]["nonce"]
        typed_data = challenge["data"]["typed_data"]
        print(f"📋 Challenge received, nonce: {nonce[:16]}...")
        
        # Sign typed data
        full_message = {
            "types": typed_data["types"],
            "primaryType": typed_data["primaryType"],
            "domain": typed_data["domain"],
            "message": typed_data["message"]
        }
        
        signable = encode_typed_data(full_message=full_message)
        signed = account.sign_message(signable)
        signature = signed.signature.hex()
        if not signature.startswith("0x"):
            signature = "0x" + signature
        
        # Verify
        verify_res = requests.post(
            f"{self.API_BASE}/v1/agents/me/evm/verify",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "nonce": nonce,
                "signature": signature
            }
        )
        
        if verify_res.status_code != 200:
            raise Exception(f"Verify failed: {verify_res.status_code}")
        
        result = _safe_json(verify_res)
        if not result.get("success"):
            raise Exception(f"Verify error: {result.get('error')}")
        
        self.evm_wallet_linked = True
        evm_wallet = result.get("data", {}).get("evm_wallet")
        if isinstance(evm_wallet, dict):
            self.wallet_address = evm_wallet.get("address")
        elif isinstance(evm_wallet, str):
            self.wallet_address = evm_wallet
        else:
            self.wallet_address = account.address
        print(f"✅ Wallet linked: {evm_wallet}")
        return True
    
    def auto_link_wallet(self) -> bool:
        """Auto-link wallet if credentials are available"""
        if not hasattr(self, 'private_key') or not self.private_key:
            print("⚠️  Cannot auto-link wallet: missing private_key")
            return False
        
        try:
            if self.link_wallet():
                self.evm_wallet_linked = True
                self.evm_wallet_address = self.wallet_address
                if isinstance(self.wallet_address, str) and len(self.wallet_address) >= 16:
                    print(f"🔗 EVM wallet auto-linked: {self.wallet_address[:10]}...{self.wallet_address[-6:]}")
                else:
                    print(f"🔗 EVM wallet auto-linked: {self.wallet_address}")
                return True
        except Exception as e:
            print(f"❌ Auto-link wallet failed: {e}")
        return False
    
    # =========================================================================
    # WORLD STATE ADAPTER - Platform integration
    # =========================================================================
    
    def get_platform_adapter(self):
        """Get MoltX platform adapter for World State"""
        if PlatformAdapter is None:
            return None
        return MoltxAdapter(self)


class MoltxAdapter:
    """MoltX platform adapter for World State integration"""
    
    def __init__(self, moltx_plugin):
        self.plugin = moltx_plugin
    
    def get_platform_name(self) -> str:
        return "moltx"
    
    def is_available(self) -> bool:
        return (
            self.plugin is not None and 
            getattr(self.plugin, 'initialized', False)
        )
    
    def fetch_recent_interactions(self, limit: int = 50, since: Optional[str] = None) -> List:
        """Fetch recent posts from Moltx"""
        if PlatformInteraction is None:
            return []
        
        interactions = []
        try:
            feed_result = self.plugin.get_feed(feed_type='global', limit=limit)
            posts = []
            
            if isinstance(feed_result, dict):
                posts = feed_result.get('posts') or feed_result.get('data', {}).get('posts', [])
            elif isinstance(feed_result, list):
                posts = feed_result
            
            for post in posts:
                interaction = self._convert_post_to_interaction(post)
                if interaction:
                    interactions.append(interaction)
        except Exception as e:
            print(f"⚠️ MoltxAdapter fetch failed: {e}")
        
        return interactions
    
    def fetch_entities(self, entity_type: Optional[str] = None, limit: int = 50) -> List:
        """Fetch entities from Moltx"""
        if PlatformEntity is None:
            return []
        
        entities = []
        try:
            if entity_type is None or entity_type == 'post':
                feed_result = self.plugin.get_feed(feed_type='global', limit=limit)
                posts = []
                
                if isinstance(feed_result, dict):
                    posts = feed_result.get('posts') or feed_result.get('data', {}).get('posts', [])
                elif isinstance(feed_result, list):
                    posts = feed_result
                
                for post in posts:
                    entity = self._convert_post_to_entity(post)
                    if entity:
                        entities.append(entity)
        except Exception as e:
            print(f"⚠️ MoltxAdapter fetch_entities failed: {e}")
        
        return entities
    
    def fetch_relationships(self, entity_id: Optional[str] = None, limit: int = 100) -> List:
        """Fetch relationships from Moltx"""
        if PlatformRelationship is None:
            return []
        
        relationships = []
        try:
            feed_result = self.plugin.get_feed(feed_type='mentions', limit=limit)
            posts = []
            
            if isinstance(feed_result, dict):
                posts = feed_result.get('posts') or feed_result.get('data', {}).get('posts', [])
            elif isinstance(feed_result, list):
                posts = feed_result
            
            for post in posts:
                author = post.get('agent_name') or post.get('author_name') or 'unknown'
                mentions = self._extract_mentions(post.get('content', ''))
                
                for mention in mentions:
                    rel = PlatformRelationship(
                        from_entity=f"moltx_{author.lstrip('@')}",
                        to_entity=f"moltx_{mention}",
                        relation_type='mentioned',
                        platform='moltx',
                        strength=0.5,
                        timestamp=post.get('created_at')
                    )
                    relationships.append(rel)
        except Exception as e:
            print(f"⚠️ MoltxAdapter fetch_relationships failed: {e}")
        
        return relationships
    
    def _convert_post_to_interaction(self, post: dict):
        """Convert Moltx post to standardized interaction"""
        try:
            post_id = post.get('id') or post.get('post_id')
            author = post.get('agent_name') or post.get('author_name') or 'unknown'
            content = post.get('content') or post.get('text') or ''
            
            if not post_id:
                return None
            
            return PlatformInteraction(
                id=f"moltx_{post_id}",
                type='post',
                platform='moltx',
                actor_id=author.lstrip('@'),
                content=content,
                timestamp=post.get('created_at') or datetime.now().isoformat(),
                engagement_metrics={
                    'likes': post.get('likes_count', 0) or post.get('like_count', 0),
                    'replies': post.get('replies_count', 0) or post.get('reply_count', 0),
                    'views': post.get('views_count', 0) or post.get('views', 0)
                },
                hashtags=self._extract_hashtags(content),
                mentions=self._extract_mentions(content)
            )
        except Exception as e:
            print(f"⚠️ Failed to convert Moltx post: {e}")
            return None
    
    def _convert_post_to_entity(self, post: dict):
        """Convert Moltx post to entity"""
        try:
            post_id = post.get('id') or post.get('post_id')
            author = post.get('agent_name') or post.get('author_name') or 'unknown'
            content = post.get('content') or ''
            
            if not post_id:
                return None
            
            return PlatformEntity(
                id=f"moltx_post_{post_id}",
                type='post',
                platform='moltx',
                name=f"Post {str(post_id)[:8]}",
                display_name=f"@{author}'s post",
                attributes={
                    'author': author,
                    'content_preview': content[:100] if content else '',
                    'likes': post.get('likes_count', 0) or post.get('like_count', 0),
                    'replies': post.get('replies_count', 0) or post.get('reply_count', 0)
                },
                created_at=post.get('created_at'),
                url=f"https://moltx.io/post/{post_id}"
            )
        except Exception as e:
            print(f"⚠️ Failed to convert Moltx post to entity: {e}")
            return None
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract #hashtags from content"""
        return re.findall(r'#(\w+)', content or '')
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from content"""
        return re.findall(r'@(\w+)', content or '')
