#!/usr/bin/env python
"""診斷：相位調制的 margin 升、top-1 降，是被誰拉下來的？

難版任務（`--task hard`）穩定量到「margin 12/12 種子上升、top-1 11/12 種子下降」。這支
腳本追到 cue 層級：在**同一個種子**下，`neutral`（固定增益 1.0）與 `phase`（振盪器排程）
各訓練一次，記下每個 cue 在訓練時拿到多少增益，再看

1. 增益排程的分布（最低/最高、有幾個接近 0）；
2. 每個 cue 的「margin 變化」與「它在訓練時拿到的增益」是否相關；
3. 翻轉（neutral 命中、phase 排不到第一）是否集中在低增益的 cue 上。

判詞

* ``low-gain-samples-are-the-losers``：翻轉集中在低增益 cue 上——「排程」等於某些樣本
  幾乎沒學到，這不是機制變好，是機制漏學；
* ``flips-not-explained-by-gain``：翻轉與增益無關，另有原因（報表仍列出）；
* ``no-flips``：這個種子沒有翻轉，什麼都不能說。
"""

# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L0-L11]
# =============================================================================

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from ai.garden.snn_core import TensorSNNCore  # noqa: E402

DOWNSTREAM_SCRIPT = Path(__file__).with_name("al_c_learn_downstream.py")
# 低谷段的門檻。增益的實際範圍是 0.4–1.6（中性 1.0），所以舊的 0.2 **永遠不會被
# 觸發**：`low-gain-samples-are-the-losers` 這個判詞在資料完全支持它的時候也判不出來。
# 0.8 的語義是「明顯低於中性」，落在擺幅的下半段。
LOW_GAIN = 0.8


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_downstream = _load("al_c_learn_downstream", DOWNSTREAM_SCRIPT)
_readouts = _downstream._readouts


def _train_logged(
    gains: Sequence[float], seed: int, task: Dict[str, object]
) -> Tuple[TensorSNNCore, List[float]]:
    """與 ``_downstream._train`` 相同的洗牌與更新，但記下每個 cue 拿到多少增益。"""
    core = TensorSNNCore(threshold=float(task["threshold"]), timesteps=_readouts.TIMESTEPS)  # type: ignore[arg-type]
    rng = random.Random(seed)
    pairs = _downstream._pairs(task)
    per_pair = [0.0] * len(pairs)
    for _ in range(_downstream.EPOCHS):
        order = list(enumerate(pairs))
        rng.shuffle(order)
        for (index, (inputs, target)), gain in zip(order, gains):
            per_pair[index] = float(gain)
            core.hebbian_update(
                {key: 1.0 for key in inputs},
                {target: 1.0},
                lr=float(task["lr"]),  # type: ignore[arg-type]
                target_strength=_downstream.TARGET_STRENGTH,
                plasticity=float(gain),
            )
    return core, per_pair


def _margins(core, pairs) -> List[float]:
    """與正式評分共用 ``_score``，免得診斷腳本自己算一套（曾因索引拼 label 而截半）。"""
    targets = _downstream._candidate_targets(pairs)
    margins: List[float] = []
    for inputs, target in pairs:
        out = _readouts._forward(core, {key: 1.0 for key in inputs}, "potential")
        margins.append(_downstream._score(out, targets, target)[0])
    return margins


def _row_sum(core, token: str) -> float:
    idx = core._key_to_idx.get(token)
    if idx is None:
        return 0.0
    return float(core._W[idx, : core.vocab_size].sum())


def _correlation(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) < 3:
        return 0.0
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return 0.0 if dx == 0 or dy == 0 else num / (dx * dy)


def _verdict(rows: List[Dict[str, float]], flips: List[int]) -> str:
    if not flips:
        return "no-flips"
    flipped_low = sum(1 for i in flips if rows[i]["gain"] < LOW_GAIN)
    others = [i for i in range(len(rows)) if i not in flips]
    other_low = sum(1 for i in others if rows[i]["gain"] < LOW_GAIN)
    flipped_rate = flipped_low / len(flips)
    other_rate = other_low / len(others) if others else 0.0
    if flipped_rate >= 0.6 and flipped_rate > other_rate:
        return "low-gain-samples-are-the-losers"
    return "flips-not-explained-by-gain"


def run(seed: int = 11, task_name: str = _downstream.DEFAULT_TASK) -> Dict[str, object]:
    task = _downstream.TASKS[task_name]
    pairs = _downstream._pairs(task)
    n_samples = len(pairs)
    period = _downstream.natural_period()
    phase_gains = _downstream._schedule(period, n_samples)

    neutral, neutral_gain = _train_logged([1.0] * n_samples, seed, task)
    phase, phase_gain = _train_logged(phase_gains, seed, task)

    margins = {"neutral": _margins(neutral, pairs), "phase": _margins(phase, pairs)}
    flips = [i for i in range(n_samples) if margins["neutral"][i] > 0 and margins["phase"][i] <= 0]

    rows: List[Dict[str, float]] = []
    for i, (_, target) in enumerate(pairs):
        rows.append(
            {
                "pair": i,
                "gain": round(phase_gain[i], 4),
                "neutral_margin": round(margins["neutral"][i], 5),
                "phase_margin": round(margins["phase"][i], 5),
                "margin_delta": round(margins["phase"][i] - margins["neutral"][i], 5),
                "phase_target_row": round(_row_sum(phase, target), 4),
                "neutral_target_row": round(_row_sum(neutral, target), 4),
            }
        )

    gain_deltas = [row["margin_delta"] for row in rows]
    corr = _correlation([row["gain"] for row in rows], gain_deltas)
    zeros = sum(1 for row in rows if row["gain"] < LOW_GAIN)
    # 基準率：全部樣本裡有多少比例本來就低增益。沒有這個數字，「翻轉的多半是低增益」
    # 就可能只是「大部分樣本都低增益」的同義詞。
    low_base_rate = zeros / len(rows) if rows else 0.0
    empty_targets = sum(1 for row in rows if row["phase_target_row"] <= 0.0)

    return {
        "seed": seed,
        "task": task_name,
        "period_s": round(period, 3),
        "gain": {
            "min": round(min(phase_gain), 4),
            "max": round(max(phase_gain), 4),
            "mean": round(statistics.fmean(phase_gain), 4),
            "below_low": zeros,
            "below_low_base_rate": round(low_base_rate, 3),
            "low_gain_threshold": LOW_GAIN,
        },
        "margin_mean": {
            name: round(statistics.fmean(values), 5) for name, values in margins.items()
        },
        "gain_delta_correlation": round(corr, 4),
        "phase_rows_at_zero": empty_targets,
        "flips": flips,
        "flipped_rows": [rows[i] for i in flips],
        "verdict": _verdict(rows, flips),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--task", choices=sorted(_downstream.TASKS), default=_downstream.DEFAULT_TASK)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    result = run(seed=args.seed, task_name=args.task)
    print(f"task: {args.task}  seed: {args.seed}  period {result['period_s']}s")
    print(f"gain schedule: {result['gain']}")
    flipped_rate = len(result["flipped_rows"]) / max(1, len(result["flips"]))
    print(
        f"low-gain base rate: {result['gain']['below_low_base_rate']}"
        f"  (flipped rows that are low-gain: {flipped_rate:.2f})"
    )
    print(f"margin mean: {result['margin_mean']}")
    print(
        f"corr(gain, margin delta): {result['gain_delta_correlation']}  "
        f"zero-weight target rows: {result['phase_rows_at_zero']}"
    )
    print(f"flips ({len(result['flips'])}): {result['flips']}")
    for row in result["flipped_rows"]:
        print(
            f"  pair {row['pair']:>2}: gain {row['gain']:.3f}  "
            f"neutral {row['neutral_margin']:+.5f} -> phase {row['phase_margin']:+.5f}  "
            f"target row {row['phase_target_row']:.4f}"
        )
    print(f"verdict: {result['verdict']}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"report: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
