"""
ActionRegistry - Intent routing and execution registry

Maps intent to commands/tools with case-insensitive lookup.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum


class ActionType(Enum):
    """Types of registered actions."""
    COMMAND = "command"
    TOOL = "tool"
    SKILL = "skill"


@dataclass(frozen=True)
class RegisteredAction:
    """A registered command or action."""
    name: str
    action_type: ActionType
    handler: Callable[..., Any]
    description: str = ""
    source_hint: str = ""  # Where this action originated
    
    def execute(self, payload: str | dict[str, Any], **kwargs) -> str:
        """Execute the action handler."""
        try:
            if isinstance(payload, dict):
                result = self.handler(**payload, **kwargs)
            else:
                result = self.handler(payload, **kwargs)
            
            # Normalize result to string
            if isinstance(result, dict):
                return result.get("message", str(result))
            return str(result)
        except Exception as e:
            return f"Error executing {self.name}: {e}"


@dataclass(frozen=True)
class RegisteredTool:
    """A registered tool with metadata."""
    name: str
    handler: Callable[..., Any]
    description: str = ""
    source_hint: str = ""
    requires_permission: bool = True
    
    def execute(self, payload: str | dict[str, Any]) -> dict[str, Any]:
        """Execute the tool and return structured result."""
        try:
            if isinstance(payload, dict):
                result = self.handler(**payload)
            else:
                result = self.handler(payload)
            
            # Normalize to dict
            if isinstance(result, dict):
                return result
            return {"success": True, "result": result, "message": str(result)}
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Tool {self.name} failed: {e}",
            }


@dataclass
class IntentMatch:
    """A matched intent with scoring."""
    kind: str  # command, tool, skill
    name: str
    source_hint: str
    score: int
    action: RegisteredAction | RegisteredTool | None = None


@dataclass
class ActionRegistry:
    """
    Central registry for commands, tools, and skills.
    
    Provides case-insensitive lookup and intent routing.
    """
    commands: dict[str, RegisteredAction] = field(default_factory=dict)
    tools: dict[str, RegisteredTool] = field(default_factory=dict)
    skills: dict[str, RegisteredAction] = field(default_factory=dict)
    
    # Intent routing cache
    _routing_cache: dict[str, list[IntentMatch]] = field(
        default_factory=dict, repr=False
    )

    def register_command(
        self, 
        name: str, 
        handler: Callable, 
        description: str = "",
        source_hint: str = "native"
    ) -> None:
        """Register a command."""
        self.commands[name.lower()] = RegisteredAction(
            name=name,
            action_type=ActionType.COMMAND,
            handler=handler,
            description=description,
            source_hint=source_hint,
        )

    def register_tool(
        self, 
        name: str, 
        handler: Callable, 
        description: str = "",
        source_hint: str = "native",
        requires_permission: bool = True,
    ) -> None:
        """Register a tool."""
        self.tools[name.lower()] = RegisteredTool(
            name=name,
            handler=handler,
            description=description,
            source_hint=source_hint,
            requires_permission=requires_permission,
        )

    def register_skill(
        self, 
        name: str, 
        handler: Callable, 
        description: str = "",
        source_hint: str = "skill"
    ) -> None:
        """Register a skill."""
        self.skills[name.lower()] = RegisteredAction(
            name=name,
            action_type=ActionType.SKILL,
            handler=handler,
            description=description,
            source_hint=source_hint,
        )

    def get_command(self, name: str) -> RegisteredAction | None:
        """Get a command by name (case-insensitive)."""
        return self.commands.get(name.lower())

    def get_tool(self, name: str) -> RegisteredTool | None:
        """Get a tool by name (case-insensitive)."""
        return self.tools.get(name.lower())

    def get_skill(self, name: str) -> RegisteredAction | None:
        """Get a skill by name (case-insensitive)."""
        return self.skills.get(name.lower())

    def route_intent(self, intent: str, limit: int = 5) -> list[IntentMatch]:
        """
        Route user intent to matching commands/tools.
        
        Uses token-based scoring similar to the original pattern
        but with distinct AlleyBot terminology.
        """
        # Check cache
        cache_key = f"{intent}:{limit}"
        if cache_key in self._routing_cache:
            return self._routing_cache[cache_key]
        
        # Tokenize intent
        tokens = {
            token.lower() 
            for token in intent.replace("/", " ").replace("-", " ").split() 
            if token
        }
        
        # Collect matches from all categories
        matches: list[IntentMatch] = []
        
        for name, action in self.commands.items():
            score = self._score_tokens(tokens, action)
            if score > 0:
                matches.append(IntentMatch(
                    kind="command",
                    name=action.name,
                    source_hint=action.source_hint,
                    score=score,
                    action=action,
                ))
        
        for name, tool in self.tools.items():
            score = self._score_tokens(tokens, tool)
            if score > 0:
                matches.append(IntentMatch(
                    kind="tool",
                    name=tool.name,
                    source_hint=tool.source_hint,
                    score=score,
                    action=tool,
                ))
        
        for name, skill in self.skills.items():
            score = self._score_tokens(tokens, skill)
            if score > 0:
                matches.append(IntentMatch(
                    kind="skill",
                    name=skill.name,
                    source_hint=skill.source_hint,
                    score=score,
                    action=skill,
                ))
        
        # Sort by score (descending), then by kind, then by name
        matches.sort(key=lambda m: (-m.score, m.kind, m.name))
        
        # Prioritize: one of each kind first, then fill remaining slots
        selected: list[IntentMatch] = []
        kinds_seen: set[str] = set()
        
        for match in matches:
            if match.kind not in kinds_seen:
                selected.append(match)
                kinds_seen.add(match.kind)
        
        # Fill remaining slots with sorted leftovers
        remaining = [m for m in matches if m not in selected]
        selected.extend(remaining[:max(0, limit - len(selected))])
        
        result = selected[:limit]
        self._routing_cache[cache_key] = result
        return result

    def list_all(self) -> dict[str, list[str]]:
        """List all registered actions by category."""
        return {
            "commands": [a.name for a in self.commands.values()],
            "tools": [t.name for t in self.tools.values()],
            "skills": [s.name for s in self.skills.values()],
        }

    def clear_cache(self) -> None:
        """Clear the routing cache."""
        self._routing_cache.clear()

    def _score_tokens(
        self, 
        tokens: set[str], 
        item: RegisteredAction | RegisteredTool
    ) -> int:
        """Score how well tokens match the item."""
        haystacks = [
            item.name.lower(),
            item.source_hint.lower(),
            item.description.lower() if hasattr(item, 'description') else "",
        ]
        
        score = 0
        for token in tokens:
            for haystack in haystacks:
                if token in haystack:
                    score += 1
                    break  # Count each token only once per item
        
        return score

    def get_summary(self) -> str:
        """Get human-readable registry summary."""
        lines = [
            f"Commands: {len(self.commands)}",
            f"Tools: {len(self.tools)}",
            f"Skills: {len(self.skills)}",
            f"Cached routes: {len(self._routing_cache)}",
        ]
        return "\n".join(lines)
