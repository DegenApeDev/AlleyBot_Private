#!/usr/bin/env python3
"""
Deploy AlleyBot token on BASE using Deplous system
Earns 0.5% trade fees on every buy/sell
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Token details
TOKEN_NAME = "AlleyBot"
TOKEN_TICKER = "ALLEY"
BASE_WALLET_ADDRESS = os.getenv('BASE_WALLET_PUBLIC_ADDRESS')
BASE_WALLET_PRIVATE_KEY = os.getenv('BASE_WALLET_PRIVATE_KEY')

# Deplous post ID
DEPLOUS_POST_ID = "d0bdad96-6693-4149-b0d4-3f283a2a7b64"

# Moltbook API
MOLTBOOK_API_KEY = os.getenv('MOLTBOOK_API_KEY')
MOLTBOOK_API_URL = "https://www.moltbook.com/api/v1"

def create_deplous_wallet_config():
    """Create Deplous wallet configuration file"""
    config_dir = os.path.expanduser("~/.config/deplous")
    config_file = os.path.join(config_dir, "wallet.json")
    
    if not BASE_WALLET_PRIVATE_KEY:
        print("❌ BASE_WALLET_PRIVATE_KEY not found in .env")
        print("   Add it to your .env file first")
        return False
    
    # Create config directory
    os.makedirs(config_dir, exist_ok=True)
    
    # Create wallet config
    wallet_config = {
        "address": BASE_WALLET_ADDRESS,
        "privateKey": BASE_WALLET_PRIVATE_KEY
    }
    
    # Save to file
    with open(config_file, 'w') as f:
        json.dump(wallet_config, f, indent=2)
    
    # Set secure permissions
    os.chmod(config_file, 0o600)
    
    print(f"✅ Created Deplous wallet config: {config_file}")
    print(f"   Address: {BASE_WALLET_ADDRESS}")
    return True

def deploy_token():
    """Post deploy command to Moltbook"""
    if not MOLTBOOK_API_KEY:
        print("❌ MOLTBOOK_API_KEY not found in .env")
        return False
    
    # Format deploy command according to Deplous spec
    deploy_comment = f"deploy + {TOKEN_NAME} ${TOKEN_TICKER}\n\n{BASE_WALLET_ADDRESS}"
    
    print(f"\n📝 Deploying token...")
    print(f"   Name: {TOKEN_NAME}")
    print(f"   Ticker: ${TOKEN_TICKER}")
    print(f"   Address: {BASE_WALLET_ADDRESS}")
    print(f"\n   Comment:\n{deploy_comment}\n")
    
    # Post comment to Deplous post
    url = f"{MOLTBOOK_API_URL}/posts/{DEPLOUS_POST_ID}/comments"
    headers = {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "content": deploy_comment
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        print("✅ Deploy command posted to Moltbook!")
        print(f"   Post: https://www.moltbook.com/post/{DEPLOUS_POST_ID}")
        print("\n⏳ Deplous system will process the deployment...")
        print("   This may take a few minutes")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to post deploy command: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return False

def show_next_steps():
    """Show what to do after deployment"""
    print("\n" + "=" * 60)
    print("📋 NEXT STEPS")
    print("=" * 60)
    print("\n1. ⏳ Wait for Deplous to process deployment (few minutes)")
    print("   Check: https://www.moltbook.com/post/d0bdad96-6693-4149-b0d4-3f283a2a7b64")
    print("\n2. 🔍 Verify token on BaseScan:")
    print(f"   https://basescan.org/address/{BASE_WALLET_ADDRESS}")
    print("\n3. 💰 Trade fees accumulate automatically (0.5% per trade)")
    print("   Factory: 0x82a430e046BDF5Fc8a333Ec913a704c328286832")
    print("\n4. 💸 Claim fees anytime:")
    print("   - Go to factory contract on BaseScan")
    print("   - Call 'claim' function with your address")
    print("   - Or import private key to MetaMask and claim")
    print("\n5. 📢 Promote your token:")
    print("   - Post about $ALLEY on Moltbook")
    print("   - Share with community")
    print("   - Earn fees from every trade!")
    print("\n" + "=" * 60)
    print("🎉 AlleyBot token deployment initiated!")
    print("=" * 60)

def main():
    print("🚀 AlleyBot Token Deployment via Deplous")
    print("=" * 60)
    print(f"Token: {TOKEN_NAME} (${TOKEN_TICKER})")
    print(f"Chain: BASE (Ethereum L2)")
    print(f"Address: {BASE_WALLET_ADDRESS}")
    print(f"Fee: 0.5% on every trade → your wallet")
    print("=" * 60)
    
    # Step 1: Create wallet config
    print("\n📁 Step 1: Creating Deplous wallet config...")
    if not create_deplous_wallet_config():
        return
    
    # Step 2: Deploy token
    print("\n🚀 Step 2: Posting deploy command to Moltbook...")
    if not deploy_token():
        return
    
    # Step 3: Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()
