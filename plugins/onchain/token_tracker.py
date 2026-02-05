"""
Token Tracker Mixin
Monitor specific ERC-20 tokens, track balances, and detect changes.
"""
import datetime
from typing import Dict, List, Any, Optional


# Well-known tokens on Base
KNOWN_TOKENS = {
    'ALLEY': {
        'address': '0x4ac87f6bf79f622768bFD2ec2b9F4c4B9267BB07',
        'symbol': 'ALLEY',
        'name': 'AlleyBot',
        'decimals': 18,
    },
    'USDC': {
        'address': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
        'symbol': 'USDC',
        'name': 'USD Coin',
        'decimals': 6,
    },
    'WETH': {
        'address': '0x4200000000000000000000000000000000000006',
        'symbol': 'WETH',
        'name': 'Wrapped Ether',
        'decimals': 18,
    },
}


class TokenTrackerMixin:
    """Mixin for tracking ERC-20 token balances and changes"""

    def _init_token_tracker(self):
        """Initialize token tracking state"""
        self.tracked_tokens: Dict[str, Dict] = {}
        self.token_snapshots: List[Dict] = []
        self._load_tracked_tokens()

    def _load_tracked_tokens(self):
        """Load tracked tokens from memory"""
        try:
            saved = self.core.get_memory('onchain_tracked_tokens')
            if saved:
                self.tracked_tokens = saved
        except Exception:
            self.tracked_tokens = {}

    def _save_tracked_tokens(self):
        """Save tracked tokens to memory"""
        try:
            self.core.save_memory('onchain_tracked_tokens', self.tracked_tokens)
        except Exception as e:
            print(f"⚠️  Failed to save tracked tokens: {e}")

    def track_token_command(self, *args):
        """Add a token to track. Usage: onchain_track <symbol_or_address>"""
        if not args:
            return "❌ Usage: onchain_track <symbol_or_address>\nKnown tokens: " + ", ".join(KNOWN_TOKENS.keys())

        token_input = args[0].upper()

        # Check known tokens first
        if token_input in KNOWN_TOKENS:
            token_info = KNOWN_TOKENS[token_input]
            token_address = token_info['address']
        elif token_input.startswith('0X') and len(token_input) == 42:
            token_address = token_input
            token_info = None
        else:
            return f"❌ Unknown token: {token_input}\nKnown tokens: {', '.join(KNOWN_TOKENS.keys())}\nOr provide a contract address (0x...)"

        if not self.web3_provider or not self.web3_provider.connected:
            return "❌ Web3 not connected"

        try:
            # Fetch token info from chain if not known
            if not token_info:
                result = self.web3_provider.get_token_balance(token_address)
                if not result['success']:
                    return f"❌ Failed to read token: {result['error']}"
                token_info = {
                    'address': token_address,
                    'symbol': result['symbol'],
                    'name': result['name'],
                    'decimals': result['decimals'],
                }

            symbol = token_info['symbol']
            self.tracked_tokens[symbol] = {
                'address': token_info['address'],
                'symbol': symbol,
                'name': token_info['name'],
                'decimals': token_info['decimals'],
                'added': datetime.datetime.now().isoformat(),
            }
            self._save_tracked_tokens()

            return f"✅ Now tracking {token_info['name']} ({symbol})\n📍 {token_info['address']}"

        except Exception as e:
            return f"❌ Error tracking token: {e}"

    def untrack_token_command(self, *args):
        """Remove a token from tracking. Usage: onchain_untrack <symbol>"""
        if not args:
            return "❌ Usage: onchain_untrack <symbol>"

        symbol = args[0].upper()
        if symbol in self.tracked_tokens:
            del self.tracked_tokens[symbol]
            self._save_tracked_tokens()
            return f"✅ Stopped tracking {symbol}"
        else:
            return f"❌ Not tracking {symbol}"

    def token_balances_command(self, *args):
        """Show balances for all tracked tokens"""
        if not self.web3_provider or not self.web3_provider.connected:
            return "❌ Web3 not connected"

        if not self.web3_provider.wallet_address:
            return "❌ No wallet address configured"

        # Always include ALLEY token
        tokens_to_check = dict(self.tracked_tokens)
        if 'ALLEY' not in tokens_to_check:
            tokens_to_check['ALLEY'] = KNOWN_TOKENS['ALLEY']

        output = "💰 Token Balances\n"
        output += f"📍 Wallet: {self.web3_provider.wallet_address[:10]}...{self.web3_provider.wallet_address[-6:]}\n"
        output += f"🌐 Network: {self.web3_provider.network_config['name']}\n\n"

        # ETH balance first
        eth_result = self.web3_provider.get_eth_balance()
        if eth_result['success']:
            output += f"  Ξ ETH: {eth_result['balance_eth']:.6f}\n"
        else:
            output += f"  Ξ ETH: Error - {eth_result['error']}\n"

        # Token balances
        for symbol, token_info in tokens_to_check.items():
            result = self.web3_provider.get_token_balance(token_info['address'])
            if result['success']:
                output += f"  🪙 {symbol}: {result['balance']:,.4f}\n"
            else:
                output += f"  🪙 {symbol}: Error - {result['error']}\n"

        # Take snapshot for change detection
        self._take_balance_snapshot(eth_result, tokens_to_check)

        return output

    def _take_balance_snapshot(self, eth_result, tokens):
        """Record a balance snapshot for change detection"""
        try:
            snapshot = {
                'timestamp': datetime.datetime.now().isoformat(),
                'eth_balance': eth_result.get('balance_eth', 0) if eth_result.get('success') else 0,
                'tokens': {},
            }
            for symbol, token_info in tokens.items():
                result = self.web3_provider.get_token_balance(token_info['address'])
                if result.get('success'):
                    snapshot['tokens'][symbol] = result['balance']

            self.token_snapshots.append(snapshot)
            # Keep last 100 snapshots
            self.token_snapshots = self.token_snapshots[-100:]

            # Save to memory
            self.core.save_memory('onchain_balance_snapshots', self.token_snapshots[-20:])

        except Exception as e:
            print(f"⚠️  Failed to take balance snapshot: {e}")

    def check_balance_changes(self) -> Optional[Dict]:
        """Compare current balances to last snapshot, return changes if any"""
        if len(self.token_snapshots) < 2:
            return None

        prev = self.token_snapshots[-2]
        curr = self.token_snapshots[-1]

        changes = {}

        # ETH change
        eth_diff = curr.get('eth_balance', 0) - prev.get('eth_balance', 0)
        if abs(eth_diff) > 0.0001:
            changes['ETH'] = {
                'previous': prev.get('eth_balance', 0),
                'current': curr.get('eth_balance', 0),
                'change': eth_diff,
            }

        # Token changes
        for symbol in set(list(curr.get('tokens', {}).keys()) + list(prev.get('tokens', {}).keys())):
            prev_bal = prev.get('tokens', {}).get(symbol, 0)
            curr_bal = curr.get('tokens', {}).get(symbol, 0)
            diff = curr_bal - prev_bal
            if abs(diff) > 0.0001:
                changes[symbol] = {
                    'previous': prev_bal,
                    'current': curr_bal,
                    'change': diff,
                }

        return changes if changes else None
