#!/usr/bin/env python3
"""Tests for Phase 4: Semantic Memory and Counterfactual Reasoning features."""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.belief_engine import BeliefEngine, Belief
from src.agentic.cognitive_integration import CognitiveIntegration
from src.agentic.knowledge_graph import KnowledgeGraph, EntityType, RelationType


class TestBeliefContext(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.be = BeliefEngine(storage_path=os.path.join(self.tmpdir, 'beliefs.json'))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_belief_has_context_history(self):
        belief = Belief(
            proposition="Test proposition",
            confidence=0.7,
            domain="test",
        )
        self.assertEqual(belief.context_history, [])
        self.assertIsNone(belief.last_outcome)

    def test_belief_outcome_timestamps(self):
        belief = Belief(
            proposition="Test proposition",
            confidence=0.7,
            domain="test",
        )
        self.assertEqual(belief.outcome_timestamps, [])

    def test_belief_recency_decay_confidence(self):
        belief = Belief(
            proposition="Test proposition",
            confidence=0.5,
            domain="test",
            evidence_for=["success1", "success2"],
            evidence_against=["failure1"],
            outcome_timestamps=["2024-01-01T00:00:00", "2024-01-02T00:00:00", "2024-01-03T00:00:00"],
        )
        decay_conf = belief.recency_decay_confidence
        self.assertIsInstance(decay_conf, float)
        self.assertGreaterEqual(decay_conf, 0.0)
        self.assertLessEqual(decay_conf, 1.0)

    def test_belief_is_conflicting_property(self):
        belief = Belief(
            proposition="Test proposition",
            confidence=0.5,
            evidence_for=["success1", "success2"],
            evidence_against=["failure1", "failure2"],
        )
        self.assertTrue(belief.is_conflicting)
        
        belief2 = Belief(
            proposition="Test proposition 2",
            confidence=0.5,
            evidence_for=["success1"],
            evidence_against=["failure1"],
        )
        self.assertFalse(belief2.is_conflicting)


class TestContextTrackingInEngine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.be = BeliefEngine(storage_path=os.path.join(self.tmpdir, 'beliefs.json'))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_update_adds_context(self):
        # Use unique action name that won't match any seed beliefs
        result = self.be.update_from_outcome(
            action="my_unique_test_action_xyz123",
            domain="testdomain",
            predicted_success=0.7,
            actual_success=True,
            context="test context with keywords",
            outcome_description="Test succeeded with good result",
        )
        
        # Find the belief we just created (has context history)
        belief_with_context = None
        for b in self.be.beliefs.values():
            if len(b.context_history) > 0:
                belief_with_context = b
                break
        
        self.assertIsNotNone(belief_with_context)
        self.assertGreater(len(belief_with_context.context_history), 0)
        self.assertIsNotNone(belief_with_context.last_outcome)

    def test_context_history_stores_timestamp_and_outcome(self):
        result = self.be.update_from_outcome(
            action="browse_my_feed_unique_xyz789",
            domain="social_unique_xyz",
            predicted_success=0.6,
            actual_success=True,
            context="visited moltx feed",
            outcome_description="Found trending topics",
        )
        
        # Find the belief with context
        belief = None
        for b in self.be.beliefs.values():
            if len(b.context_history) > 0:
                belief = b
                break
        
        self.assertIsNotNone(belief)
        ctx = belief.context_history[0]
        self.assertIn('timestamp', ctx)
        self.assertIn('outcome', ctx)
        self.assertIn('context', ctx)


class TestSemanticRetrieval(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.be = BeliefEngine(storage_path=os.path.join(self.tmpdir, 'beliefs.json'))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_find_relevant_beliefs_semantic_returns_list(self):
        # Add some beliefs
        self.be.update_from_outcome(
            action="post",
            domain="social",
            predicted_success=0.7,
            actual_success=True,
            context="create engaging content",
            outcome_description="high engagement",
        )
        
        results = self.be.find_relevant_beliefs_semantic("post content engagement", "social")
        self.assertIsInstance(results, list)

    def test_find_relevant_beliefs_semantic_falls_back_to_keyword(self):
        results = self.be.find_relevant_beliefs_semantic("xyz unknown query", "unknown")
        self.assertIsInstance(results, list)


class TestConflictDetection(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.be = BeliefEngine(storage_path=os.path.join(self.tmpdir, 'beliefs.json'))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_detect_conflicts_returns_list(self):
        conflicts = self.be.detect_conflicts()
        self.assertIsInstance(conflicts, list)

    def test_detect_conflicts_finds_contradictory_beliefs(self):
        belief = Belief(
            proposition="posting generates engagement",
            confidence=0.5,
            domain="social",
            evidence_for=["evidence1", "evidence2"],
            evidence_against=["evidence3", "evidence4"],
        )
        self.be.beliefs[self.be._hash(belief.proposition)] = belief
        
        conflicts = self.be.detect_conflicts("social")
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0]['domain'], "social")

    def test_conflict_recommendation(self):
        recommendation = self.be._resolve_conflict_recommendation(
            Belief(proposition="test", confidence=0.3, evidence_for=[], evidence_against=[])
        )
        self.assertIsInstance(recommendation, str)


class TestCounterfactualReasoning(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.be = BeliefEngine(storage_path=os.path.join(self.tmpdir, 'beliefs.json'))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generate_counterfactuals_returns_list(self):
        counterfactuals = self.be.generate_counterfactuals("post", "social", "test context")
        self.assertIsInstance(counterfactuals, list)

    def test_generate_counterfactuals_finds_alternatives(self):
        self.be.update_from_outcome(
            action="post",
            domain="social",
            predicted_success=0.7,
            actual_success=True,
            context="morning hours",
            outcome_description="high engagement",
        )
        
        counterfactuals = self.be.generate_counterfactuals(
            action="post",
            domain="social",
            failed_context="evening hours",
        )
        self.assertIsInstance(counterfactuals, list)


class TestCognitiveIntegrationPhase4(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cognitive_has_analogical_transfer(self):
        cognitive = CognitiveIntegration()
        self.assertTrue(hasattr(cognitive, 'find_analogies'))
        self.assertTrue(hasattr(cognitive, 'apply_transfer_learning'))

    def test_cognitive_has_conflict_detection(self):
        cognitive = CognitiveIntegration()
        self.assertTrue(hasattr(cognitive, 'detect_belief_conflicts'))

    def test_cognitive_has_counterfactual_generation(self):
        cognitive = CognitiveIntegration()
        self.assertTrue(hasattr(cognitive, 'generate_counterfactuals'))

    def test_find_analogies(self):
        cognitive = CognitiveIntegration()
        analogies = cognitive.find_analogies("chess", "trading")
        self.assertIsInstance(analogies, list)

    def test_apply_transfer_learning(self):
        cognitive = CognitiveIntegration()
        transfers = cognitive.apply_transfer_learning("new trading strategy", "chess")
        self.assertIsInstance(transfers, list)

    def test_detect_belief_conflicts(self):
        cognitive = CognitiveIntegration()
        conflicts = cognitive.detect_belief_conflicts()
        self.assertIsInstance(conflicts, list)

    def test_generate_counterfactuals(self):
        cognitive = CognitiveIntegration()
        counterfactuals = cognitive.generate_counterfactuals("post", "social", "test context")
        self.assertIsInstance(counterfactuals, list)


class TestKnowledgeGraphAnalogicalTransfer(unittest.TestCase):
    def test_analogical_transfer_exists(self):
        kg = KnowledgeGraph()
        self.assertTrue(hasattr(kg, 'analogical_transfer'))

    def test_analogical_transfer_returns_list(self):
        kg = KnowledgeGraph()
        result = kg.analogical_transfer("new situation in trading", "chess")
        self.assertIsInstance(result, list)


class TestDecayWeightedRecency(unittest.TestCase):
    def test_decay_confidence_property_exists(self):
        belief = Belief(
            proposition="test",
            confidence=0.5,
            outcome_timestamps=["2024-01-01T00:00:00"],
        )
        self.assertTrue(hasattr(belief, 'recency_decay_confidence'))

    def test_decay_confidence_is_valid(self):
        belief = Belief(
            proposition="test",
            confidence=0.5,
            outcome_timestamps=["2024-01-01T00:00:00"],
            evidence_for=["success"],
            evidence_against=[],
        )
        decay = belief.recency_decay_confidence
        self.assertGreaterEqual(decay, 0.0)
        self.assertLessEqual(decay, 1.0)

    def test_decay_confidence_empty_timestamps_returns_original(self):
        belief = Belief(
            proposition="test",
            confidence=0.5,
            outcome_timestamps=[],
        )
        self.assertEqual(belief.recency_decay_confidence, 0.5)


if __name__ == '__main__':
    unittest.main()