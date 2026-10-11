# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L2]
# =============================================================================
"""Visual working memory — saccades + persistence, not snapshots (2026-10-11).

One-shot sampling is a photo, not vision. Seeing is: saccade across the
scene, decide WHAT each small pile of pixels is, store (pixels + decision)
in working memory, and align later fixations against stored decisions
(persistence). No zoom, no focus, no residue, no saccades — no correctness.

Loop: coarse grid pass (gist) → revisit high-detail cells zoomed (focus) →
merge into persistent object tracks (residue). Count = tracks, not blobs.
"""

from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from PIL import Image as _PILImage
except Exception:
    _PILImage = None  # type: ignore[assignment]

# Merge bars (audit-tuned on synthetic ground truth, see tests).
SIG_DISTANCE_BAR = 0.6  # palette L1/2 above this = different object
MIN_OBJECT_FRACTION = 0.004  # smaller than this = fragment, not object


def _load(max_side: int, image_data: bytes) -> Optional[Any]:
    if _PILImage is None:
        return None
    try:
        img = _PILImage.open(io.BytesIO(image_data)).convert("RGB")
        img.thumbnail((max_side, max_side))
        return img
    except Exception as exc:
        logger.debug(f"visual memory load failed: {exc}")
        return None


def _quantize(px: Tuple[int, int, int], step: int = 24) -> Tuple[int, int, int]:
    return (px[0] // step * step, px[1] // step * step, px[2] // step * step)


def _signature(
    palette: List[Tuple[Tuple[int, int, int], float]],
) -> Dict[Tuple[int, int, int], float]:
    total = sum(w for _, w in palette) or 1.0
    return {c: w / total for c, w in palette}


def _sig_distance(
    a: Dict[Tuple[int, int, int], float], b: Dict[Tuple[int, int, int], float]
) -> float:
    union = set(a) | set(b)
    return sum(abs(a.get(c, 0.0) - b.get(c, 0.0)) for c in union) / 2.0


def _crop_palette(
    img: Any, box: Tuple[int, int, int, int]
) -> List[Tuple[Tuple[int, int, int], float]]:
    """Dominant quantized colors inside box (relative 0..1 coords)."""
    w, h = img.size
    x0, y0, x1, y1 = (int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))
    crop = img.crop((max(x0, 0), max(y0, 0), min(x1, w), min(y1, h)))
    px = list(crop.getdata())
    n = max(len(px), 1)
    import collections as _collections

    counts = _collections.Counter(_quantize(p) for p in px)
    return [(c, v / n) for c, v in counts.most_common(5)]


def _structure(img: Any, box: Tuple[int, int, int, int]) -> str:
    """Model-decided structure class for this pile of pixels: flat/edge/busy."""
    pal = _crop_palette(img, box)
    if not pal:
        return "flat"
    top_w = pal[0][1]
    if top_w >= 0.92:
        return "flat"
    if len(pal) <= 3 and top_w >= 0.6:
        return "edge"
    return "busy"


def _boxes_overlap(
    a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]
) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


class ObjectTrack:
    """One persistent thing: many fixations, one identity."""

    _next_id = 0

    def __init__(
        self,
        palette: List[Tuple[Tuple[int, int, int], float]],
        box: Tuple[float, ...],
        structure: str,
    ):
        ObjectTrack._next_id += 1
        self.id = ObjectTrack._next_id
        self.signature = _signature(palette)
        self.box = box
        self.structures: List[str] = [structure]
        self.fixations = 1

    def matches(
        self, palette: List[Tuple[Tuple[int, int, int], float]], box: Tuple[float, ...]
    ) -> bool:
        return (
            _boxes_overlap(self.box, box)
            and _sig_distance(self.signature, _signature(palette)) < SIG_DISTANCE_BAR
        )

    def absorb(
        self,
        palette: List[Tuple[Tuple[int, int, int], float]],
        box: Tuple[float, ...],
        structure: str,
    ) -> None:
        sig = _signature(palette)
        for color, weight in sig.items():
            self.signature[color] = (self.signature.get(color, 0.0) * self.fixations + weight) / (
                self.fixations + 1
            )
        self.box = (
            min(self.box[0], box[0]),
            min(self.box[1], box[1]),
            max(self.box[2], box[2]),
            max(self.box[3], box[3]),
        )
        self.structures.append(structure)
        self.fixations += 1


def scan(image_data: bytes, grid: int = 3) -> Dict[str, Any]:
    """Saccadic scan: coarse grid, then zoomed revisits, merged to tracks.

    Returns tracks (persistent objects), ground color, fixation log.
    """
    img = _load(192, image_data)
    if img is None:
        return {"tracks": [], "ground": None, "fixations": 0}
    w, h = img.size
    full = _crop_palette(img, (0, 0, 1, 1))
    ground = full[0][0] if full else (0, 0, 0)

    ObjectTrack._next_id = 0
    tracks: List[ObjectTrack] = []
    fixations = 0

    def _fixate(box: Tuple[float, float, float, float]) -> None:
        nonlocal fixations
        fixations += 1
        pal = _crop_palette(img, box)
        if not pal:
            return
        structure = _structure(img, box)
        if structure == "flat" and pal[0][0] == ground:
            return  # ground residue, not a thing
        for track in tracks:
            if track.matches(pal, box):
                track.absorb(pal, box, structure)
                return
        tracks.append(ObjectTrack(pal, box, structure))

    cell = 1.0 / grid
    hot: List[Tuple[float, float, float, float]] = []
    for gy in range(grid):
        for gx in range(grid):
            box = (gx * cell, gy * cell, (gx + 1) * cell, (gy + 1) * cell)
            _fixate(box)
            # Focus: anything not-ground deserves a second, zoomed look.
            # Busy-only revisits starve edge cells of their second fixation
            # (no persistence proof). Ground-flat cells stay skipped.
            structure = _structure(img, box)
            if structure in ("edge", "busy"):
                hot.append(box)
    # Zoomed revisits: quarter-window fixations inside hot cells.
    for x0, y0, x1, y1 in hot:
        qw, qh = (x1 - x0) / 2.0, (y1 - y0) / 2.0
        for dy in (0, 1):
            for dx in (0, 1):
                _fixate((x0 + dx * qw, y0 + dy * qh, x0 + (dx + 1) * qw, y0 + (dy + 1) * qh))

    objects = [
        {
            "id": t.id,
            "fixations": t.fixations,
            "box": [round(v, 3) for v in t.box],
            "top_color": list(max(t.signature.items(), key=lambda kv: kv[1])[0]),
            "structures": t.structures,
        }
        for t in tracks
    ]
    return {"tracks": objects, "ground": list(ground), "fixations": fixations}
