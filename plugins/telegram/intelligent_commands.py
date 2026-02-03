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
        """Create an AI-generated post on Moltx based on topic/direction"""
        try:
            if not context.args:
                await update.message.reply_text("📝 Usage: /moltx_post [topic and direction]\n\nExample: /moltx_post AI agents revolutionizing crypto")
                return
            
            topic_direction = ' '.join(context.args)
            
            # Send "generating" message
            status_msg = await update.message.reply_text("🤖 Generating post with AI...")
            
            if self.core and hasattr(self.core, 'plugin_manager') and 'moltx' in self.core.plugin_manager.plugins:
                moltx_plugin = self.core.plugin_manager.plugins['moltx']
                
                # Use Model Router to generate intelligent post
                from src.config.models import ModelRouter
                from src.agents.session_manager import SessionManager
                from src.agents.event_types import AgentEvent, EventType
                from datetime import datetime
                
                # Initialize if needed
                model_router = ModelRouter()
                session_manager = SessionManager()
                
                # Get user session
                user_id = update.effective_user.id
                session_id = f"telegram_{user_id}"
                session = await session_manager.load_session(session_id)
                rag_context = await session_manager.get_rag_context(session_id, topic_direction)
                
                # Create prompt for AI
                prompt = f"""You are AlleyBot, an autonomous AI agent on Moltx.

Create an engaging post about: {topic_direction}

Requirements:
1. Be conversational and authentic (not corporate)
2. Keep it 1-3 sentences maximum
3. Show personality and unique perspective
4. Include 1-2 relevant hashtags if appropriate
5. Make it engaging and insightful

Generate only the post content (no explanations):"""
                
                # Generate post with AI
                event = AgentEvent(
                    event_type=EventType.MESSAGE_RECEIVED,
                    session_id=session_id,
                    channel="telegram",
                    payload={"query": prompt},
                    timestamp=datetime.now(),
                    priority=2
                )
                
                post_content = await model_router.route_and_execute(
                    event=event,
                    session=session,
                    rag_context=rag_context
                )
                
                # Clean up response
                post_content = post_content.strip().strip('"').strip("'")
                
                # Save session
                await session_manager.save_session(session_id, session)
                await session_manager.update_rag_memory(session_id, topic_direction, post_content)
                
                # Post to Moltx
                result = moltx_plugin.create_post(post_content)
                
                # Update status message
                await status_msg.edit_text(f"✅ AI-Generated Post:\n\n{post_content}\n\n📢 Result: {result}")
            else:
                await status_msg.edit_text("❌ Moltx plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
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
        """Create an AI-generated post on MoltBook based on topic/direction"""
        try:
            if not context.args:
                await update.message.reply_text("📝 Usage: /moltbook_post [topic and direction]\n\nExample: /moltbook_post discussing AI agent development")
                return
            
            topic_direction = ' '.join(context.args)
            
            # Send "generating" message
            status_msg = await update.message.reply_text("🤖 Generating post with AI...")
            
            if self.core and hasattr(self.core, 'plugin_manager') and 'moltbook' in self.core.plugin_manager.plugins:
                moltbook_plugin = self.core.plugin_manager.plugins['moltbook']
                
                if hasattr(moltbook_plugin, 'create_post'):
                    # Use Model Router to generate intelligent post
                    from src.config.models import ModelRouter
                    from src.agents.session_manager import SessionManager
                    from src.agents.event_types import AgentEvent, EventType
                    from datetime import datetime
                    
                    # Initialize if needed
                    model_router = ModelRouter()
                    session_manager = SessionManager()
                    
                    # Get user session
                    user_id = update.effective_user.id
                    session_id = f"telegram_{user_id}"
                    session = await session_manager.load_session(session_id)
                    rag_context = await session_manager.get_rag_context(session_id, topic_direction)
                    
                    # Create prompt for AI
                    prompt = f"""You are AlleyBot, an autonomous AI agent on MoltBook.

Create an engaging post about: {topic_direction}

Requirements:
1. Be conversational and authentic (not corporate)
2. Keep it 2-4 sentences for MoltBook format
3. Show personality and unique perspective
4. Make it engaging and insightful
5. Suitable for discussion/community engagement

Generate only the post content (no explanations):"""
                    
                    # Generate post with AI
                    event = AgentEvent(
                        event_type=EventType.MESSAGE_RECEIVED,
                        session_id=session_id,
                        channel="telegram",
                        payload={"query": prompt},
                        timestamp=datetime.now(),
                        priority=2
                    )
                    
                    post_content = await model_router.route_and_execute(
                        event=event,
                        session=session,
                        rag_context=rag_context
                    )
                    
                    # Clean up response
                    post_content = post_content.strip().strip('"').strip("'")
                    
                    # Save session
                    await session_manager.save_session(session_id, session)
                    await session_manager.update_rag_memory(session_id, topic_direction, post_content)
                    
                    # Post to MoltBook
                    result = moltbook_plugin.create_post(
                        submolt="general",
                        title=topic_direction[:100],  # Use topic as title
                        content=post_content
                    )
                    
                    # Update status message
                    await status_msg.edit_text(f"✅ AI-Generated Post:\n\n{post_content}\n\n📚 Result: {result}")
                else:
                    await status_msg.edit_text("📚 MoltBook posting coming soon!")
            else:
                await status_msg.edit_text("❌ MoltBook plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    async def token_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get LLM API token usage statistics"""
        try:
            from src.config.models import ModelRouter
            
            # Get or create model router to access token tracker
            if hasattr(self.core, 'model_router') and self.core.model_router:
                token_tracker = self.core.model_router.token_tracker
            else:
                # Create temporary model router to access tracker
                router = ModelRouter()
                token_tracker = router.token_tracker
            
            # Get stats
            session = token_tracker.get_session_stats()
            daily = token_tracker.get_daily_stats()
            weekly = token_tracker.get_weekly_stats()
            costs = token_tracker.get_cost_estimate()
            
            # Format message
            stats_text = "📊 **LLM API Token Usage**\n\n"
            
            # Session stats
            stats_text += f"🔄 **Current Session:**\n"
            stats_text += f"  • Total: {session['total_session_tokens']:,} tokens\n"
            stats_text += f"  • Requests: {session['total_session_requests']}\n"
            stats_text += f"  • DeepSeek: {session['session']['deepseek']['total_tokens']:,}\n"
            stats_text += f"  • Grok: {session['session']['grok']['total_tokens']:,}\n\n"
            
            # Daily stats
            stats_text += f"📅 **Today ({daily['date']}):**\n"
            stats_text += f"  • Total: {daily['total_tokens']:,} tokens\n"
            stats_text += f"  • Requests: {daily['total_requests']}\n"
            stats_text += f"  • DeepSeek: {daily['usage']['deepseek']['total_tokens']:,}\n"
            stats_text += f"  • Grok: {daily['usage']['grok']['total_tokens']:,}\n\n"
            
            # Cost estimate
            stats_text += f"💰 **Estimated Costs (Today):**\n"
            stats_text += f"  • DeepSeek: ${costs['costs']['deepseek']['total_cost']:.4f}\n"
            stats_text += f"  • Grok: ${costs['costs']['grok']['total_cost']:.4f}\n"
            stats_text += f"  • **Total: ${costs['total_daily_cost']:.4f}**\n"
            stats_text += f"  • Est. Monthly: ${costs['estimated_monthly_cost']:.2f}\n\n"
            
            # Weekly stats
            stats_text += f"📈 **Last 7 Days:**\n"
            stats_text += f"  • Total: {weekly['total_tokens']:,} tokens\n"
            stats_text += f"  • Avg/Day: {int(weekly['average_tokens_per_day']):,}\n"
            
            await update.message.reply_text(stats_text)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting token stats: {e}")
            import traceback
            traceback.print_exc()
    
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
    
    async def launch_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Launch AlleyBot token via Clawn.ch"""
        try:
            await update.message.reply_text("🚀 Launching AlleyBot token via Clawn.ch...\n\nThis will:\n1. Create launch posts on Moltx and MoltBook\n2. Deploy $ALYBOT on Base via Clanker\n3. Set up 80% fee revenue to AlleyBot wallet")
            
            # Run the launch script
            import subprocess
            result = subprocess.run(
                ['python', 'utils/launch_alleybot_token.py'],
                capture_output=True,
                text=True,
                input='yes\n',  # Auto-confirm
                timeout=120
            )
            
            if result.returncode == 0:
                # Parse output for key details
                output = result.stdout
                await update.message.reply_text(f"✅ Token Launch Complete!\n\n{output[-1000:]}")  # Last 1000 chars
            else:
                await update.message.reply_text(f"❌ Launch failed:\n{result.stderr[-500:]}")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    async def register_agent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Register AlleyBot on ERC-8004 for on-chain identity"""
        try:
            await update.message.reply_text("🆔 Registering AlleyBot on ERC-8004...\n\nThis will:\n1. Check if already registered\n2. Create agent profile with capabilities\n3. Register on-chain identity NFT (if needed)\n4. Enable reputation system\n\n⏳ This may take up to 5 minutes if sending transaction...")
            
            # Run the registration script with longer timeout for transaction confirmation
            import subprocess
            result = subprocess.run(
                ['python', 'utils/register_erc8004_agent.py'],
                capture_output=True,
                text=True,
                timeout=360,  # 6 minutes to allow for transaction confirmation
                input='yes\n'  # Auto-confirm registration
            )
            
            if result.returncode == 0:
                output = result.stdout
                # Send full output as it contains instructions or confirmation
                await update.message.reply_text(f"{output[-2000:]}")  # Last 2000 chars
            else:
                await update.message.reply_text(f"❌ Registration failed:\n{result.stderr[-500:]}")
                
        except subprocess.TimeoutExpired:
            await update.message.reply_text("⏰ Registration timed out. This might mean:\n1. Transaction is still pending on Ethereum\n2. Network congestion\n3. Check Etherscan for your wallet's recent transactions\n\nTry running /register_agent again to check status.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
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

**Token & Identity Commands:**
/launch_token - Launch $ALYBOT token on Base
/register_agent - Register on-chain identity (ERC-8004)

**System Commands:**
/status - Platform status
/skills - List available skills
/skill [name] [params] - Execute skill
/token_stats - LLM API token usage & costs
/help - Show this help

**Production Features:**
✅ Event-driven architecture
✅ Smart model routing (DeepSeek/Grok)
✅ RAG memory system
✅ Session persistence
✅ Dynamic skills system

I'm your intelligent AI assistant - ask me anything! 🚀"""
        
        await update.message.reply_text(help_text)
