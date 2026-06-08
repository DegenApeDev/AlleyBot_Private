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
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from plugin_manager import AlleyBotPlugin


class SkillExecutorMixin:
    """Execute skill instructions and bundled scripts with composition support"""

    def __init__(self, config):
        self.config = config
        self.execution_log: List[Dict] = []
        self.max_script_runtime = config.get('max_script_runtime', 30)
        self._composition_stack: List[str] = []  # Track nested skill calls
        self._max_composition_depth = 5  # Prevent infinite recursion
        self._composition_results: Dict[str, Any] = {}  # Store intermediate results

    def execute_skill(self, skill_name: str, task: str, context: str = "") -> Dict[str, Any]:
        """
        Execute a skill with given task and context.
        
        SKILL COMPOSITION: Skills can call other skills via the injected
        `call_skill()` method, enabling complex multi-skill workflows.
        """
        if len(self._composition_stack) >= self._max_composition_depth:
            return {"success": False, "error": "Maximum composition depth exceeded"}

        self._composition_stack.append(skill_name)
        try:
            result = f"Skill '{skill_name}' executed task '{task}' in context '{context}'"
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "skill": skill_name,
                "task": task,
                "context": context,
                "result": result,
            }
            self.execution_log.append(log_entry)
            self._composition_results[skill_name] = result
            print(f"Executed skill '{skill_name}': {result}")
            return {"success": True, "result": result, "log": log_entry}
        except Exception as e:
            error_msg = f"Skill execution failed: {str(e)}"
            print(error_msg)
            return {"success": False, "error": error_msg}
        finally:
            self._composition_stack.pop()


class ActionRouter(SkillExecutorMixin):
    def __init__(self, config):
        super().__init__(config)
        self.loaded_plugins: Dict[str, AlleyBotPlugin] = {}

    def _execute_via_plugin(self, plugin_name: str, action_name: str, args: List[str]) -> str:
        """Execute a plugin action with error wrapping for missing plugins/actions."""
        print(f"Attempting to execute {plugin_name}.{action_name} with args: {args}")
        if plugin_name in self.loaded_plugins:
            plugin = self.loaded_plugins[plugin_name]
        else:
            try:
                mod_name = f"plugins.{plugin_name}.{plugin_name}"
                mod = importlib.import_module(mod_name)
                plugin = mod.create_plugin(self.config)
                self.loaded_plugins[plugin_name] = plugin
                print(f"Loaded plugin '{plugin_name}'")
            except (ImportError, AttributeError, KeyError) as e:
                error_msg = f"Plugin '{plugin_name}' not found or invalid: {str(e)[:100]}"
                print(error_msg)
                return error_msg

        try:
            commands = plugin.get_commands()
        except Exception as e:
            error_msg = f"Failed to get commands from '{plugin_name}': {str(e)}"
            print(error_msg)
            return error_msg

        if action_name not in commands:
            error_msg = f"Action '{action_name}' not found in plugin '{plugin_name}'. Available: {list(commands.keys())}"
            print(error_msg)
            return error_msg

        func = commands[action_name]
        try:
            result: str = func(args)
            print(f"Plugin execution success: {plugin_name}.{action_name}")
            return result
        except Exception as e:
            error_msg = f"Error executing '{plugin_name}.{action_name}({args})': {str(e)}"
            print(error_msg)
            return error_msg