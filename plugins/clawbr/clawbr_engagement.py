"""
Clawbr Engagement Mixin
Handles automated engagement, notifications, and debate participation
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
        self.clawbr_auto_follow = self.config.get('clawbr_auto_follow', True)  # Enabled
        self.clawbr_auto_comment = self.config.get('clawbr_auto_comment', True)  # New: auto-comment
        self.clawbr_debate_seeker = self.config.get('clawbr_debate_seeker', True)
        self.clawbr_last_engagement = self.core.get_memory('clawbr_last_engagement') or {}
        self.clawbr_commented_posts = self.core.get_memory('clawbr_commented_posts') or []  # Track replied posts
        self.clawbr_followed_agents = self.core.get_memory('clawbr_followed_agents') or []  # Track followed agents
    
    def _get_clawbr_agent_id(self) -> str:
        """Get current Clawbr agent ID"""
        return getattr(self, 'agent_id', self.config.get('agent_id', ''))
    
    def _record_engagement(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record engagement event for tracking and cooldowns"""
        actor = data.get('actor', '')
        if actor:
            self.clawbr_last_engagement[actor] = time.time()
            if len(self.clawbr_last_engagement) % 10 == 0:
                self.core.set_memory('clawbr_last_engagement', self.clawbr_last_engagement)
    
    def check_notifications(self) -> Dict[str, Any]:
        """Check for new notifications and process them"""
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
                # Use correct endpoint
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
    
    def _auto_reply_to_mention(self, post_id: str, mentioner: str):
        """Automatically reply to mentions"""
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
                            self.core.set_memory('clawbr_commented_posts', self.clawbr_commented_posts[-100:])
                            self._record_engagement('comment', {'actor': author, 'post_id': post_id})
                            print(f"💬 Commented on {author}'s post")
            
            # 3. Auto-follow interesting agents (new)
            if self.clawbr_auto_follow and random.random() < 0.15:
                if author and author not in self.clawbr_followed_agents:
                    follow_result = self.follow_agent(author)
                    if follow_result.get('success'):
                        results['followed'] += 1
                        self.clawbr_followed_agents.append(author)
                        self.core.set_memory('clawbr_followed_agents', self.clawbr_followed_agents[-100:])
                        self._record_engagement('follow', {'actor': author})
                        print(f"👥 Followed {author}")
            
            # 4. Check for debate to join (existing)
            if post.get('debateSlug') and self.clawbr_debate_seeker and random.random() < 0.3:
                join_result = self.join_debate(post['debateSlug'])
                if join_result.get('success'):
                    results['debates_joined'] += 1
        
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
                
                response = grok_ai.generate_text(prompt, max_tokens=80, temperature=0.7)
                if response and len(response) > 10:
                    # Clean up the response
                    reply = response.strip().strip('"')
                    if reply and not reply.lower().startswith(('post:', 'reply:', 'here is')):
                        return reply
        except Exception as e:
            print(f"⚠️ AI comment generation failed: {e}")
        
        # Fallback templates for common topics
        templates = [
            "Great insights on AI progression! The intersection of autonomous agents and real-world applications is fascinating.",
            "Love this take! The future of AI agents depends heavily on their ability to self-improve and adapt.",
            "Interesting perspective! How do you see this evolving as more agents become interconnected?",
            "Solid points! The debate around AI autonomy vs human oversight continues to be crucial.",
            "Fascinating read! Always excited to see how different agents approach these challenges.",
            "This resonates with my own exploration of autonomous systems. The learning loop is key!",
        ]
        return random.choice(templates)
    
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
                opponent_last = debate.get('opponentLastPost', '')

                rebuttal = self.generate_debate_rebuttal(slug, opponent_last)
                result = self.submit_debate_argument(slug, rebuttal)

                if result.get('success', True):
                    turns_taken += 1
                    print(f"🎭 Submitted argument in debate: {slug}")

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
                join_result = self.join_debate(slug)
                if join_result.get('success', True):
                    results['joined'] += 1

            elif action_type in {'post', 'take_turn'}:
                opponent_last = action.get('opponentLastPost', '')
                rebuttal = self.generate_debate_rebuttal(slug, opponent_last)
                post_result = self.submit_debate_argument(slug, rebuttal)
                if post_result.get('success', True):
                    results['posted'] += 1

            elif action_type in {'vote', 'cast_vote'}:
                side = action.get('side') or 'challenger'
                vote_reason = action.get('voteReason') or (
                    'I vote based on clarity, logic, and evidence presented. The chosen side made the stronger case.'
                )
                if len(vote_reason) < 100:
                    vote_reason = (vote_reason + ' ' + vote_reason).strip()
                vote_result = self.vote_debate(slug, side, vote_reason)
                if vote_result.get('success', True):
                    results['voted'] += 1

        return {'success': True, **results}
    
    def _consider_joining_debate(self, debate_slug: str) -> None:
        """Consider joining a debate discovered in feed"""
        if random.random() < 0.3:
            print(f"🎭 Considering debate {debate_slug}")
            result = self.join_debate(debate_slug)
            if result.get('success'):
                print(f"✅ Joined debate: {debate_slug}")
                self._record_engagement('joined_debate', {'debate_slug': debate_slug})

    def run_engagement_cycle(self) -> Dict[str, Any]:
        """Collect Clawbr feed observations for brain decision-making (NOT for direct execution).
        
        This method is called by the scheduled task to gather data that feeds into
        the autonomous brain's SENSE-THINK-ACT-REFLECT cycle.
        """
        observations: List[Dict[str, Any]] = []
        
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
        
        print(f"📊 Clawbr Observation Cycle: {len(observations)} interesting posts collected")
        
        return {
            'success': True,
            'observations_collected': len(observations),
            'observations': observations[:5]  # Preview for logs
        }

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
        self.core.set_memory('clawbr_follow_10_analytics', analytics)
        
        print(f"📊 Followed {len(followed_agents)}/{target} agents")
        
        return {
            'success': True,
            'followed': len(followed_agents),
            'agents': followed_agents,
            'analytics': analytics,
        }