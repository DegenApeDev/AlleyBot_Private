"""
SynergyGate - Multi-layered permission and security validation

Fail-closed security architecture for high-risk agent actions.
Aligns with AlleyBot's AGI Constitutional Rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum


class GateVerdict(Enum):
    """Permission gate verdicts."""
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"  # Requires user confirmation


@dataclass(frozen=True)
class PermissionRule:
    """A single permission rule for tool/action access."""
    pattern: str
    source: str  # e.g., 'user_config', 'session_allow', 'default'
    tool_name: str | None = None


@dataclass(frozen=True)
class PermissionDenial:
    """Record of a permission denial for audit trail."""
    tool_name: str
    reason: str
    timestamp: str | None = None
    
    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(
                self, 
                'timestamp', 
                __import__('datetime').datetime.now().isoformat()
            )


@dataclass(frozen=True)
class GateDecision:
    """Result of a permission gate check."""
    verdict: GateVerdict
    reason: str
    rule_matched: PermissionRule | None = None
    suggestion: str | None = None  # Suggested rule to add


@dataclass
class SynergyGate:
    """
    Multi-layered permission context for agent actions.
    
    Provides fail-closed validation aligned with Synergy/SyMod gating requirements.
    Permission contexts flow through the entire execution chain.
    """
    # Rule sets by category
    always_allow: list[PermissionRule] = field(default_factory=list)
    always_deny: list[PermissionRule] = field(default_factory=list)
    always_ask: list[PermissionRule] = field(default_factory=list)
    
    # Session-specific overrides
    session_allows: set[str] = field(default_factory=set)
    session_denies: set[str] = field(default_factory=set)
    
    # Gate configuration
    mode: str = "default"  # default, strict, bypass (for trusted)
    is_bypass_available: bool = False
    should_avoid_prompts: bool = False  # For background agents
    
    # Dangerous file protection
    DANGEROUS_FILES: tuple[str, ...] = field(default_factory=lambda: (
        ".gitconfig",
        ".gitmodules",
        ".bashrc",
        ".bash_profile",
        ".zshrc",
        ".zprofile",
        ".profile",
        ".env",
        ".env.local",
        "id_rsa",
        "id_ed25519",
        ".aws/credentials",
        ".ssh/config",
    ))
    
    DANGEROUS_DIRECTORIES: tuple[str, ...] = field(default_factory=lambda: (
        ".git",
        ".ssh",
        ".aws",
        ".gnupg",
        ".claude",
        "node_modules/.bin",  # Executables
    ))
    
    # Validation hooks
    _pre_check_hooks: list[Callable[[str, dict[str, Any]], GateDecision | None]] = field(
        default_factory=list, repr=False
    )

    def check_permission(
        self, 
        tool_name: str, 
        context: dict[str, Any] | None = None
    ) -> GateDecision:
        """
        Check if a tool/action is permitted.
        
        Args:
            tool_name: Name of the tool/action
            context: Additional context (file_path, command, etc.)
            
        Returns:
            GateDecision with verdict and reasoning
        """
        ctx = context or {}
        
        # Run pre-check hooks first
        for hook in self._pre_check_hooks:
            result = hook(tool_name, ctx)
            if result is not None:
                return result
        
        # Check session-level denies
        if tool_name in self.session_denies:
            return GateDecision(
                verdict=GateVerdict.DENY,
                reason=f"'{tool_name}' is in session deny list",
            )
        
        # Check always-deny rules
        for rule in self.always_deny:
            if self._matches(rule, tool_name, ctx):
                return GateDecision(
                    verdict=GateVerdict.DENY,
                    reason=f"Matched deny rule from {rule.source}: {rule.pattern}",
                    rule_matched=rule,
                )
        
        # Check session-level allows
        if tool_name in self.session_allows:
            return GateDecision(
                verdict=GateVerdict.ALLOW,
                reason=f"'{tool_name}' is in session allow list",
            )
        
        # Check always-ask rules
        for rule in self.always_ask:
            if self._matches(rule, tool_name, ctx):
                suggestion = f"Add rule: allow {tool_name}"
                return GateDecision(
                    verdict=GateVerdict.ASK,
                    reason=f"Matched ask rule from {rule.source}: {rule.pattern}",
                    rule_matched=rule,
                    suggestion=suggestion,
                )
        
        # Check always-allow rules
        for rule in self.always_allow:
            if self._matches(rule, tool_name, ctx):
                return GateDecision(
                    verdict=GateVerdict.ALLOW,
                    reason=f"Matched allow rule from {rule.source}: {rule.pattern}",
                    rule_matched=rule,
                )
        
        # Default behavior based on mode
        if self.mode == "strict":
            return GateDecision(
                verdict=GateVerdict.ASK,
                reason=f"No explicit rule for '{tool_name}' in strict mode",
                suggestion=f"Add rule: allow {tool_name}",
            )
        
        # Default deny for destructive tools
        if self._is_destructive(tool_name, ctx):
            return GateDecision(
                verdict=GateVerdict.ASK,
                reason=f"'{tool_name}' is potentially destructive and requires explicit permission",
                suggestion=f"Add rule: allow {tool_name}",
            )
        
        return GateDecision(
            verdict=GateVerdict.ALLOW,
            reason=f"'{tool_name}' allowed by default policy",
        )

    def check_file_permission(self, file_path: str, operation: str) -> GateDecision:
        """Check permission for file operations."""
        normalized = file_path.lower()
        
        # Check dangerous files
        for dangerous in self.DANGEROUS_FILES:
            if dangerous.lower() in normalized or normalized.endswith(dangerous.lower()):
                return GateDecision(
                    verdict=GateVerdict.DENY,
                    reason=f"Cannot {operation} dangerous file: {dangerous}",
                    suggestion=f"If intentional, use direct system commands",
                )
        
        # Check dangerous directories
        for dangerous in self.DANGEROUS_DIRECTORIES:
            if f"/{dangerous.lower()}/" in normalized or normalized.startswith(f"{dangerous.lower()}/"):
                return GateDecision(
                    verdict=GateVerdict.ASK,
                    reason=f"Operation affects protected directory: {dangerous}",
                )
        
        return GateDecision(
            verdict=GateVerdict.ALLOW,
            reason="File operation permitted",
        )

    def session_allow(self, tool_name: str) -> None:
        """Add tool to session allow list."""
        self.session_allows.add(tool_name)
        self.session_denies.discard(tool_name)

    def session_deny(self, tool_name: str) -> None:
        """Add tool to session deny list."""
        self.session_denies.add(tool_name)
        self.session_allows.discard(tool_name)

    def add_rule(
        self, 
        category: str, 
        pattern: str, 
        source: str = "user_config",
        tool_name: str | None = None
    ) -> None:
        """Add a permission rule."""
        rule = PermissionRule(pattern=pattern, source=source, tool_name=tool_name)
        
        if category == "allow":
            self.always_allow.append(rule)
        elif category == "deny":
            self.always_deny.append(rule)
        elif category == "ask":
            self.always_ask.append(rule)

    def register_pre_check(
        self, 
        hook: Callable[[str, dict[str, Any]], GateDecision | None]
    ) -> None:
        """Register a pre-check hook for custom validation logic."""
        self._pre_check_hooks.append(hook)

    def _matches(self, rule: PermissionRule, tool_name: str, context: dict[str, Any]) -> bool:
        """Check if a rule matches the tool and context."""
        # Direct name match
        if rule.tool_name and rule.tool_name.lower() == tool_name.lower():
            return True
        
        # Pattern match on tool name
        if rule.pattern.lower() in tool_name.lower():
            return True
        
        # Pattern match on context values
        for value in context.values():
            if isinstance(value, str) and rule.pattern.lower() in value.lower():
                return True
        
        return False

    def _is_destructive(self, tool_name: str, context: dict[str, Any]) -> bool:
        """Check if a tool operation is potentially destructive."""
        destructive_keywords = [
            "delete", "remove", "rm", "drop", "destroy",
            "write", "edit", "modify", "bash", "shell", "exec",
        ]
        name_lower = tool_name.lower()
        
        for keyword in destructive_keywords:
            if keyword in name_lower:
                return True
        
        # Check context for destructive operations
        if "command" in context:
            cmd = context["command"].lower()
            for keyword in ["rm ", "dd ", "mkfs", "format", "> "]:
                if keyword in cmd:
                    return True
        
        return False

    def get_summary(self) -> dict[str, Any]:
        """Get summary of gate configuration."""
        return {
            "mode": self.mode,
            "allow_rules": len(self.always_allow),
            "deny_rules": len(self.always_deny),
            "ask_rules": len(self.always_ask),
            "session_allows": len(self.session_allows),
            "session_denies": len(self.session_denies),
            "bypass_available": self.is_bypass_available,
            "avoid_prompts": self.should_avoid_prompts,
        }
