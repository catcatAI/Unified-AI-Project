"""
State Matrix Adapter — Phase 7 整合適配器
==========================================

雙軌整合：
  - 軌 A（新）：使用 refactored 模組（Axis, TemporalState, InfluenceSpace, AllocationPolicy）
  - 軌 B（舊）：保持現有 StateMatrix4D 所有接口和行為不變

目標：在不破壞任何現有代碼的情況下，讓新模組可以運作。
      當新模組成熟後，逐步遷移。

使用方式:
    from core.engine.state_matrix_adapter import StateMatrixAdapter

    sm = StateMatrixAdapter()

    # 舊 API（保持不變）
    sm.update_alpha(focus=0.8)
    sm.update_beta(curiosity=0.6)
    sm.compute_influences()

    # 新 API（使用 refactored 模組）
    sm.temporal.trend('alpha', 'focus', window=30)
    sm.influence_space.compute('alpha', 'beta')
    sm.allocation_decide([0.1]*32, 'test')

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
