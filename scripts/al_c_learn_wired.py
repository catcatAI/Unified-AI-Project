#!/usr/bin/env python
"""C-learn 的**生產接線**量測：真實 `GARDENEngine` 的學習路徑吃到了相位

`al_c_learn.py` 證明的是「`hebbian_update(plasticity=…)` 有效」，那是模型層。
這一支問的是另一件事：**線上聊天走的那條路**（`GARDENEngine.learn_from_interaction`
/ `learn_batch`）有沒有讀到 AL 的相位？如果沒有，C-learn 就只是實驗室裡的東西。

做法：同一個引擎、同一批互動、同一個順序，只換 `get_rhythm_tracker()` 背後
的內生相位（用 `set_rhythm_tracker()` 注入固定 activation 的替身，引擎仍經由
生產路徑 `_plasticity_gain()` 讀它）。

量什麼
------
1. ``production_path_reads_phase``：谷相位與峰相位訓練出的 SNN 權重最大逐點差；
2. ``delta_scales_with_phase``：`learn_from_interaction` 回報的 `hebbian_delta`
   比值，是否等於增益比（0.4 → 1.6 是 4×，允許 20% 誤差）；
3. ``batch_path_wired``：`learn_batch` 也有差（批次路徑是另一段程式）；
4. ``control_is_identical``：中立相位（增益恰 1.0）與**完全沒有 tracker** → 逐位相同；
5. ``not_random``：同一個相位跑兩次逐位相同（不是時鐘噪音）。

它**沒有**量什麼：沒有量「這樣學比較好」（沒有下游任務），也沒有量真實線上
對話的長期效果——那是需要長時間跑、且有 held-out 評估的東西。
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [C] [L0-L11]
# =============================================================================

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from ai.garden.garden_engine import GARDENEngine  # noqa: E402
from core.life.al_learning_gate import learning_gain  # noqa: E402
from core.life.al_oscillator import set_rhythm_tracker  # noqa: E402

TROUGH = 0.02
PEAK = 0.98
NEUTRAL = 0.5

INTERACTIONS: Sequence[tuple] = (
    ("the storm broke the harbour wall", "the storm broke the harbour wall and flooded the road"),
    ("the engine lost oil pressure", "the engine lost oil pressure before the ridge"),
    ("the baker opened the shutters", "the baker opened the shutters at first light"),
    ("the river carried the bridge away", "the river carried the bridge away in the night"),
    ("the lamp flickered twice", "the lamp flickered twice and then went dark"),
    ("the dog waited by the gate", "the dog waited by the gate until noon"),
    ("the train stopped between stations", "the train stopped between stations for an hour"),
    ("the roof leaked over the stairs", "the roof leaked over the stairs all winter"),
)


class _BrokenRhythm:
    """壞掉的節律源：讀取就爆。學習不能因此停擺，也不能因此變亂數。"""

    def activation_preview(self) -> float:
        raise RuntimeError("oscillator offline")


class _GarbageRhythm:
    """壞型別：NaN。必須收斂到中性，而不是把 lr 變成 0 或 NaN。"""

    def activation_preview(self) -> float:
        return float("nan")


class _FixedRhythm:
    """替身：只提供生產路徑會讀的那一個方法（不推進、不落盤）。"""

    def __init__(self, activation: float) -> None:
        self._activation = float(activation)

    def activation_preview(self) -> float:
        return self._activation

    def activation(self, now: Optional[float] = None) -> float:  # pragma: no cover - 介面相容
        return self._activation

    def phase(self) -> float:  # pragma: no cover - 介面相容
        return 0.0


def _engine() -> GARDENEngine:
    engine = GARDENEngine(compatibility_mode=True, snn_timesteps=4)
    engine.load_presets()
    return engine


def _train_single(rhythm: object) -> tuple:
    """走真正的 `learn_from_interaction`；rhythm 是注入的節律源。"""
    set_rhythm_tracker(rhythm)  # type: ignore[arg-type]
    try:
        engine = _engine()
        deltas: List[float] = []
        for user_text, response_text in INTERACTIONS:
            summary = engine.learn_from_interaction(user_text, response_text)
            deltas.append(float(summary.get("hebbian_delta", 0.0)))
    finally:
        set_rhythm_tracker(None)
    return engine, deltas


def _train_batch(rhythm: object) -> GARDENEngine:
    set_rhythm_tracker(rhythm)  # type: ignore[arg-type]
    try:
        engine = _engine()
        samples = [{"input": u, "output": r} for u, r in INTERACTIONS]
        engine.learn_batch(samples)
    finally:
        set_rhythm_tracker(None)
    return engine


def _weight_map(engine: GARDENEngine) -> Dict[tuple, float]:
    snn = engine.snn
    out: Dict[tuple, float] = {}
    for key_i, idx_i in snn._key_to_idx.items():  # noqa: SLF001 - 量測要看得到權重
        for key_j, idx_j in snn._key_to_idx.items():  # noqa: SLF001
            value = float(snn._W[idx_i, idx_j])  # noqa: SLF001
            if value != 0.0:
                out[(key_i, key_j)] = value
    return out


def _max_pointwise(a: GARDENEngine, b: GARDENEngine) -> float:
    left, right = _weight_map(a), _weight_map(b)
    keys = set(left) | set(right)
    return max((abs(left.get(k, 0.0) - right.get(k, 0.0)) for k in keys), default=0.0)


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def run() -> Dict[str, object]:
    trough_engine, trough_deltas = _train_single(_FixedRhythm(TROUGH))
    peak_engine, peak_deltas = _train_single(_FixedRhythm(PEAK))
    neutral_engine, _ = _train_single(_FixedRhythm(NEUTRAL))
    peak_again, _ = _train_single(_FixedRhythm(PEAK))

    trough_gain = learning_gain(TROUGH).gain
    peak_gain = learning_gain(PEAK).gain

    single_delta_max = _max_pointwise(trough_engine, peak_engine)
    delta_ratio = _mean(peak_deltas) / _mean(trough_deltas) if _mean(trough_deltas) else 0.0
    expected_ratio = peak_gain / trough_gain
    ratio_off = abs(delta_ratio - expected_ratio) / expected_ratio if expected_ratio else 1.0

    batch_trough = _train_batch(_FixedRhythm(TROUGH))
    batch_peak = _train_batch(_FixedRhythm(PEAK))
    batch_delta_max = _max_pointwise(batch_trough, batch_peak)

    # 控制組：**壞掉的源**（拋錯／NaN）必須與中立逐位相同。這比「沒有源」更強：
    # 生產環境的 `get_rhythm_tracker()` 一定會建一個 tracker，所以「沒有源」不是
    # 一種真實狀態；真正要防的是源壞掉時學習被污染。
    broken_engine, _ = _train_single(_BrokenRhythm())
    garbage_engine, _ = _train_single(_GarbageRhythm())
    control_delta = max(
        _max_pointwise(neutral_engine, broken_engine),
        _max_pointwise(neutral_engine, garbage_engine),
    )
    repeat_delta = _max_pointwise(peak_engine, peak_again)

    checks = {
        "production_path_reads_phase": bool(single_delta_max > 1e-9),
        "delta_scales_with_phase": bool(ratio_off < 0.2),
        "batch_path_wired": bool(batch_delta_max > 1e-9),
        "control_is_identical": bool(control_delta == 0.0),
        "neutral_gain_is_one": bool(learning_gain(NEUTRAL).gain == 1.0),
        "not_random": bool(repeat_delta == 0.0),
    }
    admissible = all(checks.values())

    return {
        "kind": "al_c_learn_wired",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "interactions": len(INTERACTIONS),
        "gains": {"trough": trough_gain, "peak": peak_gain},
        "single_path": {
            "max_weight_delta": single_delta_max,
            "mean_delta_trough": round(_mean(trough_deltas), 6),
            "mean_delta_peak": round(_mean(peak_deltas), 6),
            "delta_ratio": round(delta_ratio, 3),
            "expected_ratio": round(expected_ratio, 3),
        },
        "batch_path": {"max_weight_delta": batch_delta_max},
        "control_max_delta": control_delta,
        "repeat_max_delta": repeat_delta,
        "checks": checks,
        "admissible": bool(admissible),
        "verdict": (
            "phase-reaches-learning-in-production" if admissible else "phase-stops-at-the-model"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    result = run()
    single = result["single_path"]  # type: ignore[index]
    print(
        f"single: ΔW {single['max_weight_delta']:.6f}  "
        f"delta {single['mean_delta_trough']:.5f} → {single['mean_delta_peak']:.5f} "
        f"(ratio {single['delta_ratio']} vs expected {single['expected_ratio']})"
    )
    print(f"batch:  ΔW {result['batch_path']['max_weight_delta']:.6f}")  # type: ignore[index]
    print(f"control Δ {result['control_max_delta']}  repeat Δ {result['repeat_max_delta']}")
    for name, ok in result["checks"].items():  # type: ignore[union-attr]
        print(("ok  " if ok else "FAIL") + f" {name}")
    print(f"verdict: {result['verdict']}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"report: {args.json}")
    return 0 if result["admissible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
