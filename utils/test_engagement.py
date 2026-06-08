#!/usr/bin/env python3
"""
Test engagement functionality specifically
"""
import sys
from alleybot_core import AlleyBotCore

def test_engagement():
    """Test engagement plugin functionality"""
    print("🤝 Testing Engagement Plugin...")
    
    try:
        core = AlleyBotCore()
        
        # Get engagement plugin
        engagement_plugin = core.plugin_manager.plugins['engagement']
        print(f"✅ Engagement plugin loaded: {type(engagement_plugin).__name__}")
        
        # Test comment supporter
        if hasattr(engagement_plugin, 'comment_supporter'):
            supporter = engagement_plugin.comment_supporter
            print(f"✅ Comment supporter: {type(supporter).__name__}")
            
            # Test stats
            stats = supporter.get_stats()
            print(f"📊 Comment supporter stats: {stats}")
        
        # Test own post upvoter
        if hasattr(engagement_plugin, 'own_post_upvoter'):
            upvoter = engagement_plugin.own_post_upvoter
            print(f"✅ Own post upvoter: {type(upvoter).__name__}")
            
            # Test stats
            stats = upvoter.get_stats()
            print(f"📊 Own post upvoter stats: {stats}")
        
        # Test manual support
        print("\n🚀 Testing manual comment support...")
        try:
            engagement_plugin.support_comments_now()
            print("✅ Manual support completed")
        except Exception as e:
            print(f"⚠️  Manual support error: {e}")
        
        # Test manual own post support
        print("\n🎯 Testing manual own post support...")
        try:
            engagement_plugin.support_own_posts_now()
            print("✅ Manual own post support completed")
        except Exception as e:
            print(f"⚠️  Manual own post support error: {e}")
        
        core.cleanup()
        
    except Exception as e:
        print(f"❌ Engagement test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_engagement()
