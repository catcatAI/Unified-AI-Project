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
    gains: Sequence[float],
    seed: int,
    task: Dict[str, object],
    epochs: int = _downstream.EPOCHS,
    on_epoch=None,
) -> Tuple[TensorSNNCore, List[float]]:
    """與 ``_downstream._train`` 相同的洗牌與更新，但記下每個 cue 拿到多少增益。

    ``gains`` 是**逐 epoch 串接**的（第 e 個 epoch 用 ``gains[e*n:(e+1)*n]``），跟協定的
    ``_schedule(..., step_per_period=n)`` 一致。舊版把 epoch 數寫死成
    ``_downstream.EPOCHS`` 並用 ``zip`` 直接吃掉前 n 個增益——多輪時既不換增益，長度不符
    時還會靜默截斷。
    """
    pairs = _downstream._pairs(task)
    n = len(pairs)
    if n == 0:
        raise ValueError("task has no pairs")
    if len(gains) != n * epochs:
        raise ValueError(f"gains has {len(gains)} entries, expected {n} pairs x {epochs} epochs")

    core = TensorSNNCore(threshold=float(task["threshold"]), timesteps=_readouts.TIMESTEPS)  # type: ignore[arg-type]
    rng = random.Random(seed)
    per_pair = [0.0] * n
    for epoch in range(epochs):
        order = list(enumerate(pairs))
        rng.shuffle(order)
        chunk = gains[epoch * n : (epoch + 1) * n]
        for (index, (inputs, target)), gain in zip(order, chunk):
            per_pair[index] = float(gain)
            core.hebbian_update(
                {key: 1.0 for key in inputs},
                {target: 1.0},
                lr=float(task["lr"]),  # type: ignore[arg-type]
                target_strength=_downstream.TARGET_STRENGTH,
                plasticity=float(gain),
            )
        if on_epoch is not None:
            on_epoch(epoch, core, list(per_pair))
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


def _verdict(rows: List[Dict[str, float]], flips: List[int], low_gain: float = LOW_GAIN) -> str:
    if not flips:
        return "no-flips"
    flipped_low = sum(1 for i in flips if rows[i]["gain"] < low_gain)
    others = [i for i in range(len(rows)) if i not in flips]
    other_low = sum(1 for i in others if rows[i]["gain"] < low_gain)
    flipped_rate = flipped_low / len(flips)
    other_rate = other_low / len(others) if others else 0.0
    if flipped_rate >= 0.6 and flipped_rate > other_rate:
        return "low-gain-samples-are-the-losers"
    return "flips-not-explained-by-gain"


def _epoch_summary(
    neutral_margins: Sequence[float],
    phase_margins: Sequence[float],
    phase_gains: Sequence[float],
    pairs: Sequence[Tuple[List[str], str]],
    phase_core,
    cumulative_gains: Sequence[float] | None = None,
    epochs: int = 1,
) -> Dict[str, object]:
    """一個 epoch 結束時的判讀：翻轉、與增益的關係、判詞。"""
    flips = [i for i in range(len(pairs)) if neutral_margins[i] > 0 and phase_margins[i] <= 0]
    rows: List[Dict[str, float]] = []
    for i, (_, target) in enumerate(pairs):
        rows.append(
            {
                "pair": i,
                "gain": round(float(phase_gains[i]), 4),
                "neutral_margin": round(neutral_margins[i], 5),
                "phase_margin": round(phase_margins[i], 5),
                "margin_delta": round(phase_margins[i] - neutral_margins[i], 5),
                "phase_target_row": round(_row_sum(phase_core, target), 4),
            }
        )
        if cumulative_gains is not None:
            rows[i]["cum_gain"] = round(float(cumulative_gains[i]), 4)
    zeros = sum(1 for row in rows if row["gain"] < LOW_GAIN)
    flipped_low = sum(1 for i in flips if rows[i]["gain"] < LOW_GAIN)
    return {
        "flips": flips,
        "rows": rows,
        "gain": {
            "min": round(min(phase_gains), 4),
            "max": round(max(phase_gains), 4),
            "mean": round(statistics.fmean(phase_gains), 4),
            "below_low": zeros,
            "below_low_base_rate": round(zeros / len(rows), 3) if rows else 0.0,
            "low_gain_threshold": LOW_GAIN,
        },
        "margin_mean": {
            "neutral": round(statistics.fmean(neutral_margins), 5),
            "phase": round(statistics.fmean(phase_margins), 5),
        },
        "gain_delta_correlation": round(
            _correlation([row["gain"] for row in rows], [row["margin_delta"] for row in rows]), 4
        ),
        "phase_rows_at_zero": sum(1 for row in rows if row["phase_target_row"] <= 0.0),
        "low_gain_share_of_flips": round(flipped_low / len(flips), 3) if flips else None,
        "verdict": _verdict(rows, flips),
        # margin 是累積的，所以「這一輪的增益」不是正確的自變數；累積增益才是。
        "cumulative_correlation": (
            round(
                _correlation(
                    [row["cum_gain"] for row in rows], [row["margin_delta"] for row in rows]
                ),
                4,
            )
            if cumulative_gains is not None
            else None
        ),
        "cumulative_below_neutral": (
            sum(1 for row in rows if row["cum_gain"] < float(epochs))
            if cumulative_gains is not None
            else None
        ),
        "cumulative_verdict": (
            _verdict(
                [
                    {
                        "gain": row["cum_gain"],
                        "margin_delta": row["margin_delta"],
                        "phase_margin": row["phase_margin"],
                    }
                    for row in rows
                ],
                flips,
                # 累積增益的量綱是 epochs×，門檻必須跟著放大；分界線取「中性會拿到的
                # 總量」（每輪 1.0），語義是「這個 cue 拿到的可塑性比中性少」。
                low_gain=float(epochs),
            )
            if cumulative_gains is not None
            else None
        ),
    }


def run(
    seed: int = 11, task_name: str = _downstream.DEFAULT_TASK, epochs: int = _downstream.EPOCHS
) -> Dict[str, object]:
    task = _downstream.TASKS[task_name]
    pairs = _downstream._pairs(task)
    n_samples = len(pairs)
    period = _downstream.natural_period()
    # 與協定 v6 一致：每個 epoch 剛好一個調制週期，所以多輪時增益逐 epoch 不同。
    phase_gains = _downstream._schedule(period, n_samples * epochs, step_per_period=n_samples)

    snapshots: Dict[int, Dict[str, Tuple[List[float], List[float], object]]] = {}

    def capture(side: str):
        def callback(epoch: int, core, per_pair: List[float]) -> None:
            snapshots.setdefault(epoch, {})[side] = (_margins(core, pairs), per_pair, core)

        return callback

    _train_logged([1.0] * len(phase_gains), seed, task, epochs, capture("neutral"))
    _train_logged(phase_gains, seed, task, epochs, capture("phase"))

    per_epoch: List[Dict[str, object]] = []
    running = [0.0] * n_samples
    for epoch in range(epochs):
        neutral_margins = snapshots[epoch]["neutral"][0]
        phase_margins, phase_pair_gains, phase_core = snapshots[epoch]["phase"]
        running = [total + gain for total, gain in zip(running, phase_pair_gains)]
        summary = _epoch_summary(
            neutral_margins, phase_margins, phase_pair_gains, pairs, phase_core, running, epoch + 1
        )
        per_epoch.append(
            {
                "epoch": epoch + 1,
                "flips": summary["flips"],
                "flip_count": len(summary["flips"]),
                "low_gain_share_of_flips": summary["low_gain_share_of_flips"],
                "gain": summary["gain"],
                "margin_mean": summary["margin_mean"],
                "gain_delta_correlation": summary["gain_delta_correlation"],
                "cumulative_correlation": summary["cumulative_correlation"],
                "cumulative_below_neutral": summary["cumulative_below_neutral"],
                "verdict": summary["verdict"],
                "cumulative_verdict": summary["cumulative_verdict"],
            }
        )

    final = _epoch_summary(
        snapshots[epochs - 1]["neutral"][0],
        snapshots[epochs - 1]["phase"][0],
        snapshots[epochs - 1]["phase"][1],
        pairs,
        snapshots[epochs - 1]["phase"][2],
        running,
        epochs,
    )
    rows = final["rows"]

    return {
        "seed": seed,
        "task": task_name,
        "epochs": epochs,
        "period_s": round(period, 3),
        "gain": final["gain"],
        "margin_mean": final["margin_mean"],
        "gain_delta_correlation": final["gain_delta_correlation"],
        "phase_rows_at_zero": final["phase_rows_at_zero"],
        "flips": final["flips"],
        "flipped_rows": [rows[i] for i in final["flips"]],
        "verdict": final["verdict"],
        "cumulative_correlation": final["cumulative_correlation"],
        "cumulative_below_neutral": final["cumulative_below_neutral"],
        "cumulative_verdict": final["cumulative_verdict"],
        "per_epoch": per_epoch,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--task", choices=sorted(_downstream.TASKS), default=_downstream.DEFAULT_TASK)
    ap.add_argument("--epochs", type=int, default=_downstream.EPOCHS)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    result = run(seed=args.seed, task_name=args.task, epochs=args.epochs)
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
    if result["epochs"] > 1:
        print("per epoch:")
        for row in result["per_epoch"]:
            share = row["low_gain_share_of_flips"]
            print(
                f"  epoch {row['epoch']}: flips {row['flip_count']:>2}  "
                f"low-gain among flips {'n/a' if share is None else f'{share:.2f}'}  "
                f"base rate {row['gain']['below_low_base_rate']:.2f}  "
                f"margin neutral {row['margin_mean']['neutral']:+.5f} / "
                f"phase {row['margin_mean']['phase']:+.5f}  "
                f"corr {row['gain_delta_correlation']:+.3f}  "
                f"cum corr {row['cumulative_correlation']:+.3f}  "
                f"{row['verdict']} / {row['cumulative_verdict']}"
            )
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
