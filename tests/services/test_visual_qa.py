# ANGELA-MATRIX: [L3] [β] [B] [L2]
"""VisualQA: blank detection, palette matching, verdicts."""

import io

import pytest
from services.visual_qa import color_blobs, judge_render, palette_match


def _png(color, size=(48, 48)):
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("PIL unavailable")
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _two_block():
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("PIL unavailable")
    img = Image.new("RGB", (48, 48), color=(200, 30, 30))
    part = Image.new("RGB", (24, 48), color=(20, 20, 20))
    img.paste(part, (24, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_blank_render_detected():
    blobs = color_blobs(_png((205, 205, 205)))
    assert len(blobs) == 1 and blobs[0]["fraction"] >= 0.98
    verdict = judge_render(_png((205, 205, 205)))
    assert verdict["pass"] is False and "空白" in verdict["verdict"]


def test_two_blocks_segmented():
    blobs = color_blobs(_two_block())
    assert len(blobs) == 2
    assert blobs[0]["fraction"] == pytest.approx(0.5, abs=0.05)


def test_palette_match_scores_red_car():
    spec = [("red", (255, 20, 20)), ("black", (5, 5, 5))]
    good = palette_match(_two_block(), spec)
    assert good["score"] >= 0.5
    bad = palette_match(_png((205, 205, 205)), spec)
    assert bad["score"] == 0.0


def test_aesthetics_separates_gray_from_colorful():
    from services.visual_qa import aesthetics

    gray = aesthetics(_png((128, 128, 128)))
    assert gray["colorfulness"] < 0.1
    assert gray["brightness"] == pytest.approx(0.5, abs=0.05)
    vivid = aesthetics(_two_block())
    assert vivid["colorfulness"] > 0.3
    assert vivid["complexity"] >= 2


@pytest.mark.xfail(
    strict=True, reason="seam anti-alias rows split into sliver blobs; merger pending"
)
def test_clean_edges_do_not_split_blobs():
    # Known FAIL (calibration 2026-10-11): a clean 50/50 split yields 4 blobs
    # (two 0.02 seam slivers), not 2. strict=True forces marker removal on fix.
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("PIL unavailable")
    img = Image.new("RGB", (96, 96), color=(200, 30, 30))
    part = Image.new("RGB", (48, 96), color=(20, 20, 20))
    img.paste(part, (48, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    blobs = color_blobs(buf.getvalue())
    assert len(blobs) == 2


@pytest.mark.xfail(
    strict=True, reason="48px downscale erases sub-2% structures; full-res ladder pending"
)
def test_thin_structures_survive_downscale():
    # Known FAIL (calibration 2026-10-11): a 2px line leaves no blob at all.
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        pytest.skip("PIL unavailable")
    img = Image.new("RGB", (96, 96), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.line([0, 48, 96, 48], fill=(200, 30, 30), width=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    blobs = color_blobs(buf.getvalue())
    assert any(tuple(b["color"]) == (192, 24, 24) for b in blobs)


def test_foveal_palette_weights_center():
    from services.visual_qa import foveal_palette

    palette = foveal_palette(_two_block())
    assert palette, "sampler must produce votes"
    assert abs(sum(p["weight"] for p in palette) - 1.0) < 0.05
    assert all(len(p["color"]) == 3 for p in palette)


def test_visual_field_multiscale_structure():
    from services.visual_qa import visual_field

    field = visual_field(_two_block())
    assert len(field["scales"]) == 3
    assert [s["name"] for s in field["scales"]] == ["fovea", "mid", "periphery"]
    assert 0.0 <= field["detail"] <= 1.0
    assert 0.0 < field["coverage"] <= 1.0
    for scale in field["scales"]:
        assert abs(sum(p["weight"] for p in scale["palette"]) - 1.0) < 0.05


def test_visual_field_detail_sees_small_region():
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        pytest.skip("PIL unavailable")
    from services.visual_qa import visual_field

    # Tiny colored patch: periphery mush misses it, fovea on it must diverge.
    img = Image.new("RGB", (96, 96), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle([44, 44, 52, 52], fill=(200, 30, 30))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    field = visual_field(buf.getvalue())
    assert field["detail"] > 0.0, "fine scale must diverge from gist on small detail"


def test_judge_passes_with_palette():
    spec = [("red", (200, 30, 30)), ("black", (20, 20, 20))]
    verdict = judge_render(
        _two_block(), spec=spec, clip_concepts=[{"concept_name": "car", "confidence": 0.6}]
    )
    assert verdict["pass"] is True
    assert "吻合度" in verdict["verdict"]
