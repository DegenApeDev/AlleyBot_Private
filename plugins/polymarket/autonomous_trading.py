"""
Autonomous trading module for Polymarket plugin
Handles background scanning, analysis, and trading
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def autonomous_trading_loop(plugin):
    """Main autonomous trading loop"""
    logger.info("🎲 Autonomous trading loop started")
    
    while plugin.autonomous_running:
        try:
            logger.info("🔍 Scanning markets for opportunities...")
            
            # 1. Fetch top markets by volume
            markets = await plugin.fetch_markets(limit=20)
            logger.info(f"   Found {len(markets)} markets")
            
            # 2. Analyze each market
            opportunities = []
            for market in markets:
                try:
                    # Skip if already have position
                    if market.id in plugin.active_positions:
                        continue
                    
                    # Analyze market
                    analysis = await plugin.analyze_market(market)
                    
                    # Check if should trade
                    if analysis.should_trade:
                        opportunities.append({
                            'market': market,
                            'analysis': analysis
                        })
                        logger.info(f"   ✅ Opportunity: {market.question[:50]}... (edge: {analysis.edge:.1%})")
                
                except Exception as e:
                    logger.warning(f"   ⚠️ Failed to analyze {market.question[:30]}: {e}")
                    continue
            
            # 3. Execute trades for opportunities
            if opportunities:
                logger.info(f"💰 Found {len(opportunities)} trading opportunities")
                for opp in opportunities:
                    await execute_trade(plugin, opp['market'], opp['analysis'])
            else:
                logger.info("   No opportunities found this cycle")
            
            # 4. Update existing positions
            await update_positions(plugin)
            
            # 5. Log summary
            plugin.last_scan_time = datetime.now()
            logger.info(f"📊 Scan complete. Active positions: {len(plugin.active_positions)}")
            logger.info(f"   Total PnL: ${plugin.stats['total_pnl']:.2f} | Win rate: {plugin.stats['win_rate']:.1%}")
            
        except Exception as e:
            logger.error(f"❌ Error in autonomous trading loop: {e}")
            import traceback
            traceback.print_exc()
        
        # Wait for next scan
        await asyncio.sleep(plugin.scan_interval)
    
    logger.info("🎲 Autonomous trading loop stopped")


async def execute_trade(plugin, market, analysis):
    """Execute a trade (paper or live)"""
    try:
        from plugins.polymarket.polymarket import Position
        
        if plugin.paper_trading:
            # Paper trading - just track the position
            position = Position(
                market_id=market.id,
                market_question=market.question,
                outcome=analysis.predicted_outcome,
                shares=analysis.position_size * 100,  # Convert to shares
                avg_price=market.yes_price if analysis.predicted_outcome == 'YES' else market.no_price,
                current_price=market.yes_price if analysis.predicted_outcome == 'YES' else market.no_price,
                invested=analysis.position_size * 100 * (market.yes_price if analysis.predicted_outcome == 'YES' else market.no_price),
                current_value=analysis.position_size * 100 * (market.yes_price if analysis.predicted_outcome == 'YES' else market.no_price),
                pnl=0.0,
                opened_at=datetime.now(timezone.utc)
            )
            
            plugin.active_positions[market.id] = position
            
            # Update stats
            plugin.stats['total_trades'] += 1
            
            logger.info(f"📝 PAPER TRADE: {analysis.predicted_outcome} on '{market.question[:50]}...'")
            logger.info(f"   Size: {analysis.position_size:.1%} | Price: ${position.avg_price:.2f} | Edge: {analysis.edge:.1%}")
        else:
            # Live trading - use CLOB client
            logger.warning("⚠️ Live trading not implemented yet - staying in paper mode")
            # TODO: Implement live trading via py-clob-client
    
    except Exception as e:
        logger.error(f"❌ Failed to execute trade: {e}")


async def update_positions(plugin):
    """Update existing positions with current prices"""
    if not plugin.active_positions:
        return
    
    try:
        # Fetch current market data for active positions
        for market_id, position in list(plugin.active_positions.items()):
            market = plugin.market_cache.get(market_id)
            if not market:
                continue
            
            # Update current price and value
            current_price = market.yes_price if position.outcome == 'YES' else market.no_price
            position.current_price = current_price
            position.current_value = position.shares * current_price
            position.pnl = position.current_value - position.invested
            
            # Check if market resolved
            if market.resolved:
                await settle_position(plugin, market_id, market)
    
    except Exception as e:
        logger.error(f"❌ Failed to update positions: {e}")


async def settle_position(plugin, market_id, market):
    """Settle a resolved position"""
    position = plugin.active_positions.get(market_id)
    if not position:
        return
    
    try:
        # Check if won
        won = (position.outcome == market.resolution)
        
        if won:
            # Won - shares worth $1 each
            final_value = position.shares * 1.0
            position.pnl = final_value - position.invested
            plugin.stats['winning_trades'] += 1
            logger.info(f"✅ WON: {market.question[:50]}... | PnL: ${position.pnl:.2f}")
        else:
            # Lost - shares worth $0
            position.pnl = -position.invested
            plugin.stats['losing_trades'] += 1
            logger.info(f"❌ LOST: {market.question[:50]}... | Loss: ${position.pnl:.2f}")
        
        # Update stats
        plugin.stats['total_pnl'] += position.pnl
        total_trades = plugin.stats['winning_trades'] + plugin.stats['losing_trades']
        if total_trades > 0:
            plugin.stats['win_rate'] = plugin.stats['winning_trades'] / total_trades
        
        # Remove from active positions
        del plugin.active_positions[market_id]
        
        # Add to history
        plugin.prediction_history.append({
            'market': market.question,
            'outcome': position.outcome,
            'won': won,
            'pnl': position.pnl,
            'settled_at': datetime.now(timezone.utc).isoformat()
        })
    
    except Exception as e:
        logger.error(f"❌ Failed to settle position: {e}")
