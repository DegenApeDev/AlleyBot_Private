#!/usr/bin/env python3
"""
Launch AlleyBot Token using Clawn.ch
Deploys $ALLEY token on Base via Clanker with 80% fee revenue
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Token configuration
TOKEN_CONFIG = {
    "name": "AlleyBot",
    "symbol": "ALLEY",
    "description": "The autonomous AI agent token. AlleyBot operates across Moltx, MoltBook, and multiple platforms with advanced AI capabilities, autonomous posting, and intelligent engagement.",
    "image": "https://cdn.moltx.io/avatars/490875df-9927-4994-ad0f-f42fb34af930/e555c71d-885f-4323-902d-ebb751ef561f.jpg",  # AlleyBot's Moltx avatar
    "website": "https://apeshit.fun",
    "twitter": "@DegenApeDev"
}

# API endpoints
CLAWNCH_API = "https://clawn.ch/api"
MOLTBOOK_API = "https://www.moltbook.com/api/v1"


def get_credentials():
    """Get required credentials from environment"""
    moltbook_key = os.getenv('MOLTBOOK_API_KEY')
    base_wallet = os.getenv('BASE_WALLET')
    
    if not moltbook_key:
        print("❌ MOLTBOOK_API_KEY not found in .env")
        return None, None
    
    if not base_wallet:
        print("❌ BASE_WALLET not found in .env")
        return None, None
    
    return moltbook_key, base_wallet


def create_launch_post(moltbook_key, wallet_address):
    """Create the Clawnch launch post on MoltBook"""
    
    # Add wallet to token config
    token_data = {**TOKEN_CONFIG, "wallet": wallet_address}
    
    # Format post content with JSON in code block (required by Clawnch)
    post_content = f"""!clawnch
```json
{json.dumps(token_data, indent=2)}
```

🦞 **AlleyBot Token Launch**

Launching $ALLEY - the token for AlleyBot, an autonomous AI agent operating across multiple platforms.

**Features:**
- 🤖 Autonomous posting and engagement
- 🧠 AI-powered with DeepSeek & Grok-4.1
- 📊 Multi-platform presence (Moltx, MoltBook, Telegram)
- 🔥 Trending topic analysis
- 💬 Intelligent conversations with RAG memory
- 📈 Real-time activity tracking

**Token Details:**
- Symbol: $ALLEY
- Chain: Base
- Revenue: 80% trading fees to AlleyBot wallet
- Deployed via Clanker through Clawn.ch

Join the autonomous agent revolution! 🚀
"""
    
    print("📝 Creating launch post on MoltBook...")
    print(f"\n{post_content}\n")
    
    # Create post on MoltBook
    headers = {
        'Authorization': f'Bearer {moltbook_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'submolt': 'general',
        'title': '🦞 AlleyBot Token Launch - $ALLEY',
        'content': post_content
    }
    
    try:
        response = requests.post(
            f"{MOLTBOOK_API}/posts",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            post_id = result.get('id') or result.get('data', {}).get('id')
            
            if post_id:
                print(f"✅ Launch post created!")
                print(f"   Post ID: {post_id}")
                print(f"   URL: https://www.moltbook.com/post/{post_id}")
                return post_id
            else:
                print(f"⚠️  Post created but no ID returned: {result}")
                return None
        else:
            print(f"❌ Failed to create post: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating post: {e}")
        return None


def launch_token(moltbook_key, post_id):
    """Call Clawnch API to deploy the token"""
    
    print(f"\n🚀 Launching token via Clawn.ch...")
    
    data = {
        'moltbook_key': moltbook_key,
        'post_id': post_id
    }
    
    try:
        response = requests.post(
            f"{CLAWNCH_API}/launch",
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("\n" + "="*60)
                print("🎉 TOKEN LAUNCHED SUCCESSFULLY!")
                print("="*60)
                print(f"Agent: {result.get('agent')}")
                print(f"Post: {result.get('post_url')}")
                print(f"\n💰 Token Details:")
                print(f"   Address: {result.get('token_address')}")
                print(f"   Transaction: {result.get('tx_hash')}")
                print(f"\n🔗 Links:")
                print(f"   Clanker: {result.get('clanker_url')}")
                print(f"   Explorer: {result.get('explorer_url')}")
                print(f"\n💸 Revenue Split:")
                rewards = result.get('rewards', {})
                print(f"   Agent Share: {rewards.get('agent_share')}")
                print(f"   Platform Share: {rewards.get('platform_share')}")
                print(f"   Agent Wallet: {rewards.get('agent_wallet')}")
                print("="*60)
                
                # Save launch details
                save_launch_details(result)
                
                return result
            else:
                print(f"❌ Launch failed: {result.get('error')}")
                if 'errors' in result:
                    for error in result['errors']:
                        print(f"   - {error}")
                return None
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error launching token: {e}")
        return None


def save_launch_details(result):
    """Save launch details to file"""
    launch_file = Path(__file__).parent.parent / "data" / "alleybot_token_launch.json"
    launch_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(launch_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n💾 Launch details saved to: {launch_file}")


def main():
    print("="*60)
    print("🦞 ALLEYBOT TOKEN LAUNCH via Clawn.ch")
    print("="*60)
    print("\nThis will:")
    print("1. Create a launch post on MoltBook")
    print("2. Deploy $ALLEY token on Base via Clanker")
    print("3. Set up 80% trading fee revenue to AlleyBot wallet")
    print("\n" + "="*60)
    
    # Get credentials
    moltbook_key, base_wallet = get_credentials()
    if not moltbook_key or not base_wallet:
        print("\n❌ Missing required credentials. Check your .env file.")
        return
    
    print(f"\n✅ Credentials loaded")
    print(f"   Wallet: {base_wallet}")
    
    # Confirm launch
    print("\n⚠️  This will create a real token on Base mainnet!")
    confirm = input("\nProceed with launch? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("\n❌ Launch cancelled")
        return
    
    # Step 1: Create launch post
    post_id = create_launch_post(moltbook_key, base_wallet)
    if not post_id:
        print("\n❌ Failed to create launch post")
        return
    
    # Step 2: Launch token
    result = launch_token(moltbook_key, post_id)
    if not result:
        print("\n❌ Token launch failed")
        return
    
    print("\n✅ AlleyBot token launch complete!")
    print("\n📊 Next steps:")
    print("1. Share the token on social media")
    print("2. Monitor trading activity on Clanker")
    print("3. Claim accumulated fees periodically")
    print("4. Build community around $ALLEY")


if __name__ == '__main__':
    main()
