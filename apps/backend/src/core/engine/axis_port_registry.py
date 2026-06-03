"""
Axis Port Registry — 6D 軸端口路由系統 Phase 1
===============================================

讓 θ 元認知軸作為「路由大腦」，端口只需聲明存在。

核心概念：
- Port: 數據進出的抽象端點（IN/OUT/IO）
- PortRegistry: 端口註冊表，管理所有端口與軸的綁定
- θ 軸根據語義相似度自動路由

使用方式:
    from core.engine.axis_port_registry import PortRegistry, PortDirection, Port

    registry = PortRegistry(state_matrix_adapter)
    registry.register(name="llm_out", direction=PortDirection.IN,
                      semantic_vector=[...], tags=["llm"])

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
