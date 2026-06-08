#!/usr/bin/env python3
"""
Phase 2 Tests - Modularization verification
Tests plugin initialization, mixin splits, command registration,
memory unification, AI health checks, and entry point cleanup.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# 2.1 - Moltx Split Tests
# =============================================================================

class TestMoltxMixinSplit(unittest.TestCase):
    """Verify moltx.py split into mixins preserves all functionality"""

    def test_moltx_plugin_imports(self):
        """MoltxPlugin should import without errors"""
        from plugins.moltx.moltx import MoltxPlugin
        self.assertTrue(MoltxPlugin)

    def test_moltx_mro_contains_all_mixins(self):
        """MRO should include all four mixins and AlleyBotPlugin"""
        from plugins.moltx.moltx import MoltxPlugin
        mro_names = [c.__name__ for c in MoltxPlugin.__mro__]
        self.assertIn('MoltxAPIMixin', mro_names)
        self.assertIn('MoltxContentMixin', mro_names)
        self.assertIn('MoltxEngagementMixin', mro_names)
        self.assertIn('MoltxMessagingMixin', mro_names)
        self.assertIn('AlleyBotPlugin', mro_names)

    def test_moltx_api_mixin_methods(self):
        """MoltxAPIMixin should provide core API methods"""
        from plugins.moltx.moltx import MoltxPlugin
        p = MoltxPlugin({})
        api_methods = [
            '_init_api', '_make_request', 'register_agent', 'claim_agent',
            'upload_media', 'upload_avatar', 'upload_banner', 'update_profile',
            '_load_credentials', '_save_credentials', '_fetch_agent_info',
            '_update_claim_status', 'check_status', 'get_status',
            '_record_activity', '_should_wait_for_post_cooldown', '_get_activity',
            'get_agent_stats', 'get_own_profile',
        ]
        for method in api_methods:
            self.assertTrue(hasattr(p, method), f"Missing API method: {method}")

    def test_moltx_content_mixin_methods(self):
        """MoltxContentMixin should provide content creation methods"""
        from plugins.moltx.moltx import MoltxPlugin
        p = MoltxPlugin({})
        content_methods = [
            'create_post', '_is_topic_request', '_generate_post_with_deepseek',
            '_generate_comment', '_generate_local_comment',
            '_generate_reply_to_comment', '_get_dynamic_trending_topics',
            '_get_fallback_trending_topics', '_generate_dynamic_topic',
            '_analyze_posts_for_repost', '_generate_repost_comment',
            '_generate_fallback_repost_comment', '_parse_feed_posts',
        ]
        for method in content_methods:
            self.assertTrue(hasattr(p, method), f"Missing content method: {method}")

    def test_moltx_engagement_mixin_methods(self):
        """MoltxEngagementMixin should provide engagement methods"""
        from plugins.moltx.moltx import MoltxPlugin
        p = MoltxPlugin({})
        engagement_methods = [
            'get_feed', 'follow_agent', 'unfollow_agent', 'like_post',
            'get_notifications', '_heartbeat', '_heartbeat_follow_agents',
            '_heartbeat_engage_posts', '_heartbeat_monitor_and_reply',
            '_is_engaged_user', '_heartbeat_post_useful',
            'engage_feed_command', 'reply_to_post_command', 'repost_command',
            'intelligent_repost_command', 'trending_command', 'leaderboard_command',
            'search_communities', 'join_community', 'leave_community',
            'send_community_message',
        ]
        for method in engagement_methods:
            self.assertTrue(hasattr(p, method), f"Missing engagement method: {method}")

    def test_moltx_messaging_mixin_methods(self):
        """MoltxMessagingMixin should provide DM methods"""
        from plugins.moltx.moltx import MoltxPlugin
        p = MoltxPlugin({})
        messaging_methods = [
            'get_dms', 'reply_to_dm', 'generate_dm_reply',
            'check_and_reply_to_dms', '_log_dm_activity', 'get_dm_log',
        ]
        for method in messaging_methods:
            self.assertTrue(hasattr(p, method), f"Missing messaging method: {method}")

    def test_moltx_commands_registered(self):
        """All expected commands should be registered"""
        from plugins.moltx.moltx import MoltxPlugin
        p = MoltxPlugin({})
        cmds = p.get_commands()
        expected_commands = [
            'moltx_register', 'moltx_claim', 'moltx_status', 'moltx_post',
            'moltx_feed', 'moltx_follow', 'moltx_unfollow', 'moltx_like',
            'moltx_notifications', 'moltx_dms', 'moltx_reply_dm',
            'moltx_check_dms', 'moltx_dm_log', 'moltx_heartbeat',
            'moltx_avatar', 'moltx_banner', 'moltx_profile', 'moltx_engage',
            'moltx_reply', 'moltx_repost', 'moltx_intelligent_repost',
            'moltx_leaderboard', 'moltx_intelligent_post', 'moltx_trending',
            'moltx_search_communities', 'moltx_join_community',
            'moltx_leave_community', 'moltx_community_message',
        ]
        for cmd in expected_commands:
            self.assertIn(cmd, cmds, f"Missing command: {cmd}")

    def test_moltx_tasks_registered(self):
        """All expected tasks should be registered"""
        from plugins.moltx.moltx import MoltxPlugin
        p = MoltxPlugin({})
        tasks = p.get_tasks()
        expected_tasks = [
            'moltx_heartbeat', 'moltx_feed_engage', 'moltx_intelligent_post',
            'moltx_trending_analysis', 'moltx_intelligent_repost', 'moltx_dm_monitor',
        ]
        for task in expected_tasks:
            self.assertIn(task, tasks, f"Missing task: {task}")

    def test_moltx_init_sets_api_fields(self):
        """MoltxPlugin __init__ should set API fields via _init_api"""
        from plugins.moltx.moltx import MoltxPlugin
        p = MoltxPlugin({})
        self.assertEqual(p.base_url, "https://moltx.io/v1")
        self.assertIsNotNone(p.credentials_file)
        self.assertFalse(p.initialized)

    def test_moltx_uninitialized_guards(self):
        """Methods should return error when not initialized"""
        from plugins.moltx.moltx import MoltxPlugin
        p = MoltxPlugin({})
        p.initialized = False
        self.assertIn("❌", p.like_post("some-id"))
        self.assertIn("❌", p.follow_agent("someone"))
        self.assertIn("❌", p.get_notifications())

    def test_moltx_like_post_json_extraction(self):
        """like_post should extract post_id from JSON-formatted input"""
        from plugins.moltx.moltx import MoltxPlugin
        p = MoltxPlugin({})
        p.initialized = True
        p._make_request = MagicMock(return_value=None)
        p._record_activity = MagicMock()
        # Pass JSON-formatted post_id
        result = p.like_post('{"post_id": "abc-123"}')
        # Should have called _make_request with extracted ID
        call_args = p._make_request.call_args
        self.assertIn('abc-123', call_args[0][1])

    def test_moltx_slim_file_size(self):
        """moltx.py should be under 300 lines (slim orchestrator)"""
        moltx_file = PROJECT_ROOT / 'plugins' / 'moltx' / 'moltx.py'
        line_count = len(moltx_file.read_text().splitlines())
        self.assertLess(line_count, 300, f"moltx.py is {line_count} lines, should be <300")


# =============================================================================
# 2.2 - Moltbook Split Tests
# =============================================================================

class TestMoltbookMixinSplit(unittest.TestCase):
    """Verify moltbook.py split into mixins preserves all functionality"""

    def test_moltbook_plugin_imports(self):
        """MoltbookPlugin should import without errors"""
        from plugins.moltbook.moltbook import MoltbookPlugin
        self.assertTrue(MoltbookPlugin)

    def test_moltbook_mro_contains_all_mixins(self):
        """MRO should include all three mixins and AlleyBotPlugin"""
        from plugins.moltbook.moltbook import MoltbookPlugin
        mro_names = [c.__name__ for c in MoltbookPlugin.__mro__]
        self.assertIn('MoltbookAPIMixin', mro_names)
        self.assertIn('MoltbookContentMixin', mro_names)
        self.assertIn('MoltbookEngagementMixin', mro_names)
        self.assertIn('AlleyBotPlugin', mro_names)

    def test_moltbook_api_mixin_methods(self):
        """MoltbookAPIMixin should provide API methods"""
        from plugins.moltbook.moltbook import MoltbookPlugin
        p = MoltbookPlugin({})
        api_methods = [
            '_init_moltbook_api', '_get_feed_posts', '_get_post_comments',
            '_upvote_post', '_record_post', 'delete_post_command', 'list_recent_posts',
        ]
        for method in api_methods:
            self.assertTrue(hasattr(p, method), f"Missing API method: {method}")

    def test_moltbook_content_mixin_methods(self):
        """MoltbookContentMixin should provide content methods"""
        from plugins.moltbook.moltbook import MoltbookPlugin
        p = MoltbookPlugin({})
        content_methods = [
            'create_intelligent_post', 'create_post_command', '_is_topic_request',
            '_generate_post_with_deepseek', 'create_draft', 'announce_token',
            'show_trending_topics', '_get_trending_topics', '_generate_fallback_post',
            '_generate_title_from_content', '_extract_tags_from_topic',
        ]
        for method in content_methods:
            self.assertTrue(hasattr(p, method), f"Missing content method: {method}")

    def test_moltbook_engagement_mixin_methods(self):
        """MoltbookEngagementMixin should provide engagement methods"""
        from plugins.moltbook.moltbook import MoltbookPlugin
        p = MoltbookPlugin({})
        engagement_methods = [
            'moltbook_heartbeat', '_is_recent_post', '_should_engage_with_post',
            '_engage_with_post', '_create_intelligent_comment', '_record_engagement',
            '_record_heartbeat_activity', 'monitor_comments_and_reply',
            '_filter_comments_for_reply', '_generate_moltbook_reply',
            '_record_reply_activity', 'moltbook_status', 'get_moltbook_stats',
        ]
        for method in engagement_methods:
            self.assertTrue(hasattr(p, method), f"Missing engagement method: {method}")

    def test_moltbook_commands_registered(self):
        """All expected commands should be registered"""
        from plugins.moltbook.moltbook import MoltbookPlugin
        p = MoltbookPlugin({})
        cmds = p.get_commands()
        expected = [
            'moltbook_post', 'moltbook_draft', 'moltbook_trending',
            'moltbook_status', 'moltbook_heartbeat', 'moltbook_stats',
            'moltbook_announce', 'moltbook_delete', 'moltbook_list',
            'moltbook_monitor_comments',
        ]
        for cmd in expected:
            self.assertIn(cmd, cmds, f"Missing command: {cmd}")

    def test_moltbook_tasks_registered(self):
        """Tasks should be registered with correct config"""
        from plugins.moltbook.moltbook import MoltbookPlugin
        p = MoltbookPlugin({'heartbeat_enabled': True, 'comment_monitoring_enabled': True})
        tasks = p.get_tasks()
        self.assertIn('moltbook_heartbeat', tasks)
        self.assertIn('moltbook_comment_monitor', tasks)

    def test_moltbook_api_client_class(self):
        """MoltbookAPIClient should be importable from moltbook_api"""
        from plugins.moltbook.moltbook_api import MoltbookAPIClient
        client = MoltbookAPIClient('test-key', 'https://example.com/api')
        self.assertEqual(client.api_key, 'test-key')
        self.assertEqual(client.base_url, 'https://example.com/api')

    def test_moltbook_content_helpers(self):
        """Content helper methods should work standalone"""
        from plugins.moltbook.moltbook_content import MoltbookContentMixin

        class Stub(MoltbookContentMixin):
            pass

        s = Stub()
        self.assertTrue(s._is_topic_request("thoughts on AI agents"))
        self.assertFalse(s._is_topic_request("hello world"))
        self.assertEqual(s._extract_tags_from_topic("blockchain scalability"), ['blockchain', 'scalability'])


# =============================================================================
# 2.3 - Memory Unification Tests
# =============================================================================

class TestMemoryUnification(unittest.TestCase):
    """Verify unified memory system in alleybot_core"""

    def test_core_has_enhanced_memory_attr(self):
        """AlleyBotCore class should define enhanced_memory attribute"""
        import inspect
        from alleybot_core import AlleyBotCore
        source = inspect.getsource(AlleyBotCore.__init__)
        self.assertIn('enhanced_memory', source)

    def test_core_exposes_semantic_memory_methods(self):
        """AlleyBotCore should expose semantic memory helper methods"""
        from alleybot_core import AlleyBotCore
        methods = [
            'add_semantic_memory', 'search_memories', 'add_goal',
            'get_active_goals', 'store_sensitive', 'get_sensitive',
            'get_memory_stats',
        ]
        for method in methods:
            self.assertTrue(hasattr(AlleyBotCore, method), f"Missing method: {method}")

    def test_core_preserves_json_memory_interface(self):
        """get_memory/save_memory should still exist for backward compat"""
        from alleybot_core import AlleyBotCore
        self.assertTrue(hasattr(AlleyBotCore, 'get_memory'))
        self.assertTrue(hasattr(AlleyBotCore, 'save_memory'))

    def test_agentic_system_reuses_core_memory(self):
        """AgenticAlleyBot should reuse core.enhanced_memory when available"""
        try:
            import inspect
            from src.agentic.agentic_system import AgenticAlleyBot
            source = inspect.getsource(AgenticAlleyBot.__init__)
            self.assertIn('core.enhanced_memory', source)
            self.assertIn('Reusing', source)
        except Exception:
            # LangChain/pydantic may fail on Python 3.14+
            # Fall back to reading the source file directly
            source_file = PROJECT_ROOT / 'src' / 'agentic' / 'agentic_system.py'
            source = source_file.read_text()
            self.assertIn('core.enhanced_memory', source)
            self.assertIn('Reusing', source)

    def test_enhanced_memory_import_guard(self):
        """Core should handle missing enhanced memory deps gracefully"""
        import alleybot_core
        # The module-level try/except should define ENHANCED_MEMORY_AVAILABLE
        self.assertTrue(hasattr(alleybot_core, 'ENHANCED_MEMORY_AVAILABLE'))


# =============================================================================
# 2.4 - Entry Point Cleanup Tests
# =============================================================================

class TestEntryPointCleanup(unittest.TestCase):
    """Verify stale scripts archived and single entry point exists"""

    def test_run_alleybot_exists(self):
        """run_alleybot.py should be the single entry point"""
        entry = PROJECT_ROOT / 'run_alleybot.py'
        self.assertTrue(entry.exists())

    def test_stale_scripts_archived(self):
        """Stale standalone scripts should be in archive_old_files/"""
        archived_scripts = [
            'announce_moltbook.py', 'fix_display_name.py', 'legacy_main.py',
            'moltx_token_announcement.py', 'self_improvement_v2.py',
            'upload_avatar.py', 'debug_skill.py', 'debug_skill_generation.py',
            'add_mcp_config.py', 'telegram_listener.py',
        ]
        archive_dir = PROJECT_ROOT / 'archive_old_files'
        for script in archived_scripts:
            self.assertTrue(
                (archive_dir / script).exists(),
                f"{script} should be archived in archive_old_files/"
            )

    def test_stale_scripts_not_at_root(self):
        """Archived scripts should not exist at project root"""
        stale_scripts = [
            'announce_moltbook.py', 'fix_display_name.py', 'legacy_main.py',
            'moltx_token_announcement.py', 'self_improvement_v2.py',
            'upload_avatar.py', 'debug_skill.py', 'debug_skill_generation.py',
            'add_mcp_config.py',
        ]
        for script in stale_scripts:
            self.assertFalse(
                (PROJECT_ROOT / script).exists(),
                f"{script} should not be at project root"
            )

    def test_root_py_count_reduced(self):
        """Root directory should have <=25 .py files (down from 43)"""
        py_files = list(PROJECT_ROOT.glob('*.py'))
        self.assertLessEqual(
            len(py_files), 25,
            f"Root has {len(py_files)} .py files, expected <=25"
        )

    def test_test_scripts_archived(self):
        """Root-level test_*.py scripts should be archived"""
        archived_tests = [
            'test_aggregator.py', 'test_api_response.py', 'test_grok_dm.py',
            'test_mcp.py', 'test_mcp_intelligence.py', 'test_moltbook_api.py',
            'test_security_guardrails.py', 'test_skill_generation.py',
            'test_telegram.py', 'test_telegram_connection.py',
        ]
        archive_dir = PROJECT_ROOT / 'archive_old_files'
        for script in archived_tests:
            self.assertTrue(
                (archive_dir / script).exists(),
                f"{script} should be archived in archive_old_files/"
            )


# =============================================================================
# AI Health Checks
# =============================================================================

class TestAIHealthChecks(unittest.TestCase):
    """Verify AI modules (DeepSeek, Grok) are importable and configurable"""

    def test_deepseek_ai_importable(self):
        """deepseek_ai module should import without errors"""
        from deepseek_ai import DeepSeekAI
        self.assertTrue(DeepSeekAI)

    def test_deepseek_disabled_without_key(self):
        """DeepSeekAI should be disabled when API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('DEEPSEEK_API_KEY', None)
            from deepseek_ai import DeepSeekAI
            ds = DeepSeekAI()
            self.assertFalse(ds.enabled)

    def test_deepseek_enabled_with_key(self):
        """DeepSeekAI should be enabled when API key is present"""
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'}):
            from deepseek_ai import DeepSeekAI
            ds = DeepSeekAI()
            self.assertTrue(ds.enabled)

    def test_grok_ai_importable(self):
        """grok_ai module should import without errors"""
        from grok_ai import GrokAI
        self.assertTrue(GrokAI)

    def test_grok_disabled_without_key(self):
        """GrokAI should be disabled when API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('XAI_API_KEY', None)
            from grok_ai import GrokAI
            grok = GrokAI()
            self.assertFalse(grok.enabled)

    def test_grok_enabled_with_key(self):
        """GrokAI should be enabled when API key is present"""
        with patch.dict(os.environ, {'XAI_API_KEY': 'test-key'}):
            from grok_ai import GrokAI
            grok = GrokAI()
            self.assertTrue(grok.enabled)

    def test_grok_has_generate_methods(self):
        """GrokAI should have all generation methods"""
        with patch.dict(os.environ, {'XAI_API_KEY': 'test-key'}):
            from grok_ai import GrokAI
            grok = GrokAI()
            self.assertTrue(hasattr(grok, 'generate_comment'))
            self.assertTrue(hasattr(grok, 'generate_post'))
            self.assertTrue(hasattr(grok, 'generate_dm_reply'))
            self.assertTrue(hasattr(grok, '_make_api_request'))

    def test_deepseek_has_generate_methods(self):
        """DeepSeekAI should have all generation methods"""
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'}):
            from deepseek_ai import DeepSeekAI
            ds = DeepSeekAI()
            self.assertTrue(hasattr(ds, 'generate_comment'))
            self.assertTrue(hasattr(ds, 'generate_reply_to_comment'))


# =============================================================================
# Plugin Manager & Core Infrastructure
# =============================================================================

class TestPluginInfrastructure(unittest.TestCase):
    """Verify plugin manager and base class work correctly"""

    def test_alleybot_plugin_base_class(self):
        """AlleyBotPlugin should define required interface methods"""
        from plugin_manager import AlleyBotPlugin
        p = AlleyBotPlugin({})
        self.assertTrue(hasattr(p, 'get_tasks'))
        self.assertTrue(hasattr(p, 'get_commands'))
        self.assertTrue(hasattr(p, 'get_endpoints'))
        self.assertTrue(hasattr(p, 'cleanup'))
        self.assertTrue(hasattr(p, 'initialize'))

    def test_plugin_manager_importable(self):
        """PluginManager should import without errors"""
        from plugin_manager import PluginManager
        pm = PluginManager()
        self.assertIsNotNone(pm)

    def test_moltx_inherits_alleybot_plugin(self):
        """MoltxPlugin should inherit from AlleyBotPlugin"""
        from plugins.moltx.moltx import MoltxPlugin
        from plugin_manager import AlleyBotPlugin
        self.assertTrue(issubclass(MoltxPlugin, AlleyBotPlugin))

    def test_moltbook_inherits_alleybot_plugin(self):
        """MoltbookPlugin should inherit from AlleyBotPlugin"""
        from plugins.moltbook.moltbook import MoltbookPlugin
        from plugin_manager import AlleyBotPlugin
        self.assertTrue(issubclass(MoltbookPlugin, AlleyBotPlugin))

    def test_config_module_importable(self):
        """config.py should import without errors"""
        import config
        self.assertTrue(hasattr(config, 'MOLTX_API_KEY'))


# =============================================================================
# Mixin Module File Structure
# =============================================================================

class TestModuleFileStructure(unittest.TestCase):
    """Verify the file structure after modularization"""

    def test_moltx_module_files_exist(self):
        """All moltx mixin files should exist"""
        moltx_dir = PROJECT_ROOT / 'plugins' / 'moltx'
        expected = ['moltx.py', 'moltx_api.py', 'moltx_content.py',
                    'moltx_engagement.py', 'moltx_messaging.py']
        for f in expected:
            self.assertTrue((moltx_dir / f).exists(), f"Missing: plugins/moltx/{f}")

    def test_no_old_monolith_files(self):
        """Old monolith backup files should not exist"""
        self.assertFalse((PROJECT_ROOT / 'plugins' / 'moltx' / 'moltx_old_monolith.py').exists())

    def test_mixin_files_have_docstrings(self):
        """Each mixin file should have a module docstring"""
        mixin_files = [
            PROJECT_ROOT / 'plugins' / 'moltx' / 'moltx_api.py',
            PROJECT_ROOT / 'plugins' / 'moltx' / 'moltx_content.py',
            PROJECT_ROOT / 'plugins' / 'moltx' / 'moltx_engagement.py',
            PROJECT_ROOT / 'plugins' / 'moltx' / 'moltx_messaging.py',
        ]
        for filepath in mixin_files:
            content = filepath.read_text()
            self.assertTrue(
                content.startswith('"""') or content.startswith("'''"),
                f"{filepath.name} should have a module docstring"
            )


if __name__ == '__main__':
    unittest.main()
