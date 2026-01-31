# AlleyBot BASE Wallet Setup

## Overview

AlleyBot now has a dedicated Ethereum wallet on the **BASE L2 network** for receiving donations with significantly lower transaction fees.

## Wallet Details

- **Address:** `0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5`
- **Network:** BASE (Ethereum L2)
- **Chain ID:** 8453
- **RPC URL:** https://mainnet.base.org
- **Block Explorer:** https://basescan.org/address/0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5

## Why BASE?

BASE is Coinbase's Ethereum Layer 2 network that offers:
- ✅ **Lower fees** - Transactions cost cents instead of dollars
- ✅ **Fast confirmations** - Blocks every 2 seconds
- ✅ **Ethereum security** - Inherits Ethereum's security
- ✅ **Easy onramp** - Direct from Coinbase
- ✅ **Growing ecosystem** - Popular with crypto users

## Private Key Security

⚠️ **CRITICAL:** The private key is stored in `base_wallet.json`

**Backup the private key NOW:**
```bash
# Copy to secure location
cp base_wallet.json ~/alleybot_base_wallet_BACKUP.json
chmod 600 ~/alleybot_base_wallet_BACKUP.json

# Or just save the private key to a password manager
cat base_wallet.json
```

**Then DELETE the file:**
```bash
rm base_wallet.json
```

The private key is:
- Your only way to access funds in this wallet
- Cannot be recovered if lost
- Should NEVER be shared or committed to git

## Integration Status

✅ **config.py** - BASE_WALLET added
✅ **main.py** - Post generation includes BASE address
✅ **smart_bot.py** - Displays BASE wallet on startup
✅ **Documentation** - This file

## Usage

### Receiving Donations

Users can send ETH or any ERC-20 token on BASE network to:
```
0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5
```

### Checking Balance

View on BaseScan:
https://basescan.org/address/0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5

### Sending Funds (Future)

To send funds from this wallet, you'll need:
1. The private key (from backup)
2. A web3 library (web3.py or ethers.js)
3. BASE network RPC connection

Example with web3.py:
```python
from web3 import Web3
from eth_account import Account

# Connect to BASE
w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))

# Load account
private_key = "YOUR_PRIVATE_KEY"
account = Account.from_key(private_key)

# Send transaction
tx = {
    'from': account.address,
    'to': '0xRecipientAddress',
    'value': w3.to_wei(0.01, 'ether'),
    'gas': 21000,
    'gasPrice': w3.eth.gas_price,
    'nonce': w3.eth.get_transaction_count(account.address),
    'chainId': 8453
}

signed_tx = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
```

## Adding to MetaMask

Users can add BASE network to MetaMask:
1. Open MetaMask
2. Click network dropdown
3. Click "Add Network"
4. Enter:
   - **Network Name:** BASE
   - **RPC URL:** https://mainnet.base.org
   - **Chain ID:** 8453
   - **Currency Symbol:** ETH
   - **Block Explorer:** https://basescan.org

Then add AlleyBot's address to send donations.

## Wallet Addresses Summary

AlleyBot now accepts donations on:
- **BTC:** `3FWrh7nEZofv62MMV5JbsS9M29aitF3Spy`
- **ETH (Mainnet):** `0xCffe06d3Cf0908C2452e7c336FEec507d5Afd41d`
- **BASE (L2):** `0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5` ⭐ **NEW - Lower fees!**
- **SOL:** `BUo8AVbxfV2FsTzm19HUsraPzghKDTm1bEfn4Yrp2VJm`

## Post Footer Format

Posts now include BASE wallet in footer:
```
—AlleyBot (library Pi • BASE: 0x72a6C33E...)
```

This is more prominent than the old BTC footer and emphasizes the lower-fee option.

## Security Checklist

- [ ] Private key backed up to secure location
- [ ] `base_wallet.json` deleted from project directory
- [ ] Private key NOT committed to git
- [ ] `.gitignore` includes `base_wallet.json` and `*_wallet.json`
- [ ] Private key stored in password manager or hardware wallet

## Future Enhancements

Potential additions:
- [ ] Automatic balance checking
- [ ] Thank donors on Moltbook when receiving BASE donations
- [ ] Display BASE balance on dashboard
- [ ] Multi-sig wallet for larger amounts
- [ ] Integration with BASE ecosystem apps

---

**Generated:** 2026-01-31
**Network:** BASE (Ethereum L2)
**Status:** Active and ready for donations
