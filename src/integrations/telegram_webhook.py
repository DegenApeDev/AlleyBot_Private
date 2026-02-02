"""
Telegram Webhook Integration for AlleyBot
Handles incoming Telegram messages as events
"""

import asyncio
from typing import Optional
from datetime import datetime


class TelegramWebhook:
    """Telegram webhook handler for event-driven architecture"""
    
    def __init__(self, event_runner, owner_id: str):
        self.event_runner = event_runner
        self.owner_id = owner_id
        self.telegram_plugin = None  # Will be injected
        
    async def handle_message(self, message: dict):
        """Handle incoming Telegram message"""
        try:
            from src.agents.event_runner import AgentEvent, EventType
            
            user_id = str(message.get('from', {}).get('id', ''))
            text = message.get('text', '')
            
            # Only process messages from owner
            if user_id != self.owner_id:
                print(f"🚫 Ignoring message from non-owner: {user_id}")
                return
            
            print(f"📱 Telegram message from owner: {text[:50]}...")
            
            # Create event and queue it
            event = AgentEvent(
                event_type=EventType.MESSAGE_RECEIVED,
                session_id=f"telegram_{user_id}",
                channel="telegram",
                payload={
                    "query": text,
                    "user_id": user_id,
                    "message_id": message.get('message_id'),
                    "chat_id": message.get('chat', {}).get('id')
                },
                timestamp=datetime.now(),
                priority=3  # High priority for direct messages
            )
            
            await self.event_runner.queue_event(event)
            
        except Exception as e:
            print(f"❌ Telegram webhook error: {e}")
    
    def start_polling(self):
        """Start Telegram polling (fallback if webhook not available)"""
        try:
            if self.telegram_plugin and hasattr(self.telegram_plugin, 'application'):
                print("📱 Starting Telegram bot polling...")
                # Start the bot in a background thread with its own event loop
                import threading
                
                def run_bot():
                    try:
                        import asyncio
                        # Create new event loop for this thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        # Run the bot
                        self.telegram_plugin.application.run_polling(drop_pending_updates=True)
                    except Exception as e:
                        print(f"❌ Telegram bot error: {e}")
                
                bot_thread = threading.Thread(target=run_bot, daemon=True)
                bot_thread.start()
                self.telegram_plugin.is_running = True
                print("✅ Telegram bot polling started in background")
            else:
                print("⚠️ Telegram plugin not available")
        except Exception as e:
            print(f"❌ Telegram polling error: {e}")
