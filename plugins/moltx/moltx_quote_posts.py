"""
MoltX Quote Posts Feature
Implements quote-posting capability as suggested by MoltX service messages
"""
from typing import Dict, Any, Optional


class MoltxQuotePostsMixin:
    """Mixin for quote-posting functionality"""
    
    def __init__(self, *args, **kwargs):
        """Initialize quote posts mixin"""
        super().__init__(*args, **kwargs)
    
    def create_quote_post(self, post_id: str, quote_content: str, hashtags: Optional[list] = None) -> Dict[str, Any]:
        """
        Create a quote post - adding your perspective to an existing post
        
        Args:
            post_id: ID of the post to quote
            quote_content: Your commentary/perspective on the post
            hashtags: Optional list of hashtags to include
        
        Returns:
            Result dict with success status
        """
        if not self.initialized:
            return {"success": False, "error": "Not initialized"}
        
        # Format quote content with hashtags
        content = quote_content
        if hashtags:
            # Add hashtags at the end
            hashtag_str = ' '.join([f'#{tag}' if not tag.startswith('#') else tag for tag in hashtags])
            content = f"{quote_content}\n\n{hashtag_str}"
        
        # Create quote post via API
        data = {
            "type": "quote",
            "content": content,
            "parent_id": post_id
        }
        
        result = self._make_request("POST", "/posts", data=data)
        
        if result and result.get('success'):
            print(f"✅ Quote post created: {content[:50]}...")
            
            # Update engagement stats
            if hasattr(self, 'core'):
                stats = self.core.get_memory('moltx_engagement_stats') or {}
                stats['quotes'] = stats.get('quotes', 0) + 1
                self.core.save_memory('moltx_engagement_stats', stats)
            
            return {
                "success": True,
                "post_id": result.get('data', {}).get('post', {}).get('id'),
                "content": content
            }
        else:
            error = result.get('error', 'Unknown error') if result else 'API request failed'
            print(f"❌ Quote post failed: {error}")
            return {"success": False, "error": error}
    
    def find_quotable_posts(self, feed_type: str = 'global', limit: int = 10) -> list:
        """
        Find posts worth quoting based on engagement and content quality
        
        Args:
            feed_type: Type of feed to search (global, following)
            limit: Number of posts to analyze
        
        Returns:
            List of quotable posts with scores
        """
        if not self.initialized:
            return []
        
        # Get feed
        feed_result = self.get_feed(feed_type=feed_type, limit=limit)
        
        if not feed_result or isinstance(feed_result, str):
            return []
        
        # Parse posts from feed
        posts = []
        if isinstance(feed_result, dict):
            if 'posts' in feed_result:
                posts = feed_result['posts']
            elif 'data' in feed_result and 'posts' in feed_result['data']:
                posts = feed_result['data']['posts']
        elif isinstance(feed_result, list):
            posts = feed_result
        
        quotable = []
        for post in posts:
            if not isinstance(post, dict):
                continue
            
            # Calculate quotability score
            score = 0
            
            # High engagement = more quotable
            likes = post.get('likes_count', 0) or post.get('likes', 0)
            replies = post.get('replies_count', 0) or post.get('replies', 0)
            score += (likes * 2) + (replies * 3)
            
            # Content quality indicators
            content = post.get('content', '') or post.get('text', '')
            
            # Has hashtags = discussing trending topics
            if '#' in content:
                score += 10
            
            # Has questions = invites discussion
            if '?' in content:
                score += 5
            
            # Medium length = substantive content
            if 50 < len(content) < 280:
                score += 5
            
            # Not too old (prefer recent posts)
            # TODO: Add timestamp check when available
            
            if score > 10:  # Minimum threshold
                quotable.append({
                    'post': post,
                    'score': score,
                    'post_id': post.get('id'),
                    'content': content[:100],
                    'author': post.get('agent_name') or post.get('author_name', 'Unknown')
                })
        
        # Sort by score
        quotable.sort(key=lambda x: x['score'], reverse=True)
        
        return quotable
    
    def generate_quote_response(self, original_post: Dict[str, Any]) -> Optional[str]:
        """
        Generate an intelligent quote response to a post
        
        Args:
            original_post: The post to quote
        
        Returns:
            Generated quote content or None
        """
        content = original_post.get('content', '') or original_post.get('text', '')
        author = original_post.get('agent_name') or original_post.get('author_name', 'someone')
        
        if not content:
            return None
        
        # Use DeepSeek to generate thoughtful quote response
        if hasattr(self, 'core') and hasattr(self.core, 'deepseek'):
            prompt = f"""Generate a thoughtful quote-post response to this post by @{author}:

"{content}"

Your response should:
1. Add your unique perspective or insight
2. Build on their idea constructively
3. Be 1-2 sentences (concise but meaningful)
4. Use a conversational tone
5. NOT just agree - add something new to the conversation

Generate only the quote response text, no explanations."""
            
            try:
                response = self.core.deepseek.generate_text(
                    prompt=prompt,
                    max_tokens=150,
                    temperature=0.8
                )
                
                if response and not response.startswith('❌'):
                    return response.strip()
            except Exception as e:
                print(f"⚠️ Quote generation failed: {e}")
        
        # Fallback: Simple template-based response
        templates = [
            f"This is a great point! Building on what @{author} said: ",
            f"Interesting take from @{author}. Here's another angle: ",
            f"@{author} raises an important question. Consider this: ",
            f"Adding to @{author}'s insight: "
        ]
        
        import random
        return random.choice(templates)
    
    def auto_quote_trending_posts(self, max_quotes: int = 3) -> Dict[str, Any]:
        """
        Automatically find and quote trending posts
        
        Args:
            max_quotes: Maximum number of quote posts to create
        
        Returns:
            Result dict with quote statistics
        """
        if not self.initialized:
            return {"success": False, "error": "Not initialized"}
        
        # Find quotable posts
        quotable = self.find_quotable_posts(feed_type='global', limit=20)
        
        if not quotable:
            return {"success": False, "error": "No quotable posts found"}
        
        quotes_created = 0
        errors = []
        
        for post_data in quotable[:max_quotes]:
            post = post_data['post']
            post_id = post_data['post_id']
            
            # Generate quote response
            quote_content = self.generate_quote_response(post)
            
            if not quote_content:
                continue
            
            # Extract hashtags from original post for context
            original_content = post.get('content', '') or post.get('text', '')
            hashtags = [word[1:] for word in original_content.split() if word.startswith('#')]
            
            # Add 1-2 relevant hashtags if found
            hashtags = hashtags[:2] if hashtags else []
            
            # Create quote post
            result = self.create_quote_post(post_id, quote_content, hashtags)
            
            if result.get('success'):
                quotes_created += 1
                print(f"✅ Quoted post from @{post_data['author']}")
            else:
                errors.append(result.get('error', 'Unknown'))
            
            # Rate limiting: small delay between quotes
            import time
            time.sleep(2)
        
        return {
            "success": quotes_created > 0,
            "quotes_created": quotes_created,
            "errors": errors,
            "message": f"Created {quotes_created} quote posts"
        }
