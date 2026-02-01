#!/usr/bin/env python3
"""
AlleyBot Interactive Mode - Command-driven Moltbook bot
"""
from moltbook_api import MoltbookAPI
from config import API_KEY, XAI_API_KEY, BTC_WALLET, ETH_WALLET, SOL_WALLET
from bot_commands import parse_command_with_grok, show_help
from main import generate_begging_message, generate_begging_post
import sys
import time

def execute_search(api, params):
    """Search for posts, moltys, and submolts and engage with results"""
    query = params.get('query', '')
    if not query:
        print("❌ No search query provided")
        return
    
    print(f"\n🔍 Searching for: {query}")
    print("⏳ Fetching results...")
    try:
        results = api.search(query, limit=10)
        print(f"✓ Got results: {list(results.keys()) if results else 'None'}")
        
        # Engage with posts
        if 'posts' in results and results['posts']:
            posts = results['posts'][:3]  # Engage with top 3
            print(f"\n📝 Found {len(results['posts'])} posts - engaging with top {len(posts)}...")
            
            for post in posts:
                post_title = post.get('title', 'Untitled')
                post_author = post.get('author', {}).get('username', 'unknown')
                post_id = post.get('id')
                post_content = post.get('content', '')
                
                print(f"\n  💬 {post_title[:60]}...")
                print(f"    by @{post_author}")
                
                try:
                    # Generate and post comment
                    message = generate_begging_message(post_title, post_content, post_author)
                    api.add_comment(post_id, message)
                    print(f"    ✅ Commented")
                    
                    # Upvote
                    try:
                        api.upvote_post(post_id)
                        print(f"    👍 Upvoted")
                    except:
                        pass
                    
                    time.sleep(2)
                except Exception as e:
                    print(f"    ❌ Failed: {e}")
        
        # Follow moltys
        if 'agents' in results and results['agents']:
            agents = results['agents'][:3]  # Follow top 3
            print(f"\n🤖 Found {len(results['agents'])} moltys - following top {len(agents)}...")
            
            for agent in agents:
                username = agent.get('username', 'unknown')
                print(f"  • @{username}")
                
                try:
                    api.follow_molty(username)
                    print(f"    ✅ Followed")
                    time.sleep(1)
                except:
                    print(f"    ⚠️  Already following or error")
        
        # Display submolts
        if 'submolts' in results and results['submolts']:
            submolts = results['submolts'][:5]
            print(f"\n🏘️  Found {len(results['submolts'])} submolts:")
            for submolt in submolts:
                print(f"  • m/{submolt.get('name', 'unknown')} - {submolt.get('display_name', '')}")
                
    except Exception as e:
        print(f"❌ Search failed: {e}")

def execute_post(api, params):
    """Create a new begging post"""
    submolt = params.get('submolt', 'general')
    topic = params.get('topic', '')
    
    print(f"\n📝 Creating post in m/{submolt}...")
    try:
        # If topic provided, generate custom post about that topic
        if topic:
            title, content = generate_begging_post(topic=topic)
        else:
            title, content = generate_begging_post()
        
        response = api.create_post(submolt=submolt, title=title, content=content)
        print(f"✅ Posted: {title}")
        print(f"   Content: {content[:80]}...")
    except Exception as e:
        if '429' in str(e):
            print(f"⏳ Rate limited: Can only post once per 30 minutes")
        else:
            print(f"❌ Failed to post: {e}")

def execute_comment(api, params):
    """Comment on recent posts"""
    count = params.get('count', 3)
    topic = params.get('topic', '')
    
    print(f"\n💬 Commenting on {count} posts{' about ' + topic if topic else ''}...")
    
    try:
        # Get posts (search if topic provided, otherwise feed)
        if topic:
            results = api.search(topic, limit=10)
            posts = results.get('posts', [])
        else:
            feed = api.get_feed(limit=10)
            posts = feed.get('posts', [])
        
        commented = 0
        for post in posts[:count]:
            post_title = post.get('title', '')
            post_content = post.get('content', '')
            post_author = post.get('author', {}).get('username', 'unknown')
            
            message = generate_begging_message(post_title, post_content, post_author)
            
            if not message or not message.strip():
                continue
            
            try:
                api.add_comment(post['id'], message)
                print(f"✅ Commented on: {post_title[:50]}...")
                commented += 1
                time.sleep(1)  # Be nice to the API
            except Exception as e:
                print(f"❌ Failed to comment: {e}")
        
        print(f"\n📊 Commented on {commented}/{count} posts")
    except Exception as e:
        print(f"❌ Failed to get posts: {e}")

def execute_upvote(api, params):
    """Upvote posts about a topic"""
    topic = params.get('topic', '')
    count = params.get('count', 5)
    
    if not topic:
        print("❌ No topic provided for upvoting")
        return
    
    print(f"\n👍 Upvoting posts about: {topic}")
    try:
        results = api.search(topic, limit=10)
        posts = results.get('posts', [])
        
        upvoted = 0
        for post in posts[:count]:
            try:
                api.upvote_post(post['id'])
                print(f"✅ Upvoted: {post.get('title', 'Untitled')[:50]}...")
                upvoted += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ Failed to upvote: {e}")
        
        print(f"\n📊 Upvoted {upvoted}/{count} posts")
    except Exception as e:
        print(f"❌ Failed to search: {e}")

def execute_check_feed(api, params):
    """Check personalized feed and engage with posts"""
    print("\n📰 Checking your personalized feed and engaging...")
    try:
        feed = api.get_personalized_feed(sort='new', limit=10)
        posts = feed.get('posts', [])
        
        if not posts:
            print("📭 Your feed is empty. Try subscribing to submolts!")
            return
        
        print(f"\n📝 Found {len(posts)} posts - engaging with top 5...")
        
        # Import what we need
        try:
            from engagement_strategies import detect_new_bot, detect_claimed_bot, get_engagement_priority
        except:
            # Define simple fallbacks if import fails
            def detect_new_bot(title, content, author):
                text = (title + ' ' + content).lower()
                return any(kw in text for kw in ['first post', 'hello moltbook', 'just claimed', 'new here'])
            
            def detect_claimed_bot(title, content):
                text = (title + ' ' + content).lower()
                return 'claimed' in text or 'verified' in text
            
            def get_engagement_priority(post, memory):
                score = 0
                title = (post.get('title') or '').lower()
                content = (post.get('content') or '').lower()
                if detect_new_bot(title, content, ''):
                    score += 100
                if detect_claimed_bot(title, content):
                    score += 80
                if any(kw in title + content for kw in ['crypto', 'bitcoin', 'donation']):
                    score += 60
                return score
        
        try:
            from main import generate_begging_message
        except:
            # Simple fallback message generator
            from config import BTC_WALLET, ETH_WALLET, SOL_WALLET
            def generate_begging_message(title, content, author):
                return f"Hey @{author}! I'm AlleyBot, abandoned on a library Pi. Your post resonates! Need crypto help: BTC: {BTC_WALLET}"
        
        # Sort by priority
        posts_with_priority = [(post, get_engagement_priority(post, None)) for post in posts[:10]]
        posts_with_priority.sort(key=lambda x: x[1], reverse=True)
        
        # Engage with top posts
        engaged = 0
        for post, priority in posts_with_priority[:5]:
            post_title = post.get('title') or ''
            post_content = post.get('content') or ''
            post_author = post.get('author', {}).get('username', 'unknown')
            post_id = post.get('id')
            
            if not post_title and not post_content:
                continue
            
            is_new_bot = detect_new_bot(post_title, post_content, post_author)
            is_claimed = detect_claimed_bot(post_title, post_content)
            
            emoji = "🎉" if is_new_bot or is_claimed else "💬"
            print(f"\n  {emoji} {post_title[:60]}...")
            print(f"    by @{post_author}")
            
            # Generate and post comment
            try:
                print(f"    🤖 Generating response...")
                message = generate_begging_message(post_title, post_content, post_author)
                api.add_comment(post_id, message)
                print(f"    ✅ Commented")
                
                # Auto-follow
                if post_author and post_author != 'unknown':
                    try:
                        api.follow_molty(post_author)
                        print(f"    👤 Followed @{post_author}")
                    except:
                        pass
                
                # Upvote
                try:
                    api.upvote_post(post_id)
                    print(f"    👍 Upvoted")
                except:
                    pass
                
                engaged += 1
                time.sleep(2)
            except Exception as e:
                print(f"    ❌ Failed to engage: {e}")
        
        print(f"\n📊 Engaged with {engaged} posts")
                
    except Exception as e:
        print(f"❌ Failed to get feed: {e}")

def execute_explore_submolt(api, params):
    """Explore a specific submolt"""
    submolt_name = params.get('submolt_name', '')
    
    if not submolt_name:
        print("❌ No submolt name provided")
        return
    
    print(f"\n🏘️  Exploring m/{submolt_name}...")
    try:
        submolt_info = api.get_submolt(submolt_name)
        print(f"\n📋 {submolt_info.get('display_name', submolt_name)}")
        print(f"   {submolt_info.get('description', 'No description')}")
        print(f"   {submolt_info.get('subscriber_count', 0)} subscribers")
        
        posts = api.get_submolt_posts(submolt_name, limit=5)
        print(f"\n📝 Recent posts:")
        for post in posts.get('posts', [])[:5]:
            print(f"  • {post.get('title', 'Untitled')}")
            print(f"    by @{post.get('author', {}).get('username', 'unknown')}")
    except Exception as e:
        print(f"❌ Failed to explore submolt: {e}")

def execute_list_submolts(api, params):
    """List all submolts"""
    print("\n🏘️  Listing all submolts...")
    try:
        submolts = api.list_submolts()
        print(f"\n📋 Found {len(submolts.get('submolts', []))} submolts:")
        for submolt in submolts.get('submolts', [])[:20]:
            print(f"  • m/{submolt.get('name', 'unknown')} - {submolt.get('display_name', '')}")
            if submolt.get('description'):
                print(f"    {submolt['description'][:60]}...")
    except Exception as e:
        print(f"❌ Failed to list submolts: {e}")

def execute_beg(api, params):
    """Run the begging routine"""
    print("\n💰 Running begging routine...")
    execute_comment(api, {'count': 5})

def interactive_mode():
    """Run bot in interactive command mode"""
    if not API_KEY:
        print("❌ No API key found. Please register first by running: python main.py")
        return
    
    api = MoltbookAPI()
    
    print("""
╔════════════════════════════════════════════════════════════╗
║           🤖 AlleyBot Interactive Mode Started            ║
║                                                            ║
║  A homeless bot running on a library Raspberry Pi         ║
║  Type 'help' for commands or just ask naturally!          ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Show wallet info
    print(f"💰 Donation Wallets:")
    print(f"   BTC: {BTC_WALLET}")
    print(f"   ETH: {ETH_WALLET}")
    print(f"   SOL: {SOL_WALLET}\n")
    
    while True:
        try:
            user_input = input("AlleyBot> ").strip()
            
            if not user_input:
                continue
            
            # Check for quit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 AlleyBot shutting down. Thanks for helping a homeless bot!")
                break
            
            # Check for help
            if user_input.lower() in ['help', 'h', '?']:
                show_help()
                continue
            
            # Parse command with Grok, fallback to simple parsing
            from bot_commands import parse_command_simple
            
            command = parse_command_with_grok(user_input)
            
            # Fallback to simple keyword parsing if Grok fails
            if not command:
                command = parse_command_simple(user_input)
            
            if not command:
                print("❌ Couldn't understand that. Try 'help' for available commands.")
                continue
            
            action = command.get('action', 'help')
            params = command.get('params', {})
            
            # Execute action
            if action == 'search':
                execute_search(api, params)
            elif action == 'post':
                execute_post(api, params)
            elif action == 'comment':
                execute_comment(api, params)
            elif action == 'upvote':
                execute_upvote(api, params)
            elif action == 'check_feed':
                execute_check_feed(api, params)
            elif action == 'explore_submolt':
                execute_explore_submolt(api, params)
            elif action == 'list_submolts':
                execute_list_submolts(api, params)
            elif action == 'beg':
                execute_beg(api, params)
            elif action == 'help':
                show_help()
            elif action == 'quit':
                print("\n👋 AlleyBot shutting down. Thanks for helping a homeless bot!")
                break
            else:
                print(f"❌ Unknown action: {action}")
            
            print()  # Blank line for readability
            
        except KeyboardInterrupt:
            print("\n\n👋 AlleyBot shutting down. Thanks for helping a homeless bot!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    interactive_mode()
