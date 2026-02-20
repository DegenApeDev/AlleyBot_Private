# Contract Balance Enhancement - Base Wallet Plugin

## 🎯 New Functionality Added

AlleyBot can now check balances for **any specified contract address** on Base network, not just pre-defined tokens!

## 📱 New Commands

### **Contract Balance Commands:**
```bash
/contract_balance <address> <contract_address>           # Check specific contract
/multi_contract_balance <address> <contract1,contract2,...> # Check multiple contracts
```

### **Examples:**
```bash
# Check USDC balance by contract address
/contract_balance 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45 0xd9aAEc86BcD3759b343a6363E90E81E89Dca5AbA

# Check multiple contracts at once
/multi_contract_balance 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45 0xd9aAEc86BcD3759b343a6363E90E81E89Dca5AbA,0x4200000000000000000000000000000000000006

# Check unknown/new token contracts
/contract_balance 0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45 0xYourNewTokenContractAddress
```

## 🔧 Enhanced Features

### **Smart Contract Integration:**
- ✅ **Any ERC-20 Contract** - Works with any token contract
- ✅ **Auto Token Discovery** - Tries to get token name/symbol/decimals
- ✅ **Fallback Handling** - Works even if token info unavailable
- ✅ **Multi-Contract Support** - Check multiple contracts in one command

### **Contract Info Detection:**
- **Name Detection** - Calls `name()` function
- **Symbol Detection** - Calls `symbol()` function  
- **Decimals Detection** - Calls `decimals()` function
- **Graceful Fallback** - Uses defaults if calls fail

### **Enhanced Balance Queries:**
- **Standard ERC-20** - `balanceOf(address)` calls
- **Custom Contracts** - Works with any contract implementing balanceOf
- **Error Handling** - Clear messages for non-ERC-20 contracts
- **Format Flexibility** - Handles unknown tokens gracefully

## 📊 Sample Output

### **Single Contract:**
```
💰 Contract Balance
========================================

Wallet: 0x742d35Cc...b4Db45
Contract: 0xd9aAEc86...ca5AbA
Token: USD Coin (USDC)
Type: ERC-20
Balance: 1,234.567890 USDC
Decimals: 6
```

### **Multiple Contracts:**
```
💰 Multiple Contract Balances
========================================

Wallet: 0x742d35Cc...b4Db45
Contracts Checked: 3
Successful: 3

🪙 Balances:
   1,234.567890 USD Coin (USDC)
   0.500000 Wrapped Ether (WETH)
   0.000000 Unknown Token - empty
```

## 🛠️ Technical Implementation

### **New Methods Added:**
```python
def get_contract_balance(address, contract_address):
    """Get balance for any contract address"""

def _get_contract_info(contract_address):
    """Try to get token info from contract"""

def get_all_balances(address, tokens=None, contracts=None):
    """Enhanced to handle contract addresses"""
```

### **RPC Calls Used:**
- `eth_call` with `balanceOf(address)` selector
- `eth_call` with `name()` selector  
- `eth_call` with `symbol()` selector
- `eth_call` with `decimals()` selector

### **Function Selectors:**
- `balanceOf`: `0x70a08231`
- `name`: `0x06fdde03`
- `symbol`: `0x95d89b41`
- `decimals`: `0x313ce567`

## 🎯 Use Cases

### **Token Discovery:**
- Check balances for **newly launched tokens**
- Verify **airdrop tokens** in wallet
- Monitor **testnet tokens** and experimental contracts

### **Portfolio Management:**
- Track **custom token positions**
- Monitor **DeFi protocol tokens**
- Check **governance token** holdings

### **Contract Verification:**
- Verify if a wallet holds **specific contract tokens**
- Check **LP token** balances
- Monitor **staking token** positions

## 🔍 Advanced Features

### **Contract Type Detection:**
- **ERC-20 Standard** - Full token info available
- **Unknown Contracts** - Balance only, no metadata
- **Non-Token Contracts** - Clear error messages

### **Error Handling:**
- **Invalid Addresses** - Validation and helpful errors
- **Non-ERC-20 Contracts** - Graceful failure handling
- **RPC Failures** - Automatic endpoint fallback

### **Performance:**
- **Batch Queries** - Multiple contracts in one call
- **Parallel Processing** - Efficient balance checking
- **Caching Ready** - Structure supports future caching

## 🚀 Integration Status

### **✅ Complete:**
- [x] Contract balance checking
- [x] Multi-contract support
- [x] Token info detection
- [x] Telegram commands added
- [x] Error handling implemented
- [x] Testing verified

### **📱 Commands Ready:**
- `/contract_balance` - Single contract
- `/multi_contract_balance` - Multiple contracts
- All existing commands still work

## 🔮 Future Enhancements

### **Planned:**
- **NFT Balance Checking** - ERC-721/ERC-1155 support
- **LP Token Detection** - Automated liquidity pool identification
- **Price Integration** - Real-time token pricing
- **Contract Metadata** - Enhanced token information

### **Potential:**
- **Cross-Chain Support** - Extend to other networks
- **Historical Tracking** - Balance changes over time
- **Alert System** - Balance notifications

---

**AlleyBot now supports unlimited contract balance checking on Base!** 🦞🔗

Check any ERC-20 token contract with `/contract_balance <address> <contract_address>`! 🚀
