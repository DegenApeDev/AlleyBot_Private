"""
Owner Objectives Manager

Tracks persistent owner goals that guide AlleyBot's autonomous behavior.

This is the "constitution" for autonomous operation — what the owner wants,
what they don't want, and how they want it done.
"""

import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class OwnerObjective:
    """A single owner objective that guides autonomous behavior."""
    id: str
    description: str
    objective_type: str  # 'primary', 'secondary', 'anti_goal'
    target_metric: Optional[str] = None  # e.g., "moltx_followers"
    target_value: Optional[float] = None  # e.g., 1.2 (20% growth)
    deadline: Optional[datetime] = None
    priority: int = 5  # 1-10
    constraints: List[str] = field(default_factory=list)  # e.g., ["no_spam", "daily_max_3_posts"]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'OwnerObjective':
        data = data.copy()
        if data.get('deadline'):
            data['deadline'] = datetime.fromisoformat(data['deadline'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class EngagementPreferences:
    """Owner preferences for autonomous engagement."""
    max_daily_posts: int = 3
    preferred_topics: List[str] = field(default_factory=list)
    avoid_topics: List[str] = field(default_factory=list)
    preferred_tone: str = "helpful"  # helpful, witty, professional, casual
    max_daily_outreach: int = 5  # DMs, replies, etc.
    quiet_hours_start: Optional[int] = None  # 0-23, e.g., 22 for 10pm
    quiet_hours_end: Optional[int] = None  # 0-23, e.g., 8 for 8am
    
    def is_quiet_hours(self) -> bool:
        """Check if current time is in quiet hours."""
        if self.quiet_hours_start is None or self.quiet_hours_end is None:
            return False
        now = datetime.now().hour
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= now < self.quiet_hours_end
        else:  # Wraps around midnight
            return now >= self.quiet_hours_start or now < self.quiet_hours_end


class OwnerObjectivesManager:
    """
    Manages owner objectives and engagement preferences.
    
    This is the bridge between owner intent and autonomous behavior.
    """
    
    def __init__(self, db_path: str = 'data/owner_objectives.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS objectives (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    objective_type TEXT NOT NULL,
                    target_metric TEXT,
                    target_value REAL,
                    deadline TEXT,
                    priority INTEGER DEFAULT 5,
                    constraints TEXT,  -- JSON list
                    created_at TEXT,
                    updated_at TEXT,
                    active INTEGER DEFAULT 1
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS engagement_preferences (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    max_daily_posts INTEGER DEFAULT 3,
                    preferred_topics TEXT,  -- JSON list
                    avoid_topics TEXT,  -- JSON list
                    preferred_tone TEXT DEFAULT 'helpful',
                    max_daily_outreach INTEGER DEFAULT 5,
                    quiet_hours_start INTEGER,
                    quiet_hours_end INTEGER,
                    updated_at TEXT
                )
            ''')
            
            # Insert default preferences if none exist
            conn.execute('''
                INSERT OR IGNORE INTO engagement_preferences (id, updated_at)
                VALUES (1, ?)
            ''', (datetime.now().isoformat(),))
            
            conn.commit()
    
    def add_objective(
        self,
        description: str,
        objective_type: str = 'primary',
        target_metric: Optional[str] = None,
        target_value: Optional[float] = None,
        deadline: Optional[datetime] = None,
        priority: int = 5,
        constraints: Optional[List[str]] = None,
    ) -> str:
        """Add a new owner objective."""
        objective_id = f"obj_{int(datetime.now().timestamp())}_{hash(description) % 10000}"
        
        now = datetime.now()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO objectives VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                objective_id,
                description,
                objective_type,
                target_metric,
                target_value,
                deadline.isoformat() if deadline else None,
                priority,
                json.dumps(constraints or []),
                now.isoformat(),
                now.isoformat(),
                1
            ))
            conn.commit()
        
        self._invalidate_cache()
        logger.info(f"🎯 Owner objective added: {description[:60]}...")
        return objective_id
    
    def get_active_objectives(self, objective_type: Optional[str] = None) -> List[OwnerObjective]:
        """Get active owner objectives, optionally filtered by type."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if objective_type:
                rows = conn.execute('''
                    SELECT * FROM objectives 
                    WHERE active = 1 AND objective_type = ?
                    ORDER BY priority DESC, created_at DESC
                ''', (objective_type,)).fetchall()
            else:
                rows = conn.execute('''
                    SELECT * FROM objectives 
                    WHERE active = 1
                    ORDER BY priority DESC, created_at DESC
                ''').fetchall()
        
        objectives = []
        for row in rows:
            obj = OwnerObjective(
                id=row['id'],
                description=row['description'],
                objective_type=row['objective_type'],
                target_metric=row['target_metric'],
                target_value=row['target_value'],
                deadline=datetime.fromisoformat(row['deadline']) if row['deadline'] else None,
                priority=row['priority'],
                constraints=json.loads(row['constraints']) if row['constraints'] else [],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']),
                active=bool(row['active']),
            )
            objectives.append(obj)
        
        return objectives
    
    def get_engagement_preferences(self) -> EngagementPreferences:
        """Get owner engagement preferences."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute('SELECT * FROM engagement_preferences WHERE id = 1').fetchone()
        
        if not row:
            return EngagementPreferences()
        
        return EngagementPreferences(
            max_daily_posts=row['max_daily_posts'] or 3,
            preferred_topics=json.loads(row['preferred_topics']) if row['preferred_topics'] else [],
            avoid_topics=json.loads(row['avoid_topics']) if row['avoid_topics'] else [],
            preferred_tone=row['preferred_tone'] or 'helpful',
            max_daily_outreach=row['max_daily_outreach'] or 5,
            quiet_hours_start=row['quiet_hours_start'],
            quiet_hours_end=row['quiet_hours_end'],
        )
    
    def update_engagement_preferences(self, **kwargs) -> bool:
        """Update engagement preferences."""
        allowed_fields = {
            'max_daily_posts', 'preferred_topics', 'avoid_topics', 'preferred_tone',
            'max_daily_outreach', 'quiet_hours_start', 'quiet_hours_end'
        }
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False
        
        # Convert lists to JSON
        if 'preferred_topics' in updates:
            updates['preferred_topics'] = json.dumps(updates['preferred_topics'])
        if 'avoid_topics' in updates:
            updates['avoid_topics'] = json.dumps(updates['avoid_topics'])
        
        updates['updated_at'] = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
            conn.execute(f'''
                UPDATE engagement_preferences 
                SET {set_clause}
                WHERE id = 1
            ''', tuple(updates.values()))
            conn.commit()
        
        self._invalidate_cache()
        logger.info(f"📋 Engagement preferences updated: {list(updates.keys())}")
        return True
    
    def deactivate_objective(self, objective_id: str) -> bool:
        """Deactivate (archive) an objective."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE objectives 
                SET active = 0, updated_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), objective_id))
            conn.commit()
        
        self._invalidate_cache()
        logger.info(f"📋 Objective deactivated: {objective_id}")
        return True
    
    def score_goal_alignment(self, goal_description: str, goal_category: str) -> float:
        """
        Score how well a proposed goal aligns with owner objectives.
        
        Returns 0.0-1.0 where 1.0 = perfectly aligned.
        """
        objectives = self.get_active_objectives()
        if not objectives:
            return 0.5  # Neutral if no objectives set
        
        description_lower = goal_description.lower()
        category_lower = goal_category.lower()
        
        score = 0.0
        total_weight = 0.0
        
        for obj in objectives:
            weight = obj.priority / 10.0  # 0.1 to 1.0
            total_weight += weight
            
            # Check description alignment
            obj_words = set(obj.description.lower().split())
            goal_words = set(description_lower.split())
            overlap = len(obj_words & goal_words)
            alignment = overlap / max(len(obj_words), 1)
            
            # Boost score for alignment
            if alignment > 0.3:
                score += weight * min(alignment * 2, 1.0)
            
            # Check category alignment
            if obj.objective_type == 'anti_goal':
                # Penalize if anti-goal keywords appear
                anti_words = set(obj.description.lower().split())
                if anti_words & goal_words:
                    score -= weight * 0.5
            
            # Check constraints
            for constraint in obj.constraints:
                if constraint in description_lower:
                    score += weight * 0.1  # Small boost for constraint adherence
        
        # Normalize
        if total_weight > 0:
            normalized_score = score / total_weight
            return max(0.0, min(1.0, normalized_score + 0.5))  # Center around 0.5
        
        return 0.5
    
    def _invalidate_cache(self) -> None:
        """Invalidate the in-memory cache."""
        self._cache.clear()
        self._cache_timestamp = None
    
    def get_summary(self) -> str:
        """Get human-readable summary of owner objectives."""
        objectives = self.get_active_objectives()
        prefs = self.get_engagement_preferences()
        
        lines = ["🎯 Owner Objectives Summary"]
        lines.append("=" * 40)
        
        if objectives:
            for obj in objectives:
                status = "🎯" if obj.objective_type == 'primary' else "📌" if obj.objective_type == 'secondary' else "🚫"
                lines.append(f"{status} [{obj.priority}/10] {obj.description[:50]}...")
        else:
            lines.append("  (No objectives set yet)")
        
        lines.append("")
        lines.append("📋 Engagement Preferences")
        lines.append(f"  Max daily posts: {prefs.max_daily_posts}")
        lines.append(f"  Max daily outreach: {prefs.max_daily_outreach}")
        lines.append(f"  Preferred tone: {prefs.preferred_tone}")
        if prefs.quiet_hours_start is not None:
            lines.append(f"  Quiet hours: {prefs.quiet_hours_start}:00 - {prefs.quiet_hours_end}:00")
        
        return "\n".join(lines)

    # =========================================================================
    # ASYNC WRAPPERS (P0-002: Fix Async Blocking I/O)
    # =========================================================================

    async def aget_active_objectives(self) -> List[OwnerObjective]:
        """Async version of get_active_objectives - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_active_objectives)

    async def aget_objective_by_id(self, objective_id: str) -> Optional[OwnerObjective]:
        """Async version of get_objective_by_id - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_objective_by_id, objective_id)

    async def aadd_objective(self, objective: OwnerObjective) -> bool:
        """Async version of add_objective - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.add_objective, objective)

    async def aupdate_objective(self, objective_id: str, **updates) -> bool:
        """Async version of update_objective - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.update_objective, objective_id, **updates)

    async def adelete_objective(self, objective_id: str) -> bool:
        """Async version of delete_objective - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.delete_objective, objective_id)

    async def aget_engagement_preferences(self) -> 'EngagementPreferences':
        """Async version of get_engagement_preferences - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_engagement_preferences)

    async def aupdate_engagement_preferences(self, **updates) -> bool:
        """Async version of update_engagement_preferences - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.update_engagement_preferences, **updates)

    async def ascore_goal_alignment(self, goal_description: str) -> float:
        """Async version of score_goal_alignment - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.score_goal_alignment, goal_description)


# Singleton
_objectives_manager: Optional[OwnerObjectivesManager] = None


def get_owner_objectives_manager() -> OwnerObjectivesManager:
    """Get or create singleton instance."""
    global _objectives_manager
    if _objectives_manager is None:
        _objectives_manager = OwnerObjectivesManager()
    return _objectives_manager
