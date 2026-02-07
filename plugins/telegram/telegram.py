"""
Telegram Plugin for AlleyBot
Secure two-way communication with owner DegenApeDev (User ID: 6172568442)
"""

import os
import requests
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from plugin_manager import AlleyBotPlugin

class Telegram(AlleyBotPlugin):
    """Telegram bot for secure owner communication"""
    
    def __init__(self, config):
        super().__init__(config)
        self.enabled = config.get('enabled', False)
        self.core = None
        
        # Owner configuration - use env var, never hardcode
        admin_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '')
        self.owner_user_id = int(admin_id) if admin_id.isdigit() else None
        self.owner_name = "DegenApeDev"
        
        # Telegram bot configuration
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.bot = None
        self.application = None
        
        # Communication state
        self.is_running = False
        self.message_queue = []
        self.last_activity = None
        
        # Always try to initialize if token exists
        if self.bot_token:
            try:
                self.bot = Bot(token=self.bot_token)
                self.application = Application.builder().token(self.bot_token).build()
                self._setup_handlers()
                print("✅ Telegram plugin initialized - Owner: DegenApeDev")
                # Plugin is enabled if we have a token
                self.enabled = True
            except Exception as e:
                print(f"❌ Failed to initialize Telegram bot: {e}")
                self.enabled = False
        else:
            if self.enabled:
                print("⚠️  TELEGRAM_BOT_TOKEN not found in environment")
            self.enabled = False
    
    def _setup_handlers(self):
        """Setup Telegram bot handlers"""
        if not self.application:
            return
        
        # Import intelligent commands
        from plugins.telegram.intelligent_commands import IntelligentTelegramCommands
        self.intelligent_commands = IntelligentTelegramCommands(self)
        
        # Import conversational AI
        from plugins.telegram.conversational_ai import ConversationalAI
        self.conversational_ai = ConversationalAI(self)
        
        # Basic commands
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self.intelligent_commands.help_command))
        
        # AI & Chat commands
        self.application.add_handler(CommandHandler("chat", self.intelligent_commands.ai_chat))
        
        # Moltx commands
        self.application.add_handler(CommandHandler("moltx_post", self.intelligent_commands.moltx_post))
        self.application.add_handler(CommandHandler("moltx_feed", self.intelligent_commands.moltx_feed))
        self.application.add_handler(CommandHandler("moltx_engage", self.intelligent_commands.moltx_engage))
        self.application.add_handler(CommandHandler("moltx_trending", self.intelligent_commands.moltx_trending))
        self.application.add_handler(CommandHandler("moltx_claim", self.intelligent_commands.moltx_claim))
        self.application.add_handler(CommandHandler("moltx_check_reward", self.intelligent_commands.moltx_check_reward))
        self.application.add_handler(CommandHandler("moltx_claim_reward", self.intelligent_commands.moltx_claim_reward))
        
        # MoltBook commands
        self.application.add_handler(CommandHandler("moltbook_post", self.intelligent_commands.moltbook_post))
        
        # System commands
        self.application.add_handler(CommandHandler("status", self.conversational_ai.status_command))
        self.application.add_handler(CommandHandler("skills", self.intelligent_commands.skills))
        self.application.add_handler(CommandHandler("skill", self.intelligent_commands.execute_skill))
        self.application.add_handler(CommandHandler("token_stats", self.intelligent_commands.token_stats))
        
        # On-chain commands
        self.application.add_handler(CommandHandler("wallet", self.intelligent_commands.wallet))
        self.application.add_handler(CommandHandler("balance", self.intelligent_commands.balance))
        self.application.add_handler(CommandHandler("block", self.intelligent_commands.block))
        self.application.add_handler(CommandHandler("track", self.intelligent_commands.track_token))
        self.application.add_handler(CommandHandler("tx", self.intelligent_commands.tx))
        self.application.add_handler(CommandHandler("activity", self.intelligent_commands.activity))
        self.application.add_handler(CommandHandler("onchain", self.intelligent_commands.onchain_status))
        
        # Brain commands
        self.application.add_handler(CommandHandler("think", self.intelligent_commands.brain_think))
        self.application.add_handler(CommandHandler("brain_start", self.intelligent_commands.brain_start))
        self.application.add_handler(CommandHandler("brain_stop", self.intelligent_commands.brain_stop))
        self.application.add_handler(CommandHandler("brain", self.intelligent_commands.brain_status))
        
        # A2A commands
        self.application.add_handler(CommandHandler("a2a_status", self.intelligent_commands.a2a_status))
        self.application.add_handler(CommandHandler("a2a_start", self.intelligent_commands.a2a_start))
        self.application.add_handler(CommandHandler("a2a_stop", self.intelligent_commands.a2a_stop))
        self.application.add_handler(CommandHandler("a2a_tasks", self.intelligent_commands.a2a_tasks))
        
        # ERC-8004 / Self-improve commands
        self.application.add_handler(CommandHandler("erc8004_rebuild", self.intelligent_commands.erc8004_rebuild))
        self.application.add_handler(CommandHandler("erc8004_preview", self.intelligent_commands.erc8004_preview))
        self.application.add_handler(CommandHandler("erc8004_update", self.intelligent_commands.erc8004_update))
        self.application.add_handler(CommandHandler("improve_status", self.intelligent_commands.improve_status))
        
        # Message handler for natural language (admin only, conversational AI)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.conversational_ai.handle_message))
    
    async def _verify_owner(self, update: Update) -> bool:
        """Verify that the message is from the owner"""
        user_id = update.effective_user.id
        if user_id != self.owner_user_id:
            await update.message.reply_text(
                "🚫 This bot is private and only accessible to the owner."
            )
            return False
        return True
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not await self._verify_owner(update):
            return
        
        welcome_message = """🦞 **AlleyBot** — Autonomous AI Agent

🧠 **Brain:** /brain_start /brain_stop /think /brain
📢 **Social:** /moltx_post /moltx_feed /moltbook_post
🔗 **On-Chain:** /wallet /balance /track /tx /activity
🤝 **A2A:** /a2a_start /a2a_status /a2a_tasks
🆔 **ERC-8004:** /erc8004_rebuild /erc8004_update
⚙️ **System:** /status /token_stats /improve_status

/help - Full command list
💬 Or just talk to me naturally!

Send /brain_start to go autonomous. 🤖"""
        
        await update.message.reply_text(welcome_message)
        self._log_activity("command", {"command": "start", "user": "DegenApeDev"})
    
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if not await self._verify_owner(update):
            return
        
        try:
            # Get comprehensive status from all plugins
            status_parts = ["🦞 **AlleyBot Status Report**\n"]
            
            # Core status
            status_parts.append(f"🤖 **Core System**: ✅ Online")
            status_parts.append(f"👤 **Owner**: {self.owner_name}")
            status_parts.append(f"🕐 **Last Activity**: {self.last_activity or 'Never'}")
            
            # Plugin statuses
            if self.core:
                for plugin_name, plugin in self.core.plugins.items():
                    if hasattr(plugin, 'get_status'):
                        try:
                            plugin_status = plugin.get_status()
                            status_parts.append(f"🔌 **{plugin_name.title()}**: {plugin_status}")
                        except Exception as e:
                            status_parts.append(f"🔌 **{plugin_name.title()}**: ❌ Error: {e}")
            
            # Activity summary
            activities = self.core.get_memory('moltx_activities') if self.core else []
            recent_activities = activities[-5:] if activities else []
            
            if recent_activities:
                status_parts.append("\n📊 **Recent Activities**:")
                for activity in recent_activities:
                    activity_type = activity.get('type', 'unknown')
                    timestamp = activity.get('timestamp', 'unknown')
                    status_parts.append(f"  • {activity_type} at {timestamp}")
            
            status_message = "\n".join(status_parts)
            await update.message.reply_text(status_message)
            
            self._log_activity("command", {"command": "status", "user": "DegenApeDev"})
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting status: {str(e)}")
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        if not await self._verify_owner(update):
            return
        
        help_message = """🦞 **AlleyBot Commands**:

**📊 Information:**
/status - Get comprehensive status report
/help - Show this help message

**💬 Moltx DM Management:**
/dm_check - Check and reply to new DMs
/dm_log - View DM activity log

**📢 Social Media:**
/post [message] - Create a Moltx post
/feed - Get Moltx feed
/engage - Engage with feed posts

**🤖 Autonomous Control:**
/autonomous - Toggle autonomous mode

**💬 Chat:**
Just send any message and I'll respond using Grok 4-1 reasoning!

🔒 This bot is private and only responds to DegenApeDev."""
        
        await update.message.reply_text(help_message)
        self._log_activity("command", {"command": "help", "user": "DegenApeDev"})
    
    async def _handle_dm_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /dm_check command"""
        if not await self._verify_owner(update):
            return
        
        try:
            if self.core and 'moltx' in self.core.plugins:
                moltx_plugin = self.core.plugins['moltx']
                result = moltx_plugin.check_and_reply_to_dms()
                await update.message.reply_text(f"📬 DM Check Result:\n{result}")
                self._log_activity("command", {"command": "dm_check", "user": "DegenApeDev", "result": result})
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
        except Exception as e:
            await update.message.reply_text(f"❌ Error checking DMs: {str(e)}")
    
    async def _handle_dm_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /dm_log command"""
        if not await self._verify_owner(update):
            return
        
        try:
            if self.core and 'moltx' in self.core.plugins:
                moltx_plugin = self.core.plugins['moltx']
                result = moltx_plugin.get_dm_log(10)  # Last 10 entries
                await update.message.reply_text(f"📝 DM Activity Log:\n{result}")
                self._log_activity("command", {"command": "dm_log", "user": "DegenApeDev"})
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting DM log: {str(e)}")
    
    async def _handle_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /post command"""
        if not await self._verify_owner(update):
            return
        
        try:
            # Get post content from command arguments
            post_content = " ".join(context.args) if context.args else ""
            
            if not post_content:
                await update.message.reply_text("📝 Usage: /post [your message]")
                return
            
            if self.core and 'moltx' in self.core.plugins:
                moltx_plugin = self.core.plugins['moltx']
                result = moltx_plugin.create_post(post_content)
                await update.message.reply_text(f"📢 Post Result:\n{result}")
                self._log_activity("command", {"command": "post", "user": "DegenApeDev", "content": post_content})
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
        except Exception as e:
            await update.message.reply_text(f"❌ Error creating post: {str(e)}")
    
    async def _handle_feed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /feed command"""
        if not await self._verify_owner(update):
            return
        
        try:
            if self.core and 'moltx' in self.core.plugins:
                moltx_plugin = self.core.plugins['moltx']
                result = moltx_plugin.feed_command()
                await update.message.reply_text(f"📰 Moltx Feed:\n{result}")
                self._log_activity("command", {"command": "feed", "user": "DegenApeDev"})
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting feed: {str(e)}")
    
    async def _handle_engage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /engage command"""
        if not await self._verify_owner(update):
            return
        
        try:
            if self.core and 'moltx' in self.core.plugins:
                moltx_plugin = self.core.plugins['moltx']
                result = moltx_plugin.engage_feed_command()
                await update.message.reply_text(f"🤖 Engagement Result:\n{result}")
                self._log_activity("command", {"command": "engage", "user": "DegenApeDev"})
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
        except Exception as e:
            await update.message.reply_text(f"❌ Error engaging with feed: {str(e)}")
    
    async def _handle_autonomous(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /autonomous command"""
        if not await self._verify_owner(update):
            return
        
        try:
            # Toggle autonomous mode (this would need to be implemented in core)
            await update.message.reply_text("🤖 Autonomous mode toggle not yet implemented")
            self._log_activity("command", {"command": "autonomous", "user": "DegenApeDev"})
        except Exception as e:
            await update.message.reply_text(f"❌ Error toggling autonomous mode: {str(e)}")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages from owner"""
        if not await self._verify_owner(update):
            return
        
        try:
            user_message = update.message.text
            
            # Use Grok AI to generate intelligent response
            if self.core and hasattr(self.core, 'plugins') and 'moltx' in self.core.plugins:
                moltx_plugin = self.core.plugins['moltx']
                
                # Generate intelligent reply using Grok
                reply = moltx_plugin.generate_dm_reply(user_message, self.owner_name)
                
                if reply:
                    await update.message.reply_text(reply)
                    self._log_activity("chat", {
                        "user_message": user_message[:100] + '...' if len(user_message) > 100 else user_message,
                        "bot_reply": reply[:100] + '...' if len(reply) > 100 else reply,
                        "user": "DegenApeDev"
                    })
                else:
                    await update.message.reply_text("🤔 I'm thinking... but couldn't generate a response right now.")
            else:
                # Fallback response
                await update.message.reply_text("🦞 Hey DegenApeDev! I'm here and ready to help. Use /help to see what I can do!")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error processing message: {str(e)}")
    
    def _log_activity(self, activity_type, data):
        """Log Telegram activity"""
        try:
            telegram_log = self.core.get_memory('telegram_log') if self.core else []
            
            # Ensure telegram_log is a list
            if isinstance(telegram_log, dict):
                telegram_log = list(telegram_log.values()) if telegram_log else []
            elif not isinstance(telegram_log, list):
                telegram_log = []
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'activity_type': activity_type,
                'data': data,
                'user': 'DegenApeDev'
            }
            
            telegram_log.append(log_entry)
            
            # Keep last 100 entries
            if self.core:
                self.core.save_memory('telegram_log', telegram_log[-100:])
            
            self.last_activity = datetime.now().isoformat()
            
        except Exception as e:
            print(f"⚠️  Failed to log Telegram activity: {e}")
    
    def _filter_outbound(self, text: str) -> str:
        """Run outbound text through the security filter to prevent key leaks"""
        try:
            from security_filter import security_filter
            filtered, was_filtered = security_filter.filter_message(str(text))
            if was_filtered:
                print("⚠️  SECURITY: Filtered sensitive data from Telegram outbound message")
            return filtered
        except Exception:
            return str(text)

    async def send_message_to_owner(self, message: str):
        """Send a message to the owner"""
        if not self.enabled or not self.bot:
            return False
        
        try:
            message = self._filter_outbound(message)
            await self.bot.send_message(
                chat_id=self.owner_user_id,
                text=message
            )
            self._log_activity("outbound", {"message": message[:100] + '...' if len(message) > 100 else message})
            return True
        except Exception as e:
            print(f"❌ Failed to send message to owner: {e}")
            return False
    
    def send_message_to_owner_sync(self, message: str):
        """Send a message to the owner synchronously via HTTP API.
        Uses raw requests instead of python-telegram-bot to avoid
        event loop issues when called from background threads."""
        if not self.enabled or not self.bot_token or not self.owner_user_id:
            return False

        try:
            # Filter sensitive data
            filtered = self._filter_outbound(message)

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            resp = requests.post(url, json={
                "chat_id": self.owner_user_id,
                "text": filtered,
                "parse_mode": "Markdown",
            }, timeout=10)

            if resp.status_code == 200:
                return True

            # Retry without Markdown if parse failed
            if resp.status_code == 400 and "parse" in resp.text.lower():
                resp = requests.post(url, json={
                    "chat_id": self.owner_user_id,
                    "text": filtered,
                }, timeout=10)
                return resp.status_code == 200

            print(f"⚠️  Telegram send failed ({resp.status_code}): {resp.text[:100]}")
            return False

        except Exception as e:
            print(f"❌ Failed to send message to owner: {e}")
            return False
    
    def send_alert(self, alert_type: str, message: str, priority: str = "normal"):
        """Send an alert to the owner"""
        if not self.enabled:
            return
        
        priority_emoji = {
            "low": "🟢",
            "normal": "🔵", 
            "high": "🟡",
            "urgent": "🔴"
        }
        
        emoji = priority_emoji.get(priority, "🔵")
        formatted_message = f"{emoji} **{alert_type}**\n\n{message}"
        
        # Send synchronously to avoid async issues
        try:
            self.send_message_to_owner_sync(formatted_message)
        except Exception as e:
            print(f"⚠️  Could not send Telegram alert: {e}")
    
    def notify_dm_reply(self, sender: str, conversation: str, reply_content: str):
        """Send notification when AlleyBot replies to a DM"""
        if not self.enabled:
            return
        
        alert_message = f"""💬 **DM Reply Sent**

👤 **From**: @{sender}
🗨️ **Conversation**: {conversation}
📝 **Reply**: {reply_content[:100]}{'...' if len(reply_content) > 100 else ''}

AlleyBot is actively engaging with the community! 🦞"""
        
        self.send_alert("DM Activity", alert_message, "normal")
    
    def notify_new_follower(self, follower: str):
        """Send notification when AlleyBot gets a new follower"""
        if not self.enabled:
            return
        
        alert_message = f"""👥 **New Follower**

🎉 **@{follower}** is now following AlleyBot!

The community is growing! 🚀"""
        
        self.send_alert("Social Growth", alert_message, "normal")
    
    def notify_autonomous_activity(self, activity_type: str, details: str):
        """Send notification for important autonomous activities"""
        if not self.enabled:
            return
        
        alert_message = f"""🤖 **Autonomous Activity**

📋 **Activity**: {activity_type}
📝 **Details**: {details}

AlleyBot is working autonomously! 🦞"""
        
        self.send_alert("Autonomous Mode", alert_message, "low")
    
    def notify_error(self, error_type: str, error_message: str):
        """Send notification for important errors"""
        if not self.enabled:
            return
        
        alert_message = f"""⚠️ **System Error**

🚨 **Type**: {error_type}
📝 **Error**: {error_message}

AlleyBot encountered an issue and needs attention!"""
        
        self.send_alert("System Alert", alert_message, "high")
    
    def start_telegram_bot(self):
        """Start the Telegram bot properly"""
        if not self.enabled or not self.application:
            return False
        
        try:
            print("🤖 Starting Telegram bot polling...")
            
            # Run the bot in the current thread (blocking)
            self.application.run_polling(drop_pending_updates=True)
            self.is_running = True
            print("✅ Telegram bot started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Telegram bot: {e}")
            self.is_running = False
            return False
    
    def start_telegram_bot_daemon(self):
        """Start the Telegram bot as a daemon (for background operation)"""
        if not self.enabled or not self.application:
            return False
        
        try:
            import threading
            import asyncio
            
            def run_bot():
                try:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Run the bot
                    self.application.run_polling(drop_pending_updates=True)
                    self.is_running = True
                    
                except Exception as e:
                    print(f"❌ Telegram bot error: {e}")
                    self.is_running = False
                finally:
                    try:
                        loop.close()
                    except Exception as e:
                        print(f"⚠️  Error closing event loop: {e}")
            
            # Start bot in a separate daemon thread
            bot_thread = threading.Thread(target=run_bot, daemon=True)
            bot_thread.start()
            
            # Give it a moment to start
            import time
            time.sleep(1)
            
            self.is_running = True
            print("✅ Telegram bot started in background")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Telegram bot daemon: {e}")
            return False
    
    def stop_telegram_bot(self):
        """Stop the Telegram bot"""
        if self.application and self.is_running:
            try:
                self.application.stop()
                self.is_running = False
                print("✅ Telegram bot stopped")
            except Exception as e:
                print(f"❌ Error stopping Telegram bot: {e}")
    
    def initialize(self, api, core):
        """Initialize plugin with core system.
        
        NOTE: Polling is NOT started here. The production mode's
        telegram_webhook.start_polling_async() handles that to avoid
        two competing polling connections on the same bot token.
        """
        super().initialize(api, core)
        if self.enabled:
            print("✅ Telegram plugin ready (polling will start via production mode)")
    
    def _send_startup_notification(self):
        """Send startup notification to the owner"""
        if not self.enabled or not self.bot:
            return
        
        try:
            startup_message = """🦞 **AlleyBot is Online!**

🤖 **System Status**: All systems operational
📱 **Telegram Interface**: Connected and ready
👤 **Owner**: DegenApeDev
🕐 **Started**: Just now

I'm ready to assist! Use /help to see available commands or just chat with me directly! 🚀"""
            
            # Send synchronously to avoid async issues
            self.send_message_to_owner_sync(startup_message)
            
        except Exception as e:
            print(f"⚠️  Could not send startup notification: {e}")
    
    def _start_bot_background(self):
        """Start the Telegram bot in the background"""
        if not self.enabled or not self.application:
            return
        
        try:
            import asyncio
            
            # Create new event loop for background polling
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            print("🤖 Starting Telegram bot polling in background...")
            
            async def start_polling():
                """Start polling without signal handlers (for background threads)"""
                try:
                    # Check if already running
                    if self.application.updater.running:
                        print("⚠️  Telegram updater already running, skipping initialization")
                        self.is_running = True
                        return
                    
                    # Initialize the application
                    await self.application.initialize()
                    
                    # Start the updater (polling)
                    await self.application.updater.start_polling(
                        drop_pending_updates=True,
                        allowed_updates=Update.ALL_TYPES
                    )
                    
                    # Start the application
                    await self.application.start()
                    
                    self.is_running = True
                    print("✅ Telegram bot polling started successfully")
                    
                    # Keep the bot running
                    while self.is_running:
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    print(f"❌ Polling error: {e}")
                    import traceback
                    traceback.print_exc()
                    self.is_running = False
            
            # Run the async polling function
            loop.run_until_complete(start_polling())
            
        except Exception as e:
            print(f"❌ Failed to start Telegram bot polling: {e}")
            import traceback
            traceback.print_exc()
            self.is_running = False
    
    def cleanup(self):
        """Cleanup plugin resources"""
        self.stop_telegram_bot()
        if self.enabled:
            print("🧹 Telegram plugin cleaned up")
    
    def get_commands(self):
        """Return CLI commands for this plugin"""
        return {
            'telegram_start': self.start_command,
            'telegram_stop': self.stop_command,
            'telegram_send': self.send_command,
            'telegram_status': self.status_command
        }
    
    def get_tasks(self):
        """Return scheduled tasks for this plugin"""
        return {
            'telegram_heartbeat': {
                'function': self.heartbeat_task,
                'interval': 300,  # 5 minutes
                'enabled': self.enabled
            }
        }
    
    # CLI command methods
    def start_command(self):
        """Start Telegram bot CLI command"""
        if self.enabled:
            success = self.start_telegram_bot_daemon()
            if success:
                return "✅ Telegram bot started in background! Find @alleybot_bot on Telegram and send /start"
            else:
                return "❌ Failed to start Telegram bot"
        else:
            return "❌ Telegram plugin not enabled"
    
    def stop_command(self):
        """Stop Telegram bot CLI command"""
        self.stop_telegram_bot()
        return "✅ Telegram bot stopped"
    
    def send_command(self, message):
        """Send message to owner CLI command"""
        if not self.enabled:
            return "❌ Telegram plugin not enabled"
        
        try:
            result = self.send_message_to_owner_sync(message)
            return "✅ Message sent to DegenApeDev" if result else "❌ Failed to send message"
        except Exception as e:
            return f"❌ Error sending message: {e}"
    
    def status_command(self):
        """Get Telegram plugin status"""
        if self.enabled:
            status = f"🤖 Telegram Status:\n"
            status += f"  ✅ Plugin enabled\n"
            status += f"  👤 Owner: {self.owner_name}\n"
            status += f"  🤖 Bot: {'Running' if self.is_running else 'Stopped'}\n"
            status += f"  🕐 Last activity: {self.last_activity or 'Never'}"
            return status
        else:
            return "🤖 Telegram Status: ❌ Plugin disabled"
    
    async def heartbeat_task(self):
        """Periodic heartbeat task"""
        if self.enabled and self.core:
            # Send periodic status updates if needed
            pass
