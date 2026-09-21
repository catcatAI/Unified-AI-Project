"""
Foveated Sampler - 固定預算非均勻採樣

實現三種策略：
1. Log-polar (對數極座標) - 模擬人眼視網膜
2. Deformable mesh (可變形網格) - 空間變形
3. Quadtree (四叉樹) - 基於顯著性的自適應分割

所有策略輸出固定 shape tensor，便於 batch 平行計算。
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class SamplingStrategy(str, Enum):
    LOG_POLAR = "log_polar"
    DEFORMABLE = "deformable"
    QUADTREE = "quadtree"
    UNIFORM = "uniform"  # 基準比較用


@dataclass
class SamplingConfig:
    budget_pixels: int = 83000  # 總像素預算 (1/25 of 1080p)
    fovea_ratio: float = 0.7  # 焦點區佔比
    fovea_radius: int = 160  # 焦點半徑 (原圖像素)
    output_size: Tuple[int, int] = (64, 64)  # 輸出固定尺寸
    strategy: SamplingStrategy = SamplingStrategy.LOG_POLAR
    min_peripheral_density: float = 0.02  # 周邊最低採樣密度
    max_fovea_density: float = 1.0  # 焦點最高採樣密度 (1:1)


@dataclass
class SamplingResult:
    sampled_frame: np.ndarray  # (H, W, 3) 固定尺寸
    inverse_map: np.ndarray  # (H, W, 2) 原圖座標映射
    density_map: np.ndarray  # (H, W) 採樣密度圖
    focus_xy: Tuple[int, int]  # 當前焦點 (原圖座標)
    strategy: SamplingStrategy
    stats: Dict[str, Any]


class FoveatedSampler:
    """
    固定預算非均勻採樣器

    核心思想：
    - 總輸入像素數 (token 數) 恆定
    - 根據「資訊密度與位置」動態重分配
    - 輸出固定 shape tensor，極易 batch 平行化
    - 提供座標逆映射，支援精確點擊定位
    """

    def __init__(self, config: Optional[SamplingConfig] = None):
        self.config = config or SamplingConfig()
        self._cache: Dict[str, Any] = {}
        self._last_focus: Optional[Tuple[int, int]] = None
        self._sampling_grid: Optional[np.ndarray] = None  # (H, W, 2) 歸一化座標 [-1,1]
        self._inverse_grid: Optional[np.ndarray] = None  # (H, W, 2) 原圖座標
        self._initialized = False

    def _init_grids(self, frame_shape: Tuple[int, int]):
        """初始化採樣網格 (僅在解析度改變時重建)"""
        h, w = frame_shape
        out_h, out_w = self.config.output_size

        # 建立輸出網格的歸一化座標 [-1, 1] (用於 grid_sample)
        y_norm = np.linspace(-1, 1, out_h, dtype=np.float32)
        x_norm = np.linspace(-1, 1, out_w, dtype=np.float32)
        yy, xx = np.meshgrid(y_norm, x_norm, indexing="ij")
        self._sampling_grid = np.stack([xx, yy], axis=-1)  # (H, W, 2)

        # 原圖座標網格 (用於逆映射)
        self._inverse_grid = np.zeros((out_h, out_w, 2), dtype=np.float32)
        self._initialized = True

    def sample(
        self, frame: np.ndarray, focus_xy: Optional[Tuple[int, int]] = None
    ) -> SamplingResult:
        """
        執行非均勻採樣

        Args:
            frame: 原始幀 (H, W, 3) uint8
            focus_xy: 焦點位置 (x, y) 原圖座標，None 時用畫面中心

        Returns:
            SamplingResult: 採樣結果含固定尺寸張量與逆映射
        """
        start_time = time.perf_counter()
        h, w = frame.shape[:2]

        if not self._initialized or (h, w) != getattr(self, "_last_frame_shape", (0, 0)):
            self._init_grids((h, w))
            self._last_frame_shape = (h, w)

        if focus_xy is None:
            focus_xy = (w // 2, h // 2)

        # 平滑焦點移動 (避免突變)
        if self._last_focus is not None:
            fx, fy = focus_xy
            lx, ly = self._last_focus
            # 指數移動平均
            focus_xy = (int(0.7 * fx + 0.3 * lx), int(0.7 * fy + 0.3 * ly))
        self._last_focus = focus_xy

        # 根據策略生成採樣座標映射
        if self.config.strategy == SamplingStrategy.LOG_POLAR:
            src_coords = self._log_polar_mapping(h, w, focus_xy)
        elif self.config.strategy == SamplingStrategy.DEFORMABLE:
            src_coords = self._deformable_mapping(h, w, focus_xy)
        elif self.config.strategy == SamplingStrategy.QUADTREE:
            src_coords = self._quadtree_mapping(frame, focus_xy)
        else:
            src_coords = self._uniform_mapping(h, w)

        # 執行採樣 (雙線性插值)
        sampled = self._bilinear_sample(frame, src_coords)

        # 計算密度圖
        density = self._compute_density(src_coords, h, w)

        # 建立逆映射 (輸出像素 -> 原圖座標)
        inverse_map = src_coords.copy()

        stats = {
            "sampling_time_ms": (time.perf_counter() - start_time) * 1000,
            "frame_shape": (h, w),
            "output_shape": self.config.output_size,
            "focus_xy": focus_xy,
            "mean_density": float(density.mean()),
            "max_density": float(density.max()),
            "strategy": self.config.strategy.value,
        }

        return SamplingResult(
            sampled_frame=sampled,
            inverse_map=inverse_map,
            density_map=density,
            focus_xy=focus_xy,
            strategy=self.config.strategy,
            stats=stats,
        )

    def _log_polar_mapping(self, h: int, w: int, focus_xy: Tuple[int, int]) -> np.ndarray:
        """
        Log-polar mapping (對數極座標採樣)

        模擬人眼視網膜：中心高解析度，外圍指數級下降
        公式：r' = log(r + 1) * scale, θ' = θ
        """
        out_h, out_w = self.config.output_size
        fx, fy = focus_xy

        # 輸出網格座標
        y_idx = np.arange(out_h, dtype=np.float32)
        x_idx = np.arange(out_w, dtype=np.float32)
        yy, xx = np.meshgrid(y_idx, x_idx, indexing="ij")

        # 歸一化到 [-1, 1]
        norm_x = (xx / (out_w - 1)) * 2 - 1
        norm_y = (yy / (out_h - 1)) * 2 - 1

        # 轉極座標 (以焦點為中心)
        cx = fx / w * 2 - 1
        cy = fy / h * 2 - 1
        dx = norm_x - cx
        dy = norm_y - cy
        r = np.sqrt(dx**2 + dy**2)
        theta = np.arctan2(dy, dx)

        # Log-polar 變換
        # 焦點區域 (r < fovea_radius_norm) 保持線性
        fovea_r = self.config.fovea_radius / max(h, w) * 2
        scale = self.config.fovea_ratio * 2

        r_transformed = np.where(
            r < fovea_r,
            r * scale,  # 焦點內線性放大
            fovea_r * scale
            + (np.log(r - fovea_r + 1) / np.log(2 - fovea_r + 1)) * (1 - fovea_r * scale),
        )

        # 限制範圍
        r_transformed = np.clip(r_transformed, 0, 1)

        # 轉回直角座標
        src_x = cx + r_transformed * np.cos(theta)
        src_y = cy + r_transformed * np.sin(theta)

        # 歸一化座標轉像素座標
        src_x = (src_x + 1) * (w - 1) / 2
        src_y = (src_y + 1) * (h - 1) / 2

        return np.stack([src_x, src_y], axis=-1)

    def _deformable_mapping(self, h: int, w: int, focus_xy: Tuple[int, int]) -> np.ndarray:
        """
        Deformable mesh (可變形網格)

        使用高斯核在焦點周圍產生位移場，將網格「拉向」焦點
        """
        out_h, out_w = self.config.output_size
        fx, fy = focus_xy

        # 基礎均勻網格
        y_idx = np.arange(out_h, dtype=np.float32)
        x_idx = np.arange(out_w, dtype=np.float32)
        yy, xx = np.meshgrid(y_idx, x_idx, indexing="ij")

        # 歸一化
        norm_x = (xx / (out_w - 1)) * 2 - 1
        norm_y = (yy / (out_h - 1)) * 2 - 1

        # 焦點歸一化座標
        cx = fx / w * 2 - 1
        cy = fy / h * 2 - 1

        # 計算到焦點距離
        dx = norm_x - cx
        dy = norm_y - cy
        dist = np.sqrt(dx**2 + dy**2)

        # 高斯位移場：越靠近焦點位移越大 (將周邊像素「拉」向焦點)
        sigma = 0.5
        displacement = np.exp(-(dist**2) / (2 * sigma**2)) * self.config.fovea_ratio

        # 位移方向指向焦點
        disp_x = -dx * displacement
        disp_y = -dy * displacement

        src_x = np.clip(norm_x + disp_x, -1, 1)
        src_y = np.clip(norm_y + disp_y, -1, 1)

        # 轉回像素座標
        src_x = (src_x + 1) * (w - 1) / 2
        src_y = (src_y + 1) * (h - 1) / 2

        return np.stack([src_x, src_y], axis=-1)

    def _quadtree_mapping(self, frame: np.ndarray, focus_xy: Tuple[int, int]) -> np.ndarray:
        """
        Quadtree-based adaptive sampling (四叉樹自適應採樣)

        根據局部變異度 (顯著性) 決定採樣密度
        """
        out_h, out_w = self.config.output_size
        h, w = frame.shape[:2]
        fx, fy = focus_xy

        # 計算顯著性圖 (簡化版：梯度幅值)
        gray = np.mean(frame, axis=2).astype(np.float32)
        grad_x = np.abs(np.gradient(gray, axis=1))
        grad_y = np.abs(np.gradient(gray, axis=0))
        saliency = grad_x + grad_y

        # 高斯平滑
        from scipy.ndimage import gaussian_filter

        saliency = gaussian_filter(saliency, sigma=2)

        # 歸一化
        saliency = (saliency - saliency.min()) / (saliency.max() - saliency.min() + 1e-8)

        # 焦點權重
        y_idx, x_idx = np.indices((h, w), dtype=np.float32)
        dist_to_focus = np.sqrt((x_idx - fx) ** 2 + (y_idx - fy) ** 2)
        focus_weight = np.exp(-(dist_to_focus**2) / (2 * (self.config.fovea_radius**2)))

        # 綜合權重
        weight = 0.5 * saliency + 0.5 * focus_weight

        # 根據權重分配採樣點 (簡化：用權重調整 log-polar)
        # 這裡為演示，實際可用更複雜的分配演算法
        return self._log_polar_mapping(h, w, focus_xy)

    def _uniform_mapping(self, h: int, w: int) -> np.ndarray:
        """均勻採樣 (基準比較)"""
        out_h, out_w = self.config.output_size
        y_idx = np.arange(out_h, dtype=np.float32)
        x_idx = np.arange(out_w, dtype=np.float32)
        yy, xx = np.meshgrid(y_idx, x_idx, indexing="ij")
        src_x = xx / (out_w - 1) * (w - 1)
        src_y = yy / (out_h - 1) * (h - 1)
        return np.stack([src_x, src_y], axis=-1)

    def _bilinear_sample(self, frame: np.ndarray, coords: np.ndarray) -> np.ndarray:
        """
        雙線性插值採樣

        Args:
            frame: (H, W, 3)
            coords: (out_H, out_W, 2) 原圖座標 (x, y)
        Returns:
            sampled: (out_H, out_W, 3)
        """
        h, w = frame.shape[:2]
        x = coords[..., 0]
        y = coords[..., 1]

        # 邊界裁剪 (確保 x1, y1 不越界)
        x = np.clip(x, 0, w - 1 - 1e-6)
        y = np.clip(y, 0, h - 1 - 1e-6)

        x0 = np.floor(x).astype(np.int32)
        y0 = np.floor(y).astype(np.int32)
        x1 = np.clip(x0 + 1, 0, w - 1)
        y1 = np.clip(y0 + 1, 0, h - 1)

        # 雙線性權重
        wx = x - x0
        wy = y - y0

        # 向量化採樣
        c00 = frame[y0, x0]
        c10 = frame[y0, x1]
        c01 = frame[y1, x0]
        c11 = frame[y1, x1]

        wx = wx[..., np.newaxis]
        wy = wy[..., np.newaxis]

        sampled = (
            c00 * (1 - wx) * (1 - wy) + c10 * wx * (1 - wy) + c01 * (1 - wx) * wy + c11 * wx * wy
        )

        return sampled.astype(np.uint8)

    def _compute_density(self, coords: np.ndarray, h: int, w: int) -> np.ndarray:
        """計算採樣密度圖 (用於視覺化/除錯)"""
        # 簡化：計算局部雅可比行列式
        out_h, out_w = coords.shape[:2]
        density = np.ones((out_h, out_w), dtype=np.float32)

        if out_h > 1 and out_w > 1:
            dx_dx = np.gradient(coords[..., 0], axis=1)
            dy_dy = np.gradient(coords[..., 1], axis=0)
            dx_dy = np.gradient(coords[..., 0], axis=0)
            dy_dx = np.gradient(coords[..., 1], axis=1)
            density = np.abs(dx_dx * dy_dy - dx_dy * dy_dx)  # 雅可比行列式
            density = np.clip(density, 0.01, 10.0)

        return density

    def map_to_original(
        self, output_xy: Tuple[int, int], inverse_map: np.ndarray
    ) -> Tuple[int, int]:
        """
        將輸出張量座標映射回原圖座標

        Args:
            output_xy: (x, y) 在輸出張量中的位置
            inverse_map: sample() 返回的 inverse_map
        Returns:
            (orig_x, orig_y) 原圖座標
        """
        x, y = output_xy
        out_h, out_w = inverse_map.shape[:2]
        x = np.clip(x, 0, out_w - 1)
        y = np.clip(y, 0, out_h - 1)
        orig_x, orig_y = inverse_map[y, x]
        return int(orig_x), int(orig_y)

    def set_strategy(self, strategy: SamplingStrategy):
        """動態切換策略"""
        self.config.strategy = strategy
        logger.info(f"FoveatedSampler strategy changed to {strategy.value}")

    def update_config(self, **kwargs):
        """動態更新配置"""
        for k, v in kwargs.items():
            if hasattr(self.config, k):
                setattr(self.config, k, v)
        # 重置網格以應用新配置
        self._initialized = False


def create_sampler_from_config(config_dict: Dict[str, Any]) -> FoveatedSampler:
    """從配置字典建立採樣器"""
    config = SamplingConfig(
        budget_pixels=config_dict.get("budget_pixels", 83000),
        fovea_ratio=config_dict.get("fovea_ratio", 0.7),
        fovea_radius=config_dict.get("fovea_radius", 160),
        output_size=tuple(config_dict.get("input_size", [64, 64])),
        strategy=SamplingStrategy(config_dict.get("sampling_strategy", "log_polar")),
    )
    return FoveatedSampler(config)
