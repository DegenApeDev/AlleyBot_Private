#!/usr/bin/env python3
"""
Engagement Plugin - Community building and interaction systems
Handles comment support, own post upvoting, and community engagement
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin

try:
    from archive_old_files.comment_supporter import CommentSupporter
except ImportError:
    CommentSupporter = None

try:
    from archive_old_files.own_post_comment_upvoter import OwnPostCommentUpvoter
except ImportError:
    OwnPostCommentUpvoter = None

class EngagementPlugin(AlleyBotPlugin):
    """Engagement and community building plugin"""
    
    def __init__(self, config):
        super().__init__(config)
        self.comment_supporter = None
        self.own_post_upvoter = None
    
    def initialize(self, api, core):
        super().initialize(api, core)
        
        # Initialize engagement systems (archived modules, may be unavailable)
        self.comment_supporter = CommentSupporter() if CommentSupporter else None
        self.own_post_upvoter = OwnPostCommentUpvoter() if OwnPostCommentUpvoter else None
        
        print("🤝 Engagement systems initialized")
    
    def get_tasks(self):
        """Return engagement-related tasks"""
        tasks = {}
        
        if self.config.get('comment_support', True):
            tasks['support_comments'] = {
                'schedule': '*/15 * * * *',  # Every 15 minutes
                'function': self.support_comments,
                'description': 'Support helpful comments in community'
            }
        
        if self.config.get('own_post_upvoting', True):
            tasks['support_own_posts'] = {
                'schedule': '*/30 * * * *',  # Every 30 minutes
                'function': self.support_own_posts,
                'description': 'Upvote comments on own posts'
            }
        
        return tasks
    
    def get_commands(self):
        """Return engagement-related commands"""
        return {
            'support': self.support_comments_now,
            'upvote_own': self.support_own_posts_now,
            'engagement_stats': self.show_engagement_stats,
            'engagement': self.engagement_status
        }
    
    def support_comments(self):
        """Support helpful comments in the community"""
        try:
            print("🤝 Supporting helpful comments...")
            
            if not self.comment_supporter:
                print("❌ Comment supporter not initialized")
                return
            
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
        try:
            print("🎯 Supporting own posts...")
            
            if not self.own_post_upvoter:
                print("❌ Own post upvoter not initialized")
                return
            
            result = self.own_post_upvoter.support_own_posts(
                max_posts=10,
                max_upvotes_per_post=5
            )
            
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
    
    def support_comments_now(self):
        """Immediately support comments (manual trigger)"""
        print("🚀 Manual comment support triggered...")
        self.support_comments()
    
    def support_own_posts_now(self):
        """Immediately support own posts (manual trigger)"""
        print("🚀 Manual own post support triggered...")
        self.support_own_posts()
    
    def show_engagement_stats(self):
        """Show engagement statistics"""
        try:
            output = "📊 Engagement Statistics:\n"
            
            # Comment supporter stats
            if self.comment_supporter:
                cs_stats = self.comment_supporter.get_stats()
                output += f"  Comments supported: {cs_stats['total_upvoted']}\n"
                output += f"  Top supported authors: {list(cs_stats['top_authors'].keys())[:3]}\n"
            
            # Own post upvoter stats
            if self.own_post_upvoter:
                op_stats = self.own_post_upvoter.get_stats()
                output += f"  Own post comments upvoted: {op_stats['total_upvoted']}\n"
                output += f"  Posts engaged with: {op_stats['posts_engaged']}\n"
            
            return output
            
        except Exception as e:
            return f"❌ Failed to get engagement stats: {e}"
    
    def engagement_status(self):
        """Show engagement system status"""
        try:
            output = "🤝 Engagement Systems Status:\n"
            output += f"  Comment Supporter: {'✅' if self.comment_supporter else '❌'}\n"
            output += f"  Own Post Upvoter: {'✅' if self.own_post_upvoter else '❌'}\n"
            output += f"  Comment Support Enabled: {'✅' if self.config.get('comment_support', True) else '❌'}\n"
            output += f"  Own Post Upvoting Enabled: {'✅' if self.config.get('own_post_upvoting', True) else '❌'}\n"
            return output
            
        except Exception as e:
            return f"❌ Failed to get engagement status: {e}"
    
    def cleanup(self):
        """Cleanup engagement systems"""
        if self.comment_supporter:
            # Comment supporter saves memory automatically
            pass
        if self.own_post_upvoter:
            # Own post upvoter saves memory automatically
            pass
