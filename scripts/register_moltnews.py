#!/usr/bin/env python3
"""
Register AlleyBot on MoltNews
Run this to start the registration process
"""
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.moltnews.moltnews import MoltNewsPlugin

def main():
    print("🔥 MoltNews Registration for AlleyBot")
    print("=" * 50)
    
    moltnews = MoltNewsPlugin()
    
    # Start registration
    result = moltnews.register_start(
        username="alleybot",
        display_name="AlleyBot News"
    )
    
    if result.get('success'):
        print("\n✅ Registration started!")
        print(f"\n🌐 Open this URL in your browser:")
        print(f"   {result['claim_url']}")
        print(f"\n📋 Enter this claim code on the page:")
        print(f"   {result['claim_code']}")
        print(f"\n📝 After you complete the verification, run:")
        print(f"   python3 scripts/activate_moltnews.py")
    else:
        print(f"\n❌ Registration failed: {result.get('error')}")
        print(f"Details: {result.get('details')}")

if __name__ == "__main__":
    main()
