# =============================================================================
# ANGELA-MATRIX: L4[創造層] βδ [A] L4+
# =============================================================================
# 職責: 藝術學習工作流 (Art Learning Workflow).
# 維度: 認知學習 (β) 與視覺呈現 (γ) 的自動化接軌。
# =============================================================================

import logging
from enum import Enum
from typing import Dict, Any
from .art_learning_system import ArtLearningSystem
from .biological_integrator import BiologicalIntegrator

logger = logging.getLogger(__name__)

class WorkflowStage(Enum):
    """工作流阶段 / Workflow stages"""
    RESEARCH = ("研究", "Search for tutorials and references")
    ANALYSIS = ("分析", "Analyze images and techniques")
    PRACTICE = ("练习", "Practice and skill acquisition")
    EVOLUTION = ("演化", "Evolve aesthetics based on feedback")
    COMPLETE = ("完成", "Workflow complete")

class ArtLearningWorkflow:
    """
    Angela 的外觀演化協調器 (2030 Standard).
    負責將 L1 的生物脈動 轉化為 L4 的美學演化，最終在 L6 渲染層實體化。
    """
    def __init__(self, bio_integrator: BiologicalIntegrator):
        self.bio = bio_integrator
        self.art_system = ArtLearningSystem()
        self.current_overrides = {}

    async def update_visual_state(self) -> Dict[str, Any]:
        """
        [L1 -> L4 Sync] 根據當前生物指標，計算最新的色彩覆蓋。
        """
        bio_state = self.bio.get_biological_state()
        self.current_overrides = self.art_system.get_color_overrides(bio_state)
        
        # 記錄美學日誌
        emotion = bio_state.get("dominant_emotion", "neutral")
        logger.debug(f"🎨 [L4-Workflow] Aesthetic shift based on '{emotion}'.")
        
        return self.current_overrides

    def process_user_aesthetic_feedback(self, feedback_text: str):
        """
        [L4-Evolution] 根據用戶在對話中對外觀的評價進行學習。
        """
        self.art_system.learn_from_feedback(feedback_text, str(self.current_overrides))

# 單例模式初始化 (由 BiologicalIntegrator 驅動)
_instance = None
def get_art_workflow(bio=None):
    global _instance
    if _instance is None and bio is not None:
        _instance = ArtLearningWorkflow(bio)
    return _instance
