"""
CognitiveLoop - Main execution orchestration for AlleyKernel

Brings together ThoughtProcessor, SynergyGate, and ActionRegistry
into a unified cognitive execution harness.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable

from .thought_processor import ThoughtProcessor, ProcessorConfig, TurnResult
from .synergy_gate import SynergyGate, GateVerdict, PermissionDenial
from .action_registry import ActionRegistry
from .session_store import SessionStore


@dataclass(frozen=True)
class LoopConfig:
    """Configuration for the cognitive loop."""
    max_turns: int = 8
    enable_streaming: bool = True
    fail_closed: bool = True  # Fail closed on validation errors
    auto_persist: bool = True  # Auto-save sessions


@dataclass
class CognitiveLoop:
    """
    Main orchestration harness for agent cognition.
    
    Coordinates:
    - Intent routing (ActionRegistry)
    - Permission gating (SynergyGate)
    - Turn management (ThoughtProcessor)
    - Session persistence (SessionStore)
    """
    config: LoopConfig = field(default_factory=LoopConfig)
    processor: ThoughtProcessor = field(default_factory=ThoughtProcessor)
    gate: SynergyGate = field(default_factory=SynergyGate)
    registry: ActionRegistry = field(default_factory=ActionRegistry)
    store: SessionStore = field(default_factory=SessionStore)
    
    # Event hooks
    _pre_turn_hooks: list[Callable[[str], None]] = field(default_factory=list, repr=False)
    _post_turn_hooks: list[Callable[[TurnResult], None]] = field(default_factory=list, repr=False)
    _on_denial_hooks: list[Callable[[PermissionDenial], None]] = field(default_factory=list, repr=False)

    @classmethod
    def create(
        cls,
        session_id: str | None = None,
        config: LoopConfig | None = None,
        processor_config: ProcessorConfig | None = None,
        store: SessionStore | None = None,
    ) -> CognitiveLoop:
        """
        Factory method to create a configured loop.
        
        Args:
            session_id: Existing session ID to resume, or None for new
            config: Loop configuration
            processor_config: Thought processor configuration
            store: Session store instance
        """
        cfg = config or LoopConfig()
        st = store or SessionStore()
        
        if session_id:
            processor = ThoughtProcessor.from_saved_session(
                session_id, st, processor_config
            )
        else:
            processor = ThoughtProcessor.from_workspace(processor_config)
        
        return cls(
            config=cfg,
            processor=processor,
            store=st,
        )

    def run_turn(self, prompt: str) -> TurnResult:
        """
        Run a single cognitive turn.
        
        Flow:
        1. Pre-turn hooks
        2. Intent routing
        3. Permission gating
        4. Thought processing
        5. Post-turn hooks
        6. Auto-persist
        """
        # Pre-turn hooks
        for hook in self._pre_turn_hooks:
            hook(prompt)
        
        # Intent routing
        matches = self.registry.route_intent(prompt, limit=5)
        
        # Separate by type
        command_matches = [m for m in matches if m.kind == "command"]
        tool_matches = [m for m in matches if m.kind == "tool"]
        
        # Check permissions
        denials: list[PermissionDenial] = []
        allowed_tools: list[str] = []
        
        for match in tool_matches:
            decision = self.gate.check_permission(match.name)
            
            if decision.verdict == GateVerdict.ALLOW:
                allowed_tools.append(match.name)
            elif decision.verdict == GateVerdict.DENY:
                denials.append(PermissionDenial(
                    tool_name=match.name,
                    reason=decision.reason,
                ))
                # Run denial hooks
                for hook in self._on_denial_hooks:
                    hook(denials[-1])
            elif decision.verdict == GateVerdict.ASK:
                # For now, treat ASK as deny in non-interactive mode
                denials.append(PermissionDenial(
                    tool_name=match.name,
                    reason=f"Requires user confirmation: {decision.reason}",
                ))
        
        # Process the turn
        result = self.processor.process_thought(
            prompt=prompt,
            matched_commands=tuple(m.name for m in command_matches),
            matched_tools=tuple(allowed_tools),
            denied_tools=tuple(denials),
        )
        
        # Post-turn hooks
        for hook in self._post_turn_hooks:
            hook(result)
        
        # Auto-persist if enabled
        if self.config.auto_persist:
            self.persist()
        
        return result

    async def run_turn_async(self, prompt: str) -> TurnResult:
        """Async version of run_turn."""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run_turn, prompt)

    def stream_turn(self, prompt: str):
        """Stream turn execution events."""
        # Pre-turn
        for hook in self._pre_turn_hooks:
            hook(prompt)
        
        # Routing
        matches = self.registry.route_intent(prompt, limit=5)
        
        # Permission filtering
        allowed_commands: list[str] = []
        allowed_tools: list[str] = []
        denials: list[PermissionDenial] = []
        
        for match in matches:
            if match.kind == "command":
                allowed_commands.append(match.name)
            elif match.kind == "tool":
                decision = self.gate.check_permission(match.name)
                if decision.verdict == GateVerdict.ALLOW:
                    allowed_tools.append(match.name)
                else:
                    denials.append(PermissionDenial(
                        tool_name=match.name,
                        reason=decision.reason,
                    ))
        
        # Stream processing
        for event in self.processor.stream_process(
            prompt=prompt,
            matched_commands=tuple(allowed_commands),
            matched_tools=tuple(allowed_tools),
            denied_tools=tuple(denials),
        ):
            yield event
        
        # Post-turn
        result = self.processor.process_thought(
            prompt=prompt,
            matched_commands=tuple(allowed_commands),
            matched_tools=tuple(allowed_tools),
            denied_tools=tuple(denials),
        )
        
        for hook in self._post_turn_hooks:
            hook(result)
        
        if self.config.auto_persist:
            self.persist()

    def run_multi_turn(
        self, 
        prompts: list[str],
        on_turn_complete: Callable[[int, TurnResult], None] | None = None
    ) -> list[TurnResult]:
        """
        Run multiple turns in sequence.
        
        Args:
            prompts: List of prompts to process
            on_turn_complete: Optional callback(index, result)
            
        Returns:
            List of turn results
        """
        results: list[TurnResult] = []
        
        for i, prompt in enumerate(prompts):
            result = self.run_turn(prompt)
            results.append(result)
            
            if on_turn_complete:
                on_turn_complete(i, result)
            
            # Check stop reason
            if result.stop_reason != "completed":
                break
        
        return results

    def persist(self) -> str:
        """Persist current session state."""
        return self.processor.persist(self.store)

    def on_pre_turn(self, callback: Callable[[str], None]) -> None:
        """Register pre-turn hook."""
        self._pre_turn_hooks.append(callback)

    def on_post_turn(self, callback: Callable[[TurnResult], None]) -> None:
        """Register post-turn hook."""
        self._post_turn_hooks.append(callback)

    def on_denial(self, callback: Callable[[PermissionDenial], None]) -> None:
        """Register permission denial hook."""
        self._on_denial_hooks.append(callback)

    def get_session_summary(self) -> dict[str, Any]:
        """Get comprehensive session summary."""
        return {
            "session_id": self.processor.session_id,
            "turns": len(self.processor.mutable_messages),
            "tokens": {
                "input": self.processor.total_usage.input_tokens,
                "output": self.processor.total_usage.output_tokens,
                "total": self.processor.total_usage.input_tokens + self.processor.total_usage.output_tokens,
            },
            "denials": len(self.processor.permission_denials),
            "gate": self.gate.get_summary(),
            "registry": self.registry.list_all(),
        }

    def get_summary(self) -> str:
        """Get human-readable loop summary."""
        lines = [
            "=== Cognitive Loop ===",
            self.processor.get_summary(),
            "",
            "=== Gate ===",
            str(self.gate.get_summary()),
            "",
            "=== Registry ===",
            self.registry.get_summary(),
            "",
            "=== Store ===",
            self.store.get_summary(),
        ]
        return "\n".join(lines)
