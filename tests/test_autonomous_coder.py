#!/usr/bin/env python3
"""Tests for AutonomousCoder: _generate_generic scaffolds, get_best_coder, fallback."""

import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.autonomous_coder import (
    AutonomousCoder, SkillSpecification, get_best_coder,
    generate_skill_with_fallback,
)


class TestAutonomousCoderGenerateGeneric(unittest.TestCase):
    def setUp(self):
        self.coder = AutonomousCoder()
        self.spec = SkillSpecification(
            id='test_skill',
            name='Test Skill',
            description='A test skill',
            category='test',
            file_structure={},
        )

    def test_generate_generic_api_keyword(self):
        content = self.coder._generate_generic(self.spec, "API client for external service")
        self.assertIn('ApiClient', content)
        self.assertIn('aiohttp', content)
        self.assertIn('class ApiClient', content)
        self.assertNotIn('TODO', content)

    def test_generate_generic_handler_keyword(self):
        content = self.coder._generate_generic(self.spec, "Command handler for processing")
        self.assertIn('CommandHandler', content)
        self.assertIn('class Command', content)
        self.assertNotIn('TODO', content)

    def test_generate_generic_processor_keyword(self):
        # "processor" triggers the CommandHandler branch
        content = self.coder._generate_generic(self.spec, "Data processor module")
        self.assertIn('CommandHandler', content)
        self.assertNotIn('TODO', content)

    def test_generate_generic_default_branch(self):
        content = self.coder._generate_generic(self.spec, "Custom integration module")
        self.assertIn('DataProcessor', content)
        self.assertNotIn('TODO', content)

    def test_generate_generic_default_no_keywords(self):
        content = self.coder._generate_generic(self.spec, "Generic utility module")
        self.assertIn('DataProcessor', content)
        self.assertNotIn('TODO', content)

    def test_generate_generic_endpoint_keyword(self):
        content = self.coder._generate_generic(self.spec, "REST endpoint definitions")
        self.assertIn('ApiClient', content)
        self.assertNotIn('TODO', content)

    def test_generate_generic_client_keyword(self):
        content = self.coder._generate_generic(self.spec, "WebSocket client")
        self.assertIn('ApiClient', content)
        self.assertNotIn('TODO', content)

    def test_generate_generic_no_todo_in_any_branch(self):
        for desc in ["API client", "handler module", "command processor", "generic thing", "endpoint", "client"]:
            content = self.coder._generate_generic(self.spec, desc)
            self.assertNotIn('TODO', content, f"'TODO' found for description: '{desc}'")

    def test_generated_code_is_valid_python(self):
        for desc in ["API client", "Command handler for foo", "Data processor module"]:
            content = self.coder._generate_generic(self.spec, desc)
            try:
                compile(content, f'<test_{desc[:10]}>', 'exec')
            except SyntaxError as e:
                self.fail(f"Syntax error in generated code for '{desc}': {e}")


class TestAutonomousCoderBestCoder(unittest.TestCase):
    def test_get_best_coder_returns_template_when_no_plugin_manager(self):
        coder = get_best_coder(None)
        self.assertIsInstance(coder, AutonomousCoder)

    def test_get_best_coder_returns_template_when_no_selfimprove(self):
        mock_pm = MagicMock()
        mock_pm.get_plugin.return_value = None
        coder = get_best_coder(mock_pm)
        self.assertIsInstance(coder, AutonomousCoder)

    def test_get_best_coder_returns_selfimprove_when_available(self):
        mock_pm = MagicMock()
        mock_selfimprove = MagicMock()
        mock_selfimprove._generate_code_with_ai = MagicMock(return_value="code")
        mock_pm.get_plugin.return_value = mock_selfimprove
        coder = get_best_coder(mock_pm)
        self.assertEqual(coder, mock_selfimprove)

    def test_generate_skill_with_fallback_uses_template(self):
        mock_pm = MagicMock()
        mock_pm.get_plugin.return_value = None
        spec = SkillSpecification(id='fallback_test', name='Fallback', description='test', category='test')
        result = generate_skill_with_fallback(mock_pm, spec)
        self.assertEqual(result.status, 'generated')
        self.assertGreater(len(result.files_created), 0)


if __name__ == '__main__':
    unittest.main()
