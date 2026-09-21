# -*- coding: utf-8 -*-
"""
Tests for MSBA BlockCoordinator.
"""

import pytest
from ai.msba.block_coordinator import BlockCoordinator


class MockEngine:
    """Mock SNN engine for testing."""

    def __init__(self, warmed=False):
        self.W = None
        self.connections = {}
        if warmed:
            import numpy as np

            self.W = np.ones((5, 5)) * 0.1

    def forward(self, projection):
        return {k: v * 0.8 for k, v in projection.items()}

    def hebbian_update(self, input_keys, output_keys):
        pass


class TestBlockCoordinator:
    def test_creation(self):
        engine = MockEngine()
        coord = BlockCoordinator(engine, "test_block")
        assert coord.block_id == "test_block"
        assert coord.engine is engine

    def test_is_warmed_with_weights(self):
        engine = MockEngine(warmed=True)
        coord = BlockCoordinator(engine, "test")
        assert coord.is_warmed

    def test_is_warmed_without_weights(self):
        engine = MockEngine(warmed=False)
        coord = BlockCoordinator(engine, "test")
        # W is None, should not be warmed
        assert not coord.is_warmed

    def test_is_warmed_no_engine(self):
        coord = BlockCoordinator(None, "test")
        assert not coord.is_warmed

    def test_compute_basic(self):
        engine = MockEngine()
        coord = BlockCoordinator(engine, "test")
        result = coord.compute({"a": 1.0, "b": 0.5})
        assert "a" in result
        assert "b" in result
        assert result["a"] == pytest.approx(0.8)

    def test_compute_with_seed(self):
        engine = MockEngine()
        coord = BlockCoordinator(engine, "test")
        result = coord.compute({"a": 1.0}, seed_projection={"a": 0.5})
        assert "a" in result

    def test_compute_no_engine(self):
        coord = BlockCoordinator(None, "test")
        result = coord.compute({"a": 1.0})
        assert result == {"a": 1.0}

    def test_compute_engine_failure(self):
        class FailingEngine:
            def forward(self, x):
                raise RuntimeError("fail")

        coord = BlockCoordinator(FailingEngine(), "test")
        result = coord.compute({"a": 1.0})
        # Should return input as degradation
        assert result == {"a": 1.0}

    def test_hebbian_update(self):
        engine = MockEngine()
        coord = BlockCoordinator(engine, "test")
        coord.hebbian_update({"a": 1.0}, {"b": 1.0})
        # No assertion needed, just verify no exception

    def test_hebbian_update_no_engine(self):
        coord = BlockCoordinator(None, "test")
        coord.hebbian_update({"a": 1.0}, {"b": 1.0})
        # No assertion needed
