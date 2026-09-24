"""
Game Vision - 可切換的多層級視覺識別

兩路視覺源（按任務切換）：
  GAME_WINDOW: Luanti 遊戲窗口 —— 看世界（認樹/水/地形，定位挖走）
  SCREEN:      整個桌面 —— 看系統（瀏覽器/檔案/OS 操作，v1 只識別不操作）

每路內部分層（固定像素預算）：
  全局稀疏層：整幀低密度，抓版面/動態；
  焦點稠密層：FoveatedSampler 按 focus/quadtree 顯著性重分配。
兩層由同一 sampler 一次完成（輸出固定張量），此處只管源切換與接線。

識別 = sampler -> encoder -> policy grounding -> 逆映射回源像素 ->
  GAME_WINDOW: NDC -> poller 相機射線 -> 世界 XYZ（再進 look_at/dig_at）
  SCREEN:      NDC -> 屏幕點擊座標（桌面身體待接，只識別）

截圖用 OS 級 pyautogui（跟遊戲同機，40FPS 實測），不走 CSM/協議。
"""

import logging
import re
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class VisionSource(str, Enum):
    GAME_WINDOW = "game_window"
    SCREEN = "screen"


@dataclass
class VisionLevel:
    """單路內的一層：採樣策略＋輸出尺寸（token 預算）"""

    strategy: str = "quadtree"  # log_polar | deformable | quadtree | uniform
    output_size: Tuple[int, int] = (64, 64)


@dataclass
class VisionConfig:
    game_titles: Tuple[str, ...] = ("luanti", "minetest")
    screenshot_backend: str = "pyautogui"
    game_levels: VisionLevel = field(default_factory=VisionLevel)
    screen_levels: VisionLevel = field(default_factory=VisionLevel)
    switch_cooldown_sec: float = 5.0


@dataclass
class VisionFrame:
    source: VisionSource
    image: Any  # PIL Image, 源像素空間
    rect: Tuple[int, int, int, int]  # (x, y, w, h) 屏幕座標
    timestamp: float


@dataclass
class VisionRecognition:
    source: VisionSource
    features: np.ndarray  # encoder 特徵向量
    heatmap: np.ndarray  # policy grounding 熱力（採樣張量空間）
    inverse_map: np.ndarray  # 採樣像素 -> 源像素
    focus_xy: Tuple[int, int]
    stats: Dict[str, Any]


def _wmctrl_list() -> List[Dict[str, Any]]:
    """列出 X11 窗口（id, x, y, w, h, title）。"""
    try:
        out = subprocess.run(["wmctrl", "-lG"], capture_output=True, text=True, timeout=5).stdout
    except Exception as e:
        logger.debug(f"wmctrl failed: {e}")
        return []
    wins = []
    for line in out.splitlines():
        parts = line.split(None, 7)
        if len(parts) < 8:
            continue
        try:
            wins.append(
                {
                    "id": parts[0],
                    "x": int(parts[2]),
                    "y": int(parts[3]),
                    "w": int(parts[4]),
                    "h": int(parts[5]),
                    "title": parts[7],
                }
            )
        except (ValueError, IndexError):
            continue
    return wins


class GameVision:
    """雙源視覺：捕獲＋切換＋識別（sampler/encoder/policy 復用專案現貨）"""

    def __init__(self, config: Optional[VisionConfig] = None):
        self.config = config or VisionConfig()
        self.active_source: VisionSource = VisionSource.GAME_WINDOW
        self._last_switch: float = 0.0
        self._rect_cache: Optional[Tuple[int, int, int, int]] = None
        self._rect_ts: float = 0.0
        self._sampler: Optional[Any] = None
        self._encoder: Optional[Any] = None
        self._policy: Optional[Any] = None

    # ---------- 源定位與捕獲 ----------

    def locate_game_window(self) -> Optional[Tuple[int, int, int, int]]:
        """找 Luanti 遊戲窗口，返回屏幕幾何 (x, y, w, h)。30s 緩存。"""
        now = time.time()
        if self._rect_cache and now - self._rect_ts < 30:
            return self._rect_cache
        titles = [t.lower() for t in self.config.game_titles]
        cands = [w for w in _wmctrl_list() if any(t in w["title"].lower() for t in titles)]
        if not cands:
            self._rect_cache = None
            return None
        best = max(cands, key=lambda w: w["w"] * w["h"])
        self._rect_cache = (best["x"], best["y"], best["w"], best["h"])
        self._rect_ts = now
        return self._rect_cache

    def capture(self, source: Optional[VisionSource] = None) -> Optional[VisionFrame]:
        """截一幀。GAME_WINDOW 找不到窗口時返回 None（上游切 SCREEN）。"""
        from PIL import Image

        src = source or self.active_source
        try:
            import pyautogui

            if src == VisionSource.GAME_WINDOW:
                rect = self.locate_game_window()
                if not rect:
                    return None
                x, y, w, h = rect
                img = pyautogui.screenshot(region=(x, y, w, h))
            else:
                img = pyautogui.screenshot()
                w, h = img.size
                x, y = 0, 0
            if not isinstance(img, Image.Image):
                img = Image.fromarray(np.asarray(img))
            return VisionFrame(source=src, image=img, rect=(x, y, w, h), timestamp=time.time())
        except Exception as e:
            logger.debug(f"Capture failed ({src}): {e}")
            return None

    # ---------- 切換 ----------

    def select_source(self, want: Optional[VisionSource] = None) -> VisionSource:
        """切換視覺源（冷卻防抖）。want 為空=自動：有遊戲窗就遊戲，否則整屏。"""
        now = time.time()
        if now - self._last_switch < self.config.switch_cooldown_sec:
            return self.active_source
        if want is not None:
            target = want
        else:
            target = VisionSource.GAME_WINDOW if self.locate_game_window() else VisionSource.SCREEN
        if target != self.active_source:
            logger.info(f"Vision source -> {target.value}")
            self.active_source = target
            self._last_switch = now
        return self.active_source

    # ---------- 識別 ----------

    def _ensure_stack(self):
        """懶加載專案現貨：sampler + encoder + policy。"""
        if self._sampler is not None:
            return
        from ai.multimodal.foveated_sampler import (
            FoveatedSampler,
            SamplingConfig,
            SamplingStrategy,
        )
        from ai.multimodal.game_policy import GamePolicy, PolicyConfig
        from ai.multimodal.visual_encoder import VisualEncoder

        self._sampler = FoveatedSampler(
            SamplingConfig(
                budget_pixels=83000,
                fovea_ratio=0.7,
                output_size=(64, 64),
                strategy=SamplingStrategy.QUADTREE,
            )
        )
        self._encoder = VisualEncoder()
        self._policy = GamePolicy(PolicyConfig())
        logger.info("Vision stack ready (sampler+encoder+policy)")

    def recognize(
        self, frame: VisionFrame, focus_xy: Optional[Tuple[int, int]] = None
    ) -> Optional[VisionRecognition]:
        """一幀走完：採樣 -> 編碼 -> policy grounding。無 LLM，全 numpy 快迴圈。"""
        try:
            self._ensure_stack()
            sampler = self._sampler
            encoder = self._encoder
            policy = self._policy
            if sampler is None or encoder is None or policy is None:
                return None
            arr = np.asarray(frame.image.convert("RGB"), dtype=np.uint8)
            sampled = sampler.sample(arr, focus_xy=focus_xy)
            feats = encoder.encode_from_pil(frame.image)
            feats = np.asarray(feats, dtype=np.float32)
            latent = (
                feats[:128]
                if feats.shape[0] >= 128
                else np.pad(feats, (0, max(0, 128 - feats.shape[0])))
            )
            proprio = np.zeros(32, dtype=np.float32)
            out = policy.forward(latent.astype(np.float32), proprio)
            return VisionRecognition(
                source=frame.source,
                features=feats,
                heatmap=np.asarray(out.grounding_heatmap),
                inverse_map=np.asarray(sampled.inverse_map),
                focus_xy=sampled.focus_xy,
                stats={
                    **sampled.stats,
                    "policy_mode": str(out.mode),
                    "policy_confidence": float(out.confidence),
                },
            )
        except Exception as e:
            logger.warning(f"Recognize failed: {e}")
            return None

    # ---------- 座標落地 ----------

    @staticmethod
    def heatmap_peak_nDC(heatmap: np.ndarray) -> Tuple[float, float, float]:
        """熱力峰值 -> 源歸一化座標 (nx, ny 0..1)＋峰值強度。"""
        hm = np.asarray(heatmap, dtype=np.float32)
        idx = int(np.argmax(hm))
        yy, xx = np.unravel_index(idx, hm.shape[:2])
        h, w = hm.shape[:2]
        peak = float(hm[yy, xx])
        return (xx + 0.5) / max(w, 1), (yy + 0.5) / max(h, 1), peak

    @staticmethod
    def sampled_to_source(
        inverse_map: np.ndarray, sx: float, sy: float, src_w: int, src_h: int
    ) -> Tuple[float, float]:
        """採樣張量歸一化座標 -> 源歸一化座標（經逆映射＋源尺寸）。"""
        inv = np.asarray(inverse_map)
        h, w = inv.shape[:2]
        ix = min(w - 1, max(0, int(sx * w)))
        iy = min(h - 1, max(0, int(sy * h)))
        ox, oy = float(inv[iy, ix][0]), float(inv[iy, ix][1])
        return ox / max(src_w, 1), oy / max(src_h, 1)
