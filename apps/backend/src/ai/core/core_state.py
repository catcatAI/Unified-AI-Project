# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [A] [L2]
# =============================================================================
"""核心狀態的 schema、完整性與載入契約（P0；契約 §3、§9）。

這支模組只做「一個 state 物件怎麼被描述、存、驗、載」，**不做** `ai_step`／
`al_step`（那是 P1），也不接生產（那是 P4）。存在的理由是先把三件會靜默出錯的
事情變成機械檢查：

1. **拒絕，而不是重置**：`schema_version`／`weights_hash`／`checksum` 不符時
   一律拋錯。歷史問題是「載入失敗 → 當成新 session」，於是狀態延續的宣稱在重啟
   後悄悄失效，而分數照樣算得出來。
2. **不碰 pickle**：張量走 `.npz`（`allow_pickle=False`）；meta 走 JSON。載入
   任意物件是第二種「以為有狀態、其實只是讀了一個檔案」。
3. **大小有上限**：單一 session ≤ 10 MB。狀態若無界增長，它遲早會變成另一份
   context（契約 §1 的 memory／state／context 分界）。

`derived`（顯示用情緒／強度／漂移）**不落盤**，與 `core/life/al_state.py` 的
I3 一致；它們是由 state 投影出來的讀數，不是本體。

寫入是「先張量、後 meta」，且 checksum 同時涵蓋兩者：中途崩潰會留下 checksum
不符的殘檔 → 載入拒絕，不會讀到半套狀態。這裡沒有跨進程鎖；per-session 鎖與
樂觀鎖在 P1 與 `ai_step` 一起做（契約 R3）。
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import numpy as np

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1
MAX_STATE_BYTES = 10 * 1024 * 1024
META_FILENAME = "meta.json"
TENSORS_FILENAME = "tensors.npz"
MODEL_KINDS = frozenset({"gru", "slots", "snn", "ssm", "turnstore", "tokencache"})
WEIGHTS_HASH_PREFIX = "sha256:"

_META_REQUIRED = (
    "schema_version",
    "model_kind",
    "weights_hash",
    "user_id",
    "session_id",
    "born_at",
    "last_update",
    "ticks",
    "last_dt_s",
    "state_version",
    "tensors",
    "checksum",
)


class CoreStateError(Exception):
    """核心狀態的基底錯誤：載入失敗時呼叫端必須處理，不得吞掉。"""


class CoreStateInvalid(CoreStateError):
    """建立狀態時傳入的值不合法（程式錯誤，不是檔案損壞）。"""


class CoreStateCorrupt(CoreStateError):
    """檔案缺失、內容不完整或 checksum 不符（含寫入中崩潰的殘檔）。"""


class CoreStateVersionMismatch(CoreStateError):
    """schema／weights 與預期不符；需要顯式 migration，不得當成新狀態。"""


class CoreStateTooLarge(CoreStateError):
    """單一 session 超過大小上限。"""


def hash_weights_bytes(payload: bytes) -> str:
    """回傳 `sha256:<hex>`；權重雜湊的唯一格式。"""
    return WEIGHTS_HASH_PREFIX + hashlib.sha256(payload).hexdigest()


def hash_weights_file(path: os.PathLike[str] | str) -> str:
    """以檔案內容算權重雜湊（不載入模型）。"""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return WEIGHTS_HASH_PREFIX + digest.hexdigest()


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _digest(meta_without_checksum: Mapping[str, Any], tensors_bytes: bytes) -> str:
    """checksum 涵蓋「meta 的 canonical 形式＋張量位元組」。"""
    digest = hashlib.sha256()
    digest.update(_canonical_json(meta_without_checksum))
    digest.update(b"\x00")
    digest.update(tensors_bytes)
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CoreStateCorrupt(message)


def _validate_weights_hash(value: Any) -> str:
    if not isinstance(value, str):
        raise CoreStateInvalid("weights_hash must be a string")
    if not (value.startswith(WEIGHTS_HASH_PREFIX) and len(value) > len(WEIGHTS_HASH_PREFIX)):
        raise CoreStateInvalid("weights_hash must be 'sha256:<hex>'")
    return value


def _validate_meta_types(meta: Mapping[str, Any]) -> None:
    _require(isinstance(meta.get("model_kind"), str), "model_kind must be a string")
    _require(
        meta["model_kind"] in MODEL_KINDS,
        f"model_kind must be one of {sorted(MODEL_KINDS)}",
    )
    for key in ("user_id", "session_id", "born_at", "last_update"):
        _require(isinstance(meta.get(key), str), f"{key} must be a string")
    _require(isinstance(meta.get("schema_version"), int), "schema_version must be an int")
    _require(isinstance(meta.get("ticks"), int), "ticks must be an int")
    _require(meta["ticks"] >= 0, "ticks must be >= 0")
    _require(isinstance(meta.get("state_version"), int), "state_version must be an int")
    _require(meta["state_version"] >= 0, "state_version must be >= 0")
    _require(
        isinstance(meta.get("last_dt_s"), (int, float))
        and not isinstance(meta.get("last_dt_s"), bool),
        "last_dt_s must be a number",
    )
    _require(
        float(meta["last_dt_s"]) >= 0.0 and np.isfinite(meta["last_dt_s"]),
        "last_dt_s must be finite and >= 0",
    )
    _require(isinstance(meta.get("tensors"), list), "tensors must be a list of names")


@dataclass
class CoreState:
    """同一個 core 的狀態：固定大小的張量＋慢變量（契約 §3.2）。

    建構請走 :meth:`create`（新 session 的**顯式**重置）或 :meth:`load`；
    這個 dataclass 本身不驗證，驗證在兩個入口。
    """

    schema_version: int
    model_kind: str
    weights_hash: str
    user_id: str
    session_id: str
    born_at: str
    last_update: str
    ticks: int = 0
    last_dt_s: float = 0.0
    state_version: int = 0
    tensors: Dict[str, np.ndarray] = field(default_factory=dict)

    # -- 建立 ---------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        model_kind: str,
        weights_hash: str,
        user_id: str,
        session_id: str,
        tensors: Optional[Mapping[str, np.ndarray]] = None,
        now: Optional[str] = None,
    ) -> "CoreState":
        """新 session 的狀態。這是唯一合法的重置點（契約 R5）。"""
        if model_kind not in MODEL_KINDS:
            raise CoreStateInvalid(
                f"model_kind must be one of {sorted(MODEL_KINDS)}, got {model_kind!r}"
            )
        stamp = now or _utc_now()
        state = cls(
            schema_version=SCHEMA_VERSION,
            model_kind=model_kind,
            weights_hash=_validate_weights_hash(weights_hash),
            user_id=user_id,
            session_id=session_id,
            born_at=stamp,
            last_update=stamp,
            ticks=0,
            last_dt_s=0.0,
            state_version=0,
            # 容器不強制轉 numpy：state 由模型擁有（torch tensor 可能要保留
            # autograd 圖）。存檔前由 adapter 的 export_state() 轉成 numpy。
            tensors=dict(tensors or {}),
        )
        return state

    # -- 版本 ---------------------------------------------------------------

    def bump(self, *, now: Optional[str] = None) -> None:
        """一次狀態突變：`state_version` 單調遞增（樂觀鎖的比較基準）。"""
        self.state_version += 1
        self.last_update = now or _utc_now()

    # -- 序列化 -------------------------------------------------------------

    def _meta_without_checksum(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "model_kind": self.model_kind,
            "weights_hash": self.weights_hash,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "born_at": self.born_at,
            "last_update": self.last_update,
            "ticks": self.ticks,
            "last_dt_s": self.last_dt_s,
            "state_version": self.state_version,
            "tensors": sorted(self.tensors),
        }

    def _tensors_bytes(self) -> bytes:
        buffer = io.BytesIO()
        for name, value in self.tensors.items():
            if not isinstance(value, np.ndarray):
                raise CoreStateInvalid(
                    f"tensor {name!r} is {type(value).__name__}, not numpy; "
                    "call the adapter's export_state() before saving"
                )
        # ``**payload`` 以 Any 展開：numpy 的 stub 把第一個 keyword 當成
        # ``allow_pickle``，直接展開 ndarray 映射會被判成型別錯誤。
        payload: Any = {name: value for name, value in self.tensors.items()}
        np.savez_compressed(buffer, **payload)
        return buffer.getvalue()

    def save(self, directory: os.PathLike[str] | str) -> Path:
        """原子寫入 `meta.json` ＋ `tensors.npz`，回傳目錄。

        先寫張量、後寫 meta；checksum 同時涵蓋兩者，所以崩潰殘檔會在
        :meth:`load` 被拒絕。超過大小上限直接拋錯，不做截斷。
        """
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)

        tensors_bytes = self._tensors_bytes()
        meta = self._meta_without_checksum()
        meta["checksum"] = _digest(meta, tensors_bytes)
        meta_bytes = json.dumps(
            meta, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

        total = len(tensors_bytes) + len(meta_bytes)
        if total > MAX_STATE_BYTES:
            raise CoreStateTooLarge(
                f"state is {total} bytes, limit is {MAX_STATE_BYTES}; "
                "quantise or shrink the tensors instead of raising the cap"
            )

        _atomic_write(target / TENSORS_FILENAME, tensors_bytes)
        _atomic_write(target / META_FILENAME, meta_bytes)
        return target

    @classmethod
    def load(
        cls,
        directory: os.PathLike[str] | str,
        *,
        expected_weights_hash: Optional[str] = None,
        expected_schema_version: int = SCHEMA_VERSION,
    ) -> "CoreState":
        """讀回狀態；任何不一致都**拒絕**，不建立空狀態、不靜默重置。"""
        target = Path(directory)
        meta_path = target / META_FILENAME
        tensors_path = target / TENSORS_FILENAME

        if not meta_path.is_file():
            raise CoreStateCorrupt(f"missing {meta_path.name} in {target}; refusing to reset")
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CoreStateCorrupt(f"unreadable {meta_path.name}: {exc}") from exc
        _require(isinstance(meta, dict), "meta.json must contain an object")
        missing = [key for key in _META_REQUIRED if key not in meta]
        _require(not missing, f"meta.json missing keys: {missing}")
        _validate_meta_types(meta)

        if meta["schema_version"] != expected_schema_version:
            raise CoreStateVersionMismatch(
                f"schema_version {meta['schema_version']} != {expected_schema_version}"
            )

        try:
            stored_hash = _validate_weights_hash(meta["weights_hash"])
        except CoreStateInvalid as exc:
            raise CoreStateCorrupt(f"meta.json has an invalid weights_hash: {exc}") from exc
        if expected_weights_hash is not None:
            expected_hash = _validate_weights_hash(expected_weights_hash)
            if stored_hash != expected_hash:
                raise CoreStateVersionMismatch(
                    "weights_hash does not match the loaded model; refusing to reuse state"
                )

        if not tensors_path.is_file():
            raise CoreStateCorrupt(f"missing {tensors_path.name} in {target}")
        try:
            tensors_bytes = tensors_path.read_bytes()
        except OSError as exc:
            raise CoreStateCorrupt(f"unreadable {tensors_path.name}: {exc}") from exc

        unsigned = {key: meta[key] for key in _META_REQUIRED if key != "checksum"}
        if _digest(unsigned, tensors_bytes) != meta["checksum"]:
            raise CoreStateCorrupt(
                "checksum mismatch (partial write or tampered state); refusing to load"
            )

        names = meta["tensors"]
        _require(
            sorted(names) == sorted(set(names)),
            "tensors list must not contain duplicates",
        )
        try:
            with np.load(io.BytesIO(tensors_bytes), allow_pickle=False) as archive:
                tensors = {name: archive[name] for name in names}
        except (OSError, ValueError, KeyError) as exc:
            raise CoreStateCorrupt(f"unreadable tensors: {exc}") from exc

        return cls(
            schema_version=meta["schema_version"],
            model_kind=meta["model_kind"],
            weights_hash=stored_hash,
            user_id=meta["user_id"],
            session_id=meta["session_id"],
            born_at=meta["born_at"],
            last_update=meta["last_update"],
            ticks=meta["ticks"],
            last_dt_s=float(meta["last_dt_s"]),
            state_version=meta["state_version"],
            tensors=tensors,
        )


def _atomic_write(path: Path, payload: bytes) -> None:
    """同目錄暫存檔 → fsync → `os.replace`，避免讀者看到半個檔案。"""
    handle = tempfile.NamedTemporaryFile(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp", delete=False
    )
    tmp_path = Path(handle.name)
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def _utc_now() -> str:
    """UTC ISO-8601（秒級；狀態只需要排序，不需要亞秒精度）。"""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


__all__ = [
    "CoreState",
    "CoreStateCorrupt",
    "CoreStateError",
    "CoreStateInvalid",
    "CoreStateTooLarge",
    "CoreStateVersionMismatch",
    "MAX_STATE_BYTES",
    "MODEL_KINDS",
    "SCHEMA_VERSION",
    "hash_weights_bytes",
    "hash_weights_file",
]
