"""
Contextual Awareness System

Maintains awareness of current context and user state for intelligent interaction.
This enables JARVIS-style situational understanding.

Tracks:
- User's current task/focus
- Time and location context
- Platform states
- Active goals
- Recent events
- User mood/state
- Interruption appropriateness

Integration:
- Uses WorldState for current situation
- Uses ConversationalMemory for user state
- Uses GoalManager for active goals
- Feeds into PredictiveSuggestions for timing
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class UserState(Enum):
    """User's current state"""
    AVAILABLE = "available"
    BUSY = "busy"
    FOCUSED = "focused"
    IDLE = "idle"
    AWAY = "away"
    UNKNOWN = "unknown"


class UrgencyLevel(Enum):
    """Urgency levels for interruptions"""
    CRITICAL = "critical"  # Always interrupt
    HIGH = "high"  # Interrupt if not focused
    MEDIUM = "medium"  # Wait for break
    LOW = "low"  # Only when idle
    NONE = "none"  # Never interrupt


@dataclass
class ContextSnapshot:
    """Snapshot of current context"""
    timestamp: datetime
    user_state: UserState
    current_task: Optional[str]
    active_goals: List[str]
    recent_activity: List[str]
    platform_states: Dict[str, Any]
    time_context: Dict[str, Any]
    can_interrupt: bool
    reasoning: str


class ContextualAwareness:
    """
    Maintains awareness of current context.
    
    JARVIS-like situational understanding:
    - Knows what user is doing
    - Understands when to help vs stay quiet
    - Tracks multiple context dimensions
    - Assesses interruption appropriateness
    """
    
    def __init__(self,
                 world_state=None,
                 conversational_memory=None,
                 goal_manager=None):
        """
        Initialize contextual awareness system.
        
        Args:
            world_state: WorldState instance
            conversational_memory: ConversationalMemory instance
            goal_manager: GoalStackManager instance
        """
        self.world_state = world_state
        self.conversation = conversational_memory
        self.goal_manager = goal_manager
        
        # Context tracking
        self.current_user_state = UserState.UNKNOWN
        self.current_task = None
        self.last_activity_time = None
        self.focus_start_time = None
        self.activity_history = []
    
    def get_current_context(self) -> ContextSnapshot:
        """
        Get full situational awareness.
        
        Returns:
            Complete context snapshot
        """
        # Detect user state
        user_state = self.detect_user_state()
        
        # Get current task
        current_task = self._infer_current_task()
        
        # Get active goals
        active_goals = self._get_active_goal_descriptions()
        
        # Get recent activity
        recent_activity = self._get_recent_activity()
        
        # Get platform states
        platform_states = self._get_platform_states()
        
        # Get time context
        time_context = self._get_time_context()
        
        # Assess if can interrupt
        can_interrupt, reasoning = self._can_interrupt(user_state)
        
        return ContextSnapshot(
            timestamp=datetime.now(),
            user_state=user_state,
            current_task=current_task,
            active_goals=active_goals,
            recent_activity=recent_activity,
            platform_states=platform_states,
            time_context=time_context,
            can_interrupt=can_interrupt,
            reasoning=reasoning
        )
    
    def detect_user_state(self) -> UserState:
        """
        Detect user's current state.
        
        Returns:
            UserState enum
        """
        # Check last activity time
        if self.last_activity_time:
            time_since = datetime.now() - self.last_activity_time
            
            # Away if no activity for 30+ minutes
            if time_since > timedelta(minutes=30):
                return UserState.AWAY
            
            # Idle if no activity for 10+ minutes
            if time_since > timedelta(minutes=10):
                return UserState.IDLE
        
        # Check if in focused work session
        if self.focus_start_time:
            focus_duration = datetime.now() - self.focus_start_time
            
            # Focused if working for 5+ minutes
            if focus_duration > timedelta(minutes=5):
                return UserState.FOCUSED
        
        # Check conversation activity
        if self.conversation:
            summary = self.conversation.get_conversation_summary()
            if summary.get('turn_count', 0) > 0:
                # Active conversation = busy
                return UserState.BUSY
        
        # Default to available
        return UserState.AVAILABLE
    
    def assess_urgency(self, task: Dict) -> UrgencyLevel:
        """
        Determine urgency of a task/notification.
        
        Args:
            task: Task specification
            
        Returns:
            UrgencyLevel enum
        """
        task_type = task.get('type', '')
        
        # Critical: Errors, security issues
        if task_type in ['error', 'security', 'critical']:
            return UrgencyLevel.CRITICAL
        
        # High: Deadlines, important opportunities
        if task_type in ['deadline', 'opportunity']:
            deadline = task.get('deadline')
            if deadline:
                time_left = deadline - datetime.now()
                if time_left < timedelta(hours=1):
                    return UrgencyLevel.CRITICAL
                if time_left < timedelta(hours=6):
                    return UrgencyLevel.HIGH
        
        # Medium: Regular tasks, suggestions
        if task_type in ['suggestion', 'reminder']:
            return UrgencyLevel.MEDIUM
        
        # Low: Insights, updates
        if task_type in ['insight', 'update']:
            return UrgencyLevel.LOW
        
        return UrgencyLevel.NONE
    
    def should_interrupt(self, task: Dict) -> bool:
        """
        Determine if should interrupt user with this task.
        
        Args:
            task: Task/notification to deliver
            
        Returns:
            True if should interrupt
        """
        user_state = self.detect_user_state()
        urgency = self.assess_urgency(task)
        
        # Critical always interrupts
        if urgency == UrgencyLevel.CRITICAL:
            return True
        
        # Never interrupt if away (queue for later)
        if user_state == UserState.AWAY:
            return False
        
        # High urgency interrupts unless focused
        if urgency == UrgencyLevel.HIGH:
            return user_state != UserState.FOCUSED
        
        # Medium urgency only when available or idle
        if urgency == UrgencyLevel.MEDIUM:
            return user_state in [UserState.AVAILABLE, UserState.IDLE]
        
        # Low urgency only when idle
        if urgency == UrgencyLevel.LOW:
            return user_state == UserState.IDLE
        
        return False
    
    def record_activity(self, activity: str):
        """
        Record user activity.
        
        Args:
            activity: Description of activity
        """
        self.last_activity_time = datetime.now()
        self.activity_history.append({
            'activity': activity,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        cutoff = datetime.now() - timedelta(hours=1)
        self.activity_history = [
            a for a in self.activity_history
            if a['timestamp'] > cutoff
        ]
        
        # Detect focus session start
        if 'code' in activity.lower() or 'debug' in activity.lower():
            if not self.focus_start_time:
                self.focus_start_time = datetime.now()
                logger.info("🎯 Focus session detected")
        else:
            # End focus session
            if self.focus_start_time:
                duration = datetime.now() - self.focus_start_time
                logger.info(f"✅ Focus session ended ({duration.total_seconds()/60:.1f} minutes)")
                self.focus_start_time = None
    
    def _can_interrupt(self, user_state: UserState) -> tuple:
        """
        Assess if can interrupt user.
        
        Returns:
            (can_interrupt: bool, reasoning: str)
        """
        if user_state == UserState.FOCUSED:
            return False, "User is focused on a task"
        
        if user_state == UserState.BUSY:
            return False, "User is busy in conversation"
        
        if user_state == UserState.AWAY:
            return False, "User is away"
        
        if user_state == UserState.IDLE:
            return True, "User is idle and available"
        
        if user_state == UserState.AVAILABLE:
            return True, "User is available"
        
        return False, "Unknown user state"
    
    def _infer_current_task(self) -> Optional[str]:
        """Infer what user is currently working on"""
        if not self.activity_history:
            return None
        
        # Get most recent activity
        recent = self.activity_history[-1]
        return recent['activity']
    
    def _get_active_goal_descriptions(self) -> List[str]:
        """Get descriptions of active goals"""
        if not self.goal_manager:
            return []
        
        try:
            active_goals = self.goal_manager.get_active_goals()
            return [goal.description for goal in active_goals[:5]]
        except Exception as e:
            logger.debug(f"Failed to get active goals: {e}")
            return []
    
    def _get_recent_activity(self) -> List[str]:
        """Get recent activity summary"""
        return [a['activity'] for a in self.activity_history[-5:]]
    
    def _get_platform_states(self) -> Dict[str, Any]:
        """Get current state of all platforms"""
        states = {}
        
        if self.world_state:
            try:
                # Get recent events per platform
                events = self.world_state.get_events(limit=100)
                
                platform_activity = {}
                for event in events:
                    platform = event.metadata.get('platform', 'unknown')
                    if platform not in platform_activity:
                        platform_activity[platform] = []
                    platform_activity[platform].append(event)
                
                # Summarize per platform
                for platform, platform_events in platform_activity.items():
                    states[platform] = {
                        'recent_events': len(platform_events),
                        'last_activity': platform_events[0].timestamp if platform_events else None
                    }
            except Exception as e:
                logger.debug(f"Failed to get platform states: {e}")
        
        return states
    
    def _get_time_context(self) -> Dict[str, Any]:
        """Get time-based context"""
        now = datetime.now()
        hour = now.hour
        
        # Time of day
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        # Day of week
        day_of_week = now.strftime("%A")
        
        # Weekend vs weekday
        is_weekend = now.weekday() >= 5
        
        return {
            'hour': hour,
            'time_of_day': time_of_day,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'timestamp': now.isoformat()
        }
    
    def get_context_summary(self) -> str:
        """Get human-readable context summary"""
        context = self.get_current_context()
        
        lines = [
            "📍 Context Summary:",
            f"User State: {context.user_state.value}",
            f"Time: {context.time_context['time_of_day']} ({context.time_context['hour']}:00)",
        ]
        
        if context.current_task:
            lines.append(f"Current Task: {context.current_task}")
        
        if context.active_goals:
            lines.append(f"Active Goals: {len(context.active_goals)}")
        
        if context.recent_activity:
            lines.append(f"Recent Activity: {', '.join(context.recent_activity[-3:])}")
        
        lines.append(f"Can Interrupt: {'Yes' if context.can_interrupt else 'No'} ({context.reasoning})")
        
        return "\n".join(lines)


def create_contextual_awareness(world_state=None,
                                conversational_memory=None,
                                goal_manager=None):
    """Factory function to create contextual awareness system"""
    return ContextualAwareness(world_state, conversational_memory, goal_manager)
