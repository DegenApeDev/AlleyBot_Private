"""
Skill Loader and Activation
Progressive disclosure: load full skill only when needed
"""
import re
import os
import importlib
import importlib.util
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

try:
    from plugin_manager import AlleyBotPlugin
except ImportError:
    AlleyBotPlugin = object  # Fallback for typing


class SkillLoaderMixin:
    """Load and activate skills on demand"""

    def __init__(self, config):
        super().__init__(config)
        self.skill_dir: str = os.path.dirname(__file__)
        self.plugin_dir: str = os.path.dirname(self.skill_dir)
        self.skills: Dict[str, AlleyBotPlugin] = {}
        self.command_aliases: Dict[str, str] = {}
        if not hasattr(self, 'commands'):
            self.commands: Dict[str, Callable[[List[str]], str]] = {}
        self.load_skill('core')
        self.load_skill('unknown_handler')

    def load_skill(self, name: str) -> Optional[AlleyBotPlugin]:
        if name in self.skills:
            return self.skills[name]
        skill_module_path = os.path.join(self.plugin_dir, name, f"{name}.py")
        if not os.path.exists(skill_module_path):
            print(f"Skill '{name}' not found: {skill_module_path}")
            return None
        try:
            spec = importlib.util.spec_from_file_location(name, skill_module_path)
            if spec is None:
                raise ImportError("Could not create spec")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore
            plugin = module.create_plugin(self.config)
            self.skills[name] = plugin
            # Register commands
            commands = plugin.get_commands()
            for cmd_name, func in commands.items():
                self.commands[cmd_name] = func
                print(f"Registered command '{cmd_name}' from skill '{name}'")
            # Integrate aliases if from unknown_handler
            if name == 'unknown_handler':
                alias_mappings = getattr(module, 'ALIAS_MAPPINGS', {})
                self.command_aliases.update(alias_mappings)
                print(f"Loaded {len(alias_mappings)} aliases from unknown_handler")
            print(f"Successfully loaded skill '{name}' at {datetime.now()}")
            return plugin
        except Exception as e:
            print(f"Failed to load skill '{name}': {e}")
            return None

    def resolve_command_alias(self, cmd: str) -> str:
        """Resolve command via alias chain"""
        current = re.sub(r'^\s*!?\s*', '', cmd.lower().strip())
        visited: List[str] = []
        while current in self.command_aliases:
            if current in visited:
                print(f"Alias loop detected at '{current}'")
                break
            visited.append(current)
            current = self.command_aliases[current].lower()
        return current

    def get_command_handler(self, cmd: str) -> Optional[Callable[[List[str]], str]]:
        """Get handler with dynamic alias resolution"""
        resolved_cmd = self.resolve_command_alias(cmd)
        if resolved_cmd in self.commands:
            return self.commands[resolved_cmd]
        return None

    def list_loaded_skills(self) -> str:
        """List currently loaded skills"""
        if not self.skills:
            return "No skills loaded."
        skill_list = "\n".join([f"- {name}" for name in sorted(self.skills)])
        alias_count = len(self.command_aliases)
        return f"Loaded skills ({len(self.skills)}):\n{skill_list}\nAliases: {alias_count}"

    def unload_skill(self, name: str) -> bool:
        """Unload a skill (commands not removed)"""
        if name in self.skills:
            del self.skills[name]
            print(f"Unloaded skill '{name}'")
            return True
        return False