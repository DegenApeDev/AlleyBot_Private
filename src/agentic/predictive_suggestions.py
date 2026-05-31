"""
Predictive Suggestion Engine

Anticipates user needs based on patterns and proactively offers suggestions.
This is a key component of JARVIS-style proactive intelligence.

Analyzes:
- Time of day patterns
- Recurring tasks
- Goal progress
- Platform activity
- User behavior history

Generates:
- Proactive suggestions
- Opportunity alerts
- Task reminders
- Performance insights

Integration:
- Uses EpisodicMemory for historical patterns
- Uses GoalManager for goal tracking
- Uses WorldState for current context
- Feeds into DialogueManager for proactive messages
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Suggestion:
    """A proactive suggestion"""
    suggestion_type: str  # 'action', 'reminder', 'opportunity', 'insight'
    message: str
    confidence: float
    reasoning: str
    action_spec: Optional[Dict] = None
    priority: int = 5  # 1-10, higher = more important
    expires_at: Optional[datetime] = None


class PredictiveSuggestions:
    """
    Anticipates user needs based on patterns.
    
    JARVIS-like proactive assistance:
    - Predicts what user might need next
    - Offers suggestions before being asked
    - Detects opportunities
    - Reminds about goals and deadlines
    """
    
    def __init__(self, 
                 episodic_memory=None,
                 goal_manager=None,
                 world_state=None,
                 content_intelligence=None):
        """
        Initialize predictive suggestions engine.
        
        Args:
            episodic_memory: EpisodicMemory instance
            goal_manager: GoalStackManager instance
            world_state: WorldState instance
            content_intelligence: ContentIntelligence instance
        """
        self.episodes = episodic_memory
        self.goal_manager = goal_manager
        self.world_state = world_state
        self.content_intelligence = content_intelligence
        
        # Pattern tracking
        self.time_patterns = defaultdict(list)  # hour -> actions
        self.recurring_tasks = defaultdict(int)  # task -> frequency
        self.last_suggestion_time = None
        self.suggestion_cooldown = timedelta(minutes=30)  # Don't spam
    
    def predict_next_need(self, current_context: Dict = None) -> Optional[Suggestion]:
        """
        Predict what user might need next.
        
        Args:
            current_context: Current situation context
            
        Returns:
            Suggestion or None
        """
        # Check cooldown
        if self._is_in_cooldown():
            return None
        
        suggestions = []
        
        # Time-based patterns
        time_suggestion = self._predict_from_time_patterns()
        if time_suggestion:
            suggestions.append(time_suggestion)
        
        # Goal-based suggestions
        goal_suggestion = self._predict_from_goals()
        if goal_suggestion:
            suggestions.append(goal_suggestion)
        
        # Activity-based suggestions
        activity_suggestion = self._predict_from_activity()
        if activity_suggestion:
            suggestions.append(activity_suggestion)
        
        # Performance-based suggestions
        performance_suggestion = self._predict_from_performance()
        if performance_suggestion:
            suggestions.append(performance_suggestion)
        
        # Return highest priority suggestion
        if suggestions:
            best = max(suggestions, key=lambda s: (s.priority, s.confidence))
            self.last_suggestion_time = datetime.now()
            logger.info(f"💡 Predictive suggestion: {best.message[:50]}...")
            return best
        
        return None
    
    def generate_proactive_suggestions(self, limit: int = 3) -> List[Suggestion]:
        """
        Generate multiple proactive suggestions.
        
        Args:
            limit: Maximum number of suggestions
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Morning briefing
        if self._is_morning() and not self._briefing_sent_today():
            suggestions.append(self._generate_morning_briefing())
        
        # Goal progress check
        goal_suggestions = self._check_goal_progress()
        suggestions.extend(goal_suggestions)
        
        # Engagement opportunities
        engagement_suggestions = self._find_engagement_opportunities()
        suggestions.extend(engagement_suggestions)
        
        # Content opportunities
        content_suggestions = self._find_content_opportunities()
        suggestions.extend(content_suggestions)
        
        # Sort by priority and confidence
        suggestions.sort(key=lambda s: (s.priority, s.confidence), reverse=True)
        
        return suggestions[:limit]
    
    def detect_opportunities(self) -> List[Suggestion]:
        """
        Spot opportunities user might miss.
        
        Returns:
            List of opportunity suggestions
        """
        opportunities = []
        
        # Trending topics
        trending = self._detect_trending_topics()
        if trending:
            opportunities.append(trending)
        
        # High engagement windows
        timing = self._detect_optimal_timing()
        if timing:
            opportunities.append(timing)
        
        # Collaboration opportunities
        collab = self._detect_collaboration_opportunities()
        if collab:
            opportunities.append(collab)
        
        return opportunities
    
    def _predict_from_time_patterns(self) -> Optional[Suggestion]:
        """Predict based on time of day patterns"""
        current_hour = datetime.now().hour
        
        # Learn patterns from episodic memory
        if self.episodes:
            try:
                memories = self.episodes.get_all_memories()
                for memory in memories:
                    if memory.timestamp:
                        hour = memory.timestamp.hour
                        self.time_patterns[hour].append(memory.action)
            except Exception as e:
                logger.debug(f"Could not analyze time patterns: {e}")
        
        # Check if user typically does something at this hour
        if current_hour in self.time_patterns:
            actions = self.time_patterns[current_hour]
            if len(actions) >= 3:  # Pattern established
                most_common = max(set(actions), key=actions.count)
                
                return Suggestion(
                    suggestion_type='action',
                    message=f"It's {current_hour}:00 - you usually {most_common} around this time. Should I help with that?",
                    confidence=0.7,
                    reasoning=f"Historical pattern: {most_common} typically done at {current_hour}:00",
                    priority=6
                )
        
        return None
    
    def _predict_from_goals(self) -> Optional[Suggestion]:
        """Predict based on active goals"""
        if not self.goal_manager:
            return None
        
        try:
            # Get next goal
            next_goal = self.goal_manager.get_next_goal()
            if not next_goal:
                return None
            
            # Check if deadline approaching
            if next_goal.deadline:
                time_left = next_goal.deadline - datetime.now()
                
                if time_left < timedelta(hours=24):
                    return Suggestion(
                        suggestion_type='reminder',
                        message=f"Goal deadline approaching: '{next_goal.description}' due in {time_left.total_seconds()/3600:.1f} hours. Need help?",
                        confidence=0.9,
                        reasoning=f"Goal deadline in {time_left}",
                        priority=8,
                        expires_at=next_goal.deadline
                    )
                elif time_left < timedelta(days=3):
                    return Suggestion(
                        suggestion_type='reminder',
                        message=f"Upcoming goal: '{next_goal.description}' due in {time_left.days} days. Want to work on it?",
                        confidence=0.7,
                        reasoning=f"Goal deadline in {time_left.days} days",
                        priority=6
                    )
        
        except Exception as e:
            logger.debug(f"Could not predict from goals: {e}")
        
        return None
    
    def _predict_from_activity(self) -> Optional[Suggestion]:
        """Predict based on recent activity"""
        if not self.world_state:
            return None
        
        try:
            # Get recent events
            events = self.world_state.get_events(limit=50)
            
            # Check for inactivity
            if events:
                last_event = events[0]
                time_since = datetime.now() - datetime.fromisoformat(last_event.timestamp)
                
                if time_since > timedelta(hours=6):
                    return Suggestion(
                        suggestion_type='action',
                        message=f"It's been {time_since.total_seconds()/3600:.1f} hours since your last activity. Should I check for updates or create some content?",
                        confidence=0.6,
                        reasoning=f"Inactivity for {time_since}",
                        priority=5
                    )
        
        except Exception as e:
            logger.debug(f"Could not predict from activity: {e}")
        
        return None
    
    def _predict_from_performance(self) -> Optional[Suggestion]:
        """Predict based on performance trends"""
        if not self.content_intelligence:
            return None
        
        try:
            # Analyze recent performance
            insights = self.content_intelligence.analyze_content_performance(time_range_days=7)
            
            stats = insights.get('overall_stats', {})
            high_performers = stats.get('high_performers', 0)
            total = stats.get('total_content', 0)
            
            if total > 0:
                success_rate = high_performers / total
                
                # Performance trending up
                if success_rate > 0.7:
                    return Suggestion(
                        suggestion_type='insight',
                        message=f"Your content is performing well! {success_rate:.0%} success rate this week. Should I create more while engagement is high?",
                        confidence=0.8,
                        reasoning=f"High success rate: {success_rate:.0%}",
                        priority=7
                    )
                
                # Performance trending down
                elif success_rate < 0.3:
                    return Suggestion(
                        suggestion_type='insight',
                        message=f"Content performance is lower than usual ({success_rate:.0%}). Want me to analyze what's working and adjust strategy?",
                        confidence=0.8,
                        reasoning=f"Low success rate: {success_rate:.0%}",
                        priority=8
                    )
        
        except Exception as e:
            logger.debug(f"Could not predict from performance: {e}")
        
        return None
    
    def _generate_morning_briefing(self) -> Suggestion:
        """Generate morning briefing"""
        current_hour = datetime.now().hour
        greeting = "Good morning!" if current_hour < 12 else "Good afternoon!"
        
        briefing_parts = [greeting]
        
        # Add goal status
        if self.goal_manager:
            try:
                stats = self.goal_manager.get_stats()
                active = stats.get('active', 0)
                if active > 0:
                    briefing_parts.append(f"You have {active} active goals.")
            except Exception as e:
                logger.debug(f"Failed to get goal stats: {e}")
        
        # Add performance insight
        if self.content_intelligence:
            try:
                insights = self.content_intelligence.analyze_content_performance(time_range_days=1)
                stats = insights.get('overall_stats', {})
                total = stats.get('total_content', 0)
                if total > 0:
                    briefing_parts.append(f"Posted {total} times yesterday.")
            except Exception as e:
                logger.debug(f"Failed to analyze content performance: {e}")
        
        briefing_parts.append("What should we work on today?")
        
        return Suggestion(
            suggestion_type='insight',
            message=" ".join(briefing_parts),
            confidence=0.9,
            reasoning="Daily morning briefing",
            priority=7
        )
    
    def _check_goal_progress(self) -> List[Suggestion]:
        """Check progress on active goals"""
        suggestions = []
        
        if not self.goal_manager:
            return suggestions
        
        try:
            # Get active goals
            active_goals = self.goal_manager.get_active_goals()
            
            for goal in active_goals[:3]:  # Top 3 goals
                # Check if goal needs attention
                if goal.attempts > 5 and goal.status == 'active':
                    suggestions.append(Suggestion(
                        suggestion_type='reminder',
                        message=f"Goal '{goal.description}' has {goal.attempts} attempts. Need a different approach?",
                        confidence=0.7,
                        reasoning="Multiple attempts without completion",
                        priority=6
                    ))
        
        except Exception as e:
            logger.debug(f"Could not check goal progress: {e}")
        
        return suggestions
    
    def _find_engagement_opportunities(self) -> List[Suggestion]:
        """Find engagement opportunities"""
        suggestions = []
        
        # Check if it's a good time to engage
        current_hour = datetime.now().hour
        
        # Peak hours (afternoon/evening)
        if 15 <= current_hour <= 19:
            suggestions.append(Suggestion(
                suggestion_type='opportunity',
                message=f"It's {current_hour}:00 - peak engagement time! Should I check for trending posts to engage with?",
                confidence=0.7,
                reasoning="Peak engagement hours",
                priority=6
            ))
        
        return suggestions
    
    def _find_content_opportunities(self) -> List[Suggestion]:
        """Find content creation opportunities"""
        suggestions = []
        
        if not self.content_intelligence:
            return suggestions
        
        try:
            insights = self.content_intelligence.analyze_content_performance()
            best_topics = insights.get('best_topics', [])
            
            if best_topics:
                top_topic = best_topics[0]
                suggestions.append(Suggestion(
                    suggestion_type='opportunity',
                    message=f"'{top_topic}' is your best performing topic. Should I create more content about it?",
                    confidence=0.8,
                    reasoning=f"Top performing topic: {top_topic}",
                    priority=7
                ))
        
        except Exception as e:
            logger.debug(f"Could not find content opportunities: {e}")
        
        return suggestions
    
    def _detect_trending_topics(self) -> Optional[Suggestion]:
        """Detect trending topics to capitalize on"""
        # This would integrate with platform APIs to detect trends
        # For now, placeholder
        return None
    
    def _detect_optimal_timing(self) -> Optional[Suggestion]:
        """Detect optimal timing windows"""
        # Would use adaptive timing engine
        return None
    
    def _detect_collaboration_opportunities(self) -> Optional[Suggestion]:
        """Detect potential collaboration opportunities"""
        # Would analyze mentions, interactions, etc.
        return None
    
    def _is_in_cooldown(self) -> bool:
        """Check if we're in suggestion cooldown"""
        if not self.last_suggestion_time:
            return False
        
        time_since = datetime.now() - self.last_suggestion_time
        return time_since < self.suggestion_cooldown
    
    def _is_morning(self) -> bool:
        """Check if it's morning (6am-11am)"""
        hour = datetime.now().hour
        return 6 <= hour <= 11
    
    def _briefing_sent_today(self) -> bool:
        """Check if morning briefing already sent today"""
        # Would track in persistent storage
        # For now, simple check
        if not self.last_suggestion_time:
            return False
        
        today = datetime.now().date()
        last_date = self.last_suggestion_time.date()
        
        return today == last_date and self._is_morning()


def create_predictive_suggestions(episodic_memory=None, 
                                  goal_manager=None,
                                  world_state=None,
                                  content_intelligence=None):
    """Factory function to create predictive suggestions engine"""
    return PredictiveSuggestions(
        episodic_memory,
        goal_manager,
        world_state,
        content_intelligence
    )
