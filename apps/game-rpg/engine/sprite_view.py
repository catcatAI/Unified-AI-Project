# -*- coding: utf-8 -*-
"""萬物皆軸引擎 — M6 2D 表現：§5.2 精靈管線接 render_bridge（§6.3/§6.4）。

離屏幀合成（PIL）：`RenderBridge` 已像素吸附的座標 → `SpriteView.render()`
貼合成 RGB 幀。§5.2 `game_sprites.render_entity_sprite` 以 importlib+Any
動態載入（同 M5：engine 不靜態綁後端模組；缺路徑時 bootstrap
`apps/backend/src`——editable 安裝已有 .pth 時不觸發）。

本模組是**表現端**，不 import `engine/__init__` 核心以外的東西；PyQt6
視窗是 §6.4「pixel-angela ws 收快照」遠期接線，手動視覺冒煙走
``python -m engine.sprite_view --out <png>``（產生移動序列拼圖供眼看）。
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Tuple

from engine.quantize import quantize
from engine.render_bridge import EntityState, RenderBridge, RenderState
from PIL import Image

RGB = Tuple[int, int, int]
DEFAULT_BACKGROUND: RGB = (16, 16, 32)
DEFAULT_SPRITE_CODE = ("S-H-P", "物種")  # 物種/標準種|類人型|純血（§5.2 範例碼）


def _backend_src() -> Path:
    # apps/game-rpg/engine/sprite_view.py → parents[2]=apps
    return Path(__file__).resolve().parents[2] / "backend" / "src"


def _game_sprites() -> Any:
    """動態載入 §5.2 精靈管線（Any 綁定：不拖舊碼進 engine mypy 範圍）。"""
    try:
        return importlib.import_module("ai.multimodal.primitives.game_sprites")
    except ModuleNotFoundError:
        src = _backend_src()
        if not src.is_dir():
            raise ModuleNotFoundError(
                "game_sprites not importable and backend src missing: "
                f"{src} (install backend editable or add to sys.path)"
            ) from None
        sys.path.insert(0, str(src))
        return importlib.import_module("ai.multimodal.primitives.game_sprites")


def load_entity_sprite(
    axis_code: str = DEFAULT_SPRITE_CODE[0],
    group_profile: str = DEFAULT_SPRITE_CODE[1],
    size: int = 32,
) -> Image.Image:
    """§5.2 合成精靈（RGBA）；壞軸碼由 game_sprites.AxisCodeError 響亮 raise。"""
    mod = _game_sprites()
    sprite: Image.Image = mod.render_entity_sprite(axis_code, group_profile, size)
    return sprite


class SpriteView:
    """離屏幀合成器：單一精靈貼到各實體座標（sorted 疊放=確定性）。"""

    def __init__(
        self,
        width: int = 320,
        height: int = 180,
        background: RGB = DEFAULT_BACKGROUND,
        sprite: Optional[Image.Image] = None,
    ) -> None:
        if width < 1 or height < 1:
            raise ValueError(f"view size must be >= 1, got {width}x{height}")
        self.width = width
        self.height = height
        self.background = background
        self.sprite = sprite if sprite is not None else load_entity_sprite()

    def render(self, states: Mapping[str, RenderState]) -> Image.Image:
        """States → RGB 幀。座標防禦性吸附（M4 已 snap；雙保險，半遠離零）。"""
        frame = Image.new("RGB", (self.width, self.height), self.background)
        for eid in sorted(states):
            st = states[eid]
            x = int(quantize(st.x, 1.0))
            y = int(quantize(st.y, 1.0))
            frame.paste(self.sprite, (x, y), self.sprite)
        return frame

    def render_sample(self, bridge: RenderBridge, alpha: float) -> Image.Image:
        return self.render(bridge.sample(alpha))

    def render_at(self, bridge: RenderBridge, display_time: float) -> Image.Image:
        return self.render(bridge.sample_at(display_time))


# ---------------------------------------------------------------------------
# 手動視覺冒煙：移動序列拼圖（眼看漸變間距均勻、無跳格/抖動）
# ---------------------------------------------------------------------------
def motion_sheet(
    view: Optional[SpriteView] = None,
    frames: int = 24,
    columns: int = 6,
    velocity: float = 240.0,
    sim_hz: float = 30.0,
    display_hz: float = 144.0,
) -> Image.Image:
    """30Hz 模擬 / 144Hz 顯示逐幀渲染，橫向拼圖（每列 columns 幀）。"""
    if view is None:
        view = SpriteView(width=240, height=96)
    bridge = RenderBridge(pixel_size=1.0)
    images = []
    k = -1
    for m in range(frames):
        t = m / display_hz
        while k < 0 or bridge.curr_time < t:
            k += 1
            sim_t = k / sim_hz
            bridge.push(
                {"hero": EntityState("hero", 8.0 + velocity * sim_t, 32.0)},
                sim_time=sim_t,
            )
        images.append(view.render_at(bridge, t))
    cols = max(1, columns)
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * view.width, rows * view.height), view.background)
    for i, img in enumerate(images):
        sheet.paste(img, ((i % cols) * view.width, (i // cols) * view.height))
    return sheet


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="M6 手動視覺冒煙：移動序列拼圖")
    parser.add_argument("--out", default="/tmp/engine_m6_smoke.png")
    parser.add_argument("--frames", type=int, default=24)
    args = parser.parse_args(list(argv) if argv is not None else None)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet = motion_sheet(frames=args.frames)
    sheet.save(out)
    print(f"saved {out} ({sheet.width}x{sheet.height})")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
