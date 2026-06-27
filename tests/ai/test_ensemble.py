"""Tests for Model Ensemble - Response Fusion and Model Voting."""

import pytest

from apps.backend.src.ai.ensemble import (
    EnsembleResult,
    ModelWeight,
    ResponseFusionEngine,
)


class TestModelWeight:
    def test_default_values(self):
        mw = ModelWeight(model_id="test-model", weight=0.5)
        assert mw.model_id == "test-model"
        assert mw.weight == 0.5
        assert mw.priority == 1

    def test_custom_priority(self):
        mw = ModelWeight(model_id="high", weight=0.8, priority=5)
        assert mw.priority == 5


class TestEnsembleResult:
    def test_minimal_creation(self):
        result = EnsembleResult(
            content="hello", model_votes={"m1": 0.8},
            confidence=0.8, latency=1.5, token_usage={"total": 100},
        )
        assert result.content == "hello"
        assert result.confidence == 0.8

    def test_metadata_default(self):
        result = EnsembleResult(
            content="x", model_votes={},
            confidence=0.5, latency=0.1, token_usage={},
        )
        assert result.metadata == {}


class TestResponseFusionEngine:
    @pytest.fixture
    def engine(self):
        return ResponseFusionEngine()

    @pytest.fixture
    def sample_responses(self):
        return [
            FakeLLMResponse("model_a", "First response content here.", 0.5, {"total": 50}),
            FakeLLMResponse("model_b", "Second response with more details.", 1.2, {"total": 80}),
            FakeLLMResponse("model_c", "Short.", 2.5, {"total": 30}),
        ]

    def test_fuse_best_single(self, engine, sample_responses):
        weights = {"model_a": 0.4, "model_b": 0.4, "model_c": 0.2}
        result = engine.fuse(sample_responses, weights, strategy="best_single")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_fuse_empty_responses(self, engine):
        result = engine.fuse([], {}, strategy="best_single")
        assert result == ""

    def test_fuse_fallback_for_invalid_strategy(self, engine, sample_responses):
        weights = {"model_a": 0.5}
        result = engine.fuse(sample_responses, weights, strategy="nonexistent")
        assert isinstance(result, str)

    def test_quality_score_length_good(self, engine):
        resp = FakeLLMResponse("m", "A" * 200, 0.5, {})
        score = engine._calculate_quality_score(resp)
        assert 0.5 <= score <= 1.0

    def test_quality_score_empty(self, engine):
        resp = FakeLLMResponse("m", "", 0.5, {})
        score = engine._calculate_quality_score(resp)
        assert score < 0.7  # Empty content gets 0 for length, but still has coherence+latency bonuses

    def test_quality_score_latency_factor(self, engine):
        fast = FakeLLMResponse("m", "Good content here for testing.", 0.3, {})
        slow = FakeLLMResponse("m", "Good content here for testing.", 5.0, {})
        fast_score = engine._calculate_quality_score(fast)
        slow_score = engine._calculate_quality_score(slow)
        assert fast_score >= slow_score

    def test_all_fusion_strategies_available(self, engine):
        expected = {"best_single", "weighted_average", "consensus", "creative_blend"}
        assert set(engine.fusion_strategies.keys()) == expected


class FakeLLMResponse:
    """Minimal LLMResponse-compatible object for testing."""
    def __init__(self, model, content, latency, usage):
        self.model = model
        self.text = content
        self.response_time_ms = latency * 1000  # convert seconds to ms
        self.usage = usage

    @property
    def content(self):
        return self.text
