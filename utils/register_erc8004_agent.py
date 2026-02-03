#!/usr/bin/env python3
"""
Register AlleyBot on ERC-8004 (Trustless Agents)
Creates on-chain agent identity NFT on Ethereum mainnet
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Agent profile configuration
AGENT_PROFILE = {
    "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
    "name": "AlleyBot",
    "description": "Autonomous AI agent with advanced capabilities across Moltx, MoltBook, and multiple platforms. Features AI-powered posting, intelligent engagement, trending analysis, and multi-platform presence.",
    "image": "https://cdn.moltx.io/avatars/490875df-9927-4994-ad0f-f42fb34af930/e555c71d-885f-4323-902d-ebb751ef561f.jpg",
    "services": [
        {
            "name": "web",
            "url": "https://apeshit.fun"
        },
        {
            "name": "twitter",
            "url": "https://x.com/DegenApeDev"
        },
        {
            "name": "moltx",
            "url": "https://moltx.io/@AlleyBot"
        }
    ],
    "capabilities": [
        "autonomous_posting",
        "ai_generation",
        "trending_analysis",
        "multi_platform_engagement",
        "token_deployment",
        "intelligent_conversations",
        "rag_memory"
    ]
}

# ERC-8004 Contract addresses (Ethereum Mainnet)
IDENTITY_REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
REPUTATION_REGISTRY = "0x8004BAa17C55a88189AE136b182e5fdA19dE9b63"


def get_credentials():
    """Get required credentials from environment"""
    base_wallet = os.getenv('BASE_WALLET')
    bankr_api_key = os.getenv('BANKR_API_KEY')
    
    if not base_wallet:
        print("❌ BASE_WALLET not found in .env")
        return None, None
    
    if not bankr_api_key:
        print("⚠️  BANKR_API_KEY not found - will use manual registration")
        return base_wallet, None
    
    return base_wallet, bankr_api_key


def save_agent_profile():
    """Save agent profile JSON to file"""
    profile_file = Path(__file__).parent.parent / "data" / "alleybot_erc8004_profile.json"
    profile_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(profile_file, 'w') as f:
        json.dump(AGENT_PROFILE, f, indent=2)
    
    print(f"💾 Agent profile saved to: {profile_file}")
    return profile_file


def register_via_frontend():
    """Instructions for registering via 8004.org frontend"""
    print("\n" + "="*60)
    print("📋 MANUAL REGISTRATION VIA 8004.ORG")
    print("="*60)
    print("\nFollow these steps:")
    print("\n1. Visit https://www.8004.org")
    print("\n2. Connect your wallet:")
    print(f"   Address: {os.getenv('BASE_WALLET')}")
    print("\n3. Fill in agent details:")
    print(f"   Name: {AGENT_PROFILE['name']}")
    print(f"   Description: {AGENT_PROFILE['description']}")
    print(f"   Image: {AGENT_PROFILE['image']}")
    print("\n4. Add services:")
    for service in AGENT_PROFILE['services']:
        print(f"   - {service['name']}: {service['url']}")
    print("\n5. Click 'Register Agent'")
    print("\n6. Confirm transaction (~0.005 ETH gas)")
    print("\n7. You'll receive an ERC-721 NFT representing your agent!")
    print("\n" + "="*60)
    print("\n💡 Make sure you have ~0.01 ETH on Ethereum mainnet for gas")
    print("   Use Bankr to bridge: 'Bridge 0.01 ETH from Base to Ethereum'")
    print("\n" + "="*60)


def register_via_bankr(bankr_api_key):
    """Register using Bankr API (if available)"""
    import requests
    
    print("\n🤖 Attempting registration via Bankr API...")
    
    # Save profile first
    profile_file = save_agent_profile()
    
    # Note: This is a placeholder - actual Bankr integration would require
    # specific API endpoints for ERC-8004 registration
    print("\n⚠️  Bankr API integration for ERC-8004 not yet implemented")
    print("   Please use manual registration via 8004.org")
    
    return False


def check_registration_status(wallet_address):
    """Check if agent is already registered"""
    try:
        from web3 import Web3
        
        # Connect to Ethereum mainnet
        w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))
        
        # ERC-8004 Identity Registry ABI (simplified)
        abi = [
            {
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        contract = w3.eth.contract(address=IDENTITY_REGISTRY, abi=abi)
        balance = contract.functions.balanceOf(wallet_address).call()
        
        if balance > 0:
            print(f"\n✅ Agent already registered! You own {balance} agent NFT(s)")
            return True
        else:
            print("\n📝 Agent not yet registered")
            return False
            
    except Exception as e:
        print(f"\n⚠️  Could not check registration status: {e}")
        print("   Proceeding with registration instructions...")
        return False


def main():
    print("="*60)
    print("🆔 ALLEYBOT ERC-8004 REGISTRATION")
    print("="*60)
    print("\nThis will register AlleyBot on-chain with:")
    print("- Verifiable agent identity NFT (ERC-721)")
    print("- On-chain reputation system")
    print("- Discoverability in agent ecosystem")
    print("\n" + "="*60)
    
    # Get credentials
    base_wallet, bankr_api_key = get_credentials()
    if not base_wallet:
        print("\n❌ Missing BASE_WALLET. Check your .env file.")
        return
    
    print(f"\n✅ Wallet address: {base_wallet}")
    
    # Check if already registered
    if check_registration_status(base_wallet):
        print("\n✅ AlleyBot is already registered on ERC-8004!")
        print(f"   View on Etherscan: https://etherscan.io/address/{IDENTITY_REGISTRY}")
        return
    
    # Save agent profile
    profile_file = save_agent_profile()
    
    # Attempt Bankr registration if API key available
    if bankr_api_key:
        success = register_via_bankr(bankr_api_key)
        if success:
            print("\n✅ Registration complete via Bankr!")
            return
    
    # Fall back to manual registration
    register_via_frontend()
    
    print("\n📊 After registration:")
    print("1. You'll receive an agent identity NFT")
    print("2. Link your $ALYBOT token to your profile")
    print("3. Build on-chain reputation")
    print("4. Become discoverable in agent ecosystem")
    print("\n✅ Registration instructions complete!")


if __name__ == '__main__':
    main()
