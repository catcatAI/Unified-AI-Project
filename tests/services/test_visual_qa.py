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


def test_judge_passes_with_palette():
    spec = [("red", (200, 30, 30)), ("black", (20, 20, 20))]
    verdict = judge_render(
        _two_block(), spec=spec, clip_concepts=[{"concept_name": "car", "confidence": 0.6}]
    )
    assert verdict["pass"] is True
    assert "吻合度" in verdict["verdict"]
