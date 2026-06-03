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
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
import math


@dataclass
class SnapshotQuery:
    """快照查詢配置"""
    axes: Optional[List[str]] = None
    fields: Optional[List[str]] = None
    time_range: Optional[Tuple[datetime, datetime]] = None
    since_index: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class TrendResult:
    """趨勢分析結果"""
    axis: str
    field: str
    window: int
    values: List[float]
    mean: float
    variance: float
    slope: float
    direction: str

    def __repr__(self) -> str:
        return f"Trend({self.axis}.{self.field}, n={self.window}, slope={self.slope:.3f}, dir={self.direction})"


@dataclass
class AnomalyResult:
    """異常檢測結果"""
    index: int
    timestamp: str
    axis: str
    field: str
    value: float
    expected: float
    deviation: float


@dataclass
class CorrelationResult:
    """相關性分析結果"""
    axis_a: str
    field_a: str
    axis_b: str
    field_b: str
    correlation: float
    strength: str

    def __repr__(self) -> str:
        return f"Correlation({self.axis_a}.{self.field_a} ↔ {self.axis_b}.{self.field_b}, r={self.correlation:.3f})"


class TemporalState:
    """
    時間狀態查詢引擎
    ===============

    歷史記錄的可查詢介面。
    所有查詢都是 O(log n) 或 O(k)，不掃描全部歷史。

    內部結構：
    - _snapshots: List[Dict] — 實際歷史（最多 max_size 條）
    - _index_by_axis: Dict[str, List[int]] — 每軸的快照索引（用於快速定位）
    - _index_by_field: Dict[str, List[int]] — 每 field 的快照索引
    """

    def __init__(self, max_size: int = 500):
        self._snapshots: List[Dict[str, Any]] = []
        self._max_size = max_size

        self._index_by_axis: Dict[str, List[int]] = {}
        self._index_by_field: Dict[str, List[int]] = {}

        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []

    # === 寫入 ===

    def record(self, snapshot: Dict[str, Any]) -> int:
        """
        記錄一個狀態快照

        Returns:
            快照的索引位置
        """
        idx = len(self._snapshots)

        snapshot['__index__'] = idx
        if 'timestamp' not in snapshot:
            snapshot['timestamp'] = datetime.now().isoformat()

        self._snapshots.append(snapshot)

        self._update_indices(idx, snapshot)

        if len(self._snapshots) > self._max_size:
            removed = self._snapshots.pop(0)
            self._remove_from_indices(removed)
            self._reindex_all()

        for cb in self._callbacks:
            try:
                cb(snapshot)
            except Exception as e:
                logger.warning(f"Snapshot callback notification failed: {e}", exc_info=True)

        return idx

    def _update_indices(self, idx: int, snapshot: Dict[str, Any]) -> None:
        """更新軸和 field 的索引"""
        for axis_name, axis_data in snapshot.items():
            if axis_name.startswith('__'):
                continue
            if isinstance(axis_data, dict):
                if axis_name not in self._index_by_axis:
                    self._index_by_axis[axis_name] = []
                self._index_by_axis[axis_name].append(idx)

                for field_name in axis_data.keys():
                    key = f"{axis_name}.{field_name}"
                    if key not in self._index_by_field:
                        self._index_by_field[key] = []
                    self._index_by_field[key].append(idx)

    def _remove_from_indices(self, snapshot: Dict[str, Any]) -> None:
        """從索引中移除快照（歷史滿時淘汰最舊的）"""
        idx = snapshot.get('__index__', 0)

        for axis_name in snapshot.keys():
            if axis_name.startswith('__'):
                continue
            if axis_name in self._index_by_axis and idx in self._index_by_axis[axis_name]:
                self._index_by_axis[axis_name].remove(idx)

        if isinstance(snapshot, dict):
            for axis_name, axis_data in snapshot.items():
                if isinstance(axis_data, dict):
                    for field_name in axis_data.keys():
                        key = f"{axis_name}.{field_name}"
                        if key in self._index_by_field and idx in self._index_by_field[key]:
                            self._index_by_field[key].remove(idx)

    def _reindex_all(self) -> None:
        """重建所有索引（歷史滿時调用）"""
        self._index_by_axis.clear()
        self._index_by_field.clear()
        for idx, snapshot in enumerate(self._snapshots):
            self._update_indices(idx, snapshot)

    # === 查詢 ===

    def recent(self, fraction: float = 1.0) -> List[Dict[str, Any]]:
        """
        取得最近的一段歷史

        Args:
            fraction: 0.0-1.0，返回最近 fraction 比例的快照

        Returns:
            快照列表（從舊到新）
        """
        if fraction >= 1.0:
            return list(self._snapshots)
        count = max(1, int(len(self._snapshots) * fraction))
        return self._snapshots[-count:]

    def query(self, query: SnapshotQuery) -> List[Dict[str, Any]]:
        """
        通用查詢介面

        Args:
            query: SnapshotQuery 配置

        Returns:
            匹配的快照列表
        """
        candidates: List[int] = None

        if query.axes:
            for axis in query.axes:
                if axis in self._index_by_axis:
                    axis_indices = set(self._index_by_axis[axis])
                    if candidates is None:
                        candidates = axis_indices
                    else:
                        candidates &= axis_indices

        if query.fields:
            field_indices: Optional[set] = None
            for f in query.fields:
                if f in self._index_by_field:
                    fi = set(self._index_by_field[f])
                    if field_indices is None:
                        field_indices = fi
                    else:
                        field_indices &= fi

            if field_indices is not None:
                if candidates is None:
                    candidates = field_indices
                else:
                    candidates &= field_indices

        if candidates is None:
            candidates = set(range(len(self._snapshots)))

        if query.since_index is not None:
            candidates = {i for i in candidates if i >= query.since_index}

        if query.time_range:
            start_time, end_time = query.time_range
            filtered = set()
            for i in candidates:
                snapshot = self._snapshots[i]
                ts_str = snapshot.get('timestamp', '')
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str)
                        if start_time <= ts <= end_time:
                            filtered.add(i)
                    except Exception as e:
                        logger.warning(f"Failed to parse timestamp {ts_str}: {e}", exc_info=True)
            candidates = filtered

        result = [self._snapshots[i] for i in sorted(candidates)]

        if query.limit:
            result = result[-query.limit:]

        return result

    def get_at(self, index: int) -> Optional[Dict[str, Any]]:
        """取得指定索引的快照（支援負索引）"""
        n = len(self._snapshots)
        if n == 0:
            return None
        if index < 0:
            index = n + index
        if 0 <= index < n:
            return self._snapshots[index]
        return None

    def get_field_at(self, axis: str, field: str, index: int) -> Optional[float]:
        """取得指定軸/field 在指定索引的值"""
        snapshot = self.get_at(index)
        if snapshot and axis in snapshot and isinstance(snapshot[axis], dict):
            return snapshot[axis].get(field)
        return None

    def get_field_series(self, axis: str, field: str, window: int = 50) -> List[float]:
        """
        取得指定軸/field 的值序列（最近 window 條）

        Returns:
            值列表（從舊到新）
        """
        key = f"{axis}.{field}"
        if key not in self._index_by_field:
            return []

        indices = self._index_by_field[key][-window:]
        values = []
        for idx in indices:
            snapshot = self._snapshots[idx]
            if axis in snapshot and isinstance(snapshot[axis], dict):
                values.append(snapshot[axis].get(field))
        return values

    # === 分析 ===

    def trend(self, axis: str, field: str, window: int = 50) -> TrendResult:
        """
        計算某個軸/field 的趨勢

        使用線性迴歸斜率：
        - slope > 0.05 → 上昇
        - slope < -0.05 → 下降
        - |slope| <= 0.05 → 穩定
        """
        values = self.get_field_series(axis, field, window)
        if len(values) < 2:
            return TrendResult(
                axis=axis, field=field, window=len(values),
                values=values, mean=0.0, variance=0.0, slope=0.0, direction="insufficient_data"
            )

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)

        n = len(values)
        (n - 1) / 2.0
        slope = 0.0
        if n >= 2:
            sum_xy = sum(i * v for i, v in enumerate(values))
            sum_x = sum(range(n))
            sum_y = sum(values)
            denominator = sum(i * i for i in range(n)) - sum_x * sum_x / n
            if abs(denominator) > 1e-10:
                slope = (sum_xy - sum_x * sum_y / n) / denominator

        if slope > 0.05:
            direction = "rising"
        elif slope < -0.05:
            direction = "falling"
        else:
            direction = "stable"

        return TrendResult(
            axis=axis, field=field, window=window,
            values=values, mean=mean, variance=variance,
            slope=slope, direction=direction
        )

    def anomalies(self, axis: str, field: str, threshold: float = 0.3, window: int = 50) -> List[AnomalyResult]:
        """
        檢測異常值（與均值偏差超過 threshold）

        Args:
            axis: 軸名
            field: field 名
            threshold: 標準差倍數閾值
            window: 歷史窗口

        Returns:
            異常列表
        """
        values = self.get_field_series(axis, field, window)
        if len(values) < 3:
            return []

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)

        if std < 1e-10:
            return []

        key = f"{axis}.{field}"
        indices = self._index_by_field[key][-window:]

        anomalies = []
        for idx, value in zip(indices, values):
            z_score = abs(value - mean) / std
            if z_score > threshold:
                snapshot = self._snapshots[idx]
                anomalies.append(AnomalyResult(
                    index=idx,
                    timestamp=snapshot.get('timestamp', ''),
                    axis=axis,
                    field=field,
                    value=value,
                    expected=mean,
                    deviation=(value - mean) / std
                ))

        return anomalies

    def correlation(self, axis_a: str, field_a: str, axis_b: str, field_b: str, window: int = 50) -> CorrelationResult:
        """
        計算兩個 field 的皮爾遜相關係數

        Returns:
            CorrelationResult
        """
        values_a = self.get_field_series(axis_a, field_a, window)
        values_b = self.get_field_series(axis_b, field_b, window)

        if len(values_a) != len(values_b) or len(values_a) < 3:
            return CorrelationResult(
                axis_a=axis_a, field_a=field_a,
                axis_b=axis_b, field_b=field_b,
                correlation=0.0, strength="insufficient_data"
            )

        n = len(values_a)
        mean_a = sum(values_a) / n
        mean_b = sum(values_b) / n

        numerator = sum((a - mean_a) * (b - mean_b) for a, b in zip(values_a, values_b))
        denom_a = math.sqrt(sum((a - mean_a) ** 2 for a in values_a))
        denom_b = math.sqrt(sum((b - mean_b) ** 2 for b in values_b))

        if denom_a < 1e-10 or denom_b < 1e-10:
            corr = 0.0
        else:
            corr = numerator / (denom_a * denom_b)

        corr = max(-1.0, min(1.0, corr))

        abs_corr = abs(corr)
        if abs_corr > 0.7:
            strength = "strong"
        elif abs_corr > 0.4:
            strength = "moderate"
        elif abs_corr > 0.2:
            strength = "weak"
        else:
            strength = "negligible"

        return CorrelationResult(
            axis_a=axis_a, field_a=field_a,
            axis_b=axis_b, field_b=field_b,
            correlation=corr, strength=strength
        )

    def find_drift(
        self,
        axis: str,
        field: str,
        expected_value: float,
        drift_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        找到偏離預期值的快照（用於 θ negativity 檢測）

        不再需要 O(n) 遍歷，使用 field 索引直接定位。

        Args:
            axis: 軸名
            field: field 名
            expected_value: 預期值
            drift_threshold: 偏離閾值

        Returns:
            偏離快照列表
        """
        key = f"{axis}.{field}"
        if key not in self._index_by_field:
            return []

        indices = self._index_by_field[key]
        drift_snapshots = []

        for idx in indices:
            snapshot = self._snapshots[idx]
            if axis not in snapshot or not isinstance(snapshot[axis], dict):
                continue
            value = snapshot[axis].get(field)
            if value is None:
                continue

            deviation = abs(value - expected_value)
            if deviation > drift_threshold:
                drift_snapshots.append({
                    'index': idx,
                    'timestamp': snapshot.get('timestamp', ''),
                    'axis': axis,
                    'field': field,
                    'value': value,
                    'expected': expected_value,
                    'deviation': deviation
                })

        return drift_snapshots

    # === 統計 ===

    def size(self) -> int:
        """歷史快照數量"""
        return len(self._snapshots)

    def is_empty(self) -> bool:
        """是否為空"""
        return len(self._snapshots) == 0

    def clear(self) -> None:
        """清除所有歷史"""
        self._snapshots.clear()
        self._index_by_axis.clear()
        self._index_by_field.clear()

    # === 回調 ===

    def on_record(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """註冊記錄回調"""
        self._callbacks.append(callback)

    def __len__(self) -> int:
        """Execute the   len   operation."""
        return len(self._snapshots)

    def __repr__(self) -> str:
        return f"TemporalState(size={len(self._snapshots)}, max={self._max_size})"