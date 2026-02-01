#!/usr/bin/env python3
"""
Debug and test the new AlleyBot system
"""
import sys
import traceback
from alleybot_core import AlleyBotCore

def test_plugin_loading():
    """Test plugin loading"""
    print("🔍 Testing Plugin Loading...")
    
    try:
        core = AlleyBotCore()
        print(f"✅ Core initialized")
        print(f"📦 Plugins: {len(core.plugin_manager.plugins)}")
        print(f"🔧 Tasks: {len(core.plugin_manager.tasks)}")
        print(f"💬 Commands: {len(core.plugin_manager.commands)}")
        
        # Test each plugin
        for name, plugin in core.plugin_manager.plugins.items():
            print(f"  📦 {name}: {'✅' if plugin.initialized else '❌'}")
        
        return core
        
    except Exception as e:
        print(f"❌ Plugin loading failed: {e}")
        traceback.print_exc()
        return None

def test_commands(core):
    """Test basic commands"""
    print("\n🔍 Testing Commands...")
    
    test_commands = [
        'intelligence',
        'engagement', 
        'content',
        'analytics',
        'stats'
    ]
    
    for cmd in test_commands:
        try:
            print(f"  💬 Testing: {cmd}")
            result = core.run_command(cmd)
            if result:
                print(f"    ✅ {len(str(result))} chars returned")
            else:
                print(f"    ⚠️  No result")
        except Exception as e:
            print(f"    ❌ Error: {e}")

def test_plugin_functionality(core):
    """Test individual plugin functionality"""
    print("\n🔍 Testing Plugin Functionality...")
    
    # Test engagement plugin
    if 'engagement' in core.plugin_manager.plugins:
        try:
            print("  🤝 Testing engagement plugin...")
            engagement_plugin = core.plugin_manager.plugins['engagement']
            
            # Test stats
            if hasattr(engagement_plugin, 'show_engagement_stats'):
                stats = engagement_plugin.show_engagement_stats()
                print(f"    📊 Stats: {len(stats)} chars")
            
            # Test status
            if hasattr(engagement_plugin, 'engagement_status'):
                status = engagement_plugin.engagement_status()
                print(f"    📋 Status: {len(status)} chars")
                
        except Exception as e:
            print(f"    ❌ Engagement plugin error: {e}")
    
    # Test intelligence plugin
    if 'intelligence' in core.plugin_manager.plugins:
        try:
            print("  🧠 Testing intelligence plugin...")
            intelligence_plugin = core.plugin_manager.plugins['intelligence']
            
            # Test status
            if hasattr(intelligence_plugin, 'intelligence_status'):
                status = intelligence_plugin.intelligence_status()
                print(f"    📋 Status: {len(status)} chars")
                
        except Exception as e:
            print(f"    ❌ Intelligence plugin error: {e}")

def test_api_connectivity(core):
    """Test API connectivity"""
    print("\n🔍 Testing API Connectivity...")
    
    try:
        # Test basic API call
        feed = core.api.get_feed(limit=1)
        if isinstance(feed, dict):
            posts = feed.get('posts', [])
        else:
            posts = feed
        
        print(f"  📡 API Feed: {len(posts)} posts")
        
        # Test profile
        try:
            profile = core.api.get_public_profile(name="AlleyBot")
            print(f"  👤 Profile: {'✅' if profile else '❌'}")
        except Exception as e:
            print(f"  👤 Profile Error: {e}")
            
    except Exception as e:
        print(f"  ❌ API Error: {e}")

def main():
    """Main test function"""
    print("🚀 AlleyBot Debug Test Suite")
    print("=" * 50)
    
    # Test 1: Plugin Loading
    core = test_plugin_loading()
    if not core:
        print("❌ Cannot continue - core initialization failed")
        return 1
    
    # Test 2: Commands
    test_commands(core)
    
    # Test 3: Plugin Functionality
    test_plugin_functionality(core)
    
    # Test 4: API Connectivity
    test_api_connectivity(core)
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    try:
        core.cleanup()
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️  Cleanup error: {e}")
    
    print("\n🎉 Debug test complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
