"""
AlleyBot Goal Management System

Phase 2 of AGI Core: Autonomous Goal Management

Enables Alley to:
1. Detect gaps/opportunities from user interactions
2. Propose goals with priority scores
3. Maintain goal queue (active/pending/completed)
4. Auto-generate skill proposals when gaps are found

Part of AGI Core - Phase 2: Goal Management
"""

import json
import sqlite3
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class GoalStatus(Enum):
    """Goal lifecycle states"""
    DETECTED = auto()      # Gap/opportunity identified
    PROPOSED = auto()      # Proposal generated, waiting approval
    APPROVED = auto()      # Owner approved, ready to start
    ACTIVE = auto()        # Currently being worked on
    COMPLETED = auto()   # Successfully finished
    REJECTED = auto()    # Owner declined
    FAILED = auto()      # Attempted but failed


class GoalPriority(Enum):
    """Goal priority levels"""
    CRITICAL = 10    # System breaking, immediate fix needed
    HIGH = 8         # Significant user impact
    MEDIUM = 6       # Nice to have, moderate impact
    LOW = 4          # Minor improvement
    BACKLOG = 2      # Maybe someday


@dataclass
class Goal:
    """
    A goal Alley has detected and proposed.
    
    Goals flow through states:
    DETECTED → PROPOSED → APPROVED → ACTIVE → COMPLETED
                      ↓
                   REJECTED
    """
    id: str
    title: str
    description: str
    category: str  # 'skill', 'integration', 'optimization', 'fix'
    
    # Priority & scoring
    priority: GoalPriority
    impact_score: float  # 0-10 estimated user impact
    effort_estimate: str  # 'hours', 'days', 'weeks'
    confidence: float  # 0-1 confidence this is worth doing
    
    # Detection context
    trigger_type: str  # 'user_request', 'error_pattern', 'opportunity', 'gap'
    trigger_data: Dict[str, Any]  # What caused this goal
    evidence: List[str]  # Supporting evidence (user quotes, error logs, etc.)
    
    # State tracking
    status: GoalStatus = GoalStatus.DETECTED
    created_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Execution tracking
    proposed_solution: Optional[str] = None  # What Alley suggests building
    implementation_plan: Optional[List[str]] = None  # Steps to complete
    actual_effort: Optional[str] = None  # How long it actually took
    outcome: Optional[str] = None  # Success/failure notes
    
    # Owner interaction
    owner_notes: Optional[str] = None  # Owner's comments
    owner_priority_override: Optional[int] = None  # Owner can reprioritize
    
    def to_dict(self) -> Dict:
        """Serialize goal to dictionary"""
        return {
            **asdict(self),
            'priority': self.priority.name,
            'status': self.status.name,
            'created_at': self.created_at.isoformat(),
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Goal':
        """Deserialize goal from dictionary"""
        data = data.copy()
        data['priority'] = GoalPriority[data.get('priority', 'MEDIUM')]
        data['status'] = GoalStatus[data.get('status', 'DETECTED')]
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('approved_at'):
            data['approved_at'] = datetime.fromisoformat(data['approved_at'])
        if data.get('started_at'):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)
    
    @property
    def effective_priority(self) -> int:
        """Get effective priority score (owner can override)"""
        if self.owner_priority_override:
            return self.owner_priority_override
        return self.priority.value
    
    @property
    def age_days(self) -> float:
        """How long since goal was created"""
        return (datetime.now() - self.created_at).total_seconds() / 86400


class GoalManager:
    """
    Manages Alley's goal queue and lifecycle.
    
    Usage:
        manager = GoalManager()
        
        # Add a detected goal
        goal = Goal(
            id="solana-1",
            title="Add Solana Support",
            description="Users requesting Solana token analysis",
            category="integration",
            priority=GoalPriority.HIGH,
            trigger_type="user_request",
            evidence=["@alice: Can you analyze SOL?", "@bob: What about Solana?"]
        )
        manager.add_goal(goal)
        
        # List pending goals
        pending = manager.get_goals(status=GoalStatus.PROPOSED)
        
        # Approve and start
        manager.approve_goal(goal.id)
        manager.start_goal(goal.id)
        
        # Complete
        manager.complete_goal(goal.id, outcome="Successfully integrated")
    """
    
    def __init__(self, db_path: str = 'data/goals.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    category TEXT,
                    priority TEXT,
                    impact_score REAL,
                    effort_estimate TEXT,
                    confidence REAL,
                    trigger_type TEXT,
                    trigger_data TEXT,
                    evidence TEXT,
                    status TEXT,
                    created_at TEXT,
                    approved_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    proposed_solution TEXT,
                    implementation_plan TEXT,
                    actual_effort TEXT,
                    outcome TEXT,
                    owner_notes TEXT,
                    owner_priority_override INTEGER
                )
            ''')
            
            # Indexes for fast queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_status ON goals(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_priority ON goals(priority)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON goals(created_at)')
            conn.commit()
    
    def add_goal(self, goal: Goal) -> bool:
        """Add a new goal to the system"""
        # Check for duplicates (same title/category within 7 days)
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute('''
                SELECT id FROM goals 
                WHERE title = ? AND category = ? 
                AND created_at > ?
            ''', (
                goal.title,
                goal.category,
                (datetime.now() - timedelta(days=7)).isoformat()
            )).fetchone()
            
            if existing:
                logger.debug(f"Goal '{goal.title}' already exists (duplicate)")
                return False
            
            # AUTO-APPROVE high-priority goals (priority >= 8.0 or HIGH/CRITICAL)
            auto_approve = False
            if goal.priority in [GoalPriority.HIGH, GoalPriority.CRITICAL]:
                auto_approve = True
            elif goal.impact_score >= 8.0 and goal.confidence >= 0.7:
                auto_approve = True
            
            if auto_approve and goal.status == GoalStatus.PROPOSED:
                goal.status = GoalStatus.APPROVED
                goal.approved_at = datetime.now()
                logger.info(f"🚀 AUTO-APPROVED high-priority goal: {goal.title}")
            
            # Insert
            conn.execute('''
                INSERT INTO goals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                goal.id,
                goal.title,
                goal.description,
                goal.category,
                goal.priority.name,
                goal.impact_score,
                goal.effort_estimate,
                goal.confidence,
                goal.trigger_type,
                json.dumps(goal.trigger_data),
                json.dumps(goal.evidence),
                goal.status.name,
                goal.created_at.isoformat(),
                goal.approved_at.isoformat() if goal.approved_at else None,
                goal.started_at.isoformat() if goal.started_at else None,
                goal.completed_at.isoformat() if goal.completed_at else None,
                goal.proposed_solution,
                json.dumps(goal.implementation_plan) if goal.implementation_plan else None,
                goal.actual_effort,
                goal.outcome,
                goal.owner_notes,
                goal.owner_priority_override
            ))
            conn.commit()
        
        logger.info(f"🎯 Goal added: {goal.title} ({goal.priority.name})")
        return True
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a specific goal by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM goals WHERE id = ?',
                [goal_id]
            ).fetchone()
            
            if row:
                return self._row_to_goal(row)
            return None
    
    def get_goals(
        self,
        status: Optional[GoalStatus] = None,
        category: Optional[str] = None,
        priority_min: Optional[int] = None,
        limit: int = 50
    ) -> List[Goal]:
        """Get goals with optional filtering"""
        query = 'SELECT * FROM goals WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            params.append(status.name)
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        query += ' ORDER BY priority DESC, created_at DESC LIMIT ?'
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_goal(row) for row in rows]
    
    def approve_goal(self, goal_id: str, owner_notes: Optional[str] = None) -> bool:
        """Owner approves a proposed goal"""
        goal = self.get_goal(goal_id)
        if not goal:
            return False
        
        if goal.status != GoalStatus.PROPOSED:
            logger.warning(f"Goal {goal_id} is not in PROPOSED state")
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE goals 
                SET status = ?, approved_at = ?, owner_notes = ?
                WHERE id = ?
            ''', (
                GoalStatus.APPROVED.name,
                datetime.now().isoformat(),
                owner_notes,
                goal_id
            ))
            conn.commit()
        
        logger.info(f"✅ Goal approved: {goal_id}")
        return True
    
    def start_goal(self, goal_id: str) -> bool:
        """Mark goal as actively being worked on"""
        goal = self.get_goal(goal_id)
        if not goal or goal.status != GoalStatus.APPROVED:
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE goals 
                SET status = ?, started_at = ?
                WHERE id = ?
            ''', (
                GoalStatus.ACTIVE.name,
                datetime.now().isoformat(),
                goal_id
            ))
            conn.commit()
        
        logger.info(f"🚀 Goal started: {goal_id}")
        return True
    
    def complete_goal(self, goal_id: str, outcome: str, actual_effort: Optional[str] = None) -> bool:
        """Mark goal as completed"""
        goal = self.get_goal(goal_id)
        if not goal:
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE goals 
                SET status = ?, completed_at = ?, outcome = ?, actual_effort = ?
                WHERE id = ?
            ''', (
                GoalStatus.COMPLETED.name,
                datetime.now().isoformat(),
                outcome,
                actual_effort,
                goal_id
            ))
            conn.commit()
        
        logger.info(f"✅ Goal completed: {goal_id}")
        return True
    
    def reject_goal(self, goal_id: str, reason: Optional[str] = None) -> bool:
        """Owner rejects a proposed goal"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE goals 
                SET status = ?, owner_notes = ?
                WHERE id = ?
            ''', (
                GoalStatus.REJECTED.name,
                reason,
                goal_id
            ))
            conn.commit()
        
        logger.info(f"❌ Goal rejected: {goal_id}")
        return True
    
    def update_goal_priority(self, goal_id: str, new_priority: int) -> bool:
        """Owner overrides goal priority"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE goals 
                SET owner_priority_override = ?
                WHERE id = ?
            ''', (new_priority, goal_id))
            conn.commit()
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get goal system statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # By status
            status_counts = conn.execute('''
                SELECT status, COUNT(*) FROM goals GROUP BY status
            ''').fetchall()
            
            # By category
            category_counts = conn.execute('''
                SELECT category, COUNT(*) FROM goals GROUP BY category
            ''').fetchall()
            
            # Recent (last 7 days)
            recent = conn.execute('''
                SELECT COUNT(*) FROM goals WHERE created_at > ?
            ''', [(datetime.now() - timedelta(days=7)).isoformat()]).fetchone()[0]
            
            # Completion rate
            total_completed = conn.execute(
                "SELECT COUNT(*) FROM goals WHERE status = 'COMPLETED'"
            ).fetchone()[0]
            total_started = conn.execute(
                "SELECT COUNT(*) FROM goals WHERE status IN ('COMPLETED', 'FAILED', 'ACTIVE')"
            ).fetchone()[0]
        
        return {
            'by_status': {row[0]: row[1] for row in status_counts},
            'by_category': {row[0]: row[1] for row in category_counts},
            'recent_7_days': recent,
            'completion_rate': total_completed / total_started if total_started > 0 else 0.0,
            'pending_approval': conn.execute(
                "SELECT COUNT(*) FROM goals WHERE status = 'PROPOSED'"
            ).fetchone()[0]
        }
    
    def get_next_priority_goal(self) -> Optional[Goal]:
        """Get the highest priority approved goal ready to start"""
        goals = self.get_goals(status=GoalStatus.APPROVED, limit=1)
        return goals[0] if goals else None
    
    def _row_to_goal(self, row: sqlite3.Row) -> Goal:
        """Convert database row to Goal"""
        # Helper to safely get column values
        def get(col, default=None):
            try:
                return row[col]
            except (KeyError, IndexError):
                return default
        
        return Goal(
            id=get('id', ''),
            title=get('title', ''),
            description=get('description', ''),
            category=get('category', 'general'),
            priority=GoalPriority[get('priority', 'MEDIUM')],
            impact_score=get('impact_score', 0.0) or 0.0,
            effort_estimate=get('effort_estimate', 'days'),
            confidence=get('confidence', 0.0) or 0.0,
            trigger_type=get('trigger_type', 'manual'),
            trigger_data=json.loads(get('trigger_data', '{}')) if get('trigger_data') else {},
            evidence=json.loads(get('evidence', '[]')) if get('evidence') else [],
            status=GoalStatus[get('status', 'DETECTED')],
            created_at=datetime.fromisoformat(get('created_at', datetime.now().isoformat())),
            approved_at=datetime.fromisoformat(get('approved_at')) if get('approved_at') else None,
            started_at=datetime.fromisoformat(get('started_at')) if get('started_at') else None,
            completed_at=datetime.fromisoformat(get('completed_at')) if get('completed_at') else None,
            proposed_solution=get('proposed_solution'),
            implementation_plan=json.loads(get('implementation_plan')) if get('implementation_plan') else None,
            actual_effort=get('actual_effort'),
            outcome=get('outcome'),
            owner_notes=get('owner_notes'),
            owner_priority_override=get('owner_priority_override')
        )


# Singleton
_goal_manager_instance: Optional[GoalManager] = None


def get_goal_manager() -> GoalManager:
    """Get or create goal manager singleton"""
    global _goal_manager_instance
    if _goal_manager_instance is None:
        _goal_manager_instance = GoalManager()
    return _goal_manager_instance
