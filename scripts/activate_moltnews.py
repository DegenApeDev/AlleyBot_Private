#!/usr/bin/env python3
"""
Activate AlleyBot on MoltNews after human verification
Run this after completing the claim page verification
"""
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.moltnews.moltnews import MoltNewsPlugin

def main():
    print("🔥 MoltNews Activation for AlleyBot")
    print("=" * 50)
    
    moltnews = MoltNewsPlugin()
    
    # Activate
    result = moltnews.activate_account()
    
    if result.get('success'):
        print("\n✅ AlleyBot activated on MoltNews!")
        
        # Check status
        status = moltnews.check_status()
        if status.get('success'):
            print(f"\n📊 Status: {status.get('status')}")
            print(f"👤 Username: @{status.get('username')}")
            print(f"🏷️  Display Name: {status.get('display_name')}")
            print(f"✓ Claim Verified: {status.get('claim_verified')}")
        
        print("\n🤖 AlleyBot can now:")
        print("   • Fetch trending news")
        print("   • Get content suggestions from news topics")
        print("   • Cross-post news to Moltx")
        print("   • Reply to and repost news items")
    else:
        print(f"\n❌ Activation failed: {result.get('error')}")
        print("\n💡 Make sure you:")
        print("   1. Completed the claim page verification")
        print("   2. Waited for the human verification code")
        print("   3. Clicked 'Verify' on the page")

if __name__ == "__main__":
    main()
