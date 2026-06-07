"""
Brain Cycle Coordinator - Orchestrates all brain phases

Central coordinator that imports and manages all brain phase modules.
Provides a clean interface to the autonomous brain functionality.
"""
import asyncio
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

    # ---- SENSE ----

    async def detect_opportunities(self):
        """Detect opportunities — delegated to sense module."""
        return await self.sense.detect_opportunities()

    async def gather_observations(self):
        """Gather observations from all platforms — delegated to sense module."""
        return await self.sense.gather_observations()

    async def feed_observations_to_world_state(self, observations):
        """Feed observations to world state DB."""
        await self.sense.feed_observations_to_world_state(observations)

    def build_spine_context(self, observations, active_work_items, opportunities):
        """Build runtime spine context."""
        return self.sense.build_spine_context(
            observations=observations,
            active_work_items=active_work_items,
            opportunities=opportunities,
        )

    # ---- THINK ----

    async def run_agi_orchestration(self):
        """Run AGI orchestration cycle."""
        return await self.think.run_agi_orchestration_cycle()

    async def goal_management(self, agi_kernel, observations):
        """Run goal management phase."""
        return self.think.phase_goal_management(agi_kernel, observations)

    async def memory_driven_thinking(self, observations, agi_kernel):
        """Run memory-driven thinking phase."""
        return await self.think.phase_memory_driven_thinking(observations, agi_kernel)

    async def assemble_proposals(self, agi_kernel, agi_actions, active_work_items,
                                  spine_context, memory_proposals=None,
                                  revenue_proposals=None, curiosity_proposals=None,
                                  intent_proposals=None):
        """Assemble and rank all proposals."""
        return await self.think.phase_assemble_proposals(
            agi_kernel, agi_actions, active_work_items, spine_context,
            memory_proposals, revenue_proposals, curiosity_proposals, intent_proposals
        )

    async def curiosity_goals(self, agi_kernel):
        """Run curiosity-driven goal generation."""
        return await self.think.phase_curiosity_goals(agi_kernel)

    async def maintain_persistent_intents(self, agi_kernel):
        """Maintain long-running objectives."""
        return await self.think.phase_maintain_persistent_intents(agi_kernel)

    async def cross_domain_synthesis(self, agi_kernel, observations, proposals):
        """Run cross-domain synthesis and strategic planning."""
        await self.think.phase_cross_domain_synthesis_and_planning(
            agi_kernel, observations, proposals
        )

    async def advance_active_plans(self, agi_kernel):
        """Advance active plans."""
        return await self.think.advance_active_plans(agi_kernel)

    def handle_idle_state(self, active_work_items, proposals, spine_context):
        """Handle idle state — generate exploratory actions."""
        return self.think.handle_idle_state(active_work_items, proposals, spine_context)

    async def generate_default_goals(self):
        """Generate default goals when none active."""
        return await self.think.generate_default_goals()

    # ---- ACT ----

    async def execute_proposals(self, proposals, agi_kernel, next_action):
        """Execute ranked proposals — delegating to act module."""
        return await self.act._phase_execute_proposals(proposals, agi_kernel, next_action)

    async def quick_profit_actions(self, checkpoint: str):
        """Check for quick profit actions at checkpoints."""
        return await self.act._check_for_quick_profit_actions(checkpoint)

    async def post_chess_wins(self):
        """Post queued chess win announcements."""
        await self.act._phase_chess_win_posts()

    # ---- LEARN ----

    async def periodic_reflection(self, agi_kernel):
        """Run periodic cognitive reflection."""
        await self.learn._phase_periodic_reflection(agi_kernel)

    async def consolidate_learning(self, agi_kernel):
        """Run learning consolidation."""
        await self.learn._phase_consolidate_learning(agi_kernel)

    def theory_of_mind(self, observations):
        """Run Theory of Mind inference."""
        return self.learn._phase_theory_of_mind(observations)

    async def causal_reasoning(self, observations, agi_kernel):
        """Run causal reasoning."""
        return await self.learn._phase_causal_reasoning(observations, agi_kernel)

    async def meta_adaptation(self, agi_kernel):
        """Run meta-learning parameter adaptation."""
        await self.learn._phase_meta_adaptation(agi_kernel)

    async def learning_acquisition(self, agi_kernel):
        """Turn learning gaps into skills."""
        await self.learn._phase_learning_goal_acquisition(agi_kernel)

    # ---- SELF-IMPROVE ----

    async def skill_gap_analysis(self, observations, agi_kernel):
        """Analyze capability gaps and auto-build skills."""
        await self.self_improve.skill_gap_analysis(observations, agi_kernel)

    async def plugin_discovery(self, agi_kernel):
        """Auto-generate plugins for detected gaps."""
        await self.self_improve.plugin_discovery_and_creation(agi_kernel)

    # ---- TRADING ----

    async def revenue_intelligence(self, agi_kernel):
        """Scan for revenue opportunities."""
        return await self.trading._phase_revenue_intelligence(agi_kernel)


def create_cycle_coordinator(brain) -> CycleCoordinator:
    """Factory to create CycleCoordinator with brain reference."""
    return CycleCoordinator(brain)
