"""
AlleyBot Plugin Manager with Hot-Loading Support

This module provides dynamic plugin loading, unloading, and reloading
without restarting the agent.

Features:
- Load plugins from filesystem at runtime
- Hot-swap plugin implementations
- Graceful error handling (broken plugins don't crash system)
- Configuration-driven plugin activation
- Integration with SyMod for unified world model

See SOP.md for architecture details.
"""

import os
import json
import sys
import importlib
import importlib.util
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
from datetime import datetime

from plugins.base_plugin import BasePlugin, PluginRegistry

logger = logging.getLogger(__name__)


@dataclass
class PluginLoadResult:
    """Result of plugin load operation"""
    success: bool
    plugin_name: str
    error_message: Optional[str] = None
    previous_version: Optional[str] = None
    loaded_at: datetime = None
    
    def __post_init__(self):
        if self.loaded_at is None:
            self.loaded_at = datetime.now()


class PluginManager:
    """
    Central plugin manager with hot-loading capabilities.
    
    Responsibilities:
    1. Discover plugins from plugins/ directory
    2. Load/unload plugins at runtime
    3. Route events from EventLoop to appropriate plugins
    4. Route actions from Planner to appropriate plugins
    5. Maintain registry of active plugins
    
    Usage:
        pm = PluginManager(core, symod, agi_kernel)
        
        # Load from config
        pm.load_from_config('plugins.json')
        
        # Hotload a plugin
        result = pm.load_plugin('moltx', config={'api_key': 'xxx'})
        
        # Unload
        pm.unload_plugin('moltx')
        
        # Reload (hot-swap)
        pm.reload_plugin('moltx')
    """
    
    def __init__(self, core=None, symod=None, agi_kernel=None):
        """
        Initialize plugin manager.
        
        Args:
            core: AlleyBot core reference
            symod: SyMod core manager
            agi_kernel: AGI kernel reference
        """
        self.core = core
        self.symod = symod
        self.agi_kernel = agi_kernel
        
        # Active plugin instances
        self._plugins: Dict[str, BasePlugin] = {}
        
        # Plugin configurations
        self._configs: Dict[str, Dict] = {}
        
        # Plugin load timestamps
        self._load_times: Dict[str, datetime] = {}
        
        # Plugin load history for rollback
        self._load_history: Dict[str, List[str]] = {}  # name -> [paths]
        
        # Plugins directory
        self._plugins_dir = Path('plugins')
        
        logger.info("🔌 PluginManager initialized")
    
    # === Discovery ===
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in plugins/ directory.
        
        Returns:
            List of plugin names that can be loaded
        """
        available = []
        
        if not self._plugins_dir.exists():
            logger.warning(f"⚠️ Plugins directory not found: {self._plugins_dir}")
            return available
        
        for item in self._plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                # Check for plugin marker (either v1 or v2)
                init_file = item / '__init__.py'
                main_file = item / f"{item.name}.py"
                v2_file = item / f"{item.name}_v2.py"
                
                if init_file.exists() or main_file.exists() or v2_file.exists():
                    available.append(item.name)
        
        logger.info(f"🔍 Discovered {len(available)} plugins: {available}")
        return available
    
    # === Loading ===
    
    def load_plugin(self, name: str, config: Dict[str, Any] = None) -> PluginLoadResult:
        """
        Load a plugin by name.
        
        Args:
            name: Plugin name (directory name in plugins/)
            config: Plugin configuration dict
        
        Returns:
            PluginLoadResult with success/failure info
        """
        config = config or {}
        
        # Check if already loaded
        if name in self._plugins:
            logger.warning(f"⚠️ Plugin '{name}' already loaded, use reload_plugin() instead")
            return PluginLoadResult(
                success=False,
                plugin_name=name,
                error_message="Already loaded, use reload"
            )
        
        try:
            # Find plugin file
            plugin_path = self._find_plugin_file(name)
            if not plugin_path:
                return PluginLoadResult(
                    success=False,
                    plugin_name=name,
                    error_message=f"Plugin '{name}' not found in {self._plugins_dir}"
                )
            
            # Load module
            plugin_class = self._load_plugin_class(name, plugin_path)
            if not plugin_class:
                return PluginLoadResult(
                    success=False,
                    plugin_name=name,
                    error_message=f"Could not load plugin class from {plugin_path}"
                )
            
            # Instantiate
            instance = plugin_class(config)
            
            # Setup with dependencies
            instance.setup(self, self.symod, self.agi_kernel)
            
            # Register with SyMod
            if self.symod:
                self.symod.register_plugin(
                    name,
                    {
                        'description': instance.description,
                        'channels': instance.supported_channels,
                        'version': instance.version
                    }
                )
            
            # Store
            self._plugins[name] = instance
            self._configs[name] = config
            self._load_times[name] = datetime.now()
            
            # Track for rollback
            if name not in self._load_history:
                self._load_history[name] = []
            self._load_history[name].append(str(plugin_path))
            
            logger.info(f"✅ Plugin '{name}' loaded successfully")
            
            return PluginLoadResult(
                success=True,
                plugin_name=name,
                loaded_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to load plugin '{name}': {e}")
            return PluginLoadResult(
                success=False,
                plugin_name=name,
                error_message=str(e)
            )
    
    def _find_plugin_file(self, name: str) -> Optional[Path]:
        """Find the main plugin file for a plugin"""
        plugin_dir = self._plugins_dir / name
        
        if not plugin_dir.exists():
            return None
        
        # Try v2 first (new architecture)
        v2_file = plugin_dir / f"{name}_v2.py"
        if v2_file.exists():
            return v2_file
        
        # Try standard name
        main_file = plugin_dir / f"{name}.py"
        if main_file.exists():
            return main_file
        
        # Try __init__.py (package style)
        init_file = plugin_dir / '__init__.py'
        if init_file.exists():
            return init_file
        
        return None
    
    def _load_plugin_class(self, name: str, path: Path) -> Optional[Type[BasePlugin]]:
        """Load plugin class from file"""
        try:
            # Create module spec
            module_name = f"plugins.{name}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            
            if not spec or not spec.loader:
                return None
            
            # Load module
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find plugin class
            # Try common naming patterns
            class_names = [
                f"{name.title()}Plugin",
                f"{name.title()}V2Plugin",
                "Plugin",
                "AlleyBotPlugin"
            ]
            
            for class_name in class_names:
                if hasattr(module, class_name):
                    cls = getattr(module, class_name)
                    if issubclass(cls, BasePlugin):
                        return cls
            
            # Search all classes in module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BasePlugin) and 
                    attr is not BasePlugin):
                    return attr
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error loading plugin class: {e}")
            return None
    
    # === Unloading ===
    
    def unload_plugin(self, name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            name: Plugin name
        
        Returns:
            True if unloaded, False if not found
        """
        if name not in self._plugins:
            logger.warning(f"⚠️ Plugin '{name}' not loaded")
            return False
        
        try:
            # Call cleanup hook
            plugin = self._plugins[name]
            plugin.on_unload()
            
            # Remove from registry
            del self._plugins[name]
            del self._configs[name]
            del self._load_times[name]
            
            # Unregister from SyMod
            if self.symod and name in self.symod.registered_plugins:
                del self.symod.registered_plugins[name]
            
            logger.info(f"🛑 Plugin '{name}' unloaded")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error unloading plugin '{name}': {e}")
            return False
    
    # === Hot Reloading ===
    
    def reload_plugin(self, name: str) -> PluginLoadResult:
        """
        Hot-reload a plugin (unload + load with same config).
        
        This is the primary method for code updates without restart.
        
        Args:
            name: Plugin name
        
        Returns:
            PluginLoadResult
        """
        if name not in self._plugins:
            return PluginLoadResult(
                success=False,
                plugin_name=name,
                error_message="Plugin not loaded, cannot reload"
            )
        
        # Save config
        config = self._configs.get(name, {})
        
        # Unload
        if not self.unload_plugin(name):
            return PluginLoadResult(
                success=False,
                plugin_name=name,
                error_message="Unload failed during reload"
            )
        
        # Force module reload by clearing cache
        module_name = f"plugins.{name}"
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        # Reload
        return self.load_plugin(name, config)
    
    def load_from_config(self, config_path: str = 'plugins.json') -> Dict[str, PluginLoadResult]:
        """
        Load plugins from JSON configuration file.
        
        Config format:
        {
            "moltx": {
                "enabled": true,
                "api_key": "xxx",
                "config": {}
            },
            "telegram": {
                "enabled": true,
                "config": {}
            }
        }
        
        Args:
            config_path: Path to JSON config file
        
        Returns:
            Dict of plugin names to load results
        """
        results = {}
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            logger.warning(f"⚠️ Config file not found: {config_path}")
            return results
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in {config_path}: {e}")
            return results
        
        for plugin_name, plugin_config in config.items():
            if not plugin_config.get('enabled', True):
                logger.info(f"⏭️ Plugin '{plugin_name}' disabled in config")
                continue
            
            result = self.load_plugin(plugin_name, plugin_config)
            results[plugin_name] = result
        
        return results
    
    def save_config(self, config_path: str = 'plugins.json') -> bool:
        """
        Save current plugin configuration to file.
        
        Args:
            config_path: Path to save config
        
        Returns:
            True if saved successfully
        """
        config = {}
        for name, plugin in self._plugins.items():
            config[name] = {
                'enabled': plugin.enabled,
                **self._configs.get(name, {})
            }
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save config: {e}")
            return False
    
    # === Accessors ===
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get loaded plugin by name"""
        return self._plugins.get(name)
    
    def get_plugins_by_channel(self, channel: str) -> List[BasePlugin]:
        """Get all plugins that support a channel"""
        return [
            plugin for plugin in self._plugins.values()
            if channel in plugin.supported_channels
        ]
    
    def list_loaded(self) -> List[str]:
        """List names of all loaded plugins"""
        return list(self._plugins.keys())
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall plugin manager status"""
        return {
            'loaded_count': len(self._plugins),
            'loaded_plugins': self.list_loaded(),
            'discovered_plugins': self.discover_plugins(),
            'plugins': {
                name: plugin.get_status()
                for name, plugin in self._plugins.items()
            }
        }
    
    # === Event Routing ===
    
    async def route_event(self, event_type: str, channel: str, 
                         payload: Dict[str, Any]) -> None:
        """
        Route an event to all plugins supporting the channel.
        
        Called by EventLoop.
        
        Args:
            event_type: Type of event
            channel: Source channel
            payload: Event data
        """
        from plugins.base_plugin import PluginEvent
        
        event = PluginEvent(
            event_type=event_type,
            channel=channel,
            source_id=payload.get('id', 'unknown'),
            payload=payload
        )
        
        # Route to plugins
        plugins = self.get_plugins_by_channel(channel)
        
        for plugin in plugins:
            if not plugin.enabled:
                continue
            
            try:
                await plugin.on_event(event, self.symod)
            except Exception as e:
                logger.error(f"❌ Plugin '{plugin.name}' failed to handle event: {e}")
                # Don't crash - other plugins should still process
    
    # === Action Routing ===
    
    async def execute_action(self, plugin_name: str, 
                            action_type: str,
                            target_id: Optional[str] = None,
                            content: Optional[str] = None,
                            metadata: Dict = None) -> dict:
        """
        Execute an action on a specific plugin.
        
        Called by Planner after SyMod validation.
        
        Args:
            plugin_name: Target plugin
            action_type: Type of action
            target_id: Target identifier
            content: Content (for messages/posts)
            metadata: Additional action data
        
        Returns:
            Action execution result
        """
        from plugins.base_plugin import PluginAction, ActionResult
        
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return {'success': False, 'error': f"Plugin '{plugin_name}' not found"}
        
        if not plugin.enabled:
            return {'success': False, 'error': f"Plugin '{plugin_name}' disabled"}
        
        action = PluginAction(
            action_type=action_type,
            target_id=target_id,
            content=content,
            metadata=metadata or {}
        )
        
        try:
            result = await plugin.execute_action(action, self.symod)
            return {
                'success': result.success,
                'action_type': result.action_type,
                'target_id': result.target_id,
                'error': result.error_message,
                'data': result.response_data
            }
        except Exception as e:
            logger.error(f"❌ Action execution failed on '{plugin_name}': {e}")
            return {'success': False, 'error': str(e)}


# Singleton instance
_plugin_manager_instance: Optional[PluginManager] = None


def get_plugin_manager(core=None, symod=None, agi_kernel=None) -> PluginManager:
    """Get or create plugin manager singleton"""
    global _plugin_manager_instance
    if _plugin_manager_instance is None:
        _plugin_manager_instance = PluginManager(core, symod, agi_kernel)
    return _plugin_manager_instance
