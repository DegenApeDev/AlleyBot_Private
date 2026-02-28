"""
Brain Plugin for AlleyBot
The autonomous decision engine that makes AlleyBot truly agentic.

Combines:
- context_gatherer.py: Collects context from all sources
- decision_engine.py: AI-powered action selection
- smart_reply.py: Memory-enriched reply generation

This is what makes AlleyBot beat OpenClaw.
"""
import os
import sys
import time
import threading
import datetime
import asyncio
from typing import Dict, Any, Optional, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugin_manager import AlleyBotPlugin
from plugins.brain.context_gatherer import ContextGathererMixin
from plugins.brain.decision_engine import DecisionEngineMixin
from plugins.brain.smart_reply import SmartReplyMixin
from plugins.brain.feedback_loop import FeedbackLoopMixin
from plugins.brain.content_strategy import ContentStrategyMixin
from plugins.brain.dynamic_skills import DynamicSkillsMixin
from plugins.brain.operational_resilience import OperationalResilienceMixin
from plugins.brain.multi_agent import MultiAgentCollaborationMixin
from plugins.brain.reputation import ReputationSystemMixin
from plugins.brain.self_reflection import SelfReflectionMixin
from plugins.brain.goal_stack_mixin import GoalStackMixin
from plugins.brain.world_state_mixin import WorldStateMixin
from plugins.brain.cross_platform_engagement import CrossPlatformEngagementMixin
from plugins.brain.self_improvement_hooks import install_self_improvement_hooks


class BrainPlugin(ContextGathererMixin, DecisionEngineMixin, SmartReplyMixin, FeedbackLoopMixin, 
                  ContentStrategyMixin, DynamicSkillsMixin, OperationalResilienceMixin,
                  MultiAgentCollaborationMixin, ReputationSystemMixin, SelfReflectionMixin,
                  GoalStackMixin, WorldStateMixin, CrossPlatformEngagementMixin, AlleyBotPlugin):
    """AlleyBot's autonomous brain - decides what to do, when, and how"""

    def __init__(self, config):
        super().__init__(config)
        self.config = config  # Store config for later access
        self.autonomous_running = False
        self.autonomous_thread = None
        self.cycle_count = 0
        self.cycle_interval = config.get('cycle_interval', 300)  # 5 min default
        self._autonomous_brain = None  # AutonomousBrain instance (unified loop)
        self.api = None
        self.core = None
        self.voice_emotion_plugin = None
        self.current_voice_emotion: Optional[Dict[str, Any]] = None

    def get_commands(self) -> Dict[str, callable]:
        return {
            "brain": self.brain_command,
            "think": self.think_command,
            "startbrain": self.start_brain,
            "stopbrain": self.stop_brain,
        }

    def brain_command(self, args: list) -> str:
        if args and args[0] == "status":
            status = f"running={self.autonomous_running}, cycles={self.cycle_count}"
            thread_alive = self.autonomous_thread.is_alive() if self.autonomous_thread else False
            status += f", thread_alive={thread_alive}"
            return f"🧠 Brain status: {status}"
        return self.think_command(args)

    def think_command(self, args: list = None) -> str:
        if args is None:
            args = []
        # Use AGI Kernel if available (new autonomous thinking)
        if hasattr(self.core, 'agi_kernel') and self.core.agi_kernel:
            context = {
                'time': datetime.datetime.now().isoformat(),
                'hour': datetime.datetime.now().hour,
                'platform_states': 'active'
            }
            action = self.core.agi_kernel.decide(context)
            
            if action:
                return f"🧠 AGI decided: {action.get('id')} - {action.get('description', '')[:80]}"
            else:
                return "🧠 AGI: No action recommended at this time"
        
        # Fallback to old think method
        result = self.think()
        success = '✅' if result.get('success') else '⏭️' if not result.get('action') else '❌'
        return f"🧠 Cycle {result['cycle']}: {success} {result.get('action', 'none')} - {result.get('reason', '')[:100]}"

    def start_brain(self, args: list = None) -> str:
        if args is None:
            args = []
        return self.start_autonomous()

    def stop_brain(self, args: list = None) -> str:
        if args is None:
            args = []
        return self.stop_autonomous()

    def initialize(self, api, core):
        """Initialize brain plugin"""
        super().initialize(api, core)
        self.api = api
        self.core = core

        self._init_context_gatherer()
        self._init_decision_engine()
        self._init_smart_reply()
        self._init_feedback_loop()
        self._init_content_strategy()
        self._init_dynamic_skills()
        self._init_operational_resilience()
        self._init_multi_agent_collaboration()
        self._init_reputation_system()
        self._init_self_reflection()
        self._init_goal_stack()
        self._init_world_state()
        self._init_cross_platform_engagement()
        
        # Install self-improvement hooks
        install_self_improvement_hooks(self)

        # Voice emotion integration hooks
        self.voice_emotion_plugin = None
        if self.core and hasattr(self.core, 'plugin_manager'):
            pm = self.core.plugin_manager
            if hasattr(pm, 'plugins') and 'voice_emotion' in pm.plugins:
                self.voice_emotion_plugin = pm.plugins['voice_emotion']
                print("🧠 Brain: voice_emotion plugin hooked into context & multimodal emotion pipeline")

        # Wire up AutonomousBrain for unified loop
        try:
            from src.agentic.autonomous_brain import AutonomousBrain
            self._autonomous_brain = AutonomousBrain(
                core=core,
                plugin_manager=core.plugin_manager if core else None,
            )
            print("🔗 BrainPlugin: AutonomousBrain unified loop ready")
        except Exception as e:
            self._autonomous_brain = None
            print(f"⚠️ BrainPlugin: AutonomousBrain not available, using legacy loop: {e}")

        # Auto-start if configured
        if self.config.get('auto_start', False):
            self.start_autonomous()

        print("🧠 Brain plugin ready")

    def update_voice_emotion(self, emotion_data: Dict[str, Any]) -> None:
        """Integration hook: voice_emotion plugin pushes audio-processed emotion data here"""
        self.current_voice_emotion = emotion_data
        print(f"🎤 Brain audio input hook: voice emotion = {emotion_data}")

    def _fuse_emotions(self, emotions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Multimodal emotion fusion pipeline: highest confidence wins"""
        if not emotions:
            return {'dominant_emotion': 'neutral', 'confidence': 0.5, 'sources': []}
        best = max(emotions.values(), key=lambda e: e.get('confidence', 0.0))
        fused = {
            'dominant_emotion': best.get('emotion', 'unknown'),
            'confidence': best.get('confidence', 0.0),
            'sources': list(emotions.keys()),
            'all_emotions': emotions
        }
        print(f"🧠 Multimodal emotion: {fused['dominant_emotion']} ({fused['confidence']:.2f}) from {fused['sources']}")
        return fused

    def gather_full_context(self) -> Dict[str, Any]:
        """Override: integrate voice emotion into multimodal pipeline"""
        context = super().gather_full_context()
        voice_emo = self.current_voice_emotion
        if not voice_emo and self.voice_emotion_plugin:
            try:
                get_emo = getattr(self.voice_emotion_plugin, 'get_current_emotion', None)
                if callable(get_emo):
                    voice_emo = get_emo()
            except Exception as e:
                print(f"🧠 Voice emotion poll error: {e}")
        if voice_emo:
            ctx_emotions = context.setdefault('emotions', {})
            ctx_emotions['voice'] = voice_emo
            context['multimodal_emotion'] = self._fuse_emotions(ctx_emotions)
        return context

    def think(self) -> Dict[str, Any]:
        """Run one think cycle — delegates to AutonomousBrain if available, else legacy pipeline"""
        self.cycle_count += 1

        # === Unified path: delegate to AutonomousBrain._execute_cycle() ===
        if self._autonomous_brain is not None:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule as a coroutine task (non-blocking)
                    asyncio.ensure_future(self._autonomous_brain._execute_cycle())
                    return {
                        'cycle': self.cycle_count,
                        'action': 'agi_cycle',
                        'platform': 'all',
                        'reason': 'Delegated to AutonomousBrain unified cycle',
                        'success': True,
                        'output': 'AGI cycle scheduled',
                    }
                else:
                    loop.run_until_complete(self._autonomous_brain._execute_cycle())
                    return {
                        'cycle': self.cycle_count,
                        'action': 'agi_cycle',
                        'platform': 'all',
                        'reason': 'AutonomousBrain unified cycle complete',
                        'success': True,
                        'output': 'AGI cycle complete',
                    }
            except Exception as e:
                print(f"AutonomousBrain cycle failed, falling back: {e}")

        # === Legacy fallback: original BrainPlugin pipeline ===
        context = self.gather_full_context()
        action = self.decide_next_action(context)

        if not action:
            return {
                'cycle': self.cycle_count,
                'action': None,
                'reason': 'No actions available (all on cooldown or plugins not loaded)',
            }

        result = self.execute_action(action)

        if self.config.get('telegram_notify', False) and result.get('success'):
            self._notify_telegram(action, result)

        return {
            'cycle': self.cycle_count,
            'action': action['id'],
            'platform': action.get('platform', ''),
            'reason': action.get('reason', ''),
            'success': result.get('success', False),
            'output': result.get('output', '')[:200],
        }

    def start_autonomous(self):
        """Start the autonomous brain loop — uses AutonomousBrain if available"""
        if self.autonomous_running:
            return "⚠️  Brain already running"

        # === Unified path: start AutonomousBrain async loop in a background thread ===
        if self._autonomous_brain is not None:
            self.autonomous_running = True

            def _run_unified_loop():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        self._autonomous_brain.start(mode=self.config.get('mode', 'normal'))
                    )
                    loop.run_forever()
                except Exception as e:
                    print(f"🧠 AutonomousBrain loop error: {e}")
                finally:
                    loop.close()
                    self.autonomous_running = False

            self.autonomous_thread = threading.Thread(target=_run_unified_loop, daemon=True)
            self.autonomous_thread.start()
            return "🧠 Autonomous brain started (unified AutonomousBrain loop)"

        # === Legacy fallback ===
        self.autonomous_running = True

        def brain_loop():
            print(f"🧠 Autonomous brain started (legacy, cycle every {self.cycle_interval}s)")
            while self.autonomous_running:
                try:
                    result = self.think()
                    action = result.get('action', 'none')
                    success = '✅' if result.get('success') else '⏭️' if not result.get('action') else '❌'
                    print(f"🧠 Cycle {result['cycle']}: {success} {action} - {result.get('reason', '')[:60]}")
                    time.sleep(self.cycle_interval)
                except Exception as e:
                    print(f"🧠 Brain cycle error: {e}")
                    time.sleep(10)
            print("🧠 Legacy brain loop stopped")

        self.autonomous_thread = threading.Thread(target=brain_loop, daemon=True)
        self.autonomous_thread.start()
        return "🧠 Autonomous brain started (legacy loop)"

    def stop_autonomous(self):
        """Stop the autonomous brain loop"""
        if not self.autonomous_running:
            return "⚠️ Brain not running"
        self.autonomous_running = False
        if self.autonomous_thread and self.autonomous_thread.is_alive():
            self.autonomous_thread.join(timeout=5)
        if self._autonomous_brain:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._autonomous_brain.stop())
                else:
                    loop.run_until_complete(self._autonomous_brain.stop())
            except Exception as e:
                print(f"🧠 Stop AutonomousBrain error: {e}")
        print("🧠 Autonomous brain stopped")
        return "🧠 Autonomous brain stopped"


PLUGIN_INFO = {
    "name": "brain",
    "version": "2.0.0",
    "description": "AlleyBot's autonomous brain with voice_emotion integration and multimodal emotion pipeline",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return BrainPlugin(config or {})