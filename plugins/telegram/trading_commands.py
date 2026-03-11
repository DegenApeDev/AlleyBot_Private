"""
Trading Commands for Telegram
Provides trading-related commands and market analysis including autonomous trading
"""
from telegram import Update
from telegram.ext import ContextTypes

# Import security filter
try:
    from security_filter import security_filter
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    print("⚠️ Security filter not available in trading commands!")


class TradingCommands:
    """Trading command handlers for Telegram"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
    
    @property
    def core(self):
        """Access core from telegram plugin"""
        return self.telegram.core
    
    async def _verify_owner(self, update: Update) -> bool:
        """Verify user is the owner"""
        if not update.effective_user:
            return False
        return update.effective_user.id == self.telegram.owner_user_id
    
    async def swap_sol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Swap tokens on Solana using Jupiter"""
        if not await self._verify_owner(update):
            await update.message.reply_text("❌ Owner-only command")
            return
        
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "**Solana Token Swap**\n\n"
                "Usage: `/swap_sol <from_token> <to_token> <amount> [slippage_bps]`\n\n"
                "Examples:\n"
                "• `/swap_sol SOL USDC 1.0` - Swap 1 SOL for USDC (0.5% slippage)\n"
                "• `/swap_sol USDC SOL 100 100` - Swap 100 USDC for SOL (1% slippage)\n"
                "• `/swap_sol BONK USDC 1000000` - Swap 1M BONK for USDC\n\n"
                "Supported tokens: SOL, USDC, USDT, RAY, BONK, WIF\n"
                "Slippage in basis points (50 = 0.5%, 100 = 1%)",
                parse_mode='Markdown'
            )
            return
        
        from_token = context.args[0].upper()
        to_token = context.args[1].upper()
        
        try:
            amount = float(context.args[2])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount")
            return
        
        slippage_bps = 50  # Default 0.5%
        if len(context.args) >= 4:
            try:
                slippage_bps = int(context.args[3])
            except ValueError:
                await update.message.reply_text("❌ Invalid slippage (must be integer)")
                return
        
        # Get Solana trading plugin
        solana_trading = self.core.plugin_manager.plugins.get('solana_trading')
        if not solana_trading:
            await update.message.reply_text("❌ Solana trading plugin not loaded")
            return
        
        await update.message.reply_text(f"🔄 Swapping {amount} {from_token} → {to_token}...")
        
        # Execute swap
        result = solana_trading.execute_swap(from_token, to_token, amount, slippage_bps)
        
        if result.get('success'):
            # Build success message with profit analysis
            msg = f"""✅ **Swap Successful!**

📥 Input: {result['input_amount']} {result['input_token']}
📤 Output: {result['output_amount']:.6f} {result['output_token']}
📊 Price Impact: {result['price_impact']:.4f}%"""
            
            # Add profit analysis if available
            if 'profit_analysis' in result and result['profit_analysis'].get('success'):
                pa = result['profit_analysis']
                msg += f"\n\n� **Cost Breakdown:**"
                msg += f"\n• Jupiter Fee: {pa['breakdown']['jupiter_fee']}%"
                msg += f"\n• Price Impact: {pa['breakdown']['price_impact']:.2f}%"
                msg += f"\n• Gas: ${pa['breakdown']['gas']:.3f}"
                msg += f"\n• Total Cost: {pa['total_cost_percent']:.2f}%"
                
                # Add warnings if any
                if pa.get('warnings'):
                    msg += f"\n\n⚠️ **Warnings:**"
                    for warning in pa['warnings']:
                        msg += f"\n{warning}"
            
            msg += f"\n\n🔗 [View on Solscan]({result['explorer_url']})"
            msg += f"\n\nSignature: `{result['signature'][:16]}...`"
            
            # Security: Filter message before sending
            if SECURITY_AVAILABLE:
                msg, was_filtered = security_filter.filter_message(msg)
                if was_filtered:
                    msg = "✅ Swap successful but response contained sensitive data. Check explorer link for details."
            
            await update.message.reply_text(msg, parse_mode='Markdown', disable_web_page_preview=True)
            
            # Record trade in analytics
            analytics = self.core.plugin_manager.plugins.get('trading_analytics')
            if analytics:
                analytics.record_trade({
                    'chain': 'solana',
                    'dex': 'jupiter',
                    'token_in': result['input_token'],
                    'token_out': result['output_token'],
                    'amount_in': result['input_amount'],
                    'amount_out': result['output_amount'],
                    'price_impact': result['price_impact'],
                    'slippage_bps': slippage_bps,
                    'fees_usd': result.get('profit_analysis', {}).get('breakdown', {}).get('jupiter_fee', 0),
                    'gas_cost_usd': result.get('profit_analysis', {}).get('breakdown', {}).get('gas', 0.001),
                    'tx_hash': result['signature'],
                    'mev_protected': result.get('mev_protected', False),
                    'strategy': 'manual'
                })
        else:
            error_msg = f"❌ Swap failed: {result.get('error', 'Unknown error')}"
            
            # Add profit analysis if trade was rejected for profitability
            if 'profit_analysis' in result:
                pa = result['profit_analysis']
                error_msg += f"\n\n📊 **Analysis:**"
                error_msg += f"\nPrice Impact: {pa.get('price_impact_percent', 0):.2f}%"
                error_msg += f"\nTotal Cost: {pa.get('total_cost_percent', 0):.2f}%"
            
            if 'suggestion' in result:
                error_msg += f"\n\n💡 {result['suggestion']}"
            
            # Security: Filter error message
            if SECURITY_AVAILABLE:
                error_msg = security_filter.sanitize_error_message(error_msg)
            
            await update.message.reply_text(error_msg)
    
    async def swap_base(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Swap tokens on Base using Uniswap V3"""
        if not await self._verify_owner(update):
            await update.message.reply_text("❌ Owner-only command")
            return
        
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "**Base Token Swap**\n\n"
                "Usage: `/swap_base <from_token> <to_token> <amount> [slippage_%]`\n\n"
                "Examples:\n"
                "• `/swap_base ETH USDC 0.1` - Swap 0.1 ETH for USDC (0.5% slippage)\n"
                "• `/swap_base USDC ETH 100 1.0` - Swap 100 USDC for ETH (1% slippage)\n\n"
                "Supported tokens: ETH, WETH, USDC, USDbC, DAI\n"
                "Slippage in percent (0.5 = 0.5%, 1.0 = 1%)",
                parse_mode='Markdown'
            )
            return
        
        from_token = context.args[0].upper()
        to_token = context.args[1].upper()
        
        try:
            amount = float(context.args[2])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount")
            return
        
        slippage = 0.5  # Default 0.5%
        if len(context.args) >= 4:
            try:
                slippage = float(context.args[3])
            except ValueError:
                await update.message.reply_text("❌ Invalid slippage (must be number)")
                return
        
        # Get Base trading plugin
        base_trading = self.core.plugin_manager.plugins.get('base_trading')
        if not base_trading:
            await update.message.reply_text("❌ Base trading plugin not loaded")
            return
        
        await update.message.reply_text(f"🔄 Swapping {amount} {from_token} → {to_token}...")
        
        # Execute swap
        result = base_trading.execute_swap(from_token, to_token, amount, slippage)
        
        if result.get('success'):
            msg = f"""✅ **Swap Successful!**

📥 Input: {result['input_amount']} {result['input_token']}
📤 Output: {result['output_token']}
🔗 [View on BaseScan]({result['explorer_url']})

TX: `{result['tx_hash'][:16]}...`"""
            await update.message.reply_text(msg, parse_mode='Markdown', disable_web_page_preview=True)
        else:
            await update.message.reply_text(f"❌ Swap failed: {result.get('error', 'Unknown error')}")
    
    async def sol_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get token price on Solana"""
        if not await self._verify_owner(update):
            await update.message.reply_text("❌ Owner-only command")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "**Solana Token Price**\n\n"
                "Usage: `/sol_price <from_token> <to_token> [amount]`\n\n"
                "Examples:\n"
                "• `/sol_price SOL USDC` - Price of 1 SOL in USDC\n"
                "• `/sol_price BONK USDC 1000000` - Price of 1M BONK in USDC",
                parse_mode='Markdown'
            )
            return
        
        from_token = context.args[0].upper()
        to_token = context.args[1].upper()
        amount = 1.0
        
        if len(context.args) >= 3:
            try:
                amount = float(context.args[2])
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        # Get Solana trading plugin
        solana_trading = self.core.plugin_manager.plugins.get('solana_trading')
        if not solana_trading:
            await update.message.reply_text("❌ Solana trading plugin not loaded")
            return
        
        result = solana_trading.get_price(from_token, to_token, amount)
        
        if result.get('success'):
            msg = f"""💱 **Solana Price Quote**

{amount} {result['from_token']} = {result['output']:.6f} {result['to_token']}

📊 Price: {result['formatted']}
📉 Price Impact: {result['price_impact']:.4f}%"""
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Price check failed: {result.get('error', 'Unknown error')}")
    
    async def trading_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View trading performance statistics"""
        if not await self._verify_owner(update):
            await update.message.reply_text("❌ Owner-only command")
            return
        
        # Get analytics plugin
        analytics = self.core.plugin_manager.plugins.get('trading_analytics')
        if not analytics:
            await update.message.reply_text("❌ Trading analytics plugin not loaded")
            return
        
        # Get days parameter
        days = 30
        if context.args and len(context.args) > 0:
            try:
                days = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Invalid days parameter")
                return
        
        await update.message.reply_text(f"📊 Fetching {days}-day trading stats...")
        
        stats = analytics.get_performance_stats(days)
        
        if not stats.get('success'):
            await update.message.reply_text(f"❌ Failed to get stats: {stats.get('error', 'Unknown error')}")
            return
        
        if stats.get('total_trades', 0) == 0:
            await update.message.reply_text(f"📊 No trades in the last {days} days")
            return
        
        # Build stats message
        msg = f"""📊 **Trading Performance ({days} days)**

📈 **Overview:**
• Total Trades: {stats['total_trades']}
• Profitable: {stats['profitable_trades']} ({stats['win_rate']}%)
• Win Rate: {stats['win_rate']}%

💰 **Profit & Loss:**
• Gross Profit: ${stats['total_profit_usd']:.2f}
• Total Fees: ${stats['total_fees_usd']:.2f}
• Total Gas: ${stats['total_gas_usd']:.2f}
• **Net Profit: ${stats['net_profit_usd']:.2f}**

📊 **Performance:**
• Avg Profit: {stats['avg_profit_percent']:.2f}%
• Best Trade: ${stats['best_trade_usd']:.2f}
• Worst Trade: ${stats['worst_trade_usd']:.2f}"""
        
        # Add chain breakdown
        if stats.get('chains'):
            msg += f"\n\n⛓️ **By Chain:**"
            for chain, data in stats['chains'].items():
                msg += f"\n• {chain.title()}: {data['trades']} trades, ${data['profit']:.2f}"
        
        # Add strategy breakdown
        if stats.get('strategies'):
            msg += f"\n\n🎯 **By Strategy:**"
            for strategy in stats['strategies'][:3]:  # Top 3
                msg += f"\n• {strategy['strategy']}: {strategy['trades']} trades, ${strategy['profit']:.2f}"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def recent_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View recent trades"""
        if not await self._verify_owner(update):
            await update.message.reply_text("❌ Owner-only command")
            return
        
        # Get analytics plugin
        analytics = self.core.plugin_manager.plugins.get('trading_analytics')
        if not analytics:
            await update.message.reply_text("❌ Trading analytics plugin not loaded")
            return
        
        # Get limit parameter
        limit = 10
        if context.args and len(context.args) > 0:
            try:
                limit = int(context.args[0])
                limit = min(limit, 20)  # Max 20
            except ValueError:
                await update.message.reply_text("❌ Invalid limit parameter")
                return
        
        result = analytics.get_recent_trades(limit)
        
        if not result.get('success'):
            await update.message.reply_text(f"❌ Failed to get trades: {result.get('error', 'Unknown error')}")
            return
        
        trades = result.get('trades', [])
        if not trades:
            await update.message.reply_text("📊 No recent trades")
            return
        
        msg = f"📜 **Recent Trades ({len(trades)}):**\n\n"
        
        for i, trade in enumerate(trades, 1):
            profit_emoji = "✅" if trade['profit_usd'] > 0 else "❌"
            msg += f"{i}. {profit_emoji} {trade['pair']} on {trade['chain'].title()}\n"
            msg += f"   • Amount: {trade['amount_in']:.4f} → {trade['amount_out']:.4f}\n"
            msg += f"   • Profit: ${trade['profit_usd']:.2f} ({trade['profit_pct']:.2f}%)\n"
            msg += f"   • TX: `{trade['tx_hash']}`\n\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def base_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get token price on Base"""
        if not await self._verify_owner(update):
            await update.message.reply_text("❌ Owner-only command")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "**Base Token Price**\n\n"
                "Usage: `/base_price <from_token> <to_token>`\n\n"
                "Examples:\n"
                "• `/base_price ETH USDC` - Price of ETH in USDC\n"
                "• `/base_price USDC ETH` - Price of USDC in ETH",
                parse_mode='Markdown'
            )
            return
        
        from_token = context.args[0].upper()
        to_token = context.args[1].upper()
        
        # Get Base trading plugin
        base_trading = self.core.plugin_manager.plugins.get('base_trading')
        if not base_trading:
            await update.message.reply_text("❌ Base trading plugin not loaded")
            return
        
        result = base_trading.get_price(from_token, to_token)
        
        if result.get('success'):
            msg = f"""💱 **Base Price Quote**

{result['from_token']} → {result['to_token']}

⚠️ {result['note']}

💡 {result['recommendation']}"""
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Price check failed: {result.get('error', 'Unknown error')}")
    
    async def trading_enable(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enable autonomous trading with SyMod validation"""
        if not await self._verify_owner(update):
            await update.message.reply_text("❌ Owner-only command")
            return
        
        from src.agentic.autonomous_trading import get_autonomous_trading
        trading = get_autonomous_trading()
        
        if not trading:
            await update.message.reply_text("❌ Autonomous trading system not available")
            return
        
        trading.enable_trading(True)
        
        status = trading.get_trading_status()
        
        msg = f"""✅ **Autonomous Trading ENABLED**

💰 **Configuration:**
• Capital: ${status['capital']:.2f}
• Max Position: {status['config']['max_position_size_pct']}% (${status['capital'] * status['config']['max_position_size_pct'] / 100:.2f})
• Min Confidence: {status['config']['min_confidence']}
• Min Risk/Reward: {status['config']['min_risk_reward']}:1
• Daily Loss Limit: {status['config']['daily_loss_limit_pct']}%
• Max Open Positions: {status['config']['max_open_positions']}

🔢 **SyMod Validation:**
• Require Stable Field: {'✅' if status['config']['require_stable_field'] else '❌'}
• Require Golden Window: {'✅' if status['config']['require_golden_window'] else '❌'}
• Max Impedance: {status['config']['max_impedance']}

⚠️ **CONSERVATIVE MODE**
Only SyMod-validated trades with 0.8+ confidence will execute.
AlleyBot will analyze markets every 30 minutes."""
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def trading_disable(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Disable autonomous trading"""
        if not await self._verify_owner(update):
            await update.message.reply_text("❌ Owner-only command")
            return
        
        from src.agentic.autonomous_trading import get_autonomous_trading
        trading = get_autonomous_trading()
        
        if not trading:
            await update.message.reply_text("❌ Autonomous trading system not available")
            return
        
        trading.enable_trading(False)
        await update.message.reply_text("⛔ **Autonomous Trading DISABLED**")
    
    async def trading_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check autonomous trading status"""
        if not await self._verify_owner(update):
            await update.message.reply_text("❌ Owner-only command")
            return
        
        from src.agentic.autonomous_trading import get_autonomous_trading
        trading = get_autonomous_trading()
        
        if not trading:
            await update.message.reply_text("❌ Autonomous trading system not available")
            return
        
        status = trading.get_trading_status()
        
        enabled_emoji = "✅" if status['enabled'] else "⛔"
        
        msg = f"""{enabled_emoji} **Autonomous Trading Status**

💰 **Capital:** ${status['capital']:.2f}
📊 **Performance:**
• Total Trades: {status['total_trades']}
• Winning Trades: {status['winning_trades']}
• Win Rate: {status['win_rate']:.1f}%
• Total Profit: ${status['total_profit']:.2f}
• Daily P&L: ${status['daily_pnl']:.2f}

📈 **Current:**
• Open Positions: {status['open_positions']}/{status['config']['max_open_positions']}
• Status: {'ACTIVE' if status['enabled'] else 'DISABLED'}

Use /trading_enable to start autonomous trading."""
        
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def best_swap_quote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get best swap quote from multiple aggregators"""
        if not await self._verify_owner(update):
            await update.message.reply_text("❌ Owner-only command")
            return
        
        if not context.args or len(context.args) < 4:
            await update.message.reply_text(
                "**Best Swap Quote**\n\n"
                "Get the best price from multiple DEX aggregators (1inch, Paraswap, 0x, Kyber, Odos, OKX)\n\n"
                "Usage: `/best_swap_quote <network> <from_token> <to_token> <amount>`\n\n"
                "Examples:\n"
                "• `/best_swap_quote ethereum USDC WETH 1000`\n"
                "• `/best_swap_quote base USDC ETH 500`\n"
                "• `/best_swap_quote arbitrum WETH USDC 0.5`\n\n"
                "Networks: ethereum, base, arbitrum, polygon, plasma\n"
                "Tokens: Use symbols like USDC, WETH, ETH, USDT, DAI",
                parse_mode='Markdown'
            )
            return
        
        network = context.args[0].lower()
        from_token = context.args[1].upper()
        to_token = context.args[2].upper()
        
        try:
            amount = float(context.args[3])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount")
            return
        
        await update.message.reply_text(f"🔍 Finding best price for {amount} {from_token} → {to_token} on {network}...")
        
        try:
            # Import and use the skill
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from skills.best_crypto_swap_price.best_crypto_swap_skill import BestCryptoSwapSkill
            
            skill = BestCryptoSwapSkill()
            
            # Get wallet address
            user_address = os.getenv(f'{network.upper()}_WALLET_PUBLIC_ADDRESS') or os.getenv('BASE_WALLET_PUBLIC_ADDRESS', '0x0000000000000000000000000000000000000000')
            
            # Get token addresses
            sell_token = skill.get_token_address(network, from_token)
            buy_token = skill.get_token_address(network, to_token)
            
            if not sell_token:
                await update.message.reply_text(f"❌ Unknown token: {from_token} on {network}")
                return
            if not buy_token:
                await update.message.reply_text(f"❌ Unknown token: {to_token} on {network}")
                return
            
            # Calculate decimals
            decimals = 6 if from_token in ['USDC', 'USDT'] else 18
            amount_raw = int(amount * (10 ** decimals))
            
            # Get quote
            result = skill.get_best_quote(
                network=network,
                sell_token=sell_token,
                buy_token=buy_token,
                sell_amount=str(amount_raw),
                user_address=user_address,
                slippage=1.0
            )
            
            if not result.get('success'):
                await update.message.reply_text(f"❌ Failed to get quote: {result.get('error', 'Unknown error')}")
                return
            
            best = result['best_route']
            summary = result['summary']
            
            msg = f"📊 **Best Swap Quote on {network.upper()}**\n\n"
            msg += f"🔄 **{from_token} → {to_token}**\n"
            msg += f"💰 Sell: {amount} {from_token}\n"
            msg += f"🏆 **Best Route: {best.display_name}**\n"
            msg += f"📈 Buy Amount: {best.buy_amount[:30]}... (raw units)\n"
            msg += f"⚡ Price Impact: {best.price_impact}%\n"
            msg += f"⛽ Gas Price: {best.gas_price}\n\n"
            
            # Show all routes
            if len(result['all_routes']) > 1:
                msg += "🏆 **All Aggregators:**\n"
                for i, route in enumerate(result['all_routes'][:5], 1):
                    impact = f" ({route.price_impact}% impact)" if route.price_impact else ""
                    msg += f"  {i}. {route.display_name}: {route.buy_amount[:20]}...{impact}\n"
            
            msg += f"\n💡 To execute: `/best_swap_execute {network} {from_token} {to_token} {amount}`"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting quote: {str(e)[:200]}")

    async def best_swap_execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute swap using best price"""
        if not await self._verify_owner(update):
            await update.message.reply_text("❌ Owner-only command")
            return
        
        if not context.args or len(context.args) < 4:
            await update.message.reply_text(
                "**Execute Best Swap**\n\n"
                "Execute a swap using the best aggregator price.\n\n"
                "Usage: `/best_swap_execute <network> <from_token> <to_token> <amount>`\n\n"
                "Example: `/best_swap_execute base USDC ETH 100`",
                parse_mode='Markdown'
            )
            return
        
        network = context.args[0].lower()
        from_token = context.args[1].upper()
        to_token = context.args[2].upper()
        
        try:
            amount = float(context.args[3])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount")
            return
        
        # Get private key
        import os
        private_key = os.getenv(f'{network.upper()}_PRIVATE_KEY') or os.getenv('BASE_WALLET_PRIVATE_KEY')
        user_address = os.getenv(f'{network.upper()}_WALLET_PUBLIC_ADDRESS') or os.getenv('BASE_WALLET_PUBLIC_ADDRESS')
        
        if not private_key or not user_address:
            await update.message.reply_text(f"❌ Wallet not configured for {network}. Check your .env file.")
            return
        
        await update.message.reply_text(f"🚀 Executing swap: {amount} {from_token} → {to_token} on {network}...")
        
        try:
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from skills.best_crypto_swap_price.best_crypto_swap_skill import quick_swap
            
            decimals = 6 if from_token in ['USDC', 'USDT'] else 18
            
            result = quick_swap(
                network=network,
                from_token_symbol=from_token,
                to_token_symbol=to_token,
                amount=amount,
                user_address=user_address,
                private_key=private_key,
                from_decimals=decimals,
                slippage=1.0
            )
            
            if result.get('success'):
                msg = f"""✅ **Swap Executed Successfully!**

🏆 Aggregator: {result.get('aggregator')}
🔗 Tx Hash: `{result.get('tx_hash', 'N/A')[:30]}...`
📦 Buy Amount: {result.get('buy_amount', 'N/A')[:30]}...
⚡ Price Impact: {result.get('price_impact', 'N/A')}%
⛽ Gas Used: {result.get('gas_used', 'N/A')}"""
                
                if result.get('explorer_url'):
                    msg += f"\n\n📄 [View on Explorer]({result['explorer_url']})"
                
                await update.message.reply_text(msg, parse_mode='Markdown', disable_web_page_preview=True)
            else:
                await update.message.reply_text(f"❌ Swap failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Execution error: {str(e)[:200]}")

    async def best_swap_compare(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Compare all aggregator prices"""
        if not await self._verify_owner(update):
            await update.message.reply_text("❌ Owner-only command")
            return
        
        if not context.args or len(context.args) < 4:
            await update.message.reply_text(
                "**Compare Aggregators**\n\n"
                "Compare prices across all DEX aggregators.\n\n"
                "Usage: `/best_swap_compare <network> <from_token> <to_token> <amount>`",
                parse_mode='Markdown'
            )
            return
        
        network = context.args[0].lower()
        from_token = context.args[1].upper()
        to_token = context.args[2].upper()
        
        try:
            amount = float(context.args[3])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount")
            return
        
        await update.message.reply_text(f"📊 Comparing all aggregators for {amount} {from_token} → {to_token}...")
        
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from skills.best_crypto_swap_price.best_crypto_swap_skill import BestCryptoSwapSkill
            
            skill = BestCryptoSwapSkill()
            
            user_address = os.getenv(f'{network.upper()}_WALLET_PUBLIC_ADDRESS') or os.getenv('BASE_WALLET_PUBLIC_ADDRESS', '0x0000000000000000000000000000000000000000')
            
            sell_token = skill.get_token_address(network, from_token)
            buy_token = skill.get_token_address(network, to_token)
            
            if not sell_token or not buy_token:
                await update.message.reply_text("❌ Unknown token(s)")
                return
            
            decimals = 6 if from_token in ['USDC', 'USDT'] else 18
            amount_raw = int(amount * (10 ** decimals))
            
            comparison = skill.compare_aggregators(
                network=network,
                sell_token=sell_token,
                buy_token=buy_token,
                sell_amount=str(amount_raw),
                user_address=user_address,
                slippage=1.0
            )
            
            await update.message.reply_text(comparison, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:200]}")
