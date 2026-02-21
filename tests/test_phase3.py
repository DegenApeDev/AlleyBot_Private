#!/usr/bin/env python3
"""
Phase 3 Tests - On-Chain capabilities
Tests Web3 provider, onchain plugin, token tracking, tx monitoring,
and agentic system integration.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# 3.1 - Web3 Provider
# =============================================================================

class TestWeb3Provider(unittest.TestCase):
    """Verify Web3Provider connects to Base network"""

    def test_web3_available(self):
        """web3 package should be importable"""
        from plugins.onchain.web3_provider import WEB3_AVAILABLE
        self.assertTrue(WEB3_AVAILABLE)

    def test_provider_creation(self):
        """Web3Provider should instantiate without errors"""
        from plugins.onchain.web3_provider import Web3Provider
        p = Web3Provider('mainnet')
        self.assertEqual(p.network_config['chain_id'], 8453)
        self.assertEqual(p.network_config['name'], 'Base')
        self.assertFalse(p.connected)

    def test_provider_sepolia(self):
        """Web3Provider should support Base Sepolia testnet"""
        from plugins.onchain.web3_provider import Web3Provider
        p = Web3Provider('sepolia')
        self.assertEqual(p.network_config['chain_id'], 84532)

    def test_provider_connects_to_base(self):
        """Web3Provider should connect to Base mainnet RPC"""
        from plugins.onchain.web3_provider import Web3Provider
        p = Web3Provider('mainnet')
        connected = p.connect()
        self.assertTrue(connected)
        self.assertTrue(p.connected)
        self.assertIsNotNone(p.w3)

    def test_block_info(self):
        """Should fetch current block info from Base"""
        from plugins.onchain.web3_provider import Web3Provider
        p = Web3Provider('mainnet')
        p.connect()
        result = p.get_block_info()
        self.assertTrue(result['success'])
        self.assertGreater(result['block_number'], 40_000_000)
        self.assertEqual(result['network'], 'Base')

    def test_eth_balance_zero_address(self):
        """Should fetch ETH balance for any address"""
        from plugins.onchain.web3_provider import Web3Provider
        p = Web3Provider('mainnet')
        p.connect()
        result = p.get_eth_balance('0x0000000000000000000000000000000000000000')
        self.assertTrue(result['success'])
        self.assertIn('balance_eth', result)
        self.assertEqual(result['currency'], 'ETH')

    def test_eth_balance_not_connected(self):
        """Should return error when not connected"""
        from plugins.onchain.web3_provider import Web3Provider
        p = Web3Provider('mainnet')
        result = p.get_eth_balance('0x0000000000000000000000000000000000000000')
        self.assertFalse(result['success'])
        self.assertIn('Not connected', result['error'])

    def test_erc20_abi_defined(self):
        """ERC20 ABI should include standard functions"""
        from plugins.onchain.web3_provider import ERC20_ABI
        fn_names = [item.get('name') for item in ERC20_ABI if item.get('type') == 'function']
        self.assertIn('balanceOf', fn_names)
        self.assertIn('decimals', fn_names)
        self.assertIn('symbol', fn_names)
        self.assertIn('totalSupply', fn_names)

    def test_alleybot_token_defined(self):
        """ALLEYBOT_TOKEN constant should be defined"""
        from plugins.onchain.web3_provider import ALLEYBOT_TOKEN
        self.assertEqual(ALLEYBOT_TOKEN['symbol'], 'ALYBOT')
        self.assertTrue(ALLEYBOT_TOKEN['address'].startswith('0x'))
        self.assertEqual(ALLEYBOT_TOKEN['decimals'], 18)

    def test_token_balance_read(self):
        """Should read ERC-20 token balance from chain"""
        from plugins.onchain.web3_provider import Web3Provider, ALLEYBOT_TOKEN
        p = Web3Provider('mainnet')
        p.connect()
        result = p.get_token_balance(
            ALLEYBOT_TOKEN['address'],
            '0x0000000000000000000000000000000000000000'
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['symbol'], 'ALYBOT')
        self.assertEqual(result['decimals'], 18)

    def test_contract_read(self):
        """Should read public contract state"""
        from plugins.onchain.web3_provider import Web3Provider, ERC20_ABI, ALLEYBOT_TOKEN
        p = Web3Provider('mainnet')
        p.connect()
        result = p.read_contract(
            ALLEYBOT_TOKEN['address'], ERC20_ABI, 'symbol'
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['result'], 'ALYBOT')

    def test_transaction_lookup_invalid(self):
        """Should handle invalid tx hash gracefully"""
        from plugins.onchain.web3_provider import Web3Provider
        p = Web3Provider('mainnet')
        p.connect()
        result = p.get_transaction('0x' + '0' * 64)
        self.assertFalse(result['success'])


# =============================================================================
# 3.2 - OnChain Plugin Structure
# =============================================================================

class TestOnChainPlugin(unittest.TestCase):
    """Verify OnChainPlugin structure and commands"""

    def test_plugin_imports(self):
        """OnChainPlugin should import without errors"""
        from plugins.onchain.onchain import OnChainPlugin
        self.assertTrue(OnChainPlugin)

    def test_plugin_mro(self):
        """MRO should include both mixins and AlleyBotPlugin"""
        from plugins.onchain.onchain import OnChainPlugin
        mro_names = [c.__name__ for c in OnChainPlugin.__mro__]
        self.assertIn('TokenTrackerMixin', mro_names)
        self.assertIn('TxMonitorMixin', mro_names)
        self.assertIn('AlleyBotPlugin', mro_names)

    def test_plugin_inherits_base(self):
        """OnChainPlugin should inherit from AlleyBotPlugin"""
        from plugins.onchain.onchain import OnChainPlugin
        from plugin_manager import AlleyBotPlugin
        self.assertTrue(issubclass(OnChainPlugin, AlleyBotPlugin))

    def test_commands_registered(self):
        """All expected commands should be registered"""
        from plugins.onchain.onchain import OnChainPlugin
        p = OnChainPlugin({})
        cmds = p.get_commands()
        expected = [
            'onchain_wallet', 'onchain_balance', 'onchain_track',
            'onchain_untrack', 'onchain_block', 'onchain_tx',
            'onchain_activity', 'onchain_watch', 'onchain_unwatch',
            'onchain_read', 'onchain_status', 'onchain_heartbeat',
        ]
        for cmd in expected:
            self.assertIn(cmd, cmds, f"Missing command: {cmd}")

    def test_status_command_without_init(self):
        """Status command should work even without initialization"""
        from plugins.onchain.onchain import OnChainPlugin
        p = OnChainPlugin({})
        result = p.onchain_status_command()
        self.assertIn('On-Chain Status', result)

    def test_wallet_command_not_connected(self):
        """Wallet command should return error when not connected"""
        from plugins.onchain.onchain import OnChainPlugin
        p = OnChainPlugin({})
        result = p.wallet_command()
        self.assertIn('not connected', result.lower())


# =============================================================================
# 3.3 - Token Tracker
# =============================================================================

class TestTokenTracker(unittest.TestCase):
    """Verify token tracking functionality"""

    def test_known_tokens(self):
        """Known tokens should include ALLEY, USDC, WETH"""
        from plugins.onchain.token_tracker import KNOWN_TOKENS
        self.assertIn('ALYBOT', KNOWN_TOKENS)
        self.assertIn('USDC', KNOWN_TOKENS)
        self.assertIn('WETH', KNOWN_TOKENS)

    def test_usdc_address(self):
        """USDC address should be correct for Base"""
        from plugins.onchain.token_tracker import KNOWN_TOKENS
        self.assertEqual(
            KNOWN_TOKENS['USDC']['address'],
            '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
        )
        self.assertEqual(KNOWN_TOKENS['USDC']['decimals'], 6)

    def test_track_command_no_args(self):
        """Track command with no args should show usage"""
        from plugins.onchain.onchain import OnChainPlugin
        p = OnChainPlugin({})
        result = p.track_token_command()
        self.assertIn('Usage', result)

    def test_untrack_command_no_args(self):
        """Untrack command with no args should show usage"""
        from plugins.onchain.onchain import OnChainPlugin
        p = OnChainPlugin({})
        result = p.untrack_token_command()
        self.assertIn('Usage', result)

    def test_balance_command_not_connected(self):
        """Balance command should error when not connected"""
        from plugins.onchain.onchain import OnChainPlugin
        p = OnChainPlugin({})
        result = p.token_balances_command()
        self.assertIn('not connected', result.lower())


# =============================================================================
# 3.4 - Transaction Monitor
# =============================================================================

class TestTxMonitor(unittest.TestCase):
    """Verify transaction monitoring functionality"""

    def test_watch_command_no_args(self):
        """Watch command with no args should show usage"""
        from plugins.onchain.onchain import OnChainPlugin
        p = OnChainPlugin({})
        result = p.watch_address_command()
        self.assertIn('Usage', result)

    def test_watch_command_invalid_address(self):
        """Watch command with invalid address should error"""
        from plugins.onchain.onchain import OnChainPlugin
        p = OnChainPlugin({})
        result = p.watch_address_command('not-an-address')
        self.assertIn('Invalid', result)

    def test_tx_lookup_no_args(self):
        """TX lookup with no args should show usage"""
        from plugins.onchain.onchain import OnChainPlugin
        p = OnChainPlugin({})
        result = p.tx_lookup_command()
        self.assertIn('Usage', result)

    def test_heartbeat_not_connected(self):
        """Heartbeat should handle not-connected gracefully"""
        from plugins.onchain.onchain import OnChainPlugin
        p = OnChainPlugin({})
        result = p.onchain_heartbeat()
        self.assertIn('not connected', result.lower())


# =============================================================================
# 3.5 - Plugin Config & Integration
# =============================================================================

class TestOnChainIntegration(unittest.TestCase):
    """Verify on-chain integration with plugin system"""

    def test_plugin_config_has_onchain(self):
        """plugin_config.json should include onchain plugin"""
        import json
        config_path = PROJECT_ROOT / 'plugin_config.json'
        with open(config_path) as f:
            config = json.load(f)
        self.assertIn('onchain', config)
        self.assertTrue(config['onchain']['enabled'])
        self.assertEqual(config['onchain']['config']['network'], 'mainnet')

    def test_config_has_base_wallet_vars(self):
        """config.py should define BASE_WALLET_PUBLIC_ADDRESS and BASE_RPC_URL"""
        import config
        self.assertTrue(hasattr(config, 'BASE_WALLET_PUBLIC_ADDRESS'))
        self.assertTrue(hasattr(config, 'BASE_RPC_URL'))

    def test_agentic_system_uses_onchain_plugin(self):
        """AgenticAlleyBot should reference onchain plugin for Web3"""
        source_file = PROJECT_ROOT / 'src' / 'agentic' / 'agentic_system.py'
        source = source_file.read_text()
        self.assertIn("plugins.get('onchain')", source)
        self.assertIn('onchain_plugin', source)
        self.assertNotIn("web3_provider=None  # TODO", source)

    def test_module_file_structure(self):
        """All onchain plugin files should exist"""
        onchain_dir = PROJECT_ROOT / 'plugins' / 'onchain'
        expected = ['__init__.py', 'onchain.py', 'web3_provider.py',
                    'token_tracker.py', 'tx_monitor.py']
        for f in expected:
            self.assertTrue(
                (onchain_dir / f).exists(),
                f"Missing: plugins/onchain/{f}"
            )


if __name__ == '__main__':
    unittest.main()
