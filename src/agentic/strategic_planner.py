"""
Strategic Planning Horizon

Multi-day strategic planning that decomposes into persistent intents.
Brain operates on a 7-day rolling horizon with adaptive replanning.
"""

import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)


class MilestoneStatus(Enum):
    """Status of strategic milestones."""
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    MISSED = auto()


@dataclass
class StrategicMilestone:
    """A milestone within a strategic plan."""
    id: str
    description: str
    target_date: datetime
    success_criteria: str
    status: MilestoneStatus = MilestoneStatus.PENDING
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    
    @property
    def days_remaining(self) -> int:
        """Days until this milestone is due."""
        return max(0, (self.target_date - datetime.now()).days)
    
    @property
    def is_overdue(self) -> bool:
        """Check if milestone is past due."""
        return datetime.now() > self.target_date and self.status != MilestoneStatus.COMPLETED


@dataclass
class StrategicPlan:
    """
    A 7-day rolling strategic plan.
    
    Plans decompose into persistent intents and milestones.
    Adapt based on outcome feedback from previous cycles.
    """
    id: str
    title: str
    description: str
    
    # Time bounds
    created_at: datetime = field(default_factory=datetime.now)
    horizon_days: int = 7
    
    # Plan components
    milestones: List[StrategicMilestone] = field(default_factory=list)
    related_intent_ids: List[str] = field(default_factory=list)
    
    # Adaptive learning
    previous_plan_id: Optional[str] = None
    adaptations: List[str] = field(default_factory=list)  # What changed from previous plan
    
    # State
    is_active: bool = True
    completion_rate: float = 0.0
    
    def get_active_milestone(self) -> Optional[StrategicMilestone]:
        """Get the current active milestone."""
        for m in self.milestones:
            if m.status == MilestoneStatus.IN_PROGRESS:
                return m
            if m.status == MilestoneStatus.PENDING:
                m.status = MilestoneStatus.IN_PROGRESS
                return m
        return None
    
    def complete_milestone(self, milestone_id: str, outcome: str) -> bool:
        """Mark a milestone as completed."""
        for m in self.milestones:
            if m.id == milestone_id:
                m.status = MilestoneStatus.COMPLETED
                m.completed_at = datetime.now()
                m.outcome = outcome
                self._update_completion_rate()
                logger.info(f"✅ Strategic milestone completed: {m.description[:50]}...")
                return True
        return False
    
    def _update_completion_rate(self) -> None:
        """Recalculate completion rate."""
        if not self.milestones:
            return
        completed = sum(1 for m in self.milestones if m.status == MilestoneStatus.COMPLETED)
        self.completion_rate = completed / len(self.milestones)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            **asdict(self),
            'created_at': self.created_at.isoformat(),
            'milestones': [{
                **asdict(m),
                'target_date': m.target_date.isoformat(),
                'completed_at': m.completed_at.isoformat() if m.completed_at else None,
                'status': m.status.name,
            } for m in self.milestones],
        }


class StrategicPlanner:
    """
    Maintains a 7-day rolling strategic plan.
    
    Integrates with PersistentIntentManager to decompose plans
    into actionable intents. Learns from outcome feedback.
    """
    
    PLAN_TEMPLATES = {
        'growth': [
            ("Day 1-2: Establish baseline metrics", "Have current stats recorded"),
            ("Day 3-4: Execute first growth action", "At least 1 engagement or content piece"),
            ("Day 5-6: Analyze and optimize", "Document what worked/didn't"),
            ("Day 7: Plan next week based on learnings", "Have refined strategy ready"),
        ],
        'engagement': [
            ("Day 1-2: Identify high-value targets", "List of 10+ accounts to engage"),
            ("Day 3-4: Execute engagement campaign", "5+ meaningful interactions"),
            ("Day 5-6: Measure response rates", "Track which approaches worked"),
            ("Day 7: Follow up on best responses", "Maintain relationships"),
        ],
        'learning': [
            ("Day 1: Research capability requirements", "Know what needs to be built"),
            ("Day 2-3: Design and prototype", "Working sandbox version"),
            ("Day 4-5: Test and refine", "Pass basic validation"),
            ("Day 6-7: Deploy and monitor", "Live with fallback ready"),
        ],
        'revenue': [
            ("Day 1-2: Identify revenue opportunities", "List of 3+ potential sources"),
            ("Day 3-4: Evaluate and prioritize", "Ranked by effort/return"),
            ("Day 5-6: Execute top opportunity", "Actual progress on #1"),
            ("Day 7: Measure and iterate", "Document results, adjust"),
        ],
    }
    
    def __init__(
        self,
        db_path: str = 'data/strategic_plans.db',
        intent_manager=None
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.intent_manager = intent_manager
        self._current_plan: Optional[StrategicPlan] = None
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS strategic_plans (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    created_at TEXT,
                    horizon_days INTEGER,
                    milestones TEXT,  -- JSON
                    related_intent_ids TEXT,  -- JSON list
                    previous_plan_id TEXT,
                    adaptations TEXT,  -- JSON list
                    is_active INTEGER,
                    completion_rate REAL
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_active ON strategic_plans(is_active)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON strategic_plans(created_at)')
            conn.commit()
    
    def create_plan(
        self,
        plan_type: str,
        owner_objectives: List[Dict],
        recent_outcomes: Optional[List[Dict]] = None,
    ) -> Optional[StrategicPlan]:
        """
        Create a new strategic plan based on type and objectives.
        
        Args:
            plan_type: One of 'growth', 'engagement', 'learning', 'revenue'
            owner_objectives: Active owner objectives
            recent_outcomes: Recent action outcomes for adaptation
            
        Returns:
            StrategicPlan or None if insufficient information
        """
        if plan_type not in self.PLAN_TEMPLATES:
            logger.warning(f"Unknown plan type: {plan_type}")
            return None
        
        # Get previous plan for adaptation
        previous_plan = self.get_current_plan()
        adaptations = []
        
        # Analyze recent outcomes for learning
        if recent_outcomes:
            success_rate = sum(1 for o in recent_outcomes if o.get('success')) / len(recent_outcomes)
            if success_rate < 0.5:
                adaptations.append(f"Low success rate ({success_rate:.0%}) - simplifying approach")
        
        # Build milestones from template
        now = datetime.now()
        template = self.PLAN_TEMPLATES[plan_type]
        milestones = []
        
        for i, (desc, criteria) in enumerate(template):
            target = now + timedelta(days=(i + 1) * 2 - 1)
            milestones.append(StrategicMilestone(
                id=f"m_{int(now.timestamp())}_{i}",
                description=desc,
                target_date=target,
                success_criteria=criteria,
            ))
        
        # Create plan
        plan_id = f"plan_{int(now.timestamp())}"
        plan = StrategicPlan(
            id=plan_id,
            title=f"Strategic Plan: {plan_type.capitalize()}",
            description=f"7-day rolling plan focused on {plan_type} objectives",
            created_at=now,
            milestones=milestones,
            previous_plan_id=previous_plan.id if previous_plan else None,
            adaptations=adaptations,
        )
        
        # Store plan
        self._store_plan(plan)
        
        # Decompose into persistent intents if intent manager available
        if self.intent_manager:
            self._decompose_plan_to_intents(plan, owner_objectives)
        
        logger.info(f"📋 Strategic plan created: {plan.title}")
        for m in plan.milestones:
            logger.info(f"   📅 {m.description[:50]}... (due: {m.target_date.strftime('%Y-%m-%d')})")
        
        return plan
    
    def _decompose_plan_to_intents(
        self,
        plan: StrategicPlan,
        owner_objectives: List[Dict]
    ) -> None:
        """Decompose strategic plan into persistent intents."""
        # Map plan type to intent objective
        objective_map = {
            'growth': 'Execute strategic growth plan with measurable milestones',
            'engagement': 'Maintain consistent engagement schedule',
            'learning': 'Build required capabilities per strategic timeline',
            'revenue': 'Execute revenue generation opportunities',
        }
        
        # Find matching owner objective
        owner_obj_id = None
        for obj in owner_objectives:
            obj_desc = obj.get('description', '').lower()
            if plan.title.lower().replace('strategic plan: ', '') in obj_desc:
                owner_obj_id = obj.get('id')
                break
        
        # Create intent for this plan
        from src.agentic.persistent_intent import get_persistent_intent_manager
        intent_mgr = get_persistent_intent_manager()
        
        intent_id = intent_mgr.create_intent(
            objective=objective_map.get('growth', plan.title),  # Default to growth
            success_criteria={
                'plan_type': plan.title,
                'milestone_count': len(plan.milestones),
                'target_completion_rate': 0.75,
            },
            deadline=plan.created_at + timedelta(days=plan.horizon_days),
            cooldown_hours=12,  # Check twice daily
            max_daily_actions=2,
            priority=7,
            owner_objective_id=owner_obj_id,
            initial_plan=[m.description for m in plan.milestones],
        )
        
        plan.related_intent_ids.append(intent_id)
        self._store_plan(plan)
        
        logger.info(f"   🎯 Decomposed into intent: {intent_id}")
    
    def get_current_plan(self) -> Optional[StrategicPlan]:
        """Get the currently active strategic plan."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute('''
                SELECT * FROM strategic_plans 
                WHERE is_active = 1 
                ORDER BY created_at DESC 
                LIMIT 1
            ''').fetchone()
            
            if row:
                return self._row_to_plan(row)
            return None
    
    def advance_plan(self) -> Optional[StrategicPlan]:
        """
        Advance to next planning cycle.
        
        If current plan is complete (>75% milestones done), create new plan.
        If current plan is stalled, adapt it.
        """
        current = self.get_current_plan()
        
        if not current:
            logger.info("No active plan - creating default growth plan")
            return self.create_plan('growth', [])
        
        # Check if plan is complete
        if current.completion_rate >= 0.75:
            # Mark complete, create new plan
            current.is_active = False
            self._store_plan(current)
            
            # Determine next plan type based on what worked
            next_type = self._determine_next_plan_type(current)
            return self.create_plan(next_type, [])
        
        # Check for overdue milestones
        overdue = [m for m in current.milestones if m.is_overdue and m.status != MilestoneStatus.COMPLETED]
        if overdue:
            for m in overdue:
                m.status = MilestoneStatus.MISSED
                logger.warning(f"⏰ Milestone missed: {m.description[:50]}...")
            self._store_plan(current)
        
        return current
    
    def _determine_next_plan_type(self, completed_plan: StrategicPlan) -> str:
        """Determine what type of plan to create next based on outcomes."""
        # Simple logic: rotate through types, prioritizing what had success
        completion = completed_plan.completion_rate
        
        if completion > 0.9:
            return 'engagement'  # High success → build relationships
        elif completion > 0.75:
            return 'growth'  # Good success → keep growing
        else:
            return 'learning'  # Lower success → build capabilities first
    
    def get_plan_status(self, plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed status of a plan (current plan by default)."""
        if plan_id:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    'SELECT * FROM strategic_plans WHERE id = ?',
                    (plan_id,)
                ).fetchone()
                plan = self._row_to_plan(row) if row else None
        else:
            plan = self.get_current_plan()
        
        if not plan:
            return {'error': 'No plan found'}
        
        active = plan.get_active_milestone()
        
        return {
            'plan_id': plan.id,
            'title': plan.title,
            'description': plan.description,
            'created_at': plan.created_at.isoformat(),
            'days_elapsed': (datetime.now() - plan.created_at).days,
            'horizon_days': plan.horizon_days,
            'completion_rate': plan.completion_rate,
            'milestones_total': len(plan.milestones),
            'milestones_completed': sum(1 for m in plan.milestones if m.status == MilestoneStatus.COMPLETED),
            'active_milestone': {
                'description': active.description,
                'days_remaining': active.days_remaining,
                'is_overdue': active.is_overdue,
            } if active else None,
            'adaptations': plan.adaptations,
            'related_intents': plan.related_intent_ids,
        }
    
    def _store_plan(self, plan: StrategicPlan) -> None:
        """Store plan in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO strategic_plans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plan.id,
                plan.title,
                plan.description,
                plan.created_at.isoformat(),
                plan.horizon_days,
                json.dumps([{
                    **asdict(m),
                    'target_date': m.target_date.isoformat(),
                    'completed_at': m.completed_at.isoformat() if m.completed_at else None,
                    'status': m.status.name,
                } for m in plan.milestones]),
                json.dumps(plan.related_intent_ids),
                plan.previous_plan_id,
                json.dumps(plan.adaptations),
                1 if plan.is_active else 0,
                plan.completion_rate,
            ))
            conn.commit()
    
    def _row_to_plan(self, row: sqlite3.Row) -> StrategicPlan:
        """Convert database row to StrategicPlan."""
        def load_json(field):
            try:
                return json.loads(row[field]) if row[field] else []
            except:
                return []
        
        milestones_data = load_json('milestones')
        milestones = []
        for m in milestones_data:
            milestones.append(StrategicMilestone(
                id=m['id'],
                description=m['description'],
                target_date=datetime.fromisoformat(m['target_date']),
                success_criteria=m['success_criteria'],
                status=MilestoneStatus[m.get('status', 'PENDING')],
                completed_at=datetime.fromisoformat(m['completed_at']) if m.get('completed_at') else None,
                outcome=m.get('outcome'),
            ))
        
        return StrategicPlan(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            created_at=datetime.fromisoformat(row['created_at']),
            horizon_days=row['horizon_days'] or 7,
            milestones=milestones,
            related_intent_ids=load_json('related_intent_ids'),
            previous_plan_id=row['previous_plan_id'],
            adaptations=load_json('adaptations'),
            is_active=bool(row['is_active']),
            completion_rate=row['completion_rate'] or 0.0,
        )
    
    def get_summary(self) -> str:
        """Get human-readable summary of current strategic state."""
        plan = self.get_current_plan()
        
        lines = ["📋 Strategic Plan Summary"]
        lines.append("=" * 40)
        
        if not plan:
            lines.append("  (No active strategic plan)")
            return "\n".join(lines)
        
        lines.append(f"🎯 {plan.title}")
        lines.append(f"   Progress: {plan.completion_rate:.0%} complete")
        lines.append(f"   Day {min(7, (datetime.now() - plan.created_at).days)} of 7")
        
        active = plan.get_active_milestone()
        if active:
            icon = "⏰" if active.is_overdue else "▶️"
            lines.append(f"\n   {icon} Current milestone:")
            lines.append(f"      {active.description[:50]}...")
            if active.days_remaining > 0:
                lines.append(f"      Due in {active.days_remaining} days")
            elif active.is_overdue:
                lines.append(f"      ⚠️ Overdue by {abs(active.days_remaining)} days")
        
        return "\n".join(lines)


# Singleton
_planner_instance: Optional[StrategicPlanner] = None


def get_strategic_planner(intent_manager=None) -> StrategicPlanner:
    """Get or create singleton instance."""
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = StrategicPlanner(intent_manager=intent_manager)
    return _planner_instance
