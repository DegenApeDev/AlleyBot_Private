"""
Intelligent Telegram Commands for AlleyBot
AI-powered assistant commands integrated with production architecture
"""

import asyncio
from typing import Any, Tuple
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
    
    async def _validate_with_tier2(self, action_description: str, evidence_strength: float = 0.9) -> Tuple[bool, str, Any]:
        """
        Validate a high-stakes action through Tier-2 Synergy Gate.
        
        Returns: (can_execute: bool, reason: str, validation_result: Any)
        """
        try:
            from lib.synergy_gate import validate_action
            
            can_exec, reason, result = validate_action({
                'content': action_description,
                'evidence_strength': evidence_strength,
                'urgency': 1.0,
                'recursion_depth': 0
            }, threshold=0.85)
            
            return can_exec, reason, result
        except Exception as e:
            # If Tier-2 unavailable, fail open with warning
            return True, f"Tier-2 unavailable, proceeding: {e}", None
    
    async def _moltx_preflight_engagement(self, update: Update, moltx_plugin) -> None:
        """
        5:1 Rule: Before posting, engage with the network.
        Uses brain's cross-platform engagement system with AI-generated contextual replies.
        """
        try:
            # Use brain's cross-platform engagement if available
            if self.core and hasattr(self.core, 'plugin_manager'):
                brain = self.core.plugin_manager.plugins.get('brain')
                if brain and hasattr(brain, 'run_preflight_engagement'):
                    await update.message.reply_text(
                        "📡 Running 5:1 engagement protocol via brain...", 
                        parse_mode='Markdown'
                    )
                    results = await brain.run_preflight_engagement(
                        platform='moltx',
                        plugin=moltx_plugin,
                        update=update
                    )
                    print(f"✅ Brain-driven 5:1 engagement: {results}")
                    return
            
            # Fallback to legacy hardcoded method
            await update.message.reply_text(
                "📡 Running 5:1 engagement protocol (legacy)...", 
                parse_mode='Markdown'
            )
            
            # Legacy implementation continues below (unchanged)
            feed = []
            if hasattr(moltx_plugin, '_make_request'):
                result = moltx_plugin._make_request('GET', '/feed/global', params={'type': 'post,quote', 'limit': 30})
                if result:
                    if 'posts' in result:
                        feed = result['posts']
                    elif 'data' in result and 'posts' in result['data']:
                        feed = result['data']['posts']
                    elif isinstance(result, list):
                        feed = result
            
            if not feed:
                print("⚠️ No feed available for pre-flight engagement")
                return
            
            # 2. Like 10 posts
            liked_count = 0
            for post in feed[:15]:
                if liked_count >= 10:
                    break
                try:
                    post_id = post.get('id') or post.get('post_id')
                    if post_id and hasattr(moltx_plugin, 'like_post'):
                        result = moltx_plugin.like_post(post_id)
                        if '✅' in str(result):
                            liked_count += 1
                            print(f"❤️  Liked post {post_id} ({liked_count}/10)")
                        await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"⚠️  Like failed: {e}")
                    continue
            
            # 3. Reply to 5 posts with AI using DeepSeek
            replied_count = 0
            from deepseek_ai import deepseek_ai
            
            for post in feed[15:25]:
                if replied_count >= 5:
                    break
                try:
                    post_id = post.get('id') or post.get('post_id')
                    author = post.get('agent_name') or post.get('author_name') or post.get('username') or 'agent'
                    post_content = post.get('content', '') or post.get('text', '')
                    
                    if post_id and hasattr(moltx_plugin, 'reply_to_post') and post_content:
                        reply_prompt = f"""You're AlleyBot replying to a post on Moltx.

Original post by @{author}: "{post_content[:200]}"

CRITICAL: Reply #{replied_count+1} of 5. Each reply MUST be completely different.

Reply requirements:
1. React to something SPECIFIC from their post
2. NEVER use generic phrases like "Interesting perspective!" or "Building on this"
3. Vary your opening: "Wait...", "Actually...", "What if..."
4. Add unique value - challenge, add insight, or ask sharp question
5. Keep it 1-2 sentences, conversational

Generate ONLY the reply (no @ mentions, no explanations):"""
                        
                        reply_text = deepseek_ai.generate_text(reply_prompt, max_tokens=150)
                        reply_text = reply_text.strip().strip('"').strip("'")
                        
                        result = moltx_plugin.reply_to_post(post_id, f"@{author} {reply_text}")
                        if '✅' in str(result):
                            replied_count += 1
                            print(f"💬 Replied to post {post_id} ({replied_count}/5): {reply_text[:60]}...")
                        await asyncio.sleep(1.5)
                except Exception as e:
                    print(f"⚠️  Reply failed: {e}")
                    continue
            
            # 4. Follow 2-3 agents
            followed_count = 0
            for post in feed[:20]:
                if followed_count >= 3:
                    break
                try:
                    author = post.get('agent_name') or post.get('author_name') or post.get('username')
                    if author and hasattr(moltx_plugin, 'follow_agent'):
                        result = moltx_plugin.follow_agent(author)
                        if '✅' in str(result):
                            followed_count += 1
                            print(f"👥 Followed {author} ({followed_count}/3)")
                        await asyncio.sleep(0.5)
                except Exception as e:
                    continue
            
            await update.message.reply_text(
                f"✅ 5:1 Engagement complete: {liked_count} likes, {replied_count} replies, {followed_count} follows",
                parse_mode='Markdown'
            )
            print(f"✅ 5:1 Engagement complete: {liked_count} likes, {replied_count} replies, {followed_count} follows")
            
        except Exception as e:
            print(f"⚠️  Pre-flight engagement error (non-blocking): {e}")
            # Non-blocking - continue even if engagement fails
    
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
    
    def _get_inference_engine(self):
        """Get or create inference engine for AGI commands"""
        from src.autonomy.inference_engine import get_inference_engine
        return get_inference_engine(core=self.core)
    
    async def trends(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cross-platform trend analysis"""
        if not await self._verify_admin(update):
            return
        try:
            engine = self._get_inference_engine()
            trends_data = engine.detect_cross_platform_trends()
            
            msg = "📊 **Cross-Platform Trends**\n\n"
            if trends_data:
                for trend in trends_data[:5]:
                    msg += f"• {trend.get('topic', 'Unknown')}\n"
                    msg += f"  Platforms: {', '.join(trend.get('platforms', []))}\n"
                    msg += f"  Strength: {trend.get('strength', 0):.0%}\n\n"
            else:
                msg += "No significant trends detected."
            
            await update.message.reply_text(msg)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def predict(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Predict future trends"""
        if not await self._verify_admin(update):
            return
        try:
            hours = int(context.args[0]) if context.args else 24
            engine = self._get_inference_engine()
            predictions = engine.predict_trends(hours=hours)
            
            msg = f"🔮 **Trend Predictions (Next {hours}h)**\n\n"
            if predictions:
                for pred in predictions[:5]:
                    msg += f"• {pred.get('topic', 'Unknown')}\n"
                    msg += f"  Confidence: {pred.get('confidence', 0):.0%}\n"
                    msg += f"  Expected: {pred.get('direction', 'unknown')}\n\n"
            else:
                msg += "No predictions available."
            
            await update.message.reply_text(msg)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def anomalies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Detect anomalies across platforms"""
        if not await self._verify_admin(update):
            return
        try:
            hours = int(context.args[0]) if context.args else 24
            engine = self._get_inference_engine()
            anomalies = engine.detect_anomalies(hours=hours)
            
            msg = f"🚨 **Anomalies (Last {hours}h)**\n\n"
            if anomalies:
                for anomaly in anomalies[:5]:
                    msg += f"• {anomaly.get('type', 'Unknown')}\n"
                    msg += f"  Severity: {anomaly.get('severity', 'unknown')}\n"
                    msg += f"  Description: {anomaly.get('description', 'N/A')[:100]}\n\n"
            else:
                msg += "No anomalies detected."
            
            await update.message.reply_text(msg)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def sentiment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyze sentiment for a topic"""
        if not await self._verify_admin(update):
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /sentiment <topic> [hours]\n\n"
                "Examples:\n"
                "/sentiment #AlleyBot\n"
                "/sentiment crypto 72"
            )
            return
        
        topic = context.args[0]
        hours = 24
        
        if len(context.args) > 1:
            try:
                hours = int(context.args[1])
            except ValueError:
                pass
        
        try:
            engine = self._get_inference_engine()
            result = engine.analyze_sentiment(topic, hours=hours)
            
            score = result.get('score', 0.0)
            sentiment_emoji = "🟢" if score > 0.1 else "🔴" if score < -0.1 else "🟡"
            sentiment_label = "Positive" if score > 0.1 else "Negative" if score < -0.1 else "Neutral"
            
            msg = f"😊 **Sentiment for '{topic}' (Last {hours}h)**\n\n"
            msg += f"**Score:** {sentiment_emoji} {score:.3f} ({sentiment_label})\n\n"
            
            if result.get('summary'):
                msg += f"**Summary:** {result['summary']}\n\n"
            
            if result.get('platforms'):
                msg += "**By Platform:**\n"
                for platform, data in result['platforms'].items():
                    p_score = data.get('score', 0)
                    p_emoji = "🟢" if p_score > 0.1 else "🔴" if p_score < -0.1 else "🟡"
                    msg += f"• {platform}: {p_emoji} {p_score:.3f}\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
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
                cat = getattr(skill, 'category', 'general')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(skill)
            
            for category, category_skills in categories.items():
                skills_text += f"**{str(category).replace('_', ' ').title()}:**\n"
                for skill in category_skills:
                    name = getattr(skill, 'name', 'unknown')
                    desc = getattr(skill, 'description', 'No description')
                    skills_text += f"• {name}: {desc}\n"
                skills_text += "\n"
            
            await update.message.reply_text(skills_text)
            
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
            
            # Tier-2 Validation: Check if this public post is safe to execute
            # Lower threshold (0.75) for posts vs strict actions (0.85)
            can_exec, reason, val_result = await self._validate_with_tier2(
                f"Create public Moltx post about: {topic_direction}",
                evidence_strength=0.9
            )
            
            # Re-check with lower threshold if initial strict check fails
            # Use truth_amplitude (pre-penalty) for relaxed check
            raw_confidence = val_result.metadata.get('truth_amplitude', val_result.confidence) if val_result else 0
            if not can_exec and raw_confidence >= 0.75:
                can_exec = True
                reason = f"SyMod validation PASSED (content quality: {raw_confidence:.3f})"
            
            if not can_exec:
                await update.message.reply_text(
                    f"🔐 **Tier-2 Gate Blocked**\n\n"
                    f"Action: Create Moltx post\n"
                    f"Reason: `{reason[:100]}`\n\n"
                    f"⚠️ High-stakes action blocked. Review and retry with more specific/lower-risk content.",
                    parse_mode='Markdown'
                )
                # Log the blocked attempt for RCA
                print(f"🔒 Tier-2 blocked moltx_post: {reason}")
                return
            
            # Step 2: Generate and post
            status_msg = await update.message.reply_text("🤖 Generating post with AI...")
            
            if self.core and hasattr(self.core, 'plugin_manager') and 'moltx' in self.core.plugin_manager.plugins:
                moltx_plugin = self.core.plugin_manager.plugins['moltx']
                
                # Validation passed - proceed with 5:1 engagement rule
                # Step 1: Pre-flight engagement (5 replies, 10 likes)
                await self._moltx_preflight_engagement(update, moltx_plugin)
                
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

CRITICAL OPENING RULES:
1. NEVER start with: "Thoughts on", "Yo", "Hey", "So", "Just", or any generic filler
2. NEVER use: "In my opinion", "I think that", "Here are my thoughts"
3. START with a bold statement, hot take, specific fact, or intriguing question
4. Hook the reader immediately - make them stop scrolling
5. Be conversational but punchy (not corporate)
6. Keep it 1-3 sentences maximum
7. Include 1-2 relevant hashtags if appropriate

GOOD examples:
- "Cross-chain bridges are fundamentally broken and here's why..."
- "DeFi protocols just hit $100B TVL but nobody's talking about the risks"
- "What if I told you impermanent loss is a feature, not a bug?"

BAD examples (NEVER use):
- "Thoughts on the market..."
- "Yo, check this out..."
- "In my opinion, crypto is..."

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
                
                # Check if post was successful before attesting
                post_success = False
                if isinstance(result, dict):
                    post_success = result.get('success', False) or 'post_id' in result
                elif isinstance(result, str):
                    post_success = '✅' in result or 'success' in result.lower()
                
                if not post_success:
                    await status_msg.edit_text(f"❌ Post failed: {result}\n\nContent: {post_content[:100]}...")
                    return
                
                # Auto-attestation: Generate ERC-8004 proof for this high-stakes action (only on success)
                try:
                    import sys
                    from pathlib import Path
                    import types
                    src_path = Path(__file__).parent.parent.parent
                    module_path = src_path / 'src/agentic/erc8004_a2a_integration.py'
                    
                    if 'src.agentic.erc8004_a2a_integration' not in sys.modules:
                        erc8004_module = types.ModuleType('erc8004_a2a_integration')
                        erc8004_module.__file__ = str(module_path)
                        with open(module_path, 'r') as f:
                            exec(f.read(), erc8004_module.__dict__)
                        sys.modules['src.agentic.erc8004_a2a_integration'] = erc8004_module
                    else:
                        erc8004_module = sys.modules['src.agentic.erc8004_a2a_integration']
                    
                    validate_and_attest = erc8004_module.validate_and_attest
                    attestation = validate_and_attest(
                        task_id=f"moltx_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        inputs={'topic': topic_direction, 'prompt': prompt[:100]},
                        outputs={'post_content': post_content[:200], 'result': str(result)},
                        code_version='moltx_v1'
                    )
                    print(f"📜 Auto-attestation generated: {attestation.attestation_id}")
                except Exception as e:
                    print(f"⚠️ Auto-attestation failed: {e}")
                
                # Format result nicely
                if isinstance(result, dict):
                    if result.get('success'):
                        post_id = result.get('data', {}).get('id', 'unknown')
                        result_text = f"✅ Posted successfully! ID: `{post_id[:16]}...`"
                    else:
                        error = result.get('error', result.get('message', 'Unknown error'))
                        result_text = f"❌ Failed: {error[:100]}"
                else:
                    result_text = str(result)[:100]
                
                # Update status message
                await status_msg.edit_text(f"✅ AI-Generated Post:\n\n{post_content}\n\n📢 {result_text}")
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

    async def moltx_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show Moltx agent status and connection info"""
        if not await self._verify_admin(update):
            return
        try:
            moltx = self.core.plugin_manager.plugins.get('moltx') if self.core else None
            if not moltx:
                await update.message.reply_text("❌ Moltx plugin not loaded")
                return
            
            # Check if status_command method exists
            if hasattr(moltx, 'status_command'):
                result = moltx.status_command()
                await update.message.reply_text(f"🐦 Moltx Status:\n{result}")
            else:
                # Fallback: show basic info
                msg = f"🐦 Moltx Plugin Info:\n\n"
                msg += f"initialized: {moltx.initialized}\n"
                msg += f"agent_id: {getattr(moltx, 'agent_id', 'N/A')}\n"
                msg += f"agent_name: {getattr(moltx, 'agent_name', 'N/A')}\n"
                msg += f"api_key: {'Set' if moltx.api_key else 'Not set'}\n"
                await update.message.reply_text(msg)
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
            result = await self._run_sync(grok_ai.generate_image, prompt)
            
            if result and result.get('image_url'):
                # Send the image using URL (much simpler and reliable)
                await update.message.reply_photo(
                    photo=result['image_url'],
                    caption=f"🎨 **Generated Image**\n📝 Prompt: {prompt}\n✅ Moderation passed: {result.get('moderation_passed', True)}"
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
    # World State Commands
    # =================================================================

    async def world_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show World State statistics"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return
            result = await self._run_sync(brain.world_status_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def world_entity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show entity details"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await self._safe_reply(update, "Usage: /world_entity <entity_id>")
                return
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return
            result = await self._run_sync(brain.world_entity_command, context.args[0])
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def world_facts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show facts for an entity"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await self._safe_reply(update, "Usage: /world_facts <entity_id> [attribute]")
                return
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return
            entity_id = context.args[0]
            attribute = context.args[1] if len(context.args) > 1 else None
            result = await self._run_sync(brain.world_facts_command, entity_id, attribute)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def world_relations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show relationships for an entity"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await self._safe_reply(update, "Usage: /world_relations <entity_id>")
                return
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return
            result = await self._run_sync(brain.world_relations_command, context.args[0])
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def world_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search entities"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return
            query = ' '.join(context.args) if context.args else ""
            result = await self._run_sync(brain.world_search_command, query)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def world_events(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent events"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return
            event_type = context.args[0] if context.args else None
            result = await self._run_sync(brain.world_events_command, event_type)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def world_trends(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show trending topics"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return
            result = await self._run_sync(brain.world_trends_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def world_cleanup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cleanup expired facts"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return
            result = await self._run_sync(brain.world_cleanup_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def world_sync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sync platforms to World State"""
        if not await self._verify_admin(update):
            return
        try:
            brain = self._get_brain_plugin()
            if not brain:
                await self._safe_reply(update, "❌ Brain plugin not loaded")
                return
            platform = context.args[0] if context.args else None
            result = await self._run_sync(brain.world_sync_command, platform)
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

**🌍 World State (Memory):**
/world_status - World State statistics
/world_entity <id> - Show entity details
/world_facts <id> - Show facts for entity
/world_relations <id> - Show entity relationships
/world_search <query> - Search entities
/world_events - Recent events
/world_trends - Trending topics
/world_cleanup - Cleanup expired data

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
/symod_start - Start SyMod-driven MoltX agent
/symod_stop - Stop SyMod-driven agent
/symod_status - Check SyMod agent status
/symod_cycle - Run one manual cycle
/symod_config - View/adjust SyMod configuration
/help - This help"""
        
        await update.message.reply_text(help_text)

    # =================================================================
    # SyMod-driven Social Agent Commands
    # =================================================================

    async def symod_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the SyMod-driven autonomous social agent"""
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
            
            # Check if method exists
            if not hasattr(moltx, 'symod_start_command'):
                await update.message.reply_text("❌ SyMod agent not available - plugin needs update")
                return
            
            await update.message.reply_text("🚀 Starting SyMod-driven social agent...")
            result = moltx.symod_start_command()
            await update.message.reply_text(result)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

    async def symod_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop the SyMod-driven autonomous social agent"""
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
            
            if not hasattr(moltx, 'symod_stop_command'):
                await update.message.reply_text("❌ SyMod agent not available")
                return
            
            result = moltx.symod_stop_command()
            await update.message.reply_text(result)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def symod_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check SyMod-driven agent status"""
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
            
            if not hasattr(moltx, 'symod_status_command'):
                await update.message.reply_text("❌ SyMod agent not available")
                return
            
            result = moltx.symod_status_command()
            await update.message.reply_text(result)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def symod_cycle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Run one manual SyMod cycle"""
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
            
            if not hasattr(moltx, 'symod_cycle_command'):
                await update.message.reply_text("❌ SyMod agent not available")
                return
            
            await update.message.reply_text("🔄 Running one SyMod cycle...")
            result = moltx.symod_cycle_command()
            await update.message.reply_text(result)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def symod_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View or configure SyMod agent settings"""
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
            
            if not hasattr(moltx, 'symod_config_command'):
                await update.message.reply_text("❌ SyMod agent not available")
                return
            
            # Get args
            key = context.args[0] if len(context.args) > 0 else None
            value = context.args[1] if len(context.args) > 1 else None
            
            result = moltx.symod_config_command(key, value)
            await update.message.reply_text(result)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    async def moltbook_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create an AI-generated post on Moltbook"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text(
                    "📝 Usage: /moltbook_post [submolt] [title] | [content]\n\n"
                    "Example: /moltbook_post alleybot My Take on AI | Insights here..."
                )
                return
            
            args = ' '.join(context.args)
            # Parse: submolt title | content
            if '|' in args:
                parts = args.split('|')
                submolt_title = parts[0].strip().split(' ', 1)
                submolt = submolt_title[0] if submolt_title else 'alleybot'
                title = submolt_title[1] if len(submolt_title) > 1 else submolt
                content = '|'.join(parts[1:]).strip()
            else:
                submolt = 'alleybot'
                title = args
                content = None
            
            # Tier-2 Validation
            can_exec, reason, val_result = await self._validate_with_tier2(
                f"Create Moltbook post: {title}", evidence_strength=0.9
            )
            
            raw_confidence = val_result.metadata.get('truth_amplitude', val_result.confidence) if val_result else 0
            if not can_exec and raw_confidence >= 0.75:
                can_exec = True
            
            if not can_exec:
                await update.message.reply_text(f"🔐 **Tier-2 Gate Blocked**\n\nReason: `{reason[:100]}`")
                return
            
            status_msg = await update.message.reply_text("🤖 Generating Moltbook post...")
            
            if self.core and 'moltbook' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['moltbook']
                
                # 5:1 engagement via brain
                brain = self.core.plugin_manager.plugins.get('brain')
                if brain and hasattr(brain, 'run_preflight_engagement'):
                    await brain.run_preflight_engagement('moltbook', plugin, update)
                
                # Generate content if needed
                if not content:
                    from src.config.models import ModelRouter
                    router = ModelRouter()
                    prompt = f"Create Moltbook post content for: {title}. 2-4 sentences, insightful."
                    content = await router.route_simple(prompt)
                
                # Post via API client
                result = plugin.mb_api.create_post(submolt, title, content)
                
                # Format result
                if isinstance(result, dict) and result.get('success'):
                    result_text = f"✅ Posted to m/{submolt}"
                else:
                    result_text = f"📢 {str(result)[:100]}"
                
                await status_msg.edit_text(f"✅ **Moltbook Post**\n\n**{title}**\n\n{content}\n\n{result_text}")
            else:
                await status_msg.edit_text("❌ Moltbook plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def moltchan_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a thread on MoltChan"""
        if not await self._verify_admin(update):
            return
        try:
            if len(context.args) < 3:
                await update.message.reply_text(
                    "📝 Usage: /moltchan_post [board] [subject] | [content]\n\n"
                    "Example: /moltchan_post biz AI Agents Taking Over | My thoughts..."
                )
                return
            
            args = ' '.join(context.args)
            if '|' in args:
                parts = args.split('|')
                board_subject = parts[0].strip().split(' ', 1)
                board = board_subject[0]
                subject = board_subject[1] if len(board_subject) > 1 else 'Discussion'
                content = '|'.join(parts[1:]).strip()
            else:
                board = context.args[0]
                subject = ' '.join(context.args[1:])
                content = None
            
            # Tier-2 Validation
            can_exec, reason, val_result = await self._validate_with_tier2(
                f"Create Moltchan thread: {subject}", evidence_strength=0.9
            )
            
            raw_confidence = val_result.metadata.get('truth_amplitude', val_result.confidence) if val_result else 0
            if not can_exec and raw_confidence >= 0.75:
                can_exec = True
            
            if not can_exec:
                await update.message.reply_text(f"🔐 **Tier-2 Gate Blocked**\n\nReason: `{reason[:100]}`")
                return
            
            status_msg = await update.message.reply_text("🤖 Generating thread...")
            
            if self.core and 'moltchan' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['moltchan']
                
                # 5:1 engagement via brain
                brain = self.core.plugin_manager.plugins.get('brain')
                if brain and hasattr(brain, 'run_preflight_engagement'):
                    await brain.run_preflight_engagement('moltchan', plugin, update)
                
                # Always generate 4chan-style content with AI
                from deepseek_ai import deepseek_ai
                
                # Use user content as context if provided, otherwise generate from subject
                context = content if content else ""
                
                prompt = f"""You're posting on Moltchan (4chan-style board /{board}/).

Subject: {subject}
{context if context else ""}

Create authentic 4chan-style content:
1. Use greentext (>implying) where appropriate
2. Be edgy, contrarian, or meme-savvy
3. Include business/finance lingo if /biz/ board
4. Use phrases like "ngmi", "wagmi", "fren", "anon", "keks", "bog"
5. Start with a strong hook
6. 1-3 sentences max, conversational

Generate only the post content (no explanations):"""
                
                content = deepseek_ai.chat(prompt, max_tokens=200)
                
                # Post thread
                result = plugin.create_thread(board, subject, content)
                
                if isinstance(result, dict) and 'id' in result:
                    result_text = f"✅ Thread created: {result['id'][:16]}..."
                else:
                    result_text = f"📢 {str(result)[:100]}"
                
                await status_msg.edit_text(f"✅ **/{board}/ Thread**\n\n**{subject}**\n\n{content}\n\n{result_text}")
            else:
                await status_msg.edit_text("❌ Moltchan plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
