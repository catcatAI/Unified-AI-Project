"""
Core State Module — 狀態系統重構 Phase 1-4
==========================================

Phase 1: Axis 抽象
  - axis_field.py: AxisField 定義 + AxisFieldRegistry 全局註冊表
  - axis.py: Axis 軸對象（typed field 存取 + 座標 + 統計）
  - temporal.py: TemporalState（歷史查詢引擎）

Phase 2: 決策重構
  - allocation/resonance.py: ResonanceEngine — 語義共振統一引擎
  - allocation/policy.py: AllocationPolicy — 規則化分配策略
  - allocation/negativity.py: NegativityDetector — θ 自糾系統

Phase 4: 配置外部化
  - config_loader.py: StateConfig — 從 YAML 載入所有配置

Author: Angela AI v6.2
Version: 6.2.1
"""

from core.state.axis import Axis
from core.state.axis_field import AxisField, AxisFieldRegistry

try:
    from core.state.temporal import (
        AnomalyResult,
        CorrelationResult,
        SnapshotQuery,
        TemporalState,
        TrendResult,
    )
except ImportError:
    TemporalState = SnapshotQuery = TrendResult = AnomalyResult = CorrelationResult = None

try:
    from core.state.config_loader import AxisConfig, AxisFieldConfig, StateConfig, StateMatrixConfig
except ImportError:
    StateConfig = StateMatrixConfig = AxisConfig = AxisFieldConfig = None

__all__ = [
    "AxisField",
    "AxisFieldRegistry",
    "Axis",
    "TemporalState",
    "SnapshotQuery",
    "TrendResult",
    "AnomalyResult",
    "CorrelationResult",
    "StateConfig",
    "StateMatrixConfig",
    "AxisConfig",
    "AxisFieldConfig",
]