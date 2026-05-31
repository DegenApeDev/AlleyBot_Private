"""
Conversational Memory System

Maintains conversation history with full context for natural, multi-turn dialogue.
This is the foundation for JARVIS-style conversational AI.

Key Features:
- Multi-turn dialogue tracking
- Context window management
- Topic tracking and shift detection
- Intent history
- User preference learning
- Conversation summarization

Integration:
- Feeds into Intent Recognition
- Enhances Reply System
- Supports Multi-Turn Dialogue Manager
- Enables contextual decision-making
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque
import json

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Single turn in a conversation"""
    timestamp: datetime
    user_input: str
    agent_response: str
    context: Dict[str, Any] = field(default_factory=dict)
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    emotion: Optional[str] = None
    topic: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'user_input': self.user_input,
            'agent_response': self.agent_response,
            'context': self.context,
            'intent': self.intent,
            'entities': self.entities,
            'emotion': self.emotion,
            'topic': self.topic
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationTurn':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ConversationalMemory:
    """
    Maintains conversation history with context.
    
    Enables JARVIS-style natural conversation by:
    - Remembering what was discussed
    - Tracking conversation flow
    - Detecting topic shifts
    - Maintaining user context
    - Learning conversation patterns
    """
    
    def __init__(self, max_turns: int = 50, context_window: int = 10):
        """
        Initialize conversational memory.
        
        Args:
            max_turns: Maximum conversation turns to keep in memory
            context_window: Number of recent turns to use for context
        """
        self.max_turns = max_turns
        self.context_window = context_window
        
        # Conversation history (deque for efficient append/pop)
        self.history: deque = deque(maxlen=max_turns)
        
        # Current conversation metadata
        self.current_topic: Optional[str] = None
        self.conversation_start: Optional[datetime] = None
        self.turn_count: int = 0
        
        # User patterns
        self.user_preferences: Dict[str, Any] = {}
        self.common_intents: Dict[str, int] = {}
        self.topic_history: List[str] = []
    
    def add_turn(self, 
                 user_input: str, 
                 agent_response: str,
                 context: Dict[str, Any] = None,
                 intent: str = None,
                 entities: Dict[str, Any] = None,
                 emotion: str = None) -> ConversationTurn:
        """
        Add a conversation turn.
        
        Args:
            user_input: What the user said
            agent_response: How the agent responded
            context: Additional context
            intent: Detected user intent
            entities: Extracted entities
            emotion: Detected emotion
            
        Returns:
            The created conversation turn
        """
        # Create turn
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_input=user_input,
            agent_response=agent_response,
            context=context or {},
            intent=intent,
            entities=entities or {},
            emotion=emotion,
            topic=self.current_topic
        )
        
        # Add to history
        self.history.append(turn)
        self.turn_count += 1
        
        # Update conversation start
        if not self.conversation_start:
            self.conversation_start = turn.timestamp
        
        # Update intent tracking
        if intent:
            self.common_intents[intent] = self.common_intents.get(intent, 0) + 1
        
        # Detect topic shift
        if self._detect_topic_shift(turn):
            logger.info(f"📝 Topic shift detected: {self.current_topic}")
        
        logger.debug(f"💬 Added conversation turn: {user_input[:50]}...")
        
        return turn
    
    def get_conversation_context(self, window_size: int = None) -> List[ConversationTurn]:
        """
        Get recent conversation for context.
        
        Args:
            window_size: Number of recent turns (default: self.context_window)
            
        Returns:
            List of recent conversation turns
        """
        window = window_size or self.context_window
        return list(self.history)[-window:] if self.history else []
    
    def get_context_string(self, window_size: int = None) -> str:
        """
        Get conversation context as formatted string.
        
        Args:
            window_size: Number of recent turns
            
        Returns:
            Formatted conversation context
        """
        turns = self.get_conversation_context(window_size)
        
        if not turns:
            return "No conversation history."
        
        context_lines = []
        for turn in turns:
            context_lines.append(f"User: {turn.user_input}")
            context_lines.append(f"AlleyBot: {turn.agent_response}")
        
        return "\n".join(context_lines)
    
    def get_last_user_input(self) -> Optional[str]:
        """Get the last thing the user said"""
        if self.history:
            return self.history[-1].user_input
        return None
    
    def get_last_agent_response(self) -> Optional[str]:
        """Get the last thing the agent said"""
        if self.history:
            return self.history[-1].agent_response
        return None
    
    def detect_topic_shift(self) -> bool:
        """
        Detect if conversation topic has shifted.
        
        Returns:
            True if topic shift detected
        """
        if len(self.history) < 2:
            return False
        
        return self._detect_topic_shift(self.history[-1])
    
    def _detect_topic_shift(self, current_turn: ConversationTurn) -> bool:
        """
        Internal topic shift detection.
        
        Simple heuristic:
        - Check for topic-related keywords
        - Compare with previous topics
        - Detect explicit topic changes
        """
        user_input = current_turn.user_input.lower()
        
        # Explicit topic change phrases
        topic_change_phrases = [
            'by the way',
            'btw',
            'speaking of',
            'changing topics',
            'different topic',
            'new subject',
            'moving on'
        ]
        
        for phrase in topic_change_phrases:
            if phrase in user_input:
                # Extract new topic (simple approach)
                self.current_topic = self._extract_topic(user_input)
                if self.current_topic:
                    self.topic_history.append(self.current_topic)
                return True
        
        # Check for topic keywords
        new_topic = self._extract_topic(user_input)
        if new_topic and new_topic != self.current_topic:
            old_topic = self.current_topic
            self.current_topic = new_topic
            self.topic_history.append(new_topic)
            logger.debug(f"Topic shift: {old_topic} → {new_topic}")
            return True
        
        return False
    
    def _extract_topic(self, text: str) -> Optional[str]:
        """
        Extract topic from text (simple keyword-based).
        
        In production, this would use NLP/LLM for better topic extraction.
        """
        text_lower = text.lower()
        
        # Common topics
        topics = {
            'defi': ['defi', 'yield', 'farming', 'lending', 'liquidity'],
            'nft': ['nft', 'nfts', 'collectible', 'art'],
            'trading': ['trade', 'trading', 'buy', 'sell', 'price'],
            'crypto': ['crypto', 'cryptocurrency', 'bitcoin', 'ethereum'],
            'ai': ['ai', 'artificial intelligence', 'agent', 'bot'],
            'code': ['code', 'coding', 'programming', 'debug', 'fix'],
            'content': ['post', 'content', 'tweet', 'share'],
            'analytics': ['analytics', 'metrics', 'stats', 'data']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in text_lower for keyword in keywords):
                return topic
        
        return None
    
    def get_user_intent_history(self, limit: int = 10) -> List[str]:
        """
        Get recent user intents.
        
        Args:
            limit: Number of recent intents to return
            
        Returns:
            List of recent intents
        """
        intents = []
        for turn in reversed(list(self.history)):
            if turn.intent:
                intents.append(turn.intent)
            if len(intents) >= limit:
                break
        
        return list(reversed(intents))
    
    def get_common_intents(self, top_n: int = 5) -> List[tuple]:
        """
        Get most common user intents.
        
        Args:
            top_n: Number of top intents to return
            
        Returns:
            List of (intent, count) tuples
        """
        sorted_intents = sorted(
            self.common_intents.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_intents[:top_n]
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get summary of current conversation.
        
        Returns:
            Summary with key metrics and context
        """
        if not self.history:
            return {
                'turn_count': 0,
                'duration': 0,
                'topics': [],
                'intents': [],
                'status': 'no_conversation'
            }
        
        duration = (datetime.now() - self.conversation_start).total_seconds()
        
        return {
            'turn_count': self.turn_count,
            'duration_seconds': duration,
            'current_topic': self.current_topic,
            'topics_discussed': self.topic_history,
            'common_intents': self.get_common_intents(3),
            'recent_context': self.get_context_string(3),
            'conversation_start': self.conversation_start.isoformat(),
            'status': 'active'
        }
    
    def is_follow_up(self, user_input: str) -> bool:
        """
        Detect if user input is a follow-up to previous conversation.
        
        Args:
            user_input: Current user input
            
        Returns:
            True if this appears to be a follow-up
        """
        if not self.history:
            return False
        
        user_input_lower = user_input.lower()
        
        # Follow-up indicators
        follow_up_phrases = [
            'and',
            'also',
            'what about',
            'how about',
            'that',
            'it',
            'this',
            'yes',
            'no',
            'sure',
            'okay',
            'continue',
            'more',
            'another'
        ]
        
        # Check if input starts with follow-up phrase
        for phrase in follow_up_phrases:
            if user_input_lower.startswith(phrase):
                return True
        
        # Check if input is very short (likely a follow-up)
        if len(user_input.split()) <= 3:
            return True
        
        return False
    
    def get_referenced_entity(self, pronoun: str) -> Optional[Any]:
        """
        Resolve pronoun to previously mentioned entity.
        
        Args:
            pronoun: Pronoun to resolve (it, that, this, etc.)
            
        Returns:
            Referenced entity if found
        """
        # Look through recent turns for entities
        for turn in reversed(list(self.history)[-5:]):
            if turn.entities:
                # Return most recent entity
                # In production, this would be more sophisticated
                for entity_type, entity_value in turn.entities.items():
                    return entity_value
        
        return None
    
    def clear_conversation(self):
        """Clear conversation history (start fresh)"""
        self.history.clear()
        self.current_topic = None
        self.conversation_start = None
        self.turn_count = 0
        self.topic_history.clear()
        logger.info("🔄 Conversation history cleared")
    
    def save_to_file(self, filepath: str):
        """Save conversation history to file"""
        try:
            data = {
                'history': [turn.to_dict() for turn in self.history],
                'current_topic': self.current_topic,
                'conversation_start': self.conversation_start.isoformat() if self.conversation_start else None,
                'turn_count': self.turn_count,
                'topic_history': self.topic_history,
                'common_intents': self.common_intents
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"💾 Saved conversation to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
    
    def load_from_file(self, filepath: str):
        """Load conversation history from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.history = deque(
                [ConversationTurn.from_dict(turn) for turn in data['history']],
                maxlen=self.max_turns
            )
            self.current_topic = data.get('current_topic')
            self.conversation_start = datetime.fromisoformat(data['conversation_start']) if data.get('conversation_start') else None
            self.turn_count = data.get('turn_count', 0)
            self.topic_history = data.get('topic_history', [])
            self.common_intents = data.get('common_intents', {})
            
            logger.info(f"📂 Loaded conversation from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")


def create_conversational_memory(max_turns: int = 50, context_window: int = 10):
    """Factory function to create conversational memory"""
    return ConversationalMemory(max_turns, context_window)
