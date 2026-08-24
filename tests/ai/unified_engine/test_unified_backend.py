"""
Unified Engine integration test — the production LLM routing entry point.

Verifies the unified backend is registered through the real config-driven
router (step 6 of UNIFIED_AI_ENGINE.md: replace three_axis/ED3N/GARDEN text
inference with the unified engine) and that it actually answers held-out
queries through the deterministic + learned layers.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "apps", "backend", "src")
    ),
)

from services.llm.providers.registry import LLMBackend  # noqa: E402
from services.llm.providers.unified import UnifiedBackend  # noqa: E402


class TestBackendRegistration:
    def test_unified_enum_exists(self):
        assert LLMBackend.UNIFIED.value == "unified"

    def test_factory_registered(self):
        from services.llm.router import _BACKEND_FACTORIES

        assert _BACKEND_FACTORIES.get("unified") == "_init_unified"

    def test_config_enables_unified_first(self):
        from core.system.config.tiered_loader import get_config

        cfg = get_config("system/llm")
        backends = cfg.get("backends") or {}
        assert "unified-1g" in backends
        assert backends["unified-1g"]["provider"] == "unified"
        # priority 1 = first local text-inference backend.
        assert backends["unified-1g"]["priority"] == 1

    def test_routing_policy_uses_unified(self):
        from core.system.config.tiered_loader import get_config

        cfg = get_config("system/llm")
        policy = (cfg.get("routing") or {}).get("policy") or {}
        assert policy.get("math") == "unified-1g"
        assert policy.get("general") == "unified-1g"


class TestUnifiedBackendInference:
    @pytest.fixture()
    def backend(self):
        return UnifiedBackend(model="unified-1g")

    async def test_health(self, backend):
        assert await backend.check_health()

    async def test_deterministic_math(self, backend):
        r = await backend.generate("752 * 851=?")
        assert r.backend == "unified"
        assert "639952" in r.text
        assert r.metadata.get("route") == "deterministic-math"

    async def test_deterministic_logic(self, backend):
        r = await backend.generate("not (true and false)=?")
        assert r.metadata.get("route") == "deterministic-logic"
        assert "true" in r.text.lower()

    async def test_wrapper_stripped(self, backend):
        r = await backend.generate("<user_message>752 * 851=?</user_message>")
        assert "639952" in r.text

    async def test_statistical_core_route(self, backend):
        # A logic-style proposition (not pure truth-table) routes to the
        # learned statistical core and returns a True/False answer.
        # Train some boolean data first (fresh backend has no stat data).
        backend._get_engine().learn_batch(
            ["water is wet nor hydrogen is flammable=false"] * 5
        )
        r = await backend.generate("water is wet nor hydrogen is flammable=?")
        assert r.metadata.get("route") == "statistical-core"
        assert r.text.lower() in (
            "water is wet nor hydrogen is flammable=true",
            "water is wet nor hydrogen is flammable=false",
        )
