"""
Transaction Monitor Mixin
Watch for relevant on-chain events and transactions.
"""
import datetime
from typing import Dict, List, Any, Optional


class TxMonitorMixin:
    """Mixin for monitoring on-chain transactions and events"""

    def _init_tx_monitor(self):
        """Initialize transaction monitoring state"""
        self.last_seen_block: Optional[int] = None
        self.watched_addresses: List[str] = []
        self.tx_history: List[Dict] = []
        self._load_tx_state()

    def _load_tx_state(self):
        """Load transaction monitoring state from memory"""
        try:
            state = self.core.get_memory('onchain_tx_state')
            if state:
                self.last_seen_block = state.get('last_seen_block')
                self.watched_addresses = state.get('watched_addresses', [])
                self.tx_history = state.get('tx_history', [])
        except Exception:
            pass

    def _save_tx_state(self):
        """Save transaction monitoring state"""
        try:
            self.core.save_memory('onchain_tx_state', {
                'last_seen_block': self.last_seen_block,
                'watched_addresses': self.watched_addresses,
                'tx_history': self.tx_history[-50:],
            })
        except Exception as e:
            print(f"⚠️  Failed to save tx state: {e}")

    def watch_address_command(self, *args):
        """Watch an address for transactions. Usage: onchain_watch <address>"""
        if not args:
            return "❌ Usage: onchain_watch <address>"

        address = args[0]
        if not address.startswith('0x') or len(address) != 42:
            return "❌ Invalid address format. Must be 0x... (42 chars)"

        if not self.web3_provider or not self.web3_provider.connected:
            return "❌ Web3 not connected"

        try:
            address = self.web3_provider.w3.to_checksum_address(address)
        except Exception:
            return "❌ Invalid checksum address"

        if address not in self.watched_addresses:
            self.watched_addresses.append(address)
            self._save_tx_state()
            return f"✅ Now watching address: {address[:10]}...{address[-6:]}"
        else:
            return f"ℹ️  Already watching {address[:10]}...{address[-6:]}"

    def unwatch_address_command(self, *args):
        """Stop watching an address. Usage: onchain_unwatch <address>"""
        if not args:
            return "❌ Usage: onchain_unwatch <address>"

        address = args[0]
        try:
            address = self.web3_provider.w3.to_checksum_address(address)
        except Exception:
            pass

        if address in self.watched_addresses:
            self.watched_addresses.remove(address)
            self._save_tx_state()
            return f"✅ Stopped watching {address[:10]}...{address[-6:]}"
        else:
            return f"❌ Not watching that address"

    def tx_lookup_command(self, *args):
        """Look up a transaction by hash. Usage: onchain_tx <tx_hash>"""
        if not args:
            return "❌ Usage: onchain_tx <tx_hash>"

        if not self.web3_provider or not self.web3_provider.connected:
            return "❌ Web3 not connected"

        tx_hash = args[0]
        result = self.web3_provider.get_transaction(tx_hash)

        if not result['success']:
            return f"❌ Transaction not found: {result['error']}"

        output = "📋 Transaction Details\n\n"
        output += f"  🔗 Hash: {result['hash'][:16]}...\n"
        output += f"  📤 From: {result['from'][:10]}...{result['from'][-6:]}\n"
        output += f"  📥 To: {result['to'][:10]}...{result['to'][-6:]}\n"
        output += f"  💰 Value: {result['value_eth']:.6f} ETH\n"
        output += f"  ⛽ Gas Used: {result['gas_used']:,}\n"
        output += f"  📦 Block: {result['block_number']:,}\n"
        output += f"  {'✅' if result['status'] == 'success' else '❌'} Status: {result['status']}\n"
        output += f"  🔍 {result['explorer_url']}\n"

        return output

    def recent_activity_command(self, *args):
        """Show recent on-chain activity for our wallet"""
        if not self.web3_provider or not self.web3_provider.connected:
            return "❌ Web3 not connected"

        if not self.web3_provider.wallet_address:
            return "❌ No wallet address configured"

        blocks_back = 500
        if args:
            try:
                blocks_back = int(args[0])
            except ValueError:
                pass

        print(f"🔍 Scanning last {blocks_back} blocks for activity...")
        result = self.web3_provider.get_recent_transfers(blocks_back=blocks_back)

        if not result['success']:
            return f"❌ Error: {result['error']}"

        transfers = result['transfers']
        if not transfers:
            return f"📭 No transactions found in last {result['blocks_scanned']} blocks"

        output = f"📋 Recent Activity ({len(transfers)} transactions)\n"
        output += f"🔍 Scanned {result['blocks_scanned']} blocks\n\n"

        for tx in transfers[:10]:
            direction_icon = "📥" if tx['direction'] == 'in' else "📤"
            output += f"  {direction_icon} {tx['direction'].upper()} {tx['value_eth']:.6f} ETH\n"
            if tx['direction'] == 'in':
                output += f"     From: {tx['from'][:10]}...{tx['from'][-6:]}\n"
            else:
                to_addr = tx['to'] if isinstance(tx['to'], str) else 'Contract'
                output += f"     To: {to_addr[:10]}...{to_addr[-6:]}\n"
            output += f"     Block: {tx['block']:,}\n\n"

        return output

    def onchain_heartbeat(self):
        """Periodic on-chain monitoring - check balances and transactions"""
        if not self.web3_provider or not self.web3_provider.connected:
            print("⚠️  On-chain heartbeat skipped: Web3 not connected")
            return "⚠️  Web3 not connected"

        try:
            print("🔗 On-chain heartbeat - checking balances and activity...")

            # Check ETH balance
            eth_result = self.web3_provider.get_eth_balance()
            if eth_result['success']:
                print(f"  Ξ ETH: {eth_result['balance_eth']:.6f}")

            # Check tracked token balances
            for symbol, token_info in self.tracked_tokens.items():
                result = self.web3_provider.get_token_balance(token_info['address'])
                if result['success']:
                    print(f"  🪙 {symbol}: {result['balance']:,.4f}")

            # Take snapshot and check for changes
            self._take_balance_snapshot(eth_result, self.tracked_tokens)
            changes = self.check_balance_changes()

            if changes:
                print(f"⚡ Balance changes detected: {list(changes.keys())}")
                self._record_balance_change(changes)

                # Log to semantic memory if available
                for symbol, change in changes.items():
                    direction = "received" if change['change'] > 0 else "sent"
                    self.core.add_semantic_memory(
                        f"Balance change: {direction} {abs(change['change']):.6f} {symbol}",
                        memory_type='on_chain_event',
                        metadata={'symbol': symbol, 'change': change}
                    )

            # Update last seen block
            block_info = self.web3_provider.get_block_info()
            if block_info['success']:
                self.last_seen_block = block_info['block_number']
                self._save_tx_state()

            message = f"🔗 On-chain heartbeat complete (block {self.last_seen_block})"
            print(message)
            return message

        except Exception as e:
            print(f"❌ On-chain heartbeat error: {e}")
            return f"❌ On-chain heartbeat error: {e}"

    def _record_balance_change(self, changes):
        """Record balance changes in transaction history"""
        try:
            for symbol, change in changes.items():
                self.tx_history.append({
                    'type': 'balance_change',
                    'symbol': symbol,
                    'previous': change['previous'],
                    'current': change['current'],
                    'change': change['change'],
                    'timestamp': datetime.datetime.now().isoformat(),
                })

            self.tx_history = self.tx_history[-50:]
            self._save_tx_state()

        except Exception as e:
            print(f"⚠️  Failed to record balance change: {e}")
