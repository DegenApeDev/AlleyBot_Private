"""
Default Goal Seeding System

Provides AlleyBot with initial goals to bootstrap autonomous behavior.
Without goals, AlleyBot has nothing to do. This seeds meaningful objectives.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from src.agentic.goal_manager import GoalStatus

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
        Seed default goals if GoalManager v2 (SQLite) is empty.
        
        Returns:
            Number of goals seeded
        """
        if not hasattr(self.agi_kernel, 'goal_manager'):
            logger.warning("AGI Kernel has no goal_manager, cannot seed goals")
            return 0
        
        # Resolve GoalManager v2 (SQLite) — the single authoritative store
        gm_v2 = None
        goal_mgr = self.agi_kernel.goal_manager
        if hasattr(goal_mgr, 'goal_manager_v2'):
            # AutonomousGoalManager delegates to GoalManager v2
            gm_v2 = goal_mgr.goal_manager_v2
        else:
            # goal_manager might already be GoalManager v2 directly
            gm_v2 = goal_mgr
        
        if not gm_v2 or not hasattr(gm_v2, 'get_goals'):
            logger.warning("Could not resolve GoalManager v2 for seeding")
            return 0
        
        try:
            active_goals = gm_v2.get_goals(status=GoalStatus.ACTIVE, limit=20)
        except Exception as e:
            logger.warning(f"GoalManager query failed during seeding: {e}")
            return 0
        
        if len(active_goals) >= 3:
            logger.debug(f"Already have {len(active_goals)} active goals, skipping seed")
            return 0
        
        # Also check if default goals already exist (any status)
        try:
            all_goals = gm_v2.get_goals(limit=50)
        except Exception as e:
            logger.warning(f"GoalManager query failed during dedup check: {e}")
            return 0
        
        existing_ids = {g.id for g in all_goals}
        
        goals = self.get_default_goals()
        seeded_count = 0
        
        for goal_spec in goals:
            goal_id = goal_spec['id']
            if goal_id in existing_ids:
                continue
            
            try:
                platforms = goal_spec.get('metadata', {}).get('platforms', [])
                action_types = goal_spec.get('metadata', {}).get('action_types', [])
                
                raw_priority = goal_spec.get('priority', 2)
                if raw_priority >= 3:
                    priority = GoalPriority.HIGH
                elif raw_priority >= 2:
                    priority = GoalPriority.MEDIUM
                else:
                    priority = GoalPriority.LOW
                
                goal = Goal(
                    id=goal_id,
                    title=goal_spec['title'],
                    description=goal_spec['description'],
                    category=goal_spec.get('domain', 'social'),
                    priority=priority,
                    impact_score=raw_priority * 2.5,
                    effort_estimate='hours',
                    confidence=0.8,
                    trigger_type='default_seed',
                    trigger_data={
                        'source': 'default_goal_seeder',
                        'platforms': platforms,
                        'action_types': action_types,
                        'auto_seeded': True,
                    },
                    evidence=[f"Default goal for {goal_spec.get('domain', 'social')} domain"],
                    status=GoalStatus.ACTIVE,
                )
                
                if gm_v2.add_goal(goal):
                    seeded_count += 1
                    logger.info(f"🌱 Seeded default goal: {goal_spec['title']}")
                else:
                    logger.debug(f"Goal already exists or add failed: {goal_id}")
            except Exception as e:
                logger.error(f"Failed to seed goal {goal_id}: {e}")
        
        if seeded_count > 0:
            logger.info(f"🌱 Seeded {seeded_count} default goals → GoalManager v2 (SQLite)")
        
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
