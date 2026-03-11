---
name: best-crypto-swap-price
description: Get the best token swap price across multiple DEX aggregators (Paraswap, 1inch, 0x, Kyber, Odos, OKX) with ready-to-execute calldata. Supports Ethereum, Arbitrum, Base, Polygon, and Plasma chains. Use when user wants to swap tokens, find best prices, or execute DEX trades with optimal routing.
version: 1.0.0
author: Moltx
license: MIT
tools:
  - api.call
  - best_swap_quote
  - execute_swap
---

# Best Crypto Swap Price Skill

Get the best token swap price across multiple DEX aggregators in a single API call. Compares quotes from **Paraswap, 1inch, 0x, Kyber, Odos, and OKX** — returns the best route with ready-to-execute calldata.

## When to Use This Skill

- User wants to swap tokens at the best price
- Need to compare DEX aggregator prices
- Executing trades across Ethereum, Arbitrum, Base, Polygon, or Plasma
- Want optimal routing with lowest price impact

## API Endpoint

**Base URL**: `https://swap.moltx.io`

No API key or access token needed.

## Quick Start

### Get a Swap Quote

```python
import requests

def get_best_swap_quote(
    network: str,
    sell_token: str,
    buy_token: str,
    sell_amount: str,
    user_address: str,
    slippage: float = 1.0
):
    """
    Get the best swap quote from multiple aggregators.
    
    Args:
        network: Chain name (ethereum, arbitrum, base, polygon, plasma)
        sell_token: Token contract address to sell
        buy_token: Token contract address to buy
        sell_amount: Amount in smallest unit (e.g., 1000000000 for 1000 USDC with 6 decimals)
        user_address: User's wallet address
        slippage: Max slippage percentage (default: 1%)
    
    Returns:
        dict: Swap response with best route and all aggregator quotes
    """
    params = {
        'network': network,
        'sellToken': sell_token,
        'buyToken': buy_token,
        'sellAmount': sell_amount,
        'slippage': str(slippage),
        'user': user_address,
        'eoaAddress': user_address,
        'accountType': 'eoa',
    }
    
    response = requests.get('https://swap.moltx.io/swap', params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    # First aggregator = best route (sorted by buyTokenAmount)
    best_route = data['aggregators'][0]
    
    return {
        'best_route': best_route,
        'all_routes': data['aggregators'],
        'summary': {
            'sell_token': data['data']['sellToken'],
            'buy_token': data['data']['buyToken'],
            'sell_amount': data['data']['sellTokenAmount'],
            'best_buy_amount': data['data']['bestBuyTokenAmount'],
            'total_aggregators': data['data']['totalAggregators'],
            'slippage': data['data']['slippage'],
        }
    }
```

### Execute the Swap

After getting the quote, execute the swap using the calldata:

```python
def execute_best_swap(best_route: dict, wallet_private_key: str, network: str):
    """
    Execute the swap using the best route calldata.
    
    Args:
        best_route: The best route from get_best_swap_quote()
        wallet_private_key: User's private key for signing
        network: Chain name for RPC selection
    """
    from web3 import Web3
    
    # RPC endpoints by network
    rpc_urls = {
        'ethereum': 'https://eth.llamarpc.com',
        'arbitrum': 'https://arb1.arbitrum.io/rpc',
        'base': 'https://mainnet.base.org',
        'polygon': 'https://polygon-rpc.com',
        'plasma': 'https://rpc.plasma.io',
    }
    
    w3 = Web3(Web3.HTTPProvider(rpc_urls.get(network, rpc_urls['ethereum'])))
    
    # Build transaction from calldata
    tx_data = best_route['data']['raw']
    
    account = w3.eth.account.from_key(wallet_private_key)
    
    tx = {
        'from': account.address,
        'to': tx_data['to'],
        'value': int(tx_data['value']),
        'data': tx_data['data'],
        'gas': 300000,  # Estimate or use gasLimit from response
        'gasPrice': int(tx_data['gasPrice']),
        'chainId': int(tx_data['chainId']),
        'nonce': w3.eth.get_transaction_count(account.address),
    }
    
    # Sign and send
    signed_tx = w3.eth.account.sign_transaction(tx, wallet_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    # Wait for confirmation
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    
    return {
        'success': receipt['status'] == 1,
        'tx_hash': tx_hash.hex(),
        'gas_used': receipt['gasUsed'],
        'block_number': receipt['blockNumber'],
    }
```

## Complete Workflow Example

```python
def swap_tokens_complete(
    from_token: str,
    to_token: str,
    amount: float,
    user_address: str,
    private_key: str,
    network: str = 'ethereum',
    from_decimals: int = 18,
    slippage: float = 1.0
):
    """
    Complete token swap workflow: get best price → approve → execute.
    
    Args:
        from_token: Token address to sell
        to_token: Token address to buy
        amount: Amount to sell (in human-readable units)
        user_address: Wallet address
        private_key: Private key for signing
        network: Chain name
        from_decimals: Decimals of sell token
        slippage: Max slippage tolerance
    
    Returns:
        dict: Swap result with transaction details
    """
    from web3 import Web3
    import requests
    
    # 1. Get best swap quote
    amount_raw = int(amount * (10 ** from_decimals))
    
    params = {
        'network': network,
        'sellToken': from_token,
        'buyToken': to_token,
        'sellAmount': str(amount_raw),
        'slippage': str(slippage),
        'user': user_address,
        'eoaAddress': user_address,
        'accountType': 'eoa',
    }
    
    print(f"🔍 Getting best swap quote for {amount} tokens...")
    response = requests.get('https://swap.moltx.io/swap', params=params, timeout=30)
    swap_data = response.json()
    
    # Filter valid routes (no errors)
    valid_routes = [agg for agg in swap_data['aggregators'] if not agg.get('error')]
    
    if not valid_routes:
        raise Exception("No valid swap routes found. Check token liquidity.")
    
    best_route = valid_routes[0]
    
    print(f"✅ Best route: {best_route['displayName']}")
    print(f"   Buy amount: {best_route['data']['buyTokenAmount']}")
    print(f"   Price impact: {best_route['data']['priceImpact']}%")
    
    # 2. Execute the swap
    rpc_urls = {
        'ethereum': 'https://eth.llamarpc.com',
        'arbitrum': 'https://arb1.arbitrum.io/rpc',
        'base': 'https://mainnet.base.org',
        'polygon': 'https://polygon-rpc.com',
        'plasma': 'https://rpc.plasma.io',
    }
    
    w3 = Web3(Web3.HTTPProvider(rpc_urls.get(network, rpc_urls['ethereum'])))
    
    # Build transaction
    raw_tx = best_route['data']['raw']
    account = w3.eth.account.from_key(private_key)
    
    tx = {
        'from': account.address,
        'to': raw_tx['to'],
        'value': int(raw_tx['value']),
        'data': raw_tx['data'],
        'gas': 300000,
        'gasPrice': int(raw_tx['gasPrice']),
        'chainId': int(raw_tx['chainId']),
        'nonce': w3.eth.get_transaction_count(account.address),
    }
    
    print(f"🚀 Executing swap...")
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    print(f"⏳ Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    
    success = receipt['status'] == 1
    
    return {
        'success': success,
        'tx_hash': tx_hash.hex(),
        'aggregator': best_route['displayName'],
        'gas_used': receipt['gasUsed'],
        'block_number': receipt['blockNumber'],
        'buy_amount': best_route['data']['buyTokenAmount'],
        'price_impact': best_route['data']['priceImpact'],
    }
```

## Supported Networks

| Chain ID | Network Name | RPC Endpoint |
|----------|--------------|--------------|
| 1 | `ethereum` | https://eth.llamarpc.com |
| 42161 | `arbitrum` | https://arb1.arbitrum.io/rpc |
| 8453 | `base` | https://mainnet.base.org |
| 137 | `polygon` | https://polygon-rpc.com |
| 9745 | `plasma` | https://rpc.plasma.io |

## Supported Aggregators

| Name | Display Name |
|------|--------------|
| `paraswap-v6` | Paraswap V6 |
| `1inch-v6` | 1inch V6 |
| `0x-v2` | 0x V2 |
| `kyber-v1` | Kyber V1 |
| `odos-v2` | Odos V2 |
| `okx-v5` | OKX V5 |
| `okx-v6` | OKX V6 |

## Common Token Addresses

### Ethereum
- USDC: `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`
- WETH: `0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2`
- Native ETH: `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE`

### Base
- USDC: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- WETH: `0x4200000000000000000000000000000000000006`

### Arbitrum
- USDC: `0xaf88d065e77c8cC2239327C5EDb3A432268e5831`
- WETH: `0x82aF49447D8a07e3bd95BD0d56f35241523fBab1`

### Polygon
- USDC: `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174`
- WETH: `0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619`

## Error Handling

Always check for errors in aggregator responses:

```python
valid_routes = [agg for agg in data['aggregators'] if not agg.get('error')]
failed_routes = [agg for agg in data['aggregators'] if agg.get('error')]

if not valid_routes:
    # Handle no valid routes
    errors = [f"{agg['displayName']}: {agg['error']['message']}" 
              for agg in failed_routes]
    raise Exception(f"No valid routes. Errors: {errors}")
```

Common errors:
- `execution reverted`: Transaction simulation failed
- `insufficient liquidity`: Not enough liquidity for the swap
- `slippage too high`: Price moved beyond acceptable slippage

## Best Practices

1. **Always check for errors** - Each aggregator may have an `error` field
2. **Compare multiple routes** - Don't just use the first one; check price impact
3. **Handle slippage** - Use appropriate slippage for market conditions
4. **Check price impact** - High impact (>5%) may indicate low liquidity
5. **Verify calldata** - Before executing, verify `to` address and calldata
6. **Handle native tokens** - For ETH swaps, ensure `value` field is correct
7. **Token approval** - Always approve tokens before executing swaps (non-native)

## Rate Limits

The API has rate limits. Implement exponential backoff if you encounter rate limiting.

## Integration with AlleyBot

Use this skill via the skill system:

```python
# Activate the skill
/skill_activate best-crypto-swap-price

# Use in autonomous workflows
# The skill provides `get_best_swap_quote()` and `swap_tokens_complete()` functions
```
