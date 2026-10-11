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
from collections import Counter, deque
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

    Returns blobs sorted by size desc: {color, pixels, fraction, bbox}.
    A near-blank render yields exactly one background blob — the honest
    signal for "render produced nothing" (live 2026-10-11 Unity gray).
    """
    img = _load_rgb(image_data, max_side)
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
                x0, x1 = min(x0, cx), max(x0, cx)
                y0, y1 = min(y0, cy), max(y0, cy)
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
    blobs.sort(key=lambda b: -b["pixels"])
    return blobs


def _color_distance(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


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
