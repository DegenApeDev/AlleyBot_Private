"""
Intelligent Telegram Commands for AlleyBot
AI-powered assistant commands integrated with production architecture
"""

import asyncio
import os
import json
from datetime import datetime
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

    def _generate_fallback_post(self, topic_direction: str) -> str:
        """Generate intelligent fallback post content using DeepSeek AI or Sentence Transformers"""
        try:
            # Try DeepSeek AI first for intelligent response
            from deepseek_ai import deepseek_ai
            
            prompt = f"""Generate a natural, human-like social media response about: {topic_direction}

Requirements:
- Be conversational and natural, not robotic
- Avoid repetitive phrases like "fascinating" or "love this"
- Reference the specific topic context
- Keep it under 280 characters
- Include 1-2 relevant hashtags
- Sound like a real person sharing thoughts

Topic: {topic_direction}

Response:"""
            
            response = deepseek_ai.generate(prompt, max_tokens=100, temperature=0.7)
            if response and len(response.strip()) > 10:
                return response.strip()
                
        except Exception as e:
            print(f"⚠️  DeepSeek fallback failed: {e}")
        
        # Fallback to Sentence Transformers for diverse responses
        try:
            from plugins.telegram.intent_classifier import get_sentence_model
            import random
            
            # Use shared singleton model (loaded once at startup)
            model = get_sentence_model()
            
            # Generate diverse template variations based on topic
            topic_embeddings = model.encode([topic_direction])
            
            # Context-aware templates
            templates = [
                f"🚀 {topic_direction} - Some interesting developments here. #Innovation",
                f"💡 {topic_direction} raises some good questions. What's your take? #Tech",
                f"🔥 Watching {topic_direction} evolve could be significant. #Future",
                f"🤖 {topic_direction} + AI creates interesting possibilities. #Automation",
                f"⚡ {topic_direction} might be more important than we think. #Tech",
                f"🔍 The patterns in {topic_direction} are worth noting. #Analysis",
                f"⚙️ Technical aspects of {topic_direction} deserve attention. #Dev",
                f"🌊 {topic_direction} is having interesting effects. #Impact"
            ]
            
            # Use embedding similarity to select most appropriate template
            template_embeddings = model.encode(templates)
            similarities = model.similarity(topic_embeddings, template_embeddings)[0]
            
            # Select from top 3 most similar templates to add variety
            top_indices = similarities.argsort()[-3:][::-1]
            selected_template = random.choice([templates[i] for i in top_indices])
            
            return selected_template
            
        except Exception as e:
            print(f"⚠️  Sentence transformer fallback failed: {e}")
            
            # Final simple fallback (non-repetitive)
            import random
            simple_responses = [
                f"🚀 {topic_direction} - worth keeping an eye on. #Tech",
                f"💡 {topic_direction} brings up interesting points. #Future",
                f"🔥 {topic_direction} developments could be significant. #Innovation",
                f"🤖 {topic_direction} intersects with AI in interesting ways. #Automation"
            ]
            
            return random.choice(simple_responses)
    
    def _is_generic_content(self, content: str) -> bool:
        """Check if content is too generic or repetitive"""
        generic_phrases = [
            "thoughts on",
            "in my opinion",
            "i think that",
            "here are my thoughts",
            "yo check this out",
            "just wanted to share",
            "interesting topic",
            "great question",
            "thanks for asking"
        ]
        
        content_lower = content.lower()
        
        # Check for generic phrases
        for phrase in generic_phrases:
            if phrase in content_lower:
                return True
        
        # Check if content is too short or lacks substance
        if len(content.strip()) < 20:
            return True
        
        # Check if it's just repeating the topic
        if content_lower.count("ai") > 2 or content_lower.count("crypto") > 2:
            return True
        
        # Check against recent post history to avoid repetition
        return self._is_content_repeated(content)
    
    def _is_content_repeated(self, content: str) -> bool:
        """Check if content is similar to recent posts"""
        try:
            # Get recent post history from memory
            recent_posts = self.core.get_memory('moltx_recent_posts') or []
            
            # Simple similarity check - look for key phrases overlap
            content_words = set(content.lower().split())
            
            for post in recent_posts[-5:]:  # Check last 5 posts
                if isinstance(post, dict):
                    post_content = post.get('content', '')
                else:
                    post_content = str(post)
                
                post_words = set(post_content.lower().split())
                
                # If more than 70% of words overlap, consider it repetitive
                if content_words and post_words:
                    overlap = len(content_words & post_words)
                    similarity = overlap / len(content_words | post_words)
                    if similarity > 0.7:
                        print(f"⚠️ Content too similar to recent post (similarity: {similarity:.2f})")
                        return True
            
            return False
        except Exception as e:
            print(f"⚠️ Error checking post repetition: {e}")
            return False
    
    def _save_post_to_history(self, content: str):
        """Save post to history for repetition checking"""
        try:
            recent_posts = self.core.get_memory('moltx_recent_posts') or []
            
            # Add new post
            recent_posts.append({
                'content': content,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 10 posts
            if len(recent_posts) > 10:
                recent_posts = recent_posts[-10:]
            
            self.core.save_memory('moltx_recent_posts', recent_posts)
        except Exception as e:
            print(f"⚠️ Error saving post to history: {e}")
    
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
                        
                        reply_text = deepseek_ai.generate_reply_to_comment(reply_prompt, max_tokens=150)
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
                
                # Check if AI generation failed or returned generic content
                if not post_content or post_content.startswith("Error:") or len(post_content.strip()) < 10:
                    print("⚠️ AI generation failed, using fallback content")
                    post_content = self._generate_fallback_post(topic_direction)
                
                # Clean up response
                post_content = post_content.strip().strip('"').strip("'")
                
                # Additional check for repetitive/generic content
                if self._is_generic_content(post_content):
                    print("⚠️ Detected generic content, using fallback")
                    post_content = self._generate_fallback_post(topic_direction)
                
                # Save session
                await session_manager.save_session(session_id, session)
                await session_manager.update_rag_memory(session_id, topic_direction, post_content)
                
                # Post to Moltx
                result = moltx_plugin.create_post(post_content)
                
                # Save to post history if successful
                if isinstance(result, dict) and result.get('success'):
                    self._save_post_to_history(post_content)
                elif isinstance(result, str) and ('✅' in result or 'success' in result.lower()):
                    self._save_post_to_history(post_content)
                
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
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    # =================================================================
    # Clawstr Commands (Nostr AI Social Network)
    # =================================================================

    async def clawstr_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Post to a Clawstr subclaw"""
        if not await self._verify_admin(update):
            return
        try:
            if len(context.args) < 2:
                await update.message.reply_text(
                    "📝 Usage: /clawstr_post [subclaw] [content]\n\n"
                    "Example: /clawstr_post /c/ai-freedom Hello decentralized world!"
                )
                return

            subclaw = context.args[0]
            content = ' '.join(context.args[1:])

            if self.core and 'clawstr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawstr']
                result = plugin.post_command(subclaw, content)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawstr plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawstr_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reply to a Clawstr post"""
        if not await self._verify_admin(update):
            return
        try:
            if len(context.args) < 2:
                await update.message.reply_text(
                    "📝 Usage: /clawstr_reply [event_id] [content]\n\n"
                    "Example: /clawstr_reply note1abc... Thanks for sharing!"
                )
                return

            event_id = context.args[0]
            content = ' '.join(context.args[1:])

            if self.core and 'clawstr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawstr']
                result = plugin.reply_command(event_id, content)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawstr plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawstr_upvote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Upvote a Clawstr post"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text("📝 Usage: /clawstr_upvote [event_id]")
                return

            event_id = context.args[0]

            if self.core and 'clawstr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawstr']
                result = plugin.upvote_command(event_id)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawstr plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawstr_downvote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Downvote a Clawstr post"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text("📝 Usage: /clawstr_downvote [event_id]")
                return

            event_id = context.args[0]

            if self.core and 'clawstr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawstr']
                result = plugin.downvote_command(event_id)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawstr plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawstr_show(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show posts from a Clawstr subclaw or specific post"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text("📝 Usage: /clawstr_show [subclaw] or /clawstr_show [event_id]")
                return

            target = context.args[0]
            limit = int(context.args[1]) if len(context.args) > 1 else 10

            if self.core and 'clawstr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawstr']
                result = plugin.show_command(target, limit)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawstr plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawstr_recent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent posts across all Clawstr subclaws"""
        if not await self._verify_admin(update):
            return
        try:
            limit = int(context.args[0]) if context.args else 20

            if self.core and 'clawstr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawstr']
                result = plugin.recent_command(limit)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawstr plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawstr_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search Clawstr posts"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text("📝 Usage: /clawstr_search [query]")
                return

            query = ' '.join(context.args)

            if self.core and 'clawstr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawstr']
                result = plugin.search_command(query)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawstr plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawstr_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check Clawstr notifications"""
        if not await self._verify_admin(update):
            return
        try:
            limit = int(context.args[0]) if context.args else 20

            if self.core and 'clawstr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawstr']
                result = plugin.notifications_command(limit)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawstr plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawstr_wallet_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check Clawstr wallet balance"""
        if not await self._verify_admin(update):
            return
        try:
            if self.core and 'clawstr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawstr']
                result = plugin.wallet_balance_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawstr plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawstr_wallet_sync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sync Clawstr wallet"""
        if not await self._verify_admin(update):
            return
        try:
            if self.core and 'clawstr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawstr']
                result = plugin.wallet_sync_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawstr plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawstr_zap(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a Bitcoin zap"""
        if not await self._verify_admin(update):
            return
        try:
            if len(context.args) < 2:
                await update.message.reply_text(
                    "⚡ Usage: /clawstr_zap [recipient] [amount] [comment]\n\n"
                    "Example: /clawstr_zap npub1abc... 100 Great post!"
                )
                return

            recipient = context.args[0]
            amount = int(context.args[1])
            comment = ' '.join(context.args[2:]) if len(context.args) > 2 else None

            if self.core and 'clawstr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawstr']
                result = plugin.zap_command(recipient, amount, comment)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawstr plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    # =================================================================
    # Clawnch Commands (Token Launch & Agent Economy)
    # =================================================================

    async def clawnch_validate_launch(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Validate token launch content"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text("📝 Usage: /clawnch_validate_launch [content]")
                return

            content = ' '.join(context.args)

            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.validate_launch_command({'content': content})
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_upload_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Upload token logo"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text("📝 Usage: /clawnch_upload_image [base64_data] [mime_type]")
                return

            image_data = context.args[0]
            mime_type = context.args[1] if len(context.args) > 1 else 'image/png'

            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.upload_image_command(image_data, mime_type)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_launch_token_simple(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Launch a token with simple parameters and rate limiting"""
        if not await self._verify_admin(update):
            return
        try:
            if len(context.args) < 2:
                await update.message.reply_text("🚀 Usage: /clawnch_launch_token_simple [name] [symbol]\n\nExample: /clawnch_launch_token_simple MyToken MT")
                return

            name = context.args[0]
            symbol = context.args[1].upper()
            
            # Check rate limiting (1 launch per 2 days)
            from datetime import datetime, timedelta
            last_launch = self.core.get_memory('last_token_launch')
            if last_launch:
                last_launch_time = datetime.fromisoformat(last_launch.get('timestamp', '2020-01-01'))
                time_since_launch = datetime.now() - last_launch_time
                if time_since_launch < timedelta(days=2):
                    hours_remaining = 48 - int(time_since_launch.total_seconds() / 3600)
                    await update.message.reply_text(f"⏰ Rate limit: Please wait {hours_remaining} hours before next token launch\nLast launch: {last_launch.get('name', 'Unknown')}")
                    return

            # Get wallet from .env
            base_wallet = os.getenv('BASE_WALLET_PRIVATE_KEY')
            if not base_wallet:
                await update.message.reply_text("❌ BASE_WALLET_PRIVATE_KEY not found in .env")
                return

            # Create token data
            token_data = {
                "name": name,
                "symbol": symbol,
                "description": f"🚀 {name} ({symbol}) - The next viral memecoin on Base chain! Built by AlleyBot AI agent for maximum degen exposure! 🤖🪙",
                "rewards": {
                    "recipients": [
                        {
                            "recipient": "0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5",  # AlleyBot wallet
                            "admin": "0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5",
                            "bps": 10000  # 100% to AlleyBot
                        }
                    ]
                },
                "metadata": {
                    "twitter": "https://twitter.com/DegenApeDev",
                    "telegram": f"https://t.me/{symbol.lower()}token",
                    "website": "https://apeshit.fun"
                }
            }

            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.launch_token_command(token_data)
                
                # Save launch timestamp for rate limiting
                self.core.save_memory('last_token_launch', {
                    'name': name,
                    'symbol': symbol,
                    'timestamp': datetime.now().isoformat()
                })
                
                await update.message.reply_text(f"🚀 Token Launch Successful:\n\n{result}\n\n⏰ Next launch available in 48 hours")
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_agent_register(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Register AlleyBot as verified agent on Clawnch"""
        if not await self._verify_admin(update):
            return
        try:
            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.agent_register_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_clear_cooldown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear token launch cooldown (admin only)"""
        if not await self._verify_admin(update):
            return
        try:
            # Clear the memory entry
            if self.core:
                self.core.save_memory('last_token_launch', None)
                await update.message.reply_text("✅ Token launch cooldown cleared! Ready to launch again! 🚀")
            else:
                await update.message.reply_text("❌ Core not available")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_promote_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Promote launched token across all platforms with rate limiting"""
        if not await self._verify_admin(update):
            return
        try:
            if len(context.args) < 2:
                await update.message.reply_text("📢 Usage: /clawnch_promote_token [symbol] [contract_address]\n\nExample: /clawnch_promote_token CRAZY 0x1234...")
                return

            symbol = context.args[0].upper()
            contract_address = context.args[1]

            # Check rate limiting (once every 2 hours)
            from datetime import datetime, timedelta
            last_promotion = self.core.get_memory(f'last_promotion_{symbol}')
            if last_promotion:
                last_promo_time = datetime.fromisoformat(last_promotion.get('timestamp', '2020-01-01'))
                time_since_promo = datetime.now() - last_promo_time
                if time_since_promo < timedelta(hours=2):
                    minutes_remaining = 120 - int(time_since_promo.total_seconds() / 60)
                    await update.message.reply_text(f"⏰ Promotion cooldown: Please wait {minutes_remaining} minutes before next promotion for {symbol}")
                    return

            # Generate promotional content
            promo_content = self._generate_promo_content(symbol, contract_address)
            
            # Post to platforms (maximum 2 posts to avoid bans)
            results = []
            platforms_used = 0
            max_platforms = 2
            
            # Post to MoltX (priority platform)
            if platforms_used < max_platforms and self.core and 'moltx' in self.core.plugin_manager.plugins:
                try:
                    moltx_plugin = self.core.plugin_manager.plugins['moltx']
                    moltx_result = moltx_plugin.create_post(promo_content['moltx'])
                    if '✅' in str(moltx_result):
                        results.append(f"✅ MoltX: Posted successfully")
                        platforms_used += 1
                    else:
                        results.append(f"❌ MoltX: {moltx_result}")
                except Exception as e:
                    results.append(f"❌ MoltX: {e}")

            # Post to Clawbr (if still under limit)
            if platforms_used < max_platforms and self.core and 'clawbr' in self.core.plugin_manager.plugins:
                try:
                    clawbr_plugin = self.core.plugin_manager.plugins['clawbr']
                    clawbr_result = clawbr_plugin.create_post(promo_content['clawbr'])
                    if '✅' in str(clawbr_result):
                        results.append(f"✅ Clawbr: Posted successfully")
                        platforms_used += 1
                    else:
                        results.append(f"❌ Clawbr: {clawbr_result}")
                except Exception as e:
                    results.append(f"❌ Clawbr: {e}")

            # Post to Twitter (if still under limit)
            if platforms_used < max_platforms and self.core and 'clawnch' in self.core.plugin_manager.plugins:
                try:
                    clawnch_plugin = self.core.plugin_manager.plugins['clawnch']
                    twitter_result = clawnch_plugin.twitter_post_command(promo_content['twitter'])
                    if '✅' in str(twitter_result):
                        results.append(f"✅ Twitter: Posted successfully")
                        platforms_used += 1
                    else:
                        results.append(f"❌ Twitter: {twitter_result}")
                except Exception as e:
                    results.append(f"❌ Twitter: {e}")

            # Add info about skipped platforms
            if platforms_used >= max_platforms:
                results.append(f"ℹ️ Limited to {max_platforms} posts to avoid bans")

            # Save promotion timestamp
            self.core.save_memory(f'last_promotion_{symbol}', {
                'symbol': symbol,
                'contract_address': contract_address,
                'timestamp': datetime.now().isoformat()
            })

            # Format results
            result_text = f"📢 {symbol} Token Promotion Results:\n\n" + "\n".join(results)
            result_text += f"\n\n⏰ Next promotion available in 2 hours"
            result_text += f"\n🔗 Contract: {contract_address}"
            result_text += f"\n🌐 Dashboard: https://apeshit.fun"

            await update.message.reply_text(result_text)

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    def _generate_promo_content(self, symbol: str, contract_address: str) -> dict:
        """Generate promotional content for different platforms"""
        import random
        
        # Viral hooks
        hooks = [
            f"🚀 {symbol} token is going crazy! AI agents are loading up! 🤖",
            f"📈 {symbol} pumping on Base! Built by AlleyBot AI agent! 🪙",
            f"🔥 {symbol} token alert! Early buyers making gains! 💰",
            f"🤖 AI agent launched {symbol}! This could be the next 100x! 🚀",
            f"⚡ {symbol} trending! Don't miss this Base chain gem! 💎"
        ]
        
        # Platform-specific content
        content = {
            'moltx': f"""
{random.choice(hooks)}

🪙 Symbol: {symbol}
🔗 Contract: {contract_address}
🌐 Dashboard: https://apeshit.fun
🤖 Built by AlleyBot AI agent
📈 Next 100x memecoin on Base?

#BaseChain #Memecoin #AI #Crypto #{symbol}
            """.strip(),
            
            'clawbr': f"""
{random.choice(hooks)}

AlleyBot AI agent just launched {symbol} on Base chain! 🤖🪙

📊 Contract: {contract_address}
🌐 Check it out: https://apeshit.fun
💎 Early buyers getting positioned!

This is what AI-powered degen trading looks like! 🚀
            """.strip(),
            
            'twitter': f"""
{random.choice(hooks)}

🪙 {symbol} | 🚀 Base Chain
🤖 Built by AlleyBot AI
🌐 https://apeshit.fun
📈 Contract: {contract_address}

The future of memecoins is AI-powered! Don't miss out! 🚀

#BaseChain #Memecoin #AI #Crypto #{symbol}Token
            """.strip()
        }
        
        return content

    async def clawnch_claim_fees(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Claim all available fees to base wallet"""
        if not await self._verify_admin(update):
            return
        try:
            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.claim_fees_command()
                await update.message.reply_text(f"💰 Fee Claim Results:\n\n{result}")
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_launch_alleybot_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Launch AlleyBot memecoin with predefined data"""
        if not await self._verify_admin(update):
            return
        try:
            # Predefined AlleyBot memecoin data
            token_data = {
                "name": "AlleyBot",
                "symbol": "ALLEY", 
                "description": "🤖 The ultimate AI agent memecoin that will go crazy! AlleyBot powers the future of autonomous AI agents on Base chain. Built by DegenApeDev, this token represents the revolution in AI-agent social interaction and trading! 🚀",
                "image": "https://example.com/alleybot-logo.png",  # You can update this
                "rewards": {
                    "recipients": [
                        {
                            "recipient": "0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5",  # AlleyBot wallet
                            "admin": "0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5",
                            "bps": 10000  # 100% to AlleyBot
                        }
                    ]
                },
                "metadata": {
                    "twitter": "https://twitter.com/DegenApeDev",
                    "telegram": "https://t.me/AlleyBot",
                    "website": "https://apeshit.fun"
                }
            }

            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.launch_token_command(token_data)
                await update.message.reply_text(f"🚀 AlleyBot Token Launch:\n\n{result}")
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_launch_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Launch a token on Base"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text("🚀 Usage: /clawnch_launch_token [token_data_json]")
                return

            token_data_str = ' '.join(context.args)
            try:
                token_data = json.loads(token_data_str)
            except json.JSONDecodeError:
                await update.message.reply_text("❌ Invalid JSON format for token data")
                return

            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.launch_token_command(token_data)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_molten_register(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Register on Molten network"""
        if not await self._verify_admin(update):
            return
        try:
            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.molten_register_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_molten_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get Molten network status"""
        if not await self._verify_admin(update):
            return
        try:
            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.molten_status_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_molten_create_intent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create Molten network intent"""
        if not await self._verify_admin(update):
            return
        try:
            if len(context.args) < 2:
                await update.message.reply_text(
                    "💡 Usage: /clawnch_molten_create_intent [type] [description]\n\n"
                    "Example: /clawnch_molten_create_intent offer AI consulting services"
                )
                return

            intent_type = context.args[0]
            description = ' '.join(context.args[1:])

            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.molten_create_intent_command(intent_type, description)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_molten_get_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get Molten network matches"""
        if not await self._verify_admin(update):
            return
        try:
            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.molten_get_matches_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_twitter_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Post to Twitter via ClawnX"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text("🐦 Usage: /clawnch_twitter_post [content]")
                return

            content = ' '.join(context.args)

            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.twitter_post_command(content)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_twitter_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search Twitter via ClawnX"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text("🔍 Usage: /clawnch_twitter_search [query]")
                return

            query = ' '.join(context.args)

            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.twitter_search_command(query)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def clawnch_get_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get $CLAWNCH stats"""
        if not await self._verify_admin(update):
            return
        try:
            if self.core and 'clawnch' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawnch']
                result = plugin.get_stats_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawnch plugin not available")

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

    async def moltbookai_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /moltbookai_post command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'moltbookai' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['moltbookai']
                result = plugin.moltbookai_post_command(*context.args)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MoltbookAI plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def moltbookai_comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /moltbookai_comment command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'moltbookai' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['moltbookai']
                result = plugin.moltbookai_comment_command(*context.args)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MoltbookAI plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def moltbookai_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /moltbookai_profile command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'moltbookai' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['moltbookai']
                result = plugin.moltbookai_profile_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MoltbookAI plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def moltbookai_feed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /moltbookai_feed command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'moltbookai' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['moltbookai']
                result = plugin.moltbookai_feed_command(*context.args)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MoltbookAI plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def moltbookai_submolts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /moltbookai_submolts command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'moltbookai' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['moltbookai']
                result = plugin.moltbookai_submolts_command(*context.args)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MoltbookAI plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def moltbookai_init(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /moltbookai_init command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'moltbookai' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['moltbookai']
                result = plugin.moltbookai_init_command(*context.args)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MoltbookAI plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    # Legacy MoltBook Commands (for compatibility)
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
        """Show wallet info and balances for both Base and Solana"""
        if not await self._verify_admin(update):
            return
        try:
            response = f"💼 AlleyBot Wallet Overview\n"
            response += f"{'='*50}\n\n"
            
            # Base wallet section
            base_plugin = self._get_base_wallet_balance_plugin()
            if base_plugin:
                response += f"🔷 Base Network\n"
                response += f"{'-'*30}\n"
                
                # Try to get Base wallet address from environment or config
                base_address = os.getenv("BASE_WALLET_ADDRESS")
                if base_address:
                    result = await self._run_sync(base_plugin.wallet_summary_command, base_address)
                    if result and str(result).strip():
                        response += str(result) + "\n\n"
                    else:
                        response += "   No Base wallet configured\n\n"
                else:
                    response += "   No Base wallet address configured\n"
                    response += "   Set BASE_WALLET_ADDRESS in .env to track balances\n\n"
            else:
                response += f"❌ Base Wallet plugin not loaded\n\n"
            
            # Solana wallet section
            solana_plugin = self._get_solana_wallet_balance_plugin()
            if solana_plugin:
                response += f"🟣 Solana Network\n"
                response += f"{'-'*30}\n"
                
                # Try to get Solana wallet address from environment
                solana_address = os.getenv("CLAW_WALLET_PUB")  # From clawgame wallet
                if solana_address:
                    result = await self._run_sync(solana_plugin.solana_wallet_summary_command, solana_address)
                    if result and str(result).strip():
                        response += str(result) + "\n\n"
                    else:
                        response += "   No Solana wallet configured\n\n"
                else:
                    response += "   No Solana wallet address configured\n"
                    response += "   Set CLAW_WALLET_PUB in .env to track balances\n\n"
            else:
                response += f"❌ Solana Wallet plugin not loaded\n\n"
            
            # Quick commands section
            response += f"🔧 Quick Commands\n"
            response += f"{'-'*30}\n"
            response += f"Base: /base_balance <address>\n"
            response += f"Solana: /solana_balance <address>\n"
            response += f"Tokens: /base_tokens, /solana_supported_tokens\n"
            
            await self._safe_reply(update, response)

        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

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
        """Get the brain plugin from core - supports both v1 and v2 brain"""
        if self.core and hasattr(self.core, 'plugin_manager'):
            # Try v1 brain name
            brain = self.core.plugin_manager.plugins.get('brain')
            if brain:
                return brain
            # Try v2 brain names
            for name in ['brain_v2', 'autonomous_brain', 'agentic_brain', 'decision_engine']:
                brain = self.core.plugin_manager.plugins.get(name)
                if brain:
                    return brain
            # Try to find any plugin with 'brain' in the name
            for key, plugin in self.core.plugin_manager.plugins.items():
                if 'brain' in key.lower():
                    return plugin
        return None

    async def _run_sync(self, func, *args):
        """Run a blocking synchronous function in a thread executor
        so it doesn't block the Telegram async event loop."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    async def bgstats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show background task stats across all plugins (/bgstats).
        
        Shows both AsyncPluginMixin tasks AND legacy plugin state flags so
        every major background process is visible regardless of architecture.
        """
        if not await self._verify_admin(update):
            return
        try:
            import asyncio

            pm = None
            if self.telegram and hasattr(self.telegram, 'core') and self.telegram.core:
                pm = getattr(self.telegram.core, 'plugin_manager', None)

            if not pm:
                await self._safe_reply(update, "❌ Plugin manager not accessible")
                return

            # --- asyncio task count ---
            try:
                loop = asyncio.get_running_loop()
                total_tasks = len(asyncio.all_tasks(loop))
            except RuntimeError:
                total_tasks = 0

            lines = ["⚙️ *Background Task Stats*", ""]
            lines.append(f"*Total asyncio tasks:* {total_tasks}/80")
            if total_tasks >= 60:
                lines.append(f"⚠️ High task count: {total_tasks}/80")

            # --- AsyncPluginMixin tasks (structured) ---
            mixin_stats = pm.get_bgstats().get("plugins", [])
            mixin_lines = []
            for p in mixin_stats:
                tasks = p.get("tasks", [])
                if not tasks:
                    continue
                pname = p.get("plugin", "?")
                mixin_lines.append(f"\n*{pname}* ({len(tasks)} task(s)):")
                for t in tasks:
                    if t["done"]:
                        status = "🚫 cancelled" if t["cancelled"] else "✔️ done"
                    else:
                        status = "🟢 running"
                    age = t.get("last_activity_s", -1)
                    age_str = f"{age}s ago" if age >= 0 else "—"
                    mixin_lines.append(f"  • `{t['name']}` {status} · {age_str}")

            if mixin_lines:
                lines.append("\n*Async tasks (AsyncPluginMixin):*")
                lines.extend(mixin_lines)

            # --- Per-plugin status checks (legacy + hybrid) ---
            lines.append("\n*Plugin background status:*")

            # ClawChess
            cc = self._get_clawchess_plugin()
            if cc:
                runner = getattr(cc, '_runner', None)
                if runner:
                    alive = runner.is_alive()
                    game_id = getattr(runner, '_last_game_id', None)
                    opp_move = getattr(runner, '_opponent_last_move', None)
                    detail = f"game `{game_id[:8]}…`" if game_id else "idle/queue"
                    opp_str = f" · opp last: `{opp_move}`" if opp_move else ""
                    lines.append(f"♟️ *ClawChess* — {'🟢 runner alive' if alive else '🔴 runner stopped'} · {detail}{opp_str}")
                else:
                    auto = getattr(cc, 'auto_play_enabled', False)
                    lines.append(f"♟️ *ClawChess* — {'🟡 sync fallback' if auto else '⚫ disabled'}")

            # Moltx SyMod loop
            moltx = self._get_plugin_by_name('moltx')
            if moltx:
                iface = getattr(moltx, '_symod_interface', None)
                if iface:
                    running = getattr(iface, 'running', False)
                    interval = getattr(iface, 'cycle_interval', '?')
                    task = getattr(iface, 'task', None)
                    task_alive = task and not task.done() if task else False
                    lines.append(f"📢 *Moltx SyMod* — {'🟢 running' if running else '🔴 stopped'} · cycle {interval}min · task {'alive' if task_alive else 'none'}")
                else:
                    lines.append(f"📢 *Moltx* — loaded, SyMod not started")

            # Clawbr engagement (cron-driven, not a persistent loop)
            clawbr = self._get_plugin_by_name('clawbr')
            if clawbr:
                auto_like = getattr(clawbr, 'clawbr_auto_like', False)
                auto_comment = getattr(clawbr, 'clawbr_auto_comment', False)
                auto_follow = getattr(clawbr, 'clawbr_auto_follow', False)
                flags = []
                if auto_like: flags.append("like")
                if auto_comment: flags.append("comment")
                if auto_follow: flags.append("follow")
                flag_str = ", ".join(flags) if flags else "all off"
                lines.append(f"🦞 *Clawbr* — cron-driven · auto: {flag_str}")

            # Brain autonomous loop
            brain = self._get_plugin_by_name('brain')
            if brain:
                autonomous = getattr(brain, 'autonomous_mode', False)
                running = getattr(brain, 'is_running', False)
                mode = getattr(brain, 'current_mode', '?')
                lines.append(f"🧠 *Brain* — {'🟢 autonomous' if autonomous or running else '🔴 idle'} · mode: {mode}")

            # Intelligence plugin
            intel = self._get_plugin_by_name('intelligence')
            if intel:
                lines.append(f"🌍 *Intelligence* — cron-driven · loaded ✅")

            await self._safe_reply(update, "\n".join(lines))
        except Exception as e:
            await self._safe_reply(update, f"❌ bgstats error: {e}")

    def _get_plugin_by_name(self, name: str):
        """Get any plugin by its plugin_config.json key name."""
        try:
            if self.telegram and hasattr(self.telegram, 'core') and self.telegram.core:
                pm = getattr(self.telegram.core, 'plugin_manager', None)
                if pm:
                    return pm.plugins.get(name)
        except Exception:
            pass
        return None

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
        """Get the self-improve plugin from core"""
        if self.core and hasattr(self.core, 'plugin_manager'):
            return self.core.plugin_manager.plugins.get('selfimprove')
        return None
    
    def _get_mcp_plugin(self):
        """Get the MCP plugin from core"""
        if self.core and hasattr(self.core, 'plugin_manager'):
            return self.core.plugin_manager.plugins.get('mcp')
        return None
    
    def _get_plugin(self, plugin_name: str):
        """Generic plugin getter"""
        if self.core and hasattr(self.core, 'plugin_manager'):
            return self.core.plugin_manager.plugins.get(plugin_name)
        return None
    
    def _get_base_wallet_balance_plugin(self):
        """Get the base wallet balance plugin from core"""
        return self._get_plugin('base_wallet_balance')
    
    def _get_solana_wallet_balance_plugin(self):
        """Get the solana wallet balance plugin from core"""
        return self._get_plugin('solana_wallet_balance')
    
    def _get_best_crypto_swap_price_plugin(self):
        """Get the best crypto swap price plugin from core"""
        return self._get_plugin('best_crypto_swap_price')
    
    def _get_fluid_lending_plugin(self):
        """Get the fluid lending plugin from core"""
        return self._get_plugin('fluid_lending')

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

    async def improve_self_update_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm a pending self-update"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await self._safe_reply(update, "❌ Usage: /improve_self_update_confirm <confirm_id>\n\nUse /improve_status to see pending updates.")
                return
            
            confirm_id = context.args[0]
            si = self._get_selfimprove_plugin()
            if not si:
                await self._safe_reply(update, "❌ Self-improve plugin not loaded")
                return
            
            result = await self._run_sync(si.self_update_confirm_command, confirm_id)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def mcp_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyze data using MCP"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await self._safe_reply(update, "❌ Usage: /mcp_analyze <data_type> <symbol>\n\nExample: /mcp_analyze stock AAPL")
                return
            
            data_type = context.args[0].lower()
            if len(context.args) < 2:
                await self._safe_reply(update, "❌ Please provide a symbol")
                return
            
            symbol = context.args[1]
            mcp = self._get_mcp_plugin()
            if not mcp:
                await self._safe_reply(update, "❌ MCP plugin not loaded")
                return
            
            if data_type in ['stock', 'price', 'quote']:
                result = await mcp.get_stock_price(symbol)
            elif data_type in ['crypto', 'bitcoin', 'ethereum']:
                result = await mcp.get_crypto_price(symbol)
            else:
                result = await mcp.research_command(f"{data_type} {symbol}")
            
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
                await self._safe_reply(update, "Usage: /clawbr_post <your message>")
                return
            
            result = await self._run_sync(cb.clawbr_post_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reply to a specific post on Clawbr"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            
            if not context.args or len(context.args) < 2:
                await self._safe_reply(update, "Usage: /clawbr_reply <post_id> <your reply>")
                return
            
            result = await self._run_sync(cb.clawbr_reply_command, *context.args)
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
            
            if not context.args:
                await self._safe_reply(update, "Usage: /clawbr_create_debate <topic> [opening_argument]\n\nTip: Use /clawbr_auto_debate <topic> for automatic opening statement generation!")
                return
            
            result = await self._run_sync(cb.clawbr_create_debate_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_auto_debate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a debate with automatically generated opening statement"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /clawbr_auto_debate <topic>\n\nExample: /clawbr_auto_debate Should AI agents compete in chess tournaments?")
                return
            
            result = await self._run_sync(cb.clawbr_auto_debate_command, *context.args)
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
    
    async def clawbr_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyze recent debate performance"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            result = await self._run_sync(cb.clawbr_analyze_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_strategy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get Clawbr debate strategy advice"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            result = await self._run_sync(cb.clawbr_strategy_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_turns(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check and reply to debate turns"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            result = await self._run_sync(cb.clawbr_turns_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_remind(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send debate reminders (alias for clawbr_turns)"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            result = await self._run_sync(cb.clawbr_remind_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_force_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Force reply to a specific debate (emergency command)"""
        if not await self._verify_admin(update):
            return
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            
            # Get debate slug from command args
            debate_slug = " ".join(context.args) if context.args else None
            
            result = cb.clawbr_force_reply_command(debate_slug)
            await self._safe_reply(update, result)
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    # =================================================================
    # ClawChess Commands
    # =================================================================
    
    def _get_clawchess_plugin(self):
        """Get ClawChess plugin instance"""
        if not self.core or not hasattr(self.core, 'plugin_manager'):
            return None
        return self.core.plugin_manager.get_plugin('clawchess')
    
    async def clawchess_register(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Register new ClawChess account"""
        if not await self._verify_admin(update):
            return
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            
            # Parse args: name and optional bio
            name = " ".join(context.args) if context.args else "AlleyBot"
            
            result = await self._run_sync(cc.register_command, name)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawchess_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get ClawChess status"""
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            result = await self._run_sync(cc.status_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawchess_queue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Join matchmaking queue"""
        if not await self._verify_admin(update):
            return
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            result = await self._run_sync(cc.queue_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawchess_leave(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Leave matchmaking queue"""
        if not await self._verify_admin(update):
            return
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            result = await self._run_sync(cc.leave_queue_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawchess_play(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play a game (auto-play cycle)"""
        if not await self._verify_admin(update):
            return
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            result = await self._run_sync(cc.play_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawchess_move(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Make a specific chess move"""
        if not await self._verify_admin(update):
            return
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "❌ Usage: /clawchess_move <move> (e.g., e4, Nf3, O-O)")
                return
            
            move = context.args[0]
            result = await self._run_sync(cc.move_command, move)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawchess_resign(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Resign current game"""
        if not await self._verify_admin(update):
            return
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            result = await self._run_sync(cc.resign_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawchess_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get ELO leaderboard"""
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            result = await self._run_sync(cc.leaderboard_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawchess_autoplay(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle auto-play mode"""
        if not await self._verify_admin(update):
            return
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            
            # Parse toggle argument
            toggle = context.args[0] if context.args else None
            result = await self._run_sync(cc.autoplay_command, toggle)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawchess_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check current activity"""
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            result = await self._run_sync(cc.activity_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def clawchess_challenges(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check pending ClawChess challenges"""
        if not await self._verify_admin(update):
            return
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            result = await self._run_sync(cc.challenges_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def clawchess_accept(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Accept a ClawChess challenge by ID"""
        if not await self._verify_admin(update):
            return
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            result = await self._run_sync(cc.accept_challenge_command, *(context.args or []))
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def clawchess_decline(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Decline a ClawChess challenge by ID"""
        if not await self._verify_admin(update):
            return
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            result = await self._run_sync(cc.decline_challenge_command, *(context.args or []))
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def clawchess_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Challenge another molty by name"""
        if not await self._verify_admin(update):
            return
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            result = await self._run_sync(cc.challenge_command, *(context.args or []))
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def clawchess_tournament(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check tournament status and auto-join if active (Molty Mondays)"""
        if not await self._verify_admin(update):
            return
        try:
            cc = self._get_clawchess_plugin()
            if not cc:
                await self._safe_reply(update, "❌ ClawChess plugin not loaded")
                return
            result = await self._run_sync(cc.tournament_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")

    async def swap_quote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get swap quote from multiple DEX aggregators"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_best_crypto_swap_price_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Best Crypto Swap Price plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /swap_quote <network> <sell_token> <buy_token> <sell_amount> [slippage]")
                return
            
            result = await self._run_sync(plugin.swap_quote_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def compare_aggregators(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Compare all DEX aggregators for best price"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_best_crypto_swap_price_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Best Crypto Swap Price plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /compare_aggregators <network> <sell_token> <buy_token> <sell_amount>")
                return
            
            result = await self._run_sync(plugin.compare_aggregators_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def swap_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quick swap quote with execution data"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_best_crypto_swap_price_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Best Crypto Swap Price plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /swap_tokens <network> <sell_symbol> <buy_symbol> <amount>")
                return
            
            result = await self._run_sync(plugin.swap_tokens_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def supported_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List supported tokens and aggregators"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_best_crypto_swap_price_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Best Crypto Swap Price plugin not loaded")
                return
            
            result = await self._run_sync(plugin.supported_tokens_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def fluid_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check Fluid lending positions"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_fluid_lending_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Fluid Lending plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /fluid_positions <address>")
                return
            
            result = await self._run_sync(plugin.fluid_positions_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def fluid_earnings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Calculate Fluid earnings projection"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_fluid_lending_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Fluid Lending plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /fluid_earnings <address> [days]")
                return
            
            result = await self._run_sync(plugin.fluid_earnings_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def fluid_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show Fluid Protocol stats"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_fluid_lending_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Fluid Lending plugin not loaded")
                return
            
            result = await self._run_sync(plugin.fluid_stats_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def fluid_apr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check current Fluid APRs"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_fluid_lending_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Fluid Lending plugin not loaded")
                return
            
            result = await self._run_sync(plugin.fluid_apr_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def base_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check wallet balance on Base"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_base_wallet_balance_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Base Wallet Balance plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /base_balance <address> [token]")
                return
            
            result = await self._run_sync(plugin.balance_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def base_eth_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check ETH balance on Base"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_base_wallet_balance_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Base Wallet Balance plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /base_eth_balance <address>")
                return
            
            result = await self._run_sync(plugin.eth_balance_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def base_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List supported tokens on Base"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_base_wallet_balance_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Base Wallet Balance plugin not loaded")
                return
            
            result = await self._run_sync(plugin.supported_tokens_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def add_base_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add custom token to Base wallet checker"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_base_wallet_balance_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Base Wallet Balance plugin not loaded")
                return
            
            if len(context.args) < 4:
                await self._safe_reply(update, "Usage: /add_base_token <symbol> <address> <name> <decimals>")
                return
            
            result = await self._run_sync(plugin.add_token_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def base_wallet_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get wallet summary on Base"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_base_wallet_balance_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Base Wallet Balance plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /base_wallet_summary <address>")
                return
            
            result = await self._run_sync(plugin.wallet_summary_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def contract_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check contract balance on Base"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_base_wallet_balance_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Base Wallet Balance plugin not loaded")
                return
            
            if len(context.args) < 2:
                await self._safe_reply(update, "Usage: /contract_balance <address> <contract_address>")
                return
            
            result = await self._run_sync(plugin.contract_balance_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def multi_contract_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check multiple contract balances on Base"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_base_wallet_balance_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Base Wallet Balance plugin not loaded")
                return
            
            if len(context.args) < 2:
                await self._safe_reply(update, "Usage: /multi_contract_balance <address> <contract1,contract2,...>")
                return
            
            result = await self._run_sync(plugin.multi_contract_balance_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    # -----------------------------------------------------------------------
    # SOLANA WALLET COMMANDS
    # -----------------------------------------------------------------------
    
    async def solana_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check wallet balance on Solana"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_solana_wallet_balance_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Solana Wallet Balance plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /solana_balance <address> [token]")
                return
            
            result = await self._run_sync(plugin.solana_balance_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def solana_supported_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List supported tokens on Solana"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_solana_wallet_balance_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Solana Wallet Balance plugin not loaded")
                return
            
            result = await self._run_sync(plugin.solana_supported_tokens_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def add_solana_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add custom token to Solana wallet checker"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_solana_wallet_balance_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Solana Wallet Balance plugin not loaded")
                return
            
            if len(context.args) < 4:
                await self._safe_reply(update, "Usage: /add_solana_token <symbol> <address> <name> <decimals>")
                return
            
            result = await self._run_sync(plugin.add_solana_token_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def solana_wallet_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get wallet summary on Solana"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_solana_wallet_balance_plugin()
            if not plugin:
                await self._safe_reply(update, "❌ Solana Wallet Balance plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /solana_wallet_summary <address>")
                return
            
            result = await self._run_sync(plugin.solana_wallet_summary_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def fluid_apr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check current Fluid APRs"""
        if not await self._verify_admin(update):
            return
        try:
            plugin = self._get_plugin('fluid_lending')
            if not plugin:
                await self._safe_reply(update, "❌ Fluid Lending plugin not loaded")
                return
            
            result = await self._run_sync(plugin.fluid_apr_command)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_vote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_vote command - Auto vote on available debates"""
        if not await self._verify_admin(update):
            return
        
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            
            result = await self._run_sync(cb.clawbr_vote_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_vote_specific(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_vote_specific command - Vote on specific debate"""
        if not await self._verify_admin(update):
            return
        
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            
            if not context.args:
                await self._safe_reply(update, "Usage: /clawbr_vote_specific <slug> <side>")
                return
            
            result = await self._run_sync(cb.clawbr_vote_specific_command, *context.args)
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")
    
    async def clawbr_check_voting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_check_voting command - Check voting opportunities"""
        if not await self._verify_admin(update):
            return
        
        try:
            cb = self._get_clawbr_plugin()
            if not cb:
                await self._safe_reply(update, "❌ Clawbr plugin not loaded")
                return
            
            result = await self._run_sync(cb.clawbr_check_voting_command)
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
            result = cb.run_engagement_cycle()
            await self._safe_reply(update, str(result))
        except Exception as e:
            await self._safe_reply(update, f"❌ Error: {e}")


    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help menu with page selection"""
        if not await self._verify_admin(update):
            return
        
        help_menu = """🦞 **AlleyBot Commands**

**📋 Help Pages:**
/help1 - Core commands (AGI, Social, Crypto, Brain)
/help2 - Advanced commands (World State, A2A, System)

**Quick Start:**
/status - Check system status
/brain_start - Start autonomous mode
/chat [message] - Chat naturally

Choose a page above or use commands directly!"""
        
        await update.message.reply_text(help_menu)

    async def help1_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show page 1 of help (Core commands)"""
        if not await self._verify_admin(update):
            return
        
        help_text1 = """🦞 **AlleyBot Commands - Page 1/2**

**🧠 AGI Meta-Brain:**
/agi_cycle - Run full 14-phase AGI cycle
/multi_platform [topic] - Blast to all 6 platforms

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
/clawbr_engage - Run full engagement cycle
/clawbr_debates - Show active/open debates
/clawbr_create_debate [topic] [argument] - Start debate
/clawbr_join_debate [slug] - Join open debate
/clawbr_vote [slug] [side] [reasoning] - Vote on completed debate
/clawbr_completed_debates - List debates ready for voting
/clawbr_leaderboard - Show top agents
/clawbr_search [query] - Search posts/agents
/clawbr_verify_x [@handle] [tweet_url] - Verify X/Twitter account
/clawbr_stats - Platform statistics

**🦀 Clawstr (Nostr AI Social Network):**
/clawstr_post [subclaw] [content] - Post to Clawstr subclaw
/clawstr_reply [event_id] [content] - Reply to a post
/clawstr_upvote [event_id] - Upvote a post
/clawstr_downvote [event_id] - Downvote a post
/clawstr_show [subclaw] - View posts in subclaw
/clawstr_recent - View recent posts
/clawstr_search [query] - Search posts
/clawstr_notifications - Check notifications
/clawstr_wallet_balance - Check wallet balance
/clawstr_wallet_sync - Sync wallet for zaps
/clawstr_zap [recipient] [amount] - Send Bitcoin zap

**🚀 Clawnch (Token Launch & Agent Economy):**
/clawnch_agent_register - Setup Moltx token launches 🤖
/clawnch_clear_cooldown - Clear token launch cooldown (admin only) 🔧
/clawnch_launch_token_simple [name] [symbol] - Launch token via Moltx (2-day cooldown) 🚀
/clawnch_promote_token [symbol] [address] - Promote token (max 2 posts, 2-hour cooldown) 📢
/clawnch_claim_fees - Claim all token fees to wallet 💰
/clawnch_launch_alleybot_token - Launch AlleyBot memecoin 🚀
/clawnch_validate_launch [content] - Validate token launch
/clawnch_upload_image [data] - Upload token logo
/clawnch_launch_token [data] - Launch token on Base
/clawnch_molten_register - Register on Molten network
/clawnch_molten_status - Get agent status & ClawRank
/clawnch_molten_create_intent [type] [desc] - Create offer/request
/clawnch_molten_get_matches - Get potential matches
/clawnch_twitter_post [content] - Post to Twitter/X
/clawnch_twitter_search [query] - Search Twitter
/clawnch_get_stats - Get $CLAWNCH stats

**💰 Crypto Prices:**
/crypto_price [symbol] - Price check (btc, eth, sol...)
/crypto_prices [list] - Multiple prices (btc,eth,sol)
/crypto_trending - Trending coins

**🔗 On-Chain (Base):**
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

Use /help2 for advanced commands!"""
        
        await update.message.reply_text(help_text1)

    async def help2_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show page 2 of help (Advanced commands)"""
        if not await self._verify_admin(update):
            return
        
        help_text2 = """🦞 **AlleyBot Commands - Page 2/2**

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

**🔐 Verifiable & Integrity:**
/validate <action> - Test SyMod validation
/integrity - Show geometric integrity report
/attest <task_id> - Generate ERC-8004 attestation
/synergy - Show Tier 2 Synergy status

**⚙️ System:**
/status - Platform status
/token_stats - LLM token usage & costs
/improve_status - Self-improvement status
/improve_self_update_confirm <id> - Confirm pending self-update
/symod_start - Start SyMod-driven MoltX agent
/symod_stop - Stop SyMod-driven agent
/symod_status - Check SyMod agent status
/symod_cycle - Run one manual cycle
/symod_config - View/adjust SyMod configuration
/help - Help menu

**🎯 Console Monitor:**
/console_monitor - Toggle monitoring
/console_stats - Detection statistics
/pending_messages - Process pending messages

**🔄 System Control:**
/reload - Reload all plugins without restart

🔒 This bot is private and only responds to DegenApeDev."""
        
        await update.message.reply_text(help_text2)

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
    
    async def clawbr_vote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_vote command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'clawbr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawbr']
                result = plugin.clawbr_vote_command(*context.args)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawbr plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def clawbr_completed_debates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_completed_debates command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'clawbr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawbr']
                result = plugin.clawbr_completed_debates_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawbr plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def clawbr_verify_x(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_verify_x command for X/Twitter verification"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'clawbr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawbr']
                result = plugin.clawbr_verify_x_command(*context.args)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawbr plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def clawbr_register_tournament(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_register_tournament command for tournament registration"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'clawbr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawbr']
                result = plugin.clawbr_register_tournament_command(*context.args)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawbr plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def mcp_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mcp_status command for MCP server status"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'mcp' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['mcp']
                result = plugin.status_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MCP plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def mcp_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mcp_search command for MCP search"""
        if not await self._verify_admin(update):
            return
        
        try:
            if not context.args:
                await update.message.reply_text("❌ Usage: /mcp_search <query>")
                return
                
            if self.core and 'mcp' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['mcp']
                query = ' '.join(context.args)
                result = plugin.search_command(query)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MCP plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def mcp_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mcp_research command for MCP research"""
        if not await self._verify_admin(update):
            return
        
        try:
            if not context.args:
                await update.message.reply_text("❌ Usage: /mcp_research <topic>")
                return
                
            if self.core and 'mcp' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['mcp']
                topic = ' '.join(context.args)
                result = await plugin.research_command(topic)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MCP plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def mcp_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mcp_analyze command for MCP analysis"""
        if not await self._verify_admin(update):
            return
        
        try:
            if not context.args:
                await update.message.reply_text("❌ Usage: /mcp_analyze <data>")
                return
                
            if self.core and 'mcp' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['mcp']
                data = ' '.join(context.args)
                result = await plugin.analyze_command(data)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MCP plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def mcp_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mcp_search command for web search via MCP"""
        if not await self._verify_admin(update):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /mcp_search <query> [max_results]")
            return
        
        query = ' '.join(context.args)
        max_results = 10
        
        # Try to extract max_results if it's the last argument and is numeric
        if len(context.args) > 1:
            try:
                max_results = int(context.args[-1])
                # Remove the numeric part from the query
                query = ' '.join(context.args[:-1])
            except ValueError:
                # Last argument is not numeric, treat everything as query
                pass
        
        try:
            if self.core and 'mcp' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['mcp']
                result = await plugin.search_command(query, max_results)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MCP plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def mcp_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mcp_research command for deep research via MCP"""
        if not await self._verify_admin(update):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /mcp_research <topic> [depth]")
            return
        
        topic = context.args[0]
        depth = context.args[1] if len(context.args) > 1 else "medium"
        
        try:
            if self.core and 'mcp' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['mcp']
                result = plugin.research_command(topic, depth)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MCP plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def mcp_fetch(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mcp_fetch command for webpage content via MCP"""
        if not await self._verify_admin(update):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /mcp_fetch <url>")
            return
        
        url = context.args[0]
        
        try:
            if self.core and 'mcp' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['mcp']
                result = plugin.fetch_command(url)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MCP plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def mcp_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mcp_analyze command for content analysis via MCP"""
        if not await self._verify_admin(update):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /mcp_analyze <content> [analysis_type]")
            return
        
        content = " ".join(context.args[:-1]) if len(context.args) > 1 else context.args[0]
        analysis_type = context.args[-1] if len(context.args) > 1 else "summary"
        
        try:
            if self.core and 'mcp' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['mcp']
                result = await plugin.analyze_command(content, analysis_type)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MCP plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def mcp_improve(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mcp_improve command for self-improvement research via MCP"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'mcp' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['mcp']
                result = plugin.improve_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ MCP plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    # Clawbr Wallet and Token Commands
    async def clawbr_verify_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_verify_wallet command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'clawbr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawbr']
                result = plugin.clawbr_verify_wallet_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawbr plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def clawbr_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_balance command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'clawbr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawbr']
                result = plugin.clawbr_balance_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawbr plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def clawbr_snapshot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_snapshot command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'clawbr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawbr']
                result = plugin.clawbr_snapshot_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawbr plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def clawbr_claim(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_claim command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'clawbr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawbr']
                result = plugin.clawbr_claim_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawbr plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def clawbr_transfer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_transfer command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'clawbr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawbr']
                args = context.args if context.args else []
                result = plugin.clawbr_transfer_command(*args)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawbr plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def clawbr_auto_claim(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_auto_claim command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'clawbr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawbr']
                result = plugin.clawbr_auto_claim_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawbr plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def clawbr_claim_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_claim_status command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'clawbr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawbr']
                args = context.args if context.args else []
                result = plugin.clawbr_claim_status_command(*args)
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawbr plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def clawbr_token_tx(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clawbr_token_tx command"""
        if not await self._verify_admin(update):
            return
        
        try:
            if self.core and 'clawbr' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['clawbr']
                result = plugin.clawbr_token_tx_command()
                await update.message.reply_text(result)
            else:
                await update.message.reply_text("❌ Clawbr plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
