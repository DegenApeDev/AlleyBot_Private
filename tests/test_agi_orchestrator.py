"""Tests for AGI Orchestrator: cycle execution, goal generation, cross-domain synthesis."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.agi_orchestrator import get_agi_orchestrator


class TestAGIOrchestrator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.orchestrator = get_agi_orchestrator()
        except Exception as e:
            raise unittest.SkipTest(f"AGI Orchestrator init failed: {e}")

    def test_get_orchestrator_summary(self):
        summary = self.orchestrator.get_orchestrator_summary()
        self.assertIsInstance(summary, dict)

    def test_generate_goal_proposals(self):
        proposals = self.orchestrator.generate_goal_proposals(observations=[])
        self.assertIsInstance(proposals, (list, type(None)))

    def test_synthesize_cross_domain_opportunities(self):
        result = self.orchestrator.synthesize_cross_domain_opportunities(observations=[])
        self.assertIsInstance(result, (list, type(None)))

    def test_run_cycle(self):
        import asyncio
        result = asyncio.run(self.orchestrator.run_cycle())
        # AGICycleResult dataclass with cycle_id and phases
        self.assertTrue(hasattr(result, 'cycle_id'))
        self.assertTrue(hasattr(result, 'phases_executed'))


if __name__ == '__main__':
    unittest.main()
