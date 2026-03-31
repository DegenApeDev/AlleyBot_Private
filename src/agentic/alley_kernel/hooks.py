"""
Hooks System - Lifecycle event hooks for agent execution

Shell commands and callbacks triggered at key lifecycle points.
"""

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum, auto
from datetime import datetime
import os
from pathlib import Path


class HookType(Enum):
    """Types of lifecycle hooks."""
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"
    POST_TOOL_FAILURE = "post_tool_failure"
    PRE_COMPACT = "pre_compact"
    POST_COMPACT = "post_compact"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    PERMISSION_DENIED = "permission_denied"
    USER_PROMPT_SUBMIT = "user_prompt_submit"
    SUBAGENT_START = "subagent_start"
    SUBAGENT_STOP = "subagent_stop"


@dataclass
class HookCommand:
    """
    A shell command hook.
    
    Hooks can run synchronously or asynchronously in background.
    They receive event context via environment variables.
    """
    name: str
    command: str  # Shell command to execute
    hook_type: HookType
    async_execution: bool = False  # Run in background
    timeout_ms: int = 600_000  # 10 min default
    env_vars: dict[str, str] = field(default_factory=dict)
    
    # Filter: only run for specific tools/actions
    tool_filter: list[str] | None = None  # e.g., ["bash", "file_edit"]
    
    # Execution tracking
    _execution_count: int = field(default=0, repr=False)
    _last_execution: str | None = field(default=None, repr=False)


@dataclass
class HookCallback:
    """A Python callback hook."""
    name: str
    callback: Callable[[dict[str, Any]], Any]
    hook_type: HookType
    async_execution: bool = False


@dataclass
class HooksRegistry:
    """
    Registry for lifecycle hooks.
    
    Supports both shell command hooks and Python callbacks.
    Hooks receive context data and can modify execution flow.
    """
    shell_hooks: dict[HookType, list[HookCommand]] = field(
        default_factory=lambda: {t: [] for t in HookType}
    )
    callback_hooks: dict[HookType, list[HookCallback]] = field(
        default_factory=lambda: {t: [] for t in HookType}
    )
    
    # Global hooks that run for all events
    global_shell_hooks: list[HookCommand] = field(default_factory=list)
    global_callback_hooks: list[HookCallback] = field(default_factory=list)
    
    # Execution log
    _execution_log: list[dict[str, Any]] = field(default_factory=list, repr=False)

    def register_shell(
        self,
        name: str,
        command: str,
        hook_type: HookType,
        async_exec: bool = False,
        tool_filter: list[str] | None = None,
        timeout_ms: int = 600_000,
    ) -> HookCommand:
        """Register a shell command hook."""
        hook = HookCommand(
            name=name,
            command=command,
            hook_type=hook_type,
            async_execution=async_exec,
            timeout_ms=timeout_ms,
            tool_filter=tool_filter,
        )
        self.shell_hooks[hook_type].append(hook)
        return hook

    def register_callback(
        self,
        name: str,
        callback: Callable[[dict[str, Any]], Any],
        hook_type: HookType,
        async_exec: bool = False,
    ) -> HookCallback:
        """Register a Python callback hook."""
        hook = HookCallback(
            name=name,
            callback=callback,
            hook_type=hook_type,
            async_execution=async_exec,
        )
        self.callback_hooks[hook_type].append(hook)
        return hook

    async def trigger(
        self,
        hook_type: HookType,
        context: dict[str, Any],
        tool_name: str | None = None,
    ) -> list[Any]:
        """
        Trigger all hooks for a given event type.
        
        Args:
            hook_type: Type of event
            context: Event context data
            tool_name: Optional tool name for filtering
            
        Returns:
            List of hook results
        """
        results: list[Any] = []
        
        # Build environment for shell hooks
        env = os.environ.copy()
        env.update({
            f"ALLEYBOT_{k.upper()}": str(v)
            for k, v in context.items()
        })
        env["ALLEYBOT_HOOK_TYPE"] = hook_type.value
        env["ALLEYBOT_TIMESTAMP"] = datetime.now().isoformat()
        
        # Execute shell hooks
        for hook in self.shell_hooks.get(hook_type, []):
            # Check tool filter
            if hook.tool_filter and tool_name not in hook.tool_filter:
                continue
            
            result = await self._execute_shell_hook(hook, env, context)
            results.append(result)
        
        # Execute callback hooks
        for hook in self.callback_hooks.get(hook_type, []):
            try:
                if hook.async_execution:
                    # Run in background
                    asyncio.create_task(
                        self._execute_callback_hook(hook, context)
                    )
                    results.append(None)
                else:
                    result = hook.callback(context)
                    results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        
        # Log execution
        self._execution_log.append({
            "hook_type": hook_type.value,
            "timestamp": datetime.now().isoformat(),
            "context_keys": list(context.keys()),
            "tool_name": tool_name,
            "results_count": len(results),
        })
        
        return results

    async def _execute_shell_hook(
        self,
        hook: HookCommand,
        env: dict[str, str],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a shell command hook."""
        hook._execution_count += 1
        hook._last_execution = datetime.now().isoformat()
        
        try:
            if hook.async_execution:
                # Background execution - don't wait
                subprocess.Popen(
                    hook.command,
                    shell=True,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return {
                    "hook": hook.name,
                    "status": "background",
                    "command": hook.command,
                }
            else:
                # Synchronous execution with timeout
                proc = await asyncio.wait_for(
                    asyncio.create_subprocess_shell(
                        hook.command,
                        env=env,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    ),
                    timeout=hook.timeout_ms / 1000,
                )
                
                stdout, stderr = await proc.communicate()
                
                return {
                    "hook": hook.name,
                    "status": "completed",
                    "returncode": proc.returncode,
                    "stdout": stdout.decode()[:1000] if stdout else "",
                    "stderr": stderr.decode()[:1000] if stderr else "",
                }
                
        except asyncio.TimeoutError:
            return {
                "hook": hook.name,
                "status": "timeout",
                "timeout_ms": hook.timeout_ms,
            }
        except Exception as e:
            return {
                "hook": hook.name,
                "status": "error",
                "error": str(e),
            }

    async def _execute_callback_hook(
        self,
        hook: HookCallback,
        context: dict[str, Any],
    ) -> None:
        """Execute a callback hook (background)."""
        try:
            hook.callback(context)
        except Exception:
            pass  # Background execution - don't propagate errors

    def load_from_directory(self, hooks_dir: str | Path) -> int:
        """
        Load hooks from a directory structure:
        
        hooks/
          pre_tool_use/
            my_hook.sh
          session_start/
            welcome.sh
        """
        loaded = 0
        hooks_path = Path(hooks_dir)
        
        if not hooks_path.exists():
            return 0
        
        for hook_type in HookType:
            type_dir = hooks_path / hook_type.value
            if type_dir.exists():
                for hook_file in type_dir.iterdir():
                    if hook_file.is_file() and os.access(hook_file, os.X_OK):
                        self.register_shell(
                            name=hook_file.stem,
                            command=str(hook_file),
                            hook_type=hook_type,
                        )
                        loaded += 1
        
        return loaded

    def get_execution_summary(self) -> dict[str, Any]:
        """Get summary of hook executions."""
        from collections import Counter
        
        if not self._execution_log:
            return {"total_executions": 0}
        
        by_type = Counter(e["hook_type"] for e in self._execution_log)
        
        return {
            "total_executions": len(self._execution_log),
            "by_type": dict(by_type),
            "shell_hooks": sum(len(h) for h in self.shell_hooks.values()),
            "callback_hooks": sum(len(h) for h in self.callback_hooks.values()),
        }


# Predefined useful hooks

def create_default_hooks() -> HooksRegistry:
    """Create registry with useful default hooks."""
    registry = HooksRegistry()
    
    # Session start hook - log session info
    registry.register_callback(
        name="session_logger",
        callback=lambda ctx: print(f"🚀 Session started: {ctx.get('session_id', 'unknown')}"),
        hook_type=HookType.SESSION_START,
    )
    
    # Permission denied hook - alert on security events
    registry.register_callback(
        name="security_alert",
        callback=lambda ctx: print(f"🛡️ Permission denied: {ctx.get('tool_name', 'unknown')} - {ctx.get('reason', '')}"),
        hook_type=HookType.PERMISSION_DENIED,
    )
    
    # Pre-compact hook - notify before compaction
    registry.register_callback(
        name="compact_notifier",
        callback=lambda ctx: print(f"📦 Compacting context window (current tokens: {ctx.get('tokens', '?')})"),
        hook_type=HookType.PRE_COMPACT,
    )
    
    return registry
