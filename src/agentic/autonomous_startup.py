"""
Autonomous Startup System for AlleyBot

Handles automatic brain startup, self-healing, and continuous operation.
Makes AlleyBot 100% autonomous without manual intervention.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class AutonomousStartup:
    """
    Manages autonomous brain startup and self-healing.
    
    Features:
    - Auto-start brain on boot
    - Self-healing on errors
    - Health monitoring
    - Automatic recovery
    """
    
    def __init__(self, core, plugin_manager):
        self.core = core
        self.plugin_manager = plugin_manager
        self.brain = None
        self.health_check_task = None
        self.restart_count = 0
        self.last_restart = None
        
        # Configuration from environment
        self.auto_start = os.getenv('AUTO_START_BRAIN', 'true').lower() == 'true'
        self.brain_mode = os.getenv('BRAIN_MODE', 'normal')
        self.auto_restart = os.getenv('BRAIN_AUTO_RESTART', 'true').lower() == 'true'
        self.health_check_interval = int(os.getenv('BRAIN_HEALTH_CHECK_MINUTES', '5'))
        self.max_restarts_per_hour = int(os.getenv('BRAIN_MAX_RESTARTS_PER_HOUR', '3'))
    
    async def initialize(self):
        """Initialize autonomous systems"""
        logger.info("🤖 Initializing Autonomous Startup System...")
        
        # === GOAL PERSISTENCE: Resume USER_COMMAND goals from previous session ===
        await self._resume_user_command_goals()
        
        if self.auto_start:
            logger.info(f"✅ Auto-start enabled (mode: {self.brain_mode})")
            # Wait a bit for all plugins to be ready
            await asyncio.sleep(5)
            await self.start_brain()
        else:
            logger.info("ℹ️  Auto-start disabled (use /brain_start to start manually)")
        
        # Start health monitoring
        if self.auto_restart:
            self.health_check_task = asyncio.create_task(self._health_monitor_loop())
            logger.info(f"✅ Self-healing enabled (check every {self.health_check_interval} min)")
    
    async def start_brain(self):
        """Start the autonomous brain"""
        try:
            # Get or create brain instance
            if not self.brain:
                from src.agentic.autonomous_brain import AutonomousBrain
                self.brain = AutonomousBrain(
                    core=self.core,
                    plugin_manager=self.plugin_manager
                )
            
            # Start brain
            result = await self.brain.start(mode=self.brain_mode)
            logger.info(f"🧠 {result}")
            
            # Send Telegram notification
            await self._send_startup_notification()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start brain: {e}")
            return False
    
    async def _health_monitor_loop(self):
        """Monitor brain health and restart if needed"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval * 60)
                
                if not self.brain or not self.brain._running:
                    logger.warning("⚠️  Brain not running, attempting restart...")
                    
                    # Check restart rate limit
                    if self._can_restart():
                        await self.restart_brain()
                    else:
                        logger.error("🚨 Restart rate limit exceeded, waiting...")
                        await self._send_alert("Brain restart rate limit exceeded")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}")
    
    def _can_restart(self) -> bool:
        """Check if we can restart (rate limiting)"""
        now = datetime.now()
        
        # Reset counter if it's been more than an hour
        if self.last_restart and (now - self.last_restart) > timedelta(hours=1):
            self.restart_count = 0
        
        return self.restart_count < self.max_restarts_per_hour
    
    async def restart_brain(self):
        """Restart the brain (self-healing)"""
        try:
            logger.info("🔄 Restarting brain...")
            
            # Stop if running
            if self.brain and self.brain._running:
                await self.brain.stop()
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Start again
            success = await self.start_brain()
            
            if success:
                self.restart_count += 1
                self.last_restart = datetime.now()
                logger.info(f"✅ Brain restarted successfully (restart #{self.restart_count})")
            else:
                logger.error("❌ Brain restart failed")
                await self._send_alert("Brain restart failed")
            
        except Exception as e:
            logger.error(f"❌ Restart error: {e}")
            await self._send_alert(f"Brain restart error: {e}")
    
    async def _send_startup_notification(self):
        """Send Telegram notification that brain started"""
        try:
            telegram = self.plugin_manager.get_plugin('telegram')
            if telegram and hasattr(telegram, 'send_alert'):
                message = (
                    f"🧠 **Autonomous Brain Started**\n\n"
                    f"Mode: {self.brain_mode.upper()}\n"
                    f"Cycle: {self.brain.config.cycle_interval_minutes} min\n"
                    f"Max actions/hour: {self.brain.config.max_actions_per_hour}\n"
                    f"Min confidence: {self.brain.config.min_confidence}\n"
                    f"Auto-restart: {'✅ Enabled' if self.auto_restart else '❌ Disabled'}\n\n"
                    f"AlleyBot is now operating autonomously! 🚀"
                )
                telegram.send_alert("Autonomous Mode", message, "low")
        except Exception as e:
            logger.warning(f"⚠️  Could not send startup notification: {e}")
    
    async def _send_alert(self, message: str):
        """Send alert to owner"""
        try:
            telegram = self.plugin_manager.get_plugin('telegram')
            if telegram and hasattr(telegram, 'send_alert'):
                telegram.send_alert("Brain Alert", message, "high")
        except Exception as e:
            logger.warning(f"⚠️  Could not send alert: {e}")
    
    async def _resume_user_command_goals(self):
        """
        Resume USER_COMMAND goals from previous session.
        
        Called on startup to ensure user-requested tasks are not lost
        if the bot was restarted while processing.
        """
        try:
            logger.info("🔍 Checking for pending USER_COMMAND goals from previous session...")
            
            # Get work item manager
            from src.agentic.work_item_manager import get_work_item_manager
            work_item_manager = get_work_item_manager()
            
            # Get all active work items
            active_items = work_item_manager.get_active_work_items(limit=50)
            
            if not active_items:
                logger.info("✅ No pending work items to resume")
                return
            
            # Filter for user-originated items
            user_items = [
                item for item in active_items 
                if item.get('source') == 'user' 
                or 'user' in str(item.get('metadata', {})).lower()
                or 'telegram' in str(item.get('metadata', {})).lower()
            ]
            
            if not user_items:
                logger.info(f"✅ Found {len(active_items)} work items, none are USER_COMMAND")
                return
            
            logger.info(f"🎯 Found {len(user_items)} USER_COMMAND goals to resume")
            
            # Log each resumed goal
            for item in user_items:
                summary = item.get('summary', 'Unknown task')
                logger.info(f"   📌 Resuming: {summary[:60]}...")
            
            # Notify user about resumed goals
            await self._send_resumed_goals_notification(user_items)
            
        except Exception as e:
            logger.warning(f"⚠️  Could not resume user command goals: {e}")
    
    async def _send_resumed_goals_notification(self, user_items):
        """Notify user that goals were resumed after restart"""
        try:
            telegram = self.plugin_manager.get_plugin('telegram')
            if not telegram or not hasattr(telegram, 'send_alert'):
                return
            
            if len(user_items) == 0:
                return
            
            # Build message
            message = f"🔄 **Bot Restarted - Resuming {len(user_items)} Task(s)**\n\n"
            message += "The following user-requested tasks were preserved:\n"
            
            for i, item in enumerate(user_items[:5], 1):  # Show max 5
                summary = item.get('summary', 'Unknown task')[:50]
                message += f"{i}. {summary}...\n"
            
            if len(user_items) > 5:
                message += f"...and {len(user_items) - 5} more\n"
            
            message += "\nThese tasks will be completed and you'll be notified of results."
            
            telegram.send_alert("Tasks Resumed", message, "medium")
            logger.info(f"📨 Sent resumed goals notification for {len(user_items)} tasks")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not send resumed goals notification: {e}")
    
    def get_status(self) -> dict:
        """Get autonomous system status"""
        return {
            'auto_start_enabled': self.auto_start,
            'brain_mode': self.brain_mode,
            'brain_running': self.brain._running if self.brain else False,
            'auto_restart_enabled': self.auto_restart,
            'restart_count': self.restart_count,
            'last_restart': self.last_restart.isoformat() if self.last_restart else None,
            'health_check_interval_minutes': self.health_check_interval
        }


# Singleton instance
_autonomous_startup = None


def get_autonomous_startup(core=None, plugin_manager=None):
    """Get or create autonomous startup singleton"""
    global _autonomous_startup
    if _autonomous_startup is None and core and plugin_manager:
        _autonomous_startup = AutonomousStartup(core, plugin_manager)
    return _autonomous_startup
