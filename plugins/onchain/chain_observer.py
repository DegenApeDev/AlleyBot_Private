"""
Chain Observer Mixin — watches mempool + recent blocks for pattern learning
Monitors Base and Apechain, categorizes transactions, stores observations
for the brain cycle to consume. Purely observational — no wallet actions.
"""
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from src.utils.shared_http import http_post

# Chain RPC endpoints
CHAINS = {
    'base': {
        'name': 'Base',
        'chain_id': 8453,
        'rpc': 'https://mainnet.base.org',
        'explorer': 'https://basescan.org',
        'currency': 'ETH',
    },
    'apechain': {
        'name': 'ApeChain',
        'chain_id': 33139,
        'rpc': 'https://rpc.apechain.com',
        'explorer': 'https://apescan.io',
        'currency': 'APE',
    },
}

# Known protocol signatures (first 4 bytes of method selector)
SIGNATURES = {
    '0x38ed1739': 'swap_exact_tokens_for_tokens',
    '0x7ff36ab5': 'swap_exact_eth_for_tokens',
    '0x18cbafe5': 'swap_exact_tokens_for_eth',
    '0x5c11d795': 'swap_exact_tokens_for_tokens_supporting_fee',
    '0x022c0d9f': 'swap',
    '0xa9059cbb': 'transfer',
    '0x095ea7b3': 'approve',
    '0x23b872dd': 'transfer_from',
    '0xa22cb465': 'set_approval_for_all',
    '0x414bf389': 'mint',
    '0x2e1a7d4d': 'withdraw',
    '0xd0e30db0': 'deposit',
    '0x3593564c': 'execute',
    '0x24856bc3': 'create_pool',
}

KNOWN_CONTRACTS: Dict[str, Dict[str, str]] = {
    'base': {
        '0x0000000000000000000000000000000000000000': 'ETH',
        '0x4200000000000000000000000000000000000006': 'WETH',
        '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913': 'USDC',
        '0x50c5725949a6f0c72e6c4a641f24049a917db0cb': 'DAI',
        '0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22': 'cbETH',
        '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee': 'ETH (native)',
    },
    'apechain': {},
}


def _rpc_call(url: str, method: str, params: list) -> Optional[dict]:
    """Make a JSON-RPC call to a chain endpoint."""
    try:
        resp = http_post(
            url,
            json={'jsonrpc': '2.0', 'method': method, 'params': params, 'id': 1},
            headers={'Content-Type': 'application/json'},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if 'result' in data:
                return data['result']
        return None
    except Exception:
        return None


def classify_transaction(tx: dict, chain_key: str) -> str:
    """Classify a transaction into a category based on its input data."""
    if not tx.get('input') or tx['input'] == '0x':
        if tx.get('to') is None:
            return 'deploy'
        value = int(tx.get('value', '0x0'), 16) if isinstance(tx.get('value'), str) else 0
        if value > 0:
            return 'transfer'
        return 'interaction'

    selector = tx['input'][:10]
    return SIGNATURES.get(selector, 'contract_call')


def extract_transfer_value(tx: dict, chain_key: str) -> float:
    """Extract human-readable value from a transaction."""
    value_wei = int(tx.get('value', '0x0'), 16) if isinstance(tx.get('value'), str) else 0
    return value_wei / 1e18


def lookup_contract(address: str, chain_key: str) -> str:
    """Look up a known contract name or return truncated address."""
    if not address:
        return 'unknown'
    lower = address.lower()
    known = KNOWN_CONTRACTS.get(chain_key, {})
    for addr, name in known.items():
        if addr.lower() == lower:
            return name
    return f"{address[:6]}...{address[-4:]}"


class ChainObserverMixin:
    """Mixin that watches Base + Apechain for transaction patterns."""

    def _init_chain_observer(self):
        self._observed_chains = set()
        self._last_checked_block: Dict[str, int] = {}
        self._pattern_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._high_value_txs: List[Dict] = []
        self._MAX_STORED_TXS = 100

    def poll_chains(self) -> List[Dict]:
        """Poll Base and Apechain for new blocks and categorize transactions.

        Returns a list of observation dicts for the brain cycle.
        """
        observations = []

        for chain_key, chain_info in CHAINS.items():
            try:
                block_obs = self._poll_chain(chain_key, chain_info)
                observations.extend(block_obs)
            except Exception as e:
                print(f"⚠️ Chain observer poll failed for {chain_key}: {e}")

        self._store_pattern_summary()
        return observations

    def _poll_chain(self, chain_key: str, chain_info: dict) -> List[Dict]:
        """Poll a single chain for new blocks and extract observations."""
        observations = []
        rpc_url = chain_info['rpc']

        # Get latest block number
        result = _rpc_call(rpc_url, 'eth_blockNumber', [])
        if not result:
            return observations

        latest_block = int(result, 16)
        last_seen = self._last_checked_block.get(chain_key, latest_block - 5)

        # Don't scan more than 10 blocks at a time
        start_block = max(last_seen + 1, latest_block - 10)
        if start_block > latest_block:
            return observations

        for block_num in range(start_block, latest_block + 1):
            block = _rpc_call(rpc_url, 'eth_getBlockByNumber', [hex(block_num), True])
            if not block or not block.get('transactions'):
                continue

            txs = block['transactions']
            block_time = int(block.get('timestamp', '0x0'), 16)

            for tx in txs:
                obs = self._analyze_transaction(tx, chain_key, block_num, block_time)
                if obs:
                    observations.append(obs)

            # Track patterns per block
            categories = [self._categorize_for_pattern(tx, chain_key) for tx in txs]
            for cat in categories:
                if cat:
                    self._pattern_counts[chain_key][cat] += 1

        self._last_checked_block[chain_key] = latest_block
        return observations

    def _categorize_for_pattern(self, tx: dict, chain_key: str) -> Optional[str]:
        """Categorize a transaction for pattern counting (lighter than full obs)."""
        cat = classify_transaction(tx, chain_key)
        return cat

    def _analyze_transaction(self, tx: dict, chain_key: str,
                             block_num: int, block_time: int) -> Optional[Dict]:
        """Analyze a single transaction and return an observation if interesting.

        Interesting = high value, known contract interaction, or unusual pattern.
        """
        value_eth = extract_transfer_value(tx, chain_key)
        tx_hash = tx.get('hash', '')
        to_addr = tx.get('to', '')
        from_addr = tx.get('from', '')
        category = classify_transaction(tx, chain_key)

        # Always note: transfer, swap, mint, deploy
        interesting_categories = {'transfer', 'swap', 'mint', 'deploy',
                                  'swap_exact_eth_for_tokens', 'swap_exact_tokens_for_tokens'}

        # High-value threshold (0.1 ETH equivalent)
        is_high_value = value_eth >= 0.1
        is_interesting_category = category in interesting_categories

        if not is_high_value and not is_interesting_category:
            return None

        to_name = lookup_contract(to_addr, chain_key)
        from_name = lookup_contract(from_addr, chain_key)

        obs = {
            'type': 'chain_transaction',
            'chain': chain_key,
            'chain_name': CHAINS[chain_key]['name'],
            'block': block_num,
            'hash': tx_hash[:20] if tx_hash else '',
            'from': from_addr[:10] if from_addr else '',
            'to': to_addr[:10] if to_addr else '',
            'to_name': to_name,
            'value_eth': round(value_eth, 6),
            'category': category,
            'timestamp': datetime.fromtimestamp(block_time).isoformat() if block_time else '',
            'source_plugin': 'onchain',
        }

        # Add to high-value tracker
        if is_high_value:
            self._high_value_txs.append(obs)
            self._high_value_txs = self._high_value_txs[-self._MAX_STORED_TXS:]

        return obs

    def _store_pattern_summary(self):
        """Store aggregated pattern data in core memory for the brain cycle."""
        if not hasattr(self, 'core') or not self.core:
            return

        try:
            summary = {}
            for chain_key, patterns in self._pattern_counts.items():
                total = sum(patterns.values())
                top = sorted(patterns.items(), key=lambda x: -x[1])[:5]
                summary[chain_key] = {
                    'total_tx_observed': total,
                    'top_patterns': [{'type': k, 'count': v} for k, v in top],
                }

            self.core.save_memory('chain_observer_patterns', {
                'summary': summary,
                'high_value_txs': self._high_value_txs[-20:],
                'last_update': datetime.now().isoformat(),
            })
        except Exception:
            pass

    def get_chain_observations(self) -> List[Dict]:
        """Return stored chain observations for the brain cycle."""
        if not hasattr(self, 'core') or not self.core:
            return []
        try:
            data = self.core.get_memory('chain_observer_patterns') or {}
            return data.get('high_value_txs', [])
        except Exception:
            return []

    def get_chain_summary(self) -> str:
        """Return a human-readable summary of chain activity."""
        if not hasattr(self, 'core') or not self.core:
            return "Chain observer not initialized"

        try:
            data = self.core.get_memory('chain_observer_patterns') or {}
            summary = data.get('summary', {})
            if not summary:
                return "No chain activity observed yet"

            lines = []
            for chain_key, info in summary.items():
                lines.append(f"\n  {CHAINS[chain_key]['name']}:")
                lines.append(f"    Total observed: {info['total_tx_observed']}")
                for pat in info.get('top_patterns', []):
                    lines.append(f"    {pat['type']}: {pat['count']}")
            return '\n'.join(lines)
        except Exception:
            return "Error reading chain summary"
