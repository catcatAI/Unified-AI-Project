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


def clip_embed(crop_png: bytes) -> Optional[List[float]]:
    """Appearance vector of one crop (for re-id, not classification)."""
    snap = _clip_snapshot()
    if snap is None or _PILImage is None:
        return None
    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor

        model = CLIPModel.from_pretrained(snap)
        proc = CLIPProcessor.from_pretrained(snap)
        img = _PILImage.open(io.BytesIO(crop_png)).convert("RGB")
        inp = proc(images=img, return_tensors="pt")
        with torch.no_grad():
            vec = model.get_image_features(**inp)[0].flatten()
        vec = vec / vec.norm()
        flat = vec.tolist()
        return flat if flat and isinstance(flat[0], float) else None
    except Exception as exc:
        logger.debug(f"CLIP embed failed: {exc}")
        return None


def size_band(box: List[float]) -> int:
    """Log-area bucket: person vs its doll share looks, never size."""
    import math as _math

    area = max(box[2] - box[0], 0.0) * max(box[3] - box[1], 0.0)
    return int(round(_math.log2(max(area, 1e-6)) * 2.0))


def _cosine(a: List[float], b: List[float]) -> float:
    import math as _math

    dot = sum(x * y for x, y in zip(a, b))
    na = _math.sqrt(sum(x * x for x in a)) or 1.0
    nb = _math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def link_subjects(items: List[Dict[str, Any]], sim_bar: float = 0.9) -> List[List[Dict[str, Any]]]:
    """Re-id grouping: same decision + same looks + same size = one subject.

    Pure (embeddings injected as item['emb']). Replaces box-touch chaining:
    touching boxes of different subjects must NOT merge (the giant-group
    pathology), while distant boxes of one subject SHOULD (mirrored pairs).
    Person vs its doll: same looks, different size band -> two subjects.
    """
    parent = list(range(len(items)))

    def _find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def _union(i: int, j: int) -> None:
        parent[_find(i)] = _find(j)

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            if a.get("decision") != b.get("decision"):
                continue
            if a.get("decision") is None:
                continue
            if a.get("emb") is None or b.get("emb") is None:
                continue
            if size_band(a["box"]) != size_band(b["box"]):
                continue
            if _cosine(a["emb"], b["emb"]) >= sim_bar:
                _union(i, j)
    groups: Dict[int, List[Dict[str, Any]]] = {}
    for i, item in enumerate(items):
        groups.setdefault(_find(i), []).append(item)
    return list(groups.values())


# Probe margin below this = abstention (coin flips must not merge or count).
MARGIN_BAR = 0.2


def gate_decision(decision: Optional[str], margin: float) -> Optional[str]:
    """Weak probes abstain instead of joining groups."""
    if decision is None:
        return None
    return decision if margin >= MARGIN_BAR else None


def merge_by_decision(tracks: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Group touching tracks that share the same person-decision.

    Pure (probe outcomes injected as track['decision']). One group = one
    persistent thing = counted once. Straddlers merge instead of doubling.
    Abstained (None-decision) tracks never merge — an unanswered question
    must not move the count either way.
    """
    groups: List[List[Dict[str, Any]]] = []
    for track in tracks:
        decision = track.get("decision")
        placed = False
        if decision is not None:
            for group in groups:
                if group[0].get("decision") == decision and any(
                    _touch(track["box"], member["box"]) for member in group
                ):
                    group.append(track)
                    placed = True
                    break
        if not placed:
            groups.append([track])
    return groups


def group_box(group: List[Dict[str, Any]]) -> List[float]:
    """Union box of a group (for group-level referee crops)."""
    return [
        min(m["box"][0] for m in group),
        min(m["box"][1] for m in group),
        max(m["box"][2] for m in group),
        max(m["box"][3] for m in group),
    ]


def _quadrants(box: List[float]) -> List[List[float]]:
    x0, y0, x1, y1 = box
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    return [
        [x0, y0, mx, my],
        [mx, y0, x1, my],
        [x0, my, mx, y1],
        [mx, my, x1, y1],
    ]


def zoom_probe(
    image_data: bytes,
    box: List[float],
    probe_fn: Any,
    depth: int = 1,
) -> List[Dict[str, Any]]:
    """Recursive semantic zoom: probe the box; on weak verdicts, split and
    probe quadrants (the saccade principle one level down).

    probe_fn(crop_png) -> (decision, margin). Returns leaf verdicts with
    sub-boxes. Grid cells are not objects — sub-cell structures (dolls,
    hats inside a mask-read cell) only appear here.
    """
    crop = crop_for_track(image_data, box, max_side=512)
    if crop is None:
        return []
    decision, margin = probe_fn(crop)
    gated = gate_decision(decision, margin)
    leaves = [{"box": list(box), "decision": gated, "margin": margin}]
    if depth > 0 and gated is None:
        # Weak whole-box verdict: look inside instead of abstaining blind.
        for quad in _quadrants(list(box)):
            leaves.extend(zoom_probe(image_data, quad, probe_fn, depth - 1))
    return leaves
