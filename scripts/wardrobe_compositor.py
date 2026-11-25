#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [A] [L3]
# =============================================================================
"""
Wardrobe Layer Compositor (分層紙娃娃換裝合成器) for Angela AI.

Architecture:
- Base Mannequin Layer: Angela in a minimalist, form-fitting swimsuit/innerwear
  (no bulky sleeves, no skirts, bare limbs), 100% transparent alpha background.
- Clothing Overlay Layers: Full-resolution raster PNG garments (tops, bottoms,
  outerwear, shoes, accessories) with clean alpha transparency, scaled and
  anchored to the canonical mannequin coordinates (768x1376 canvas).
- Compositing Engine: Precise alpha-blending ensuring that base innerwear is
  strictly covered by clothing overlays without clipping, fringe, or poke-through.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
WARDROBE_DIR = ROOT / "resources" / "wardrobe"
CANONICAL_SIZE = (768, 1376)


class WardrobeCompositor:
    """Composites layered clothing assets onto the Angela base mannequin."""

    def __init__(self, base_mannequin_path: Optional[Path] = None):
        self.base_path = base_mannequin_path or (WARDROBE_DIR / "base_mannequin.png")
        if not self.base_path.is_file():
            raise FileNotFoundError(f"Base mannequin missing at {self.base_path}")
        self.base_img = Image.open(self.base_path).convert("RGBA")
        if self.base_img.size != CANONICAL_SIZE:
            self.base_img = self.base_img.resize(CANONICAL_SIZE, Image.Resampling.LANCZOS)

    def extract_clean_alpha(
        self,
        image_path: Path,
        bg_threshold: int = 240,
        feather_radius: int = 1,
    ) -> Image.Image:
        """Removes solid background and extracts smooth, anti-aliased RGBA cutout."""
        img = Image.open(image_path).convert("RGBA")
        if img.size != CANONICAL_SIZE:
            img = img.resize(CANONICAL_SIZE, Image.Resampling.LANCZOS)

        arr = np.array(img)
        h, w, _ = arr.shape

        # Identify border-connected near-white background pixels
        from collections import deque

        visited = np.zeros((h, w), dtype=bool)
        is_bg = np.zeros((h, w), dtype=bool)
        q = deque()

        for y in range(h):
            for x in [0, w - 1]:
                if np.all(arr[y, x, :3] >= bg_threshold):
                    q.append((y, x))
                    visited[y, x] = True
                    is_bg[y, x] = True

        for x in range(w):
            for y in [0, h - 1]:
                if not visited[y, x] and np.all(arr[y, x, :3] >= bg_threshold):
                    q.append((y, x))
                    visited[y, x] = True
                    is_bg[y, x] = True

        while q:
            y, x = q.popleft()
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                    visited[ny, nx] = True
                    if np.all(arr[ny, nx, :3] >= bg_threshold):
                        is_bg[ny, nx] = True
                        q.append((ny, nx))

        arr[is_bg, 3] = 0

        # Anti-aliased feathering on boundary
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if not is_bg[y, x] and arr[y, x, 3] == 255:
                    if is_bg[y - 1, x] or is_bg[y + 1, x] or is_bg[y, x - 1] or is_bg[y, x + 1]:
                        brightness = float(np.mean(arr[y, x, :3]))
                        if brightness > 220:
                            alpha = int(255 * (1.0 - (brightness - 220) / 35.0))
                            arr[y, x, 3] = max(0, min(255, alpha))

        return Image.fromarray(arr)

    def composite_layers(
        self,
        layers: List[Image.Image],
        output_path: Optional[Path] = None,
    ) -> Image.Image:
        """Sequentially overlay clothing layers onto the base mannequin.

        Layer order:
        0: Base Mannequin (swimsuit/innerwear)
        1..N: Clothing overlays (bottom -> top -> outer -> accessories)
        """
        canvas = self.base_img.copy()
        for layer in layers:
            if layer.size != CANONICAL_SIZE:
                layer = layer.resize(CANONICAL_SIZE, Image.Resampling.LANCZOS)
            canvas = Image.alpha_composite(canvas, layer)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            canvas.save(output_path, "PNG")
            logger.info("Composited standing sprite saved to %s", output_path)

        return canvas


def main():
    parser = argparse.ArgumentParser(description="Angela Wardrobe Layer Compositor")
    parser.add_argument("--base", type=str, help="Path to base mannequin sprite")
    parser.add_argument(
        "--layer", type=str, action="append", help="Paths to clothing overlay layers"
    )
    parser.add_argument(
        "--out", type=str, default="resources/wardrobe/composite_preview.png", help="Output path"
    )
    args = parser.parse_args()

    base_path = Path(args.base) if args.base else None
    compositor = WardrobeCompositor(base_path)

    layers = []
    if args.layer:
        for l_path in args.layer:
            layers.append(Image.open(l_path).convert("RGBA"))

    out_path = Path(args.out)
    result = compositor.composite_layers(layers, out_path)
    print(
        f"Successfully composited {len(layers)} clothing layers onto base mannequin -> {out_path}"
    )


if __name__ == "__main__":
    main()
