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
    'onchain': {
        'category': 'blockchain',
        'skills': [
            'analytical_skills/data_analysis/blockchain_analysis',
            'tool_interaction/api_schema_understanding',
            'evaluation_monitoring/performance_monitoring',
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
        'category': 'interoperability',
        'skills': [
            'interoperability/agent_to_agent_protocol',
            'interoperability/task_delegation',
            'interoperability/agent_discovery',
            'interoperability/x402_payment_gate',
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
                    "domains": [
                        "technology/blockchain",
                        "technology/blockchain/cryptocurrency",
                        "media_and_entertainment/content_creation",
                        "technology/software_engineering/apis_integration",
                    ],
                },
                {
                    "name": "Agent Dashboard",
                    "endpoint": "https://apeshit.fun",
                },
                {
                    "name": "A2A",
                    "endpoint": "https://apeshit.fun/.well-known/agent-card.json",
                    "version": "0.3.0",
                    "a2aSkills": skills,
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
            'a2a': ['agent_to_agent_protocol', 'task_delegation', 'agent_discovery'],
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

    def update_onchain(self, dry_run: bool = False) -> str:
        """Update AlleyBot's ERC-8004 on-chain profile with current skills.

        Calls updateRegistration(uint256 agentId, string registrationURI) on
        the Identity Registry contract on Ethereum mainnet.

        Args:
            dry_run: If True, generate the data URI but don't send the tx.

        Returns:
            Status message string.
        """
        import os

        data_uri = self.to_data_uri()
        skill_count = len(self._collect_skills())

        if dry_run:
            card = self.generate()
            skills_preview = '\n'.join(f"  - {s}" for s in card.get('capabilities', [])[:10])
            return (
                f"🆔 ERC-8004 Agent #{AGENT_ID} — Dry Run\n"
                f"📊 {skill_count} OASF skills from {len(self._get_loaded_plugins())} plugins\n"
                f"📝 Data URI length: {len(data_uri)} chars\n\n"
                f"Capabilities preview:\n{skills_preview}\n\n"
                f"Use without dry_run to submit the on-chain transaction."
            )

        # Need private key for Ethereum mainnet tx
        private_key = os.getenv('BASE_WALLET_PRIVATE_KEY') or os.getenv('ETH_PRIVATE_KEY')
        if not private_key:
            return "❌ No private key found. Set BASE_WALLET_PRIVATE_KEY or ETH_PRIVATE_KEY in .env"

        try:
            from web3 import Web3

            # Connect to Ethereum mainnet
            eth_rpc = os.getenv('ETH_RPC_URL', 'https://eth.llamarpc.com')
            w3 = Web3(Web3.HTTPProvider(eth_rpc))
            if not w3.is_connected():
                return "❌ Failed to connect to Ethereum mainnet"

            account = w3.eth.account.from_key(private_key)

            # Check ETH balance
            balance = w3.eth.get_balance(account.address)
            balance_eth = w3.from_wei(balance, 'ether')
            if balance_eth < 0.005:
                return f"❌ Insufficient ETH on mainnet ({balance_eth:.4f} ETH). Need ~0.005 ETH for gas."

            # ERC-8004 updateRegistration ABI
            abi = [
                {
                    "inputs": [
                        {"name": "agentId", "type": "uint256"},
                        {"name": "registrationURI", "type": "string"},
                    ],
                    "name": "updateRegistration",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function",
                }
            ]

            contract = w3.eth.contract(address=IDENTITY_REGISTRY, abi=abi)
            nonce = w3.eth.get_transaction_count(account.address)

            # Estimate gas
            try:
                gas_estimate = contract.functions.updateRegistration(
                    AGENT_ID, data_uri
                ).estimate_gas({'from': account.address})
            except Exception:
                gas_estimate = 300000  # fallback

            gas_price = w3.eth.gas_price
            total_cost = w3.from_wei(gas_estimate * gas_price, 'ether')

            # Build and send tx
            tx = contract.functions.updateRegistration(
                AGENT_ID, data_uri
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

            print(f"📤 ERC-8004 update tx sent: {tx_hex}")
            print(f"⏳ Waiting for confirmation...")

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

            if receipt['status'] == 1:
                return (
                    f"✅ ERC-8004 profile updated on-chain!\n"
                    f"🆔 Agent #{AGENT_ID}\n"
                    f"📊 {skill_count} skills from {len(self._get_loaded_plugins())} plugins\n"
                    f"⛽ Gas used: {receipt['gasUsed']}\n"
                    f"💵 Cost: {total_cost:.6f} ETH\n"
                    f"🔗 https://etherscan.io/tx/{tx_hex}"
                )
            else:
                return f"❌ Transaction failed. https://etherscan.io/tx/{tx_hex}"

        except ImportError:
            return "❌ web3 package not installed"
        except Exception as e:
            return f"❌ ERC-8004 update failed: {e}"
