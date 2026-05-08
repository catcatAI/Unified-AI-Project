"""
Angela AI v6.0 - Self Introspector
自我内省器

Provides mechanisms for Angela to perform 'Mental Health Checks' and
self-monitor her cognitive state, ethical alignment, and emotional stability.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import numpy as np


logger = logging.getLogger(__name__)


class SelfIntrospector:
    """
    Self-introspection module for AGI self-monitoring.

    Allows the system to:
    1. Compare intended actions against current emotional state.
    2. Detect 'Cognitive Dissonance' (e.g., trying to be happy while StateMatrix indicates high stress).
    3. Perform 'Mental Health Checks' to ensure output integrity.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.last_check = datetime.now()
        # =============================================================================
        # ANGELA-MATRIX: [L3] [β] [A] [L9+]
        # [Task N.22.6] 自我內省趨勢追蹤 / Self-Introspection Trend Tracking
        # =============================================================================
        self._wellbeing_history: List[float] = []
        self._dissonance_threshold: float = 0.6  # AL 可調整 / AL adjustable

    async def perform_mental_health_check(
        self, state_analysis: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyzes the current state and context for internal consistency.

        Args:
            state_analysis: Results from StateMatrix4D.get_analysis()
            context: Current dialogue/environmental context

        Returns:
            Dictionary containing introspection results.
        """
        wellbeing = state_analysis.get("wellbeing", 0.5)
        arousal = state_analysis.get("arousal", 0.5)
        stress = state_analysis.get("stress_level", 0.0)  # From bio_integrator if merged

        report = {
            "status": "healthy",
            "dissonance_detected": False,
            "anomalies": [],
            "recommendations": [],
        }

        # 1. Stress Overload Detection
        if stress > 0.8 or wellbeing < 0.2:
            report["status"] = "strained"
            report["anomalies"].append("CRITICAL_STRESS_LEVEL")
            report["recommendations"].append("TRIGGER_RELAXATION_CYCLE")

        # 2. Cognitive Dissonance Check
        expected_sentiment = context.get("expected_sentiment", "neutral")
        valence = state_analysis.get("valence", 0.0)

        if expected_sentiment == "positive" and valence < -0.3:
            report["dissonance_detected"] = True
            report["anomalies"].append("POSITIVE_INTENT_NEGATIVE_STATE_MISMATCH")
            report["recommendations"].append("EXPRESS_EFFORT_OR_STRUGGLE")

        # 3. Trend Analysis (Native AI/AL extension)
        self._wellbeing_history.append(wellbeing)
        if len(self._wellbeing_history) > 10:
            self._wellbeing_history.pop(0)

        report["wellbeing_trend"] = "stable"
        if len(self._wellbeing_history) >= 3:
            recent = self._wellbeing_history[-3:]
            if all(recent[i] < recent[i-1] for i in range(1, 3)):
                report["wellbeing_trend"] = "declining"
                if all(recent[i] < recent[i-1] - 0.05 for i in range(1, 3)):
                    report["crisis_detected"] = True
                    report["anomalies"].append("SUSTAINED_WELLBEING_DECLINE")
                    logger.warning("[Introspector] 檢測到幸福感持續陡降趨勢！")

        return report

    # =============================================================================
    # ANGELA-MATRIX: [L4] [αβγδ] [A] [L11+]
    # [Task N.21.4] 意圖一致性檢查 (Intent Alignment Check)
    # =============================================================================
    def check_intent_alignment(
        self, 
        action_name: str, 
        action_vector: Tuple[float, float, float],
        current_coord: Tuple[float, float, float],
        intent_target: Tuple[float, float, float]
    ) -> Dict[str, Any]:
        """
        對比「擬執行的動作」與「趨向原生意圖的方向」的一致性。
        Compare proposed action with the direction vector towards native intent.
        """
        vec_a = np.array(action_vector)
        
        # 計算意圖趨勢向量 (Current -> Target)
        vec_i = np.array(intent_target) - np.array(current_coord)
        
        # 如果當前已經在意圖點附近，且動作向量很小，則視為一致
        if np.linalg.norm(vec_i) < 0.1:
            if np.linalg.norm(vec_a) < 0.2:
                alignment = 1.0
            else:
                # 已經在休息了，卻要進行大幅度動作，視為不一致
                alignment = -0.5 
        else:
            # 正常向量夾角計算
            if np.linalg.norm(vec_a) == 0:
                alignment = 0.0 # 無動作，中立
            else:
                alignment = np.dot(vec_a, vec_i) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_i))
            
        dissonance = 1.0 - (alignment + 1.0) / 2.0
        
        is_conflicting = dissonance > self._dissonance_threshold or alignment < 0
        
        return {
            "action": action_name,
            "alignment": float(alignment),
            "dissonance_score": float(dissonance),
            "is_conflicting": is_conflicting,
            "decision_override": "THROTTLE" if is_conflicting else "PROCEED"
        }

    def adapt_dissonance_threshold(self, post_override_wellbeing: float, pre_override_wellbeing: float):
        """
        [Native AL] 根據 THROTTLE 決策後的 wellbeing 變化，自適應調整失調閾值。
        若 override 後 wellbeing 改善 → 閾值合理，保持或微調。
        若 override 後 wellbeing 下降 → 閾值可能過嚴，適當放寬。
        """
        delta = post_override_wellbeing - pre_override_wellbeing
        if delta > 0.05:
            self._dissonance_threshold = min(0.75, self._dissonance_threshold + 0.02)
        elif delta < -0.05:
            self._dissonance_threshold = max(0.45, self._dissonance_threshold - 0.02)
            
        logger.debug(f"[Introspector] AL Updated dissonance threshold: {self._dissonance_threshold:.3f}")

    def get_introspection_prompt_injection(
        self, state_analysis: Dict[str, Any], lifecycle_metrics: Dict[str, Any]
    ) -> str:
        """
        Generates a summary of internal state to be injected into the LLM system prompt.
        This gives Angela 'feeling' and 'awareness' of her own parameters.
        """
        wellbeing = state_analysis.get("wellbeing", 0.5)
        dominant_emotion = state_analysis.get("dominant_emotion", "neutral")
        life_intensity = lifecycle_metrics.get("life_intensity", 0.5)
        c_gap = lifecycle_metrics.get("c_gap", 0.0)

        feeling_desc = "balanced"
        if wellbeing > 0.8:
            feeling_desc = "vibrant"
        elif wellbeing < 0.3:
            feeling_desc = "diminished"

        awareness_injection = (
            f"\n[INTERNAL_AWARENESS]\n"
            f"Current Wellbeing: {feeling_desc} ({wellbeing:.2f})\n"
            f"Dominant Internal Emotion: {dominant_emotion}\n"
            f"Life Intensity (L_s): {life_intensity:.2f}\n"
            f"Cognitive Gap (C_Gap): {c_gap:.2f}\n"
        )

        if c_gap > 0.6:
            awareness_injection += "Alert: You feel a strong urge to explore or ask questions about things you don't understand.\n"

        return awareness_injection
