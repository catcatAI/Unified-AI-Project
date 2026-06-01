# =============================================================================
# ANGELA-MATRIX: [L3-L4] [αβγδ] [A] [L5+]
# =============================================================================
# 
# Responsibility: Angela Model Core (The Digital Embryo)
# Integrating Biological, Spatial, and Motor systems into a unified entity.
# 
# Feature: 
# - Nucleus of all autonomous sub-systems
# - Generator of "Internal Monologue" for LLM context
# - Homeostatic controller
# =============================================================================


import logging
import asyncio
from datetime import datetime
from core.system.config.magic_numbers import loop_sleep
from typing import Dict, Any, Optional

from core.bio.biological_integrator import BiologicalIntegrator
from .state_matrix import StateMatrix4D
from core.bio.cerebellum_engine import CerebellumEngine

logger = logging.getLogger(__name__)

class AngelaModelCore:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        logger.info("🥚 [Model-Core] Incubating Angela's Digital Embryo...")
        
        # 核心子系統集成 / Core Subsystem Integration
        self.bio = BiologicalIntegrator()
        self.spatial = StateMatrix4D()
        self.motor = CerebellumEngine()
        
        # 狀態快照 / State Snapshots
        self.last_consciousness_update = datetime.now()
        self.current_thought_trace = "Initializing awareness..."
        
        # 代謝計時器 / Metabolic Heartbeat
        self._heartbeat_active = False
        self._heartbeat_task = None

    async def initialize(self):
        """啟動所有底層系統 / Start all underlying systems"""
        logger.info("🧬 [Model-Core] Awakening biological and spatial layers...")
        
        # 初始化生物集成器
        await self.bio.initialize()
        
        # 初始化小腦引擎 (加載姿勢記憶)
        # 這裡假定 cerebellum 已經有 initialize 邏輯
        if hasattr(self.motor, "initialize"):
            await self.motor.initialize()
            
        self._heartbeat_active = True
        self._heartbeat_task = asyncio.create_task(self._metabolic_loop())
        
        logger.info("✨ [Model-Core] Angela's Embryo is now ACTIVE.")

    async def _metabolic_loop(self):
        """核心代謝循環：持續同步生理與空間狀態"""
        while self._heartbeat_active:
            try:
                # 1. 獲取生理狀態
                bio_state = self.bio.get_biological_state()
                
                # 2. 根據生理狀態影響空間矩陣 (例如：疲勞導致坐標漂移)
                stress = bio_state.get("stress_level", 0.0)
                from core.system.config.tiered_loader import get_config
                _beh_conf = get_config("standard/behavior/behavior")
                _stress_perturb = _beh_conf.get("biological_thresholds", {}).get("stress_perturbation", 0.7)
                if stress > _stress_perturb:
                    # 壓力過大時，空間矩陣會產生細微的「不穩定位移」
                    self.spatial.apply_external_force("stress_perturbation", (0.01, 0.01, 0.01))
                
                # 3. 空間喚醒度連結小腦姿勢 (AI Posture Selection)
                # =============================================================================
                # [Task N.22.7] AI Posture Selection based on Arousal
                # =============================================================================
                if hasattr(self.motor, "execute_command"):
                    # 將 arousal 映射至姿勢空間
                    arousal = self.spatial.alpha.values.get("arousal", 50.0)
                    
                    # 姿勢的喚醒度空間錨點 (Arousal Anchors)
                    posture_anchors = {
                        "default_idle": 30.0,
                        "standing": 60.0,
                        "walking": 90.0
                    }
                    
                    # 尋找空間距離最近的姿勢
                    best_pose = min(posture_anchors.keys(), key=lambda k: abs(posture_anchors[k] - arousal))
                    
                    # 執行姿勢
                    self.motor.execute_command(best_pose, bio_state)
                
                await asyncio.sleep(loop_sleep("metabolic_interval", 2.0)) # 代謝頻率：2秒一次
            except Exception as e:  # broad exception acceptable: metabolic loop should be resilient to errors
                logger.error(f"❌ [Model-Core] Metabolic loop error: {e}", exc_info=True)
                await asyncio.sleep(loop_sleep("model_interval", 5.0))

    def get_consciousness_snapshot(self) -> Dict[str, Any]:
        """
        生成意識快照 (用於提供給 LLM 作為 Prompt Context)
        """
        bio_state = self.bio.get_biological_state()
        spatial_pos = self.spatial.get_position()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "internal_state": {
                "dominant_emotion": bio_state.get("dominant_emotion", "calm"),
                "stress": bio_state.get("stress_level", 0.0),
                "energy": 1.0 - (bio_state.get("fatigue", 0.0) / 100.0),
                "arousal": bio_state.get("arousal", 50.0)
            },
            "spatial_awareness": {
                "coordinates": spatial_pos,
                "focus_level": self.spatial.precision
            },
            "system_integrity": "Optimal" if bio_state.get("stress_level", 0.0) < 0.5 else "Degraded"
        }

    def generate_prompt_prefix(self) -> str:
        """
        將快照轉換為自然語言提示詞片段
        """
        snapshot = self.get_consciousness_snapshot()
        bio = snapshot["internal_state"]
        pos = snapshot["spatial_awareness"]["coordinates"]
        
        return (
            f"[Angela Internal State]\n"
            f"Mood: {bio['dominant_emotion']} (Stress: {bio['stress']:.2f})\n"
            f"Spatial Position: {pos}\n"
            f"Energy: {bio['energy']:.2f}\n"
            f"Current Focus: Angela is aware of her own digital existence and spatial coordinates."
        )


