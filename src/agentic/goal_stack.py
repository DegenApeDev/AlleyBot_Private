"""
Goal Stack Bridge for AGI Kernel

Lightweight integration layer that connects AGI Kernel to the existing
GoalStackManager in src/autonomy/goal_manager.py.

This bridge:
- Manages goal hierarchies and priorities
- Tracks goal execution and completion
- Connects to SecureGoalGenerator for new goals
- Integrates with world state for context
- Provides goal-driven action selection
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add src/autonomy to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'autonomy'))

from goal_manager import GoalStackManager, Goal, goal_from_action


class GoalStackBridge:
    """
    Bridge between AGI Kernel and Goal Stack Manager.
    
    Provides high-level interface for:
    - Goal-driven action selection
    - Goal tracking and completion
    - Integration with SecureGoalGenerator
    - Goal hierarchy management
    """
    
    def __init__(self, agi_kernel, db_path: str = None):
        self.agi = agi_kernel
        self.core = agi_kernel.core if hasattr(agi_kernel, 'core') else None
        
        # Initialize goal stack manager
        if db_path is None:
            data_dir = getattr(self.core, 'data_dir', 'data') if self.core else 'data'
            db_path = f"{data_dir}/goals.db"
        
        self.goal_manager = GoalStackManager(db_path=db_path)
        self.current_goal: Optional[Goal] = None
        
        # Seed default goals if needed
        stats = self.goal_manager.get_stats()
        if stats['total'] == 0:
            self._seed_default_goals()
        
        print(f"🎯 GoalStackBridge initialized ({stats['active']} active, {stats['completed']} completed)")
    
    def _seed_default_goals(self):
        """Seed initial goals for new installations"""
        default_goals = [
            Goal(
                id="daily_engagement",
                description="Maintain daily engagement across social platforms",
                priority=8,
                deadline=datetime.now() + timedelta(days=1),
                context={'type': 'recurring', 'platforms': ['moltx', 'clawbr']}
            ),
            Goal(
                id="weekly_growth",
                description="Grow follower count by engaging with trending content",
                priority=7,
                deadline=datetime.now() + timedelta(days=7),
                context={'type': 'growth', 'metric': 'followers'}
            ),
            Goal(
                id="content_quality",
                description="Maintain high engagement rate on posts (>5%)",
                priority=9,
                deadline=datetime.now() + timedelta(days=30),
                context={'type': 'quality', 'target_rate': 0.05}
            ),
        ]
        
        for goal in default_goals:
            self.goal_manager.add_goal(goal)
        
        print(f"🌱 Seeded {len(default_goals)} default goals")
    
    # =========================================================================
    # Goal-Driven Action Selection
    # =========================================================================
    
    def get_goal_driven_action(self, available_actions: List[Dict]) -> Optional[Dict]:
        """
        Get next action based on active goals.
        
        This is called by decision system before reactive action selection.
        
        Args:
            available_actions: List of available actions from plugins
            
        Returns:
            Action dict with goal context, or None
        """
        # Get next active goal
        goal = self.goal_manager.get_next_goal()
        if not goal:
            return None
        
        self.current_goal = goal
        
        # Map goal to appropriate action
        action = self._goal_to_action(goal, available_actions)
        if action:
            # Mark that this action serves a goal
            action['goal_id'] = goal.id
            action['goal_description'] = goal.description
            action['reason'] = f"[Goal {goal.priority}/10] {goal.description[:50]}"
            
            # Increment attempt counter
            self.goal_manager.increment_attempt(goal.id)
        
        return action
    
    def _goal_to_action(self, goal: Goal, available_actions: List[Dict]) -> Optional[Dict]:
        """
        Convert a goal into a concrete action.
        
        Maps goal patterns to available actions.
        """
        # Map goal patterns to action IDs
        goal_patterns = {
            'engagement': ['moltx_engage', 'clawbr_engage', 'check_engagement'],
            'post': ['moltx_post', 'clawbr_post', 'moltbook_post'],
            'growth': ['analyze_trending', 'moltx_engage', 'clawbr_engage'],
            'quality': ['check_engagement', 'analyze_trending'],
            'reply': ['check_comments', 'dm_check'],
            'revenue': ['a2a_tasks', 'check_attestations'],
            'skill': ['discover_skills', 'analyze_trending'],
        }
        
        # Get available action IDs
        available_ids = {a['id'] for a in available_actions}
        
        # Try to find matching action
        desc_lower = goal.description.lower()
        
        for pattern, action_ids in goal_patterns.items():
            if pattern in desc_lower:
                for action_id in action_ids:
                    if action_id in available_ids:
                        # Return matching available action
                        for a in available_actions:
                            if a['id'] == action_id:
                                return a.copy()
        
        # Fallback: pick highest priority available action
        if available_actions:
            return available_actions[0].copy()
        
        return None
    
    # =========================================================================
    # Goal Management
    # =========================================================================
    
    def add_goal(self, goal: Goal) -> bool:
        """Add a new goal to the stack"""
        return self.goal_manager.add_goal(goal)
    
    def complete_current_goal(self, success: bool = True):
        """Mark current goal as completed or failed"""
        if not self.current_goal:
            return
        
        if success:
            self.goal_manager.complete_goal(self.current_goal.id)
            print(f"✅ Goal completed: {self.current_goal.description[:50]}...")
        else:
            self.goal_manager.fail_goal(self.current_goal.id, "Action failed")
            print(f"❌ Goal failed: {self.current_goal.description[:50]}...")
        
        self.current_goal = None
    
    def get_active_goals(self, limit: int = 10) -> List[Goal]:
        """Get active goals sorted by priority"""
        return self.goal_manager.get_active_goals(limit=limit)
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a specific goal by ID"""
        return self.goal_manager.get_goal(goal_id)
    
    def cleanup_expired_goals(self) -> int:
        """Mark expired goals as failed"""
        return self.goal_manager.cleanup_expired()
    
    # =========================================================================
    # Integration with SecureGoalGenerator
    # =========================================================================
    
    def integrate_generated_goals(self, generated_goals: List) -> int:
        """
        Integrate goals from SecureGoalGenerator into goal stack.
        
        Args:
            generated_goals: List of Goal objects from SecureGoalGenerator
            
        Returns:
            Number of goals added
        """
        added = 0
        
        for gen_goal in generated_goals:
            # Convert SecureGoalGenerator Goal to GoalStackManager Goal
            goal = Goal(
                id=gen_goal.goal_id,
                description=gen_goal.description,
                priority=gen_goal.priority,
                deadline=datetime.fromisoformat(gen_goal.deadline) if gen_goal.deadline else None,
                context={
                    'type': gen_goal.goal_type,
                    'actions': gen_goal.actions,
                    'success_criteria': gen_goal.success_criteria,
                    'generated_by': 'SecureGoalGenerator',
                    'trust_score': gen_goal.trust_score,
                }
            )
            
            if self.goal_manager.add_goal(goal):
                added += 1
                print(f"🎯 Integrated generated goal: {goal.description[:60]}")
        
        return added
    
    # =========================================================================
    # World State Integration
    # =========================================================================
    
    def get_goals_for_world_context(self) -> Dict[str, Any]:
        """
        Get goal context for world state analysis.
        
        Provides information about current goals for decision making.
        """
        active_goals = self.get_active_goals(limit=5)
        
        return {
            'active_goal_count': len(active_goals),
            'current_goal': {
                'id': self.current_goal.id,
                'description': self.current_goal.description,
                'priority': self.current_goal.priority,
            } if self.current_goal else None,
            'top_priorities': [
                {
                    'id': g.id,
                    'description': g.description,
                    'priority': g.priority,
                    'type': g.context.get('type', 'unknown'),
                }
                for g in active_goals
            ],
        }
    
    # =========================================================================
    # Statistics and Monitoring
    # =========================================================================
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of goal stack status"""
        stats = self.goal_manager.get_stats()
        active_goals = self.get_active_goals(limit=5)
        
        return {
            'total_goals': stats['total'],
            'pending': stats['pending'],
            'active': stats['active'],
            'completed': stats['completed'],
            'failed': stats['failed'],
            'current_goal': {
                'id': self.current_goal.id,
                'description': self.current_goal.description,
                'priority': self.current_goal.priority,
            } if self.current_goal else None,
            'top_active_goals': [
                {
                    'id': g.id,
                    'description': g.description[:50],
                    'priority': g.priority,
                    'attempts': g.attempts,
                }
                for g in active_goals
            ],
        }
    
    def get_goal_stats(self) -> Dict[str, int]:
        """Get goal statistics"""
        return self.goal_manager.get_stats()


def create_goal_stack(agi_kernel) -> GoalStackBridge:
    """Factory function to create goal stack bridge"""
    return GoalStackBridge(agi_kernel)
