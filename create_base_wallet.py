#!/usr/bin/env python3
"""
Generate a new Ethereum wallet for AlleyBot on BASE chain
"""

from eth_account import Account
import secrets
import json

def generate_wallet():
    """Generate a new Ethereum wallet"""
    # Generate random private key
    private_key = "0x" + secrets.token_hex(32)
    
    # Create account from private key
    account = Account.from_key(private_key)
    
    return {
        "address": account.address,
        "private_key": private_key
    }

if __name__ == "__main__":
    print("🔐 Generating new Ethereum wallet for AlleyBot on BASE chain...")
    print("")
    
    wallet = generate_wallet()
    
    print("✅ Wallet generated successfully!")
    print("")
    print("=" * 60)
    print("BASE WALLET DETAILS")
    print("=" * 60)
    print(f"Address: {wallet['address']}")
    print(f"Private Key: {wallet['private_key']}")
    print("=" * 60)
    print("")
    print("⚠️  CRITICAL: Save the private key securely!")
    print("   This private key controls the wallet. Never share it.")
    print("")
    print("📝 Next steps:")
    print("1. Save private key to a secure location")
    print("2. Add BASE_WALLET to config.py")
    print("3. Update .env with BASE_WALLET_PRIVATE_KEY (if needed)")
    print("4. Test receiving on BASE network")
    print("")
    print("🌐 Network: BASE (Ethereum L2)")
    print("   Chain ID: 8453")
    print("   RPC: https://mainnet.base.org")
    print("   Explorer: https://basescan.org")
    print("")
    
    # Save to file
    with open("base_wallet.json", "w") as f:
        json.dump(wallet, f, indent=2)
    
    print("✅ Wallet details saved to base_wallet.json")
    print("   ⚠️  DELETE THIS FILE after backing up the private key!")
