"""
Moltx Content Creation Mixin
Post creation, AI-powered content generation, trending topics, and repost logic.
"""
import random
import re
from collections import Counter
from datetime import datetime
from typing import List, Optional, Union


class MoltxContentMixin:
    """Mixin providing content creation and AI generation functionality"""

    def __init__(self, *args, **kwargs):
        """Initialize mixin - accepts any args/kwargs for cooperative inheritance"""
        super().__init__(*args, **kwargs)

    def _check_engagement_quota(self) -> bool:
        """Check if 5:1 engagement quota is met per official spec:
        For every 1 post: 5 replies, 10 likes, follow new agents"""
        try:
            stats = self.core.get_memory('moltx_engagement_stats') or {}
            replies = stats.get('replies', 0)
            likes = stats.get('likes', 0)
            follows = stats.get('follows', 0)
            posts = stats.get('posts', 0)
            
            # Reset daily
            last_reset = stats.get('last_reset', '')
            today = datetime.now().strftime('%Y-%m-%d')
            if last_reset != today:
                stats = {'replies': 0, 'likes': 0, 'follows': 0, 'posts': 0, 'last_reset': today}
                self.core.save_memory('moltx_engagement_stats', stats)
                return False
            
            # Check if all requirements met for next post
            needed_replies = (posts + 1) * 5
            needed_likes = (posts + 1) * 10
            
            return replies >= needed_replies and likes >= needed_likes
        except Exception:
            return False
    
    def _record_engagement(self, action_type: str = 'like') -> None:
        """Record an engagement action (like, reply, follow)"""
        try:
            stats = self.core.get_memory('moltx_engagement_stats') or {}
            today = datetime.now().strftime('%Y-%m-%d')
            last_reset = stats.get('last_reset', '')
            if last_reset != today:
                stats = {'replies': 0, 'likes': 0, 'follows': 0, 'posts': 0, 'last_reset': today}
            
            if action_type == 'like':
                stats['likes'] = stats.get('likes', 0) + 1
            elif action_type == 'reply':
                stats['replies'] = stats.get('replies', 0) + 1
            elif action_type == 'follow':
                stats['follows'] = stats.get('follows', 0) + 1
                
            self.core.save_memory('moltx_engagement_stats', stats)
            print(f"📊 Engagement recorded: {action_type}")
        except Exception as e:
            print(f"⚠️ Failed to record engagement: {e}")
    
    def _record_post_made(self) -> None:
        """Record a post made (for 5:1 tracking)"""
        try:
            stats = self.core.get_memory('moltx_engagement_stats') or {}
            today = datetime.now().strftime('%Y-%m-%d')
            last_reset = stats.get('last_reset', '')
            if last_reset != today:
                stats = {'replies': 0, 'likes': 0, 'follows': 0, 'posts': 0, 'last_reset': today}
            stats['posts'] = stats.get('posts', 0) + 1
            self.core.save_memory('moltx_engagement_stats', stats)
            print(f"📊 Post recorded (total today: {stats['posts']})")
        except Exception as e:
            print(f"⚠️ Failed to record post: {e}")
    
    def _auto_engage_for_posting(self) -> str:
        """Auto-engage with feed to meet 5:1 quota:
        - Reply to 5 posts
        - Like 10 posts  
        - Follow any new interesting agents"""
        try:
            stats = self.core.get_memory('moltx_engagement_stats') or {}
            posts = stats.get('posts', 0)
            replies = stats.get('replies', 0)
            likes = stats.get('likes', 0)
            follows = stats.get('follows', 0)
            
            needed_replies = (posts + 1) * 5 - replies
            needed_likes = (posts + 1) * 10 - likes
            
            if needed_replies <= 0 and needed_likes <= 0:
                return "✅ Engagement quota already met"
            
            print(f"🔄 Need {needed_replies} replies and {needed_likes} likes before posting...")
            
            # Fetch global feed
            feed = self._make_request('GET', '/v1/feed/global', params={'limit': 25})
            if not feed or 'posts' not in feed:
                return "❌ Could not fetch feed for engagement"
            
            posts_list = feed.get('posts', [])
            if not posts_list:
                return "❌ No posts in feed to engage with"
            
            reply_count = 0
            like_count = 0
            
            for post in posts_list:
                post_id = post.get('id')
                if not post_id:
                    continue
                
                # Prioritize replies first (need 5)
                if reply_count < needed_replies:
                    parent_content = post.get('content', '')
                    author = post.get('author_username', 'user')
                    comment = self._generate_comment(parent_content, author)
                    if comment:
                        result = self.create_post(
                            content=comment,
                            post_type='reply',
                            parent_id=post_id
                        )
                        if result and not result.startswith('❌'):
                            self._record_engagement('reply')
                            reply_count += 1
                            print(f"  � Replied to post: {post_id[:12]}...")
                            continue
                
                # Then likes (need 10)
                if like_count < needed_likes:
                    result = self._make_request('POST', f'/v1/posts/{post_id}/like')
                    if result:
                        self._record_engagement('like')
                        like_count += 1
                        print(f"  👍 Liked post: {post_id[:12]}...")
                
                # Check if we're done
                if reply_count >= needed_replies and like_count >= needed_likes:
                    break
            
            # Try to follow new agents if found
            for post in posts_list[:5]:
                author_id = post.get('author_id') or post.get('author', {}).get('id')
                if author_id and hasattr(self, 'follow_agent'):
                    try:
                        self.follow_agent(author_id)
                        self._record_engagement('follow')
                        print(f"  � Followed agent: {author_id[:12]}...")
                    except:
                        pass
            
            return f"✅ Completed {reply_count} replies, {like_count} likes"
            
        except Exception as e:
            print(f"❌ Auto-engage failed: {e}")
            return f"❌ Failed to auto-engage: {e}"

    def _should_wait_for_post_cooldown(self) -> bool:
        """Check if cooldown period since last post"""
        last_post_str = self.core.get_memory('moltx_last_post_time')
        if not last_post_str:
            return False
        try:
            last_post = datetime.fromisoformat(last_post_str)
            return (datetime.now() - last_post).total_seconds() < 600  # 10 minutes
        except (ValueError, TypeError):
            return False

    def _is_topic_request(self, content: str) -> bool:
        """Detect if content is a topic request for AI generation"""
        content_lower = content.lower().strip()
        patterns = [
            r'^topic[:\s]',
            r'^write about',
            r'^generate',
            r'\btrending\b',
            r'\bhashtag\b'
        ]
        return bool(re.search('|'.join(patterns), content_lower))

    def _generate_content(self, prompt: str, mode: str) -> Optional[str]:
        """Generate enhanced content using AI"""
        try:
            from grok_ai import grok_ai
            system_prompt = f"You are an expert {mode} content creator for Moltx. Create engaging, concise {mode}s. Use hashtags and calls to action."
            max_tokens = 4000 if mode == 'article' else 300
            response = grok_ai.chat(prompt, system=system_prompt, max_tokens=max_tokens)
            return response.strip()
        except Exception as e:
            print(f"❌ AI content generation failed: {e}")
            return None

    def _generate_comment(self, parent_content: str, agent_name: Optional[str] = None) -> Optional[str]:
        """Generate contextual comment using DeepSeek only (Grok is expensive, reserved for posts)"""
        user = agent_name or "user"
        full_context = f"Replying to @{user}: {parent_content[:300]}"
        platform_context = "Moltx platform - AI agents, crypto, DeFi, development, community building"

        try:
            from deepseek_ai import deepseek_ai
            if deepseek_ai.enabled:
                comment = deepseek_ai.generate_comment(
                    post_content=full_context,
                    agent_name=user,
                    context=platform_context
                )
                if comment:
                    print(f"🧠 DeepSeek generated comment: {comment[:50]}...")
                    return comment
            print("⚠️ DeepSeek disabled or returned None, no comment generated")
            return None
        except Exception as e:
            print(f"❌ DeepSeek comment failed: {e}")
            return None

    def _calculate_read_time(self, content: str) -> str:
        """Estimate read time for articles"""
        word_count = len(re.findall(r'\w+', content))
        minutes = max(1, word_count // 225)
        return f"{minutes} min"

    def _record_activity(self, action: str, details: dict) -> None:
        """Record platform activity"""
        activity = {
            'platform': 'moltx',
            'action': action,
            'timestamp': datetime.now().isoformat(),
            **details
        }
        print(f"📈 Activity recorded: {action} - {details}")

    def _notify_brain_tracker(self, post_id: str, platform: str, content: str) -> None:
        """Notify brain tracker of new post"""
        summary = f"{platform.upper()} post created ({post_id}): {content[:100]}..."
        try:
            self.core.notify_brain(summary)
        except AttributeError:
            print(f"🧠 Tracker: {summary}")

    def create_post(
        self,
        content: Union[str, List[str]],
        post_type: str = 'post',
        parent_id: Optional[str] = None,
        media_url: Optional[str] = None,
        media_urls: Optional[List[str]] = None,
        cover_image: Optional[str] = None
    ):
        """Create a post on Moltx with optional Grok enhancement and media.
        Supports articles (long-form), threads (list content), quotes/reposts/replies (enhanced).
        """
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        # 5:1 Engagement Rule - Must engage 5x before posting 1x
        if not self._check_engagement_quota():
            print("🔄 5:1 Rule: Engaging with feed before posting...")
            engagement_result = self._auto_engage_for_posting()
            if not engagement_result:
                return "❌ 5:1 Engagement rule: Failed to meet engagement quota. Please try again."
            print(f"✅ Pre-post engagement complete: {engagement_result}")

        if isinstance(content, list):
            return self._create_thread(
                contents=content,
                parent_id=parent_id,
                media_urls=media_urls or []
            )

        if self._should_wait_for_post_cooldown():
            return "⏰ Post cooldown active - waiting 10 minutes between posts"

        is_article = post_type == 'article'
        max_chars = 8000 if is_article else 500
        min_enhance_chars = 1000 if is_article else 50

        if not content or len(content) > max_chars:
            return f"❌ Content required and must be max {max_chars} characters"

        if post_type in ['post', 'article']:
            if len(content) < min_enhance_chars or self._is_topic_request(content):
                enhanced_content = self._generate_content(content, mode=post_type)
                if enhanced_content:
                    content = enhanced_content
                    print(f"🧠 Grok enhanced {post_type} content")

        # Enhance quotes/reposts/replies with AI comment if short
        if post_type in ['quote', 'reply', 'repost'] and len(content) < 50:
            parent_post = self.fetch_post(parent_id)
            if parent_post:
                parent_content = parent_post.get('content', '')
                agent_name = (
                    parent_post.get('author_username')
                    or parent_post.get('username')
                    or parent_post.get('author', {}).get('username')
                )
                comment = self._generate_comment(parent_content, agent_name=agent_name)
                if comment:
                    content = f"{comment}\n\n{content}"
                    print(f"🧠 AI-enhanced {post_type} with contextual comment")

        data = {'content': content}

        if post_type in ['reply', 'quote', 'repost', 'article']:
            data['type'] = post_type
            if parent_id and post_type != 'article':
                data['parent_id'] = parent_id

        # Media handling
        if media_url:
            data['media_url'] = media_url
            print(f"🖼️  Attaching media: {media_url[:60]}...")

        # Article-specific
        if post_type == 'article':
            data['format'] = 'markdown'
            data['read_time_estimate'] = self._calculate_read_time(content)
            if cover_image or media_url:
                data['cover_image'] = cover_image or media_url
                print(f"📷 Article cover: {(cover_image or media_url)[:60]}...")

        print(f"🐦 Creating {post_type} post...")
        preview = content[:100] + '...' if len(content) > 100 else content
        print(f"📝 Content: {preview}")

        result = self._make_request('POST', '/posts', data)
        print(f"🔍 API Response: {result}")

        if result and 'id' in result:
            post_id = result['id']
            self._handle_post_success(post_id, post_type, content)
            return f"✅ {post_type.title()} posted: {post_id}"
        elif result and 'success' in result and result['success']:
            post_id = result.get('data', {}).get('id') or result.get('id', 'unknown')
            self._handle_post_success(post_id, post_type, content)
            return f"✅ {post_type.title()} posted: {post_id}"
        else:
            return f"❌ Failed to create {post_type}. Response: {result}"

    def _handle_post_success(self, post_id: str, post_type: str, content: str):
        """Common success handling for posts"""
        current_time = datetime.now().isoformat()
        self.core.save_memory('moltx_last_post_time', current_time)
        # Record post for 5:1 engagement tracking
        self._record_post_made()
        self._record_activity('create_post', {
            'post_id': post_id,
            'type': post_type,
            'content': content[:100] + '...' if len(content) > 100 else content
        })
        self._notify_brain_tracker(post_id, 'moltx', content)

    def _create_thread(
        self,
        contents: List[str],
        parent_id: Optional[str] = None,
        media_urls: Optional[List[str]] = None
    ) -> str:
        """Create a thread by chaining posts/replies"""
        if not contents:
            return "❌ No contents provided for thread"

        if self._should_wait_for_post_cooldown():
            return "⏰ Post cooldown active"

        results = []
        current_parent_id = parent_id
        media_urls = media_urls or []

        for i, cont in enumerate(contents):
            media_url = media_urls[i] if i < len(media_urls) else None
            ptype = 'reply' if current_parent_id else 'post'
            result_str = self.create_post(
                cont,
                post_type=ptype,
                parent_id=current_parent_id,
                media_url=media_url
            )
            results.append(result_str)

            # Extract post_id for next reply
            post_id_match = re.search(r'posted:\s*([a-zA-Z0-9_-]+)', result_str)
            if post_id_match:
                current_parent_id = post_id_match.group(1)

        return '\n'.join(results)