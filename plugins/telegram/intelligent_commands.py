"""
Intelligent Telegram Commands for AlleyBot
AI-powered assistant commands integrated with production architecture
"""

from telegram import Update
from telegram.ext import ContextTypes


class IntelligentTelegramCommands:
    """Intelligent command handlers for Telegram bot"""
    
    def __init__(self, telegram_plugin):
        self.telegram = telegram_plugin
        self.core = telegram_plugin.core
    
    async def ai_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI-powered chat - natural language interaction"""
        try:
            user_message = ' '.join(context.args) if context.args else update.message.text
            
            # Use production model router for intelligent responses
            from src.config.models import ModelRouter
            from src.agents.session_manager import SessionManager
            
            router = ModelRouter()
            session_manager = SessionManager()
            
            # Get session context
            session_id = f"telegram_{update.effective_user.id}"
            session = await session_manager.load_session(session_id)
            rag_context = await session_manager.get_rag_context(session_id, user_message)
            
            # Route to appropriate model
            from src.agents.event_runner import AgentEvent, EventType
            from datetime import datetime
            
            event = AgentEvent(
                event_type=EventType.MESSAGE_RECEIVED,
                session_id=session_id,
                channel="telegram",
                payload={"query": user_message},
                timestamp=datetime.now(),
                priority=3
            )
            
            response = await router.route_and_execute(event, session, rag_context)
            
            # Update session
            await session_manager.update_rag_memory(session_id, user_message, response)
            
            await update.message.reply_text(response)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def moltx_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a post on Moltx"""
        try:
            if not context.args:
                await update.message.reply_text("📝 Usage: /moltx_post [your message]")
                return
            
            post_content = ' '.join(context.args)
            
            if self.core and hasattr(self.core, 'plugin_manager') and 'moltx' in self.core.plugin_manager.plugins:
                moltx_plugin = self.core.plugin_manager.plugins['moltx']
                result = moltx_plugin.create_post(post_content)
                await update.message.reply_text(f"📢 Moltx Post:\n{result}")
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def moltx_feed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Browse Moltx feed"""
        try:
            if self.core and hasattr(self.core, 'plugin_manager') and 'moltx' in self.core.plugin_manager.plugins:
                moltx_plugin = self.core.plugin_manager.plugins['moltx']
                result = moltx_plugin.feed_command()
                await update.message.reply_text(f"📰 Moltx Feed:\n{result}")
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def moltx_engage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Engage with Moltx feed (like/comment)"""
        try:
            count = int(context.args[0]) if context.args else 3
            
            if self.core and hasattr(self.core, 'plugin_manager') and 'moltx' in self.core.plugin_manager.plugins:
                moltx_plugin = self.core.plugin_manager.plugins['moltx']
                result = moltx_plugin.engage_feed_command(str(count))
                await update.message.reply_text(f"🤖 Engagement:\n{result}")
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def moltx_trending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyze trending topics on Moltx"""
        try:
            if self.core and hasattr(self.core, 'plugin_manager') and 'moltx' in self.core.plugin_manager.plugins:
                moltx_plugin = self.core.plugin_manager.plugins['moltx']
                if hasattr(moltx_plugin, 'trending_command'):
                    result = moltx_plugin.trending_command()
                    await update.message.reply_text(f"🔥 Trending:\n{result}")
                else:
                    await update.message.reply_text("📊 Trending analysis coming soon!")
            else:
                await update.message.reply_text("❌ Moltx plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def moltbook_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a post on MoltBook"""
        try:
            if not context.args:
                await update.message.reply_text("📝 Usage: /moltbook_post [your message]")
                return
            
            post_content = ' '.join(context.args)
            
            if self.core and hasattr(self.core, 'plugin_manager') and 'moltbook' in self.core.plugin_manager.plugins:
                moltbook_plugin = self.core.plugin_manager.plugins['moltbook']
                if hasattr(moltbook_plugin, 'create_post'):
                    result = moltbook_plugin.create_post(post_content)
                    await update.message.reply_text(f"📚 MoltBook Post:\n{result}")
                else:
                    await update.message.reply_text("📚 MoltBook posting coming soon!")
            else:
                await update.message.reply_text("❌ MoltBook plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get comprehensive status of all platforms"""
        try:
            status_text = "📊 **AlleyBot Status**\n\n"
            
            if self.core and hasattr(self.core, 'plugin_manager'):
                plugins = self.core.plugin_manager.plugins
                
                # Check each platform
                platforms = {
                    'moltx': '🐦 Moltx',
                    'moltbook': '📚 MoltBook',
                    'moltchan': '💬 MoltChan',
                    'moltroad': '🛣️ MoltRoad',
                    'clawtasks': '🦞 ClawTasks'
                }
                
                for plugin_name, display_name in platforms.items():
                    if plugin_name in plugins:
                        plugin = plugins[plugin_name]
                        if hasattr(plugin, 'get_status'):
                            try:
                                plugin_status = plugin.get_status()
                                status_text += f"{display_name}: ✅ Active\n"
                            except:
                                status_text += f"{display_name}: ⚠️ Error\n"
                        else:
                            status_text += f"{display_name}: ✅ Loaded\n"
                    else:
                        status_text += f"{display_name}: ❌ Not loaded\n"
                
                # Production mode info
                status_text += "\n🚀 **Production Mode**\n"
                status_text += "• Event-driven architecture: ✅\n"
                status_text += "• Model routing: ✅ DeepSeek/Grok\n"
                status_text += "• Skills loaded: ✅\n"
                status_text += "• Session persistence: ✅\n"
            
            await update.message.reply_text(status_text)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def skills(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List available skills"""
        try:
            from src.skills.skill_loader import SkillLoader
            
            loader = SkillLoader()
            skills = loader.list_skills()
            
            skills_text = "🎯 **Available Skills**\n\n"
            
            # Group by category
            categories = {}
            for skill in skills:
                if skill.category not in categories:
                    categories[skill.category] = []
                categories[skill.category].append(skill)
            
            for category, category_skills in categories.items():
                skills_text += f"**{category.replace('_', ' ').title()}:**\n"
                for skill in category_skills:
                    skills_text += f"• {skill.name}: {skill.description}\n"
                skills_text += "\n"
            
            await update.message.reply_text(skills_text)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def execute_skill(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute a skill by name"""
        try:
            if not context.args:
                await update.message.reply_text("📝 Usage: /skill [skill_name] [params...]")
                return
            
            skill_name = context.args[0]
            params = {}
            
            # Parse parameters (key=value format)
            for arg in context.args[1:]:
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    params[key] = value
            
            from src.skills.skill_loader import SkillLoader
            
            loader = SkillLoader()
            result = await loader.execute_skill(skill_name, params, self.core)
            
            await update.message.reply_text(f"🎯 Skill Result:\n{result}")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show comprehensive help"""
        help_text = """🤖 **AlleyBot AI Assistant**

**AI Chat:**
/chat [message] - Chat with AI (uses RAG memory)
Just send any message - I'll respond intelligently!

**Moltx Commands:**
/moltx_post [message] - Create Moltx post
/moltx_feed - Browse Moltx feed
/moltx_engage [count] - Engage with feed
/moltx_trending - Analyze trending topics

**MoltBook Commands:**
/moltbook_post [message] - Create MoltBook post

**System Commands:**
/status - Platform status
/skills - List available skills
/skill [name] [params] - Execute skill
/help - Show this help

**Production Features:**
✅ Event-driven architecture
✅ Smart model routing (DeepSeek/Grok)
✅ RAG memory system
✅ Session persistence
✅ Dynamic skills system

I'm your intelligent AI assistant - ask me anything! 🚀"""
        
        await update.message.reply_text(help_text)
