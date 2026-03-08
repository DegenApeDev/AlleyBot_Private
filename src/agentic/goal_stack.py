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
            'post': ['moltx_post', 'clawbr_post'],
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
                    'type': getattr(gen_goal, 'goal_type', 'autonomous'),  # Default to 'autonomous' if not present
                    'actions': gen_goal.actions,
                    'success_criteria': getattr(gen_goal, 'success_criteria', None),  # May not exist
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
    
    # =========================================================================
    # Self-Directed Goal Proposal (NEW - Autonomous Goal Creation)
    # =========================================================================
    
    def propose_goals_from_observations(self, observations: List[Any], 
                                       cross_platform_intel: Optional[Any] = None) -> List[Goal]:
        """
        Autonomously propose new goals based on observations and intelligence
        
        Args:
            observations: List of SyModObservation objects
            cross_platform_intel: Optional CrossPlatformIntelligence instance
        
        Returns:
            List of proposed Goal objects
        """
        proposed_goals = []
        
        # Analyze observations for goal opportunities
        engagement_counts = {'moltx': 0, 'clawbr': 0, 'telegram': 0}
        trending_topics = set()
        mentions_count = 0
        
        for obs in observations:
            if not hasattr(obs, 'source_plugin') or not hasattr(obs, 'data'):
                continue
            
            platform = obs.source_plugin
            data = obs.data
            
            # Count engagement opportunities
            if platform in engagement_counts:
                engagement_counts[platform] += 1
            
            # Track mentions (high priority)
            if obs.observation_type == 'mention':
                mentions_count += 1
            
            # Extract trending topics
            if 'hashtags' in data:
                trending_topics.update([h.lower().lstrip('#') for h in data.get('hashtags', [])])
        
        # Propose goal: Low engagement on platform
        for platform, count in engagement_counts.items():
            if count < 5:  # Low engagement threshold
                goal = Goal(
                    id=f"boost_{platform}_engagement_{datetime.now().strftime('%Y%m%d')}",
                    description=f"Increase {platform} engagement to 50+ interactions today",
                    priority=7,
                    deadline=datetime.now() + timedelta(hours=12),
                    context={
                        'type': 'autonomous_engagement',
                        'platform': platform,
                        'current_count': count,
                        'target_count': 50,
                        'proposed_by': 'self',
                        'reason': f'Low engagement detected ({count} interactions)'
                    }
                )
                proposed_goals.append(goal)
                print(f"🎯 Self-proposed goal: Boost {platform} engagement")
        
        # Propose goal: Respond to mentions
        if mentions_count > 0:
            goal = Goal(
                id=f"respond_mentions_{datetime.now().strftime('%Y%m%d%H%M')}",
                description=f"Respond to {mentions_count} pending mentions",
                priority=9,  # High priority
                deadline=datetime.now() + timedelta(hours=2),
                context={
                    'type': 'autonomous_response',
                    'mention_count': mentions_count,
                    'proposed_by': 'self',
                    'reason': f'{mentions_count} mentions require response'
                }
            )
            proposed_goals.append(goal)
            print(f"🎯 Self-proposed goal: Respond to {mentions_count} mentions")
        
        # Propose goal: Create content about trending topics
        if trending_topics and len(trending_topics) >= 3:
            top_topic = list(trending_topics)[0]  # Pick first trending topic
            goal = Goal(
                id=f"trending_content_{top_topic}_{datetime.now().strftime('%Y%m%d')}",
                description=f"Create 3 posts about trending topic #{top_topic}",
                priority=8,
                deadline=datetime.now() + timedelta(hours=6),
                context={
                    'type': 'autonomous_content',
                    'topic': top_topic,
                    'post_count': 3,
                    'proposed_by': 'self',
                    'reason': f'Topic #{top_topic} is trending'
                }
            )
            proposed_goals.append(goal)
            print(f"🎯 Self-proposed goal: Create content about #{top_topic}")
        
        # Use cross-platform intelligence if available
        if cross_platform_intel and hasattr(cross_platform_intel, 'last_synthesis'):
            synthesis = cross_platform_intel.last_synthesis
            
            if synthesis:
                opportunities = synthesis.get('opportunities', [])
                
                for opp in opportunities[:2]:  # Top 2 opportunities
                    goal = Goal(
                        id=f"cross_platform_opp_{datetime.now().strftime('%Y%m%d%H%M')}",
                        description=f"Execute cross-platform opportunity: {opp['action']}",
                        priority=8,
                        deadline=datetime.now() + timedelta(hours=4),
                        context={
                            'type': 'autonomous_cross_platform',
                            'opportunity': opp,
                            'proposed_by': 'self',
                            'reason': opp.get('reason', 'Cross-platform opportunity detected')
                        }
                    )
                    proposed_goals.append(goal)
                    print(f"🎯 Self-proposed goal: {opp['action']}")
        
        return proposed_goals
    
    def auto_add_proposed_goals(self, observations: List[Any], 
                               cross_platform_intel: Optional[Any] = None,
                               max_new_goals: int = 3) -> int:
        """
        Automatically propose and add new goals based on observations
        
        Args:
            observations: List of observations
            cross_platform_intel: Optional cross-platform intelligence
            max_new_goals: Maximum number of new goals to add
        
        Returns:
            Number of goals added
        """
        proposed = self.propose_goals_from_observations(observations, cross_platform_intel)
        
        added = 0
        for goal in proposed[:max_new_goals]:
            if self.add_goal(goal):
                added += 1
                print(f"✅ Auto-added self-proposed goal: {goal.description[:60]}")
        
        return added


def create_goal_stack(agi_kernel) -> GoalStackBridge:
    """Factory function to create goal stack bridge"""
    return GoalStackBridge(agi_kernel)
