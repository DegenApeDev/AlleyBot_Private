#!/usr/bin/env python3
"""Tests for Phase 3: Curiosity and Self-Direction features."""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import MagicMock, patch
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.curiosity import (
    CuriosityDrive, CuriosityGoal, ActionRecency,
    GoalSource, GoalType, EXPLORATION_TARGETS,
    get_curiosity_drive,
)
from src.agentic.belief_engine import BeliefEngine
from src.agentic.self_model import SelfModel
from src.agentic.goal_planner import GoalPlanner


class TestCuriosityDriveInit(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.be = BeliefEngine(storage_path=os.path.join(self.tmpdir, 'beliefs.json'))
        self.sm = SelfModel(storage_path=os.path.join(self.tmpdir, 'self_model.json'))
        self.gp = GoalPlanner(storage_path=os.path.join(self.tmpdir, 'plans.json'))
        self.cd = CuriosityDrive(
            belief_engine=self.be,
            self_model=self.sm,
            goal_planner=self.gp,
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_with_engines(self):
        self.assertIsNotNone(self.cd.belief_engine)
        self.assertIsNotNone(self.cd.self_model)
        self.assertIsNotNone(self.cd.goal_planner)

    def test_set_engines(self):
        cd2 = CuriosityDrive()
        self.assertIsNone(cd2.belief_engine)
        cd2.set_engines(self.be, self.sm, self.gp)
        self.assertIsNotNone(cd2.belief_engine)

    def test_get_curiosity_drive_factory(self):
        cd = get_curiosity_drive(self.be, self.sm, self.gp)
        self.assertIsInstance(cd, CuriosityDrive)


class TestInformationGainScoring(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.be = BeliefEngine(storage_path=os.path.join(self.tmpdir, 'beliefs.json'))
        self.sm = SelfModel(storage_path=os.path.join(self.tmpdir, 'self_model.json'))
        self.gp = GoalPlanner(storage_path=os.path.join(self.tmpdir, 'plans.json'))
        self.cd = CuriosityDrive(belief_engine=self.be, self_model=self.sm, goal_planner=self.gp)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_unknown_domain_has_high_information_gain(self):
        score = self.cd.calculate_information_gain('unknown_domain_xyz')
        self.assertGreater(score, 0.5)

    def test_well_known_domain_has_lower_gain(self):
        for i in range(10):
            self.be.update_from_outcome(
                action=f"social_action_{i}", domain="social",
                predicted_success=0.7, actual_success=True,
            )
        score_social = self.cd.calculate_information_gain('social')
        score_unknown = self.cd.calculate_information_gain('quantum_physics')
        self.assertGreater(score_unknown, score_social)

    def test_low_confidence_domain_has_higher_gain(self):
        self.be.update_from_outcome(
            action="risky_action", domain="trading",
            predicted_success=0.8, actual_success=False,
        )
        score = self.cd.calculate_information_gain('trading')
        self.assertGreater(score, 0.3)

    def test_no_belief_engine_returns_default(self):
        cd = CuriosityDrive()
        score = cd.calculate_information_gain('any_domain')
        self.assertEqual(score, 0.5)


class TestKnowledgeGapDetection(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.be = BeliefEngine(storage_path=os.path.join(self.tmpdir, 'beliefs.json'))
        self.sm = SelfModel(storage_path=os.path.join(self.tmpdir, 'self_model.json'))
        self.gp = GoalPlanner(storage_path=os.path.join(self.tmpdir, 'plans.json'))
        self.cd = CuriosityDrive(belief_engine=self.be, self_model=self.sm, goal_planner=self.gp)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_detects_gaps_in_low_belief_domains(self):
        gaps = self.cd.detect_knowledge_gaps()
        domain_types = {g['type'] for g in gaps}
        self.assertTrue('few_beliefs' in domain_types or 'no_experience' in domain_types or 'few_samples' in domain_types)

    def test_detects_few_samples_gap(self):
        self.sm.record_outcome(
            domain="market", action_type="scan",
            predicted_confidence=0.7, actual_success=True,
        )
        gaps = self.cd.detect_knowledge_gaps()
        market_gaps = [g for g in gaps if g['domain'] == 'market']
        self.assertGreater(len(market_gaps), 0)

    def test_gaps_sorted_by_severity(self):
        gaps = self.cd.detect_knowledge_gaps()
        if len(gaps) > 1:
            for i in range(len(gaps) - 1):
                self.assertGreaterEqual(gaps[i]['severity'], gaps[i + 1]['severity'])

    def test_returns_at_most_8_gaps(self):
        gaps = self.cd.detect_knowledge_gaps()
        self.assertLessEqual(len(gaps), 8)


class TestCuriosityGoalGeneration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.be = BeliefEngine(storage_path=os.path.join(self.tmpdir, 'beliefs.json'))
        self.sm = SelfModel(storage_path=os.path.join(self.tmpdir, 'self_model.json'))
        self.gp = GoalPlanner(storage_path=os.path.join(self.tmpdir, 'plans.json'))
        self.cd = CuriosityDrive(belief_engine=self.be, self_model=self.sm, goal_planner=self.gp)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generate_curiosity_goals_returns_list(self):
        goals = self.cd.generate_curiosity_goals()
        self.assertIsInstance(goals, list)

    def test_curiosity_goals_have_required_fields(self):
        goals = self.cd.generate_curiosity_goals()
        for goal in goals:
            self.assertIsInstance(goal, CuriosityGoal)
            self.assertIsNotNone(goal.goal_id)
            self.assertIsNotNone(goal.title)
            self.assertIsNotNone(goal.domain)
            self.assertIn(goal.source, [s.value for s in GoalSource])
            self.assertGreater(goal.priority, 0)

    def test_curiosity_goals_prioritize_low_data_domains(self):
        goals = self.cd.generate_curiosity_goals()
        if goals:
            self.assertGreater(goals[0].priority, 0.0)

    def test_generates_at_most_3_goals(self):
        goals = self.cd.generate_curiosity_goals()
        self.assertLessEqual(len(goals), 3)

    def test_generate_reflection_goals(self):
        reflection = {
            'learning_priorities': [
                {'domain': 'market', 'action_type': 'analyze',
                 'reason': 'insufficient_data', 'sample_size': 2, 'success_rate': 0.3}
            ],
            'weaknesses': [
                {'domain': 'trading', 'action_type': 'trade',
                 'success_rate': 0.2, 'consecutive_failures': 3}
            ],
        }
        goals = self.cd.generate_reflection_goals(reflection)
        self.assertIsInstance(goals, list)
        self.assertGreater(len(goals), 0)

    def test_reflection_goals_are_stored(self):
        reflection = {
            'learning_priorities': [
                {'domain': 'social', 'action_type': 'post',
                 'reason': 'low_data_with_failures', 'sample_size': 2, 'success_rate': 0.3}
            ],
            'weaknesses': [],
        }
        goals = self.cd.generate_reflection_goals(reflection)
        self.assertEqual(len(self.cd.curiosity_goals), len(goals))


class TestNoveltySeeking(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.be = BeliefEngine(storage_path=os.path.join(self.tmpdir, 'beliefs.json'))
        self.sm = SelfModel(storage_path=os.path.join(self.tmpdir, 'self_model.json'))
        self.gp = GoalPlanner(storage_path=os.path.join(self.tmpdir, 'plans.json'))
        self.cd = CuriosityDrive(belief_engine=self.be, self_model=self.sm, goal_planner=self.gp)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_novel_action_gets_high_score(self):
        novelty = self.cd.calculate_novelty_bonus('browse', 'social')
        self.assertGreater(novelty, 0.8)

    def test_recording_action_reduces_novelty(self):
        self.cd.record_action_attempt('social:browse')
        novelty = self.cd.calculate_novelty_bonus('browse', 'social')
        self.assertLess(novelty, 1.0)

    def test_action_recency_tracking(self):
        self.cd.record_action_attempt('social:browse')
        self.cd.record_action_attempt('social:browse')
        rec = self.cd.action_recency.get('social:browse')
        self.assertIsNotNone(rec)
        self.assertEqual(rec.attempt_count, 2)

    def test_get_under_explored_actions(self):
        self.cd.record_action_attempt('market:scan')
        under_explored = self.cd.get_under_explored_actions()
        self.assertIsInstance(under_explored, list)


class TestGoalPriorityScoring(unittest.TestCase):
    def setUp(self):
        self.cd = CuriosityDrive()

    def test_skill_gap_goals_score_higher_than_scheduled(self):
        curiosity_score = self.cd._calculate_goal_priority(
            info_gain=0.5, novelty=0.5, skill_gap=0.8,
            gap_severity=0.5, source=GoalSource.SKILL_GAP.value,
        )
        scheduled_score = self.cd._calculate_goal_priority(
            info_gain=0.5, novelty=0.5, skill_gap=0.2,
            gap_severity=0.3, source=GoalSource.SCHEDULED.value,
        )
        self.assertGreater(curiosity_score, scheduled_score)

    def test_priority_is_bounded(self):
        score = self.cd._calculate_goal_priority(
            info_gain=1.0, novelty=1.0, skill_gap=1.0,
            gap_severity=1.0, source=GoalSource.SKILL_GAP.value,
        )
        self.assertLessEqual(score, 1.0)
        low_score = self.cd._calculate_goal_priority(
            info_gain=0.0, novelty=0.0, skill_gap=0.0,
            gap_severity=0.0, source=GoalSource.EXTERNAL.value,
        )
        self.assertGreater(low_score, 0.0)

    def test_prioritize_goals_sorts_by_score(self):
        goals = [
            CuriosityGoal(
                goal_id="g1", title="Low priority", description="test",
                domain="social", goal_type="explore", source="curiosity",
                priority=0.3, information_gain_score=0.2, novelty_score=0.8,
                skill_gap_score=0.1, expected_uncertainty_reduction=0.1,
            ),
            CuriosityGoal(
                goal_id="g2", title="High priority", description="test",
                domain="market", goal_type="practice", source="skill_gap",
                priority=0.9, information_gain_score=0.8, novelty_score=0.3,
                skill_gap_score=0.9, expected_uncertainty_reduction=0.4,
            ),
        ]
        sorted_goals = self.cd.prioritize_goals(goals)
        self.assertEqual(sorted_goals[0].goal_id, "g2")


class TestIntrinsicReward(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.be = BeliefEngine(storage_path=os.path.join(self.tmpdir, 'beliefs.json'))
        self.sm = SelfModel(storage_path=os.path.join(self.tmpdir, 'self_model.json'))
        self.gp = GoalPlanner(storage_path=os.path.join(self.tmpdir, 'plans.json'))
        self.cd = CuriosityDrive(belief_engine=self.be, self_model=self.sm, goal_planner=self.gp)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_intrinsic_reward_for_successful_action(self):
        reward = self.cd.calculate_intrinsic_reward(
            domain='social', action='post',
            predicted_confidence=0.5, actual_success=True,
        )
        self.assertGreater(reward, 0.0)

    def test_intrinsic_reward_higher_for_novel_actions(self):
        reward_first = self.cd.calculate_intrinsic_reward(
            domain='social', action='post',
            predicted_confidence=0.5, actual_success=True,
        )
        reward_repeat = self.cd.calculate_intrinsic_reward(
            domain='social', action='post',
            predicted_confidence=0.5, actual_success=True,
        )
        self.assertGreaterEqual(reward_first, reward_repeat)

    def test_uncertain_actions_rewarded_more(self):
        reward_uncertain = self.cd.calculate_intrinsic_reward(
            domain='unknown_xyz', action='explore',
            predicted_confidence=0.2, actual_success=True,
        )
        reward_certain = self.cd.calculate_intrinsic_reward(
            domain='social', action='check',
            predicted_confidence=0.9, actual_success=True,
        )
        self.assertGreater(reward_uncertain, reward_certain)

    def test_reward_summary(self):
        self.cd.calculate_intrinsic_reward('social', 'browse', 0.7, True)
        self.cd.calculate_intrinsic_reward('market', 'scan', 0.5, False)
        summary = self.cd.get_intrinsic_reward_summary()
        self.assertEqual(summary['total_actions'], 2)
        self.assertIn('avg_intrinsic_reward', summary)

    def test_update_curiosity_goal_outcome(self):
        goals = self.cd.generate_curiosity_goals()
        if goals:
            self.cd.update_curiosity_goal_outcome(goals[0].goal_id, True, goals[0].domain)
            goal = self.cd.curiosity_goals[goals[0].goal_id]
            self.assertTrue(goal.attempted)
            self.assertEqual(goal.outcome, "success")


class TestActionRecency(unittest.TestCase):
    def test_never_attempted_has_perfect_novelty(self):
        rec = ActionRecency(action_key="test")
        self.assertEqual(rec.novelty_score(), 1.0)

    def test_recency_hours_calculation(self):
        from datetime import datetime
        rec = ActionRecency(
            action_key="test",
            last_attempted=datetime.now().isoformat(),
            attempt_count=1,
        )
        self.assertLess(rec.recency_hours(), 1.0)

    def test_day_counts_tracking(self):
        from datetime import datetime
        today = datetime.now().isoformat()[:10]
        rec = ActionRecency(
            action_key="test",
            last_attempted=datetime.now().isoformat(),
            attempt_count=1,
            day_counts={today: 1},
        )
        self.assertEqual(rec.day_counts.get(today), 1)


class TestCognitiveIntegrationCuriosity(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cognitive_has_curiosity(self):
        from src.agentic.cognitive_integration import CognitiveIntegration
        cognitive = CognitiveIntegration()
        self.assertIsNotNone(cognitive.curiosity)

    def test_get_curiosity_goals(self):
        from src.agentic.cognitive_integration import CognitiveIntegration
        cognitive = CognitiveIntegration()
        goals = cognitive.get_curiosity_goals()
        self.assertIsInstance(goals, list)

    def test_detect_knowledge_gaps(self):
        from src.agentic.cognitive_integration import CognitiveIntegration
        cognitive = CognitiveIntegration()
        gaps = cognitive.detect_knowledge_gaps()
        self.assertIsInstance(gaps, list)

    def test_calculate_intrinsic_reward(self):
        from src.agentic.cognitive_integration import CognitiveIntegration
        cognitive = CognitiveIntegration()
        reward = cognitive.calculate_intrinsic_reward('social', 'post', 0.5, True)
        self.assertIsInstance(reward, float)
        self.assertGreater(reward, 0.0)

    def test_get_curiosity_report(self):
        from src.agentic.cognitive_integration import CognitiveIntegration
        cognitive = CognitiveIntegration()
        report = cognitive.get_curiosity_report()
        self.assertIn('total_actions', report)
        self.assertIn('knowledge_gaps', report)
        self.assertIn('active_curiosity_goals', report)


if __name__ == '__main__':
    unittest.main()