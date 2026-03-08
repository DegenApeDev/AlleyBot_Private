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

from src.agentic.action_logger import get_action_logger

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

    MAX_REVISION_CHAIN_DEPTH = 3
    
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

            conn.execute('''
                CREATE TABLE IF NOT EXISTS action_family_state (
                    action_family TEXT PRIMARY KEY,
                    trust_bucket TEXT,
                    degradation_score REAL,
                    recovery_score REAL,
                    cooldown_until TEXT,
                    last_plan_id TEXT,
                    last_updated_at TEXT,
                    metadata TEXT
                )
            ''')
            
            conn.commit()

    def update_action_family_state(
        self,
        action_family: str,
        trust_bucket: str,
        degradation_score: float,
        recovery_score: float,
        cooldown_until: Optional[datetime],
        last_plan_id: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist trust state for an action family so learning survives beyond active plans."""
        normalized_family = str(action_family or '').strip().lower()
        if not normalized_family:
            return

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO action_family_state VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                normalized_family,
                trust_bucket,
                float(degradation_score or 0.0),
                float(recovery_score or 0.0),
                cooldown_until.isoformat() if cooldown_until else None,
                last_plan_id,
                datetime.now().isoformat(),
                json.dumps(metadata or {}),
            ))
            conn.commit()

    def get_action_family_states(self) -> Dict[str, Dict[str, Any]]:
        """Load persisted trust state for action families."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('SELECT * FROM action_family_state').fetchall()

        states: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            states[row['action_family']] = {
                'action_family': row['action_family'],
                'trust_bucket': row['trust_bucket'] or 'healthy',
                'degradation_score': float(row['degradation_score'] or 0.0),
                'recovery_score': float(row['recovery_score'] or 0.0),
                'cooldown_until': row['cooldown_until'],
                'last_plan_id': row['last_plan_id'],
                'last_updated_at': row['last_updated_at'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else {},
            }
        return states

    def _derive_trust_bucket(
        self,
        degradation_score: float,
        recovery_score: float,
        cooldown_until: Optional[datetime],
    ) -> str:
        """Map degradation and recovery signals into a bounded trust bucket."""
        now = datetime.now()
        cooling_down = bool(cooldown_until and cooldown_until > now)
        if degradation_score >= 0.75 and cooling_down:
            return 'degraded'
        if cooling_down:
            return 'cooling_down'
        if recovery_score >= 0.5:
            return 'recovering'
        return 'healthy'

    def create_routed_plan(
        self,
        goal_id: str,
        title: str,
        description: str,
        plan_steps: List[Dict[str, Any]],
    ) -> Plan:
        """Create and persist a lightweight routed plan from AGI-orchestrator plan steps."""
        import uuid

        plan_id = f"routed-plan-{str(uuid.uuid4())[:8]}"
        normalized_goal_id = goal_id or plan_id
        plan = Plan(
            id=plan_id,
            goal_id=normalized_goal_id,
            title=title,
            description=description,
            status='active',
            started_at=datetime.now(),
        )

        previous_step_id = None
        total_steps = len(plan_steps or [])
        for index, raw_step in enumerate(plan_steps or [], start=1):
            step_id = f"{plan_id}-step{index}"
            details = raw_step.get('details') if isinstance(raw_step, dict) else {}
            if not isinstance(details, dict):
                details = {'raw_details': str(details)}

            action_name = raw_step.get('action', f'step_{index}') if isinstance(raw_step, dict) else f'step_{index}'
            title_text = raw_step.get('title') if isinstance(raw_step, dict) else None
            description_text = raw_step.get('description') if isinstance(raw_step, dict) else None

            step = PlanStep(
                id=step_id,
                goal_id=normalized_goal_id,
                title=title_text or f"Step {index}: {action_name}",
                description=description_text or f"Execute routed plan step '{action_name}' ({index}/{total_steps})",
                step_type=StepType.CUSTOM,
                command=action_name,
                parameters=details,
                dependencies=[previous_step_id] if previous_step_id else [],
                status=StepStatus.READY if previous_step_id is None else StepStatus.BLOCKED,
            )

            if previous_step_id and previous_step_id in plan.steps:
                plan.steps[previous_step_id].dependents.append(step_id)

            plan.steps[step_id] = step
            previous_step_id = step_id

        self.save_plan(plan)
        return plan

    def create_revised_plan(
        self,
        plan_id: str,
        failed_step_id: str,
        outcome: Dict[str, Any],
    ) -> Optional[Plan]:
        """Create a lightweight revised plan when a routed step requires replanning."""
        plan = self.get_plan(plan_id)
        if not plan or failed_step_id not in plan.steps:
            return None

        failed_step = plan.steps[failed_step_id]
        lineage = self._build_revision_lineage(plan, failed_step)
        revision_depth = len(lineage)
        mismatch_score = (
            outcome.get('mismatch_score')
            or ((outcome.get('outcome_record') or {}).get('mismatch_score'))
            or ((outcome.get('prediction_evaluation') or {}).get('mismatch_score'))
            or 0.0
        )
        failure_reason = outcome.get('error') or outcome.get('reason') or failed_step.last_error or 'execution mismatch'
        prediction_evaluation = (outcome.get('prediction_evaluation') or {})
        if not prediction_evaluation:
            prediction_evaluation = (outcome.get('outcome_record') or {}).get('prediction_evaluation', {}) or {}
        ranking_evidence = (outcome.get('ranking_evidence') or {})
        if not ranking_evidence:
            ranking_evidence = (outcome.get('outcome_record') or {}).get('ranking_evidence', {}) or {}
        dispatch_path = str(
            outcome.get('dispatch_path')
            or (outcome.get('outcome_record') or {}).get('dispatch_path')
            or 'unknown'
        ).lower()
        legacy_fallback_used = bool(
            outcome.get('legacy_fallback_used')
            or (outcome.get('outcome_record') or {}).get('legacy_fallback_used')
        )
        fallback_details = (outcome.get('fallback_details') or {})
        if not fallback_details:
            fallback_details = (outcome.get('outcome_record') or {}).get('fallback_details', {}) or {}

        observed_risk = str(prediction_evaluation.get('observed_risk', 'medium')).lower()
        risk_alignment = str(prediction_evaluation.get('risk_alignment', 'matched')).lower()
        calibration = str(prediction_evaluation.get('confidence_calibration', 'well_calibrated')).lower()
        value_alignment = str(prediction_evaluation.get('value_alignment', 'matched')).lower()
        ranked_predicted_value = str(ranking_evidence.get('predicted_value', 'medium') or 'medium').lower()
        ranked_adjustment = float(ranking_evidence.get('memory_shaped_adjustment', 0.0) or 0.0)
        ranked_used_memory_recall = bool(
            (ranking_evidence.get('memory_relevance_count', 0) or 0) > 0
            or ranking_evidence.get('entity_context_found')
        )
        ranked_negative_memory_count = int(ranking_evidence.get('negative_memory_count', 0) or 0)
        action_type = str(
            outcome.get('action_type')
            or (outcome.get('outcome_record') or {}).get('action_type')
            or failed_step.command
            or ''
        ).lower()
        plugin_name = str(
            outcome.get('plugin')
            or (outcome.get('outcome_record') or {}).get('plugin')
            or ''
        ).lower()
        performance_summary = {}
        action_performance = None
        try:
            performance_summary = get_action_logger().get_action_performance_summary(hours=72, limit=50)
        except Exception:
            performance_summary = {}

        if action_type:
            direct_key = action_type
            routed_key = f"{plugin_name}:{action_type}" if plugin_name else action_type
            action_performance = performance_summary.get(direct_key) or performance_summary.get(routed_key)

        recent_success_rate = float((action_performance or {}).get('success_rate', 0.0) or 0.0)
        recent_avg_mismatch = float((action_performance or {}).get('avg_mismatch_score', 0.0) or 0.0)
        recent_high_mismatch_rate = float((action_performance or {}).get('high_mismatch_rate', 0.0) or 0.0)
        recent_calibration_bias = str((action_performance or {}).get('calibration_bias', 'balanced')).lower()
        recent_total = int((action_performance or {}).get('total', 0) or 0)

        outcome_text = f"{failure_reason} {failed_step.title} {failed_step.description} {failed_step.command}".lower()
        next_action = failed_step.command or 'retry_with_adjustment'
        next_details = {
            **(failed_step.parameters or {}),
            'revised_from_plan_id': plan.id,
            'revised_from_step_id': failed_step.id,
            'retry_mode': 'bounded_adjustment',
            'prior_failure_reason': str(failure_reason),
        }
        if action_performance:
            next_details['recent_action_performance'] = {
                'success_rate': recent_success_rate,
                'avg_mismatch_score': recent_avg_mismatch,
                'high_mismatch_rate': recent_high_mismatch_rate,
                'calibration_bias': recent_calibration_bias,
                'total': recent_total,
            }
        if ranking_evidence:
            next_details['ranking_evidence'] = ranking_evidence
        if legacy_fallback_used or dispatch_path != 'golden_path':
            next_details['dispatch_metadata'] = {
                'dispatch_path': dispatch_path,
                'legacy_fallback_used': legacy_fallback_used,
                'fallback_details': fallback_details,
            }
        next_details['revision_depth'] = revision_depth
        next_details['revision_lineage'] = lineage
        next_title = f"Adjusted retry for {failed_step.title}"
        next_description = 'Retry with narrower scope or safer constraints after reassessment'

        should_abandon = (
            revision_depth >= self.MAX_REVISION_CHAIN_DEPTH
            and recent_total >= 3
            and recent_success_rate < 0.35
            and max(mismatch_score, recent_avg_mismatch) >= 0.65
        )
        should_escalate = (
            not should_abandon
            and revision_depth >= 2
            and (
                max(mismatch_score, recent_avg_mismatch) >= 0.6
                or recent_high_mismatch_rate >= 0.5
            )
        )

        if should_abandon:
            revised_steps = [
                {
                    'action': 'reassess_strategy',
                    'title': 'Reassess exhausted strategy',
                    'description': f"Review repeated failures for '{failed_step.title}' and terminate unsafe retry loops",
                    'details': {
                        'original_plan_id': plan.id,
                        'failed_step_id': failed_step.id,
                        'failure_reason': str(failure_reason),
                        'mismatch_score': float(mismatch_score or 0.0),
                        'revision_depth': revision_depth,
                        'revision_lineage': lineage,
                        'escalation_mode': 'abandon',
                    },
                },
                {
                    'action': 'analyze_performance',
                    'title': 'Document degraded action family',
                    'description': 'Capture failure evidence and mark this strategy as degraded instead of retrying it again',
                    'details': {
                        'time_window': '7d',
                        'revised_from_plan_id': plan.id,
                        'revised_from_step_id': failed_step.id,
                        'replan_basis': 'strategy_abandoned',
                        'escalation_mode': 'abandon',
                        'prior_failure_reason': str(failure_reason),
                        'revision_depth': revision_depth,
                        'revision_lineage': lineage,
                        'recent_action_performance': next_details.get('recent_action_performance'),
                    },
                },
            ]

            revised_plan = self.create_routed_plan(
                goal_id=plan.goal_id,
                title=f"Abandoned: {plan.title}",
                description=f"Escalated abandonment of {plan.id} after repeated failed revisions for step '{failed_step.title}'",
                plan_steps=revised_steps,
            )
            revised_plan.status = 'escalated'
            self.save_plan(revised_plan)
            return revised_plan

        if should_escalate:
            revised_steps = [
                {
                    'action': 'reassess_strategy',
                    'title': 'Escalate to safer strategy',
                    'description': f"Repeated mismatch for '{failed_step.title}' requires a safer alternate path",
                    'details': {
                        'original_plan_id': plan.id,
                        'failed_step_id': failed_step.id,
                        'failure_reason': str(failure_reason),
                        'mismatch_score': float(mismatch_score or 0.0),
                        'revision_depth': revision_depth,
                        'revision_lineage': lineage,
                        'escalation_mode': 'safer_alternate',
                    },
                },
                {
                    'action': 'analyze_performance',
                    'title': 'Analyze before alternate path',
                    'description': 'Pause direct retries and ground the next move in safer evidence before continuing',
                    'details': {
                        'time_window': '7d',
                        'revised_from_plan_id': plan.id,
                        'revised_from_step_id': failed_step.id,
                        'replan_basis': 'safer_alternate_path',
                        'escalation_mode': 'safer_alternate',
                        'prior_failure_reason': str(failure_reason),
                        'revision_depth': revision_depth,
                        'revision_lineage': lineage,
                        'recent_action_performance': next_details.get('recent_action_performance'),
                    },
                },
                {
                    'action': 'moltx_engage' if plugin_name != 'clawbr' else 'clawbr_engage',
                    'title': 'Gather fresh external signal',
                    'description': 'Use a bounded lower-risk engagement pass before selecting another outward action',
                    'details': {
                        'count': failed_step.parameters.get('count', 3),
                        'revised_from_plan_id': plan.id,
                        'revised_from_step_id': failed_step.id,
                        'replan_basis': 'safer_signal_reentry',
                        'escalation_mode': 'safer_alternate',
                        'prior_failure_reason': str(failure_reason),
                        'revision_depth': revision_depth,
                        'revision_lineage': lineage,
                        'recent_action_performance': next_details.get('recent_action_performance'),
                    },
                },
            ]

            revised_plan = self.create_routed_plan(
                goal_id=plan.goal_id,
                title=f"Escalated: {plan.title}",
                description=f"Safer alternate revision of {plan.id} after repeated mismatch on step '{failed_step.title}'",
                plan_steps=revised_steps,
            )
            revised_plan.status = 'active'
            self.save_plan(revised_plan)
            return revised_plan

        if (
            recent_total >= 3 and recent_success_rate < 0.35 and recent_high_mismatch_rate >= 0.4
        ):
            next_action = 'analyze_performance'
            next_title = 'Pause and analyze weak action family'
            next_description = 'Recent history shows this action family is underperforming, so gather evidence before retrying'
            next_details = {
                'time_window': '7d',
                'revised_from_plan_id': plan.id,
                'revised_from_step_id': failed_step.id,
                'replan_basis': 'historically_weak_action_family',
                'prior_failure_reason': str(failure_reason),
                'recent_action_performance': {
                    'success_rate': recent_success_rate,
                    'avg_mismatch_score': recent_avg_mismatch,
                    'high_mismatch_rate': recent_high_mismatch_rate,
                    'calibration_bias': recent_calibration_bias,
                    'total': recent_total,
                },
            }
        elif observed_risk in {'high', 'critical'} or risk_alignment == 'underestimated_risk':
            next_action = 'analyze_performance'
            next_title = 'Analyze risk before retry'
            next_description = 'Inspect recent performance and risk signals before taking another action'
            next_details = {
                'time_window': '7d',
                'revised_from_plan_id': plan.id,
                'revised_from_step_id': failed_step.id,
                'replan_basis': 'risk_mitigation',
                'prior_failure_reason': str(failure_reason),
                'recent_action_performance': next_details.get('recent_action_performance'),
            }
        elif (
            calibration == 'overconfident'
            or (recent_calibration_bias == 'overconfident' and recent_total >= 3)
        ) and max(mismatch_score, recent_avg_mismatch) >= 0.6:
            next_action = 'analyze_performance'
            next_title = 'Recalibrate before retry'
            next_description = 'Reduce overconfidence by gathering fresh performance evidence before the next move'
            next_details = {
                'time_window': '7d',
                'revised_from_plan_id': plan.id,
                'revised_from_step_id': failed_step.id,
                'replan_basis': 'confidence_recalibration',
                'prior_failure_reason': str(failure_reason),
                'recent_action_performance': next_details.get('recent_action_performance'),
            }
        elif legacy_fallback_used and dispatch_path != 'golden_path':
            next_action = 'analyze_performance'
            next_title = 'Reassess action that left Golden Path'
            next_description = 'This action required legacy fallback execution, so pause and gather evidence before retrying it directly'
            next_details = {
                'time_window': '7d',
                'revised_from_plan_id': plan.id,
                'revised_from_step_id': failed_step.id,
                'replan_basis': 'golden_path_fallback',
                'prior_failure_reason': str(failure_reason),
                'recent_action_performance': next_details.get('recent_action_performance'),
                'dispatch_metadata': {
                    'dispatch_path': dispatch_path,
                    'legacy_fallback_used': legacy_fallback_used,
                    'fallback_details': fallback_details,
                },
            }
        elif ranked_negative_memory_count >= 1 and ranked_used_memory_recall:
            next_action = 'analyze_performance'
            next_title = 'Reassess recalled negative pattern'
            next_description = 'Recent recall surfaced negative prior evidence, so pause and ground the next move before retrying'
            next_details = {
                'time_window': '7d',
                'revised_from_plan_id': plan.id,
                'revised_from_step_id': failed_step.id,
                'replan_basis': 'negative_memory_recall',
                'prior_failure_reason': str(failure_reason),
                'recent_action_performance': next_details.get('recent_action_performance'),
                'ranking_evidence': ranking_evidence,
            }
        elif (
            action_type in {'reply', 'moltx_reply'}
            or any(keyword in outcome_text for keyword in ['reply', 'comment', 'response', 'mention'])
        ) and failed_step.parameters.get('target_id'):
            next_action = 'moltx_reply'
            next_title = 'Retry as direct reply'
            next_description = 'Respond directly with narrower scope and contextual targeting'
            next_details = {
                'target_id': failed_step.parameters.get('target_id'),
                'content': failed_step.parameters.get('content') or failed_step.parameters.get('message') or 'Following up with a more focused response.',
                'revised_from_plan_id': plan.id,
                'revised_from_step_id': failed_step.id,
                'replan_basis': 'reply_retry',
                'prior_failure_reason': str(failure_reason),
                'recent_action_performance': next_details.get('recent_action_performance'),
            }
        elif (
            plugin_name == 'analytics'
            or action_type in {'analyze_performance', 'report'}
            or value_alignment == 'underestimated_value'
            or ranked_predicted_value == 'high'
            or (recent_total >= 3 and recent_success_rate < 0.45 and action_type in {'moltx_intelligent_post', 'post'})
        ):
            next_action = 'moltx_engage'
            next_title = 'Gather stronger live signal'
            next_description = 'Run a bounded engagement cycle to improve context before selecting the next outward action'
            next_details = {
                'count': failed_step.parameters.get('count', 3),
                'revised_from_plan_id': plan.id,
                'revised_from_step_id': failed_step.id,
                'replan_basis': 'signal_gathering',
                'prior_failure_reason': str(failure_reason),
                'recent_action_performance': next_details.get('recent_action_performance'),
                'ranking_evidence': ranking_evidence,
                'ranking_bias': 'high_predicted_value_recovery' if ranked_predicted_value == 'high' else 'standard',
            }
        elif ranked_adjustment <= -0.04 and max(mismatch_score, recent_avg_mismatch) >= 0.5:
            next_action = 'analyze_performance'
            next_title = 'Recalibrate weak ranked action'
            next_description = 'Ranking evidence already cooled this action, so gather safer evidence before trying again'
            next_details = {
                'time_window': '7d',
                'revised_from_plan_id': plan.id,
                'revised_from_step_id': failed_step.id,
                'replan_basis': 'ranking_recalibration',
                'prior_failure_reason': str(failure_reason),
                'recent_action_performance': next_details.get('recent_action_performance'),
                'ranking_evidence': ranking_evidence,
            }
        elif action_type in {'moltx_intelligent_post', 'post', 'execute_post'} or any(keyword in outcome_text for keyword in ['timeout', 'no content', 'content', 'post', 'publish', 'creative']):
            next_action = 'moltx_intelligent_post'
            next_title = 'Retry content post with tighter topic'
            next_description = 'Generate a narrower, more grounded post topic before retrying publication'
            next_details = {
                'content': failed_step.parameters.get('topic') or failed_step.parameters.get('content') or failed_step.description,
                'revised_from_plan_id': plan.id,
                'revised_from_step_id': failed_step.id,
                'replan_basis': 'content_retry',
                'prior_failure_reason': str(failure_reason),
                'recent_action_performance': next_details.get('recent_action_performance'),
            }
        elif action_type in {'moltx_engage', 'engage', 'clawbr_engage'} or any(keyword in outcome_text for keyword in ['engage', 'feed', 'signal', 'discovery', 'browse']):
            next_action = 'clawbr_engage' if plugin_name == 'clawbr' or action_type == 'clawbr_engage' else 'moltx_engage'
            next_title = 'Gather fresh signal before retry'
            next_description = 'Run a bounded engagement cycle to gather better context before the next move'
            next_details = {
                'count': failed_step.parameters.get('count', 3),
                'revised_from_plan_id': plan.id,
                'revised_from_step_id': failed_step.id,
                'replan_basis': 'engagement_retry',
                'prior_failure_reason': str(failure_reason),
                'recent_action_performance': next_details.get('recent_action_performance'),
            }

        revised_steps = [
            {
                'action': 'reassess_strategy',
                'title': 'Reassess strategy',
                'description': f"Review failed/high-mismatch step '{failed_step.title}' and choose a safer next move",
                'details': {
                    'original_plan_id': plan.id,
                    'failed_step_id': failed_step.id,
                    'failure_reason': str(failure_reason),
                    'mismatch_score': float(mismatch_score or 0.0),
                },
            },
            {
                'action': next_action,
                'title': next_title,
                'description': next_description,
                'details': next_details,
            },
        ]

        revised_plan = self.create_routed_plan(
            goal_id=plan.goal_id,
            title=f"Revised: {plan.title}",
            description=f"Revision of {plan.id} after step '{failed_step.title}' required replanning",
            plan_steps=revised_steps,
        )
        revised_plan.status = 'active'
        self.save_plan(revised_plan)
        return revised_plan

    def _build_revision_lineage(self, plan: Plan, failed_step: PlanStep) -> List[str]:
        """Build revision lineage by following revised_from_plan_id metadata across plan chains."""
        lineage = [plan.id]
        current_plan_id = (failed_step.parameters or {}).get('revised_from_plan_id')
        visited = {plan.id}

        while current_plan_id and current_plan_id not in visited:
            visited.add(current_plan_id)
            lineage.append(current_plan_id)
            current_plan = self.get_plan(current_plan_id)
            if not current_plan:
                break
            current_step_id = current_plan.current_step_id
            current_step = current_plan.steps.get(current_step_id) if current_step_id else None
            current_plan_id = (current_step.parameters or {}).get('revised_from_plan_id') if current_step else None

        return lineage
    
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

    def get_recent_plan_summaries(self, limit: int = 5, statuses: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return recent plan summaries for decision-layer continuity and prioritization."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = 'SELECT id FROM plans'
            params: List[Any] = []
            if statuses:
                placeholders = ', '.join(['?'] * len(statuses))
                query += f' WHERE status IN ({placeholders})'
                params.extend(statuses)
            query += ' ORDER BY COALESCE(started_at, created_at) DESC LIMIT ?'
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

        summaries: List[Dict[str, Any]] = []
        for row in rows:
            plan = self.get_plan(row['id'])
            if not plan:
                continue

            current_step = plan.steps.get(plan.current_step_id) if plan.current_step_id else None
            next_step = plan.get_next_step()
            summaries.append({
                'plan_id': plan.id,
                'goal_id': plan.goal_id,
                'title': plan.title,
                'description': plan.description,
                'status': plan.status,
                'progress_percent': round(plan.progress_percent, 2),
                'current_step_id': current_step.id if current_step else None,
                'current_step_title': current_step.title if current_step else None,
                'current_step_command': current_step.command if current_step else None,
                'next_step_id': next_step.id if next_step else None,
                'next_step_title': next_step.title if next_step else None,
                'next_step_command': next_step.command if next_step else None,
                'failed_steps': list(plan.failed_steps),
                'completed_steps': list(plan.completed_steps),
                'step_count': len(plan.steps),
                'revision_depth': len(self._build_revision_lineage(plan, current_step or next_step)) if (current_step or next_step) else 1,
            })

        return summaries

    def get_decision_plan_summary(self) -> Dict[str, Any]:
        """Return a compact active/revised plan summary for autonomous decision selection."""
        active_plans = self.get_recent_plan_summaries(limit=3, statuses=['active', 'replan_required', 'escalated'])
        degraded_actions: List[Dict[str, Any]] = []
        now = datetime.now()
        performance_summary = {}
        try:
            performance_summary = get_action_logger().get_action_performance_summary(hours=72, limit=50)
        except Exception:
            performance_summary = {}
        for plan in active_plans:
            if plan.get('status') != 'escalated':
                continue
            degraded_command = plan.get('current_step_command') or plan.get('next_step_command')
            if not degraded_command:
                continue
            created_at_raw = plan.get('created_at')
            age_hours = 0.0
            if created_at_raw:
                try:
                    created_at = datetime.fromisoformat(created_at_raw)
                    age_hours = max((now - created_at).total_seconds() / 3600.0, 0.0)
                except Exception:
                    age_hours = 0.0
            cooldown_hours = 24.0
            remaining_hours = max(cooldown_hours - age_hours, 0.0)
            decay_factor = round(min(remaining_hours / cooldown_hours, 1.0), 3)
            performance = performance_summary.get(degraded_command) or performance_summary.get(f"moltx:{degraded_command}") or performance_summary.get(f"clawbr:{degraded_command}")
            recovered = False
            recovery_score = 0.0
            degradation_score = decay_factor
            if performance:
                success_rate = float(performance.get('success_rate', 0.0) or 0.0)
                avg_mismatch = float(performance.get('avg_mismatch_score', 0.0) or 0.0)
                high_mismatch_rate = float(performance.get('high_mismatch_rate', 0.0) or 0.0)
                total = int(performance.get('total', 0) or 0)
                if total >= 3 and success_rate >= 0.6 and avg_mismatch <= 0.35 and high_mismatch_rate <= 0.34:
                    recovered = True
                    recovery_score = round(min((success_rate - avg_mismatch), 1.0), 3)
                    decay_factor = round(max(decay_factor * 0.25, 0.0), 3)
                    degradation_score = decay_factor
            cooldown_until = now + timedelta(hours=remaining_hours) if remaining_hours > 0 else None
            trust_bucket = self._derive_trust_bucket(degradation_score, recovery_score, cooldown_until)
            self.update_action_family_state(
                action_family=degraded_command,
                trust_bucket=trust_bucket,
                degradation_score=degradation_score,
                recovery_score=recovery_score,
                cooldown_until=cooldown_until,
                last_plan_id=plan.get('plan_id'),
                metadata={
                    'revision_depth': plan.get('revision_depth', 1),
                    'status': plan.get('status'),
                    'age_hours': round(age_hours, 2),
                },
            )
            degraded_actions.append({
                'action_family': degraded_command,
                'plan_id': plan.get('plan_id'),
                'revision_depth': plan.get('revision_depth', 1),
                'status': plan.get('status'),
                'age_hours': round(age_hours, 2),
                'cooldown_hours': cooldown_hours,
                'cooldown_remaining_hours': round(remaining_hours, 2),
                'decay_factor': decay_factor,
                'is_cooling_down': remaining_hours > 0,
                'trust_bucket': trust_bucket,
                'degradation_score': degradation_score,
                'recovered': recovered,
                'recovery_score': recovery_score,
                'recent_performance': {
                    'success_rate': float((performance or {}).get('success_rate', 0.0) or 0.0),
                    'avg_mismatch_score': float((performance or {}).get('avg_mismatch_score', 0.0) or 0.0),
                    'high_mismatch_rate': float((performance or {}).get('high_mismatch_rate', 0.0) or 0.0),
                    'total': int((performance or {}).get('total', 0) or 0),
                } if performance else None,
            })
        persisted_states = self.get_action_family_states()
        for family, state in persisted_states.items():
            if any(item.get('action_family') == family for item in degraded_actions):
                continue
            cooldown_until_raw = state.get('cooldown_until')
            cooldown_remaining_hours = 0.0
            is_cooling_down = False
            if cooldown_until_raw:
                try:
                    cooldown_until = datetime.fromisoformat(cooldown_until_raw)
                    cooldown_remaining_hours = max((cooldown_until - now).total_seconds() / 3600.0, 0.0)
                    is_cooling_down = cooldown_remaining_hours > 0
                except Exception:
                    cooldown_remaining_hours = 0.0
                    is_cooling_down = False
            degraded_actions.append({
                'action_family': family,
                'plan_id': state.get('last_plan_id'),
                'revision_depth': (state.get('metadata') or {}).get('revision_depth', 1),
                'status': (state.get('metadata') or {}).get('status', 'persisted'),
                'age_hours': None,
                'cooldown_hours': None,
                'cooldown_remaining_hours': round(cooldown_remaining_hours, 2),
                'decay_factor': float(state.get('degradation_score', 0.0) or 0.0),
                'is_cooling_down': is_cooling_down,
                'trust_bucket': state.get('trust_bucket', 'healthy'),
                'degradation_score': float(state.get('degradation_score', 0.0) or 0.0),
                'recovered': state.get('trust_bucket') == 'recovering',
                'recovery_score': float(state.get('recovery_score', 0.0) or 0.0),
                'recent_performance': (state.get('metadata') or {}).get('recent_performance'),
                'persisted_state': True,
            })

        return {
            'active_plan_count': len(active_plans),
            'has_replan_required': any(plan.get('status') == 'replan_required' for plan in active_plans),
            'has_escalated_plan': any(plan.get('status') == 'escalated' for plan in active_plans),
            'degraded_action_families': degraded_actions,
            'action_family_trust_state': persisted_states,
            'plans': active_plans,
            'top_plan': active_plans[0] if active_plans else None,
        }

    def get_top_resumable_plan(self) -> Optional[Dict[str, Any]]:
        """Return the highest-priority resumable plan for AGI cycle continuation."""
        plans = self.get_recent_plan_summaries(limit=5, statuses=['replan_required', 'active', 'escalated'])
        if not plans:
            return None

        plans.sort(
            key=lambda plan: (
                0 if plan.get('status') == 'replan_required' else 1,
                1 if plan.get('status') == 'escalated' else 0,
                -(plan.get('progress_percent') or 0.0),
            )
        )
        top_plan = plans[0]
        if not top_plan.get('next_step_id'):
            return None
        return top_plan
    
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

    def mark_step_active(self, plan_id: str, step_id: str) -> Optional[Plan]:
        """Mark a routed plan step active and persist current step tracking."""
        plan = self.get_plan(plan_id)
        if not plan or step_id not in plan.steps:
            return None

        step = plan.steps[step_id]
        step.status = StepStatus.ACTIVE
        step.started_at = datetime.now()
        step.attempts += 1
        plan.current_step_id = step_id
        plan.started_at = plan.started_at or datetime.now()
        self.save_plan(plan)
        return plan

    def complete_step_from_outcome(
        self,
        plan_id: str,
        step_id: str,
        outcome: Dict[str, Any],
    ) -> Optional[Plan]:
        """Update plan/step state from a routed execution outcome."""
        plan = self.get_plan(plan_id)
        if not plan or step_id not in plan.steps:
            return None

        step = plan.steps[step_id]
        success = bool(outcome.get('success', False) or outcome.get('result') == 'success')
        mismatch_score = (
            outcome.get('mismatch_score')
            or ((outcome.get('outcome_record') or {}).get('mismatch_score'))
            or ((outcome.get('prediction_evaluation') or {}).get('mismatch_score'))
            or 0.0
        )

        step.output = str(outcome)[:500]
        step.completed_at = datetime.now()

        if success:
            plan.update_step_status(step_id, StepStatus.COMPLETED)
        else:
            error_text = outcome.get('error') or outcome.get('reason') or outcome.get('result_summary') or 'step failed'
            plan.update_step_status(step_id, StepStatus.FAILED, error=str(error_text))

        if plan.is_complete:
            plan.status = 'completed'
            plan.completed_at = datetime.now()
        elif not success:
            plan.status = 'replan_required' if float(mismatch_score or 0.0) >= 0.5 else 'failed'
        elif float(mismatch_score or 0.0) >= 0.65:
            plan.status = 'replan_required'
        else:
            plan.status = 'active'

        self.save_plan(plan)
        return plan
    
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
