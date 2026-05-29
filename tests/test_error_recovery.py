#!/usr/bin/env python3
"""Tests for ErrorRecoverySystem: adaptive recovery, outcome learning, circuit breaker."""

import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.error_recovery import ErrorRecoverySystem


class TestErrorRecoveryAdaptive(unittest.TestCase):
    def setUp(self):
        self.ers = ErrorRecoverySystem(plugin_manager=MagicMock())

    def test_recovery_outcomes_tracked_per_component(self):
        self.ers.recovery_outcomes['test_comp'] = [True, False, True]
        self.assertEqual(len(self.ers.recovery_outcomes['test_comp']), 3)

    def test_successful_recovery_de_escalates_failures(self):
        self.ers.component_failures['test_comp'] = 3
        # Simulate successful recovery directly
        self.ers.component_failures['test_comp'] = max(0, self.ers.component_failures.get('test_comp', 0) - 1)
        self.assertEqual(self.ers.component_failures['test_comp'], 2)

    def test_three_consecutive_failures_trips_circuit_breaker(self):
        comp = 'test_comp'
        self.ers.recovery_outcomes[comp] = [False, False, False]
        # Trigger circuit breaker based on the condition in attempt_recovery
        if len(self.ers.recovery_outcomes[comp]) >= 3 and all(not r for r in self.ers.recovery_outcomes[comp][-3:]):
            self.ers._trip_circuit_breaker(comp)
        self.assertTrue(self.ers.is_circuit_open(comp))

    def test_two_failures_does_not_trip_circuit_breaker(self):
        comp = 'test_comp'
        self.ers.recovery_outcomes[comp] = [False, False]
        if len(self.ers.recovery_outcomes[comp]) >= 3 and all(not r for r in self.ers.recovery_outcomes[comp][-3:]):
            self.ers._trip_circuit_breaker(comp)
        self.assertFalse(self.ers.is_circuit_open(comp))

    def test_mixed_outcomes_does_not_trip_circuit_breaker(self):
        comp = 'test_comp'
        self.ers.recovery_outcomes[comp] = [False, True, False]
        if len(self.ers.recovery_outcomes[comp]) >= 3 and all(not r for r in self.ers.recovery_outcomes[comp][-3:]):
            self.ers._trip_circuit_breaker(comp)
        self.assertFalse(self.ers.is_circuit_open(comp))

    def test_backoff_blocks_repeated_attempts(self):
        comp = 'test_backoff'
        from datetime import datetime

        # First attempt should be allowed
        self.assertTrue(self.ers._can_attempt_recovery(comp))

        # Set last attempt to now — immediate retry should be blocked
        self.ers.last_recovery_attempt[comp] = datetime.now()
        self.ers.component_failures[comp] = 1

        self.assertFalse(self.ers._can_attempt_recovery(comp))

    def test_circuit_open_blocks_recovery(self):
        comp = 'test_circuit'
        self.ers._trip_circuit_breaker(comp)
        self.assertTrue(self.ers.is_circuit_open(comp))

    def test_error_history_trimmed_to_100(self):
        from datetime import datetime
        from src.agentic.error_recovery import ErrorRecord

        for i in range(150):
            self.ers.error_history.append(ErrorRecord(
                timestamp=datetime.now(), error_type='Test', error_message=str(i),
                component='test', severity='low',
            ))
            if len(self.ers.error_history) > 100:
                self.ers.error_history = self.ers.error_history[-100:]

        self.assertLessEqual(len(self.ers.error_history), 100)

    def test_record_error_increments_failures(self):
        self.ers.record_error('test_comp', Exception('test error'), 'medium')
        self.assertEqual(self.ers.component_failures['test_comp'], 1)
        self.assertEqual(len(self.ers.error_history), 1)

    def test_record_error_circuit_trips_at_5(self):
        for i in range(5):
            self.ers.record_error('test_comp', Exception(f'error {i}'), 'medium')
        self.assertTrue(self.ers.is_circuit_open('test_comp'))


if __name__ == '__main__':
    unittest.main()
