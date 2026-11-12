# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [A] [L2]
# =============================================================================
"""The two step functions of one core: ``ai_step`` / ``al_step``（契約 §4）。

這裡只定義**介面與時間切段**，不含任何模型。原因：契約的 R1 是「同一份權重、
兩個入口」，而最容易走偏的地方是把 AL 週期做成第二個模型或第二份狀態。把介面
釘在這裡，adapter（GRU／SNN／SSM）就只能是同一個 recurrence 的不同實作。

時間切段（契約 §4.2）刻意只有一個實作：``dt`` 一律切成 **≤ max_chunk_s** 的等長
段。理由不是精度，而是可比較性——如果每個 adapter 自己決定怎麼切，T5 的
「同一個 dt、不同呼叫方式」就量不到同一個東西。

注意：切段讓 `al_step(dt1)` 後接 `al_step(dt2)` 對非同步切分只是**近似**
`al_step(dt1+dt2)`。這不是缺陷，是 GRU 這類非線性遞歸的性質；AL ladder r1 的
精確半群是閉式積分器量到的，不能拿來要求一個學出來的 recurrence。半群因此是
**量測項**，不是宣稱項。
"""

from __future__ import annotations

import math
from typing import Any, Dict, Protocol, Sequence, Tuple, runtime_checkable

DEFAULT_MAX_CHUNK_S = 60.0


def chunk_dt(dt_s: float, max_chunk_s: float = DEFAULT_MAX_CHUNK_S) -> Tuple[float, ...]:
    """把 ``dt_s`` 切成等長的 ``n`` 段，每段 ≤ ``max_chunk_s``。

    - ``dt_s <= 0`` → ``()``：**零時間是恆等**，呼叫端不得因此改變 state。
    - 非有限值／非正的上限 → ``ValueError``（不靜默回 0）。
    """
    if max_chunk_s <= 0 or not math.isfinite(max_chunk_s):
        raise ValueError(f"max_chunk_s must be finite and > 0, got {max_chunk_s!r}")
    if not isinstance(dt_s, (int, float)) or isinstance(dt_s, bool):
        raise ValueError(f"dt_s must be a number, got {type(dt_s).__name__}")
    if not math.isfinite(dt_s):
        raise ValueError(f"dt_s must be finite, got {dt_s!r}")
    if dt_s <= 0:
        return ()
    chunks = math.ceil(dt_s / max_chunk_s)
    step = dt_s / chunks
    return tuple(step for _ in range(chunks))


@runtime_checkable
class CoreStep(Protocol):
    """同一個模型的兩個入口；實作者**必須**共用同一組權重與同一個 state。"""

    def init_state(self, batch_size: int) -> Any:
        """建立一個新的 state（只在 session 建立時呼叫；契約 R5）。"""

    def ai_step(self, tokens: Any, state: Any) -> Tuple[Any, Any]:
        """有外部輸入：回傳 ``(logits, state)``。"""

    def al_step(self, dt_s: float, state: Any) -> Any:
        """沒有外部 token，只有時間：回傳更新後的 state。"""

    def weights_hash(self) -> str:
        """``sha256:<hex>``；T6 用它證明兩個週期是同一份權重。"""


_REGISTRY: Dict[str, Any] = {}


def register_core_step(name: str, factory: Any) -> None:
    if not name:
        raise ValueError("name must be non-empty")
    _REGISTRY[name] = factory


def get_core_step(name: str) -> Any:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"unknown core step {name!r}; registered: {sorted(_REGISTRY)}") from exc


def registered_core_steps() -> Sequence[str]:
    return tuple(sorted(_REGISTRY))


__all__ = [
    "CoreStep",
    "DEFAULT_MAX_CHUNK_S",
    "chunk_dt",
    "get_core_step",
    "register_core_step",
    "registered_core_steps",
]
