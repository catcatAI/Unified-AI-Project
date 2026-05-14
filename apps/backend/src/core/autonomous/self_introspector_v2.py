"""
SelfIntrospector v2 — 新架構版本
=================================

使用 TemporalState + NegativityDetector + AllocationPolicy 重構 N.22.6 自我內省。

改進：
- 幸福感歷史 → TemporalState（支援 trend/correlation/drift 查詢）
- 認知失調檢測 → NegativityDetector（已有 θ 自糾邏輯）
- 意圖一致性 → AllocationPolicy（規則化評估）

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

if False:
    from core.state.temporal import TemporalState
    from core.allocation.negativity import NegativityDetector
    from core.autonomous.state_matrix_adapter import StateMatrixAdapter

logger = logging.getLogger(__name__)


class SelfIntrospectorV2:
    """
    自我內省器 v2 — 新架構版本
    ==========================

    使用新架構的能力實現 N.22.6 自我內省趨勢追蹤。

    核心能力：
    1. 幸福感追蹤 — TemporalState.trend() 分析幸福感的上升/下降
    2. 認知失調檢測 — NegativityDetector 觸發 θ 負值
    3. 意圖一致性 — 使用分配決策的相似度邏輯
    4. 危機檢測 — TemporalState.anomalies() 檢測異常波動
    """

    def __init__(
        self,
        state_adapter: Optional["StateMatrixAdapter"] = None,
        dissonance_threshold: float = 0.6,
    ):
        self._adapter = state_adapter
        self._dissonance_threshold = dissonance_threshold
        self._last_check = datetime.now()

        if state_adapter is not None:
            self._timeline = state_adapter.temporal
            self._negativity = state_adapter.negativity_detector
        else:
            from core.state.temporal import TemporalState
            self._timeline = TemporalState(max_size=500)
            self._negativity = None

    def record_wellbeing(self, wellbeing: float, context: Optional[Dict[str, Any]] = None) -> None:
        """
        記錄幸福感快照到 TemporalState

        Args:
            wellbeing: 幸福感值 [0, 1]
            context: 額外上下文（預期情緒、壓力等級等）
        """
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'introspection': {
                'wellbeing': wellbeing,
                'context': context or {},
            },
        }
        self._timeline.record(snapshot)

    def perform_mental_health_check(
        self,
        state_analysis: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        執行心理健康檢查（新架構版本）

        使用 TemporalState.trend() 分析幸福感趨勢，
        使用 TemporalState.anomalies() 檢測異常波動。

        Returns:
            內省報告
        """
        wellbeing = state_analysis.get("wellbeing", 0.5)
        arousal = state_analysis.get("arousal", 0.5)
        stress = state_analysis.get("stress_level", 0.0)

        self.record_wellbeing(wellbeing, context)

        report: Dict[str, Any] = {
            "status": "healthy",
            "dissonance_detected": False,
            "anomalies": [],
            "recommendations": [],
            "wellbeing_trend": None,
            "crisis_detected": False,
        }

        if stress > 0.8 or wellbeing < 0.2:
            report["status"] = "strained"
            report["anomalies"].append("CRITICAL_STRESS_LEVEL")
            report["recommendations"].append("TRIGGER_RELAXATION_CYCLE")

        expected_sentiment = context.get("expected_sentiment", "neutral")
        valence = state_analysis.get("valence", 0.0)

        if expected_sentiment == "positive" and valence < -0.3:
            report["dissonance_detected"] = True
            report["anomalies"].append("POSITIVE_INTENT_NEGATIVE_STATE_MISMATCH")
            report["recommendations"].append("EXPRESS_EFFORT_OR_STRUGGLE")

            if self._negativity is not None:
                self._negativity.trigger(0.1)

        trend = self._timeline.trend('introspection', 'wellbeing', window=10)
        report["wellbeing_trend"] = trend.direction

        if trend.direction == 'falling' and trend.slope < -0.05:
            report["anomalies"].append("SUSTAINED_WELLBEING_DECLINE")
            report["recommendations"].append("INVESTIGATE_CAUSE_OF_WELLBEING_DECLINE")
            report["crisis_detected"] = True
            logger.warning("[IntrospectorV2] 檢測到幸福感持續下降趨勢")

        if trend.direction == 'rising' and trend.slope > 0.05:
            report["recommendations"].append("LEVERAGE_POSITIVE_TREND")

        anomalies = self._timeline.anomalies(
            'introspection', 'wellbeing', threshold=0.5, window=10
        )
        if anomalies:
            report["wellbeing_anomalies"] = len(anomalies)

        return report

    def check_intent_alignment_v2(
        self,
        action_name: str,
        action_vector: List[float],
        current_coord: List[float],
        intent_target: List[float],
    ) -> Dict[str, Any]:
        """
        意圖一致性檢查（新版本）

        評估「擬執行的動作」與「趨向原生意圖的方向」的一致性。
        使用 AllocationPolicy 的相似度邏輯。

        Returns:
            一致性報告
        """
        import math

        vec_a = action_vector
        vec_i = [
            intent_target[i] - current_coord[i] for i in range(min(len(intent_target), len(current_coord)))
        ]

        norm_i = math.sqrt(sum(v * v for v in vec_i))
        norm_a = math.sqrt(sum(v * v for v in vec_a))

        if norm_i < 0.1:
            alignment = 1.0 if norm_a < 0.2 else -0.5
        elif norm_a == 0:
            alignment = 0.0
        else:
            dot = sum(vec_a[i] * vec_i[i] for i in range(min(len(vec_a), len(vec_i))))
            alignment = dot / (norm_a * norm_i)

        alignment = max(-1.0, min(1.0, alignment))
        dissonance = 1.0 - (alignment + 1.0) / 2.0

        is_conflicting = dissonance > self._dissonance_threshold or alignment < 0

        return {
            "action": action_name,
            "alignment": alignment,
            "dissonance_score": dissonance,
            "is_conflicting": is_conflicting,
            "decision_override": "THROTTLE" if is_conflicting else "PROCEED",
        }

    def detect_cognitive_dissonance(
        self,
        expected_state: Dict[str, float],
        actual_state: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        檢測認知失調

        比較預期狀態與實際狀態的差異，
        使用 NegativityDetector 處理高失調情況。

        Args:
            expected_state: 預期狀態 {field: value}
            actual_state: 實際狀態 {field: value}

        Returns:
            失調報告
        """
        import math

        total_deviation = 0.0
        field_deviations = {}

        for field, expected in expected_state.items():
            actual = actual_state.get(field, expected)
            deviation = abs(actual - expected)
            field_deviations[field] = deviation
            total_deviation += deviation

        avg_deviation = total_deviation / max(1, len(field_deviations))
        dissonance_score = min(1.0, avg_deviation)

        if self._negativity is not None and dissonance_score > 0.3:
            self._negativity.trigger(dissonance_score * 0.2)

        return {
            "dissonance_score": dissonance_score,
            "field_deviations": field_deviations,
            "needs_correction": dissonance_score > 0.4,
            "triggered_negativity": dissonance_score > 0.3,
        }

    def get_wellbeing_report(self, window: int = 20) -> Dict[str, Any]:
        """
        獲取幸福感分析報告

        使用 TemporalState 的時間序列分析能力。
        """
        trend = self._timeline.trend('introspection', 'wellbeing', window=window)
        corr = self._timeline.correlation(
            'introspection', 'wellbeing', 'introspection', 'wellbeing', window=window
        )

        anomalies = self._timeline.anomalies(
            'introspection', 'wellbeing', threshold=0.5, window=window
        )

        return {
            "window": window,
            "trend": {
                "direction": trend.direction,
                "slope": trend.slope,
                "mean": trend.mean,
                "variance": trend.variance,
            },
            "self_correlation": {
                "correlation": corr.correlation,
                "strength": corr.strength,
            },
            "anomalies_count": len(anomalies),
            "snapshot_count": self._timeline.size(),
        }

    def adapt_dissonance_threshold(
        self,
        post_wellbeing: float,
        pre_wellbeing: float,
    ) -> None:
        """
        自適應調整失調閾值

        若 override 後 wellbeing 改善 → 閾值合理，保持或微調。
        若 override 後 wellbeing 下降 → 閾值可能過嚴，適當放寬。
        """
        delta = post_wellbeing - pre_wellbeing
        if delta > 0.05:
            self._dissonance_threshold = min(0.75, self._dissonance_threshold + 0.02)
        elif delta < -0.05:
            self._dissonance_threshold = max(0.45, self._dissonance_threshold - 0.02)

        logger.debug(
            f"[IntrospectorV2] Updated dissonance threshold: {self._dissonance_threshold:.3f}"
        )