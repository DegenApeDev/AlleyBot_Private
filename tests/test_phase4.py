#!/usr/bin/env python3
"""
Phase 4 Tests - Self-Improvement capabilities
Tests git workflow, test gate, skill marketplace, and agentic integration.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# 4.1 - SelfImprove Plugin Structure
# =============================================================================

class TestSelfImprovePlugin(unittest.TestCase):
    """Verify SelfImprovePlugin structure and commands"""

    def test_plugin_imports(self):
        """SelfImprovePlugin should import without errors"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        self.assertTrue(SelfImprovePlugin)

    def test_plugin_mro(self):
        """MRO should include all mixins and AlleyBotPlugin"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        mro_names = [c.__name__ for c in SelfImprovePlugin.__mro__]
        self.assertIn('GitWorkflowMixin', mro_names)
        self.assertIn('TestGateMixin', mro_names)
        self.assertIn('SkillMarketplaceMixin', mro_names)
        self.assertIn('AlleyBotPlugin', mro_names)

    def test_plugin_inherits_base(self):
        """SelfImprovePlugin should inherit from AlleyBotPlugin"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        from plugin_manager import AlleyBotPlugin
        self.assertTrue(issubclass(SelfImprovePlugin, AlleyBotPlugin))

    def test_commands_registered(self):
        """All expected commands should be registered"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        cmds = p.get_commands()
        expected = [
            'improve', 'improve_status',
            'improve_branch', 'improve_commit', 'improve_done', 'improve_git',
            'improve_test', 'improve_gate', 'improve_sandbox',
            'improve_drafts', 'improve_approve', 'improve_deploy',
            'improve_market', 'improve_publish', 'improve_import', 'improve_market_status',
        ]
        for cmd in expected:
            self.assertIn(cmd, cmds, f"Missing command: {cmd}")

    def test_command_count(self):
        """Should have 18 commands (16 original + improve_skills + improve_build)"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        self.assertEqual(len(p.get_commands()), 18)

    def test_plugin_config_has_selfimprove(self):
        """plugin_config.json should include selfimprove plugin"""
        config_path = PROJECT_ROOT / 'plugin_config.json'
        with open(config_path) as f:
            config = json.load(f)
        self.assertIn('selfimprove', config)
        self.assertTrue(config['selfimprove']['enabled'])

    def test_module_file_structure(self):
        """All selfimprove plugin files should exist"""
        plugin_dir = PROJECT_ROOT / 'plugins' / 'selfimprove'
        expected = ['__init__.py', 'selfimprove.py', 'git_workflow.py',
                    'test_gate.py', 'skill_marketplace.py']
        for f in expected:
            self.assertTrue(
                (plugin_dir / f).exists(),
                f"Missing: plugins/selfimprove/{f}"
            )


# =============================================================================
# 4.2 - Git Workflow
# =============================================================================

class TestGitWorkflow(unittest.TestCase):
    """Verify git workflow functionality"""

    def test_git_workflow_mixin_methods(self):
        """GitWorkflowMixin should expose expected methods"""
        from plugins.selfimprove.git_workflow import GitWorkflowMixin
        methods = [
            'create_improvement_branch', 'commit_changes',
            'switch_back_to_base', 'git_branch_command',
            'git_commit_command', 'git_done_command', 'git_status_command',
        ]
        for m in methods:
            self.assertTrue(hasattr(GitWorkflowMixin, m), f"Missing method: {m}")

    def test_branch_command_no_args(self):
        """Branch command with no args should show usage"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        p.project_root = str(PROJECT_ROOT)
        p.active_branch = None
        p.branch_history = []
        result = p.git_branch_command()
        self.assertIn('Usage', result)

    def test_commit_command_no_args(self):
        """Commit command with no args should show usage"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        p.project_root = str(PROJECT_ROOT)
        result = p.git_commit_command()
        self.assertIn('Usage', result)

    def test_git_status_command(self):
        """Git status command should return formatted output"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        p.project_root = str(PROJECT_ROOT)
        p.branch_history = []
        result = p.git_status_command()
        self.assertIn('Git Workflow Status', result)
        self.assertIn('Branch', result)

    def test_commit_safety_non_auto_branch(self):
        """Should refuse to auto-commit on non-auto/ branches"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        p.project_root = str(PROJECT_ROOT)
        result = p.commit_changes("test commit")
        # Should fail because we're on opus_rebuild, not auto/*
        self.assertFalse(result['success'])
        self.assertIn('auto/', result['error'].lower())


# =============================================================================
# 4.3 - Test Gate
# =============================================================================

class TestTestGate(unittest.TestCase):
    """Verify test-before-merge gate functionality"""

    def test_test_gate_mixin_methods(self):
        """TestGateMixin should expose expected methods"""
        from plugins.selfimprove.test_gate import TestGateMixin
        methods = [
            'run_test_suite', 'validate_code_safety',
            'test_code_in_sandbox', 'merge_gate_check',
            'test_gate_command', 'merge_gate_command', 'sandbox_test_command',
        ]
        for m in methods:
            self.assertTrue(hasattr(TestGateMixin, m), f"Missing method: {m}")

    def test_validate_safe_code(self):
        """Safe code should pass validation"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        result = p.validate_code_safety("x = 1 + 2\nprint(x)")
        self.assertTrue(result['safe'])
        self.assertEqual(len(result['issues']), 0)

    def test_validate_unsafe_code_eval(self):
        """Code with eval() should fail validation"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        result = p.validate_code_safety("result = eval(user_input)")
        self.assertFalse(result['safe'])
        self.assertTrue(any('eval' in i.lower() for i in result['issues']))

    def test_validate_unsafe_code_os_system(self):
        """Code with os.system() should fail validation"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        result = p.validate_code_safety("import os\nos.system('rm -rf /')")
        self.assertFalse(result['safe'])

    def test_validate_syntax_error(self):
        """Code with syntax errors should fail validation"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        result = p.validate_code_safety("def foo(\n  broken")
        self.assertFalse(result['safe'])

    def test_sandbox_safe_code(self):
        """Safe code should pass sandbox test"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        p.project_root = str(PROJECT_ROOT)
        result = p.test_code_in_sandbox("x = 1 + 2\nprint(x)")
        self.assertTrue(result['success'])

    def test_sandbox_unsafe_code_blocked(self):
        """Unsafe code should be blocked by sandbox"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        p.project_root = str(PROJECT_ROOT)
        result = p.test_code_in_sandbox("eval('1+1')")
        self.assertFalse(result['success'])

    def test_run_test_suite(self):
        """Should be able to run the actual test suite"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        p.project_root = str(PROJECT_ROOT)
        # Run test_fixes (Phase 1, no network calls, always present)
        result = p.run_test_suite(['tests.test_fixes'])
        self.assertTrue(result['success'])
        self.assertGreater(result['tests_run'], 0)

    def test_sandbox_command_no_args(self):
        """Sandbox command with no args should show usage"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        result = p.sandbox_test_command()
        self.assertIn('Usage', result)


# =============================================================================
# 4.4 - Skill Marketplace
# =============================================================================

class TestSkillMarketplace(unittest.TestCase):
    """Verify skill marketplace functionality"""

    def test_marketplace_mixin_methods(self):
        """SkillMarketplaceMixin should expose expected methods"""
        from plugins.selfimprove.skill_marketplace import SkillMarketplaceMixin
        methods = [
            'publish_skill', 'import_skill', 'list_marketplace_skills',
            'marketplace_list_command', 'marketplace_publish_command',
            'marketplace_import_command', 'marketplace_status_command',
        ]
        for m in methods:
            self.assertTrue(hasattr(SkillMarketplaceMixin, m), f"Missing method: {m}")

    def test_marketplace_list_empty(self):
        """Empty marketplace should show helpful message"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        p.marketplace_dir = Path(tempfile.mkdtemp())
        result = p.marketplace_list_command()
        self.assertIn('empty', result.lower())

    def test_publish_command_no_args(self):
        """Publish command with no args should show helpful message"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        p.skills_dir = Path(tempfile.mkdtemp())
        result = p.marketplace_publish_command()
        # Either shows usage or tells user to generate skills first
        self.assertTrue('Usage' in result or 'No dynamic skills' in result)

    def test_import_command_no_args(self):
        """Import command with no args should show usage"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        result = p.marketplace_import_command()
        self.assertIn('Usage', result)

    def test_import_nonexistent_package(self):
        """Importing nonexistent package should error"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin
        p = SelfImprovePlugin({})
        p.marketplace_dir = Path(tempfile.mkdtemp())
        result = p.import_skill('nonexistent_skill')
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'].lower())

    def test_publish_and_import_roundtrip(self):
        """Should be able to publish and import a skill"""
        from plugins.selfimprove.selfimprove import SelfImprovePlugin

        p = SelfImprovePlugin({})
        tmp = Path(tempfile.mkdtemp())
        p.skills_dir = tmp / 'skills'
        p.skills_dir.mkdir()
        p.marketplace_dir = tmp / 'marketplace'
        p.marketplace_dir.mkdir()
        p.published_skills = {}
        p.imported_skills = {}

        # Create a fake skill
        skill_code = "def test_skill():\n    return {'success': True}\n"
        skill_file = p.skills_dir / 'test_roundtrip.py'
        skill_file.write_text(skill_code)

        registry = {'test_roundtrip': {
            'file': str(skill_file),
            'description': 'Test skill for roundtrip',
        }}
        (p.skills_dir / 'registry.json').write_text(json.dumps(registry))

        # Publish
        pub_result = p.publish_skill('test_roundtrip')
        self.assertTrue(pub_result['success'])

        # Import into a fresh directory
        p2 = SelfImprovePlugin({})
        p2.skills_dir = tmp / 'skills2'
        p2.skills_dir.mkdir()
        p2.marketplace_dir = p.marketplace_dir
        p2.imported_skills = {}

        imp_result = p2.import_skill('test_roundtrip')
        self.assertTrue(imp_result['success'])
        self.assertTrue((p2.skills_dir / 'test_roundtrip.py').exists())


# =============================================================================
# 4.5 - Agentic Integration
# =============================================================================

class TestAgenticIntegration(unittest.TestCase):
    """Verify self-improvement integration with agentic system"""

    def test_agentic_system_has_selfimprove_ref(self):
        """AgenticAlleyBot should reference selfimprove plugin"""
        source_file = PROJECT_ROOT / 'src' / 'agentic' / 'agentic_system.py'
        source = source_file.read_text()
        self.assertIn("selfimprove_plugin", source)
        self.assertIn("plugins.get('selfimprove')", source)

    def test_agentic_system_has_test_tool(self):
        """AgenticAlleyBot should have run_tests tool"""
        source_file = PROJECT_ROOT / 'src' / 'agentic' / 'agentic_system.py'
        source = source_file.read_text()
        self.assertIn('run_tests', source)
        self.assertIn('_run_tests_tool', source)

    def test_agentic_system_has_improve_tool(self):
        """AgenticAlleyBot should have self_improve tool"""
        source_file = PROJECT_ROOT / 'src' / 'agentic' / 'agentic_system.py'
        source = source_file.read_text()
        self.assertIn('self_improve', source)
        self.assertIn('_self_improve_tool', source)

    def test_autonomous_coder_exists(self):
        """autonomous_coder.py should exist at project root"""
        self.assertTrue((PROJECT_ROOT / 'autonomous_coder.py').exists())

    def test_autonomous_coder_importable(self):
        """AutonomousCoder should be importable"""
        from autonomous_coder import AutonomousCoder
        coder = AutonomousCoder()
        self.assertIsNotNone(coder)
        self.assertTrue(hasattr(coder, 'generate_code'))
        self.assertTrue(hasattr(coder, 'test_code'))
        self.assertTrue(hasattr(coder, 'approve_draft'))
        self.assertTrue(hasattr(coder, 'deploy_code'))


if __name__ == '__main__':
    unittest.main()
