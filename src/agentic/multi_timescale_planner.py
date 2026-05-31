"""
Multi-Timescale Planner for AlleyBot AGI
Plans and coordinates actions across different time horizons
Bridges long-term strategic goals with immediate tactical actions
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class Timescale(Enum):
    """Time horizons for planning"""
    STRATEGIC = "strategic"  # Months to years
    TACTICAL = "tactical"  # Days to weeks
    OPERATIONAL = "operational"  # Hours to days
    IMMEDIATE = "immediate"  # Minutes to hours


@dataclass
class Action:
    """An action to be taken"""
    id: str
    description: str
    goal_id: str  # Associated goal
    timescale: Timescale
    priority: int  # 1-10
    estimated_duration: timedelta
    dependencies: List[str] = field(default_factory=list)
    resources_needed: List[str] = field(default_factory=list)
    expected_outcome: str = ""
    scheduled_time: Optional[datetime] = None


@dataclass
class Plan:
    """A plan at a specific timescale"""
    id: str
    goal_id: str
    timescale: Timescale
    actions: List[Action] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    horizon: timedelta = field(default_factory=lambda: timedelta(days=1))
    status: str = "active"  # active, completed, abandoned


class MultiTimescalePlanner:
    """
    Multi-Timescale Planning System
    
    Coordinates planning across different time horizons:
    - Strategic (months-years): High-level direction
    - Tactical (days-weeks): Medium-term objectives
    - Operational (hours-days): Day-to-day execution
    - Immediate (minutes-hours): Real-time actions
    
    Ensures:
    - Long-term goals drive short-term actions
    - Short-term actions align with long-term strategy
    - Adaptive replanning when context changes
    - Resource allocation across timescales
    """
    
    def __init__(self, goal_hierarchy=None):
        """
        Initialize multi-timescale planner
        
        Args:
            goal_hierarchy: Hierarchical goal system
        """
        self.goal_hierarchy = goal_hierarchy
        
        # Plans at different timescales
        self.strategic_plans: Dict[str, Plan] = {}
        self.tactical_plans: Dict[str, Plan] = {}
        self.operational_plans: Dict[str, Plan] = {}
        self.immediate_actions: List[Action] = []
        
        # Planning horizons
        self.horizons = {
            Timescale.STRATEGIC: timedelta(days=90),  # 3 months
            Timescale.TACTICAL: timedelta(days=7),  # 1 week
            Timescale.OPERATIONAL: timedelta(days=1),  # 1 day
            Timescale.IMMEDIATE: timedelta(hours=1)  # 1 hour
        }
        
        logger.info("✅ Multi-Timescale Planner initialized")
    
    def create_strategic_plan(self, goal_id: str) -> Plan:
        """
        Create strategic plan for a goal (months-years)
        
        Args:
            goal_id: Goal to plan for
            
        Returns:
            Strategic plan
        """
        if not self.goal_hierarchy:
            logger.warning("⚠️ No goal hierarchy available")
            return None
        
        goal = self.goal_hierarchy.get_goal(goal_id)
        if not goal:
            logger.warning(f"⚠️ Goal {goal_id} not found")
            return None
        
        logger.info(f"📋 Creating strategic plan for: {goal.title}")
        
        # Create plan
        plan = Plan(
            id=f"strategic_{goal_id}",
            goal_id=goal_id,
            timescale=Timescale.STRATEGIC,
            horizon=self.horizons[Timescale.STRATEGIC]
        )
        
        # Break goal into major milestones
        milestones = self._identify_milestones(goal)
        
        # Create actions for each milestone
        for i, milestone in enumerate(milestones):
            action = Action(
                id=f"strategic_action_{goal_id}_{i}",
                description=milestone,
                goal_id=goal_id,
                timescale=Timescale.STRATEGIC,
                priority=10 - i,  # Earlier milestones higher priority
                estimated_duration=timedelta(days=30),
                expected_outcome=f"Complete milestone: {milestone}"
            )
            plan.actions.append(action)
        
        self.strategic_plans[plan.id] = plan
        
        logger.info(f"✅ Created strategic plan with {len(plan.actions)} milestones")
        
        return plan
    
    def create_tactical_plan(self, strategic_action: Action) -> Plan:
        """
        Create tactical plan from strategic action (days-weeks)
        
        Args:
            strategic_action: Strategic action to decompose
            
        Returns:
            Tactical plan
        """
        logger.info(f"📋 Creating tactical plan for: {strategic_action.description}")
        
        plan = Plan(
            id=f"tactical_{strategic_action.id}",
            goal_id=strategic_action.goal_id,
            timescale=Timescale.TACTICAL,
            horizon=self.horizons[Timescale.TACTICAL]
        )
        
        # Decompose strategic action into weekly objectives
        objectives = self._decompose_to_objectives(strategic_action)
        
        for i, objective in enumerate(objectives):
            action = Action(
                id=f"tactical_action_{strategic_action.id}_{i}",
                description=objective,
                goal_id=strategic_action.goal_id,
                timescale=Timescale.TACTICAL,
                priority=8 - i,
                estimated_duration=timedelta(days=2),
                expected_outcome=f"Complete objective: {objective}"
            )
            plan.actions.append(action)
        
        self.tactical_plans[plan.id] = plan
        
        logger.info(f"✅ Created tactical plan with {len(plan.actions)} objectives")
        
        return plan
    
    def create_operational_plan(self, tactical_action: Action) -> Plan:
        """
        Create operational plan from tactical action (hours-days)
        
        Args:
            tactical_action: Tactical action to decompose
            
        Returns:
            Operational plan
        """
        logger.info(f"📋 Creating operational plan for: {tactical_action.description}")
        
        plan = Plan(
            id=f"operational_{tactical_action.id}",
            goal_id=tactical_action.goal_id,
            timescale=Timescale.OPERATIONAL,
            horizon=self.horizons[Timescale.OPERATIONAL]
        )
        
        # Decompose tactical action into daily tasks
        tasks = self._decompose_to_tasks(tactical_action)
        
        for i, task in enumerate(tasks):
            action = Action(
                id=f"operational_action_{tactical_action.id}_{i}",
                description=task,
                goal_id=tactical_action.goal_id,
                timescale=Timescale.OPERATIONAL,
                priority=6 - i,
                estimated_duration=timedelta(hours=4),
                expected_outcome=f"Complete task: {task}"
            )
            plan.actions.append(action)
        
        self.operational_plans[plan.id] = plan
        
        logger.info(f"✅ Created operational plan with {len(plan.actions)} tasks")
        
        return plan
    
    def schedule_immediate_actions(self, operational_action: Action) -> List[Action]:
        """
        Schedule immediate actions from operational action (minutes-hours)
        
        Args:
            operational_action: Operational action to execute
            
        Returns:
            List of immediate actions
        """
        logger.info(f"⚡ Scheduling immediate actions for: {operational_action.description}")
        
        # Decompose operational action into immediate steps
        steps = self._decompose_to_steps(operational_action)
        
        immediate_actions = []
        current_time = datetime.now()
        
        for i, step in enumerate(steps):
            action = Action(
                id=f"immediate_action_{operational_action.id}_{i}",
                description=step,
                goal_id=operational_action.goal_id,
                timescale=Timescale.IMMEDIATE,
                priority=5,
                estimated_duration=timedelta(minutes=15),
                scheduled_time=current_time + timedelta(minutes=i*15),
                expected_outcome=f"Complete step: {step}"
            )
            immediate_actions.append(action)
        
        self.immediate_actions.extend(immediate_actions)
        
        logger.info(f"✅ Scheduled {len(immediate_actions)} immediate actions")
        
        return immediate_actions
    
    def get_next_action(self) -> Optional[Action]:
        """
        Get the next action to execute right now
        
        Returns:
            Next immediate action or None
        """
        if not self.immediate_actions:
            # Generate immediate actions from operational plans
            self._generate_immediate_actions()
        
        if not self.immediate_actions:
            return None
        
        # Get highest priority action that's ready
        now = datetime.now()
        ready_actions = [
            a for a in self.immediate_actions
            if not a.scheduled_time or a.scheduled_time <= now
        ]
        
        if not ready_actions:
            return None
        
        # Sort by priority
        ready_actions.sort(key=lambda a: a.priority, reverse=True)
        
        return ready_actions[0]
    
    def complete_action(self, action_id: str):
        """Mark action as completed and update plans"""
        # Remove from immediate actions
        self.immediate_actions = [a for a in self.immediate_actions if a.id != action_id]
        
        # Update goal progress if goal hierarchy available
        if self.goal_hierarchy:
            # Find action's goal and update progress
            for action in self.immediate_actions:
                if action.id == action_id:
                    goal = self.goal_hierarchy.get_goal(action.goal_id)
                    if goal:
                        # Increment progress slightly
                        new_progress = min(goal.progress + 0.05, 1.0)
                        self.goal_hierarchy.update_progress(action.goal_id, new_progress)
                    break
        
        logger.info(f"✅ Completed action: {action_id}")
    
    def _generate_immediate_actions(self):
        """Generate immediate actions from operational plans"""
        for plan in self.operational_plans.values():
            if plan.status != "active":
                continue
            
            # Get first incomplete action
            for action in plan.actions:
                if action not in [a.id for a in self.immediate_actions]:
                    immediate = self.schedule_immediate_actions(action)
                    if immediate:
                        break  # Only schedule one operational action at a time
    
    def _identify_milestones(self, goal) -> List[str]:
        """Identify major milestones for a goal"""
        # Use success criteria as milestones
        if goal.success_criteria:
            return goal.success_criteria
        
        # Default milestones based on goal level
        from goal_hierarchy import GoalLevel
        
        if goal.level == GoalLevel.LIFE:
            return [
                "Achieve 80% AGI capability",
                "Achieve 90% AGI capability",
                "Achieve 95% AGI capability"
            ]
        elif goal.level == GoalLevel.YEAR:
            return [
                "Q1: Foundation systems",
                "Q2: Integration and testing",
                "Q3: Optimization and scaling",
                "Q4: Advanced capabilities"
            ]
        elif goal.level == GoalLevel.QUARTER:
            return [
                "Month 1: Core implementation",
                "Month 2: Integration",
                "Month 3: Testing and refinement"
            ]
        else:
            return ["Complete goal"]
    
    def _decompose_to_objectives(self, strategic_action: Action) -> List[str]:
        """Decompose strategic action into weekly objectives"""
        # Simple decomposition - can be enhanced with AI
        base = strategic_action.description
        
        return [
            f"Research and design: {base}",
            f"Implement core functionality: {base}",
            f"Test and validate: {base}",
            f"Integrate and deploy: {base}"
        ]
    
    def _decompose_to_tasks(self, tactical_action: Action) -> List[str]:
        """Decompose tactical action into daily tasks"""
        base = tactical_action.description
        
        return [
            f"Plan approach: {base}",
            f"Execute main work: {base}",
            f"Review and refine: {base}"
        ]
    
    def _decompose_to_steps(self, operational_action: Action) -> List[str]:
        """Decompose operational action into immediate steps"""
        base = operational_action.description
        
        return [
            f"Prepare: {base}",
            f"Execute: {base}",
            f"Verify: {base}"
        ]
    
    def replan(self, timescale: Timescale, reason: str):
        """
        Replan at a specific timescale due to changed circumstances
        
        Args:
            timescale: Which timescale to replan
            reason: Why replanning is needed
        """
        logger.info(f"🔄 Replanning {timescale.value} due to: {reason}")
        
        if timescale == Timescale.STRATEGIC:
            # Replan strategic level
            for plan in list(self.strategic_plans.values()):
                if plan.status == "active":
                    # Mark old plan as abandoned
                    plan.status = "abandoned"
                    # Create new plan
                    self.create_strategic_plan(plan.goal_id)
        
        elif timescale == Timescale.TACTICAL:
            # Replan tactical level
            for plan in list(self.tactical_plans.values()):
                if plan.status == "active":
                    plan.status = "abandoned"
                    # Would need strategic action to replan
        
        elif timescale == Timescale.OPERATIONAL:
            # Replan operational level
            for plan in list(self.operational_plans.values()):
                if plan.status == "active":
                    plan.status = "abandoned"
                    # Would need tactical action to replan
        
        elif timescale == Timescale.IMMEDIATE:
            # Clear immediate actions and regenerate
            self.immediate_actions.clear()
            self._generate_immediate_actions()
    
    def get_planning_status(self) -> Dict[str, Any]:
        """Get status of planning across all timescales"""
        return {
            'strategic_plans': len(self.strategic_plans),
            'tactical_plans': len(self.tactical_plans),
            'operational_plans': len(self.operational_plans),
            'immediate_actions': len(self.immediate_actions),
            'next_action': self.get_next_action().description if self.get_next_action() else None,
            'active_plans': {
                'strategic': len([p for p in self.strategic_plans.values() if p.status == "active"]),
                'tactical': len([p for p in self.tactical_plans.values() if p.status == "active"]),
                'operational': len([p for p in self.operational_plans.values() if p.status == "active"])
            }
        }
    
    def align_plans(self):
        """Ensure all plans are aligned across timescales"""
        logger.info("🔗 Aligning plans across timescales")
        
        # Strategic → Tactical alignment
        for strategic_plan in self.strategic_plans.values():
            if strategic_plan.status != "active":
                continue
            
            # Ensure tactical plans exist for strategic actions
            for strategic_action in strategic_plan.actions:
                tactical_plan_id = f"tactical_{strategic_action.id}"
                if tactical_plan_id not in self.tactical_plans:
                    self.create_tactical_plan(strategic_action)
        
        # Tactical → Operational alignment
        for tactical_plan in self.tactical_plans.values():
            if tactical_plan.status != "active":
                continue
            
            # Ensure operational plans exist for tactical actions
            for tactical_action in tactical_plan.actions:
                operational_plan_id = f"operational_{tactical_action.id}"
                if operational_plan_id not in self.operational_plans:
                    self.create_operational_plan(tactical_action)
        
        logger.info("✅ Plans aligned across timescales")


# Singleton instance
_multi_timescale_planner = None

def get_multi_timescale_planner(goal_hierarchy=None) -> MultiTimescalePlanner:
    """Get or create singleton multi-timescale planner"""
    global _multi_timescale_planner
    if _multi_timescale_planner is None:
        _multi_timescale_planner = MultiTimescalePlanner(goal_hierarchy)
    return _multi_timescale_planner
