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

        return "\n".join(results)