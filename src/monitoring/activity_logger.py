"""
Activity Logger for AlleyBot
Tracks and logs all agent activities for dashboard display
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from collections import deque


class ActivityLogger:
    """Log and track AlleyBot activities for dashboard monitoring"""
    
    def __init__(self, storage_dir: str = "data/activity_logs", max_activities: int = 1000):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_activities = max_activities
        self.activities = deque(maxlen=max_activities)
        
        # Load today's activities
        self.today_file = self._get_today_file()
        self._load_activities()
        
        # Stats counters
        self.stats = {
            'total_posts': 0,
            'total_comments': 0,
            'total_likes': 0,
            'total_engagements': 0,
            'moltx_posts': 0,
            'moltbook_posts': 0,
            'telegram_messages': 0,
            'ai_generations': 0
        }
        self._load_stats()
    
    def _get_today_file(self) -> Path:
        """Get the file path for today's activity log"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.storage_dir / f"activity_{today}.json"
    
    def _load_activities(self):
        """Load today's activities from file"""
        if self.today_file.exists():
            try:
                with open(self.today_file, 'r') as f:
                    data = json.load(f)
                    self.activities = deque(data.get('activities', []), maxlen=self.max_activities)
            except Exception as e:
                print(f"⚠️  Failed to load activities: {e}")
                self.activities = deque(maxlen=self.max_activities)
    
    def _save_activities(self):
        """Save activities to file"""
        try:
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'activities': list(self.activities),
                'count': len(self.activities)
            }
            with open(self.today_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save activities: {e}")
    
    def _load_stats(self):
        """Load cumulative stats"""
        stats_file = self.storage_dir / "cumulative_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    self.stats = json.load(f)
            except Exception as e:
                print(f"⚠️  Failed to load stats: {e}")
    
    def _save_stats(self):
        """Save cumulative stats"""
        try:
            stats_file = self.storage_dir / "cumulative_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save stats: {e}")
    
    def log_activity(self, activity_type: str, platform: str, details: Dict = None):
        """
        Log an activity
        
        Args:
            activity_type: Type of activity (post, comment, like, engage, ai_generation, etc.)
            platform: Platform where activity occurred (moltx, moltbook, telegram, etc.)
            details: Additional details about the activity
        """
        activity = {
            'timestamp': datetime.now().isoformat(),
            'type': activity_type,
            'platform': platform,
            'details': details or {}
        }
        
        self.activities.append(activity)
        
        # Update stats
        if activity_type == 'post':
            self.stats['total_posts'] += 1
            if platform == 'moltx':
                self.stats['moltx_posts'] += 1
            elif platform == 'moltbook':
                self.stats['moltbook_posts'] += 1
        elif activity_type == 'comment':
            self.stats['total_comments'] += 1
        elif activity_type == 'like' or activity_type == 'upvote':
            self.stats['total_likes'] += 1
        elif activity_type == 'engage':
            self.stats['total_engagements'] += 1
        elif activity_type == 'telegram_message':
            self.stats['telegram_messages'] += 1
        elif activity_type == 'ai_generation':
            self.stats['ai_generations'] += 1
        
        # Save to disk
        self._save_activities()
        self._save_stats()
        
        print(f"📝 Activity logged: {activity_type} on {platform}")
    
    def get_recent_activities(self, limit: int = 50) -> List[Dict]:
        """Get recent activities"""
        activities_list = list(self.activities)
        activities_list.reverse()  # Most recent first
        return activities_list[:limit]
    
    def get_stats(self) -> Dict:
        """Get current stats"""
        return {
            **self.stats,
            'recent_activity_count': len(self.activities),
            'last_activity': self.activities[-1] if self.activities else None
        }
    
    def get_activity_by_platform(self) -> Dict:
        """Get activity breakdown by platform"""
        platform_counts = {}
        for activity in self.activities:
            platform = activity.get('platform', 'unknown')
            if platform not in platform_counts:
                platform_counts[platform] = 0
            platform_counts[platform] += 1
        return platform_counts
    
    def get_activity_by_type(self) -> Dict:
        """Get activity breakdown by type"""
        type_counts = {}
        for activity in self.activities:
            activity_type = activity.get('type', 'unknown')
            if activity_type not in type_counts:
                type_counts[activity_type] = 0
            type_counts[activity_type] += 1
        return type_counts
    
    def get_hourly_activity(self) -> Dict:
        """Get activity counts by hour for today"""
        hourly = {}
        for activity in self.activities:
            timestamp = activity.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(timestamp)
                hour = dt.strftime('%H:00')
                if hour not in hourly:
                    hourly[hour] = 0
                hourly[hour] += 1
            except:
                continue
        return hourly
    
    def clear_old_logs(self, days_to_keep: int = 30):
        """Clear activity logs older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for log_file in self.storage_dir.glob("activity_*.json"):
                try:
                    date_str = log_file.stem.replace('activity_', '')
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    if file_date < cutoff_date:
                        log_file.unlink()
                        print(f"🗑️  Deleted old activity log: {log_file.name}")
                except:
                    continue
        except Exception as e:
            print(f"⚠️  Failed to clear old logs: {e}")
