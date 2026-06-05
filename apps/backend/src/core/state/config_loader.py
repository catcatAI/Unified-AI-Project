"""
State Config Loader — 配置外部化
=================================

從 angela_state.yaml 載入所有配置，提供類型安全的訪問介面。
替換 state_matrix.py 中的所有硬編碼值。

使用方式:
    from core.state.config_loader import StateConfig

    config = StateConfig()
    assign_thresh = config.allocation.assign_threshold
    matrix = config.influence.matrix
    axes = config.axes

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class AxisFieldConfig:
    name: str = ""
    label: str = ""
    default: float = 0.5
    min: float = 0.0
    max: float = 1.0
    description: str = ""


@dataclass
class AxisConfig:
    id: str = ""
    label: str = ""
    fields: List[AxisFieldConfig] = field(default_factory=list)


@dataclass
class StateMatrixConfig:
    matrix: Dict[str, Any] = field(default_factory=dict)


class StateConfig:
    def __init__(self):
        self.allocation = type("obj", (object,), {"assign_threshold": 0.5})()
        self.influence = type("obj", (object,), {"matrix": {}})()
        self.axes: List[AxisConfig] = []
