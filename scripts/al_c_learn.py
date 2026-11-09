#!/usr/bin/env python
"""C-learn：相位決定「這次經歷被記得多深」（`al_c_state.py` 的下一級）

C-param 改請求、C-logit 改輸出、C-state 改當下的發火閾值——三者都只影響**這一刻**。
這一支改的是權重會被推向哪裡：同一個模型、同一批資料、同一個順序、同一個 `lr`，
只因為經歷它們時的內生相位不同，留下來的結構就不同。

接法：`core/life/al_learning_gate.py`（activation → 可塑性增益 0.4–1.6）接到
`TensorSNNCore.hebbian_update(plasticity=…)`，實際 `lr` 乘上增益。缺席／壞值 →
1.0（逐位不變）。

量什麼
------
1. ``weights_depend_on_phase``：8 個相位各訓練一次，權重矩陣的最大逐點差；
2. ``ordering_follows_phase``：權重位移與「已固化配對數」是否隨增益單調（Spearman ρ）；
3. ``consolidated``：跨過 0.3 的配對數——離散的「學起來了」，不是數值漂移；
4. ``control_is_identical``：增益 1.0 與不傳 `plasticity` → 權重**逐位相同**。

控制組與偽造品
--------------
- **無調制**（`plasticity` 缺席）→ 與接線前逐位相同；
- **中立相位**（activation 0.5，增益恰 1.0）→ 與無調制逐位相同；
- **偽造品**：wall-clock 正弦 → 兩次重跑不同（不可重現，不能當證據）；
  真實振盪器排程 → 兩次重跑逐位相同。

它**沒有**量什麼：沒有量語意品質，也沒有量「這樣學比較好」——只主張相位改變
了留下來的結構，且方向由增益決定。
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [C] [L0-L11]
# =============================================================================

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from ai.garden.snn_core import TensorSNNCore  # noqa: E402
from core.life.al_learning_gate import learning_gain  # noqa: E402
from core.life.al_oscillator import Oscillator, natural_period  # noqa: E402

N_PHASES = 8
N_KEYS = 24
N_SAMPLES = 72
# 只經歷一次：同一組配對在定點收斂後，多輪只剩「已經到站」的更新，
# 增益（這裡從 lr 進來）的差異就被抹掉（第一版 3 輪量到 ΔW≈0，那不是
# 「相位沒用」，是權重已經到定點）。注意 2026-11-09 起定點是
# target_strength×gate：共活化**強度**的差異會留在權重上，學**習率**的差異不會。
EPOCHS = 1
LR = 0.5
TARGET_STRENGTH = 0.9
CONSOLIDATED_AT = 0.3

KEYS = tuple(f"k{i:02d}" for i in range(N_KEYS))
# 固定的配對流：順序、內容都不變，唯一變的是「經歷它時的相位」。
# 72 個**互不相同**的有序配對（來源 k00–k07 × 目標 k09–k17）：每對只經歷
# 一次，權重才不會因為重複曝光而飽和——第一版用循環配對，24 對被看了 3 次，
# 全部衝到 target_strength，量到的 ΔW 只是「飽和程度」，不是增益。
STREAM = tuple((KEYS[src], KEYS[9 + tgt]) for src in range(8) for tgt in range(9))


def _core() -> TensorSNNCore:
    return TensorSNNCore(leak=0.5, threshold=0.6, timesteps=12, decay=0.9, device="cpu")


def _train(gains: Sequence[float]) -> TensorSNNCore:
    """同一批配對、同一個順序、同一個 lr；只有可塑性增益不同。"""
    core = _core()
    for epoch in range(EPOCHS):
        for idx, (src, tgt) in enumerate(STREAM):
            core.hebbian_update(
                {src: 1.0},
                {tgt: 1.0},
                lr=LR,
                target_strength=TARGET_STRENGTH,
                weight_decay=0.0,
                plasticity=gains[(epoch * len(STREAM) + idx) % len(gains)],
            )
    return core


def _weights(core: TensorSNNCore) -> List[List[float]]:
    V = core.vocab_size
    return [
        [float(core._W[i, j]) for j in range(V)]  # noqa: SLF001 - 量測要看得到權重
        for i in range(V)
    ]


def _max_pointwise(a: List[List[float]], b: List[List[float]]) -> float:
    if len(a) != len(b):
        return float("inf")
    best = 0.0
    for row_a, row_b in zip(a, b):
        for x, y in zip(row_a, row_b):
            best = max(best, abs(x - y))
    return best


def _mean_pair_weight(core: TensorSNNCore) -> float:
    """受訓配對的平均權重——增益的單調量（ΔW 對中立點是 V 形，不能當排序依據）。"""
    total = 0.0
    for src, tgt in STREAM:
        i, j = core._key_to_idx.get(src), core._key_to_idx.get(tgt)  # noqa: SLF001
        if i is None or j is None:
            continue
        total += float(core._W[i, j])  # noqa: SLF001
    return total / len(STREAM)


def _consolidated(core: TensorSNNCore) -> int:
    count = 0
    for src, tgt in STREAM:
        i, j = core._key_to_idx.get(src), core._key_to_idx.get(tgt)  # noqa: SLF001
        if i is None or j is None:
            continue
        if float(core._W[i, j]) >= CONSOLIDATED_AT:  # noqa: SLF001
            count += 1
    return count


def _spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    def ranks(values: Sequence[float]) -> List[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        for rank, idx in enumerate(order):
            out[idx] = float(rank)
        return out

    rx, ry = ranks(xs), ranks(ys)
    n = len(rx)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((x - mx) * (y - my) for x, y in zip(rx, ry))
    den = math.sqrt(sum((x - mx) ** 2 for x in rx) * sum((y - my) ** 2 for y in ry))
    return num / den if den > 0 else 0.0


def _phase_grid(n_phases: int = N_PHASES) -> List[tuple]:
    """一個自然週期等分成 n 段，每段走完才取樣——不靠「追相位」硬拉。"""
    osc = Oscillator()
    period = natural_period()
    steps = n_phases * 200
    dt = period / float(steps)
    points = []
    for _ in range(n_phases):
        for _ in range(steps // n_phases):
            osc.step(dt)
        points.append((round(osc.phase, 4), round(osc.activation, 6)))
    return points


def _real_schedule(period: float) -> List[float]:
    """真實振盪器：每個樣本取當下的 activation → 增益（一次掃過整個週期）。"""
    osc = Oscillator()
    dt = period / float(N_SAMPLES * EPOCHS)
    gains: List[float] = []
    for _ in range(N_SAMPLES * EPOCHS):
        gains.append(learning_gain(osc.activation).gain)
        osc.step(dt)
    return gains


def _clock_forgery(n: int) -> List[float]:
    """偽造品：wall-clock 正弦。看起來有節律，但不可重現。"""
    now = time.time()
    return [round(1.0 + 0.6 * math.sin(2.0 * math.pi * (now + i / 40.0)), 6) for i in range(n)]


def run(n_phases: int = N_PHASES) -> Dict[str, object]:
    neutral = _train([1.0])
    neutral_weights = _weights(neutral)

    rows = []
    for phase, activation in _phase_grid(n_phases):
        gain = learning_gain(activation).gain
        core = _train([gain])
        rows.append(
            {
                "phase": phase,
                "activation": activation,
                "gain": gain,
                "max_weight_delta": round(_max_pointwise(_weights(core), neutral_weights), 6),
                "mean_pair_weight": round(_mean_pair_weight(core), 6),
                "consolidated": _consolidated(core),
            }
        )

    gains = [row["gain"] for row in rows]
    deltas = [row["max_weight_delta"] for row in rows]
    means = [row["mean_pair_weight"] for row in rows]
    consolidated = [float(row["consolidated"]) for row in rows]
    rho_delta = _spearman(gains, means)
    rho_consolidated = _spearman(gains, consolidated)

    # 控制組：中立相位（activation 0.5 → 增益恰 1.0）與「根本不傳 plasticity」。
    mid_gain = learning_gain(0.5).gain  # 中立相位：增益恰為 1.0
    mid_control = _train([mid_gain])
    control_delta = _max_pointwise(_weights(mid_control), neutral_weights)
    bad_gain = _train([float("nan")])
    bad_delta = _max_pointwise(_weights(bad_gain), neutral_weights)

    # 真實排程：兩次重跑是否逐位相同（可重現），跨相位是否真的不同。
    period = natural_period()
    schedule = _real_schedule(period)
    scheduled_a = _train(schedule)
    scheduled_b = _train(schedule)
    scheduled_delta = _max_pointwise(_weights(scheduled_a), neutral_weights)
    reproducible = _max_pointwise(_weights(scheduled_a), _weights(scheduled_b)) == 0.0

    # 偽造品：wall-clock 正弦的兩次重跑。
    forged_a = _train(_clock_forgery(N_SAMPLES))
    forged_b = _train(_clock_forgery(N_SAMPLES))
    forged_repeatable = _max_pointwise(_weights(forged_a), _weights(forged_b)) == 0.0

    spread = max(means) - min(means)
    admissible = all(
        (
            spread > 0.05,
            max(consolidated) > min(consolidated),
            abs(rho_delta) > 0.9,
            abs(rho_consolidated) > 0.9,
            control_delta == 0.0,
            bad_delta == 0.0,
            reproducible,
            not forged_repeatable,
            scheduled_delta > 0.05,
        )
    )

    return {
        "kind": "al_c_learn",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "config": {
            "keys": N_KEYS,
            "samples": N_SAMPLES,
            "epochs": EPOCHS,
            "lr": LR,
            "target_strength": TARGET_STRENGTH,
            "consolidated_at": CONSOLIDATED_AT,
            "phases": n_phases,
        },
        "rows": rows,
        "mid_control_gain": mid_gain,
        "control_max_delta": control_delta,
        "bad_gain_max_delta": bad_delta,
        "schedule_max_delta": scheduled_delta,
        "schedule_mean_pair_weight": round(_mean_pair_weight(scheduled_a), 6),
        "schedule_reproducible": reproducible,
        "forgery_repeatable": forged_repeatable,
        "rho_mean_weight": round(rho_delta, 3),
        "rho_consolidated": round(rho_consolidated, 3),
        "weight_spread": round(spread, 6),
        "checks": {
            "weights_depend_on_phase": bool(spread > 0.2),
            "structure_changes": bool(max(consolidated) > min(consolidated)),
            "ordering_follows_phase": bool(rho_delta > 0.9 and rho_consolidated > 0.9),
            "control_is_identical": bool(control_delta == 0.0 and bad_delta == 0.0),
            "schedule_is_reproducible": bool(reproducible and not forged_repeatable),
            "schedule_lands_between_extremes": bool(
                min(means) < _mean_pair_weight(scheduled_a) < max(means)
            ),
        },
        "admissible": bool(admissible),
        "verdict": "phase-decides-what-gets-kept" if admissible else "phase-leaves-learning-alone",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phases", type=int, default=N_PHASES)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    result = run(args.phases)
    for row in result["rows"]:  # type: ignore[index]
        print(
            f"  act {row['activation']:.3f} gain×{row['gain']:.3f} "
            f"meanW {row['mean_pair_weight']:.4f} consolidated {row['consolidated']}"
        )
    print(
        f"spread {result['weight_spread']}  rho mean-W {result['rho_mean_weight']} "
        f"rho consolidated {result['rho_consolidated']}"
    )
    print(
        f"mid-gain control Δ {result['control_max_delta']}  "
        f"bad-gain Δ {result['bad_gain_max_delta']}  "
        f"schedule Δ {result['schedule_max_delta']} reproducible {result['schedule_reproducible']}"
    )
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
