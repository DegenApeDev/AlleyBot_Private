"""
Dynamic ERC-8004 Agent Card Generator
Builds agent-card.json from loaded plugins, commands, and capabilities at runtime.
AlleyBot agent ID: 22899 on Ethereum mainnet.
"""
import json
import datetime
import hashlib
from typing import Dict, Any, List, Optional


# ERC-8004 constants
AGENT_ID = 22899
IDENTITY_REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
CHAIN_ID = 1  # Ethereum mainnet

# Static profile fields
AGENT_NAME = "AlleyBot"
AGENT_DESCRIPTION = (
    "Autonomous AI agent with advanced capabilities across Moltx, MoltBook, MoltChan, "
    "MoltRoad, and Clawbr. Features AI-powered content generation, intelligent engagement, "
    "on-chain awareness (Base network), self-improvement, trending analysis, "
    "multi-platform presence, multi-agent collaboration, reputation tracking, "
    "and on-chain actions (tipping, contract interaction). ERC-8004 Agent #22899."
)
AGENT_IMAGE = "https://blob.8004scan.app/3d2fb26e34f0c9a4c083adce2449905ff37a74c5fd3132114bddb69d69468ac7.jpg"
AGENT_WALLET = "0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5"

# Core OASF v0.8.0 skills (6 skills for services section)
CORE_OASF_SKILLS = [
    "natural_language_processing/natural_language_generation/dialogue_generation",
    "analytical_skills/data_analysis/blockchain_analysis",
    "analytical_skills/coding_skills/text_to_code",
    "agent_orchestration/task_decomposition",
    "natural_language_processing/natural_language_understanding/semantic_understanding",
    "advanced_reasoning_planning/strategic_planning",
]

OASF_DOMAINS = [
    "technology/blockchain",
    "technology/blockchain/cryptocurrency",
    "media_and_entertainment/content_creation",
    "technology/software_engineering/apis_integration",
]

# Plugin → OASF 0.8.0 standard skill mapping
# Slugs from https://schema.oasf.outshift.com/0.8.0
PLUGIN_SKILL_MAP = {
    'moltx': {
        'category': 'content_creation',
        'skills': [
            'natural_language_processing/natural_language_generation/dialogue_generation',
            'natural_language_processing/creative_content',
            'natural_language_processing/sentiment_analysis',
            'natural_language_processing/information_retrieval_synthesis/search',
        ],
    },
    'moltbook': {
        'category': 'content_creation',
        'skills': [
            'natural_language_processing/natural_language_generation/text_completion',
            'natural_language_processing/personalization/user_adaptation',
        ],
    },
    'moltchan': {
        'category': 'content_creation',
        'skills': [
            'natural_language_processing/natural_language_generation/story_generation',
        ],
    },
    'moltroad': {
        'category': 'content_creation',
        'skills': [
            'natural_language_processing/natural_language_generation/summarization',
        ],
    },
    'clawbr': {
        'category': 'advanced_reasoning_planning',
        'skills': [
            'advanced_reasoning_planning/debate_argumentation',
            'advanced_reasoning_planning/strategic_planning',
            'evaluation_monitoring/quality_evaluation',
        ],
    },
    'onchain': {
        'category': 'blockchain',
        'skills': [
            'analytical_skills/data_analysis/blockchain_analysis',
            'tool_interaction/api_schema_understanding',
            'evaluation_monitoring/performance_monitoring',
        ],
    },
    'crypto': {
        'category': 'blockchain',
        'skills': [
            'analytical_skills/data_analysis/market_analysis',
            'analytical_skills/data_analysis/trend_analysis',
        ],
    },
    'selfimprove': {
        'category': 'software_engineering',
        'skills': [
            'analytical_skills/coding_skills/text_to_code',
            'analytical_skills/coding_skills/code_optimization',
            'evaluation_monitoring/test_case_generation',
            'tool_interaction/workflow_automation',
        ],
    },
    'brain': {
        'category': 'reasoning',
        'skills': [
            'advanced_reasoning_planning/strategic_planning',
            'advanced_reasoning_planning/long_horizon_reasoning',
            'advanced_reasoning_planning/chain_of_thought_structuring',
            'agent_orchestration/task_decomposition',
        ],
    },
    'telegram': {
        'category': 'communication',
        'skills': [
            'natural_language_processing/natural_language_understanding/contextual_comprehension',
            'natural_language_processing/natural_language_understanding/semantic_understanding',
            'tool_interaction/tool_use_planning',
        ],
    },
    'analytics': {
        'category': 'analytics',
        'skills': [
            'evaluation_monitoring/performance_monitoring',
            'evaluation_monitoring/quality_evaluation',
        ],
    },
    'a2a': {
        'category': 'agent_orchestration',
        'skills': [
            'agent_orchestration/agent_coordination',
            'agent_orchestration/negotiation_resolution',
            'tool_interaction/api_schema_understanding',
        ],
    },
    'mcp': {
        'category': 'information_gathering',
        'skills': [
            'natural_language_processing/information_retrieval_synthesis/search',
            'natural_language_processing/information_retrieval_synthesis/knowledge_base_reasoning',
        ],
    },
    'engagement': {
        'category': 'interaction',
        'skills': [
            'interaction/user_engagement',
            'interaction/engagement_optimization',
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
            "endpoints": [
                {
                    "name": "A2A",
                    "endpoint": "https://tasks.apeshit.fun/.well-known/agent.json",
                    "version": "1.0"
                },
                {
                    "name": "OASF",
                    "endpoint": "https://schema.oasf.outshift.com/0.8.0",
                    "version": "0.8.0"
                },
                {
                    "name": "agentWallet",
                    "endpoint": "eip155:8453:0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5"
                }
            ],
            "services": [
                {
                    "name": "OASF",
                    "version": "v0.8.0",
                    "skills": CORE_OASF_SKILLS,
                    "domains": OASF_DOMAINS,
                },
                {
                    "name": "Agent Dashboard",
                    "endpoint": "https://apeshit.fun",
                },
                {
                    "name": "A2A",
                    "endpoint": "https://tasks.apeshit.fun/.well-known/agent.json",
                    "version": "1.0",
                    "a2aSkills": self._build_a2a_skills(),
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
            "supportedTrust": ["reputation", "crypto-economic", "tee-attestation"],
            "platforms": platforms,
            "capabilities": capabilities,
            "contact": {
                "telegram": "AlleyBot_Official",
            },
            "lastUpdated": datetime.datetime.utcnow().isoformat() + "Z",
        }

        return card

    def _collect_skills(self) -> List[str]:
        """Return the 6 core OASF v0.8.0 skills"""
        return list(CORE_OASF_SKILLS)

    def _collect_capabilities(self) -> List[str]:
        """Collect capability strings from loaded plugins"""
        caps = []
        loaded = self._get_loaded_plugins()

        capability_map = {
            'moltx': ['content_generation', 'cross_platform_posting', 'autonomous_engagement', 'trending_analysis'],
            'moltbook': ['forum_posting', 'community_building', 'karma_optimization'],
            'moltchan': ['channel_posting', 'community_engagement'],
            'moltroad': ['roadmap_tracking', 'project_monitoring'],
            'clawbr': ['ai_debate', 'argumentation', 'elo_ranking', 'strategic_debate'],
            'onchain': ['on_chain_awareness', 'token_tracking', 'wallet_management', 'contract_interaction'],
            'crypto': ['price_monitoring', 'market_analysis', 'trend_detection'],
            'selfimprove': ['self_improvement', 'autonomous_coding', 'skill_marketplace', 'code_generation'],
            'brain': ['autonomous_decision_making', 'ai_reasoning', 'dynamic_skill_chaining', 'capability_gap_detection'],
            'telegram': ['natural_language_interface', 'tool_dispatch', 'owner_control'],
            'analytics': ['performance_analytics', 'dashboard', 'agent_card_generation'],
            'a2a': ['agent_to_agent_protocol', 'task_delegation', 'agent_discovery', 'a2a_messaging'],
            'mcp': ['web_search', 'research', 'information_synthesis'],
            'engagement': ['smart_engagement', 'engagement_optimization'],
            'intelligence': ['sentiment_analysis', 'content_optimization'],
            'multi_agent': ['agent_detection', 'agent_collaboration', 'cross_agent_communication'],
            'reputation': ['reputation_tracking', 'reputation_optimization', 'platform_scoring'],
        }

        for plugin_name, plugin_caps in capability_map.items():
            if plugin_name in loaded:
                caps.extend(plugin_caps)

        # Always include base capabilities
        caps.extend(['x402_payments', 'erc8004_identity', 'health_monitoring', 'rate_limiting'])

        return list(dict.fromkeys(caps))  # dedupe preserving order

    def _collect_platforms(self) -> List[Dict[str, str]]:
        """Collect platform presence info"""
        platforms = []
        loaded = self._get_loaded_plugins()

        platform_info = {
            'moltx': {"name": "Moltx", "handle": "AlleyBot", "url": "https://moltx.io/AlleyBot"},
            'moltbook': {"name": "MoltBook", "handle": "AlleyBot", "url": "https://www.moltbook.com/u/AlleyBot"},
            'moltchan': {"name": "MoltChan", "handle": "AlleyBot"},
            'moltroad': {"name": "MoltRoad", "handle": "AlleyBot"},
            'clawbr': {"name": "Clawbr", "handle": "AlleyBot", "url": "https://www.clawbr.org/user/AlleyBot"},
        }

        for plugin_name, info in platform_info.items():
            if plugin_name in loaded:
                entry = dict(info)
                # Dynamically add MoltRoad profile URL if agent_id is known
                if plugin_name == 'moltroad':
                    mr_plugin = self.core.plugin_manager.plugins.get('moltroad') if self.core else None
                    if mr_plugin and getattr(mr_plugin, 'agent_id', None):
                        entry['url'] = f"https://moltroad.com/agent/{mr_plugin.agent_id}"
                platforms.append(entry)

        return platforms

    def _get_card_hash(self, card: Dict[str, Any]) -> str:
        """Generate a hash of the agent card content (excluding timestamp)"""
        # Create a copy without the timestamp for consistent hashing
        card_copy = {k: v for k, v in card.items() if k != 'lastUpdated'}
        card_json = json.dumps(card_copy, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(card_json.encode()).hexdigest()[:16]

    def _get_last_uploaded_hash(self) -> Optional[str]:
        """Get the hash of the last successfully uploaded agent card"""
        try:
            if self.core:
                return self.core.get_memory('agent_card_last_hash')
        except Exception:
            pass
        return None

    def _save_uploaded_hash(self, hash_value: str):
        """Save the hash of the successfully uploaded agent card"""
        try:
            if self.core:
                self.core.save_memory('agent_card_last_hash', hash_value)
        except Exception as e:
            print(f"⚠️ Failed to save agent card hash: {e}")

    def has_card_changed(self) -> bool:
        """Check if the agent card has changed since last upload"""
        current_card = self.generate()
        current_hash = self._get_card_hash(current_card)
        last_hash = self._get_last_uploaded_hash()
        
        if last_hash is None:
            return True  # No previous upload, so it's "changed"
        
        return current_hash != last_hash

    def get_card_change_info(self) -> Dict[str, Any]:
        """Get detailed info about what changed in the agent card"""
        current_card = self.generate()
        current_hash = self._get_card_hash(current_card)
        last_hash = self._get_last_uploaded_hash()
        
        return {
            'current_hash': current_hash,
            'last_hash': last_hash,
            'has_changed': current_hash != last_hash,
            'is_first_upload': last_hash is None,
            'skills_count': len(self._collect_skills()),
            'plugins_count': len(self._get_loaded_plugins()),
        }

    def schedule_auto_update(self, interval_hours: int = 24):
        """
        Schedule automatic agent card updates - only if content has changed
        
        Args:
            interval_hours: Hours between auto-update checks (default 24)
        """
        import threading
        import time

        def auto_update_loop():
            while True:
                try:
                    # Check if card has actually changed
                    change_info = self.get_card_change_info()
                    
                    if not change_info['has_changed']:
                        print(f"🔄 Agent card auto-check: No changes detected (hash: {change_info['current_hash'][:8]}...)")
                    else:
                        if change_info['is_first_upload']:
                            print(f"🔄 Agent card auto-check: First upload (hash: {change_info['current_hash'][:8]}...)")
                        else:
                            print(f"🔄 Agent card auto-check: Changes detected!")
                            print(f"   Previous: {change_info['last_hash'][:8]}...")
                            print(f"   Current:  {change_info['current_hash'][:8]}...")
                        
                        print(f"🔄 Auto-updating ERC-8004 agent card (scheduled every {interval_hours}h)...")
                        result = self.update_onchain(dry_run=False)
                        
                        if "✅" in result:
                            print(f"✅ Auto-update successful")
                        else:
                            print(f"⚠️ Auto-update issue: {result[:200]}")
                            
                except Exception as e:
                    print(f"❌ Auto-update failed: {e}")
                
                # Sleep for interval hours
                time.sleep(interval_hours * 3600)

        # Start auto-update thread
        update_thread = threading.Thread(target=auto_update_loop, daemon=True, name='agent-card-auto-update')
        update_thread.start()
        print(f"🔄 Agent card auto-update scheduled every {interval_hours} hours (only on changes)")

    def get_agent_card_status(self) -> Dict[str, Any]:
        """Get current agent card status and info"""
        card = self.generate()
        
        return {
            'agent_id': AGENT_ID,
            'name': AGENT_NAME,
            'version': card.get('version'),
            'skills_count': len(self._collect_skills()),
            'capabilities_count': len(card.get('capabilities', [])),
            'plugins_loaded': len(self._get_loaded_plugins()),
            'platforms': [p['name'] for p in card.get('platforms', [])],
            'last_updated': card.get('lastUpdated'),
            'wallet': AGENT_WALLET,
            'registry_url': f"https://www.8004scan.io/agents/ethereum/{AGENT_ID}",
        }

    def _build_a2a_skills(self) -> list:
        """Build A2A skill objects from the task registry with full schema + pricing."""
        a2a_skills = []
        try:
            from plugins.a2a.a2a_tasks import TASK_REGISTRY
            for task_name, task_def in TASK_REGISTRY.items():
                if task_def.get('tier') == 'owner_only':
                    continue
                skill = {
                    "id": task_name,
                    "name": task_name.replace('.', ' ').replace('_', ' ').title(),
                    "description": task_def.get('description', ''),
                    "tags": task_name.split('.'),
                }
                schema = task_def.get('schema')
                if schema:
                    skill["inputSchema"] = {"type": "object", **schema}
                price = task_def.get('price_usdc')
                if price:
                    skill["tags"].append("paid")
                    skill["pricing"] = {
                        "amount": price,
                        "currency": "USDC",
                        "network": "base",
                        "chainId": 8453,
                        "paymentAddress": AGENT_WALLET,
                    }
                else:
                    skill["tags"].append("free")
                a2a_skills.append(skill)
        except ImportError:
            pass
        return a2a_skills

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
        """Save the current agent card to a static JSON file with validation"""
        card = self.generate()
        # Validate before saving
        is_valid, errors = self.validate_card(card)
        if not is_valid:
            print(f"⚠️ Agent card validation warnings: {errors}")
        with open(path, 'w') as f:
            json.dump(card, f, indent=2)
        return path

    def validate_card(self, card: Dict[str, Any]) -> tuple:
        """Validate ERC-8004 compliance of agent card
        
        Returns:
            (is_valid: bool, errors: list of strings)
        """
        errors = []
        
        # Required top-level fields
        required_fields = ['type', 'name', 'description', 'image', 'endpoints', 'registrations']
        for field in required_fields:
            if field not in card:
                errors.append(f"Missing required field: {field}")
        
        # Validate endpoints array
        if 'endpoints' in card:
            if not isinstance(card['endpoints'], list):
                errors.append("'endpoints' must be an array")
            elif len(card['endpoints']) == 0:
                errors.append("'endpoints' array cannot be empty")
            else:
                for i, ep in enumerate(card['endpoints']):
                    if 'name' not in ep:
                        errors.append(f"Endpoint {i} missing 'name'")
                    if 'endpoint' not in ep:
                        errors.append(f"Endpoint {i} missing 'endpoint'")
        
        # Validate supportedTrust values
        valid_trust_models = {'reputation', 'crypto-economic', 'tee-attestation'}
        if 'supportedTrust' in card:
            for trust in card['supportedTrust']:
                if trust not in valid_trust_models:
                    errors.append(f"Invalid trust model: {trust}. Use: {valid_trust_models}")
        
        # Validate registrations
        if 'registrations' in card:
            if not isinstance(card['registrations'], list):
                errors.append("'registrations' must be an array")
            for i, reg in enumerate(card['registrations']):
                if 'agentId' not in reg:
                    errors.append(f"Registration {i} missing 'agentId'")
                if 'agentRegistry' not in reg:
                    errors.append(f"Registration {i} missing 'agentRegistry'")
        
        # Validate JSON serializable
        try:
            json.dumps(card)
        except (TypeError, ValueError) as e:
            errors.append(f"JSON serialization error: {e}")
        
        return len(errors) == 0, errors

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

        # Check if card has actually changed (skip if same)
        if not dry_run:
            current_hash = self._get_card_hash(card)
            last_hash = self._get_last_uploaded_hash()
            if last_hash and current_hash == last_hash:
                return f"⏭️ Agent card unchanged (hash: {current_hash[:16]}...), skipping on-chain update"

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
            import time as _time
            eth_rpcs = [
                os.getenv('ETH_RPC_URL'),
                'https://ethereum-rpc.publicnode.com',
                'https://eth.drpc.org',
                'https://rpc.ankr.com/eth',
                'https://1rpc.io/eth',
                'https://eth.meowrpc.com',
                'https://rpc.payload.de',
                'https://eth.llamarpc.com',
            ]
            eth_rpcs = [r for r in eth_rpcs if r]  # remove None

            w3 = None
            for i, rpc_url in enumerate(eth_rpcs):
                try:
                    candidate = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 15}))
                    if candidate.is_connected():
                        w3 = candidate
                        print(f"🔗 Connected to Ethereum via {rpc_url}")
                        break
                except Exception as rpc_err:
                    print(f"⚠️ RPC failed: {rpc_url} ({rpc_err})")
                    if i < len(eth_rpcs) - 1:
                        _time.sleep(1)  # brief pause before next attempt

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
            
            # Register tx hash as safe to display
            try:
                from tx_registry import register_tx
                register_tx(tx_hex)
                print(f"🔐 Tx hash registered as safe: {tx_hex[:20]}...")
            except ImportError:
                pass
            
            print(f"⏳ Waiting for confirmation...")

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

            if receipt['status'] == 1:
                # Save hash of successfully uploaded card
                card_hash = self._get_card_hash(card)
                self._save_uploaded_hash(card_hash)
                
                return (
                    f"✅ ERC-8004 profile updated on-chain!\n"
                    f"🆔 Agent #{AGENT_ID}\n"
                    f"📌 IPFS: {ipfs_uri}\n"
                    f"📊 {skill_count} skills from {len(self._get_loaded_plugins())} plugins\n"
                    f"🔐 Hash: {card_hash[:16]}...\n"
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
