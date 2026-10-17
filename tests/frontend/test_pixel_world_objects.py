"""PixelObject 規範樣例契約測試（apps/pixel-angela/data/world_objects/）。

WHY: world_manifest.md §3 規定物件以 JSON 描述檔交付，但 PixelWorld 運行時
尚未實作（全倉零代碼引用）。本測試守護樣例檔的欄位契約，確保運行時落地時
註冊表可直接消費、且 manifest 與樣例不漂移。
"""

import json
from pathlib import Path

import pytest

OBJECTS_DIR = (
    Path(__file__).resolve().parents[2] / "apps" / "pixel-angela" / "data" / "world_objects"
)
SAMPLES = sorted(OBJECTS_DIR.glob("*.json"))
CATEGORIES = {"static", "consumable", "living"}
INTERACT_MODES = {"block", "consume", "observe"}


def test_samples_exist():
    assert len(SAMPLES) >= 3, f"expected >=3 spec samples, found {len(SAMPLES)}"


@pytest.mark.parametrize("path", SAMPLES, ids=[p.stem for p in SAMPLES] or ["<none>"])
def test_sample_contract(path):
    data = json.loads(path.read_text(encoding="utf-8"))

    for key in (
        "name",
        "category",
        "collision",
        "pattern",
        "palette",
        "metabolic_impact",
        "interact",
    ):
        assert key in data, f"{path.name}: missing required key '{key}'"

    assert data["name"] == path.stem, f"name '{data['name']}' must match filename"
    assert data["category"] in CATEGORIES, data["category"]

    col = data["collision"]
    assert set(col) == {"x", "y", "w", "h"}, col
    assert all(isinstance(col[k], int) for k in col), col
    assert col["w"] > 0 and col["h"] > 0, col

    pattern = data["pattern"]
    assert pattern, "pattern must be non-empty"
    width = len(pattern[0])
    assert all(len(row) == width for row in pattern), "pattern rows must be equal width"

    palette = data["palette"]
    assert palette, "palette must be non-empty"
    # every pattern character must resolve to a palette colour
    for row in pattern:
        for ch in row:
            if ch != ".":
                assert ch in palette, f"pattern char '{ch}' not in palette"

    impact = data["metabolic_impact"]
    assert set(impact) == {"energy", "arousal"}, impact
    assert all(isinstance(v, (int, float)) for v in impact.values()), impact

    interact = data["interact"]
    assert interact["on_contact"] in INTERACT_MODES, interact


def test_names_unique():
    names = [json.loads(p.read_text(encoding="utf-8"))["name"] for p in SAMPLES]
    assert len(names) == len(set(names)), f"duplicate names: {names}"
