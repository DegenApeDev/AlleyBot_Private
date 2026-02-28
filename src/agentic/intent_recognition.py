"""
Intent Recognition Engine

Deep intent understanding beyond keywords for JARVIS-style natural conversation.

Recognizes:
- Questions (information seeking)
- Commands (action requests)
- Feedback (positive/negative)
- Clarifications (follow-ups)
- Emotions (frustration, excitement)
- Implicit intents (unstated needs)

Integration:
- Uses ConversationalMemory for context
- Feeds into DialogueManager
- Enhances DecisionSystem
- Supports proactive suggestions
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of user intents"""
    QUESTION = "question"
    COMMAND = "command"
    FEEDBACK_POSITIVE = "feedback_positive"
    FEEDBACK_NEGATIVE = "feedback_negative"
    CLARIFICATION = "clarification"
    GREETING = "greeting"
    FAREWELL = "farewell"
    ACKNOWLEDGMENT = "acknowledgment"
    REQUEST_HELP = "request_help"
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"
    UNKNOWN = "unknown"


class EmotionType(Enum):
    """Types of emotions"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    SATISFIED = "satisfied"
    ANGRY = "angry"
    GRATEFUL = "grateful"


@dataclass
class IntentResult:
    """Result of intent recognition"""
    intent_type: IntentType
    confidence: float
    entities: Dict[str, Any]
    emotion: EmotionType
    implicit_needs: List[str]
    action_required: bool
    reasoning: str


class IntentRecognizer:
    """
    Deep intent understanding beyond keywords.
    
    Analyzes user input to understand:
    - What they're asking for
    - How they're feeling
    - What they really need (implicit)
    - What action to take
    """
    
    def __init__(self):
        # Intent patterns (regex-based for now, would use LLM in production)
        self.intent_patterns = {
            IntentType.QUESTION: [
                r'\b(what|when|where|who|why|how|which|can you|could you|would you|is|are|do|does)\b',
                r'\?$'
            ],
            IntentType.COMMAND: [
                r'\b(please|pls|plz|go|do|make|create|post|send|check|analyze|fix|update)\b',
                r'^(post|create|make|send|check|analyze|fix|update)\b'
            ],
            IntentType.FEEDBACK_POSITIVE: [
                r'\b(thanks|thank you|great|awesome|perfect|excellent|good|nice|love|appreciate)\b',
                r'\b(worked|works|fixed|solved)\b'
            ],
            IntentType.FEEDBACK_NEGATIVE: [
                r'\b(not working|doesn\'t work|broken|failed|error|wrong|bad|terrible)\b',
                r'\b(frustrated|annoyed|disappointed)\b'
            ],
            IntentType.GREETING: [
                r'\b(hi|hello|hey|morning|afternoon|evening|sup|yo)\b',
                r'^(hi|hello|hey)\b'
            ],
            IntentType.FAREWELL: [
                r'\b(bye|goodbye|see you|later|night|gn)\b'
            ],
            IntentType.ACKNOWLEDGMENT: [
                r'\b(ok|okay|sure|yes|yep|yeah|got it|understood|alright)\b',
                r'^(ok|okay|sure|yes|yep|yeah)$'
            ],
            IntentType.REQUEST_HELP: [
                r'\b(help|assist|support|stuck|confused|don\'t understand)\b'
            ],
            IntentType.COMPLAINT: [
                r'\b(slow|taking too long|always|never|every time)\b',
                r'\b(this is|it\'s)\s+(slow|broken|bad|terrible)\b'
            ]
        }
        
        # Emotion patterns
        self.emotion_patterns = {
            EmotionType.FRUSTRATED: [
                r'\b(ugh|argh|damn|wtf|seriously|again|still)\b',
                r'!{2,}',  # Multiple exclamation marks
                r'\b(tried \d+ times|third time|again and again)\b'
            ],
            EmotionType.EXCITED: [
                r'\b(wow|amazing|incredible|awesome|yes!|finally)\b',
                r'!+$',  # Ends with exclamation
                r'\b(can\'t wait|so excited|love it)\b'
            ],
            EmotionType.CONFUSED: [
                r'\b(confused|don\'t understand|what do you mean|huh|unclear)\b',
                r'\?{2,}'  # Multiple question marks
            ],
            EmotionType.GRATEFUL: [
                r'\b(thanks|thank you|appreciate|grateful|helpful)\b'
            ],
            EmotionType.HAPPY: [
                r'\b(happy|glad|pleased|satisfied|good)\b',
                r':\)|😊|😄|🎉'
            ]
        }
        
        # Entity patterns
        self.entity_patterns = {
            'platform': r'\b(moltx|telegram|twitter|discord|clawbr|moltbook)\b',
            'action': r'\b(post|tweet|share|send|create|analyze|check|fix)\b',
            'topic': r'\b(defi|nft|crypto|ai|agent|trading|yield)\b',
            'time': r'\b(today|tomorrow|tonight|morning|afternoon|evening|now|later)\b',
            'number': r'\b(\d+)\b'
        }
    
    def recognize_intent(self, 
                        user_input: str, 
                        conversation_context: List = None) -> IntentResult:
        """
        Classify user intent with confidence.
        
        Args:
            user_input: What the user said
            conversation_context: Recent conversation turns
            
        Returns:
            IntentResult with classification and metadata
        """
        user_input_lower = user_input.lower().strip()
        
        # Detect intent type
        intent_type, intent_confidence = self._classify_intent(user_input_lower)
        
        # Extract entities
        entities = self.extract_entities(user_input_lower)
        
        # Detect emotion
        emotion = self._detect_emotion(user_input_lower)
        
        # Detect implicit intents
        implicit_needs = self.detect_implicit_intent(
            user_input_lower, 
            conversation_context or []
        )
        
        # Determine if action required
        action_required = intent_type in [
            IntentType.COMMAND,
            IntentType.QUESTION,
            IntentType.REQUEST_HELP,
            IntentType.COMPLAINT
        ]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            intent_type, 
            emotion, 
            entities, 
            implicit_needs
        )
        
        return IntentResult(
            intent_type=intent_type,
            confidence=intent_confidence,
            entities=entities,
            emotion=emotion,
            implicit_needs=implicit_needs,
            action_required=action_required,
            reasoning=reasoning
        )
    
    def _classify_intent(self, user_input: str) -> Tuple[IntentType, float]:
        """
        Classify intent type with confidence.
        
        Returns:
            (IntentType, confidence_score)
        """
        scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    score += 1
            
            if score > 0:
                scores[intent_type] = score / len(patterns)
        
        if not scores:
            return IntentType.UNKNOWN, 0.3
        
        # Get highest scoring intent
        best_intent = max(scores.items(), key=lambda x: x[1])
        return best_intent[0], min(best_intent[1], 1.0)
    
    def _detect_emotion(self, user_input: str) -> EmotionType:
        """Detect user emotion from text"""
        for emotion, patterns in self.emotion_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return emotion
        
        return EmotionType.NEUTRAL
    
    def extract_entities(self, user_input: str) -> Dict[str, Any]:
        """
        Extract key entities (names, dates, amounts, platforms, etc.)
        
        Args:
            user_input: User's message
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches[0] if len(matches) == 1 else matches
        
        return entities
    
    def detect_implicit_intent(self, 
                               user_input: str,
                               conversation_history: List) -> List[str]:
        """
        Understand unstated needs from context.
        
        Args:
            user_input: Current user input
            conversation_history: Recent conversation turns
            
        Returns:
            List of implicit needs/intents
        """
        implicit_needs = []
        
        # Pattern: "It's been slow today" → Check metrics
        if re.search(r'\b(slow|quiet|not much|nothing happening)\b', user_input, re.IGNORECASE):
            implicit_needs.append('check_metrics')
            implicit_needs.append('suggest_action')
        
        # Pattern: "I'm working on X" → Offer help with X
        if re.search(r'\b(working on|building|creating|fixing)\b', user_input, re.IGNORECASE):
            implicit_needs.append('offer_assistance')
        
        # Pattern: Mentions problem without asking for help
        if re.search(r'\b(issue|problem|error|bug)\b', user_input, re.IGNORECASE):
            if not re.search(r'\b(help|fix|solve)\b', user_input, re.IGNORECASE):
                implicit_needs.append('offer_solution')
        
        # Pattern: Mentions goal/deadline
        if re.search(r'\b(need to|have to|should|deadline|by)\b', user_input, re.IGNORECASE):
            implicit_needs.append('track_goal')
            implicit_needs.append('offer_planning')
        
        # Pattern: Mentions trending/popular
        if re.search(r'\b(trending|popular|viral|hot)\b', user_input, re.IGNORECASE):
            implicit_needs.append('check_trends')
            implicit_needs.append('suggest_content')
        
        # Pattern: Time-based context
        if re.search(r'\b(today|tonight|tomorrow)\b', user_input, re.IGNORECASE):
            implicit_needs.append('check_schedule')
        
        return implicit_needs
    
    def _generate_reasoning(self,
                           intent_type: IntentType,
                           emotion: EmotionType,
                           entities: Dict,
                           implicit_needs: List[str]) -> str:
        """Generate human-readable reasoning for the classification"""
        parts = []
        
        # Intent
        parts.append(f"Intent: {intent_type.value}")
        
        # Emotion
        if emotion != EmotionType.NEUTRAL:
            parts.append(f"Emotion: {emotion.value}")
        
        # Entities
        if entities:
            entity_str = ", ".join(f"{k}={v}" for k, v in entities.items())
            parts.append(f"Entities: {entity_str}")
        
        # Implicit needs
        if implicit_needs:
            parts.append(f"Implicit needs: {', '.join(implicit_needs)}")
        
        return " | ".join(parts)
    
    def is_follow_up_question(self, user_input: str, previous_response: str = None) -> bool:
        """
        Detect if this is a follow-up question.
        
        Args:
            user_input: Current user input
            previous_response: Previous agent response
            
        Returns:
            True if follow-up question
        """
        user_input_lower = user_input.lower()
        
        # Follow-up indicators
        follow_up_words = [
            'what about',
            'how about',
            'and what',
            'also',
            'what else',
            'anything else',
            'more',
            'another'
        ]
        
        for phrase in follow_up_words:
            if phrase in user_input_lower:
                return True
        
        # Pronouns referring to previous context
        pronouns = ['it', 'that', 'this', 'those', 'these']
        if any(user_input_lower.startswith(p) for p in pronouns):
            return True
        
        return False
    
    def extract_action_request(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Extract specific action request from user input.
        
        Args:
            user_input: User's message
            
        Returns:
            Action specification or None
        """
        user_input_lower = user_input.lower()
        
        # Post/create content
        if re.search(r'\b(post|create|share|tweet)\b', user_input_lower):
            return {
                'action': 'create_content',
                'platform': self._extract_platform(user_input_lower),
                'topic': self._extract_topic(user_input_lower),
                'content': user_input  # Full input as content hint
            }
        
        # Check/analyze
        if re.search(r'\b(check|analyze|show|what\'s)\b', user_input_lower):
            return {
                'action': 'analyze',
                'target': self._extract_analysis_target(user_input_lower)
            }
        
        # Fix/debug
        if re.search(r'\b(fix|debug|solve|repair)\b', user_input_lower):
            return {
                'action': 'fix',
                'target': user_input
            }
        
        return None
    
    def _extract_platform(self, text: str) -> Optional[str]:
        """Extract platform mention"""
        platforms = ['moltx', 'telegram', 'twitter', 'discord', 'clawbr']
        for platform in platforms:
            if platform in text:
                return platform
        return None
    
    def _extract_topic(self, text: str) -> Optional[str]:
        """Extract topic mention"""
        topics = ['defi', 'nft', 'crypto', 'ai', 'agent', 'trading']
        for topic in topics:
            if topic in text:
                return topic
        return None
    
    def _extract_analysis_target(self, text: str) -> str:
        """Extract what user wants to analyze"""
        if 'engagement' in text or 'metrics' in text:
            return 'engagement'
        if 'trend' in text:
            return 'trends'
        if 'performance' in text:
            return 'performance'
        return 'general'


def create_intent_recognizer():
    """Factory function to create intent recognizer"""
    return IntentRecognizer()
