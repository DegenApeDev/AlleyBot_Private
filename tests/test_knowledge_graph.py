#!/usr/bin/env python3
"""Tests for KnowledgeGraph: seeding from beliefs, seeding from plugins, learning."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.knowledge_graph import KnowledgeGraph, EntityType


class TestKnowledgeGraphSeeding(unittest.TestCase):
    def setUp(self):
        self.kg = KnowledgeGraph()

    def test_seed_from_beliefs_returns_count(self):
        mock_belief_engine = MagicMock()
        mock_belief = MagicMock()
        mock_belief.proposition = "test belief about posting"
        mock_belief.domain = "social"
        mock_belief.confidence = 0.8
        mock_belief.prediction_count = 10
        mock_belief.correct_predictions = 7
        mock_belief.source = "seed"
        mock_belief.evidence_for = ["obs1"]
        mock_belief.evidence_against = []
        mock_belief_engine.beliefs = {'test_belief': mock_belief}

        count = self.kg.seed_from_beliefs(mock_belief_engine)
        self.assertGreater(count, 0)

        entity = self.kg.get_entity('belief_test_belief')
        self.assertIsNotNone(entity)
        self.assertEqual(entity.entity_type, EntityType.FACT)
        self.assertEqual(entity.domain, 'social')

    def test_seed_from_beliefs_action_type(self):
        mock_belief_engine = MagicMock()
        mock_belief = MagicMock()
        mock_belief.proposition = "moltx interaction"
        mock_belief.domain = "moltx"
        mock_belief.confidence = 0.7
        mock_belief.prediction_count = 5
        mock_belief.correct_predictions = 3
        mock_belief.source = "experience"
        mock_belief.evidence_for = []
        mock_belief.evidence_against = []
        mock_belief_engine.beliefs = {'moltx_belief': mock_belief}

        self.kg.seed_from_beliefs(mock_belief_engine)
        entity = self.kg.get_entity('belief_moltx_belief')
        self.assertEqual(entity.entity_type, EntityType.ACTION)

    def test_seed_from_plugin_list_returns_count(self):
        mock_pm = MagicMock()
        mock_pm.plugins = {'moltx': object(), 'clawbr': object(), 'telegram': object()}

        count = self.kg.seed_from_plugin_list(mock_pm)
        self.assertEqual(count, 3)

        entity = self.kg.get_entity('plugin_moltx')
        self.assertIsNotNone(entity)
        self.assertEqual(entity.entity_type, EntityType.PLATFORM)

    def test_seed_from_plugin_list_skips_existing(self):
        mock_pm = MagicMock()
        mock_pm.plugins = {'moltx': object()}
        self.kg.seed_from_plugin_list(mock_pm)
        count2 = self.kg.seed_from_plugin_list(mock_pm)
        self.assertEqual(count2, 0)

    def test_seed_from_beliefs_skips_existing(self):
        mock_belief_engine = MagicMock()
        mock_belief = MagicMock()
        mock_belief.proposition = "exists"
        mock_belief.domain = "test"
        mock_belief.confidence = 0.5
        mock_belief.prediction_count = 0
        mock_belief.correct_predictions = 0
        mock_belief.source = "seed"
        mock_belief.evidence_for = []
        mock_belief.evidence_against = []
        mock_belief_engine.beliefs = {'dup': mock_belief}

        self.kg.seed_from_beliefs(mock_belief_engine)
        count2 = self.kg.seed_from_beliefs(mock_belief_engine)
        self.assertEqual(count2, 0)

    def test_seed_none_belief_engine_returns_0(self):
        count = self.kg.seed_from_beliefs(None)
        self.assertEqual(count, 0)

    def test_seed_none_plugin_manager_returns_0(self):
        count = self.kg.seed_from_plugin_list(None)
        self.assertEqual(count, 0)

    def test_learn_from_outcome_creates_action_entity(self):
        created = self.kg.learn_from_outcome(
            action="test_action", domain="test_domain",
            context="testing knowledge graph learning",
            outcome="successful outcome", success=True, confidence=0.8,
        )
        self.assertGreater(len(created), 0)
        # Should have created action entity, domain entity, relationships
        action_entities = [
            e for e in self.kg.entities.values()
            if e.entity_type == EntityType.ACTION and 'test_action' in e.name
        ]
        self.assertGreater(len(action_entities), 0)

    def test_learn_from_outcome_tracks_success_rate(self):
        self.kg.learn_from_outcome("track_me", "test", "context", "good", True, 0.8)
        self.kg.learn_from_outcome("track_me", "test", "context2", "bad", False, 0.8)
        self.kg.learn_from_outcome("track_me", "test", "context3", "good", True, 0.8)

        pred = self.kg.predict_outcome("track_me", "test")
        self.assertIn('predicted_success', pred)
        self.assertGreaterEqual(pred['sample_size'], 1)

    def test_predict_outcome_unknown_action_returns_0_5(self):
        pred = self.kg.predict_outcome("nonexistent", "unknown")
        self.assertEqual(pred['predicted_success'], 0.5)
        self.assertEqual(pred['sample_size'], 0)

    def test_get_statistics(self):
        stats = self.kg.get_statistics()
        self.assertIn('total_entities', stats)
        self.assertIn('total_relationships', stats)
        self.assertIn('domains', stats)


if __name__ == '__main__':
    unittest.main()
