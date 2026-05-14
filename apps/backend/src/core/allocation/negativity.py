"""
Negativity Detector — θ 自糾系統
===================================

將 θ 軸的懷疑能力從 StateMatrix 中釋放出來。
支援：
- 觸發 θ 軸負值（表示懷疑當前分配）
- 檢測錯配的點位（使用 TemporalState 的索引查詢，不再 O(n)）
- 自動校正高置信度錯配
- 校正審計軌跡

使用方式:
    from core.allocation.negativity import NegativityDetector

    detector = NegativityDetector(timeline=history_timeline)
    detector.trigger(strength=0.2)
    misallocated = detector.detect()

    for item in misallocated:
        result = detector.correct(item['point_id'])

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Callable
import logging

from core.state.temporal import TemporalState, TrendResult
from core.allocation.resonance import ResonanceEngine

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """檢測結果"""
    count: int
    items: List[Dict[str, Any]]
    negativity_level: float
    audit_intensity: float

    def __repr__(self) -> str:
        return f"DetectionResult(n={self.count}, neg={self.negativity_level:.2f})"


@dataclass
class CorrectionResult:
    """校正結果"""
    status: str
    point_id: Optional[str] = None
    source_axis: Optional[str] = None
    target_axis: Optional[str] = None
    key: Optional[str] = None
    value: Optional[float] = None
    reasoning: str = ""
    dry_run: bool = False

    def __repr__(self) -> str:
        return f"CorrectionResult({self.status}: {self.point_id})"


class NegativityDetector:
    """
    負值檢測器
    =========

    獨立模組，負責 θ 軸的懷疑與修正能力。
    使用 TemporalState 的索引查詢，檢測從 O(n) → O(k)。
    """

    def __init__(
        self,
        timeline: TemporalState,
        resonance_engine: Optional[ResonanceEngine] = None,
        negativity_threshold: float = 0.5,
        correction_urge_threshold: float = 0.6,
        audit_intensity_base: float = 0.5,
    ):
        self._timeline = timeline
        self._resonance = resonance_engine

        self._negativity = 0.0
        self._correction_urge = 0.0
        self._audit_intensity = 0.0

        self._negativity_threshold = negativity_threshold
        self._correction_urge_threshold = correction_urge_threshold
        self._audit_intensity_base = audit_intensity_base

        self._misallocation_log: List[Dict[str, Any]] = []
        self._correction_audit_trail: List[Dict[str, Any]] = []
        self._max_log = 100
        self._max_trail = 50

        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []

    @property
    def negativity(self) -> float:
        return self._negativity

    @property
    def correction_urge(self) -> float:
        return self._correction_urge

    @property
    def needs_correction(self) -> bool:
        return self._negativity >= self._negativity_threshold

    @property
    def ready_to_correct(self) -> bool:
        return self._correction_urge >= self._correction_urge_threshold

    def trigger(self, strength: float = 0.1) -> None:
        """
        觸發 θ 軸負值 — 表示懷疑當前分配

        當以下情況發生時調用：
        - 用戶反饋顯示分配錯誤
        - 新輸入與舊分配矛盾
        - 長時間未校正的不確定狀態
        """
        self._negativity = min(1.0, self._negativity + strength)
        self._audit_intensity = min(1.0, self._audit_intensity + strength * 0.5)

        if self._negativity > 0.3:
            self._correction_urge = min(1.0, self._correction_urge + strength * 0.3)

        logger.info(
            f"[Theta-Neg] Triggered: negativity={self._negativity:.2f}, "
            f"correction_urge={self._correction_urge:.2f}"
        )

    def detect(self) -> DetectionResult:
        """
        檢測錯配的點位（使用索引查詢，非 O(n) 遍歷）

        原理：
        - 根據 audit_intensity 確定掃描範圍（並非全部歷史）
        - 使用 _timeline.get_field_series() 和 _timeline.find_drift()
        - 對於每個軸的每個 field：計算與理想值的偏差

        Returns:
            DetectionResult
        """
        if self._negativity < self._negativity_threshold:
            return DetectionResult(
                count=0, items=[], negativity_level=self._negativity, audit_intensity=self._audit_intensity
            )

        if self._timeline.is_empty():
            return DetectionResult(
                count=0, items=[], negativity_level=self._negativity, audit_intensity=self._audit_intensity
            )

        recent_snapshots = self._timeline.recent(fraction=audit_fraction)

        if not recent_snapshots:
            return DetectionResult(
                count=0, items=[], negativity_level=self._negativity, audit_intensity=self._audit_intensity
            )

        misallocated = []
        axes_in_snapshot = set()
        for snapshot in recent_snapshots:
            for axis_name in snapshot.keys():
                if not axis_name.startswith('__'):
                    axes_in_snapshot.add(axis_name)

        axes_to_check = list(axes_in_snapshot - {'__index__', 'timestamp'})

        for axis_name in axes_to_check:
            fields_in_axis = set()
            for snapshot in recent_snapshots:
                if axis_name in snapshot and isinstance(snapshot[axis_name], dict):
                    fields_in_axis.update(snapshot[axis_name].keys())

            for field_name in fields_in_axis:
                drift_threshold = 0.3 - (self._negativity - 0.5) * 0.1
                drift_threshold = max(0.15, min(0.4, drift_threshold))

                trend = self._timeline.trend(axis_name, field_name, window=min(50, len(recent_snapshots)))
                if trend.values and len(trend.values) >= 3:
                    mean = trend.mean
                    variance = trend.variance
                    std = variance ** 0.5

                    for i, value in enumerate(trend.values):
                        deviation = abs(value - mean)
                        if deviation > drift_threshold and std > 0.01:
                            idx = len(self._timeline) - len(trend.values) + i
                            misallocated.append({
                                "point_id": f"hist_{idx}_{axis_name}_{field_name}",
                                "source_axis": axis_name,
                                "field": field_name,
                                "value": value,
                                "expected": mean,
                                "deviation": deviation,
                                "drift_ratio": deviation / max(std, 0.01),
                                "misallocation_confidence": min(1.0, deviation / max(std, 0.01)),
                            })

        self._misallocation_log.extend(misallocated)
        if len(self._misallocation_log) > self._max_log:
            self._misallocation_log = self._misallocation_log[-self._max_log:]

        logger.info(
            f"[Theta-Neg] Detected {len(misallocated)} misallocated points "
            f"(negativity={self._negativity:.2f})"
        )

        return DetectionResult(
            count=len(misallocated),
            items=misallocated,
            negativity_level=self._negativity,
            audit_intensity=self._audit_intensity,
        )

    def correct(
        self,
        point_id: str,
        target_axis: Optional[str] = None,
        dry_run: bool = False,
    ) -> CorrectionResult:
        """
        校正一個錯配的點位

        Args:
            point_id: 錯配點位ID（格式：hist_{idx}_{axis}_{field}）
            target_axis: 目標軸（自動檢測如果為None）
            dry_run: True=只分析不實際移動

        Returns:
            CorrectionResult
        """
        if self._negativity < 0.3:
            return CorrectionResult(status="skip", reasoning="negativity too low")

        parts = point_id.split("_")
        if len(parts) < 4:
            return CorrectionResult(status="error", reasoning=f"invalid point_id: {point_id}")

        try:
            hist_idx = int(parts[1])
            source_axis = parts[2]
            field_name = "_".join(parts[3:]) if len(parts) > 4 else parts[3]
        except (ValueError, IndexError):
            return CorrectionResult(status="error", reasoning=f"cannot parse point_id: {point_id}")

        snapshot = self._timeline.get_at(hist_idx)
        if snapshot is None:
            return CorrectionResult(status="error", reasoning=f"history index out of range: {hist_idx}")

        axis_data = snapshot.get(source_axis, {})
        if not isinstance(axis_data, dict):
            return CorrectionResult(status="error", reasoning=f"no axis data for {source_axis}")

        value = axis_data.get(field_name)
        if value is None:
            return CorrectionResult(status="error", reasoning=f"no field {field_name} in {source_axis}")

        if target_axis is None:
            target_axis = self._find_best_axis_for_key(field_name, source_axis)

        if dry_run:
            return CorrectionResult(
                status="dry_run",
                point_id=point_id,
                source_axis=source_axis,
                target_axis=target_axis,
                key=field_name,
                value=value,
                reasoning=f"自動檢測：'{field_name}' 更適合分配到 {target_axis} 而非 {source_axis}",
                dry_run=True,
            )

        correction = {
            "timestamp": datetime.now().isoformat(),
            "point_id": point_id,
            "source_axis": source_axis,
            "target_axis": target_axis,
            "key": field_name,
            "original_value": value,
            "delta": 0.1,
            "negativity_at_correction": self._negativity,
        }
        self._correction_audit_trail.append(correction)
        if len(self._correction_audit_trail) > self._max_trail:
            self._correction_audit_trail = self._correction_audit_trail[-self._max_trail:]

        self._negativity = max(0.0, self._negativity - 0.1)
        self._correction_urge = max(0.0, self._correction_urge - 0.15)

        logger.info(f"[Theta-Neg] Corrected {point_id}: {source_axis} → {target_axis}")

        return CorrectionResult(
            status="corrected",
            point_id=point_id,
            source_axis=source_axis,
            target_axis=target_axis,
            key=field_name,
            value=value,
            reasoning=f"{source_axis}.{field_name} → {target_axis}.{field_name}",
        )

    def auto_correct_all(self, min_confidence: float = 0.5) -> Dict[str, Any]:
        """
        自動校正所有高置信度的錯配點位

        當 correction_urge >= threshold 時調用。
        """
        if not self.ready_to_correct:
            return {"status": "skip", "reason": "correction_urge too low", "corrected": 0}

        detection = self.detect()
        high_conf = [m for m in detection.items if m.get("misallocation_confidence", 0) >= min_confidence]

        corrected_count = 0
        for item in high_conf:
            result = self.correct(item["point_id"])
            if result.status == "corrected":
                corrected_count += 1

        self._negativity = max(0.0, self._negativity - corrected_count * 0.05)
        self._correction_urge = max(0.0, self._correction_urge - corrected_count * 0.1)

        return {
            "status": "completed",
            "corrected": corrected_count,
            "total_detected": detection.count,
            "negativity_after": self._negativity,
            "correction_urge_after": self._correction_urge,
        }

    def _find_best_axis_for_key(self, key: str, current_axis: str) -> str:
        """根據鍵名找到最合適的軸"""
        key_lower = key.lower()
        key_to_axis = {
            "energy": "alpha", "comfort": "alpha", "arousal": "alpha", "tension": "alpha", "vitality": "alpha",
            "curiosity": "beta", "focus": "beta", "confusion": "beta", "learning": "beta", "clarity": "beta",
            "happiness": "gamma", "sadness": "gamma", "anger": "gamma", "fear": "gamma",
            "surprise": "gamma", "trust": "gamma", "calm": "gamma", "anticipation": "gamma",
            "bond": "delta", "attention": "delta", "presence": "delta", "engagement": "delta",
            "logic": "epsilon", "precision": "epsilon", "certainty": "epsilon", "complexity": "epsilon",
        }
        if key_lower in key_to_axis:
            candidate = key_to_axis[key_lower]
            if candidate != current_axis:
                return candidate
        return current_axis

    def report(self) -> Dict[str, Any]:
        """獲取完整狀態報告"""
        return {
            "negativity": self._negativity,
            "correction_urge": self._correction_urge,
            "audit_intensity": self._audit_intensity,
            "misallocation_count": len(self._misallocation_log),
            "correction_count": len(self._correction_audit_trail),
            "recent_corrections": self._correction_audit_trail[-5:],
            "needs_correction": self.needs_correction,
            "ready_to_correct": self.ready_to_correct,
        }

    def reset(self) -> None:
        """重置負值系統"""
        self._negativity = 0.0
        self._correction_urge = 0.0
        self._audit_intensity = 0.0
        logger.info("[Theta-Neg] Negativity system reset")

    def on_correct(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """註冊校正回調"""
        self._callbacks.append(callback)

    def __repr__(self) -> str:
        return f"NegativityDetector(neg={self._negativity:.2f}, urge={self._correction_urge:.2f})"