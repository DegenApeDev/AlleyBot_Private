"""
Telegram Commands for Autonomous Brain Control

Provides /brain_start, /brain_stop, /brain_status commands
for owner to control Alley's autonomous mode.

Part of AGI Core - Phase 1
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

from src.agentic.autonomous_brain import get_autonomous_brain

logger = logging.getLogger(__name__)


class BrainCommands:
    """Telegram commands for controlling the autonomous brain"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
        self._brain = None
        self._core = None
    
    def _get_core(self):
        """Lazy-get core from telegram plugin"""
        if self._core is None:
            # Core is set on telegram plugin after init
            self._core = getattr(self.telegram, 'core', None)
        return self._core
    
    def _get_brain(self):
        """Lazy-get brain instance"""
        if self._brain is None:
            core = self._get_core()
            if core and hasattr(core, 'plugin_manager'):
                from src.agentic.autonomous_brain import AutonomousBrain
                self._brain = AutonomousBrain(core, core.plugin_manager)
        return self._brain
    
    async def brain_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start autonomous brain mode.
        
        Usage: /brain_start [mode]
        Modes: conservative, normal (default), aggressive
        """
        # Check owner
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        # Get mode argument
        mode = 'normal'
        if context.args:
            mode = context.args[0].lower()
            if mode not in ['conservative', 'normal', 'aggressive']:
                await update.message.reply_text(
                    "❌ Unknown mode. Use: conservative, normal, or aggressive"
                )
                return
        
        # Initialize brain if needed
        brain = self._get_brain()
        if not brain:
            await update.message.reply_text("❌ Brain not available (core not ready)")
            return
        
        # Start
        try:
            result = await brain.start(mode)
            await update.message.reply_text(result)
        except Exception as e:
            logger.error(f"Brain start error: {e}")
            await update.message.reply_text(f"❌ Error starting brain: {e}")
    
    async def brain_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop autonomous brain mode"""
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        brain = self._get_brain()
        if not brain:
            await update.message.reply_text("⚠️ Brain not running")
            return
        
        try:
            result = await brain.stop()
            await update.message.reply_text(result)
        except Exception as e:
            logger.error(f"Brain stop error: {e}")
            await update.message.reply_text(f"❌ Error stopping brain: {e}")
    
    async def brain_confidence_debug(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Debug why AGI cycles get low confidence"""
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        try:
            core = self._get_core()
            if core and 'brain' in core.plugin_manager.plugins:
                plugin = core.plugin_manager.plugins['brain']
                result = plugin.confidence_debug_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Brain plugin not available")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def brain_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get brain status and statistics"""
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        brain = self._get_brain()
        if not brain:
            await update.message.reply_text(
                "🧠 Brain Status\n\n"
                "Status: 🔴 Stopped\n"
                "Use /brain_start to activate"
            )
            return
        
        try:
            status = brain.get_status()
            
            # Format status
            running_emoji = "🟢" if status['running'] else "🔴"
            
            msg = (
                f"🧠 Brain Status\n\n"
                f"Status: {running_emoji} {'Running' if status['running'] else 'Stopped'}\n"
                f"Mode: {status['mode'].upper()}\n"
                f"Uptime: {status['uptime']}\n"
                f"Last Cycle: {status['last_cycle'][:19] if status['last_cycle'] else 'N/A'}\n\n"
                f"📊 Statistics (Last Hour)\n"
                f"Cycles: {status['cycles_completed']}\n"
                f"Actions: {status['actions_taken']}\n"
                f"Blocked: {status['actions_blocked']}\n"
                f"Success Rate: {status['success_rate']:.1%}\n\n"
                f"⏱️ Current Hour\n"
                f"Actions: {status['actions_this_hour']}/{status['max_actions_per_hour']}\n"
            )
            
            # Add recent breakdown
            if status['recent_stats'] and status['recent_stats'].get('by_action_type'):
                msg += "\n📈 Recent Actions:\n"
                for action_type, count in list(status['recent_stats']['by_action_type'].items())[:5]:
                    msg += f"  • {action_type}: {count}\n"
            
            await update.message.reply_text(msg)
            
        except Exception as e:
            logger.error(f"Brain status error: {e}")
            await update.message.reply_text(f"❌ Error getting status: {e}")
    
    async def brain_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Change brain mode without stopping.
        
        Usage: /brain_mode <conservative|normal|aggressive>
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /brain_mode <conservative|normal|aggressive>"
            )
            return
        
        mode = context.args[0].lower()
        
        brain = self._get_brain()
        if not brain:
            await update.message.reply_text("⚠️ Brain not initialized")
            return
        
        try:
            result = brain.set_mode(mode)
            await update.message.reply_text(result)
        except Exception as e:
            logger.error(f"Brain mode error: {e}")
            await update.message.reply_text(f"❌ Error setting mode: {e}")
    
    async def brain_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        View recent action log.
        
        Usage: /brain_log [hours]
        """
        if not self._is_owner(update):
            await update.message.reply_text("⛔ Owner only")
            return
        
        hours = 1
        if context.args:
            try:
                hours = int(context.args[0])
            except ValueError:
                pass
        
        # Log doesn't need brain running, just needs database
        try:
            from src.agentic.action_logger import ActionLogger
            logger_db = ActionLogger()
            
            actions = logger_db.get_recent_actions(limit=10)
            
            if not actions:
                await update.message.reply_text(f"📭 No actions in last {hours} hour(s)")
                return
            
            msg = f"📝 Recent Actions (Last {hours}h)\n\n"
            
            for action in actions:
                outcome_emoji = "✅" if action.outcome == "success" else "❌" if action.outcome == "failure" else "⏳"
                msg += (
                    f"{outcome_emoji} {action.action_type.upper()}\n"
                    f"  Target: {action.target_name or action.target_id or 'N/A'}\n"
                    f"  Conf: {action.confidence:.2f} | Field: {action.field_status}\n"
                    f"  Time: {action.timestamp.strftime('%H:%M')}\n\n"
                )
            
            await update.message.reply_text(msg[:4000])  # Telegram limit
            
        except Exception as e:
            logger.error(f"Brain log error: {e}")
            await update.message.reply_text(f"❌ Error getting log: {e}")
    
    def _is_owner(self, update: Update) -> bool:
        """Check if user is owner"""
        user_id = str(update.effective_user.id)
        owner_id = None
        
        # Try to get owner ID from config
        core = self._get_core()
        if core and hasattr(core, 'config'):
            owner_id = core.config.get('TELEGRAM_ADMIN_CHAT_ID')
        
        # Fallback to env
        if not owner_id:
            import os
            owner_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
        
        return user_id == str(owner_id)
    
    def get_handlers(self):
        """Get command handlers for registration"""
        from telegram.ext import CommandHandler
        
        return [
            CommandHandler('brain_start', self.brain_start),
            CommandHandler('brain_stop', self.brain_stop),
            CommandHandler('brain_status', self.brain_status),
            CommandHandler('brain_mode', self.brain_mode),
            CommandHandler('brain_log', self.brain_log),
        ]


# Convenience function for registration
def register_brain_commands(dispatcher, core=None):
    """Register all brain commands with dispatcher"""
    commands = BrainCommands(core)
    for handler in commands.get_handlers():
        dispatcher.add_handler(handler)
    logger.info("🧠 Brain commands registered")
