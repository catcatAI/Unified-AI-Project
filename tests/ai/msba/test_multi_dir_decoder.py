# -*- coding: utf-8 -*-
"""
Tests for MSBA MultiDirectionalDecoder.
"""

import pytest

from ai.msba.multi_dir_decoder import MultiDirectionalDecoder
from ai.msba.types import FusedRepresentation, SeedResult


class TestMultiDirectionalDecoder:
    def test_creation(self):
        decoder = MultiDirectionalDecoder()
        assert decoder.dictionary is None
        assert decoder.llm_service is None

    def test_decode_basic(self):
        decoder = MultiDirectionalDecoder()
        fused = FusedRepresentation(
            primary={
                ("emotional", "happiness", 0.9): 0.9,
                ("cognitive", "focus", 0.6): 0.6,
            },
            dimensions=["emotional", "cognitive"],
            confidence=0.75,
        )
        seed = SeedResult(answer="42", confidence=0.8)
        result = decoder.decode(fused, seed)
        assert result != ""
        assert "happiness" in result.lower() or "42" in result

    def test_decode_empty_fused(self):
        decoder = MultiDirectionalDecoder()
        fused = FusedRepresentation()
        result = decoder.decode(fused, SeedResult())
        assert result == "I'm not sure how to respond to that."

    def test_decode_high_confidence_seed(self):
        decoder = MultiDirectionalDecoder()
        fused = FusedRepresentation(
            primary={},
            dimensions=[],
            confidence=0.5,
        )
        seed = SeedResult(answer="42", confidence=0.99)
        result = decoder.decode(fused, seed)
        assert "42" in result

    def test_decode_with_extra_context(self):
        decoder = MultiDirectionalDecoder()
        fused = FusedRepresentation(
            primary={},
            dimensions=[],
            confidence=0.5,
        )
        seed = SeedResult(answer="42", confidence=0.99)
        result = decoder.decode(fused, seed, extra_context="extra")
        assert "extra" in result

    def test_decode_drift_too_high(self):
        decoder = MultiDirectionalDecoder()
        fused = FusedRepresentation(
            primary={
                ("emotional", "happiness", 0.9): 0.9,
            },
            dimensions=["emotional"],
            confidence=0.9,
        )
        seed = SeedResult(answer="42", confidence=0.99)
        # Drift should trigger fallback to seed
        result = decoder.decode(fused, seed)
        assert "42" in result

    def test_decode_dimension(self):
        decoder = MultiDirectionalDecoder()
        activations = {
            ("a", "b", 1.0): 0.9,
            ("c", "d", 2.0): 0.6,
        }
        result = decoder._decode_dimension(activations)
        assert result != ""
        assert "b" in result
        assert "d" in result

    def test_decode_dimension_empty(self):
        decoder = MultiDirectionalDecoder()
        result = decoder._decode_dimension({})
        assert result == ""

    def test_empty_response_with_seed(self):
        decoder = MultiDirectionalDecoder()
        result = decoder._empty_response(SeedResult(answer="42", confidence=0.8))
        assert result == "42"

    def test_empty_response_no_seed(self):
        decoder = MultiDirectionalDecoder()
        result = decoder._empty_response(SeedResult())
        assert result == "I'm not sure how to respond to that."
