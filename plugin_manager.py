#!/usr/bin/env python3
"""
Plugin Manager - Dynamic loading and management of AlleyBot plugins
"""
import json
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, Callable

class AlleyBotPlugin:
    """Base class for all AlleyBot plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
        self.initialized = False
    
    def initialize(self, api, core):
        """Initialize plugin with API and core access"""
        self.api = api
        self.core = core
        self.initialized = True
    
    def get_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Return scheduled tasks for this plugin"""
        return {}
    
    def get_commands(self) -> Dict[str, Callable]:
        """Return CLI commands for this plugin"""
        return {}
    
    def get_endpoints(self) -> Dict[str, Callable]:
        """Return web endpoints for this plugin"""
        return {}
    
    def cleanup(self):
        """Cleanup resources"""
        pass


class PluginManager:
    """Manages loading and execution of plugins"""
    
    def __init__(self, plugin_dir: str = 'plugins'):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, AlleyBotPlugin] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.commands: Dict[str, Callable] = {}
        self.endpoints: Dict[str, Callable] = {}
    
    def load_plugins(self, config_file: str, api, core):
        """Load all enabled plugins from configuration"""
        config_path = Path(config_file)
        
        # Create default config if it doesn't exist
        if not config_path.exists():
            self._create_default_config(config_path)
        
        # Load configuration
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Load each enabled plugin
        for plugin_name, plugin_config in config.items():
            if plugin_config.get('enabled', True):
                self.load_plugin(plugin_name, plugin_config, api, core)
            else:
                print(f"⏸️  Plugin disabled: {plugin_name}")
    
    def _create_default_config(self, config_path: Path):
        """Create default plugin configuration"""
        default_config = {
            "intelligence": {
                "enabled": True,
                "config": {
                    "engagement_threshold": 40,
                    "learning_rate": 0.1
                }
            },
            "engagement": {
                "enabled": True,
                "config": {
                    "comment_support": True,
                    "own_post_upvoting": True
                }
            },
            "content": {
                "enabled": True,
                "config": {
                    "auto_posting": True,
                    "post_interval": 2
                }
            },
            "analytics": {
                "enabled": True,
                "config": {
                    "dashboard_port": 7001,
                    "refresh_interval": 120
                }
            }
        }
        
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"📝 Created default plugin config: {config_path}")
    
    def load_plugin(self, plugin_name: str, plugin_config: Dict[str, Any], api, core):
        """Load individual plugin"""
        try:
            # Import plugin module
            if plugin_name == 'mcp':
                module_path = f'plugins.{plugin_name}.mcp_plugin'
            else:
                module_path = f'plugins.{plugin_name}.{plugin_name}'
            
            # Force reload to get latest version
            if module_path in sys.modules:
                module = importlib.reload(sys.modules[module_path])
            else:
                module = importlib.import_module(module_path)
            
            # Find plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, AlleyBotPlugin) and 
                    obj != AlleyBotPlugin):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                print(f"❌ No plugin class found in {plugin_name}")
                return
            
            # Initialize plugin
            plugin = plugin_class(plugin_config.get('config', {}))
            plugin.initialize(api, core)
            
            # Register plugin
            self.plugins[plugin_name] = plugin
            
            # Register tasks, commands, and endpoints
            self.tasks.update(plugin.get_tasks())
            self.commands.update(plugin.get_commands())
            self.endpoints.update(plugin.get_endpoints())
            
            print(f"✅ Loaded plugin: {plugin_name}")
            
        except ImportError as e:
            print(f"❌ Failed to import plugin {plugin_name}: {e}")
        except Exception as e:
            print(f"❌ Failed to load plugin {plugin_name}: {e}")
    
    def unload_plugin(self, plugin_name: str):
        """Unload a specific plugin"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            
            # Cleanup plugin
            if hasattr(plugin, 'cleanup'):
                plugin.cleanup()
            
            # Remove from registries
            del self.plugins[plugin_name]
            
            # Remove tasks, commands, and endpoints
            tasks_to_remove = []
            for task_name, task_config in self.tasks.items():
                if hasattr(task_config.get('function'), '__self__') and \
                   task_config['function'].__self__ == plugin:
                    tasks_to_remove.append(task_name)
            
            for task_name in tasks_to_remove:
                del self.tasks[task_name]
            
            commands_to_remove = []
            for command_name, command_func in self.commands.items():
                if hasattr(command_func, '__self__') and command_func.__self__ == plugin:
                    commands_to_remove.append(command_name)
            
            for command_name in commands_to_remove:
                del self.commands[command_name]
            
            endpoints_to_remove = []
            for endpoint_name, endpoint_func in self.endpoints.items():
                if hasattr(endpoint_func, '__self__') and endpoint_func.__self__ == plugin:
                    endpoints_to_remove.append(endpoint_name)
            
            for endpoint_name in endpoints_to_remove:
                del self.endpoints[endpoint_name]
            
            print(f"🗑️  Unloaded plugin: {plugin_name}")
        else:
            print(f"❌ Plugin not found: {plugin_name}")
    
    def reload_plugin(self, plugin_name: str, plugin_config: Dict[str, Any], api, core):
        """Reload a plugin"""
        if plugin_name in self.plugins:
            self.unload_plugin(plugin_name)
        self.load_plugin(plugin_name, plugin_config, api, core)
    
    def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        """Get information about a specific plugin"""
        if plugin_name not in self.plugins:
            return {"error": "Plugin not found"}
        
        plugin = self.plugins[plugin_name]
        return {
            "name": plugin.name,
            "initialized": plugin.initialized,
            "config": plugin.config,
            "tasks": len([t for t in self.tasks.keys() if hasattr(self.tasks[t].get('function'), '__self__') and self.tasks[t]['function'].__self__ == plugin]),
            "commands": len([c for c in self.commands.keys() if hasattr(self.commands[c], '__self__') and self.commands[c].__self__ == plugin]),
            "endpoints": len([e for e in self.endpoints.keys() if hasattr(self.endpoints[e], '__self__') and self.endpoints[e].__self__ == plugin])
        }
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List all loaded plugins with their info"""
        return {name: self.get_plugin_info(name) for name in self.plugins.keys()}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get plugin manager statistics"""
        return {
            "total_plugins": len(self.plugins),
            "total_tasks": len(self.tasks),
            "total_commands": len(self.commands),
            "total_endpoints": len(self.endpoints),
            "plugins": list(self.plugins.keys())
        }
