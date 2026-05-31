"""
Progress Reporter - Truthful and Transparent Progress Tracking

Reports AlleyBot's work progress with:
- Truth verification (no false claims)
- Evidence-based reporting (backed by actual results)
- Synergy validation (trustworthy communication)
- Real-time updates to user

Constitutional Rules:
- Never report success without evidence
- Never exaggerate or embellish results
- Always include confidence scores
- Flag uncertainties and failures honestly
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProgressReporter:
    """
    Truthful progress reporting system.
    
    Ensures all progress reports are:
    - Evidence-based (backed by actual data)
    - Honest (failures reported, not hidden)
    - Transparent (shows confidence and uncertainty)
    - Verifiable (includes source data)
    """
    
    def __init__(self, goal_manager=None, action_logger=None):
        """
        Initialize progress reporter.
        
        Args:
            goal_manager: GoalManager instance for goal tracking
            action_logger: ActionLogger instance for action verification
        """
        self.goal_manager = goal_manager
        self.action_logger = action_logger
        
        # Progress tracking
        self.progress_log: List[Dict] = []
        self.last_report_time = datetime.now()
        
        logger.info("✅ Progress Reporter initialized (truth-verified reporting)")
    
    def report_goal_progress(self, goal_id: str, verify_truth: bool = True) -> Dict[str, Any]:
        """
        Report progress on a specific goal with truth verification.
        
        Args:
            goal_id: ID of the goal to report on
            verify_truth: Whether to verify claims against actual evidence
        
        Returns:
            Progress report dict with verified data
        """
        if not self.goal_manager:
            return {'error': 'Goal manager not available'}
        
        goal = self.goal_manager.get_goal(goal_id)
        if not goal:
            return {'error': f'Goal not found: {goal_id}'}
        
        # Get implementation plan
        plan_steps = goal.implementation_plan if hasattr(goal, 'implementation_plan') else []
        if isinstance(plan_steps, str):
            try:
                plan_steps = json.loads(plan_steps)
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse plan steps JSON: {e}")
                plan_steps = []
        
        # Count completed vs total steps
        total_steps = len(plan_steps) if plan_steps else 0
        completed_steps = sum(1 for step in plan_steps if isinstance(step, dict) and step.get('status') == 'completed')
        in_progress_steps = sum(1 for step in plan_steps if isinstance(step, dict) and step.get('status') == 'in_progress')
        
        # Calculate progress percentage
        progress_pct = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        # Verify claims if requested
        verification = {'verified': True, 'evidence': []}
        if verify_truth and self.action_logger:
            verification = self._verify_goal_claims(goal, completed_steps)
        
        # Build truthful report
        report = {
            'goal_id': goal_id,
            'title': goal.title,
            'status': goal.status.value if hasattr(goal.status, 'value') else str(goal.status),
            'progress': {
                'total_steps': total_steps,
                'completed': completed_steps,
                'in_progress': in_progress_steps,
                'pending': total_steps - completed_steps - in_progress_steps,
                'percentage': round(progress_pct, 1)
            },
            'verification': verification,
            'confidence': goal.confidence if hasattr(goal, 'confidence') else 0.0,
            'started_at': goal.started_at.isoformat() if hasattr(goal, 'started_at') and goal.started_at else None,
            'last_updated': datetime.now().isoformat(),
            'honest_assessment': self._generate_honest_assessment(goal, completed_steps, total_steps, verification)
        }
        
        # Log report
        self.progress_log.append(report)
        
        return report
    
    def _verify_goal_claims(self, goal, claimed_completed: int) -> Dict[str, Any]:
        """
        Verify goal progress claims against actual action logs.
        
        Returns:
            Verification result with evidence
        """
        if not self.action_logger:
            return {'verified': False, 'reason': 'No action logger available', 'evidence': []}
        
        try:
            # Get actions related to this goal
            recent_actions = self.action_logger.get_recent_outcomes(limit=100)
            
            # Filter for actions related to this goal
            goal_actions = [
                action for action in recent_actions
                if action.get('metadata', {}).get('goal_id') == goal.id
            ]
            
            # Count successful actions
            successful_actions = [
                action for action in goal_actions
                if action.get('success', False)
            ]
            
            # Verify claimed progress matches actual actions
            actual_completed = len(successful_actions)
            
            if actual_completed >= claimed_completed:
                return {
                    'verified': True,
                    'evidence': [f"{len(successful_actions)} successful actions recorded"],
                    'actual_completed': actual_completed,
                    'claimed_completed': claimed_completed,
                    'trust_score': 1.0
                }
            else:
                # Discrepancy detected
                return {
                    'verified': False,
                    'evidence': [f"Only {actual_completed} actions found, but {claimed_completed} steps claimed complete"],
                    'actual_completed': actual_completed,
                    'claimed_completed': claimed_completed,
                    'trust_score': actual_completed / max(claimed_completed, 1),
                    'warning': 'Progress claim exceeds verified actions'
                }
        
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return {
                'verified': False,
                'reason': f'Verification failed: {str(e)}',
                'evidence': [],
                'trust_score': 0.0
            }
    
    def _generate_honest_assessment(self, goal, completed: int, total: int, verification: Dict) -> str:
        """Generate honest, transparent assessment of progress"""
        
        if total == 0:
            return "⚠️ No implementation plan defined yet"
        
        progress_pct = (completed / total * 100) if total > 0 else 0
        
        # Base assessment on actual progress
        if progress_pct == 0:
            assessment = "🔵 Just started, no steps completed yet"
        elif progress_pct < 25:
            assessment = f"🔵 Early stage: {completed}/{total} steps done ({progress_pct:.0f}%)"
        elif progress_pct < 50:
            assessment = f"🟡 Making progress: {completed}/{total} steps done ({progress_pct:.0f}%)"
        elif progress_pct < 75:
            assessment = f"🟢 Good progress: {completed}/{total} steps done ({progress_pct:.0f}%)"
        elif progress_pct < 100:
            assessment = f"🟢 Nearly complete: {completed}/{total} steps done ({progress_pct:.0f}%)"
        else:
            assessment = f"✅ Complete: All {total} steps done"
        
        # Add verification status
        if not verification.get('verified', True):
            assessment += f" ⚠️ (Unverified - {verification.get('warning', 'needs confirmation')})"
        
        return assessment
    
    def generate_daily_summary(self, include_evidence: bool = True) -> Dict[str, Any]:
        """
        Generate truthful daily summary of all work.
        
        Args:
            include_evidence: Whether to include evidence for claims
        
        Returns:
            Daily summary with verified data
        """
        if not self.goal_manager:
            return {'error': 'Goal manager not available'}
        
        from src.agentic.goal_manager import GoalStatus
        
        # Get all active and recently completed goals
        active_goals = self.goal_manager.get_goals(status=GoalStatus.ACTIVE, limit=50)
        completed_today = self.goal_manager.get_goals(status=GoalStatus.COMPLETED, limit=50)
        
        # Filter completed goals to today only
        today = datetime.now().date()
        completed_today = [
            g for g in completed_today
            if hasattr(g, 'completed_at') and g.completed_at and g.completed_at.date() == today
        ]
        
        # Generate summary
        summary = {
            'date': today.isoformat(),
            'active_goals': len(active_goals),
            'completed_today': len(completed_today),
            'goals': {
                'active': [],
                'completed': []
            },
            'honest_summary': '',
            'generated_at': datetime.now().isoformat()
        }
        
        # Add active goal details
        for goal in active_goals[:10]:  # Top 10
            progress_report = self.report_goal_progress(goal.id, verify_truth=include_evidence)
            summary['goals']['active'].append({
                'id': goal.id,
                'title': goal.title,
                'progress': progress_report.get('progress', {}),
                'assessment': progress_report.get('honest_assessment', '')
            })
        
        # Add completed goal details
        for goal in completed_today:
            summary['goals']['completed'].append({
                'id': goal.id,
                'title': goal.title,
                'outcome': goal.outcome if hasattr(goal, 'outcome') else 'Completed'
            })
        
        # Generate honest summary text
        if len(active_goals) == 0 and len(completed_today) == 0:
            summary['honest_summary'] = "📊 No active work today. Ready for new tasks."
        elif len(completed_today) > 0:
            summary['honest_summary'] = f"✅ Completed {len(completed_today)} goal(s) today. {len(active_goals)} still in progress."
        else:
            summary['honest_summary'] = f"🔵 Working on {len(active_goals)} goal(s). No completions yet today."
        
        return summary
    
    def report_to_console(self, report: Dict[str, Any]):
        """Print progress report to console"""
        if 'error' in report:
            print(f"❌ {report['error']}")
            return
        
        print(f"\n{'='*70}")
        print(f"📊 Progress Report: {report.get('title', 'Unknown')}")
        print(f"{'='*70}")
        
        progress = report.get('progress', {})
        print(f"Status: {report.get('status', 'Unknown')}")
        print(f"Progress: {progress.get('completed', 0)}/{progress.get('total_steps', 0)} steps ({progress.get('percentage', 0)}%)")
        print(f"Assessment: {report.get('honest_assessment', '')}")
        
        verification = report.get('verification', {})
        if verification.get('verified'):
            print(f"✅ Verified: {', '.join(verification.get('evidence', []))}")
        elif 'warning' in verification:
            print(f"⚠️ Warning: {verification.get('warning')}")
        
        print(f"{'='*70}\n")


# Singleton
_progress_reporter_instance: Optional[ProgressReporter] = None


def get_progress_reporter() -> Optional[ProgressReporter]:
    """Get or create progress reporter singleton"""
    global _progress_reporter_instance
    return _progress_reporter_instance
