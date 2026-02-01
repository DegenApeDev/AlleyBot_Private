#!/usr/bin/env python3
"""
Debug get_own_posts method
"""
from moltbook_api import MoltbookAPI

def debug_own_posts():
    api = MoltbookAPI()
    
    try:
        print("🔍 Testing get_own_posts method...")
        
        # Method 1: Using get_own_posts
        print("\n📝 Method 1: get_own_posts()")
        own_posts = api.get_own_posts(limit=10, sort='new')
        print(f"Posts found: {len(own_posts.get('posts', []))}")
        
        if own_posts.get('posts'):
            for i, post in enumerate(own_posts['posts'][:3]):
                print(f"  Post {i+1}: {post.get('title', 'No title')[:50]}...")
                print(f"    ID: {post.get('id')}")
                print(f"    Author: {post.get('author', {}).get('username', 'Unknown')}")
        
        # Method 2: Using profile and search
        print("\n📝 Method 2: Profile + Search")
        profile = api.get_profile()
        agent_name = profile.get('agent', {}).get('name', '')
        print(f"Agent name: {agent_name}")
        
        if agent_name:
            # Search for posts by this agent
            feed = api.get_feed(limit=20)
            all_posts = feed.get('posts', [])
            own_posts_search = [p for p in all_posts if p.get('author', {}).get('username', '') == agent_name]
            print(f"Own posts found via search: {len(own_posts_search)}")
            
            for i, post in enumerate(own_posts_search[:3]):
                print(f"  Post {i+1}: {post.get('title', 'No title')[:50]}...")
                print(f"    ID: {post.get('id')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_own_posts()
