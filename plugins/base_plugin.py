"""
AlleyBot Base Plugin Interface

All plugins MUST inherit from BasePlugin and implement the interface below.
This ensures:
1. Consistent event handling across all platforms
2. SyMod integration for all observations and actions
3. Hot-loading capability
4. No duplicate logic in plugins

See SOP.md and WORLD_MODEL.md for architecture details.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PluginEvent:
    """Normalized event from any platform"""
    event_type: str           # 'post', 'message', 'transaction', 'price_update', etc.
    channel: str              # 'moltx', 'telegram', 'onchain', etc.
    source_id: str            # ID from source platform
    payload: Dict[str, Any]   # Platform-specific data
    timestamp: datetime = field(default_factory=datetime.now)
    raw_data: Optional[Any] = None  # Original platform data (if needed)


@dataclass
class PluginAction:
    """Action to be executed by a plugin"""
    action_type: str          # 'like', 'reply', 'post', 'trade', 'alert', etc.
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    content: Optional[str] = None  # For replies, posts, messages
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # SyMod validation fields (populated by core)
    confidence: float = 0.0
    valid: bool = False
    justification: str = ""


@dataclass
class ActionResult:
    """Result of action execution"""
    success: bool
    action_type: str
    target_id: Optional[str] = None
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None
    timestamp: datetime = field(default_factory=datetime.now)


class BasePlugin(ABC):
    """
    Base class for all AlleyBot plugins.
    
    RULES (from SOP.md):
    1. Maximum 200 lines (excluding docstrings and imports)
    2. Only two public methods: on_event(), execute_action()
    3. No persistent state - use SyMod for state
    4. No direct LLM calls - use AGI kernel
    5. No own event loops - EventLoop calls on_event()
    
    Example minimal implementation:
    
        class MyPlugin(BasePlugin):
            name = "my_platform"
            supported_channels = ["my_platform"]
            
            async def on_event(self, event: PluginEvent, symod) -> None:
                # Normalize to observation
                observation = self._normalize(event)
                # Submit to SyMod
                symod.observe(observation)
            
            async def execute_action(self, action: PluginAction, symod) -> ActionResult:
                # Validate
                is_valid, reason = symod.validate_action(self.name, action)
                if not is_valid:
                    return ActionResult(success=False, action_type=action.action_type,
                                       error_message=reason)
                # Execute
                result = await self._execute(action)
                # Reflect
                outcome = self._create_outcome(action, result)
                symod.reflect(self.name, action, outcome)
                return result
    """
    
    # Plugin metadata - MUST be overridden by subclasses
    name: str = "base"                    # Unique plugin identifier
    supported_channels: List[str] = []   # Channels this plugin handles
    version: str = "1.0.0"
    description: str = "Base plugin interface"
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize plugin with configuration.
        
        Args:
            config: Plugin-specific configuration from plugins.json
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self._initialized = False
        
        # These are set by PluginManager after load
        self._plugin_manager = None
        self._symod = None
        self._agi_kernel = None
        
        logger.info(f"🔌 Plugin '{self.name}' initialized")
    
    @property
    def initialized(self) -> bool:
        """Whether plugin has been fully initialized by PluginManager"""
        return self._initialized
    
    def setup(self, plugin_manager, symod, agi_kernel) -> None:
        """
        Called by PluginManager after loading.
        
        Do NOT override this - use on_load() for custom setup.
        """
        self._plugin_manager = plugin_manager
        self._symod = symod
        self._agi_kernel = agi_kernel
        self._initialized = True
        
        # Call subclass hook
        self.on_load()
        
        logger.info(f"✅ Plugin '{self.name}' setup complete")
    
    def on_load(self) -> None:
        """
        Hook for subclass setup. Called after setup().
        
        Use this for:
        - API client initialization
        - Connection establishment
        - Resource allocation
        
        Do NOT start event loops here.
        """
        pass
    
    def on_unload(self) -> None:
        """
        Hook for cleanup before unload. Called by PluginManager.
        
        Use this for:
        - Closing connections
        - Flushing buffers
        - Cleanup resources
        """
        pass
    
    @abstractmethod
    async def on_event(self, event: PluginEvent, symod) -> None:
        """
        Handle incoming event from EventLoop.
        
        This is called by the central EventLoop when an event matching
        this plugin's channels arrives.
        
        Args:
            event: Normalized PluginEvent
            symod: SyMod core manager reference
        
        Implementation MUST:
        1. Normalize event.payload to SyModObservation
        2. Call symod.observe(observation)
        3. NOT make decisions (SyMod decides)
        
        Example:
            async def on_event(self, event, symod):
                obs = SyModObservation(
                    observation_type='post',
                    source_plugin=self.name,
                    data=event.payload
                )
                symod.observe(obs)
        """
        raise NotImplementedError("Plugin must implement on_event()")
    
    @abstractmethod
    async def execute_action(self, action: PluginAction, symod) -> ActionResult:
        """
        Execute an action requested by Planner.
        
        This is called by PluginManager when the Planner decides
        this plugin should execute an action.
        
        Args:
            action: PluginAction with all required fields
            symod: SyMod core manager reference
        
        Returns:
            ActionResult with execution outcome
        
        Implementation MUST:
        1. Validate via symod.validate_action() first
        2. Execute the action on the platform
        3. Create and reflect outcome via symod.reflect()
        4. Return ActionResult
        
        Example:
            async def execute_action(self, action, symod):
                # Validate
                is_valid, reason = symod.validate_action(self.name, action)
                if not is_valid:
                    return ActionResult(success=False, error_message=reason, ...)
                
                # Execute
                result = await self.api.like(action.target_id)
                
                # Reflect
                outcome = SyModActionOutcome(...)
                symod.reflect(self.name, action, outcome)
                
                return ActionResult(success=True, ...)
        """
        raise NotImplementedError("Plugin must implement execute_action()")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Return plugin status for monitoring.
        
        Override to add plugin-specific status.
        
        Returns:
            Dict with status info
        """
        return {
            'name': self.name,
            'enabled': self.enabled,
            'initialized': self._initialized,
            'channels': self.supported_channels,
            'version': self.version
        }
    
    def enable(self) -> None:
        """Enable plugin (can be called at runtime)"""
        self.enabled = True
        logger.info(f"✅ Plugin '{self.name}' enabled")
    
    def disable(self) -> None:
        """Disable plugin (can be called at runtime)"""
        self.enabled = False
        logger.info(f"🔴 Plugin '{self.name}' disabled")
    
    def _validate_action_type(self, action: PluginAction) -> bool:
        """Check if plugin supports this action type"""
        # Override in subclass if plugin has limited action support
        return True


class PluginRegistry:
    """
    Registry of available plugin classes.
    
    Plugins register themselves here using the @register decorator.
    """
    _plugins: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str):
        """Decorator to register a plugin class"""
        def decorator(plugin_class: type):
            if not issubclass(plugin_class, BasePlugin):
                raise TypeError(f"Plugin {name} must inherit from BasePlugin")
            cls._plugins[name] = plugin_class
            logger.info(f"📋 Registered plugin class: {name}")
            return plugin_class
        return decorator
    
    @classmethod
    def get(cls, name: str) -> Optional[type]:
        """Get plugin class by name"""
        return cls._plugins.get(name)
    
    @classmethod
    def list_plugins(cls) -> List[str]:
        """List all registered plugin names"""
        return list(cls._plugins.keys())
    
    @classmethod
    def clear(cls) -> None:
        """Clear registry (for testing)"""
        cls._plugins.clear()


# Convenience decorator
register_plugin = PluginRegistry.register
