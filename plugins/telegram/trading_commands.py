"""
Trading Commands for Telegram Bot
Handles Solana and Base token trading commands
"""
from telegram import Update
from telegram.ext import ContextTypes


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
            msg = f"""✅ **Swap Successful!**

📥 Input: {result['input_amount']} {result['input_token']}
📤 Output: {result['output_amount']:.6f} {result['output_token']}
📊 Price Impact: {result['price_impact']:.4f}%
🔗 [View on Solscan]({result['explorer_url']})

Signature: `{result['signature'][:16]}...`"""
            await update.message.reply_text(msg, parse_mode='Markdown', disable_web_page_preview=True)
        else:
            await update.message.reply_text(f"❌ Swap failed: {result.get('error', 'Unknown error')}")
    
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
