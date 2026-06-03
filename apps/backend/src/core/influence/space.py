"""
Influence Space — 影響規則抽象 Phase 6
========================================

將硬編碼的影響矩陣重構為可配置、可組合的規則系統。
支援：
- GravityRule（逆平方定律）
- EntropyRule（熵驅動）
- MemoryRule（記憶衰減）
- 規則衝突解決策略

使用方式:
    from core.influence.space import InfluenceSpace, GravityRule

    space = InfluenceSpace()
    space.rules.add(GravityRule())

    influence = space.compute(source=alpha, target=beta)
    computed = space.compute_all(matrix)  # 對所有軸對

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
