"""
Brain Trading Module - Market analysis, position management

Extracted from autonomous_brain.py for modularity.
Contains: autonomous trading logic
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


class BrainTrading:
    """Trading operations for the autonomous brain."""

    def __init__(self, brain):
        self.brain = brain

    async def _phase_revenue_intelligence(self, agi_kernel=None) -> List:
        """Scan for revenue opportunities and generate high-priority proposals.

        Runs every 5 cycles. Identifies trading, content, and service opportunities,
        scores them by expected value, and generates proposals with elevated confidence.
        """
        revenue_proposals = []
        try:
            cycle_count = self.brain.stats.get('cycles_completed', 0)
            if cycle_count < 1 or cycle_count % 5 != 0:
                return revenue_proposals

            from src.agentic.revenue_intelligence import get_revenue_intelligence
            ri = get_revenue_intelligence()

            # 1. Gather context from available data sources
            wallet_balances = None
            if hasattr(self.brain, 'plugin_manager') and self.brain.plugin_manager:
                onchain = self.brain.plugin_manager.get_plugin('onchain')
                if onchain and hasattr(onchain, 'get_wallet_balances'):
                    try:
                        wallet_balances = onchain.get_wallet_balances()
                    except Exception:
                        pass

            # 2. Scan for opportunities
            opps = ri.scan_all_opportunities(wallet_balances=wallet_balances)
            top = ri.get_top_opportunities(limit=3)

            if not top:
                return revenue_proposals

            logger.info(f"💰 === REVENUE INTELLIGENCE === {len(opps)} opportunities scanned, "
                        f"top: {top[0].source}.{top[0].action} (${top[0].expected_value:.2f} est)")

            # 3. Generate proposals for top opportunities
            from src.agentic.symod_core import SyModActionProposal
            for opp in top:
                if opp.outcome == 'failed' and opp.last_attempted:
                    continue  # don't re-attempt failed experiments without new info

                confidence = min(opp.confidence * (1 + 0.1 * opp.seen_count), 0.9)
                proposal = SyModActionProposal(
                    action_type=opp.action,
                    target_id=opp.source,
                    target_name=opp.description[:60],
                    confidence=confidence,
                    justification=f"Revenue opportunity: {opp.description} "
                                  f"(est ${opp.expected_value:.2f}, risk={opp.risk_level})",
                    metadata={
                        'plugin': opp.source,
                        'revenue_opportunity': True,
                        'source': opp.source,
                        'action': opp.action,
                        'expected_value': opp.expected_value,
                        'effort': opp.effort_estimate,
                        'risk': opp.risk_level,
                    }
                )
                revenue_proposals.append(proposal)

            # 4. Log P&L summary
            pnl = ri.get_pnl_summary()
            if pnl['total_events'] > 0:
                logger.info(f"   📊 P&L: ${pnl['total_net']:.4f} across {pnl['total_events']} events")
                for source, data in pnl['by_source'].items():
                    logger.info(f"      {source}: ${data['net']:.4f} ({data['count']} events)")

        except Exception as e:
            logger.debug(f"Revenue intelligence error: {e}")

        if revenue_proposals:
            logger.info(f"💰 Generated {len(revenue_proposals)} revenue-driven proposals")
        return revenue_proposals

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
