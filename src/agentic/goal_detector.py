"""
AlleyBot Goal Detection System

Detects gaps, opportunities, and user needs that should become goals.
Analyzes:
- User requests Alley can't fulfill (skill gaps)
- Error patterns (fix goals)
- High-engagement opportunities
- Platform integration gaps

Part of AGI Core - Phase 2: Goal Management
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from src.agentic.goal_manager import Goal, GoalPriority, get_goal_manager
from src.agentic.action_logger import ActionLogger

logger = logging.getLogger(__name__)


@dataclass
class DetectedGap:
    """A detected gap or opportunity"""
    gap_type: str  # 'missing_skill', 'platform_gap', 'error_pattern', 'opportunity'
    description: str
    evidence: List[str]  # Specific examples
    impact_estimate: int  # 1-10
    frequency: int  # How often this occurs
    suggested_category: str
    suggested_priority: GoalPriority


class GoalDetector:
    """
    Detects goals from various sources:
    - Failed action patterns
    - User requests that couldn't be handled
    - Error logs
    - Platform gaps
    
    Usage:
        detector = GoalDetector()
        
        # Scan for gaps
        gaps = detector.scan_for_gaps()
        
        # Auto-generate goals
        for gap in gaps:
            goal = detector.gap_to_goal(gap)
            if goal:
                detector.propose_goal(goal)
    """
    
    def __init__(self, goal_manager=None, action_logger=None):
        self.goal_manager = goal_manager or get_goal_manager()
        self.action_logger = action_logger or ActionLogger()
        
        # Keywords that indicate skill gaps
        self.skill_gap_keywords = {
            'analyze': ['analysis', 'analyze', 'check', 'scan', 'audit'],
            'trade': ['buy', 'sell', 'trade', 'swap', 'exchange'],
            'alert': ['alert', 'notify', 'warn', 'when', 'if price'],
            'monitor': ['monitor', 'track', 'watch', 'follow'],
            'report': ['report', 'summary', 'stats', 'analytics'],
        }
        
        # Platform names we might not support
        self.platform_keywords = [
            'solana', 'ethereum', 'arbitrum', 'polygon', 'avalanche',
            'discord', 'slack', 'matrix', 'signal',
            'github', 'gitlab', 'notion', 'jira',
            'uniswap', 'aave', 'compound', 'maker'
        ]
    
    def scan_for_gaps(self, hours: int = 24) -> List[DetectedGap]:
        """
        Scan recent activity for gaps and opportunities.
        
        Returns:
            List of detected gaps that could become goals
        """
        gaps = []
        
        # 1. Scan failed actions for patterns
        failed_gaps = self._scan_failed_actions(hours)
        gaps.extend(failed_gaps)
        
        # 2. Scan user requests we couldn't handle
        request_gaps = self._scan_unhandled_requests(hours)
        gaps.extend(request_gaps)
        
        # 3. Scan for platform gaps
        platform_gaps = self._scan_platform_gaps(hours)
        gaps.extend(platform_gaps)
        
        # 4. Scan for high-engagement opportunities
        opportunity_gaps = self._scan_opportunities(hours)
        gaps.extend(opportunity_gaps)
        
        logger.info(f"🔍 Detected {len(gaps)} gaps/opportunities")
        return gaps
    
    def _scan_failed_actions(self, hours: int) -> List[DetectedGap]:
        """Scan failed actions for patterns that indicate gaps"""
        gaps = []
        
        # Get recent failures
        failed_actions = self.action_logger.get_recent_actions(
            outcome='failure',
            limit=50
        )
        
        # Group by action type and error
        patterns: Dict[str, Dict] = {}
        for action in failed_actions:
            if action.timestamp < datetime.now() - timedelta(hours=hours):
                continue
            
            key = f"{action.plugin}:{action.action_type}"
            if key not in patterns:
                patterns[key] = {
                    'count': 0,
                    'errors': [],
                    'examples': []
                }
            
            patterns[key]['count'] += 1
            if action.outcome_data and 'error' in action.outcome_data:
                patterns[key]['errors'].append(action.outcome_data['error'])
            patterns[key]['examples'].append(action.justification)
        
        # Create gaps for frequent failures
        for key, data in patterns.items():
            if data['count'] >= 3:  # 3+ failures indicates a real problem
                plugin, action = key.split(':')
                
                # Determine if it's a bug or missing capability
                error_types = set(data['errors'])
                
                if 'not implemented' in str(error_types).lower() or 'not supported' in str(error_types).lower():
                    gap = DetectedGap(
                        gap_type='missing_skill',
                        description=f"{plugin} plugin lacks {action} capability",
                        evidence=data['examples'][:3],
                        impact_estimate=min(data['count'] * 2, 10),
                        frequency=data['count'],
                        suggested_category='skill',
                        suggested_priority=GoalPriority.HIGH if data['count'] > 5 else GoalPriority.MEDIUM
                    )
                else:
                    gap = DetectedGap(
                        gap_type='error_pattern',
                        description=f"{plugin} {action} failing frequently: {list(error_types)[0] if error_types else 'unknown error'}",
                        evidence=data['examples'][:3],
                        impact_estimate=min(data['count'], 10),
                        frequency=data['count'],
                        suggested_category='fix',
                        suggested_priority=GoalPriority.CRITICAL if data['count'] > 10 else GoalPriority.HIGH
                    )
                
                gaps.append(gap)
        
        return gaps
    
    def _scan_unhandled_requests(self, hours: int) -> List[DetectedGap]:
        """Scan for user requests we couldn't fulfill"""
        gaps = []
        
        # This would scan conversation logs, mentions, DMs
        # For now, placeholder - would integrate with memory system
        
        # Example pattern detection:
        # - User asks about "Solana" but we can't help
        # - User requests "Discord integration" but we don't have it
        
        return gaps
    
    def _scan_platform_gaps(self, hours: int) -> List[DetectedGap]:
        """Detect missing platform integrations users are asking for"""
        gaps = []
        
        # Scan recent observations for platform mentions
        # This is a simplified version - real implementation would
        # analyze memory/conversations
        
        return gaps
    
    def _scan_opportunities(self, hours: int) -> List[DetectedGap]:
        """Detect high-value opportunities"""
        gaps = []
        
        # High engagement patterns
        successful_actions = self.action_logger.get_recent_actions(
            outcome='success',
            limit=100
        )
        
        # Find what's working well - do more of it
        by_type: Dict[str, List] = {}
        for action in successful_actions:
            if action.timestamp < datetime.now() - timedelta(hours=hours):
                continue
            
            if action.action_type not in by_type:
                by_type[action.action_type] = []
            by_type[action.action_type].append(action)
        
        # High engagement actions suggest opportunity
        for action_type, actions in by_type.items():
            avg_engagement = sum(a.engagement_received for a in actions) / len(actions)
            
            if avg_engagement > 5:  # High engagement
                gap = DetectedGap(
                    gap_type='opportunity',
                    description=f"High engagement on {action_type} - opportunity to scale",
                    evidence=[f"Avg {avg_engagement:.1f} engagement per action"],
                    impact_estimate=8,
                    frequency=len(actions),
                    suggested_category='optimization',
                    suggested_priority=GoalPriority.MEDIUM
                )
                gaps.append(gap)
        
        return gaps
    
    def gap_to_goal(self, gap: DetectedGap) -> Optional[Goal]:
        """Convert a detected gap into a Goal object"""
        import uuid
        
        goal_id = f"{gap.suggested_category}-{str(uuid.uuid4())[:8]}"
        
        # Generate title and description based on gap type
        if gap.gap_type == 'missing_skill':
            title = f"Add {gap.description.split('lacks ')[1] if 'lacks ' in gap.description else 'Missing Capability'}"
            description = gap.description
        elif gap.gap_type == 'error_pattern':
            title = f"Fix: {gap.description[:50]}..."
            description = gap.description
        elif gap.gap_type == 'platform_gap':
            title = f"Integrate {gap.description}"
            description = gap.description
        elif gap.gap_type == 'opportunity':
            title = f"Scale: {gap.description}"
            description = gap.description
        else:
            title = gap.description[:60]
            description = gap.description
        
        # Generate proposed solution
        proposed_solution = self._generate_solution(gap)
        
        # Estimate effort
        effort = self._estimate_effort(gap)
        
        goal = Goal(
            id=goal_id,
            title=title,
            description=description,
            category=gap.suggested_category,
            priority=gap.suggested_priority,
            impact_score=gap.impact_estimate,
            effort_estimate=effort,
            confidence=min(gap.frequency / 10, 0.9),  # Higher confidence with more evidence
            trigger_type=gap.gap_type,
            evidence=gap.evidence,
            proposed_solution=proposed_solution
        )
        
        return goal
    
    def propose_goal(self, goal: Goal) -> bool:
        """Submit a goal to the goal manager"""
        from src.agentic.goal_manager import GoalStatus
        auto_approved = False
        if hasattr(self.goal_manager, 'should_auto_approve_goal') and self.goal_manager.should_auto_approve_goal(goal):
            goal.status = GoalStatus.APPROVED
            goal.approved_at = datetime.now()
            auto_approved = True
        else:
            goal.status = GoalStatus.PROPOSED
        
        success = self.goal_manager.add_goal(goal)
        
        if success:
            logger.info(f"🎯 Goal registered: {goal.title} (status: {goal.status.name}, priority: {goal.priority.name})")

            if auto_approved:
                try:
                    from plugin_manager import get_plugin_manager
                    plugin_manager = get_plugin_manager()
                    telegram = plugin_manager.get_plugin('telegram') if plugin_manager else None
                    if telegram and hasattr(telegram, 'notify_autonomous_activity'):
                        details = (
                            f"Auto-approved low-risk {goal.category} goal `{goal.id}`: "
                            f"{goal.title[:120]}"
                        )
                        telegram.notify_autonomous_activity('goal_auto_approved', details)
                except Exception as e:
                    logger.debug(f"Could not send auto-approved goal notification: {e}")

                try:
                    started_goal = self.goal_manager.start_next_safe_goal() if hasattr(self.goal_manager, 'start_next_safe_goal') else None
                    if started_goal and started_goal.id == goal.id:
                        logger.info(f"🚀 Auto-started safe goal: {goal.id}")
                        try:
                            from plugin_manager import get_plugin_manager
                            plugin_manager = get_plugin_manager()
                            telegram = plugin_manager.get_plugin('telegram') if plugin_manager else None
                            if telegram and hasattr(telegram, 'notify_autonomous_activity'):
                                telegram.notify_autonomous_activity(
                                    'goal_auto_started',
                                    f"Started safe low-risk goal `{goal.id}`: {goal.title[:120]}"
                                )
                        except Exception as e:
                            logger.debug(f"Could not send auto-start goal notification: {e}")
                except Exception as e:
                    logger.debug(f"Could not auto-start safe goal: {e}")
        
        return success
    
    def auto_detect_and_propose(self, hours: int = 24) -> List[Goal]:
        """
        Full pipeline: detect gaps → convert to goals → propose
        
        Returns:
            List of newly proposed goals
        """
        gaps = self.scan_for_gaps(hours)
        proposed = []
        
        for gap in gaps:
            goal = self.gap_to_goal(gap)
            if goal:
                if self.propose_goal(goal):
                    proposed.append(goal)
        
        return proposed
    
    def _generate_solution(self, gap: DetectedGap) -> str:
        """Generate a proposed solution based on gap type"""
        if gap.gap_type == 'missing_skill':
            return f"Create new skill module to handle: {gap.description}"
        elif gap.gap_type == 'error_pattern':
            return "Debug and fix the error pattern in existing code"
        elif gap.gap_type == 'platform_gap':
            return "Create new platform plugin with full integration"
        elif gap.gap_type == 'opportunity':
            return "Scale successful pattern with automation and monitoring"
        return "Implement solution to address detected gap"
    
    def _estimate_effort(self, gap: DetectedGap) -> str:
        """Estimate effort based on gap complexity"""
        if gap.gap_type == 'error_pattern':
            return 'hours'
        elif gap.gap_type == 'missing_skill':
            return 'days'
        elif gap.gap_type == 'platform_gap':
            return 'weeks'
        elif gap.gap_type == 'opportunity':
            return 'days'
        return 'days'
    
    def get_gap_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of current gaps"""
        gaps = self.scan_for_gaps(hours)
        
        by_type = {}
        for gap in gaps:
            by_type[gap.gap_type] = by_type.get(gap.gap_type, 0) + 1
        
        return {
            'total_gaps': len(gaps),
            'by_type': by_type,
            'high_impact': [g for g in gaps if g.impact_estimate >= 7],
            'frequent': [g for g in gaps if g.frequency >= 5]
        }


# Singleton
detector_instance: Optional[GoalDetector] = None


def get_goal_detector() -> GoalDetector:
    """Get or create goal detector singleton"""
    global detector_instance
    if detector_instance is None:
        detector_instance = GoalDetector()
    return detector_instance
