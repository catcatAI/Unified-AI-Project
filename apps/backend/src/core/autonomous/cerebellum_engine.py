# =============================================================================
# ANGELA-MATRIX: L1-L6[小腦] γ [A] L2+
# =============================================================================
# 職責: 小腦運動神經系統 (Cerebellum Engine).
# 維度: 物理維度 (γ) 的運動插值、震顫控制與步態演化。
# =============================================================================

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
            },
            "walking": {
                "spine": [0.0, 0.15, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "fingers": {"left": [0.0]*5, "right": [0.0]*5},
                "stiffness": 0.6
            }
        }
        
        # 2. 當前執行狀態
        self.current_pose_name = "default_idle"
        self.transition_speed = 0.1
        self.active_theta = np.zeros(9) # 當前脊椎緩衝

        # 3. 學習路徑與演化里程
        self.storage_path = os.path.join(os.path.dirname(__file__), "../../../data/evolution/motor_memory.json")
        self.total_distance = 0.0
        self.evolution_threshold = 10000.0 # 演化門檻
        self.error_accumulation = 0.0
        self.kinetic_history = []
        
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

    def refine_pose(self, name: str, adjustments: Dict[str, Any]):
        """
        [Optimization] 大腦對現有姿態進行微調。
        adjustments: {"spine": [index, value], "stiffness": delta}
        """
        if name in self.pose_library:
            pose = self.pose_library[name]
            if "spine" in adjustments:
                idx, val = adjustments["spine"]
                pose["spine"][idx] += val
            if "stiffness" in adjustments:
                pose["stiffness"] += adjustments["stiffness"]
            
            logger.info(f"📈 [Cerebellum] Optimized pose '{name}': index {adjustments.get('spine')} updated.")
            self._save_memory()

    def capture_current_state(self, new_name: str, current_full_state: Dict[str, Any]):
        """
        [New Pose] 大腦捕捉目前的物理快照並定義為新姿態標籤。
        """
        self.pose_library[new_name] = {
            "spine": current_full_state.get("theta_matrix", [0.0]*9),
            "fingers": current_full_state.get("fingers", {"left": [0.0]*5, "right": [0.0]*5}),
            "stiffness": current_full_state.get("stiffness", 0.5),
            "created_at": datetime.now().isoformat()
        }
        logger.info(f"🆕 [Cerebellum] New pose learned via Brain capture: '{new_name}'")
        self._save_memory()

    def _save_memory(self):
        """持久化姿態庫到硬碟"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.pose_library, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Persistence failed: {e}")

    def update_proprioception(self, actual_theta: List[float], external_force: float = 0.0):
        """
        [Proprioception] 身體自覺反饋：比較預期與實際姿勢。
        """
        actual_np = np.array(actual_theta)
        error = np.linalg.norm(self.active_theta - actual_np)
        
        # 如果誤差持續存在，說明環境阻力大 (如撞牆或被滑鼠拖動)
        if error > 0.5:
            # 調高阻尼，嘗試穩定身體
            self.damping = min(0.5, self.damping + 0.05)
            logger.debug(f"⚖️ [Cerebellum] Proprioception warning: Pose error {error:.2f}. Increasing damping.")
        else:
            # 恢復自然靈韌度
            self.damping = max(0.15, self.damping - 0.01)
            
        self.record_movement_error(np.mean(self.active_theta), np.mean(actual_np))

    def record_movement_error(self, expected_pos: float, actual_pos: float):
        """
        [+N16.1.1] 誤差反饋與里程累積。
        """
        error = abs(expected_pos - actual_pos)
        self.total_distance += error # 使用位移殘差作為里程指標
        self.error_accumulation += error
        
        if len(self.kinetic_history) > 100: self.kinetic_history.pop(0)
        self.kinetic_history.append({
            "timestamp": datetime.now().isoformat(),
            "error": error
        })
        
        # 檢查是否達到演化門檻 (10000px)
        if self.total_distance >= self.evolution_threshold:
            self._evolve_gait()
            self.total_distance = 0.0 # 重置里程

    def _evolve_gait(self):
        """
        [N.16.3] 自律姿態演化：根據歷史誤差微調。
        """
        avg_error = self.error_accumulation / max(1, len(self.kinetic_history))
        logger.info(f"🧬 [Cerebellum] Autonomous Evolution Triggered. Avg Error: {avg_error:.2f}")
        
        # 演化邏輯：如果誤差大，優化「walking」姿勢的重心
        if "walking" in self.pose_library:
            pose = self.pose_library["walking"]
            if avg_error > 2.0:
                # 降低複雜度，追求穩定
                pose["spine"] = [s * 0.9 for s in pose["spine"]]
            else:
                # 增加靈動性
                pose["spine"] = [s * 1.1 for s in pose["spine"]]
            
            self._save_memory()
            self.error_accumulation = 0.0 # 重置
            logger.info("✨ [Cerebellum] Walking gait has evolved for better stability.")

    def execute_command(self, pose_name: str, bio_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        [Execution] 接收大腦指令，執行姿態細節。
        整合 N.16.1.2 神經與心跳對接邏輯。
        """
        if pose_name not in self.pose_library:
            logger.warning(f"⚠️ [Cerebellum] Unknown pose: '{pose_name}'. Using default.")
            pose_name = "default_idle"
        
        self.current_pose_name = pose_name
        target_data = self.pose_library[pose_name]
        
        # 1. 提取生物維度
        fatigue = bio_state.get("fatigue", 0.0) / 100.0
        stress = bio_state.get("stress_level", 0.0)
        energy = (100.0 - fatigue * 100.0) / 100.0
        hormones = bio_state.get("hormones", {})
        adrenaline = hormones.get("adrenaline", 20.0) / 100.0

        # 2. 動態轉換速度 (受能量影響)
        # 能量低時，姿勢切換變慢 (反應遲鈍)
        current_speed = self.transition_speed * (0.5 + energy * 0.5)
        
        # 3. 插值計算
        target_spine = np.array(target_data.get("spine", [0.0]*9))
        self.active_theta = self.active_theta * (1 - current_speed) + target_spine * current_speed
        
        # 4. 生物特徵疊加 (Biological Overlays)
        # 疲勞衰減：動作不到位
        if fatigue > 0.4:
            self.active_theta *= (1.0 - (fatigue - 0.4) * 0.5)
            
        # 緊張震顫：高壓力或高腎上腺素導致高頻微小抖動
        tremor_intensity = max(0.0, stress * 0.05 + adrenaline * 0.02)
        if tremor_intensity > 0.01:
            tremor = np.random.normal(0, tremor_intensity, size=9)
            self.active_theta += tremor

        # 5. [Task N.12.9] 五指神經矩陣 (Fingers)
        # 根據姿勢獲取手指捲縮度 (f_curl 0~1)
        finger_matrix = target_data.get("fingers", {"left": [0.0]*5, "right": [0.0]*5})

        return {
            "pose_name": pose_name,
            "theta_matrix": self.active_theta.tolist(),
            "finger_matrix": finger_matrix,
            "is_stable": np.allclose(self.active_theta, target_spine, atol=0.01),
            "tremor_active": tremor_intensity > 0.01
        }

    def get_posture_snapshot(self) -> Dict[str, Any]:
        return {
            "current_pose": self.current_pose_name,
            "spine_state": self.active_theta.tolist()
        }
