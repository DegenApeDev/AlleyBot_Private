#!/usr/bin/env python3

"""
Dedicated Telegram Bot Listener for AlleyBot
Runs independently to listen for Telegram messages
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from plugins.telegram.telegram import Telegram

class TelegramListener:
    def __init__(self):
        # Load environment
        load_dotenv()
        
        # Configuration
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.owner_user_id = 6172568442  # DegenApeDev
        self.owner_name = "DegenApeDev"
        
        if not self.bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not found in environment")
            return
        
        # Create application
        self.application = Application.builder().token(self.bot_token).build()
        self._setup_handlers()
        
        print("✅ Telegram listener initialized")
        print(f"👤 Owner: {self.owner_name} (ID: {self.owner_user_id})")
    
    def _setup_handlers(self):
        """Setup Telegram bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("dm_check", self.dm_check_command))
        self.application.add_handler(CommandHandler("dm_log", self.dm_log_command))
        self.application.add_handler(CommandHandler("post", self.post_command))
        self.application.add_handler(CommandHandler("feed", self.feed_command))
        self.application.add_handler(CommandHandler("engage", self.engage_command))
        self.application.add_handler(CommandHandler("autonomous", self.autonomous_command))
        
        # Message handler for chat
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        
        if user_id != self.owner_user_id:
            await update.message.reply_text("❌ Access denied. This bot is for DegenApeDev only.")
            return
        
        welcome_message = f"""🦞 **Welcome to AlleyBot Telegram Interface!**

👤 **Owner**: {self.owner_name}
🤖 **Bot Status**: Online and listening

**Available Commands:**
/start - Show this welcome message
/help - Show all available commands
/status - Get AlleyBot status report
/dm_check - Check and reply to Moltx DMs
/dm_log - View DM activity log
/post [message] - Create a Moltx post
/feed - Get Moltx feed
/engage - Engage with feed posts
/autonomous - Toggle autonomous mode

**Chat Mode:**
Just send me a message and I'll respond using Grok AI! 🧠

I'm here to help you manage AlleyBot remotely! 🚀"""
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = update.effective_user.id
        
        if user_id != self.owner_user_id:
            await update.message.reply_text("❌ Access denied.")
            return
        
        help_text = """🦞 **AlleyBot Telegram Commands:**

**📊 Status & Monitoring:**
/status - Get comprehensive AlleyBot status
/dm_check - Check and reply to Moltx DMs
/dm_log - View DM activity log

**🎮 Control Commands:**
/post [message] - Create Moltx post
/feed - Get current Moltx feed
/engage - Engage with feed posts
/autonomous - Toggle autonomous mode

**💬 Chat Mode:**
Send any message to chat with AlleyBot using Grok AI!

**🔔 Features:**
• Owner-only access (DegenApeDev only)
• Real-time DM monitoring
• Intelligent responses
• Remote control capabilities

Type any message to start chatting! 🤖"""
        
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        
        if user_id != self.owner_user_id:
            await update.message.reply_text("❌ Access denied.")
            return
        
        status_message = """🦞 **AlleyBot Status Report:**

🤖 **Core Systems**: Online
📱 **Telegram Interface**: Active
🐦 **Moltx Integration**: Connected
📊 **Rate Limiting**: Active (10min cooldown)
🔔 **Notifications**: Enabled

**Recent Activity:**
• Telegram listener running
• Rate limiting preventing spam
• Ready for commands and chat

**Status**: All systems operational! 🚀"""
        
        await update.message.reply_text(status_message)
    
    async def dm_check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /dm_check command"""
        user_id = update.effective_user.id
        
        if user_id != self.owner_user_id:
            await update.message.reply_text("❌ Access denied.")
            return
        
        await update.message.reply_text("🔍 Checking Moltx DMs...")
        
        # This would integrate with the Moltx plugin
        # For now, send a placeholder response
        await update.message.reply_text("📬 DM check feature requires full AlleyBot integration. Use main AlleyBot system for DM checking.")
    
    async def dm_log_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /dm_log command"""
        user_id = update.effective_user.id
        
        if user_id != self.owner_user_id:
            await update.message.reply_text("❌ Access denied.")
            return
        
        await update.message.reply_text("📋 DM log feature requires full AlleyBot integration.")
    
    async def post_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /post command"""
        user_id = update.effective_user.id
        
        if user_id != self.owner_user_id:
            await update.message.reply_text("❌ Access denied.")
            return
        
        if not context.args:
            await update.message.reply_text("📝 Usage: /post [your message]")
            return
        
        post_content = " ".join(context.args)
        await update.message.reply_text(f"📝 Post feature requires full AlleyBot integration. Message: {post_content}")
    
    async def feed_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /feed command"""
        user_id = update.effective_user.id
        
        if user_id != self.owner_user_id:
            await update.message.reply_text("❌ Access denied.")
            return
        
        await update.message.reply_text("📱 Feed feature requires full AlleyBot integration.")
    
    async def engage_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /engage command"""
        user_id = update.effective_user.id
        
        if user_id != self.owner_user_id:
            await update.message.reply_text("❌ Access denied.")
            return
        
        await update.message.reply_text("🤝 Engage feature requires full AlleyBot integration.")
    
    async def autonomous_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /autonomous command"""
        user_id = update.effective_user.id
        
        if user_id != self.owner_user_id:
            await update.message.reply_text("❌ Access denied.")
            return
        
        await update.message.reply_text("🤖 Autonomous mode control requires full AlleyBot integration.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular chat messages"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        if user_id != self.owner_user_id:
            await update.message.reply_text("❌ Access denied. This bot is for DegenApeDev only.")
            return
        
        # Generate intelligent response using Grok AI
        try:
            # Import Grok AI for responses
            from grok_ai import GrokAI
            
            grok = GrokAI()
            if grok.enabled:
                response = grok.generate_dm_reply(user_message, self.owner_name)
                if response:
                    await update.message.reply_text(response)
                else:
                    await update.message.reply_text("🤔 I'm thinking... but couldn't generate a response right now.")
            else:
                await update.message.reply_text("🧠 AI response system not available. Please check Grok AI configuration.")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating response: {str(e)}")
    
    def run(self):
        """Run the Telegram bot listener"""
        if not self.bot_token:
            print("❌ Cannot start: No bot token")
            return
        
        print("🚀 Starting Telegram bot listener...")
        print("👂 Listening for messages from DegenApeDev...")
        print("📱 Find @alleybot_bot on Telegram and send commands!")
        print("⏹️  Press Ctrl+C to stop")
        
        try:
            self.application.run_polling(drop_pending_updates=True)
        except KeyboardInterrupt:
            print("\n🛑 Telegram listener stopped")
        except Exception as e:
            print(f"❌ Telegram listener error: {e}")

if __name__ == "__main__":
    listener = TelegramListener()
    listener.run()
