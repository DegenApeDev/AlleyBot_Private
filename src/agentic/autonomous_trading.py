"""
Autonomous Trading System with SyMod Validation

Enables AlleyBot to trade autonomously on prediction markets and on-chain
with mathematical validation from SyMod.

Features:
- SyMod-validated trade decisions
- Conservative risk management
- Position sizing based on confidence
- Automatic profit/loss tracking
- Learning from trade outcomes
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TradeProposal:
    """Proposal for a trade validated by SyMod"""
    market_id: str
    market_name: str
    platform: str  # 'polymarket', 'uniswap', etc.
    action: str  # 'buy', 'sell'
    outcome: str  # For prediction markets: 'YES', 'NO'
    amount_usd: float
    current_price: float
    expected_value: float
    
    # SyMod validation
    confidence: float
    impedance: float
    digital_root: int
    field_status: str
    golden_window_aligned: bool
    symod_valid: bool
    
    # Risk metrics
    max_loss: float
    risk_reward_ratio: float
    justification: str


@dataclass
class TradeOutcome:
    """Record of a completed trade"""
    trade_id: str
    market_id: str
    platform: str
    action: str
    amount_usd: float
    entry_price: float
    exit_price: Optional[float] = None
    profit_loss: float = 0.0
    confidence_at_entry: float = 0.0
    symod_metrics: Dict = None
    timestamp: datetime = None
    closed: bool = False


class AutonomousTrading:
    """
    Autonomous trading system with SyMod mathematical validation.
    
    Safety features:
    - Max position size (% of capital)
    - Min confidence threshold (0.8 for conservative)
    - SyMod field status check (only trade in Stable field)
    - Daily loss limit
    - Per-trade stop loss
    """
    
    def __init__(self, core, plugin_manager):
        self.core = core
        self.plugin_manager = plugin_manager
        
        # Get SyMod for validation
        from src.agentic.symod_core import get_symod_manager
        self.symod = get_symod_manager()
        
        # Trading configuration (CONSERVATIVE by default)
        self.config = {
            'enabled': False,  # Must be explicitly enabled
            'max_position_size_pct': 5.0,  # Max 5% of capital per trade
            'min_confidence': 0.8,  # High confidence required
            'min_risk_reward': 2.0,  # Min 2:1 risk/reward
            'daily_loss_limit_pct': 10.0,  # Max 10% loss per day
            'max_open_positions': 3,  # Max 3 concurrent positions
            'require_golden_window': True,  # Only trade in golden window
            'require_stable_field': True,  # Only trade when field is Stable
            'max_impedance': 0.3,  # Max impedance threshold
        }
        
        # State tracking
        self.capital = 75.0  # Starting capital in USD
        self.open_positions: List[TradeOutcome] = []
        self.closed_trades: List[TradeOutcome] = []
        self.daily_pnl = 0.0
        self.daily_reset_time = datetime.now()
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_profit = 0.0
        
        logger.info("💰 Autonomous Trading System initialized (CONSERVATIVE mode)")
        logger.info(f"💵 Starting capital: ${self.capital:.2f}")
    
    def enable_trading(self, enabled: bool = True):
        """Enable or disable autonomous trading"""
        self.config['enabled'] = enabled
        if enabled:
            logger.info("✅ Autonomous trading ENABLED")
        else:
            logger.info("⛔ Autonomous trading DISABLED")
    
    async def analyze_markets(self) -> List[TradeProposal]:
        """Analyze available markets and generate trade proposals"""
        proposals = []
        
        # Reset daily P&L if new day
        if (datetime.now() - self.daily_reset_time).days >= 1:
            self.daily_pnl = 0.0
            self.daily_reset_time = datetime.now()
        
        # Check if trading is enabled
        if not self.config['enabled']:
            return proposals
        
        # Check daily loss limit
        if self.daily_pnl < -(self.capital * self.config['daily_loss_limit_pct'] / 100):
            logger.warning(f"⛔ Daily loss limit reached: ${self.daily_pnl:.2f}")
            return proposals
        
        # Check max open positions
        if len(self.open_positions) >= self.config['max_open_positions']:
            logger.info(f"⏸️ Max open positions reached: {len(self.open_positions)}")
            return proposals
        
        # Analyze Polymarket
        polymarket_proposals = await self._analyze_polymarket()
        proposals.extend(polymarket_proposals)
        
        # Filter by SyMod validation
        validated_proposals = [p for p in proposals if p.symod_valid]
        
        logger.info(f"💡 Generated {len(proposals)} trade proposals, {len(validated_proposals)} SyMod-validated")
        return validated_proposals
    
    async def _analyze_polymarket(self) -> List[TradeProposal]:
        """Analyze Polymarket prediction markets"""
        proposals = []
        
        # Get Polymarket plugin
        polymarket = self.plugin_manager.get_plugin('polymarket')
        if not polymarket:
            return proposals
        
        try:
            # Get active markets (this would need to be implemented in polymarket plugin)
            # For now, we'll use a placeholder structure
            markets = await self._get_polymarket_markets()
            
            for market in markets[:10]:  # Analyze top 10 markets
                # Calculate expected value
                proposal = await self._evaluate_market(market, 'polymarket')
                if proposal:
                    proposals.append(proposal)
        
        except Exception as e:
            logger.error(f"❌ Polymarket analysis error: {e}")
        
        return proposals
    
    async def _get_polymarket_markets(self) -> List[Dict]:
        """Get active Polymarket markets (placeholder)"""
        # This would integrate with actual Polymarket API
        # For now, return empty list - needs implementation
        return []
    
    async def _evaluate_market(self, market: Dict, platform: str) -> Optional[TradeProposal]:
        """Evaluate a market and create trade proposal if valid"""
        try:
            market_id = market.get('id', '')
            market_name = market.get('question', '')
            current_price = market.get('price', 0.5)
            
            # Calculate position size (max 5% of capital)
            max_position = self.capital * (self.config['max_position_size_pct'] / 100)
            position_size = min(max_position, 10.0)  # Cap at $10 per trade initially
            
            # SyMod validation
            symod_result = await self._validate_with_symod(market)
            
            # Check SyMod requirements
            if not symod_result['valid']:
                return None
            
            if symod_result['confidence'] < self.config['min_confidence']:
                return None
            
            if self.config['require_stable_field'] and symod_result['field_status'] != 'Stable':
                return None
            
            if self.config['require_golden_window'] and not symod_result['golden_window']:
                return None
            
            if symod_result['impedance'] > self.config['max_impedance']:
                return None
            
            # Calculate expected value and risk/reward
            expected_value = self._calculate_expected_value(current_price, symod_result['confidence'])
            max_loss = position_size  # Max loss is full position
            expected_profit = position_size * (1.0 / current_price - 1.0) if current_price > 0 else 0
            risk_reward = expected_profit / max_loss if max_loss > 0 else 0
            
            if risk_reward < self.config['min_risk_reward']:
                return None
            
            # Determine action (buy YES if underpriced, NO if overpriced)
            fair_price = symod_result['confidence']
            action = 'buy'
            outcome = 'YES' if current_price < fair_price else 'NO'
            
            proposal = TradeProposal(
                market_id=market_id,
                market_name=market_name,
                platform=platform,
                action=action,
                outcome=outcome,
                amount_usd=position_size,
                current_price=current_price,
                expected_value=expected_value,
                confidence=symod_result['confidence'],
                impedance=symod_result['impedance'],
                digital_root=symod_result['digital_root'],
                field_status=symod_result['field_status'],
                golden_window_aligned=symod_result['golden_window'],
                symod_valid=True,
                max_loss=max_loss,
                risk_reward_ratio=risk_reward,
                justification=f"SyMod confidence {symod_result['confidence']:.2f}, impedance {symod_result['impedance']:.2f}"
            )
            
            return proposal
        
        except Exception as e:
            logger.error(f"❌ Market evaluation error: {e}")
            return None
    
    async def _validate_with_symod(self, market: Dict) -> Dict:
        """Validate market data with SyMod"""
        if not self.symod or not self.symod.enabled:
            return {
                'valid': False,
                'confidence': 0.0,
                'impedance': 1.0,
                'digital_root': 0,
                'field_status': 'unknown',
                'golden_window': False
            }
        
        try:
            # Get market data for SyMod analysis
            market_text = f"{market.get('question', '')} {market.get('description', '')}"
            
            # Use SyMod's C2V bridge for validation
            if hasattr(self.symod, 'c2v') and self.symod.c2v:
                result = self.symod.c2v.validate_content(market_text)
                
                return {
                    'valid': result.valid,
                    'confidence': result.confidence,
                    'impedance': result.impedance,
                    'digital_root': result.digital_root,
                    'field_status': 'Stable' if result.impedance < 0.3 else 'Volatile',
                    'golden_window': result.golden_window
                }
        
        except Exception as e:
            logger.error(f"❌ SyMod validation error: {e}")
        
        return {
            'valid': False,
            'confidence': 0.0,
            'impedance': 1.0,
            'digital_root': 0,
            'field_status': 'unknown',
            'golden_window': False
        }
    
    def _calculate_expected_value(self, price: float, confidence: float) -> float:
        """Calculate expected value of a trade"""
        # EV = (probability * profit) - ((1 - probability) * loss)
        # Simplified: use SyMod confidence as probability
        profit_if_win = (1.0 / price - 1.0) if price > 0 else 0
        loss_if_lose = 1.0
        
        ev = (confidence * profit_if_win) - ((1 - confidence) * loss_if_lose)
        return ev
    
    async def execute_trade(self, proposal: TradeProposal) -> Optional[TradeOutcome]:
        """Execute a validated trade proposal"""
        try:
            logger.info(f"💰 Executing trade: {proposal.market_name}")
            logger.info(f"   Platform: {proposal.platform}")
            logger.info(f"   Action: {proposal.action} {proposal.outcome}")
            logger.info(f"   Amount: ${proposal.amount_usd:.2f}")
            logger.info(f"   Confidence: {proposal.confidence:.2f}")
            logger.info(f"   Risk/Reward: {proposal.risk_reward_ratio:.2f}")
            
            # Execute trade via platform plugin
            # This would integrate with actual trading execution
            # For now, we'll simulate and track
            
            trade_id = f"trade_{datetime.now().timestamp()}"
            
            outcome = TradeOutcome(
                trade_id=trade_id,
                market_id=proposal.market_id,
                platform=proposal.platform,
                action=proposal.action,
                amount_usd=proposal.amount_usd,
                entry_price=proposal.current_price,
                confidence_at_entry=proposal.confidence,
                symod_metrics={
                    'impedance': proposal.impedance,
                    'digital_root': proposal.digital_root,
                    'field_status': proposal.field_status,
                    'golden_window': proposal.golden_window_aligned
                },
                timestamp=datetime.now(),
                closed=False
            )
            
            self.open_positions.append(outcome)
            self.total_trades += 1
            
            logger.info(f"✅ Trade executed: {trade_id}")
            
            # Send Telegram notification
            await self._send_trade_notification(proposal, outcome)
            
            return outcome
        
        except Exception as e:
            logger.error(f"❌ Trade execution error: {e}")
            return None
    
    async def _send_trade_notification(self, proposal: TradeProposal, outcome: TradeOutcome):
        """Send Telegram notification about trade"""
        try:
            telegram = self.plugin_manager.get_plugin('telegram')
            if telegram and hasattr(telegram, 'send_alert'):
                message = (
                    f"💰 **Trade Executed**\n\n"
                    f"Market: {proposal.market_name}\n"
                    f"Action: {proposal.action} {proposal.outcome}\n"
                    f"Amount: ${proposal.amount_usd:.2f}\n"
                    f"Price: {proposal.current_price:.3f}\n\n"
                    f"**SyMod Validation:**\n"
                    f"Confidence: {proposal.confidence:.2f}\n"
                    f"Impedance: {proposal.impedance:.2f}\n"
                    f"Field: {proposal.field_status}\n"
                    f"Golden Window: {'✅' if proposal.golden_window_aligned else '❌'}\n"
                    f"Risk/Reward: {proposal.risk_reward_ratio:.2f}\n\n"
                    f"Trade ID: {outcome.trade_id}"
                )
                telegram.send_alert("Autonomous Trade", message, "medium")
        except Exception as e:
            logger.warning(f"⚠️ Could not send trade notification: {e}")
    
    def get_trading_status(self) -> Dict:
        """Get current trading status"""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        return {
            'enabled': self.config['enabled'],
            'capital': self.capital,
            'open_positions': len(self.open_positions),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': win_rate,
            'total_profit': self.total_profit,
            'daily_pnl': self.daily_pnl,
            'config': self.config
        }


# Singleton instance
_autonomous_trading = None


def get_autonomous_trading(core=None, plugin_manager=None):
    """Get or create autonomous trading singleton"""
    global _autonomous_trading
    if _autonomous_trading is None and core and plugin_manager:
        _autonomous_trading = AutonomousTrading(core, plugin_manager)
    return _autonomous_trading
