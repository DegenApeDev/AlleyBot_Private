"""
Polymarket Telegram Commands
Prediction market trading commands for Telegram bot
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class PolymarketCommands:
    """Polymarket command handlers for Telegram"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
    
    @property
    def core(self):
        """Dynamically access core from telegram plugin"""
        return self.telegram.core
    
    async def polymarket_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get Polymarket plugin status"""
        try:
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                await update.message.reply_text("❌ Core not available")
                return
            
            polymarket = self.core.plugin_manager.get_plugin('polymarket')
            
            if not polymarket:
                await update.message.reply_text("❌ Polymarket plugin not loaded")
                return
            
            status = polymarket.status_command()
            await update.message.reply_text(status)
            
        except Exception as e:
            logger.error(f"Error in polymarket_status: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def polymarket_markets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List active prediction markets"""
        try:
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                await update.message.reply_text("❌ Core not available")
                return
            
            polymarket = self.core.plugin_manager.get_plugin('polymarket')
            
            if not polymarket:
                await update.message.reply_text("❌ Polymarket plugin not loaded")
                return
            
            # Get limit from args or default to 10
            limit = 10
            if context.args and len(context.args) > 0:
                try:
                    limit = int(context.args[0])
                    limit = min(limit, 50)  # Cap at 50
                except ValueError:
                    await update.message.reply_text("❌ Invalid limit. Usage: /polymarket_markets [limit]")
                    return
            
            result = polymarket.markets_command(limit=limit)
            await update.message.reply_text(result)
            
        except Exception as e:
            logger.error(f"Error in polymarket_markets: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def polymarket_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyze a specific market"""
        try:
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                await update.message.reply_text("❌ Core not available")
                return
            
            polymarket = self.core.plugin_manager.get_plugin('polymarket')
            
            if not polymarket:
                await update.message.reply_text("❌ Polymarket plugin not loaded")
                return
            
            # Get market ID from args
            if not context.args or len(context.args) == 0:
                await update.message.reply_text("❌ Usage: /polymarket_analyze <market_id>")
                return
            
            market_id = context.args[0]
            result = polymarket.analyze_command(market_id)
            await update.message.reply_text(result)
            
        except Exception as e:
            logger.error(f"Error in polymarket_analyze: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def polymarket_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View active positions"""
        try:
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                await update.message.reply_text("❌ Core not available")
                return
            
            polymarket = self.core.plugin_manager.get_plugin('polymarket')
            
            if not polymarket:
                await update.message.reply_text("❌ Polymarket plugin not loaded")
                return
            
            result = polymarket.positions_command()
            await update.message.reply_text(result)
            
        except Exception as e:
            logger.error(f"Error in polymarket_positions: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def polymarket_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get trading statistics"""
        try:
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                await update.message.reply_text("❌ Core not available")
                return
            
            polymarket = self.core.plugin_manager.get_plugin('polymarket')
            
            if not polymarket:
                await update.message.reply_text("❌ Polymarket plugin not loaded")
                return
            
            result = polymarket.stats_command()
            await update.message.reply_text(result)
            
        except Exception as e:
            logger.error(f"Error in polymarket_stats: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    def get_handlers(self):
        """Return command handlers for registration"""
        from telegram.ext import CommandHandler
        
        return [
            CommandHandler('polymarket_status', self.polymarket_status),
            CommandHandler('polymarket_markets', self.polymarket_markets),
            CommandHandler('polymarket_analyze', self.polymarket_analyze),
            CommandHandler('polymarket_positions', self.polymarket_positions),
            CommandHandler('polymarket_stats', self.polymarket_stats),
        ]


def register_polymarket_commands(telegram_plugin, dispatcher):
    """Register Polymarket commands with Telegram dispatcher"""
    commands = PolymarketCommands(telegram_plugin)
    for handler in commands.get_handlers():
        dispatcher.add_handler(handler)
    logger.info("🎲 Polymarket commands registered")
