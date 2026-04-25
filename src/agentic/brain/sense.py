"""
Brain Sense Module - Observation gathering, platform polling

Extracted from autonomous_brain.py for modularity.
Contains: _phase_detect_opportunities, observation gathering
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class BrainSense:
    """Sense phase operations for the autonomous brain."""
    
    def __init__(self, brain):
        self.brain = brain
    
    async def detect_opportunities(self, observations) -> List[Dict]:
        """Detect opportunities from observations."""
        return await self.brain._phase_detect_opportunities(observations)
    
    def gather_observations(self, agi_kernel) -> List[Any]:
        """Gather observations from all platforms."""
        return self.brain._gather_observations(agi_kernel)
    
    def build_spine_context(self, observations, active_work_items, opportunities) -> Dict:
        """Build runtime spine context."""
        return self.brain._build_runtime_spine_context(
            observations=observations,
            active_work_items=active_work_items,
            opportunities=opportunities,
        )


def create_brain_sense(brain) -> BrainSense:
    """Factory to create BrainSense with brain reference."""
    return BrainSense(brain)