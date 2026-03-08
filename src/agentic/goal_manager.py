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

from src.agentic.planning import get_plan_manager

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
        self.plan_manager = get_plan_manager()
        self._init_db()

    def _infer_action_family_for_goal(self, goal: Goal) -> Optional[str]:
        """Infer likely action family for a goal from its category and text."""
        goal_blob = f"{goal.title} {goal.description} {goal.category}".lower()
        trigger_blob = json.dumps(goal.trigger_data or {}).lower()
        combined = f"{goal_blob} {trigger_blob}"

        if 'moltx' in combined or 'post' in combined or 'content' in combined:
            return 'post'
        if 'engage' in combined or 'reply' in combined or 'social' in combined:
            return 'engage'
        if 'analy' in combined or 'research' in combined or 'report' in combined:
            return 'analyze'
        if 'fix' in combined or 'repair' in combined or 'retry' in combined:
            return 'fix'
        return None

    def _score_goal_with_trust_state(self, goal: Goal) -> float:
        """Blend goal priority with persisted action-family trust state."""
        score = float(goal.effective_priority)
        action_family = self._infer_action_family_for_goal(goal)
        if not action_family:
            action_family = None

        trust_state = self.plan_manager.get_action_family_states().get(action_family, {}) if action_family else {}
        trust_bucket = trust_state.get('trust_bucket', 'healthy')
        degradation_score = float(trust_state.get('degradation_score', 0.0) or 0.0)
        recovery_score = float(trust_state.get('recovery_score', 0.0) or 0.0)

        if trust_bucket == 'degraded':
            score -= 2.5 + degradation_score
        elif trust_bucket == 'cooling_down':
            score -= 1.5 + (degradation_score * 0.5)
        elif trust_bucket == 'recovering':
            score += 0.75 + recovery_score
        elif trust_bucket == 'healthy':
            score += 0.25

        owner_notes = goal.owner_notes or ''
        if 'BLOCKED:' in owner_notes:
            last_blocked_marker = owner_notes.rsplit('BLOCKED:', 1)[-1].strip().lower()
            if last_blocked_marker:
                score -= 1.0
            if goal.started_at:
                hours_since_start = (datetime.now() - goal.started_at).total_seconds() / 3600
                if hours_since_start < 2:
                    score -= 1.5

        return score

    def should_auto_approve_goal(self, goal: Goal) -> bool:
        """Fail-closed policy for safe low-risk autonomous goal auto-approval."""
        if not goal:
            return False

        if goal.category not in {'analysis', 'optimization', 'fix'}:
            return False

        if goal.trigger_type not in {'gap', 'opportunity', 'error_pattern'}:
            return False

        if float(goal.impact_score or 0.0) > 6.5:
            return False

        if float(goal.confidence or 0.0) < 0.55:
            return False

        combined = f"{goal.title} {goal.description} {goal.category}".lower()
        blocked_markers = {
            'post', 'reply', 'wallet', 'transfer', 'trade', 'swap', 'claim',
            'deploy', 'delete', 'private key', 'self-update', 'update skill',
            'skill', 'code', 'patch', 'execute', 'message owner', 'telegram',
            'plugin lacks', 'create new skill', 'create new platform plugin',
            'register', 'write file', 'save file', 'commit', 'restart',
        }
        if any(marker in combined for marker in blocked_markers):
            return False

        action_family = self._infer_action_family_for_goal(goal)
        if goal.category == 'fix' and action_family not in {None, 'fix', 'analyze'}:
            return False
        if goal.category in {'analysis', 'optimization'} and action_family and action_family != 'analyze':
            return False

        trust_state = self.plan_manager.get_action_family_states().get(action_family or 'analyze', {})
        trust_bucket = trust_state.get('trust_bucket', 'healthy')
        return trust_bucket in {'healthy', 'recovering'}
    
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
            goals = [self._row_to_goal(row) for row in rows]

        if status in {GoalStatus.APPROVED, GoalStatus.ACTIVE, None}:
            goals.sort(key=lambda goal: (self._score_goal_with_trust_state(goal), goal.created_at.timestamp()), reverse=True)
        return goals

    def has_active_goals(self) -> bool:
        """Return True when at least one goal is already actively in progress."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM goals WHERE status = ?",
                [GoalStatus.ACTIVE.name],
            ).fetchone()
        return bool(row and row[0] > 0)
    
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

        try:
            from plugin_manager import get_plugin_manager
            plugin_manager = get_plugin_manager()
            telegram = plugin_manager.get_plugin('telegram') if plugin_manager else None
            if telegram and hasattr(telegram, 'notify_autonomous_accomplishment'):
                reward_signal = f"Completed a {goal.category} goal with priority {goal.priority.name.lower()}"
                summary = outcome[:240] if outcome else f"Goal {goal_id} completed successfully"
                telegram.notify_autonomous_accomplishment(goal.title, summary, reward_signal)
                if hasattr(telegram, 'maybe_send_autonomous_digest'):
                    telegram.maybe_send_autonomous_digest(hours=24, cooldown_hours=6)
        except Exception as e:
            logger.debug(f"Could not send goal completion notification: {e}")

        logger.info(f"✅ Goal completed: {goal_id}")
        return True
    
    def record_goal_action_success(self, goal_id: str, note: Optional[str] = None) -> bool:
        """Record progress for a safe active goal after a successful goal-tagged action."""
        goal = self.get_goal(goal_id)
        if not goal or goal.status != GoalStatus.ACTIVE:
            return False

        if not self.should_auto_approve_goal(goal):
            return False

        existing_notes = goal.owner_notes or ''
        progress_note = (note or 'Goal-aligned action succeeded').strip()[:180]
        blocked_count = existing_notes.count('BLOCKED:')
        if blocked_count > 0:
            trimmed_notes = existing_notes.rsplit('BLOCKED:', 1)[0].rstrip()
        else:
            trimmed_notes = existing_notes
        updated_notes = f"{trimmed_notes}\nSUCCESS: {progress_note}".strip()[:1000]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE goals
                SET owner_notes = ?
                WHERE id = ?
            ''', (
                updated_notes,
                goal_id,
            ))
            conn.commit()

        success_count = updated_notes.count('SUCCESS:')
        if success_count in {1, 2}:
            try:
                from plugin_manager import get_plugin_manager
                plugin_manager = get_plugin_manager()
                telegram = plugin_manager.get_plugin('telegram') if plugin_manager else None
                if telegram and hasattr(telegram, 'notify_autonomous_activity'):
                    telegram.notify_autonomous_activity(
                        'goal_progress',
                        f"Safe goal `{goal_id}` progressing ({success_count}/3): {goal.title[:120]}"
                    )
            except Exception as e:
                logger.debug(f"Could not send goal progress notification: {e}")

        if success_count >= 3:
            outcome = note or f"Completed after {success_count} successful goal-aligned actions"
            return self.complete_goal(goal_id, outcome=outcome)

        return True

    def record_goal_action_failure(self, goal_id: str, note: Optional[str] = None) -> bool:
        """Record failure for a safe active goal and fail it after repeated goal-tagged failures."""
        goal = self.get_goal(goal_id)
        if not goal or goal.status != GoalStatus.ACTIVE:
            return False

        if not self.should_auto_approve_goal(goal):
            return False

        existing_notes = goal.owner_notes or ''
        failure_note = (note or 'Goal-aligned action failed').strip()[:180]
        updated_notes = f"{existing_notes}\nFAILURE: {failure_note}".strip()[:1000]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE goals
                SET owner_notes = ?
                WHERE id = ?
            ''', (
                updated_notes,
                goal_id,
            ))
            conn.commit()

        failure_count = updated_notes.count('FAILURE:')
        if failure_count == 1:
            blocked_notes = f"{updated_notes}\nBLOCKED: {failure_note}".strip()[:1000]
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE goals
                    SET owner_notes = ?
                    WHERE id = ?
                ''', (
                    blocked_notes,
                    goal_id,
                ))
                conn.commit()
            updated_notes = blocked_notes

        if failure_count in {1, 2}:
            try:
                from plugin_manager import get_plugin_manager
                plugin_manager = get_plugin_manager()
                telegram = plugin_manager.get_plugin('telegram') if plugin_manager else None
                if telegram and hasattr(telegram, 'notify_autonomous_activity'):
                    telegram.notify_autonomous_activity(
                        'goal_cooling',
                        f"Safe goal `{goal_id}` hit resistance ({failure_count}/3): {goal.title[:120]}"
                    )
            except Exception as e:
                logger.debug(f"Could not send goal cooling notification: {e}")

        if failure_count >= 3:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE goals
                    SET status = ?, outcome = ?, owner_notes = ?
                    WHERE id = ?
                ''', (
                    GoalStatus.FAILED.name,
                    note or f"Goal failed after {failure_count} goal-aligned action failures",
                    updated_notes,
                    goal_id,
                ))
                conn.commit()
            logger.info(f"❌ Goal failed after repeated goal-aligned failures: {goal_id}")
            try:
                from plugin_manager import get_plugin_manager
                plugin_manager = get_plugin_manager()
                telegram = plugin_manager.get_plugin('telegram') if plugin_manager else None
                if telegram and hasattr(telegram, 'notify_autonomous_activity'):
                    telegram.notify_autonomous_activity(
                        'goal_failed',
                        f"Safe goal `{goal_id}` failed after repeated resistance: {goal.title[:120]}"
                    )
            except Exception as e:
                logger.debug(f"Could not send goal failed notification: {e}")
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

    def start_next_safe_goal(self) -> Optional[Goal]:
        """Start the next safe approved goal if no goal is currently active."""
        if self.has_active_goals():
            return None

        next_goal = self.get_next_priority_goal()
        if not next_goal:
            return None

        if not self.should_auto_approve_goal(next_goal):
            return None

        if not self.start_goal(next_goal.id):
            return None

        return self.get_goal(next_goal.id)
    
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
