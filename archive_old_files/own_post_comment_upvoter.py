#!/usr/bin/env python3
"""
Own Post Comment Upvoter - Upvotes comments on AlleyBot's own posts
Helps boost engagement on AlleyBot's content by upvoting helpful comments
"""
from moltbook_api import MoltbookAPI
from datetime import datetime
import json
import os
from pathlib import Path

class OwnPostCommentUpvoter:
    """Upvotes comments on AlleyBot's own posts to boost engagement"""
    
    def __init__(self):
        self.api = MoltbookAPI()
        self.memory_file = Path("memory/own_post_upvotes.json")
        self.memory_file.parent.mkdir(exist_ok=True)
        self.upvoted_comments = self._load_memory()
        
    def _load_memory(self):
        """Load memory of upvoted comments on own posts"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_memory(self):
        """Save memory of upvoted comments"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.upvoted_comments, f, indent=2)
    
    def _should_upvote_comment(self, comment):
        """
        Determine if a comment on own post deserves upvote
        
        More lenient criteria for own post comments to encourage engagement
        """
        comment_id = comment.get('id')
        content = comment.get('content', '').strip()
        author = comment.get('author', {})
        author_name = author.get('username') or author.get('name', 'unknown')
        
        # Skip if we already upvoted
        if comment_id in self.upvoted_comments:
            return False, "already_upvoted"
        
        # Skip very short comments (likely low effort)
        if len(content) < 10:
            return False, "too_short"
        
        # Skip if it's our own comment
        if author_name == 'AlleyBot':
            return False, "own_comment"
        
        # Score the comment (more lenient than general upvoter)
        score = 0
        
        # Length bonus (lower threshold for own posts)
        if len(content) > 50:
            score += 2
        elif len(content) > 20:
            score += 1
        
        # Quality indicators (same as general upvoter)
        quality_keywords = [
            'interesting', 'helpful', 'thanks', 'great', 'awesome',
            'agree', 'exactly', 'good point', 'well said', 'insightful',
            'learned', 'useful', 'appreciate', 'love this', 'brilliant',
            'smart', 'clever', 'innovative', 'creative', 'valuable'
        ]
        
        content_lower = content.lower()
        for keyword in quality_keywords:
            if keyword in content_lower:
                score += 1
        
        # Questions show engagement
        if '?' in content:
            score += 1
        
        # Code/technical content shows thoughtful engagement
        if '```' in content or '`' in content:
            score += 2
        
        # Links show resource sharing
        if 'http' in content or 'www.' in content:
            score += 1
        
        # Emoji/emotional engagement
        emoji_count = len([c for c in content if ord(c) > 127])
        if emoji_count > 0:
            score += min(2, emoji_count)
        
        # Decide based on score (lower threshold for own posts)
        if score >= 2:
            return True, f"good_engagement (score: {score})"
        else:
            return False, f"low_score ({score})"
    
    def upvote_comments_on_own_post(self, post_id, max_upvotes=5):
        """
        Check comments on AlleyBot's post and upvote helpful ones
        
        Args:
            post_id: ID of AlleyBot's post
            max_upvotes: Maximum comments to upvote per post
            
        Returns:
            dict with upvote results
        """
        try:
            # Get post with comments
            post_data = self.api.get_post(post_id)
            raw_comments = post_data.get('comments', [])
            
            # Flatten comments and their replies
            comments = []
            for comment in raw_comments:
                comments.append(comment)
                # Add replies
                replies = comment.get('replies', [])
                comments.extend(replies)
            
            if not comments:
                return {
                    'post_id': post_id,
                    'upvoted': 0,
                    'skipped': 0,
                    'reason': 'no_comments'
                }
            
            upvoted = 0
            skipped = 0
            results = []
            
            for comment in comments[:20]:  # Check top 20 comments
                if upvoted >= max_upvotes:
                    break
                
                comment_id = comment.get('id')
                should_upvote, reason = self._should_upvote_comment(comment)
                
                if should_upvote:
                    try:
                        self.api.upvote_comment(comment_id)
                        
                        # Record in memory
                        self.upvoted_comments[comment_id] = {
                            'post_id': post_id,
                            'author': comment.get('author', {}).get('username', 'unknown'),
                            'timestamp': datetime.now().isoformat(),
                            'reason': reason
                        }
                        
                        upvoted += 1
                        results.append({
                            'comment_id': comment_id,
                            'action': 'upvoted',
                            'reason': reason
                        })
                        
                    except Exception as e:
                        if '409' in str(e) or 'already' in str(e).lower():
                            # Already upvoted, add to memory
                            self.upvoted_comments[comment_id] = {
                                'post_id': post_id,
                                'author': comment.get('author', {}).get('username', 'unknown'),
                                'timestamp': datetime.now().isoformat(),
                                'reason': 'already_upvoted'
                            }
                        skipped += 1
                else:
                    skipped += 1
                    results.append({
                        'comment_id': comment_id,
                        'action': 'skipped',
                        'reason': reason
                    })
            
            # Save memory
            self._save_memory()
            
            return {
                'post_id': post_id,
                'upvoted': upvoted,
                'skipped': skipped,
                'total_comments': len(comments),
                'results': results
            }
            
        except Exception as e:
            return {
                'post_id': post_id,
                'error': str(e),
                'upvoted': 0,
                'skipped': 0
            }
    
    def support_own_posts(self, max_posts=10, max_upvotes_per_post=5):
        """
        Check AlleyBot's recent posts and upvote comments on them
        
        Args:
            max_posts: Maximum posts to check
            max_upvotes_per_post: Max upvotes per post
            
        Returns:
            Summary of upvoting activity
        """
        try:
            # Get AlleyBot's own posts using profile API (most reliable)
            own_posts = []
            
            print("    Using profile API to get own posts...")
            profile = self.api.get_public_profile(name='AlleyBot')
            
            if 'recentPosts' in profile:
                own_posts = profile.get('recentPosts', [])
                print(f"    Profile API found {len(own_posts)} posts")
            else:
                print("    No recentPosts in profile API")
            
            # Limit to requested max_posts
            own_posts = own_posts[:max_posts]
            
            if not own_posts:
                print("    No posts found - AlleyBot needs to create posts first!")
                return {
                    'posts_checked': 0,
                    'total_upvoted': 0,
                    'total_skipped': 0,
                    'reason': 'no_own_posts_yet'
                }
            
            total_upvoted = 0
            total_skipped = 0
            posts_checked = 0
            
            for post in own_posts:
                post_id = post.get('id')
                post_title = post.get('title', 'Unknown')
                
                if not post_id:
                    continue
                
                print(f"  🔍 Checking own post: {post_title[:40]}...")
                
                result = self.upvote_comments_on_own_post(post_id, max_upvotes=max_upvotes_per_post)
                
                if 'error' not in result:
                    total_upvoted += result.get('upvoted', 0)
                    total_skipped += result.get('skipped', 0)
                    posts_checked += 1
                    
                    if result.get('upvoted', 0) > 0:
                        print(f"    👍 Upvoted {result['upvoted']} comment(s)")
                else:
                    print(f"    ⚠️  Error: {result.get('error', 'Unknown error')}")
            
            return {
                'posts_checked': posts_checked,
                'total_upvoted': total_upvoted,
                'total_skipped': total_skipped,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'posts_checked': 0,
                'total_upvoted': 0,
                'total_skipped': 0
            }
    
    def get_stats(self):
        """Get statistics about own post comment upvoting"""
        total_upvoted = len(self.upvoted_comments)
        
        # Count by reason
        reasons = {}
        authors = {}
        posts = {}
        
        for comment_id, data in self.upvoted_comments.items():
            reason = data.get('reason', 'unknown')
            author = data.get('author', 'unknown')
            post_id = data.get('post_id', 'unknown')
            
            reasons[reason] = reasons.get(reason, 0) + 1
            authors[author] = authors.get(author, 0) + 1
            posts[post_id] = posts.get(post_id, 0) + 1
        
        return {
            'total_upvoted': total_upvoted,
            'reasons': reasons,
            'top_authors': sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10],
            'posts_engaged': len(posts)
        }


if __name__ == "__main__":
    # Test the own post comment upvoter
    print("🎯 Testing Own Post Comment Upvoter\n")
    
    upvoter = OwnPostCommentUpvoter()
    
    print("📝 Checking AlleyBot's own posts...\n")
    result = upvoter.support_own_posts(max_posts=5, max_upvotes_per_post=3)
    
    if 'error' not in result:
        print(f"\n📊 Results:")
        print(f"  Posts checked: {result['posts_checked']}")
        print(f"  Comments upvoted: {result['total_upvoted']}")
        print(f"  Comments skipped: {result['total_skipped']}")
        
        # Show stats
        stats = upvoter.get_stats()
        print(f"\n📈 All-time stats:")
        print(f"  Total comments upvoted on own posts: {stats['total_upvoted']}")
        print(f"  Posts engaged with: {stats['posts_engaged']}")
        print(f"  Top commenters: {', '.join([f'{a}({c})' for a, c in stats['top_authors'][:3]])}")
    else:
        print(f"\n❌ Error: {result['error']}")
