"""
Trading Analytics Plugin for AlleyBot
Tracks all trades and provides performance analytics
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from plugin_manager import AlleyBotPlugin


class TradingAnalytics(AlleyBotPlugin):
    """Track and analyze trading performance"""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "trading_analytics"
        self.version = "1.0.0"
        
        # Database path
        self.db_path = Path("data/trading_analytics.db")
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        print("✅ Trading Analytics initialized")
    
    def _init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                chain TEXT NOT NULL,
                dex TEXT NOT NULL,
                token_in TEXT NOT NULL,
                token_out TEXT NOT NULL,
                amount_in REAL NOT NULL,
                amount_out REAL NOT NULL,
                price_impact REAL,
                slippage_bps INTEGER,
                fees_usd REAL,
                gas_cost_usd REAL,
                net_profit_usd REAL,
                profit_percent REAL,
                tx_hash TEXT,
                mev_protected INTEGER DEFAULT 0,
                strategy TEXT,
                notes TEXT
            )
        """)
        
        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_performance (
                date TEXT PRIMARY KEY,
                total_trades INTEGER DEFAULT 0,
                profitable_trades INTEGER DEFAULT 0,
                total_profit_usd REAL DEFAULT 0,
                total_fees_usd REAL DEFAULT 0,
                total_gas_usd REAL DEFAULT 0,
                best_trade_profit REAL DEFAULT 0,
                worst_trade_profit REAL DEFAULT 0,
                avg_profit_percent REAL DEFAULT 0,
                win_rate REAL DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a completed trade
        
        Args:
            trade_data: Trade information including:
                - chain: 'solana' or 'base'
                - dex: 'jupiter', 'uniswap', etc.
                - token_in, token_out: Token symbols
                - amount_in, amount_out: Trade amounts
                - price_impact: Price impact %
                - slippage_bps: Slippage in basis points
                - fees_usd, gas_cost_usd: Costs in USD
                - net_profit_usd: Net profit/loss
                - tx_hash: Transaction hash
                - mev_protected: Boolean
                - strategy: Trading strategy used
        
        Returns:
            Success status and trade ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            
            # Calculate profit percent
            profit_percent = 0
            if trade_data.get('amount_in', 0) > 0:
                profit_percent = (trade_data.get('net_profit_usd', 0) / trade_data['amount_in']) * 100
            
            cursor.execute("""
                INSERT INTO trades (
                    timestamp, chain, dex, token_in, token_out,
                    amount_in, amount_out, price_impact, slippage_bps,
                    fees_usd, gas_cost_usd, net_profit_usd, profit_percent,
                    tx_hash, mev_protected, strategy, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                trade_data.get('chain', 'unknown'),
                trade_data.get('dex', 'unknown'),
                trade_data.get('token_in', ''),
                trade_data.get('token_out', ''),
                trade_data.get('amount_in', 0),
                trade_data.get('amount_out', 0),
                trade_data.get('price_impact', 0),
                trade_data.get('slippage_bps', 0),
                trade_data.get('fees_usd', 0),
                trade_data.get('gas_cost_usd', 0),
                trade_data.get('net_profit_usd', 0),
                profit_percent,
                trade_data.get('tx_hash', ''),
                1 if trade_data.get('mev_protected') else 0,
                trade_data.get('strategy', 'manual'),
                trade_data.get('notes', '')
            ))
            
            trade_id = cursor.lastrowid
            conn.commit()
            
            # Update daily performance
            self._update_daily_performance(timestamp[:10])
            
            conn.close()
            
            return {
                'success': True,
                'trade_id': trade_id,
                'timestamp': timestamp
            }
        except Exception as e:
            return {'success': False, 'error': f'Failed to record trade: {str(e)}'}
    
    def _update_daily_performance(self, date: str):
        """Update daily performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate daily stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN net_profit_usd > 0 THEN 1 ELSE 0 END) as profitable_trades,
                SUM(net_profit_usd) as total_profit,
                SUM(fees_usd) as total_fees,
                SUM(gas_cost_usd) as total_gas,
                MAX(net_profit_usd) as best_trade,
                MIN(net_profit_usd) as worst_trade,
                AVG(profit_percent) as avg_profit_pct
            FROM trades
            WHERE DATE(timestamp) = ?
        """, (date,))
        
        stats = cursor.fetchone()
        
        if stats and stats[0] > 0:
            total_trades, profitable_trades, total_profit, total_fees, total_gas, best_trade, worst_trade, avg_profit_pct = stats
            win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
            
            cursor.execute("""
                INSERT OR REPLACE INTO daily_performance (
                    date, total_trades, profitable_trades, total_profit_usd,
                    total_fees_usd, total_gas_usd, best_trade_profit,
                    worst_trade_profit, avg_profit_percent, win_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date, total_trades, profitable_trades, total_profit or 0,
                total_fees or 0, total_gas or 0, best_trade or 0,
                worst_trade or 0, avg_profit_pct or 0, win_rate
            ))
            
            conn.commit()
        
        conn.close()
    
    def get_performance_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get trading performance statistics
        
        Args:
            days: Number of days to analyze (default: 30)
        
        Returns:
            Performance metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Overall stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN net_profit_usd > 0 THEN 1 ELSE 0 END) as profitable_trades,
                    SUM(net_profit_usd) as total_profit,
                    SUM(fees_usd) as total_fees,
                    SUM(gas_cost_usd) as total_gas,
                    AVG(profit_percent) as avg_profit_pct,
                    MAX(net_profit_usd) as best_trade,
                    MIN(net_profit_usd) as worst_trade
                FROM trades
                WHERE DATE(timestamp) >= ?
            """, (start_date,))
            
            stats = cursor.fetchone()
            
            if not stats or stats[0] == 0:
                conn.close()
                return {
                    'success': True,
                    'period_days': days,
                    'total_trades': 0,
                    'message': 'No trades in this period'
                }
            
            total_trades, profitable_trades, total_profit, total_fees, total_gas, avg_profit_pct, best_trade, worst_trade = stats
            
            win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
            net_profit = (total_profit or 0) - (total_fees or 0) - (total_gas or 0)
            
            # Strategy breakdown
            cursor.execute("""
                SELECT 
                    strategy,
                    COUNT(*) as trades,
                    SUM(net_profit_usd) as profit,
                    AVG(profit_percent) as avg_pct
                FROM trades
                WHERE DATE(timestamp) >= ?
                GROUP BY strategy
                ORDER BY profit DESC
            """, (start_date,))
            
            strategies = [
                {
                    'strategy': row[0],
                    'trades': row[1],
                    'profit': row[2] or 0,
                    'avg_profit_pct': row[3] or 0
                }
                for row in cursor.fetchall()
            ]
            
            # Chain breakdown
            cursor.execute("""
                SELECT 
                    chain,
                    COUNT(*) as trades,
                    SUM(net_profit_usd) as profit
                FROM trades
                WHERE DATE(timestamp) >= ?
                GROUP BY chain
            """, (start_date,))
            
            chains = {row[0]: {'trades': row[1], 'profit': row[2] or 0} for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'success': True,
                'period_days': days,
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'win_rate': round(win_rate, 2),
                'total_profit_usd': round(total_profit or 0, 2),
                'total_fees_usd': round(total_fees or 0, 2),
                'total_gas_usd': round(total_gas or 0, 2),
                'net_profit_usd': round(net_profit, 2),
                'avg_profit_percent': round(avg_profit_pct or 0, 2),
                'best_trade_usd': round(best_trade or 0, 2),
                'worst_trade_usd': round(worst_trade or 0, 2),
                'strategies': strategies,
                'chains': chains
            }
        except Exception as e:
            return {'success': False, 'error': f'Failed to get stats: {str(e)}'}
    
    def get_recent_trades(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent trades"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    timestamp, chain, dex, token_in, token_out,
                    amount_in, amount_out, net_profit_usd, profit_percent,
                    tx_hash
                FROM trades
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            trades = [
                {
                    'timestamp': row[0],
                    'chain': row[1],
                    'dex': row[2],
                    'pair': f"{row[3]}/{row[4]}",
                    'amount_in': row[5],
                    'amount_out': row[6],
                    'profit_usd': round(row[7] or 0, 2),
                    'profit_pct': round(row[8] or 0, 2),
                    'tx_hash': row[9][:16] + '...' if row[9] else ''
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                'success': True,
                'trades': trades,
                'count': len(trades)
            }
        except Exception as e:
            return {'success': False, 'error': f'Failed to get trades: {str(e)}'}


PLUGIN_INFO = {
    "name": "trading_analytics",
    "version": "1.0.0",
    "description": "Track and analyze trading performance",
    "author": "AlleyBot"
}


def create_plugin(config=None):
    return TradingAnalytics(config or {})
