import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
logger = logging.getLogger(__name__)

class AudioFeatureType(Enum):
    VOICEPRINT = auto()  # 聲紋特徵 (User/Speaker ID)
    EMOTION = auto()     # 情感特徵
    ENVIRONMENT = auto() # 環境音 (背景雜訊)
    SPEECH = auto()      # 語義內容
    UNKNOWN = auto()

@dataclass
class AudioParticle:
    """音頻採樣粒子，代表音頻流中的一個特徵片段"""
    timestamp: float
    frequency_range: Tuple[float, float]
    intensity: float
    feature_vector: np.ndarray = field(default_factory=lambda: np.zeros(128))
    source_type: AudioFeatureType = AudioFeatureType.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)

class AuditorySampler:
    """聽覺採樣器：模擬人類聽覺的採樣與特徵提取過程"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.sample_rate = self.config.get('sample_rate', 16000)
        self.particles: List[AudioParticle] = []
        
    def sample_audio_stream(self, audio_data: bytes, duration: float = 1.0) -> List[AudioParticle]:
        """將原始音頻流採樣為一系列音頻粒子 (Audio Particles)"""
        # 模擬特徵提取過程 (實際實現應使用 MFCC, Mel-Spectrogram 或 AST/HuBERT 模型)
        # 這裡我們模擬在混亂場景中提取多個聲音來源的特徵
        count = self.config.get('particle_count', 10)
        new_particles = []
        
        for i in range(count):
            # 隨機模擬不同的聲源
            timestamp = i * (duration / count)
            freq_range = (random.uniform(20, 5000), random.uniform(5000, 20000))
            intensity = random.uniform(0.1, 1.0)
            
            # 模擬 128 維的聲紋特徵向量
            feature_vector = np.random.normal(0, 1, 128)
            
            particle = AudioParticle(
                timestamp=timestamp,
                frequency_range=freq_range,
                intensity=intensity,
                feature_vector=feature_vector,
                source_type=self._estimate_source_type(feature_vector)
            )
            new_particles.append(particle)
            
        self.particles = new_particles
        return new_particles

    def _estimate_source_type(self, feature_vector: np.ndarray) -> AudioFeatureType:
        """初步估計聲音來源類型 (模擬)"""
        # 在實際情況下，這會由一個輕量級分類器完成
        val = np.mean(feature_vector)
        if val > 0.1: return AudioFeatureType.SPEECH
        if val < -0.1: return AudioFeatureType.ENVIRONMENT
        return AudioFeatureType.VOICEPRINT

    def get_focus_stats(self) -> Dict[str, Any]:
        """獲取當前聽覺場景的統計數據"""
        if not self.particles:
            return {"status": "idle"}
            
        avg_intensity = np.mean([p.intensity for p in self.particles])
        source_counts = {}
        for p in self.particles:
            source_counts[p.source_type.name] = source_counts.get(p.source_type.name, 0) + 1
            
        return {
            "status": "active",
            "average_intensity": float(avg_intensity),
            "source_distribution": source_counts,
            "particle_count": len(self.particles)
        }

import random # Added for internal mock logic
