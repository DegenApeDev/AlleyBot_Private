#!/usr/bin/env python3
"""Tests for GoalPlanner: LLM fallback decompose, domain detection."""

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agentic.goal_planner import (
    _fallback_decompose, llm_decompose, detect_domain,
    TOOL_REGISTRY,
)


class TestFallbackDecompose(unittest.TestCase):
    def test_fallback_decompose_returns_3_steps(self):
        steps = _fallback_decompose("Test goal", "general", TOOL_REGISTRY)
        self.assertEqual(len(steps), 3)
        for step in steps:
            self.assertIn('action', step)
            self.assertIn('plugin', step)
            self.assertIn('description', step)
            self.assertIn('confidence', step)

    def test_fallback_decompose_has_research_analyze_act(self):
        steps = _fallback_decompose("Post content", "social", TOOL_REGISTRY)
        # First step should be information gathering
        self.assertIn('feed', steps[0]['action'])
        # Last step should be an action (post)
        self.assertEqual(steps[2]['action'], 'post')

    def test_fallback_decompose_engage_goal(self):
        steps = _fallback_decompose("Engage with community", "social", TOOL_REGISTRY)
        self.assertEqual(steps[2]['action'], 'engage')

    def test_fallback_decompose_report_goal(self):
        steps = _fallback_decompose("Report findings", "analysis", TOOL_REGISTRY)
        self.assertEqual(steps[2]['action'], 'report')


class TestLLMDecompose(unittest.TestCase):
    def test_llm_decompose_fallback_when_llm_unavailable(self):
        """When llm_router is not importable, should fallback to template."""
        steps = llm_decompose("Test goal", "general", TOOL_REGISTRY)
        self.assertIsNotNone(steps)
        self.assertGreater(len(steps), 0)

    def test_llm_decompose_retries_and_falls_back(self):
        steps = llm_decompose("Unknown domain task", "unknown", TOOL_REGISTRY)
        self.assertIsNotNone(steps)
        self.assertGreater(len(steps), 0)


class TestDomainDetection(unittest.TestCase):
    def test_detect_social_domain(self):
        self.assertEqual(detect_domain("Post engaging content on Moltx"), 'social')

    def test_detect_market_domain(self):
        self.assertEqual(detect_domain("Trade on Polymarket"), 'market')

    def test_detect_analysis_domain(self):
        self.assertEqual(detect_domain("Analyze market trends"), 'analysis')

    def test_detect_unknown_domain(self):
        self.assertEqual(detect_domain("Completely random goal"), 'unknown')

    def test_detect_security_domain(self):
        self.assertEqual(detect_domain("Security check wallet"), 'security')

    def test_detect_self_improvement_domain(self):
        self.assertEqual(detect_domain("Improve my trading skill"), 'self_improvement')

    def test_detect_content_domain(self):
        self.assertEqual(detect_domain("Create a new article"), 'content')

    def test_detect_case_insensitive(self):
        self.assertEqual(detect_domain("POST ON MOLTX"), 'social')

    def test_detect_onchain_domain(self):
        self.assertEqual(detect_domain("Check wallet transaction"), 'onchain')


if __name__ == '__main__':
    unittest.main()
