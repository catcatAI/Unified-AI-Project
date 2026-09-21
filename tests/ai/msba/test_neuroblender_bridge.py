# -*- coding: utf-8 -*-
"""
Tests for MSBA NeuroBlenderBridge.
"""

import numpy as np
import pytest
from ai.msba.neuroblender_bridge import (
    BLENDER_DIMS,
    FUSED_TO_BLENDER_MAP,
    NeuroBlenderBridge,
)
from ai.msba.types import FusedRepresentation


class TestNeuroBlenderBridge:
    def test_creation(self):
        bridge = NeuroBlenderBridge()
        assert bridge.dim_count == 9
        assert len(bridge.dim_names) == 9

    def test_fused_to_blender_vector(self):
        bridge = NeuroBlenderBridge()
        fused = FusedRepresentation(
            primary={
                ("emotional", "happiness", 0.9): 0.9,
                ("cognitive", "focus", 0.6): 0.6,
            },
            dimensions=["emotional", "cognitive"],
        )
        vec = bridge.fused_to_blender_vector(fused)
        assert vec.shape == (9,)
        assert np.max(np.abs(vec)) <= 1.0  # Normalized

    def test_fused_to_blender_empty(self):
        bridge = NeuroBlenderBridge()
        fused = FusedRepresentation()
        vec = bridge.fused_to_blender_vector(fused)
        assert vec.shape == (9,)
        assert np.all(vec == 0)

    def test_blender_to_context(self):
        bridge = NeuroBlenderBridge()
        vec = np.array([0.8, 0.6, 0.4, 0.2, 0.1, 0.3, 0.5, 0.7, 0.9])
        context = bridge.blender_to_context(vec)
        assert "alpha_energy" in context
        assert context["alpha_energy"] == pytest.approx(0.8)

    def test_get_dominant_dimension(self):
        bridge = NeuroBlenderBridge()
        vec = np.zeros(9)
        vec[2] = 0.9  # gamma_valence
        dominant = bridge.get_dominant_dimension(vec)
        assert dominant == "gamma_valence"

    def test_get_dominant_dimension_empty(self):
        bridge = NeuroBlenderBridge()
        vec = np.array([])
        dominant = bridge.get_dominant_dimension(vec)
        assert dominant is None

    def test_get_dimension_weights(self):
        bridge = NeuroBlenderBridge()
        fused = FusedRepresentation(
            primary={
                ("emotional", "happiness", 0.9): 0.9,
                ("emotional", "sadness", 0.1): 0.1,
                ("cognitive", "focus", 0.6): 0.6,
            },
            dimensions=["emotional", "cognitive"],
        )
        weights = bridge.get_dimension_weights(fused)
        assert "gamma_valence" in weights
        assert "beta_curiosity" in weights

    def test_mapping_completeness(self):
        # All 9 dimensions should be mapped
        assert len(FUSED_TO_BLENDER_MAP) == 9
        assert len(BLENDER_DIMS) == 9
        for key in FUSED_TO_BLENDER_MAP:
            assert key in [
                "biological",
                "cognitive",
                "emotional",
                "social",
                "mathematical",
                "temporal",
                "causal",
                "knowledge",
                "linguistic",
            ]
