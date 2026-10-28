# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""
Unit tests for the AI + AL Joint Dataset loader and schema validation.
Ensures the 10 pilot samples are correctly formatted and fully accessible
by development tools and training pipelines.
"""

import json
import os

import pytest
from ai.core.ai_al_dataset_loader import AiAlDatasetLoader
from ai.core.ai_al_joint_dataset import (
    PILOT_AI_AL_DATASET,
    AiAlExample,
    AlStateVector,
    export_pilot_dataset_json,
)


def test_ai_al_pilot_dataset_length():
    """Verify that exactly 10 pilot samples are defined."""
    assert len(PILOT_AI_AL_DATASET) == 10


def test_ai_al_sample_structure():
    """Verify that every pilot sample contains both AI text fields and AL state vectors."""
    for ex in PILOT_AI_AL_DATASET:
        assert isinstance(ex, AiAlExample)
        assert ex.sample_id.startswith("aial_")
        assert len(ex.input_text) > 0
        assert len(ex.expected_response) > 0

        # Verify AL state vector structure
        assert isinstance(ex.al_state_in, AlStateVector)
        assert isinstance(ex.al_state_out, AlStateVector)

        # Check PAD ranges [-1.0, 1.0]
        for state in [ex.al_state_in, ex.al_state_out]:
            assert -1.0 <= state.pad_valence <= 1.0
            assert -1.0 <= state.pad_arousal <= 1.0
            assert -1.0 <= state.pad_dominance <= 1.0
            # Check metabolic ranges [0.0, 1.0]
            assert 0.0 <= state.fatigue <= 1.0
            assert 0.0 <= state.stress <= 1.0
            assert 0.0 <= state.health <= 1.0
            assert state.routing_mode in ["exploratory", "conservative", "neutral"]


def test_export_and_reload_dataset(tmp_path):
    """Test JSON export and reload compatibility for development tools."""
    test_file = tmp_path / "ai_al_pilot_test.json"
    exported_path = export_pilot_dataset_json(str(test_file))

    assert os.path.exists(exported_path)

    with open(exported_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["version"] == "1.0.0"
    assert data["total_samples"] == 10
    assert len(data["examples"]) == 10

    # Verify first sample roundtrip
    first_ex = data["examples"][0]
    assert first_ex["sample_id"] == "aial_001"
    assert "你好，Angela！" in first_ex["input_text"]
    assert first_ex["al_state_in"]["routing_mode"] == "exploratory"


def test_default_production_dataset_export():
    """Verify the production path dataset export works and is discoverable."""
    prod_path = AiAlDatasetLoader.DEFAULT_PATH
    exported_path = export_pilot_dataset_json(prod_path)
    assert os.path.exists(exported_path)

    # Confirm discoverability by inspection
    with open(exported_path, "r", encoding="utf-8") as f:
        content = json.load(f)
    assert content["total_samples"] >= 10
