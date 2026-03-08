"""
Goal-Driven Autonomous Cycle

Transforms AlleyBot from reactive to proactive by actively pursuing goals.

Instead of:
- Random opportunistic actions
- Reactive responses only

Now:
- Work on highest priority goal
- Detect opportunities and generate new goals
- Track progress toward objectives
- Measure goal completion

This is the final piece of the AGI loop: Goals → Actions → Learning → Better Goals
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GoalDrivenCycle:
    """
    Manages goal-driven autonomous behavior.
    
    Integrates with:
    - GoalStackManager: Persistent goal tracking
    - GoalGenerator: Autonomous goal creation
    - ActionRouter: Goal-driven action execution
    - WorldState: Opportunity detection
    """
    
    def __init__(self, agi_kernel):
        self.agi = agi_kernel
        self.goal_stack = None
        self.goal_generator = None
        self.world_state = None
        
        # Initialize components
        if hasattr(agi_kernel, 'goal_stack'):
            self.goal_stack = agi_kernel.goal_stack
        if hasattr(agi_kernel, 'goal_generator'):
            self.goal_generator = agi_kernel.goal_generator
        if hasattr(agi_kernel, 'world_state'):
            self.world_state = agi_kernel.world_state
    
    async def get_next_action(self) -> Optional[Dict]:
        """
        Get next action based on goal-driven strategy.
        
        Priority order:
        1. Active goals (work on highest priority)
        2. Detected opportunities (generate new goals)
        3. None (no action needed)
        
        Returns:
            Action spec for ActionRouter, or None
        """
        # Step 1: Check for active goals
        if self.goal_stack:
            active_goals = self.goal_stack.get_active_goals(limit=5)
            
            if active_goals:
                # Work on highest priority goal
                goal = active_goals[0]
                action = await self._get_action_for_goal(goal)
                
                if action:
                    logger.info(f"🎯 Goal-driven action: {goal.description[:50]}...")
                    return action
        
        # Step 2: Detect opportunities for new goals
        opportunities = self._detect_opportunities()
        
        if opportunities:
            # Generate goal from best opportunity
            goal = await self._generate_goal_from_opportunity(opportunities[0])
            
            if goal:
                logger.info(f"💡 New goal generated: {goal.description[:50]}...")
                return {
                    'action_type': 'goal_generated',
                    'goal_id': goal.id,
                    'goal_description': goal.description
                }
        
        # Step 3: No goals or opportunities
        return None
    
    async def _get_action_for_goal(self, goal) -> Optional[Dict]:
        """
        Determine next action to work toward goal.
        
        Maps goal context to appropriate actions:
        - 'engagement' goals → engage with content
        - 'growth' goals → post quality content
        - 'quality' goals → analyze and improve
        """
        goal_type = goal.context.get('type', 'general')

        def build_action(plugin: str, action_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
            return {
                'plugin': plugin,
                'action_type': action_type,
                'params': params,
                'context': {
                    'goal_driven': True,
                    'goal_id': goal.id,
                    'goal_description': goal.description,
                    'impact': 'high',
                    'source': 'goal_driven_cycle',
                }
            }
        
        # Engagement goals
        if goal_type == 'recurring' or 'engagement' in goal.description.lower():
            platforms = goal.context.get('platforms', ['moltx'])

            primary_platform = platforms[0]
            if primary_platform == 'moltx':
                return build_action('moltx', 'moltx_engage', {'count': 3})
            if primary_platform == 'clawbr':
                return build_action('clawbr', 'clawbr_engage', {})
            return build_action(primary_platform, 'engage', {'count': 3})
        
        # Growth goals
        elif goal_type == 'growth' or 'grow' in goal.description.lower():
            return build_action('moltx', 'moltx_intelligent_post', {'topic': goal.description})
        
        # Quality goals
        elif goal_type == 'quality' or 'engagement rate' in goal.description.lower():
            # Analyze performance and adjust strategy
            return build_action('analytics', 'analyze_performance', {'time_window': '7d'})
        
        # Default: increment attempt counter
        if self.goal_stack:
            self.goal_stack.increment_attempt(goal.id)
        
        return None
    
    def _detect_opportunities(self) -> List[Dict]:
        """
        Detect opportunities from world state for new goals.
        
        Opportunities include:
        - Trending topics (high engagement potential)
        - Underperforming metrics (improvement needed)
        - User interactions (relationship building)
        - Time-based patterns (optimal posting times)
        """
        opportunities = []
        
        if not self.world_state:
            return opportunities
        
        try:
            # Opportunity 1: Trending topics
            trending = self.world_state.get_trending_topics(limit=3)
            for topic_data in trending:
                topic = topic_data.get('topic')
                count = topic_data.get('count', 0)
                
                if count > 5:  # Significant trend
                    opportunities.append({
                        'type': 'trending_topic',
                        'topic': topic,
                        'evidence': {'mention_count': count},
                        'priority': min(10, count / 2),
                        'description': f"Capitalize on trending topic: {topic}"
                    })
            
            # Opportunity 2: Active users (relationship building)
            # Get entities with recent interactions
            recent_interactions = self.world_state.get_events(limit=20)
            active_users = {}
            
            for event in recent_interactions:
                user = event.actor_id
                if user and user != 'alleybot':
                    active_users[user] = active_users.get(user, 0) + 1
            
            # Find most active user
            if active_users:
                top_user = max(active_users.items(), key=lambda x: x[1])
                if top_user[1] > 3:  # Multiple interactions
                    opportunities.append({
                        'type': 'relationship',
                        'user_id': top_user[0],
                        'evidence': {'interaction_count': top_user[1]},
                        'priority': 7,
                        'description': f"Build relationship with active user: {top_user[0]}"
                    })
        
        except Exception as e:
            logger.debug(f"Opportunity detection failed: {e}")
        
        # Sort by priority
        opportunities.sort(key=lambda x: x.get('priority', 0), reverse=True)
        return opportunities
    
    async def _generate_goal_from_opportunity(self, opportunity: Dict) -> Optional[Any]:
        """
        Generate a goal from detected opportunity.
        
        Uses GoalGenerator if available, otherwise creates simple goal.
        """
        if not self.goal_stack:
            return None
        
        try:
            # Use goal generator if available
            if self.goal_generator:
                # Build world state context
                world_state = {
                    'opportunity': opportunity,
                    'timestamp': datetime.now().isoformat()
                }
                
                goals = self.goal_generator.generate_goals(world_state)
                if goals:
                    # Add to goal stack
                    for goal in goals:
                        self.goal_stack.add_goal_from_autonomous(goal)
                    return goals[0]
            
            # Fallback: Create simple goal directly
            from src.autonomy.goal_manager import Goal
            
            goal_id = f"opp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            description = opportunity.get('description', 'Capitalize on opportunity')
            priority = int(opportunity.get('priority', 5))
            
            goal = Goal(
                id=goal_id,
                description=description,
                priority=priority,
                context={
                    'type': opportunity.get('type', 'opportunity'),
                    'evidence': opportunity.get('evidence', {}),
                    'source': 'opportunity_detection'
                }
            )
            
            if self.goal_stack.add_goal(goal):
                return goal
        
        except Exception as e:
            logger.warning(f"Failed to generate goal from opportunity: {e}")
        
        return None
    
    def update_goal_progress(self, goal_id: str, action_result: Dict):
        """
        Update goal progress based on action result.
        
        Args:
            goal_id: Goal ID
            action_result: Result from ActionRouter
        """
        if not self.goal_stack:
            return
        
        try:
            success = action_result.get('success', False)
            
            if success:
                # Check if goal is complete
                goal = self.goal_stack.get_goal(goal_id)
                if goal:
                    # Simple completion check: if action succeeded, increment progress
                    # More sophisticated checks can be added based on success_criteria
                    if goal.attempts >= 5:  # After 5 successful attempts
                        self.goal_stack.complete_goal(goal_id)
                        logger.info(f"✅ Goal completed: {goal.description[:50]}...")
            else:
                # Action failed, increment attempt counter
                self.goal_stack.increment_attempt(goal_id)
        
        except Exception as e:
            logger.debug(f"Failed to update goal progress: {e}")


def create_goal_driven_cycle(agi_kernel):
    """Factory function to create goal-driven cycle"""
    return GoalDrivenCycle(agi_kernel)
