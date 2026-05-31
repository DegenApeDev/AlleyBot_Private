"""
Persistent Intent System

Long-running objectives that survive across brain cycles, hours, and days.
Unlike work items (discrete tasks), intents represent continuous objectives
like "grow moltx following by 20%" that require sustained action over time.
"""

import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)


class IntentStatus(Enum):
    """Lifecycle states for persistent intents."""
    ACTIVE = auto()      # Being pursued
    PAUSED = auto()      # Temporarily suspended
    COMPLETED = auto()   # Success criteria met
    FAILED = auto()      # Abandoned after max retries
    ARCHIVED = auto()    # Preserved for learning but not active


@dataclass
class PersistentIntent:
    """
    A long-running objective that guides autonomous behavior over time.
    
    Unlike a goal (which is a discrete outcome), an intent is a direction
    that generates multiple goals and actions over its lifetime.
    """
    id: str
    objective: str  # e.g., "grow moltx following by 20%"
    
    # Success criteria
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    # e.g., {"metric": "moltx_followers", "target_increase": 200, "deadline": "2026-05-01"}
    
    # Current state
    current_value: float = 0.0
    target_value: float = 0.0
    progress_percent: float = 0.0
    
    # Time bounds
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    last_action_time: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Execution parameters
    cooldown_hours: float = 6.0  # Minimum time between intent-driven actions
    max_daily_actions: int = 3   # Cap on actions per day for this intent
    priority: int = 5  # 1-10
    
    # Current plan
    current_plan: List[str] = field(default_factory=list)
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    
    # Tracking
    status: IntentStatus = IntentStatus.ACTIVE
    action_count_today: int = 0
    action_count_total: int = 0
    last_reset_date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    
    # Learning
    effective_strategies: List[str] = field(default_factory=list)
    failed_strategies: List[str] = field(default_factory=list)
    notes: str = ""  # Learning notes, pattern observations
    
    # Owner linkage
    owner_objective_id: Optional[str] = None  # Link to owner_objectives
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            **asdict(self),
            'status': self.status.name,
            'created_at': self.created_at.isoformat(),
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'last_action_time': self.last_action_time.isoformat() if self.last_action_time else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PersistentIntent':
        """Deserialize from dictionary."""
        data = data.copy()
        data['status'] = IntentStatus[data.get('status', 'ACTIVE')]
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('deadline'):
            data['deadline'] = datetime.fromisoformat(data['deadline'])
        if data.get('last_action_time'):
            data['last_action_time'] = datetime.fromisoformat(data['last_action_time'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def is_ready_for_action(self) -> bool:
        """Check if enough time has passed since last action."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Reset daily counter if new day
        if self.last_reset_date != today:
            self.action_count_today = 0
            self.last_reset_date = today
        
        # Check daily cap
        if self.action_count_today >= self.max_daily_actions:
            return False
        
        # Check cooldown
        if self.last_action_time:
            hours_since = (datetime.now() - self.last_action_time).total_seconds() / 3600
            return hours_since >= self.cooldown_hours
        
        return True
    
    def record_action(self, action_description: str, success: bool) -> None:
        """Record an action taken to advance this intent."""
        self.last_action_time = datetime.now()
        self.action_count_today += 1
        self.action_count_total += 1
        
        today = datetime.now().strftime('%Y-%m-%d')
        if self.last_reset_date != today:
            self.action_count_today = 1
            self.last_reset_date = today
        
        if success:
            if action_description not in self.completed_steps:
                self.completed_steps.append(action_description)
        else:
            if action_description not in self.failed_steps:
                self.failed_steps.append(action_description)
    
    def update_progress(self, current_value: float) -> None:
        """Update progress toward target."""
        self.current_value = current_value
        if self.target_value > 0:
            self.progress_percent = min(100.0, (current_value / self.target_value) * 100)
        
        # Check completion
        if self.progress_percent >= 100:
            self.status = IntentStatus.COMPLETED
            self.completed_at = datetime.now()
            logger.info(f"✅ Intent completed: {self.objective}")


class PersistentIntentManager:
    """
    Manages persistent intents with SQLite storage.
    
    Intents survive across restarts and provide continuity of purpose.
    """
    
    def __init__(self, db_path: str = 'data/persistent_intents.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._active_intents_cache: Dict[str, PersistentIntent] = {}
        self._cache_timestamp: Optional[datetime] = None
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS persistent_intents (
                    id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    success_criteria TEXT,  -- JSON
                    current_value REAL DEFAULT 0.0,
                    target_value REAL DEFAULT 0.0,
                    progress_percent REAL DEFAULT 0.0,
                    created_at TEXT,
                    deadline TEXT,
                    last_action_time TEXT,
                    completed_at TEXT,
                    cooldown_hours REAL DEFAULT 6.0,
                    max_daily_actions INTEGER DEFAULT 3,
                    priority INTEGER DEFAULT 5,
                    current_plan TEXT,  -- JSON list
                    completed_steps TEXT,  -- JSON list
                    failed_steps TEXT,  -- JSON list
                    status TEXT DEFAULT 'ACTIVE',
                    action_count_today INTEGER DEFAULT 0,
                    action_count_total INTEGER DEFAULT 0,
                    last_reset_date TEXT,
                    effective_strategies TEXT,  -- JSON list
                    failed_strategies TEXT,  -- JSON list
                    notes TEXT,
                    owner_objective_id TEXT
                )
            ''')
            
            # Index for fast queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_status ON persistent_intents(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_priority ON persistent_intents(priority)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON persistent_intents(created_at)')
            conn.commit()
    
    def create_intent(
        self,
        objective: str,
        success_criteria: Optional[Dict[str, Any]] = None,
        target_value: float = 0.0,
        deadline: Optional[datetime] = None,
        cooldown_hours: float = 6.0,
        max_daily_actions: int = 3,
        priority: int = 5,
        owner_objective_id: Optional[str] = None,
        initial_plan: Optional[List[str]] = None,
    ) -> str:
        """Create a new persistent intent."""
        intent_id = f"intent_{int(datetime.now().timestamp())}_{hash(objective) % 10000}"
        
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO persistent_intents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                intent_id,
                objective,
                json.dumps(success_criteria) if success_criteria else None,
                0.0,  # current_value
                target_value,
                0.0,  # progress_percent
                now.isoformat(),
                deadline.isoformat() if deadline else None,
                None,  # last_action_time
                None,  # completed_at
                cooldown_hours,
                max_daily_actions,
                priority,
                json.dumps(initial_plan or []),
                '[]',  # completed_steps
                '[]',  # failed_steps
                'ACTIVE',
                0,  # action_count_today
                0,  # action_count_total
                today,
                '[]',  # effective_strategies
                '[]',  # failed_strategies
                '',  # notes
                owner_objective_id,
            ))
            conn.commit()
        
        self._invalidate_cache()
        logger.info(f"🎯 Persistent intent created: {objective[:60]}...")
        return intent_id
    
    def get_intent(self, intent_id: str) -> Optional[PersistentIntent]:
        """Get a specific intent by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM persistent_intents WHERE id = ?',
                (intent_id,)
            ).fetchone()
            
            if row:
                return self._row_to_intent(row)
            return None
    
    def get_active_intents(self, limit: int = 10) -> List[PersistentIntent]:
        """Get active intents sorted by priority and progress."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('''
                SELECT * FROM persistent_intents 
                WHERE status = 'ACTIVE'
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
            ''', (limit,)).fetchall()
        
        return [self._row_to_intent(row) for row in rows]
    
    def get_ready_intents(self) -> List[PersistentIntent]:
        """Get active intents that are ready for action (cooldown passed, daily cap not hit)."""
        active = self.get_active_intents(limit=50)
        return [i for i in active if i.is_ready_for_action()]
    
    def update_intent(self, intent_id: str, **kwargs) -> bool:
        """Update intent fields."""
        allowed = {
            'current_value', 'target_value', 'progress_percent', 'status',
            'last_action_time', 'completed_at', 'current_plan', 'completed_steps',
            'failed_steps', 'action_count_today', 'action_count_total',
            'last_reset_date', 'effective_strategies', 'failed_strategies', 'notes'
        }
        
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        
        # Serialize complex fields
        for field in ['current_plan', 'completed_steps', 'failed_steps', 
                      'effective_strategies', 'failed_strategies']:
            if field in updates:
                updates[field] = json.dumps(updates[field])
        
        # Handle datetime fields
        for field in ['last_action_time', 'completed_at']:
            if field in updates and isinstance(updates[field], datetime):
                updates[field] = updates[field].isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
            conn.execute(f'''
                UPDATE persistent_intents 
                SET {set_clause}
                WHERE id = ?
            ''', (*updates.values(), intent_id))
            conn.commit()
        
        self._invalidate_cache()
        return True
    
    def record_intent_action(self, intent_id: str, action_description: str, success: bool, current_value: Optional[float] = None) -> bool:
        """Record an action taken to advance an intent."""
        intent = self.get_intent(intent_id)
        if not intent:
            return False
        
        intent.record_action(action_description, success)
        
        updates = {
            'last_action_time': intent.last_action_time,
            'action_count_today': intent.action_count_today,
            'action_count_total': intent.action_count_total,
            'last_reset_date': intent.last_reset_date,
            'completed_steps': intent.completed_steps,
            'failed_steps': intent.failed_steps,
        }
        
        if current_value is not None:
            intent.update_progress(current_value)
            updates['current_value'] = intent.current_value
            updates['progress_percent'] = intent.progress_percent
            if intent.status == IntentStatus.COMPLETED:
                updates['status'] = 'COMPLETED'
                updates['completed_at'] = intent.completed_at
        
        return self.update_intent(intent_id, **updates)
    
    def pause_intent(self, intent_id: str, reason: str = "paused") -> bool:
        """Pause an intent (temporarily suspend pursuit)."""
        intent = self.get_intent(intent_id)
        if not intent:
            return False
        
        success = self.update_intent(
            intent_id,
            status='PAUSED',
            notes=f"{intent.notes}\nPaused: {reason} at {datetime.now().isoformat()}"
        )
        if success:
            logger.info(f"⏸️ Intent paused: {intent_id} ({reason})")
        return success
    
    def complete_intent(self, intent_id: str, outcome: str = "") -> bool:
        """Mark intent as completed."""
        success = self.update_intent(
            intent_id,
            status='COMPLETED',
            completed_at=datetime.now(),
            progress_percent=100.0,
            notes=f"Completed: {outcome}"
        )
        if success:
            logger.info(f"✅ Intent completed: {intent_id}")
        return success
    
    def fail_intent(self, intent_id: str, reason: str = "") -> bool:
        """Mark intent as failed (abandoned)."""
        success = self.update_intent(
            intent_id,
            status='FAILED',
            notes=f"Failed: {reason} at {datetime.now().isoformat()}"
        )
        if success:
            logger.info(f"❌ Intent failed: {intent_id} ({reason})")
        return success
    
    def generate_action_for_intent(self, intent: PersistentIntent) -> Optional[Dict]:
        """
        Generate a concrete action to advance an intent.
        
        Returns action spec dict that can be routed through ActionRouter.
        """
        if not intent.current_plan and not intent.completed_steps:
            # Generate initial plan based on objective type
            if 'follower' in intent.objective.lower() or 'growth' in intent.objective.lower():
                intent.current_plan = [
                    "Analyze current audience demographics",
                    "Identify high-engagement content types",
                    "Create daily engagement routine",
                    "A/B test content styles",
                    "Engage with high-value accounts",
                    "Cross-post to maximize reach"
                ]
            elif 'skill' in intent.objective.lower():
                intent.current_plan = [
                    "Research capability requirements",
                    "Design skill architecture",
                    "Generate skill code",
                    "Test in sandbox",
                    "Deploy if successful"
                ]
            else:
                intent.current_plan = [
                    "Gather current state data",
                    "Identify gaps vs target",
                    "Propose intervention",
                    "Execute and measure",
                    "Iterate based on feedback"
                ]
        
        # Find next uncompleted step
        next_step = None
        for step in intent.current_plan:
            if step not in intent.completed_steps and step not in intent.failed_steps:
                next_step = step
                break
        
        if not next_step:
            # All steps completed or failed - replan
            return None
        
        # Map to action type
        action_type = 'analyze'
        if 'create' in next_step.lower() or 'post' in next_step.lower():
            action_type = 'create_post'
        elif 'engage' in next_step.lower():
            action_type = 'engage'
        elif 'test' in next_step.lower() or 'sandbox' in next_step.lower():
            action_type = 'execute_skill'
        elif 'research' in next_step.lower() or 'gather' in next_step.lower():
            action_type = 'analyze'
        
        return {
            'intent_id': intent.id,
            'action_type': action_type,
            'description': next_step,
            'context': {
                'source': 'persistent_intent',
                'intent_objective': intent.objective,
                'intent_priority': intent.priority,
                'progress_percent': intent.progress_percent,
            }
        }
    
    def _row_to_intent(self, row: sqlite3.Row) -> PersistentIntent:
        """Convert database row to PersistentIntent."""
        def load_json(field, default=None):
            try:
                return json.loads(row[field]) if row[field] else default
            except (json.JSONDecodeError, TypeError):
                return default
        
        return PersistentIntent(
            id=row['id'],
            objective=row['objective'],
            success_criteria=load_json('success_criteria', {}),
            current_value=row['current_value'] or 0.0,
            target_value=row['target_value'] or 0.0,
            progress_percent=row['progress_percent'] or 0.0,
            created_at=datetime.fromisoformat(row['created_at']),
            deadline=datetime.fromisoformat(row['deadline']) if row['deadline'] else None,
            last_action_time=datetime.fromisoformat(row['last_action_time']) if row['last_action_time'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            cooldown_hours=row['cooldown_hours'] or 6.0,
            max_daily_actions=row['max_daily_actions'] or 3,
            priority=row['priority'] or 5,
            current_plan=load_json('current_plan', []),
            completed_steps=load_json('completed_steps', []),
            failed_steps=load_json('failed_steps', []),
            status=IntentStatus[row['status']] if row['status'] else IntentStatus.ACTIVE,
            action_count_today=row['action_count_today'] or 0,
            action_count_total=row['action_count_total'] or 0,
            last_reset_date=row['last_reset_date'] or datetime.now().strftime('%Y-%m-%d'),
            effective_strategies=load_json('effective_strategies', []),
            failed_strategies=load_json('failed_strategies', []),
            notes=row['notes'] or '',
            owner_objective_id=row['owner_objective_id'],
        )
    
    def _invalidate_cache(self) -> None:
        """Invalidate in-memory cache."""
        self._active_intents_cache.clear()
        self._cache_timestamp = None
    
    def get_summary(self) -> str:
        """Get human-readable summary of active intents."""
        intents = self.get_active_intents(limit=20)
        
        lines = ["🎯 Persistent Intents Summary"]
        lines.append("=" * 40)
        
        if not intents:
            lines.append("  (No active intents)")
            return "\n".join(lines)
        
        for intent in intents:
            status_icon = "🟢" if intent.status == IntentStatus.ACTIVE else "⏸️"
            progress_bar = f"[{int(intent.progress_percent):3d}%]"
            ready = "READY" if intent.is_ready_for_action() else f"cooldown {intent.cooldown_hours}h"
            lines.append(f"{status_icon} {progress_bar} {intent.objective[:40]}... ({ready})")
        
        return "\n".join(lines)

    # =========================================================================
    # ASYNC WRAPPERS (P0-002: Fix Async Blocking I/O)
    # =========================================================================

    async def aget_intent(self, intent_id: str) -> Optional[PersistentIntent]:
        """Async version of get_intent - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_intent, intent_id)

    async def aget_active_intents(self, limit: int = 20) -> List[PersistentIntent]:
        """Async version of get_active_intents - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_active_intents, limit)

    async def aget_ready_intents(self, limit: int = 5) -> List[PersistentIntent]:
        """Async version of get_ready_intents - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_ready_intents, limit)

    async def aadd_intent(self, intent: PersistentIntent) -> bool:
        """Async version of add_intent - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.add_intent, intent)

    async def arecord_action(self, intent_id: str, success: bool, outcome: str) -> bool:
        """Async version of record_action - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.record_action, intent_id, success, outcome)

    async def acomplete_intent(self, intent_id: str, final_outcome: str) -> bool:
        """Async version of complete_intent - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.complete_intent, intent_id, final_outcome)

    async def aget_next_action_for_intent(self, intent: PersistentIntent) -> Optional[Dict[str, Any]]:
        """Async version of get_next_action_for_intent - non-blocking"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_next_action_for_intent, intent)


# Singleton
_manager_instance: Optional[PersistentIntentManager] = None


def get_persistent_intent_manager() -> PersistentIntentManager:
    """Get or create singleton instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = PersistentIntentManager()
    return _manager_instance
