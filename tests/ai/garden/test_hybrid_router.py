# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [C] [L0]
# =============================================================================
"""
Tests for GARDEN HybridRouter (ED3N/GARDEN/cloud routing).
"""

import pytest

from apps.backend.src.ai.garden.hybrid_router import HybridRouter, TierResult


class TestTierResult:
    """Tests for TierResult dataclass."""

    def test_create(self):
        tr = TierResult(tier="garden", text="hello", confidence=0.8, latency_ms=15.0)
        assert tr.tier == "garden"
        assert tr.text == "hello"
        assert tr.confidence == 0.8
        assert tr.latency_ms == 15.0
        assert tr.error is None
        assert tr.keys == []

    def test_with_error(self):
        tr = TierResult(
            tier="ed3n", text="", confidence=0.0, latency_ms=0.0, error="Failed"
        )
        assert tr.error == "Failed"

    def test_with_keys(self):
        tr = TierResult(
            tier="garden",
            text="response",
            confidence=0.7,
            latency_ms=10.0,
            keys=["g1", "g5"],
        )
        assert tr.keys == ["g1", "g5"]


class TestHybridRouterInit:
    """Tests for router construction."""

    def test_init_defaults(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        assert hr.ed3n_threshold == 0.90
        assert hr.garden_threshold == 0.60
        assert hr.max_latency_ms == 1000.0
        assert hr.enable_adaptive_routing is True
        assert hr.has_ed3n is False
        assert hr.has_garden is False
        assert hr.has_cloud is False

    def test_init_custom(self):
        hr = HybridRouter(
            ed3n_threshold=0.80,
            garden_threshold=0.50,
            max_latency_ms=500.0,
            enable_adaptive_routing=False,
        )
        assert hr.ed3n_threshold == 0.80
        assert hr.garden_threshold == 0.50
        assert hr.max_latency_ms == 500.0
        assert hr.enable_adaptive_routing is False

    def test_backend_availability(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        assert hr.has_ed3n is False
        assert hr.has_garden is False
        assert hr.has_cloud is False


class MockED3NEngine:
    """Mock ED3N engine for testing."""

    def __init__(self, response: str = "reflex response", confidence: float = 0.95):
        self.response = response
        self.confidence = confidence

    def process(self, text: str):
        if text == "fail":
            raise RuntimeError("Mock failure")
        return self.response


class MockGARDENEngine:
    """Mock GARDEN engine for testing."""

    def __init__(self, response: str = "garden response"):
        self.response = response

    def process(self, text: str, context=None):
        if text == "fail":
            raise RuntimeError("Mock failure")
        return self.response


class MockCloudBackend:
    """Mock cloud LLM backend for testing."""

    def __init__(self, response_text: str = "cloud response"):
        self.response_text = response_text

    async def generate(self, prompt: str):
        from core.interfaces.protocols import LLMResponse
        if prompt == "fail":
            raise RuntimeError("Mock cloud failure")
        return LLMResponse(
            text=self.response_text,
            backend="mock",
            model="mock",
            tokens_used=10,
            confidence=0.95,
        )


class TestHybridRouterBackends:
    """Tests for setting backends."""

    def test_set_ed3n(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        hr.set_ed3n(MockED3NEngine())
        assert hr.has_ed3n is True

    def test_set_garden(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        hr.set_garden(MockGARDENEngine())
        assert hr.has_garden is True

    def test_set_cloud(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        hr.set_cloud(MockCloudBackend())
        assert hr.has_cloud is True


class TestHybridRouterRouting:
    """Tests for the routing logic."""

    @pytest.mark.asyncio
    async def test_empty_input(self, hybrid_router: HybridRouter):
        result = await hybrid_router.route("")
        assert result.tier == "none"
        assert result.text == ""
        assert result.error == "Empty input"

    @pytest.mark.asyncio
    async def test_no_backends(self, hybrid_router: HybridRouter):
        result = await hybrid_router.route("hello")
        assert result.tier == "none"
        assert "No AI backend available" in result.text

    @pytest.mark.asyncio
    async def test_ed3n_route(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        hr.ed3n_threshold = 0.80  # Lower threshold so ED3N's 0.85 confidence qualifies
        hr.set_ed3n(MockED3NEngine(response="reflex hit"))
        hr.set_garden(MockGARDENEngine())
        hr.set_cloud(MockCloudBackend())
        result = await hr.route("hello")
        assert result.tier == "ed3n"
        assert result.text == "reflex hit"

    @pytest.mark.asyncio
    async def test_ed3n_low_confidence_falls_through(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        # Set threshold high so ED3N won't qualify
        hr.ed3n_threshold = 0.99
        hr.set_ed3n(MockED3NEngine(response="reflex"))
        hr.set_garden(MockGARDENEngine(response="garden response"))
        hr.set_cloud(MockCloudBackend())
        result = await hr.route("hello")
        # Should fall through to garden or cloud
        assert result.tier in ("garden", "cloud")

    @pytest.mark.asyncio
    async def test_garden_route(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        hr.set_ed3n(MockED3NEngine())
        # Lower ED3N threshold so it tries but falls to garden
        hr.ed3n_threshold = 0.99
        hr.set_garden(MockGARDENEngine(response="garden hit"))
        hr.set_cloud(MockCloudBackend())
        result = await hr.route("hello")
        # GARDEN should be selected (confidence 0.75 >= garden_threshold 0.60)
        assert result.tier == "garden"
        assert result.text == "garden hit"

    @pytest.mark.asyncio
    async def test_cloud_fallback(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        hr.set_ed3n(MockED3NEngine())
        hr.set_garden(MockGARDENEngine())
        hr.set_cloud(MockCloudBackend(response_text="cloud hit"))
        # Raise thresholds so ED3N and GARDEN both skip
        hr.ed3n_threshold = 0.99
        hr.garden_threshold = 0.99
        result = await hr.route("hello")
        assert result.tier == "cloud"
        assert result.text == "cloud hit"

    @pytest.mark.asyncio
    async def test_force_tier(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        hr.set_ed3n(MockED3NEngine(response="ed3n only"))
        hr.set_garden(MockGARDENEngine(response="garden only"))
        result = await hr.route("hello", force_tier="ed3n")
        assert result.text == "ed3n only"
        result2 = await hr.route("hello", force_tier="garden")
        assert result2.text == "garden only"

    @pytest.mark.asyncio
    async def test_ed3n_error_falls_through(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        hr.set_ed3n(MockED3NEngine(response=""))
        hr.set_garden(MockGARDENEngine(response="garden backup"))
        hr.set_cloud(MockCloudBackend())
        hr.ed3n_threshold = 0.99
        result = await hr.route("hello")
        # Should try garden as fallback
        assert result.tier in ("garden", "cloud")


class TestHybridRouterTracking:
    """Tests for performance tracking and adaptive routing."""

    def test_record_and_average(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        hr._record("ed3n", TierResult("ed3n", "a", 0.8, 10.0))
        hr._record("ed3n", TierResult("ed3n", "b", 0.9, 20.0))
        assert hr.get_average_latency("ed3n") == 15.0
        assert hr.get_success_rate("ed3n") == 1.0

    def test_success_rate(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        hr._record("ed3n", TierResult("ed3n", "ok", 0.8, 10.0))
        hr._record("ed3n", TierResult("ed3n", "", 0.0, 5.0, error="fail"))
        assert hr.get_success_rate("ed3n") == 0.5

    def test_empty_history(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        assert hr.get_average_latency("nonexistent") == 0.0
        assert hr.get_success_rate("nonexistent") == 0.0

    def test_tune_thresholds_disabled(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        hr.enable_adaptive_routing = False
        thresholds = hr.tune_thresholds()
        assert thresholds["ed3n"] == 0.90
        assert thresholds["garden"] == 0.60

    def test_tune_thresholds(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        # Simulate good ED3N performance
        for _ in range(50):
            hr._record("ed3n", TierResult("ed3n", "ok", 0.8, 5.0))
        for _ in range(50):
            hr._record("garden", TierResult("garden", "ok", 0.7, 15.0))
        thresholds = hr.tune_thresholds()
        assert thresholds["ed3n"] >= 0.90
        assert thresholds["garden"] <= 0.60


class TestHybridRouterStats:
    """Tests for statistics and diagnostics."""

    def test_get_stats_empty(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        s = hr.get_stats()
        assert s["total_decisions"] == 0
        assert s["adaptive_routing"] is True
        assert s["backends"]["ed3n"] is False

    def test_get_stats_with_decisions(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        from apps.backend.src.ai.garden.hybrid_router import RoutingDecision
        hr._decisions.append(RoutingDecision(
            query="test", selected_tier="ed3n",
            results={}, total_latency_ms=5.0,
            confidence=0.9, decision_reason="test",
        ))
        s = hr.get_stats()
        assert s["total_decisions"] == 1

    def test_get_recent_decisions(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        from apps.backend.src.ai.garden.hybrid_router import RoutingDecision
        hr._decisions.append(RoutingDecision(
            query="hello", selected_tier="ed3n",
            results={}, total_latency_ms=5.0,
            confidence=0.9, decision_reason="direct hit",
        ))
        recent = hr.get_recent_decisions(n=10)
        assert len(recent) == 1
        assert recent[0]["query"] == "hello"

    def test_clear_history(self, hybrid_router: HybridRouter):
        hr = hybrid_router
        hr._record("ed3n", TierResult("ed3n", "ok", 0.8, 10.0))
        hr.clear_history()
        assert len(hr._history["ed3n"]) == 0
        assert len(hr._decisions) == 0
