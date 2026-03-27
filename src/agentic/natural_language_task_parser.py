"""
Natural Language Task Parser

Converts natural language requests into executable goals.
When user says "launch a bankr token for yourself", this creates a goal
that AlleyBot will actually execute, not just chat about.

Constitutional Rules:
- All goals must pass trust validation
- Deceptive requests are blocked
- High-risk actions require manual approval
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ParsedTask:
    """Parsed task from natural language"""
    title: str
    description: str
    action_type: str
    plugin: str
    params: Dict[str, Any]
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    confidence: float
    implementation_plan: List[Dict[str, str]]
    evidence: str


class NaturalLanguageTaskParser:
    """
    Converts natural language requests into executable goals.
    
    Example:
        "launch a bankr token for yourself"
        → Goal: "Launch AlleyBot Bankr token"
        → Plan: [research, create, deploy, announce]
        → Actions: Execute through plugins
    """
    
    # Action patterns and their mappings
    ACTION_PATTERNS = {
        # Token/DeFi actions
        r'launch.*token|create.*token|deploy.*token': {
            'action_type': 'launch_token',
            'plugin': 'bankr',
            'priority': 'HIGH',
            'plan_template': [
                {'description': 'Research token parameters and requirements', 'status': 'pending'},
                {'description': 'Create token contract and metadata', 'status': 'pending'},
                {'description': 'Deploy token to blockchain', 'status': 'pending'},
                {'description': 'Announce token launch on social media', 'status': 'pending'},
            ]
        },
        r'trade|buy|sell|swap': {
            'action_type': 'execute_trade',
            'plugin': 'onchain',
            'priority': 'HIGH',
            'plan_template': [
                {'description': 'Analyze market conditions', 'status': 'pending'},
                {'description': 'Calculate optimal trade parameters', 'status': 'pending'},
                {'description': 'Execute trade through DEX', 'status': 'pending'},
                {'description': 'Verify trade completion', 'status': 'pending'},
            ]
        },
        
        # Social media actions
        r'post.*about|create.*post|share.*on': {
            'action_type': 'create_post',
            'plugin': 'moltx',
            'priority': 'MEDIUM',
            'plan_template': [
                {'description': 'Research topic and gather information', 'status': 'pending'},
                {'description': 'Generate engaging content', 'status': 'pending'},
                {'description': 'Post to platform', 'status': 'pending'},
                {'description': 'Monitor engagement', 'status': 'pending'},
            ]
        },
        r'engage.*with|reply.*to|respond.*to': {
            'action_type': 'engage',
            'plugin': 'moltx',
            'priority': 'MEDIUM',
            'plan_template': [
                {'description': 'Analyze target user/post', 'status': 'pending'},
                {'description': 'Generate thoughtful response', 'status': 'pending'},
                {'description': 'Post reply', 'status': 'pending'},
            ]
        },
        r'gain.*followers|increase.*engagement|grow.*audience': {
            'action_type': 'grow_audience',
            'plugin': 'moltx',
            'priority': 'MEDIUM',
            'plan_template': [
                {'description': 'Analyze current audience metrics', 'status': 'pending'},
                {'description': 'Create engagement strategy', 'status': 'pending'},
                {'description': 'Execute content plan', 'status': 'pending'},
                {'description': 'Monitor and adjust', 'status': 'pending'},
            ]
        },
        
        # Analysis actions
        r'analyze|research|investigate|study': {
            'action_type': 'analyze',
            'plugin': 'analytics',
            'priority': 'MEDIUM',
            'plan_template': [
                {'description': 'Gather relevant data', 'status': 'pending'},
                {'description': 'Perform analysis', 'status': 'pending'},
                {'description': 'Generate insights report', 'status': 'pending'},
                {'description': 'Share findings', 'status': 'pending'},
            ]
        },
        
        # Monitoring actions
        r'monitor|watch|track|observe': {
            'action_type': 'monitor',
            'plugin': 'analytics',
            'priority': 'LOW',
            'plan_template': [
                {'description': 'Set up monitoring parameters', 'status': 'pending'},
                {'description': 'Collect data continuously', 'status': 'pending'},
                {'description': 'Alert on significant changes', 'status': 'pending'},
            ]
        },
    }
    
    def __init__(self):
        """Initialize task parser"""
        pass
    
    def parse(self, message: str, sender_name: str = "User") -> Optional[ParsedTask]:
        """
        Parse natural language message into executable task.
        
        Args:
            message: Natural language request
            sender_name: Name of person making request
        
        Returns:
            ParsedTask or None if not actionable
        """
        message_lower = message.lower().strip()
        
        # Match against action patterns
        for pattern, config in self.ACTION_PATTERNS.items():
            if re.search(pattern, message_lower):
                return self._build_task(message, config, sender_name)
        
        # No clear action detected
        return None
    
    def _build_task(
        self,
        message: str,
        config: Dict,
        sender_name: str
    ) -> ParsedTask:
        """Build a ParsedTask from matched pattern"""
        
        # Extract key entities from message
        entities = self._extract_entities(message)
        
        # Build title
        title = self._generate_title(message, config['action_type'])
        
        # Build description
        description = f"User request from {sender_name}: {message}"
        
        # Build implementation plan
        plan = [step.copy() for step in config['plan_template']]
        
        # Determine confidence based on specificity
        confidence = self._calculate_confidence(message, entities)
        
        # Build params
        params = {
            'original_request': message,
            'sender': sender_name,
            'entities': entities,
        }
        
        return ParsedTask(
            title=title,
            description=description,
            action_type=config['action_type'],
            plugin=config['plugin'],
            params=params,
            priority=config['priority'],
            confidence=confidence,
            implementation_plan=plan,
            evidence=f"User request: {message}"
        )
    
    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract key entities from message"""
        entities = {}
        
        # Extract token names
        token_match = re.search(r'\b([A-Z]{2,10})\b', message)
        if token_match:
            entities['token'] = token_match.group(1)
        
        # Extract platform names
        platforms = ['moltx', 'clawbr', 'twitter', 'telegram', 'bankr']
        for platform in platforms:
            if platform in message.lower():
                entities['platform'] = platform
        
        # Extract numbers
        number_match = re.search(r'\b(\d+(?:\.\d+)?)\b', message)
        if number_match:
            entities['number'] = float(number_match.group(1))
        
        # Extract usernames
        username_match = re.search(r'@(\w+)', message)
        if username_match:
            entities['username'] = username_match.group(1)
        
        return entities
    
    def _generate_title(self, message: str, action_type: str) -> str:
        """Generate concise title for task"""
        # Take first 60 chars of message as title
        title = message[:60].strip()
        if len(message) > 60:
            title += "..."
        
        # Capitalize first letter
        title = title[0].upper() + title[1:] if title else f"Execute {action_type}"
        
        return title
    
    def _calculate_confidence(self, message: str, entities: Dict) -> float:
        """Calculate confidence score based on message specificity"""
        confidence = 0.7  # Base confidence
        
        # More entities = higher confidence
        confidence += len(entities) * 0.05
        
        # Longer message = more context = higher confidence
        if len(message) > 50:
            confidence += 0.1
        
        # Cap at 0.95
        return min(confidence, 0.95)


# Singleton
_task_parser_instance: Optional[NaturalLanguageTaskParser] = None


def get_task_parser() -> NaturalLanguageTaskParser:
    """Get or create task parser singleton"""
    global _task_parser_instance
    if _task_parser_instance is None:
        _task_parser_instance = NaturalLanguageTaskParser()
    return _task_parser_instance
