"""
Brain Act Module - Action execution, outcome recording

Extracted from autonomous_brain.py for modularity.
Contains: _phase_execute_proposals, proposal execution logic
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class BrainAct:
    """Act phase operations for the autonomous brain."""
    
    def __init__(self, brain):
        self.brain = brain
    
    async def execute_proposals(
        self,
        proposals: List,
        agi_kernel,
        next_action: Optional[Dict],
    ) -> int:
        """Execute proposals - main act phase."""
        return await self.brain._phase_execute_proposals(
            proposals, agi_kernel, next_action
        )
    
    async def execute_single_proposal(self, proposal, agi_kernel) -> bool:
        """Execute a single proposal."""
        return await self.brain._execute_proposal(proposal)


def create_brain_act(brain) -> BrainAct:
    """Factory to create BrainAct with brain reference."""
    return BrainAct(brain)