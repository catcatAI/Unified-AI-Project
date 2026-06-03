"""
Resonance Engine — 語義共振統一引擎
====================================

所有軸的相似度計算通過這裡：
- 計算向量與軸的共振度
- 找最佳軸 / 複合軸
- 計算跨軸不確定性（entropy）

使用方式:
    from core.allocation.resonance import ResonanceEngine

    engine = ResonanceEngine(axes=[alpha, beta, gamma, delta, epsilon])
    resonance = engine.compute_resonance(vector, target=alpha)
    best_axis = engine.find_best_axis(vector)

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
