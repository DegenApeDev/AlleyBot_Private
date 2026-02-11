"""
Phase 12: Memory & Learning System
Tracks long-term patterns, user relationships, and content performance
"""
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class ContentPerformance:
    """Performance metrics for a piece of content"""
    content_id: str
    platform: str
    content_type: str  # post, debate, reply, etc.
    topic: str
    created_at: datetime
    engagement_score: float = 0.0
    likes: int = 0
    replies: int = 0
    reposts: int = 0
    views: int = 0
    sentiment: str = 'neutral'
    
    def to_dict(self):
        return {
            'content_id': self.content_id,
            'platform': self.platform,
            'content_type': self.content_type,
            'topic': self.topic,
            'created_at': self.created_at.isoformat(),
            'engagement_score': self.engagement_score,
            'likes': self.likes,
            'replies': self.replies,
            'reposts': self.reposts,
            'views': self.views,
            'sentiment': self.sentiment
        }


@dataclass
class UserRelationship:
    """Track relationship with a specific user"""
    user_id: str
    platform: str
    username: str
    first_interaction: datetime
    last_interaction: datetime
    interaction_count: int = 0
    preferred_topics: List[str] = None
    sentiment_trend: str = 'neutral'  # positive, neutral, negative
    notes: str = ''
    
    def __post_init__(self):
        if self.preferred_topics is None:
            self.preferred_topics = []
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'platform': self.platform,
            'username': self.username,
            'first_interaction': self.first_interaction.isoformat(),
            'last_interaction': self.last_interaction.isoformat(),
            'interaction_count': self.interaction_count,
            'preferred_topics': self.preferred_topics,
            'sentiment_trend': self.sentiment_trend,
            'notes': self.notes
        }


class ContentPerformanceDB:
    """
    SQLite database for persistent content performance tracking
    Phase 12.3: Content performance database
    """
    
    def __init__(self, db_path: str = 'data/performance.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS content_performance (
                    content_id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    topic TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    likes INTEGER DEFAULT 0,
                    replies INTEGER DEFAULT 0,
                    reposts INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    engagement_score REAL DEFAULT 0.0,
                    sentiment TEXT DEFAULT 'neutral',
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS topic_performance (
                    topic TEXT PRIMARY KEY,
                    platform TEXT,
                    total_posts INTEGER DEFAULT 0,
                    total_engagement REAL DEFAULT 0.0,
                    avg_engagement REAL DEFAULT 0.0,
                    best_performing_content_id TEXT,
                    last_posted TIMESTAMP,
                    weekly_scores TEXT  -- JSON of weekly performance
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    date TEXT PRIMARY KEY,
                    platform TEXT,
                    posts_count INTEGER DEFAULT 0,
                    total_engagement REAL DEFAULT 0.0,
                    top_topic TEXT,
                    metadata TEXT
                )
            """)
            
            conn.commit()
    
    def record_content(self, content_id: str, platform: str, content_type: str,
                      topic: str, metadata: Optional[Dict] = None) -> bool:
        """Record new content for tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO content_performance 
                    (content_id, platform, content_type, topic, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    content_id, platform, content_type, topic,
                    datetime.now().isoformat(),
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error recording content: {e}")
            return False
    
    def update_engagement(self, content_id: str, likes: int = 0, 
                         replies: int = 0, reposts: int = 0, 
                         views: int = 0) -> bool:
        """Update engagement metrics for content"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Calculate engagement score: weighted combination
                conn.execute("""
                    UPDATE content_performance 
                    SET likes = likes + ?,
                        replies = replies + ?,
                        reposts = reposts + ?,
                        views = views + ?,
                        engagement_score = (likes + ?) * 1 + (replies + ?) * 3 + 
                                         (reposts + ?) * 5 + (views + ?) * 0.1
                    WHERE content_id = ?
                """, (likes, replies, reposts, views, likes, replies, reposts, views, content_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error updating engagement: {e}")
            return False
    
    def get_topic_performance(self, days: int = 30) -> Dict[str, Dict]:
        """
        Phase 12.1: Long-term pattern learning
        Get performance metrics by topic over time
        """
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT 
                        topic,
                        COUNT(*) as post_count,
                        AVG(engagement_score) as avg_engagement,
                        SUM(likes) as total_likes,
                        SUM(replies) as total_replies,
                        SUM(reposts) as total_reposts,
                        MAX(engagement_score) as best_score
                    FROM content_performance
                    WHERE created_at > ? AND topic IS NOT NULL
                    GROUP BY topic
                    ORDER BY avg_engagement DESC
                """, (cutoff,))
                
                results = {}
                for row in cursor.fetchall():
                    results[row['topic']] = {
                        'post_count': row['post_count'],
                        'avg_engagement': round(row['avg_engagement'], 2),
                        'total_likes': row['total_likes'],
                        'total_replies': row['total_replies'],
                        'total_reposts': row['total_reposts'],
                        'best_score': round(row['best_score'], 2)
                    }
                return results
        except Exception as e:
            print(f"⚠️ Error getting topic performance: {e}")
            return {}
    
    def get_weekly_trends(self, weeks: int = 4) -> Dict[str, List]:
        """Get weekly performance trends"""
        try:
            results = {}
            now = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                for week in range(weeks):
                    week_start = now - timedelta(weeks=week + 1)
                    week_end = now - timedelta(weeks=week)
                    
                    cursor = conn.execute("""
                        SELECT 
                            topic,
                            COUNT(*) as count,
                            AVG(engagement_score) as avg_engagement
                        FROM content_performance
                        WHERE created_at BETWEEN ? AND ?
                        GROUP BY topic
                    """, (week_start.isoformat(), week_end.isoformat()))
                    
                    week_key = f"week_{week + 1}"
                    results[week_key] = [dict(row) for row in cursor.fetchall()]
            
            return results
        except Exception as e:
            print(f"⚠️ Error getting weekly trends: {e}")
            return {}
    
    def get_best_topics(self, limit: int = 5, days: int = 30) -> List[Dict]:
        """Get top performing topics"""
        performance = self.get_topic_performance(days)
        sorted_topics = sorted(
            performance.items(),
            key=lambda x: x[1]['avg_engagement'],
            reverse=True
        )
        return [
            {'topic': topic, **data}
            for topic, data in sorted_topics[:limit]
        ]
    
    def get_content_report(self, content_id: str) -> Optional[Dict]:
        """Get full performance report for specific content"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM content_performance WHERE content_id = ?",
                    (content_id,)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            print(f"⚠️ Error getting content report: {e}")
            return None


class UserRelationshipTracker:
    """
    Phase 12.2: User relationship tracking
    Maintains persistent records of user interactions and preferences
    """
    
    def __init__(self, db_path: str = 'data/relationships.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize relationship database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_relationships (
                    user_id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    username TEXT,
                    first_interaction TIMESTAMP,
                    last_interaction TIMESTAMP,
                    interaction_count INTEGER DEFAULT 0,
                    preferred_topics TEXT,  -- JSON list
                    sentiment_trend TEXT DEFAULT 'neutral',
                    notes TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interaction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    platform TEXT,
                    interaction_type TEXT,  -- like, reply, debate, follow
                    content_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sentiment TEXT,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES user_relationships(user_id)
                )
            """)
            
            conn.commit()
    
    def record_interaction(self, user_id: str, platform: str, 
                          interaction_type: str, username: str = None,
                          content_id: str = None, sentiment: str = 'neutral',
                          notes: str = '') -> bool:
        """Record an interaction with a user"""
        try:
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                # Check if user exists
                cursor = conn.execute(
                    "SELECT interaction_count FROM user_relationships WHERE user_id = ?",
                    (user_id,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing relationship
                    conn.execute("""
                        UPDATE user_relationships 
                        SET last_interaction = ?,
                            interaction_count = interaction_count + 1,
                            sentiment_trend = ?
                        WHERE user_id = ?
                    """, (now, sentiment, user_id))
                else:
                    # Create new relationship
                    conn.execute("""
                        INSERT INTO user_relationships 
                        (user_id, platform, username, first_interaction, 
                         last_interaction, interaction_count, sentiment_trend, notes)
                        VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                    """, (user_id, platform, username, now, now, sentiment, notes))
                
                # Record in history
                conn.execute("""
                    INSERT INTO interaction_history 
                    (user_id, platform, interaction_type, content_id, timestamp, sentiment, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, platform, interaction_type, content_id, now, sentiment, notes))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error recording interaction: {e}")
            return False
    
    def update_user_preferences(self, user_id: str, topics: List[str]) -> bool:
        """Update user's preferred topics based on interactions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT preferred_topics FROM user_relationships WHERE user_id = ?",
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if row and row[0]:
                    existing = json.loads(row[0])
                    # Merge and deduplicate
                    all_topics = list(set(existing + topics))
                else:
                    all_topics = topics
                
                conn.execute(
                    "UPDATE user_relationships SET preferred_topics = ? WHERE user_id = ?",
                    (json.dumps(all_topics), user_id)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error updating preferences: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get full profile for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM user_relationships WHERE user_id = ?",
                    (user_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return None
                
                profile = dict(row)
                # Parse JSON fields
                if profile.get('preferred_topics'):
                    profile['preferred_topics'] = json.loads(profile['preferred_topics'])
                
                # Get recent interactions
                cursor = conn.execute("""
                    SELECT * FROM interaction_history 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, (user_id,))
                profile['recent_interactions'] = [dict(r) for r in cursor.fetchall()]
                
                return profile
        except Exception as e:
            print(f"⚠️ Error getting user profile: {e}")
            return None
    
    def get_active_users(self, days: int = 7, limit: int = 20) -> List[Dict]:
        """Get most active users in recent period"""
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM user_relationships 
                    WHERE last_interaction > ?
                    ORDER BY interaction_count DESC
                    LIMIT ?
                """, (cutoff, limit))
                
                users = []
                for row in cursor.fetchall():
                    user = dict(row)
                    if user.get('preferred_topics'):
                        user['preferred_topics'] = json.loads(user['preferred_topics'])
                    users.append(user)
                return users
        except Exception as e:
            print(f"⚠️ Error getting active users: {e}")
            return []
    
    def search_users_by_topic(self, topic: str) -> List[Dict]:
        """Find users interested in a specific topic"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM user_relationships WHERE preferred_topics LIKE ?",
                    (f'%"{topic}"%',)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error searching users: {e}")
            return []


class Phase12LearningMixin:
    """
    Main mixin for Phase 12 Memory & Learning features
    Integrates performance tracking and user relationships
    """
    
    def __init__(self, *args, **kwargs):
        self.performance_db = ContentPerformanceDB()
        self.user_tracker = UserRelationshipTracker()
    
    # Content Performance Methods
    def record_content_performance(self, content_id: str, platform: str,
                                   content_type: str, topic: str,
                                   metadata: Optional[Dict] = None) -> bool:
        """Record content for performance tracking"""
        return self.performance_db.record_content(content_id, platform, 
                                                  content_type, topic, metadata)
    
    def update_content_engagement(self, content_id: str, likes: int = 0,
                                  replies: int = 0, reposts: int = 0,
                                  views: int = 0) -> bool:
        """Update engagement metrics"""
        return self.performance_db.update_engagement(content_id, likes, 
                                                     replies, reposts, views)
    
    def get_top_topics(self, limit: int = 5, days: int = 30) -> List[Dict]:
        """Get best performing topics"""
        return self.performance_db.get_best_topics(limit, days)
    
    def get_topic_trends(self, weeks: int = 4) -> Dict:
        """Get weekly topic performance trends"""
        return self.performance_db.get_weekly_trends(weeks)
    
    def generate_content_strategy(self) -> Dict:
        """
        Generate recommendations based on performance data
        Phase 12.1: Long-term pattern learning output
        """
        top_topics = self.get_top_topics(limit=10, days=30)
        trends = self.get_topic_trends(weeks=4)
        
        # Identify rising/falling topics
        rising = []
        falling = []
        
        for topic_data in top_topics:
            topic = topic_data['topic']
            # Check week-over-week trend
            weekly_scores = []
            for week_key, week_data in trends.items():
                for item in week_data:
                    if item.get('topic') == topic:
                        weekly_scores.append(item.get('avg_engagement', 0))
            
            if len(weekly_scores) >= 2:
                if weekly_scores[0] > weekly_scores[-1] * 1.2:
                    rising.append(topic)
                elif weekly_scores[-1] > weekly_scores[0] * 1.2:
                    falling.append(topic)
        
        return {
            'top_topics': top_topics,
            'rising_topics': rising,
            'falling_topics': falling,
            'recommendations': [
                f"Focus on: {t['topic']}" for t in top_topics[:3]
            ] if top_topics else []
        }
    
    # User Relationship Methods
    def track_user_interaction(self, user_id: str, platform: str,
                               interaction_type: str, username: str = None,
                               content_id: str = None, sentiment: str = 'neutral',
                               topics: List[str] = None) -> bool:
        """Track an interaction with a user"""
        success = self.user_tracker.record_interaction(
            user_id, platform, interaction_type, username,
            content_id, sentiment
        )
        
        if success and topics:
            self.user_tracker.update_user_preferences(user_id, topics)
        
        return success
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user's relationship profile"""
        return self.user_tracker.get_user_profile(user_id)
    
    def get_active_community_members(self, days: int = 7) -> List[Dict]:
        """Get most active community members"""
        return self.user_tracker.get_active_users(days)
    
    def find_users_by_interest(self, topic: str) -> List[Dict]:
        """Find users interested in a topic"""
        return self.user_tracker.search_users_by_topic(topic)
    
    def get_relationship_summary(self) -> Dict:
        """Get summary of user relationships"""
        active_users = self.get_active_community_members(days=30)
        
        # Calculate sentiment distribution
        sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
        for user in active_users:
            trend = user.get('sentiment_trend', 'neutral')
            sentiments[trend] = sentiments.get(trend, 0) + 1
        
        return {
            'total_tracked_users': len(active_users),
            'highly_engaged': len([u for u in active_users if u.get('interaction_count', 0) > 5]),
            'sentiment_distribution': sentiments,
            'top_contributors': active_users[:5]
        }
