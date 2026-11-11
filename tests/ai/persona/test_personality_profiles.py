# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""
Unit tests for Angela canonical personality profiles, Space avatars, and knowledge bases.
Ensures that no profiles contain placeholder zeros, empty arrays, or unpopulated schemas.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_angela_core_profile_completeness():
    profile_path = ROOT / "apps/backend/configs/personality_profiles/angela_core.json"
    assert profile_path.is_file(), f"missing {profile_path}"
    with open(profile_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["profile_name"] == "angela_core"
    assert data["character_id"] == "angela.core"
    assert data["version"] == "1.0.0"
    traits = data["personality_traits_base"]
    assert len(traits) >= 8
    # Assert no placeholder 0.0 values
    for trait_name, val in traits.items():
        assert val > 0.0, f"trait {trait_name} is zero placeholder"
    assert data["core_values"]
    assert data["behavioral_guidelines"]


def test_lucifaella_profile_completeness():
    profile_path = ROOT / "apps/backend/configs/personality_profiles/lucifaella.json"
    assert profile_path.is_file(), f"missing {profile_path}"
    with open(profile_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["profile_name"] == "lucifaella"
    assert data["character_id"] == "angela.lucifaella"
    assert data["core_id"] == "angela.core"
    assert data["role"] == "迎賓主持／看板娘"
    traits = data["personality_traits_base"]
    for trait_name, val in traits.items():
        assert val > 0.0, f"trait {trait_name} is zero placeholder"


def test_miko_base_profile_has_no_zero_placeholders():
    profile_path = ROOT / "apps/backend/configs/personality_profiles/miko_base.json"
    assert profile_path.is_file()
    with open(profile_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    traits = data["personality_traits_base"]
    for trait_name, val in traits.items():
        assert val > 0.0, f"miko trait {trait_name} was left as 0.0 placeholder"


def test_fragmenta_persona_chain_is_populated():
    chain_path = ROOT / "apps/backend/data/knowledge_bases/Fragmenta_persona_chain.json"
    assert chain_path.is_file()
    with open(chain_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) >= 5, "chain must contain cognitive stages, not empty list"
    stage_ids = [s["stage_id"] for s in data]
    assert "observer" in stage_ids
    assert "analyzer" in stage_ids
    assert "synthesizer" in stage_ids
    assert "empathizer" in stage_ids
    assert "reflector" in stage_ids


def test_angela_knowledge_base_files():
    personality_path = ROOT / "apps/backend/data/knowledge_bases/AngelaAI_personality.json"
    formulas_path = ROOT / "apps/backend/data/knowledge_bases/AngelaAI_formulas.json"
    assert personality_path.is_file()
    assert formulas_path.is_file()

    with open(personality_path, "r", encoding="utf-8") as f:
        pdata = json.load(f)
    assert pdata["character_id"] == "angela.core"
    assert pdata["personality_traits"]["curiosity"] > 0.5

    with open(formulas_path, "r", encoding="utf-8") as f:
        fdata = json.load(f)
    assert len(fdata) >= 5


def test_space_lucifaella_avatar():
    avatar_path = ROOT / "space/avatars/lucifaella.json"
    assert avatar_path.is_file()
    with open(avatar_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["avatar_id"] == "lucifaella"
    assert data["character_id"] == "angela.lucifaella"
    assert data["palette"]["hair"] == "#E88DB8"
    assert data["palette"]["eyes"] == "#69A9E8"
    assert data["palette"]["signature"] == "#C9A44C"
