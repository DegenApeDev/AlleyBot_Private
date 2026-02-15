"""
AlleyBot Multi-Step Planning System

Phase 3 of AGI Core: Multi-Step Planning

Enables Alley to break complex goals into executable sub-tasks:
1. Goal Decomposer - AI-driven step generation
2. Dependency Tracker - DAG-based dependency management
3. Plan Executor - Topological sort execution
4. Progress Monitor - State tracking & retry logic

Part of AGI Core - Phase 3: Multi-Step Planning
"""

import json
import sqlite3
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Step lifecycle states"""
    PENDING = auto()      # Not yet started
    READY = auto()        # Dependencies satisfied, can start
    ACTIVE = auto()       # Currently being executed
    COMPLETED = auto()  # Successfully finished
    FAILED = auto()       # Failed, needs retry or abort
    BLOCKED = auto()      # Waiting for dependencies
    SKIPPED = auto()      # Manually skipped


class StepType(Enum):
    """Types of plan steps"""
    RESEARCH = auto()     # Information gathering
    DESIGN = auto()     # Architecture/design
    IMPLEMENT = auto()  # Code implementation
    TEST = auto()       # Testing/validation
    DEPLOY = auto()     # Deployment
    REVIEW = auto()     # Code review
    DOCUMENT = auto()   # Documentation
    CUSTOM = auto()     # Custom step


@dataclass
class PlanStep:
    """
    A single step in a multi-step plan.
    
    Steps form a DAG via dependencies:
    - step.dependencies: List of step_ids that must complete first
    - step.dependents: List of step_ids waiting on this step
    """
    id: str
    goal_id: str  # Parent goal
    
    # Step definition
    title: str
    description: str
    step_type: StepType
    
    # Execution
    command: Optional[str]  # Command to execute (e.g., "create_file", "run_test")
    parameters: Dict[str, Any]  # Parameters for the command
    
    # Dependencies (DAG structure)
    dependencies: List[str] = field(default_factory=list)  # Must complete before this
    dependents: List[str] = field(default_factory=list)  # Waiting on this
    
    # State tracking
    status: StepStatus = StepStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Execution tracking
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    
    # Results
    output: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)  # Files created, etc.
    
    def to_dict(self) -> Dict:
        """Serialize step to dictionary"""
        return {
            **asdict(self),
            'step_type': self.step_type.name,
            'status': self.status.name,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    @property
    def is_ready(self) -> bool:
        """Check if all dependencies are satisfied"""
        return self.status == StepStatus.READY
    
    @property
    def can_retry(self) -> bool:
        """Check if step can be retried"""
        return self.attempts < self.max_attempts
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return None


@dataclass
class Plan:
    """
    A multi-step plan for achieving a goal.
    
    Contains a DAG of steps with automatic dependency resolution.
    """
    id: str
    goal_id: str
    title: str
    description: str
    
    # Steps (DAG)
    steps: Dict[str, PlanStep] = field(default_factory=dict)
    
    # State
    status: str = 'active'  # 'active', 'completed', 'failed', 'aborted'
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Progress
    current_step_id: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    
    @property
    def progress_percent(self) -> float:
        """Calculate completion percentage"""
        if not self.steps:
            return 0.0
        completed = len([s for s in self.steps.values() if s.status == StepStatus.COMPLETED])
        return (completed / len(self.steps)) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if all steps are completed"""
        return all(s.status == StepStatus.COMPLETED for s in self.steps.values())
    
    @property
    def has_failures(self) -> bool:
        """Check if any step has failed"""
        return any(s.status == StepStatus.FAILED for s in self.steps.values())
    
    def get_ready_steps(self) -> List[PlanStep]:
        """Get all steps that are ready to execute"""
        return [s for s in self.steps.values() if s.status == StepStatus.READY]
    
    def get_next_step(self) -> Optional[PlanStep]:
        """Get the next step to execute (topological order)"""
        ready = self.get_ready_steps()
        if ready:
            # Sort by step type priority, then by creation order
            type_priority = {
                StepType.RESEARCH: 1,
                StepType.DESIGN: 2,
                StepType.IMPLEMENT: 3,
                StepType.TEST: 4,
                StepType.REVIEW: 5,
                StepType.DOCUMENT: 6,
                StepType.DEPLOY: 7,
                StepType.CUSTOM: 8,
            }
            ready.sort(key=lambda s: (type_priority.get(s.step_type, 99), s.created_at))
            return ready[0]
        return None
    
    def update_step_status(self, step_id: str, new_status: StepStatus, error: Optional[str] = None):
        """Update step status and propagate to dependents"""
        if step_id not in self.steps:
            return
        
        step = self.steps[step_id]
        old_status = step.status
        step.status = new_status
        
        if error:
            step.last_error = error
        
        # Track completion/failure
        if new_status == StepStatus.COMPLETED and step_id not in self.completed_steps:
            self.completed_steps.append(step_id)
            if step_id in self.failed_steps:
                self.failed_steps.remove(step_id)
        elif new_status == StepStatus.FAILED and step_id not in self.failed_steps:
            self.failed_steps.append(step_id)
        
        # If completed, check if dependents are now ready
        if new_status == StepStatus.COMPLETED:
            for dep_id in step.dependents:
                dep_step = self.steps.get(dep_id)
                if dep_step and dep_step.status == StepStatus.BLOCKED:
                    # Check if all its dependencies are now complete
                    if all(
                        self.steps[d].status == StepStatus.COMPLETED 
                        for d in dep_step.dependencies 
                        if d in self.steps
                    ):
                        dep_step.status = StepStatus.READY
        
        logger.info(f"Step {step_id}: {old_status.name} → {new_status.name}")


class GoalDecomposer:
    """
    Decomposes goals into executable steps using AI/analysis.
    
    Usage:
        decomposer = GoalDecomposer()
        plan = decomposer.decompose_goal(goal)
    """
    
    # Step templates by goal category
    STEP_TEMPLATES = {
        'skill': [
            ('Research API', 'Research the API documentation and requirements', StepType.RESEARCH, [], []),
            ('Design Architecture', 'Design the skill structure and interfaces', StepType.DESIGN, ['research-api'], []),
            ('Implement Core', 'Implement the main skill functionality', StepType.IMPLEMENT, ['design-architecture'], []),
            ('Write Tests', 'Create unit and integration tests', StepType.TEST, ['implement-core'], []),
            ('Code Review', 'Review implementation for quality', StepType.REVIEW, ['write-tests'], []),
            ('Add Documentation', 'Write README and API docs', StepType.DOCUMENT, ['code-review'], []),
            ('Deploy Skill', 'Deploy the skill to production', StepType.DEPLOY, ['add-documentation'], []),
        ],
        'integration': [
            ('Research Platform', 'Research platform API and capabilities', StepType.RESEARCH, [], []),
            ('Design Integration', 'Design the integration architecture', StepType.DESIGN, ['research-platform'], []),
            ('Implement Adapter', 'Create the platform adapter', StepType.IMPLEMENT, ['design-integration'], []),
            ('Test Integration', 'Test the integration end-to-end', StepType.TEST, ['implement-adapter'], []),
            ('Deploy Integration', 'Deploy to production', StepType.DEPLOY, ['test-integration'], []),
        ],
        'fix': [
            ('Reproduce Issue', 'Reproduce the reported issue', StepType.RESEARCH, [], []),
            ('Root Cause Analysis', 'Identify the root cause', StepType.DESIGN, ['reproduce-issue'], []),
            ('Implement Fix', 'Write the fix', StepType.IMPLEMENT, ['root-cause-analysis'], []),
            ('Test Fix', 'Verify the fix resolves the issue', StepType.TEST, ['implement-fix'], []),
            ('Deploy Fix', 'Deploy the fix to production', StepType.DEPLOY, ['test-fix'], []),
        ],
        'optimization': [
            ('Profile Performance', 'Measure current performance', StepType.RESEARCH, [], []),
            ('Identify Bottlenecks', 'Find performance bottlenecks', StepType.DESIGN, ['profile-performance'], []),
            ('Implement Optimization', 'Apply optimization techniques', StepType.IMPLEMENT, ['identify-bottlenecks'], []),
            ('Validate Improvement', 'Measure performance improvement', StepType.TEST, ['implement-optimization'], []),
        ],
    }
    
    def decompose_goal(self, goal) -> Plan:
        """
        Decompose a goal into a multi-step plan.
        
        Args:
            goal: Goal object to decompose
            
        Returns:
            Plan with steps forming a DAG
        """
        import uuid
        
        plan_id = f"plan-{str(uuid.uuid4())[:8]}"
        
        # Get template for goal category
        templates = self.STEP_TEMPLATES.get(goal.category, self.STEP_TEMPLATES.get('skill', []))
        
        # Create plan
        plan = Plan(
            id=plan_id,
            goal_id=goal.id,
            title=f"Plan: {goal.title}",
            description=goal.description
        )
        
        # Create steps from template
        step_map = {}  # template_id -> step_id
        for i, (title, desc, step_type, deps, _) in enumerate(templates):
            step_id = f"{plan_id}-step{i+1}"
            
            # Map template dependency names to step_ids
            step_deps = []
            for dep_template in deps:
                if dep_template in step_map:
                    step_deps.append(step_map[dep_template])
            
            step = PlanStep(
                id=step_id,
                goal_id=goal.id,
                title=title,
                description=desc,
                step_type=step_type,
                command=self._get_command_for_step(step_type),
                parameters={},
                dependencies=step_deps
            )
            
            # If no dependencies, it's ready to start
            if not step_deps:
                step.status = StepStatus.READY
            else:
                step.status = StepStatus.BLOCKED
            
            plan.steps[step_id] = step
            step_map[title.lower().replace(' ', '-')] = step_id
        
        # Populate dependents (reverse of dependencies)
        for step in plan.steps.values():
            for dep_id in step.dependencies:
                if dep_id in plan.steps:
                    plan.steps[dep_id].dependents.append(step.id)
        
        logger.info(f"✅ Decomposed goal '{goal.title}' into {len(plan.steps)} steps")
        return plan
    
    def _get_command_for_step(self, step_type: StepType) -> str:
        """Get default command for step type"""
        commands = {
            StepType.RESEARCH: 'research',
            StepType.DESIGN: 'design',
            StepType.IMPLEMENT: 'implement',
            StepType.TEST: 'test',
            StepType.REVIEW: 'review',
            StepType.DOCUMENT: 'document',
            StepType.DEPLOY: 'deploy',
            StepType.CUSTOM: 'execute',
        }
        return commands.get(step_type, 'execute')


class PlanManager:
    """
    Manages plan storage, execution, and monitoring.
    
    Usage:
        manager = PlanManager()
        
        # Create plan
        plan = GoalDecomposer().decompose_goal(goal)
        manager.save_plan(plan)
        
        # Execute
        manager.start_plan(plan.id)
        while not plan.is_complete:
            step = plan.get_next_step()
            if step:
                manager.execute_step(plan.id, step.id)
            else:
                break
    """
    
    def __init__(self, db_path: str = 'data/plans.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            # Plans table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT,
                    title TEXT,
                    description TEXT,
                    status TEXT,
                    created_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    current_step_id TEXT,
                    completed_steps TEXT,
                    failed_steps TEXT
                )
            ''')
            
            # Steps table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS plan_steps (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT,
                    plan_id TEXT,
                    title TEXT,
                    description TEXT,
                    step_type TEXT,
                    command TEXT,
                    parameters TEXT,
                    dependencies TEXT,
                    dependents TEXT,
                    status TEXT,
                    created_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    attempts INTEGER,
                    max_attempts INTEGER,
                    last_error TEXT,
                    output TEXT,
                    artifacts TEXT
                )
            ''')
            
            conn.commit()
    
    def save_plan(self, plan: Plan) -> None:
        """Save plan and steps to database"""
        with sqlite3.connect(self.db_path) as conn:
            # Save plan
            conn.execute('''
                INSERT OR REPLACE INTO plans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plan.id,
                plan.goal_id,
                plan.title,
                plan.description,
                plan.status,
                plan.created_at.isoformat(),
                plan.started_at.isoformat() if plan.started_at else None,
                plan.completed_at.isoformat() if plan.completed_at else None,
                plan.current_step_id,
                json.dumps(plan.completed_steps),
                json.dumps(plan.failed_steps)
            ))
            
            # Save steps
            for step in plan.steps.values():
                conn.execute('''
                    INSERT OR REPLACE INTO plan_steps VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    step.id,
                    step.goal_id,
                    plan.id,
                    step.title,
                    step.description,
                    step.step_type.name,
                    step.command,
                    json.dumps(step.parameters),
                    json.dumps(step.dependencies),
                    json.dumps(step.dependents),
                    step.status.name,
                    step.created_at.isoformat(),
                    step.started_at.isoformat() if step.started_at else None,
                    step.completed_at.isoformat() if step.completed_at else None,
                    step.attempts,
                    step.max_attempts,
                    step.last_error,
                    step.output,
                    json.dumps(step.artifacts)
                ))
            
            conn.commit()
    
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Load plan from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Load plan
            row = conn.execute(
                'SELECT * FROM plans WHERE id = ?',
                [plan_id]
            ).fetchone()
            
            if not row:
                return None
            
            # Load steps
            step_rows = conn.execute(
                'SELECT * FROM plan_steps WHERE plan_id = ?',
                [plan_id]
            ).fetchall()
            
            steps = {}
            for s_row in step_rows:
                step = self._row_to_step(s_row)
                steps[step.id] = step
            
            return Plan(
                id=row['id'],
                goal_id=row['goal_id'],
                title=row['title'],
                description=row['description'],
                steps=steps,
                status=row['status'],
                created_at=datetime.fromisoformat(row['created_at']),
                started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
                completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                current_step_id=row['current_step_id'],
                completed_steps=json.loads(row['completed_steps']) if row['completed_steps'] else [],
                failed_steps=json.loads(row['failed_steps']) if row['failed_steps'] else []
            )
    
    def update_step(self, plan_id: str, step_id: str, status: StepStatus, 
                    output: Optional[str] = None, error: Optional[str] = None) -> None:
        """Update step status in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE plan_steps 
                SET status = ?, output = ?, last_error = ?, completed_at = ?
                WHERE id = ? AND plan_id = ?
            ''', (
                status.name,
                output,
                error,
                datetime.now().isoformat() if status == StepStatus.COMPLETED else None,
                step_id,
                plan_id
            ))
            conn.commit()
    
    def _row_to_step(self, row: sqlite3.Row) -> PlanStep:
        """Convert database row to PlanStep"""
        def get(col, default=None):
            try:
                return row[col]
            except (KeyError, IndexError):
                return default
        
        return PlanStep(
            id=get('id', ''),
            goal_id=get('goal_id', ''),
            title=get('title', ''),
            description=get('description', ''),
            step_type=StepType[get('step_type', 'CUSTOM')],
            command=get('command'),
            parameters=json.loads(get('parameters', '{}')) if get('parameters') else {},
            dependencies=json.loads(get('dependencies', '[]')) if get('dependencies') else [],
            dependents=json.loads(get('dependents', '[]')) if get('dependents') else [],
            status=StepStatus[get('status', 'PENDING')],
            created_at=datetime.fromisoformat(get('created_at', datetime.now().isoformat())),
            started_at=datetime.fromisoformat(get('started_at')) if get('started_at') else None,
            completed_at=datetime.fromisoformat(get('completed_at')) if get('completed_at') else None,
            attempts=get('attempts', 0) or 0,
            max_attempts=get('max_attempts', 3) or 3,
            last_error=get('last_error'),
            output=get('output'),
            artifacts=json.loads(get('artifacts', '[]')) if get('artifacts') else []
        )


# Singleton
_plan_manager_instance: Optional[PlanManager] = None


def get_plan_manager() -> PlanManager:
    """Get or create plan manager singleton"""
    global _plan_manager_instance
    if _plan_manager_instance is None:
        _plan_manager_instance = PlanManager()
    return _plan_manager_instance
