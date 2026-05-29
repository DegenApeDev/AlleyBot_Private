#!/usr/bin/env python3
"""Tests for CognitiveIntegration: wiring BeliefEngine, SelfModel, GoalPlanner."""

import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.cognitive_integration import CognitiveIntegration, get_cognitive


class TestCognitiveIntegrationCore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cog = CognitiveIntegration(telegram_plugin=None)
        # Override storage paths so tests don't pollute real data
        self.cog.belief_engine.storage_path = Path(os.path.join(self.tmpdir, 'beliefs.json'))
        self.cog.self_model.storage_path = Path(os.path.join(self.tmpdir, 'self_model.json'))
        self.cog.goal_planner.storage_path = Path(os.path.join(self.tmpdir, 'plans.json'))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_predict_action_outcome(self):
        result = self.cog.predict_action_outcome("moltx:post", "social")
        self.assertIn('predicted_success', result)
        self.assertIn('should_attempt', result)
        self.assertIn('should_wait', result)
        self.assertIsInstance(result['predicted_success'], float)

    def test_record_action_outcome(self):
        self.cog.predict_action_outcome("test_action", "test_domain")
        result = self.cog.record_action_outcome(
            action="test_action", domain="test_domain",
            predicted_confidence=0.6, actual_success=True,
            outcome_description="worked",
        )
        self.assertIn('belief_update', result)
        self.assertIn('capability_update', result)

    def test_plan_goal(self):
        plan = self.cog.plan_goal("Post on Moltx", "social")
        self.assertIn('plan_id', plan)
        self.assertIn('steps', plan)
        self.assertGreater(len(plan['steps']), 0)

    def test_get_available_tools(self):
        tools = self.cog.get_available_tools()
        self.assertIsInstance(tools, dict)

    def test_self_awareness_report(self):
        report = self.cog.get_self_awareness_report()
        self.assertIn('strengths', report)
        self.assertIn('weaknesses', report)

    def test_belief_calibration(self):
        cal = self.cog.get_belief_calibration()
        self.assertIn('total_beliefs', cal)

    def test_reflect(self):
        reflection = self.cog.reflect()
        self.assertIn('cycle', reflection)
        self.assertIn('beliefs', reflection)
        self.assertIn('calibration', reflection)

    def test_telegram_notification_skipped_without_plugin(self):
        # Should not raise even with no telegram plugin
        self.cog.notify_completion("test_action", "test_domain", "details")
        self.cog.notify_failure("test_action", "test_domain", "details", {})
        self.cog.notify_goal_completion("test_goal", "social", "plan_123")

    def test_telegram_notification_with_mock_plugin(self):
        mock_telegram = MagicMock()
        mock_telegram.notify_autonomous_accomplishment = MagicMock()
        self.cog.set_telegram(mock_telegram)
        self.cog.notify_completion("post", "market", "Trade completed")
        mock_telegram.notify_autonomous_accomplishment.assert_called_once()


class TestGetCognitive(unittest.TestCase):
    def test_get_cognitive_returns_singleton(self):
        # Reset singleton for test
        import src.agentic.cognitive_integration as ci
        ci._cognitive = None
        c1 = get_cognitive()
        c2 = get_cognitive()
        self.assertIs(c1, c2)
        ci._cognitive = None


if __name__ == '__main__':
    unittest.main()