"""
Backtesting module for Base Yield Hunter
Historical performance analysis and strategy optimization
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np


class YieldBacktester:
    """Backtesting engine for yield farming strategies"""
    
    def __init__(self):
        self.historical_data = {}
        self.performance_metrics = {}
    
    async def fetch_historical_apy_data(self, pool_address: str, days: int = 30) -> List[Dict[str, Any]]:
        """Fetch historical APY data for a specific pool"""
        try:
            # This would integrate with DefiLlama historical API or similar
            # For now, simulate historical data
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            historical_data = []
            current_date = start_date
            
            # Simulate APY variations
            base_apy = np.random.uniform(5, 25)  # Random base APY
            
            while current_date <= end_date:
                # Add some realistic variation
                daily_variation = np.random.normal(0, 0.02)  # 2% daily variation
                weekend_effect = 1.0
                if current_date.weekday() >= 5:  # Weekend
                    weekend_effect = 0.98
                
                apy = base_apy * (1 + daily_variation) * weekend_effect
                apy = max(0.1, apy)  # Minimum APY
                
                historical_data.append({
                    'date': current_date.isoformat(),
                    'apy': apy,
                    'tvl_usd': np.random.uniform(50000, 500000),  # Simulated TVL
                    'volume_usd': np.random.uniform(10000, 100000)
                })
                
                current_date += timedelta(days=1)
            
            return historical_data
            
        except Exception as e:
            print(f"❌ Error fetching historical data: {e}")
            return []
    
    def calculate_volatility(self, apy_series: List[float]) -> float:
        """Calculate APY volatility (standard deviation)"""
        if len(apy_series) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(apy_series)):
            daily_return = (apy_series[i] - apy_series[i-1]) / apy_series[i-1]
            returns.append(daily_return)
        
        return np.std(returns) * np.sqrt(365) if returns else 0.0  # Annualized
    
    def calculate_sharpe_ratio(self, apy_series: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio for risk-adjusted returns"""
        if len(apy_series) < 2:
            return 0.0
        
        avg_apy = np.mean(apy_series)
        volatility = self.calculate_volatility(apy_series)
        
        if volatility == 0:
            return 0.0
        
        return (avg_apy - risk_free_rate) / volatility
    
    def calculate_max_drawdown(self, apy_series: List[float]) -> float:
        """Calculate maximum drawdown from peak"""
        if len(apy_series) < 2:
            return 0.0
        
        peak = apy_series[0]
        max_drawdown = 0.0
        
        for apy in apy_series:
            if apy > peak:
                peak = apy
            
            drawdown = (peak - apy) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    async def backtest_pool_strategy(self, pool_data: Dict[str, Any], strategy: str = 'buy_and_hold') -> Dict[str, Any]:
        """Backtest a specific pool with a given strategy"""
        pool_address = pool_data.get('address', '')
        
        # Fetch historical data
        historical_data = await self.fetch_historical_apy_data(pool_address, days=90)
        
        if not historical_data:
            return {'success': False, 'error': 'No historical data available'}
        
        # Extract APY series
        apy_series = [day['apy'] for day in historical_data]
        tvl_series = [day['tvl_usd'] for day in historical_data]
        
        # Calculate performance metrics
        metrics = {
            'pool_address': pool_address,
            'strategy': strategy,
            'period_days': len(historical_data),
            'start_date': historical_data[0]['date'],
            'end_date': historical_data[-1]['date'],
            'avg_apy': np.mean(apy_series),
            'median_apy': np.median(apy_series),
            'min_apy': np.min(apy_series),
            'max_apy': np.max(apy_series),
            'volatility': self.calculate_volatility(apy_series),
            'sharpe_ratio': self.calculate_sharpe_ratio(apy_series),
            'max_drawdown': self.calculate_max_drawdown(apy_series),
            'avg_tvl': np.mean(tvl_series),
            'tvol_growth': (tvl_series[-1] - tvl_series[0]) / tvl_series[0] if tvl_series[0] > 0 else 0
        }
        
        # Strategy-specific calculations
        if strategy == 'buy_and_hold':
            # Simple buy and hold returns
            initial_investment = 1000
            final_value = initial_investment * (1 + metrics['avg_apy'] / 100)
            metrics.update({
                'initial_investment': initial_investment,
                'final_value': final_value,
                'total_return': (final_value - initial_investment) / initial_investment,
                'annualized_return': metrics['avg_apy']
            })
        
        elif strategy == 'rebalance_weekly':
            # Simulate weekly rebalancing
            weekly_returns = []
            for i in range(0, len(apy_series), 7):
                week_slice = apy_series[i:i+7]
                if week_slice:
                    weekly_returns.append(np.mean(week_slice))
            
            if weekly_returns:
                metrics.update({
                    'weekly_avg_apy': np.mean(weekly_returns),
                    'weekly_volatility': self.calculate_volatility(weekly_returns),
                    'rebalance_count': len(weekly_returns)
                })
        
        # Risk assessment
        risk_score = self._calculate_risk_score(metrics)
        metrics['risk_score'] = risk_score
        metrics['risk_category'] = self._get_risk_category(risk_score)
        
        return {
            'success': True,
            'metrics': metrics,
            'historical_data': historical_data[:10]  # Return sample of historical data
        }
    
    def _calculate_risk_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate risk score (0-100, higher = riskier)"""
        score = 0.0
        
        # Volatility risk
        volatility = metrics.get('volatility', 0)
        if volatility > 0.5:
            score += 40
        elif volatility > 0.3:
            score += 25
        elif volatility > 0.2:
            score += 15
        
        # Drawdown risk
        max_drawdown = metrics.get('max_drawdown', 0)
        if max_drawdown > 0.5:
            score += 30
        elif max_drawdown > 0.3:
            score += 20
        elif max_drawdown > 0.2:
            score += 10
        
        # Sharpe ratio risk (inverse)
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe < 0.5:
            score += 20
        elif sharpe < 1.0:
            score += 10
        
        # TVL stability
        tvol_growth = abs(metrics.get('tvol_growth', 0))
        if tvol_growth > 0.5:  # TVL changed by more than 50%
            score += 10
        
        return min(score, 100)
    
    def _get_risk_category(self, risk_score: float) -> str:
        """Get risk category based on score"""
        if risk_score >= 70:
            return "HIGH RISK"
        elif risk_score >= 40:
            return "MEDIUM RISK"
        else:
            return "LOW RISK"
    
    async def compare_strategies(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare different strategies for the same pool"""
        strategies = ['buy_and_hold', 'rebalance_weekly']
        results = {}
        
        for strategy in strategies:
            result = await self.backtest_pool_strategy(pool_data, strategy)
            if result.get('success'):
                results[strategy] = result['metrics']
        
        # Find best strategy
        best_strategy = None
        best_score = -1
        
        for strategy, metrics in results.items():
            # Score based on risk-adjusted returns
            sharpe = metrics.get('sharpe_ratio', 0)
            risk_score = metrics.get('risk_score', 100)
            
            # Higher Sharpe and lower risk is better
            strategy_score = sharpe * 100 - risk_score
            if strategy_score > best_score:
                best_score = strategy_score
                best_strategy = strategy
        
        return {
            'pool_address': pool_data.get('address', ''),
            'strategies': results,
            'best_strategy': best_strategy,
            'best_score': best_score,
            'comparison_date': datetime.now().isoformat()
        }
    
    def format_backtest_results(self, results: Dict[str, Any]) -> str:
        """Format backtest results for display"""
        if not results.get('success'):
            return f"❌ Backtest failed: {results.get('error', 'Unknown error')}"
        
        metrics = results['metrics']
        
        output = f"📊 **Backtest Results**\n"
        output += f"{'='*30}\n"
        output += f"📅 Period: {metrics['period_days']} days\n"
        output += f"📈 Strategy: {metrics['strategy']}\n"
        output += f"💰 Avg APY: {metrics['avg_apy']:.2f}%\n"
        output += f"📊 Volatility: {metrics['volatility']:.2f}\n"
        output += f"⚡ Sharpe Ratio: {metrics['sharpe_ratio']:.2f}\n"
        output += f"📉 Max Drawdown: {metrics['max_drawdown']:.2f}%\n"
        output += f"⚠️  Risk Score: {metrics['risk_score']}/100 ({metrics['risk_category']})\n"
        
        if 'total_return' in metrics:
            output += f"💵 Total Return: {metrics['total_return']:.2%}\n"
        
        return output


# Global backtester instance
backtester = YieldBacktester()
