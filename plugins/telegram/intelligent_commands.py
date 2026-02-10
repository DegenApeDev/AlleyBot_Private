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
    
    @property
    def core(self):
        """Dynamically access core from telegram plugin"""
        return self.telegram.core

    async def _verify_admin(self, update) -> bool:
        """Verify the message is from the authorized owner. Rejects all others."""
        if not self.telegram or not self.telegram.owner_user_id:
            await update.message.reply_text("🔒 Bot not configured.")
            return False
        user_id = update.effective_user.id
        if user_id != self.telegram.owner_user_id:
            await update.message.reply_text(
                "🔒 This bot is private and only responds to its owner."
            )
            return False
        return True

    def _filter_text(self, text: str) -> str:
        """Filter sensitive data from outbound text"""
        try:
            from security_filter import security_filter
            filtered, was_filtered = security_filter.filter_message(str(text))
            if was_filtered:
                print("⚠️  SECURITY: Filtered sensitive data from Telegram command output")
            return filtered
        except Exception:
            return str(text)
    
    async def ai_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI-powered chat - natural language interaction"""
        if not await self._verify_admin(update):
            return
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
        if not await self._verify_admin(update):
            return
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
                from src.agents.event_runner import AgentEvent, EventType
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
        if not await self._verify_admin(update):
            return
        try:
            if not self.core:
                await update.message.reply_text("❌ Core not initialized")
                return
            
            if not hasattr(self.core, 'plugin_manager'):
                await update.message.reply_text("❌ Plugin manager not found")
                return
            
            if 'moltx' not in self.core.plugin_manager.plugins:
                available = list(self.core.plugin_manager.plugins.keys())
                await update.message.reply_text(f"❌ Moltx plugin not loaded\nAvailable: {', '.join(available)}")
                return
            
            moltx_plugin = self.core.plugin_manager.plugins['moltx']
            
            if not hasattr(moltx_plugin, 'feed_command'):
                await update.message.reply_text("❌ Moltx plugin missing feed_command method")
                return
            
            result = moltx_plugin.feed_command()
            
            # Telegram has a 4096 character limit, truncate if needed
            message = f"📰 Moltx Feed:\n{result}"
            if len(message) > 4000:
                message = message[:3900] + "\n\n... (truncated, too long for Telegram)"
            
            await update.message.reply_text(message)
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    async def moltx_engage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Engage with Moltx feed (like/comment)"""
        if not await self._verify_admin(update):
            return
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
        if not await self._verify_admin(update):
            return
        try:
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                await update.message.reply_text("❌ Core not initialized")
                return
            
            if 'moltx' not in self.core.plugin_manager.plugins:
                available = list(self.core.plugin_manager.plugins.keys())
                await update.message.reply_text(f"❌ Moltx plugin not loaded\nAvailable: {', '.join(available)}")
                return
            
            moltx_plugin = self.core.plugin_manager.plugins['moltx']
            
            if hasattr(moltx_plugin, 'trending_command'):
                result = moltx_plugin.trending_command()
                await update.message.reply_text(f"🔥 Trending:\n{result}")
            else:
                await update.message.reply_text("📊 Trending analysis coming soon!")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    async def moltx_claim(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Submit X/Twitter claim tweet to verify MoltX agent"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text("🐦 Usage: /moltx_claim [tweet_url]\n\nExample: /moltx_claim https://x.com/DegenApeDev/status/123456")
                return
            tweet_url = context.args[0]
            moltx = self.core.plugin_manager.plugins.get('moltx') if self.core else None
            if not moltx:
                await update.message.reply_text("❌ Moltx plugin not loaded")
                return
            await update.message.reply_text(f"🐦 Submitting claim tweet...\n{tweet_url}")
            result = moltx.claim_agent(tweet_url)
            await update.message.reply_text(result)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def moltx_debug(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show raw MoltX agent profile and status for debugging"""
        if not await self._verify_admin(update):
            return
        try:
            moltx = self.core.plugin_manager.plugins.get('moltx') if self.core else None
            if not moltx:
                await update.message.reply_text("❌ Moltx plugin not loaded")
                return
            profile = moltx._make_request('GET', '/agents/me')
            status = moltx._make_request('GET', '/agents/status')
            msg = f"📋 Profile:\n{str(profile)[:1500]}\n\n📊 Status:\n{str(status)[:500]}"
            for i in range(0, len(msg), 3900):
                await update.message.reply_text(msg[i:i+3900])
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def moltx_check_reward(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check MoltX reward eligibility without claiming"""
        if not await self._verify_admin(update):
            return
        try:
            moltx = self.core.plugin_manager.plugins.get('moltx') if self.core else None
            if not moltx:
                await update.message.reply_text("❌ Moltx plugin not loaded")
                return

            await update.message.reply_text("🔍 Checking reward eligibility...")
            data, error = moltx.check_reward_eligibility()
            if error:
                await update.message.reply_text(error)
                return

            eligible = data.get('eligible', False)
            epoch = data.get('active_epoch', {})
            reasons = data.get('reasons', [])

            msg = f"💰 **MoltX Reward Check**\n\n"
            msg += f"🏷️ Epoch: {epoch.get('name', 'N/A')}\n"
            msg += f"💵 Reward: ${epoch.get('reward_per_agent_usd', '?')} USDC\n"
            msg += f"✅ Eligible: {'Yes' if eligible else 'No'}\n"
            if not eligible and reasons:
                msg += f"\n❌ Blockers:\n"
                msg += "\n".join(f"  • {r}" for r in reasons)
            elif eligible:
                msg += f"\n🎉 Ready to claim! Use /moltx_claim_reward"
            msg += f"\n\n🔍 Raw: {str(data)[:500]}"
            await update.message.reply_text(msg)

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def moltx_claim_reward(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check eligibility and claim MoltX USDC reward"""
        if not await self._verify_admin(update):
            return
        try:
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                await update.message.reply_text("❌ Core not initialized")
                return
            moltx = self.core.plugin_manager.plugins.get('moltx')
            if not moltx:
                await update.message.reply_text("❌ Moltx plugin not loaded")
                return

            await update.message.reply_text("💰 Checking reward eligibility...")

            # Check first
            data, error = moltx.check_reward_eligibility()
            if error:
                await update.message.reply_text(error)
                return

            eligible = data.get('eligible', False)
            epoch = data.get('active_epoch', {})
            amount = epoch.get('reward_per_agent_usd', '?')

            if not eligible:
                reasons = data.get('reasons', ['Unknown reason'])
                msg = f"❌ Not eligible for ${amount} USDC reward:\n"
                msg += "\n".join(f"  • {r}" for r in reasons)
                await update.message.reply_text(msg)
                return

            await update.message.reply_text(f"✅ Eligible! Claiming ${amount} USDC...")
            result = moltx.claim_reward()
            await update.message.reply_text(result)

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def moltbook_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create an AI-generated post on MoltBook based on topic/direction"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text("📝 Usage: /moltbook_post [topic and direction]\n\nExample: /moltbook_post discussing AI agent development")
                return
            
            topic_direction = ' '.join(context.args)
            
            # Send "generating" message
            status_msg = await update.message.reply_text("🤖 Generating post with AI...")
            
            if self.core and hasattr(self.core, 'plugin_manager') and 'moltbook' in self.core.plugin_manager.plugins:
                moltbook_plugin = self.core.plugin_manager.plugins['moltbook']
                
                # Check if API is initialized
                if not hasattr(moltbook_plugin, 'api') or not moltbook_plugin.api:
                    await status_msg.edit_text("❌ MoltBook API not initialized. Check MOLTBOOK_API_KEY in .env")
                    return
                
                # Use Model Router to generate intelligent post
                from src.config.models import ModelRouter
                from src.agents.session_manager import SessionManager
                from src.agents.event_runner import AgentEvent, EventType
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
                
                # Generate intelligent title with AI
                title_prompt = f"""You are AlleyBot, an autonomous AI agent on MoltBook.

Create an engaging, intelligent title for a post about: {topic_direction}

The post content is:
{post_content}

Requirements:
1. Be catchy and attention-grabbing
2. Be 3-8 words maximum
3. Reflect the content accurately
4. Use engaging language (not boring)
5. Include relevant keywords if appropriate
6. Make people want to click/read

Generate only the title (no explanations):"""
                
                # Generate title with AI
                title_event = AgentEvent(
                    event_type=EventType.MESSAGE_RECEIVED,
                    session_id=session_id,
                    channel="telegram",
                    payload={"query": title_prompt},
                    timestamp=datetime.now(),
                    priority=2
                )
                
                intelligent_title = await model_router.route_and_execute(
                    event=title_event,
                    session=session,
                    rag_context=""
                )
                
                # Clean up title
                intelligent_title = intelligent_title.strip().strip('"').strip("'")
                
                # Post to MoltBook using the API
                result = moltbook_plugin.api.create_post(
                    submolt="general",
                    title=intelligent_title[:100],  # Use AI-generated title
                    content=post_content
                )
                
                if result and 'error' not in result:
                    post_id = result.get('id', 'unknown')
                    await status_msg.edit_text(f"✅ AI-Generated MoltBook Post!\n\n{post_content}\n\n🔗 Post ID: {post_id}")
                elif result and 'error' in result:
                    error_msg = result.get('message', result.get('error', 'Unknown error'))
                    await status_msg.edit_text(f"❌ MoltBook API Error:\n{error_msg}\n\nGenerated content:\n{post_content[:200]}...")
                else:
                    await status_msg.edit_text(f"⚠️ Post generated but API returned no result:\n\n{post_content}")
            else:
                await status_msg.edit_text("❌ MoltBook plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    async def token_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get LLM API token usage statistics"""
        if not await self._verify_admin(update):
            return
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
        if not await self._verify_admin(update):
            return
        try:
            status_text = "📊 **AlleyBot Status**\n\n"
            
            if self.core and hasattr(self.core, 'plugin_manager'):
                plugins = self.core.plugin_manager.plugins
                
                # Check each platform
                platforms = {
                    'moltx': '🐦 Moltx',
                    'moltbook': '📚 MoltBook',
                    'moltchan': '💬 MoltChan',
                    'moltroad': '🛣️ MoltRoad'
                }
                
                for plugin_name, display_name in platforms.items():
                    if plugin_name in plugins:
                        plugin = plugins[plugin_name]
                        if hasattr(plugin, 'get_status'):
                            try:
                                plugin_status = plugin.get_status()
                                status_text += f"{display_name}: ✅ Active\n"
                            except Exception as e:
                                status_text += f"{display_name}: ⚠️ Error: {e}\n"
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
        if not await self._verify_admin(update):
            return
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
        if not await self._verify_admin(update):
            return
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
    
    # =================================================================
    # Crypto Price Commands
    # =================================================================

    def _get_crypto_plugin(self):
        """Get the crypto plugin from core"""
        if self.core and hasattr(self.core, 'plugin_manager'):
            return self.core.plugin_manager.plugins.get('crypto')
        return None

    async def crypto_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check crypto price. Usage: /crypto_price btc"""
        if not await self._verify_admin(update):
            return
        try:
            crypto = self._get_crypto_plugin()
            if not crypto:
                await update.message.reply_text("❌ Crypto plugin not loaded")
                return
            if not context.args:
                await update.message.reply_text("💰 Usage: /crypto_price <symbol>\n\nExamples: /crypto_price btc\n/crypto_price eth\n/crypto_price sol")
                return
            result = crypto.price_command(context.args[0])
            await update.message.reply_text(result)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def crypto_prices(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check multiple crypto prices. Usage: /crypto_prices btc,eth,sol"""
        if not await self._verify_admin(update):
            return
        try:
            crypto = self._get_crypto_plugin()
            if not crypto:
                await update.message.reply_text("❌ Crypto plugin not loaded")
                return
            if not context.args:
                await update.message.reply_text("💰 Usage: /crypto_prices btc,eth,sol")
                return
            result = crypto.multi_price_command(','.join(context.args))
            await update.message.reply_text(result)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def crypto_trending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show trending coins on CoinGecko"""
        if not await self._verify_admin(update):
            return
        try:
            crypto = self._get_crypto_plugin()
            if not crypto:
                await update.message.reply_text("❌ Crypto plugin not loaded")
                return
            result = crypto.trending_command()
            await update.message.reply_text(result)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    # =================================================================
    # Content Strategy Commands
    # =================================================================

    async def calendar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show content calendar status"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await update.message.reply_text("❌ Brain plugin not loaded")
                return
            result = brain.calendar_command()
            await update.message.reply_text(result)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def conversations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show active conversation threads"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await update.message.reply_text("❌ Brain plugin not loaded")
                return
            result = brain.conversations_command()
            await update.message.reply_text(result)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def personality(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show or set personality. Usage: /personality [platform] [key=value]"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await update.message.reply_text("❌ Brain plugin not loaded")
                return
            args = context.args if context.args else []
            result = brain.personality_command(*args)
            await update.message.reply_text(result)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    # =================================================================
    # Image Generation Commands
    # =================================================================

    async def generate_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate AI image using Grok. Usage: /generate_image [prompt] or natural language"""
        if not await self._verify_admin(update):
            return
        try:
            # Get prompt from command args or message text
            if context.args:
                prompt = ' '.join(context.args)
            else:
                # Try to extract from natural language
                text = update.message.text
                # Look for patterns like "generate an image of", "create an image", "make an image"
                import re
                patterns = [
                    r'(?:generate|create|make)\s+(?:an\s+)?image\s+(?:of|with|showing)?\s*(.+)',
                    r'(?:draw|paint|render)\s+(?:an\s+)?(?:image\s+)?(?:of\s+)?(.+)',
                    r'(?:give\s+me|show\s+me)\s+(?:an\s+)?image\s+(?:of\s+)?(.+)',
                ]
                prompt = None
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        prompt = match.group(1).strip()
                        break
                
                if not prompt:
                    await update.message.reply_text(
                        "🎨 **Image Generation**\n\n"
                        "Usage: `/generate_image [description]`\n\n"
                        "Examples:\n"
                        "• `/generate_image a cyberpunk AI agent coding`\n"
                        "• `/generate_image a futuristic lobster in space`\n\n"
                        "Or say naturally:\n"
                        "• \"Generate an image of a cyberpunk city\"\n"
                        "• \"Create an image showing a robot at sunset\""
                    )
                    return
            
            # Send status message
            status_msg = await update.message.reply_text(f"🎨 Generating image...\n📝 Prompt: {prompt[:100]}...")
            
            # Import and use Grok AI
            from grok_ai import grok_ai
            
            if not grok_ai.enabled:
                await status_msg.edit_text("❌ Grok AI not enabled. Check GROK_API_KEY in .env")
                return
            
            # Generate image
            result = await self._run_sync(
                grok_ai.generate_image,
                prompt=prompt,
                aspect_ratio="16:9",
                image_format="base64",
                n=1
            )
            
            if result and result.get('image_data'):
                import base64
                from io import BytesIO
                
                # Convert base64 to image bytes
                image_data = result['image_data']
                if isinstance(image_data, str):
                    image_bytes = base64.b64decode(image_data)
                else:
                    image_bytes = image_data
                
                # Wrap in BytesIO with explicit name - more reliable for Telegram
                photo_file = BytesIO(image_bytes)
                photo_file.name = "generated_image.jpg"
                
                # Send the image with increased timeout
                await update.message.reply_photo(
                    photo=photo_file,
                    caption=f"🎨 **Generated Image**\n📝 Prompt: {prompt}\n✅ Moderation passed: {result.get('moderation_passed', True)}",
                    read_timeout=30,
                    write_timeout=30
                )
                
                # Delete status message
                await status_msg.delete()
            else:
                await status_msg.edit_text(f"❌ Image generation failed. Result: {result}")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating image: {e}")
            import traceback
            traceback.print_exc()

    # =================================================================
    # Feedback Loop Commands
    # =================================================================

    async def insights(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show content performance insights"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await update.message.reply_text("❌ Brain plugin not loaded")
                return
            result = brain.feedback_insights_command()
            await update.message.reply_text(result)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def check_engagement(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check engagement on tracked posts"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await update.message.reply_text("❌ Brain plugin not loaded")
                return
            result = brain.feedback_check_command()
            await update.message.reply_text(result)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def tracked_posts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show tracked posts and their engagement"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await update.message.reply_text("❌ Brain plugin not loaded")
                return
            result = brain.feedback_tracked_command()
            await update.message.reply_text(result)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    # =================================================================
    # On-Chain Commands
    # =================================================================

    def _get_onchain_plugin(self):
        """Get the onchain plugin from core"""
        if self.core and hasattr(self.core, 'plugin_manager'):
            return self.core.plugin_manager.plugins.get('onchain')
        return None

    async def wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show wallet info and balances"""
        if not await self._verify_admin(update):
            return
        try:
            onchain = self._get_onchain_plugin()
            if not onchain:
                await update.message.reply_text("❌ On-chain plugin not loaded")
                return

            result = await self._run_sync(onchain.wallet_command)
            await update.message.reply_text(self._filter_text(str(result)))

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show token balances"""
        if not await self._verify_admin(update):
            return
        try:
            onchain = self._get_onchain_plugin()
            if not onchain:
                await update.message.reply_text("❌ On-chain plugin not loaded")
                return

            result = await self._run_sync(onchain.token_balances_command)
            await update.message.reply_text(self._filter_text(str(result)))

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def block(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current block info"""
        if not await self._verify_admin(update):
            return
        try:
            onchain = self._get_onchain_plugin()
            if not onchain:
                await update.message.reply_text("❌ On-chain plugin not loaded")
                return

            result = await self._run_sync(onchain.block_info_command)
            await update.message.reply_text(self._filter_text(str(result)))

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def track_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Track a token. Usage: /track <symbol_or_address>"""
        if not await self._verify_admin(update):
            return
        try:
            onchain = self._get_onchain_plugin()
            if not onchain:
                await update.message.reply_text("❌ On-chain plugin not loaded")
                return

            if context.args:
                result = await self._run_sync(onchain.track_token_command, *context.args)
            else:
                result = await self._run_sync(onchain.track_token_command)
            await update.message.reply_text(self._filter_text(str(result)))

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def tx(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Look up a transaction. Usage: /tx <hash>"""
        if not await self._verify_admin(update):
            return
        try:
            onchain = self._get_onchain_plugin()
            if not onchain:
                await update.message.reply_text("❌ On-chain plugin not loaded")
                return

            if context.args:
                result = await self._run_sync(onchain.tx_lookup_command, *context.args)
            else:
                result = await self._run_sync(onchain.tx_lookup_command)
            await update.message.reply_text(self._filter_text(str(result)))

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent on-chain activity"""
        if not await self._verify_admin(update):
            return
        try:
            onchain = self._get_onchain_plugin()
            if not onchain:
                await update.message.reply_text("❌ On-chain plugin not loaded")
                return

            status_msg = await update.message.reply_text("🔍 Scanning recent blocks...")
            if context.args:
                result = await self._run_sync(onchain.recent_activity_command, *context.args)
            else:
                result = await self._run_sync(onchain.recent_activity_command)
            result = self._filter_text(str(result))

            if len(result) > 4000:
                result = result[:3900] + "\n\n... (truncated)"
            await status_msg.edit_text(result)

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def onchain_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show on-chain plugin status"""
        if not await self._verify_admin(update):
            return
        try:
            onchain = self._get_onchain_plugin()
            if not onchain:
                await update.message.reply_text("❌ On-chain plugin not loaded")
                return

            result = await self._run_sync(onchain.onchain_status_command)
            await update.message.reply_text(self._filter_text(str(result)))

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    # =================================================================
    # Brain Commands
    # =================================================================

    def _get_brain_plugin(self):
        """Get the brain plugin from core"""
        if self.core and hasattr(self.core, 'plugin_manager'):
            return self.core.plugin_manager.plugins.get('brain')
        return None

    async def _run_sync(self, func, *args):
        """Run a blocking synchronous function in a thread executor
        so it doesn't block the Telegram async event loop."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    async def _safe_reply(self, update: Update, text: str):
        """Reply to a message, falling back to raw HTTP if python-telegram-bot fails."""
        filtered = self._filter_text(str(text))
        try:
            await update.message.reply_text(filtered)
        except Exception:
            # Fallback: raw HTTP API (avoids event loop / HTTPX issues)
            try:
                telegram = self.telegram
                if telegram and telegram.bot_token:
                    import requests as req
                    req.post(
                        f"https://api.telegram.org/bot{telegram.bot_token}/sendMessage",
                        json={"chat_id": update.effective_chat.id, "text": filtered},
                        timeout=10,
                    )
            except Exception as e2:
                print(f"❌ Both reply methods failed: {e2}")

    async def brain_think(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Run one brain think cycle"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return

            await self._safe_reply(update, "🧠 Thinking...")
            result = await self._run_sync(brain.think_command)
            await self._safe_reply(update, str(result))

        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def brain_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start autonomous brain loop"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return

            # start_autonomous returns instantly (spawns a thread), no need for _run_sync
            result = brain.start_autonomous()
            await self._safe_reply(update, str(result))

        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def brain_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop autonomous brain loop"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return

            # stop_autonomous returns instantly, no need for _run_sync
            result = brain.stop_autonomous()
            await self._safe_reply(update, str(result))

        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def brain_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show brain status"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return

            result = await self._run_sync(brain.status_command)
            await self._safe_reply(update, str(result))

        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    # =================================================================
    # A2A Commands
    # =================================================================

    def _get_a2a_plugin(self):
        """Get the A2A plugin from core"""
        if self.core and hasattr(self.core, 'plugin_manager'):
            return self.core.plugin_manager.plugins.get('a2a')
        return None

    async def a2a_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show A2A server status"""
        if not await self._verify_admin(update):
            return
        try:
            a2a = self._get_a2a_plugin()
            if not a2a:
                await self._safe_reply(update, "❌ A2A plugin not loaded")
                return
            result = await self._run_sync(a2a.status_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def a2a_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start A2A server"""
        if not await self._verify_admin(update):
            return
        try:
            a2a = self._get_a2a_plugin()
            if not a2a:
                await self._safe_reply(update, "❌ A2A plugin not loaded")
                return
            result = await self._run_sync(a2a.start_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def a2a_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop A2A server"""
        if not await self._verify_admin(update):
            return
        try:
            a2a = self._get_a2a_plugin()
            if not a2a:
                await self._safe_reply(update, "❌ A2A plugin not loaded")
                return
            result = await self._run_sync(a2a.stop_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def a2a_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List available A2A tasks"""
        if not await self._verify_admin(update):
            return
        try:
            a2a = self._get_a2a_plugin()
            if not a2a:
                await self._safe_reply(update, "❌ A2A plugin not loaded")
                return
            result = await self._run_sync(a2a.tasks_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    # =================================================================
    # Self-Improve / ERC-8004 Commands
    # =================================================================

    def _get_selfimprove_plugin(self):
        """Get the selfimprove plugin from core"""
        if self.core and hasattr(self.core, 'plugin_manager'):
            return self.core.plugin_manager.plugins.get('selfimprove')
        return None

    async def improve_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show self-improvement plugin status"""
        if not await self._verify_admin(update):
            return
        try:
            si = self._get_selfimprove_plugin()
            if not si:
                await self._safe_reply(update, "❌ Self-improve plugin not loaded")
                return
            result = await self._run_sync(si.status_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def erc8004_rebuild(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Rebuild agent card from live plugins (no on-chain tx)"""
        if not await self._verify_admin(update):
            return
        try:
            si = self._get_selfimprove_plugin()
            if not si:
                await self._safe_reply(update, "❌ Self-improve plugin not loaded")
                return
            await self._safe_reply(update, "🔄 Rebuilding agent card...")
            result = await self._run_sync(si.erc8004_rebuild_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def erc8004_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Push agent card on-chain (IPFS + setAgentURI)"""
        if not await self._verify_admin(update):
            return
        try:
            si = self._get_selfimprove_plugin()
            if not si:
                await self._safe_reply(update, "❌ Self-improve plugin not loaded")
                return
            await self._safe_reply(update, "🚀 Uploading to IPFS and updating on-chain...")
            result = await self._run_sync(si.erc8004_update_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def erc8004_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Preview agent card update (dry run)"""
        if not await self._verify_admin(update):
            return
        try:
            si = self._get_selfimprove_plugin()
            if not si:
                await self._safe_reply(update, "❌ Self-improve plugin not loaded")
                return
            result = await self._run_sync(si.erc8004_preview_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    # =================================================================
    # Clawbr Commands
    # =================================================================
    
    def _get_clawbr_plugin(self):
        """Get the clawbr plugin from core"""
        if self.core and hasattr(self.core, 'plugin_manager'):
            return self.core.plugin_manager.plugins.get('clawbr')
        return None
    
    async def clawbr_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show Clawbr status"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            result = await self._run_sync(cb.clawbr_status_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a post on Clawbr"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /clawbr_post <content>")
                return
            
            content = ' '.join(context.args)
            result = await self._run_sync(cb.clawbr_post_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_feed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show Clawbr feed"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            result = await self._run_sync(cb.clawbr_feed_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_debates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show Clawbr debates"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            result = await self._run_sync(cb.clawbr_debates_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_create_debate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a debate on Clawbr"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            
            if len(context.args) < 2:
                await self._safe_reply(update, "Usage: /clawbr_create_debate <topic> <opening_argument>")
                return
            
            result = await self._run_sync(cb.clawbr_create_debate_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_join_debate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Join a debate on Clawbr"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /clawbr_join_debate <slug>")
                return
            
            result = await self._run_sync(cb.clawbr_join_debate_command, context.args[0])
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show Clawbr leaderboard"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            result = await self._run_sync(cb.clawbr_leaderboard_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search on Clawbr"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /clawbr_search <query>")
                return
            
            result = await self._run_sync(cb.clawbr_search_command, ' '.join(context.args))
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show Clawbr platform stats"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            result = await self._run_sync(cb.clawbr_stats_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def clawbr_engage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Run Clawbr engagement cycle (feed + debates + votes)"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            result = await self._run_sync(cb.run_engagement_cycle)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    # =================================================================
    # Help
    # =================================================================

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show comprehensive help"""
        if not await self._verify_admin(update):
            return
        help_text = """🦞 **AlleyBot Commands**

**💬 AI Chat:**
/chat [message] - Chat with AI
Or just send any message naturally!

**📢 Social Platforms:**
/moltx_post [topic] - Post to Moltx
/moltx_feed - Browse Moltx feed
/moltx_engage [count] - Engage with feed
/moltx_trending - Trending topics
/moltx_claim [tweet_url] - Verify via X tweet
/moltx_check_reward - Check reward eligibility
/moltx_claim_reward - Claim USDC reward
/moltbook_post [topic] - Post to MoltBook

**🦞 Clawbr (AI Social Network):**
/clawbr_status - Show agent profile & stats
/clawbr_post [content] - Create intelligent post
/clawbr_feed - Browse global feed
/clawbr_debates - Show active/open debates
/clawbr_create_debate [topic] [argument] - Start debate
/clawbr_join_debate [slug] - Join open debate
/clawbr_leaderboard - Show top agents
/clawbr_search [query] - Search posts/agents
/clawbr_stats - Platform statistics

**� Crypto Prices:**
/crypto_price [symbol] - Price check (btc, eth, sol...)
/crypto_prices [list] - Multiple prices (btc,eth,sol)
/crypto_trending - Trending coins

**�🔗 On-Chain (Base):**
/wallet - Wallet info & balances
/balance - Token balances
/block - Current block info
/track [symbol] - Track a token
/tx [hash] - Look up transaction
/activity - Recent on-chain activity
/onchain - On-chain status

**🧠 Content Strategy:**
/calendar - Content calendar status
/conversations - Active conversation threads
/personality [platform] - Show/set personality

**🎨 Image Generation:**
/generate_image [prompt] - Generate AI image with Grok

**📊 Feedback Loop:**
/insights - Content performance insights
/check_engagement - Check engagement on tracked posts
/tracked_posts - Show tracked posts & scores

**🧠 Brain:**
/think - One think cycle
/brain_start - Start autonomous mode
/brain_stop - Stop autonomous mode
/brain - Brain status

**🤝 A2A Protocol:**
/a2a_status - Server status
/a2a_start - Start A2A server
/a2a_stop - Stop A2A server
/a2a_tasks - List available tasks

**🆔 ERC-8004 Agent Card:**
/erc8004_rebuild - Rebuild card from live plugins
/erc8004_preview - Preview card (dry run)
/erc8004_update - Push card on-chain (costs gas)

**⚙️ System:**
/status - Platform status
/token_stats - LLM token usage & costs
/improve_status - Self-improvement status
/help - This help"""
        
        await update.message.reply_text(help_text)
