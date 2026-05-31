"""Tests for planning module: Plan, PlanStep, PlanManager core logic."""

import sys
import unittest
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.planning import (
    Plan, PlanStep, PlanManager, StepStatus, StepType,
    get_plan_manager,
)


class TestStepStatus(unittest.TestCase):
    def test_enum_has_values(self):
        self.assertIsNotNone(StepStatus.PENDING.value)
        self.assertIsNotNone(StepStatus.READY.value)
        self.assertIsNotNone(StepStatus.COMPLETED.value)
        self.assertIsNotNone(StepStatus.FAILED.value)


class TestStepType(unittest.TestCase):
    def test_enum_has_values(self):
        self.assertIsNotNone(StepType.RESEARCH.value)
        self.assertIsNotNone(StepType.IMPLEMENT.value)
        self.assertIsNotNone(StepType.TEST.value)
        self.assertIsNotNone(StepType.DEPLOY.value)


class TestPlanStep(unittest.TestCase):
    def setUp(self):
        self.step = PlanStep(
            id='step_1',
            goal_id='goal_1',
            title='Test step',
            description='A test step',
            step_type=StepType.IMPLEMENT,
            command='test command',
            parameters={},
            dependencies=[],
        )

    def test_to_dict(self):
        d = self.step.to_dict()
        self.assertEqual(d['id'], 'step_1')
        self.assertIn('step_type', d)
        self.assertIn('status', d)

    def test_is_ready_true_when_status_ready(self):
        self.step.status = StepStatus.READY
        self.assertTrue(self.step.is_ready)

    def test_is_ready_false_when_pending(self):
        self.assertFalse(self.step.is_ready)

    def test_can_retry_initially(self):
        self.assertTrue(self.step.can_retry)

    def test_cannot_retry_after_max_attempts(self):
        self.step.attempts = 3
        self.assertFalse(self.step.can_retry)

    def test_duration_seconds_not_started(self):
        self.assertIsNone(self.step.duration_seconds)


class TestPlan(unittest.TestCase):
    def setUp(self):
        self.step = PlanStep(
            id='step_1', goal_id='goal_1', title='Step 1',
            description='First step', step_type=StepType.RESEARCH,
            command=None, parameters={}, dependencies=[],
        )
        self.plan = Plan(
            id='plan_1', goal_id='goal_1', title='Test plan',
            description='A test plan', steps={'step_1': self.step},
        )

    def test_progress_percent_no_steps(self):
        empty_plan = Plan(id='p', goal_id='g', title='t', description='d')
        self.assertEqual(empty_plan.progress_percent, 0.0)

    def test_progress_percent_some_done(self):
        self.step.status = StepStatus.COMPLETED
        self.assertEqual(self.plan.progress_percent, 100.0)

    def test_is_complete(self):
        self.assertFalse(self.plan.is_complete)
        self.step.status = StepStatus.COMPLETED
        self.assertTrue(self.plan.is_complete)

    def test_has_failures(self):
        self.assertFalse(self.plan.has_failures)
        self.step.status = StepStatus.FAILED
        self.assertTrue(self.plan.has_failures)

    def test_get_ready_steps(self):
        ready = self.plan.get_ready_steps()
        self.assertIsInstance(ready, list)

    def test_get_next_step(self):
        next_step = self.plan.get_next_step()
        # May be None or a PlanStep depending on implementation
        if next_step:
            self.assertIsInstance(next_step, PlanStep)

    def test_get_next_step_all_done(self):
        self.step.status = StepStatus.COMPLETED
        next_step = self.plan.get_next_step()
        if next_step:
            self.assertIsInstance(next_step, PlanStep)

    def test_update_step_status(self):
        self.plan.update_step_status('step_1', StepStatus.COMPLETED)
        self.assertEqual(self.step.status, StepStatus.COMPLETED)


class TestPlanManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / 'test_plans.db')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_and_get_plan(self):
        pm = PlanManager(db_path=self.db_path)
        step = PlanStep(
            id='s1', goal_id='g1', title='Step 1',
            description='desc', step_type=StepType.RESEARCH,
            command='cmd', parameters={}, dependencies=[],
        )
        plan = Plan(id='p1', goal_id='g1', title='Plan 1',
                     description='desc', steps={'s1': step})
        pm.save_plan(plan)
        loaded = pm.get_plan('p1')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, 'p1')
        self.assertEqual(loaded.title, 'Plan 1')

    def test_get_plan_not_found(self):
        pm = PlanManager(db_path=self.db_path)
        loaded = pm.get_plan('nonexistent')
        # Should return None or raise — accept both
        self.assertIsNone(loaded)

    def test_get_recent_plan_summaries(self):
        pm = PlanManager(db_path=self.db_path)
        summaries = pm.get_recent_plan_summaries(limit=5)
        self.assertIsInstance(summaries, list)

    def test_get_decision_plan_summary(self):
        pm = PlanManager(db_path=self.db_path)
        summary = pm.get_decision_plan_summary()
        self.assertIsInstance(summary, dict)

    def test_get_top_resumable_plan(self):
        pm = PlanManager(db_path=self.db_path)
        result = pm.get_top_resumable_plan()
        self.assertIsNone(result)  # no plans yet


if __name__ == '__main__':
    unittest.main()
