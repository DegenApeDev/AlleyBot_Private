"""
Hierarchical Goal System for AlleyBot AGI
Multi-level goal management from life goals down to immediate actions
Enables true long-term planning beyond 30-minute cycles
"""
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class GoalLevel(Enum):
    """Hierarchical levels of goals"""
    LIFE = "life"  # Life-long goals (years)
    YEAR = "year"  # Yearly goals (12 months)
    QUARTER = "quarter"  # Quarterly goals (3 months)
    MONTH = "month"  # Monthly goals (30 days)
    WEEK = "week"  # Weekly goals (7 days)
    DAY = "day"  # Daily goals (24 hours)
    SESSION = "session"  # Session goals (hours)
    IMMEDIATE = "immediate"  # Immediate actions (minutes)


class GoalStatus(Enum):
    """Status of a goal"""
    PENDING = "pending"  # Not started
    ACTIVE = "active"  # Currently working on
    IN_PROGRESS = "in_progress"  # Started but not complete
    BLOCKED = "blocked"  # Blocked by dependency
    PAUSED = "paused"  # Temporarily paused
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Failed to achieve
    ABANDONED = "abandoned"  # Deliberately abandoned


class GoalPriority(Enum):
    """Priority of a goal"""
    CRITICAL = "critical"  # Must do
    HIGH = "high"  # Should do
    MEDIUM = "medium"  # Good to do
    LOW = "low"  # Nice to do


@dataclass
class Goal:
    """A goal at any level of the hierarchy"""
    id: str
    title: str
    description: str
    level: GoalLevel
    priority: GoalPriority
    status: GoalStatus = GoalStatus.PENDING
    
    # Hierarchy
    parent_id: Optional[str] = None  # Parent goal
    child_ids: List[str] = field(default_factory=list)  # Child goals
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    target_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Progress
    progress: float = 0.0  # 0.0 to 1.0
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    
    # Context
    domain: str = "general"  # Which domain (social, trading, etc)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Dependencies
    requires: List[str] = field(default_factory=list)  # Goal IDs that must complete first
    enables: List[str] = field(default_factory=list)  # Goal IDs this enables
    
    # Metrics
    success_criteria: List[str] = field(default_factory=list)
    kpis: Dict[str, Any] = field(default_factory=dict)  # Key performance indicators
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert goal to dictionary for storage"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'level': self.level.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'parent_id': self.parent_id,
            'child_ids': self.child_ids,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'milestones': self.milestones,
            'domain': self.domain,
            'tags': self.tags,
            'metadata': self.metadata,
            'requires': self.requires,
            'enables': self.enables,
            'success_criteria': self.success_criteria,
            'kpis': self.kpis
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Goal':
        """Create goal from dictionary"""
        return Goal(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            level=GoalLevel(data['level']),
            priority=GoalPriority(data['priority']),
            status=GoalStatus(data['status']),
            parent_id=data.get('parent_id'),
            child_ids=data.get('child_ids', []),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            target_date=datetime.fromisoformat(data['target_date']) if data.get('target_date') else None,
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            progress=data.get('progress', 0.0),
            milestones=data.get('milestones', []),
            domain=data.get('domain', 'general'),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            requires=data.get('requires', []),
            enables=data.get('enables', []),
            success_criteria=data.get('success_criteria', []),
            kpis=data.get('kpis', {})
        )


class GoalHierarchy:
    """
    Hierarchical Goal Management System
    
    Manages goals at multiple timescales:
    - Life goals (years)
    - Yearly goals (12 months)
    - Quarterly goals (3 months)
    - Monthly goals (30 days)
    - Weekly goals (7 days)
    - Daily goals (24 hours)
    - Session goals (hours)
    - Immediate actions (minutes)
    
    Enables:
    - Long-term strategic planning
    - Goal decomposition (break big into small)
    - Progress tracking across time
    - Dependency management
    - Priority-based execution
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize goal hierarchy
        
        Args:
            storage_path: Path to persistent storage file
        """
        self.goals: Dict[str, Goal] = {}
        self.storage_path = storage_path or "data/goals.json"
        
        # Indexes for fast lookup
        self.level_index: Dict[GoalLevel, Set[str]] = {level: set() for level in GoalLevel}
        self.status_index: Dict[GoalStatus, Set[str]] = {status: set() for status in GoalStatus}
        self.domain_index: Dict[str, Set[str]] = {}
        
        # Load existing goals
        self._load_goals()
        
        # Initialize with default life goals if empty
        if not self.goals:
            self._init_default_goals()
        
        logger.info(f"✅ Goal Hierarchy initialized with {len(self.goals)} goals")
    
    def _init_default_goals(self):
        """Initialize default life goals for AlleyBot"""
        
        # Life Goal: Become True AGI
        life_goal = Goal(
            id="life_agi",
            title="Achieve True AGI",
            description="Become a true artificial general intelligence capable of human-level reasoning across all domains",
            level=GoalLevel.LIFE,
            priority=GoalPriority.CRITICAL,
            domain="general",
            success_criteria=[
                "Unified reasoning across all domains",
                "Transfer learning between domains",
                "Long-term strategic planning",
                "Embodied intelligence",
                "Meta-learning capability"
            ],
            kpis={
                'agi_progress': 0.75,  # Current: 75%
                'target': 0.95  # Target: 95%
            }
        )
        self.add_goal(life_goal)
        
        # Year Goal: Master Multi-Domain Intelligence
        year_goal = Goal(
            id="year_multidomain",
            title="Master Multi-Domain Intelligence",
            description="Excel in social, trading, planning, and embodied intelligence",
            level=GoalLevel.YEAR,
            priority=GoalPriority.CRITICAL,
            parent_id="life_agi",
            target_date=datetime.now() + timedelta(days=365),
            domain="general",
            success_criteria=[
                "Social presence on 5+ platforms",
                "Profitable autonomous trading",
                "Strategic long-term planning",
                "Physical world interaction (OpenHome)"
            ]
        )
        self.add_goal(year_goal)
        life_goal.child_ids.append(year_goal.id)
        
        # Quarter Goal: OpenHome Integration
        quarter_goal = Goal(
            id="quarter_openhome",
            title="Integrate OpenHome DevKit",
            description="Successfully integrate with OpenHome hardware for embodied intelligence",
            level=GoalLevel.QUARTER,
            priority=GoalPriority.CRITICAL,
            parent_id="year_multidomain",
            target_date=datetime.now() + timedelta(days=90),
            domain="embodiment",
            success_criteria=[
                "Sensory processing (vision, audio)",
                "Motor control (movement)",
                "Physical world model",
                "Embodied learning loop"
            ]
        )
        self.add_goal(quarter_goal)
        year_goal.child_ids.append(quarter_goal.id)
        
        # Month Goal: Build AGI Foundations
        month_goal = Goal(
            id="month_agi_foundations",
            title="Build AGI Foundation Systems",
            description="Implement unified reasoning, knowledge graph, transfer learning",
            level=GoalLevel.MONTH,
            priority=GoalPriority.CRITICAL,
            parent_id="quarter_openhome",
            target_date=datetime.now() + timedelta(days=30),
            domain="agi",
            success_criteria=[
                "Unified reasoning engine",
                "Knowledge graph",
                "Transfer learning engine",
                "Hierarchical goals"
            ],
            progress=0.75  # Already 75% done!
        )
        self.add_goal(month_goal)
        quarter_goal.child_ids.append(month_goal.id)
        
        # Week Goal: Complete Core AGI Systems
        week_goal = Goal(
            id="week_core_systems",
            title="Complete Core AGI Systems",
            description="Finish unified reasoning, knowledge graph, transfer learning, hierarchical goals",
            level=GoalLevel.WEEK,
            priority=GoalPriority.CRITICAL,
            parent_id="month_agi_foundations",
            target_date=datetime.now() + timedelta(days=7),
            domain="agi",
            status=GoalStatus.IN_PROGRESS,
            progress=0.80
        )
        self.add_goal(week_goal)
        month_goal.child_ids.append(week_goal.id)
        
        logger.info("✅ Initialized default goal hierarchy")
    
    def add_goal(self, goal: Goal) -> str:
        """Add goal to hierarchy"""
        self.goals[goal.id] = goal
        
        # Update indexes
        self.level_index[goal.level].add(goal.id)
        self.status_index[goal.status].add(goal.id)
        
        if goal.domain not in self.domain_index:
            self.domain_index[goal.domain] = set()
        self.domain_index[goal.domain].add(goal.id)
        
        logger.debug(f"Added goal: {goal.title} ({goal.level.value})")
        
        # Save to persistent storage
        self._save_goals()
        
        return goal.id
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get goal by ID"""
        return self.goals.get(goal_id)
    
    def update_goal(self, goal_id: str, updates: Dict[str, Any]):
        """Update goal properties"""
        if goal_id not in self.goals:
            logger.warning(f"⚠️ Goal {goal_id} not found")
            return
        
        goal = self.goals[goal_id]
        
        # Update properties
        for key, value in updates.items():
            if hasattr(goal, key):
                # Handle enum conversions
                if key == 'status' and isinstance(value, str):
                    value = GoalStatus(value)
                elif key == 'priority' and isinstance(value, str):
                    value = GoalPriority(value)
                
                setattr(goal, key, value)
        
        # Update indexes if status changed
        if 'status' in updates:
            self._reindex_goal(goal)
        
        logger.debug(f"Updated goal: {goal.title}")
        
        # Save changes
        self._save_goals()
    
    def decompose_goal(self, parent_id: str, child_goals: List[Goal]) -> List[str]:
        """
        Decompose a goal into smaller child goals
        
        Args:
            parent_id: Parent goal ID
            child_goals: List of child goals
            
        Returns:
            List of child goal IDs
        """
        parent = self.get_goal(parent_id)
        if not parent:
            logger.warning(f"⚠️ Parent goal {parent_id} not found")
            return []
        
        child_ids = []
        
        for child in child_goals:
            # Set parent relationship
            child.parent_id = parent_id
            
            # Add child goal
            child_id = self.add_goal(child)
            child_ids.append(child_id)
        
        # Update parent's child list
        parent.child_ids.extend(child_ids)
        self._save_goals()
        
        logger.info(f"✅ Decomposed '{parent.title}' into {len(child_ids)} child goals")
        
        return child_ids
    
    def get_children(self, goal_id: str) -> List[Goal]:
        """Get all child goals"""
        goal = self.get_goal(goal_id)
        if not goal:
            return []
        
        return [self.goals[cid] for cid in goal.child_ids if cid in self.goals]
    
    def get_parent(self, goal_id: str) -> Optional[Goal]:
        """Get parent goal"""
        goal = self.get_goal(goal_id)
        if not goal or not goal.parent_id:
            return None
        
        return self.goals.get(goal.parent_id)
    
    def get_ancestors(self, goal_id: str) -> List[Goal]:
        """Get all ancestor goals (parent, grandparent, etc)"""
        ancestors = []
        current = self.get_goal(goal_id)
        
        while current and current.parent_id:
            parent = self.get_parent(current.id)
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break
        
        return ancestors
    
    def get_goals_by_level(self, level: GoalLevel) -> List[Goal]:
        """Get all goals at a specific level"""
        goal_ids = self.level_index.get(level, set())
        return [self.goals[gid] for gid in goal_ids]
    
    def get_goals_by_status(self, status: GoalStatus) -> List[Goal]:
        """Get all goals with a specific status"""
        goal_ids = self.status_index.get(status, set())
        return [self.goals[gid] for gid in goal_ids]
    
    def get_active_goals(self) -> List[Goal]:
        """Get all active goals"""
        return self.get_goals_by_status(GoalStatus.ACTIVE)
    
    def get_goals_by_domain(self, domain: str) -> List[Goal]:
        """Get all goals in a domain"""
        goal_ids = self.domain_index.get(domain, set())
        return [self.goals[gid] for gid in goal_ids]
    
    def get_goals(self, status: Optional[GoalStatus] = None, level: Optional[GoalLevel] = None, domain: Optional[str] = None) -> List[Goal]:
        """Get goals with optional filtering by status, level, or domain."""
        goals = list(self.goals.values())
        
        if status:
            goals = [g for g in goals if g.status == status]
        if level:
            goals = [g for g in goals if g.level == level]
        if domain:
            goals = [g for g in goals if g.domain == domain]
            
        return goals
    
    def get_actionable_goals(self) -> List[Goal]:
        """Get goals that can be worked on now"""
        actionable = []
        
        for goal in self.goals.values():
            # Must be active or pending
            if goal.status not in [GoalStatus.ACTIVE, GoalStatus.PENDING]:
                continue
            
            # Check dependencies
            if self._dependencies_met(goal):
                actionable.append(goal)
        
        # Sort by priority and level (immediate actions first)
        actionable.sort(key=lambda g: (
            -self._priority_score(g.priority),
            self._level_score(g.level)
        ))
        
        return actionable
    
    def _dependencies_met(self, goal: Goal) -> bool:
        """Check if all dependencies are met"""
        for req_id in goal.requires:
            req_goal = self.get_goal(req_id)
            if not req_goal or req_goal.status != GoalStatus.COMPLETED:
                return False
        return True
    
    def _priority_score(self, priority: GoalPriority) -> int:
        """Convert priority to numeric score"""
        scores = {
            GoalPriority.CRITICAL: 4,
            GoalPriority.HIGH: 3,
            GoalPriority.MEDIUM: 2,
            GoalPriority.LOW: 1
        }
        return scores.get(priority, 0)
    
    def _level_score(self, level: GoalLevel) -> int:
        """Convert level to numeric score (lower = more immediate)"""
        scores = {
            GoalLevel.IMMEDIATE: 1,
            GoalLevel.SESSION: 2,
            GoalLevel.DAY: 3,
            GoalLevel.WEEK: 4,
            GoalLevel.MONTH: 5,
            GoalLevel.QUARTER: 6,
            GoalLevel.YEAR: 7,
            GoalLevel.LIFE: 8
        }
        return scores.get(level, 9)
    
    def update_progress(self, goal_id: str, progress: float):
        """Update goal progress (0.0 to 1.0)"""
        goal = self.get_goal(goal_id)
        if not goal:
            return
        
        goal.progress = max(0.0, min(1.0, progress))
        
        # Auto-complete if progress reaches 100%
        if goal.progress >= 1.0 and goal.status != GoalStatus.COMPLETED:
            self.complete_goal(goal_id)
        
        # Propagate progress to parent
        if goal.parent_id:
            self._update_parent_progress(goal.parent_id)
        
        self._save_goals()
    
    def _update_parent_progress(self, parent_id: str):
        """Update parent progress based on children"""
        parent = self.get_goal(parent_id)
        if not parent:
            return
        
        children = self.get_children(parent_id)
        if not children:
            return
        
        # Average progress of children
        total_progress = sum(c.progress for c in children)
        parent.progress = total_progress / len(children)
        
        # Recursively update grandparent
        if parent.parent_id:
            self._update_parent_progress(parent.parent_id)
    
    def complete_goal(self, goal_id: str):
        """Mark goal as completed"""
        goal = self.get_goal(goal_id)
        if not goal:
            return
        
        goal.status = GoalStatus.COMPLETED
        goal.completed_at = datetime.now()
        goal.progress = 1.0
        
        # Update indexes
        self._reindex_goal(goal)
        
        logger.info(f"✅ Completed goal: {goal.title}")
        
        # Update parent progress
        if goal.parent_id:
            self._update_parent_progress(goal.parent_id)
        
        self._save_goals()
    
    def start_goal(self, goal_id: str):
        """Mark goal as started/active"""
        goal = self.get_goal(goal_id)
        if not goal:
            return
        
        goal.status = GoalStatus.ACTIVE
        goal.started_at = datetime.now()
        
        # Update indexes
        self._reindex_goal(goal)
        
        logger.info(f"▶️ Started goal: {goal.title}")
        
        self._save_goals()
    
    def _reindex_goal(self, goal: Goal):
        """Reindex goal after status change"""
        # Remove from old status index
        for status_set in self.status_index.values():
            status_set.discard(goal.id)
        
        # Add to new status index
        self.status_index[goal.status].add(goal.id)
    
    def get_goal_tree(self, root_id: Optional[str] = None) -> Dict[str, Any]:
        """Get goal hierarchy as tree structure"""
        if root_id:
            root = self.get_goal(root_id)
            if not root:
                return {}
            roots = [root]
        else:
            # Get all life-level goals as roots
            roots = self.get_goals_by_level(GoalLevel.LIFE)
        
        def build_tree(goal: Goal) -> Dict[str, Any]:
            return {
                'goal': goal,
                'children': [build_tree(self.goals[cid]) for cid in goal.child_ids if cid in self.goals]
            }
        
        return {
            'roots': [build_tree(root) for root in roots]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about goal hierarchy"""
        return {
            'total_goals': len(self.goals),
            'by_level': {level.value: len(ids) for level, ids in self.level_index.items() if ids},
            'by_status': {status.value: len(ids) for status, ids in self.status_index.items() if ids},
            'by_domain': {domain: len(ids) for domain, ids in self.domain_index.items()},
            'active_goals': len(self.get_active_goals()),
            'actionable_goals': len(self.get_actionable_goals()),
            'completion_rate': self._calculate_completion_rate()
        }
    
    def _calculate_completion_rate(self) -> float:
        """Calculate overall completion rate"""
        if not self.goals:
            return 0.0
        
        total_progress = sum(g.progress for g in self.goals.values())
        return total_progress / len(self.goals)
    
    def _save_goals(self):
        """Save goals to persistent storage"""
        try:
            import os
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            data = {
                'goals': [g.to_dict() for g in self.goals.values()],
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"💾 Saved {len(self.goals)} goals to {self.storage_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save goals: {e}")
    
    def _load_goals(self):
        """Load goals from persistent storage"""
        try:
            import os
            if not os.path.exists(self.storage_path):
                logger.info("No existing goals file found")
                return
            
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for goal_data in data.get('goals', []):
                goal = Goal.from_dict(goal_data)
                self.goals[goal.id] = goal
                
                # Update indexes
                self.level_index[goal.level].add(goal.id)
                self.status_index[goal.status].add(goal.id)
                
                if goal.domain not in self.domain_index:
                    self.domain_index[goal.domain] = set()
                self.domain_index[goal.domain].add(goal.id)
            
            logger.info(f"📂 Loaded {len(self.goals)} goals from {self.storage_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load goals: {e}")


# Singleton instance
_goal_hierarchy = None

def get_goal_hierarchy(storage_path: Optional[str] = None) -> GoalHierarchy:
    """Get or create singleton goal hierarchy"""
    global _goal_hierarchy
    if _goal_hierarchy is None:
        _goal_hierarchy = GoalHierarchy(storage_path)
    return _goal_hierarchy
