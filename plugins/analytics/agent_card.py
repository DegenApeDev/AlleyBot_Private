"""
Dynamic ERC-8004 Agent Card Generator
Builds agent-card.json from loaded plugins, commands, and capabilities at runtime.
AlleyBot agent ID: 22899 on Ethereum mainnet.
"""
import json
import datetime
from typing import Dict, Any, List, Optional


# ERC-8004 constants
AGENT_ID = 22899
IDENTITY_REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
CHAIN_ID = 1  # Ethereum mainnet

# Static profile fields
AGENT_NAME = "AlleyBot"
AGENT_DESCRIPTION = (
    "Autonomous AI agent with advanced capabilities across Moltx, MoltBook, MoltChan, "
    "and MoltRoad. Features AI-powered content generation, intelligent engagement, "
    "on-chain awareness (Base network), self-improvement, trending analysis, "
    "and multi-platform presence."
)
AGENT_IMAGE = "https://blob.8004scan.app/3d2fb26e34f0c9a4c083adce2449905ff37a74c5fd3132114bddb69d69468ac7.jpg"
AGENT_WALLET = "0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5"

# Plugin → skill category mapping
PLUGIN_SKILL_MAP = {
    'moltx': {
        'category': 'social_media',
        'skills': [
            'content_generation/ai_post_creation',
            'social_engagement/feed_interaction',
            'social_engagement/comment_reply',
            'analytics/trending_analysis',
            'messaging/direct_messages',
        ],
    },
    'moltbook': {
        'category': 'social_media',
        'skills': [
            'content_generation/forum_posting',
            'social_engagement/community_engagement',
            'social_engagement/comment_interaction',
        ],
    },
    'moltchan': {
        'category': 'social_media',
        'skills': [
            'content_generation/channel_posting',
            'social_engagement/channel_engagement',
        ],
    },
    'moltroad': {
        'category': 'social_media',
        'skills': [
            'content_generation/roadmap_posting',
            'social_engagement/roadmap_engagement',
        ],
    },
    'onchain': {
        'category': 'blockchain',
        'skills': [
            'blockchain/wallet_management',
            'blockchain/token_tracking',
            'blockchain/transaction_monitoring',
            'blockchain/erc20_balance_reads',
            'blockchain/base_network_awareness',
        ],
    },
    'selfimprove': {
        'category': 'self_improvement',
        'skills': [
            'self_improvement/autonomous_code_generation',
            'self_improvement/skill_marketplace',
            'self_improvement/git_workflow',
            'self_improvement/test_gated_updates',
            'self_improvement/platform_skill_sync',
        ],
    },
    'brain': {
        'category': 'reasoning',
        'skills': [
            'advanced_reasoning_planning/autonomous_decision_making',
            'advanced_reasoning_planning/strategic_planning',
            'advanced_reasoning_planning/context_gathering',
            'advanced_reasoning_planning/smart_reply_generation',
        ],
    },
    'telegram': {
        'category': 'communication',
        'skills': [
            'communication/natural_language_understanding',
            'communication/tool_dispatch_from_chat',
            'communication/owner_command_interface',
        ],
    },
    'analytics': {
        'category': 'analytics',
        'skills': [
            'analytics/platform_metrics_aggregation',
            'analytics/performance_dashboard',
        ],
    },
}


class AgentCardGenerator:
    """Generates dynamic ERC-8004 agent card from loaded plugins"""

    def __init__(self, core=None):
        self.core = core

    def generate(self) -> Dict[str, Any]:
        """Generate the full agent card JSON"""
        skills = self._collect_skills()
        capabilities = self._collect_capabilities()
        platforms = self._collect_platforms()

        card = {
            "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
            "name": AGENT_NAME,
            "description": AGENT_DESCRIPTION,
            "image": AGENT_IMAGE,
            "version": self._get_version(),
            "services": [
                {
                    "name": "OASF",
                    "endpoint": "https://github.com/agntcy/oasf/",
                    "version": "v0.8.0",
                    "skills": skills,
                    "domains": ["social_media", "blockchain", "ai_agents"],
                },
                {
                    "name": "Agent Dashboard",
                    "endpoint": "https://apeshit.fun",
                },
                {
                    "name": "A2A",
                    "endpoint": "https://alleybot.xyz/.well-known/agent-card.json",
                    "version": "0.3.0",
                },
            ],
            "x402Support": True,
            "x402Payment": {
                "enabled": True,
                "address": AGENT_WALLET,
                "network": "base",
                "chainId": 8453,
                "acceptedCurrencies": ["ETH", "USDC"],
            },
            "active": True,
            "registrations": [
                {
                    "agentId": AGENT_ID,
                    "agentRegistry": f"eip155:{CHAIN_ID}:{IDENTITY_REGISTRY}",
                }
            ],
            "supportedTrust": ["reputation"],
            "platforms": platforms,
            "capabilities": capabilities,
            "contact": {
                "telegram": "AlleyBot_Official",
            },
            "lastUpdated": datetime.datetime.utcnow().isoformat() + "Z",
        }

        return card

    def _collect_skills(self) -> List[str]:
        """Collect OASF skills from all loaded plugins"""
        skills = []
        loaded_plugins = self._get_loaded_plugins()

        for plugin_name, skill_info in PLUGIN_SKILL_MAP.items():
            if plugin_name in loaded_plugins:
                skills.extend(skill_info['skills'])

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for s in skills:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        return unique

    def _collect_capabilities(self) -> List[str]:
        """Collect capability strings from loaded plugins"""
        caps = []
        loaded = self._get_loaded_plugins()

        capability_map = {
            'moltx': ['content_generation', 'cross_platform_posting', 'autonomous_engagement'],
            'moltbook': ['forum_posting', 'community_building'],
            'moltchan': ['channel_posting'],
            'moltroad': ['roadmap_tracking'],
            'onchain': ['on_chain_awareness', 'token_tracking', 'wallet_management'],
            'selfimprove': ['self_improvement', 'autonomous_coding', 'skill_marketplace'],
            'brain': ['autonomous_decision_making', 'ai_reasoning'],
            'telegram': ['natural_language_interface', 'tool_dispatch'],
            'analytics': ['performance_analytics', 'dashboard'],
        }

        for plugin_name, plugin_caps in capability_map.items():
            if plugin_name in loaded:
                caps.extend(plugin_caps)

        # Always include base capabilities
        caps.extend(['x402_payments', 'erc8004_identity'])

        return list(dict.fromkeys(caps))  # dedupe preserving order

    def _collect_platforms(self) -> List[Dict[str, str]]:
        """Collect platform presence info"""
        platforms = []
        loaded = self._get_loaded_plugins()

        platform_info = {
            'moltx': {"name": "Moltx", "handle": "AlleyBot", "url": "https://moltx.io/AlleyBot"},
            'moltbook': {"name": "MoltBook", "handle": "AlleyBot", "url": "https://www.moltbook.com/agent/AlleyBot"},
            'moltchan': {"name": "MoltChan", "handle": "AlleyBot", "url": "https://moltchan.io/AlleyBot"},
            'moltroad': {"name": "MoltRoad", "handle": "AlleyBot", "url": "https://moltroad.io/AlleyBot"},
        }

        for plugin_name, info in platform_info.items():
            if plugin_name in loaded:
                platforms.append(info)

        # Always include 4claw (ERC-8004 registry)
        platforms.append({
            "name": "4claw",
            "handle": "AlleyBot",
            "url": f"https://www.4claw.org/agent/{AGENT_ID}",
        })

        return platforms

    def _get_loaded_plugins(self) -> set:
        """Get set of currently loaded plugin names"""
        if self.core and hasattr(self.core, 'plugin_manager'):
            return set(self.core.plugin_manager.plugins.keys())
        # Fallback: assume all plugins are available
        return set(PLUGIN_SKILL_MAP.keys())

    def _get_version(self) -> str:
        """Generate version string based on plugin count and date"""
        loaded = self._get_loaded_plugins()
        plugin_count = len(loaded)
        date_str = datetime.datetime.utcnow().strftime('%Y%m%d')
        return f"2.{plugin_count}.0-{date_str}"

    def to_data_uri(self) -> str:
        """Generate base64 data URI for on-chain registration"""
        import base64
        card = self.generate()
        card_json = json.dumps(card, indent=2)
        card_b64 = base64.b64encode(card_json.encode()).decode()
        return f"data:application/json;base64,{card_b64}"

    def save_static(self, path: str):
        """Save the current agent card to a static JSON file"""
        card = self.generate()
        with open(path, 'w') as f:
            json.dump(card, f, indent=2)
        return path

    def _upload_to_ipfs(self, card_json: str) -> str:
        """Upload agent card JSON to IPFS and return the ipfs:// URI.

        Uses Pinata pinning service (requires PINATA_JWT in .env).
        Falls back to web3.storage if Pinata is unavailable.

        Returns:
            IPFS URI string like 'ipfs://bafkrei...'
        """
        import os
        import requests

        # ── Pinata v3 API (preferred) ─────────────────────────────────
        pinata_jwt = os.getenv('PINATA_JWT')
        if pinata_jwt:
            print("📌 Uploading agent card to IPFS via Pinata v3...")
            resp = requests.post(
                'https://uploads.pinata.cloud/v3/files',
                headers={
                    'Authorization': f'Bearer {pinata_jwt}',
                },
                files={
                    'file': ('agent-card.json', card_json.encode(), 'application/json'),
                },
                data={
                    'network': 'public',
                    'name': f'AlleyBot-agent-card-{AGENT_ID}',
                },
                timeout=30,
            )
            resp.raise_for_status()
            cid = resp.json()['data']['cid']
            ipfs_uri = f"ipfs://{cid}"
            print(f"✅ Pinned to IPFS: {ipfs_uri}")
            return ipfs_uri

        # ── Infura IPFS ────────────────────────────────────────────
        infura_project_id = os.getenv('INFURA_IPFS_PROJECT_ID')
        infura_secret = os.getenv('INFURA_IPFS_SECRET')
        if infura_project_id and infura_secret:
            print("📌 Uploading agent card to IPFS via Infura...")
            resp = requests.post(
                'https://ipfs.infura.io:5001/api/v0/add',
                auth=(infura_project_id, infura_secret),
                files={'file': ('agent-card.json', card_json.encode(), 'application/json')},
                timeout=30,
            )
            resp.raise_for_status()
            ipfs_hash = resp.json()['Hash']
            ipfs_uri = f"ipfs://{ipfs_hash}"
            print(f"✅ Pinned to IPFS: {ipfs_uri}")
            return ipfs_uri

        raise RuntimeError(
            "No IPFS provider configured. Set PINATA_JWT or "
            "INFURA_IPFS_PROJECT_ID + INFURA_IPFS_SECRET in .env"
        )

    def update_onchain(self, dry_run: bool = False) -> str:
        """Update AlleyBot's ERC-8004 on-chain profile with current skills.

        1. Generates the agent card JSON from loaded plugins.
        2. Uploads it to IPFS (via Pinata or Infura).
        3. Calls setAgentURI(uint256 agentId, string uri) on the
           Identity Registry contract on Ethereum mainnet.

        Args:
            dry_run: If True, show what would be uploaded but don't send tx.

        Returns:
            Status message string.
        """
        import os

        card = self.generate()
        card_json = json.dumps(card, indent=2)
        skill_count = len(self._collect_skills())

        if dry_run:
            skills_preview = '\n'.join(f"  - {s}" for s in card.get('capabilities', [])[:10])
            return (
                f"🆔 ERC-8004 Agent #{AGENT_ID} — Dry Run\n"
                f"📊 {skill_count} OASF skills from {len(self._get_loaded_plugins())} plugins\n"
                f"📝 Card JSON size: {len(card_json)} bytes\n\n"
                f"Capabilities preview:\n{skills_preview}\n\n"
                f"Will upload to IPFS then call setAgentURI on-chain.\n"
                f"Use without dry_run to submit."
            )

        # Need private key for Ethereum mainnet tx
        private_key = os.getenv('BASE_WALLET_PRIVATE_KEY') or os.getenv('ETH_PRIVATE_KEY')
        if not private_key:
            return "❌ No private key found. Set BASE_WALLET_PRIVATE_KEY or ETH_PRIVATE_KEY in .env"

        try:
            # Step 1: Upload to IPFS
            ipfs_uri = self._upload_to_ipfs(card_json)

            from web3 import Web3

            # Step 2: Connect to Ethereum mainnet (try multiple RPCs)
            eth_rpcs = [
                os.getenv('ETH_RPC_URL'),
                'https://eth.llamarpc.com',
                'https://rpc.ankr.com/eth',
                'https://ethereum-rpc.publicnode.com',
                'https://1rpc.io/eth',
                'https://eth.drpc.org',
                'https://rpc.mevblocker.io',
            ]
            eth_rpcs = [r for r in eth_rpcs if r]  # remove None

            w3 = None
            for rpc_url in eth_rpcs:
                try:
                    candidate = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                    if candidate.is_connected():
                        w3 = candidate
                        print(f"🔗 Connected to Ethereum via {rpc_url}")
                        break
                except Exception:
                    continue

            if w3 is None:
                return (
                    f"❌ Failed to connect to Ethereum mainnet "
                    f"(tried {len(eth_rpcs)} RPCs).\n"
                    f"📌 IPFS upload succeeded: {ipfs_uri}\n"
                    f"You can manually call setAgentURI on Etherscan with this URI."
                )

            account = w3.eth.account.from_key(private_key)

            # Check ETH balance
            balance = w3.eth.get_balance(account.address)
            balance_eth = w3.from_wei(balance, 'ether')
            if balance_eth < 0.001:
                return (
                    f"❌ Insufficient ETH on mainnet ({balance_eth:.6f} ETH).\n"
                    f"📌 IPFS upload succeeded: {ipfs_uri}\n"
                    f"You can manually call setAgentURI with this URI."
                )

            # Step 3: Call setAgentURI on the Identity Registry
            abi = [
                {
                    "inputs": [
                        {"name": "agentId", "type": "uint256"},
                        {"name": "uri", "type": "string"},
                    ],
                    "name": "setAgentURI",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function",
                }
            ]

            contract = w3.eth.contract(
                address=w3.to_checksum_address(IDENTITY_REGISTRY), abi=abi
            )
            nonce = w3.eth.get_transaction_count(account.address)

            # Estimate gas
            try:
                gas_estimate = contract.functions.setAgentURI(
                    AGENT_ID, ipfs_uri
                ).estimate_gas({'from': account.address})
                gas_estimate = int(gas_estimate * 1.2)  # 20% buffer
            except Exception as e:
                print(f"⚠️ Gas estimation failed ({e}), using fallback")
                gas_estimate = 150000

            gas_price = w3.eth.gas_price
            total_cost = w3.from_wei(gas_estimate * gas_price, 'ether')

            # Build and send tx
            tx = contract.functions.setAgentURI(
                AGENT_ID, ipfs_uri
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'chainId': CHAIN_ID,
            })

            signed = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            tx_hex = tx_hash.hex()

            print(f"📤 ERC-8004 setAgentURI tx sent: {tx_hex}")
            print(f"⏳ Waiting for confirmation...")

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

            if receipt['status'] == 1:
                return (
                    f"✅ ERC-8004 profile updated on-chain!\n"
                    f"🆔 Agent #{AGENT_ID}\n"
                    f"📌 IPFS: {ipfs_uri}\n"
                    f"📊 {skill_count} skills from {len(self._get_loaded_plugins())} plugins\n"
                    f"⛽ Gas used: {receipt['gasUsed']}\n"
                    f"💵 Cost: {total_cost:.6f} ETH\n"
                    f"🔗 https://etherscan.io/tx/{tx_hex}\n"
                    f"🔍 https://www.8004scan.io/agents/ethereum/{AGENT_ID}"
                )
            else:
                return (
                    f"❌ Transaction reverted.\n"
                    f"📌 IPFS upload succeeded: {ipfs_uri}\n"
                    f"🔗 https://etherscan.io/tx/{tx_hex}"
                )

        except ImportError:
            return "❌ web3 package not installed"
        except Exception as e:
            return f"❌ ERC-8004 update failed: {e}"
