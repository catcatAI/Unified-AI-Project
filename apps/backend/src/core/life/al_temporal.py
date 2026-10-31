# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [A] [L0-L11]
# =============================================================================
"""AL 側時間序列觀測緩衝（三核心計畫 Phase 3 item 2）。

此 singleton 此前住在 ``api/routes/chat_routes.py``（API 層全域變數），
對外的唯一讀者是 causal 的 Granger 收集 —— 即「時間序列觀測」這份 AL
資產寄宿在組裝層。移入 AL 側後介面收斂成兩個（契約 §9「讀走快照，寫走
事件」的時間序列面向）：

- ``get_temporal()``：唯讀查詢介面 —— 拿到 :class:`TemporalState` 物件
  只能拿來查詢或餵給下游引擎（讀取發生在呼叫者側）。
- ``record_interaction()``：受控寫入口 —— 寫只經此處，且**只收統計摘要**
  （§8：對話原始內容不進 AL；鍵名 ``engagement_ratio`` 為歷史名，值是
  長度比）。

與 ``al_state`` 的事件緩衝（``submit_event``，100 筆 deque）分工：那是
事件流、v1 不持久化；這裡是等寬時間序列（``max_size=200``），供
``causal.ingest_temporal_state()`` 做 Granger 因果。core/life 出站只到
``core.state``（同為 core 側），不違反 I8。
"""

from __future__ import annotations

import threading
from typing import Optional

from core.state.temporal import TemporalState

_TEMPORAL_MAX_SIZE = 200

_bridge: Optional[TemporalState] = None
_bridge_lock = threading.Lock()


def get_temporal() -> TemporalState:
    """唯讀查詢介面：拿時間序列緩衝（process-wide singleton）。

    以 double-checked lock 保證並發下只建一個實例（API worker 多執行緒）。
    """
    global _bridge
    if _bridge is None:
        with _bridge_lock:
            if _bridge is None:
                _bridge = TemporalState(max_size=_TEMPORAL_MAX_SIZE)
    return _bridge


def record_interaction(
    msg_length: float, resp_length: float, engagement_ratio: float
) -> TemporalState:
    """受控寫入口：記錄一筆互動統計觀測，回傳緩衝本體。

    回傳本體是為了讓呼叫者（組裝層）決定何時把序列餵給 causal 引擎 ——
    讀取策略留在使用側，寫的形狀收斂在這裡。
    """
    ts = get_temporal()
    ts.record(
        {
            "interaction": {
                "msg_length": msg_length,
                "resp_length": resp_length,
                # 歷史鍵名；值為 resp/msg 長度比（Granger 序列沿用此鍵）
                "engagement_ratio": engagement_ratio,
            },
        }
    )
    return ts
