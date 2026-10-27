# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [A] [L0-L11]
# =============================================================================
"""AL 單一狀態面：欄位類別、單一時鐘與唯讀快照（契約 §3–§4、§9）。

三分法 Phase 2 item 1 —— schema 先行。本模組只有三件事：

1. **欄位類別表**（``FIELD_CLASSES``）：v1 八個欄位各屬 ``invariant`` /
   ``slow`` / ``fast`` / ``derived``（§3.1–§3.2）。類別決定是否落盤、
   時常數上界、是否參與漂移修正。
2. **單一時鐘**（``born_at`` / ``ticks``）：首次初始化持久化、每次推進
   持久化；進程啟動先讀檔，**不得以當前時間重建**（§4.4）。
3. **唯讀快照** ``get_al_state() -> ALSnapshot``：讀走快照（§9）。
   來源在 core 側的直接讀（``intensity`` / ``tendency``）；實例握在 api
   側的（``life_phase`` / ``health`` / ``drift``）經 provider 登記簿注入 ——
   AL 出站不 import ``ai.*`` / ``api.*``（I8），所以永遠不會自己伸手去拿。

三條紀律：

- **未觀測一律 ``None``，絕不寫 ``0.0`` / ``1.0``**（D11）。
- **``derived`` 欄位不落盤**（I3）：由 ``_persist()`` 機械拒絕，不靠記得。
- **``emotion`` v1 恆 ``None``**：情緒實例在 ``ai/alignment``，AL 出站
  import ``ai.*`` 即 I8 違規；等 §8 ``submit_event`` 事件通道接上後才有
  觀測值，因此 ``PROVIDABLE_SOURCES`` 也不含它 —— 登記也登不進來。
"""

from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Tuple, Union

from core.data_config import get_data_root
from core.life.life_essence import get_life_essence
from core.life_intensity_formula import get_life_intensity_formula
from core.system.config.magic_numbers import threshold_value

logger = logging.getLogger(__name__)

# 快照 schema 版本 — 讀者靠它判斷欄位語義（I9）
AL_STATE_VERSION = 1

# =========================================================================
# §3.1–§3.2 欄位類別表（v1 八欄；maturity 依 D9 不進 schema）
# =========================================================================
FIELD_CLASSES: Dict[str, str] = {
    "born_at": "invariant",
    "ticks": "invariant",
    "life_phase": "invariant",
    "health": "fast",
    "intensity": "slow",
    "emotion": "fast",
    "tendency": "slow",
    "drift": "derived",
}

# derived 欄位禁止出現在任何持久化檔案（I3）
DERIVED_FIELDS: frozenset = frozenset(
    name for name, cls in FIELD_CLASSES.items() if cls == "derived"
)

# =========================================================================
# §7 參數層：源佔比（D7 — v1 只實作 ai + user，group 留槽位）
# =========================================================================
PARAM_SOURCES: Tuple[str, ...] = ("ai", "user", "group_fast", "group_slow")

# v1 佔比：自我基準持滿，其餘源尚未啟用（group 槽位為 0，非缺席）
DEFAULT_WEIGHTS: Dict[str, float] = {
    "ai": 1.0,
    "user": 0.0,
    "group_fast": 0.0,
    "group_slow": 0.0,
}

# I1 歸一容差：Σw = 1 ± ε
WEIGHT_EPS = 1e-6

# I2 自我地板預設（配置鍵 `al_w_self_min`，改值走 magic_numbers 慣例）
DEFAULT_W_SELF_MIN = 0.5

# provider 登記簿可提供的來源。emotion 故意不在其中（見模組 docstring）
PROVIDABLE_SOURCES: Tuple[str, ...] = ("life_phase", "health", "drift")


class ALValidationError(RuntimeError):
    """schema 驗證失敗 — 契約 §13 的「違反 boot 失敗」語意。"""


# =========================================================================
# §7.3 安全帶：I1 歸一 + I2 自我地板
# =========================================================================
def self_weight_floor() -> float:
    """自我地板 MIN — 配置鍵 `al_w_self_min`（§7.3-2，紀律上不隨便調）。"""
    return float(threshold_value("al_w_self_min", DEFAULT_W_SELF_MIN))


def validate_weights(weights: Mapping[str, float], *, w_self_min: Optional[float] = None) -> None:
    """I1 ``Σw = 1 ± ε``、I2 ``w_self ≥ MIN``、源鍵合法性。

    違反拋 :class:`ALValidationError`（boot 失敗語意，不是降級）。
    """
    unknown = sorted(set(weights) - set(PARAM_SOURCES))
    if unknown:
        raise ALValidationError(f"I1: unknown parameter sources: {unknown}")
    total = math.fsum(weights.values())
    if abs(total - 1.0) > WEIGHT_EPS:
        raise ALValidationError(
            f"I1: Σw = {total!r}, expected 1 ± {WEIGHT_EPS} (weights={dict(weights)})"
        )
    floor = self_weight_floor() if w_self_min is None else w_self_min
    w_self = float(weights.get("ai", 0.0))
    if w_self < floor:
        raise ALValidationError(
            f"I2: w_self = {w_self!r} below floor {floor!r} — "
            "self-weight may not drift toward zero (contract §7.3-2)"
        )


# =========================================================================
# §3.2 快照：讀走快照（§9）
# =========================================================================
@dataclass(frozen=True)
class ALSnapshot:
    """AL 對外的唯一狀態交換量（contract §9）。

    歸因欄位（I9）：``version`` + ``effective`` + 分量 ``components`` +
    ``weights`` + ``source`` —— 少一樣，「怎麼突然變了」就無法取證。

    - ``effective``：參數層生效值 ``Σ w_s · x_s``（§7.2）。v1 濾波器組
      尚未接線 → ``None``（D11），接上後才有觀測值。
    - ``source``：每欄 provenance，未觀測 → ``None``。
    - ``taken_at``：快照取得時刻（wall-clock 只標時間，不參與衰減，I4）。
    """

    version: int
    taken_at: float
    effective: Optional[float]
    components: Dict[str, Optional[float]]
    weights: Dict[str, float]
    source: Dict[str, Optional[str]]
    born_at: Optional[float]
    ticks: Optional[int]
    life_phase: Optional[str]
    health: Optional[float]
    intensity: Optional[float]
    emotion: Optional[Dict[str, float]]
    tendency: Optional[Dict[str, float]]
    drift: Optional[Dict[str, float]]

    def as_dict(self) -> Dict[str, Any]:
        """序列化 — I9 機器驗證的對象。"""
        return asdict(self)


def validate_snapshot(snapshot: ALSnapshot) -> None:
    """快照出口驗證（I1/I2/I9）——違反即拋，不靜默降級。"""
    if snapshot.version != AL_STATE_VERSION:
        raise ALValidationError(f"I9: snapshot version {snapshot.version} != {AL_STATE_VERSION}")
    validate_weights(snapshot.weights)
    missing = sorted(set(snapshot.weights) - set(snapshot.components))
    if missing:
        raise ALValidationError(f"I9: components missing for weights: {missing}")


# =========================================================================
# §4 時鐘：born_at / ticks 單一時間基準，跨重啟不歸零
# =========================================================================
def _clock_path(path: Optional[Union[str, Path]] = None) -> Path:
    if path is not None:
        return Path(path)
    return get_data_root() / "al_state.json"


def _persist(payload: Mapping[str, Any], path: Optional[Union[str, Path]] = None) -> None:
    """寫時鐘檔；``derived`` 鍵直接拋（I3 機械保證，不靠記得）。"""
    illegal = sorted(DERIVED_FIELDS.intersection(payload))
    if illegal:
        raise ALValidationError(f"I3: derived fields must never be persisted: {illegal}")
    target = _clock_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as fh:
        json.dump(dict(payload), fh, indent=2, ensure_ascii=False)


def load_clock(path: Optional[Union[str, Path]] = None) -> Tuple[Optional[float], Optional[int]]:
    """讀持久化時鐘。缺檔/壞檔 → ``(None, None)``（D11 未觀測，不偷寫）。"""
    target = _clock_path(path)
    if not target.is_file():
        return None, None
    try:
        with open(target, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("[ALState] unreadable clock file %s: %s", target, exc)
        return None, None
    if not isinstance(data, dict):
        logger.warning("[ALState] clock file %s is not an object", target)
        return None, None
    born = data.get("born_at")
    ticks = data.get("ticks")
    if isinstance(born, bool) or not isinstance(born, (int, float)):
        born = None
    if isinstance(ticks, bool) or not isinstance(ticks, int):
        ticks = None
    return (float(born) if born is not None else None), ticks


def init_clock(
    now: Optional[float] = None, path: Optional[Union[str, Path]] = None
) -> Tuple[float, int]:
    """首次初始化起鐘；已有時鐘一律沿用（§4.4 跨重啟不得以當前時間重建）。"""
    born, ticks = load_clock(path)
    if born is not None:
        return born, ticks if ticks is not None else 0
    born_at = time.time() if now is None else float(now)
    _persist({"version": AL_STATE_VERSION, "born_at": born_at, "ticks": 0}, path)
    return born_at, 0


def advance_tick(path: Optional[Union[str, Path]] = None) -> int:
    """推進一次 tick 並持久化（§4.1：ticks 每次推進持久化）。"""
    born, ticks = load_clock(path)
    if born is None:
        # 從未起鐘的首次推進就是出生：now 是唯一誠實的答案
        born = time.time()
    next_ticks = (ticks or 0) + 1
    _persist({"version": AL_STATE_VERSION, "born_at": born, "ticks": next_ticks}, path)
    return next_ticks


# =========================================================================
# provider 登記簿：api 側單例由註冊注入，AL 不出站伸手（I8）
# =========================================================================
_AL_SOURCES: Dict[str, Callable[[], Any]] = {}


def register_al_source(name: str, produce: Callable[[], Any]) -> None:
    """登記一個狀態來源（由 api/lifespan 等組裝層呼叫）。

    只收 ``PROVIDABLE_SOURCES`` 內的名字 —— 打錯字靜默失效比崩潰更貴；
    ``emotion`` 不在其中（I8 / §8 事件通道，見模組 docstring）。
    """
    if name not in PROVIDABLE_SOURCES:
        raise ALValidationError(
            f"unknown AL source {name!r}; providable = {list(PROVIDABLE_SOURCES)}"
        )
    _AL_SOURCES[name] = produce


def clear_al_sources() -> None:
    """清空登記簿（測試隔離用；生產不呼叫）。"""
    _AL_SOURCES.clear()


def _call_source(name: str) -> Any:
    produce = _AL_SOURCES.get(name)
    if produce is None:
        return None
    try:
        return produce()
    except Exception as exc:  # 來源故障 → 未觀測（D11），不拖垮整個快照
        logger.debug("[ALState] source %s unavailable: %s", name, exc)
        return None


# =========================================================================
# 讀路徑（§9）：唯讀快照
# =========================================================================
def _read_intensity() -> Optional[float]:
    try:
        return float(get_life_intensity_formula().peek_life_intensity())
    except Exception as exc:
        logger.debug("[ALState] intensity unavailable: %s", exc)
        return None


def _read_tendency() -> Optional[Dict[str, float]]:
    try:
        values = get_life_essence().get_all_blended_tendencies()
        return {str(k): float(v) for k, v in values.items()}
    except Exception as exc:
        logger.debug("[ALState] tendency unavailable: %s", exc)
        return None


def _phase_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raw = getattr(value, "value", value)
    return str(raw)


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_al_state() -> ALSnapshot:
    """取 AL 唯讀快照（contract §9 的讀路徑，唯一的對外交換量）。"""
    born_at, ticks = load_clock()
    life_phase_raw = _call_source("life_phase")
    health_raw = _call_source("health")
    drift_raw = _call_source("drift")
    intensity = _read_intensity()
    tendency = _read_tendency()

    source: Dict[str, Optional[str]] = {
        "born_at": "al_state.clock" if born_at is not None else None,
        "ticks": "al_state.clock" if ticks is not None else None,
        "life_phase": "provider:life_phase" if life_phase_raw is not None else None,
        "health": "provider:health" if health_raw is not None else None,
        "intensity": (
            "core.life_intensity_formula.peek_life_intensity" if intensity is not None else None
        ),
        # I8：情緒實例在 ai/alignment，AL 不得出站 import ai.*；等 §8 事件通道
        "emotion": None,
        "tendency": (
            "core.life.life_essence.get_all_blended_tendencies" if tendency is not None else None
        ),
        "drift": "provider:drift" if drift_raw is not None else None,
    }

    snapshot = ALSnapshot(
        version=AL_STATE_VERSION,
        taken_at=time.time(),
        # 參數層一階濾波（§7.2）尚未接線 → 未觀測（D11），非 0.0
        effective=None,
        components={name: None for name in PARAM_SOURCES},
        weights=dict(DEFAULT_WEIGHTS),
        source=source,
        born_at=born_at,
        ticks=ticks,
        life_phase=_phase_str(life_phase_raw),
        health=_as_float(health_raw),
        intensity=intensity,
        emotion=None,
        tendency=tendency,
        drift=drift_raw if isinstance(drift_raw, dict) else None,
    )
    validate_snapshot(snapshot)
    return snapshot
