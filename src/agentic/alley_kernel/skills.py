"""
Skills System - Bundled capabilities with conditional activation

Prompt-based skills that activate based on context and user intent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum
import asyncio
from datetime import datetime


class SkillActivation(Enum):
    """How a skill can be activated."""
    USER_INVOKED = "user_invoked"  # User explicitly calls /skillname
    CONTEXTUAL = "contextual"  # Auto-activated based on context
    CONDITIONAL = "conditional"  # Activated when is_enabled() returns True


@dataclass
class SkillDefinition:
    """
    Definition for a bundled skill in AlleyBot.
    
    Skills are prompt-based capabilities with:
    - Conditional activation based on context
    - Tool allowlisting for security
    - Background execution capability
    """
    name: str
    description: str
    prompt_template: str
    aliases: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    when_to_use: str = ""
    activation: SkillActivation = SkillActivation.USER_INVOKED
    is_enabled: Callable[[], bool] = field(default_factory=lambda: lambda: True)
    requires_model: str | None = None  # Specific model for this skill
    disable_model_invocation: bool = False
    max_turns: int | None = None  # Override default max turns
    
    # Files to extract on first use (lazy loading pattern)
    files: dict[str, str] = field(default_factory=dict)
    _files_extracted: bool = False
    _files_dir: str | None = None
    
    def get_prompt(self, args: str = "", context: dict[str, Any] | None = None) -> str:
        """Generate the full prompt for this skill."""
        prompt = self.prompt_template
        
        # Add file base directory if extracted
        if self._files_dir:
            prompt = f"Base directory for this skill: {self._files_dir}\n\n{prompt}"
        
        # Add user arguments
        if args:
            prompt += f"\n\n## User Request\n\n{args}"
        
        # Add context if provided
        if context:
            prompt += f"\n\n## Context\n\n{self._format_context(context)}"
        
        return prompt
    
    def _format_context(self, context: dict[str, Any]) -> str:
        """Format context dictionary for prompt."""
        lines = []
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    async def extract_files(self, base_dir: str) -> str | None:
        """
        Extract skill files to disk for on-demand reading.
        Lazy extraction - only runs once per skill.
        """
        if self._files_extracted or not self.files:
            return self._files_dir
        
        try:
            import os
            from pathlib import Path
            
            skill_dir = Path(base_dir) / self.name
            skill_dir.mkdir(parents=True, exist_ok=True)
            
            for filename, content in self.files.items():
                filepath = skill_dir / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                filepath.write_text(content)
            
            self._files_dir = str(skill_dir)
            self._files_extracted = True
            return self._files_dir
            
        except Exception:
            return None


@dataclass
class SkillRegistry:
    """Registry for managing bundled skills."""
    skills: dict[str, SkillDefinition] = field(default_factory=dict)
    _execution_history: list[dict[str, Any]] = field(default_factory=list, repr=False)
    
    def register(self, skill: SkillDefinition) -> None:
        """Register a skill."""
        self.skills[skill.name.lower()] = skill
        
        # Register aliases
        for alias in skill.aliases:
            if alias.lower() not in self.skills:
                self.skills[alias.lower()] = skill
    
    def get(self, name: str) -> SkillDefinition | None:
        """Get a skill by name (case-insensitive)."""
        return self.skills.get(name.lower())
    
    def list_active(self) -> list[SkillDefinition]:
        """List all currently enabled skills."""
        return [s for s in self.skills.values() if s.is_enabled()]
    
    def match_intent(self, intent: str) -> list[SkillDefinition]:
        """Match user intent to relevant skills."""
        tokens = set(intent.lower().split())
        matches: list[tuple[SkillDefinition, int]] = []
        
        for skill in self.skills.values():
            score = 0
            haystacks = [
                skill.name.lower(),
                skill.description.lower(),
                skill.when_to_use.lower(),
            ]
            
            for token in tokens:
                for haystack in haystacks:
                    if token in haystack:
                        score += 1
                        break
            
            if score > 0:
                matches.append((skill, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: -x[1])
        
        # Return unique skills (deduplicate aliases)
        seen: set[str] = set()
        result: list[SkillDefinition] = []
        for skill, _ in matches:
            if skill.name not in seen:
                result.append(skill)
                seen.add(skill.name)
        
        return result
    
    def execute(
        self, 
        skill_name: str, 
        args: str = "", 
        context: dict[str, Any] | None = None
    ) -> str:
        """
        Execute a skill and return the prompt for the LLM.
        
        This prepares the skill prompt - actual execution happens
        through the cognitive loop.
        """
        skill = self.get(skill_name)
        if not skill:
            return f"Error: Skill '{skill_name}' not found"
        
        if not skill.is_enabled():
            return f"Error: Skill '{skill_name}' is currently disabled"
        
        # Record execution
        self._execution_history.append({
            "skill": skill_name,
            "args": args,
            "timestamp": datetime.now().isoformat(),
        })
        
        return skill.get_prompt(args, context)
    
    async def execute_async(
        self,
        skill_name: str,
        args: str = "",
        context: dict[str, Any] | None = None,
        files_base_dir: str | None = None,
    ) -> str:
        """Async version with file extraction support."""
        skill = self.get(skill_name)
        if not skill:
            return f"Error: Skill '{skill_name}' not found"
        
        # Extract files if needed
        if files_base_dir and skill.files:
            await skill.extract_files(files_base_dir)
        
        return self.execute(skill_name, args, context)
    
    def get_execution_summary(self) -> dict[str, Any]:
        """Get summary of skill executions."""
        from collections import Counter
        
        if not self._execution_history:
            return {"total": 0, "by_skill": {}}
        
        skill_counts = Counter(e["skill"] for e in self._execution_history)
        
        return {
            "total": len(self._execution_history),
            "by_skill": dict(skill_counts),
            "recent": self._execution_history[-5:],
        }
    
    def clear_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()


# Predefined skills for AlleyBot

def create_builtin_skills() -> SkillRegistry:
    """Create registry with useful built-in skills."""
    registry = SkillRegistry()
    
    # Stuck detection skill
    registry.register(SkillDefinition(
        name="stuck",
        description="Diagnose frozen or slow AlleyBot sessions",
        prompt_template="""# Session Diagnostics

Investigate and report on system resource usage and potential hangs.

## What to look for:
- High CPU processes (≥90% sustained)
- Processes in uninterruptible sleep state (D)
- Stopped processes (T) - user hit Ctrl+Z
- Zombie processes (Z)
- High memory usage (≥4GB RSS)
- Stuck child processes

## Investigation steps:
1. List AlleyBot processes with resource usage
2. Check for suspicious child processes
3. Sample high CPU processes if found

Report findings with specific PIDs, CPU%, memory, and state.
""",
        aliases=["diagnose", "debug"],
        when_to_use="Use when AlleyBot appears frozen, stuck, or unusually slow",
        allowed_tools=["bash", "process_list", "system_info"],
    ))
    
    # Verification skill
    registry.register(SkillDefinition(
        name="verify",
        description="Verify code changes work correctly",
        prompt_template="""# Code Verification

Verify that recent code changes work as intended.

## Steps:
1. Review the changes made
2. Check for syntax errors
3. Run relevant tests if available
4. Validate the fix works as expected
5. Check for regressions

## Report:
- What was changed
- Verification method used
- Results (pass/fail)
- Any issues found
""",
        aliases=["check", "validate"],
        when_to_use="Use after making code changes to verify they work",
        allowed_tools=["file_read", "bash", "test_runner"],
    ))
    
    # Memory review skill
    registry.register(SkillDefinition(
        name="remember",
        description="Review and organize memory entries",
        prompt_template="""# Memory Review

Review the memory landscape and propose organization.

## Goal:
Analyze memory layers and propose changes grouped by action type.

## Steps:
1. Gather all memory layers (CLAUDE.md, project notes, auto-memory)
2. Classify entries by destination:
   - Project conventions → project docs
   - Personal preferences → user config
   - Temporary notes → working memory
3. Identify duplicates, outdated entries, conflicts
4. Present structured report for user approval

## Report sections:
1. Promotions (entries to move)
2. Cleanup (duplicates, outdated, conflicts)
3. Ambiguous (need user input)
4. No action needed
""",
        aliases=["memory", "organize"],
        when_to_use="Use to review, organize, or promote memory entries",
        allowed_tools=["file_read", "file_write", "memory_query"],
    ))
    
    # Simplification skill
    registry.register(SkillDefinition(
        name="simplify",
        description="Simplify code or explanations",
        prompt_template="""# Simplification Request

Simplify the provided code or explanation while preserving functionality.

## Principles:
- Remove unnecessary complexity
- Use clearer variable/function names
- Break down nested structures
- Remove redundant code
- Prefer standard library solutions
- Add explanatory comments for non-obvious logic

## Output:
- Simplified version
- Explanation of changes made
- Rationale for simplifications
""",
        aliases=["clean", "refactor"],
        when_to_use="Use when code or explanation is overly complex",
        allowed_tools=["file_read", "file_edit"],
    ))
    
    # Loop/iteration skill
    registry.register(SkillDefinition(
        name="loop",
        description="Iterate on code multiple times with refinement",
        prompt_template="""# Iterative Refinement

Iterate on code N times, improving with each pass.

## Process:
1. Review current implementation
2. Identify specific improvements
3. Apply changes
4. Verify still functional
5. Repeat for remaining iterations

## Each iteration focus on:
- Iteration 1: Structure and organization
- Iteration 2: Error handling and edge cases
- Iteration 3: Performance and polish

## Report after each iteration:
- Changes made
- Issues addressed
- Verification results
""",
        aliases=["iterate", "refine"],
        when_to_use="Use for iterative code improvement",
        allowed_tools=["file_read", "file_edit", "bash"],
        max_turns=12,
    ))
    
    return registry
