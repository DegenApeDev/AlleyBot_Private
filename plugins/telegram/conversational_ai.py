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
            
            self.conversation_history[user_id].append({
                'role': 'user',
                'content': message
            })
            
            # Keep last 10 messages for context
            if len(self.conversation_history[user_id]) > 10:
                self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
            
            # Add conversation context to message
            context_message = self._build_context_message(user_id, message)
            
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
            self.conversation_history[user_id].append({
                'role': 'assistant',
                'content': response
            })
            
            return response
            
        except Exception as e:
            print(f"❌ Agentic response error: {e}")
            return f"❌ Error processing request: {e}"
    
    def _build_context_message(self, user_id: int, message: str) -> str:
        """Build message with conversation context"""
        history = self.conversation_history.get(user_id, [])
        
        if len(history) <= 1:
            return message
        
        # Add recent context
        context = "Recent conversation:\n"
        for msg in history[-5:-1]:  # Last 4 messages (excluding current)
            role = "You" if msg['role'] == 'assistant' else "Admin"
            context += f"{role}: {msg['content'][:100]}\n"
        
        context += f"\nCurrent request: {message}"
        return context
    
    async def _fallback_response(self, message: str) -> str:
        """
        Fallback response using DeepSeek directly
        Used when agentic system is not available
        """
        try:
            from deepseek_ai import deepseek_ai
            import requests
            
            if not deepseek_ai.enabled:
                return "🤖 AlleyBot here! Agentic system is not running. Use /help for available commands."
            
            system_prompt = """You are AlleyBot, an autonomous AI agent that manages social media presence across multiple platforms (MoltX, Moltbook, etc.) and handles crypto operations.

You help your admin by:
- Providing status updates on engagement and karma
- Executing tasks like creating posts, engaging with feeds
- Analyzing trends and suggesting strategies
- Managing platform integrations

Be helpful, concise, and proactive. Use emojis appropriately."""

            headers = {
                "Authorization": f"Bearer {deepseek_ai.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": deepseek_ai.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{deepseek_ai.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                return "🤖 I'm here! Use /help to see what I can do."
                
        except Exception as e:
            print(f"❌ Fallback response error: {e}")
            return "🤖 AlleyBot ready! Use /help for commands."
    
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
