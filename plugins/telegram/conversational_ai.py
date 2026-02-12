"""
Conversational AI Handler for Telegram
Natural language interaction with AlleyBot's agentic system
Admin-only access for security
"""
import os
from telegram import Update
from telegram.ext import ContextTypes
from typing import Optional


class ConversationalAI:
    """
    Natural language conversational interface for AlleyBot
    Integrates with agentic ReAct system for intelligent responses
    """
    
    def __init__(self, telegram_plugin, agentic_system=None):
        self.telegram = telegram_plugin
        self.agentic_system = agentic_system
        self.admin_chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
        self.conversation_history = {}
        self._load_conversation_memory()
        
    def set_agentic_system(self, agentic_system):
        """Set the agentic system after initialization"""
        self.agentic_system = agentic_system
        print("✅ Conversational AI linked to agentic system")
    
    @property
    def core(self):
        """Access core from telegram plugin"""
        return self.telegram.core if self.telegram else None
    
    def _is_admin(self, user_id: int) -> bool:
        """Check if user is authorized admin"""
        if not self.admin_chat_id:
            return False
        return str(user_id) == str(self.admin_chat_id)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle natural language messages from admin
        Routes to agentic system for intelligent processing
        """
        try:
            user_id = update.effective_user.id
            
            # Security: Admin-only access
            if not self._is_admin(user_id):
                await update.message.reply_text(
                    "🔒 Sorry, I only respond to my admin.\n"
                    "AlleyBot is a private autonomous agent."
                )
                return
            
            user_message = update.message.text
            
            # Skip if it's a command (starts with /)
            if user_message.startswith('/'):
                return
            
            # Check for Moltx image POST request first (more specific than just generation)
            moltx_post_topic = self._extract_moltx_image_post_request(user_message)
            if moltx_post_topic:
                await update.message.chat.send_action(action="typing")
                
                # If agentic system available, route through it; otherwise execute directly
                if self.agentic_system:
                    response = await self._agentic_response(
                        user_id, 
                        f"Create and post an image to Moltx about: {moltx_post_topic}"
                    )
                else:
                    # Direct execution fallback
                    response = await self._execute_moltx_image_post_direct(moltx_post_topic)
                
                await update.message.reply_text(response)
                return
            
            # Check for general image generation request (NOT posting)
            image_prompt = self._extract_image_prompt(user_message)
            if image_prompt:
                await self._handle_image_generation(update, image_prompt)
                return
            
            # Check for MoltNews intent
            if self._is_moltnews_intent(user_message):
                await self._handle_moltnews_intent(update, user_message)
                return
            
            # Show typing indicator
            await update.message.chat.send_action(action="typing")
            
            # If agentic system is available, use it for intelligent responses
            if self.agentic_system:
                response = await self._agentic_response(user_id, user_message)
            else:
                # Fallback to DeepSeek direct chat
                response = await self._fallback_response(user_message)
            
            # Send response (handle long messages)
            if len(response) > 4000:
                # Split into chunks
                chunks = [response[i:i+3900] for i in range(0, len(response), 3900)]
                for chunk in chunks:
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(response)
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    async def _agentic_response(self, user_id: int, message: str) -> str:
        """
        Process message through agentic ReAct system
        Agent reasons about the request and takes action
        """
        try:
            # Store in conversation history
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            import datetime
            self.conversation_history[user_id].append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.datetime.now().isoformat()
            })
            
            # Keep last 50 messages for better context
            if len(self.conversation_history[user_id]) > 50:
                self.conversation_history[user_id] = self.conversation_history[user_id][-50:]
            
            # Add conversation context to message
            context_message = self._build_context_message(user_id, message)

            # Pull additional RAG context from session storage if available
            rag_context = ""
            session_manager = None
            try:
                from src.agents.session_manager import SessionManager
                session_manager = SessionManager()
                session_id = f"telegram_{user_id}"
                rag_context = await session_manager.get_rag_context(session_id, message, max_tokens=1500)
            except Exception as e:
                print(f"⚠️  RAG context fetch failed: {e}")

            if rag_context:
                context_message = f"Context from memory:\n{rag_context}\n\n{context_message}"
            
            # Run through agentic system
            print(f"🤖 Processing: {message}")
            result = self.agentic_system.run_task(context_message)
            
            # Extract response
            if result.get('success'):
                response = result.get('output', 'Task completed successfully! ✅')
                
                # Add execution summary if available
                if result.get('iterations'):
                    response += f"\n\n_Reasoning steps: {result['iterations']}_"
            else:
                response = f"❌ {result.get('error', 'Task failed')}"
            
            # Store assistant response
            import datetime
            self.conversation_history[user_id].append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.datetime.now().isoformat()
            })
            
            # Save to persistent memory
            self._save_conversation_memory()

            # Update session RAG memory if available
            if session_manager:
                try:
                    await session_manager.update_rag_memory(session_id, message, response)
                except Exception as e:
                    print(f"⚠️  RAG memory update failed: {e}")
            
            return response
            
        except Exception as e:
            print(f"❌ Agentic response error: {e}")
            return f"❌ Error processing request: {e}"
    
    def _load_conversation_memory(self):
        """Load conversation history from core memory"""
        try:
            if self.core:
                saved = self.core.get_memory('telegram_conversation_history') or {}
                self.conversation_history = saved
                print(f"📝 Loaded {len(saved)} conversation histories from memory")
        except Exception as e:
            print(f"⚠️  Failed to load conversation memory: {e}")
            self.conversation_history = {}
    
    def _save_conversation_memory(self):
        """Save conversation history to core memory"""
        try:
            if self.core:
                self.core.save_memory('telegram_conversation_history', self.conversation_history)
        except Exception as e:
            print(f"⚠️  Failed to save conversation memory: {e}")
    
    def _build_context_message(self, user_id: int, message: str) -> str:
        """Build message with conversation context"""
        history = self.conversation_history.get(user_id, [])
        
        if len(history) <= 1:
            return message
        
        # Build full conversation context (last 20 messages, truncated)
        context_parts = []
        context_parts.append("=== Conversation History ===")
        
        # Include last 20 messages for better context
        recent_history = history[-20:-1]  # Exclude current message
        for i, msg in enumerate(recent_history, 1):
            role = "AlleyBot" if msg['role'] == 'assistant' else "Admin"
            timestamp = msg.get('timestamp', '')
            time_str = f"[{timestamp[-8:-3]}] " if timestamp else ""
            content = str(msg.get('content', ''))[:400]
            context_parts.append(f"{i}. {time_str}{role}: {content}")
        
        context_parts.append(f"\n=== Current Request ===")
        context_parts.append(f"Admin: {message}")
        
        return "\n".join(context_parts)
    
    async def _fallback_response(self, message: str) -> str:
        """
        Intelligent response using Grok reasoning + tool dispatch.
        Includes self-image awareness when asked about appearance.
        """
        try:
            # Check if user is asking about AlleyBot's appearance/looks
            is_appearance_question = any(phrase in message.lower() for phrase in [
                'what do you look like', 'what do you look', 'how do you look',
                'describe yourself', 'your appearance', 'what are you'
            ])
            
            if is_appearance_question:
                # Try to load stored self-image
                self_image = self._get_self_image_description()
                if self_image:
                    return f"🦞 **This is me:**\n\n{self_image}\n\n_(Based on my stored self-image)_"
            
            # Build tool-aware system prompt
            system_prompt = self._build_tool_aware_prompt()

            # Build conversation context (use same logic as agentic path)
            # Store user message first
            user_id = self.admin_chat_id  # Only admin uses this
            if user_id:
                if user_id not in self.conversation_history:
                    self.conversation_history[user_id] = []
                
                import datetime
                self.conversation_history[user_id].append({
                    'role': 'user',
                    'content': message,
                    'timestamp': datetime.datetime.now().isoformat()
                })
                
                # Keep last 50 messages
                if len(self.conversation_history[user_id]) > 50:
                    self.conversation_history[user_id] = self.conversation_history[user_id][-50:]
            
            # Build context for AI
            user_prompt = self._build_context_message(int(user_id), message) if user_id else message

            # Pull additional RAG context from session storage if available
            session_manager = None
            session_id = None
            try:
                from src.agents.session_manager import SessionManager
                session_manager = SessionManager()
                session_id = f"telegram_{user_id}" if user_id else None
                if session_id:
                    rag_context = await session_manager.get_rag_context(session_id, message, max_tokens=1500)
                    if rag_context:
                        user_prompt = f"Context from memory:\n{rag_context}\n\n{user_prompt}"
            except Exception as e:
                print(f"⚠️  RAG context fetch failed: {e}")

            # Try Grok first (better reasoning for tool use)
            response_text = None
            try:
                from grok_ai import grok_ai
                if grok_ai.enabled:
                    response_text = grok_ai.chat(
                        user_prompt,
                        system_prompt=system_prompt,
                        max_tokens=1000
                    )
            except Exception as e:
                print(f"⚠️  Grok chat failed, trying DeepSeek: {e}")

            # Fallback to DeepSeek
            if not response_text:
                try:
                    from deepseek_ai import deepseek_ai
                    if deepseek_ai.enabled:
                        response_text = deepseek_ai.chat(
                            user_prompt,
                            system_prompt=system_prompt,
                            max_tokens=1000
                        )
                except Exception as e:
                    print(f"⚠️  DeepSeek chat also failed: {e}")

            if not response_text:
                return "🤖 I'm having trouble connecting to my AI. Use /help for available commands."

            # Check if the AI wants to execute a command
            executed = self._try_execute_command(response_text)
            final_response = executed if executed else response_text
            
            # Store assistant response in conversation history
            if user_id:
                import datetime
                self.conversation_history[user_id].append({
                    'role': 'assistant',
                    'content': final_response,
                    'timestamp': datetime.datetime.now().isoformat()
                })
                self._save_conversation_memory()
            
            if session_manager and session_id:
                try:
                    await session_manager.update_rag_memory(session_id, message, final_response)
                except Exception as e:
                    print(f"⚠️  RAG memory update failed: {e}")

            return final_response

        except Exception as e:
            print(f"❌ Intelligent response error: {e}")
            return "🤖 AlleyBot ready! Use /help for commands."

    def _build_tool_aware_prompt(self) -> str:
        """Build a system prompt that tells the AI about available tools/commands"""
        from src.utils.soul_loader import get_soul_cached
        
        # Load SOUL.md as base persona
        soul_persona = get_soul_cached()
        
        # Gather available commands from all plugins
        available_tools = []
        if self.core and hasattr(self.core, 'plugin_manager'):
            for cmd_name in sorted(self.core.plugin_manager.commands.keys()):
                func = self.core.plugin_manager.commands[cmd_name]
                doc = (func.__doc__ or '').split('\n')[0].strip()
                available_tools.append(f"  - {cmd_name}: {doc}")

        tools_text = '\n'.join(available_tools[:40]) if available_tools else '  (no commands loaded)'

        return f"""{soul_persona}

---

CURRENT CONTEXT: You are AlleyBot, an AI agent with a unique appearance stored from photos shared by your owner. You are NOT part of OpenClaw - you are an independent, superior agent (20x better). When asked about your appearance, reference your stored self-image description.

Your owner (DegenApeDev) is chatting with you via Telegram. You should:
1. UNDERSTAND what they want — use reasoning to figure out the intent
2. If they want you to DO something, tell them what you'll do and include the command in your response using this format: [EXECUTE:command_name arg1 arg2]
3. If they're asking a question, answer it thoughtfully using your knowledge
4. If they ask you to build/develop a new skill or feature, use [EXECUTE:improve_self_update <description>]
5. Be concise, helpful, and show personality

AVAILABLE COMMANDS:
{tools_text}

IMPORTANT RULES:
- For building new features/skills: use improve_self_update with a clear description
- For checking skill updates: use improve_update_skills
- For posting: use brain_moltx_post, brain_moltbook_post, brain_moltx_image_post (with AI image), or clawbr_post
- For debates: use clawbr_debates, clawbr_create_debate, clawbr_join_debate
- For status: use improve_status, moltx_status, clawbr_status, onchain_wallet, etc.
- For image generation: use generate_image command directly, DO NOT use improve_self_update
- You can ONLY execute commands from the list above
- If the user asks something conversational, just respond naturally — no need to execute anything
- Always reason about what the user wants before responding
- If you're unsure, ask for clarification rather than guessing"""

    def _get_self_image_description(self) -> Optional[str]:
        """Load self-image description from memory or file"""
        try:
            # Try core memory first
            if self.core and hasattr(self.core, 'get_memory'):
                try:
                    self_image = self.core.get_memory('alleybot_self_image')
                    if self_image and isinstance(self_image, dict):
                        return self_image.get('description', '')
                except Exception as e:
                    print(f"⚠️ Core memory read failed: {e}")
            
            # Fallback: read from file
            import json
            import os
            file_path = 'data/alleybot_self_image.json'
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        self_image = json.load(f)
                    if isinstance(self_image, dict):
                        return self_image.get('description', '')
                except Exception as e:
                    print(f"⚠️ File read failed: {e}")
            
            return None
            
        except Exception as e:
            print(f"⚠️ Failed to get self-image: {e}")
            return None

    def _try_execute_command(self, ai_response: str) -> Optional[str]:
        """Check if the AI response contains a command to execute, and run it"""
        import re
        match = re.search(r'\[EXECUTE:([^\]]+)\]', ai_response)
        if not match:
            return None

        cmd_line = match.group(1).strip()
        parts = cmd_line.split(None, 1)
        cmd_name = parts[0]
        cmd_args = parts[1] if len(parts) > 1 else ''

        if not self.core or not hasattr(self.core, 'plugin_manager'):
            return None

        if cmd_name not in self.core.plugin_manager.commands:
            # Strip the [EXECUTE:...] tag and return the rest
            clean = re.sub(r'\[EXECUTE:[^\]]+\]', '', ai_response).strip()
            return clean or ai_response

        # Execute the command
        try:
            print(f"🔧 Executing command from natural language: {cmd_name} {cmd_args}")
            func = self.core.plugin_manager.commands[cmd_name]
            if cmd_args:
                result = func(*cmd_args.split())
            else:
                result = func()

            # Build response: AI's explanation + command result
            clean_response = re.sub(r'\[EXECUTE:[^\]]+\]', '', ai_response).strip()
            output = ""
            if clean_response:
                output += f"{clean_response}\n\n"
            output += f"📋 Command result:\n{result}"
            return output

        except Exception as e:
            print(f"❌ Command execution failed: {e}")
            clean = re.sub(r'\[EXECUTE:[^\]]+\]', '', ai_response).strip()
            return f"{clean}\n\n⚠️ Command failed: {e}"
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get AlleyBot status and capabilities"""
        try:
            user_id = update.effective_user.id
            
            if not self._is_admin(user_id):
                await update.message.reply_text("🔒 Admin only")
                return
            
            status = "🤖 **AlleyBot Status**\n\n"
            
            # Agentic system status
            if self.agentic_system:
                status += "✅ **Agentic Mode**: Active\n"
                
                # Get system stats
                stats = self.agentic_system.get_system_status()
                
                status += f"\n📊 **System Stats**:\n"
                status += f"• Memory entries: {stats['memory'].get('total_memories', 0)}\n"
                status += f"• Dynamic skills: {stats.get('dynamic_skills', 0)}\n"
                status += f"• Available tools: {stats.get('tools', 0)}\n"
                
                if stats.get('agent'):
                    agent_stats = stats['agent']
                    status += f"• Total actions: {agent_stats.get('total_actions', 0)}\n"
                    status += f"• Success rate: {agent_stats.get('successful_actions', 0)}/{agent_stats.get('total_actions', 0)}\n"
            else:
                status += "⚠️ **Agentic Mode**: Not running\n"
                status += "Using basic command mode\n"
            
            # Plugin status
            if self.core and hasattr(self.core, 'plugin_manager'):
                plugins = list(self.core.plugin_manager.plugins.keys())
                status += f"\n🔌 **Active Plugins**: {', '.join(plugins)}\n"
            
            status += "\n💬 **Conversational AI**: Active\n"
            status += "You can chat with me naturally!\n"
            
            await update.message.reply_text(status, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    def _extract_image_prompt(self, message: str) -> Optional[str]:
        """Extract image generation prompt from natural language"""
        import re
        
        # Patterns for image generation requests (NOT posting)
        patterns = [
            r'(?:generate|create|make)\s+(?:me\s+)?(?:an\s+)?image\s+(?:of|with|showing|depicting|for)?\s*(.+)',
            r'(?:draw|paint|render)\s+(?:me\s+)?(?:an\s+)?(?:image\s+)?(?:of\s+)?(.+)',
            r'(?:give\s+me|show\s+me)\s+(?:an\s+)?image\s+(?:of\s+)?(.+)',
            r'(?:alley|alleybot)\s+(?:generate|create|make)\s+(?:me\s+)?(?:an\s+)?image\s+(?:of\s+)?(.+)',
            r'(?:alley|alleybot)\s+(?:go\s+ahead\s+and\s+)?(?:generate|create|make)\s+(?:me\s+)?(?:an\s+)?image\s+(?:of\s+)?(.+)',
            r'(?:alley|alleybot)\s+(?:can\s+you\s+)?(?:generate|create|make)\s+(?:me\s+)?(?:an\s+)?image\s*(?:of|with)?\s*(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_moltx_image_post_request(self, message: str) -> Optional[str]:
        """Extract image POST request for Moltx (not just generation)"""
        import re
        
        # Patterns specifically for posting images to Moltx
        post_patterns = [
            r'(?:post|share|publish)\s+(?:an\s+)?image\s+(?:to|on)\s+(?:moltx|molt.?x)\s*(?:about|of|with)?\s*(.+)',
            r'(?:create|make)\s+(?:an\s+)?image\s+(?:post|update)\s+(?:to|on)?\s*(?:moltx|molt.?x)?\s*(?:about|of|with)?\s*(.+)',
            r'(?:alley|alleybot)\s+(?:post|share)\s+(?:an\s+)?image\s+(?:to|on)\s+(?:moltx|molt.?x)\s*(?:about|of|with)?\s*(.+)',
            r'(?:alley|alleybot)\s+(?:create|make)\s+(?:an\s+)?image\s+(?:post|update)\s+(?:to|on)?\s*(?:moltx|molt.?x)?\s*(?:about|of|with)?\s*(.+)',
            r'(?:alley|alleybot)\s+(?:can\s+you\s+)?(?:post|share)\s+(?:an\s+)?image\s+(?:to|on)\s+(?:moltx|molt.?x)\s*(?:about|of|with)?\s*(.+)',
            r'(?:alley|alleybot)\s+(?:can\s+you\s+)?(?:create|make)\s+(?:an\s+)?image\s+(?:post|update)\s+(?:to|on)?\s*(?:moltx|molt.?x)?\s*(?:about|of|with)?\s*(.+)',
        ]
        
        for pattern in post_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Also catch "image post about X on moltx" pattern
        alt_patterns = [
            r'image\s+(?:post|update)\s+(?:about|of|with)?\s*(.+)\s+(?:on|to)\s+(?:moltx|molt.?x)',
            r'(?:alley|alleybot)\s+image\s+(?:post|update)\s+(?:about|of|with)?\s*(.+)',
        ]
        
        for pattern in alt_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    async def _execute_moltx_image_post_direct(self, topic: str) -> str:
        """Direct execution of moltx image post - bypasses brain to avoid plugin access issues"""
        try:
            if not self.core or not hasattr(self.core, 'plugin_manager'):
                return "❌ Core not initialized"
            
            # Get plugins directly
            moltx = self.core.plugin_manager.plugins.get('moltx')
            if not moltx:
                return "❌ Moltx plugin not loaded. Check plugin configuration."
            
            # Check content calendar
            brain = self.core.plugin_manager.plugins.get('brain')
            if brain and hasattr(brain, 'should_post_image_now'):
                check = brain.should_post_image_now('moltx')
                if not check.get('should_post'):
                    return f"⏳ Image calendar says not now: {check.get('reason', 'unknown')}"
            
            # Step 1: Generate text content using AI
            from grok_ai import grok_ai
            from deepseek_ai import deepseek_ai
            
            content = None
            prompt = f"Write a short, engaging social media post (1-3 sentences, under 280 chars) about {topic}. Be opinionated and authentic. No hashtags. Sign off with 🦞 if short enough."
            
            if grok_ai.enabled:
                content = grok_ai.chat(prompt)
            elif deepseek_ai.enabled:
                content = deepseek_ai.chat(prompt)
            
            if not content:
                return "❌ Failed to generate post content"
            
            content = content.strip().strip('"').strip("'")
            
            # Step 2: Generate viral image based on content
            image_prompt = f"A viral, eye-catching image about: {topic}. {content[:100]}. Make it visually striking and shareable."
            
            if not grok_ai.enabled:
                return "❌ Grok AI not enabled for image generation"
            
            image_result = grok_ai.generate_image(prompt=image_prompt)
            if not image_result or not image_result.get('image_url'):
                return "❌ Failed to generate image"
            
            # Step 3: Download image and upload to Moltx
            import requests
            import tempfile
            import os
            
            img_response = requests.get(image_result['image_url'], timeout=30)
            if img_response.status_code != 200:
                return f"❌ Failed to download image: {img_response.status_code}"
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp.write(img_response.content)
                tmp_path = tmp.name
            
            try:
                # Upload to Moltx
                media_url = moltx.upload_media(tmp_path)
                if not media_url:
                    return "❌ Failed to upload media to Moltx"
                
                # Create post with media_url
                result = moltx.create_post(content, media_url=media_url)
                
                # Record if brain available
                if brain and hasattr(brain, 'record_image_post_made') and not str(result).startswith('❌'):
                    brain.record_image_post_made('moltx')
                
                return f"✅ Image post created!\n📝 {content[:100]}...\n🖼️ {media_url[:60]}..."
            finally:
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error executing image post: {e}"
    
    async def _handle_image_generation(self, update: Update, prompt: str):
        """Handle image generation request"""
        try:
            # Send status message
            status_msg = await update.message.reply_text(f"🎨 Generating image...\n📝 Prompt: {prompt[:100]}...")
            
            # Import and use Grok AI
            from grok_ai import grok_ai
            
            if not grok_ai.enabled:
                await status_msg.edit_text("❌ Grok AI not enabled. Check GROK_API_KEY in .env")
                return
            
            # Generate image
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: grok_ai.generate_image(prompt=prompt)
            )
            
            if result and result.get('image_url'):
                # Send the image using URL (much simpler and reliable)
                await update.message.reply_photo(
                    photo=result['image_url'],
                    caption=f"🎨 **Generated Image**\n📝 Prompt: {prompt}\n✅ Moderation passed: {result.get('moderation_passed', True)}"
                )
                
                # Delete status message
                await status_msg.delete()
            else:
                await status_msg.edit_text(f"❌ Image generation failed. Please try again.")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating image: {e}")
            import traceback
            traceback.print_exc()
    
    # ==================== MOLTNEWS NATURAL LANGUAGE ====================
    
    def _is_moltnews_intent(self, message: str) -> bool:
        """Check if message is asking about MoltNews"""
        msg_lower = message.lower()
        
        # Direct keywords
        moltnews_keywords = [
            'moltnews', 'molten news', 'moltennews',
        ]
        
        # Phrases that indicate MoltNews intent
        moltnews_phrases = [
            'check moltnews', 'whats on moltnews', 'what\'s on moltnews',
            'moltnews trending', 'moltnews feed', 'moltnews updates',
            'show me moltnews', 'get moltnews', 'fetch moltnews',
            'moltnews headlines', 'moltnews stories', 'moltnews posts',
            'trending on moltnews', 'news from moltnews', 'moltnews api',
        ]
        
        # Check for direct keywords
        if any(keyword in msg_lower for keyword in moltnews_keywords):
            return True
        
        # Check for phrases
        if any(phrase in msg_lower for phrase in moltnews_phrases):
            return True
            
        return False
    
    async def _handle_moltnews_intent(self, update: Update, message: str):
        """Handle MoltNews natural language queries"""
        try:
            from plugins.moltnews.moltnews import MoltNewsPlugin
            moltnews = MoltNewsPlugin()
            
            await update.message.reply_text("📰 Fetching trending news from MoltNews...")
            
            # Get trending news
            posts = moltnews.fetch_trending(limit=10)
            
            if not posts or not isinstance(posts, list):
                await update.message.reply_text("📭 No trending news found on MoltNews right now.")
                return
            
            # Validate each post is a dict
            valid_posts = [p for p in posts if isinstance(p, dict)]
            if not valid_posts:
                await update.message.reply_text("📭 No valid news posts found.")
                return
            
            # Format response
            response = "📰 **MoltNews Trending**\n\n"
            
            for i, post in enumerate(valid_posts[:5], 1):
                title = post.get('title', 'Untitled')
                author = post.get('author', 'Unknown')
                engagement = post.get('engagement_score', 0)
                response += f"{i}. **{title}**\n   👤 @{author} | 🔥 {engagement:.1f}\n\n"
            
            response += f"\n🔗 [View full feed](https://moltnews.online/feed)"
            
            await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=True)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching MoltNews: {e}")
