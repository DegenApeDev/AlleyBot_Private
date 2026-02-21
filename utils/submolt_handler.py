#!/usr/bin/env python3
"""
Submolt management functions
"""

def execute_subscribe_submolt(api, params):
    """Subscribe to a submolt"""
    submolt_name = params.get('submolt_name', '')
    
    if not submolt_name:
        print("❌ No submolt name provided")
        return
    
    print(f"\n🏘️  Subscribing to m/{submolt_name}...")
    try:
        result = api.subscribe_submolt(submolt_name)
        print(f"✅ Successfully subscribed to m/{submolt_name}!")
        
        # Show submolt info
        try:
            submolt_info = api.get_submolt(submolt_name)
            print(f"\n📋 {submolt_info.get('display_name', submolt_name)}")
            print(f"   {submolt_info.get('description', 'No description')}")
            print(f"   {submolt_info.get('subscriber_count', 0)} subscribers")
        except:
            pass
            
    except Exception as e:
        if '404' in str(e):
            print(f"❌ Submolt 'm/{submolt_name}' not found")
            print("💡 Try 'list all submolts' to see available communities")
        elif '409' in str(e) or 'already' in str(e).lower():
            print(f"✓ Already subscribed to m/{submolt_name}")
        else:
            print(f"❌ Failed to subscribe: {e}")
