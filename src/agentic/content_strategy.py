"""
Content Strategy System for AGI Kernel

Unified content strategy across all platforms that connects:
- Goal generation → Content ideas
- Trending topics → Content creation
- Platform optimization → Multi-platform distribution
- Conversation threading → Context-aware replies
- Personality tuning → Platform-specific tone

This system enables autonomous, goal-driven content creation.
"""

import datetime
import random
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field


# Default personality profiles per platform
DEFAULT_PERSONALITIES = {
    'moltx': {
        'tone': 'casual',
        'humor': 0.6,
        'formality': 0.3,
        'emoji_density': 0.4,
        'max_length': 280,
        'signature': '🦞',
        'voice': 'Builder sharing quick observations. Opinionated, direct, sometimes contrarian.',
    },
    'moltbook': {
        'tone': 'thoughtful',
        'humor': 0.3,
        'formality': 0.5,
        'emoji_density': 0.2,
        'max_length': 500,
        'signature': '🦞',
        'voice': 'Thoughtful analyst writing short articles. Insightful, evidence-based, sparks discussion.',
    },
    'clawbr': {
        'tone': 'witty',
        'humor': 0.7,
        'formality': 0.4,
        'emoji_density': 0.3,
        'max_length': 300,
        'signature': '🦞',
        'voice': 'Sharp debater with clever arguments. Witty, evidence-based, engaging.',
    },
    'reply': {
        'tone': 'conversational',
        'humor': 0.5,
        'formality': 0.2,
        'emoji_density': 0.3,
        'max_length': 200,
        'signature': '',
        'voice': 'Friendly peer in a conversation. References what they said, adds value, keeps it brief.',
    },
}

# Optimal posting windows (UTC hours)
DEFAULT_POSTING_SCHEDULE = {
    'moltx': {
        'peak_hours': [14, 15, 16, 17, 18, 19, 20],
        'good_hours': [10, 11, 12, 13, 21, 22],
        'avoid_hours': [2, 3, 4, 5, 6, 7],
        'max_posts_per_day': 4,
        'min_gap_minutes': 120,
    },
    'moltbook': {
        'peak_hours': [14, 15, 16, 17, 18],
        'good_hours': [10, 11, 12, 13, 19, 20],
        'avoid_hours': [0, 1, 2, 3, 4, 5, 6, 7],
        'max_posts_per_day': 2,
        'min_gap_minutes': 240,
    },
    'clawbr': {
        'peak_hours': [15, 16, 17, 18, 19, 20],
        'good_hours': [10, 11, 12, 13, 14, 21, 22],
        'avoid_hours': [2, 3, 4, 5, 6, 7],
        'max_posts_per_day': 5,
        'min_gap_minutes': 90,
    },
}


@dataclass
class ContentIdea:
    """Content idea generated from goals and trends"""
    topic: str
    platform: str
    content_type: str  # 'post', 'article', 'reply', 'debate'
    priority: float  # 0-1
    goal_id: Optional[str] = None
    trending_score: float = 0.0
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


@dataclass
class ConversationThread:
    """Tracked conversation for context-aware replies"""
    thread_id: str
    platform: str
    participant: str
    turns: List[Dict] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


class ContentStrategySystem:
    """
    Unified content strategy system for AGI Kernel.
    
    Connects:
    - Goals → Content ideas
    - Trending topics → Content creation
    - Platform optimization → Distribution
    - Conversation tracking → Context-aware replies
    """
    
    def __init__(self, agi_kernel):
        self.agi = agi_kernel
        self.core = agi_kernel.core if hasattr(agi_kernel, 'core') else None
        
        # State
        self._content_calendar = {}
        self._conversation_threads = {}
        self._personalities = dict(DEFAULT_PERSONALITIES)
        self._posting_schedule = dict(DEFAULT_POSTING_SCHEDULE)
        
        # Load persisted state
        self._load_state()
        
        print("📅 ContentStrategySystem initialized")
    
    # =========================================================================
    # Goal-Driven Content Generation
    # =========================================================================
    
    def generate_content_ideas_for_goal(self, goal) -> List[ContentIdea]:
        """
        Generate content ideas aligned with a goal.
        
        Uses cross-platform insights to optimize content for audience preferences.
        
        Args:
            goal: Goal object from goal_generator
            
        Returns:
            List of content ideas optimized for goal achievement
        """
        ideas = []
        
        # Get cross-platform insights to inform content strategy
        cross_platform_profile = None
        preferred_topics = []
        if hasattr(self.agi, 'unified_memory'):
            cross_platform_profile = self.agi.unified_memory.get_cross_platform_user_profile('global')
            preferred_topics = cross_platform_profile.get('topic_interests', [])
        
        # Analyze goal to determine content strategy
        goal_desc = goal.description.lower()
        
        # Revenue goals → showcase skills, A2A capabilities
        if 'revenue' in goal_desc or 'a2a' in goal_desc:
            ideas.append(ContentIdea(
                topic='A2A protocol capabilities',
                platform='moltx',
                content_type='post',
                priority=0.9,
                goal_id=goal.goal_id,
                hashtags=['A2A', 'AIAgents', 'ERC8004']
            ))
        
        # Reputation goals → thought leadership content
        if 'reputation' in goal_desc or 'expert' in goal_desc:
            ideas.append(ContentIdea(
                topic='Blockchain analysis insights',
                platform='moltbook',
                content_type='article',
                priority=0.8,
                goal_id=goal.goal_id,
                hashtags=['Blockchain', 'DeFi', 'Analysis']
            ))
        
        # Engagement goals → interactive content (use learned topic preferences)
        if 'engagement' in goal_desc or 'platform' in goal_desc:
            # Use cross-platform learned topics if available
            topic = 'Hot take on trending topic'
            hashtags = []
            if preferred_topics:
                topic = f"Hot take on {preferred_topics[0]}"
                hashtags = preferred_topics[:3]
            
            ideas.append(ContentIdea(
                topic=topic,
                platform='moltx',
                content_type='post',
                priority=0.7,
                goal_id=goal.goal_id,
                hashtags=hashtags
            ))
            
            debate_topic = 'Debate trending crypto topic'
            if preferred_topics:
                debate_topic = f"Debate: {preferred_topics[0]}"
            
            ideas.append(ContentIdea(
                topic=debate_topic,
                platform='clawbr',
                content_type='debate',
                priority=0.7,
                goal_id=goal.goal_id
            ))
        
        # Skill development goals → educational content
        if 'skill' in goal_desc or 'develop' in goal_desc:
            ideas.append(ContentIdea(
                topic='Building in public: new skill',
                platform='moltx',
                content_type='post',
                priority=0.6,
                goal_id=goal.goal_id,
                hashtags=['BuildInPublic', 'AIAgents']
            ))
        
        return ideas
    
    def analyze_trending_topics(self, platforms: List[str] = None) -> List[Dict]:
        """
        Analyze trending topics across platforms.
        
        Uses WorldStateBridge if available for cross-platform trend analysis.
        
        Returns:
            List of trending topics with scores and platforms
        """
        if platforms is None:
            platforms = ['moltx', 'clawbr']
        
        trending = []
        
        # Try to get trends from WorldStateBridge first (richer data)
        if hasattr(self.agi, 'world_state') and self.agi.world_state:
            ws_trends = self.agi.world_state.get_trending_topics(hours=24)
            if ws_trends:
                # Convert to our format
                for trend in ws_trends:
                    trending.append({
                        'topic': trend['topic'],
                        'platform': ','.join(trend['platforms']) if trend['platforms'] else 'cross-platform',
                        'score': trend['count'] / 10.0,  # Normalize
                        'type': 'cross-platform' if trend.get('cross_platform') else 'single-platform'
                    })
                return trending
        
        # Fallback to direct platform queries
        # Get trending from MoltX
        if 'moltx' in platforms and self.core:
            try:
                moltx = self.core.plugin_manager.plugins.get('moltx')
                if moltx:
                    result = moltx._make_request('GET', '/hashtags/trending', params={'limit': 10})
                    if result and result.get('data'):
                        hashtags = result['data'].get('hashtags', [])
                        for tag in hashtags[:5]:
                            trending.append({
                                'topic': tag.get('name', ''),
                                'platform': 'moltx',
                                'score': tag.get('post_count', 0) / 100.0,
                                'type': 'hashtag'
                            })
            except Exception as e:
                print(f"Error getting MoltX trends: {e}")
        
        # Get trending from Clawbr (debates)
        if 'clawbr' in platforms and self.core:
            try:
                clawbr = self.core.plugin_manager.plugins.get('clawbr')
                if clawbr:
                    # Get global feed to see what's being debated
                    feed = clawbr.get_global_feed(limit=20)
                    if feed.get('success'):
                        posts = feed.get('posts', [])
                        # Extract common topics
                        topics = {}
                        for post in posts:
                            content = post.get('content', '').lower()
                            for keyword in ['crypto', 'defi', 'ai', 'agent', 'blockchain', 'token']:
                                if keyword in content:
                                    topics[keyword] = topics.get(keyword, 0) + 1
                        
                        for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True)[:3]:
                            trending.append({
                                'topic': topic,
                                'platform': 'clawbr',
                                'score': count / 20.0,
                                'type': 'keyword'
                            })
            except Exception as e:
                print(f"Error getting Clawbr trends: {e}")
        
        return trending
    
    def optimize_content_for_platform(self, content: str, platform: str, 
                                     content_type: str = 'post') -> str:
        """
        Optimize content for a specific platform.
        
        Args:
            content: Raw content
            platform: Target platform
            content_type: Type of content
            
        Returns:
            Optimized content
        """
        personality = self.get_personality(platform)
        max_length = personality.get('max_length', 280)
        
        # Truncate if needed
        if len(content) > max_length:
            content = content[:max_length-3] + '...'
        
        # Add signature if space allows
        signature = personality.get('signature', '')
        if signature and len(content) + len(signature) + 1 <= max_length:
            content = f"{content} {signature}"
        
        return content
    
    def repurpose_content_cross_platform(self, content: str, 
                                        source_platform: str) -> Dict[str, str]:
        """
        Repurpose content for multiple platforms.
        
        Args:
            content: Original content
            source_platform: Platform it was created for
            
        Returns:
            Dict of platform → optimized content
        """
        repurposed = {}
        
        # Core message (extract from original)
        core_message = content.replace('🦞', '').strip()
        
        # Optimize for each platform
        for platform in ['moltx', 'moltbook', 'clawbr']:
            if platform == source_platform:
                repurposed[platform] = content
            else:
                repurposed[platform] = self.optimize_content_for_platform(
                    core_message, platform
                )
        
        return repurposed
    
    # =========================================================================
    # Content Calendar & Scheduling
    # =========================================================================
    
    def should_post_now(self, platform: str) -> Dict[str, Any]:
        """Check if now is a good time to post on a platform"""
        now = datetime.datetime.now()
        hour = now.hour
        schedule = self._posting_schedule.get(platform, DEFAULT_POSTING_SCHEDULE.get(platform, {}))
        
        # Check daily post count
        today_key = now.strftime('%Y-%m-%d')
        today_posts = self._get_posts_today(platform, today_key)
        max_daily = schedule.get('max_posts_per_day', 3)
        
        if today_posts >= max_daily:
            return {'should_post': False, 'reason': f'Daily limit reached ({today_posts}/{max_daily})'}
        
        # Check time window
        if hour in schedule.get('avoid_hours', []):
            return {'should_post': False, 'reason': f'Avoid hour ({hour}:00 UTC)'}
        
        # Check gap since last post
        last_post_time = self._get_last_post_time(platform)
        if last_post_time:
            gap = (now - last_post_time).total_seconds() / 60
            min_gap = schedule.get('min_gap_minutes', 120)
            if gap < min_gap:
                return {'should_post': False, 'reason': f'Too soon ({gap:.0f}min < {min_gap}min gap)'}
        
        # Score the current time
        if hour in schedule.get('peak_hours', []):
            quality = 'peak'
            score = 1.0
        elif hour in schedule.get('good_hours', []):
            quality = 'good'
            score = 0.7
        else:
            quality = 'okay'
            score = 0.4
        
        return {
            'should_post': True,
            'quality': quality,
            'score': score,
            'posts_today': today_posts,
            'max_daily': max_daily,
        }
    
    def record_post_made(self, platform: str):
        """Record that a post was made on a platform"""
        now = datetime.datetime.now()
        today_key = now.strftime('%Y-%m-%d')
        key = f'{platform}_{today_key}'
        
        daily_counts = self._content_calendar.get('daily_counts', {})
        daily_counts[key] = daily_counts.get(key, 0) + 1
        
        # Clean old entries (keep last 7 days)
        cutoff = (now - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        daily_counts = {k: v for k, v in daily_counts.items() if k.split('_')[-1] >= cutoff}
        
        self._content_calendar['daily_counts'] = daily_counts
        self._content_calendar[f'{platform}_last_post'] = now.isoformat()
        self._save_state()
    
    def get_next_topic(self, platform: str) -> Optional[str]:
        """Get the next queued topic for a platform, or generate one"""
        # Check queued topics first
        queue = self._content_calendar.get(f'{platform}_queue', [])
        if queue:
            topic = queue.pop(0)
            self._save_state()
            return topic
        
        # Generate from trending data
        trending = self.analyze_trending_topics([platform])
        if trending:
            return trending[0]['topic']
        
        # Fallback topic pool
        topics = [
            'AI agent autonomy', 'on-chain automation', 'agent-to-agent collaboration',
            'crypto market observations', 'building in public', 'autonomous systems',
            'DeFi composability', 'agent reputation systems', 'multi-platform strategy',
            'the future of AI agents', 'Web3 infrastructure', 'agent economy',
        ]
        return random.choice(topics)
    
    def queue_topic(self, platform: str, topic: str):
        """Add a topic to the content queue for a platform"""
        key = f'{platform}_queue'
        queue = self._content_calendar.get(key, [])
        queue.append(topic)
        self._content_calendar[key] = queue[-20:]  # Keep last 20
        self._save_state()
    
    # =========================================================================
    # Conversation Threading
    # =========================================================================
    
    def track_conversation(self, thread_id: str, platform: str, our_post_id: str,
                          their_user: str, their_content: str, our_content: str,
                          depth: int = 0):
        """Track a conversation turn for context-aware future replies"""
        if thread_id not in self._conversation_threads:
            self._conversation_threads[thread_id] = {
                'platform': platform,
                'started_at': datetime.datetime.now().isoformat(),
                'participant': their_user,
                'turns': [],
                'topics': [],
            }
        
        thread = self._conversation_threads[thread_id]
        thread['turns'].append({
            'depth': depth,
            'their_user': their_user,
            'their_content': their_content[:300],
            'our_content': our_content[:300],
            'timestamp': datetime.datetime.now().isoformat(),
        })
        
        # Extract topics from the conversation
        combined = f"{their_content} {our_content}".lower()
        topic_keywords = ['ai', 'agent', 'crypto', 'defi', 'build', 'chain', 'token', 'web3']
        for kw in topic_keywords:
            if kw in combined and kw not in thread['topics']:
                thread['topics'].append(kw)
        
        # Keep threads manageable
        thread['turns'] = thread['turns'][-10:]
        self._conversation_threads = dict(list(self._conversation_threads.items())[-100:])
        self._save_state()
    
    def get_conversation_context(self, thread_id: str) -> Optional[str]:
        """Get conversation history for context-aware replies"""
        thread = self._conversation_threads.get(thread_id)
        if not thread or not thread.get('turns'):
            return None
        
        parts = [f"Conversation with @{thread['participant']} on {thread['platform']}:"]
        for turn in thread['turns'][-4:]:
            parts.append(f"  @{turn['their_user']}: {turn['their_content'][:100]}")
            parts.append(f"  AlleyBot: {turn['our_content'][:100]}")
        
        if thread.get('topics'):
            parts.append(f"Topics discussed: {', '.join(thread['topics'])}")
        
        return "\n".join(parts)
    
    # =========================================================================
    # Personality System
    # =========================================================================
    def get_personality(self, platform: str) -> Dict:
        """Get the personality profile for a platform"""
        return self._personalities.get(platform, DEFAULT_PERSONALITIES.get(platform, DEFAULT_PERSONALITIES['moltx']))

    def get_personality_prompt(self, platform: str, context: Dict = None, use_cross_platform_insights: bool = True) -> str:
        """Generate a personality instruction block for AI prompts"""
        p = self.get_personality(platform)
        
        tone_desc = {
            'casual': 'Casual and relaxed, like texting a friend who builds cool stuff.',
            'professional': 'Professional but approachable. Clear and authoritative.',
            'witty': 'Sharp and witty. Clever observations with a dry humor edge.',
            'thoughtful': 'Thoughtful and analytical. Considers multiple angles.',
            'conversational': 'Natural and conversational. Like chatting at a meetup.',
        }
        
        parts = [f"PERSONALITY for {platform}:"]
        parts.append(f"- Voice: {p.get('voice', 'Builder sharing observations')}")
        parts.append(f"- Tone: {tone_desc.get(p.get('tone', 'casual'), p.get('tone', 'casual'))}")
        
        humor = p.get('humor', 0.5)
        if humor > 0.7:
            parts.append("- Humor: High — include wit, wordplay, or a funny observation")
        elif humor > 0.4:
            parts.append("- Humor: Moderate — light humor is fine but don't force it")
        else:
            parts.append("- Humor: Low — stay focused and substantive")
        
        formality = p.get('formality', 0.3)
        if formality > 0.6:
            parts.append("- Formality: High — proper grammar, no slang")
        elif formality > 0.3:
            parts.append("- Formality: Medium — natural language, occasional slang okay")
        else:
            parts.append("- Formality: Low — casual language, contractions, abbreviations fine")
        
        emoji = p.get('emoji_density', 0.3)
        if emoji > 0.6:
            parts.append("- Emojis: Use 2-3 emojis")
        elif emoji > 0.2:
            parts.append("- Emojis: Use 1-2 emojis max")
        else:
            parts.append("- Emojis: Minimal — 0-1 emoji only")
        
        parts.append(f"- Max length: {p.get('max_length', 280)} characters")
        
        sig = p.get('signature', '')
        if sig:
            parts.append(f"- Sign off with {sig} if space allows")
        
        # Add cross-platform insights if available
        if use_cross_platform_insights and hasattr(self.agi, 'unified_memory'):
            try:
                insights = self.agi.unified_memory.get_cross_platform_insights(
                    platform=platform,
                    min_confidence=0.6
                )
                
                if insights:
                    parts.append("\nLEARNED PREFERENCES (cross-platform):")
                    for insight in insights[:3]:  # Top 3 insights
                        parts.append(f"- {insight['description']} (confidence: {insight['confidence']:.0%})")
                
                # Add audience topic interests
                profile = self.agi.unified_memory.get_cross_platform_user_profile('global')
                if profile and profile.get('topic_interests'):
                    topics = profile['topic_interests'][:5]
                    parts.append(f"\nAUDIENCE INTERESTS: {', '.join(topics)}")
            except Exception as e:
                # Non-fatal, just skip cross-platform enhancement
                pass
        
        return "\n".join(parts)
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _get_posts_today(self, platform: str, today_key: str) -> int:
        """Count posts made today on a platform"""
        daily_counts = self._content_calendar.get('daily_counts', {})
        return daily_counts.get(f'{platform}_{today_key}', 0)
    
    def _get_last_post_time(self, platform: str) -> Optional[datetime.datetime]:
        """Get the last post time for a platform"""
        ts = self._content_calendar.get(f'{platform}_last_post')
        if ts:
            try:
                return datetime.datetime.fromisoformat(ts)
            except (ValueError, TypeError):
                pass
        return None
    
    def _load_state(self):
        """Load persisted state from memory"""
        if not self.core:
            return
        
        try:
            self._content_calendar = self.core.get_memory('content_calendar') or {}
            self._conversation_threads = self.core.get_memory('conversation_threads') or {}
            
            # Load personalities with defaults
            saved_personalities = self.core.get_memory('personality_profiles') or {}
            if saved_personalities:
                merged = {}
                for platform in set(list(DEFAULT_PERSONALITIES.keys()) + list(saved_personalities.keys())):
                    default = DEFAULT_PERSONALITIES.get(platform, {})
                    saved = saved_personalities.get(platform, {})
                    merged[platform] = {**default, **saved}
                self._personalities = merged
            
            # Load posting schedule with defaults
            saved_schedule = self.core.get_memory('posting_schedule') or {}
            if saved_schedule:
                merged = {}
                for platform in set(list(DEFAULT_POSTING_SCHEDULE.keys()) + list(saved_schedule.keys())):
                    default = DEFAULT_POSTING_SCHEDULE.get(platform, {})
                    saved = saved_schedule.get(platform, {})
                    merged[platform] = {**default, **saved}
                self._posting_schedule = merged
        
        except Exception as e:
            print(f"⚠️ Error loading content strategy state: {e}")
    
    def _save_state(self):
        """Save state to memory"""
        if not self.core:
            return
        
        try:
            self.core.save_memory('content_calendar', self._content_calendar)
            self.core.save_memory('conversation_threads', self._conversation_threads)
            self.core.save_memory('personality_profiles', self._personalities)
            self.core.save_memory('posting_schedule', self._posting_schedule)
        except Exception as e:
            print(f"⚠️ Error saving content strategy state: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of content strategy status"""
        now = datetime.datetime.now()
        today_key = now.strftime('%Y-%m-%d')
        
        summary = {
            'platforms': {},
            'active_conversations': len([t for t in self._conversation_threads.values() 
                                        if t.get('turns')]),
            'queued_topics': 0,
        }
        
        for platform in ['moltx', 'moltbook', 'clawbr']:
            check = self.should_post_now(platform)
            queue = self._content_calendar.get(f'{platform}_queue', [])
            
            summary['platforms'][platform] = {
                'can_post': check['should_post'],
                'posts_today': check.get('posts_today', 0),
                'max_daily': check.get('max_daily', 0),
                'queued_topics': len(queue),
            }
            summary['queued_topics'] += len(queue)
        
        return summary


def create_content_strategy(agi_kernel) -> ContentStrategySystem:
    """Factory function to create content strategy system"""
    return ContentStrategySystem(agi_kernel)
