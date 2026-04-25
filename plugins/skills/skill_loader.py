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
        self.skill_abbrevs: Dict[str, str] = {
            "c": "core",
            "co": "core",
            "core": "core",
            "uh": "unknown_handler",
            "unk": "unknown_handler",
            "unknown": "unknown_handler",
            "unknown_handler": "unknown_handler",
            "d": "debate",
            "deb": "debate",
            "debate": "debate",
        }
        self.command_aliases: Dict[str, str] = {}
        if not hasattr(self, 'commands'):
            self.commands: Dict[str, Callable[[List[str]], str]] = {}
        priority_skills = ['core', 'unknown_handler', 'debate']
        for skill_name in priority_skills:
            self.load_skill(skill_name)

    def resolve_skill_abbrev(self, name: str) -> str:
        """Resolve skill name abbreviation"""
        normalized = re.sub(r'^\s*!?\s*', '', name.lower().strip())
        return self.skill_abbrevs.get(normalized, normalized)

    def load_skill(self, name: str) -> Optional[AlleyBotPlugin]:
        full_name = self.resolve_skill_abbrev(name)
        if full_name != name:
            print(f"Abbreviation '{name}' resolved to skill '{full_name}'")
        if full_name in self.skills:
            return self.skills[full_name]
        skill_module_path = os.path.join(self.plugin_dir, full_name, f"{full_name}.py")
        if not os.path.exists(skill_module_path):
            print(f"Skill '{full_name}' (from '{name}') not found: {skill_module_path}")
            return None
        try:
            spec = importlib.util.spec_from_file_location(full_name, skill_module_path)
            if spec is None:
                raise ImportError("Could not create spec")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore
            plugin = module.create_plugin(self.config)
            self.skills[full_name] = plugin
            # Register commands
            commands = plugin.get_commands()
            for cmd_name, func in commands.items():
                self.commands[cmd_name] = func
                print(f"Registered command '{cmd_name}' from skill '{full_name}'")
            # Integrate aliases if from unknown_handler
            if full_name == 'unknown_handler':
                alias_mappings = getattr(module, 'ALIAS_MAPPINGS', {})
                self.command_aliases.update(alias_mappings)
                print(f"Loaded {len(alias_mappings)} aliases from unknown_handler")
            print(f"Successfully loaded skill '{full_name}' at {datetime.now()}")
            return plugin
        except Exception as e:
            print(f"Failed to load skill '{full_name}' ({name}): {e}")
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
        """Get handler with dynamic alias resolution and lazy loading"""
        resolved_cmd = self.resolve_command_alias(cmd)
        if resolved_cmd in self.commands:
            return self.commands[resolved_cmd]
        # Lazy load the skill corresponding to this command
        self.load_skill(resolved_cmd)
        # Re-resolve and check again after potential load and new aliases
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
        abbrev_count = len(self.skill_abbrevs)
        return f"Loaded skills ({len(self.skills)}):\n{skill_list}\nAliases: {alias_count}\nSkill abbrevs: {abbrev_count}"

    def unload_skill(self, name: str) -> bool:
        """Unload a skill (commands not removed)"""
        full_name = self.resolve_skill_abbrev(name)
        if full_name in self.skills:
            del self.skills[full_name]
            print(f"Unloaded skill '{full_name}'")
            return True
        print(f"Skill '{name}' ({full_name}) not loaded.")
        return False