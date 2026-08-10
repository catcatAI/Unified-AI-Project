# =============================================================================
# ANGELA-MATRIX: L1-L6[全层] αβγδεθζη [A] L2+
# =============================================================================
#
# 职责: 主幹線資料契約 — Envelope / IOPair / Mountable / TranslationRule
# 協定（§5.0.1 成對追蹤 + §4.2 可掛載資源統一介面）
# 維度: 跨所有維度（η 執行維度負責追蹤成對/孤兒）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸主幹線契約概念
#
# =============================================================================

"""主幹線資料契約定義（§5.0.1 / §4.2）。

- `Envelope`：主幹線內部統一的輸入/輸出信封，承載 `direction`（up/down）、
  `kind`、`correlation_id` 與 payload。
- `IOPair`：每個輸入輸出共享的成對追蹤結構（§5.0.1）。所有主幹線輸入輸出
  必須成對——每個輸入都必須（或在分析後能）對應一個輸出。
- `Mountable`：可掛載/釋放資源的統一介面（§4.2）。
- `TranslationRule`：轉譯器協定（§5.3）。
"""

from __future__ import annotations

import time
import uuid
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol, TypedDict, runtime_checkable


def _new_id() -> str:
    return uuid.uuid4().hex


class EnvelopeKind:
    """信封種類（kind）。"""

    CHAT = "chat"
    TOOL_CALL = "tool_call"
    EXTERNAL = "external"
    LEARNING = "learning"
    RESPONSE = "response"
    EVENT = "event"
    QUERY = "query"
    STATE_WRITE = "state_write"
    STATE_READ = "state_read"


@dataclass
class Envelope:
    """主幹線統一的輸入/輸出信封。

    Attributes:
        message_id: 訊息唯一識別 (uuid hex)。
        direction: "up"（下層→上層，回應/輸出）| "down"（上層→下層，請求/輸入）。
        kind: 信封種類（見 `EnvelopeKind`）。
        payload: 承載資料。
        correlation_id: 沿用 HSP/HTTP 既有追蹤 id（預設與 message_id 相同）。
        source: 來源元件名稱（例如 "router"、"chat_routes"）。
        target: 目標元件名稱（可選）。
        timestamp: 建立時間（time.time()）。
        meta: 額外中繼資料（可選）。
    """

    payload: Any
    kind: str = EnvelopeKind.QUERY
    direction: str = "down"
    message_id: str = field(default_factory=_new_id)
    correlation_id: Optional[str] = None
    source: str = ""
    target: str = ""
    timestamp: float = field(default_factory=lambda: time.time())
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.correlation_id is None:
            self.correlation_id = self.message_id

    @property
    def is_input(self) -> bool:
        """方向是否為輸入（down）。"""
        return self.direction == "down"

    @property
    def is_output(self) -> bool:
        """方向是否為輸出（up）。"""
        return self.direction == "up"

    def with_direction(self, direction: str) -> "Envelope":
        """複製信封並改方向（保留 correlation_id）。"""
        return Envelope(
            payload=self.payload,
            kind=self.kind,
            direction=direction,
            message_id=self.message_id,
            correlation_id=self.correlation_id,
            source=self.target if self.source else self.source,
            target=self.source if self.target else self.target,
            timestamp=self.timestamp,
            meta=dict(self.meta),
        )


# ---------------------------------------------------------------------------
# IOPair — 成對追蹤結構（§5.0.1）
# ---------------------------------------------------------------------------


class PairPattern:
    """成對模式（§5.0.1）。"""

    REQUEST_RESPONSE = "REQUEST_RESPONSE"
    REQUEST_ACK = "REQUEST_ACK"
    EVENT_HANDLER = "EVENT_HANDLER"
    BROADCAST_ACK = "BROADCAST_ACK"
    FIRE_AND_FORGET = "FIRE_AND_FORGET"
    PROACTIVE = "PROACTIVE"


class PairStatus:
    """配對狀態（§5.0.1）。"""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAIRED = "PAIRED"
    TIMEOUT = "TIMEOUT"
    ORPHAN = "ORPHAN"
    CONFLICT = "CONFLICT"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"

    TERMINAL = frozenset({PAIRED, TIMEOUT, ORPHAN, CONFLICT, ERROR, CANCELLED})
    FAILED = frozenset({TIMEOUT, ORPHAN, CONFLICT, ERROR, CANCELLED})


@dataclass
class IOPair:
    """輸入輸出配對追蹤結構（§5.0.1）。

    每個輸入輸出共享一個 `IOPair`：提交時建立（status=QUEUED），解析輸出後
    status=PAIRED；逾時未配對 → TIMEOUT/ORPHAN；重試 → QUEUED。
    """

    kind: str
    input_ref: Envelope
    pattern: str = PairPattern.REQUEST_RESPONSE
    pair_id: str = field(default_factory=_new_id)
    correlation_id: Optional[str] = None
    output_ref: Optional[Envelope] = None
    status: str = PairStatus.QUEUED
    schedule: Dict[str, Any] = field(default_factory=dict)
    analysis: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.correlation_id is None:
            self.correlation_id = self.input_ref.correlation_id or self.input_ref.message_id

    @property
    def is_pending(self) -> bool:
        """是否仍待配對。"""
        return self.status in (PairStatus.QUEUED, PairStatus.RUNNING)

    @property
    def is_terminal(self) -> bool:
        """是否已達終態。"""
        return self.status in PairStatus.TERMINAL

    def to_dict(self) -> Dict[str, Any]:
        """序列化為 dict（供 GlobalStateStore 持久化）。"""
        return {
            "pair_id": self.pair_id,
            "correlation_id": self.correlation_id,
            "kind": self.kind,
            "pattern": self.pattern,
            "status": self.status,
            "input_message_id": self.input_ref.message_id,
            "output_message_id": (self.output_ref.message_id if self.output_ref else None),
            "schedule": dict(self.schedule),
            "analysis": dict(self.analysis),
        }


# ---------------------------------------------------------------------------
# Mountable — 可掛載/釋放資源協定（§4.2）
# ---------------------------------------------------------------------------


@runtime_checkable
class Mountable(Protocol):
    """可掛載/釋放資源的統一介面（§4.2）。

    - `mount()`：從磁碟載入 → 記憶體，回傳是否成功。
    - `unmount()`：記憶體 → 磁碟 (flush)，釋放 RAM，回傳是否成功。
    - `is_mounted()`：目前是否已掛載。
    - `persistence_path()`：持久化路徑。
    """

    @abstractmethod
    def mount(self) -> bool:
        """從磁碟載入 → 記憶體。"""
        ...

    @abstractmethod
    def unmount(self) -> bool:
        """記憶體 → 磁碟 (flush)，釋放 RAM。"""
        ...

    @abstractmethod
    def is_mounted(self) -> bool:
        """目前是否已掛載。"""
        ...

    @abstractmethod
    def persistence_path(self) -> str:
        """持久化路徑。"""
        ...


@runtime_checkable
class MultimodalDictionary(Protocol):
    """多模態字典統一協定（§3.5 / 步驟 C2）。

    跨模態字典（ED3N DictionaryLayer / GARDEN VectorDictionary / 圖像 /
    音頻 / 物件 / 空間字典）的統一介面，讓主幹線 `register_dictionary` +
    `query_dictionary` 可以一致地查詢任何字典。

    - `modality()`：此字典服務的模態（"text"/"image"/"audio"/"object"/"space"）。
    - `register_entry(key, payload)`：寫入辭條（key 為唯一字面鍵）。
    - `encode(input)`：把輸入編碼為候選鍵（list[str]）。
    - `decode(keys)`：把鍵解碼回酬載（list[payload]）。
    - `query(input, top_k)`：相似性查詢，回傳 [(key, score, payload), ...]。
    - `save(path)` / `load(path)`：持久化。
    - `size()`：辭條數。

    實作者不需一次實作全部；介面存取全程以 getattr fallback 進行，
    缺方法時回傳 None / 空結果，不使主幹線崩潰。
    """

    def modality(self) -> str: ...
    def encode(self, input: Any, **kwargs: Any) -> list: ...
    def register_entry(self, key: str, payload: Any = None, **kwargs: Any) -> bool: ...
    def query(self, input: Any, top_k: int = 5, **kwargs: Any) -> list: ...


# ---------------------------------------------------------------------------
# TranslationRule — 轉譯器協定（§5.3）
# ---------------------------------------------------------------------------


class TranslationDirection:
    """轉譯方向。"""

    UP = "up"  # 下層 → 上層（例：LLM 原始輸出 → 主幹線信封）
    DOWN = "down"  # 上層 → 下層（例：主幹線信封 → LLM 請求格式）


@runtime_checkable
class TranslationRule(Protocol):
    """轉譯器協定（§5.3）。

    每個 translator 需實作：
    - `can_translate(source, target, direction) -> bool`：是否可處理此路徑。
    - `translate(data, direction, **kwargs) -> Any`：實際轉譯。
    - `name`：轉譯器名稱。
    """

    name: str

    @abstractmethod
    def can_translate(self, source: str, target: str, direction: str) -> bool:
        """是否可處理此轉譯路徑。"""
        ...

    @abstractmethod
    def translate(
        self, data: Any, direction: str = TranslationDirection.DOWN, **kwargs: Any
    ) -> Any:
        """執行實際轉譯。"""
        ...


class TranslatingEnvelope(TypedDict, total=False):
    """轉譯後的信封骨架（可選型別提示用）。"""

    payload: Any
    kind: str
    direction: str
    correlation_id: str
    source: str
    target: str
