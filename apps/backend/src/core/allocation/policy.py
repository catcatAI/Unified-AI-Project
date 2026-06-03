"""
Allocation Policy — 分配策略系統
=================================

將 meta_allocate 的 if-elif 鏈重構為規則化 stages。
每個 stage 是獨立的條件評估器，結果可組合、可測試、可配置。

使用方式:
    from core.allocation.policy import AllocationPolicy, AllocationAction

    policy = AllocationPolicy()
    decision = policy.decide(context=AllocationContext(
        vector=input_vector,
        label='user_query',
        entropy=0.3,
        novelty=0.4,
        active_dims=3,
    ))

    if decision.action == AllocationAction.ASSIGN:
        axis = decision.target

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple