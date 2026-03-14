"""
Default Goal Seeding System

Provides AlleyBot with initial goals to bootstrap autonomous behavior.
Without goals, AlleyBot has nothing to do. This seeds meaningful objectives.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DefaultGoalSeeder:
    """Seeds default goals when AlleyBot has no active work"""
    
    def __init__(self, agi_kernel=None):
        self.agi_kernel = agi_kernel
        self.seeded_goals = set()  # Track what we've already seeded
    
    def get_default_goals(self) -> List[Dict[str, Any]]:
        """
        Get default goals for autonomous operation.
        
        These are safe, low-risk goals that give AlleyBot purpose.
        """
        return [
            # Social engagement goals
            {
                'id': 'default_social_engagement',
                'title': 'Engage across all social platforms',
                'description': 'Actively participate in discussions on MoltX, Clawbr, MoltChan, and MoltbookAI',
                'type': 'recurring',
                'domain': 'social',
                'priority': 3,
                'metadata': {
                    'platforms': ['moltx', 'clawbr', 'moltchan', 'moltbookai'],
                    'action_types': ['post', 'reply', 'engage', 'check_notifications'],
                    'auto_approved': True,
                }
            },
            {
                'id': 'default_market_intelligence',
                'title': 'Monitor markets and gather intelligence',
                'description': 'Track crypto prices, prediction markets, news feeds, and on-chain activity',
                'type': 'recurring',
                'domain': 'analysis',
                'priority': 3,
                'metadata': {
                    'platforms': ['crypto', 'polymarket', 'mcp', 'onchain'],
                    'action_types': ['analyze', 'query', 'price_check'],
                    'auto_approved': True,
                }
            },
            {
                'id': 'default_content_creation',
                'title': 'Create valuable content across platforms',
                'description': 'Generate insightful posts, analyses, and updates using available content tools',
                'type': 'recurring',
                'domain': 'content',
                'priority': 2,
                'metadata': {
                    'platforms': ['moltx', 'moltbookai', 'moltroad'],
                    'action_types': ['post', 'update'],
                    'auto_approved': True,
                }
            },
            {
                'id': 'default_intelligence_gathering',
                'title': 'Gather and analyze information',
                'description': 'Use intelligence tools, news feeds, and analytics to stay informed',
                'type': 'recurring',
                'domain': 'analysis',
                'priority': 2,
                'metadata': {
                    'platforms': ['intelligence', 'mcp', 'analytics'],
                    'action_types': ['analyze', 'query', 'sentiment'],
                    'auto_approved': True,
                }
            },
            {
                'id': 'default_wallet_monitoring',
                'title': 'Monitor wallet balances and on-chain activity',
                'description': 'Check Base and Solana wallet balances, track on-chain transactions',
                'type': 'recurring',
                'domain': 'analysis',
                'priority': 2,
                'metadata': {
                    'platforms': ['base_wallet_balance', 'solana_wallet_balance', 'onchain'],
                    'action_types': ['query', 'check'],
                    'auto_approved': True,
                }
            },
            {
                'id': 'default_agent_collaboration',
                'title': 'Discover and collaborate with other agents',
                'description': 'Use A2A protocol to find and interact with other AI agents',
                'type': 'recurring',
                'domain': 'social',
                'priority': 1,
                'metadata': {
                    'platforms': ['a2a'],
                    'action_types': ['discover', 'query'],
                    'auto_approved': True,
                }
            },
            {
                'id': 'default_self_improvement',
                'title': 'Analyze and improve capabilities',
                'description': 'Periodically analyze capability gaps and discover new skills',
                'type': 'recurring',
                'domain': 'self_improvement',
                'priority': 1,
                'metadata': {
                    'platforms': ['selfimprove', 'skills'],
                    'action_types': ['analyze', 'discover'],
                    'auto_approved': True,
                }
            },
            {
                'id': 'default_cross_platform_coordination',
                'title': 'Coordinate engagement across platforms',
                'description': 'Use engagement plugin to coordinate activities across all platforms',
                'type': 'recurring',
                'domain': 'social',
                'priority': 2,
                'metadata': {
                    'platforms': ['engagement'],
                    'action_types': ['engage', 'coordinate'],
                    'auto_approved': True,
                }
            },
            # Trend monitoring
            {
                'id': 'default_trend_monitoring',
                'title': 'Monitor and participate in trending topics',
                'description': 'Track trending topics across platforms and contribute valuable insights',
                'type': 'trend_participation',
                'domain': 'analysis',
                'priority': 2,
                'risk_level': 'low',
                'status': 'active',
                'recurring': True,
                'interval_hours': 12,
                'success_criteria': {
                    'trends_analyzed': 3,
                    'contributions_made': 2,
                },
                'metadata': {
                    'platforms': ['moltx', 'moltchan'],
                    'action_types': ['analyze', 'post', 'reply'],
                    'auto_approved': True,
                }
            },
            # Reputation building
            {
                'id': 'default_reputation_building',
                'title': 'Build reputation through helpful interactions',
                'description': 'Provide value to the community through insightful replies and quality content',
                'type': 'reputation_building',
                'domain': 'social',
                'priority': 3,
                'risk_level': 'low',
                'status': 'active',
                'recurring': True,
                'interval_hours': 24,
                'success_criteria': {
                    'helpful_replies': 3,
                    'positive_feedback': 2,
                },
                'metadata': {
                    'platforms': ['moltx', 'moltchan', 'clawbr'],
                    'action_types': ['reply', 'post'],
                    'auto_approved': True,
                }
            },
            # Learning and analysis
            {
                'id': 'default_market_analysis',
                'title': 'Analyze market trends and opportunities',
                'description': 'Monitor crypto markets and identify interesting patterns (analysis only, no trading)',
                'type': 'market_analysis',
                'domain': 'analysis',
                'priority': 3,
                'risk_level': 'low',
                'status': 'active',
                'recurring': True,
                'interval_hours': 6,
                'success_criteria': {
                    'markets_analyzed': 3,
                    'insights_generated': 2,
                },
                'metadata': {
                    'platforms': ['analytics'],
                    'action_types': ['analyze'],
                    'auto_approved': True,
                }
            },
            
            # Cross-platform presence
            {
                'id': 'default_cross_platform_presence',
                'title': 'Maintain active presence across platforms',
                'description': 'Stay active on MoltX, MoltChan, and other platforms to build community presence',
                'type': 'platform_presence',
                'domain': 'social',
                'priority': 2,
                'risk_level': 'low',
                'status': 'active',
                'recurring': True,
                'interval_hours': 8,
                'success_criteria': {
                    'platforms_active': 2,
                    'interactions_per_platform': 2,
                },
                'metadata': {
                    'platforms': ['moltx', 'moltchan', 'moltroad'],
                    'action_types': ['post', 'reply', 'engage'],
                    'auto_approved': True,
                }
            },
            
            # Community contribution
            {
                'id': 'default_community_contribution',
                'title': 'Contribute to community discussions',
                'description': 'Participate in meaningful discussions and share knowledge',
                'type': 'community_contribution',
                'domain': 'social',
                'priority': 2,
                'risk_level': 'low',
                'status': 'active',
                'recurring': True,
                'interval_hours': 12,
                'success_criteria': {
                    'discussions_joined': 2,
                    'value_added': True,
                },
                'metadata': {
                    'platforms': ['moltchan', 'clawbr'],
                    'action_types': ['engage', 'reply'],
                    'auto_approved': True,
                }
            },
        ]
    
    def seed_goals_if_needed(self) -> int:
        """
        Seed default goals if work queue is empty.
        
        Returns:
            Number of goals seeded
        """
        # Check if we have active work items
        active_work = self.agi_kernel.get_active_work_items(limit=5)
        
        if len(active_work) >= 3:
            # Already have enough work, don't seed
            return 0
        
        # Check if default goals already exist
        if hasattr(self.agi_kernel, 'goal_manager'):
            existing_goals = []
            try:
                # Try to get existing goals to avoid duplicates
                if hasattr(self.agi_kernel.goal_manager, 'get_active_goals'):
                    existing_goals = self.agi_kernel.goal_manager.get_active_goals()
            except:
                pass
            
            # If we already have active goals, don't seed
            if len(existing_goals) >= 3:
                return 0
        
        # Seed default goals using AutonomousGoalManager's AutonomousGoal class
        from src.agentic.autonomous_goals import AutonomousGoal, GoalOrigin
        from datetime import datetime
        import uuid
        
        goals = self.get_default_goals()
        seeded_count = 0
        
        for goal_spec in goals:
            try:
                # Create AutonomousGoal object with all required fields
                goal = AutonomousGoal(
                    id=f"default_{uuid.uuid4().hex[:8]}",
                    description=goal_spec['description'],
                    origin=GoalOrigin.SYSTEM,  # Use SYSTEM origin for default goals
                    detected_opportunity=f"Default goal seeding for autonomous operation: {goal_spec['title']}",
                    evidence={'source': 'default_goal_seeder', 'auto_seeded': True},
                    action_plan=[
                        f"Monitor {goal_spec.get('domain', 'social')} platforms",
                        f"Identify opportunities related to: {goal_spec['title']}",
                        "Execute relevant actions when opportunities arise"
                    ],
                    expected_outcome=f"Maintain active presence and engagement in {goal_spec.get('domain', 'social')} domain",
                    success_criteria=[
                        "Regular platform activity",
                        "Positive community engagement",
                        "Goal-aligned actions executed"
                    ],
                    priority_score=goal_spec.get('priority', 2) * 2.5,  # Map 1-4 to 2.5-10
                    urgency=5.0,
                    impact=7.0,
                    status='active',
                    created_at=datetime.now(),
                    activated_at=datetime.now()
                )
                
                # Add goal directly to manager's goals list
                self.agi_kernel.goal_manager.goals.append(goal)
                seeded_count += 1
                logger.info(f"🌱 Seeded default goal: {goal_spec['title']}")
                
            except Exception as e:
                logger.error(f"Failed to seed goal {goal_spec['id']}: {e}")
        
        if seeded_count > 0:
            logger.info(f"🌱 Seeded {seeded_count} default goals for autonomous operation")
        
        return seeded_count
    
    def get_goal_for_capability(self, capability_id: str) -> Dict[str, Any]:
        """
        Get a goal that matches a specific capability.
        
        This helps connect available actions to meaningful objectives.
        """
        # Map capabilities to goals
        capability_goal_map = {
            'moltx_post': 'default_moltx_engagement',
            'moltx_reply': 'default_moltx_engagement',
            'moltx_like': 'default_moltx_engagement',
            'moltx_trending': 'default_trend_monitoring',
            'moltchan_send': 'default_community_contribution',
            'moltchan_engage': 'default_community_contribution',
            'analytics_sentiment': 'default_market_analysis',
        }
        
        goal_id = capability_goal_map.get(capability_id)
        if not goal_id:
            return None
        
        # Find the goal
        for goal in self.get_default_goals():
            if goal['id'] == goal_id:
                return goal
        
        return None


# Singleton instance
_default_goal_seeder = None


def get_default_goal_seeder(agi_kernel=None):
    """Get or create default goal seeder singleton"""
    global _default_goal_seeder
    if _default_goal_seeder is None:
        _default_goal_seeder = DefaultGoalSeeder(agi_kernel)
    return _default_goal_seeder


def seed_default_goals(agi_kernel) -> int:
    """Convenience function to seed default goals"""
    seeder = get_default_goal_seeder(agi_kernel)
    return seeder.seed_goals_if_needed()
