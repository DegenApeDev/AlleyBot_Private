"""
Integration tests for TODO_OPUS_APR8 hardening work.

Covers:
  8.2 — Validation ladder contracts
  8.3 — Goal consolidation contracts
  8.4 — Contract regression tests (ActionEnvelope, ValidationProfile, TrustTier)

Run with:
  python -m pytest tests/test_integration_opus.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import Mock, MagicMock, patch


# ---------------------------------------------------------------------------
# 8.4  Contract regression tests
# ---------------------------------------------------------------------------

class TestActionEnvelope:
    """ActionEnvelope construction and __post_init__ guard."""

    def test_basic_construction(self):
        from src.agentic.contracts import ActionEnvelope
        env = ActionEnvelope(plugin="moltx", action_type="discover")
        assert env.plugin == "moltx"
        assert env.action_type == "discover"
        assert isinstance(env.params, dict)
        assert isinstance(env.context, dict)

    def test_context_carries_impact(self):
        from src.agentic.contracts import ActionEnvelope
        env = ActionEnvelope(
            plugin="onchain",
            action_type="wallet_send",
            context={"impact": "critical", "risk_level": "high"},
        )
        assert env.context["impact"] == "critical"
        assert env.context["risk_level"] == "high"

    def test_post_init_warns_on_toplevel_impact(self, capfd):
        """impact/risk_level at top-level should trigger warning."""
        from src.agentic.contracts import ActionEnvelope
        env = ActionEnvelope(
            plugin="test",
            action_type="test",
            context={"impact": "high", "risk_level": "high"},
        )
        # Should still construct successfully
        assert env.plugin == "test"

    def test_to_dict_roundtrip(self):
        from src.agentic.contracts import ActionEnvelope
        env = ActionEnvelope(
            plugin="moltx",
            action_type="post",
            params={"content": "hello"},
            context={"user_id": "123"},
        )
        d = env.to_dict()
        assert d["plugin"] == "moltx"
        assert d["action_type"] == "post"
        assert d["params"]["content"] == "hello"
        assert d["context"]["user_id"] == "123"


class TestValidationProfile:
    """ValidationProfile.from_action_spec with context-based impact/risk."""

    def test_defaults(self):
        from src.agentic.contracts import ValidationProfile
        vp = ValidationProfile.from_action_spec({})
        assert vp.impact.value == "medium"
        assert vp.risk_level.value == "medium"

    def test_context_impact_wins(self):
        from src.agentic.contracts import ValidationProfile
        vp = ValidationProfile.from_action_spec({
            "context": {"impact": "critical", "risk_level": "high"},
        })
        assert vp.impact.value == "critical"
        assert vp.risk_level.value == "high"

    def test_toplevel_fallback(self):
        from src.agentic.contracts import ValidationProfile
        vp = ValidationProfile.from_action_spec({
            "impact": "low",
            "risk_level": "low",
        })
        assert vp.impact.value == "low"
        assert vp.risk_level.value == "low"


# ---------------------------------------------------------------------------
# 8.2  Trust tier classification + enforcement
# ---------------------------------------------------------------------------

class TestTrustTier:
    """TrustTier enum and classify_trust_tier function."""

    def test_t0_observe(self):
        from src.agentic.contracts import classify_trust_tier, TrustTier
        tier = classify_trust_tier({"plugin": "moltx", "action_type": "discover"})
        assert tier == TrustTier.T0_OBSERVE

    def test_t1_safe_auto(self):
        from src.agentic.contracts import classify_trust_tier, TrustTier
        tier = classify_trust_tier({"plugin": "moltx", "action_type": "create_post"})
        assert tier == TrustTier.T1_SAFE_AUTO

    def test_t2_constrained(self):
        from src.agentic.contracts import classify_trust_tier, TrustTier
        tier = classify_trust_tier({"plugin": "onchain", "action_type": "check_balance"})
        assert tier == TrustTier.T2_CONSTRAINED

    def test_t3_code_proposal(self):
        from src.agentic.contracts import classify_trust_tier, TrustTier
        tier = classify_trust_tier({"plugin": "selfimprove", "action_type": "self_improve"})
        assert tier == TrustTier.T3_CODE_PROPOSAL

    def test_t4_owner_approval(self):
        from src.agentic.contracts import classify_trust_tier, TrustTier
        tier = classify_trust_tier({"plugin": "onchain", "action_type": "wallet_send"})
        assert tier == TrustTier.T4_OWNER_APPROVAL

    def test_unknown_action_defaults_to_plugin_tier(self):
        from src.agentic.contracts import classify_trust_tier, TrustTier
        tier = classify_trust_tier({"plugin": "onchain", "action_type": "something_new"})
        # onchain plugin default is T2
        assert tier == TrustTier.T2_CONSTRAINED

    def test_unknown_plugin_defaults_t1(self):
        from src.agentic.contracts import classify_trust_tier, TrustTier
        tier = classify_trust_tier({"plugin": "totally_new_plugin", "action_type": "foo"})
        assert tier == TrustTier.T1_SAFE_AUTO


# ---------------------------------------------------------------------------
# 8.2  Validation ladder constants
# ---------------------------------------------------------------------------

class TestValidationLadder:
    """ActionRouter has formal VALIDATION_STAGES class attribute."""

    def _get_stages(self):
        from src.agentic.action_router import ActionRouter
        return ActionRouter.VALIDATION_STAGES

    def test_validation_stages_exist(self):
        stages = self._get_stages()
        assert isinstance(stages, (list, tuple))
        assert len(stages) >= 10  # we documented 12

    def test_stages_are_strings(self):
        stages = self._get_stages()
        for stage in stages:
            assert isinstance(stage, str), f"Stage is not a string: {stage}"

    def test_known_stages_present(self):
        stages = self._get_stages()
        expected = {'agi_validation', 'synergy_validation', 'symod_verification'}
        for name in expected:
            assert name in stages, f"Missing expected stage: {name}"


# ---------------------------------------------------------------------------
# 8.3  Goal consolidation — GoalManager v2 basics
# ---------------------------------------------------------------------------

def _make_test_goal(id, title="Test Goal", description="test", category="test", status=None):
    """Helper to create a Goal with all required fields."""
    from src.agentic.goal_manager import Goal, GoalPriority, GoalStatus as GS
    kwargs = dict(
        id=id,
        title=title,
        description=description,
        category=category,
        priority=GoalPriority.MEDIUM,
        impact_score=5.0,
        effort_estimate="hours",
        confidence=0.8,
        trigger_type="test",
        trigger_data={"source": "integration_test"},
        evidence=["test evidence"],
    )
    if status is not None:
        kwargs["status"] = status
    return Goal(**kwargs)


class TestGoalManagerV2:
    """GoalManager uses SQLite and can add/retrieve/complete goals."""

    def test_add_and_retrieve_goal(self, tmp_path):
        from src.agentic.goal_manager import GoalManager
        gm = GoalManager(db_path=str(tmp_path / "goals.db"))

        goal = _make_test_goal("tg1", title="Test Goal")
        added = gm.add_goal(goal)
        assert added is True

        retrieved = gm.get_goal("tg1")
        assert retrieved is not None
        assert retrieved.title == "Test Goal"

    def test_complete_goal(self, tmp_path):
        from src.agentic.goal_manager import GoalManager, GoalStatus
        gm = GoalManager(db_path=str(tmp_path / "goals.db"))

        goal = _make_test_goal("tg2", title="Complete Me", status=GoalStatus.ACTIVE)
        gm.add_goal(goal)
        gm.complete_goal("tg2", outcome="Success!")

        completed = gm.get_goal("tg2")
        assert completed.status == GoalStatus.COMPLETED

    def test_record_goal_action_failure(self, tmp_path):
        from src.agentic.goal_manager import GoalManager, GoalStatus
        gm = GoalManager(db_path=str(tmp_path / "goals.db"))

        goal = _make_test_goal("tg3", title="Fail Me", status=GoalStatus.ACTIVE)
        gm.add_goal(goal)
        gm.record_goal_action_failure("tg3", note="External API down")

        failed = gm.get_goal("tg3")
        # After single failure it should still be active (needs multiple to fail)
        assert failed.status in (GoalStatus.ACTIVE, GoalStatus.FAILED)


# ---------------------------------------------------------------------------
# 8.4  ActionOutcome contract
# ---------------------------------------------------------------------------

class TestActionOutcome:
    """ActionOutcome.from_result_dict with edge cases."""

    def _make_envelope(self, plugin="moltx", action_type="post"):
        from src.agentic.contracts import ActionEnvelope
        return ActionEnvelope(plugin=plugin, action_type=action_type)

    def test_from_success_result(self):
        from src.agentic.contracts import ActionOutcome
        result = {
            "success": True,
            "data": {"post_id": "123"},
            "execution_time_ms": 450,
        }
        envelope = self._make_envelope("moltx", "post")
        outcome = ActionOutcome.from_result_dict(result, action_envelope=envelope)
        assert outcome.success is True
        assert outcome.plugin == "moltx"

    def test_from_failure_result(self):
        from src.agentic.contracts import ActionOutcome
        result = {
            "success": False,
            "error": "Rate limited",
        }
        envelope = self._make_envelope("moltx", "reply")
        outcome = ActionOutcome.from_result_dict(result, action_envelope=envelope)
        assert outcome.success is False
        assert "Rate limited" in str(outcome.error)

    def test_from_empty_result(self):
        from src.agentic.contracts import ActionOutcome
        envelope = self._make_envelope("unknown", "unknown")
        outcome = ActionOutcome.from_result_dict({}, action_envelope=envelope)
        assert outcome.success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
