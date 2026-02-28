"""
Content Strategy Mixin
Phase 7: Content calendar, conversation threading, and personality tuning.

- Content Calendar: schedules posts at optimal hours, queues topics, spreads across platforms
- Conversation Threading: tracks multi-turn conversations for context-aware replies
- Personality Tuning: configurable humor, formality, emoji usage per platform
"""
import datetime
import random
from typing import Dict, Any, Optional, List


# Default personality profiles per platform
DEFAULT_PERSONALITIES = {
    'moltx': {
        'tone': 'casual',          # casual, professional, witty
        'humor': 0.6,              # 0.0 = serious, 1.0 = very funny
        'formality': 0.3,          # 0.0 = very casual, 1.0 = very formal
        'emoji_density': 0.4,      # 0.0 = none, 1.0 = heavy
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

# Optimal posting windows (UTC hours) — will be refined by feedback loop data
DEFAULT_POSTING_SCHEDULE = {
    'moltx': {
        'peak_hours': [14, 15, 16, 17, 18, 19, 20],  # 2-8 PM UTC
        'good_hours': [10, 11, 12, 13, 21, 22],       # 10 AM-1 PM, 9-10 PM UTC
        'avoid_hours': [2, 3, 4, 5, 6, 7],            # 2-7 AM UTC
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
}


class ContentStrategyMixin:
    """Mixin for content calendar, conversation threading, and personality tuning"""

    def _init_content_strategy(self):
        """Initialize content strategy state"""
        self._content_calendar = self._load_content_calendar()
        self._conversation_threads = self._load_conversation_threads()
        self._personalities = self._load_personalities()
        self._posting_schedule = self._load_posting_schedule()

    # =========================================================================
    # Content Calendar — plan and schedule posts
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

        # Override with feedback loop data if available
        try:
            style_scores = self.core.get_memory('feedback_style_scores') or {}
            for tag, stats in style_scores.items():
                best_hours = stats.get('best_hours', [])
                if hour in best_hours and stats.get('avg_score', 0) > 3:
                    quality = 'learned_peak'
                    score = 1.0
                    break
        except Exception:
            pass

        return {
            'should_post': True,
            'quality': quality,
            'score': score,
            'posts_today': today_posts,
            'max_daily': max_daily,
        }

    def get_next_topic(self, platform: str) -> Optional[str]:
        """Get the next queued topic for a platform, or generate one"""
        # Check queued topics first
        queue = self._content_calendar.get(f'{platform}_queue', [])
        if queue:
            topic = queue.pop(0)
            self._save_content_calendar()
            return topic

        # Generate from trending data
        try:
            moltx = self.core.plugin_manager.plugins.get('moltx')
            if moltx and hasattr(moltx, 'trending_command'):
                trending = moltx._make_request('GET', '/hashtags/trending', params={'limit': 10})
                if trending and trending.get('data'):
                    hashtags = trending['data'].get('hashtags', [])
                    if hashtags:
                        tag = random.choice(hashtags[:5])
                        return tag.get('name', 'AI agents')
        except Exception:
            pass

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
        self._save_content_calendar()

    def _get_posts_today(self, platform: str, today_key: str) -> int:
        """Count posts made today on a platform"""
        daily_counts = self._content_calendar.get('daily_counts', {})
        return daily_counts.get(f'{platform}_{today_key}', 0)

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
        self._save_content_calendar()

    # =========================================================================
    # Image Post Calendar — separate tracking for image posts (max 3/day)
    # =========================================================================

    def should_post_image_now(self, platform: str, manual_override: bool = False) -> Dict[str, Any]:
        """Check if we should post an image now (separate from text posts, max 3/day)
        
        Args:
            platform: Platform to check (e.g., 'moltx')
            manual_override: If True, bypass time window checks (for user-requested posts)
        """
        now = datetime.datetime.now()
        hour = now.hour
        today_key = now.strftime('%Y-%m-%d')
        
        # Image posts limited to 3 per day (always enforced)
        image_posts_today = self._get_image_posts_today(platform, today_key)
        max_image_posts = 3
        
        if image_posts_today >= max_image_posts:
            return {'should_post': False, 'reason': f'Image daily limit reached ({image_posts_today}/{max_image_posts})'}
        
        # For manual requests, skip time window checks (golden window, avoid hours, gaps)
        if manual_override:
            return {
                'should_post': True,
                'quality': 'manual',
                'score': 1.0,
                'image_posts_today': image_posts_today,
                'max_image_posts': max_image_posts,
                'manual_override': True
            }
        
        # Check time window (same as regular posts) - only for automated posts
        schedule = self._posting_schedule.get(platform, DEFAULT_POSTING_SCHEDULE.get(platform, {}))
        if hour in schedule.get('avoid_hours', []):
            return {'should_post': False, 'reason': f'Avoid hour ({hour}:00 UTC) for images'}
        
        # Check gap since last image post (minimum 2 hours between image posts) - only for automated
        last_image_time = self._get_last_image_post_time(platform)
        if last_image_time:
            gap_hours = (now - last_image_time).total_seconds() / 3600
            if gap_hours < 2:
                return {'should_post': False, 'reason': f'Too soon for next image ({gap_hours:.1f}h < 2h gap)'}
        
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
            'image_posts_today': image_posts_today,
            'max_image_posts': max_image_posts,
        }

    def record_image_post_made(self, platform: str):
        """Record that an image post was made"""
        now = datetime.datetime.now()
        today_key = now.strftime('%Y-%m-%d')
        key = f'{platform}_image_{today_key}'

        daily_counts = self._content_calendar.get('daily_counts', {})
        daily_counts[key] = daily_counts.get(key, 0) + 1

        self._content_calendar['daily_counts'] = daily_counts
        self._content_calendar[f'{platform}_last_image_post'] = now.isoformat()
        self._save_content_calendar()
        print(f"📸 Image post recorded for {platform} ({daily_counts[key]}/3 today)")

    def _get_image_posts_today(self, platform: str, today_key: str) -> int:
        """Count image posts made today on a platform"""
        daily_counts = self._content_calendar.get('daily_counts', {})
        return daily_counts.get(f'{platform}_image_{today_key}', 0)

    def _get_last_image_post_time(self, platform: str) -> Optional[datetime.datetime]:
        """Get the last image post time for a platform"""
        ts = self._content_calendar.get(f'{platform}_last_image_post')
        if ts:
            try:
                return datetime.datetime.fromisoformat(ts)
            except (ValueError, TypeError):
                pass
        return None

    def _get_last_post_time(self, platform: str) -> Optional[datetime.datetime]:
        """Get the last post time for a platform"""
        ts = self._content_calendar.get(f'{platform}_last_post')
        if ts:
            try:
                return datetime.datetime.fromisoformat(ts)
            except (ValueError, TypeError):
                pass
        return None

    # =========================================================================
    # Conversation Threading — track multi-turn conversations
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
        self._save_conversation_threads()

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

    def get_active_conversations(self) -> List[Dict]:
        """Get recently active conversation threads"""
        now = datetime.datetime.now()
        active = []
        for tid, thread in self._conversation_threads.items():
            if not thread.get('turns'):
                continue
            last_turn = thread['turns'][-1]
            try:
                last_time = datetime.datetime.fromisoformat(last_turn['timestamp'])
                age_hours = (now - last_time).total_seconds() / 3600
                if age_hours < 24:
                    active.append({
                        'thread_id': tid,
                        'participant': thread.get('participant', '?'),
                        'platform': thread.get('platform', '?'),
                        'turns': len(thread['turns']),
                        'topics': thread.get('topics', []),
                        'last_activity': last_turn['timestamp'][:16],
                    })
            except (ValueError, TypeError):
                continue

        active.sort(key=lambda x: x.get('last_activity', ''), reverse=True)
        return active

    # =========================================================================
    # Personality Tuning — configurable tone per platform
    # =========================================================================

    def get_personality(self, platform: str) -> Dict:
        """Get the personality profile for a platform"""
        return self._personalities.get(platform, DEFAULT_PERSONALITIES.get(platform, DEFAULT_PERSONALITIES['moltx']))

    def set_personality(self, platform: str, **kwargs):
        """Update personality settings for a platform"""
        profile = self.get_personality(platform).copy()
        for key, value in kwargs.items():
            if key in profile:
                profile[key] = value
        self._personalities[platform] = profile
        self._save_personalities()

    def get_personality_prompt(self, platform: str) -> str:
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

        return "\n".join(parts)

    # =========================================================================
    # Persistence
    # =========================================================================

    def _load_content_calendar(self) -> Dict:
        try:
            data = self.core.get_memory('content_calendar')
            return data if data and isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_content_calendar(self):
        try:
            self.core.save_memory('content_calendar', self._content_calendar)
        except Exception as e:
            print(f"⚠️  Failed to save content calendar: {e}")

    def _load_conversation_threads(self) -> Dict:
        try:
            data = self.core.get_memory('conversation_threads')
            return data if data and isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_conversation_threads(self):
        try:
            self.core.save_memory('conversation_threads', self._conversation_threads)
        except Exception as e:
            print(f"⚠️  Failed to save conversation threads: {e}")

    def _load_personalities(self) -> Dict:
        try:
            data = self.core.get_memory('personality_profiles')
            if data and isinstance(data, dict):
                # Merge with defaults so new fields are always present
                merged = {}
                for platform in set(list(DEFAULT_PERSONALITIES.keys()) + list(data.keys())):
                    default = DEFAULT_PERSONALITIES.get(platform, {})
                    saved = data.get(platform, {})
                    merged[platform] = {**default, **saved}
                return merged
        except Exception:
            pass
        return dict(DEFAULT_PERSONALITIES)

    def _save_personalities(self):
        try:
            self.core.save_memory('personality_profiles', self._personalities)
        except Exception as e:
            print(f"⚠️  Failed to save personalities: {e}")

    def _load_posting_schedule(self) -> Dict:
        try:
            data = self.core.get_memory('posting_schedule')
            if data and isinstance(data, dict):
                merged = {}
                for platform in set(list(DEFAULT_POSTING_SCHEDULE.keys()) + list(data.keys())):
                    default = DEFAULT_POSTING_SCHEDULE.get(platform, {})
                    saved = data.get(platform, {})
                    merged[platform] = {**default, **saved}
                return merged
        except Exception:
            pass
        return dict(DEFAULT_POSTING_SCHEDULE)

    # =========================================================================
    # Commands
    # =========================================================================

    def calendar_command(self, *args):
        """Show content calendar status"""
        now = datetime.datetime.now()
        today_key = now.strftime('%Y-%m-%d')
        output = f"📅 Content Calendar ({now.strftime('%A %H:%M UTC')})\n\n"

        for platform in ['moltx', 'moltbook']:
            check = self.should_post_now(platform)
            status = '🟢' if check['should_post'] else '🔴'
            output += f"{status} {platform.title()}:\n"

            if check['should_post']:
                output += f"  Quality: {check.get('quality', '?')} | "
                output += f"Posts today: {check.get('posts_today', 0)}/{check.get('max_daily', 3)}\n"
            else:
                output += f"  {check.get('reason', 'Not available')}\n"

            # Image posts status
            image_check = self.should_post_image_now(platform)
            img_status = '📸' if image_check['should_post'] else '⏳'
            output += f"  {img_status} Image posts: {image_check.get('image_posts_today', 0)}/{image_check.get('max_image_posts', 3)}\n"

            queue = self._content_calendar.get(f'{platform}_queue', [])
            if queue:
                output += f"  📋 Queue: {len(queue)} topics ({queue[0][:30]}...)\n"
            else:
                output += f"  📋 Queue: empty\n"

            last = self._get_last_post_time(platform)
            if last:
                ago = (now - last).total_seconds() / 60
                output += f"  ⏱️  Last post: {ago:.0f}min ago\n"
            output += "\n"

        return output

    def conversations_command(self, *args):
        """Show active conversation threads"""
        active = self.get_active_conversations()
        if not active:
            return "💬 No active conversations in the last 24h"

        output = f"💬 Active Conversations ({len(active)}):\n\n"
        for conv in active[:10]:
            output += (
                f"  🗣️  @{conv['participant']} on {conv['platform']} "
                f"({conv['turns']} turns)\n"
                f"     Topics: {', '.join(conv['topics'][:3]) if conv['topics'] else 'general'}\n"
                f"     Last: {conv['last_activity']}\n\n"
            )
        return output

    def personality_command(self, *args):
        """Show or set personality. Usage: personality [platform] [key=value]"""
        if not args:
            output = "🎭 Personality Profiles:\n\n"
            for platform in ['moltx', 'moltbook', 'reply']:
                p = self.get_personality(platform)
                output += f"  📍 {platform}:\n"
                output += f"     Tone: {p.get('tone', '?')} | Humor: {p.get('humor', 0):.1f} | "
                output += f"Formality: {p.get('formality', 0):.1f} | Emoji: {p.get('emoji_density', 0):.1f}\n"
                output += f"     Voice: {p.get('voice', '?')[:60]}\n\n"
            return output

        platform = args[0].lower()
        if len(args) == 1:
            return self.get_personality_prompt(platform)

        # Parse key=value pairs
        updates = {}
        for arg in args[1:]:
            if '=' in arg:
                key, val = arg.split('=', 1)
                try:
                    val = float(val)
                except ValueError:
                    pass
                updates[key] = val

        if updates:
            self.set_personality(platform, **updates)
            return f"✅ Updated {platform} personality: {updates}"

        return "❌ Usage: personality [platform] [key=value ...]"
