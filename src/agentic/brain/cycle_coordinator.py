"""
Brain Cycle Coordinator - Orchestrates all brain phases

Central coordinator that imports and manages all brain phase modules.
Provides a clean interface to the autonomous brain functionality.
"""

import logging
from typing import Dict, List, Any, Optional

from .sense import create_brain_sense
from .think import create_brain_think
from .validate import create_brain_validate
from .act import create_brain_act
from .learn import create_brain_learn
from .self_improve import create_brain_self_improve
from .trading import create_brain_trading

logger = logging.getLogger(__name__)


class CycleCoordinator:
    """
    Central coordinator for brain cycle phases.
    
    Imports all phase modules and provides a unified interface.
    This reduces autonomous_brain.py complexity by delegating
    to specialized phase handlers.
    """
    
    def __init__(self, brain):
        self.brain = brain
        
        # Initialize all phase handlers
        self.sense = create_brain_sense(brain)
        self.think = create_brain_think(brain)
        self.validate = create_brain_validate(brain)
        self.act = create_brain_act(brain)
        self.learn = create_brain_learn(brain)
        self.self_improve = create_brain_self_improve(brain)
        self.trading = create_brain_trading(brain)
        
        logger.info("✅ CycleCoordinator initialized with all phase handlers")
    
    async def run_sense_phase(self, observations, agi_kernel) -> List[Dict]:
        """Run SENSE - gather observations and detect opportunities."""
        ops = await self.sense.detect_opportunities(observations)
        return ops
    
    async def run_think_phase(
        self,
        agi_kernel,
        agi_actions,
        active_work_items,
        spine_context,
        observations,
    ) -> List:
        """Run THINK - goal generation, planning, reflection."""
        proposals = await self.think.think_phase(
            agi_kernel, agi_actions, active_work_items, spine_context, observations
        )
        
        await self.think.curiosity_goals(agi_kernel, proposals)
        await self.think.periodic_reflection(agi_kernel)
        await self.think.maintain_persistent_intents(agi_kernel, proposals)
        await self.think.cross_domain_synthesis(agi_kernel, observations, proposals)
        
        return proposals
    
    async def run_validate_phase(self, proposals) -> None:
        """Run VALIDATE - apply cognitive bias and safety gates."""
        self.validate.apply_cognitive_bias(proposals)
    
    async def run_act_phase(
        self,
        proposals: List,
        agi_kernel,
        next_action: Optional[Dict],
    ) -> int:
        """Run ACT - execute proposals."""
        return await self.act.execute_proposals(proposals, agi_kernel, next_action)
    
    async def run_learn_phase(self, success: bool, result: Any = None) -> None:
        """Run LEARN - cognitive reflection and belief updates."""
        cognitive_end = self.learn.cognitive_reflect()
        beliefs = self.learn.get_domain_strengths()
        calibration = self.learn.get_belief_calibration()
        
        logger.info(
            f"🧠 Cycle end: {cognitive_end.get('overall_assessment', '?')} | "
            f"Beliefs: {len(beliefs)} domains | "
            f"Calibrated: {calibration.get('calibrated', '?')}"
        )
    
    async def run_self_improve_phase(self, observations, agi_kernel) -> None:
        """Run SELF-IMPROVE - skill gap detection and code generation."""
        await self.self_improve.skill_gap_analysis(observations, agi_kernel)
    
    async def run_trading_phase(self) -> None:
        """Run trading analysis if enabled."""
        if hasattr(self.brain, 'autonomous_trading') and self.brain.autonomous_trading:
            try:
                trade_proposals = await self.trading.analyze_markets()
                if trade_proposals:
                    logger.info(f"💰 Found {len(trade_proposals)} trade opportunities")
            except Exception as e:
                logger.debug(f"Trading analysis error: {e}")


def create_cycle_coordinator(brain) -> CycleCoordinator:
    """Factory to create CycleCoordinator with brain reference."""
    return CycleCoordinator(brain)