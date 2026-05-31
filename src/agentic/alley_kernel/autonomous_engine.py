"""
AutonomousCognitiveEngine - Proactive thinking system for AlleyBot

Uses AlleyKernel's CognitiveLoop to run background thought cycles,
enabling AlleyBot to take initiative without user direction.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable
from datetime import datetime
from enum import Enum


class ProactiveTrigger(Enum):
    """Types of triggers for proactive behavior."""
    SCHEDULED = "scheduled"  # Time-based
    EVENT_DRIVEN = "event_driven"  # React to system events
    GOAL_DRIVEN = "goal_driven"  # Pursue autonomous goals
    ANOMALY_DRIVEN = "anomaly_driven"  # Detect and respond to issues
    OPPORTUNITY_DRIVEN = "opportunity_driven"  # Spot and act on opportunities


@dataclass
class ProactiveThought:
    """A proactive thought cycle configuration."""
    id: str
    trigger: ProactiveTrigger
    priority: int  # 1-10, higher = more urgent
    max_turns: int = 3
    cooldown_minutes: int = 5
    
    # Trigger conditions
    schedule_interval: int | None = None  # Minutes for SCHEDULED
    event_patterns: list[str] | None = None  # For EVENT_DRIVEN
    goal_types: list[str] | None = None  # For GOAL_DRIVEN
    anomaly_threshold: float = 0.7  # For ANOMALY_DRIVEN
    
    # Action to take
    skill_name: str | None = None  # Use AlleyKernel skill
    custom_action: Callable | None = None
    
    # State tracking
    last_run: datetime | None = None
    run_count: int = 0
    last_result: Any = None


@dataclass
class AutonomousCognitiveEngine:
    """
    Proactive thinking engine for AlleyBot.
    
    Runs background cognitive cycles that:
    - Monitor system health (auto /stuck detection)
    - Verify recent changes (auto /verify)
    - Compact context before overflow
    - Extract memory periodically
    - Pursue goals autonomously
    """
    
    agi_kernel: Any = field(repr=False)
    alley_kernel: dict[str, Any] = field(repr=False)
    
    # Proactive thought registry
    thoughts: dict[str, ProactiveThought] = field(default_factory=dict)
    
    # Background task management
    _running: bool = False
    _task: asyncio.Task | None = field(default=None, repr=False)
    _check_interval: int = 30  # seconds
    
    # Event queue for trigger processing
    _event_queue: asyncio.Queue = field(default_factory=asyncio.Queue, repr=False)
    
    # Callbacks for integration
    _on_thought_start: list[Callable[[str], None]] = field(default_factory=list, repr=False)
    _on_thought_complete: list[Callable[[str, Any], None]] = field(default_factory=list, repr=False)

    def __post_init__(self):
        """Initialize default proactive thoughts."""
        self._register_default_thoughts()

    def _register_default_thoughts(self) -> None:
        """Register built-in proactive thinking patterns."""
        
        # 1. System health check (auto /stuck detection)
        self.register_thought(ProactiveThought(
            id="system_health_monitor",
            trigger=ProactiveTrigger.SCHEDULED,
            priority=8,
            schedule_interval=10,  # Check every 10 minutes
            skill_name="stuck",
            max_turns=1,
        ))
        
        # 2. Post-code-change verification (auto /verify)
        self.register_thought(ProactiveThought(
            id="auto_verify_changes",
            trigger=ProactiveTrigger.EVENT_DRIVEN,
            priority=9,
            event_patterns=["file_write", "file_edit", "code_change"],
            skill_name="verify",
            cooldown_minutes=2,
            max_turns=2,
        ))
        
        # 3. Context compaction watcher
        self.register_thought(ProactiveThought(
            id="context_compaction_watcher",
            trigger=ProactiveTrigger.ANOMALY_DRIVEN,
            priority=7,
            anomaly_threshold=0.8,  # Trigger at 80% context usage
            max_turns=1,
        ))
        
        # 4. Memory extraction (auto /remember)
        self.register_thought(ProactiveThought(
            id="periodic_memory_extraction",
            trigger=ProactiveTrigger.SCHEDULED,
            priority=5,
            schedule_interval=30,  # Every 30 minutes
            skill_name="remember",
            max_turns=1,
        ))
        
        # 5. Goal-driven autonomous pursuit
        self.register_thought(ProactiveThought(
            id="autonomous_goal_pursuit",
            trigger=ProactiveTrigger.GOAL_DRIVEN,
            priority=6,
            goal_types=["analysis", "research", "monitoring"],
            max_turns=5,
            cooldown_minutes=15,
        ))
        
        # 6. Repeated failure self-healing
        self.register_thought(ProactiveThought(
            id="self_healing_loop",
            trigger=ProactiveTrigger.ANOMALY_DRIVEN,
            priority=10,  # High priority
            anomaly_threshold=0.6,  # 2+ recent failures
            skill_name="loop",
            max_turns=3,
            cooldown_minutes=5,
        ))

    def register_thought(self, thought: ProactiveThought) -> None:
        """Register a proactive thought pattern."""
        self.thoughts[thought.id] = thought

    def unregister_thought(self, thought_id: str) -> bool:
        """Unregister a thought pattern."""
        if thought_id in self.thoughts:
            del self.thoughts[thought_id]
            return True
        return False

    async def start(self) -> None:
        """Start the autonomous cognitive engine."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._cognitive_loop())
        print("🧠 AutonomousCognitiveEngine started - AlleyBot is now proactive")

    async def stop(self) -> None:
        """Stop the autonomous engine."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("🛑 AutonomousCognitiveEngine stopped")

    async def _cognitive_loop(self) -> None:
        """Main cognitive loop - checks triggers and executes thoughts."""
        while self._running:
            try:
                # Check scheduled triggers
                await self._check_scheduled_thoughts()
                
                # Process event queue
                await self._process_events()
                
                # Check anomaly conditions
                await self._check_anomaly_conditions()
                
                # Check goal-driven triggers
                await self._check_goal_triggers()
                
                await asyncio.sleep(self._check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ AutonomousCognitiveEngine error: {e}")
                await asyncio.sleep(self._check_interval)

    async def _check_scheduled_thoughts(self) -> None:
        """Execute thoughts based on schedule."""
        now = datetime.now()
        
        for thought in self.thoughts.values():
            if thought.trigger != ProactiveTrigger.SCHEDULED:
                continue
            
            if thought.schedule_interval is None:
                continue
            
            # Check cooldown
            if thought.last_run:
                elapsed = (now - thought.last_run).total_seconds() / 60
                if elapsed < thought.cooldown_minutes:
                    continue
                if elapsed < thought.schedule_interval:
                    continue
            
            await self._execute_thought(thought)

    async def _process_events(self) -> None:
        """Process events from the queue."""
        try:
            while not self._event_queue.empty():
                event = self._event_queue.get_nowait()
                await self._handle_event(event)
        except asyncio.QueueEmpty:
            pass

    async def _handle_event(self, event: dict[str, Any]) -> None:
        """Handle an event and trigger matching thoughts."""
        event_type = event.get('type', '')
        
        for thought in self.thoughts.values():
            if thought.trigger != ProactiveTrigger.EVENT_DRIVEN:
                continue
            
            if not thought.event_patterns:
                continue
            
            # Check if event matches patterns
            if any(pattern in event_type for pattern in thought.event_patterns):
                # Check cooldown
                if thought.last_run:
                    elapsed = (datetime.now() - thought.last_run).total_seconds() / 60
                    if elapsed < thought.cooldown_minutes:
                        continue
                
                await self._execute_thought(thought, event_context=event)

    async def _check_anomaly_conditions(self) -> None:
        """Check for anomaly conditions that should trigger thoughts."""
        
        # Check context window usage
        context_usage = self._get_context_usage_ratio()
        if context_usage > 0.8:
            # Find context compaction watcher
            thought = self.thoughts.get('context_compaction_watcher')
            if thought and self._can_execute(thought):
                await self._execute_thought(thought, 
                    context={'usage_ratio': context_usage})
        
        # Check for repeated failures
        failure_ratio = self._get_recent_failure_ratio()
        if failure_ratio > 0.6:  # 60% failure rate
            thought = self.thoughts.get('self_healing_loop')
            if thought and self._can_execute(thought):
                await self._execute_thought(thought,
                    context={'failure_ratio': failure_ratio})

    async def _check_goal_triggers(self) -> None:
        """Check for active goals that should trigger autonomous pursuit."""
        goal_manager = getattr(self.agi_kernel, 'goal_manager', None)
        if not goal_manager:
            return
        
        try:
            active_goals = goal_manager.get_active_goals()
        except Exception:
            return
        
        if not active_goals:
            return
        
        thought = self.thoughts.get('autonomous_goal_pursuit')
        if not thought or not self._can_execute(thought):
            return
        
        # Check if any goals match our target types
        matching_goals = [
            g for g in active_goals
            if any(t in str(g).lower() for t in (thought.goal_types or []))
        ]
        
        if matching_goals:
            await self._execute_thought(thought,
                context={'goals': matching_goals})

    def _can_execute(self, thought: ProactiveThought) -> bool:
        """Check if a thought can be executed (cooldown, etc)."""
        if not thought.last_run:
            return True
        
        elapsed = (datetime.now() - thought.last_run).total_seconds() / 60
        return elapsed >= thought.cooldown_minutes

    async def _execute_thought(
        self,
        thought: ProactiveThought,
        event_context: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a proactive thought."""
        
        # Notify start
        for callback in self._on_thought_start:
            try:
                callback(thought.id)
            except Exception:
                pass
        
        print(f"🧠 Proactive thought: {thought.id} (priority {thought.priority})")
        
        result = None
        
        try:
            if thought.skill_name:
                # Execute via AlleyKernel skill
                result = await self._execute_skill_thought(thought, event_context)
            elif thought.custom_action:
                # Execute custom action
                if asyncio.iscoroutinefunction(thought.custom_action):
                    result = await thought.custom_action(event_context)
                else:
                    result = thought.custom_action(event_context)
            else:
                # Default: run cognitive loop
                result = await self._execute_cognitive_thought(thought, event_context)
            
            thought.last_result = result
            thought.run_count += 1
            
        except Exception as e:
            print(f"⚠️ Thought execution failed: {e}")
            result = {'success': False, 'error': str(e)}
        
        finally:
            thought.last_run = datetime.now()
            
            # Notify completion
            for callback in self._on_thought_complete:
                try:
                    callback(thought.id, result)
                except Exception:
                    pass
        
        return result

    async def _execute_skill_thought(
        self,
        thought: ProactiveThought,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a thought using an AlleyKernel skill."""
        skill_registry = self.alley_kernel.get('skill_registry')
        if not skill_registry:
            return {'success': False, 'error': 'SkillRegistry not available'}
        
        # Build args from context
        args = ""
        if context:
            if 'file_path' in context:
                args = context['file_path']
            elif 'event_type' in context:
                args = f"Detected: {context['event_type']}"
        
        prompt = await skill_registry.execute_async(
            skill_name=thought.skill_name,
            args=args,
            context=context,
        )
        
        return {
            'success': True,
            'skill': thought.skill_name,
            'prompt': prompt,
        }

    async def _execute_cognitive_thought(
        self,
        thought: ProactiveThought,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a thought using the cognitive loop."""
        cognitive_loop = self.alley_kernel.get('cognitive_loop')
        if not cognitive_loop:
            return {'success': False, 'error': 'CognitiveLoop not initialized'}
        
        # Run cognitive turn
        # Note: This would integrate with actual LLM in production
        return {
            'success': True,
            'thought_id': thought.id,
            'turns': thought.max_turns,
            'context': context,
        }

    def emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event that might trigger proactive thoughts."""
        try:
            self._event_queue.put_nowait({
                'type': event_type,
                'data': data,
                'timestamp': datetime.now().isoformat(),
            })
        except asyncio.QueueFull:
            pass

    def _get_context_usage_ratio(self) -> float:
        """Get current context window usage ratio (0.0-1.0)."""
        # This would integrate with actual context tracking
        # For now, return conservative estimate
        return 0.5

    def _get_recent_failure_ratio(self) -> float:
        """Get ratio of recent failures (0.0-1.0)."""
        action_router = getattr(self.agi_kernel, 'action_router', None)
        if not action_router:
            return 0.0
        
        stats = action_router.get_execution_stats()
        total = stats.get('total', 0)
        if total == 0:
            return 0.0
        
        failures = stats.get('failures', 0)
        # Only consider recent history (last 10)
        recent_total = min(total, 10)
        recent_failures = min(failures, recent_total)
        
        return recent_failures / recent_total if recent_total > 0 else 0.0

    def on_thought_start(self, callback: Callable[[str], None]) -> None:
        """Register callback for thought start."""
        self._on_thought_start.append(callback)

    def on_thought_complete(self, callback: Callable[[str, Any], None]) -> None:
        """Register callback for thought completion."""
        self._on_thought_complete.append(callback)

    def get_status(self) -> dict[str, Any]:
        """Get current engine status."""
        return {
            'running': self._running,
            'registered_thoughts': len(self.thoughts),
            'thoughts': [
                {
                    'id': t.id,
                    'trigger': t.trigger.value,
                    'priority': t.priority,
                    'last_run': t.last_run.isoformat() if t.last_run else None,
                    'run_count': t.run_count,
                    'skill': t.skill_name,
                }
                for t in self.thoughts.values()
            ],
        }


def create_autonomous_engine(agi_kernel: Any) -> AutonomousCognitiveEngine | None:
    """Factory to create autonomous engine if AlleyKernel available."""
    alley_kernel = getattr(agi_kernel, 'alley_kernel', None)
    if not alley_kernel:
        print("⚠️ Cannot create AutonomousCognitiveEngine - AlleyKernel not available")
        return None
    
    return AutonomousCognitiveEngine(
        agi_kernel=agi_kernel,
        alley_kernel=alley_kernel,
    )
