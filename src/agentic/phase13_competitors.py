"""
Phase 13.4: Competitor Monitoring System
Track what similar agents/accounts post and their performance
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CompetitorPost:
    """A post from a competitor"""
    competitor_id: str
    platform: str
    content: str
    timestamp: datetime
    engagement: Dict[str, int]
    topic: Optional[str] = None
    content_type: str = 'post'  # post, reply, thread


class CompetitorMonitor:
    """
    Monitors competitor accounts/agents
    Tracks their content, timing, and performance
    """
    
    def __init__(self, db_path: str = 'data/competitors.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize competitor database"""
        with sqlite3.connect(self.db_path) as conn:
            # Tracked competitors
            conn.execute("""
                CREATE TABLE IF NOT EXISTS competitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id TEXT UNIQUE NOT NULL,
                    handle TEXT,
                    platform TEXT NOT NULL,
                    display_name TEXT,
                    category TEXT,  -- e.g., 'ai_agent', 'crypto_influencer', 'tech_news'
                    follower_count INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    notes TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_checked TIMESTAMP
                )
            """)
            
            # Competitor posts
            conn.execute("""
                CREATE TABLE IF NOT EXISTS competitor_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    external_post_id TEXT,
                    content TEXT,
                    content_hash TEXT,  -- For deduplication
                    topic TEXT,
                    content_type TEXT DEFAULT 'post',
                    posted_at TIMESTAMP,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    likes INTEGER DEFAULT 0,
                    replies INTEGER DEFAULT 0,
                    reposts INTEGER DEFAULT 0,
                    impressions INTEGER,
                    engagement_rate REAL,
                    has_media BOOLEAN DEFAULT 0,
                    has_links BOOLEAN DEFAULT 0,
                    sentiment REAL  -- -1 to 1
                )
            """)
            
            # Content patterns detected
            conn.execute("""
                CREATE TABLE IF NOT EXISTS content_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,  -- timing, topic, style, engagement
                    pattern_value TEXT,
                    frequency REAL,  -- 0-1 how often this pattern occurs
                    avg_engagement REAL,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP
                )
            """)
            
            # Performance benchmarks
            conn.execute("""
                CREATE TABLE IF NOT EXISTS benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    metric_name TEXT NOT NULL,  -- avg_likes, post_frequency, etc.
                    metric_value REAL,
                    sample_size INTEGER,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, platform, metric_name)
                )
            """)
            
            conn.commit()
    
    def add_competitor(self, competitor_id: str, platform: str,
                      handle: str = None, display_name: str = None,
                      category: str = None, notes: str = None) -> bool:
        """Add a competitor to track"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO competitors "
                    "(competitor_id, handle, platform, display_name, category, notes) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (competitor_id, handle, platform, display_name, category, notes)
                )
                conn.commit()
                print(f"👁️  Now tracking competitor: {handle or competitor_id} on {platform}")
                return True
        except Exception as e:
            print(f"⚠️ Error adding competitor: {e}")
            return False
    
    def remove_competitor(self, competitor_id: str) -> bool:
        """Stop tracking a competitor"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE competitors SET is_active = 0 WHERE competitor_id = ?",
                    (competitor_id,)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error removing competitor: {e}")
            return False
    
    def record_post(self, post: CompetitorPost) -> bool:
        """Record a competitor post"""
        try:
            import hashlib
            content_hash = hashlib.md5(post.content.encode()).hexdigest()[:16]
            
            # Calculate engagement rate if we have follower count
            engagement_rate = 0
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT follower_count FROM competitors WHERE competitor_id = ?",
                    (post.competitor_id,)
                )
                result = cursor.fetchone()
                if result and result[0] and result[0] > 0:
                    total_eng = (post.engagement.get('likes', 0) + 
                                post.engagement.get('replies', 0) +
                                post.engagement.get('reposts', 0))
                    engagement_rate = total_eng / result[0]
                
                conn.execute(
                    "INSERT INTO competitor_posts "
                    "(competitor_id, platform, content, content_hash, topic, "
                    "content_type, posted_at, likes, replies, reposts, engagement_rate) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (post.competitor_id, post.platform, post.content, content_hash,
                     post.topic, post.content_type, post.timestamp.isoformat(),
                     post.engagement.get('likes', 0),
                     post.engagement.get('replies', 0),
                     post.engagement.get('reposts', 0),
                     engagement_rate)
                )
                
                conn.execute(
                    "UPDATE competitors SET last_checked = ? WHERE competitor_id = ?",
                    (datetime.now().isoformat(), post.competitor_id)
                )
                
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error recording competitor post: {e}")
            return False
    
    def get_competitor_activity(self, competitor_id: str = None,
                               hours: int = 24) -> List[Dict]:
        """Get recent competitor activity"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if competitor_id:
                    cursor = conn.execute(
                        "SELECT * FROM competitor_posts WHERE competitor_id = ? "
                        "AND collected_at > ? ORDER BY posted_at DESC",
                        (competitor_id, cutoff.isoformat())
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM competitor_posts WHERE collected_at > ? "
                        "ORDER BY posted_at DESC",
                        (cutoff.isoformat(),)
                    )
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error getting competitor activity: {e}")
            return []
    
    def analyze_patterns(self, competitor_id: str = None,
                        hours: int = 168) -> Dict:
        """Analyze posting patterns"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get posts
                if competitor_id:
                    cursor = conn.execute(
                        "SELECT * FROM competitor_posts WHERE competitor_id = ? "
                        "AND collected_at > ?",
                        (competitor_id, cutoff.isoformat())
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM competitor_posts WHERE collected_at > ?",
                        (cutoff.isoformat(),)
                    )
                
                posts = [dict(row) for row in cursor.fetchall()]
                
                if not posts:
                    return {'error': 'No data available'}
                
                # Timing patterns
                hours_dist = defaultdict(int)
                for post in posts:
                    try:
                        dt = datetime.fromisoformat(post['posted_at'])
                        hours_dist[dt.hour] += 1
                    except:
                        pass
                
                # Topic analysis
                topics = defaultdict(int)
                for post in posts:
                    if post['topic']:
                        topics[post['topic']] += 1
                
                # Engagement patterns
                avg_engagement = sum(p['engagement_rate'] or 0 for p in posts) / len(posts)
                best_performing = sorted(posts, 
                    key=lambda x: x['engagement_rate'] or 0, reverse=True)[:5]
                
                # Posting frequency
                if len(posts) >= 2:
                    timestamps = sorted([datetime.fromisoformat(p['posted_at']) 
                                       for p in posts if p['posted_at']])
                    if len(timestamps) > 1:
                        total_span = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
                        frequency = len(posts) / max(total_span, 1)  # posts per hour
                    else:
                        frequency = 0
                else:
                    frequency = 0
                
                return {
                    'posts_analyzed': len(posts),
                    'posting_frequency_per_hour': frequency,
                    'avg_engagement_rate': avg_engagement,
                    'peak_hours': sorted(hours_dist.items(), key=lambda x: x[1], reverse=True)[:3],
                    'top_topics': sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5],
                    'best_performing_posts': [
                        {
                            'content_preview': p['content'][:100] + '...' if len(p['content']) > 100 else p['content'],
                            'engagement_rate': p['engagement_rate'],
                            'topic': p['topic']
                        }
                        for p in best_performing_posts[:5]
                    ]
                }
        except Exception as e:
            print(f"⚠️ Error analyzing patterns: {e}")
            return {'error': str(e)}
    
    def get_competitive_insights(self, platform: str = None) -> List[Dict]:
        """Get actionable competitive insights"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get active competitors
                if platform:
                    cursor = conn.execute(
                        "SELECT competitor_id, category FROM competitors "
                        "WHERE platform = ? AND is_active = 1",
                        (platform,)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT competitor_id, category FROM competitors WHERE is_active = 1"
                    )
                
                competitors = cursor.fetchall()
                
                insights = []
                
                for comp in competitors:
                    comp_id = comp['competitor_id']
                    category = comp['category']
                    
                    # Get recent performance
                    cutoff = datetime.now() - timedelta(hours=24)
                    cursor = conn.execute(
                        "SELECT AVG(engagement_rate) as avg_eng, COUNT(*) as count "
                        "FROM competitor_posts WHERE competitor_id = ? AND collected_at > ?",
                        (comp_id, cutoff.isoformat())
                    )
                    result = cursor.fetchone()
                    
                    if result and result['count'] > 0:
                        insights.append({
                            'competitor_id': comp_id,
                            'category': category,
                            'recent_posts': result['count'],
                            'avg_engagement_rate': result['avg_eng'] or 0,
                            'alert': result['avg_eng'] > 0.05  # High engagement alert
                        })
                
                return insights
        except Exception as e:
            print(f"⚠️ Error getting insights: {e}")
            return []
    
    def calculate_benchmarks(self, category: str, platform: str) -> Dict:
        """Calculate performance benchmarks for a category"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get competitors in category
                cursor = conn.execute(
                    "SELECT competitor_id FROM competitors WHERE category = ? AND platform = ?",
                    (category, platform)
                )
                comp_ids = [row['competitor_id'] for row in cursor.fetchall()]
                
                if not comp_ids:
                    return {'error': 'No competitors in category'}
                
                placeholders = ','.join('?' * len(comp_ids))
                
                # Calculate metrics
                cutoff = datetime.now() - timedelta(days=7)
                
                cursor = conn.execute(
                    f"SELECT AVG(likes) as avg_likes, AVG(replies) as avg_replies, "
                    f"AVG(reposts) as avg_reposts, AVG(engagement_rate) as avg_rate, "
                    f"COUNT(*) as total_posts "
                    f"FROM competitor_posts WHERE competitor_id IN ({placeholders}) "
                    f"AND collected_at > ?",
                    comp_ids + [cutoff.isoformat()]
                )
                result = cursor.fetchone()
                
                benchmarks = {
                    'category': category,
                    'platform': platform,
                    'competitors_count': len(comp_ids),
                    'avg_likes': result['avg_likes'] or 0,
                    'avg_replies': result['avg_replies'] or 0,
                    'avg_reposts': result['avg_reposts'] or 0,
                    'avg_engagement_rate': result['avg_rate'] or 0,
                    'posts_analyzed': result['total_posts'] or 0,
                    'calculated_at': datetime.now().isoformat()
                }
                
                # Store benchmarks
                for metric, value in [
                    ('avg_likes', benchmarks['avg_likes']),
                    ('avg_replies', benchmarks['avg_replies']),
                    ('avg_reposts', benchmarks['avg_reposts']),
                    ('engagement_rate', benchmarks['avg_engagement_rate'])
                ]:
                    conn.execute(
                        "INSERT OR REPLACE INTO benchmarks "
                        "(category, platform, metric_name, metric_value, sample_size, calculated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (category, platform, metric, value, 
                         benchmarks['posts_analyzed'], datetime.now().isoformat())
                    )
                
                conn.commit()
                
                return benchmarks
        except Exception as e:
            print(f"⚠️ Error calculating benchmarks: {e}")
            return {'error': str(e)}
    
    def get_tracked_competitors(self, active_only: bool = True) -> List[Dict]:
        """Get list of tracked competitors"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if active_only:
                    cursor = conn.execute(
                        "SELECT * FROM competitors WHERE is_active = 1 ORDER BY added_at DESC"
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM competitors ORDER BY added_at DESC"
                    )
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error getting competitors: {e}")
            return []


class CompetitorAlertSystem:
    """Alerts on competitor activity"""
    
    def __init__(self, monitor: CompetitorMonitor, alert_callback=None):
        self.monitor = monitor
        self.alert_callback = alert_callback
        self.alert_thresholds = {
            'high_engagement': 0.05,  # 5% engagement rate
            'frequent_posting': 5,     # 5 posts per hour
            'viral_velocity': 1000     # 1000 likes in first hour
        }
    
    async def check_alerts(self):
        """Check for competitor alerts"""
        try:
            insights = self.monitor.get_competitive_insights()
            
            for insight in insights:
                if insight.get('alert'):
                    message = (f"🔔 Competitor Alert: {insight['competitor_id']} "
                              f"high engagement ({insight['avg_engagement_rate']:.2%})")
                    
                    print(message)
                    
                    if self.alert_callback:
                        await self.alert_callback({
                            'type': 'high_engagement',
                            'competitor': insight['competitor_id'],
                            'message': message,
                            'engagement_rate': insight['avg_engagement_rate']
                        })
        except Exception as e:
            print(f"⚠️ Error checking alerts: {e}")
