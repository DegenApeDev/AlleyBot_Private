"""
Goal Stack Manager - Persistent goal tracking for AGI autonomy

Manages long-term objectives with priority queues, deadlines, and success criteria.
Integrates with Brain decision engine to guide autonomous behavior.
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path


class Goal:
    """Represents a single goal with metadata"""
    
    def __init__(self, 
                 id: str,
                 description: str,
                 priority: int = 5,
                 deadline: Optional[datetime] = None,
                 success_criteria: Optional[Callable] = None,
                 context: Optional[Dict] = None,
                 parent_id: Optional[str] = None):
        self.id = id
        self.description = description
        self.priority = priority  # 1-10, higher = more important
        self.deadline = deadline
        self.success_criteria = success_criteria
        self.context = context or {}
        self.parent_id = parent_id
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.status = "pending"  # pending, active, completed, failed
        self.attempts = 0
        self.last_attempt: Optional[datetime] = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for storage"""
        return {
            'id': self.id,
            'description': self.description,
            'priority': self.priority,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'context': json.dumps(self.context),
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'attempts': self.attempts,
            'last_attempt': self.last_attempt.isoformat() if self.last_attempt else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Goal':
        """Deserialize from dict"""
        goal = cls(
            id=data['id'],
            description=data['description'],
            priority=data['priority'],
            deadline=datetime.fromisoformat(data['deadline']) if data['deadline'] else None,
            context=json.loads(data['context']) if data['context'] else {},
            parent_id=data['parent_id']
        )
        goal.created_at = datetime.fromisoformat(data['created_at'])
        goal.completed_at = datetime.fromisoformat(data['completed_at']) if data['completed_at'] else None
        goal.status = data['status']
        goal.attempts = data['attempts']
        goal.last_attempt = datetime.fromisoformat(data['last_attempt']) if data['last_attempt'] else None
        return goal
    
    def is_expired(self) -> bool:
        """Check if deadline has passed"""
        if self.deadline and datetime.now() > self.deadline:
            return True
        return False
    
    def __repr__(self):
        return f"<Goal {self.id}: {self.description[:50]} (P{self.priority}, {self.status})>"


class GoalStackManager:
    """
    Manages persistent goal stack for autonomous behavior.
    
    Features:
    - Priority queue with deadlines
    - Success criteria evaluation
    - Goal decomposition (parent/child goals)
    - Persistence via SQLite
    - Integration with Brain decision engine
    """
    
    def __init__(self, db_path: str = "data/goals.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    deadline TEXT,
                    context TEXT DEFAULT '{}',
                    parent_id TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT DEFAULT 'pending',
                    attempts INTEGER DEFAULT 0,
                    last_attempt TEXT,
                    FOREIGN KEY (parent_id) REFERENCES goals(id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority DESC)
            """)
            conn.commit()
    
    def add_goal(self, goal: Goal) -> bool:
        """Add a new goal to the stack"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                data = goal.to_dict()
                conn.execute("""
                    INSERT INTO goals 
                    (id, description, priority, deadline, context, parent_id, 
                     created_at, completed_at, status, attempts, last_attempt)
                    VALUES 
                    (:id, :description, :priority, :deadline, :context, :parent_id,
                     :created_at, :completed_at, :status, :attempts, :last_attempt)
                """, data)
                conn.commit()
                print(f"🎯 Goal added: {goal.description[:60]}...")
                return True
        except sqlite3.IntegrityError:
            print(f"⚠️ Goal {goal.id} already exists")
            return False
        except Exception as e:
            print(f"❌ Failed to add goal: {e}")
            return False
    
    def get_active_goals(self, limit: int = 10) -> List[Goal]:
        """Get top priority active goals (pending or active status)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM goals 
                WHERE status IN ('pending', 'active')
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [Goal.from_dict(dict(row)) for row in rows]
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a specific goal by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM goals WHERE id = ?", (goal_id,)
            )
            row = cursor.fetchone()
            return Goal.from_dict(dict(row)) if row else None
    
    def activate_goal(self, goal_id: str) -> bool:
        """Mark a goal as actively being worked on"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE goals SET status = 'active', last_attempt = ? WHERE id = ?",
                    (datetime.now().isoformat(), goal_id)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Failed to activate goal: {e}")
            return False
    
    def add_goal_from_autonomous(self, autonomous_goal) -> bool:
        """
        Add a goal from autonomous goal generator.
        
        Converts AutonomousGoal to Goal for tracking.
        """
        try:
            goal = Goal(
                id=autonomous_goal.goal_id,
                description=autonomous_goal.description,
                priority=int(autonomous_goal.priority),
                context=autonomous_goal.context or {}
            )
            return self.add_goal(goal)
        except Exception as e:
            print(f"❌ Failed to add autonomous goal: {e}")
            return False
    
    def complete_goal(self, goal_id: str) -> bool:
        """Mark a goal as completed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """UPDATE goals 
                       SET status = 'completed', completed_at = ? 
                       WHERE id = ?""",
                    (datetime.now().isoformat(), goal_id)
                )
                conn.commit()
                print(f"✅ Goal completed: {goal_id}")
                return True
        except Exception as e:
            print(f"❌ Failed to complete goal: {e}")
            return False
    
    def fail_goal(self, goal_id: str, reason: str = "") -> bool:
        """Mark a goal as failed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE goals SET status = 'failed' WHERE id = ?",
                    (goal_id,)
                )
                conn.commit()
                print(f"❌ Goal failed: {goal_id} - {reason}")
                return True
        except Exception as e:
            print(f"❌ Failed to mark goal as failed: {e}")
            return False
    
    def increment_attempt(self, goal_id: str) -> bool:
        """Increment attempt counter for a goal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """UPDATE goals 
                       SET attempts = attempts + 1, last_attempt = ? 
                       WHERE id = ?""",
                    (datetime.now().isoformat(), goal_id)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Failed to increment attempt: {e}")
            return False
    
    def get_next_goal(self) -> Optional[Goal]:
        """Get the highest priority active goal that isn't expired"""
        goals = self.get_active_goals(limit=20)
        for goal in goals:
            if not goal.is_expired():
                self.activate_goal(goal.id)
                return goal
            else:
                self.fail_goal(goal.id, "Deadline expired")
        return None
    
    def get_goal_tree(self, parent_id: Optional[str] = None) -> List[Goal]:
        """Get all goals with given parent (or top-level if None)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if parent_id:
                cursor = conn.execute(
                    "SELECT * FROM goals WHERE parent_id = ? ORDER BY priority DESC",
                    (parent_id,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM goals WHERE parent_id IS NULL ORDER BY priority DESC"
                )
            rows = cursor.fetchall()
            return [Goal.from_dict(dict(row)) for row in rows]
    
    def delete_goal(self, goal_id: str) -> bool:
        """Delete a goal and its children"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete children first
                conn.execute("DELETE FROM goals WHERE parent_id = ?", (goal_id,))
                # Delete parent
                conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Failed to delete goal: {e}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get goal statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT status, COUNT(*) FROM goals GROUP BY status"
            )
            stats = dict(cursor.fetchall())
            return {
                'total': sum(stats.values()),
                'pending': stats.get('pending', 0),
                'active': stats.get('active', 0),
                'completed': stats.get('completed', 0),
                'failed': stats.get('failed', 0)
            }
    
    def cleanup_expired(self) -> int:
        """Mark all expired goals as failed, return count"""
        count = 0
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, deadline FROM goals WHERE status IN ('pending', 'active') AND deadline IS NOT NULL"
            )
            for row in cursor.fetchall():
                deadline = datetime.fromisoformat(row['deadline'])
                if datetime.now() > deadline:
                    self.fail_goal(row['id'], "Deadline expired")
                    count += 1
        return count


# Convenience functions for Brain integration
def create_goal_manager(core=None) -> GoalStackManager:
    """Factory function to create GoalStackManager with appropriate path"""
    if core and hasattr(core, 'data_dir'):
        db_path = Path(core.data_dir) / "goals.db"
    else:
        db_path = "data/goals.db"
    return GoalStackManager(str(db_path))


def goal_from_action(action_id: str, context: Dict = None) -> Optional[Goal]:
    """Convert a Brain action into a Goal object"""
    action_to_goal = {
        'moltx_post': 'Create engaging post on Moltx',
        'moltx_engage': 'Engage with Moltx community',
        'clawbr_post': 'Create intelligent post on Clawbr',
        'clawbr_engage': 'Engage with Clawbr debates',
        'analyze_trending': 'Analyze trending topics across platforms',
        'check_engagement': 'Monitor post engagement metrics',
    }
    
    if action_id in action_to_goal:
        return Goal(
            id=f"{action_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=action_to_goal[action_id],
            priority=context.get('priority', 5) if context else 5,
            deadline=datetime.now() + timedelta(hours=context.get('deadline_hours', 24)) if context else None,
            context=context
        )
    return None
