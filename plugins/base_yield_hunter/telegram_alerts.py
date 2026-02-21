"""
Telegram alerts module for Base Yield Hunter
Formatted notifications for yield opportunities and alerts
"""
import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup


class YieldAlerts:
    """Telegram alert system for yield opportunities"""
    
    def __init__(self, telegram_bot_token: str = None, admin_chat_id: str = None):
        self.bot_token = telegram_bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_chat_id = admin_chat_id or os.getenv('TELEGRAM_ADMIN_CHAT_ID')
        self.bot = None
        
        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
    
    async def send_yield_opportunity_alert(self, pool_data: Dict[str, Any], rank: int = 1) -> bool:
        """Send formatted yield opportunity alert to Telegram"""
        if not self.bot or not self.admin_chat_id:
            return False
        
        try:
            # Format the alert message
            message = self._format_yield_alert(pool_data, rank)
            
            # Create inline keyboard for quick actions
            keyboard = self._create_yield_keyboard(pool_data)
            
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending yield alert: {e}")
            return False
    
    def _format_yield_alert(self, pool_data: Dict[str, Any], rank: int) -> str:
        """Format yield opportunity alert message"""
        symbol = pool_data.get('symbol', 'UNKNOWN')
        project = pool_data.get('project', 'Unknown')
        apy = pool_data.get('apy', 0)
        tvl_usd = pool_data.get('tvlUsd', 0)
        contract_address = pool_data.get('address', '')
        
        # Rank emoji
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        rank_emoji = rank_emojis.get(rank, "🏅")
        
        # Risk assessment
        risk_score = pool_data.get('risk_score', 0)
        if risk_score < 20:
            risk_emoji = "🟢"
            risk_text = "Low Risk"
        elif risk_score < 40:
            risk_emoji = "🟡"
            risk_text = "Medium Risk"
        elif risk_score < 60:
            risk_emoji = "🟠"
            risk_text = "High Risk"
        else:
            risk_emoji = "🔴"
            risk_text = "Very High Risk"
        
        message = f"{rank_emoji} **Yield Opportunity Alert!**\n\n"
        message += f"🏊 **Pool:** {symbol} - {project}\n"
        message += f"💰 **APY:** {apy:.2f}%\n"
        message += f"💎 **TVL:** ${tvl_usd:,.0f}\n"
        message += f"{risk_emoji} **Risk:** {risk_text} ({risk_score}/100)\n\n"
        
        # Security info
        security = pool_data.get('security', {})
        if security.get('verified'):
            message += f"✅ Contract Verified\n"
        else:
            message += f"❌ Contract Not Verified\n"
        
        # Add Etherscan link
        if contract_address:
            message += f"\n🔗 [View on BaseScan](https://basescan.org/address/{contract_address})"
        
        message += f"\n\n⏰ *{datetime.now().strftime('%H:%M:%S')}*"
        
        return message
    
    def _create_yield_keyboard(self, pool_data: Dict[str, Any]) -> InlineKeyboardMarkup:
        """Create inline keyboard for yield opportunity actions"""
        contract_address = pool_data.get('address', '')
        symbol = pool_data.get('symbol', 'UNKNOWN')
        
        keyboard = []
        
        # First row - Main actions
        row1 = []
        if contract_address:
            row1.append(InlineKeyboardButton("🔍 BaseScan", url=f"https://basescan.org/address/{contract_address}"))
        
        # Add DefiLlama link if available
        pool_id = pool_data.get('pool')
        if pool_id:
            row1.append(InlineKeyboardButton("📊 DeFiLlama", url=f"https://defillama.com/yields/pool/{pool_id}"))
        
        if row1:
            keyboard.append(row1)
        
        # Second row - Analysis actions
        row2 = []
        row2.append(InlineKeyboardButton("📈 Backtest", callback_data=f"backtest_{contract_address[:8]}"))
        row2.append(InlineKeyboardButton("🔍 Security", callback_data=f"security_{contract_address[:8]}"))
        
        keyboard.append(row2)
        
        # Third row - Alert preferences
        row3 = []
        row3.append(InlineKeyboardButton("🔔 Set Alert", callback_data=f"alert_{contract_address[:8]}"))
        row3.append(InlineKeyboardButton("🚫 Mute", callback_data=f"mute_{contract_address[:8]}"))
        
        keyboard.append(row3)
        
        return InlineKeyboardMarkup(keyboard)
    
    async def send_scan_summary(self, scan_results: Dict[str, Any]) -> bool:
        """Send scan summary with top opportunities"""
        if not self.bot or not self.admin_chat_id:
            return False
        
        try:
            pools = scan_results.get('pools', [])
            if not pools:
                message = "📭 *Yield Scan Complete*\n\nNo high-quality opportunities found."
                await self.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                return True
            
            message = f"🏹 **Base Yield Scan Complete**\n\n"
            message += f"🔍 Found {len(pools)} opportunities\n"
            message += f"⛽ Gas: {scan_results.get('gas_price', 0):.1f} gwei\n\n"
            
            # Show top 3 pools
            for i, pool in enumerate(pools[:3], 1):
                symbol = pool.get('symbol', 'UNKNOWN')
                project = pool.get('project', 'Unknown')
                apy = pool.get('apy', 0)
                risk_score = pool.get('risk_score', 0)
                
                # Risk emoji
                if risk_score < 20:
                    risk_emoji = "🟢"
                elif risk_score < 40:
                    risk_emoji = "🟡"
                elif risk_score < 60:
                    risk_emoji = "🟠"
                else:
                    risk_emoji = "🔴"
                
                message += f"{i}. **{symbol}** - {project}\n"
                message += f"   💰 {apy:.2f}% APY {risk_emoji} {risk_score}/100\n\n"
            
            # Add quick action buttons
            keyboard = []
            row1 = []
            row1.append(InlineKeyboardButton("📊 Full Report", callback_data="yield_full_report"))
            row1.append(InlineKeyboardButton("🔄 Scan Again", callback_data="yield_rescan"))
            keyboard.append(row1)
            
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending scan summary: {e}")
            return False
    
    async def send_security_alert(self, pool_data: Dict[str, Any], security_issues: List[str]) -> bool:
        """Send security alert for suspicious pool"""
        if not self.bot or not self.admin_chat_id:
            return False
        
        try:
            symbol = pool_data.get('symbol', 'UNKNOWN')
            project = pool_data.get('project', 'Unknown')
            contract_address = pool_data.get('address', '')
            
            message = f"⚠️ **Security Alert**\n\n"
            message += f"🏊 **Pool:** {symbol} - {project}\n"
            message += f"🚨 **Issues Detected:**\n"
            
            for issue in security_issues:
                message += f"• {issue}\n"
            
            if contract_address:
                message += f"\n🔗 [View on BaseScan](https://basescan.org/address/{contract_address})"
            
            message += f"\n\n⏰ *{datetime.now().strftime('%H:%M:%S')}*"
            
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending security alert: {e}")
            return False
    
    async def send_backtest_results(self, pool_data: Dict[str, Any], backtest_results: Dict[str, Any]) -> bool:
        """Send backtest analysis results"""
        if not self.bot or not self.admin_chat_id:
            return False
        
        try:
            if not backtest_results.get('success'):
                message = f"❌ Backtest failed: {backtest_results.get('error', 'Unknown error')}"
                await self.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                return True
            
            metrics = backtest_results['metrics']
            symbol = pool_data.get('symbol', 'UNKNOWN')
            
            message = f"📊 **Backtest Results**\n\n"
            message += f"🏊 **Pool:** {symbol}\n"
            message += f"📈 **Strategy:** {metrics['strategy']}\n"
            message += f"💰 **Avg APY:** {metrics['avg_apy']:.2f}%\n"
            message += f"📊 **Volatility:** {metrics['volatility']:.2f}\n"
            message += f"⚡ **Sharpe Ratio:** {metrics['sharpe_ratio']:.2f}\n"
            message += f"📉 **Max Drawdown:** {metrics['max_drawdown']:.2f}%\n"
            message += f"⚠️ **Risk Score:** {metrics['risk_score']}/100 ({metrics['risk_category']})\n"
            
            if 'total_return' in metrics:
                message += f"💵 **Total Return:** {metrics['total_return']:.2%}\n"
            
            message += f"\n⏰ *{datetime.now().strftime('%H:%M:%S')}*"
            
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending backtest results: {e}")
            return False
    
    async def handle_callback_query(self, callback_query) -> Optional[str]:
        """Handle callback queries from inline keyboards"""
        callback_data = callback_query.data
        
        if callback_data == "yield_full_report":
            return "📊 Full yield report feature coming soon!"
        
        elif callback_data == "yield_rescan":
            return "🔄 Initiating new yield scan..."
        
        elif callback_data.startswith("backtest_"):
            pool_address = callback_data.split("_")[1]
            return f"📈 Running backtest for pool {pool_address}..."
        
        elif callback_data.startswith("security_"):
            pool_address = callback_data.split("_")[1]
            return f"🔍 Running security analysis for pool {pool_address}..."
        
        elif callback_data.startswith("alert_"):
            pool_address = callback_data.split("_")[1]
            return f"🔔 Setting up alerts for pool {pool_address}..."
        
        elif callback_data.startswith("mute_"):
            pool_address = callback_data.split("_")[1]
            return f"🔕 Muting alerts for pool {pool_address}..."
        
        return None


# Global alerts instance
alerts = YieldAlerts()
