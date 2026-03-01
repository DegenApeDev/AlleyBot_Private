"""
Outcome Learner
Tracks results of decisions and actions to learn what works and continuously improve
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class OutcomeLearner:
    """
    Learns from outcomes to improve future decisions
    """
    
    def __init__(self, core):
        """
        Initialize outcome learner
        
        Args:
            core: AlleyBotCore instance for memory access
        """
        self.core = core
        self.outcomes_file = Path('memory/outcomes.json')
        self.outcomes_file.parent.mkdir(exist_ok=True)
        
        # Load existing outcomes
        self.outcomes = self._load_outcomes()
        
        # Performance tracking
        self.performance_by_action = defaultdict(lambda: {'success': 0, 'failure': 0, 'total': 0})
        self.performance_by_platform = defaultdict(lambda: {'success': 0, 'failure': 0, 'total': 0})
        self.performance_by_topic = defaultdict(lambda: {'success': 0, 'failure': 0, 'total': 0})
        
        # Rebuild performance stats from outcomes
        self._rebuild_performance_stats()
        
        logger.info("📊 OutcomeLearner initialized")
    
    def _load_outcomes(self) -> List[Dict[str, Any]]:
        """Load outcomes from file"""
        if self.outcomes_file.exists():
            try:
                with open(self.outcomes_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load outcomes: {e}")
        return []
    
    def _save_outcomes(self):
        """Save outcomes to file"""
        try:
            with open(self.outcomes_file, 'w') as f:
                json.dump(self.outcomes[-1000:], f, indent=2)  # Keep last 1000
        except Exception as e:
            logger.error(f"Failed to save outcomes: {e}")
    
    def _rebuild_performance_stats(self):
        """Rebuild performance statistics from stored outcomes"""
        for outcome in self.outcomes:
            action_type = outcome.get('action_type', 'unknown')
            platform = outcome.get('platform', 'unknown')
            success = outcome.get('success', False)
            
            # Update action stats
            self.performance_by_action[action_type]['total'] += 1
            if success:
                self.performance_by_action[action_type]['success'] += 1
            else:
                self.performance_by_action[action_type]['failure'] += 1
            
            # Update platform stats
            self.performance_by_platform[platform]['total'] += 1
            if success:
                self.performance_by_platform[platform]['success'] += 1
            else:
                self.performance_by_platform[platform]['failure'] += 1
            
            # Update topic stats
            topic = outcome.get('topic', 'unknown')
            if topic != 'unknown':
                self.performance_by_topic[topic]['total'] += 1
                if success:
                    self.performance_by_topic[topic]['success'] += 1
                else:
                    self.performance_by_topic[topic]['failure'] += 1
    
    def record_outcome(self, action_type: str, platform: str, success: bool, 
                      data: Optional[Dict[str, Any]] = None) -> None:
        """
        Record the outcome of an action
        
        Args:
            action_type: Type of action (e.g., 'post', 'reply', 'trade', 'quote')
            platform: Platform where action occurred (e.g., 'moltx', 'clawbr', 'solana')
            success: Whether the action was successful
            data: Additional data about the outcome (engagement, profit, etc.)
        """
        outcome = {
            'action_type': action_type,
            'platform': platform,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        
        # Extract topic if available
        topic = None
        if data:
            content = data.get('content', '')
            if content:
                # Extract first hashtag as topic
                words = content.split()
                hashtags = [w[1:].lower() for w in words if w.startswith('#')]
                if hashtags:
                    topic = hashtags[0]
                    outcome['topic'] = topic
        
        # Store outcome
        self.outcomes.append(outcome)
        
        # Update performance stats
        self.performance_by_action[action_type]['total'] += 1
        if success:
            self.performance_by_action[action_type]['success'] += 1
        else:
            self.performance_by_action[action_type]['failure'] += 1
        
        self.performance_by_platform[platform]['total'] += 1
        if success:
            self.performance_by_platform[platform]['success'] += 1
        else:
            self.performance_by_platform[platform]['failure'] += 1
        
        if topic:
            self.performance_by_topic[topic]['total'] += 1
            if success:
                self.performance_by_topic[topic]['success'] += 1
            else:
                self.performance_by_topic[topic]['failure'] += 1
        
        # Save periodically
        if len(self.outcomes) % 10 == 0:
            self._save_outcomes()
        
        logger.info(f"📊 Recorded outcome: {action_type} on {platform} - {'✅' if success else '❌'}")
    
    def get_success_rate(self, action_type: Optional[str] = None, 
                        platform: Optional[str] = None) -> float:
        """
        Get success rate for specific action type or platform
        
        Args:
            action_type: Optional action type filter
            platform: Optional platform filter
        
        Returns:
            Success rate (0-1)
        """
        if action_type:
            stats = self.performance_by_action.get(action_type, {'success': 0, 'total': 0})
        elif platform:
            stats = self.performance_by_platform.get(platform, {'success': 0, 'total': 0})
        else:
            # Overall success rate
            total_success = sum(s['success'] for s in self.performance_by_action.values())
            total_actions = sum(s['total'] for s in self.performance_by_action.values())
            return total_success / total_actions if total_actions > 0 else 0.5
        
        return stats['success'] / stats['total'] if stats['total'] > 0 else 0.5
    
    def get_best_performing_actions(self, min_samples: int = 5) -> List[Dict[str, Any]]:
        """
        Get best performing action types
        
        Args:
            min_samples: Minimum number of samples required
        
        Returns:
            List of action types sorted by success rate
        """
        best = []
        
        for action_type, stats in self.performance_by_action.items():
            if stats['total'] >= min_samples:
                success_rate = stats['success'] / stats['total']
                best.append({
                    'action_type': action_type,
                    'success_rate': success_rate,
                    'total_attempts': stats['total'],
                    'successes': stats['success']
                })
        
        best.sort(key=lambda x: x['success_rate'], reverse=True)
        return best
    
    def get_best_performing_platforms(self, min_samples: int = 5) -> List[Dict[str, Any]]:
        """Get best performing platforms"""
        best = []
        
        for platform, stats in self.performance_by_platform.items():
            if stats['total'] >= min_samples:
                success_rate = stats['success'] / stats['total']
                best.append({
                    'platform': platform,
                    'success_rate': success_rate,
                    'total_attempts': stats['total'],
                    'successes': stats['success']
                })
        
        best.sort(key=lambda x: x['success_rate'], reverse=True)
        return best
    
    def get_best_performing_topics(self, min_samples: int = 3) -> List[Dict[str, Any]]:
        """Get best performing topics"""
        best = []
        
        for topic, stats in self.performance_by_topic.items():
            if stats['total'] >= min_samples:
                success_rate = stats['success'] / stats['total']
                best.append({
                    'topic': topic,
                    'success_rate': success_rate,
                    'total_attempts': stats['total'],
                    'successes': stats['success']
                })
        
        best.sort(key=lambda x: x['success_rate'], reverse=True)
        return best
    
    def should_try_action(self, action_type: str, platform: str) -> bool:
        """
        Determine if an action should be attempted based on historical performance
        
        Args:
            action_type: Type of action
            platform: Platform for action
        
        Returns:
            True if should try, False if historically unsuccessful
        """
        # Get success rates
        action_success = self.get_success_rate(action_type=action_type)
        platform_success = self.get_success_rate(platform=platform)
        
        # If either has very low success rate, reconsider
        if action_success < 0.3 or platform_success < 0.3:
            logger.warning(f"⚠️ Low success rate for {action_type} on {platform}")
            return False
        
        return True
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """
        Get insights from learning
        
        Returns:
            Dict with learning insights and recommendations
        """
        insights = {
            'total_outcomes': len(self.outcomes),
            'overall_success_rate': self.get_success_rate(),
            'best_actions': self.get_best_performing_actions(min_samples=3),
            'best_platforms': self.get_best_performing_platforms(min_samples=3),
            'best_topics': self.get_best_performing_topics(min_samples=2),
            'recommendations': []
        }
        
        # Generate recommendations
        if insights['best_actions']:
            best_action = insights['best_actions'][0]
            insights['recommendations'].append(
                f"Focus on {best_action['action_type']} actions (success rate: {best_action['success_rate']:.1%})"
            )
        
        if insights['best_platforms']:
            best_platform = insights['best_platforms'][0]
            insights['recommendations'].append(
                f"Prioritize {best_platform['platform']} platform (success rate: {best_platform['success_rate']:.1%})"
            )
        
        if insights['best_topics']:
            best_topic = insights['best_topics'][0]
            insights['recommendations'].append(
                f"Create more content about #{best_topic['topic']} (success rate: {best_topic['success_rate']:.1%})"
            )
        
        return insights
    
    def get_learning_summary(self) -> str:
        """Get human-readable learning summary"""
        insights = self.get_learning_insights()
        
        summary = f"📊 Outcome Learning Summary:\n\n"
        summary += f"Total Outcomes Tracked: {insights['total_outcomes']}\n"
        summary += f"Overall Success Rate: {insights['overall_success_rate']:.1%}\n\n"
        
        if insights['best_actions']:
            summary += "🏆 Best Performing Actions:\n"
            for action in insights['best_actions'][:3]:
                summary += f"  • {action['action_type']}: {action['success_rate']:.1%} ({action['successes']}/{action['total_attempts']})\n"
            summary += "\n"
        
        if insights['best_platforms']:
            summary += "🌟 Best Performing Platforms:\n"
            for platform in insights['best_platforms'][:3]:
                summary += f"  • {platform['platform']}: {platform['success_rate']:.1%} ({platform['successes']}/{platform['total_attempts']})\n"
            summary += "\n"
        
        if insights['best_topics']:
            summary += "🔥 Best Performing Topics:\n"
            for topic in insights['best_topics'][:3]:
                summary += f"  • #{topic['topic']}: {topic['success_rate']:.1%} ({topic['successes']}/{topic['total_attempts']})\n"
            summary += "\n"
        
        if insights['recommendations']:
            summary += "💡 Recommendations:\n"
            for rec in insights['recommendations']:
                summary += f"  • {rec}\n"
        
        return summary


def get_outcome_learner(core) -> OutcomeLearner:
    """Get or create OutcomeLearner singleton"""
    if not hasattr(get_outcome_learner, '_instance'):
        get_outcome_learner._instance = OutcomeLearner(core)
    return get_outcome_learner._instance
