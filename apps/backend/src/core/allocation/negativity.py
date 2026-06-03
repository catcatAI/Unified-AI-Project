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
from typing import Dict, List, Optional, Any, Callable