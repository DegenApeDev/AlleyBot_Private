#!/usr/bin/env python3
"""Tests for GoalPlanner: dependency-graph plans with rollback."""

import os
import sys
import unittest
import tempfile
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.goal_planner import GoalPlanner, Plan, PlanStep


class TestGoalPlannerCore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.planner = GoalPlanner(storage_path=os.path.join(self.tmpdir, 'plans.json'))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_decompose_goal_creates_dependency_chain(self):
        plan = self.planner.decompose_goal("Post engaging content on Moltx", "social")
        self.assertIsInstance(plan, Plan)
        self.assertGreater(len(plan.steps), 1)
        self.assertEqual(plan.status, "pending")
        for i, step in enumerate(plan.steps):
            if i > 0:
                self.assertGreater(len(step.depends_on), 0)

    def test_decompose_goal_market_domain(self):
        plan = self.planner.decompose_goal("Trade on Polymarket", "market")
        self.assertGreater(len(plan.steps), 1)
        self.assertEqual(plan.domain, "market")

    def test_check_preconditions_sets_ready(self):
        plan = self.planner.decompose_goal("Analyze market trends", "analysis")
        plan = self.planner.check_preconditions(plan)
        first_step = plan.steps[0]
        self.assertIn(first_step.status, ("ready", "pending"))

    def test_get_next_step_returns_ready_step(self):
        plan = self.planner.decompose_goal("Engage with community", "social")
        plan = self.planner.check_preconditions(plan)
        next_step = self.planner.get_next_step(plan)
        self.assertIsNotNone(next_step)

    def test_mark_step_completed_advances_deps(self):
        plan = self.planner.decompose_goal("Post on Moltx", "social")
        plan = self.planner.check_preconditions(plan)
        first_step = self.planner.get_next_step(plan)
        if first_step:
            result_plan = self.planner.mark_step_completed(plan.id, first_step.id, {"output": "done"})
            self.assertIsNotNone(result_plan)
            self.assertEqual(first_step.status, "completed")

    def test_mark_step_failed_blocks_deps(self):
        plan = self.planner.decompose_goal("Post on Moltx", "social")
        plan = self.planner.check_preconditions(plan)
        first_step = self.planner.get_next_step(plan)
        if first_step:
            result_plan = self.planner.mark_step_failed(
                plan.id, first_step.id, "Test failure", {"error": "timeout"}
            )
            self.assertIsNotNone(result_plan)
            self.assertIn(result_plan.status, ("failed", "blocked"))

    def test_get_alternative_path(self):
        plan = self.planner.decompose_goal("Post content", "social")
        alt = self.planner.get_alternative_path(plan, plan.steps[0].id)
        # Alternative may or may not exist depending on tool registry

    def test_get_available_tools(self):
        tools = self.planner.get_available_tools()
        self.assertIn('moltx', tools)
        self.assertIn('crypto', tools)

    def test_get_available_tools_domain_filter(self):
        tools = self.planner.get_available_tools('moltx')
        self.assertIn('moltx', tools)
        self.assertNotIn('crypto', tools)

    def test_thread_safety(self):
        errors = []

        def planner_action(i):
            try:
                self.planner.decompose_goal(f"Goal {i}", "social")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=planner_action, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread safety errors: {errors}")

    def test_save_load_roundtrip(self):
        plan = self.planner.decompose_goal("Test goal", "general")
        path = self.planner.storage_path

        planner2 = GoalPlanner(storage_path=str(path))
        self.assertIn(plan.id, planner2.plans)


if __name__ == '__main__':
    unittest.main()