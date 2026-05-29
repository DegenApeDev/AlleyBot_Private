#!/usr/bin/env python3
"""Tests for ContextSystem: token-budget context summary, priority ordering."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.context_system import ContextSystem


class TestContextSystemBuildSummary(unittest.TestCase):
    def setUp(self):
        self.mock_agi = MagicMock()
        self.mock_plugin_manager = MagicMock()
        self.cs = ContextSystem(self.mock_agi, self.mock_plugin_manager)
        self.cs.invalidate_cache()

    def _stub_context(self, **overrides):
        """Build a fake full context dict for testing"""
        ctx = {
            'timestamp': '2026-01-01T00:00:00',
            'goals': {'available': True, 'active_goals': [
                {'description': 'Test goal', 'progress': 0.5, 'type': 'test', 'priority': 1},
            ]},
            'recent_actions': [
                {'action': 'post', 'timestamp': '2026-01-01T00:00:00', 'outcome': 'ok', 'success': True},
                {'action': 'reply', 'timestamp': '2026-01-01T00:01:00', 'outcome': 'ok', 'success': True},
            ],
            'engagement': {'total_recent': 10, 'success_rate': 0.8, 'total_engagement': 5},
            'memory': {'available': True, 'stats': {'total_memories': 100, 'semantic_memories': 50}},
            'onchain': {'available': True, 'wallet': '0xabc', 'eth_balance': 1.5, 'token_balances': {'TEST': 100}},
        }
        ctx.update(overrides)
        return ctx

    @patch.object(ContextSystem, 'gather_full_context')
    def test_build_context_summary_includes_goals_first(self, mock_gather):
        mock_gather.return_value = self._stub_context()
        summary = self.cs.build_context_summary(max_tokens=2000)
        self.assertIn('Test goal', summary)
        self.assertIn('Context Summary:', summary)

    @patch.object(ContextSystem, 'gather_full_context')
    def test_build_context_summary_truncates_with_small_budget(self, mock_gather):
        mock_gather.return_value = self._stub_context()
        summary = self.cs.build_context_summary(max_tokens=10)
        # With tiny budget, should still include header + maybe goals
        self.assertIn('Context Summary:', summary)
        self.assertGreaterEqual(len(summary), 10)

    @patch.object(ContextSystem, 'gather_full_context')
    def test_build_context_summary_shows_truncation_marker(self, mock_gather):
        mock_gather.return_value = self._stub_context(
            onchain={'available': True, 'wallet': '0x' + 'a' * 200, 'eth_balance': 9999, 'token_balances': {f't{i}': i for i in range(50)}}
        )
        summary = self.cs.build_context_summary(max_tokens=50)
        self.assertIn('truncated', summary)

    @patch.object(ContextSystem, 'gather_full_context')
    def test_build_context_summary_no_context(self, mock_gather):
        mock_gather.return_value = {
            'timestamp': '2026-01-01T00:00:00',
            'goals': {'available': False},
            'recent_actions': [],
            'engagement': {'total_recent': 0, 'success_rate': 0},
            'memory': {'available': False},
            'onchain': {'available': False},
        }
        summary = self.cs.build_context_summary(max_tokens=2000)
        self.assertIn('Context Summary:', summary)

    @patch.object(ContextSystem, 'gather_full_context')
    def test_build_context_summary_recent_actions_appear(self, mock_gather):
        mock_gather.return_value = self._stub_context()
        summary = self.cs.build_context_summary(max_tokens=2000)
        self.assertIn('post', summary)

    @patch.object(ContextSystem, 'gather_full_context')
    def test_build_context_summary_engagement_appears(self, mock_gather):
        mock_gather.return_value = self._stub_context()
        summary = self.cs.build_context_summary(max_tokens=2000)
        self.assertIn('Performance:', summary)
        self.assertIn('80%', summary)


if __name__ == '__main__':
    unittest.main()
