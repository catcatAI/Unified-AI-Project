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
    assert len(result["objects"]) == 2, result["tracks"]


def test_one_square_seen_twice_is_one_track():
    # Adjacent fixations on the same square must merge (persistence),
    # not double-count. This is what blob counting cannot do.
    img = Image.new("RGB", (192, 192), (240, 240, 240))
    img.paste(Image.new("RGB", (50, 50), (200, 30, 30)), (70, 70))
    result = scan(_png(img))
    assert len(result["objects"]) == 1, result["tracks"]
    assert result["objects"][0]["fixations"] >= 2


def test_blank_is_zero_tracks():
    img = Image.new("RGB", (192, 192), (240, 240, 240))
    result = scan(_png(img))
    assert result["objects"] == []


def test_textured_ground_is_residue_not_object():
    # Busy but ground-colored (the track-7 case from blind 001): kept in
    # residue, excluded from the object count.
    import random

    random.seed(7)
    img = Image.new("RGB", (192, 192), (240, 240, 240))
    px = img.load()
    for y in range(128, 192):
        for x in range(192):
            # Sparse dark speckle on ground: top stays ground, structure busy.
            if random.random() < 0.15:
                v = 200 + random.randint(0, 16)
                px[x, y] = (v, v, v)
    result = scan(_png(img))
    ground_tracks = [t for t in result["tracks"] if t["ground_texture"]]
    assert ground_tracks, "textured band must leave residue"
    assert all(t not in result["objects"] for t in ground_tracks)
