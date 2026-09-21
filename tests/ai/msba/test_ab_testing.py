# -*- coding: utf-8 -*-
"""
Tests for MSBA ABTesting.
"""

import pytest

from ai.msba.ab_testing import ABTesting


class MockPipeline:
    """Mock pipeline for testing."""

    def __init__(self, response: str = "response"):
        self.response = response
        self.call_count = 0

    def process(self, input_text: str) -> str:
        self.call_count += 1
        return f"{self.response}: {input_text}"


class TestABTesting:
    def test_creation(self):
        msba = MockPipeline("msba")
        legacy = MockPipeline("legacy")
        ab = ABTesting(msba, legacy, msba_percentage=0.5)
        assert ab.msba_percentage == 0.5

    def test_route_msba(self):
        msba = MockPipeline("msba")
        legacy = MockPipeline("legacy")
        ab = ABTesting(msba, legacy, msba_percentage=1.0)

        # With 100% MSBA, all routes should go to MSBA
        for _ in range(10):
            result = ab.route("test input")
            assert "msba" in result
        assert msba.call_count == 10
        assert legacy.call_count == 0

    def test_route_legacy(self):
        msba = MockPipeline("msba")
        legacy = MockPipeline("legacy")
        ab = ABTesting(msba, legacy, msba_percentage=0.0)

        # With 0% MSBA, all routes should go to legacy
        for _ in range(10):
            result = ab.route("test input")
            assert "legacy" in result
        assert msba.call_count == 0
        assert legacy.call_count == 10

    def test_metrics(self):
        msba = MockPipeline("msba")
        legacy = MockPipeline("legacy")
        ab = ABTesting(msba, legacy, msba_percentage=0.5)

        for _ in range(10):
            ab.route("test")

        metrics = ab.get_metrics()
        assert metrics["total_experiments"] == 10
        assert metrics["msba_count"] + metrics["legacy_count"] == 10

    def test_set_percentage(self):
        msba = MockPipeline("msba")
        legacy = MockPipeline("legacy")
        ab = ABTesting(msba, legacy, msba_percentage=0.1)

        ab.set_percentage(0.5)
        assert ab.msba_percentage == 0.5

    def test_set_percentage_bounds(self):
        msba = MockPipeline("msba")
        legacy = MockPipeline("legacy")
        ab = ABTesting(msba, legacy, msba_percentage=0.5)

        ab.set_percentage(1.5)
        assert ab.msba_percentage == 1.0

        ab.set_percentage(-0.5)
        assert ab.msba_percentage == 0.0

    def test_gradual_rollout(self):
        msba = MockPipeline("msba")
        legacy = MockPipeline("legacy")
        ab = ABTesting(msba, legacy, msba_percentage=0.0)

        results = ab.gradual_rollout([0.1, 0.5, 1.0])
        assert len(results) == 3
        assert results[0]["target_percentage"] == 0.1
        assert results[2]["target_percentage"] == 1.0
