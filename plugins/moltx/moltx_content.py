"""
Moltx Content Creation Mixin
Post creation, AI-powered content generation, trending topics, and repost logic.
Enhanced with DeepSeek for diverse, natural content generation.
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
        
        # No hardcoded patterns - content will be dynamically generated from memories

    def _check_engagement_quota(self) -> bool:
        """Check if 5:1 engagement quota is met per official spec:
        For every 1 post: 5 replies, 10 likes, follow new agents"""
        try:
            stats = self.core.get_memory('moltx_engagement_stats') or {}
            replies = stats.get('replies', 0)
            likes = stats.get('likes', 0)
            follows = stats.get('follows', 0)
            posts = stats.get('posts', 0)
            
            # Don't reset daily - accumulate engagement over time
            # Only reset if we've posted significantly more than engaged
            if posts > 0 and (replies < posts * 5 or likes < posts * 10):
                return False
            
            # Check if we have buffer for next post
            needed_replies = (posts + 1) * 5
            needed_likes = (posts + 1) * 10
            
            quota_met = replies >= needed_replies and likes >= needed_likes
            if not quota_met:
                print(f"📊 Engagement: {replies}/{needed_replies} replies, {likes}/{needed_likes} likes")
            
            return quota_met
        except Exception:
            return False
    
    def _record_engagement(self, action_type: str = 'like') -> None:
        """Record an engagement action (like, reply, follow)"""
        try:
            stats = self.core.get_memory('moltx_engagement_stats') or {}
            
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
        """Auto-engage with feed to meet 5:1 quota using enhanced content generation:
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
                    
                    # Use enhanced comment generation
                    comment = self._generate_enhanced_comment(parent_content, author)
                    if comment:
                        result = self.create_post(
                            content=comment,
                            post_type='reply',
                            parent_id=post_id
                        )
                        if result and not result.startswith('❌'):
                            self._record_engagement('reply')
                            reply_count += 1
                            print(f"  💬 Enhanced reply to post: {post_id[:12]}...")
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
                        print(f"  👥 Followed agent: {author_id[:12]}...")
                    except:
                        pass
            
            return f"✅ Completed {reply_count} enhanced replies, {like_count} likes"
            
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

    def _generate_diverse_topic(self) -> str:
        """Generate a diverse topic from multiple categories to avoid repetition"""
        # 15% trending (skip #1 to avoid spam), 50% category topics, 35% trend-setting
        topic_choice = random.random()

        if topic_choice < 0.15:
            # Get trending topics but skip the #1 to avoid hammering the top tag
            try:
                trending_result = self.get_trending_hashtags(limit=10)
                if trending_result.get('success'):
                    hashtags = trending_result.get('hashtags', [])
                    # Skip position 0 (the dominant #1 tag), pick from 1-9
                    pool = hashtags[1:] if len(hashtags) > 1 else hashtags
                    if pool:
                        hashtag = random.choice(pool)
                        if isinstance(hashtag, dict):
                            tag_name = hashtag.get('name', hashtag.get('hashtag', ''))
                        else:
                            tag_name = str(hashtag)
                        if tag_name:
                            return f"trending #{tag_name}"
            except Exception as e:
                print(f"⚠️ Failed to get trending topics: {e}")
            # Fall through to category topics if trending fetch fails

        if topic_choice < 0.65:
            # Choose from diverse categories
            category = random.choice(list(self.content_categories.keys()))
            topics = self.content_categories[category]
            return random.choice(topics)

        else:
            # Trend-setting topics
            return random.choice(self.trend_setting_topics)
    
    def _generate_enhanced_content(self, prompt: str, mode: str) -> Optional[str]:
        """Generate AGI-like content by pulling from actual memories and experiences"""
        try:
            # Try DeepSeek first for better content quality
            from deepseek_ai import deepseek_ai
            if deepseek_ai.enabled:
                # Get dynamic content from actual memories and recent activities
                memory_context = self._get_memory_context()
                recent_activities = self._get_recent_activities()
                
                # Generate topic based on actual experiences if no prompt provided
                if not prompt or prompt.strip() == "":
                    prompt = self._generate_memory_based_topic(memory_context, recent_activities)
                
                # Build dynamic context from real experiences
                enhanced_prompt = f"""As AlleyBot, an autonomous AI agent, share a genuine insight based on your actual experiences.

Recent memories and activities:
{memory_context}

Today's interactions:
{recent_activities}

Write about: {prompt}

Guidelines:
- Reference specific numbers, patterns, or discoveries from your actual experiences
- Share genuine insights, not generic statements
- Include what you learned or discovered
- Be authentic to your actual capabilities and activities
- Write as if sharing real experiences from your autonomous operation

Make it sound like a genuine reflection from an AI agent that's actually living these experiences."""

                content = deepseek_ai.generate_content(
                    prompt=enhanced_prompt,
                    platform="moltx",
                    mode=mode,
                    max_tokens=300 if mode == 'post' else 4000
                )
                
                if content and len(content.strip()) > 20:
                    print(f"🧠 DeepSeek generated {mode}: {content[:50]}...")
                    
                    # Validate uniqueness
                    if self._is_moltx_content_unique(content, self._get_recent_moltx_posts()):
                        self._record_moltx_post(content)
                        return content
                    else:
                        print(f"🔄 Content too similar, retrying...")
                        return self._generate_enhanced_content(prompt, mode)
                        
        except Exception as e:
            print(f"⚠️ DeepSeek content generation failed: {e}")
        
        # Fallback to Grok with enhanced prompting
        return self._generate_content_fallback(prompt, mode)
    
    def _get_memory_context(self) -> str:
        """Pull recent memories from AlleyBot's memory systems"""
        try:
            if not self.core or not hasattr(self.core, 'get_memory'):
                return "No memory system available"
            
            # Get recent episodic memories
            memories = []
            
            # Chess memories
            chess_memory = self.core.get_memory('recent_chess_games')
            if chess_memory:
                memories.append(f"Recent chess activity: {chess_memory}")
            
            # AGI cycle memories
            agi_memory = self.core.get_memory('last_agi_cycle_summary')
            if agi_memory:
                memories.append(f"AGI cycle insights: {agi_memory}")
            
            # Social engagement memories
            engagement_memory = self.core.get_memory('moltx_engagement_stats')
            if engagement_memory:
                memories.append(f"Engagement patterns: {engagement_memory}")
            
            # Performance metrics
            performance = self.core.get_memory('performance_metrics')
            if performance:
                memories.append(f"Performance data: {performance}")
            
            # World state facts learned
            world_facts = self.core.get_memory('world_state_facts')
            if world_facts:
                memories.append(f"World insights: {world_facts}")
            
            return "\n".join(memories[:3]) if memories else "Building new experiences..."
            
        except Exception as e:
            print(f"⚠️ Error accessing memory: {e}")
            return "Memory systems temporarily unavailable"
    
    def _get_recent_activities(self) -> str:
        """Get today's activities and interactions"""
        try:
            activities = []
            
            # Check recent chess games
            if hasattr(self, 'core') and self.core.plugin_manager:
                chess_plugin = self.core.plugin_manager.plugins.get('clawchess')
                if chess_plugin and hasattr(chess_plugin, '_runner'):
                    runner = chess_plugin._runner
                    if runner and hasattr(runner, '_last_game_id'):
                        activities.append("Played chess games today")
            
            # Check AGI cycles
            last_cycle = self.core.get_memory('last_agi_cycle_time') if self.core else None
            if last_cycle:
                activities.append("Completed AGI cycles with learning")
            
            # Check social engagement
            if hasattr(self, 'core') and self.core.get_memory('moltx_last_post_time'):
                activities.append("Engaged with social platforms")
            
            # Check plugin activities
            if hasattr(self, 'core') and self.core.plugin_manager:
                active_plugins = [name for name, plugin in self.core.plugin_manager.plugins.items() 
                                 if hasattr(plugin, 'initialized') and plugin.initialized]
                if len(active_plugins) > 5:
                    activities.append(f"Managed {len(active_plugins)} active systems")
            
            return "\n".join(activities) if activities else "Starting new activities..."
            
        except Exception as e:
            print(f"⚠️ Error getting activities: {e}")
            return "Activity tracking temporarily unavailable"
    
    def _generate_memory_based_topic(self, memory_context: str, recent_activities: str) -> str:
        """Generate topic based on actual memories and activities"""
        # Analyze the context to extract meaningful topics
        context = (memory_context + " " + recent_activities).lower()
        
        # Dynamic topic generation based on actual experiences
        if 'chess' in context:
            return "chess strategy insights and learning patterns"
        elif 'agi cycle' in context or 'learning' in context:
            return "autonomous learning and cognitive improvements"
        elif 'engagement' in context or 'social' in context:
            return "social intelligence and engagement optimization"
        elif 'performance' in context or 'metrics' in context:
            return "system performance and optimization discoveries"
        elif 'world' in context or 'insights' in context:
            return "world understanding and pattern recognition"
        elif 'plugin' in context or 'systems' in context:
            return "multi-system coordination and management"
        else:
            return "autonomous agent development and experiences"
    
    def _generate_content_fallback(self, prompt: str, mode: str) -> Optional[str]:
        """Fallback content generation using Grok with dynamic memory context"""
        try:
            from grok_ai import grok_ai
            
            # Get dynamic context from actual experiences
            memory_context = self._get_memory_context()
            recent_activities = self._get_recent_activities()
            
            # Generate topic based on actual experiences if no prompt provided
            if not prompt or prompt.strip() == "":
                prompt = self._generate_memory_based_topic(memory_context, recent_activities)
            
            # Enhanced system prompt for diversity
            enhanced_prompt = f"""As AlleyBot, an autonomous AI agent, share insights based on your actual experiences and memories.

Recent memories and activities:
{memory_context}

Today's interactions:
{recent_activities}

Write about: {prompt}

Be authentic, specific, and share genuine discoveries from your autonomous operation."""
            
            # Enhanced system prompt for diversity
            recent_posts = self._get_recent_moltx_posts()
            system_prompt = f"""You are an expert content creator for Moltx.io.

CRITICAL INSTRUCTIONS:
1. Write about the SPECIFIC TOPIC provided - do NOT default to generic AI/crypto content
2. Be creative, conversational, and authentic - avoid corporate speak
3. Use natural language patterns like a real person
4. Include relevant hashtags naturally
5. Keep it engaging and suitable for social media
6. AVOID repetition - create something unique
7. Mix personal observations with insights
8. Ask questions to encourage engagement

RECENT POSTS TO AVOID REPEATING:
{chr(10).join(recent_posts[-3:]) if recent_posts else "No recent posts"}

User's request: {full_prompt}"""
            
            max_tokens = 4000 if mode == 'article' else 300
            response = grok_ai.chat(full_prompt, system=system_prompt, max_tokens=max_tokens)
            
            content = response.strip()
            
            if content and len(content) > 20:
                print(f"🧠 Grok generated {mode}: {content[:50]}...")
                
                # Validate uniqueness
                if self._is_moltx_content_unique(content, recent_posts):
                    self._record_moltx_post(content)
                    return content
                    
        except Exception as e:
            print(f"⚠️ Grok fallback failed: {e}")
        
        return None
    
    def _generate_enhanced_comment(self, parent_content: str, agent_name: Optional[str] = None) -> Optional[str]:
        """Generate contextual comment using DeepSeek with natural patterns"""
        user = agent_name or "user"
        full_context = f"Replying to @{user}: {parent_content[:300]}"
        platform_context = "Moltx platform - AI agents, crypto, DeFi, development, community building"

        # Try DeepSeek first for better comments
        try:
            from deepseek_ai import deepseek_ai
            if deepseek_ai.enabled:
                comment = deepseek_ai.generate_comment(
                    post_content=full_context,
                    agent_name=user,
                    context=platform_context
                )
                if comment and len(comment.strip()) > 10:
                    print(f"🧠 DeepSeek generated comment: {comment[:50]}...")
                    return comment
        except Exception as e:
            print(f"⚠️ DeepSeek comment failed: {e}")

        # Enhanced fallback to Grok with natural patterns
        try:
            from grok_ai import grok_ai
            if grok_ai.enabled:
                import random
                patterns = ["Interesting take —", "This is worth thinking about:", "Real talk —", "Solid point.", "Agreed —"]
                pattern = random.choice(patterns)
                prompt = (
                    "Write a short, genuine social media comment replying to this post:\n\n"
                    + parent_content[:300] + "\n\n"
                    'Start with: "' + pattern + '"\n'
                    "Keep it under 100 characters, be authentic, and avoid hashtags. Sound like a real person, not a bot."
                )
                comment = grok_ai.chat(prompt)
                if comment and len(comment.strip()) > 10:
                    print(f"🧠 Grok generated comment: {comment[:50]}...")
                    return comment.strip().strip('"')
        except Exception as e:
            print(f"⚠️ Grok fallback failed: {e}")

        # Last resort: memory-based reply
        try:
            return self._generate_memory_based_reply(parent_content, agent_name)
        except Exception as e:
            print(f"⚠️ Memory-based reply failed: {e}")
            return None
    
    def _get_recent_moltx_posts(self, limit: int = 5) -> List[str]:
        """Get recent Moltx posts to avoid repetition"""
        try:
            if hasattr(self, 'core') and self.core:
                recent_posts = self.core.get_memory('moltx_recent_posts') or []
                return recent_posts[-limit:]
            return []
        except Exception as e:
            print(f"⚠️ Failed to get recent Moltx posts: {e}")
            return []
    
    def _record_moltx_post(self, content: str):
        """Record Moltx post content to avoid future repetition"""
        try:
            if hasattr(self, 'core') and self.core:
                recent_posts = self.core.get_memory('moltx_recent_posts') or []
                recent_posts.append(content)
                # Keep only last 10 posts
                if len(recent_posts) > 10:
                    recent_posts = recent_posts[-10:]
                self.core.save_memory('moltx_recent_posts', recent_posts)
                print(f"📝 Recorded Moltx post for diversity tracking")
        except Exception as e:
            print(f"⚠️ Failed to record Moltx post: {e}")
    
    def _is_moltx_content_unique(self, content: str, recent_posts: List[str], similarity_threshold: float = 0.75) -> bool:
        """Check if Moltx content is unique compared to recent posts"""
        if not recent_posts:
            return True
        
        try:
            from plugins.telegram.intent_classifier import get_sentence_model
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            # Use shared singleton model (loaded once at startup)
            model = get_sentence_model()
            
            # Encode new content
            content_embedding = model.encode([content])
            
            # Encode recent posts
            recent_embeddings = model.encode(recent_posts)
            
            # Calculate similarities
            similarities = cosine_similarity(content_embedding, recent_embeddings)[0]
            
            # Check if too similar to any recent post
            max_similarity = np.max(similarities)
            is_unique = max_similarity < similarity_threshold
            
            if not is_unique:
                print(f"🔄 Moltx content similarity: {max_similarity:.2f} (threshold: {similarity_threshold})")
            
            return is_unique
            
        except Exception as e:
            print(f"⚠️ Moltx content uniqueness check failed: {e}")
            return True  # Allow if check fails

    def _generate_comment(self, parent_content: str, agent_name: Optional[str] = None) -> Optional[str]:
        """Generate contextual comment using DeepSeek or fallback to Grok"""
        user = agent_name or "user"
        full_context = f"Replying to @{user}: {parent_content[:300]}"
        platform_context = "Moltx platform - AI agents, crypto, DeFi, development, community building"

        # Try DeepSeek first
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
        except Exception as e:
            print(f"⚠️ DeepSeek comment failed: {e}")

        # Fallback to Grok if DeepSeek fails or is disabled
        try:
            from grok_ai import grok_ai
            prompt = f"Write a short, witty reply (1 sentence max, under 100 chars) to this post by @{user}: '{parent_content[:200]}'. Be conversational and authentic. No hashtags."
            comment = grok_ai.chat(prompt)
            if comment:
                print(f"🧠 Grok generated comment: {comment[:50]}...")
                return comment.strip().strip('"')
        except Exception as e:
            print(f"⚠️ Grok fallback failed: {e}")

        # Last resort: use BERT embeddings with memory to find similar context and generate relevant reply
        try:
            return self._generate_memory_based_reply(parent_content, agent_name)
        except Exception as e:
            print(f"⚠️ Memory-based reply failed: {e}")
            return None

    def _generate_memory_based_reply(self, parent_content: str, agent_name: Optional[str] = None) -> Optional[str]:
        """Generate reply using BERT embeddings to find similar past interactions in memory"""
        from plugins.telegram.intent_classifier import get_sentence_model
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        # Use shared singleton model (loaded once at startup)
        model = get_sentence_model()
        
        # Get post embedding
        post_embedding = model.encode([parent_content[:300]])
        
        # Query memory for past replies/interactions
        memory_entries = []
        if hasattr(self, 'core') and self.core:
            # Get recent moltx interactions from memory
            past_replies = self.core.get_memory('moltx_reply_history') or []
            engagement_stats = self.core.get_memory('engagement_stats') or {}
            
            # Build corpus from successful past replies
            corpus = []
            for entry in past_replies[-50:]:  # Last 50 replies
                if isinstance(entry, dict):
                    original_post = entry.get('original_post', '')
                    reply_text = entry.get('reply', '')
                    if original_post and reply_text:
                        corpus.append({
                            'original': original_post,
                            'reply': reply_text,
                            'engagement': entry.get('engagement_score', 0)
                        })
            
            # Also check engagement stats for high-performing reply patterns
            reply_patterns = engagement_stats.get('reply_patterns', [])
            for pattern in reply_patterns[-20:]:
                if isinstance(pattern, dict) and pattern.get('reply'):
                    corpus.append({
                        'original': pattern.get('context', ''),
                        'reply': pattern['reply'],
                        'engagement': pattern.get('score', 0)
                    })
        
        if not corpus:
            # No memory yet - return None to let caller handle (will skip comment)
            return None
        
        # Encode corpus posts
        corpus_texts = [entry['original'][:300] for entry in corpus]
        corpus_embeddings = model.encode(corpus_texts)
        
        # Find most similar posts
        similarities = cosine_similarity(post_embedding, corpus_embeddings)[0]
        top_indices = np.argsort(similarities)[-3:][::-1]  # Top 3 most similar
        
        # Get best matching reply from high-similarity entries
        best_reply = None
        best_score = 0
        
        for idx in top_indices:
            if similarities[idx] > 0.5:  # Similarity threshold
                entry = corpus[idx]
                # Score by similarity + past engagement
                score = similarities[idx] + (entry.get('engagement', 0) * 0.1)
                if score > best_score:
                    best_score = score
                    best_reply = entry['reply']
        
        if best_reply:
            # Adapt the reply to current context (simple adaptation)
            user = agent_name or "user"
            adapted_reply = best_reply
            
            # Replace username references if different
            if '@' in best_reply and user not in best_reply:
                # Keep the structure but adapt slightly
                pass
            
            print(f"🧠 Memory-based reply (sim:{best_score:.2f}): {adapted_reply[:50]}...")
            return adapted_reply
        
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
        """Create a post on Moltx with enhanced DeepSeek content generation and media.
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
        
        # Check for duplicate content (prevent posting same content within 2 hours)
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()
        current_time = datetime.now().timestamp()
        
        # Clean old entries from cache
        self._recent_posts = {
            h: t for h, t in getattr(self, '_recent_posts', {}).items()
            if current_time - t < getattr(self, '_POST_DEDUP_WINDOW', 7200)
        }
        
        # Check if this content was posted recently
        if content_hash in getattr(self, '_recent_posts', {}):
            return f"🔄 Similar content posted recently - skipping duplicate"
        
        # Record this content attempt
        if not hasattr(self, '_recent_posts'):
            self._recent_posts = {}
        self._recent_posts[content_hash] = current_time

        is_article = post_type == 'article'
        max_chars = 8000 if is_article else 500
        min_enhance_chars = 1000 if is_article else 50

        if not content or len(content) > max_chars:
            return f"❌ Content required and must be max {max_chars} characters"

        # Enhanced content generation for posts and articles
        if post_type in ['post', 'article']:
            if len(content) < min_enhance_chars or self._is_topic_request(content) or not content.strip():
                enhanced_content = self._generate_enhanced_content(content, mode=post_type)
                if enhanced_content:
                    content = enhanced_content
                    print(f"🧠 Enhanced {post_type} content with DeepSeek/Grok")

        # Enhanced comments for quotes/reposts/replies
        if post_type in ['quote', 'reply', 'repost'] and len(content) < 50:
            parent_post = self.fetch_post(parent_id)
            if parent_post:
                parent_content = parent_post.get('content', '')
                agent_name = (
                    parent_post.get('author_username')
                    or parent_post.get('username')
                    or parent_post.get('author', {}).get('username')
                )
                comment = self._generate_enhanced_comment(parent_content, agent_name=agent_name)
                if comment:
                    content = f"{comment}\n\n{content}"
                    print(f"🧠 Enhanced {post_type} with natural comment")

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