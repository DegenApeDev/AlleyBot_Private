"""Tests for TheoryOfMind: belief attribution, intent inference, perspective-taking."""

import sys
import unittest
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.theory_of_mind import (
    TheoryOfMind, BeliefAttribution, ObservedAction,
    IntentInference, get_theory_of_mind,
)


class TestTheoryOfMindObservation(unittest.TestCase):
    def setUp(self):
        self.tom = TheoryOfMind()

    def test_observe_action_records(self):
        self.tom.observe_action('agent_a', 'reply', target='post_123')
        actions = self.tom.get_recent_actions('agent_a')
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].action_type, 'reply')
        self.assertEqual(actions[0].target, 'post_123')

    def test_get_recent_actions_limit(self):
        for i in range(15):
            self.tom.observe_action('agent_b', 'like')
        self.assertEqual(len(self.tom.get_recent_actions('agent_b', limit=10)), 10)

    def test_unknown_agent_returns_empty(self):
        self.assertEqual(self.tom.get_recent_actions('ghost'), [])


class TestTheoryOfMindIntentInference(unittest.TestCase):
    def setUp(self):
        self.tom = TheoryOfMind()

    def test_no_observations_returns_none(self):
        self.assertIsNone(self.tom.infer_intent('silent_agent'))

    def test_detect_engage_intent(self):
        for _ in range(5):
            self.tom.observe_action('debatable', 'reply')
            self.tom.observe_action('debatable', 'mention')
        intent = self.tom.infer_intent('debatable')
        self.assertIsNotNone(intent)
        self.assertEqual(intent.inferred_intent, 'engage_discourse')
        self.assertGreater(intent.confidence, 0.0)

    def test_detect_build_network_intent(self):
        for _ in range(4):
            self.tom.observe_action('connector', 'follow')
        intent = self.tom.infer_intent('connector')
        self.assertIsNotNone(intent)
        self.assertEqual(intent.inferred_intent, 'build_network')

    def test_predict_next_action_known_intent(self):
        self.tom.observe_action('trader', 'trade')
        prediction = self.tom.predict_next_action('trader')
        self.assertIsNotNone(prediction)

    def test_predict_next_action_unknown_returns_none(self):
        self.assertIsNone(self.tom.predict_next_action('nobody'))


class TestTheoryOfMindBeliefAttribution(unittest.TestCase):
    def setUp(self):
        self.tom = TheoryOfMind()

    def test_attribute_belief_creates(self):
        self.tom.attribute_belief('agent_x', 'likes_alleybot', 0.8,
                                   evidence=['liked 3 posts'], inferred_from='observation')
        beliefs = self.tom.get_beliefs('agent_x')
        self.assertEqual(len(beliefs), 1)
        self.assertEqual(beliefs[0].belief_predicate, 'likes_alleybot')
        self.assertEqual(beliefs[0].confidence, 0.8)

    def test_attribute_belief_updates_existing(self):
        self.tom.attribute_belief('agent_y', 'is_trader', 0.6, evidence=['one trade'])
        self.tom.attribute_belief('agent_y', 'is_trader', 0.9,
                                   evidence=['many trades'], inferred_from='observation')
        beliefs = self.tom.get_beliefs('agent_y')
        self.assertEqual(len(beliefs), 1)
        self.assertEqual(beliefs[0].confidence, 0.9)

    def test_get_beliefs_min_confidence_filter(self):
        self.tom.attribute_belief('agent_z', 'low_conf', 0.3, evidence=[])
        self.tom.attribute_belief('agent_z', 'high_conf', 0.8, evidence=[])
        filtered = self.tom.get_beliefs('agent_z', min_confidence=0.5)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].belief_predicate, 'high_conf')

    def test_get_all_agents(self):
        self.tom.observe_action('alice', 'like')
        self.tom.attribute_belief('bob', 'active', 0.7, evidence=[])
        agents = self.tom.get_all_agents()
        self.assertIn('alice', agents)
        self.assertIn('bob', agents)


class TestTheoryOfMindSerialization(unittest.TestCase):
    def setUp(self):
        self.tom = TheoryOfMind()

    def test_to_dict_round_trip(self):
        self.tom.observe_action('alice', 'reply', target='post_1')
        self.tom.attribute_belief('bob', 'friendly', 0.7, evidence=['hello'])
        data = self.tom.to_dict()
        self.assertIn('observations', data)
        self.assertIn('beliefs', data)
        self.assertIn('intents', data)
        self.assertIn('alice', data['observations'])
        self.assertIn('bob', data['beliefs'])


class TestBeliefAttributionDataclass(unittest.TestCase):
    def test_to_dict(self):
        b = BeliefAttribution(
            agent_id='test_agent',
            belief_predicate='is_active',
            confidence=0.85,
            evidence=['seen online'],
            inferred_from='observation',
        )
        d = b.to_dict()
        self.assertEqual(d['agent_id'], 'test_agent')
        self.assertEqual(d['belief_predicate'], 'is_active')
        self.assertIn('created_at', d)

    def test_default_last_updated(self):
        b = BeliefAttribution(agent_id='a', belief_predicate='b',
                               confidence=0.5, evidence=[], inferred_from='obs')
        self.assertIsNotNone(b.created_at)
        self.assertIsNotNone(b.last_updated)


class TestObservedActionDataclass(unittest.TestCase):
    def test_to_dict(self):
        o = ObservedAction(agent_id='a', action_type='reply',
                            target='t', context={'key': 'val'})
        d = o.to_dict()
        self.assertEqual(d['action_type'], 'reply')
        self.assertEqual(d['context']['key'], 'val')


class TestIntentInferenceDataclass(unittest.TestCase):
    def test_to_dict(self):
        ii = IntentInference(agent_id='a', inferred_intent='engage',
                              confidence=0.9, supporting_actions=['reply'],
                              explanation='test')
        d = ii.to_dict()
        self.assertEqual(d['inferred_intent'], 'engage')
        self.assertEqual(d['confidence'], 0.9)


class TestGetTheoryOfMind(unittest.TestCase):
    def test_singleton(self):
        tom1 = get_theory_of_mind()
        tom2 = get_theory_of_mind()
        self.assertIs(tom1, tom2)


if __name__ == '__main__':
    unittest.main()
