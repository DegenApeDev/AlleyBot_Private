"""
BrainEvents — Global event bridge for real-time brain triggers.

Any plugin can import this module and call trigger() to wake the brain
immediately, bypassing the periodic polling loop. The AutonomousBrain
registers itself at startup.
"""
import logging
from typing import Dict, Optional, Callable, List
from datetime import datetime

logger = logging.getLogger(__name__)

_brain_ref = None
_event_handlers: Dict[str, List[Callable]] = {}


def register_brain(brain_instance) -> None:
    global _brain_ref
    _brain_ref = brain_instance
    logger.info("📡 Brain registered for event triggers")


def unregister_brain() -> None:
    global _brain_ref
    _brain_ref = None


def trigger(event_type: str, data: Optional[Dict] = None) -> None:
    """Trigger an immediate brain cycle from any plugin or module.

    Args:
        event_type: Short identifier like 'telegram_message', 'trade_signal',
                   'onchain_tx', 'mention', 'owner_command'
        data: Optional payload with event details
    """
    event = {
        'type': event_type,
        'data': data or {},
        'timestamp': datetime.now().isoformat(),
    }
    logger.info(f"📡 Brain event: {event_type}")

    # Forward to registered brain
    if _brain_ref is not None:
        try:
            _brain_ref.trigger_event(event_type, data)
        except Exception as e:
            logger.debug(f"Brain event forward error: {e}")

    # Dispatch to local handlers
    for handler in _event_handlers.get(event_type, []):
        try:
            handler(event)
        except Exception as e:
            logger.debug(f"Event handler error: {e}")


def on(event_type: str, handler: Callable) -> None:
    """Register a handler for a specific event type."""
    if event_type not in _event_handlers:
        _event_handlers[event_type] = []
    _event_handlers[event_type].append(handler)
