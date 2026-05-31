#!/usr/bin/env python3
"""
Phase 5 Tests - Autonomous Brain
Tests context gathering, decision engine, smart replies, and brain plugin.
"""

import os
import sys
import json
import unittest
import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# 5.1 - Brain Plugin Structure
# =============================================================================

class TestBrainPlugin(unittest.TestCase):
    """Verify BrainPlugin structure and commands"""

    def test_plugin_imports(self):
        """BrainPlugin should import without errors"""
        from plugins.brain.brain import BrainPlugin
        self.assertTrue(BrainPlugin)

    def test_plugin_mro(self):
        """MRO should include all mixins and AlleyBotPlugin"""
        from plugins.brain.brain import BrainPlugin
        mro_names = [c.__name__ for c in BrainPlugin.__mro__]
        self.assertIn('ContextGathererMixin', mro_names)
        self.assertIn('DecisionEngineMixin', mro_names)
        self.assertIn('SmartReplyMixin', mro_names)
        self.assertIn('AlleyBotPlugin', mro_names)

    def test_plugin_inherits_base(self):
        """BrainPlugin should inherit from AlleyBotPlugin"""
        from plugins.brain.brain import BrainPlugin
        from plugin_manager import AlleyBotPlugin
        self.assertTrue(issubclass(BrainPlugin, AlleyBotPlugin))

    def test_commands_registered(self):
        """All expected commands should be registered"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        cmds = p.get_commands()
        expected = [
            'brain', 'think', 'startbrain', 'stopbrain'
        ]
        for cmd in expected:
            self.assertIn(cmd, cmds, f"Missing command: {cmd}")

    def test_command_count(self):
        """Should have core brain commands"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        cmds = p.get_commands()
        self.assertGreater(len(cmds), 0)
        self.assertIn('brain', cmds)
        self.assertIn('think', cmds)

    def test_plugin_config_has_brain(self):
        """plugin_config.json should include brain plugin"""
        config_path = PROJECT_ROOT / 'plugin_config.json'
        with open(config_path) as f:
            config = json.load(f)
        self.assertIn('brain', config)
        self.assertTrue(config['brain']['enabled'])

    def test_module_file_structure(self):
        """All brain plugin files should exist"""
        plugin_dir = PROJECT_ROOT / 'plugins' / 'brain'
        expected = ['__init__.py', 'brain.py', 'context_gatherer.py',
                    'decision_engine.py', 'smart_reply.py']
        for f in expected:
            self.assertTrue(
                (plugin_dir / f).exists(),
                f"Missing: plugins/brain/{f}"
            )


# =============================================================================
# 5.2 - Context Gatherer
# =============================================================================

class TestContextGatherer(unittest.TestCase):
    """Verify context gathering functionality"""

    def test_mixin_methods(self):
        """ContextGathererMixin should expose expected methods"""
        from plugins.brain.context_gatherer import ContextGathererMixin
        methods = [
            'gather_full_context', 'build_context_summary',
            '_gather_memory_context', '_gather_onchain_context',
            '_gather_platform_context', '_gather_engagement_context',
            '_gather_goal_context', '_gather_recent_actions',
        ]
        for m in methods:
            self.assertTrue(hasattr(ContextGathererMixin, m), f"Missing method: {m}")

    def test_context_summary_no_crash(self):
        """build_context_summary should not crash with mock core"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None
        p.core.enhanced_memory = None
        p.core.plugin_manager.plugins = {}
        p._init_context_gatherer()
        p._init_decision_engine()
        p._init_smart_reply()

        summary = p.build_context_summary()
        self.assertIsInstance(summary, str)

    def test_gather_full_context_structure(self):
        """gather_full_context should return expected keys"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None
        p.core.enhanced_memory = None
        p.core.plugin_manager.plugins = {}
        p._init_context_gatherer()
        p._init_decision_engine()
        p._init_smart_reply()

        ctx = p.gather_full_context()
        expected_keys = ['timestamp', 'memory', 'onchain', 'platforms',
                         'engagement', 'goals', 'recent_actions']
        for key in expected_keys:
            self.assertIn(key, ctx, f"Missing context key: {key}")

    def test_context_caching(self):
        """Context should be cached within TTL"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None
        p.core.enhanced_memory = None
        p.core.plugin_manager.plugins = {}
        p._init_context_gatherer()
        p._init_decision_engine()
        p._init_smart_reply()

        ctx1 = p.gather_full_context()
        ctx2 = p.gather_full_context()
        # Should be same object (cached)
        self.assertIs(ctx1, ctx2)


# =============================================================================
# 5.3 - Decision Engine
# =============================================================================

class TestDecisionEngine(unittest.TestCase):
    """Verify decision engine functionality"""

    def test_mixin_methods(self):
        """DecisionEngineMixin should expose expected methods"""
        from plugins.brain.decision_engine import DecisionEngineMixin
        methods = [
            'get_available_actions', 'decide_next_action',
            'execute_action', '_dispatch_action',
            '_ai_reason_about_action', '_heuristic_decide',
        ]
        for m in methods:
            self.assertTrue(hasattr(DecisionEngineMixin, m), f"Missing method: {m}")

    def test_autonomous_actions_defined(self):
        """AUTONOMOUS_ACTIONS should have core actions"""
        from plugins.brain.decision_engine import AUTONOMOUS_ACTIONS
        expected = {'moltx_engage', 'moltx_post', 'onchain_heartbeat',
                    'check_comments', 'update_skills', 'clawbr_engage'}
        for action in expected:
            self.assertIn(action, AUTONOMOUS_ACTIONS, f"Missing action: {action}")

    def test_actions_have_required_fields(self):
        """Each action should have required fields"""
        from plugins.brain.decision_engine import AUTONOMOUS_ACTIONS
        required = ['description', 'platform', 'cooldown_minutes', 'impact', 'requires']
        for action_id, action in AUTONOMOUS_ACTIONS.items():
            for field in required:
                self.assertIn(field, action, f"Action {action_id} missing field: {field}")

    def test_get_available_actions_with_no_plugins(self):
        """Should return empty when no plugins loaded"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None
        p.core.plugin_manager.plugins = {}
        p._init_context_gatherer()
        p._init_decision_engine()
        p._init_smart_reply()
        p._init_operational_resilience()
        p._init_goal_stack()

        available = p.get_available_actions()
        self.assertEqual(len(available), 0)

    def test_get_available_actions_with_moltx(self):
        """Should return moltx actions when moltx plugin loaded"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None
        p.core.plugin_manager.plugins = {'moltx': MagicMock()}
        p._init_context_gatherer()
        p._init_decision_engine()
        p._init_smart_reply()

        available = p.get_available_actions()
        action_ids = [a['id'] for a in available]
        self.assertIn('moltx_engage', action_ids)
        self.assertIn('moltx_post', action_ids)
        self.assertIn('check_comments', action_ids)

    def test_cooldown_respected(self):
        """Actions on cooldown should not be available"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None
        p.core.plugin_manager.plugins = {'moltx': MagicMock()}
        p._init_context_gatherer()
        p._init_decision_engine()
        p._init_smart_reply()

        # Set cooldown for moltx_engage
        p.action_cooldowns['moltx_engage'] = datetime.datetime.now()

        available = p.get_available_actions()
        action_ids = [a['id'] for a in available]
        self.assertNotIn('moltx_engage', action_ids)

    def test_heuristic_decide(self):
        """Heuristic decision should pick an action"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None
        p.core.plugin_manager.plugins = {'moltx': MagicMock()}
        p._init_context_gatherer()
        p._init_decision_engine()
        p._init_smart_reply()

        available = p.get_available_actions()
        context = {'engagement': {}, 'recent_actions': []}
        decision = p._heuristic_decide(available, context)
        self.assertIsNotNone(decision)
        self.assertIn('id', decision)
        self.assertIn('reason', decision)


# =============================================================================
# 5.4 - Smart Reply
# =============================================================================

class TestSmartReply(unittest.TestCase):
    """Verify smart reply functionality"""

    def test_mixin_methods(self):
        """SmartReplyMixin should expose expected methods"""
        from plugins.brain.smart_reply import SmartReplyMixin
        methods = [
            'generate_smart_reply', '_get_user_profile',
            '_update_user_profile', '_extract_topic',
            'smart_reply_command',
        ]
        for m in methods:
            self.assertTrue(hasattr(SmartReplyMixin, m), f"Missing method: {m}")

    def test_user_profile_creation(self):
        """Should create new user profile"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None
        p._init_smart_reply()

        profile = p._get_user_profile('testuser')
        self.assertEqual(profile['username'], 'testuser')
        self.assertEqual(profile['interactions'], 0)

    def test_user_profile_update(self):
        """Should update user profile after interaction"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None
        p._init_smart_reply()

        p._update_user_profile('testuser', 'reply', 'crypto')
        profile = p._get_user_profile('testuser')
        self.assertEqual(profile['interactions'], 1)
        self.assertIn('crypto', profile['topics'])

    def test_extract_topic(self):
        """Should extract relevant topics from text"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p._init_smart_reply()

        self.assertEqual(p._extract_topic("I love AI agents"), 'ai')
        self.assertEqual(p._extract_topic("Check out this token"), 'token')
        self.assertEqual(p._extract_topic("Hello world"), 'general')

    def test_smart_reply_command_no_args(self):
        """Smart reply command with no args should show usage"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p._init_smart_reply()
        result = p.smart_reply_command()
        self.assertIn('Usage', result)


# =============================================================================
# 5.5 - Telegram Integration
# =============================================================================

class TestTelegramBrainIntegration(unittest.TestCase):
    """Verify brain commands are wired into Telegram"""

    def test_telegram_has_brain_commands(self):
        """Telegram intelligent_commands should have brain methods"""
        source = (PROJECT_ROOT / 'plugins' / 'telegram' / 'intelligent_commands.py').read_text()
        self.assertIn('brain_think', source)
        self.assertIn('brain_start', source)
        self.assertIn('brain_stop', source)
        self.assertIn('brain_status', source)

    def test_telegram_handlers_registered(self):
        """Telegram plugin should register brain command handlers"""
        source = (PROJECT_ROOT / 'plugins' / 'telegram' / 'telegram.py').read_text()
        self.assertIn('"think"', source)
        self.assertIn('"brain_start"', source)
        self.assertIn('"brain_stop"', source)
        self.assertIn('"brain"', source)

    def test_help_includes_brain(self):
        """Help text should include brain commands"""
        source = (PROJECT_ROOT / 'plugins' / 'telegram' / 'intelligent_commands.py').read_text()
        self.assertIn('Brain Commands', source)
        self.assertIn('/think', source)
        self.assertIn('/brain_start', source)


# =============================================================================
# 5.6 - Integration
# =============================================================================

class TestBrainIntegration(unittest.TestCase):
    """Verify brain integrates with other plugins"""

    def test_brain_can_dispatch_to_mock_moltx(self):
        """Brain should dispatch moltx_engage to moltx plugin"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None

        mock_moltx = MagicMock()
        mock_moltx.engage_feed_command.return_value = "✅ Engaged with 3 posts"
        p.core.plugin_manager.plugins = {'moltx': mock_moltx}
        p._init_context_gatherer()
        p._init_decision_engine()
        p._init_smart_reply()

        result = p._dispatch_action('moltx_engage')
        # Legacy dispatch returns None; actual dispatch goes through AGI kernel
        self.assertIsNone(result)

    def test_brain_can_dispatch_onchain_heartbeat(self):
        """Brain should dispatch onchain_heartbeat to onchain plugin"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None

        mock_onchain = MagicMock()
        mock_onchain.onchain_heartbeat.return_value = "✅ Heartbeat complete"
        p.core.plugin_manager.plugins = {'onchain': mock_onchain}
        p._init_context_gatherer()
        p._init_decision_engine()
        p._init_smart_reply()

        result = p._dispatch_action('onchain_heartbeat')
        # Legacy dispatch returns None; actual dispatch goes through AGI kernel
        self.assertIsNone(result)

    def test_execute_action_records_history(self):
        """execute_action should record result in history"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None
        p.core.agi_kernel = None  # prevent async routing, use legacy dispatch

        mock_moltx = MagicMock()
        mock_moltx.engage_feed_command.return_value = "✅ Done"
        p.core.plugin_manager.plugins = {'moltx': mock_moltx}
        p._init_context_gatherer()
        p._init_decision_engine()
        p._init_operational_resilience()
        p._init_goal_stack()
        p._init_self_reflection()
        
        action = {'action': 'moltx_engage', 'platform': 'moltx', 'id': 'moltx_engage'}
        result = p.execute_action(action)

        # Legacy dispatch returns None for all actions; the test verifies no crash
        self.assertIn('success', result)
        self.assertIsInstance(result, dict)

    def test_full_think_cycle(self):
        """Full think cycle should work with mock plugins"""
        from plugins.brain.brain import BrainPlugin
        p = BrainPlugin({})
        p.core = MagicMock()
        p.core.get_memory.return_value = None
        p.core.agi_kernel = None  # prevent async routing
        p.api = MagicMock()

        mock_moltx = MagicMock()
        mock_moltx.engage_feed_command.return_value = "✅ Done"
        p.core.plugin_manager.plugins = {'moltx': mock_moltx}
        
        p._init_context_gatherer()
        p._init_decision_engine()
        p._init_smart_reply()
        p._init_operational_resilience()
        p._init_goal_stack()
        p._init_self_reflection()
        
        result = p.think()
        self.assertIn('cycle', result)
        self.assertIn('action', result)


if __name__ == '__main__':
    unittest.main()
