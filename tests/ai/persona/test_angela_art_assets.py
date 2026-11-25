# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""
Art-asset integrity for the Angela character (portrait, icon, wardrobe layers).

Kept separate from ``test_personality_profiles.py`` on purpose: these
assertions describe pixels (canvas size, alpha channel), so they travel with
the art work rather than with the persona configuration.
"""

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]


def test_angela_art_assets_integrity():
    master_ref = ROOT / "resources/canon/master_character_sheet.jpg"
    assert master_ref.is_file(), f"missing locked master setting reference {master_ref}"
    with Image.open(master_ref) as im:
        assert im.size == (896, 1200)

    spec_doc = ROOT / "resources/canon/MASTER_SPEC.md"
    assert spec_doc.is_file()
    assert "angela.core@1.0.0-locked" in spec_doc.read_text(encoding="utf-8")

    viewer_icon = ROOT / "apps/web-live2d-viewer/assets/angela-viewer-icon.svg"
    assert viewer_icon.is_file()
    content = viewer_icon.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "#E88DB8" in content  # rose
    assert "#C9A44C" in content  # signature gold star

    portrait_path = ROOT / "resources/angela_core_portrait.jpg"
    assert portrait_path.is_file()
    with Image.open(portrait_path) as im:
        assert im.size == (896, 1200)

    desktop_icon = ROOT / "apps/desktop-app/electron_app/assets/icon.png"
    assert desktop_icon.is_file()
    with Image.open(desktop_icon) as im:
        assert im.size == (256, 256)
        assert im.mode == "RGBA"


def test_base_mannequin_wardrobe_contract():
    mannequin_path = ROOT / "resources/wardrobe/base_mannequin.png"
    assert mannequin_path.is_file()
    with Image.open(mannequin_path) as im:
        assert im.size == (768, 1376)
        assert im.mode == "RGBA"
        # Verify alpha transparency exists
        extrema = im.getextrema()
        assert extrema[3][0] == 0  # has fully transparent pixels
        assert extrema[3][1] == 255  # has fully opaque pixels

    catalog_path = ROOT / "resources/wardrobe/catalog.json"
    assert catalog_path.is_file()
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["character_id"] == "angela.core"
    assert "base_mannequin" in data
    assert "top" in data["slots"]
    assert "bottom" in data["slots"]

    # Verify transparent clothing overlay and composited dressed sprite
    outfit_path = ROOT / "resources/wardrobe/outfit_workshop.png"
    assert outfit_path.is_file()
    with Image.open(outfit_path) as im:
        assert im.size == (768, 1376)
        assert im.mode == "RGBA"

    dressed_path = ROOT / "resources/wardrobe/angela_dressed_workshop.png"
    assert dressed_path.is_file()
    with Image.open(dressed_path) as im:
        assert im.size == (768, 1376)
        assert im.mode == "RGBA"


def test_canon_standee_and_expressions_contract():
    catalog_path = ROOT / "resources/canon/catalog.json"
    assert catalog_path.is_file()
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    assert catalog["character_id"] == "angela.core"
    assert catalog["canon_version"] == "angela.core@1.0.0-locked"
    assert catalog["rendering_mode"] == "standee_switching"

    # Verify all canonical standees
    for key in ("workshop", "casual_hoodie"):
        entry = catalog["standees"][key]
        img_path = ROOT / entry["path"]
        assert img_path.is_file(), f"Missing canonical standee: {img_path}"
        with Image.open(img_path) as im:
            assert im.size == (896, 1200)
            assert im.mode == "RGBA"
            extrema = im.getextrema()
            assert extrema[3][0] == 0
            assert extrema[3][1] == 255

    # Verify all 6 canonical expressions + smug alias
    expected_exprs = ("smile", "happy", "thinking", "blush", "serious", "witty")
    for key in expected_exprs:
        entry = catalog["expressions"][key]
        img_path = ROOT / entry["path"]
        assert img_path.is_file(), f"Missing canonical expression: {img_path}"
        with Image.open(img_path) as im:
            assert im.size == (512, 512)
            assert im.mode == "RGBA"
            extrema = im.getextrema()
            assert extrema[3][0] == 0
            assert extrema[3][1] == 255

    assert (ROOT / "resources/canon/expressions/smug.png").is_file()
