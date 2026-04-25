"""
Brain Trading Module - Market analysis, position management

Extracted from autonomous_brain.py for modularity.
Contains: autonomous trading logic
"""

import logging

logger = logging.getLogger(__name__)


class BrainTrading:
    """Trading operations for the autonomous brain."""
    
    def __init__(self, brain):
        self.brain = brain
    
    async def analyze_markets(self):
        """Analyze markets and find opportunities."""
        if hasattr(self.brain, 'autonomous_trading') and self.brain.autonomous_trading:
            return await self.brain.autonomous_trading.analyze_markets()
        return []
    
    async def execute_trade(self, trade_proposal):
        """Execute a trade."""
        if hasattr(self.brain, 'autonomous_trading') and self.brain.autonomous_trading:
            return await self.brain.autonomous_trading.execute_trade(trade_proposal)
        return None
    
    def gather_trading_observations(self):
        """Gather trading observations."""
        from src.agentic.trading_observations import gather_trading_observations
        return gather_trading_observations()


def create_brain_trading(brain) -> BrainTrading:
    """Factory to create BrainTrading with brain reference."""
    return BrainTrading(brain)