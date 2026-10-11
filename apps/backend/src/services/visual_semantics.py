# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L2]
# =============================================================================
"""L4 track semantics — per-track probes, decisions written back, merge by
decision (2026-10-11).

Region tracks (19 on 001) become person tracks by asking each crop WHAT it
is: CLIP probe per track-crop (fast, seconds), VLM referee only on dispute.
Merge rule: adjacent tracks with the same person-decision join one group.
Count = person groups. This is the continuity the region votes lacked:
the straddling middle fairy is asked once per track and merged once.
"""

from __future__ import annotations

import io
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from PIL import Image as _PILImage
except Exception:
    _PILImage = None  # type: ignore[assignment]

PERSON_CANDIDATES = ("an anime character", "background scenery")
_FALLBACK_SNAP = "models--openai--clip-vit-base-patch32"


def _clip_snapshot() -> Optional[str]:
    root = os.path.expanduser("~/.cache/huggingface/hub")
    snap_root = os.path.join(root, _FALLBACK_SNAP, "snapshots")
    if not os.path.isdir(snap_root):
        return None
    for snap in sorted(os.listdir(snap_root)):
        if os.path.exists(os.path.join(snap_root, snap, "preprocessor_config.json")):
            return os.path.join(snap_root, snap)
    return None


def crop_for_track(image_data: bytes, box: List[float], max_side: int = 256) -> Optional[bytes]:
    """Full-resolution crop of a track box (relative coords) as PNG bytes."""
    if _PILImage is None:
        return None
    try:
        img = _PILImage.open(io.BytesIO(image_data)).convert("RGB")
        w, h = img.size
        crop = img.crop(
            (
                max(int(box[0] * w), 0),
                max(int(box[1] * h), 0),
                min(int(box[2] * w), w),
                min(int(box[3] * h), h),
            )
        )
        crop.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        crop.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as exc:
        logger.debug(f"track crop failed: {exc}")
        return None


def clip_probe(crop_png: bytes, candidates: Tuple[str, ...] = PERSON_CANDIDATES) -> Dict[str, Any]:
    """Zero-shot probe of one crop. Returns winner + margin (first-hand)."""
    snap = _clip_snapshot()
    if snap is None or _PILImage is None:
        return {"winner": None, "margin": 0.0, "probs": {}}
    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor

        model = CLIPModel.from_pretrained(snap)
        proc = CLIPProcessor.from_pretrained(snap)
        img = _PILImage.open(io.BytesIO(crop_png)).convert("RGB")
        inp = proc(text=list(candidates), images=img, return_tensors="pt", padding=True)
        with torch.no_grad():
            out = model(**inp)
        probs = out.logits_per_image.softmax(dim=1)[0].tolist()
        ranked = sorted(zip(candidates, probs), key=lambda kv: -kv[1])
        margin = ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0.0)
        return {
            "winner": ranked[0][0],
            "margin": round(margin, 3),
            "probs": {c: round(p, 3) for c, p in ranked},
        }
    except Exception as exc:
        logger.debug(f"CLIP probe failed: {exc}")
        return {"winner": None, "margin": 0.0, "probs": {}}


def _touch(a: List[float], b: List[float]) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def merge_by_decision(tracks: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Group touching tracks that share the same person-decision.

    Pure (probe outcomes injected as track['decision']). One group = one
    persistent thing = counted once. Straddlers merge instead of doubling.
    """
    groups: List[List[Dict[str, Any]]] = []
    for track in tracks:
        placed = False
        for group in groups:
            if group[0].get("decision") == track.get("decision") and any(
                _touch(track["box"], member["box"]) for member in group
            ):
                group.append(track)
                placed = True
                break
        if not placed:
            groups.append([track])
    return groups
