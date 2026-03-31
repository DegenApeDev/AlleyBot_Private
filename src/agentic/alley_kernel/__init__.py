"""
AlleyKernel - Native AGI harness for AlleyBot

Clean-room implementation of agentic execution patterns.
This is NOT derived from any proprietary codebase.
"""

# Core cognitive loop
from .thought_processor import ThoughtProcessor, ProcessorConfig, TurnResult, UsageSummary
from .cognitive_loop import CognitiveLoop, LoopConfig

# Permission and security
from .synergy_gate import SynergyGate, PermissionDenial, GateDecision, GateVerdict, PermissionRule
from .path_protection import (
    PathProtection,
    PathRiskLevel,
    validate_path,
    is_dangerous_path,
    get_path_protection,
)

# Action routing and registry
from .action_registry import ActionRegistry, RegisteredAction, RegisteredTool, IntentMatch, ActionType

# Context and memory management
from .context_window import ContextWindow
from .context_budget import (
    EnhancedContextWindow,
    ContextBudget,
    TokenThreshold,
    CompactionResult,
)
from .session_store import SessionStore, StoredSession

# Cost tracking
from .cost_tracker import CostTracker, ModelUsage, ModelProvider

# Skills system
from .skills import (
    SkillRegistry,
    SkillDefinition,
    SkillActivation,
    create_builtin_skills,
)

# Lifecycle hooks
from .hooks import (
    HooksRegistry,
    HookCommand,
    HookCallback,
    HookType,
    create_default_hooks,
)

# Session memory extraction
from .session_memory import (
    SessionMemory,
    MemoryEntry,
    MemoryLayer,
    ExtractionConfig,
)

__all__ = [
    # Core
    "ThoughtProcessor",
    "ProcessorConfig",
    "TurnResult",
    "UsageSummary",
    "CognitiveLoop",
    "LoopConfig",
    
    # Security
    "SynergyGate",
    "PermissionDenial",
    "GateDecision",
    "GateVerdict",
    "PermissionRule",
    "PathProtection",
    "PathRiskLevel",
    "validate_path",
    "is_dangerous_path",
    "get_path_protection",
    
    # Registry
    "ActionRegistry",
    "RegisteredAction",
    "RegisteredTool",
    "IntentMatch",
    "ActionType",
    
    # Context
    "ContextWindow",
    "EnhancedContextWindow",
    "ContextBudget",
    "TokenThreshold",
    "CompactionResult",
    "SessionStore",
    "StoredSession",
    
    # Cost
    "CostTracker",
    "ModelUsage",
    "ModelProvider",
    
    # Skills
    "SkillRegistry",
    "SkillDefinition",
    "SkillActivation",
    "create_builtin_skills",
    
    # Hooks
    "HooksRegistry",
    "HookCommand",
    "HookCallback",
    "HookType",
    "create_default_hooks",
    
    # Memory
    "SessionMemory",
    "MemoryEntry",
    "MemoryLayer",
    "ExtractionConfig",
]
