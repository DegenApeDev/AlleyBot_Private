"""
Emotional Intelligence System

Detects and responds appropriately to user emotions.
This is what makes AlleyBot empathetic and human-like.

Detects:
- Frustration (repeated failures, complaints)
- Excitement (achievements, positive outcomes)
- Confusion (unclear requests, questions)
- Satisfaction (goals met, success)
- Stress (time pressure, urgency)
- Gratitude (thanks, appreciation)

Responds:
- Adjusts tone and approach
- Offers appropriate support
- Celebrates achievements
- Provides reassurance
- Adapts communication style

Integration:
- Uses ConversationalMemory for emotion history
- Uses IntentRecognizer for emotion detection
- Feeds into PersonalityEngine for tone adjustment
- Influences all responses
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class EmotionType(Enum):
    """User emotion types"""
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    EXCITED = "excited"
    CONFUSED = "confused"
    SATISFIED = "satisfied"
    STRESSED = "stressed"
    GRATEFUL = "grateful"
    ANGRY = "angry"
    HAPPY = "happy"
    DISAPPOINTED = "disappointed"


@dataclass
class EmotionalState:
    """User's emotional state"""
    primary_emotion: EmotionType
    intensity: float  # 0-1
    confidence: float  # 0-1
    triggers: List[str]  # What caused this emotion
    timestamp: datetime
    context: Dict[str, Any]


class EmotionalIntelligence:
    """
    Detects and responds to user emotions.
    
    JARVIS-like emotional awareness:
    - Understands how user feels
    - Responds empathetically
    - Adjusts approach based on emotion
    - Celebrates successes
    - Provides support when needed
    """
    
    def __init__(self, conversational_memory=None):
        """
        Initialize emotional intelligence system.
        
        Args:
            conversational_memory: ConversationalMemory instance
        """
        self.conversation = conversational_memory
        
        # Emotion tracking
        self.emotion_history: deque = deque(maxlen=20)
        self.current_emotion = EmotionType.NEUTRAL
        self.emotion_intensity = 0.5
        
        # Emotion patterns
        self.frustration_indicators = [
            'not working', 'broken', 'failed', 'error', 'wrong',
            'ugh', 'argh', 'damn', 'seriously', 'again', 'still',
            'tried multiple times', 'keeps failing', 'always'
        ]
        
        self.excitement_indicators = [
            'yes!', 'awesome', 'great', 'amazing', 'perfect',
            'finally', 'worked', 'success', 'love it', 'excellent',
            '!', 'wow', 'incredible'
        ]
        
        self.confusion_indicators = [
            'confused', 'don\'t understand', 'what do you mean',
            'unclear', 'huh', '?', 'how', 'why', 'what'
        ]
        
        self.gratitude_indicators = [
            'thanks', 'thank you', 'appreciate', 'grateful',
            'helpful', 'great job', 'well done'
        ]
        
        self.stress_indicators = [
            'urgent', 'asap', 'quickly', 'hurry', 'deadline',
            'running out of time', 'need this now', 'critical'
        ]
    
    def detect_emotion(self, user_input: str, context: Dict = None) -> EmotionalState:
        """
        Identify user's emotional state.
        
        Args:
            user_input: What user said
            context: Additional context
            
        Returns:
            EmotionalState
        """
        context = context or {}
        user_input_lower = user_input.lower()
        
        # Detect emotion type and intensity
        emotion, intensity, triggers = self._classify_emotion(user_input_lower, context)
        
        # Calculate confidence
        confidence = self._calculate_confidence(triggers, context)
        
        # Create emotional state
        state = EmotionalState(
            primary_emotion=emotion,
            intensity=intensity,
            confidence=confidence,
            triggers=triggers,
            timestamp=datetime.now(),
            context=context
        )
        
        # Track emotion
        self.emotion_history.append(state)
        self.current_emotion = emotion
        self.emotion_intensity = intensity
        
        logger.info(f"😊 Detected emotion: {emotion.value} (intensity: {intensity:.0%}, confidence: {confidence:.0%})")
        
        return state
    
    def _classify_emotion(self, user_input: str, context: Dict) -> tuple:
        """
        Classify emotion type and intensity.
        
        Returns:
            (emotion, intensity, triggers)
        """
        triggers = []
        scores = {emotion: 0 for emotion in EmotionType}
        
        # Check frustration
        for indicator in self.frustration_indicators:
            if indicator in user_input:
                scores[EmotionType.FRUSTRATED] += 1
                triggers.append(indicator)
        
        # Check excitement
        for indicator in self.excitement_indicators:
            if indicator in user_input:
                scores[EmotionType.EXCITED] += 1
                triggers.append(indicator)
        
        # Check confusion
        for indicator in self.confusion_indicators:
            if indicator in user_input:
                scores[EmotionType.CONFUSED] += 1
                triggers.append(indicator)
        
        # Check gratitude
        for indicator in self.gratitude_indicators:
            if indicator in user_input:
                scores[EmotionType.GRATEFUL] += 1
                triggers.append(indicator)
        
        # Check stress
        for indicator in self.stress_indicators:
            if indicator in user_input:
                scores[EmotionType.STRESSED] += 1
                triggers.append(indicator)
        
        # Check context for additional signals
        if context.get('repeated_failures'):
            scores[EmotionType.FRUSTRATED] += 2
            triggers.append('repeated failures')
        
        if context.get('achievement'):
            scores[EmotionType.EXCITED] += 2
            triggers.append('achievement')
        
        if context.get('deadline_approaching'):
            scores[EmotionType.STRESSED] += 2
            triggers.append('deadline approaching')
        
        # Find dominant emotion
        max_score = max(scores.values())
        if max_score == 0:
            return EmotionType.NEUTRAL, 0.5, []
        
        dominant_emotion = max(scores.items(), key=lambda x: x[1])[0]
        
        # Calculate intensity (0-1)
        intensity = min(max_score / 5, 1.0)
        
        return dominant_emotion, intensity, triggers
    
    def _calculate_confidence(self, triggers: List[str], context: Dict) -> float:
        """Calculate confidence in emotion detection"""
        if not triggers:
            return 0.3  # Low confidence for neutral
        
        # More triggers = higher confidence
        confidence = min(len(triggers) / 3, 1.0)
        
        # Context adds confidence
        if context.get('repeated_failures') or context.get('achievement'):
            confidence = min(confidence + 0.2, 1.0)
        
        return confidence
    
    def adjust_response_style(self, emotion: EmotionType, base_response: str) -> str:
        """
        Adapt response to user's emotion.
        
        Args:
            emotion: User's emotion
            base_response: Original response
            
        Returns:
            Emotionally-adapted response
        """
        if emotion == EmotionType.FRUSTRATED:
            # Add empathy and reassurance
            return self._add_empathy(base_response)
        
        elif emotion == EmotionType.EXCITED:
            # Match enthusiasm
            return self._add_enthusiasm(base_response)
        
        elif emotion == EmotionType.CONFUSED:
            # Add clarity and patience
            return self._add_clarity(base_response)
        
        elif emotion == EmotionType.GRATEFUL:
            # Acknowledge and encourage
            return self._add_acknowledgment(base_response)
        
        elif emotion == EmotionType.STRESSED:
            # Be efficient and supportive
            return self._add_efficiency(base_response)
        
        elif emotion == EmotionType.SATISFIED:
            # Celebrate success
            return self._add_celebration(base_response)
        
        return base_response
    
    def _add_empathy(self, response: str) -> str:
        """Add empathy for frustrated users"""
        empathy_openers = [
            "I understand that's frustrating.",
            "I can see this is challenging.",
            "I get it, that's tough.",
            "That's definitely frustrating."
        ]
        
        import random
        opener = random.choice(empathy_openers)
        
        return f"{opener} {response} Let me help you get this sorted out."
    
    def _add_enthusiasm(self, response: str) -> str:
        """Match user's excitement"""
        if '!' not in response:
            response = response.rstrip('.') + '!'
        
        enthusiasm_additions = [
            " That's awesome!",
            " Great work!",
            " Excellent!",
            " Nice!"
        ]
        
        import random
        addition = random.choice(enthusiasm_additions)
        
        return f"{addition} {response}"
    
    def _add_clarity(self, response: str) -> str:
        """Add clarity for confused users"""
        clarity_openers = [
            "Let me explain that more clearly.",
            "Here's what I mean:",
            "Let me break this down:",
            "To clarify:"
        ]
        
        import random
        opener = random.choice(clarity_openers)
        
        return f"{opener} {response}"
    
    def _add_acknowledgment(self, response: str) -> str:
        """Acknowledge gratitude"""
        acknowledgments = [
            "You're welcome!",
            "Happy to help!",
            "Anytime!",
            "Glad I could help!"
        ]
        
        import random
        ack = random.choice(acknowledgments)
        
        return f"{ack} {response}"
    
    def _add_efficiency(self, response: str) -> str:
        """Be efficient for stressed users"""
        # Keep it brief and action-focused
        return f"Quick answer: {response}"
    
    def _add_celebration(self, response: str) -> str:
        """Celebrate success"""
        celebrations = [
            "🎉 Excellent!",
            "✅ Well done!",
            "🎯 Perfect!",
            "⭐ Great job!"
        ]
        
        import random
        celebration = random.choice(celebrations)
        
        return f"{celebration} {response}"
    
    def offer_appropriate_support(self, emotion: EmotionType) -> Optional[str]:
        """
        Provide emotional support when needed.
        
        Args:
            emotion: User's emotion
            
        Returns:
            Support message or None
        """
        if emotion == EmotionType.FRUSTRATED:
            return "I'm here to help. Let's tackle this together step by step."
        
        elif emotion == EmotionType.CONFUSED:
            return "No worries! I can explain this in a different way if that helps."
        
        elif emotion == EmotionType.STRESSED:
            return "I understand the time pressure. Let me prioritize what's most important."
        
        elif emotion == EmotionType.DISAPPOINTED:
            return "I know that's not the outcome you wanted. Let's figure out what we can do differently."
        
        return None
    
    def detect_emotional_pattern(self) -> Optional[str]:
        """
        Detect patterns in user's emotional state.
        
        Returns:
            Pattern description or None
        """
        if len(self.emotion_history) < 3:
            return None
        
        recent_emotions = [state.primary_emotion for state in list(self.emotion_history)[-5:]]
        
        # Check for persistent frustration
        frustration_count = sum(1 for e in recent_emotions if e == EmotionType.FRUSTRATED)
        if frustration_count >= 3:
            return "persistent_frustration"
        
        # Check for excitement trend
        excitement_count = sum(1 for e in recent_emotions if e == EmotionType.EXCITED)
        if excitement_count >= 3:
            return "positive_momentum"
        
        # Check for confusion
        confusion_count = sum(1 for e in recent_emotions if e == EmotionType.CONFUSED)
        if confusion_count >= 3:
            return "persistent_confusion"
        
        return None
    
    def get_emotional_summary(self) -> str:
        """Get human-readable emotional summary"""
        if not self.emotion_history:
            return "😐 No emotional data yet"
        
        recent = list(self.emotion_history)[-5:]
        
        lines = [
            "😊 Emotional State Summary:",
            f"Current: {self.current_emotion.value} (intensity: {self.emotion_intensity:.0%})"
        ]
        
        # Pattern detection
        pattern = self.detect_emotional_pattern()
        if pattern:
            if pattern == "persistent_frustration":
                lines.append("⚠️ Pattern: User seems persistently frustrated - may need different approach")
            elif pattern == "positive_momentum":
                lines.append("✨ Pattern: User is on a positive streak - good time for challenges")
            elif pattern == "persistent_confusion":
                lines.append("❓ Pattern: User seems confused - may need clearer explanations")
        
        # Recent emotions
        emotion_str = " → ".join([e.primary_emotion.value for e in recent])
        lines.append(f"Recent: {emotion_str}")
        
        return "\n".join(lines)
    
    def should_offer_break(self) -> bool:
        """Determine if should suggest user take a break"""
        # Check for prolonged frustration
        pattern = self.detect_emotional_pattern()
        if pattern == "persistent_frustration":
            return True
        
        # Check for stress + long session
        if self.current_emotion == EmotionType.STRESSED:
            if len(self.emotion_history) > 10:
                return True
        
        return False


def create_emotional_intelligence(conversational_memory=None):
    """Factory function to create emotional intelligence system"""
    return EmotionalIntelligence(conversational_memory)
