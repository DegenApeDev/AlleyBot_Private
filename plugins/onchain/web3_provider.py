"""
Web3 Provider - Base network connection and wallet management
Centralized Web3 connection used by all on-chain functionality.
"""
import os
from typing import Optional, Dict, Any

# Web3 import with graceful fallback
try:
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("⚠️  web3 not installed. Run: pip install web3")


# Base network configuration
BASE_MAINNET = {
    'name': 'Base',
    'chain_id': 8453,
    'rpc_url': 'https://mainnet.base.org',
    'explorer': 'https://basescan.org',
    'currency': 'ETH',
}

BASE_SEPOLIA = {
    'name': 'Base Sepolia',
    'chain_id': 84532,
    'rpc_url': 'https://sepolia.base.org',
    'explorer': 'https://sepolia.basescan.org',
    'currency': 'ETH',
}

# Common ERC-20 ABI (balanceOf, decimals, symbol, name, transfer)
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"anonymous": False, "inputs": [{"indexed": True, "name": "from", "type": "address"}, {"indexed": True, "name": "to", "type": "address"}, {"indexed": False, "name": "value", "type": "uint256"}], "name": "Transfer", "type": "event"},
]

# AlleyBot token on Base
ALLEYBOT_TOKEN = {
    'address': '0x08a18FE29158B1de5704F99cA396Ad9B2B6a58F3',
    'symbol': 'ALYBOT',
    'name': 'AlleyBot',
    'decimals': 18,
}


class Web3Provider:
    """Manages Web3 connection to Base network"""

    def __init__(self, network: str = 'mainnet'):
        self.network_config = BASE_MAINNET if network == 'mainnet' else BASE_SEPOLIA
        self.w3: Optional[Web3] = None
        self.wallet_address: Optional[str] = None
        self.connected = False

    def connect(self) -> bool:
        """Connect to Base network via RPC"""
        if not WEB3_AVAILABLE:
            print("❌ web3 package not available")
            return False

        try:
            rpc_url = os.getenv('BASE_RPC_URL', self.network_config['rpc_url'])
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))

            # Add POA middleware for Base (L2)
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

            if self.w3.is_connected():
                chain_id = self.w3.eth.chain_id
                self.connected = True
                print(f"✅ Connected to {self.network_config['name']} (chain {chain_id})")

                # Load wallet address
                self.wallet_address = os.getenv('BASE_WALLET_PUBLIC_ADDRESS') or os.getenv('BASE_WALLET')
                if self.wallet_address:
                    print(f"💰 Wallet: {self.wallet_address[:10]}...{self.wallet_address[-6:]}")
                else:
                    print("⚠️  No wallet address configured (set BASE_WALLET_PUBLIC_ADDRESS)")

                return True
            else:
                print(f"❌ Failed to connect to {self.network_config['name']}")
                return False

        except Exception as e:
            print(f"❌ Web3 connection error: {e}")
            return False

    def get_eth_balance(self, address: Optional[str] = None) -> Dict[str, Any]:
        """Get ETH balance for an address"""
        if not self.connected:
            return {'success': False, 'error': 'Not connected'}

        address = address or self.wallet_address
        if not address:
            return {'success': False, 'error': 'No address provided'}

        try:
            address = self.w3.to_checksum_address(address)
            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = float(self.w3.from_wei(balance_wei, 'ether'))

            return {
                'success': True,
                'address': address,
                'balance_wei': balance_wei,
                'balance_eth': balance_eth,
                'currency': 'ETH',
                'network': self.network_config['name'],
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_token_balance(self, token_address: str, wallet_address: Optional[str] = None) -> Dict[str, Any]:
        """Get ERC-20 token balance"""
        if not self.connected:
            return {'success': False, 'error': 'Not connected'}

        wallet_address = wallet_address or self.wallet_address
        if not wallet_address:
            return {'success': False, 'error': 'No wallet address'}

        try:
            token_address = self.w3.to_checksum_address(token_address)
            wallet_address = self.w3.to_checksum_address(wallet_address)

            contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)

            balance = contract.functions.balanceOf(wallet_address).call()
            decimals = contract.functions.decimals().call()
            symbol = contract.functions.symbol().call()
            name = contract.functions.name().call()

            human_balance = balance / (10 ** decimals)

            return {
                'success': True,
                'token_address': token_address,
                'wallet_address': wallet_address,
                'balance_raw': balance,
                'balance': human_balance,
                'decimals': decimals,
                'symbol': symbol,
                'name': name,
                'network': self.network_config['name'],
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_block_info(self) -> Dict[str, Any]:
        """Get latest block information"""
        if not self.connected:
            return {'success': False, 'error': 'Not connected'}

        try:
            block = self.w3.eth.get_block('latest')
            gas_price = self.w3.eth.gas_price

            return {
                'success': True,
                'block_number': block['number'],
                'timestamp': block['timestamp'],
                'gas_price_gwei': float(self.w3.from_wei(gas_price, 'gwei')),
                'transactions_count': len(block.get('transactions', [])),
                'network': self.network_config['name'],
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction details by hash"""
        if not self.connected:
            return {'success': False, 'error': 'Not connected'}

        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)

            return {
                'success': True,
                'hash': tx_hash,
                'from': tx['from'],
                'to': tx['to'],
                'value_eth': float(self.w3.from_wei(tx['value'], 'ether')),
                'gas_used': receipt['gasUsed'],
                'status': 'success' if receipt['status'] == 1 else 'failed',
                'block_number': receipt['blockNumber'],
                'explorer_url': f"{self.network_config['explorer']}/tx/{tx_hash}",
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def read_contract(self, contract_address: str, abi: list, function_name: str, *args) -> Dict[str, Any]:
        """Read data from a smart contract (view/pure functions only)"""
        if not self.connected:
            return {'success': False, 'error': 'Not connected'}

        try:
            contract_address = self.w3.to_checksum_address(contract_address)
            contract = self.w3.eth.contract(address=contract_address, abi=abi)
            fn = contract.functions[function_name]
            result = fn(*args).call()

            return {
                'success': True,
                'contract': contract_address,
                'function': function_name,
                'result': result,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_recent_transfers(self, address: Optional[str] = None, blocks_back: int = 1000) -> Dict[str, Any]:
        """Get recent ETH transfers to/from an address using block scanning"""
        if not self.connected:
            return {'success': False, 'error': 'Not connected'}

        address = address or self.wallet_address
        if not address:
            return {'success': False, 'error': 'No address provided'}

        try:
            address = self.w3.to_checksum_address(address)
            latest_block = self.w3.eth.block_number
            from_block = max(0, latest_block - blocks_back)

            transfers = []
            # Scan last N blocks for transactions involving this address
            # Note: For production, use an indexer API (Basescan, Alchemy, etc.)
            for block_num in range(latest_block, from_block, -1):
                block = self.w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.get('transactions', []):
                    if tx['from'] == address or tx.get('to') == address:
                        direction = 'out' if tx['from'] == address else 'in'
                        transfers.append({
                            'hash': tx['hash'].hex(),
                            'direction': direction,
                            'from': tx['from'],
                            'to': tx.get('to', 'Contract Creation'),
                            'value_eth': float(self.w3.from_wei(tx['value'], 'ether')),
                            'block': block_num,
                        })

                if len(transfers) >= 10:
                    break

            return {
                'success': True,
                'address': address,
                'transfers': transfers,
                'blocks_scanned': latest_block - from_block,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
