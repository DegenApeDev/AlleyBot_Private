#!/usr/bin/env python3
"""Tests for BeliefEngine: predict-compare-update belief system."""

import os
import sys
import unittest
import tempfile
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.belief_engine import BeliefEngine, Belief, Prediction


class TestBeliefEngineCore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.engine = BeliefEngine(storage_path=os.path.join(self.tmpdir, 'beliefs.json'))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_core_beliefs(self):
        self.assertGreaterEqual(len(self.engine.beliefs), 16)
        seed_beliefs = [b for b in self.engine.beliefs.values() if b.source == "seed"]
        self.assertGreaterEqual(len(seed_beliefs), 16)

    def test_predict_returns_prediction(self):
        pred = self.engine.predict("moltx:post", "social")
        self.assertIsInstance(pred, Prediction)
        self.assertEqual(pred.action, "moltx:post")
        self.assertEqual(pred.domain, "social")
        self.assertGreater(pred.predicted_success, 0.0)
        self.assertLessEqual(pred.predicted_success, 1.0)

    def test_predict_unknown_action(self):
        pred = self.engine.predict("unknown_action_12345", "general")
        self.assertEqual(pred.predicted_success, 0.5)
        self.assertEqual(pred.predicted_outcome, "unknown — no prior experience")

    def test_update_from_outcome_adjusts_confidence(self):
        initial_pred = self.engine.predict("moltx:post", "social")
        initial_conf = initial_pred.predicted_success

        for _ in range(3):
            self.engine.update_from_outcome(
                action="moltx:post", domain="social",
                predicted_success=initial_conf, actual_success=True,
            )

        pred_after = self.engine.predict("moltx:post", "social")
        self.assertGreater(pred_after.predicted_success, 0.5)

    def test_update_from_outcome_failures_lower_confidence(self):
        for _ in range(5):
            self.engine.update_from_outcome(
                action="bad_action", domain="test",
                predicted_success=0.5, actual_success=False,
            )

        pred = self.engine.predict("bad_action", "test")
        self.assertLessEqual(pred.predicted_success, 0.5)

    def test_find_relevant_beliefs_compound_tokens(self):
        beliefs = self.engine.find_relevant_beliefs("moltx:feed_browse", "social")
        self.assertGreater(len(beliefs), 0)

    def test_should_wait_unknown_action(self):
        should, reason = self.engine.should_wait("totally_unknown_action_xyz", "general")
        self.assertTrue(should)

    def test_should_wait_above_threshold(self):
        for _ in range(10):
            self.engine.update_from_outcome(
                action="moltx:post", domain="social",
                predicted_success=0.7, actual_success=True,
            )
        should, reason = self.engine.should_wait("moltx:post", "social")
        self.assertFalse(should)

    def test_get_domain_strengths_no_stale_reference(self):
        for _ in range(3):
            self.engine.update_from_outcome(
                action="test_action", domain="test_domain",
                predicted_success=0.6, actual_success=True,
            )
        strengths = self.engine.get_domain_strengths()
        if "test_domain" in strengths:
            s = strengths["test_domain"]
            self.assertIsInstance(s['success_rate'], float)
            self.assertLessEqual(s['success_rate'], 1.0)

    def test_save_load_roundtrip(self):
        for _ in range(3):
            self.engine.update_from_outcome(
                action="roundtrip_action", domain="test",
                predicted_success=0.6, actual_success=True,
            )
        path = self.engine.storage_path

        engine2 = BeliefEngine(storage_path=str(path))
        self.assertGreaterEqual(len(engine2.beliefs), len(self.engine.beliefs))

    def test_thread_safety(self):
        errors = []

        def writer(i):
            try:
                self.engine.update_from_outcome(
                    action=f"thread_action_{i}", domain="test",
                    predicted_success=0.5, actual_success=(i % 2 == 0),
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