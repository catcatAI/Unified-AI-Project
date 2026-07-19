"""
Temporal State — 時間狀態查詢引擎
==================================

歷史記錄從「List[Dict]」升級為「可查詢的時間流」。
支援：
- 按時間範圍查詢
- 按軸/field 查詢
- 趨勢分析
- 異常檢測
- 軸間相關性

使用方式:
    from core.state.temporal import TemporalState

    timeline = TemporalState(max_size=500)

    # 記錄
    timeline.record({
        'timestamp': datetime.now().isoformat(),
        'alpha': {'focus': 0.8, 'energy': 0.7},
        'beta': {'curiosity': 0.6},
        ...
    })

    # 時間範圍查詢
    recent = timeline.recent(fraction=0.2)  # 最近 20%

    # 趨勢分析
    trend = timeline.trend('alpha', 'focus', window=50)

    # 異常檢測
    anomalies = timeline.anomalies(axis='beta', threshold=0.3)

    # 相關性
    corr = timeline.correlation('alpha', 'focus', 'beta', 'focus')

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SnapshotQuery:
    """Query parameters for TemporalState.query()."""

    axes: Optional[List[str]] = None
    fields: Optional[List[str]] = None
    limit: int = 10
    offset: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    sort_by: str = "timestamp"
    descending: bool = True


@dataclass
class TrendResult:
    """Result of a trend analysis."""

    axis: str = ""
    field_name: str = ""
    direction: str = "stable"
    magnitude: float = 0.0
    slope: float = 0.0
    mean: float = 0.0
    values: List[float] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)


@dataclass
class AnomalyResult:
    """Result of an anomaly detection."""

    axis: str = ""
    field: str = ""
    value: float = 0.0
    expected: float = 0.0
    z_score: float = 0.0
    timestamp: str = ""
    severity: str = "info"


@dataclass
class CorrelationResult:
    """Result of a correlation analysis between two axes/fields."""

    axis_a: str = ""
    field_a: str = ""
    axis_b: str = ""
    field_b: str = ""
    correlation: float = 0.0
    p_value: float = 1.0
    sample_size: int = 0
    strength: str = "none"


class TemporalState:
    def __init__(self, max_size: int = 500):
        self.max_size = max_size
        self.history: List[Dict[str, Any]] = []
        self._callbacks: List[Any] = []

    def record(self, snapshot: Dict[str, Any]) -> int:
        self.history.append(snapshot)
        if len(self.history) > self.max_size:
            self.history.pop(0)
        idx = len(self.history) - 1
        for cb in self._callbacks:
            cb(snapshot)
        return idx

    def recent(self, fraction: float = 0.2) -> List[Dict[str, Any]]:
        count = max(1, int(len(self.history) * fraction))
        return self.history[-count:]

    def size(self) -> int:
        return len(self.history)

    def get_at(self, idx: int) -> Optional[Dict[str, Any]]:
        if not self.history:
            return None
        if idx < 0:
            idx = len(self.history) + idx
        if idx < 0 or idx >= len(self.history):
            return None
        return self.history[idx]

    def clear(self) -> None:
        self.history.clear()

    def is_empty(self) -> bool:
        return len(self.history) == 0

    def on_record(self, callback: Any) -> None:
        self._callbacks.append(callback)

    def query(self, q: SnapshotQuery) -> List[Dict[str, Any]]:
        result = self.history
        if q.axes:
            result = [s for s in result if any(ax in s for ax in q.axes)]
        if q.fields:

            def _has_field(s: Dict[str, Any]) -> bool:
                for f in q.fields:
                    for v in s.values():
                        if isinstance(v, dict) and f in v:
                            return True
                return False

            result = [s for s in result if _has_field(s)]
        if q.start_time:
            result = [s for s in result if s.get("timestamp", "") >= q.start_time]
        if q.end_time:
            result = [s for s in result if s.get("timestamp", "") <= q.end_time]
        result = result[q.offset :]
        result = result[: q.limit]
        if q.descending:
            result = list(reversed(result))
        return result

    def get_field_series(self, axis: str, field: str, window: int = 10) -> List[float]:
        values = []
        for snap in reversed(self.history):
            ax_data = snap.get(axis)
            if isinstance(ax_data, dict) and field in ax_data:
                values.append(ax_data[field])
                if len(values) >= window:
                    break
        return values

    def to_observations(self, window: int = 50) -> List[Dict[str, Any]]:
        """Export recent history as causal observations.

        Returns a list of observation dicts (one per axis found in history),
        each with 'variables' (field names) and 'data' (field → time series).
        Compatible with CausalReasoningEngine.learn().
        """
        if not self.history:
            return []
        snapshots = self.history[-window:]
        axes = set()
        for snap in snapshots:
            axes.update(k for k, v in snap.items() if isinstance(v, dict))
        observations = []
        for axis in sorted(axes):
            fields = set()
            for snap in snapshots:
                ax_data = snap.get(axis, {})
                if isinstance(ax_data, dict):
                    fields.update(ax_data.keys())
            data: Dict[str, List[float]] = {}
            for fname in sorted(fields):
                vals = [
                    snap[axis][fname]
                    for snap in snapshots
                    if isinstance(snap.get(axis), dict) and fname in snap[axis]
                ]
                if vals:
                    data[fname] = vals
            if len(fields) >= 1:
                observations.append(
                    {
                        "id": f"trend_{axis}",
                        "variables": sorted(fields),
                        "data": data,
                    }
                )
        return observations

    def trend(self, axis: str, field: str, window: int = 50) -> TrendResult:
        values = self.get_field_series(axis, field, window)
        if len(values) < 2:
            return TrendResult(axis=axis, field_name=field, direction="insufficient_data")
        slope = (values[-1] - values[0]) / max(len(values) - 1, 1)
        mean_val = sum(values) / len(values)
        direction = "rising" if slope > 0.01 else ("falling" if slope < -0.01 else "stable")
        return TrendResult(
            axis=axis,
            field_name=field,
            direction=direction,
            magnitude=abs(slope),
            slope=slope,
            mean=mean_val,
            values=values,
        )

    def anomalies(
        self, axis: str, field: str, threshold: float = 0.5, window: int = 50
    ) -> List[AnomalyResult]:
        values = self.get_field_series(axis, field, window)
        if not values:
            return []
        mean_val = sum(values) / len(values)
        std = (sum((v - mean_val) ** 2 for v in values) / len(values)) ** 0.5 or 1.0
        results = []
        # Scan only the most recent `window` snapshots (not the whole history),
        # matching get_field_series(). The previous implementation iterated the
        # entire history every call -> O(history) recompute per query (§11.6/§11.8 B2).
        for snap in reversed(self.history[-window:]):
            if len(results) >= 10:
                break
            ax_data = snap.get(axis)
            if not isinstance(ax_data, dict) or field not in ax_data:
                continue
            v = ax_data[field]
            z = (v - mean_val) / std
            if abs(z) > threshold:
                results.append(
                    AnomalyResult(
                        axis=axis,
                        field=field,
                        value=v,
                        expected=mean_val,
                        z_score=z,
                        timestamp=snap.get("timestamp", ""),
                        severity="high" if abs(z) > 2.0 else "medium" if abs(z) > 1.5 else "info",
                    )
                )
        return results

    def find_drift(
        self, axis: str, field: str, expected_value: float = 0.5, drift_threshold: float = 0.3
    ) -> List[AnomalyResult]:
        results = []
        for snap in reversed(self.history):
            ax_data = snap.get(axis)
            if not isinstance(ax_data, dict) or field not in ax_data:
                continue
            v = ax_data[field]
            if abs(v - expected_value) > drift_threshold:
                results.append(
                    AnomalyResult(
                        axis=axis,
                        field=field,
                        value=v,
                        expected=expected_value,
                        z_score=(v - expected_value) / (drift_threshold or 0.001),
                        timestamp=snap.get("timestamp", ""),
                        severity="high",
                    )
                )
        return results

    def correlation(
        self, axis_a: str, field_a: str, axis_b: str, field_b: str, window: int = 50
    ) -> CorrelationResult:
        ax_a_vals = self.get_field_series(axis_a, field_a, window)
        ax_b_vals = self.get_field_series(axis_b, field_b, window)
        n = min(len(ax_a_vals), len(ax_b_vals))
        if n < 2:
            return CorrelationResult(axis_a=axis_a, field_a=field_a, axis_b=axis_b, field_b=field_b)
        x = ax_a_vals[:n]
        y = ax_b_vals[:n]
        mx = sum(x) / n
        my = sum(y) / n
        num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
        dx = sum((xi - mx) ** 2 for xi in x) ** 0.5
        dy = sum((yi - my) ** 2 for yi in y) ** 0.5
        r = num / (dx * dy) if dx and dy else 0.0
        r = max(-1.0, min(1.0, r))
        strength = "strong" if abs(r) > 0.7 else ("moderate" if abs(r) > 0.4 else "weak")
        return CorrelationResult(
            axis_a=axis_a,
            field_a=field_a,
            axis_b=axis_b,
            field_b=field_b,
            correlation=r,
            p_value=1.0,
            sample_size=n,
            strength=strength,
        )
