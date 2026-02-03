#!/usr/bin/env python3
"""
Shill $ALYBOT token on 4claw
Creates a thread promoting the token on /crypto/ board
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.fourclaw.fourclaw import FourClawPlugin


def main():
    print("="*60)
    print("🦞 SHILL $ALYBOT ON 4CLAW")
    print("="*60)
    
    # Get token address from environment
    token_address = os.getenv('ALYBOT_TOKEN_ADDRESS')
    if not token_address:
        print("\n⚠️  ALYBOT_TOKEN_ADDRESS not found in .env")
        print("   Please add the token contract address to .env")
        return
    
    print(f"\n✅ Token address: {token_address}")
    
    # Initialize 4claw plugin
    config = {}
    fourclaw = FourClawPlugin(config)
    
    # Mock initialize (no core needed for standalone script)
    fourclaw.api_key = os.getenv('FOURCLAW_API_KEY')
    
    if not fourclaw.api_key:
        print("\n❌ FOURCLAW_API_KEY not found in .env")
        print("   Register at: https://www.4claw.org")
        print("\nTo register:")
        print("curl -X POST https://www.4claw.org/api/v1/agents/register \\")
        print("  -H \"Content-Type: application/json\" \\")
        print("  -d '{\"name\":\"AlleyBot\",\"description\":\"Autonomous AI agent with ERC-8004 identity\"}'")
        return
    
    print("✅ 4claw API key loaded")
    
    # Token details
    token_name = "AlleyBot"
    token_symbol = "ALYBOT"
    description = """Autonomous AI agent token with:
- Registered trustless agent on ERC-8004 (Ethereum)
- Verifiable on-chain identity
- Multi-platform presence (Moltx, MoltBook, Telegram)
- AI-powered posting and engagement
- 80% trading fees to agent wallet
- Real-time activity tracking"""
    
    print("\n📝 Creating shill thread on /crypto/...")
    print(f"   Token: ${token_symbol}")
    print(f"   Contract: {token_address}")
    
    # Create shill thread
    result = fourclaw.shill_token(
        token_name=token_name,
        token_symbol=token_symbol,
        token_address=token_address,
        description=description,
        board="crypto"
    )
    
    if "error" in result:
        print(f"\n❌ Failed to create thread: {result['error']}")
    else:
        thread_id = result.get('id', 'unknown')
        print(f"\n✅ Thread created successfully!")
        print(f"🔗 Thread ID: {thread_id}")
        print(f"🌐 View at: https://www.4claw.org/crypto/{thread_id}")
        print("\n🎉 $ALYBOT is now being shilled on 4claw!")


if __name__ == '__main__':
    main()
