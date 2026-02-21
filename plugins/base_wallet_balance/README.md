# Base Wallet Balance Plugin

## 🎯 Overview
AlleyBot can now check token balances for any wallet address on Base network! This plugin provides comprehensive balance checking capabilities with support for native ETH and ERC-20 tokens.

## 📱 Available Commands

### **Core Balance Commands:**
```bash
/base_balance <address> [token]           # Check specific token or all tokens
/base_eth_balance <address>                # Check ETH balance only  
/base_tokens                              # List all supported tokens
/base_wallet_summary <address>             # Get wallet overview
/add_base_token <symbol> <address> <name> <decimals>  # Add custom token
```

### **Examples:**
```bash
# Check all token balances
/base_balance 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45

# Check specific token
/base_balance 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45 USDC

# Quick ETH balance
/base_eth_balance 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45

# Wallet summary with USD value
/base_wallet_summary 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45

# Add custom token
/add_base_token PEPE 0x1234...abcd "Pepe Token" 18
```

## 🪙 Supported Tokens (Base Network)

| Token | Symbol | Address | Decimals |
|-------|--------|---------|----------|
| Ethereum | ETH | native | 18 |
| Wrapped Ethereum | WETH | 0x4200...0006 | 18 |
| USD Coin | USDC | 0xd9aA...c5AbA | 6 |
| USD Base Coin | USDbC | 0xd9aA...c5AbA | 6 |
| Dai Stablecoin | DAI | 0x50c5...57b3 | 18 |
| Wrapped Bitcoin | WBTC | 0x2bA2...2ba3 | 8 |
| Chainlink | LINK | 0x8836...632 | 18 |
| Uniswap | UNI | 0x3e25...2b64 | 18 |

## 🔧 Technical Features

### **Network Integration:**
- **RPC Endpoints:** Multiple Base RPC endpoints for redundancy
- **Fallback:** Automatic failover between providers
- **Speed:** Fast balance queries with 10s timeout

### **Token Support:**
- **Native ETH:** Direct balance queries
- **ERC-20 Tokens:** Standard `balanceOf` calls
- **Custom Tokens:** Dynamic token addition
- **Decimals:** Proper decimal handling for all tokens

### **Data Features:**
- **USD Estimation:** Basic USD value calculation
- **Formatted Output:** Human-readable balance formatting
- **Raw Values:** Access to raw wei/token amounts
- **Error Handling:** Comprehensive error reporting

## 📊 Sample Output

### **Single Token Balance:**
```
💰 Token Balance
========================================

Address: 0x742d35Cc...4Db45
Token: USDC (USD Coin)
Balance: 1,234.567890 USDC
```

### **Multi-Token Summary:**
```
💰 Wallet Balances
========================================

Address: 0x742d35Cc...4Db45
Network: Base
Total USD Value: $3,745.67

🪙 Balances:
   1.234567 WETH
   1,234.567890 USDC
   0.000000 DAI (empty)

⚠️  Errors:
   WBTC: API rate limit
```

### **Wallet Summary:**
```
💼 Wallet Summary
========================================

Address: 0x742d35Cc...4Db45
Network: Base
Total Tokens: 3
Total USD Value: $3,745.67

🪙 Holdings:
   1.234567 WETH
   1,234.567890 USDC
   0.500000 WBTC

📅 Last Updated: 2026-02-20 00:30:00
```

## 🛡️ Safety & Security

### **Read-Only Operations:**
- ✅ No private keys required
- ✅ No transaction capabilities
- ✅ Public RPC endpoints only
- ✅ No wallet access permissions

### **Input Validation:**
- ✅ Address format validation
- ✅ Token address verification
- ✅ RPC response validation
- ✅ Error boundary protection

## 🚀 Integration Status

### **✅ Complete Integration:**
- [x] Plugin created and tested
- [x] Telegram commands added
- [x] RPC connectivity verified
- [x] Balance queries working
- [x] Error handling implemented

### **📱 Telegram Commands Ready:**
- `/base_balance` - Main balance command
- `/base_eth_balance` - ETH only
- `/base_tokens` - List tokens
- `/base_wallet_summary` - Portfolio overview
- `/add_base_token` - Custom tokens

## 🔮 Future Enhancements

### **Planned Features:**
- Real-time price oracle integration
- Historical balance tracking
- Portfolio performance analytics
- Multi-wallet support
- Price alerts and notifications

### **Potential Integrations:**
- DeFi protocol position tracking
- NFT balance checking
- Transaction history analysis
- Gas price monitoring

## 🐛 Troubleshooting

### **Common Issues:**
1. **"RPC endpoints failed"** - Network connectivity issue
2. **"Invalid address"** - Check address format (0x...)
3. **"Unknown token"** - Use `/base_tokens` to see supported tokens
4. **"Empty balance"** - Wallet may have no tokens

### **Solutions:**
- Ensure valid Base network address
- Check token is supported on Base
- Verify network connectivity
- Try custom token addition for new tokens

---

**AlleyBot now has full Base network wallet balance capabilities!** 🦞💰

Check any wallet's token holdings instantly with `/base_balance <address>`! 🚀
