# =============================================================================
# ANGELA-MATRIX: L1-L6[全层] αβγδεθζη [A] L2+
# =============================================================================
#
# 職責: Stability Core — IOPair + PairScheduler + PairState 成對排程
#       （§5.0 成對性不變式：∀ 輸入 ∃ 輸出 ∨ 可計算的潛在輸出）
# 維度: η 執行維度追蹤成對/孤兒/衝突；ζ 連通維度跨模組一致
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸成對排程概念
#
# =============================================================================

"""成對排程 / 配對狀態（§5.0 Stability Core）。

合併現有 `core/waiting_scheduler.py` 的 slot 分配與 timeout，並在其上加入
**成對追蹤**：任務不再「submit 完即忘」，而是 `submit(輸入) → resolve(輸出)`，
中間狀態全程可查。

排程保證（§5.0.2）：
- **先入先配**：輸出永不早於其輸入被處理（避免時序反轉）。
- **同對單執行**：同一 `pair_id` 不會被並發處理兩次（消除寫衝突）。
- **逾時診斷**：超過 `deadline` 未配對 → 標記 `TIMEOUT`/`ORPHAN`，可重試或診斷，
  絕不靜默丟棄。

公開介面（§5.0.2 / §5.0.3）：
- `submit(input_envelope, timeout=8.0) -> pair_id`
- `resolve(pair_id, output_envelope)` → PAIRED
- `cancel(pair_id)` → CANCELLED
- `retry(pair_id)` → QUEUED
- `status(pair_id)` / `pending()` / `orphans()` / `by_kind(kind)`
- 配對日誌以 `correlation_id` 為索引，複用 `GlobalStateStore`（domain `io_pairs`）。
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

from core.backbone.contracts import (
    Envelope,
    IOPair,
    PairPattern,
    PairStatus,
)

# 引入僅供 TYPE_CHECKING 的 WaitingScheduler 型別註釋
try:  # pragma: no cover - 型別註釋路徑
    from core.waiting_scheduler import WaitingScheduler
except ImportError:  # pragma: no cover
    WaitingScheduler = Any

_IO_PAIRS_DOMAIN = "io_pairs"


class PairConflictError(RuntimeError):
    """同對重複執行 / 非法狀態轉換衝突。"""


class PairScheduler:
    """成對排程器（§5.0.2）— slot 排程 + 成對追蹤。

    合併 `WaitingScheduler` 的 slot 分配與 timeout，並以 `_pairs` dict 追蹤
    每個 `pair_id` 的完整生命週期（QUEUED→RUNNING→PAIRED/ERROR/...）。

    執行模型：
    - `submit()` 建立 IOPair（QUEUED）並登記 deadline。
    - `resolve()` 以輸出信封配對 → PAIRED。
    - `sweep()` 由呼叫方定時觸發（或 async task）掃描逾時未配對對 → ORPHAN。
    - 單執行保證：同一 pair_id 的處理任務以 lock 互斥；重複 submit 相同
      correlation_id 且未完成 → CONFLICT（除非 `allow_duplicate=True`）。
    """

    def __init__(
        self,
        state_store: Any = None,
        max_wait_seconds: float = 8.0,
        default_timeout: float = 8.0,
    ) -> None:
        self._pairs: Dict[str, IOPair] = {}
        self._lock = threading.RLock()
        self._pair_locks: Dict[str, threading.Lock] = {}
        self._max_wait_seconds = max_wait_seconds
        self.default_timeout = default_timeout
        self._state_store = state_store
        self._deadline = time.monotonic() + max_wait_seconds

    # ------------------------------------------------------------------
    # 內部輔助
    # ------------------------------------------------------------------
    def _get_lock(self, pair_id: str) -> threading.Lock:
        with self._lock:
            return self._pair_locks.setdefault(pair_id, threading.Lock())

    def _record_to_store(self, pair: IOPair) -> None:
        if self._state_store is not None:
            try:
                current = dict(self._state_store.get_state(_IO_PAIRS_DOMAIN) or {})
                current[pair.pair_id] = pair.to_dict()
                self._state_store.update_state(_IO_PAIRS_DOMAIN, current, notify=False)
            except Exception as e:
                logger.debug(f"Pair store persist failed for {pair.pair_id}: {e}", exc_info=True)

    def _transition(self, pair: IOPair, new_status: str) -> None:
        allowed = {
            PairStatus.QUEUED: {
                PairStatus.RUNNING,
                PairStatus.PAIRED,
                PairStatus.ERROR,
                PairStatus.CANCELLED,
                PairStatus.ORPHAN,
                PairStatus.TIMEOUT,
            },
            PairStatus.RUNNING: {
                PairStatus.PAIRED,
                PairStatus.ERROR,
                PairStatus.TIMEOUT,
                PairStatus.ORPHAN,
                PairStatus.CANCELLED,
            },
            PairStatus.PAIRED: set(),
            PairStatus.TIMEOUT: {PairStatus.QUEUED},
            PairStatus.ORPHAN: {PairStatus.QUEUED, PairStatus.CANCELLED},
            PairStatus.ERROR: {PairStatus.QUEUED},
            PairStatus.CANCELLED: {PairStatus.QUEUED},
            PairStatus.CONFLICT: set(),
        }
        if new_status not in allowed.get(pair.status, set()):
            raise PairConflictError(
                f"Illegal pair transition {pair.status} -> {new_status} for {pair.pair_id}"
            )
        pair.status = new_status

    # ------------------------------------------------------------------
    # 公開 API（§5.0.2）
    # ------------------------------------------------------------------
    def submit(
        self,
        input_envelope: Envelope,
        timeout: Optional[float] = None,
        kind: Optional[str] = None,
        pattern: str = PairPattern.REQUEST_RESPONSE,
        allow_duplicate: bool = False,
    ) -> str:
        """提交輸入信封，建立 IOPair（QUEUED），回傳 pair_id。

        若相同 `correlation_id` 已存在且未達終態 → CONFLICT（除非 allow_duplicate）。
        """
        correlation_id = input_envelope.correlation_id or input_envelope.message_id
        timeout = timeout or self.default_timeout
        with self._lock:
            for existing in self._pairs.values():
                if existing.correlation_id == correlation_id and existing.is_pending:
                    if not allow_duplicate:
                        raise PairConflictError(
                            f"Duplicate pending pair for correlation_id={correlation_id}: "
                            f"{existing.pair_id}"
                        )
            pair = IOPair(
                kind=kind or input_envelope.kind,
                input_ref=input_envelope,
                pattern=pattern,
                correlation_id=correlation_id,
            )
            pair.schedule["submitted_at"] = time.time()
            pair.schedule["deadline"] = time.monotonic() + timeout
            pair.schedule["timeout"] = timeout
            pair.schedule["retries"] = 0
            pair.schedule["slot"] = int(time.time() * 1000) % max(1, self._max_wait_seconds)
            self._pairs[pair.pair_id] = pair
            self._record_to_store(pair)
            # Auto-prune if over limit to prevent unbounded growth
            if len(self._pairs) > 2000:
                try:
                    self.prune(max_pairs=2000)
                except Exception as e:
                    logger.debug(f"Auto-prune failed: {e}", exc_info=True)
            return pair.pair_id

    def resolve(self, pair_id: str, output_envelope: Envelope) -> None:
        """以輸出信封配對 → PAIRED。"""
        with self._lock:
            pair = self._pairs.get(pair_id)
            if pair is None:
                raise KeyError(f"No such pair_id: {pair_id}")
            if pair.status == PairStatus.PAIRED:
                raise PairConflictError(f"Pair {pair_id} already PAIRED")
            pair.output_ref = output_envelope
            self._transition(pair, PairStatus.PAIRED)
            pair.schedule["resolved_at"] = time.time()
            self._record_to_store(pair)

    def start(self, pair_id: str) -> None:
        """標記為 RUNNING（處理中）。"""
        with self._lock:
            pair = self._pairs.get(pair_id)
            if pair is None:
                raise KeyError(f"No such pair_id: {pair_id}")
            self._transition(pair, PairStatus.RUNNING)
            pair.schedule["started_at"] = time.time()

    def fail(self, pair_id: str, reason: str = "") -> None:
        """標記為 ERROR（可重試）。"""
        with self._lock:
            pair = self._pairs.get(pair_id)
            if pair is None:
                raise KeyError(f"No such pair_id: {pair_id}")
            self._transition(pair, PairStatus.ERROR)
            pair.analysis["error"] = reason
            pair.schedule["failed_at"] = time.time()
            self._record_to_store(pair)

    def cancel(self, pair_id: str) -> None:
        """取消 → CANCELLED。"""
        with self._lock:
            pair = self._pairs.get(pair_id)
            if pair is None:
                raise KeyError(f"No such pair_id: {pair_id}")
            if not pair.is_terminal:
                self._transition(pair, PairStatus.CANCELLED)
                pair.schedule["cancelled_at"] = time.time()
                self._record_to_store(pair)

    def retry(self, pair_id: str, timeout: Optional[float] = None) -> None:
        """重排 → QUEUED，retries+1。"""
        with self._lock:
            pair = self._pairs.get(pair_id)
            if pair is None:
                raise KeyError(f"No such pair_id: {pair_id}")
            if pair.status not in (
                PairStatus.ERROR,
                PairStatus.TIMEOUT,
                PairStatus.ORPHAN,
                PairStatus.CANCELLED,
            ):
                raise PairConflictError(f"Pair {pair_id} cannot retry from {pair.status}")
            self._transition(pair, PairStatus.QUEUED)
            pair.schedule["retries"] = pair.schedule.get("retries", 0) + 1
            pair.schedule["deadline"] = time.monotonic() + (
                timeout or pair.schedule.get("timeout", self.default_timeout)
            )
            pair.output_ref = None
            self._record_to_store(pair)

    def adjust_deadline(self, pair_id: str, timeout: float) -> None:
        """調整 deadline。"""
        with self._lock:
            pair = self._pairs.get(pair_id)
            if pair is None:
                raise KeyError(f"No such pair_id: {pair_id}")
            pair.schedule["deadline"] = time.monotonic() + timeout
            pair.schedule["timeout"] = timeout

    # ------------------------------------------------------------------
    # 查詢（§5.0.3 PairState）
    # ------------------------------------------------------------------
    def status(self, pair_id: str) -> Optional[Dict[str, Any]]:
        pair = self._pairs.get(pair_id)
        return pair.to_dict() if pair else None

    def get_pair(self, pair_id: str) -> Optional[IOPair]:
        return self._pairs.get(pair_id)

    def pending(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._pairs.values() if p.is_pending]

    def orphans(self) -> List[Dict[str, Any]]:
        """逾時未配對的對（ORPHAN 或逾時 QUEUED/RUNNING）。"""
        now = time.monotonic()
        out: List[Dict[str, Any]] = []
        for p in self._pairs.values():
            deadline = p.schedule.get("deadline", 0.0)
            if p.is_pending and deadline and now > deadline:
                out.append(p.to_dict())
            elif p.status == PairStatus.ORPHAN:
                out.append(p.to_dict())
        return out

    def by_kind(self, kind: str) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._pairs.values() if p.kind == kind]

    def all(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._pairs.values()]

    def sweep(self) -> List[str]:
        """掃描並將逾時未配對的對標記為 ORPHAN；回傳標記者 pair_id 清單。"""
        now = time.monotonic()
        swept: List[str] = []
        with self._lock:
            for pair_id, pair in list(self._pairs.items()):
                deadline = pair.schedule.get("deadline", 0.0)
                if pair.is_pending and deadline and now > deadline:
                    self._transition(pair, PairStatus.ORPHAN)
                    pair.schedule["orphaned_at"] = time.time()
                    self._record_to_store(pair)
                    swept.append(pair_id)
        return swept

    def run_pair_async(
        self,
        pair_id: str,
        handler: Callable[[Envelope], Any],
    ) -> None:
        """以背景任務執行成對處理（同對單執行 + RUNNING 標記）。

        設計上以 thread 執行；handler 內部可自行 async。此處以 lock 保證
        同一 pair_id 不會被並發處理兩次。
        """
        lock = self._get_lock(pair_id)
        if not lock.acquire(blocking=False):
            raise PairConflictError(f"Pair {pair_id} already being processed")

        def _run() -> None:
            try:
                self.start(pair_id)
                pair = self._pairs.get(pair_id)
                if pair is None:
                    return
                result = handler(pair.input_ref)
                output = (
                    result
                    if isinstance(result, Envelope)
                    else Envelope(
                        payload=result,
                        kind=pair.kind,
                        direction="up",
                        correlation_id=pair.correlation_id,
                        source="pairs",
                    )
                )
                self.resolve(pair_id, output)
            except Exception as exc:  # noqa: BLE001 - 成對錯誤必須追蹤，不靜默
                try:
                    self.fail(pair_id, reason=str(exc))
                except Exception as e2:
                    logger.debug(f"Pair fail fallback failed for {pair_id}: {e2}", exc_info=True)
            finally:
                lock.release()

        thread = threading.Thread(target=_run, daemon=True, name=f"pair-{pair_id[:8]}")
        thread.start()

    # ------------------------------------------------------------------
    # 清理
    # ------------------------------------------------------------------
    def prune(self, max_pairs: int = 2000) -> int:
        """清理超過上限的終態對（舊先清）。回傳清除數。"""
        with self._lock:
            terminal = [p for p in self._pairs.values() if p.is_terminal]
            terminal.sort(key=lambda p: p.schedule.get("submitted_at", 0.0))
            overflow = len(self._pairs) - max_pairs
            removed = 0
            for pair in terminal[: max(0, overflow)]:
                self._pairs.pop(pair.pair_id, None)
                self._pair_locks.pop(pair.pair_id, None)
                removed += 1
            return removed

    def clear(self) -> None:
        with self._lock:
            self._pairs.clear()
            self._pair_locks.clear()


class PairState:
    """配對狀態查詢門面（§5.0.3）— 能查排程與處理狀態並管理。

    - 查詢：`status(pair_id)`、`pending()`、`orphans()`、`by_kind(kind)`。
    - 管理：`retry` / `cancel` / `adjust_deadline`。
    - 儲存：以 `correlation_id` 為索引的配對日誌（可經 `to_log()` 導出）。
    """

    def __init__(self, scheduler: PairScheduler) -> None:
        self._scheduler = scheduler

    # 查詢
    def status(self, pair_id: str) -> Optional[Dict[str, Any]]:
        return self._scheduler.status(pair_id)

    def pending(self) -> List[Dict[str, Any]]:
        return self._scheduler.pending()

    def orphans(self) -> List[Dict[str, Any]]:
        return self._scheduler.orphans()

    def by_kind(self, kind: str) -> List[Dict[str, Any]]:
        return self._scheduler.by_kind(kind)

    # 管理
    def retry(self, pair_id: str) -> None:
        self._scheduler.retry(pair_id)

    def cancel(self, pair_id: str) -> None:
        self._scheduler.cancel(pair_id)

    def adjust_deadline(self, pair_id: str, timeout: float) -> None:
        self._scheduler.adjust_deadline(pair_id, timeout)

    def to_log(self) -> List[Dict[str, Any]]:
        """導出配對日誌（以 correlation_id 為索引欄位）。"""
        return sorted(self._scheduler.all(), key=lambda d: d["schedule"].get("submitted_at", 0.0))


def get_pair_scheduler(state_store: Any = None) -> PairScheduler:
    """取得進程級成對排程器單例（延遲建立）。"""
    global _pair_scheduler_instance
    if _pair_scheduler_instance is None:
        _pair_scheduler_instance = PairScheduler(state_store=state_store)
    return _pair_scheduler_instance


_pair_scheduler_instance: Optional[PairScheduler] = None


def reset_pair_scheduler() -> None:
    """測試隔離用：重置單例。"""
    global _pair_scheduler_instance
    _pair_scheduler_instance = None
