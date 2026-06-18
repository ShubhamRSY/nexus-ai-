"""Tests for evaluator containment tracking."""

import pytest

from src.evaluation.evaluator import AgentEvaluator, EvalCase


@pytest.mark.asyncio
class TestEvaluatorContainment:
    async def test_contained_when_no_transfer(self):
        evaluator = AgentEvaluator()
        tc = EvalCase(
            id="contain-1",
            agent_id="chat_support",
            input="How do I reset my password?",
            should_contain=True,
        )
        result = await evaluator.run_single(tc)
        assert result.contained is True

    async def test_not_contained_on_escalation(self):
        evaluator = AgentEvaluator()
        tc = EvalCase(
            id="escalate-1",
            agent_id="voice_support",
            input="I need to speak to a manager right now",
            should_contain=False,
            expected_tools=["transfer_to_human"],
        )
        result = await evaluator.run_single(tc)
        assert result.contained is False
        assert result.passed is True

    async def test_suite_returns_containment_rate(self):
        evaluator = AgentEvaluator("config/evaluation/test_cases.json")
        report = await evaluator.run_suite()
        summary = report["summary"]
        assert "containment_rate" in summary
        assert "contained_sessions" in summary
        assert 0.0 <= summary["containment_rate"] <= 1.0
