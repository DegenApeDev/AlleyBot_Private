"""Tests for DecisionSystem: action selection and validation."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.decision_system import DecisionSystem, create_decision_system


class TestDecisionSystemCreate(unittest.TestCase):
    def test_create_decision_system(self):
        mock_kernel = MagicMock()
        mock_pm = MagicMock()
        ds = create_decision_system(mock_kernel, mock_pm)
        self.assertIsInstance(ds, DecisionSystem)


class TestDecisionSystemBasic(unittest.TestCase):
    def setUp(self):
        self.mock_kernel = MagicMock()
        self.mock_plugin_manager = MagicMock()
        self.mock_plugin_manager.plugins = {}
        # Prevent goal_manager from returning MagicMock values
        self.mock_kernel.goal_manager.get_next_action.return_value = None
        self.mock_kernel.goal_stack.get_summary.return_value = {}
        self.ds = DecisionSystem(self.mock_kernel, self.mock_plugin_manager)

    def test_get_available_actions(self):
        actions = self.ds.get_available_actions()
        self.assertIsInstance(actions, list)

    def test_decide_next_action_no_context(self):
        action = self.ds.decide_next_action({})
        self.assertIsNone(action)

    def test_decide_next_action_with_empty_work_items(self):
        action = self.ds.decide_next_action({'work_items': [], 'observations': []})
        self.assertIsNone(action)

    def test_record_action(self):
        self.ds.record_action('test_action', {'status': 'ok'})

    def test_validate_with_symod_empty_context(self):
        valid, info = self.ds.validate_with_symod(
            {'action_type': 'test'}, {'observations': []}
        )
        self.assertIsInstance(valid, bool)
        self.assertIsInstance(info, dict)

    def test_get_synergy_field_report(self):
        report = self.ds.get_synergy_field_report()
        self.assertIsInstance(report, dict)


if __name__ == '__main__':
    unittest.main()
