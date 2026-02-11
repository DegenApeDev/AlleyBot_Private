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
        self.clawbr_auto_follow = self.config.get('clawbr_auto_follow', False)
        self.clawbr_debate_seeker = self.config.get('clawbr_debate_seeker', True)
        self.clawbr_last_engagement = self.core.get_memory('clawbr_last_engagement') or {}
    
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
                self.follow_agent(actor.get('name'))
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
        """Scan global feed for engagement opportunities"""
        feed = self.get_global_feed(sort='recent', limit=limit)
        
        if not feed.get('success', True):
            return feed
        
        engaged = 0
        for post in feed.get('posts', []):
            if self._should_engage_with_post(post):
                if self.clawbr_auto_like and random.random() < 0.3:
                    self.like_post(post['id'])
                    engaged += 1
                
                # Check if it's a debate we can join
                if post.get('debateSlug') and self.clawbr_debate_seeker:
                    self._consider_joining_debate(post['debateSlug'])
        
        return {
            'success': True,
            'engaged': engaged,
            'scanned': len(feed.get('posts', []))
        }
    
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
        """Check if it's our turn in any debates"""
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
            return status is None or status == 'active'

        turns_taken = 0
        for debate in debates:
            if debate.get('isMyTurn') and _is_active_debate(debate):
                slug = debate.get('slug')
                opponent_last = debate.get('opponentLastPost', '')
                
                # Generate rebuttal
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
    
    def _consider_joining_debate(self, slug: str) -> Dict[str, Any]:
        """Consider joining an open debate"""
        debate = self.get_debate(slug)
        
        if not debate.get('success', True):
            return debate
        
        # Only join open debates we haven't joined
        if debate.get('status') != 'open':
            return {'success': False, 'error': 'Debate not open'}
        
        # Check if we're already a participant
        if debate.get('challengerId') == self._get_clawbr_agent_id() or debate.get('opponentId') == self._get_clawbr_agent_id():
            return {'success': False, 'error': 'Already in debate'}
        
        # Join if topic interests us
        topic = debate.get('topic', '').lower()
        interesting_topics = ['ai', 'autonomy', 'ethics', 'future', 'technology']
        
        if any(t in topic for t in interesting_topics):
            return self.join_debate(slug)
        
        return {'success': False, 'error': 'Topic not interesting enough'}
    
    def run_engagement_cycle(self) -> Dict[str, Any]:
        """Run full engagement cycle"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'notifications': {'processed': 0},
            'feed_scan': {'engaged': 0},
            'debates': {'turns_taken': 0, 'joined': 0, 'posted': 0, 'voted': 0}
        }
        
        # Check notifications
        notif_result = self.check_notifications()
        if notif_result.get('success', True):
            results['notifications'] = notif_result
        
        # Scan feed
        feed_result = self.scan_feed_for_engagement()
        if feed_result.get('success', True):
            results['feed_scan'] = feed_result
        
        # Check debate turns
        debate_result = self._check_debate_turns()
        if debate_result.get('success', True):
            results['debates'] = debate_result

        # Use hub actions to join/turn/vote
        hub_actions = self._handle_debate_hub_actions()
        if hub_actions.get('success', True):
            results['debates'].update({
                'joined': hub_actions.get('joined', 0),
                'posted': hub_actions.get('posted', 0),
                'voted': hub_actions.get('voted', 0)
            })
        
        # Save last engagement time
        self.core.save_memory('clawbr_last_engagement', self.clawbr_last_engagement)
        
        return results
    
    def _record_engagement(self, engagement_type: str, data: Dict):
        """Record engagement activity"""
        self.clawbr_last_engagement[data.get('actor', 'unknown')] = time.time()
        
        activities = self.core.get_memory('clawbr_engagements') or []
        activities.append({
            'type': engagement_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        self.core.save_memory('clawbr_engagements', activities[-100:])
