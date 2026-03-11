"""
Trading Performance Tracker & Learning System

Tracks all trades (paper and live), analyzes performance,
and provides insights for improving the $1M strategy.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TradeRecord:
    """Record of a single trade"""
    trade_id: str
    timestamp: str
    venue: str  # 'polymarket', 'solana', 'base'
    market: str
    strategy: str  # 'prediction_market', 'memecoin', 'yield', 'swing', 'arbitrage'
    side: str  # 'buy', 'sell'
    outcome: str  # For prediction markets: 'YES', 'NO'
    size_usd: float
    entry_price: float
    exit_price: Optional[float]
    pnl_usd: Optional[float]
    pnl_percent: Optional[float]
    edge_at_entry: float
    confidence: float
    status: str  # 'open', 'closed', 'settled'
    paper_trade: bool
    tx_hash: Optional[str]
    reasoning: str
    lessons_learned: Optional[str]


class TradingPerformanceTracker:
    """
    Track and analyze trading performance across all venues.
    
    Helps AlleyBot learn from every trade and improve strategies.
    """
    
    def __init__(self, storage_dir: str = "memory/trading"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.trades_file = self.storage_dir / "trade_history.json"
        self.stats_file = self.storage_dir / "performance_stats.json"
        
        self.trades: List[TradeRecord] = []
        self.daily_stats: Dict[str, Any] = {}
        
        self._load_data()
    
    def _load_data(self):
        """Load historical trade data"""
        if self.trades_file.exists():
            try:
                with open(self.trades_file, 'r') as f:
                    data = json.load(f)
                    self.trades = [TradeRecord(**t) for t in data]
                print(f"📊 Loaded {len(self.trades)} historical trades")
            except Exception as e:
                print(f"⚠️ Failed to load trade history: {e}")
    
    def _save_data(self):
        """Save trade data to disk"""
        try:
            with open(self.trades_file, 'w') as f:
                json.dump([asdict(t) for t in self.trades], f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Failed to save trade history: {e}")
    
    def record_trade(self, trade: TradeRecord):
        """Record a new trade"""
        self.trades.append(trade)
        self._save_data()
        
        mode = "📝 PAPER" if trade.paper_trade else "🎯 LIVE"
        print(f"{mode} TRADE RECORDED: {trade.venue} | {trade.market[:40]}...")
        print(f"   Size: ${trade.size_usd:.2f} | Edge: {trade.edge_at_entry:.1%} | Conf: {trade.confidence:.1%}")
    
    def close_trade(self, trade_id: str, exit_price: float, pnl_usd: float, 
                    lessons: Optional[str] = None):
        """Close a trade and record PnL"""
        for trade in self.trades:
            if trade.trade_id == trade_id:
                trade.exit_price = exit_price
                trade.pnl_usd = pnl_usd
                trade.pnl_percent = (pnl_usd / trade.size_usd) * 100 if trade.size_usd > 0 else 0
                trade.status = 'closed'
                trade.lessons_learned = lessons
                
                self._save_data()
                
                emoji = "✅" if pnl_usd > 0 else "❌"
                print(f"{emoji} Trade closed: ${pnl_usd:+.2f} ({trade.pnl_percent:+.1f}%)")
                if lessons:
                    print(f"   Lesson: {lessons}")
                return True
        
        return False
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get performance summary for last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_trades = [
            t for t in self.trades 
            if datetime.fromisoformat(t.timestamp) > cutoff
        ]
        
        if not recent_trades:
            return {"message": "No trades in the last {} days".format(days)}
        
        # Calculate metrics
        total_trades = len(recent_trades)
        winning_trades = sum(1 for t in recent_trades if (t.pnl_usd or 0) > 0)
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_pnl = sum(t.pnl_usd or 0 for t in recent_trades)
        
        avg_winner = sum(
            t.pnl_usd for t in recent_trades 
            if (t.pnl_usd or 0) > 0
        ) / winning_trades if winning_trades > 0 else 0
        
        avg_loser = sum(
            t.pnl_usd for t in recent_trades 
            if (t.pnl_usd or 0) < 0
        ) / losing_trades if losing_trades > 0 else 0
        
        # Risk metrics
        open_positions = sum(1 for t in recent_trades if t.status == 'open')
        max_drawdown = self._calculate_max_drawdown(recent_trades)
        
        # Strategy breakdown
        strategies = {}
        for t in recent_trades:
            if t.strategy not in strategies:
                strategies[t.strategy] = {'trades': 0, 'pnl': 0, 'wins': 0}
            strategies[t.strategy]['trades'] += 1
            strategies[t.strategy]['pnl'] += t.pnl_usd or 0
            if (t.pnl_usd or 0) > 0:
                strategies[t.strategy]['wins'] += 1
        
        return {
            'period_days': days,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl_usd': total_pnl,
            'avg_winner': avg_winner,
            'avg_loser': avg_loser,
            'profit_factor': abs(avg_winner / avg_loser) if avg_loser != 0 else float('inf'),
            'open_positions': open_positions,
            'max_drawdown_percent': max_drawdown,
            'by_strategy': strategies,
            'paper_vs_live': {
                'paper': sum(1 for t in recent_trades if t.paper_trade),
                'live': sum(1 for t in recent_trades if not t.paper_trade)
            }
        }
    
    def _calculate_max_drawdown(self, trades: List[TradeRecord]) -> float:
        """Calculate maximum drawdown from trade history"""
        if not trades:
            return 0.0
        
        # Sort by timestamp
        sorted_trades = sorted(trades, key=lambda t: t.timestamp)
        
        peak = 0
        max_dd = 0
        running_pnl = 0
        
        for trade in sorted_trades:
            running_pnl += trade.pnl_usd or 0
            if running_pnl > peak:
                peak = running_pnl
            dd = peak - running_pnl
            if dd > max_dd:
                max_dd = dd
        
        # As percentage of peak
        return (max_dd / peak * 100) if peak > 0 else 0
    
    def get_strategy_insights(self) -> List[Dict]:
        """Generate insights for improving strategies"""
        insights = []
        
        # Group by strategy
        by_strategy = {}
        for t in self.trades:
            if t.strategy not in by_strategy:
                by_strategy[t.strategy] = []
            by_strategy[t.strategy].append(t)
        
        for strategy, trades in by_strategy.items():
            if len(trades) < 5:
                continue  # Need more data
            
            wins = sum(1 for t in trades if (t.pnl_usd or 0) > 0)
            total_pnl = sum(t.pnl_usd or 0 for t in trades)
            win_rate = wins / len(trades)
            
            insight = {
                'strategy': strategy,
                'trades': len(trades),
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'recommendation': None
            }
            
            # Generate recommendation
            if win_rate < 0.4:
                insight['recommendation'] = "STOP - Win rate too low, strategy needs revision"
                insight['priority'] = 'HIGH'
            elif win_rate < 0.5:
                insight['recommendation'] = "WARNING - Below 50% win rate, review edge calculation"
                insight['priority'] = 'MEDIUM'
            elif total_pnl < 0:
                insight['recommendation'] = "REVIEW - Negative PnL despite wins, check position sizing"
                insight['priority'] = 'HIGH'
            elif win_rate > 0.6 and total_pnl > 0:
                insight['recommendation'] = "SCALE UP - Strong performance, consider increasing allocation"
                insight['priority'] = 'LOW'
            else:
                insight['recommendation'] = "MONITOR - Continue tracking performance"
                insight['priority'] = 'MEDIUM'
            
            insights.append(insight)
        
        # Sort by priority
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        insights.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return insights
    
    def get_daily_report(self) -> str:
        """Generate daily trading report"""
        summary = self.get_performance_summary(days=1)
        
        if 'message' in summary:
            return f"📊 Daily Report: {summary['message']}"
        
        report = f"""📊 Daily Trading Report ({datetime.now().strftime('%Y-%m-%d')})

Performance (Last 24h):
- Trades: {summary['total_trades']}
- Win Rate: {summary['win_rate']:.1%}
- PnL: ${summary['total_pnl_usd']:+.2f}
- Open Positions: {summary['open_positions']}

Strategies:
"""
        for strategy, data in summary['by_strategy'].items():
            wr = data['wins'] / data['trades'] if data['trades'] > 0 else 0
            report += f"  {strategy}: {data['trades']} trades, {wr:.1%} WR, ${data['pnl']:+.2f}\n"
        
        # Add insights
        insights = self.get_strategy_insights()
        if insights:
            report += "\nInsights:\n"
            for i in insights[:3]:  # Top 3
                emoji = "🚨" if i['priority'] == 'HIGH' else "⚠️" if i['priority'] == 'MEDIUM' else "✅"
                report += f"{emoji} {i['strategy']}: {i['recommendation']}\n"
        
        return report
    
    def export_for_learning(self) -> List[Dict]:
        """Export trade data for AGI learning system"""
        return [
            {
                'trade_id': t.trade_id,
                'venue': t.venue,
                'strategy': t.strategy,
                'edge': t.edge_at_entry,
                'confidence': t.confidence,
                'outcome': 'win' if (t.pnl_usd or 0) > 0 else 'loss',
                'pnl_percent': t.pnl_percent,
                'reasoning': t.reasoning,
                'lessons': t.lessons_learned
            }
            for t in self.trades
            if t.status == 'closed'  # Only completed trades
        ]


# Global tracker instance
tracker: Optional[TradingPerformanceTracker] = None

def get_tracker() -> TradingPerformanceTracker:
    """Get or create global tracker instance"""
    global tracker
    if tracker is None:
        tracker = TradingPerformanceTracker()
    return tracker
