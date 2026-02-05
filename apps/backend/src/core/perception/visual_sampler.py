"""
Angela AI v6.0 - Visual Sampler
視覺採樣器

基於粒子雲與隨機分布的視覺採樣系統，模擬人類視覺的注意機制與精度變化。
Supports foveated sampling, particle cloud transformations, and attention-based precision.
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum, auto

logger = logging.getLogger(__name__)

class SamplingDistribution(Enum):
    UNIFORM = auto()
    GAUSSIAN = auto()  # Foveated / 中央凹採樣
    PARTICLE_CLOUD = auto()  # 粒子雲隨機採樣
    GRID = auto()

@dataclass
class SamplingParticle:
    """採樣粒子 / Sampling particle"""
    x: float
    y: float
    intensity: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class VisualSampler:
    """
    視覺採樣器 / Visual Sampler
    
    實現將採樣像素粒子雲化，並支持變形、縮放等行為。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.particles: List[SamplingParticle] = []
        self.current_focus: Tuple[float, float] = (0.5, 0.5)  # Normalized coordinates
        
    def generate_cloud(
        self, 
        count: int = 1000, 
        center: Tuple[float, float] = (0.5, 0.5),
        distribution: SamplingDistribution = SamplingDistribution.GAUSSIAN,
        spread: float = 0.2
    ) -> List[SamplingParticle]:
        """
        生成採樣粒子雲 / Generate a particle cloud
        """
        self.current_focus = center
        particles = []
        
        if distribution == SamplingDistribution.GAUSSIAN:
            # 高斯分布模擬人類視覺中央凹 (Fovea)
            xs = np.random.normal(center[0], spread, count)
            ys = np.random.normal(center[1], spread, count)
        elif distribution == SamplingDistribution.UNIFORM:
            xs = np.random.uniform(center[0] - spread, center[0] + spread, count)
            ys = np.random.uniform(center[1] - spread, center[1] + spread, count)
        else:
            # 默認粒子雲採樣
            xs = np.random.uniform(0, 1, count)
            ys = np.random.uniform(0, 1, count)
            
        # 裁剪到 [0, 1] 範圍
        xs = np.clip(xs, 0, 1)
        ys = np.clip(ys, 0, 1)
        
        for x, y in zip(xs, ys):
            # 計算距離中心的權重（模擬精度變化）
            dist = np.sqrt((x - center[0])**2 + (y - center[1])**2)
            intensity = np.exp(-dist / (spread * 2))
            particles.append(SamplingParticle(x=float(x), y=float(y), intensity=float(intensity)))
            
        self.particles = particles
        return particles

    def apply_transform(self, scale: float = 1.0, deformation: float = 0.0, rotation: float = 0.0):
        """
        對粒子雲應用變換 / Apply transformations to the particle cloud
        
        Args:
            scale: 縮放因子，影響注意範圍
            deformation: 變形因子，模擬視覺扭曲或動態聚焦
            rotation: 旋轉角度（弧度）
        """
        if not self.particles:
            return
            
        cx, cy = self.current_focus
        
        for p in self.particles:
            # 1. 縮放 (Relative to center)
            p.x = cx + (p.x - cx) * scale
            p.y = cy + (p.y - cy) * scale
            
            # 2. 變形 (Simple non-linear radial deformation)
            if deformation != 0:
                dx, dy = p.x - cx, p.y - cy
                r = np.sqrt(dx**2 + dy**2)
                factor = 1.0 + deformation * r
                p.x = cx + dx * factor
                p.y = cy + dy * factor
            
            # 3. 旋轉
            if rotation != 0:
                dx, dy = p.x - cx, p.y - cy
                new_dx = dx * np.cos(rotation) - dy * np.sin(rotation)
                new_dy = dx * np.sin(rotation) + dy * np.cos(rotation)
                p.x = cx + new_dx
                p.y = cy + new_dy
                
            # Keep in bounds
            p.x = max(0.0, min(1.0, p.x))
            p.y = max(0.0, min(1.0, p.y))

    def get_attention_stats(self) -> Dict[str, Any]:
        """
        獲取當前注意範圍與識別力統計
        """
        if not self.particles:
            return {"precision": 0, "range": 0}
            
        intensities = [p.intensity for p in self.particles]
        avg_precision = np.mean(intensities)
        
        # 估計範圍 (粒子分布的標準差)
        xs = [p.x for p in self.particles]
        ys = [p.y for p in self.particles]
        attention_range = (np.std(xs) + np.std(ys)) / 2
        
        return {
            "particle_count": len(self.particles),
            "average_precision": float(avg_precision),
            "attention_range": float(attention_range),
            "focus_point": self.current_focus
        }

    async def sample_image(self, image_data: np.ndarray) -> List[Dict[str, Any]]:
        """
        根據當前粒子雲對圖像進行採樣
        """
        h, w = image_data.shape[:2]
        samples = []
        
        for p in self.particles:
            px = int(p.x * (w - 1))
            py = int(p.y * (h - 1))
            color = image_data[py, px]
            samples.append({
                "pos": (p.x, p.y),
                "color": color.tolist() if hasattr(color, 'tolist') else color,
                "intensity": p.intensity
            })
            
        return samples
