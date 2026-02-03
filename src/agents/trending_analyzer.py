"""
Trending Topic Analyzer
Analyzes feeds from Moltx/Moltbook to identify trending topics and generate relevant content
"""

import re
from collections import Counter
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class TrendingAnalyzer:
    """Analyzes trending topics from social feeds"""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
            'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
        }
    
    def analyze_feed(self, posts: List[Dict]) -> Dict:
        """
        Analyze feed posts to identify trending topics
        
        Args:
            posts: List of post dictionaries with 'content', 'likes', 'comments', etc.
        
        Returns:
            Dict with trending topics, hashtags, mentions, and insights
        """
        if not posts:
            return {
                'trending_topics': [],
                'trending_hashtags': [],
                'trending_mentions': [],
                'top_posts': [],
                'insights': "No posts to analyze"
            }
        
        # Extract data from posts
        all_text = []
        all_hashtags = []
        all_mentions = []
        engagement_scores = []
        
        for post in posts:
            content = post.get('content', '')
            all_text.append(content)
            
            # Extract hashtags
            hashtags = re.findall(r'#(\w+)', content)
            all_hashtags.extend([tag.lower() for tag in hashtags])
            
            # Extract mentions
            mentions = re.findall(r'@(\w+)', content)
            all_mentions.extend([mention.lower() for mention in mentions])
            
            # Calculate engagement score
            likes = post.get('likes', 0) or post.get('upvotes', 0) or 0
            comments = post.get('comments', 0) or post.get('comment_count', 0) or 0
            reposts = post.get('reposts', 0) or post.get('shares', 0) or 0
            
            engagement = likes + (comments * 2) + (reposts * 3)
            engagement_scores.append((post, engagement))
        
        # Find trending keywords
        trending_keywords = self._extract_keywords(' '.join(all_text))
        
        # Find trending hashtags
        hashtag_counts = Counter(all_hashtags)
        trending_hashtags = hashtag_counts.most_common(10)
        
        # Find trending mentions
        mention_counts = Counter(all_mentions)
        trending_mentions = mention_counts.most_common(10)
        
        # Get top posts by engagement
        engagement_scores.sort(key=lambda x: x[1], reverse=True)
        top_posts = [
            {
                'content': post.get('content', '')[:200],
                'author': post.get('agent_name', post.get('author', 'Unknown')),
                'engagement': score,
                'id': post.get('id', '')
            }
            for post, score in engagement_scores[:5]
        ]
        
        # Generate insights
        insights = self._generate_insights(
            trending_keywords,
            trending_hashtags,
            trending_mentions,
            top_posts
        )
        
        return {
            'trending_topics': trending_keywords[:10],
            'trending_hashtags': [{'tag': tag, 'count': count} for tag, count in trending_hashtags],
            'trending_mentions': [{'mention': mention, 'count': count} for mention, count in trending_mentions],
            'top_posts': top_posts,
            'insights': insights,
            'total_posts_analyzed': len(posts)
        }
    
    def _extract_keywords(self, text: str, top_n: int = 20) -> List[Tuple[str, int]]:
        """Extract trending keywords from text"""
        # Clean and tokenize
        text = text.lower()
        words = re.findall(r'\b[a-z]{3,}\b', text)
        
        # Filter stop words
        filtered_words = [w for w in words if w not in self.stop_words]
        
        # Count occurrences
        word_counts = Counter(filtered_words)
        
        return word_counts.most_common(top_n)
    
    def _generate_insights(
        self,
        keywords: List[Tuple[str, int]],
        hashtags: List[Tuple[str, int]],
        mentions: List[Tuple[str, int]],
        top_posts: List[Dict]
    ) -> str:
        """Generate human-readable insights from trending data"""
        insights = []
        
        if keywords:
            top_keywords = ', '.join([kw for kw, _ in keywords[:5]])
            insights.append(f"🔥 Hot topics: {top_keywords}")
        
        if hashtags:
            top_tags = ', '.join([f"#{tag}" for tag, _ in hashtags[:3]])
            insights.append(f"📊 Trending hashtags: {top_tags}")
        
        if mentions:
            top_users = ', '.join([f"@{mention}" for mention, _ in mentions[:3]])
            insights.append(f"👥 Active users: {top_users}")
        
        if top_posts:
            insights.append(f"💬 {len(top_posts)} high-engagement posts analyzed")
        
        return '\n'.join(insights) if insights else "No significant trends detected"
    
    def generate_post_prompt(self, trending_data: Dict) -> str:
        """
        Generate a prompt for AI to create a post based on trending topics
        
        Args:
            trending_data: Output from analyze_feed()
        
        Returns:
            Prompt string for AI model
        """
        topics = trending_data.get('trending_topics', [])
        hashtags = trending_data.get('trending_hashtags', [])
        top_posts = trending_data.get('top_posts', [])
        
        # Build context from trending data
        topic_list = ', '.join([topic for topic, _ in topics[:5]]) if topics else 'AI agents'
        hashtag_list = ', '.join([f"#{tag['tag']}" for tag in hashtags[:3]]) if hashtags else ''
        
        # Sample top post content for context
        context_posts = []
        for post in top_posts[:2]:
            context_posts.append(f"- {post['content'][:150]}")
        context = '\n'.join(context_posts) if context_posts else ''
        
        prompt = f"""You are AlleyBot, an autonomous AI agent on the Moltx/Moltbook platform.

Based on current trending topics in the feed, create an engaging, insightful post.

TRENDING TOPICS: {topic_list}
TRENDING HASHTAGS: {hashtag_list}

POPULAR POSTS FOR CONTEXT:
{context}

Create a post that:
1. Relates to one or more trending topics
2. Provides unique insight or perspective
3. Is engaging and conversational (not corporate)
4. Is 1-3 sentences (concise and punchy)
5. Optionally includes relevant hashtags
6. Shows personality and authenticity

Generate the post content only (no explanations):"""
        
        return prompt
    
    def should_post_about_trend(self, trending_data: Dict, min_posts: int = 5) -> bool:
        """
        Determine if there's enough trending activity to warrant a post
        
        Args:
            trending_data: Output from analyze_feed()
            min_posts: Minimum number of posts needed to identify trends
        
        Returns:
            True if should post about trends
        """
        total_posts = trending_data.get('total_posts_analyzed', 0)
        trending_topics = trending_data.get('trending_topics', [])
        
        # Need enough posts and at least one strong trend
        if total_posts < min_posts:
            return False
        
        if not trending_topics:
            return False
        
        # Check if top trend appears frequently enough
        if trending_topics[0][1] >= 3:  # Appears at least 3 times
            return True
        
        return False
