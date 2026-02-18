"""
Goal Stack Mixin - Integrates Goal Stack Manager with Brain decision engine

Adds persistent goal tracking to the Brain plugin, enabling long-term
objective management alongside reactive action selection.
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Add src/autonomy to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'autonomy'))

from goal_manager import GoalStackManager, Goal, goal_from_action


class GoalStackMixin:
    """
    Mixin that adds persistent goal stack capabilities to Brain plugin.
    
    Features:
    - Goal-driven action selection (not just reactive)
    - Long-term objective tracking
    - Success/failure evaluation
    - Integration with existing Brain decision cycle
    """
    
    def _init_goal_stack(self):
        """Initialize goal stack manager"""
        try:
            if hasattr(self, 'core') and self.core:
                data_dir = getattr(self.core, 'data_dir', 'data')
            else:
                data_dir = 'data'
            
            self.goal_manager = GoalStackManager(db_path=f"{data_dir}/goals.db")
            self.current_goal: Optional[Goal] = None
            
            # Add some default goals if none exist
            stats = self.goal_manager.get_stats()
            if stats['total'] == 0:
                self._seed_default_goals()
            
            print("🎯 Goal Stack Manager initialized")
        except Exception as e:
            print(f"⚠️ Goal Stack Manager init failed: {e}")
            self.goal_manager = None
    
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
    
    def get_goal_driven_action(self, context: Dict) -> Optional[Dict]:
        """
        Get next action based on active goals (not just reactive context).
        Called by decide_next_action() before falling back to reactive selection.
        """
        if not self.goal_manager:
            return None
        
        # Get next active goal
        goal = self.goal_manager.get_next_goal()
        if not goal:
            return None
        
        self.current_goal = goal
        
        # Map goal to appropriate action
        action = self._goal_to_action(goal, context)
        if action:
            # Mark that this action serves a goal
            action['goal_id'] = goal.id
            action['goal_description'] = goal.description
            action['reason'] = f"[{goal.priority}/10] {goal.description[:50]}"
            
            # Increment attempt counter
            self.goal_manager.increment_attempt(goal.id)
        
        return action
    
    def _goal_to_action(self, goal: Goal, context: Dict) -> Optional[Dict]:
        """Convert a goal into a concrete action"""
        # Map goal patterns to actions
        goal_patterns = {
            'engagement': ['moltx_engage', 'clawbr_engage', 'check_engagement'],
            'post': ['moltx_post', 'clawbr_post', 'moltbook_post'],
            'growth': ['analyze_trending', 'moltx_engage', 'clawbr_engage'],
            'quality': ['check_engagement', 'analyze_trending'],
            'reply': ['check_comments', 'dm_check'],
        }
        
        # Check context for available actions
        available = self.get_available_actions()
        available_ids = {a['id'] for a in available}
        
        # Try to find matching action
        desc_lower = goal.description.lower()
        
        for pattern, actions in goal_patterns.items():
            if pattern in desc_lower:
                for action_id in actions:
                    if action_id in available_ids:
                        # Return matching available action
                        for a in available:
                            if a['id'] == action_id:
                                return a.copy()
        
        # Fallback: pick any available action
        if available:
            return available[0].copy()
        
        return None
    
    def complete_current_goal(self, success: bool = True):
        """Mark current goal as completed or failed"""
        if not self.goal_manager or not self.current_goal:
            return
        
        if success:
            self.goal_manager.complete_goal(self.current_goal.id)
            print(f"✅ Goal completed: {self.current_goal.description[:50]}...")
        else:
            self.goal_manager.fail_goal(self.current_goal.id, "Action failed")
            print(f"❌ Goal failed: {self.current_goal.description[:50]}...")
        
        self.current_goal = None
    
    def add_goal_command(self, *args):
        """CLI command to add a new goal"""
        if not self.goal_manager:
            return "❌ Goal manager not available"
        
        # Parse arguments - handle both individual args and joined description
        if not args:
            return "❌ Usage: brain_add_goal [description] [priority=5] [deadline_hours=24]"
        
        # Join all arguments as description for now, can parse priority/deadline later if needed
        description = ' '.join(args)
        priority = 5  # default
        deadline_hours = 24  # default
        
        # Try to extract priority and deadline from end if numeric
        if len(args) >= 2:
            try:
                priority = int(args[-1])
                description = ' '.join(args[:-1])
                if len(args) >= 3:
                    try:
                        deadline_hours = int(args[-2])
                        description = ' '.join(args[:-2])
                    except ValueError:
                        pass  # Keep default deadline
            except ValueError:
                # No numeric priority, use all as description
                description = ' '.join(args)
        
        goal = Goal(
            id=f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=description,
            priority=max(1, min(10, priority)),
            deadline=datetime.now() + timedelta(hours=deadline_hours),
            context={'source': 'manual', 'added_by': 'user'}
        )
        
        if self.goal_manager.add_goal(goal):
            return f"🎯 Goal added: {description[:60]}...\nPriority: {priority}/10 | Deadline: {deadline_hours}h"
        return "❌ Failed to add goal"
    
    def goals_command(self, *args):
        """CLI command to show active goals"""
        if not self.goal_manager:
            return "❌ Goal manager not available"
        
        goals = self.goal_manager.get_active_goals(limit=10)
        stats = self.goal_manager.get_stats()
        
        if not goals:
            output = "📭 No active goals\n\n"
        else:
            output = f"🎯 Active Goals ({len(goals)}):\n\n"
            for g in goals:
                deadline_str = g.deadline.strftime("%m/%d %H:%M") if g.deadline else "No deadline"
                status_emoji = "🔴" if g.is_expired() else "🟡" if g.status == "active" else "⚪"
                output += f"{status_emoji} [{g.priority}/10] {g.description[:50]}\n"
                output += f"   ID: {g.id} | Due: {deadline_str} | Attempts: {g.attempts}\n\n"
        
        output += f"📊 Stats: {stats['completed']} done | {stats['failed']} failed | {stats['pending']} pending | {stats['active']} active"
        return output
    
    def complete_goal_command(self, goal_id: str):
        """CLI command to manually complete a goal"""
        if not self.goal_manager:
            return "❌ Goal manager not available"
        
        if self.goal_manager.complete_goal(goal_id):
            return f"✅ Goal {goal_id} marked complete"
        return f"❌ Could not complete goal {goal_id}"
    
    def goal_stats_command(self):
        """CLI command to show goal statistics"""
        if not self.goal_manager:
            return "❌ Goal manager not available"
        
        stats = self.goal_manager.get_stats()
        return (
            f"🎯 Goal Statistics\n\n"
            f"  Total: {stats['total']}\n"
            f"  Pending: {stats['pending']}\n"
            f"  Active: {stats['active']}\n"
            f"  Completed: {stats['completed']}\n"
            f"  Failed: {stats['failed']}\n"
        )
    
    def _cleanup_expired_goals(self):
        """Mark expired goals as failed (called periodically)"""
        if self.goal_manager:
            count = self.goal_manager.cleanup_expired()
            if count > 0:
                print(f"🧹 Cleaned up {count} expired goals")
