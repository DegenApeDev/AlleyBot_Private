"""
Brain Think Module - Goal generation, belief evaluation, planning

Extracted from autonomous_brain.py for modularity.
Contains: _phase_assemble_proposals, _phase_goal_management, 
_phase_periodic_reflection, _phase_curiosity_goals
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class BrainThink:
    """Think phase operations for the autonomous brain."""
    
    def __init__(self, brain):
        self.brain = brain
    
    async def think_phase(
        self,
        agi_kernel,
        agi_actions,
        active_work_items,
        spine_context,
        observations,
    ) -> List:
        """Main think phase - assembles and ranks proposals."""
        return await self.brain._phase_assemble_proposals(
            agi_kernel, agi_actions, active_work_items, spine_context
        )
    
    async def goal_management(self, agi_kernel, observations) -> Optional[Dict]:
        """Goal generation and management."""
        return self.brain._phase_goal_management(agi_kernel, observations)
    
    async def curiosity_goals(self, agi_kernel, proposals) -> None:
        """Self-directed curiosity goals injection."""
        await self.brain._phase_curiosity_goals(agi_kernel, proposals)
    
    async def periodic_reflection(self, agi_kernel) -> None:
        """Periodic reflection - cognitive data review."""
        await self.brain._phase_periodic_reflection(agi_kernel)
    
    async def maintain_persistent_intents(self, agi_kernel, proposals) -> None:
        """Maintain long-running objectives."""
        await self.brain._phase_maintain_persistent_intents(agi_kernel, proposals)
    
    async def cross_domain_synthesis(self, agi_kernel, observations, proposals) -> None:
        """Cross-domain strategic planning."""
        await self.brain._phase_cross_domain_synthesis_and_planning(
            agi_kernel, observations, proposals
        )


def create_brain_think(brain) -> BrainThink:
    """Factory to create BrainThink with brain reference."""
    return BrainThink(brain)