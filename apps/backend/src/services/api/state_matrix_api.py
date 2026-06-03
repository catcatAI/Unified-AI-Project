"""
State Matrix FastAPI Router
==========================

為 StateMatrixAdapter 提供 HTTP API 接口。

端點：
  GET  /state/summary           — 完整狀態報告
  GET  /state/axis/{name}        — 單個軸的 values
  POST /state/axis/{name}/update — 更新軸值
  GET  /state/gradient           — 吸引子場梯度
  POST /state/navigate           — 沿梯度導航
  GET  /state/temporal/trend     — 時間趨勢查詢
  GET  /state/temporal/anomalies — 異常檢測
  POST /state/port/register      — 註冊端口
  POST /state/port/unregister    — 註銷端口
  GET  /state/port/list          — 列舉端口
  POST /state/ripple             — 應用漣漪
  GET  /state/allocation          — 分配決策
  GET  /state/negativity         — θ 自糾狀態
  POST /state/save                — 保存狀態
  POST /state/load                — 恢復狀態

使用方式:
    from api.router import router as state_matrix_router
    app.include_router(state_matrix_router, prefix="/api/v1")

Author: Angela AI v6.2.1
"""

from __future__ import annotations
