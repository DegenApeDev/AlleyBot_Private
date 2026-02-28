"""
Adaptive Response System

Combines personality, emotional intelligence, and context to generate
perfectly-tuned responses for any situation.

This is the orchestrator that makes AlleyBot feel truly intelligent and human-like.

Integrates:
- PersonalityEngine for consistent character
- EmotionalIntelligence for empathy
- ContextualAwareness for situational understanding
- ConversationalMemory for context
- IntentRecognizer for understanding

Generates:
- Contextually appropriate responses
- Emotionally intelligent replies
- Personality-consistent messages
- Adaptive tone and style
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ResponseContext:
    """Context for response generation"""
    user_input: str
    user_emotion: str = 'neutral'
    user_state: str = 'available'
    situation: str = 'normal'
    intent: str = 'unknown'
    conversation_history: List = None
    time_context: Dict = None
    can_be_proactive: bool = True


class AdaptiveResponse:
    """
    Generates perfectly-tuned responses.
    
    JARVIS-like response intelligence:
    - Adapts to user's emotional state
    - Maintains consistent personality
    - Considers full context
    - Adjusts tone appropriately
    - Feels natural and human-like
    """
    
    def __init__(self,
                 personality_engine,
                 emotional_intelligence,
                 contextual_awareness=None,
                 conversational_memory=None,
                 intent_recognizer=None):
        """
        Initialize adaptive response system.
        
        Args:
            personality_engine: PersonalityEngine instance
            emotional_intelligence: EmotionalIntelligence instance
            contextual_awareness: ContextualAwareness instance
            conversational_memory: ConversationalMemory instance
            intent_recognizer: IntentRecognizer instance
        """
        self.personality = personality_engine
        self.emotional_intelligence = emotional_intelligence
        self.context_awareness = contextual_awareness
        self.conversation = conversational_memory
        self.intent_recognizer = intent_recognizer
    
    def generate_response(self, 
                         base_message: str,
                         context: ResponseContext) -> str:
        """
        Generate adaptive response.
        
        Args:
            base_message: Core message content
            context: Response context
            
        Returns:
            Fully-adapted response
        """
        # Start with base message
        response = base_message
        
        # Detect user emotion
        emotional_state = self.emotional_intelligence.detect_emotion(
            context.user_input,
            {
                'situation': context.situation,
                'user_state': context.user_state
            }
        )
        
        # Adjust for emotion
        response = self.emotional_intelligence.adjust_response_style(
            emotional_state.primary_emotion,
            response
        )
        
        # Apply personality
        personality_context = {
            'user_emotion': emotional_state.primary_emotion.value,
            'situation': context.situation,
            'hour': context.time_context.get('hour') if context.time_context else 12,
            'is_new_conversation': len(context.conversation_history or []) == 0
        }
        
        response = self.personality.apply_personality(response, personality_context)
        
        # Add proactive element if appropriate
        if context.can_be_proactive and self._should_be_proactive(context, emotional_state):
            proactive_addition = self._generate_proactive_addition(context)
            if proactive_addition:
                response += f" {proactive_addition}"
        
        return response
    
    def generate_greeting(self, context: ResponseContext) -> str:
        """Generate contextual greeting"""
        # Get base greeting from personality
        greeting = self.personality.generate_greeting({
            'hour': context.time_context.get('hour') if context.time_context else 12
        })
        
        # Add personalization based on context
        if context.user_state == 'away':
            greeting += " Welcome back!"
        
        return greeting
    
    def generate_acknowledgment(self, context: ResponseContext) -> str:
        """Generate acknowledgment"""
        ack = self.personality.generate_acknowledgment()
        
        # Add enthusiasm if user is excited
        if context.user_emotion == 'excited':
            ack = ack.rstrip('.') + '!'
        
        return ack
    
    def generate_error_response(self, error_message: str, context: ResponseContext) -> str:
        """Generate error response with empathy"""
        # Detect if user is frustrated
        emotional_state = self.emotional_intelligence.detect_emotion(
            context.user_input,
            {'situation': 'error'}
        )
        
        if emotional_state.primary_emotion.value == 'frustrated':
            response = "I understand that's frustrating. "
        else:
            response = ""
        
        response += f"Here's what happened: {error_message}"
        
        # Offer solution
        response += " Let me help you fix this."
        
        return response
    
    def generate_success_response(self, success_message: str, context: ResponseContext) -> str:
        """Generate success response with celebration"""
        # Use personality for success message
        response = self.personality.generate_success_message({
            'performance_metric': success_message
        })
        
        # Add celebration if appropriate
        if context.user_emotion == 'excited' or context.situation == 'achievement':
            response = self.emotional_intelligence._add_celebration(response)
        
        return response
    
    def generate_clarification_request(self, context: ResponseContext) -> str:
        """Generate clarification request"""
        # Be friendly and patient
        clarifications = [
            "Could you provide a bit more detail?",
            "I want to make sure I understand - could you elaborate?",
            "Just to clarify, what specifically would you like me to do?",
            "Help me understand better - what exactly do you need?"
        ]
        
        import random
        base = random.choice(clarifications)
        
        # Add empathy if user seems confused
        if context.user_emotion == 'confused':
            base = "No worries! " + base
        
        return base
    
    def generate_proactive_suggestion(self, suggestion: str, context: ResponseContext) -> str:
        """Generate proactive suggestion"""
        # Check if good time to suggest
        if self.context_awareness:
            ctx = self.context_awareness.get_current_context()
            if not ctx.can_interrupt:
                return None  # Don't suggest if bad time
        
        # Frame suggestion appropriately
        if context.user_state == 'idle':
            return f"Hey! {suggestion}"
        elif context.user_state == 'available':
            return f"Quick thought: {suggestion}"
        else:
            return None  # Don't interrupt
    
    def _should_be_proactive(self, context: ResponseContext, emotional_state) -> bool:
        """Determine if should add proactive element"""
        # Don't be proactive if user is frustrated or stressed
        if emotional_state.primary_emotion.value in ['frustrated', 'stressed', 'angry']:
            return False
        
        # Don't be proactive if user is busy
        if context.user_state == 'busy':
            return False
        
        # Be proactive if user is satisfied or excited
        if emotional_state.primary_emotion.value in ['satisfied', 'excited', 'happy']:
            return True
        
        # Be proactive if user is idle
        if context.user_state == 'idle':
            return True
        
        return False
    
    def _generate_proactive_addition(self, context: ResponseContext) -> Optional[str]:
        """Generate proactive addition to response"""
        proactive_additions = [
            "Want to keep going?",
            "Should we tackle something else?",
            "What's next?",
            "Anything else I can help with?"
        ]
        
        import random
        return random.choice(proactive_additions)
    
    def format_multi_turn_response(self,
                                   base_message: str,
                                   context: ResponseContext,
                                   is_follow_up: bool = False) -> str:
        """Format response for multi-turn conversation"""
        if is_follow_up:
            # Reference previous context
            if context.conversation_history:
                # More casual for follow-ups
                return base_message
        
        # New topic - might need greeting
        return self.generate_response(base_message, context)
    
    def get_response_summary(self) -> str:
        """Get summary of response system state"""
        lines = [
            "🎭 Adaptive Response System:",
            f"Personality: {self.personality.traits.helpfulness:.0%} helpful, {self.personality.traits.wit:.0%} witty",
            f"Emotional Intelligence: Active"
        ]
        
        if self.emotional_intelligence.emotion_history:
            current = self.emotional_intelligence.current_emotion.value
            lines.append(f"Current User Emotion: {current}")
        
        if self.context_awareness:
            ctx = self.context_awareness.get_current_context()
            lines.append(f"User State: {ctx.user_state.value}")
            lines.append(f"Can Interrupt: {ctx.can_interrupt}")
        
        return "\n".join(lines)


def create_adaptive_response(personality_engine,
                            emotional_intelligence,
                            contextual_awareness=None,
                            conversational_memory=None,
                            intent_recognizer=None):
    """Factory function to create adaptive response system"""
    return AdaptiveResponse(
        personality_engine,
        emotional_intelligence,
        contextual_awareness,
        conversational_memory,
        intent_recognizer
    )
