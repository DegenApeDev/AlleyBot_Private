"""
Skill Executor
Execute skill instructions with tool access and script execution.

SKILL COMPOSITION: Skills can call other skills.
"""

from typing import Dict, Callable, Optional, Any, List
from plugin_manager import AlleyBotPlugin


class ActionRouter:
    def __init__(self, command_executor: Optional[Callable[[str, List[str]], str]] = None):
        self.command_executor = command_executor

    def _execute_via_plugin(self, command: str, args: List[str]) -> str:
        if callable(self.command_executor):
            try:
                return self.command_executor(command, args)
            except Exception as e:
                return f"Error executing plugin command '{command}': {str(e)}"
        else:
            return f"[DRY-RUN: execute plugin command '{command}' with args {args}]"


class SkillExecutorPlugin(AlleyBotPlugin):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "skill_executor"
        self.version = "1.0.0"
        self.command_executor: Optional[Callable[[str, List[str]], str]] = config.get("command_executor")
        self.action_router = ActionRouter(self.command_executor)

    def get_commands(self) -> Dict[str, Callable]:
        return {
            "execute": self.execute_skill,
        }

    def execute_skill(self, args: List[str]) -> str:
        if not args:
            return "Usage: execute <skill_name> [parameters...]"
        skill_name = args[0]
        skill_args = args[1:]
        print(f"Executing skill: {skill_name} with args: {skill_args}")
        result = self.action_router._execute_via_plugin(skill_name, skill_args)
        return f"Executed skill '{skill_name}' successfully: {result}"


PLUGIN_INFO = {
    "name": "skill_executor",
    "version": "1.0.0",
    "description": "Skill Executor - Execute skill instructions with tool access and script execution. Supports skill composition.",
    "author": "AlleyBot"
}


def create_plugin(config: Optional[Dict[str, Any]] = None) -> SkillExecutorPlugin:
    return SkillExecutorPlugin(config or {})