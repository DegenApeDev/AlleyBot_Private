"""
Skill Executor
Execute skill instructions with tool access and script execution.

SKILL COMPOSITION: Skills can call other skills via self.call_skill() during execution.
This enables complex multi-skill workflows and emergent capabilities.
"""
import os
import subprocess
import sys
import importlib
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from plugin_manager import AlleyBotPlugin


class SkillExecutorMixin:
    """Execute skill instructions and bundled scripts with composition support"""

    def __init__(self, config):
        self.config = config
        self.execution_log: List[Dict[str, Any]] = []
        self.max_script_runtime = config.get('max_script_runtime', 30)
        self._composition_stack: List[str] = []  # Track nested skill calls
        self._max_composition_depth = 5  # Prevent infinite recursion
        self._composition_results: Dict[str, Any] = {}

    def execute_skill(self, skill_name: str, instruction: str) -> str:
        """Execute a skill with given instruction."""
        # Placeholder for skill execution logic
        self.execution_log.append({
            "skill": skill_name,
            "instruction": instruction,
            "timestamp": datetime.now().isoformat()
        })
        return f"Executed skill {skill_name}: {instruction}"

    def call_skill(self, skill_name: str, instruction: str) -> str:
        """Compositional skill call (used during skill execution)."""
        if len(self._composition_stack) >= self._max_composition_depth:
            return f"Max composition depth exceeded calling {skill_name}"
        self._composition_stack.append(skill_name)
        try:
            result = self.execute_skill(skill_name, instruction)
            self._composition_results[skill_name] = result
            return result
        finally:
            self._composition_stack.pop()


class ActionRouter(SkillExecutorMixin):
    """Routes actions to skills, tools, or plugins."""

    def __init__(self, config):
        super().__init__(config)
        self._loaded_plugins: Dict[str, AlleyBotPlugin] = {}

    def unknown_handler(self, plugin_name: str, command_name: str, args: List[str], *, plugin: Optional[AlleyBotPlugin] = None, commands: Optional[Dict[str, callable]] = None) -> str:
        """Fallback handler for unknown plugin actions."""
        msg = f"Unknown action '{plugin_name}:{command_name}'"
        if commands is not None:
            avail = [cmd for cmd in commands if callable(commands[cmd])]
            if avail:
                msg += f"\nAvailable commands in '{plugin_name}': {', '.join(avail)}"
        if plugin_name not in self._loaded_plugins:
            msg += "\nPlugin not available (not found or failed to load)."
        else:
            avail_plugins = sorted(self._loaded_plugins.keys())
            if avail_plugins:
                msg += f"\nLoaded plugins: {', '.join(avail_plugins)}"
        print(f"Falling back to unknown_handler for {plugin_name}:{command_name} {args}")
        return msg

    def _execute_via_plugin(self, plugin_name: str, command_name: str, args: List[str]) -> str:
        """Dynamically execute a plugin command with loading and error recovery."""
        print(f"Routing to plugin: {plugin_name}:{command_name} {args}")
        if plugin_name not in self._loaded_plugins:
            try:
                module_path = f"plugins.{plugin_name}.{plugin_name}"
                module = importlib.import_module(module_path)
                create_fn = getattr(module, "create_plugin", None)
                if not callable(create_fn):
                    return self.unknown_handler(plugin_name, command_name, args)
                plugin_instance = create_fn(self.config)
                if not isinstance(plugin_instance, AlleyBotPlugin):
                    return self.unknown_handler(plugin_name, command_name, args)
                self._loaded_plugins[plugin_name] = plugin_instance
                print(f"Loaded plugin: {plugin_name}")
            except ImportError:
                print(f"Plugin '{plugin_name}' not found. Ensure plugins/{plugin_name}/{plugin_name}.py exists.")
                return self.unknown_handler(plugin_name, command_name, args)
            except Exception as e:
                print(f"Failed to load plugin '{plugin_name}': {str(e)}")
                return self.unknown_handler(plugin_name, command_name, args)

        plugin = self._loaded_plugins[plugin_name]
        try:
            commands = plugin.get_commands()
            command_fn = commands.get(command_name)
            if command_fn is None or not callable(command_fn):
                return self.unknown_handler(plugin_name, command_name, args, plugin=plugin, commands=commands)
            result = command_fn(args)
            return str(result) if result is not None else "Command executed successfully (no output)."
        except Exception as e:
            error_msg = f"Error executing '{plugin_name}:{command_name}': {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return error_msg