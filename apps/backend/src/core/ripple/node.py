"""
Ripple System — 漣漪對象化 Phase 5
===================================

將 MathRippleEngine 的漣漪應用從串列 if 重構為策略模式。
每個軸有自己的 RippleApplicator，級聯策略可插拔。

使用方式:
    from core.ripple.node import RippleNode, AxisRippleApplicator

    # 創建漣漪節點
    node = RippleNode(operator=MathOp.DIV, result=10.0)
    node.apply(epsilon=1.0, alpha=0.3, beta=0.2, gamma=0.1)

    # 級聯傳播
    cascade = LinearCascadeStrategy(decay=0.72)
    ripples = node.cascade(targets=['alpha', 'beta', 'gamma'], strategy=cascade)

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Protocol, Callable