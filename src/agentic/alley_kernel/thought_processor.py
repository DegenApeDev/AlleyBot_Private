"""
ThoughtProcessor - Session-scoped cognitive execution engine

Manages conversation turns, permission tracking, and context compaction.
Similar to a query engine but focused on agent cognition.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable
from uuid import uuid4

from .synergy_gate import PermissionDenial
from .session_store import SessionStore, StoredSession
from .context_window import ContextWindow


@dataclass(frozen=True)
class ProcessorConfig:
    """Configuration for thought processing limits."""
    max_turns: int = 8
    max_budget_tokens: int = 2000
    compact_after_turns: int = 12
    structured_output: bool = False
    structured_retry_limit: int = 2


@dataclass(frozen=True)
class UsageSummary:
    """Token usage tracking for cognitive turns."""
    input_tokens: int = 0
    output_tokens: int = 0

    def add_turn(self, prompt: str, output: str) -> UsageSummary:
        """Calculate projected usage after adding a turn."""
        # Rough estimation: 4 chars ~= 1 token
        new_input = len(prompt) // 4
        new_output = len(output) // 4
        return UsageSummary(
            input_tokens=self.input_tokens + new_input,
            output_tokens=self.output_tokens + new_output,
        )


@dataclass(frozen=True)
class TurnResult:
    """Result of a single cognitive turn."""
    prompt: str
    output: str
    matched_commands: tuple[str, ...]
    matched_tools: tuple[str, ...]
    permission_denials: tuple[PermissionDenial, ...]
    usage: UsageSummary
    stop_reason: str


@dataclass
class ThoughtProcessor:
    """
    Owns the cognitive lifecycle and session state for agent conversations.
    
    One ThoughtProcessor per conversation. Each process_thought() call 
    starts a new turn within the same session. State persists across turns.
    """
    config: ProcessorConfig = field(default_factory=ProcessorConfig)
    session_id: str = field(default_factory=lambda: uuid4().hex)
    mutable_messages: list[str] = field(default_factory=list)
    permission_denials: list[PermissionDenial] = field(default_factory=list)
    total_usage: UsageSummary = field(default_factory=UsageSummary)
    context_window: ContextWindow = field(default_factory=ContextWindow)
    _on_turn_complete: Callable[[TurnResult], None] | None = None

    @classmethod
    def from_workspace(cls, config: ProcessorConfig | None = None) -> ThoughtProcessor:
        """Initialize a fresh processor from current workspace."""
        return cls(config=config or ProcessorConfig())

    @classmethod
    def from_saved_session(
        cls, 
        session_id: str, 
        store: SessionStore,
        config: ProcessorConfig | None = None
    ) -> ThoughtProcessor:
        """Restore processor from persisted session."""
        stored = store.load(session_id)
        return cls(
            config=config or ProcessorConfig(),
            session_id=stored.session_id,
            mutable_messages=list(stored.messages),
            total_usage=UsageSummary(stored.input_tokens, stored.output_tokens),
            context_window=ContextWindow(entries=list(stored.messages), flushed=True),
        )

    def process_thought(
        self,
        prompt: str,
        matched_commands: tuple[str, ...] = (),
        matched_tools: tuple[str, ...] = (),
        denied_tools: tuple[PermissionDenial, ...] = (),
    ) -> TurnResult:
        """
        Process a single thought/turn in the cognitive loop.
        
        Args:
            prompt: The user's input or agent thought
            matched_commands: Commands matched to this thought
            matched_tools: Tools selected for execution
            denied_tools: Tools that were permission-denied
            
        Returns:
            TurnResult with output, usage, and stop reason
        """
        # Check turn limits
        if len(self.mutable_messages) >= self.config.max_turns:
            output = f"Max cognitive turns reached. Cannot process: {prompt[:50]}..."
            return TurnResult(
                prompt=prompt,
                output=output,
                matched_commands=matched_commands,
                matched_tools=matched_tools,
                permission_denials=denied_tools,
                usage=self.total_usage,
                stop_reason="max_turns_reached",
            )

        # Build cognitive output
        summary_lines = [
            f"Thought: {prompt}",
            f"Commands: {', '.join(matched_commands) if matched_commands else 'none'}",
            f"Tools: {', '.join(matched_tools) if matched_tools else 'none'}",
            f"Blocked: {len(denied_tools)}",
        ]
        output = self._format_output(summary_lines)
        
        # Track usage
        projected_usage = self.total_usage.add_turn(prompt, output)
        
        # Determine stop reason
        stop_reason = "completed"
        total_tokens = projected_usage.input_tokens + projected_usage.output_tokens
        if total_tokens > self.config.max_budget_tokens:
            stop_reason = "max_budget_reached"

        # Update state
        self.mutable_messages.append(prompt)
        self.context_window.append(prompt)
        self.permission_denials.extend(denied_tools)
        self.total_usage = projected_usage
        
        # Compact if needed
        self._compact_if_needed()
        
        result = TurnResult(
            prompt=prompt,
            output=output,
            matched_commands=matched_commands,
            matched_tools=matched_tools,
            permission_denials=denied_tools,
            usage=self.total_usage,
            stop_reason=stop_reason,
        )
        
        # Callback if registered
        if self._on_turn_complete:
            self._on_turn_complete(result)
            
        return result

    def stream_process(
        self,
        prompt: str,
        matched_commands: tuple[str, ...] = (),
        matched_tools: tuple[str, ...] = (),
        denied_tools: tuple[PermissionDenial, ...] = (),
    ):
        """Stream processing events for real-time UI updates."""
        yield {"type": "thought_start", "session_id": self.session_id, "prompt": prompt}
        
        if matched_commands:
            yield {"type": "command_match", "commands": matched_commands}
        if matched_tools:
            yield {"type": "tool_match", "tools": matched_tools}
        if denied_tools:
            yield {"type": "permission_denial", "denials": [d.tool_name for d in denied_tools]}
            
        result = self.process_thought(prompt, matched_commands, matched_tools, denied_tools)
        
        yield {"type": "thought_delta", "text": result.output}
        yield {
            "type": "thought_complete",
            "usage": {
                "input_tokens": result.usage.input_tokens,
                "output_tokens": result.usage.output_tokens,
            },
            "stop_reason": result.stop_reason,
            "context_size": len(self.context_window.entries),
        }

    def _compact_if_needed(self) -> None:
        """Compact message history to prevent context overflow."""
        if len(self.mutable_messages) > self.config.compact_after_turns:
            self.mutable_messages[:] = self.mutable_messages[-self.config.compact_after_turns:]
        self.context_window.compact(self.config.compact_after_turns)

    def replay_history(self) -> tuple[str, ...]:
        """Replay stored message history."""
        return self.context_window.replay()

    def flush_context(self) -> None:
        """Flush context to persistent storage."""
        self.context_window.flush()

    def persist(self, store: SessionStore) -> str:
        """Persist session state to storage."""
        self.flush_context()
        session = StoredSession(
            session_id=self.session_id,
            messages=tuple(self.mutable_messages),
            input_tokens=self.total_usage.input_tokens,
            output_tokens=self.total_usage.output_tokens,
        )
        return store.save(session)

    def _format_output(self, summary_lines: list[str]) -> str:
        """Format output based on configuration."""
        if self.config.structured_output:
            payload = {
                "summary": summary_lines,
                "session_id": self.session_id,
            }
            return self._render_structured(payload)
        return "\n".join(summary_lines)

    def _render_structured(self, payload: dict[str, Any]) -> str:
        """Render structured output with retry logic."""
        last_error: Exception | None = None
        for _ in range(self.config.structured_retry_limit):
            try:
                return json.dumps(payload, indent=2)
            except (TypeError, ValueError) as exc:
                last_error = exc
                payload = {"summary": ["structured output retry"], "session_id": self.session_id}
        raise RuntimeError("structured output rendering failed") from last_error

    def on_turn_complete(self, callback: Callable[[TurnResult], None]) -> None:
        """Register callback for turn completion."""
        self._on_turn_complete = callback

    def get_summary(self) -> str:
        """Get human-readable summary of processor state."""
        lines = [
            f"Session: {self.session_id}",
            f"Turns: {len(self.mutable_messages)} / {self.config.max_turns}",
            f"Tokens: {self.total_usage.input_tokens + self.total_usage.output_tokens} / {self.config.max_budget_tokens}",
            f"Denials: {len(self.permission_denials)}",
            f"Context flushed: {self.context_window.flushed}",
        ]
        return "\n".join(lines)
