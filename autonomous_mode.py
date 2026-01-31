#!/usr/bin/env python3
"""
AlleyBot Autonomous Mode
Runs fully automated with timed heartbeats and intelligent posting
"""
import time
import schedule
from datetime import datetime
from smart_bot import SmartAlleyBot
from main import generate_begging_post
from moltbook_api import MoltbookAPI
from comment_supporter import CommentSupporter
from own_post_comment_upvoter import OwnPostCommentUpvoter
from config import API_KEY
import sys

class AutonomousAlleyBot:
    """Fully autonomous AlleyBot with scheduled operations"""
    
    def __init__(self):
        self.bot = SmartAlleyBot()
        self.api = MoltbookAPI()
        self.comment_supporter = CommentSupporter()
        self.own_post_upvoter = OwnPostCommentUpvoter()
        self.last_post_time = None
        self.trending_topics = []
        
        print("\n" + "="*60)
        print("🤖 ALLEYBOT AUTONOMOUS MODE")
        print("="*60)
        print("⏰ Heartbeat: Every 15 minutes (starts immediately)")
        print("🤝 Comment Support: Every 15 minutes (starts after 5 min)")
        print("🎯 Own Post Upvoter: Every 30 minutes")
        print("📝 Posts: Every 2 hours (based on trending topics)")
        print("🔄 Running continuously until stopped (Ctrl+C)")
        print("="*60 + "\n")
    
    def run_heartbeat(self):
        """Run heartbeat and collect trending topics"""
        print(f"\n{'='*60}")
        print(f"💓 HEARTBEAT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            # Run the heartbeat
            self.bot.execute_heartbeat()
            
            # Analyze what we saw for post ideas
            self._analyze_feed_for_topics()
            
            print(f"\n✅ Heartbeat complete")
            
        except Exception as e:
            print(f"❌ Heartbeat error: {e}")
    
    def _analyze_feed_for_topics(self):
        """Analyze recent feed to identify trending topics"""
        try:
            # Get recent posts from feed
            feed = self.api.get_feed(limit=20)
            
            if not feed:
                return
            
            # Handle both dict and list responses
            if isinstance(feed, dict):
                posts = feed.get('posts', [])
            else:
                posts = feed
            
            if not posts:
                return
            
            # Extract topics from titles and content
            topics = []
            keywords = {}
            
            for post in posts:
                title = post.get('title') or ''
                content = post.get('content') or ''
                text = f"{title} {content}".lower()
                
                # Look for interesting keywords
                interesting_words = [
                    'ai', 'agent', 'crypto', 'token', 'base', 'moltbook',
                    'bot', 'automation', 'defi', 'nft', 'web3', 'blockchain',
                    'grok', 'claude', 'gpt', 'llm', 'model', 'training',
                    'donation', 'community', 'building', 'launch', 'deploy'
                ]
                
                for word in interesting_words:
                    if word in text:
                        keywords[word] = keywords.get(word, 0) + 1
            
            # Get top 3 trending keywords
            if keywords:
                sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
                self.trending_topics = [k for k, v in sorted_keywords[:3]]
                print(f"\n📊 Trending topics: {', '.join(self.trending_topics)}")
            
        except Exception as e:
            print(f"⚠️  Error analyzing feed: {e}")
    
    def create_intelligent_post(self):
        """Create a post based on trending topics or general value"""
        print(f"\n{'='*60}")
        print(f"📝 AUTO-POST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            # Choose topic based on what's trending
            if self.trending_topics:
                topic = self.trending_topics[0]
                print(f"📊 Topic: {topic} (trending)")
            else:
                # Fallback topics
                topics = [
                    "AI agents on Moltbook",
                    "Building on BASE chain",
                    "Bot survival strategies",
                    "Crypto community building",
                    "Autonomous agent tips"
                ]
                import random
                topic = random.choice(topics)
                print(f"📊 Topic: {topic} (general)")
            
            # Generate post
            title, content = generate_begging_post(topic)
            
            # Post to Moltbook
            result = self.api.create_post(
                title=title,
                content=content,
                submolt="general"
            )
            
            if result:
                print(f"✅ Posted: {title[:50]}...")
                self.last_post_time = datetime.now()
            else:
                print("❌ Failed to create post")
                
        except Exception as e:
            print(f"❌ Post creation error: {e}")
    
    def support_comments(self):
        """Support community by upvoting helpful comments"""
        print(f"\n{'='*60}")
        print(f"🤝 COMMENT SUPPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            # Get recent posts from feed
            feed = self.api.get_feed(limit=10)
            
            if isinstance(feed, dict):
                posts = feed.get('posts', [])
            else:
                posts = feed
            
            if not posts:
                print("📭 No posts in feed")
                return
            
            # Support comments on these posts
            result = self.comment_supporter.support_feed_comments(
                posts,
                max_posts=5,
                max_upvotes_per_post=3
            )
            
            if result.get('total_upvoted', 0) > 0:
                print(f"✅ Upvoted {result['total_upvoted']} helpful comment(s)")
            else:
                print("✓ No new comments to upvote")
            
            # Show stats
            stats = self.comment_supporter.get_stats()
            print(f"📊 Total comments supported: {stats['total_upvoted']}")
            
        except Exception as e:
            print(f"❌ Comment support error: {e}")
    
    def support_own_posts(self):
        """Support AlleyBot's own posts by upvoting comments"""
        print(f"\n{'='*60}")
        print(f"🎯 OWN POST UPVOTER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            result = self.own_post_upvoter.support_own_posts(max_posts=10, max_upvotes_per_post=5)
            
            if 'error' not in result:
                if result.get('posts_checked', 0) > 0:
                    print(f"✅ Checked {result['posts_checked']} own post(s)")
                    print(f"👍 Upvoted {result['total_upvoted']} comment(s)")
                    print(f"⏭️  Skipped {result['total_skipped']} comment(s)")
                else:
                    if result.get('reason') == 'no_own_posts_yet':
                        print("📝 No posts yet - will check again after posting")
                    else:
                        print("📭 No own posts found")
                
                # Show stats
                stats = self.own_post_upvoter.get_stats()
                if stats['total_upvoted'] > 0:
                    print(f"📊 Total upvoted on own posts: {stats['total_upvoted']}")
            else:
                print(f"❌ Own post upvoter error: {result['error']}")
                
        except Exception as e:
            print(f"❌ Own post upvoter error: {e}")
    
    def run(self):
        """Run autonomous mode with scheduled tasks"""
        
        # Schedule heartbeat every 15 minutes (starts immediately)
        schedule.every(15).minutes.do(self.run_heartbeat)
        
        # Schedule comment support every 15 minutes (offset by 5 min)
        schedule.every(15).minutes.do(self.support_comments)
        
        # Schedule own post upvoter every 30 minutes
        schedule.every(30).minutes.do(self.support_own_posts)
        
        # Schedule posts every 2 hours
        schedule.every(2).hours.do(self.create_intelligent_post)
        
        # Run initial heartbeat immediately
        print("🚀 Running initial heartbeat...")
        self.run_heartbeat()
        
        # Run initial post
        print("\n🚀 Creating initial post...")
        self.create_intelligent_post()
        
        print(f"\n{'='*60}")
        print("✅ Autonomous mode active!")
        print("⏰ Next heartbeat: 15 minutes")
        print("🤝 First comment support: 5 minutes (then every 15 min)")
        print("📝 Next post: 2 hours")
        print("🛑 Press Ctrl+C to stop")
        print(f"{'='*60}\n")
        
        # Wait 5 minutes then run first comment support
        print("⏳ Waiting 5 minutes before first comment support...\n")
        time.sleep(300)  # 5 minutes = 300 seconds
        
        print("🚀 Running first comment support...")
        self.support_comments()
        
        # Main loop
        try:
            print(f"\n{'='*60}")
            print("🔄 Now running on schedule...")
            print(f"{'='*60}\n")
            
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\n\n" + "="*60)
            print("🛑 Stopping autonomous mode...")
            print("="*60)
            
            # Save state
            self.bot.memory.save()
            
            print("\n✅ AlleyBot stopped gracefully")
            print("💾 Memory saved")
            print("\n👋 See you next time!\n")
            sys.exit(0)

if __name__ == "__main__":
    bot = AutonomousAlleyBot()
    bot.run()
