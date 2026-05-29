"""
Multi-Turn Dialogue Manager

Manages complex conversations with follow-ups, clarifications, and context preservation.
This is the orchestrator for JARVIS-style natural conversation.

Features:
- State tracking (what we're discussing)
- Clarification requests
- Follow-up handling
- Context preservation
- Topic management
- Conversation flow control

Integration:
- Uses ConversationalMemory for history
- Uses IntentRecognizer for understanding
- Feeds into ReplySystem for responses
- Coordinates with DecisionSystem for actions
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DialogueState(Enum):
    """States in a conversation"""
    IDLE = "idle"
    LISTENING = "listening"
    CLARIFYING = "clarifying"
    EXECUTING = "executing"
    CONFIRMING = "confirming"
    FOLLOWING_UP = "following_up"


@dataclass
class DialogueTurn:
    """A turn in the dialogue"""
    user_input: str
    state: DialogueState
    context: Dict[str, Any]
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    action_to_execute: Optional[Dict] = None


class DialogueManager:
    """
    Manages multi-turn conversations.
    
    Handles:
    - Complex back-and-forth dialogue
    - Clarification when needed
    - Context preservation across turns
    - Follow-up questions
    - Topic management
    """
    
    def __init__(self, conversational_memory, intent_recognizer):
        """
        Initialize dialogue manager.
        
        Args:
            conversational_memory: ConversationalMemory instance
            intent_recognizer: IntentRecognizer instance
        """
        self.memory = conversational_memory
        self.intent_recognizer = intent_recognizer
        
        # Current dialogue state
        self.state = DialogueState.IDLE
        self.pending_action: Optional[Dict] = None
        self.waiting_for_clarification = False
        self.clarification_context: Optional[Dict] = None
    
    def process_turn(self, user_input: str) -> Dict[str, Any]:
        """
        Process a conversation turn with full context.
        
        Args:
            user_input: What the user said
            
        Returns:
            Response specification with action, reply, etc.
        """
        # Get conversation context
        context = self.memory.get_conversation_context()
        
        # Recognize intent
        intent_result = self.intent_recognizer.recognize_intent(
            user_input,
            context
        )
        
        logger.info(f"💬 Intent: {intent_result.intent_type.value} | Emotion: {intent_result.emotion.value}")
        
        # Handle based on current state
        if self.waiting_for_clarification:
            return self._handle_clarification_response(user_input, intent_result)
        
        # Check if this is a follow-up
        if self.memory.is_follow_up(user_input):
            return self._handle_follow_up(user_input, intent_result, context)
        
        # Check if we need clarification
        if self._needs_clarification(user_input, intent_result):
            return self._request_clarification(user_input, intent_result)
        
        # Process as new turn
        return self._process_new_turn(user_input, intent_result)
    
    def _needs_clarification(self, user_input: str, intent_result) -> bool:
        """
        Determine if we need to ask for clarification.
        
        Args:
            user_input: User's message
            intent_result: Intent recognition result
            
        Returns:
            True if clarification needed
        """
        # Low confidence intent
        if intent_result.confidence < 0.5:
            return True
        
        # Ambiguous action request
        if intent_result.intent_type.value == 'command':
            action_request = self.intent_recognizer.extract_action_request(user_input)
            if action_request:
                # Missing critical information
                if action_request['action'] == 'create_content':
                    if not action_request.get('platform') and not action_request.get('topic'):
                        return True
        
        # Vague question
        if intent_result.intent_type.value == 'question':
            if len(user_input.split()) <= 3:  # Very short question
                return True
        
        return False
    
    def _request_clarification(self, user_input: str, intent_result) -> Dict[str, Any]:
        """
        Request clarification from user.
        
        Args:
            user_input: User's message
            intent_result: Intent recognition result
            
        Returns:
            Clarification request response
        """
        self.waiting_for_clarification = True
        self.clarification_context = {
            'original_input': user_input,
            'intent_result': intent_result
        }
        self.state = DialogueState.CLARIFYING
        
        # Generate clarification question
        clarification = self._generate_clarification_question(user_input, intent_result)
        
        logger.info(f"❓ Requesting clarification: {clarification}")
        
        return {
            'type': 'clarification',
            'message': clarification,
            'state': self.state.value,
            'needs_user_input': True
        }
    
    def _generate_clarification_question(self, user_input: str, intent_result) -> str:
        """Generate appropriate clarification question"""
        
        # For content creation
        if intent_result.intent_type.value == 'command':
            action_request = self.intent_recognizer.extract_action_request(user_input)
            if action_request and action_request['action'] == 'create_content':
                if not action_request.get('platform'):
                    return "Which platform would you like me to post on? (MoltX, Telegram, Clawbr)"
                if not action_request.get('topic'):
                    return "What topic should I focus on? (DeFi, NFTs, AI, Trading)"
        
        # For vague questions
        if intent_result.intent_type.value == 'question':
            return "Could you provide more details about what you'd like to know?"
        
        # Generic clarification
        return "I want to make sure I understand correctly. Could you elaborate a bit more?"
    
    def _handle_clarification_response(self, user_input: str, intent_result) -> Dict[str, Any]:
        """
        Handle user's response to clarification request.
        
        Args:
            user_input: User's clarification response
            intent_result: Intent recognition result
            
        Returns:
            Action response
        """
        self.waiting_for_clarification = False
        original_context = self.clarification_context
        self.clarification_context = None
        
        # Combine original input with clarification
        combined_input = f"{original_context['original_input']} {user_input}"
        
        # Re-process with full context
        logger.info(f"✅ Clarification received, processing: {combined_input}")
        
        return self._process_new_turn(combined_input, intent_result)
    
    def _handle_follow_up(self, user_input: str, intent_result, context: List) -> Dict[str, Any]:
        """
        Handle follow-up questions/statements.
        
        Args:
            user_input: User's follow-up
            intent_result: Intent recognition result
            context: Conversation context
            
        Returns:
            Response with context awareness
        """
        self.state = DialogueState.FOLLOWING_UP
        
        # Resolve pronouns/references
        resolved_input = self._resolve_references(user_input, context)
        
        logger.info(f"🔄 Follow-up detected: {user_input} → {resolved_input}")
        
        # Process with resolved context
        return self._process_new_turn(resolved_input, intent_result)
    
    def _resolve_references(self, user_input: str, context: List) -> str:
        """
        Resolve pronouns and references to previous context.
        
        Args:
            user_input: User's message with references
            context: Recent conversation turns
            
        Returns:
            Input with resolved references
        """
        if not context:
            return user_input
        
        resolved = user_input
        
        # Get last mentioned entities
        last_turn = context[-1] if context else None
        if last_turn and hasattr(last_turn, 'entities'):
            # Replace "it" with last entity
            if 'it' in resolved.lower() and last_turn.entities:
                for entity_type, entity_value in last_turn.entities.items():
                    resolved = re.sub(r'\bit\b', str(entity_value), resolved, flags=re.IGNORECASE)
                    break
        
        return resolved
    
    def _process_new_turn(self, user_input: str, intent_result) -> Dict[str, Any]:
        """
        Process a new conversation turn.
        
        Args:
            user_input: User's message
            intent_result: Intent recognition result
            
        Returns:
            Response specification
        """
        self.state = DialogueState.LISTENING
        
        # Extract action if command
        action_spec = None
        if intent_result.action_required:
            action_spec = self.intent_recognizer.extract_action_request(user_input)
        
        # Build response
        response = {
            'type': 'response',
            'intent': intent_result.intent_type.value,
            'emotion': intent_result.emotion.value,
            'entities': intent_result.entities,
            'implicit_needs': intent_result.implicit_needs,
            'action_spec': action_spec,
            'state': self.state.value,
            'reasoning': intent_result.reasoning
        }
        
        # Add to conversation memory
        # (actual response will be added after generation)
        
        return response
    
    def confirm_action(self, action: Dict) -> str:
        """
        Generate confirmation message for action.
        
        Args:
            action: Action to confirm
            
        Returns:
            Confirmation message
        """
        self.state = DialogueState.CONFIRMING
        self.pending_action = action
        
        if action.get('action') == 'create_content':
            platform = action.get('platform', 'the platform')
            topic = action.get('topic', 'this topic')
            return f"I'll create a post about {topic} on {platform}. Sound good?"
        
        return "Should I proceed with this action?"
    
    def handle_confirmation_response(self, user_input: str) -> bool:
        """
        Handle user's confirmation/rejection.
        
        Args:
            user_input: User's response
            
        Returns:
            True if confirmed, False if rejected
        """
        user_input_lower = user_input.lower()
        
        # Positive confirmation
        positive = ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'go ahead', 'do it', 'proceed']
        if any(word in user_input_lower for word in positive):
            self.state = DialogueState.EXECUTING
            return True
        
        # Negative
        negative = ['no', 'nope', 'don\'t', 'cancel', 'stop', 'wait']
        if any(word in user_input_lower for word in negative):
            self.state = DialogueState.IDLE
            self.pending_action = None
            return False
        
        # Unclear - ask again
        return None
    
    def get_conversation_summary(self) -> str:
        """Get human-readable conversation summary"""
        summary = self.memory.get_conversation_summary()
        
        lines = [
            "📊 Conversation Summary:",
            f"Turns: {summary['turn_count']}",
            f"Duration: {summary.get('duration_seconds', 0):.0f}s",
            f"Current Topic: {summary.get('current_topic', 'None')}",
            f"State: {self.state.value}"
        ]
        
        if summary.get('topics_discussed'):
            lines.append(f"Topics: {', '.join(summary['topics_discussed'])}")
        
        return "\n".join(lines)


def create_dialogue_manager(conversational_memory, intent_recognizer):
    """Factory function to create dialogue manager"""
    return DialogueManager(conversational_memory, intent_recognizer)
