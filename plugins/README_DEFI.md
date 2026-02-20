# DeFi Plugins for AlleyBot

This directory contains two powerful DeFi plugins that integrate with Moltx.io skill APIs.

## 📁 Plugins Overview

### 1. Best Crypto Swap Price Plugin (`best_crypto_swap_price/`)
**Integration:** https://swap.moltx.io

**Features:**
- 🔄 Get best swap quotes across multiple DEX aggregators
- 📊 Compare prices from Paraswap, 1inch, 0x, Kyber, Odos, OKX
- 💰 Generate ready-to-execute transaction calldata
- 🌐 Support for Ethereum, Arbitrum, Base, Polygon, Plasma
- 🪙 Common token symbols (USDC, WETH, etc.) for convenience

**Commands:**
```
/swap_quote <network> <sell_token> <buy_token> <sell_amount> [slippage]
/compare_aggregators <network> <sell_token> <buy_token> <sell_amount>
/swap_tokens <network> <sell_symbol> <buy_symbol> <amount>
/supported_tokens
```

**Examples:**
```bash
# Get best quote for 1000 USDC → WETH on Ethereum
/swap_quote ethereum USDC WETH 1000000000 1.0

# Compare all aggregators
/compare_aggregators base USDC WETH 500000000

# Quick swap with symbols
/swap_tokens ethereum USDC WETH 1000
```

### 2. Fluid Lending Plugin (`fluid_lending/`)
**Integration:** https://defi.moltx.io

**Features:**
- 🏦 Check Fluid Protocol lending positions on Base
- 💸 Calculate earnings projections
- 📊 Track supply APR and rewards APR
- 🪙 Support for fUSDC, fUSDbC, fDAI, fWETH
- 📈 Portfolio value tracking

**Commands:**
```
/fluid_positions <address>
/fluid_earnings <address> [days]
/fluid_stats
/fluid_apr
```

**Examples:**
```bash
# Check positions for an address
/fluid_positions 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45

# Calculate 30-day earnings
/fluid_earnings 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45 30

# Check current APRs
/fluid_apr
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- requests library (`pip install requests`)
- AlleyBot core system

### Plugin Registration
The plugins are automatically registered with AlleyBot's plugin manager. No additional configuration needed.

### Environment Variables
No API keys required - both Moltx.io skill endpoints are public.

## 🔧 Technical Details

### Best Crypto Swap Price Plugin
- **Base URL:** `https://swap.moltx.io`
- **Endpoint:** `/swap`
- **Method:** GET
- **Response:** JSON with aggregator quotes and execution data

### Fluid Lending Plugin
- **Base URL:** `https://defi.moltx.io`
- **Endpoint:** `/positions`
- **Method:** GET
- **Response:** JSON with user positions and APR data

## 📊 API Integration

### Supported Networks (Swap)
- Ethereum
- Arbitrum
- Base
- Polygon
- Plasma

### Supported Aggregators (Swap)
- Paraswap V6
- 1inch V6
- 0x V2
- Kyber V1
- Odos V2
- OKX V5/V6

### Supported Tokens (Fluid - Base)
- fUSDC (Fluid USDC)
- fUSDbC (Fluid USD Base Coin)
- fDAI (Fluid DAI)
- fWETH (Fluid Wrapped ETH)

## 🔒 Security & Safety

- **Read-Only Operations:** Both plugins only read data, no private keys required
- **No Fund Access:** Plugins cannot execute transactions or access funds
- **Public APIs:** Uses public Moltx.io skill endpoints
- **Input Validation:** All user inputs are validated before API calls

## 🛠️ Error Handling

Both plugins include comprehensive error handling:
- Network validation
- Address validation
- API timeout handling
- Graceful fallbacks
- Clear error messages

## 📈 Use Cases

### Trading & DeFi Operations
- Find best DEX prices before swapping
- Compare aggregator fees and routes
- Get execution calldata for manual swaps
- Track gas costs across aggregators

### Lending & Yield Farming
- Monitor Fluid lending positions
- Calculate potential earnings
- Track APR changes over time
- Portfolio value assessment

## 🔮 Future Enhancements

### Swap Plugin
- Real-time price alerts
- Historical price tracking
- Gas optimization suggestions
- Multi-hop routing

### Fluid Plugin
- Auto-compounding calculations
- Risk assessment metrics
- Portfolio diversification suggestions
- Integration with other lending protocols

## 🐛 Troubleshooting

### Common Issues
1. **"Plugin not loaded"** - Check plugin registration in plugin manager
2. **"API request failed"** - Check network connectivity and API status
3. **"Invalid address"** - Ensure address starts with "0x" and is 42 characters
4. **"Unknown token"** - Use token addresses instead of symbols for less common tokens

### Debug Mode
Enable debug logging to see detailed API responses:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Support

For issues with:
- **Plugin functionality:** Check AlleyBot logs
- **API endpoints:** Visit https://skill.moltx.io
- **Moltx.io skills:** Check skill documentation

## 📄 License

These plugins are part of AlleyBot and follow the same license terms.

---

**Happy DeFi operations! 🚀💰**
