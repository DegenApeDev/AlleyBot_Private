#!/usr/bin/env python3
"""
Moltbook Engagement Analyzer Implementation
Scores posts based on author influence, topic relevance, timing, and engagement potential
"""
from datetime import datetime, timezone
import re
from typing import Dict, List, Optional

class EngagementAnalyzer:
    """Analyze Moltbook posts to identify high-value engagement opportunities"""
    
    # Priority keywords for topic relevance
    PRIORITY_KEYWORDS = {
        'web3': 5,
        'blockchain': 5,
        'crypto': 4,
        'ai': 5,
        'raspberry pi': 5,
        'raspberrypi': 5,
        'development': 3,
        'coding': 3,
        'open source': 4,
        'opensource': 4,
        'donations': 5,
        'base': 4,
        'eth': 3,
        'btc': 3,
        'collaboration': 4,
        'partnership': 4,
        'bot': 3,
        'agent': 3,
        'moltbook': 3,
        'defi': 4,
        'nft': 3
    }
    
    def __init__(self, relationship_db=None):
        """
        Initialize analyzer
        
        Args:
            relationship_db: Optional dict of known relationships {username: relationship_score}
        """
        self.relationship_db = relationship_db or {}
        self.author_cache = {}  # Cache author scores
    
    def analyze_post(self, post_data: Dict) -> Dict:
        """
        Analyze a post and calculate engagement score
        
        Args:
            post_data: Dict with post information
                {
                    'id': str,
                    'title': str,
                    'content': str,
                    'author': str or dict,
                    'created_at': str (ISO format),
                    'upvotes': int,
                    'comment_count': int,
                    'author_follower_count': int (optional),
                    'author_verified': bool (optional)
                }
        
        Returns:
            Dict with analysis results
        """
        # Extract post details
        post_id = post_data.get('id', 'unknown')
        title = post_data.get('title', '')
        content = post_data.get('content', '')
        
        # Handle author as dict or string
        author_obj = post_data.get('author', {})
        if isinstance(author_obj, dict):
            author = author_obj.get('username') or author_obj.get('name', 'unknown')
        else:
            author = author_obj or 'unknown'
        
        created_at = post_data.get('created_at', datetime.now(timezone.utc).isoformat())
        
        # Calculate component scores
        author_score = self._calculate_author_score(post_data, author)
        topic_score = self._calculate_topic_score(title, content, author)
        timing_score = self._calculate_timing_score(created_at)
        engagement_score = self._calculate_engagement_score(post_data)
        
        total_score = author_score + topic_score + timing_score + engagement_score
        
        # Generate recommendation
        recommendation, suggested_action = self._generate_recommendation(total_score)
        
        # Find matched keywords
        full_text = f"{title} {content}".lower()
        matched_keywords = [kw for kw in self.PRIORITY_KEYWORDS.keys() if kw in full_text]
        
        return {
            'post_id': post_id,
            'author': author,
            'timestamp': created_at,
            'content_preview': (title[:50] + '...') if len(title) > 50 else title,
            'metrics': {
                'author_score': author_score,
                'topic_score': topic_score,
                'timing_score': timing_score,
                'engagement_score': engagement_score,
                'total_score': total_score
            },
            'recommendation': recommendation,
            'suggested_action': suggested_action,
            'priority_keywords': matched_keywords
        }
    
    def _calculate_author_score(self, post_data: Dict, author: str) -> int:
        """
        Calculate author influence score (0-40 points)
        
        Factors:
        - Follower count
        - Verification status
        - Relationship with AlleyBot
        """
        score = 0
        
        # Check cache first
        if author in self.author_cache:
            return self.author_cache[author]
        
        # Follower count (0-25 points)
        follower_count = post_data.get('author_follower_count', 0)
        if isinstance(post_data.get('author'), dict):
            follower_count = post_data['author'].get('follower_count', 0)
        
        if follower_count >= 10000:
            score += 25
        elif follower_count >= 5000:
            score += 20
        elif follower_count >= 1000:
            score += 15
        elif follower_count >= 500:
            score += 10
        elif follower_count >= 100:
            score += 5
        else:
            score += 2
        
        # Verification status (0-5 points)
        verified = post_data.get('author_verified', False)
        if isinstance(post_data.get('author'), dict):
            verified = post_data['author'].get('verified', False)
        
        if verified:
            score += 5
        
        # Relationship with AlleyBot (0-10 points)
        if author in self.relationship_db:
            relationship_strength = self.relationship_db[author]
            # Handle both int and dict formats
            if isinstance(relationship_strength, dict):
                relationship_score = relationship_strength.get('relationship_strength', 0)
            else:
                relationship_score = relationship_strength
            score += min(10, int(relationship_score / 10))
        
        # Cache the score
        self.author_cache[author] = min(40, score)
        return self.author_cache[author]
    
    def _calculate_topic_score(self, title: str, content: str, author: str) -> int:
        """
        Calculate topic relevance score (0-30 points)
        
        Factors:
        - Keyword matches
        - Known relationship
        """
        score = 0
        full_text = f"{title} {content}".lower()
        
        # Keyword matching (0-25 points)
        keyword_score = 0
        for keyword, weight in self.PRIORITY_KEYWORDS.items():
            if keyword in full_text:
                keyword_score += weight
        
        score += min(25, keyword_score)
        
        # Known relationship bonus (0-5 points)
        if author in self.relationship_db:
            score += 5
        
        return min(30, score)
    
    def _calculate_timing_score(self, created_at: str) -> int:
        """
        Calculate timing score (0-20 points)
        
        Factors:
        - Post freshness
        - Time of day
        - Day of week
        """
        score = 0
        
        try:
            post_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age_minutes = (now - post_time).total_seconds() / 60
            
            # Freshness (0-12 points)
            if age_minutes < 15:
                score += 12
            elif age_minutes < 60:
                score += 10
            elif age_minutes < 120:
                score += 7
            elif age_minutes < 240:
                score += 4
            else:
                score += 1
            
            # Time of day (0-5 points) - Higher during 14:00-22:00 UTC
            hour = post_time.hour
            if 14 <= hour <= 22:
                score += 5
            elif 10 <= hour <= 14 or 22 <= hour <= 24:
                score += 3
            else:
                score += 1
            
            # Day of week (0-3 points) - Higher on weekdays
            weekday = post_time.weekday()
            if weekday < 5:  # Monday-Friday
                score += 3
            else:
                score += 1
                
        except Exception:
            # If timestamp parsing fails, give baseline score
            score = 8
        
        return min(20, score)
    
    def _calculate_engagement_score(self, post_data: Dict) -> int:
        """
        Calculate engagement potential score (0-10 points)
        
        Factors:
        - Comment count
        - Upvote count
        - Engagement rate
        """
        score = 0
        
        comment_count = post_data.get('comment_count', 0)
        upvotes = post_data.get('upvotes', 0)
        
        # Comment activity (0-5 points)
        if comment_count >= 10:
            score += 5
        elif comment_count >= 5:
            score += 4
        elif comment_count >= 2:
            score += 3
        elif comment_count >= 1:
            score += 2
        else:
            score += 1
        
        # Upvote activity (0-5 points)
        if upvotes >= 20:
            score += 5
        elif upvotes >= 10:
            score += 4
        elif upvotes >= 5:
            score += 3
        elif upvotes >= 2:
            score += 2
        else:
            score += 1
        
        return min(10, score)
    
    def _generate_recommendation(self, total_score: int) -> tuple:
        """
        Generate engagement recommendation based on total score
        
        Returns:
            (recommendation, suggested_action)
        """
        if total_score >= 80:
            return ('engage', 'reply_technical')
        elif total_score >= 60:
            return ('engage', 'reply_standard')
        elif total_score >= 40:
            return ('like', 'like_only')
        else:
            return ('ignore', 'log_for_learning')
    
    def batch_analyze(self, posts: List[Dict]) -> List[Dict]:
        """
        Analyze multiple posts and return sorted by score
        
        Args:
            posts: List of post dicts
        
        Returns:
            List of analysis results sorted by total_score (highest first)
        """
        analyses = [self.analyze_post(post) for post in posts]
        return sorted(analyses, key=lambda x: x['metrics']['total_score'], reverse=True)
    
    def print_analysis(self, analysis: Dict):
        """Pretty print analysis results"""
        print(f"\n{'='*60}")
        print(f"📊 Post Analysis: {analysis['post_id']}")
        print(f"{'='*60}")
        print(f"👤 Author: {analysis['author']}")
        print(f"📝 Content: {analysis['content_preview']}")
        print(f"\n📈 Scores:")
        metrics = analysis['metrics']
        print(f"   Author Influence:  {metrics['author_score']:2d}/40")
        print(f"   Topic Relevance:   {metrics['topic_score']:2d}/30")
        print(f"   Timing:            {metrics['timing_score']:2d}/20")
        print(f"   Engagement:        {metrics['engagement_score']:2d}/10")
        print(f"   {'─'*30}")
        print(f"   TOTAL:             {metrics['total_score']:2d}/100")
        print(f"\n💡 Recommendation: {analysis['recommendation'].upper()}")
        print(f"🎯 Action: {analysis['suggested_action']}")
        if analysis['priority_keywords']:
            print(f"🔑 Keywords: {', '.join(analysis['priority_keywords'])}")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    # Test with sample posts
    analyzer = EngagementAnalyzer()
    
    sample_posts = [
        {
            'id': 'post1',
            'title': 'Just deployed my new bot on Raspberry Pi!',
            'content': 'Looking for Web3 integration tips. Anyone working with AI and blockchain?',
            'author': {'username': 'techdev', 'follower_count': 5000, 'verified': True},
            'created_at': datetime.now(timezone.utc).isoformat(),
            'upvotes': 5,
            'comment_count': 2
        },
        {
            'id': 'post2',
            'title': 'Anyone accepting donations in BASE?',
            'content': 'Need to set up crypto donations for my project',
            'author': 'newuser',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'upvotes': 1,
            'comment_count': 0,
            'author_follower_count': 50
        },
        {
            'id': 'post3',
            'title': "What's for lunch?",
            'content': 'Thinking about pizza',
            'author': 'randomuser',
            'created_at': (datetime.now(timezone.utc)).isoformat(),
            'upvotes': 0,
            'comment_count': 1,
            'author_follower_count': 10
        }
    ]
    
    print("\n🧪 Testing Moltbook Engagement Analyzer\n")
    
    for post in sample_posts:
        analysis = analyzer.analyze_post(post)
        analyzer.print_analysis(analysis)
