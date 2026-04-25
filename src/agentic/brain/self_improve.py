"""
Brain Self-Improve Module - Skill gap detection, code generation

Extracted from autonomous_brain.py for modularity.
Contains: _phase_skill_gap_analysis, _detect_skill_gaps
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class BrainSelfImprove:
    """Self-improvement operations for the autonomous brain."""
    
    def __init__(self, brain):
        self.brain = brain
    
    async def skill_gap_analysis(self, observations, agi_kernel) -> None:
        """Main skill gap analysis phase."""
        await self.brain._phase_skill_gap_analysis(observations, agi_kernel)
    
    async def detect_skill_gaps(self, agi_kernel) -> List[Dict]:
        """Detect capability gaps requiring new skills."""
        return await self.brain._detect_skill_gaps(agi_kernel)
    
    def get_auto_skill_builder(self):
        """Get the auto skill builder if available."""
        return getattr(self.brain, 'auto_skill_builder', None)


def create_brain_self_improve(brain) -> BrainSelfImprove:
    """Factory to create BrainSelfImprove with brain reference."""
    return BrainSelfImprove(brain)