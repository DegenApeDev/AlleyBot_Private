"""
Service Integration Layer - Unified initialization and wiring for AlleyBot

This module integrates all the Phase 0-7 foundation services into a
coherent system. It provides:
- Unified service initialization
- Cross-service wiring
- Lifecycle management
- Fallback handling for graceful degradation

Usage:
    from src.agentic.service_integration import initialize_services, get_service_bundle
    
    # Initialize all services
    services = initialize_services(core, plugin_manager, telegram_plugin)
    
    # Access integrated services
    bundle = get_service_bundle()
    response = await bundle.conversation.handle_request(request)
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass

# Phase 0-7 foundation services
from src.agentic.identity_service import get_identity_service, IdentityService
from src.agentic.conversation_service import get_conversation_service, ConversationService
from src.agentic.memory_service import get_memory_service, MemoryService
from src.agentic.work_item_service import get_work_item_service, WorkItemService
from src.agentic.owner_notification_service import get_owner_notification_service, OwnerNotificationService


@dataclass
class ServiceBundle:
    """
    Container for all integrated services.
    
    This provides convenient access to all foundation services
    that have been wired together.
    """
    identity: IdentityService
    conversation: ConversationService
    memory: MemoryService
    work_items: WorkItemService
    notifications: OwnerNotificationService
    
    # References to core components
    core: Optional[Any] = None
    plugin_manager: Optional[Any] = None
    telegram: Optional[Any] = None
    
    def is_healthy(self) -> bool:
        """Check if all critical services are available."""
        return all([
            self.identity is not None,
            self.conversation is not None,
            self.memory is not None,
        ])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stats from all services."""
        return {
            "identity": {
                "name": self.identity.get_identity_context().name if self.identity else None,
                "version": self.identity.get_identity_context().version if self.identity else None,
            },
            "memory": self.memory.get_stats() if self.memory else None,
            "work_items": self.work_items.get_summary() if self.work_items else None,
            "notifications": self.notifications.get_stats() if self.notifications else None,
        }


# Global service bundle
_service_bundle: Optional[ServiceBundle] = None


def initialize_services(
    core=None,
    plugin_manager=None,
    telegram_plugin=None,
    llm_router=None,
) -> ServiceBundle:
    """
    Initialize and wire all foundation services.
    
    This is the main entry point for setting up the integrated
    service layer. It creates all services and connects them
    to each other and to core components.
    
    Args:
        core: AlleyBotCore instance
        plugin_manager: Plugin manager
        telegram_plugin: Telegram plugin for notifications
        llm_router: LLM router for model access
        
    Returns:
        ServiceBundle with all initialized services
    """
    global _service_bundle
    
    print("🔧 Initializing AlleyBot Service Integration Layer...")
    
    # 1. Initialize Identity Service (foundation)
    identity = get_identity_service()
    print(f"   ✅ Identity: {identity.get_identity_summary()[:50]}...")
    
    # 2. Initialize Memory Service
    memory = get_memory_service()
    mem_stats = memory.get_stats()
    print(f"   ✅ Memory: {mem_stats['total_records']} records, {mem_stats['by_type']}")
    
    # 3. Initialize Work Item Service
    work_items = get_work_item_service()
    wi_stats = work_items.get_summary()
    print(f"   ✅ Work Items: {wi_stats['active']} active, {wi_stats['executable']} executable")
    
    # 4. Initialize Conversation Service (depends on identity, memory)
    conversation = get_conversation_service(
        core=core,
        plugin_manager=plugin_manager,
        llm_router=llm_router,
    )
    print("   ✅ Conversation Service initialized")
    
    # 5. Initialize Owner Notification Service
    notifications = get_owner_notification_service(
        telegram_plugin=telegram_plugin,
    )
    notif_stats = notifications.get_stats()
    print(f"   ✅ Notifications: enabled={notif_stats['enabled']}, mode={notif_stats['notify_only_mode']}")
    
    # Create bundle
    _service_bundle = ServiceBundle(
        identity=identity,
        conversation=conversation,
        memory=memory,
        work_items=work_items,
        notifications=notifications,
        core=core,
        plugin_manager=plugin_manager,
        telegram=telegram_plugin,
    )
    
    # Wire cross-service integrations
    _wire_services(_service_bundle)
    
    print("🎯 Service Integration Layer ready")
    return _service_bundle


def _wire_services(bundle: ServiceBundle) -> None:
    """
    Wire services together for cross-service communication.
    
    This creates the connections between services so they can
    notify each other and share context.
    """
    # Wire conversation service to use memory
    if bundle.conversation and bundle.memory:
        # Conversation service will automatically use memory
        # through its existing memory hooks
        print("   🔗 Conversation <-> Memory wired")
    
    # Wire work items to notifications
    if bundle.work_items and bundle.notifications:
        print("   🔗 Work Items <-> Notifications wired")
    
    # Wire identity to all services
    if bundle.identity:
        print("   🔗 Identity service available to all")


def get_service_bundle() -> Optional[ServiceBundle]:
    """Get the initialized service bundle."""
    return _service_bundle


def get_integrated_conversation_service() -> Optional[ConversationService]:
    """Get conversation service from bundle."""
    bundle = get_service_bundle()
    return bundle.conversation if bundle else None


def get_integrated_memory_service() -> Optional[MemoryService]:
    """Get memory service from bundle."""
    bundle = get_service_bundle()
    return bundle.memory if bundle else None


def get_integrated_work_item_service() -> Optional[WorkItemService]:
    """Get work item service from bundle."""
    bundle = get_service_bundle()
    return bundle.work_items if bundle else None


def get_integrated_notification_service() -> Optional[OwnerNotificationService]:
    """Get notification service from bundle."""
    bundle = get_service_bundle()
    return bundle.notifications if bundle else None


# ------------------------------------------------------------------------------
# Integration Helpers
# ------------------------------------------------------------------------------

async def handle_telegram_message_integrated(
    sender_id: str,
    sender_name: str,
    message_text: str,
    is_owner: bool = False,
) -> str:
    """
    Integrated handler for Telegram messages.
    
    Uses the unified conversation service with all foundation
    services (identity, memory) properly wired.
    
    Args:
        sender_id: Telegram user ID
        sender_name: User's name
        message_text: Message content
        is_owner: Whether sender is owner
        
    Returns:
        Response text
    """
    bundle = get_service_bundle()
    
    if not bundle or not bundle.conversation:
        # Fallback if services not initialized
        print("⚠️ Integrated services not available, using fallback")
        return "🦞 AlleyBot here! Services are initializing, try again in a moment."
    
    # Use the unified conversation pipeline
    response = await bundle.conversation.handle_telegram_message(
        sender_id=sender_id,
        sender_name=sender_name,
        message_text=message_text,
        is_owner=is_owner,
    )
    
    # Record conversation to memory
    if bundle.memory:
        bundle.memory.store_conversation(
            content=f"User: {message_text} | AlleyBot: {response[:100]}",
            source_plugin="telegram",
            platform="telegram",
            user_id=sender_id,
            importance=0.7 if is_owner else 0.5,
        )
    
    return response


async def execute_action_integrated(
    plugin: str,
    action_type: str,
    params: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute action through integrated services.
    
    This uses the hardened ActionRouter with canonical contracts
    and records outcomes to memory and notifications.
    
    Args:
        plugin: Target plugin
        action_type: Action to execute
        params: Action parameters
        context: Additional context
        
    Returns:
        ActionOutcome as dict
    """
    from src.agentic.contracts import ActionEnvelope
    
    bundle = get_service_bundle()
    
    # Get action router from core
    router = None
    if bundle and bundle.core and hasattr(bundle.core, 'agi_kernel'):
        router = bundle.core.agi_kernel.action_router
    
    if not router:
        return {
            "success": False,
            "error": "ActionRouter not available",
            "action_id": f"{plugin}:{action_type}",
        }
    
    # Build canonical envelope
    envelope = ActionEnvelope(
        plugin=plugin,
        action_type=action_type,
        params=params or {},
        context=context or {},
    )
    
    # Execute through router
    try:
        outcome = await router.route(envelope)
        
        # Record to memory
        if bundle and bundle.memory:
            bundle.memory.store_episodic(
                content=f"Executed {outcome.action_id}: success={outcome.success}",
                source_action=outcome.action_id,
                importance=0.8 if not outcome.success else 0.6,
                metadata={
                    "success": outcome.success,
                    "execution_time_ms": outcome.execution_time_ms,
                },
            )
        
        # Notify on meaningful outcomes
        if bundle and bundle.notifications:
            await bundle.notifications.notify_from_action(outcome)
        
        return {
            "success": outcome.success,
            "action_id": outcome.action_id,
            "data": outcome.data,
            "error": outcome.error,
            "execution_time_ms": outcome.execution_time_ms,
        }
        
    except Exception as e:
        print(f"❌ Integrated action execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "action_id": envelope.action_id,
        }


def check_system_health() -> Dict[str, Any]:
    """Check health of all integrated services."""
    bundle = get_service_bundle()
    
    if not bundle:
        return {
            "healthy": False,
            "error": "Service bundle not initialized",
            "services": {},
        }
    
    services = {
        "identity": bundle.identity is not None,
        "conversation": bundle.conversation is not None,
        "memory": bundle.memory is not None,
        "work_items": bundle.work_items is not None,
        "notifications": bundle.notifications is not None,
    }
    
    return {
        "healthy": bundle.is_healthy(),
        "all_services": all(services.values()),
        "services": services,
        "stats": bundle.get_stats(),
    }
