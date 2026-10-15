# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L2]
# =============================================================================
"""VisualQA — deterministic image quality judgments (no LLM needed).

The project could SEE (vision_service features, CLIP) but never JUDGED:
answers about images were template rambles. This module turns pixels into
verdicts: color-blob segmentation (what regions exist), palette-vs-spec
matching, brightness/complexity gates, CLIP concept signal. Pure stdlib +
PIL/numpy, bounded and testable. Used by /chat/with-image for QA questions
(檢查/質量/怎麼樣) and by agent art loops (Unity/Blender513? no — renders).
"""

from __future__ import annotations

import io
import logging
import math
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from PIL import Image as _PILImage
except Exception:
    _PILImage = None  # type: ignore[assignment]


def _load_rgb(image_data: bytes, max_side: int = 64):
    """Downscaled RGB image for fast analysis."""
    if _PILImage is None:
        return None
    img = _PILImage.open(io.BytesIO(image_data)).convert("RGB")
    img.thumbnail((max_side, max_side))
    return img


def _quantize(px: Tuple[int, int, int], step: int = 24) -> Tuple[int, int, int]:
    return (px[0] // step * step, px[1] // step * step, px[2] // step * step)


def color_blobs(image_data: bytes, max_side: int = 48) -> List[Dict[str, Any]]:
    """Flood-fill color regions on a quantized thumbnail.

    Full-res ladder (calibration 2026-10-11, fixed 2026-10-14): sources whose
    longest side ≤ 4×max_side are analyzed at NATIVE resolution — bicubic
    thumbnailing of small images creates anti-alias seam slivers along hard
    edges and erases ≤2px structures entirely. Larger sources keep the fast
    thumbnail path; seam slivers are additionally absorbed by
    ``_merge_seam_slivers`` at every scale.

    Returns blobs sorted by size desc: {color, pixels, fraction, bbox}.
    A near-blank render yields exactly one background blob — the honest
    signal for "render produced nothing" (live 2026-10-11 Unity gray).
    """
    if _PILImage is None:
        return []
    with _PILImage.open(io.BytesIO(image_data)) as probe:
        native_max_side = max(probe.size)
    # Ladder: native up to 4×max_side (192px by default), thumbnail beyond
    scale = max_side if native_max_side > max_side * 4 else max_side * 4
    img = _load_rgb(image_data, scale)
    if img is None:
        return []
    w, h = img.size
    px = img.load()
    grid = [[_quantize(px[x, y]) for x in range(w)] for y in range(h)]
    seen = [[False] * w for _ in range(h)]
    blobs: List[Dict[str, Any]] = []
    for y in range(h):
        for x in range(w):
            if seen[y][x]:
                continue
            color = grid[y][x]
            queue = deque([(x, y)])
            seen[y][x] = True
            cells = 0
            x0 = x1 = x
            y0 = y1 = y
            while queue:
                cx, cy = queue.popleft()
                cells += 1
                x0, x1 = min(x0, cx), max(x1, cx)
                y0, y1 = min(y0, cy), max(y1, cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx]:
                        if grid[ny][nx] == color:
                            seen[ny][nx] = True
                            queue.append((nx, ny))
            blobs.append(
                {
                    "color": color,
                    "pixels": cells,
                    "fraction": round(cells / (w * h), 3),
                    "bbox": (x0, y0, x1, y1),
                }
            )
    blobs = _merge_seam_slivers(blobs, w, h)
    blobs.sort(key=lambda b: -b["pixels"])
    return blobs


def _abuts(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int], gap: int = 1) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return ax0 <= bx1 + gap and bx0 <= ax1 + gap and ay0 <= by1 + gap and by0 <= ay1 + gap


def _merge_seam_slivers(blobs: List[Dict[str, Any]], w: int, h: int) -> List[Dict[str, Any]]:
    """Absorb anti-alias seam slivers into the regions they interpolate.

    A resampled hard edge can leave a thin blob whose color sits BETWEEN two
    major regions. Absorb it only when it abuts ≥2 dominant (>15%) neighbors
    that are themselves more dissimilar to each other than to the sliver —
    the signature of an interpolation artifact. A genuine thin structure
    (line/text) touches one dominant region and is kept.
    """
    total = w * h
    min_big = 0.15 * total
    max_sliver = 0.05 * total
    out = list(blobs)
    merged = True
    while merged:
        merged = False
        for sliver in list(out):
            if sliver["pixels"] == 0 or sliver["pixels"] > max_sliver:
                continue
            bigs = [
                b
                for b in out
                if b is not sliver and b["pixels"] >= min_big and _abuts(sliver["bbox"], b["bbox"])
            ]
            if len(bigs) < 2:
                continue
            bigs.sort(key=lambda b: _color_distance(sliver["color"], b["color"]))
            nearest, second = bigs[0], bigs[1]
            d_between = _color_distance(nearest["color"], second["color"])
            if d_between <= _color_distance(
                sliver["color"], nearest["color"]
            ) or d_between <= _color_distance(sliver["color"], second["color"]):
                continue  # sliver is not interpolating between dissimilar regions
            x0, y0, x1, y1 = nearest["bbox"]
            sx0, sy0, sx1, sy1 = sliver["bbox"]
            nearest["bbox"] = (min(x0, sx0), min(y0, sy0), max(x1, sx1), max(y1, sy1))
            nearest["pixels"] += sliver["pixels"]
            out.remove(sliver)
            merged = True
            break
    for b in out:
        b["fraction"] = round(b["pixels"] / total, 3)
    return out


def _color_distance(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _sample_at(
    arr: Any, sampler: Any, center: Tuple[float, float], spread: float, count: int
) -> Dict[Tuple[int, int, int], float]:
    """One fixation: Gaussian cloud votes, intensity-weighted."""
    sampler.generate_cloud(count=count, center=center, spread=spread)
    h, w, _ = arr.shape
    votes: Dict[Tuple[int, int, int], float] = {}
    for p in sampler.particles:
        px = min(int(p.x * (w - 1)), w - 1)
        py = min(int(p.y * (h - 1)), h - 1)
        color = _quantize((int(arr[py, px, 0]), int(arr[py, px, 1]), int(arr[py, px, 2])))
        votes[color] = votes.get(color, 0.0) + float(p.intensity)
    return votes


def foveal_palette(
    image_data: bytes, center: Tuple[float, float] = (0.5, 0.5), count: int = 500
) -> List[Dict[str, Any]]:
    """Attention-weighted dominant colors via the foveated particle sampler.

    Uses the project's own VisualSampler (core/perception): 500 Gaussian
    particles around the fixation point, intensity-weighted color votes.
    Answers "how much looking": focused sensing instead of full scans —
    what the eye does, and what the old sampler was wired into judgments for.
    """
    img = _load_rgb(image_data, 96)
    if img is None:
        return []
    try:
        import numpy as _np
        from core.perception.visual_sampler import VisualSampler
    except Exception:
        return []
    try:
        sampler = VisualSampler()
        arr = _np.asarray(img).astype(float)
        votes = _sample_at(arr, sampler, center, 0.2, count)
        total = sum(votes.values()) or 1.0
        ranked = sorted(votes.items(), key=lambda kv: -kv[1])[:5]
        return [{"color": list(c), "weight": round(v / total, 3)} for c, v in ranked]
    except Exception as exc:
        logger.debug(f"Foveal palette failed: {exc}")
        return []


def aesthetics(image_data: bytes) -> Dict[str, Any]:
    """Deterministic aesthetic signals (no taste, just measurements).

    - colorfulness: saturation spread 0..1 (gray mud scores ~0).
    - balance: 1 - normalized centroid offset (centered mass scores high).
    - brightness: mean luminance 0..1 (too dark/bright flagged).
    - complexity: distinct-blob count capped (blank=1, photo≈hundreds).
    Each is a measurement, not a verdict; callers set their own bars.
    """
    img = _load_rgb(image_data, 64)
    if img is None:
        return {"colorfulness": 0.0, "balance": 0.0, "brightness": 0.0, "complexity": 1}
    import math as _math

    # get_flattened_data 對 RGB 回傳逐像素 (r,g,b) 元組（同 getdata），
    # 為 Pillow 14 (2027) 弃用後的替代 API
    px = list(img.get_flattened_data())
    n = max(len(px), 1)
    # Brightness (luminance mean).
    lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px]
    brightness = round(sum(lum) / (n * 255.0), 3)
    # Colorfulness: mean saturation distance from gray axis, normalized.
    sat = [max(abs(r - g), abs(g - b), abs(b - r)) for r, g, b in px]
    colorfulness = round(min(sum(sat) / (n * 255.0) * 2.0, 1.0), 3)
    # Balance: colorful-mass centroid offset from center (symmetry proxy).
    wsum = sum(sat) or 1.0
    w, h = img.size
    cx = sum(x * s for (x, _y), s in zip([(i % w, i // w) for i in range(n)], sat))
    cy = sum(y * s for (_x, y), s in zip([(i % w, i // w) for i in range(n)], sat))
    off = _math.hypot(cx / wsum / w - 0.5, cy / wsum / h - 0.5) * 2.0
    balance = round(max(0.0, 1.0 - min(off, 1.0)), 3)
    complexity = len(color_blobs(image_data))
    return {
        "colorfulness": colorfulness,
        "balance": balance,
        "brightness": brightness,
        "complexity": complexity,
    }


# Default visual field: fovea (dense detail) + mid (context) + periphery
# (gist). Different densities cover different areas with different detail
# control — composed, they are a visual field (2026-10-11).
DEFAULT_FIELD_SCALES = (
    {"center": (0.5, 0.5), "spread": 0.12, "count": 600, "name": "fovea"},
    {"center": (0.5, 0.5), "spread": 0.30, "count": 300, "name": "mid"},
    {"center": (0.5, 0.5), "spread": 0.60, "count": 100, "name": "periphery"},
)


def visual_field(
    image_data: bytes,
    scales: Optional[List[Dict[str, Any]]] = None,
    fixations: Optional[List[Tuple[float, float]]] = None,
) -> Dict[str, Any]:
    """Multi-scale foveated field: one sampler, several densities, one verdict.

    Each scale votes its own palette; fine scales resolve detail (small text,
    wheel spokes), coarse scales hold gist. Detail verdict: the smallest
    scale whose top colors diverge from the periphery sees structure the
    gist misses — that divergence IS the detail signal.
    fixations optionally recenters all scales (multi-fixation coverage).
    """
    img = _load_rgb(image_data, 96)
    if img is None:
        return {"scales": [], "detail": 0.0, "coverage": 0.0}
    try:
        import numpy as _np
        from core.perception.visual_sampler import VisualSampler
    except Exception:
        return {"scales": [], "detail": 0.0, "coverage": 0.0}
    try:
        sampler = VisualSampler()
        arr = _np.asarray(img).astype(float)
        h, w, _ = arr.shape
        centers = fixations or [(0.5, 0.5)]
        scale_defs = scales or list(DEFAULT_FIELD_SCALES)
        scale_out: List[Dict[str, Any]] = []
        for sdef in scale_defs:
            votes: Dict[Tuple[int, int, int], float] = {}
            for center in centers:
                part = _sample_at(
                    arr,
                    sampler,
                    center,
                    float(sdef.get("spread", 0.3)),
                    int(sdef.get("count", 300)),
                )
                for color, weight in part.items():
                    votes[color] = votes.get(color, 0.0) + weight
            total = sum(votes.values()) or 1.0
            ranked = sorted(votes.items(), key=lambda kv: -kv[1])[:4]
            scale_out.append(
                {
                    "name": str(sdef.get("name", "?")),
                    "spread": float(sdef.get("spread", 0.3)),
                    "palette": [
                        {"color": list(c), "weight": round(v / total, 3)} for c, v in ranked
                    ],
                }
            )

        # Detail: palette divergence of finest vs coarsest (L1/2 over the
        # union of top colors, weight-aware). Set-Jaccard was tried first —
        # too brittle: one stray peripheral particle flips the verdict.
        # 0 = same mush everywhere, →1 = fine structure the gist misses.
        detail = 0.0
        if len(scale_out) >= 2:
            fine = {tuple(p["color"]): p["weight"] for p in scale_out[0]["palette"]}
            coarse = {tuple(p["color"]): p["weight"] for p in scale_out[-1]["palette"]}
            union = set(fine) | set(coarse)
            l1 = sum(abs(fine.get(c, 0.0) - coarse.get(c, 0.0)) for c in union)
            detail = round(l1 / 2.0, 3)
        # Coverage: fraction of image area touched by any particle (approx by
        # widest spread's disc area, capped at 1).
        widest = max(float(s.get("spread", 0.3)) for s in scale_defs)
        import math as _math

        coverage = round(min(_math.pi * (widest**2) * len(centers), 1.0), 3)
        return {"scales": scale_out, "detail": detail, "coverage": coverage}
    except Exception as exc:
        logger.debug(f"Visual field failed: {exc}")
        return {"scales": [], "detail": 0.0, "coverage": 0.0}


def palette_match(
    image_data: bytes, spec: List[Tuple[str, Tuple[int, int, int]]]
) -> Dict[str, Any]:
    """Match dominant colors against a spec palette [(name, rgb)].

    Returns per-name best distance + overall score 0..1. Used to check a
    render against its art direction (car: red/white/black).
    """
    blobs = color_blobs(image_data)
    if not blobs:
        return {"score": 0.0, "matches": {}, "blobs": 0}
    per_name: Dict[str, float] = {}
    for name, rgb in spec:
        best = min((_color_distance(b["color"], rgb) for b in blobs[:8]), default=441.0)
        per_name[name] = round(best, 1)
    # Score: fraction of spec colors found within tolerance (96 ≈ clearly near).
    found = sum(1 for d in per_name.values() if d < 96.0)
    score = round(found / max(len(spec), 1), 3)
    return {"score": score, "matches": per_name, "blobs": len(blobs)}


def judge_render(
    image_data: bytes,
    spec: Optional[List[Tuple[str, Tuple[int, int, int]]]] = None,
    clip_concepts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Full verdict: blank check + palette + concepts → text + pass/fail."""
    blobs = color_blobs(image_data)
    if not blobs:
        return {"verdict": "無法解析圖像", "pass": False, "blobs": []}
    top = blobs[0]
    # Blank render: single blob covering ≥98% (live Unity gray case).
    if len(blobs) == 1 and top["fraction"] >= 0.98:
        return {
            "verdict": f"畫面近乎空白（單一色塊 top={top['color']} 佔100%），疑似渲染失敗或鏡頭沒對準物體。",
            "pass": False,
            "blobs": blobs,
            "blank": True,
        }
    lines = [f"檢出 {len(blobs)} 個色塊，最大 {top['color']} 佔{top['fraction']:.0%}."]
    try:
        _aes = aesthetics(image_data)
        lines.append(
            f"美學量測：鮮艷{_aes['colorfulness']:.2f}、均衡{_aes['balance']:.2f}、"
            f"亮度{_aes['brightness']:.2f}。"
        )
    except Exception:
        logger.debug("aesthetics enrichment failed", exc_info=True)
    try:
        _field = visual_field(image_data)
        if _field["scales"]:
            lines.append(
                f"視域：三尺度注視（fovea/mid/periphery）覆蓋{_field['coverage']:.0%}，"
                f"細節度{_field['detail']:.2f}。"
            )
    except Exception:
        logger.debug("visual_field enrichment failed", exc_info=True)
    if spec:
        pm = palette_match(image_data, spec)
        lines.append(
            f"調色盤吻合度 {pm['score']:.0%}（"
            + "、".join(f"{k}偏差{v}" for k, v in pm["matches"].items())
            + ")。"
        )
    else:
        pm = {"score": None}
    if clip_concepts:
        top_c = clip_concepts[0]
        lines.append(
            f"CLIP首判 {top_c.get('concept_name')}（{float(top_c.get('confidence', 0)):.2f}）。"
        )
    verdict = "".join(lines)
    passed = True
    if spec and (pm.get("score") or 0) < 0.5:
        passed = False
        verdict += "未達調色盤門檻，需調整材質。"
    return {"verdict": verdict, "pass": passed, "blobs": blobs[:5], "palette": pm}
