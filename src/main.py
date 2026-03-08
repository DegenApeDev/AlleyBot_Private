"""
Production-Ready AlleyBot Entry Point
Event-driven architecture with DeepSeek + Grok-4.1-reasoning

Uses asyncio.run() with a clean async main that:
1. Initializes + starts the Telegram Application
2. Starts the updater polling
3. Starts the event runner + autonomous brain as background tasks
4. Keeps everything running via asyncio.gather()
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Configure logging to suppress httpx HTTP spam
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)
# Suppress httpx HTTP request logging
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.event_runner import EventRunner
from src.agents.session_manager import SessionManager
from src.config.models import ModelRouter
from src.skills.skill_loader import SkillLoader


async def _run_production(core):
    """Async main — all startup happens inside a running event loop."""

    print("\n" + "="*60)
    print("🚀 PRODUCTION ALLEYBOT - EVENT-DRIVEN MODE")
    print("="*60 + "\n")

    # --- Build components ---
    session_manager = SessionManager()
    print("✅ Session Manager initialized")
    model_router = ModelRouter()
    print("✅ Model Router initialized")
    skill_loader = SkillLoader()
    print("✅ Skill Loader initialized")
    event_runner = EventRunner(core)
    event_runner.session_manager = session_manager
    event_runner.model_router = model_router
    print("✅ Event Runner initialized")

    # --- Get Telegram Application ---
    telegram_plugin = None
    if hasattr(core, 'plugin_manager') and 'telegram' in core.plugin_manager.plugins:
        telegram_plugin = core.plugin_manager.plugins['telegram']

    if not telegram_plugin or not telegram_plugin.application:
        print("❌ Telegram plugin not available — cannot start")
        return

    app = telegram_plugin.application
    total_handlers = sum(len(h) for h in app.handlers.values())
    print(f"📱 Telegram: {total_handlers} handlers registered")

    # --- Start background tasks ---
    # Event runner
    event_runner_task = asyncio.create_task(event_runner.start(), name="event_runner")
    print("✅ Event Runner started")

    # Autonomous brain
    try:
        from src.agentic.autonomous_startup import get_autonomous_startup
        autonomous_startup = get_autonomous_startup(core, core.plugin_manager)
        brain_task = asyncio.create_task(autonomous_startup.initialize(), name="autonomous_brain")
        print("✅ Autonomous startup scheduled")
    except Exception as e:
        print(f"⚠️  Autonomous startup error: {e}")
        brain_task = None

    # Startup notification (sync HTTP in thread)
    try:
        if hasattr(telegram_plugin, '_send_startup_notification'):
            asyncio.get_event_loop().run_in_executor(
                None, telegram_plugin._send_startup_notification
            )
    except Exception:
        pass

    telegram_task = asyncio.create_task(
        telegram_plugin._start_polling_async(),
        name="telegram_polling",
    )
    print("✅ Telegram polling task scheduled")

    telegram_ready = False
    try:
        if hasattr(telegram_plugin, 'wait_until_polling_started'):
            telegram_ready = await telegram_plugin.wait_until_polling_started(timeout=15.0)
    except Exception as e:
        print(f"⚠️  Telegram polling readiness check failed: {e}")

    if telegram_ready:
        print("\n🎉 All systems GO — Telegram commands are live!\n")
    else:
        print("\n⚠️  Telegram polling was scheduled but did not confirm readiness yet.\n")

    # --- Keep running until interrupted ---
    try:
        # Simple keepalive — the event loop is running, polling is active,
        # background tasks are scheduled. Just sleep forever.
        while True:
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass
    finally:
        # --- Shutdown ---
        print("🧹 Shutting down...")
        telegram_plugin.is_running = False
        telegram_task.cancel()
        event_runner.stop()
        try:
            await telegram_task
        except asyncio.CancelledError:
            pass
        print("✅ Shutdown complete")


def run_production_mode(core):
    """Entry point called from alleybot_core.py (synchronous)."""
    asyncio.run(_run_production(core))


if __name__ == "__main__":
    print("⚠️  This module should be imported and run through alleybot_core.py")
    print("Usage: python run_alleybot.py autonomous")
