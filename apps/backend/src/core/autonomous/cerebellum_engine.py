import logging
import math
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CerebellumEngine:
    """
    Angela 的小腦運動神經系統 (ASI Cerebellum v1.0).
    負責運動協調、姿勢學習與平衡校正。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CerebellumEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self._initialized = True
        
        # 1. 脊椎運動矩陣 (Spine Control Matrix)
        # 代表 9 段脊椎的當前扭轉角度 (Theta)
        self.spine_state = np.zeros(9)
        
        # 2. 運動學習記憶 (Motor Memory)
        self.kinetic_history = []
        self.error_accumulation = 0.0
        
        # 3. 仿生參數 (來自 N.12 遺產)
        self.flexibility = 0.8 # 靈韌度
        self.damping = 0.15     # 動作阻尼

        logger.info("🧠 [Cerebellum] Motor Neural Engine initialized.")

    def calculate_posture(self, target_x: float, current_x: float, bio_state: Dict[str, Any]) -> Dict[str, float]:
        """
        [N.16.1] 核心演算法：根據目標位移計算 2.5D 姿勢補償。
        """
        dx = target_x - current_x
        stress = bio_state.get("stress_level", 0.0)
        
        # 姿勢預測模型：
        # 當位移 dx 為正時 (向右)，脊椎應向右產生微小的拋物線彎曲
        bend_factor = math.tanh(dx / 100.0) * self.flexibility
        
        # 疲勞影響：當 stress > 0.7，反應變慢且彎曲幅度減小
        if stress > 0.7:
            bend_factor *= 0.5
            
        # 計算 9 段脊椎的角度偏移 (C1-Sacrum)
        # 模擬 S 型曲線
        new_spine = np.array([bend_factor * math.sin(i * 0.4) for i in range(9)])
        
        # 應用阻尼 (Smoothed Transition)
        self.spine_state = self.spine_state * (1 - self.damping) + new_spine * self.damping
        
        return {
            "spine_bend": float(bend_factor),
            "lateral_shift": float(dx * 0.05),
            "theta_matrix": self.spine_state.tolist()
        }

    def record_movement_error(self, expected_pos: float, actual_pos: float):
        """
        [+N16.1.1] 誤差反饋：小腦學習的基礎。
        """
        error = abs(expected_pos - actual_pos)
        self.error_accumulation += error
        if len(self.kinetic_history) > 100: self.kinetic_history.pop(0)
        self.kinetic_history.append({
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "state": "learning" if error > 1.0 else "stable"
        })
        
        if error > 5.0:
            logger.warning(f"⚖️ [Cerebellum] Movement imbalance detected! Error: {error:.2f}")

    def get_posture_snapshot(self) -> Dict[str, Any]:
        return {
            "spine_state": self.spine_state.tolist(),
            "average_error": self.error_accumulation / max(1, len(self.kinetic_history))
        }
