"""
Brain Validate Module - Moderation, safety gates, HITL

Extracted from autonomous_brain.py for modularity.
Contains: validation logic, confidence gates, HITL checks
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class BrainValidate:
    """Validate phase operations for the autonomous brain."""
    
    def __init__(self, brain):
        self.brain = brain
    
    def apply_cognitive_bias(self, proposals) -> None:
        """Apply belief-engine predictions to proposals."""
        self.brain._apply_cognitive_bias(proposals)
    
    def should_approve_action(self, action: Dict, domain: str) -> bool:
        """Check if action should be approved (HITL or automated)."""
        return self.brain._should_approve_action(action, domain)
    
    def check_safety_gates(self, action: Dict) -> bool:
        """Check safety gates before execution."""
        return self.brain._check_safety_gates(action)


def create_brain_validate(brain) -> BrainValidate:
    """Factory to create BrainValidate with brain reference."""
    return BrainValidate(brain)