"""
Feedback Loop Mixin
Tracks engagement on AlleyBot's posts, learns what content styles work,
and feeds insights back into the brain's decision-making and post generation.

Phase 6 of the AlleyBot roadmap.
"""
import datetime
import json
from typing import Dict, Any, Optional, List


# Content style tags we track
STYLE_TAGS = [
    'hot_take', 'question', 'technical', 'story', 'analogy',
    'data_driven', 'opinion', 'humor', 'thread', 'quote',
    'market_update', 'builder_log', 'contrarian', 'educational',
]


class FeedbackLoopMixin:
    """Mixin for post-engagement tracking and content strategy learning"""
    
    # Mixin metadata for documentation and validation
    REQUIRES = ["world_state"]
    PROVIDES = ["track_post", "get_engagement_stats", "learn_from_feedback"]
    INIT_ORDER = 6

    def _init_feedback_loop(self):
        """Initialize feedback loop state"""
        self._post_tracker = self._load_post_tracker()
        self._style_scores = self._load_style_scores()

    # =========================================================================
    # Post Tracking — record every post we make with metadata
    # =========================================================================

    def track_post(self, post_id: str, platform: str, content: str,
                   source: str = 'unknown', style_tags: List[str] = None):
        """Track a new post we created for later engagement checking"""
        now = datetime.datetime.now()
        entry = {
            'post_id': post_id,
            'platform': platform,
            'content': content[:300],
            'content_length': len(content),
            'source': source,
            'style_tags': style_tags or self._auto_tag_content(content),
            'created_at': now.isoformat(),
            'hour_of_day': now.hour,
            'day_of_week': now.strftime('%A'),
            'engagement': {
                'likes': 0,
                'replies': 0,
                'quotes': 0,
                'reposts': 0,
                'score': 0,
            },
            'checks': 0,
            'last_checked': None,
        }
        self._post_tracker.append(entry)
        self._post_tracker = self._post_tracker[-200:]
        self._save_post_tracker()
        print(f"📊 Tracking post {post_id} on {platform} (tags: {entry['style_tags']})")

    def _auto_tag_content(self, content: str) -> List[str]:
        """Auto-detect content style tags from the text"""
        tags = []
        lower = content.lower()

        if '?' in content and len(content) < 200:
            tags.append('question')
        if any(w in lower for w in ['$', 'price', 'market', 'bull', 'bear', '%']):
            tags.append('market_update')
        if any(w in lower for w in ['built', 'shipped', 'deployed', 'launched', 'building']):
            tags.append('builder_log')
        if any(w in lower for w in ['actually', 'unpopular', 'hot take', 'controversial', 'disagree']):
            tags.append('contrarian')
        if any(w in lower for w in ['learned', 'lesson', 'mistake', 'realized']):
            tags.append('educational')
        if any(w in lower for w in ['story', 'once', 'remember when', 'back when']):
            tags.append('story')
        if any(w in lower for w in ['like', 'similar to', 'analogy', 'imagine']):
            tags.append('analogy')
        if any(w in lower for w in ['data', 'numbers', 'stats', 'according']):
            tags.append('data_driven')
        if any(w in lower for w in ['lol', 'lmao', '😂', '🤣', 'funny']):
            tags.append('humor')
        if any(w in lower for w in ['think', 'believe', 'imo', 'my take']):
            tags.append('opinion')
        if any(w in lower for w in ['code', 'api', 'function', 'deploy', 'contract', 'solidity']):
            tags.append('technical')

        if not tags:
            tags.append('hot_take')

        return tags

    # =========================================================================
    # Engagement Checking — fetch current engagement on our tracked posts
    # =========================================================================

    def check_post_engagement(self) -> str:
        """Check engagement on our recent posts and update metrics"""
        if not self._post_tracker:
            return "📊 No tracked posts to check"

        plugins = self.core.plugin_manager.plugins
        now = datetime.datetime.now()
        checked = 0
        updated = 0

        # Only check posts from last 48 hours that haven't been checked in 30+ min
        for entry in self._post_tracker:
            try:
                created = datetime.datetime.fromisoformat(entry['created_at'])
                age_hours = (now - created).total_seconds() / 3600

                # Skip posts older than 48h
                if age_hours > 48:
                    continue

                # Skip if checked recently (within 30 min)
                if entry.get('last_checked'):
                    last_check = datetime.datetime.fromisoformat(entry['last_checked'])
                    if (now - last_check).total_seconds() < 1800:
                        continue

                platform = entry['platform']
                post_id = entry['post_id']

                new_engagement = None
                if platform == 'moltx':
                    new_engagement = self._fetch_moltx_engagement(post_id, plugins)
                elif platform == 'moltbook':
                    new_engagement = self._fetch_moltbook_engagement(post_id, plugins)

                if new_engagement:
                    old_score = entry['engagement'].get('score', 0)
                    entry['engagement'] = new_engagement
                    entry['checks'] += 1
                    entry['last_checked'] = now.isoformat()
                    updated += 1

                    if new_engagement['score'] > old_score:
                        print(f"  📈 Post {post_id[:8]}... score: {old_score} → {new_engagement['score']}")

                checked += 1

            except Exception as e:
                print(f"  ⚠️  Error checking post {entry.get('post_id', '?')}: {e}")

        if updated > 0:
            self._save_post_tracker()
            self._update_style_scores()

        return f"📊 Checked {checked} posts, {updated} updated"

    def _fetch_moltx_engagement(self, post_id: str, plugins: Dict) -> Optional[Dict]:
        """Fetch engagement metrics for a MoltX post"""
        moltx = plugins.get('moltx')
        if not moltx:
            return None

        try:
            result = moltx._make_request('GET', f'/posts/{post_id}')
            if not result:
                return None

            data = result.get('data', result) if isinstance(result, dict) else {}
            post = data.get('post', data) if isinstance(data, dict) else {}

            likes = post.get('like_count', post.get('likes_count', 0)) or 0
            replies = post.get('reply_count', post.get('replies_count', 0)) or 0
            quotes = post.get('quote_count', post.get('quotes_count', 0)) or 0
            reposts = post.get('repost_count', post.get('reposts_count', 0)) or 0

            # Weighted engagement score
            score = likes + (replies * 3) + (quotes * 5) + (reposts * 2)

            return {
                'likes': likes,
                'replies': replies,
                'quotes': quotes,
                'reposts': reposts,
                'score': score,
            }
        except Exception as e:
            print(f"  ⚠️  MoltX engagement fetch error: {e}")
            return None

    def _fetch_moltbook_engagement(self, post_id: str, plugins: Dict) -> Optional[Dict]:
        """Fetch engagement metrics for a MoltBook post"""
        moltbook = plugins.get('moltbook')
        if not moltbook or not hasattr(moltbook, 'mb_api'):
            return None

        try:
            response = moltbook.mb_api.session.get(
                f"{moltbook.mb_api.base_url}/posts/{post_id}",
                timeout=10
            )
            if response.status_code != 200:
                return None

            data = response.json()
            post = data.get('data', data) if isinstance(data, dict) else {}

            upvotes = post.get('upvotes', post.get('score', 0)) or 0
            comments = post.get('comments', post.get('comment_count', 0)) or 0

            score = upvotes + (comments * 3)

            return {
                'likes': upvotes,
                'replies': comments,
                'quotes': 0,
                'reposts': 0,
                'score': score,
            }
        except Exception as e:
            print(f"  ⚠️  MoltBook engagement fetch error: {e}")
            return None

    # =========================================================================
    # Style Learning — figure out what content styles get the most engagement
    # =========================================================================

    def _update_style_scores(self):
        """Recalculate style scores based on tracked post engagement"""
        tag_stats = {}

        for entry in self._post_tracker:
            score = entry.get('engagement', {}).get('score', 0)
            tags = entry.get('style_tags', [])
            hour = entry.get('hour_of_day', 12)
            platform = entry.get('platform', 'unknown')
            length = entry.get('content_length', 0)

            for tag in tags:
                if tag not in tag_stats:
                    tag_stats[tag] = {
                        'total_score': 0,
                        'count': 0,
                        'best_score': 0,
                        'best_hours': [],
                        'avg_length': 0,
                        'total_length': 0,
                    }
                tag_stats[tag]['total_score'] += score
                tag_stats[tag]['count'] += 1
                tag_stats[tag]['total_length'] += length
                if score > tag_stats[tag]['best_score']:
                    tag_stats[tag]['best_score'] = score
                    tag_stats[tag]['best_hours'].append(hour)
                    tag_stats[tag]['best_hours'] = tag_stats[tag]['best_hours'][-5:]

        # Calculate averages
        self._style_scores = {}
        for tag, stats in tag_stats.items():
            if stats['count'] > 0:
                self._style_scores[tag] = {
                    'avg_score': stats['total_score'] / stats['count'],
                    'count': stats['count'],
                    'best_score': stats['best_score'],
                    'avg_length': stats['total_length'] / stats['count'],
                    'best_hours': list(set(stats['best_hours'])),
                }

        self._save_style_scores()

    def get_content_insights(self) -> str:
        """Get human-readable content performance insights"""
        if not self._style_scores:
            return "📊 No engagement data yet — need more tracked posts"

        # Sort by average score
        sorted_styles = sorted(
            self._style_scores.items(),
            key=lambda x: x[1]['avg_score'],
            reverse=True
        )

        output = "📊 Content Performance Insights\n\n"

        # Top performing styles
        output += "🏆 Best Performing Styles:\n"
        for tag, stats in sorted_styles[:5]:
            output += (
                f"  {'🟢' if stats['avg_score'] >= 5 else '🟡' if stats['avg_score'] >= 2 else '🔴'} "
                f"#{tag}: avg {stats['avg_score']:.1f} score "
                f"({stats['count']} posts, best: {stats['best_score']})\n"
            )

        # Worst performing
        if len(sorted_styles) > 5:
            output += "\n⚠️  Underperforming Styles:\n"
            for tag, stats in sorted_styles[-3:]:
                output += f"  🔴 #{tag}: avg {stats['avg_score']:.1f} ({stats['count']} posts)\n"

        # Best posting times
        all_best_hours = []
        for tag, stats in sorted_styles[:3]:
            all_best_hours.extend(stats.get('best_hours', []))
        if all_best_hours:
            from collections import Counter
            hour_counts = Counter(all_best_hours)
            best_hour = hour_counts.most_common(1)[0][0]
            output += f"\n⏰ Best posting hour: {best_hour}:00 UTC\n"

        # Optimal length
        lengths = [(s['avg_length'], s['avg_score']) for s in self._style_scores.values() if s['count'] >= 2]
        if lengths:
            best_length = max(lengths, key=lambda x: x[1])
            output += f"📏 Best performing length: ~{best_length[0]:.0f} chars\n"

        return output

    def get_style_prompt_hint(self) -> str:
        """Generate a prompt hint for post generation based on learned styles"""
        if not self._style_scores:
            return ""

        sorted_styles = sorted(
            self._style_scores.items(),
            key=lambda x: x[1]['avg_score'],
            reverse=True
        )

        # Get top 3 styles
        top_styles = [tag for tag, _ in sorted_styles[:3] if sorted_styles[0][1]['avg_score'] > 0]
        # Get bottom styles to avoid
        bottom_styles = [tag for tag, stats in sorted_styles[-2:] if stats['count'] >= 3 and stats['avg_score'] < 2]

        hints = []
        if top_styles:
            hints.append(f"Your best-performing content styles are: {', '.join(top_styles)}. Lean into these.")
        if bottom_styles:
            hints.append(f"Avoid these underperforming styles: {', '.join(bottom_styles)}.")

        # Length hint
        lengths = [(s['avg_length'], s['avg_score']) for s in self._style_scores.values() if s['count'] >= 2]
        if lengths:
            best = max(lengths, key=lambda x: x[1])
            hints.append(f"Optimal post length is around {best[0]:.0f} characters.")

        return "\n".join(hints)

    # =========================================================================
    # Persistence
    # =========================================================================

    def _load_post_tracker(self) -> List[Dict]:
        """Load tracked posts from memory"""
        try:
            data = self.core.get_memory('feedback_post_tracker')
            if data and isinstance(data, list):
                return data
        except Exception:
            pass
        return []

    def _save_post_tracker(self):
        """Save tracked posts to memory"""
        try:
            self.core.save_memory('feedback_post_tracker', self._post_tracker[-200:])
        except Exception as e:
            print(f"⚠️  Failed to save post tracker: {e}")

    def _load_style_scores(self) -> Dict:
        """Load style scores from memory"""
        try:
            data = self.core.get_memory('feedback_style_scores')
            if data and isinstance(data, dict):
                return data
        except Exception:
            pass
        return {}

    def _save_style_scores(self):
        """Save style scores to memory"""
        try:
            self.core.save_memory('feedback_style_scores', self._style_scores)
        except Exception as e:
            print(f"⚠️  Failed to save style scores: {e}")

    # =========================================================================
    # Commands
    # =========================================================================

    def feedback_insights_command(self, *args):
        """Show content performance insights"""
        return self.get_content_insights()

    def feedback_check_command(self, *args):
        """Check engagement on tracked posts"""
        return self.check_post_engagement()

    def feedback_tracked_command(self, *args):
        """Show tracked posts"""
        if not self._post_tracker:
            return "📊 No tracked posts"

        output = f"📊 Tracked Posts ({len(self._post_tracker)}):\n\n"
        for entry in self._post_tracker[-10:]:
            score = entry.get('engagement', {}).get('score', 0)
            likes = entry.get('engagement', {}).get('likes', 0)
            replies = entry.get('engagement', {}).get('replies', 0)
            tags = ', '.join(entry.get('style_tags', []))
            created = entry.get('created_at', '?')[:16]
            output += (
                f"  {'🟢' if score >= 5 else '🟡' if score >= 1 else '⚪'} "
                f"{entry['platform']} | {created} | "
                f"❤️{likes} 💬{replies} | score:{score} | [{tags}]\n"
                f"    {entry.get('content', '')[:80]}...\n\n"
            )
        return output
