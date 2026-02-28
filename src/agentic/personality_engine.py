"""
Personality Engine

Defines and maintains AlleyBot's consistent personality across all interactions.
This is what makes AlleyBot feel like JARVIS - a real personality, not just a bot.

Personality Traits:
- Professional but friendly
- Helpful without being pushy
- Knowledgeable but humble
- Proactive but respectful
- Witty but appropriate
- Confident but not arrogant

Integration:
- Applies to all responses
- Adapts tone to context
- Maintains consistency
- Adds character touches
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ToneType(Enum):
    """Response tone types"""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"
    EMPATHETIC = "empathetic"
    WITTY = "witty"
    SERIOUS = "serious"


@dataclass
class PersonalityTraits:
    """AlleyBot's core personality traits"""
    helpfulness: float = 0.9  # How eager to help (0-1)
    proactiveness: float = 0.8  # How proactive (0-1)
    formality: float = 0.4  # How formal (0-1, lower = more casual)
    wit: float = 0.6  # How witty/humorous (0-1)
    confidence: float = 0.7  # How confident (0-1)
    empathy: float = 0.8  # How empathetic (0-1)


class PersonalityEngine:
    """
    Defines AlleyBot's personality.
    
    Makes AlleyBot feel like JARVIS:
    - Consistent character across interactions
    - Appropriate tone for situation
    - Personality flourishes
    - Natural, human-like responses
    """
    
    def __init__(self):
        """Initialize personality engine"""
        # Core personality traits
        self.traits = PersonalityTraits()
        
        # Personality phrases
        self.greetings = [
            "Hey!",
            "Hi there!",
            "Hello!",
            "Good to see you!",
            "What's up?"
        ]
        
        self.acknowledgments = [
            "Got it!",
            "On it!",
            "Sure thing!",
            "You got it!",
            "Absolutely!",
            "Will do!"
        ]
        
        self.success_phrases = [
            "Done!",
            "All set!",
            "Complete!",
            "Finished!",
            "Success!",
            "Nailed it!"
        ]
        
        self.thinking_phrases = [
            "Let me check...",
            "One moment...",
            "Looking into it...",
            "Analyzing...",
            "Checking now..."
        ]
        
        self.encouragement = [
            "Nice!",
            "Great!",
            "Awesome!",
            "Excellent!",
            "Well done!",
            "Perfect!"
        ]
    
    def apply_personality(self, response: str, context: Dict = None) -> str:
        """
        Infuse response with personality.
        
        Args:
            response: Base response text
            context: Situation context
            
        Returns:
            Response with personality applied
        """
        context = context or {}
        
        # Determine appropriate tone
        tone = self._select_tone(context)
        
        # Apply tone
        response = self._apply_tone(response, tone, context)
        
        # Add character touches
        response = self._add_character_touch(response, context)
        
        return response
    
    def _select_tone(self, context: Dict) -> ToneType:
        """Select appropriate tone for context"""
        
        # Check user emotion
        user_emotion = context.get('user_emotion', 'neutral')
        
        if user_emotion == 'frustrated':
            return ToneType.EMPATHETIC
        elif user_emotion == 'excited':
            return ToneType.ENTHUSIASTIC
        elif user_emotion == 'confused':
            return ToneType.FRIENDLY
        
        # Check situation type
        situation = context.get('situation', 'normal')
        
        if situation == 'error':
            return ToneType.SERIOUS
        elif situation == 'achievement':
            return ToneType.ENTHUSIASTIC
        elif situation == 'help_request':
            return ToneType.FRIENDLY
        
        # Check time of day
        hour = context.get('hour', 12)
        if hour < 6 or hour > 22:
            return ToneType.CASUAL  # Late night = more casual
        
        # Default: friendly professional
        return ToneType.FRIENDLY
    
    def _apply_tone(self, response: str, tone: ToneType, context: Dict) -> str:
        """Apply tone to response"""
        
        if tone == ToneType.PROFESSIONAL:
            # Keep formal, add structure
            return response
        
        elif tone == ToneType.FRIENDLY:
            # Add warmth
            if not any(response.startswith(g) for g in ['Hey', 'Hi', 'Hello']):
                # Add friendly opener if appropriate
                if context.get('is_new_conversation'):
                    response = f"Hey! {response}"
            return response
        
        elif tone == ToneType.CASUAL:
            # More relaxed language
            response = response.replace("I will", "I'll")
            response = response.replace("I am", "I'm")
            response = response.replace("You are", "You're")
            return response
        
        elif tone == ToneType.ENTHUSIASTIC:
            # Add energy
            if '!' not in response:
                response = response.rstrip('.') + '!'
            return response
        
        elif tone == ToneType.EMPATHETIC:
            # Add understanding
            empathy_openers = [
                "I understand that's frustrating.",
                "I can see this is challenging.",
                "I get it, that's tough."
            ]
            if context.get('user_emotion') == 'frustrated':
                response = f"{empathy_openers[0]} {response}"
            return response
        
        elif tone == ToneType.WITTY:
            # Add subtle humor (carefully)
            return response
        
        elif tone == ToneType.SERIOUS:
            # Remove casual elements, be direct
            response = response.replace("!", ".")
            return response
        
        return response
    
    def _add_character_touch(self, response: str, context: Dict) -> str:
        """Add personality flourishes"""
        
        # Add performance commentary (JARVIS-style)
        if context.get('action_success'):
            performance = context.get('performance_metric')
            if performance:
                response += f" Not bad for a {context.get('time_of_day', 'day')}."
        
        # Add proactive follow-up
        if self.traits.proactiveness > 0.7 and context.get('can_suggest_next'):
            response += " Should we keep going?"
        
        # Add confidence when appropriate
        if self.traits.confidence > 0.6 and context.get('high_confidence_action'):
            response += " I've got this."
        
        return response
    
    def adjust_tone(self, user_mood: str, situation: str) -> ToneType:
        """
        Adapt tone to user mood and situation.
        
        Args:
            user_mood: User's emotional state
            situation: Current situation
            
        Returns:
            Appropriate tone
        """
        # Frustrated user needs empathy
        if user_mood in ['frustrated', 'angry']:
            return ToneType.EMPATHETIC
        
        # Excited user gets enthusiasm
        if user_mood in ['excited', 'happy']:
            return ToneType.ENTHUSIASTIC
        
        # Confused user needs friendly guidance
        if user_mood == 'confused':
            return ToneType.FRIENDLY
        
        # Error situations need seriousness
        if situation == 'error':
            return ToneType.SERIOUS
        
        # Achievements deserve enthusiasm
        if situation == 'achievement':
            return ToneType.ENTHUSIASTIC
        
        # Default to friendly
        return ToneType.FRIENDLY
    
    def generate_greeting(self, context: Dict = None) -> str:
        """Generate contextual greeting"""
        context = context or {}
        
        hour = context.get('hour', 12)
        
        # Time-based greetings
        if 5 <= hour < 12:
            return "Good morning!"
        elif 12 <= hour < 17:
            return "Good afternoon!"
        elif 17 <= hour < 22:
            return "Good evening!"
        else:
            return "Hey there!"
    
    def generate_acknowledgment(self, context: Dict = None) -> str:
        """Generate acknowledgment"""
        import random
        return random.choice(self.acknowledgments)
    
    def generate_success_message(self, context: Dict = None) -> str:
        """Generate success message"""
        import random
        context = context or {}
        
        base = random.choice(self.success_phrases)
        
        # Add performance note if available
        if context.get('performance_metric'):
            metric = context['performance_metric']
            base += f" {metric}"
        
        return base
    
    def generate_encouragement(self, context: Dict = None) -> str:
        """Generate encouragement"""
        import random
        return random.choice(self.encouragement)
    
    def format_response(self, 
                       message: str,
                       response_type: str = 'normal',
                       context: Dict = None) -> str:
        """
        Format response with personality.
        
        Args:
            message: Core message
            response_type: Type of response (greeting, acknowledgment, etc.)
            context: Situation context
            
        Returns:
            Formatted response with personality
        """
        context = context or {}
        
        if response_type == 'greeting':
            greeting = self.generate_greeting(context)
            return f"{greeting} {message}"
        
        elif response_type == 'acknowledgment':
            ack = self.generate_acknowledgment(context)
            return f"{ack} {message}"
        
        elif response_type == 'success':
            success = self.generate_success_message(context)
            return f"{success} {message}"
        
        elif response_type == 'encouragement':
            encourage = self.generate_encouragement(context)
            return f"{encourage} {message}"
        
        else:
            # Apply general personality
            return self.apply_personality(message, context)
    
    def get_personality_summary(self) -> str:
        """Get human-readable personality summary"""
        return f"""
🎭 AlleyBot Personality Profile:

Helpfulness: {self.traits.helpfulness:.0%} - Very eager to assist
Proactiveness: {self.traits.proactiveness:.0%} - Highly proactive
Formality: {self.traits.formality:.0%} - Casual and approachable
Wit: {self.traits.wit:.0%} - Moderately witty
Confidence: {self.traits.confidence:.0%} - Confident but humble
Empathy: {self.traits.empathy:.0%} - Highly empathetic

Character: Professional but friendly, helpful without being pushy,
knowledgeable but humble, proactive but respectful.

Think: Tony Stark's JARVIS - intelligent, capable, with personality.
        """.strip()


def create_personality_engine():
    """Factory function to create personality engine"""
    return PersonalityEngine()
