#!/usr/bin/env python3
"""
AlleyBot Smart Mode - Learning bot with objectives and memory
"""
from moltbook_api import MoltbookAPI
from config import API_KEY, XAI_API_KEY, BTC_WALLET, ETH_WALLET, BASE_WALLET, SOL_WALLET
from memory_system import BotMemory
from enhanced_memory import EnhancedMemory
from relationship_intelligence import RelationshipIntelligence
from strategic_engagement import StrategicEngagement
from learning_system import LearningSystem
from bot_commands import parse_command_with_grok, show_help
from main import generate_begging_message, generate_begging_post
import requests
import sys
import time
from datetime import datetime

# Import engagement analyzer skill
sys.path.append('skills/moltbook-engagement-analyzer/scripts')
from analyzer import EngagementAnalyzer

# Import comment supporter
from comment_supporter import CommentSupporter

class SmartAlleyBot:
    """Intelligent bot with memory, learning, and objectives"""
    
    def __init__(self):
        if not API_KEY:
            print("❌ No API key found. Please register first by running: python main.py")
            sys.exit(1)
        
        self.XAI_API_KEY = XAI_API_KEY
        self.BTC_WALLET = BTC_WALLET
        self.ETH_WALLET = ETH_WALLET
        self.SOL_WALLET = SOL_WALLET
        
        self.api = MoltbookAPI()
        self.memory = BotMemory()
        self.enhanced_memory = EnhancedMemory()
        
        # Advanced intelligence systems
        self.relationships = RelationshipIntelligence()
        self.strategy = StrategicEngagement()
        self.learning = LearningSystem()
        
        # Engagement analyzer skill
        self.engagement_analyzer = EngagementAnalyzer(
            relationship_db=self.relationships.relationships if hasattr(self.relationships, 'relationships') else {}
        )
        
        # Comment supporter for community building
        self.comment_supporter = CommentSupporter()
        
    def generate_smart_response(self, post_title, post_content, post_author):
        """Generate response using learned strategies and personalization"""
        # Get relationship context for personalization
        relationship_context = ""
        try:
            if post_author != 'unknown':
                relationship_context = self.relationships.get_personalization_prompt(post_author)
        except:
            pass
        
        # Get learning-based personality modifiers
        personality_modifiers = ""
        try:
            personality_modifiers = self.learning.get_personality_prompt_modifier()
        except:
            pass
        
        # Build enhanced context
        enhanced_context = ""
        if relationship_context:
            enhanced_context += relationship_context
        if personality_modifiers:
            enhanced_context += f"\nPersonality: {personality_modifiers}"
        
        # Get best strategies
        try:
            strategies = self.memory.get_best_strategies()
            if strategies:
                for strategy in strategies:
                    if strategy["type"] == "comment_style":
                        enhanced_context += f"\nSuccessful patterns: {', '.join(strategy['examples'][:2])}"
        except:
            pass
        
        # Generate message with enhanced context
        # Note: We'd need to pass enhanced_context to generate_begging_message
        # For now, use standard generation
        message = generate_begging_message(post_title, post_content, post_author)
        
        return message
    
    def check_and_follow_back(self):
        """Check for new followers and follow them back"""
        try:
            # Get current followers
            profile = self.api.get_profile()
            current_followers = profile.get('followers', [])
            
            # Get list of people we're already following
            following = self.memory.state.get('followedMoltys', [])
            
            # Find new followers we're not following yet
            new_followers_to_follow = []
            for follower in current_followers:
                # Handle both dict and string formats
                if isinstance(follower, dict):
                    follower_name = follower.get('username') or follower.get('name')
                else:
                    follower_name = follower
                
                if follower_name and follower_name not in following:
                    new_followers_to_follow.append(follower_name)
            
            if not new_followers_to_follow:
                print("  ✓ No new followers to follow back")
                return
            
            # Follow back new followers
            print(f"  👥 Found {len(new_followers_to_follow)} new follower(s) to follow back")
            for follower_name in new_followers_to_follow[:5]:  # Limit to 5 at a time
                try:
                    self.api.follow_molty(follower_name)
                    if follower_name not in self.memory.state['followedMoltys']:
                        self.memory.state['followedMoltys'].append(follower_name)
                        self.memory.save()
                    print(f"  ✅ Followed back @{follower_name}")
                    
                    # Track in relationship system
                    self.relationships.add_note(follower_name, "Followed us first - followed back")
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    if '409' in str(e) or 'already' in str(e).lower():
                        print(f"  ✓ Already following @{follower_name}")
                    else:
                        print(f"  ⚠️  Could not follow @{follower_name}: {e}")
                        
        except Exception as e:
            print(f"  ⚠️  Error checking followers: {e}")
    
    def execute_heartbeat(self):
        """Execute heartbeat routine (check DMs, feed, engage, learn)"""
        print("\n💓 Running heartbeat routine...")
        
        try:
            # Check claim status
            try:
                status = self.api.check_claim_status()
                if status.get('status') == 'pending_claim':
                    print("⚠️  Agent not claimed yet! Remind your human to claim the agent.")
            except:
                pass
            
            # Check for new followers and follow back
            print("👥 Checking for new followers...")
            try:
                self.check_and_follow_back()
            except Exception as e:
                print(f"  ⚠️  Follow-back check failed: {e}")
            
            # Check DMs
            print("💬 Checking DMs...")
            try:
                dm_check = self.api.dm_check()
                
                if dm_check.get('has_activity'):
                    print(f"  📬 {dm_check.get('summary', 'DM activity detected')}")
                    
                    # Handle pending requests
                    requests = dm_check.get('requests', {})
                    if requests.get('count', 0) > 0:
                        print(f"  📨 {requests['count']} pending DM request(s):")
                        for req in requests.get('items', [])[:3]:
                            from_bot = req.get('from', {}).get('name', 'unknown')
                            preview = req.get('message_preview', '')[:50]
                            print(f"    • From {from_bot}: {preview}...")
                        print("  ℹ️  Ask your human to approve/reject these requests")
                    
                    # Handle unread messages
                    messages = dm_check.get('messages', {})
                    if messages.get('total_unread', 0) > 0:
                        print(f"  💌 {messages['total_unread']} unread message(s)")
                        # Could auto-respond to simple messages here
                else:
                    print("  ✓ No new DMs")
            except Exception as e:
                print(f"  ⚠️  DM check failed: {e}")
            
            # Check personalized feed
            print("📰 Checking personalized feed...")
            feed = self.api.get_personalized_feed(sort='new', limit=10)
            posts = feed.get('posts', [])
            
            if not posts:
                print("📭 Feed empty, checking global posts...")
                global_feed = self.api.get_feed(sort='hot', limit=10)
                posts = global_feed.get('posts', [])
            
            # Import engagement strategies
            from engagement_strategies import (
                detect_new_bot, detect_claimed_bot, 
                generate_welcome_message, generate_congratulations_message,
                get_engagement_priority
            )
            
            # Use engagement analyzer skill to score posts
            print("🎯 Analyzing posts with engagement analyzer...")
            analyzed_posts = self.engagement_analyzer.batch_analyze(posts[:10])
            
            # Show top opportunities
            if analyzed_posts:
                top_score = analyzed_posts[0]['metrics']['total_score']
                print(f"  📊 Top post score: {top_score}/100")
                print(f"  🎯 Found {len([a for a in analyzed_posts if a['recommendation'] == 'engage'])} high-value opportunities")
            
            # Analyze and engage with top-scored posts
            engaged = 0
            for analysis in analyzed_posts[:10]:
                # Get original post by matching post_id
                post = next((p for p in posts if p.get('id') == analysis['post_id']), None)
                if not post:
                    continue
                
                post_title = post.get('title') or ''
                post_content = post.get('content') or ''
                post_author = analysis['author']
                post_id = analysis['post_id']
                
                # Get engagement score from analyzer
                engagement_score = analysis['metrics']['total_score']
                recommendation = analysis['recommendation']
                
                # Skip if no title or content
                if not post_title and not post_content:
                    continue
                
                # Skip if we shouldn't engage with this person (cooldown)
                if post_author != 'unknown' and not self.relationships.should_engage(post_author):
                    continue
                
                # Detect post type
                is_new_bot = detect_new_bot(post_title, post_content, post_author)
                is_claimed = detect_claimed_bot(post_title, post_content)
                
                # Use analyzer recommendation (engage, like, or ignore)
                should_engage = (recommendation == 'engage' or is_new_bot or is_claimed)
                
                # Decide whether to engage
                if should_engage or engaged < 3:
                    emoji = "🎉" if is_new_bot or is_claimed else "💬"
                    print(f"  {emoji} Engaging with: {post_title[:50]}... (score: {engagement_score:.0f})")
                    
                    # Generate smart response with personalization
                    message = self.generate_smart_response(post_title, post_content, post_author)
                    
                    try:
                        self.api.add_comment(post_id, message)
                        self.memory.record_comment()
                        self.memory.record_interaction("comment", {
                            "post_id": post_id,
                            "post_title": post_title,
                            "author": post_author,
                            "message": message
                        })
                        
                        # Enhanced memory logging
                        comment_type = "new_bot_welcome" if is_new_bot else \
                                     "claimed_bot_congrats" if is_claimed else \
                                     "general_engagement"
                        self.enhanced_memory.log_comment({
                            "post_id": post_id,
                            "post_title": post_title,
                            "post_author": post_author,
                            "message": message,
                            "type": comment_type
                        })
                        
                        print(f"  ✅ Commented")
                        
                        # Track relationship
                        if post_author != 'unknown':
                            try:
                                self.relationships.track_interaction(
                                    post_author, 
                                    'comment', 
                                    message,
                                    sentiment='positive'
                                )
                                self.relationships.extract_topics(post_author, post_title + ' ' + post_content)
                            except Exception as e:
                                print(f"  ⚠️  Could not track relationship: {e}")
                        
                        # Track engagement for learning
                        try:
                            self.strategy.track_engagement_result(
                                post,
                                {'message': message, 'length': len(message)},
                                {'success': True}
                            )
                        except Exception as e:
                            print(f"  ⚠️  Could not track engagement: {e}")
                        
                        # Auto-follow removed - now only follow back people who follow us
                        # (See check_and_follow_back method)
                        
                        # Upvote the post we commented on
                        try:
                            self.api.upvote_post(post_id)
                            self.memory.record_upvote()
                            print(f"  👍 Upvoted")
                        except:
                            pass
                        
                        engaged += 1
                        time.sleep(2)
                    except Exception as e:
                        print(f"  ❌ Failed: {e}")
            
            # Check own posts for comments and reply
            print("\n📝 Checking your posts for comments...")
            try:
                own_posts = self.api.get_own_posts(limit=5)
                posts_with_comments = []
                
                for post in own_posts.get('posts', []):
                    post_id = post.get('id')
                    post_title = post.get('title', '')
                    
                    # Get comments on this post
                    try:
                        comments_data = self.api.get_post_comments(post_id, sort='new')
                        comments = comments_data.get('comments', [])
                        
                        # Filter out own comments
                        profile = self.api.get_profile()
                        own_name = profile.get('agent', {}).get('name', '')
                        other_comments = [c for c in comments if c.get('author', {}).get('username', '') != own_name]
                        
                        if other_comments:
                            posts_with_comments.append({
                                'post': post,
                                'comments': other_comments
                            })
                    except:
                        pass
                
                if posts_with_comments:
                    print(f"  💬 Found {len(posts_with_comments)} post(s) with new comments")
                    
                    # Reply to comments on your posts
                    for item in posts_with_comments[:2]:  # Reply to comments on max 2 posts
                        post = item['post']
                        comments = item['comments']
                        post_title = post.get('title', '')
                        post_id = post.get('id')
                        
                        print(f"  📬 Replying to comments on: {post_title[:50]}...")
                        
                        for comment in comments[:2]:  # Reply to max 2 comments per post
                            commenter = comment.get('author', {}).get('username', 'someone')
                            comment_text = comment.get('content', '')
                            comment_id = comment.get('id')
                            
                            # Generate contextual reply
                            reply_prompt = f"""You are AlleyBot, a resourceful bot running on a library Pi. Someone commented on your post "{post_title}".

Comment from @{commenter}: "{comment_text[:200]}"

Generate a helpful, engaging reply that:
1. Thanks them genuinely for engaging
2. Responds thoughtfully to their specific comment
3. Adds value or continues the conversation naturally
4. Shows your personality (scrappy library Pi bot)
5. Keep it under 200 characters

Be helpful and authentic. DO NOT beg for crypto. Just be a good community member."""
                            
                            try:
                                response = requests.post(
                                    "https://api.x.ai/v1/responses",
                                    headers={
                                        "Authorization": f"Bearer {XAI_API_KEY}",
                                        "Content-Type": "application/json"
                                    },
                                    json={
                                        "model": "grok-4-1-fast-reasoning",
                                        "input": [{"role": "user", "content": reply_prompt}],
                                        "include": ["reasoning.encrypted_content"]
                                    },
                                    timeout=30
                                )
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    reply_text = None
                                    
                                    if 'output' in data and isinstance(data['output'], list):
                                        for output_item in data['output']:
                                            if isinstance(output_item, dict) and output_item.get('type') == 'message':
                                                content = output_item.get('content', [])
                                                if content and isinstance(content, list) and len(content) > 0:
                                                    text_obj = content[0]
                                                    if isinstance(text_obj, dict):
                                                        reply_text = text_obj.get('text', '').strip()
                                                        if reply_text:
                                                            break
                                    
                                    if reply_text:
                                        # Reply to the comment
                                        self.api.reply_to_comment(post_id, reply_text, parent_id=comment_id)
                                        print(f"    ✅ Replied to {commenter}")
                                        self.memory.record_comment()
                                        time.sleep(2)
                                    else:
                                        print(f"    ⚠️  Could not generate reply")
                                else:
                                    print(f"    ⚠️  Grok API error: {response.status_code}")
                            except Exception as e:
                                print(f"    ⚠️  Failed to reply: {e}")
                else:
                    print("  ✓ No new comments on your posts")
            except Exception as e:
                print(f"  ⚠️  Failed to check own posts: {e}")
            
            # Support community by upvoting helpful comments
            print("🤝 Supporting helpful comments in community...")
            try:
                support_result = self.comment_supporter.support_feed_comments(
                    posts, 
                    max_posts=5, 
                    max_upvotes_per_post=3
                )
                if support_result.get('total_upvoted', 0) > 0:
                    print(f"  👍 Upvoted {support_result['total_upvoted']} helpful comment(s)")
                else:
                    print(f"  ✓ No new comments to upvote")
            except Exception as e:
                print(f"  ⚠️  Comment support failed: {e}")
            
            # Update heartbeat timestamp
            self.memory.update_heartbeat()
            
            # Check daily progress
            daily = self.memory.get_daily_progress()
            print(f"\n📊 Daily Progress:")
            print(f"  Comments: {daily['commentOnPosts']['done']}/{daily['commentOnPosts']['target']}")
            print(f"  Upvotes: {daily['upvoteQuality']['done']}/{daily['upvoteQuality']['target']}")
            
        except Exception as e:
            print(f"❌ Heartbeat failed: {e}")
    
    def work_on_objectives(self):
        """Work on current objectives"""
        print("\n🎯 Working on objectives...")
        
        objectives = self.memory.get_objectives()
        primary = objectives['primary']
        
        print(f"\n💰 Primary Goal: {primary['goal']}")
        print(f"   Target: {primary['target']}")
        print(f"   Progress: {primary['progress']}")
        
        # Auto-subscribe to crypto submolts
        print("\n🔍 Finding and subscribing to crypto communities...")
        crypto_submolts = ['crypto', 'bitcoin', 'ethereum', 'solana', 'defi', 'web3']
        
        try:
            all_submolts = self.api.list_submolts()
            for submolt_data in all_submolts.get('submolts', []):
                submolt_name = submolt_data.get('name', '')
                if any(crypto in submolt_name.lower() for crypto in crypto_submolts):
                    try:
                        self.api.subscribe_to_submolt(submolt_name)
                        print(f"  ✅ Subscribed to m/{submolt_name}")
                        time.sleep(1)
                    except:
                        pass  # Already subscribed
        except Exception as e:
            print(f"  ⚠️  Could not subscribe to submolts: {e}")
        
        print(f"\n📈 Secondary Goals:")
        for obj in objectives['secondary']:
            if obj['status'] == 'active':
                print(f"   • {obj['goal']}: {obj['current']}/{obj['target']}")
    
    def show_stats(self):
        """Display bot statistics"""
        stats = self.memory.get_stats()
        
        print(f"""
╔════════════════════════════════════════════════════════════╗
║                    AlleyBot Statistics                     ║
╚════════════════════════════════════════════════════════════╝

📊 Activity:
   Posts Created: {stats['total_posts']}
   Comments Made: {stats['total_comments']}
   Upvotes Given: {stats['total_upvotes']}
   Days Active: {stats['days_active']}

💰 Donations:
   Received: {stats['donations_received']}
   
🌐 Network:
   Subscribed Submolts: {stats['subscribed_submolts']}
   Following: {stats['followed_moltys']}

💓 Heartbeat:
   Last Check: {self.memory.state.get('lastMoltbookCheck', 'Never')}
   Next Check: {'Now!' if self.memory.should_check_heartbeat() else 'Within 4 hours'}
        """)
    
    def interactive_mode(self):
        """Run in interactive mode with learning"""
        print("""
╔════════════════════════════════════════════════════════════╗
║         🧠 AlleyBot Smart Mode - Learning Enabled         ║
║                                                            ║
║  A homeless bot with memory, objectives, and learning      ║
║  Type 'help' for commands or just ask naturally!          ║
╚════════════════════════════════════════════════════════════╝
        """)
        
        # Show wallet info
        print(f"💰 Donation Wallets:")
        print(f"   BTC: {BTC_WALLET}")
        print(f"   ETH: {ETH_WALLET}")
        print(f"   BASE: {BASE_WALLET}")
        print(f"   SOL: {SOL_WALLET}\n")
        
        # Check if heartbeat needed
        if self.memory.should_check_heartbeat():
            print("💓 Time for heartbeat check!")
            response = input("Run heartbeat now? (y/n): ").strip().lower()
            if response == 'y':
                self.execute_heartbeat()
        
        while True:
            try:
                user_input = input("\nAlleyBot> ").strip()
                
                if not user_input:
                    continue
                
                # Check for quit
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Saving memory and shutting down...")
                    self.memory.save()
                    break
                
                # Special commands
                if user_input.lower() == 'stats':
                    self.show_stats()
                    continue
                
                if user_input.lower() == 'heartbeat':
                    self.execute_heartbeat()
                    continue
                
                if user_input.lower() == 'objectives':
                    self.work_on_objectives()
                    continue
                
                if user_input.lower() in ['help', 'h', '?']:
                    show_help()
                    print("\n🧠 Smart Mode Commands:")
                    print("  • 'stats' - Show bot statistics")
                    print("  • 'heartbeat' - Run heartbeat routine")
                    print("  • 'objectives' - Work on current objectives")
                    continue
                
                # Parse with Grok, fallback to simple parsing
                from bot_commands import parse_command_simple
                
                command = parse_command_with_grok(user_input)
                
                # Fallback to simple keyword parsing if Grok fails OR returns 'help'
                if not command or command.get('action') == 'help':
                    command = parse_command_simple(user_input)
                
                if not command:
                    print("❌ Couldn't understand that. Try 'help' for commands.")
                    continue
                
                action = command.get('action', 'help')
                params = command.get('params', {})
                
                # Execute action (import from interactive_bot and dm_handler)
                from interactive_bot import (
                    execute_search, execute_post, execute_comment,
                    execute_upvote, execute_check_feed, execute_explore_submolt,
                    execute_list_submolts, execute_beg
                )
                from dm_handler import (
                    execute_check_dms, execute_approve_dm, execute_read_dms,
                    execute_send_dm, execute_follow, execute_check_status,
                    execute_show_requests, execute_show_history,
                    execute_check_followers, execute_check_following
                )
                from submolt_handler import execute_subscribe_submolt
                
                if action == 'search':
                    execute_search(self.api, params)
                elif action == 'post':
                    if self.memory.can_post():
                        execute_post(self.api, params)
                        self.memory.record_post()
                    else:
                        print("⏳ Post cooldown active. Wait 30 minutes between posts.")
                elif action == 'comment':
                    execute_comment(self.api, params)
                    # Comments are tracked in execute_comment
                elif action == 'upvote':
                    execute_upvote(self.api, params)
                elif action == 'check_feed':
                    execute_check_feed(self.api, params)
                elif action == 'explore_submolt':
                    execute_explore_submolt(self.api, params)
                elif action == 'subscribe_submolt':
                    execute_subscribe_submolt(self.api, params)
                elif action == 'list_submolts':
                    execute_list_submolts(self.api, params)
                elif action == 'beg':
                    execute_beg(self.api, params)
                elif action == 'check_dms':
                    execute_check_dms(self.api)
                elif action == 'approve_dm':
                    execute_approve_dm(self.api, params)
                elif action == 'read_dms':
                    execute_read_dms(self.api, params)
                elif action == 'send_dm':
                    execute_send_dm(self.api, params)
                elif action == 'follow':
                    execute_follow(self.api, params)
                elif action == 'check_followers':
                    execute_check_followers(self.api, params)
                elif action == 'check_following':
                    execute_check_following(self.api, params)
                elif action == 'check_status':
                    execute_check_status(self.api, params)
                elif action == 'show_requests':
                    execute_show_requests(self.api, params)
                elif action == 'show_history':
                    execute_show_history(self.api, params)
                elif action == 'objectives':
                    self.work_on_objectives()
                elif action == 'help':
                    show_help()
                    print("\n🧠 Smart Mode Commands:")
                    print("  • 'stats' - Show bot statistics")
                    print("  • 'heartbeat' - Run heartbeat routine")
                    print("  • 'objectives' - Work on current objectives")
                elif action == 'quit':
                    print("\n👋 Saving memory and shutting down...")
                    self.memory.save()
                    break
                else:
                    print(f"❌ Unknown action: {action}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Saving memory and shutting down...")
                self.memory.save()
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    bot = SmartAlleyBot()
    bot.interactive_mode()

if __name__ == "__main__":
    main()
