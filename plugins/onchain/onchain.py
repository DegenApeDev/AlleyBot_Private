"""
On-Chain Plugin for AlleyBot
Web3 connection, wallet management, token tracking, and transaction monitoring on Base network.

Split into mixins for maintainability:
- web3_provider.py: Web3 connection, balance checks, contract reads
- token_tracker.py: ERC-20 token tracking and balance snapshots
- tx_monitor.py: Transaction monitoring, address watching, heartbeat
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin
from plugins.onchain.web3_provider import Web3Provider, ALLEYBOT_TOKEN, WEB3_AVAILABLE
from plugins.onchain.token_tracker import TokenTrackerMixin, KNOWN_TOKENS
from plugins.onchain.tx_monitor import TxMonitorMixin
from plugins.onchain.onchain_actions import OnChainActionsMixin


class OnChainPlugin(TokenTrackerMixin, TxMonitorMixin, OnChainActionsMixin, AlleyBotPlugin):
    """On-chain capabilities plugin for Base network"""

    def __init__(self, config):
        super().__init__(config)
        self.web3_provider = None
        self.tracked_tokens = {}
        self.token_snapshots = []

    def initialize(self, api, core):
        """Initialize on-chain plugin and connect to Base network"""
        super().initialize(api, core)

        if not WEB3_AVAILABLE:
            print("⚠️  On-chain plugin disabled: web3 not installed")
            return

        # Initialize Web3 provider
        network = self.config.get('network', 'mainnet')
        self.web3_provider = Web3Provider(network=network)
        connected = self.web3_provider.connect()

        if connected:
            # Initialize sub-systems
            self._init_token_tracker()
            self._init_tx_monitor()
            self._init_onchain_actions()

            # Auto-track AlleyBot token
            if 'ALYBOT' not in self.tracked_tokens:
                self.tracked_tokens['ALYBOT'] = ALLEYBOT_TOKEN
                self._save_tracked_tokens()

            # Show initial balance
            eth_result = self.web3_provider.get_eth_balance()
            if eth_result['success']:
                print(f"  Ξ Balance: {eth_result['balance_eth']:.6f} ETH")

            alley_result = self.web3_provider.get_token_balance(ALLEYBOT_TOKEN['address'])
            if alley_result['success']:
                print(f"  🪙 ALYBOT: {alley_result['balance']:,.4f}")

            print("✅ On-chain plugin ready")
        else:
            print("⚠️  On-chain plugin: Web3 connection failed, commands will be limited")

    def wallet_command(self, *args):
        """Show wallet info and balances"""
        if not self.web3_provider or not self.web3_provider.connected:
            return "❌ Web3 not connected. Check BASE_RPC_URL or network connectivity."

        if not self.web3_provider.wallet_address:
            return "❌ No wallet configured. Set BASE_WALLET_PUBLIC_ADDRESS in .env"

        addr = self.web3_provider.wallet_address
        output = "🔗 On-Chain Wallet\n\n"
        output += f"  📍 Address: {addr}\n"
        output += f"  🌐 Network: {self.web3_provider.network_config['name']}\n"
        output += f"  🔗 Explorer: {self.web3_provider.network_config['explorer']}/address/{addr}\n\n"

        # ETH balance
        eth_result = self.web3_provider.get_eth_balance()
        if eth_result['success']:
            output += f"  Ξ ETH: {eth_result['balance_eth']:.6f}\n"

        # Tracked token balances
        for symbol, token_info in self.tracked_tokens.items():
            result = self.web3_provider.get_token_balance(token_info['address'])
            if result['success']:
                output += f"  🪙 {symbol}: {result['balance']:,.4f}\n"

        return output

    def block_info_command(self, *args):
        """Show current block information"""
        if not self.web3_provider or not self.web3_provider.connected:
            return "❌ Web3 not connected"

        result = self.web3_provider.get_block_info()
        if not result['success']:
            return f"❌ Error: {result['error']}"

        output = "📦 Block Info\n\n"
        output += f"  🔢 Block: {result['block_number']:,}\n"
        output += f"  ⛽ Gas Price: {result['gas_price_gwei']:.2f} gwei\n"
        output += f"  📊 Transactions: {result['transactions_count']}\n"
        output += f"  🌐 Network: {result['network']}\n"

        return output

    def contract_read_command(self, *args):
        """Read a public contract function. Usage: onchain_read <address> <function> [args...]"""
        if not args or len(args) < 2:
            return "❌ Usage: onchain_read <contract_address> <function_name> [args...]\nExample: onchain_read 0x... balanceOf 0x..."

        if not self.web3_provider or not self.web3_provider.connected:
            return "❌ Web3 not connected"

        contract_address = args[0]
        function_name = args[1]
        fn_args = list(args[2:]) if len(args) > 2 else []

        # For common functions, use ERC20 ABI
        from plugins.onchain.web3_provider import ERC20_ABI
        result = self.web3_provider.read_contract(contract_address, ERC20_ABI, function_name, *fn_args)

        if not result['success']:
            return f"❌ Contract read failed: {result['error']}"

        output = "📜 Contract Read Result\n\n"
        output += f"  📍 Contract: {result['contract'][:10]}...{result['contract'][-6:]}\n"
        output += f"  🔧 Function: {result['function']}\n"
        output += f"  📊 Result: {result['result']}\n"

        return output

    def onchain_status_command(self, *args):
        """Show on-chain plugin status"""
        output = "🔗 On-Chain Status\n\n"

        if not WEB3_AVAILABLE:
            output += "❌ web3 package not installed\n"
            return output

        if not self.web3_provider:
            output += "❌ Web3 provider not initialized\n"
            return output

        output += f"  🌐 Network: {self.web3_provider.network_config['name']}\n"
        output += f"  {'✅' if self.web3_provider.connected else '❌'} Connected: {self.web3_provider.connected}\n"

        if self.web3_provider.wallet_address:
            output += f"  💰 Wallet: {self.web3_provider.wallet_address[:10]}...{self.web3_provider.wallet_address[-6:]}\n"
        else:
            output += "  ⚠️  Wallet: Not configured\n"

        output += f"  🪙 Tracked Tokens: {len(self.tracked_tokens)}\n"
        for symbol in self.tracked_tokens:
            output += f"     - {symbol}\n"

        output += f"  👁️  Watched Addresses: {len(self.watched_addresses)}\n"

        if self.last_seen_block:
            output += f"  📦 Last Block: {self.last_seen_block:,}\n"

        output += f"  📊 TX History: {len(self.tx_history)} events\n"

        return output

    def get_tasks(self):
        """Return scheduled tasks"""
        tasks = {}

        if self.config.get('heartbeat_enabled', True) and self.web3_provider and self.web3_provider.connected:
            tasks['onchain_heartbeat'] = {
                'function': self.onchain_heartbeat,
                'schedule': '*/10 * * * *',
                'description': 'Monitor on-chain balances and transactions'
            }

        return tasks

    def get_commands(self):
        """Return CLI commands"""
        return {
            'onchain_wallet': self.wallet_command,
            'onchain_balance': self.token_balances_command,
            'onchain_track': self.track_token_command,
            'onchain_untrack': self.untrack_token_command,
            'onchain_block': self.block_info_command,
            'onchain_tx': self.tx_lookup_command,
            'onchain_activity': self.recent_activity_command,
            'onchain_watch': self.watch_address_command,
            'onchain_unwatch': self.unwatch_address_command,
            'onchain_read': self.contract_read_command,
            'onchain_status': self.onchain_status_command,
            'onchain_heartbeat': self.onchain_heartbeat,
            'onchain_tip': self.tip_command,
            'onchain_tipstats': self.tipstats_command,
        }

    def get_endpoints(self):
        """Return web endpoints"""
        return {}

    def cleanup(self):
        """Cleanup on-chain plugin"""
        if self.web3_provider:
            self._save_tracked_tokens()
            self._save_tx_state()
            self._save_actions_state()
            print("🔗 On-chain plugin cleaned up")
