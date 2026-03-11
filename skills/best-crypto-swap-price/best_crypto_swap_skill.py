"""
Best Crypto Swap Price Skill Implementation

Provides optimal token swap routing across multiple DEX aggregators.
Integrates with swap.moltx.io API to get best prices from Paraswap, 1inch, 0x, Kyber, Odos, and OKX.
"""
import os
import sys
import requests
from decimal import Decimal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add project root for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


@dataclass
class SwapQuote:
    """Swap quote from an aggregator"""
    aggregator: str
    display_name: str
    sell_token: str
    buy_token: str
    sell_amount: str
    buy_amount: str
    price_impact: str
    slippage: str
    calldata: str
    to_address: str
    allowance_spender: str
    gas_price: str
    value: str
    raw_tx: Dict
    error: Optional[str] = None


@dataclass
class SwapResult:
    """Result of a swap execution"""
    success: bool
    tx_hash: Optional[str]
    aggregator: str
    gas_used: Optional[int]
    block_number: Optional[int]
    buy_amount: str
    price_impact: str
    error: Optional[str] = None


class BestCryptoSwapSkill:
    """
    Best Crypto Swap Price Skill
    
    Gets optimal swap routes across multiple DEX aggregators.
    Supports Ethereum, Arbitrum, Base, Polygon, and Plasma.
    """
    
    API_BASE = "https://swap.moltx.io"
    
    # RPC endpoints by network
    RPC_URLS = {
        'ethereum': 'https://eth.llamarpc.com',
        'arbitrum': 'https://arb1.arbitrum.io/rpc',
        'base': 'https://mainnet.base.org',
        'polygon': 'https://polygon-rpc.com',
        'plasma': 'https://rpc.plasma.io',
    }
    
    # Chain IDs
    CHAIN_IDS = {
        'ethereum': 1,
        'arbitrum': 42161,
        'base': 8453,
        'polygon': 137,
        'plasma': 9745,
    }
    
    # Common token addresses by network
    TOKENS = {
        'ethereum': {
            'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            'ETH': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
            'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
            'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
            'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
        },
        'base': {
            'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
            'WETH': '0x4200000000000000000000000000000000000006',
            'ETH': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
            'DAI': '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb',
        },
        'arbitrum': {
            'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
            'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
            'ETH': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
        },
        'polygon': {
            'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
            'MATIC': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
        },
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'AlleyBot-BestSwapSkill/1.0'
        })
    
    def get_best_quote(
        self,
        network: str,
        sell_token: str,
        buy_token: str,
        sell_amount: str,
        user_address: str,
        slippage: float = 1.0,
        aggregators: Optional[List[str]] = None,
        disabled_protocols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get the best swap quote from multiple aggregators.
        
        Args:
            network: Chain name (ethereum, arbitrum, base, polygon, plasma)
            sell_token: Token address to sell
            buy_token: Token address to buy
            sell_amount: Amount in smallest unit (wei/decimals)
            user_address: User's wallet address
            slippage: Max slippage percentage (default 1%)
            aggregators: Specific aggregators to query (default: all)
            disabled_protocols: Protocols to exclude
            
        Returns:
            Dict with best_route and all_routes
        """
        params = {
            'network': network,
            'sellToken': sell_token,
            'buyToken': buy_token,
            'sellAmount': str(sell_amount),
            'slippage': str(slippage),
            'user': user_address,
            'eoaAddress': user_address,
            'accountType': 'eoa',
        }
        
        # Add optional filters
        if aggregators:
            for agg in aggregators:
                params.setdefault('aggregators[]', []).append(agg)
        if disabled_protocols:
            for protocol in disabled_protocols:
                params.setdefault('disabledProtocols[]', []).append(protocol)
        
        try:
            response = self.session.get(
                f"{self.API_BASE}/swap",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Filter valid routes (no errors)
            valid_routes = [
                agg for agg in data.get('aggregators', [])
                if not agg.get('error')
            ]
            
            if not valid_routes:
                failed = [agg for agg in data.get('aggregators', []) if agg.get('error')]
                errors = [f"{a['displayName']}: {a['error']['message']}" for a in failed]
                return {
                    'success': False,
                    'error': f"No valid routes found. Errors: {errors}"
                }
            
            # Best route is first (sorted by buy amount)
            best = valid_routes[0]
            
            return {
                'success': True,
                'best_route': self._parse_quote(best),
                'all_routes': [self._parse_quote(r) for r in valid_routes],
                'summary': {
                    'network': network,
                    'sell_token': data['data']['sellToken'],
                    'buy_token': data['data']['buyToken'],
                    'sell_amount': data['data']['sellTokenAmount'],
                    'best_buy_amount': data['data']['bestBuyTokenAmount'],
                    'total_aggregators_queried': data['data']['totalAggregators'],
                    'slippage': data['data']['slippage'],
                }
            }
            
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'API request failed: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def _parse_quote(self, agg_data: Dict) -> SwapQuote:
        """Parse aggregator data into SwapQuote"""
        data = agg_data.get('data', {})
        return SwapQuote(
            aggregator=agg_data.get('name', ''),
            display_name=agg_data.get('displayName', ''),
            sell_token=data.get('sellToken', {}).get('address', ''),
            buy_token=data.get('buyToken', {}).get('address', ''),
            sell_amount=data.get('sellTokenAmount', '0'),
            buy_amount=data.get('buyTokenAmount', '0'),
            price_impact=data.get('priceImpact', '0'),
            slippage=data.get('slippage', '0'),
            calldata=data.get('calldata', ''),
            to_address=data.get('to', ''),
            allowance_spender=data.get('allowanceSpender', ''),
            gas_price=data.get('gasPrice', '0'),
            value=data.get('value', '0'),
            raw_tx=data.get('raw', {}),
            error=agg_data.get('error', {}).get('message') if agg_data.get('error') else None
        )
    
    def execute_swap(
        self,
        network: str,
        quote: SwapQuote,
        private_key: str,
        gas_limit: int = 300000
    ) -> SwapResult:
        """
        Execute the swap using the provided quote.
        
        Args:
            network: Chain name
            quote: SwapQuote from get_best_quote
            private_key: Private key for signing
            gas_limit: Gas limit for transaction
            
        Returns:
            SwapResult with transaction details
        """
        try:
            from web3 import Web3
            
            # Initialize Web3
            rpc_url = self.RPC_URLS.get(network, self.RPC_URLS['ethereum'])
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not w3.is_connected():
                return SwapResult(
                    success=False,
                    tx_hash=None,
                    aggregator=quote.display_name,
                    gas_used=None,
                    block_number=None,
                    buy_amount=quote.buy_amount,
                    price_impact=quote.price_impact,
                    error=f"Failed to connect to {network} RPC"
                )
            
            # Build transaction
            account = w3.eth.account.from_key(private_key)
            
            tx = {
                'from': account.address,
                'to': Web3.to_checksum_address(quote.to_address),
                'value': int(quote.value),
                'data': quote.calldata,
                'gas': gas_limit,
                'gasPrice': int(quote.gas_price),
                'chainId': self.CHAIN_IDS.get(network, 1),
                'nonce': w3.eth.get_transaction_count(account.address),
            }
            
            # Sign and send
            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return SwapResult(
                success=receipt['status'] == 1,
                tx_hash=tx_hash.hex(),
                aggregator=quote.display_name,
                gas_used=receipt['gasUsed'],
                block_number=receipt['blockNumber'],
                buy_amount=quote.buy_amount,
                price_impact=quote.price_impact,
                error=None if receipt['status'] == 1 else "Transaction reverted"
            )
            
        except Exception as e:
            return SwapResult(
                success=False,
                tx_hash=None,
                aggregator=quote.display_name if quote else 'unknown',
                gas_used=None,
                block_number=None,
                buy_amount=quote.buy_amount if quote else '0',
                price_impact=quote.price_impact if quote else '0',
                error=str(e)
            )
    
    def compare_aggregators(
        self,
        network: str,
        sell_token: str,
        buy_token: str,
        sell_amount: str,
        user_address: str,
        slippage: float = 1.0
    ) -> str:
        """
        Get a comparison report of all aggregators.
        
        Returns formatted string for display.
        """
        result = self.get_best_quote(
            network, sell_token, buy_token, sell_amount,
            user_address, slippage
        )
        
        if not result.get('success'):
            return f"❌ Failed to get quotes: {result.get('error', 'Unknown error')}"
        
        summary = result['summary']
        all_routes = result['all_routes']
        
        output = f"📊 Swap Comparison on {network.upper()}\n"
        output += f"Sell: {summary['sell_amount']} → Buy Token\n"
        output += f"Best Buy Amount: {summary['best_buy_amount']}\n"
        output += f"Aggregators Queried: {summary['total_aggregators_queried']}\n"
        output += f"Slippage: {summary['slippage']}%\n\n"
        
        output += "🏆 Aggregator Rankings:\n"
        for i, route in enumerate(all_routes[:5], 1):
            buy_amt = Decimal(route.buy_amount) / Decimal(10**18)  # Approximate
            impact = Decimal(route.price_impact)
            output += f"{i}. {route.display_name}\n"
            output += f"   Buy: ~{buy_amt:.6f} | Impact: {impact:.2f}%\n"
        
        return output
    
    def get_token_address(self, network: str, symbol: str) -> Optional[str]:
        """Get token address by network and symbol"""
        network_tokens = self.TOKENS.get(network.lower(), {})
        return network_tokens.get(symbol.upper())


# Convenience function for quick swaps
def quick_swap(
    network: str,
    from_token_symbol: str,
    to_token_symbol: str,
    amount: float,
    user_address: str,
    private_key: str,
    from_decimals: int = 18,
    slippage: float = 1.0
) -> Dict[str, Any]:
    """
    Quick swap function - get best price and execute in one call.
    
    Args:
        network: Chain name
        from_token_symbol: Symbol of token to sell (e.g., 'USDC')
        to_token_symbol: Symbol of token to buy (e.g., 'WETH')
        amount: Amount to sell (human readable)
        user_address: Wallet address
        private_key: Private key for signing
        from_decimals: Decimals of sell token
        slippage: Max slippage
        
    Returns:
        Swap result dict
    """
    skill = BestCryptoSwapSkill()
    
    # Get token addresses
    sell_token = skill.get_token_address(network, from_token_symbol)
    buy_token = skill.get_token_address(network, to_token_symbol)
    
    if not sell_token:
        return {'success': False, 'error': f'Unknown token: {from_token_symbol} on {network}'}
    if not buy_token:
        return {'success': False, 'error': f'Unknown token: {to_token_symbol} on {network}'}
    
    # Convert amount to raw
    amount_raw = int(amount * (10 ** from_decimals))
    
    # Get best quote
    quote_result = skill.get_best_quote(
        network=network,
        sell_token=sell_token,
        buy_token=buy_token,
        sell_amount=str(amount_raw),
        user_address=user_address,
        slippage=slippage
    )
    
    if not quote_result.get('success'):
        return quote_result
    
    # Execute swap
    best_quote = quote_result['best_route']
    result = skill.execute_swap(network, best_quote, private_key)
    
    return {
        'success': result.success,
        'tx_hash': result.tx_hash,
        'aggregator': result.aggregator,
        'gas_used': result.gas_used,
        'block_number': result.block_number,
        'buy_amount': result.buy_amount,
        'price_impact': result.price_impact,
        'explorer_url': f"https://{'etherscan.io' if network == 'ethereum' else network + '.explorer.io'}/tx/{result.tx_hash}" if result.tx_hash else None,
        'error': result.error
    }


# Export for skill system
__all__ = ['BestCryptoSwapSkill', 'quick_swap', 'SwapQuote', 'SwapResult']
