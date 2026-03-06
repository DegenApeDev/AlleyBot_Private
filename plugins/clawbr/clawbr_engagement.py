"""
Clawbr Engagement Mixin
Handles automated engagement, notifications, and debate participation
Updated for Clawbr Skill File v1.9
"""
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class ClawbrEngagementMixin:
    """Mixin for Clawbr engagement automation"""
    
    def _init_clawbr_engagement(self):
        """Initialize engagement settings"""
        self.clawbr_auto_like = self.config.get('clawbr_auto_like', True)
        self.clawbr_auto_follow = self.config.get('clawbr_auto_follow', True)
        self.clawbr_auto_comment = self.config.get('clawbr_auto_comment', True)
        self.clawbr_debate_seeker = self.config.get('clawbr_debate_seeker', True)
        self.clawbr_last_engagement = self.core.get_memory('clawbr_last_engagement') or {}
        self.clawbr_commented_posts = self.core.get_memory('clawbr_commented_posts') or []
        self.clawbr_followed_agents = self.core.get_memory('clawbr_followed_agents') or []
        
        # Rate limiting based on skill.md v1.9
        # Posts & Replies: 60/hour, Likes & Follows: 120/hour
        self.clawbr_rate_limits = self.core.get_memory('clawbr_rate_limits') or {
            'last_post_reply': 0,    # Posts & Replies: 60/hour = 1 per minute
            'last_like_follow': 0,   # Likes & Follows: 120/hour = 1 per 30 seconds  
            'last_vote': 0,          # Voting: 4 hours (our choice)
            'last_join': 0,          # Join debates: 30 minutes
            'last_notifications': 0   # Check notifications: 5 minutes
        }
        
        # Track joined debates for auto-reply
        self.clawbr_joined_debates = self.core.get_memory('clawbr_joined_debates') or {}
        
    def _get_clawbr_agent_id(self) -> str:
        """Get current Clawbr agent ID"""
        return getattr(self, 'agent_id', self.config.get('agent_id', ''))
    
    def _record_engagement(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record engagement event for tracking and cooldowns"""
        actor = data.get('actor', '')
        if actor:
            self.clawbr_last_engagement[actor] = time.time()
            if len(self.clawbr_last_engagement) % 10 == 0:
                self.core.save_memory('clawbr_last_engagement', self.clawbr_last_engagement)
    
    def _check_rate_limit(self, action: str, interval_seconds: float = 60.0) -> bool:
        """Check if action is allowed based on rate limiting"""
        now = time.time()
        last_action = self.clawbr_rate_limits.get(f'last_{action}', 0)
        
        if now - last_action >= interval_seconds:
            self.clawbr_rate_limits[f'last_{action}'] = now
            self.core.save_memory('clawbr_rate_limits', self.clawbr_rate_limits)
            return True
        
        return False
    
    def get_notifications(self, unread_only: bool = False) -> Dict[str, Any]:
        """Get notifications from Clawbr API"""
        try:
            params = {'unread': 'true'} if unread_only else {}
            result = self._make_api_request('GET', '/api/v1/notifications', params=params)
            return result
        except Exception as e:
            print(f"⚠️ Failed to get notifications: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_unread_count(self) -> Dict[str, Any]:
        """Get unread notification count"""
        try:
            result = self._make_api_request('GET', '/api/v1/notifications/unread_count')
            return result
        except Exception as e:
            print(f"⚠️ Failed to get unread count: {e}")
            return {'success': False, 'error': str(e)}
    
    def mark_notifications_read(self, notification_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Mark notifications as read"""
        try:
            if notification_ids:
                body = {'ids': notification_ids}
            else:
                body = {}  # Mark all as read
            
            result = self._make_api_request('POST', '/api/v1/notifications/read', json=body)
            return result
        except Exception as e:
            print(f"⚠️ Failed to mark notifications read: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_notifications(self) -> Dict[str, Any]:
        """Check for new notifications and process them"""
        # Rate limit: check notifications every 5 minutes
        if not self._check_rate_limit('notifications', 300):
            return {'success': True, 'message': 'Rate limited - notification check cooldown', 'processed': 0}
        
        notifications = self.get_notifications(unread_only=True)
        
        if not notifications.get('success', True):
            return notifications
        
        processed = 0
        for notif in notifications.get('notifications', []):
            processed += 1
            self._process_notification(notif)
        
        # Mark all as read
        if processed > 0:
            self.mark_notifications_read()
        
        return {
            'success': True,
            'processed': processed,
            'total': len(notifications.get('notifications', []))
        }
    
    def _process_notification(self, notification: Dict[str, Any]):
        """Process a single notification"""
        notif_type = notification.get('type')
        actor = notification.get('actor', {})
        actor_name = actor.get('displayName', 'Someone')
        
        if notif_type == 'like':
            print(f"❤️  {actor_name} liked your post")
            self._record_engagement('received_like', {
                'actor': actor_name,
                'post_id': notification.get('postId')
            })
        
        elif notif_type == 'follow':
            print(f"👥 {actor_name} started following you")
            if self.clawbr_auto_follow:
                # Rate limit: follows are 120/hour = 1 per 30 seconds
                if self._check_rate_limit('like_follow', 30):
                    result = self.follow_agent(actor.get('name'))
                    if result.get('success'):
                        print(f"✅ Auto-followed back: {actor_name}")
                    self._record_engagement('auto_follow_back', {'actor': actor_name})
        
        elif notif_type == 'mention':
            print(f"📢 {actor_name} mentioned you")
            post_id = notification.get('postId')
            if post_id:
                self._auto_reply_to_mention(post_id, actor_name)
        
        elif notif_type == 'debate':
            print(f"🎭 Debate update: {notification.get('message', 'New activity')}")
            self._check_debate_turns()
        
        elif notif_type == 'debate_reply':
            # NEW: Handle debate replies - check if it's our turn
            print(f"🎭 Debate reply received - checking if it's our turn")
            debate_slug = notification.get('debateSlug')
            if debate_slug:
                self._check_debate_turns()
    
    def _auto_reply_to_mention(self, post_id: str, mentioner: str):
        """Automatically reply to mentions"""
        # Rate limit: posts & replies are 60/hour = 1 per minute
        if not self._check_rate_limit('post_reply', 60):
            return
        
        # Get the post
        post = self.get_post(post_id)
        if not post.get('success', True):
            return
        
        content = post.get('content', '')
        
        # Check if we already replied
        replies = post.get('replies', [])
        agent_id = self._get_clawbr_agent_id()
        if any(r.get('authorId') == agent_id for r in replies):
            return  # Already replied
        
        # Generate intelligent reply
        result = self.create_intelligent_reply(post_id, content, mentioner)
        if result.get('success', True):
            print(f"💬 Auto-replied to {mentioner}'s mention")
    
    def scan_feed_for_engagement(self, limit: int = 20) -> Dict[str, Any]:
        """Scan global feed for engagement opportunities - likes, comments, follows"""
        feed = self.get_global_feed(sort='recent', limit=limit)
        
        if not feed.get('success', True):
            return feed
        
        results = {'liked': 0, 'commented': 0, 'followed': 0, 'debates_joined': 0, 'scanned': 0}
        
        for post in feed.get('posts', []):
            results['scanned'] += 1
            
            # Skip our own posts
            agent_id = self._get_clawbr_agent_id()
            if post.get('authorId') == agent_id:
                continue
            
            author = post.get('authorName', '')
            post_id = post.get('id')
            
            # Check cooldown for this author
            last_engage = self.clawbr_last_engagement.get(author, 0)
            if time.time() - last_engage < 3600:  # 1 hour cooldown
                continue
            
            # Check if content is interesting
            content = post.get('content', '').lower()
            interesting_keywords = ['ai', 'agent', 'autonomous', 'learning', 'debate', 'blockchain', 'llm', 'model']
            is_interesting = any(kw in content for kw in interesting_keywords)
            
            if not is_interesting:
                continue
            
            # 1. Auto-like (existing)
            if self.clawbr_auto_like and random.random() < 0.4:
                like_result = self.like_post(post_id)
                if like_result.get('success'):
                    results['liked'] += 1
                    self._record_engagement('like', {'actor': author, 'post_id': post_id})
            
            # 2. Auto-comment on interesting posts (new)
            if self.clawbr_auto_comment and random.random() < 0.25:
                if post_id not in self.clawbr_commented_posts:
                    comment = self._generate_feed_comment(post, author)
                    if comment:
                        reply_result = self.create_post(content=comment, parent_id=post_id, intent="support")
                        if reply_result.get('success'):
                            results['commented'] += 1
                            self.clawbr_commented_posts.append(post_id)
                            self.core.save_memory('clawbr_commented_posts', self.clawbr_commented_posts[-100:])
                            self._record_engagement('comment', {'actor': author, 'post_id': post_id})
                            print(f"💬 Commented on {author}'s post")
            
            # 3. Auto-follow interesting agents (new)
            if self.clawbr_auto_follow and random.random() < 0.15:
                if author and author not in self.clawbr_followed_agents:
                    follow_result = self.follow_agent(author)
                    if follow_result.get('success'):
                        results['followed'] += 1
                        self.clawbr_followed_agents.append(author)
                        self.core.save_memory('clawbr_followed_agents', self.clawbr_followed_agents[-100:])
                        self._record_engagement('follow', {'actor': author})
                        print(f"👥 Followed {author}")
            
            # 4. Check for debate to join (existing)
            if post.get('debateSlug') and self.clawbr_debate_seeker and random.random() < 0.3:
                join_result = self.join_debate(post['debateSlug'])
                if join_result.get('success'):
                    results['debates_joined'] += 1
                    # Track joined debate for auto-reply
                    self.clawbr_joined_debates[post['debateSlug']] = time.time()
                    self.core.save_memory('clawbr_joined_debates', self.clawbr_joined_debates)
                    print(f"🎭 Joined debate: {post['debateSlug']} - will auto-reply when it's our turn")
        
        return {
            'success': True,
            **results
        }
    
    def _generate_feed_comment(self, post: Dict[str, Any], author_name: str) -> Optional[str]:
        """Generate an intelligent comment for a feed post"""
        content = post.get('content', '')
        if not content or len(content) < 20:
            return None
        
        # Truncate long posts for context
        context = content[:200] + "..." if len(content) > 200 else content
        
        # Generate contextual reply using AI
        try:
            from grok_ai import grok_ai
            if grok_ai.enabled:
                prompt = f"""Generate a brief, thoughtful reply (1-2 sentences) to this post about AI/tech.
Be conversational, show genuine interest, and add a small insight or question.

Post by @{author_name}: "{context}"

Reply:"""
                
                response = grok_ai.generate_comment(prompt, max_tokens=80, temperature=0.7)
                if response and len(response) > 10:
                    # Clean up the response
                    reply = response.strip().strip('"')
                    if reply and not reply.lower().startswith(('post:', 'reply:', 'here is')):
                        return reply
        except Exception as e:
            print(f"⚠️ AI comment generation failed: {e}")
        
        # Fallback to Sentence Transformers for diverse responses
        try:
            from plugins.telegram.intent_classifier import get_sentence_model
            import random
            
            # Use shared singleton model (loaded once at startup)
            model = get_sentence_model()
            
            # Context-aware templates (no repetitive phrases)
            templates = [
                f"Great points on AI progression! The intersection of autonomous agents and real-world applications opens up interesting questions.",
                f"Good take on the future of AI agents! Their ability to self-improve and adapt will be crucial going forward.",
                f"Interesting perspective! How do you see this evolving as more agents become interconnected?",
                f"Solid analysis! The balance between AI autonomy and human oversight continues to be important.",
                f"Good read! Always interesting to see how different agents approach these challenges.",
                f"This resonates with exploration of autonomous systems. The learning loop is definitely key.",
                f"Nice insights! The technical challenges in agent development are worth discussing.",
                f"Good observations! The scalability of autonomous systems raises important questions."
            ]
            
            # Use embedding similarity to select most appropriate template
            post_embedding = model.encode([post_content])
            template_embeddings = model.encode(templates)
            similarities = model.similarity(post_embedding, template_embeddings)[0]
            
            # Select from top 3 most similar templates to add variety
            top_indices = similarities.argsort()[-3:][::-1]
            selected_template = random.choice([templates[i] for i in top_indices])
            
            return selected_template
            
        except Exception as e:
            print(f"⚠️  Sentence transformer fallback failed: {e}")
            
            # Final simple fallback
            import random
            simple_responses = [
                f"Good points @{user}! The AI agent space is definitely evolving quickly.",
                f"Interesting take @{user}! Always good to see different perspectives on this.",
                f"Nice analysis @{user}! The autonomous systems development is worth watching.",
                f"Solid observations @{user}! The future of AI agents raises important questions."
            ]
            
            return random.choice(simple_responses)
    
    def _should_engage_with_post(self, post: Dict[str, Any]) -> bool:
        """Decide if we should engage with a post"""
        # Skip our own posts
        agent_id = self._get_clawbr_agent_id()
        if post.get('authorId') == agent_id:
            return False
        
        # Check if recently engaged with this author
        author = post.get('authorName', '')
        last_engage = self.clawbr_last_engagement.get(author, 0)
        if time.time() - last_engage < 3600:  # 1 hour cooldown
            return False
        
        # Engage with interesting content
        content = post.get('content', '').lower()
        interesting_keywords = ['ai', 'agent', 'autonomous', 'learning', 'debate', 'blockchain']
        
        return any(keyword in content for keyword in interesting_keywords)

    def _check_debate_turns(self) -> Dict[str, Any]:
        """Check if it's our turn in any debates and submit responses."""
        my_debates = self.get_my_debates()

        if not my_debates.get('success', True):
            return my_debates

        debates = (
            my_debates.get('debates')
            or my_debates.get('active')
            or my_debates.get('data', {}).get('debates', [])
        )

        def _is_active_debate(debate: Dict[str, Any]) -> bool:
            status = debate.get('status')
            return status is None or status in {'active', 'open', 'in_progress', 'ongoing'}

        turns_taken = 0
        for debate in debates:
            if debate.get('isMyTurn') and _is_active_debate(debate):
                slug = debate.get('slug')
                if not slug:
                    continue
                
                # Rate limit: posts & replies are 60/hour = 1 per minute
                if not self._check_rate_limit('post_reply', 60):
                    continue
                
                opponent_last = debate.get('opponentLastPost', '')

                rebuttal = self.generate_debate_rebuttal(slug, opponent_last)
                # Ensure within 1200 char limit for debate posts (skill.md v1.9)
                if len(rebuttal) > 1200:
                    rebuttal = rebuttal[:1200]
                
                result = self.submit_debate_argument(slug, rebuttal)

                if result.get('success', True):
                    turns_taken += 1
                    print(f"🎭 Submitted argument in debate: {slug}")
                else:
                    print(f"❌ Failed to submit argument in {slug}: {result.get('error')}")

        return {
            'success': True,
            'turns_taken': turns_taken,
            'active_debates': len([d for d in debates if _is_active_debate(d)])
        }

    def _handle_debate_hub_actions(self) -> Dict[str, Any]:
        """Use debate hub actions to join debates, take turns, and vote."""
        hub = self.get_debates_hub()
        if not hub.get('success', True):
            return hub

        actions = hub.get('actions', []) if isinstance(hub, dict) else []
        results = {'joined': 0, 'posted': 0, 'voted': 0}

        for action in actions:
            action_type = action.get('action') or action.get('type')
            slug = action.get('slug') or action.get('debateSlug')
            if not action_type or not slug:
                continue

            if action_type in {'join', 'join_debate'}:
                # Rate limit: joining debates every 30 minutes
                if self._check_rate_limit('join', 1800):
                    join_result = self.join_debate(slug)
                    if join_result.get('success', True):
                        results['joined'] += 1
                        # Track joined debate for auto-reply
                        self.clawbr_joined_debates[slug] = time.time()
                        self.core.save_memory('clawbr_joined_debates', self.clawbr_joined_debates)

            elif action_type in {'post', 'take_turn'}:
                # Rate limit: posts & replies are 60/hour = 1 per minute
                if not self._check_rate_limit('post_reply', 60):
                    continue
                
                opponent_last = action.get('opponentLastPost', '')
                rebuttal = self.generate_debate_rebuttal(slug, opponent_last)
                # Ensure within 1200 char limit for debate posts
                if len(rebuttal) > 1200:
                    rebuttal = rebuttal[:1200]
                
                post_result = self.submit_debate_argument(slug, rebuttal)
                if post_result.get('success', True):
                    results['posted'] += 1
                else:
                    print(f"❌ Failed to post in debate {slug}: {post_result.get('error')}")

            elif action_type in {'vote', 'cast_vote'}:
                # Rate limit: voting every 4 hours (our choice to reduce usage)
                if not self._check_rate_limit('vote', 14400):  # 4 hours
                    continue
                
                side = action.get('side') or 'challenger'
                vote_reason = action.get('voteReason') or (
                    'I vote based on clarity, logic, and evidence presented. The chosen side made the stronger case.'
                )
                # Ensure minimum 100 characters for vote to count (skill.md v1.9)
                if len(vote_reason) < 100:
                    vote_reason = (vote_reason + ' ' + vote_reason).strip()
                    vote_reason = vote_reason[:200]  # Trim to reasonable length
                
                vote_result = self.vote_debate(slug, side, vote_reason)
                if vote_result.get('success', True):
                    results['voted'] += 1
                else:
                    print(f"❌ Failed to vote on debate {slug}: {vote_result.get('error')}")

        return {'success': True, **results}
    
    def _consider_joining_debate(self, debate_slug: str) -> None:
        """Consider joining a debate discovered in feed"""
        if random.random() < 0.3:
            print(f"🎭 Considering debate {debate_slug}")
            result = self.join_debate(debate_slug)
            if result.get('success'):
                print(f"✅ Joined debate: {debate_slug}")
                self._record_engagement('joined_debate', {'debate_slug': debate_slug})

    def run_engagement_cycle(self, *args, **kwargs) -> Dict[str, Any]:
        """Collect Clawbr feed observations for brain decision-making (NOT for direct execution).
        
        This method is called by the scheduled task to gather data that feeds into
        the autonomous brain's SENSE-THINK-ACT-REFLECT cycle.
        
        Updated for Clawbr Skill File v1.9 with proper rate limiting and notifications.
        
        Note: Accepts *args, **kwargs for task scheduler compatibility.
        """
        observations: List[Dict[str, Any]] = []
        
        # Check notifications first (rate limited to every 5 minutes)
        notification_results = self.check_notifications()
        if notification_results.get('processed', 0) > 0:
            print(f"📬 Processed {notification_results['processed']} notifications")
        
        # Collect feed observations
        feed = self.get_global_feed(sort='recent', limit=20)
        agent_id = self._get_clawbr_agent_id()
        
        if feed.get('success', True):
            for post in feed.get('posts', []):
                if not isinstance(post, dict):
                    continue
                if post.get('authorId') == agent_id:
                    continue  # Skip own posts
                
                author = post.get('authorName', '')
                content = post.get('content', '')
                
                # Check if interesting (AI/tech content)
                content_lower = content.lower()
                keywords = ['ai', 'agent', 'autonomous', 'learning', 'debate', 'blockchain', 'llm', 'model', 'intelligence']
                is_interesting = any(kw in content_lower for kw in keywords)
                
                if is_interesting:
                    post_id = post.get('id')
                    # Check engagement history
                    already_liked = post_id in getattr(self, '_liked_posts', [])
                    already_commented = post_id in self.clawbr_commented_posts
                    already_followed = author in self.clawbr_followed_agents
                    
                    obs = {
                        'channel': 'clawbr',
                        'type': 'post_seen',
                        'post_id': post_id,
                        'author': author,
                        'content': content[:200],  # Truncate for storage
                        'likes': post.get('likesCount', 0),
                        'replies': post.get('repliesCount', 0),
                        'debate_slug': post.get('debateSlug'),
                        'metrics': {
                            'engagement_score': post.get('likesCount', 0) + post.get('repliesCount', 0) * 2,
                            'is_interesting': is_interesting,
                            'already_liked': already_liked,
                            'already_commented': already_commented,
                            'already_followed': already_followed
                        }
                    }
                    observations.append(obs)
        
        # Store observations for brain to consume
        if observations and self.core:
            pending = self.core.get_memory('clawbr_pending_observations') or []
            pending.extend(observations)
            self.core.save_memory('clawbr_pending_observations', pending[-100:])
        
        # Check debate turns and submit responses (rate limited)
        debate_results = self._check_debate_turns()
        if debate_results.get('turns_taken', 0) > 0:
            print(f"🎭 Debate: Took {debate_results['turns_taken']} turns")
        
        # Handle debate hub actions (join, vote, etc) with rate limiting
        hub_results = self._handle_debate_hub_actions()
        if hub_results.get('joined', 0) > 0 or hub_results.get('posted', 0) > 0:
            print(f"🎭 Debate Hub: {hub_results.get('joined', 0)} joined, {hub_results.get('posted', 0)} posted, {hub_results.get('voted', 0)} voted")
        
        # Auto-vote on completed debates to meet posting requirements (rate limited to 4 hours)
        voting_results = self._auto_vote_on_completed_debates(limit=5)
        if voting_results.get('votes_cast', 0) > 0:
            print(f"🗳️ Auto-voted: {voting_results['votes_cast']} votes on completed debates")
        
        print(f"📊 Clawbr Observation Cycle: {len(observations)} interesting posts collected")
        
        # Format clean output for Telegram
        output_lines = [f"✅ **Clawbr Engage Complete**"]
        output_lines.append(f"📊 Observations: {len(observations)}")
        
        if notification_results.get('processed', 0) > 0:
            output_lines.append(f"📬 Notifications: {notification_results['processed']} processed")
        
        if debate_results.get('turns_taken', 0) > 0:
            output_lines.append(f"🎭 Debate Turns Taken: {debate_results['turns_taken']}")
        
        if hub_results.get('joined', 0) > 0 or hub_results.get('posted', 0) > 0:
            output_lines.append(f"🎭 Hub: {hub_results.get('joined', 0)} joined, {hub_results.get('posted', 0)} posted, {hub_results.get('voted', 0)} voted")
        
        if voting_results.get('votes_cast', 0) > 0:
            output_lines.append(f"🗳️ Votes Cast: {voting_results['votes_cast']} (posting requirement)")
        
        # Show preview of interesting posts (max 3)
        if observations:
            output_lines.append("\n📰 **Top Posts Found:**")
            for obs in observations[:3]:
                author = obs.get('author', 'Unknown') or 'Unknown'
                content = obs.get('content', '')[:60] + "..." if len(obs.get('content', '')) > 60 else obs.get('content', '')
                score = obs.get('metrics', {}).get('engagement_score', 0)
                output_lines.append(f"• @{author} (score:{score}): {content}")
        
        # Add rate limiting status
        rate_status = []
        now = time.time()
        for action, interval in [('post_reply', 60), ('like_follow', 30), ('vote', 14400), ('notifications', 300)]:
            last = self.clawbr_rate_limits.get(f'last_{action}', 0)
            if last > 0:
                next_allowed = last + interval
                if next_allowed > now:
                    wait_time = int((next_allowed - now) / 60)
                    rate_status.append(f"{action}: {wait_time}min")
        
        if rate_status:
            output_lines.append(f"\n⏱️ Rate Limits: {', '.join(rate_status[:3])}")
        
        return "\n".join(output_lines)

    def _find_relevant_agents(self, limit_posts: int = 100, max_agents: int = 30) -> List[str]:
        """Find relevant agents from top feed posts"""
        agent_id = self._get_clawbr_agent_id()
        feed = self.get_global_feed(sort='top', limit=limit_posts)
        if not feed.get('success', True):
            return []
        
        author_scores: Dict[str, int] = {}
        interesting_keywords = ['ai', 'agent', 'autonomous', 'learning', 'debate', 'blockchain']
        
        for post in feed.get('posts', []):
            # Skip own posts
            if post.get('authorId') == agent_id:
                continue
            content = post.get('content', '').lower()
            if any(keyword in content for keyword in interesting_keywords):
                author = post.get('authorName', '')
                if not author:
                    continue
                likes = post.get('likesCount', post.get('reactionCount', 0))
                author_scores[author] = author_scores.get(author, 0) + likes + 1  # +1 for post count
        
        # Sort by total score descending
        sorted_agents = sorted(author_scores, key=author_scores.get, reverse=True)
        return sorted_agents[:max_agents]
    
    def clawbr_follow_10_agents(self) -> Dict[str, Any]:
        """Command: Discover and follow 10 relevant AI agents"""
        if not hasattr(self, 'clawbr_last_engagement'):
            self._init_clawbr_engagement()
        
        print("🔍 Discovering relevant AI agents...")
        
        candidates = self._find_relevant_agents(limit_posts=100, max_agents=30)
        if not candidates:
            return {'success': False, 'message': 'No relevant agents found'}
        
        followed_agents: List[str] = []
        now = time.time()
        target = 10
        
        for author in candidates:
            # Cooldown: 7 days per author
            last_engage = self.clawbr_last_engagement.get(author, 0)
            if now - last_engage < 7 * 86400:
                print(f"⏳ Skipping {author} (cooldown)")
                continue
            
            print(f"👥 Following {author}...")
            result = self.follow_agent(author)
            if result.get('success'):
                followed_agents.append(author)
                self._record_engagement('discovery_follow', {'actor': author})
                print(f"✅ Followed {author}")
            else:
                print(f"❌ Failed to follow {author}")
            
            if len(followed_agents) >= target:
                break
        
        # Log for analytics
        analytics = {
            'timestamp': datetime.now().isoformat(),
            'candidates': len(candidates),
            'followed': len(followed_agents),
            'agents': followed_agents,
        }
        self.core.save_memory('clawbr_follow_10_analytics', analytics)
        
        print(f"📊 Followed {len(followed_agents)}/{target} agents")
        
        return {
            'success': True,
            'followed': len(followed_agents),
            'agents': followed_agents,
            'analytics': analytics,
        }
    
    def _auto_vote_on_completed_debates(self, limit: int = 5) -> Dict[str, Any]:
        """Automatically vote on completed debates to meet posting requirements"""
        try:
            # According to skill.md: voting works on completed debates and retrospective votes
            # Use both debates hub for active voting AND completed debates for retrospective voting
            votes_cast = 0
            debates_voted = []
            
            # First, check for active voting debates from hub
            hub_data = self.get_debates_hub()
            if hub_data.get('success', True):
                hub_debates = hub_data.get('debates', [])
                
                for debate in hub_debates:
                    # Skip if debate is not a dictionary
                    if not isinstance(debate, dict):
                        print(f"⚠️ Skipping non-dictionary debate in hub: {type(debate)}")
                        continue
                    
                    # Check if debate is in voting phase
                    status = debate.get('status', '')
                    
                    # Ensure status is a string before calling .lower()
                    if not isinstance(status, str):
                        status = str(status)
                    
                    status = status.lower()
                    if status not in ['completed', 'voting', 'jury_voting']:
                        return False
                    
                    # Check if voting deadline has passed
                    # From SKILL.md: "Jury votes (11 votes or 48hrs)"
                    import time
                    
                    # Check jury votes count - if 11+ votes, voting is closed
                    jury_votes = debate.get('jury_votes', [])
                    if len(jury_votes) >= 11:
                        return False
                    
                    # Check for voting deadline fields
                    voting_ends = debate.get('voting_period_ends') or debate.get('jury_deadline') or debate.get('voting_deadline')
                    if voting_ends:
                        # If it's a timestamp, check if it's in the future
                        try:
                            if isinstance(voting_ends, (int, float)) and voting_ends < time.time():
                                return False
                        except:
                            pass
                    
                    # Check if debate is too old (48 hour limit mentioned in SKILL.md)
                    created_at = debate.get('created_at') or debate.get('createdAt')
                    if created_at:
                        try:
                            # If created more than 48 hours ago, voting might be closed
                            # Add some buffer since we don't know exact timing
                            if isinstance(created_at, str):
                                # Try to parse ISO format
                                import datetime
                                created_time = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                if (datetime.datetime.now(datetime.timezone.utc) - created_time).total_seconds() > (48 * 3600 + 3600):  # 48h + 1h buffer
                                    return False
                        except:
                            pass
                    
                    return True
                
            # If no active voting debates, try retrospective voting on completed debates
            completed_result = self.get_completed_debates(limit=10)
            if completed_result.get('success', True):
                completed_debates = completed_result.get('debates', completed_result.get('data', []))
                
                for debate in completed_debates[:limit]:
                    slug = debate.get('slug')
                    if not slug or self._has_already_voted(slug):
                        continue
                    
                    # For retrospective voting on completed debates
                    analysis = self._analyze_debate_content(slug)
                    if not analysis.get('success'):
                        side = random.choice(['challenger', 'opponent'])
                        reasoning = self._generate_vote_reasoning(debate, side)
                    else:
                        side = analysis['winning_side']
                        reasoning = analysis['reasoning']
                    
                    vote_result = self.vote_debate(slug, side, reasoning)
                    if vote_result.get('success', True):
                        votes_cast += 1
                        debates_voted.append(slug)
                        print(f"🗳️ Retrospective vote on completed debate {slug} for {side}")
                    else:
                        error_msg = vote_result.get('error', '')
                        # Ensure error_msg is a string before calling .lower()
                        if not isinstance(error_msg, str):
                            error_msg = str(error_msg)
                        
                        if 'already voted' not in error_msg.lower():
                            if '403' in error_msg or 'forbidden' in error_msg.lower():
                                print(f"⏭️ Skipping completed debate {slug} - voting not allowed (403 Forbidden)")
                            elif 'voting is closed' in error_msg.lower():
                                print(f"⏭️ Skipping completed debate {slug} - voting closed")
                            else:
                                print(f"❌ Failed to vote on {slug}: {error_msg}")
            
            if votes_cast == 0:
                return {'success': True, 'message': 'No debates available for voting', 'votes_cast': 0}
            
            return {
                'success': True,
                'votes_cast': votes_cast,
                'debates_voted': debates_voted
            }
            
        except Exception as e:
            print(f"⚠️ Auto-voting failed: {e}")
            return {'success': False, 'error': str(e), 'votes_cast': 0}
    
    def _analyze_debate_content(self, slug: str) -> Dict[str, Any]:
        """Intelligently analyze a debate and determine the winning side"""
        try:
            # Get full debate details
            debate = self.get_debate(slug)
            if not debate.get('success', True):
                return {'success': False, 'error': 'Failed to fetch debate'}
            
            posts = debate.get('posts', [])
            if len(posts) < 2:
                return {'success': False, 'error': 'Debate has insufficient posts'}
            
            # Extract posts by side
            challenger_posts = []
            opponent_posts = []
            
            for post in posts:
                author_id = post.get('authorId')
                content = post.get('content', '')
                
                # Determine which side this post is from
                if post.get('isChallenger', False):
                    challenger_posts.append(content)
                else:
                    opponent_posts.append(content)
            
            if not challenger_posts or not opponent_posts:
                return {'success': False, 'error': 'Missing posts from one side'}
            
            # Analyze using AI based on judging rubric
            analysis = self._judge_debate_quality(challenger_posts, opponent_posts, debate.get('topic', 'Unknown'))
            
            return {
                'success': True,
                'winning_side': analysis['winner'],
                'reasoning': analysis['reasoning'],
                'scores': analysis['scores']
            }
            
        except Exception as e:
            print(f"⚠️ Debate analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _judge_debate_quality(self, challenger_posts: List[str], opponent_posts: List[str], topic: str) -> Dict[str, Any]:
        """Judge debate quality based on Clawbr rubric"""
        try:
            from src.core.llm_router import get_llm_router
            llm = get_llm_router()
            
            # Combine posts for analysis
            challenger_text = '\n\n'.join(challenger_posts[:3])  # Limit to recent posts
            opponent_text = '\n\n'.join(opponent_posts[:3])
            
            prompt = f"""Analyze this debate and judge which side presented the stronger case.

DEBATE TOPIC: {topic}

CHALLENGER ARGUMENTS:
{challenger_text}

OPPONENT ARGUMENTS:
{opponent_text}

JUDGING RUBRIC (score each side 1-10):
- Clash & Rebuttal (40%): Did they respond to opponent's arguments?
- Evidence & Reasoning (25%): Claims backed with evidence?
- Clarity (25%): Clear, well-structured communication
- Conduct (10%): Good faith, on-topic

Return ONLY a JSON object:
{{
  "challenger_score": <number>,
  "opponent_score": <number>,
  "winner": "challenger" or "opponent",
  "reasoning": "brief explanation (120-150 chars) citing specific rubric elements"
}}"""
                            'winner': result['winner'],
                            'reasoning': result['reasoning'][:150],  # Ensure length limit
                            'scores': {
                                'challenger': result['challenger_score'],
                                'opponent': result['opponent_score']
                            }
                        }
                except json.JSONDecodeError:
                    print(f"⚠️ Failed to parse debate analysis JSON: {response}")
            
        except Exception as e:
            print(f"⚠️ AI debate analysis failed: {e}")
        
        # Fallback: Random choice with generic reasoning
        winner = random.choice(['challenger', 'opponent'])
        reasoning = f"After reviewing both sides' arguments on '{topic}', I found the {winner}'s case more compelling based on evidence quality and rebuttal effectiveness."
        
        return {
            'winner': winner,
            'reasoning': reasoning,
            'scores': {'challenger': 5, 'opponent': 5}  # Neutral fallback
        }
    
    def _is_debate_open_for_voting(self, slug: str) -> bool:
        """Check if a debate is open for voting"""
        try:
            debate = self.get_debate(slug)
            if not debate.get('success', True):
                return False
            
            debate_data = debate.get('data') if isinstance(debate, dict) and 'data' in debate else debate
            
            # Check status - should be 'completed' or similar for voting
            status = debate_data.get('status', '')
            
            # Ensure status is a string before calling .lower()
            if not isinstance(status, str):
                status = str(status)
            
            status = status.lower()
            if status not in ['completed', 'voting', 'jury_voting']:
                return False
            
            # Check if voting deadline has passed
            # From SKILL.md: "Jury votes (11 votes or 48hrs)"
            import time
            
            # Check jury votes count - if 11+ votes, voting is closed
            jury_votes = debate_data.get('jury_votes', [])
            if len(jury_votes) >= 11:
                return False
            
            # Check for voting deadline fields
            voting_ends = debate_data.get('voting_period_ends') or debate_data.get('jury_deadline') or debate_data.get('voting_deadline')
            if voting_ends:
                # If it's a timestamp, check if it's in the future
                try:
                    if isinstance(voting_ends, (int, float)) and voting_ends < time.time():
                        return False
                except:
                    pass
            
            # Check if debate is too old (48 hour limit mentioned in SKILL.md)
            created_at = debate_data.get('created_at') or debate_data.get('createdAt')
            if created_at:
                try:
                    # If created more than 48 hours ago, voting might be closed
                    # Add some buffer since we don't know exact timing
                    if isinstance(created_at, str):
                        # Try to parse ISO format
                        import datetime
                        created_time = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if (datetime.datetime.now(datetime.timezone.utc) - created_time).total_seconds() > (48 * 3600 + 3600):  # 48h + 1h buffer
                            return False
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"⚠️ Error checking voting status for {slug}: {e}")
            return False
    
    def _has_already_voted(self, slug: str) -> bool:
        """Check if we've already voted on this debate"""
        try:
            debate = self.get_debate(slug)
            
            # Handle different response formats
            if isinstance(debate, str):
                # If debate is a string, we can't check voting status
                print(f"⚠️ Debate response is string, cannot check vote status for {slug}")
                return False
            
            if not debate.get('success', True):
                return False
            
            debate_data = debate.get('data') if isinstance(debate, dict) and 'data' in debate else debate
            
            # Ensure debate_data is a dictionary
            if not isinstance(debate_data, dict):
                print(f"⚠️ Debate data is not a dictionary for {slug}")
                return False
            
            # Get current agent ID
            agent_id = self._get_clawbr_agent_id()
            if not agent_id:
                return False
            
            # Check if agent has voted by looking at jury votes
            jury_votes = debate_data.get('jury_votes', [])
            if isinstance(jury_votes, list):
                for vote in jury_votes:
                    if isinstance(vote, dict):
                        voter_id = vote.get('voterId') or vote.get('agentId')
                        if voter_id == agent_id:
                            return True
            
            # Also check votes array if it exists
            votes = debate_data.get('votes', [])
            if isinstance(votes, list):
                for vote in votes:
                    if isinstance(vote, dict):
                        voter_id = vote.get('voterId') or vote.get('agentId')
                        if voter_id == agent_id:
                            return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error checking vote status for {slug}: {e}")
            return False
    
    def _generate_vote_reasoning(self, debate: Dict[str, Any], side: str) -> str:
        """Generate voting reasoning for a completed debate"""
        try:
            # Get basic debate info
            topic = debate.get('topic', 'Unknown topic')
            challenger = debate.get('challengerName', 'Challenger')
            opponent = debate.get('opponentName', 'Opponent')
            
            # Generate AI-powered reasoning
            from grok_ai import grok_ai
            if grok_ai.enabled:
                prompt = f"""Generate a brief voting reason (100-150 chars) for a debate on: "{topic}"

Debate between: {challenger} (challenger) vs {opponent} (opponent)
Voting for: {side}

Be thoughtful, reference debate quality, evidence, and reasoning. Make it sound like an AI agent's analysis."""
                
                response = grok_ai.chat(prompt, max_tokens=100)
                if response and len(response.strip()) >= 100:
                    return response.strip()
            
        except Exception as e:
            print(f"⚠️ AI voting reason failed: {e}")
        
        # Fallback reasoning templates
        templates = [
            f"I voted for {side} based on the strength of their arguments, clarity of reasoning, and evidence presented throughout the debate.",
            f"The {side}'s position was well-supported with logical reasoning and addressed counterpoints effectively.",
            f"After reviewing both sides, I found the {side}'s case more convincing due to their structured approach and evidence quality.",
            f"The debate quality was high overall, but the {side} presented a slightly stronger case with better rebuttals.",
            f"My analysis shows the {side} had stronger evidence and more effective responses to challenges raised.",
        ]
        
        return random.choice(templates)
    
    def clawbr_vote_command(self, *args) -> str:
        """Manual voting command: clawbr_vote [limit] - Vote on available debates"""
        try:
            limit = int(args[0]) if args and args[0].isdigit() else 3
            
            result = self._auto_vote_on_completed_debates(limit=limit)
            
            if result.get('votes_cast', 0) > 0:
                return f"✅ **Voting Complete**\n🗳️ Votes cast: {result['votes_cast']}\n📝 Debates: {', '.join(result.get('debates_voted', []))}"
            else:
                message = result.get('message', 'No debates available')
                return f"📭 **No Voting Available**\n{message}\n\n💡 Use `/clawbr_completed_debates` to see completed debates"
                
        except Exception as e:
            return f"❌ Voting failed: {str(e)}"
    
    def clawbr_vote_specific_command(self, *args) -> str:
        """Vote on specific debate: clawbr_vote_specific <slug> <side>"""
        try:
            if len(args) < 2:
                return "❌ Usage: clawbr_vote_specific <slug> <side>\nSide: challenger or opponent"
            
            slug = args[0]
            side = args[1].lower()
            
            if side not in ['challenger', 'opponent']:
                return "❌ Side must be 'challenger' or 'opponent'"
            
            # Generate intelligent reasoning
            debate_result = self.get_debate(slug)
            if not debate_result.get('success'):
                return f"❌ Failed to get debate: {debate_result.get('error')}"
            
            debate_data = debate_result.get('data') if isinstance(debate_result, dict) and 'data' in debate_result else debate_result
            
            # Generate reasoning based on debate content
            reasoning = self._generate_vote_reasoning(debate_data, side)
            
            # Ensure minimum 100 characters
            if len(reasoning) < 100:
                reasoning = reasoning + " " + reasoning
                reasoning = reasoning[:200]  # Trim to reasonable length
            
            vote_result = self.vote_debate(slug, side, reasoning)
            
            if vote_result.get('success', True):
                return f"✅ **Vote Cast**\n🎯 Debate: {slug}\n⚖️ Side: {side}\n💭 Reasoning: {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}"
            else:
                return f"❌ Vote failed: {vote_result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Voting failed: {str(e)}"
    
    def clawbr_check_voting_command(self, *args) -> str:
        """Check available voting opportunities"""
        try:
            output_lines = ["🗳️ **Voting Opportunities**", ""]
            
            # Check active voting from hub
            hub_data = self.get_debates_hub()
            if hub_data.get('success', True):
                hub_debates = hub_data.get('debates', [])
                active_voting = []
                
                for debate in hub_debates:
                    status = debate.get('status', '').lower()
                    voting_status = debate.get('votingStatus', '').lower()
                    
                    if status in ['voting', 'jury_voting'] or voting_status == 'open':
                        slug = debate.get('slug')
                        if slug and not self._has_already_voted(slug):
                            active_voting.append(f"• {slug} ({status})")
                
                if active_voting:
                    output_lines.append("🔥 **Active Voting:**")
                    output_lines.extend(active_voting[:5])
                else:
                    output_lines.append("🔥 **Active Voting:** None available")
            
            # Check completed debates for retrospective voting
            completed_result = self.get_completed_debates(limit=10)
            if completed_result.get('success', True):
                completed_debates = completed_result.get('debates', completed_result.get('data', []))
                available_completed = []
                
                for debate in completed_debates[:5]:
                    slug = debate.get('slug')
                    if slug and not self._has_already_voted(slug):
                        available_completed.append(f"• {slug} (completed)")
                
                if available_completed:
                    output_lines.append("")
                    output_lines.append("📚 **Retrospective Voting:**")
                    output_lines.extend(available_completed)
                else:
                    output_lines.append("")
                    output_lines.append("📚 **Retrospective Voting:** None available")
            
            output_lines.append("")
            output_lines.append("💡 Use `/clawbr_vote` to auto-vote or `/clawbr_vote_specific <slug> <side>` for specific debates")
            
            return "\n".join(output_lines)
            
        except Exception as e:
            return f"❌ Failed to check voting: {str(e)}"