"""
Production-Ready AlleyBot Entry Point
Event-driven architecture with DeepSeek + Grok-4.1-reasoning
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.event_runner import EventRunner
from src.agents.session_manager import SessionManager
from src.config.models import ModelRouter
from src.skills.skill_loader import SkillLoader
from src.integrations.telegram_webhook import TelegramWebhook


class ProductionAlleyBot:
    """Production-ready AlleyBot with event-driven architecture"""
    
    def __init__(self, core):
        self.core = core
        
        # Initialize components
        print("🚀 Initializing Production AlleyBot...")
        
        # Session management
        self.session_manager = SessionManager()
        print("✅ Session Manager initialized")
        
        # Model routing
        self.model_router = ModelRouter()
        print("✅ Model Router initialized")
        
        # Skills system
        self.skill_loader = SkillLoader()
        print("✅ Skill Loader initialized")
        
        # Event runner
        self.event_runner = EventRunner(core)
        self.event_runner.session_manager = self.session_manager
        self.event_runner.model_router = self.model_router
        print("✅ Event Runner initialized")
        
        # Telegram integration
        owner_id = os.getenv('TELEGRAM_OWNER_ID', '6172568442')
        self.telegram_webhook = TelegramWebhook(self.event_runner, owner_id)
        
        # Inject telegram plugin if available
        if hasattr(core, 'plugin_manager') and 'telegram' in core.plugin_manager.plugins:
            self.telegram_webhook.telegram_plugin = core.plugin_manager.plugins['telegram']
            print("✅ Telegram integration ready")
        
        print("🎉 Production AlleyBot initialized successfully!")
    
    async def start(self):
        """Start the production event-driven system"""
        try:
            print("\n" + "="*60)
            print("🚀 PRODUCTION ALLEYBOT - EVENT-DRIVEN MODE")
            print("="*60)
            print("📊 Architecture:")
            print("  • Central Event Queue (asyncio.Queue)")
            print("  • Session State Management (JSON storage)")
            print("  • Dynamic Model Routing (DeepSeek/Grok-4.1)")
            print("  • Modular Skills System (YAML definitions)")
            print("  • Webhook-Ready Integrations")
            print("="*60 + "\n")
            
            # Start Telegram polling (will be replaced with webhook in production)
            self.telegram_webhook.start_polling()
            
            # Start event runner
            await self.event_runner.start()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down Production AlleyBot...")
            self.event_runner.stop()
        except Exception as e:
            print(f"❌ Production AlleyBot error: {e}")
            raise


async def run_production_mode(core):
    """Run AlleyBot in production event-driven mode"""
    bot = ProductionAlleyBot(core)
    await bot.start()


if __name__ == "__main__":
    print("⚠️  This module should be imported and run through alleybot_core.py")
    print("Usage: python run_alleybot.py autonomous")
