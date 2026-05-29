#!/usr/bin/env python3
"""Tests for SelfModel: calibrated capability tracking."""

import os
import sys
import unittest
import tempfile
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.self_model import SelfModel, CapabilityEstimate


class TestSelfModelCore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.model = SelfModel(storage_path=os.path.join(self.tmpdir, 'self_model.json'))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_record_outcome_creates_capability(self):
        result = self.model.record_outcome(
            domain="social", action_type="post",
            predicted_confidence=0.7, actual_success=True,
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['sample_size'], 1)
        key = "social:post"
        self.assertIn(key, self.model.capabilities)

    def test_consecutive_failures_tracking(self):
        for _ in range(5):
            self.model.record_outcome(
                domain="test", action_type="fail_action",
                predicted_confidence=0.3, actual_success=False,
            )
        key = "test:fail_action"
        self.assertEqual(self.model.capabilities[key].consecutive_failures, 5)
        self.assertEqual(self.model.capabilities[key].consecutive_successes, 0)

    def test_consecutive_successes_reset_failures(self):
        for _ in range(3):
            self.model.record_outcome(
                domain="test", action_type="success_action",
                predicted_confidence=0.8, actual_success=True,
            )
        key = "test:success_action"
        self.assertEqual(self.model.capabilities[key].consecutive_successes, 3)
        self.assertEqual(self.model.capabilities[key].consecutive_failures, 0)

    def test_should_attempt_unknown_action(self):
        should, reason = self.model.should_attempt("unknown", "action")
        self.assertTrue(should)

    def test_should_attempt_consecutive_failures(self):
        for _ in range(5):
            self.model.record_outcome(
                domain="bad", action_type="thing",
                predicted_confidence=0.3, actual_success=False,
            )
        should, reason = self.model.should_attempt("bad", "thing")
        self.assertFalse(should)

    def test_what_should_i_learn(self):
        for i in range(2):
            self.model.record_outcome(
                domain="sparse", action_type="action",
                predicted_confidence=0.5, actual_success=(i % 2 == 0),
            )
        learn = self.model.what_should_i_learn()
        self.assertIsInstance(learn, list)

    def test_what_should_i_avoid(self):
        for _ in range(10):
            self.model.record_outcome(
                domain="avoid", action_type="this",
                predicted_confidence=0.8, actual_success=False,
            )
        avoid = self.model.what_should_i_avoid()
        self.assertGreater(len(avoid), 0)
        self.assertLess(avoid[0]['success_rate'], 0.3)

    def test_save_load_roundtrip(self):
        self.model.record_outcome(
            domain="social", action_type="post",
            predicted_confidence=0.7, actual_success=True,
        )
        path = self.model.storage_path
        model2 = SelfModel(storage_path=str(path))
        self.assertIn("social:post", model2.capabilities)

    def test_thread_safety(self):
        errors = []

        def writer(i):
            try:
                self.model.record_outcome(
                    domain="test", action_type=f"action_{i}",
                    predicted_confidence=0.5, actual_success=(i % 2 == 0),
                )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread safety errors: {errors}")


if __name__ == '__main__':
    unittest.main()