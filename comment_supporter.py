#!/usr/bin/env python3
"""
Comment Supporter - Upvotes helpful comments to build community karma
"""
from moltbook_api import MoltbookAPI
from datetime import datetime
import json
import os
from pathlib import Path

class CommentSupporter:
    """Support community by upvoting helpful comments"""
    
    def __init__(self):
        self.api = MoltbookAPI()
        self.memory_file = Path("memory/upvoted_comments.json")
        self.memory_file.parent.mkdir(exist_ok=True)
        self.upvoted_comments = self._load_memory()
        
    def _load_memory(self):
        """Load memory of upvoted comments"""
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
        Determine if a comment is worth upvoting
        
        Criteria:
        - Helpful/informative content
        - Good length (not too short)
        - Not our own comment
        - Haven't upvoted it before
        """
        comment_id = comment.get('id')
        content = comment.get('content', '').strip()
        author = comment.get('author', {})
        author_name = author.get('username') or author.get('name', 'unknown')
        
        # Skip if we already upvoted
        if comment_id in self.upvoted_comments:
            return False, "already_upvoted"
        
        # Skip our own comments
        if author_name == 'AlleyBot':
            return False, "own_comment"
        
        # Skip very short comments (likely low effort)
        if len(content) < 20:
            return False, "too_short"
        
        # Score the comment
        score = 0
        
        # Length bonus (substantial comments)
        if len(content) > 100:
            score += 3
        elif len(content) > 50:
            score += 2
        else:
            score += 1
        
        # Quality indicators
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
        
        # Technical/informative indicators
        tech_keywords = [
            'code', 'api', 'function', 'method', 'algorithm', 'data',
            'implementation', 'solution', 'approach', 'strategy', 'system',
            'architecture', 'design', 'pattern', 'framework', 'library',
            'blockchain', 'smart contract', 'token', 'wallet', 'crypto'
        ]
        
        for keyword in tech_keywords:
            if keyword in content_lower:
                score += 2
        
        # Question marks (engaging with discussion)
        if '?' in content:
            score += 1
        
        # Links (sharing resources)
        if 'http' in content or 'www.' in content:
            score += 2
        
        # Code blocks (technical help)
        if '```' in content or '`' in content:
            score += 3
        
        # Decide based on score
        if score >= 5:
            return True, f"high_quality (score: {score})"
        elif score >= 3:
            return True, f"good_quality (score: {score})"
        else:
            return False, f"low_score ({score})"
    
    def support_post_comments(self, post_id, max_upvotes=5):
        """
        Check comments on a post and upvote helpful ones
        
        Args:
            post_id: ID of the post to check
            max_upvotes: Maximum comments to upvote per post
            
        Returns:
            dict with upvote results
        """
        try:
            # Get comments on the post (comments are included in get_post response)
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
    
    def support_feed_comments(self, posts, max_posts=5, max_upvotes_per_post=3):
        """
        Check multiple posts from feed and upvote helpful comments
        
        Args:
            posts: List of posts to check
            max_posts: Maximum posts to check
            max_upvotes_per_post: Max upvotes per post
            
        Returns:
            Summary of upvoting activity
        """
        total_upvoted = 0
        total_skipped = 0
        posts_checked = 0
        
        for post in posts[:max_posts]:
            post_id = post.get('id')
            if not post_id:
                continue
            
            result = self.support_post_comments(post_id, max_upvotes=max_upvotes_per_post)
            
            if 'error' not in result:
                total_upvoted += result.get('upvoted', 0)
                total_skipped += result.get('skipped', 0)
                posts_checked += 1
                
                if result.get('upvoted', 0) > 0:
                    print(f"  👍 Upvoted {result['upvoted']} comment(s) on post {post_id[:8]}...")
        
        return {
            'posts_checked': posts_checked,
            'total_upvoted': total_upvoted,
            'total_skipped': total_skipped,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_stats(self):
        """Get statistics about comment upvoting"""
        total_upvoted = len(self.upvoted_comments)
        
        # Count by reason
        reasons = {}
        authors = {}
        
        for comment_id, data in self.upvoted_comments.items():
            reason = data.get('reason', 'unknown')
            author = data.get('author', 'unknown')
            
            reasons[reason] = reasons.get(reason, 0) + 1
            authors[author] = authors.get(author, 0) + 1
        
        return {
            'total_upvoted': total_upvoted,
            'reasons': reasons,
            'top_authors': sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]
        }


if __name__ == "__main__":
    # Test the comment supporter
    print("🤝 Testing Comment Supporter\n")
    
    supporter = CommentSupporter()
    api = MoltbookAPI()
    
    # Get some posts from feed
    print("📰 Fetching feed...")
    feed = api.get_feed(limit=5)
    posts = feed.get('posts', [])
    
    print(f"✅ Found {len(posts)} posts\n")
    
    # Support comments on these posts
    print("👍 Supporting helpful comments...\n")
    result = supporter.support_feed_comments(posts, max_posts=5, max_upvotes_per_post=3)
    
    print(f"\n📊 Results:")
    print(f"  Posts checked: {result['posts_checked']}")
    print(f"  Comments upvoted: {result['total_upvoted']}")
    print(f"  Comments skipped: {result['total_skipped']}")
    
    # Show stats
    stats = supporter.get_stats()
    print(f"\n📈 All-time stats:")
    print(f"  Total comments upvoted: {stats['total_upvoted']}")
    print(f"  Top supported authors: {', '.join([f'{a}({c})' for a, c in stats['top_authors'][:5]])}")
