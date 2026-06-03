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
from typing import Dict, List, Optional, Tuple, Any, Callable