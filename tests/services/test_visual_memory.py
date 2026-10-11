# ANGELA-MATRIX: [L3] [β] [B] [L2]
"""VisualMemory: saccades + persistence. Ground-truth calibrated."""

import io

import pytest
from PIL import Image
from services.visual_memory import scan


def _png(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_two_separated_squares_are_two_tracks():
    img = Image.new("RGB", (192, 192), (240, 240, 240))
    img.paste(Image.new("RGB", (30, 30), (200, 30, 30)), (20, 80))
    img.paste(Image.new("RGB", (30, 30), (200, 30, 30)), (140, 80))
    result = scan(_png(img))
    assert len(result["tracks"]) == 2, result["tracks"]


def test_one_square_seen_twice_is_one_track():
    # Adjacent fixations on the same square must merge (persistence),
    # not double-count. This is what blob counting cannot do.
    img = Image.new("RGB", (192, 192), (240, 240, 240))
    img.paste(Image.new("RGB", (50, 50), (200, 30, 30)), (70, 70))
    result = scan(_png(img))
    assert len(result["tracks"]) == 1, result["tracks"]
    assert result["tracks"][0]["fixations"] >= 2


def test_blank_is_zero_tracks():
    img = Image.new("RGB", (192, 192), (240, 240, 240))
    result = scan(_png(img))
    assert result["tracks"] == []
