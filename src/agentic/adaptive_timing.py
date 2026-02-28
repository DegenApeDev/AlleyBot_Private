"""
Adaptive Timing Engine

Learns optimal timing for each action type and platform based on historical performance.
Replaces rigid golden window with learned patterns.

This system analyzes when actions perform best and provides data-driven timing recommendations.
It continuously learns from outcomes and adapts to changing patterns.

Key Features:
- Learns optimal timing from historical performance
- Per-platform, per-action-type optimization
- Replaces rigid rules with adaptive patterns
- Continuous learning and improvement

Integration:
- Uses EpisodicMemory for historical data
- Uses WorldState for event timing
- Integrates with ActionRouter for timing decisions
- Feeds into ContentIntelligence
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class AdaptiveTimingEngine:
    """
    Learns optimal timing for each action type and platform.
    
    Analyzes:
    - Historical action performance by hour
    - Platform-specific timing patterns
    - Action-type specific patterns
    - Day-of-week patterns
    
    Provides:
    - Should act now? (yes/no with confidence)
    - Best hours for action type
    - Performance score for current time
    - Reasoning for decision
    """
    
    def __init__(self, episodic_memory=None, world_state=None):
        self.episodes = episodic_memory
        self.world_state = world_state
        
        # Performance thresholds
        self.good_performance_threshold = 0.6  # 60% success rate
        self.min_samples_per_hour = 3  # Minimum data points to trust
    
    def get_optimal_timing(self, action_type: str, platform: str) -> Dict[str, Any]:
        """
        Calculate optimal timing based on historical performance.
        
        Args:
            action_type: Type of action (e.g., 'create_post', 'engage')
            platform: Platform name (e.g., 'moltx', 'telegram')
            
        Returns:
            Timing recommendation with confidence
        """
        try:
            # Get historical performance
            hourly_performance = self._analyze_hourly_performance(action_type, platform)
            
            if not hourly_performance:
                return self._default_timing_response()
            
            # Calculate current hour performance
            current_hour = datetime.now().hour
            current_performance = hourly_performance.get(current_hour, {})
            current_score = current_performance.get('success_rate', 0.5)
            sample_count = current_performance.get('sample_count', 0)
            
            # Find best hours
            best_hours = self._get_best_hours(hourly_performance)
            worst_hours = self._get_worst_hours(hourly_performance)
            
            # Determine if should act now
            should_act = current_score >= self.good_performance_threshold
            
            # Adjust confidence based on sample size
            confidence = current_score
            if sample_count < self.min_samples_per_hour:
                confidence *= 0.7  # Lower confidence with limited data
            
            # Generate reasoning
            if current_hour in best_hours:
                reason = f"Optimal time - {current_score:.0%} success rate at {current_hour}:00 ({sample_count} samples)"
            elif current_hour in worst_hours:
                reason = f"Suboptimal time - {current_score:.0%} success rate at {current_hour}:00 ({sample_count} samples)"
            else:
                reason = f"Neutral time - {current_score:.0%} success rate at {current_hour}:00 ({sample_count} samples)"
            
            return {
                'should_act_now': should_act,
                'confidence': confidence,
                'current_hour': current_hour,
                'current_hour_score': current_score,
                'best_hours': best_hours,
                'worst_hours': worst_hours,
                'reason': reason,
                'sample_count': sample_count
            }
        
        except Exception as e:
            logger.error(f"Optimal timing calculation failed: {e}")
            return self._default_timing_response()
    
    def should_act_now(self, action_type: str, platform: str) -> bool:
        """
        Simple yes/no decision on whether to act now.
        
        Args:
            action_type: Type of action
            platform: Platform name
            
        Returns:
            True if good time to act, False otherwise
        """
        timing = self.get_optimal_timing(action_type, platform)
        return timing['should_act_now']
    
    def get_best_time_today(self, action_type: str, platform: str) -> Optional[int]:
        """
        Get the best hour to perform action today.
        
        Args:
            action_type: Type of action
            platform: Platform name
            
        Returns:
            Best hour (0-23) or None
        """
        timing = self.get_optimal_timing(action_type, platform)
        best_hours = timing.get('best_hours', [])
        
        if not best_hours:
            return None
        
        # Return first best hour that hasn't passed today
        current_hour = datetime.now().hour
        for hour in best_hours:
            if hour > current_hour:
                return hour
        
        # All best hours have passed, return first one (for tomorrow)
        return best_hours[0]
    
    def _analyze_hourly_performance(self, action_type: str, platform: str) -> Dict[int, Dict]:
        """
        Analyze performance by hour for specific action type and platform.
        
        Returns:
            Dict mapping hour (0-23) to performance metrics
        """
        hourly_data = defaultdict(lambda: {'successes': 0, 'failures': 0, 'total': 0})
        
        # Get data from episodic memory
        if self.episodes:
            try:
                all_memories = self.episodes.get_all_memories()
                
                for memory in all_memories:
                    # Filter by action type and platform
                    if action_type.lower() not in memory.action.lower():
                        continue
                    if platform.lower() not in memory.context.lower():
                        continue
                    
                    # Extract hour
                    hour = memory.timestamp.hour if memory.timestamp else 0
                    
                    # Determine success/failure
                    is_success = memory.emotional_valence > 0
                    
                    hourly_data[hour]['total'] += 1
                    if is_success:
                        hourly_data[hour]['successes'] += 1
                    else:
                        hourly_data[hour]['failures'] += 1
            
            except Exception as e:
                logger.debug(f"Could not analyze episodic memory: {e}")
        
        # Get data from world state
        if self.world_state:
            try:
                events = self.world_state.get_events(limit=1000)
                
                for event in events:
                    # Filter by action type and platform
                    if action_type.lower() not in event.event_type.lower():
                        continue
                    
                    event_platform = event.metadata.get('platform', '')
                    if platform.lower() not in event_platform.lower():
                        continue
                    
                    # Extract hour
                    if event.timestamp:
                        hour = datetime.fromisoformat(event.timestamp).hour
                    else:
                        continue
                    
                    # Determine success (based on engagement or outcome)
                    engagement = event.metadata.get('engagement', {})
                    likes = engagement.get('likes', 0)
                    replies = engagement.get('replies', 0)
                    is_success = (likes + replies) > 0
                    
                    hourly_data[hour]['total'] += 1
                    if is_success:
                        hourly_data[hour]['successes'] += 1
                    else:
                        hourly_data[hour]['failures'] += 1
            
            except Exception as e:
                logger.debug(f"Could not analyze world state: {e}")
        
        # Calculate success rates
        hourly_performance = {}
        for hour, data in hourly_data.items():
            total = data['total']
            if total > 0:
                success_rate = data['successes'] / total
                hourly_performance[hour] = {
                    'success_rate': success_rate,
                    'sample_count': total,
                    'successes': data['successes'],
                    'failures': data['failures']
                }
        
        return hourly_performance
    
    def _get_best_hours(self, hourly_performance: Dict[int, Dict], top_n: int = 3) -> List[int]:
        """Get top N best performing hours"""
        # Filter hours with enough samples
        valid_hours = {
            hour: data for hour, data in hourly_performance.items()
            if data['sample_count'] >= self.min_samples_per_hour
        }
        
        if not valid_hours:
            # Not enough data, return default best hours
            return [15, 16, 17]  # 3-5pm default
        
        # Sort by success rate
        sorted_hours = sorted(
            valid_hours.items(),
            key=lambda x: x[1]['success_rate'],
            reverse=True
        )
        
        return [hour for hour, _ in sorted_hours[:top_n]]
    
    def _get_worst_hours(self, hourly_performance: Dict[int, Dict], bottom_n: int = 3) -> List[int]:
        """Get bottom N worst performing hours"""
        # Filter hours with enough samples
        valid_hours = {
            hour: data for hour, data in hourly_performance.items()
            if data['sample_count'] >= self.min_samples_per_hour
        }
        
        if not valid_hours:
            # Not enough data, return default worst hours
            return [2, 3, 4]  # 2-4am default
        
        # Sort by success rate (ascending)
        sorted_hours = sorted(
            valid_hours.items(),
            key=lambda x: x[1]['success_rate']
        )
        
        return [hour for hour, _ in sorted_hours[:bottom_n]]
    
    def _default_timing_response(self) -> Dict[str, Any]:
        """Default response when no data available"""
        current_hour = datetime.now().hour
        
        # Default best hours (afternoon/evening)
        default_best = [15, 16, 17, 18, 19]
        
        # Default worst hours (late night/early morning)
        default_worst = [2, 3, 4, 5]
        
        # Simple heuristic: good if in default best hours
        should_act = current_hour in default_best
        
        return {
            'should_act_now': should_act,
            'confidence': 0.5,
            'current_hour': current_hour,
            'current_hour_score': 0.5,
            'best_hours': default_best,
            'worst_hours': default_worst,
            'reason': 'No historical data available, using default timing heuristics',
            'sample_count': 0
        }
    
    def get_timing_report(self, action_type: str, platform: str) -> str:
        """
        Generate human-readable timing report.
        
        Args:
            action_type: Type of action
            platform: Platform name
            
        Returns:
            Formatted report string
        """
        timing = self.get_optimal_timing(action_type, platform)
        
        report = f"⏰ Timing Report: {action_type} on {platform}\n\n"
        report += f"Current Time: {timing['current_hour']}:00\n"
        report += f"Current Score: {timing['current_hour_score']:.0%}\n"
        report += f"Recommendation: {'✅ Good time' if timing['should_act_now'] else '⏳ Wait for better time'}\n"
        report += f"Confidence: {timing['confidence']:.0%}\n\n"
        report += f"Best Hours: {', '.join(f'{h}:00' for h in timing['best_hours'])}\n"
        report += f"Worst Hours: {', '.join(f'{h}:00' for h in timing['worst_hours'])}\n\n"
        report += f"Reasoning: {timing['reason']}\n"
        
        if timing['sample_count'] > 0:
            report += f"\nData Points: {timing['sample_count']} historical actions analyzed"
        else:
            report += f"\nData Points: No historical data, using defaults"
        
        return report


def create_adaptive_timing_engine(episodic_memory=None, world_state=None):
    """Factory function to create adaptive timing engine"""
    return AdaptiveTimingEngine(episodic_memory, world_state)
