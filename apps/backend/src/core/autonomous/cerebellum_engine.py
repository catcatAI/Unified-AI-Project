import logging
import json
import os
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CerebellumEngine:
    """
    Angela 的小腦運動神經系統 (AL Pose Controller v2.0).
    負責「大腦指令 -> 肢體細節」的編譯、執行與持續學習。
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
        
        # 1. 姿態庫 (Pose Library) - [姿態名稱] -> {PartID: [Offset_X, Offset_Y, Angle]}
        self.pose_library: Dict[str, Dict[str, Any]] = {
            "default_idle": {
                "spine": [0.0] * 9,
                "fingers": {"left": [0.0]*5, "right": [0.0]*5},
                "stiffness": 0.5
            },
            "standing": {
                "spine": [0.0, 0.1, 0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "fingers": {"left": [0.0]*5, "right": [0.0]*5},
                "stiffness": 0.7
            }
        }
        
        # 2. 當前執行狀態
        self.current_pose_name = "default_idle"
        self.transition_speed = 0.1
        self.active_theta = np.zeros(9) # 當前脊椎緩衝

        # 3. 學習路徑
        self.storage_path = "apps/data/evolution/motor_memory.json"
        self._load_memory()

        logger.info("🧠 [Cerebellum] Pose-based AI Engine initialized.")

    def _load_memory(self):
        """讀取已學習的姿勢數據"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.pose_library.update(json.load(f))
                logger.info(f"💾 [Cerebellum] Loaded {len(self.pose_library)} poses from memory.")
            except Exception as e:
                logger.error(f"Failed to load motor memory: {e}")

    def learn_pose(self, name: str, data: Dict[str, Any]):
        """
        [Learning] 大腦將具體的關節數據標註為一個新姿態，或優化舊有數據。
        """
        self.pose_library[name] = data
        # 持久化學習結果
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.pose_library, f, ensure_ascii=False, indent=2)
            logger.info(f"🎓 [Cerebellum] Learned/Updated pose: '{name}'")
        except Exception as e:
            logger.error(f"Motor learning persistence failed: {e}")

    def execute_command(self, pose_name: str, bio_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        [Execution] 接收大腦指令，執行姿態細節。
        """
        if pose_name not in self.pose_library:
            logger.warning(f"⚠️ [Cerebellum] Unknown pose: '{pose_name}'. Using default.")
            pose_name = "default_idle"
        
        self.current_pose_name = pose_name
        target_data = self.pose_library[pose_name]
        
        # 動態插值 (Interpolation)：讓姿勢切換變得平滑，而非瞬間跳變
        target_spine = np.array(target_data.get("spine", [0.0]*9))
        self.active_theta = self.active_theta * (1 - self.transition_speed) + target_spine * self.transition_speed
        
        # 考慮生物影響 (疲勞時動作到位率下降)
        fatigue = bio_state.get("fatigue", 0.0) / 100.0
        if fatigue > 0.5:
            self.active_theta *= (1.0 - (fatigue - 0.5))

        return {
            "pose_name": pose_name,
            "theta_matrix": self.active_theta.tolist(),
            "is_stable": np.allclose(self.active_theta, target_spine, atol=0.01)
        }

    def get_posture_snapshot(self) -> Dict[str, Any]:
        return {
            "current_pose": self.current_pose_name,
            "spine_state": self.active_theta.tolist()
        }
