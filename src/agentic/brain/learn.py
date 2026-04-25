"""
Brain Learn Module - Reflection, metacognition, belief update

Extracted from autonomous_brain.py for modularity.
Contains: reflection, belief updates, cognitive cycle integration
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BrainLearn:
    """Learn phase operations for the autonomous brain."""
    
    def __init__(self, brain):
        self.brain = brain
    
    def cognitive_reflect(self) -> Dict:
        """Run cognitive reflection at cycle end."""
        return self.brain.cognitive.reflect()
    
    def cognitive_record_outcome(
        self,
        action: str,
        domain: str,
        predicted: float,
        actual: bool,
        context: str = "",
        outcome_desc: str = "",
    ) -> Dict:
        """Record action outcome to cognitive systems."""
        return self.brain.cognitive.record_action_outcome(
            action=action,
            domain=domain,
            predicted_confidence=predicted,
            actual_success=actual,
            context=context,
            outcome_description=outcome_desc,
        )
    
    def get_belief_calibration(self) -> Dict:
        """Get belief calibration report."""
        return self.brain.cognitive.get_belief_calibration()
    
    def get_domain_strengths(self) -> Dict:
        """Get domain strength summary."""
        return self.brain.cognitive.get_domain_strengths()


def create_brain_learn(brain) -> BrainLearn:
    """Factory to create BrainLearn with brain reference."""
    return BrainLearn(brain)