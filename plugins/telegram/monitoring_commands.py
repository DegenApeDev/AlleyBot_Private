"""
Monitoring Dashboard Commands for Telegram

Provides real-time visibility into AlleyBot's autonomous operations.
"""

import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class MonitoringCommands:
    """Telegram commands for monitoring autonomous operations"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
        self.core = telegram_plugin.core
    
    @property
    def plugin_manager(self):
        """Get plugin manager from core"""
        return self.core.plugin_manager if self.core else None
    
    async def _verify_owner(self, update: Update) -> bool:
        """Verify user is owner"""
        return await self.telegram._verify_owner(update)
    
    async def brain_recent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show last 10 brain actions"""
        if not await self._verify_owner(update):
            return
        
        try:
            # Get brain instance
            from src.agentic.autonomous_brain import AutonomousBrain
            brain = None
            
            # Try to get from plugin manager
            if self.plugin_manager:
                for plugin_name, plugin in self.plugin_manager.plugins.items():
                    if hasattr(plugin, '_brain'):
                        brain = plugin._brain
                        break
            
            if not brain:
                await update.message.reply_text("❌ Brain not running")
                return
            
            # Get recent actions from action logger
            if hasattr(brain, 'action_logger'):
                recent_actions = brain.action_logger.get_recent_actions(limit=10)
                
                if not recent_actions:
                    await update.message.reply_text("📭 No recent actions")
                    return
                
                msg = "📊 **Recent Brain Actions** (Last 10)\n\n"
                for action in recent_actions:
                    timestamp = action.timestamp.strftime("%H:%M:%S")
                    status = "✅" if action.success else "❌"
                    msg += f"{status} `{timestamp}` - {action.action_type}\n"
                    if action.target_name:
                        msg += f"   Target: {action.target_name[:30]}\n"
                
                await update.message.reply_text(msg)
            else:
                await update.message.reply_text("❌ Action logger not available")
        
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def brain_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show brain performance statistics"""
        if not await self._verify_owner(update):
            return
        
        try:
            # Get brain instance
            from src.agentic.autonomous_brain import AutonomousBrain
            brain = None
            
            if self.plugin_manager:
                for plugin_name, plugin in self.plugin_manager.plugins.items():
                    if hasattr(plugin, '_brain'):
                        brain = plugin._brain
                        break
            
            if not brain or not brain._running:
                await update.message.reply_text("❌ Brain not running")
                return
            
            # Calculate uptime
            if brain.stats.get('start_time'):
                uptime = datetime.now() - brain.stats['start_time']
                uptime_str = str(uptime).split('.')[0]
            else:
                uptime_str = "Unknown"
            
            # Calculate success rate
            total_actions = brain.stats['actions_taken']
            success_rate = brain._get_success_rate() if hasattr(brain, '_get_success_rate') else 0.0
            
            msg = (
                f"📊 **Brain Performance Stats**\n\n"
                f"⏱️ Uptime: {uptime_str}\n"
                f"🔄 Cycles: {brain.stats['cycles_completed']}\n"
                f"✅ Actions: {total_actions}\n"
                f"⛔ Blocked: {brain.stats['actions_blocked']}\n"
                f"❌ Errors: {brain.stats['errors']}\n"
                f"📈 Success Rate: {success_rate:.1%}\n"
                f"⚡ Actions/hour: {brain._actions_this_hour}/{brain.config.max_actions_per_hour}\n"
                f"🎯 Mode: {brain.config.mode.upper()}\n"
                f"🔄 Cycle: {brain.config.cycle_interval_minutes} min\n"
                f"🎲 Min Confidence: {brain.config.min_confidence}"
            )
            
            await update.message.reply_text(msg)
        
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def brain_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system health check"""
        if not await self._verify_owner(update):
            return
        
        try:
            health_status = []
            
            # Check brain
            from src.agentic.autonomous_brain import AutonomousBrain
            brain = None
            if self.plugin_manager:
                for plugin_name, plugin in self.plugin_manager.plugins.items():
                    if hasattr(plugin, '_brain'):
                        brain = plugin._brain
                        break
            
            if brain and brain._running:
                health_status.append("✅ Brain: Running")
                
                # Check last cycle time
                if brain._last_cycle:
                    time_since = (datetime.now() - brain._last_cycle).total_seconds() / 60
                    if time_since < brain.config.cycle_interval_minutes * 2:
                        health_status.append(f"✅ Last Cycle: {time_since:.1f} min ago")
                    else:
                        health_status.append(f"⚠️ Last Cycle: {time_since:.1f} min ago (delayed)")
            else:
                health_status.append("❌ Brain: Not running")
            
            # Check error recovery
            from src.agentic.error_recovery import get_error_recovery
            error_recovery = get_error_recovery()
            if error_recovery:
                summary = error_recovery.get_error_summary()
                errors_last_hour = summary['total_errors_last_hour']
                
                if errors_last_hour == 0:
                    health_status.append("✅ Errors: None (last hour)")
                elif errors_last_hour < 5:
                    health_status.append(f"⚠️ Errors: {errors_last_hour} (last hour)")
                else:
                    health_status.append(f"❌ Errors: {errors_last_hour} (last hour)")
                
                # Check circuit breakers
                if summary['circuit_breakers']:
                    health_status.append(f"⚠️ Circuit Breakers: {len(summary['circuit_breakers'])} tripped")
                else:
                    health_status.append("✅ Circuit Breakers: All clear")
            
            # Check autonomous startup
            from src.agentic.autonomous_startup import get_autonomous_startup
            startup = get_autonomous_startup()
            if startup:
                status = startup.get_status()
                if status['brain_running']:
                    health_status.append("✅ Autonomous Mode: Active")
                else:
                    health_status.append("❌ Autonomous Mode: Inactive")
                
                if status['restart_count'] > 0:
                    health_status.append(f"🔄 Restarts: {status['restart_count']} (this hour)")
            
            # Check auto skill builder
            from src.agentic.auto_skill_builder import get_auto_skill_builder
            skill_builder = get_auto_skill_builder()
            if skill_builder:
                status = skill_builder.get_status()
                health_status.append(f"🔨 Skills Built: {status['skills_built']}")
                health_status.append(f"💡 Proposals: {status['proposals_pending']}")
            
            # Check plugins
            if self.plugin_manager:
                total_plugins = len(self.plugin_manager.plugins)
                health_status.append(f"🔌 Plugins: {total_plugins} loaded")
            
            msg = "🏥 **System Health Check**\n\n" + "\n".join(health_status)
            await update.message.reply_text(msg)
        
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def brain_skills(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show auto-built skills status"""
        if not await self._verify_owner(update):
            return
        
        try:
            from src.agentic.auto_skill_builder import get_auto_skill_builder
            skill_builder = get_auto_skill_builder()
            
            if not skill_builder:
                await update.message.reply_text("❌ Auto skill builder not available")
                return
            
            status = skill_builder.get_status()
            
            msg = "🔨 **Auto Skill Builder Status**\n\n"
            msg += f"💡 Proposals Pending: {status['proposals_pending']}\n"
            msg += f"✅ Skills Built: {status['skills_built']}\n\n"
            
            if status['recent_builds']:
                msg += "**Recent Builds:**\n"
                for skill in status['recent_builds']:
                    msg += f"  • {skill}\n"
            
            if status['top_skills']:
                msg += "\n**Most Used Skills:**\n"
                for skill, count in status['top_skills']:
                    msg += f"  • {skill}: {count} uses\n"
            
            await update.message.reply_text(msg)
        
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    def register_commands(self, application):
        """Register monitoring commands"""
        from telegram.ext import CommandHandler
        
        application.add_handler(CommandHandler("brain_recent", self.brain_recent))
        application.add_handler(CommandHandler("brain_stats", self.brain_stats))
        application.add_handler(CommandHandler("brain_health", self.brain_health))
        application.add_handler(CommandHandler("brain_skills", self.brain_skills))
