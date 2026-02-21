"""
Phase 13.1: Smart Scheduling System
Posts content when engagement is highest per platform
Uses historical performance data to optimize timing
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import asyncio


@dataclass
class OptimalTimeSlot:
    """Represents an optimal posting time"""
    day_of_week: int  # 0=Monday, 6=Sunday
    hour: int  # 0-23
    engagement_score: float
    confidence: float  # Based on sample size
    sample_size: int


class SmartScheduler:
    """
    Analyzes historical engagement to find optimal posting times
    Schedules content for maximum impact
    """
    
    def __init__(self, db_path: str = 'data/scheduler.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.schedule_queue: List[Dict] = []
    
    def _init_db(self):
        """Initialize scheduler database"""
        with sqlite3.connect(self.db_path) as conn:
            # Historical engagement by time slot
            conn.execute("""
                CREATE TABLE IF NOT EXISTS time_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    day_of_week INTEGER NOT NULL,  -- 0-6
                    hour INTEGER NOT NULL,  -- 0-23
                    posts_count INTEGER DEFAULT 0,
                    avg_engagement REAL DEFAULT 0,
                    total_likes INTEGER DEFAULT 0,
                    total_replies INTEGER DEFAULT 0,
                    total_reposts INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, day_of_week, hour)
                )
            """)
            
            # Scheduled posts queue
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    content_type TEXT DEFAULT 'post',
                    optimal_time TIMESTAMP,
                    scheduled_time TIMESTAMP,
                    posted_time TIMESTAMP,
                    status TEXT DEFAULT 'pending',  -- pending, scheduled, posted, cancelled
                    priority INTEGER DEFAULT 5,  -- 1-10, lower = more urgent
                    engagement_prediction REAL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Platform activity log for pattern analysis
            conn.execute("""
                CREATE TABLE IF NOT EXISTS platform_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active_users INTEGER,  -- proxy metric if available
                    trending_score REAL,  -- how "hot" the platform is
                    metadata TEXT
                )
            """)
            
            conn.commit()
    
    def record_post_performance(self, platform: str, post_time: datetime,
                                engagement: Dict[str, int]) -> bool:
        """Record when a post was made and its performance"""
        try:
            day = post_time.weekday()
            hour = post_time.hour
            
            likes = engagement.get('likes', 0)
            replies = engagement.get('replies', 0)
            reposts = engagement.get('reposts', 0)
            
            # Calculate engagement score
            score = likes + (replies * 2) + (reposts * 3)
            
            with sqlite3.connect(self.db_path) as conn:
                # Check if slot exists
                cursor = conn.execute(
                    "SELECT posts_count, avg_engagement, total_likes, total_replies, total_reposts "
                    "FROM time_performance WHERE platform = ? AND day_of_week = ? AND hour = ?",
                    (platform, day, hour)
                )
                existing = cursor.fetchone()
                
                if existing:
                    old_count, old_avg, old_likes, old_replies, old_reposts = existing
                    new_count = old_count + 1
                    # Weighted average for engagement
                    new_avg = ((old_avg * old_count) + score) / new_count
                    
                    conn.execute(
                        "UPDATE time_performance SET posts_count = ?, avg_engagement = ?, "
                        "total_likes = ?, total_replies = ?, total_reposts = ?, "
                        "last_updated = ? WHERE platform = ? AND day_of_week = ? AND hour = ?",
                        (new_count, new_avg, old_likes + likes,
                         old_replies + replies, old_reposts + reposts,
                         datetime.now().isoformat(), platform, day, hour)
                    )
                else:
                    conn.execute(
                        "INSERT INTO time_performance "
                        "(platform, day_of_week, hour, posts_count, avg_engagement, "
                        "total_likes, total_replies, total_reposts) VALUES (?, ?, ?, 1, ?, ?, ?, ?)",
                        (platform, day, hour, score, likes, replies, reposts)
                    )
                
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error recording post performance: {e}")
            return False
    
    def get_optimal_times(self, platform: str, limit: int = 5) -> List[OptimalTimeSlot]:
        """Get best posting times for a platform"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT day_of_week, hour, posts_count, avg_engagement "
                    "FROM time_performance WHERE platform = ? AND posts_count >= 3 "
                    "ORDER BY avg_engagement DESC LIMIT ?",
                    (platform, limit)
                )
                
                slots = []
                for row in cursor.fetchall():
                    # Confidence based on sample size
                    confidence = min(row['posts_count'] / 10, 1.0)  # Max at 10+ samples
                    slots.append(OptimalTimeSlot(
                        day_of_week=row['day_of_week'],
                        hour=row['hour'],
                        engagement_score=row['avg_engagement'],
                        confidence=confidence,
                        sample_size=row['posts_count']
                    ))
                
                return slots
        except Exception as e:
            print(f"⚠️ Error getting optimal times: {e}")
            return []
    
    def predict_best_time(self, platform: str, 
                         within_hours: int = 48) -> Optional[datetime]:
        """Predict the best time to post within the next N hours"""
        optimal_slots = self.get_optimal_times(platform, limit=10)
        
        if not optimal_slots:
            # Default: tomorrow at 9am
            tomorrow = datetime.now() + timedelta(days=1)
            return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        
        now = datetime.now()
        best_time = None
        best_score = -1
        
        # Check each slot within the window
        for slot in optimal_slots:
            # Find next occurrence of this slot
            days_ahead = slot.day_of_week - now.weekday()
            if days_ahead < 0:
                days_ahead += 7
            
            slot_time = now + timedelta(days=days_ahead)
            slot_time = slot_time.replace(hour=slot.hour, minute=0, second=0)
            
            # If this slot is within our window
            if slot_time > now and (slot_time - now).total_seconds() <= within_hours * 3600:
                # Score = engagement * confidence
                score = slot.engagement_score * slot.confidence
                if score > best_score:
                    best_score = score
                    best_time = slot_time
        
        return best_time
    
    def schedule_post(self, content: str, platform: str,
                     content_type: str = 'post', priority: int = 5,
                     target_time: Optional[datetime] = None,
                     metadata: Optional[Dict] = None) -> Optional[int]:
        """Schedule a post for optimal time"""
        try:
            # If no target time, predict best time
            if target_time is None:
                target_time = self.predict_best_time(platform)
            
            if not target_time:
                return None
            
            # Get prediction score
            engagement_prediction = self._predict_engagement(platform, target_time)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "INSERT INTO scheduled_posts "
                    "(content, platform, content_type, optimal_time, priority, "
                    "engagement_prediction, metadata, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (content, platform, content_type, target_time.isoformat(),
                     priority, engagement_prediction,
                     json.dumps(metadata) if metadata else None, 'pending')
                )
                conn.commit()
                post_id = cursor.lastrowid
                
                print(f"📅 Scheduled {platform} post for {target_time.strftime('%a %H:%M')} "
                      f"(predicted engagement: {engagement_prediction:.1f})")
                
                return post_id
        except Exception as e:
            print(f"⚠️ Error scheduling post: {e}")
            return None
    
    def _predict_engagement(self, platform: str, post_time: datetime) -> float:
        """Predict engagement for a specific time slot"""
        try:
            day = post_time.weekday()
            hour = post_time.hour
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT avg_engagement, posts_count FROM time_performance "
                    "WHERE platform = ? AND day_of_week = ? AND hour = ?",
                    (platform, day, hour)
                )
                result = cursor.fetchone()
                
                if result:
                    avg_eng, count = result
                    # Adjust for confidence
                    confidence = min(count / 10, 1.0)
                    return avg_eng * confidence
                
                # Default prediction based on time of day
                if 9 <= hour <= 17:  # Business hours
                    return 50.0
                elif 18 <= hour <= 22:  # Evening
                    return 70.0
                else:  # Late night/early morning
                    return 30.0
        except Exception as e:
            print(f"⚠️ Error predicting engagement: {e}")
            return 50.0
    
    def get_scheduled_posts(self, platform: str = None, 
                           status: str = 'pending') -> List[Dict]:
        """Get scheduled posts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if platform:
                    cursor = conn.execute(
                        "SELECT * FROM scheduled_posts WHERE platform = ? AND status = ? "
                        "ORDER BY optimal_time",
                        (platform, status)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM scheduled_posts WHERE status = ? ORDER BY optimal_time",
                        (status,)
                    )
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error getting scheduled posts: {e}")
            return []
    
    def get_due_posts(self) -> List[Dict]:
        """Get posts that are due to be posted now"""
        try:
            now = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM scheduled_posts WHERE status = 'pending' "
                    "AND optimal_time <= ? ORDER BY priority, optimal_time",
                    (now,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error getting due posts: {e}")
            return []
    
    def mark_posted(self, post_id: int, actual_engagement: Optional[Dict] = None) -> bool:
        """Mark a scheduled post as posted"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE scheduled_posts SET status = 'posted', posted_time = ? WHERE id = ?",
                    (datetime.now().isoformat(), post_id)
                )
                conn.commit()
                
                # If we have engagement data, record it for learning
                if actual_engagement:
                    cursor = conn.execute(
                        "SELECT platform, optimal_time FROM scheduled_posts WHERE id = ?",
                        (post_id,)
                    )
                    result = cursor.fetchone()
                    if result:
                        platform, post_time_str = result
                        post_time = datetime.fromisoformat(post_time_str)
                        self.record_post_performance(platform, post_time, actual_engagement)
                
                return True
        except Exception as e:
            print(f"⚠️ Error marking post as posted: {e}")
            return False
    
    def cancel_post(self, post_id: int) -> bool:
        """Cancel a scheduled post"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE scheduled_posts SET status = 'cancelled' WHERE id = ?",
                    (post_id,)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Error cancelling post: {e}")
            return False
    
    def get_schedule_stats(self) -> Dict:
        """Get scheduling statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT platform, COUNT(*) as count, AVG(engagement_prediction) as avg_pred "
                    "FROM scheduled_posts WHERE status = 'pending' GROUP BY platform"
                )
                pending = {row[0]: {'count': row[1], 'avg_prediction': row[2]} 
                          for row in cursor.fetchall()}
                
                cursor = conn.execute(
                    "SELECT status, COUNT(*) FROM scheduled_posts GROUP BY status"
                )
                by_status = {row[0]: row[1] for row in cursor.fetchall()}
                
                return {
                    'pending_by_platform': pending,
                    'by_status': by_status,
                    'total_scheduled': sum(by_status.values())
                }
        except Exception as e:
            print(f"⚠️ Error getting schedule stats: {e}")
            return {}
    
    def get_platform_heatmap(self, platform: str) -> Dict:
        """Get engagement heatmap data for a platform"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT day_of_week, hour, avg_engagement, posts_count "
                    "FROM time_performance WHERE platform = ?",
                    (platform,)
                )
                
                heatmap = {}
                for row in cursor.fetchall():
                    day = row['day_of_week']
                    hour = row['hour']
                    if day not in heatmap:
                        heatmap[day] = {}
                    heatmap[day][hour] = {
                        'engagement': row['avg_engagement'],
                        'samples': row['posts_count']
                    }
                
                return heatmap
        except Exception as e:
            print(f"⚠️ Error getting heatmap: {e}")
            return {}


class ScheduleRunner:
    """Runs scheduled posting loop"""
    
    def __init__(self, scheduler: SmartScheduler, post_callback):
        self.scheduler = scheduler
        self.post_callback = post_callback  # Function to actually post content
        self.running = False
    
    async def run(self, check_interval: int = 60):
        """Run the scheduling loop"""
        self.running = True
        print("📅 Schedule runner started")
        
        while self.running:
            try:
                # Get posts that are due
                due_posts = self.scheduler.get_due_posts()
                
                for post in due_posts:
                    print(f"🚀 Posting scheduled content to {post['platform']}")
                    
                    # Call the post callback
                    success = await self.post_callback(
                        platform=post['platform'],
                        content=post['content'],
                        content_type=post['content_type'],
                        metadata=json.loads(post['metadata']) if post['metadata'] else None
                    )
                    
                    if success:
                        self.scheduler.mark_posted(post['id'])
                    else:
                        print(f"⚠️ Failed to post scheduled content")
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                print(f"⚠️ Schedule runner error: {e}")
                await asyncio.sleep(check_interval)
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        print("📅 Schedule runner stopped")
