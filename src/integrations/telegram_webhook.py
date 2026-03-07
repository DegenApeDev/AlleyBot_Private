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
    
    async def start_polling_async(self):
        """Start Telegram polling as async task"""
        try:
            if not self.telegram_plugin:
                print("⚠️  Telegram plugin not injected into webhook")
                return
            if not hasattr(self.telegram_plugin, 'application') or not self.telegram_plugin.application:
                print("⚠️  Telegram application not built (missing bot token?)")
                return

            app = self.telegram_plugin.application
            print("📱 Starting Telegram bot polling...")

            # Initialize the application (registers handlers)
            await app.initialize()
            print("  ✅ Application initialized")

            # Start the application (enables handlers to process updates)
            await app.start()
            print("  ✅ Application started")

            # Start polling in background task
            # NOTE: drop_pending_updates=False so we process commands sent during startup
            await app.updater.start_polling(
                drop_pending_updates=False,
                allowed_updates=["message", "callback_query"]
            )

            self.telegram_plugin.is_running = True
            print("✅ Telegram bot polling started — commands are live!")
            
            # Start all AsyncPluginMixin background tasks now that event loop is running
            if hasattr(self.telegram_plugin, 'core') and hasattr(self.telegram_plugin.core, 'plugin_manager'):
                try:
                    await self.telegram_plugin.core.plugin_manager.start_all_background()
                    print("▶️  All plugin background tasks started")
                except Exception as bg_err:
                    print(f"⚠️  start_all_background error: {bg_err}")

            # Send startup notification
            try:
                if hasattr(self.telegram_plugin, '_send_startup_notification'):
                    self.telegram_plugin._send_startup_notification()
            except Exception:
                pass
            
            # Keep polling alive - this is critical!
            # The updater runs in background, but we need to keep this coroutine alive
            # so the event loop doesn't exit
            import asyncio
            while self.telegram_plugin.is_running:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Telegram polling error: {e}")
            import traceback
            traceback.print_exc()
    
    def start_polling(self):
        """Start Telegram polling (sync wrapper)"""
        try:
            if self.telegram_plugin and hasattr(self.telegram_plugin, 'application'):
                # Just mark as ready - actual polling will be started by event runner
                self.telegram_plugin.is_running = True
                print("📱 Telegram bot ready for polling")
            else:
                print("⚠️ Telegram plugin not available")
        except Exception as e:
            print(f"❌ Telegram polling error: {e}")
