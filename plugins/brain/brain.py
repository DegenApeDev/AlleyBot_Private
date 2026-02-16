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

    def initialize(self, api, core):
        """Initialize brain plugin"""
        super().initialize(api, core)

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

        # Auto-start if configured
        if self.config.get('auto_start', False):
            self.start_autonomous()

        print("🧠 Brain plugin ready")

    def think(self) -> Dict[str, Any]:
        """Run one think cycle: gather context → decide → execute"""
        self.cycle_count += 1

        # 1. Gather context
        context = self.gather_full_context()

        # 2. Decide next action
        action = self.decide_next_action(context)

        if not action:
            return {
                'cycle': self.cycle_count,
                'action': None,
                'reason': 'No actions available (all on cooldown or plugins not loaded)',
            }

        # 3. Execute
        result = self.execute_action(action)

        # 4. Notify via Telegram if configured
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
        """Start the autonomous brain loop in a background thread"""
        if self.autonomous_running:
            return "⚠️  Brain already running"

        self.autonomous_running = True

        def brain_loop():
            print(f"🧠 Autonomous brain started (cycle every {self.cycle_interval}s)")
            while self.autonomous_running:
                try:
                    result = self.think()
                    action = result.get('action', 'none')
                    success = '✅' if result.get('success') else '⏭️' if not result.get('action') else '❌'
                    print(f"🧠 Cycle {result['cycle']}: {success} {action} - {result.get('reason', '')[:60]}")
                except Exception as e:
                    print(f"🧠 Brain cycle error: {e}")

                # Sleep in small increments so we can stop quickly
                for _ in range(self.cycle_interval):
                    if not self.autonomous_running:
                        break
                    time.sleep(1)

            print("🧠 Autonomous brain stopped")

        self.autonomous_thread = threading.Thread(target=brain_loop, daemon=True)
        self.autonomous_thread.start()
        return "🧠 Autonomous brain started"

    def stop_autonomous(self):
        """Stop the autonomous brain loop"""
        self.autonomous_running = False
        return "🧠 Brain stopping..."

    def _notify_telegram(self, action: Dict, result: Dict):
        """Send Telegram notification about autonomous action"""
        try:
            telegram = self.core.plugin_manager.plugins.get('telegram')
            if telegram and hasattr(telegram, 'send_message_to_owner_sync'):
                msg = (
                    f"🧠 **Autonomous Action**\n\n"
                    f"📋 {action['id']}\n"
                    f"🎯 {action.get('reason', 'N/A')}\n"
                    f"{'✅' if result['success'] else '❌'} "
                    f"{result.get('output', 'No output')[:200]}"
                )
                telegram.send_message_to_owner_sync(msg)
        except Exception:
            pass

    # =========================================================================
    # CLI Commands
    # =========================================================================

    def think_command(self, *args):
        """Run one brain think cycle manually"""
        result = self.think()
        action = result.get('action', 'none')
        if action == 'none' or action is None:
            return f"🧠 Cycle {result['cycle']}: No actions available right now\n{result.get('reason', '')}"

        success = '✅' if result.get('success') else '❌'
        output = (
            f"🧠 Cycle {result['cycle']}: {success} {action}\n"
            f"📍 Platform: {result.get('platform', '?')}\n"
            f"💭 Reason: {result.get('reason', '?')}\n"
            f"📝 Output: {result.get('output', '')[:300]}"
        )
        return output

    def start_command(self, *args):
        """Start autonomous brain loop"""
        return self.start_autonomous()

    def stop_command(self, *args):
        """Stop autonomous brain loop"""
        return self.stop_autonomous()

    def moltx_image_post_command(self, *args):
        """Create a post with AI-generated image on Moltx (max 3/day)"""
        result = self._dispatch_action('moltx_image_post')
        return result if result else "❌ Image post failed"

    def moltx_post_command(self, *args):
        """Create a post on Moltx. Usage: brain_moltx_post [topic/content]"""
        topic = ' '.join(args) if args else None
        
        # Get moltx plugin
        if not hasattr(self, 'core') or not self.core:
            return "❌ Core not available"
        
        moltx = self.core.plugin_manager.plugins.get('moltx')
        if not moltx:
            return "❌ Moltx plugin not loaded"
        
        # Generate content using decision engine
        content = self._generate_post_content('moltx')
        
        if not content:
            return "❌ Failed to generate post content"
        
        # Create the post
        result = moltx.create_post(content)
        return result if result else "❌ Failed to create post"

    def context_command(self, *args):
        """Show current context summary"""
        return f"🧠 Current Context:\n\n{self.build_context_summary()}"

    def actions_command(self, *args):
        """Show available actions"""
        available = self.get_available_actions()
        if not available:
            return "⏳ All actions on cooldown. Try again later."

        output = f"🎯 Available Actions ({len(available)}):\n\n"
        for a in available:
            output += f"  {'🔴' if a['impact'] == 'high' else '🟡' if a['impact'] == 'medium' else '🟢'} "
            output += f"{a['id']} ({a['platform']})\n"
            output += f"     {a['description'][:60]}\n"
            if a.get('last_run'):
                output += f"     Last: {a['last_run'][:16]}\n"
        return output

    def history_command(self, *args):
        """Show recent brain action history"""
        if not self.action_history:
            return "📭 No action history yet"

        output = f"📋 Brain History (last {min(10, len(self.action_history))}):\n\n"
        for entry in self.action_history[-10:]:
            icon = '✅' if entry.get('success') else '❌'
            output += f"  {icon} {entry['action']} ({entry.get('platform', '?')})\n"
            output += f"     {entry.get('reason', '')[:50]}\n"
            output += f"     {entry.get('timestamp', '?')[:16]}\n\n"
        return output

    def status_command(self, *args):
        """Show brain status"""
        ctx = self.gather_full_context()
        eng = ctx.get('engagement', {})
        available = self.get_available_actions()

        output = "🧠 Brain Status\n\n"
        output += f"  🔄 Autonomous: {'Running' if self.autonomous_running else 'Stopped'}\n"
        output += f"  ⏱️  Cycle interval: {self.cycle_interval}s\n"
        output += f"  📊 Total cycles: {self.cycle_count}\n"
        output += f"  🎯 Available actions: {len(available)}\n"
        output += f"  📈 Success rate: {eng.get('success_rate', 0):.0%} ({eng.get('total_recent', 0)} recent)\n"
        output += f"  👥 Known users: {len(self.user_profiles)}\n"

        # Platform status
        platforms = ctx.get('platforms', {})
        output += "\n  📡 Platforms:\n"
        for name, info in platforms.items():
            icon = '✅' if info.get('loaded') else '❌'
            output += f"    {icon} {name}\n"

        # On-chain
        oc = ctx.get('onchain', {})
        if oc.get('available'):
            output += f"\n  🔗 On-chain: {oc.get('eth_balance', 0):.4f} ETH"
            for sym, bal in oc.get('token_balances', {}).items():
                output += f" | {bal:,.0f} {sym}"
            output += "\n"

        return output

    # =========================================================================
    # Plugin Interface
    # =========================================================================

    def get_commands(self):
        """Return CLI commands"""
        return {
            'brain_think': self.think_command,
            'brain_start': self.start_command,
            'brain_stop': self.stop_command,
            'brain_moltx_image_post': self.moltx_image_post_command,
            'brain_moltx_post': self.moltx_post_command,
            'brain_context': self.context_command,
            'brain_actions': self.actions_command,
            'brain_history': self.history_command,
            'brain_status': self.status_command,
            'brain_reply': self.smart_reply_command,
            'brain_insights': self.feedback_insights_command,
            'brain_check_engagement': self.feedback_check_command,
            'brain_tracked': self.feedback_tracked_command,
            'brain_calendar': self.calendar_command,
            'brain_conversations': self.conversations_command,
            'brain_personality': self.personality_command,
            'brain_skills_status': self.skills_status_command,
            'brain_skills_generate': self.skills_generate_command,
            'brain_skills_update': self.skills_update_command,
            'brain_compose_chain': self.compose_chain_command,
            'brain_resilience': self.resilience_status_command,
            'brain_test_alert': self.test_alert_command,
            # Phase 10: Multi-agent
            'brain_detect_agents': self.detect_agents_command,
            'brain_agents_list': self.agents_list_command,
            'brain_agents_interact': self.agents_interact_command,
            'brain_agents_propose': self.agents_propose_command,
            'brain_agents_history': self.agents_history_command,
            # Phase 10: Reputation
            'brain_reputation': self.reputation_check_command,
            'brain_reputation_trends': self.reputation_trends_command,
            'brain_reputation_goals': self.reputation_goals_command,
            # Self-reflection
            'brain_reflect': self.reflection_run_command,
            'brain_reflect_summary': self.reflection_summary_command,
            # Goal Stack
            'brain_goals': self.goals_command,
            'brain_add_goal': self.add_goal_command,
            'brain_complete_goal': self.complete_goal_command,
            'brain_goal_stats': self.goal_stats_command,
            # World State
            'brain_world_status': self.world_status_command,
            'brain_world_entity': self.world_entity_command,
            'brain_world_facts': self.world_facts_command,
            'brain_world_relations': self.world_relations_command,
            'brain_world_search': self.world_search_command,
            'brain_world_events': self.world_events_command,
            'brain_world_trends': self.world_trends_command,
            'brain_world_cleanup': self.world_cleanup_command,
            'brain_world_sync': self.world_sync_command,
        }

    def get_tasks(self):
        """Return scheduled tasks"""
        return {
            'golden_window_queue_checker': {
                'function': self._check_golden_window_queue,
                'schedule': '*/5 * * * *',  # Every 5 minutes
                'description': 'Check Golden Window queue and execute actions at optimal timing'
            },
            'self_reflection': {
                'function': self._run_scheduled_reflection,
                'schedule': '0 2 * * *',  # Every day at 2 AM
                'description': 'Run self-reflection and update decision weights'
            },
            'world_state_cleanup': {
                'function': self._cleanup_expired_world_state,
                'schedule': '0 */6 * * *',  # Every 6 hours
                'description': 'Cleanup expired facts from World State'
            },
            'world_state_sync': {
                'function': self._sync_world_state,
                'schedule': '*/15 * * * *',  # Every 15 minutes
                'description': 'Sync all platforms to World State'
            }
        }
    
    def _run_scheduled_reflection(self):
        """Scheduled self-reflection task"""
        print("🧠 Running scheduled self-reflection...")
        result = self.run_self_reflection()
        insights = result.get('insights', [])
        if insights:
            print(f"💡 Generated {len(insights)} insights from reflection")
        else:
            print("📊 No new insights (not enough data yet)")
    
    def _check_golden_window_queue(self):
        """Scheduled task to check and execute queued Golden Window actions"""
        if hasattr(self, '_execute_queued_actions'):
            self._execute_queued_actions()

    def get_endpoints(self):
        """Return web endpoints"""
        return {}

    def cleanup(self):
        """Cleanup brain plugin"""
        self.stop_autonomous()
        self._save_decision_state()
        self._save_user_profiles()
        self._save_post_tracker()
        self._save_style_scores()
        self._save_content_calendar()
        self._save_conversation_threads()
        self._save_skill_state()
        self._save_personalities()
        self._save_resilience_state()
        self._save_collaboration_state()
        self._save_reputation_state()
        print("🧠 Brain plugin cleaned up")
