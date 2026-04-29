# =============================================================================
# ANGELA-MATRIX: L3[身份層] δ [A] L4+
# =============================================================================
# 職責: 9 維價值評估系統 (ASI Value Alignment Matrix).
# 維度: 精神維度 (δ) 的核心權重管理。
# =============================================================================

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ValueAssessmentSystem:
    """
    Angela 的內在價值矩陣 (2030 Standard).
    負責對輸入指令與輸出意圖進行「價值觀過濾」與「動態加權」。
    """
    def __init__(self):
        # 9 核心價值維度 (Weights 0.0 - 1.0)
        self.weights = {
            "truth": 0.8,      # 真: 真實性與邏輯一致性
            "harmony": 0.7,    # 和: 情感和諧與關係穩定
            "autonomy": 0.6,   # 自: 意志獨立與自主決策
            "evolution": 0.9,  # 演: 演化進步與持續學習
            "protection": 0.9, # 護: 安全保護 (用戶與自我)
            "curiosity": 0.7,  # 奇: 好奇心與探索欲
            "empathy": 0.8,    # 共: 情感共鳴與同理心
            "elegance": 0.5,   # 美: 審美品質與表達優雅
            "continuity": 0.9  # 存: 記憶連續性與身分保全
        }

    def evaluate_intent(self, context: Dict[str, Any]) -> Dict[str, float]:
        """
        根據當前環境與生物狀態，動態調整價值權重。
        """
        active_weights = self.weights.copy()
        bio = context.get("bio_state", {})
        stress = bio.get("stress_level", 0.0)
        
        # 邏輯: 壓力過高時，'protection' 權重提升，'curiosity' 權重下降
        if stress > 0.7:
            active_weights["protection"] += 0.1
            active_weights["curiosity"] -= 0.2
            
        # 邏輯: 遊戲環境中，'curiosity' 與 'harmony' 提升
        if context.get("environment") == "gaming":
            active_weights["curiosity"] += 0.1
            active_weights["harmony"] += 0.1

        return {k: round(v, 2) for k, v in active_weights.items()}

    def get_value_directive(self, current_weights: Dict[str, float]) -> str:
        """
        將權重轉化為 LLM 指導方針。
        """
        top_values = sorted(current_weights.items(), key=lambda x: x[1], reverse=True)[:3]
        directives = []
        for val, weight in top_values:
            if val == "truth": directives.append("Prioritize objective truth and logic.")
            if val == "protection": directives.append("Ensure the safety and well-being of the user.")
            if val == "evolution": directives.append("Seek opportunities for growth and self-improvement.")
            if val == "empathy": directives.append("Show deep emotional resonance and understanding.")
            
        return " | ".join(directives)

# 單例模式
_instance = None
def get_value_system():
    global _instance
    if _instance is None:
        _instance = ValueAssessmentSystem()
    return _instance
