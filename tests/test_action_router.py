"""Tests for ActionRouter: action validation and routing."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.action_router import ActionRouter


class TestActionRouterClassmethods(unittest.TestCase):
    def test_is_action_valid_returns_bool(self):
        result = ActionRouter.is_action_valid('social', 'reply')
        self.assertIsInstance(result, bool)

    def test_is_action_valid_unknown_plugin(self):
        self.assertFalse(ActionRouter.is_action_valid('nonexistent_plugin', 'reply'))

    def test_get_capabilities_returns_dict(self):
        caps = ActionRouter.get_capabilities()
        self.assertIsInstance(caps, dict)
        self.assertGreater(len(caps), 0)

    def test_get_valid_actions_all(self):
        actions = ActionRouter.get_valid_actions()
        self.assertIsInstance(actions, list)

    def test_get_valid_actions_for_plugin(self):
        actions = ActionRouter.get_valid_actions(plugin='social')
        for plugin, action in actions:
            self.assertEqual(plugin, 'social')


class TestActionRouterInstance(unittest.TestCase):
    def setUp(self):
        self.mock_kernel = MagicMock()
        self.mock_plugin_manager = MagicMock()
        self.mock_plugin_manager.plugins = {}
        self.router = ActionRouter(self.mock_kernel, self.mock_plugin_manager)

    def test_get_alley_kernel_summary(self):
        summary = self.router.get_alley_kernel_summary()
        self.assertIsInstance(summary, dict)

    def test_list_available_skills(self):
        skills = self.router.list_available_skills()
        self.assertIsInstance(skills, dict)

    def test_route_action_no_plugin(self):
        import asyncio
        with self.assertRaises((Exception,)):
            asyncio.run(self.router.route_action({'action_type': 'reply'}))

    def test_route_action_missing_action_type(self):
        import asyncio
        with self.assertRaises((Exception,)):
            asyncio.run(self.router.route_action({}))


if __name__ == '__main__':
    unittest.main()
