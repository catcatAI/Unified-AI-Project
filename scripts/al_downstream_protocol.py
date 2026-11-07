#!/usr/bin/env python
"""固定評分協定：相位調制到底有沒有用？（唯一可用的判準）

§23 之後的問題不是「哪個數字對」，而是**量測本身可以被三個旋鈕翻轉**（讀出、剪枝
門檻、訓練量）。所以先固定協定，再只用協定下結論。

協定（寫死在常數裡，不從命令列給）

1. **讀出**：膜電位（§20 量到脈衝次數在同權重下完全無鑑別力）；
2. **任務**：`hard`（48 候選 + 共用噪聲位）；
3. **regime 矩陣**：epochs ∈ {1, 5}，兩個都要跑、**兩個都要報**（不允许挑）；
4. **難度校準**：每個 regime 先用中性臂在固定 lr 格點上校準，取第一個讓中性臂
   top-1 落在 [0.30, 0.70] 的 lr。校準不到就標 `uninformative`——該 regime 不能
   拿來下結論（天花板或地板都不算證據）；
5. **種子**：12 個固定種子；
6. **控制組**：`shuffled`（同增益打亂）；
7. **判詞**：`_verdict` 要求 margin **與** top-1 同向；只升 margin 不算贏。

整體判詞

* ``insufficient-informative-regimes``：可下結論的 regime 少於 2 個；
* ``mechanism-benefit-consistent``：所有可下結論的 regime 都是 `phase-beats-matched-mean`；
* ``no-mechanism-benefit-consistent``：所有可下結論的 regime 都沒有贏過 neutral；
* ``regime-dependent-no-claim``：其餘（方向不一致）。
"""

# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L0-L11]
# =============================================================================

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

PROTOCOL_VERSION = "al-downstream-v2"
READOUT = "potential"
EPOCHS_MATRIX = (1, 5)
# 難度階梯：候選數 × 噪聲位。先小後大，第一個讓中性臂落在中段的就採用。
# v1 只用固定任務 + lr 格點，結果 ep5 在任何 lr 都停在 0.979（結構上太容易）；
# 所以難度也必須是可校準的維度，而且用固定階梯、不是逐格硬調。
LADDER = ((48, 3), (96, 3), (96, 2), (144, 2), (144, 1))
LR_GRID = (0.005, 0.008, 0.01, 0.015, 0.02, 0.03, 0.05)
HIT_RANGE = (0.30, 0.70)
SEEDS = (11, 23, 37, 41, 53, 67, 79, 83, 97, 101, 113, 127)
CALIBRATION_SEEDS = (11, 23, 37)

DOWNSTREAM_SCRIPT = Path(__file__).with_name("al_c_learn_downstream.py")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_downstream = _load("al_c_learn_downstream", DOWNSTREAM_SCRIPT)

assert READOUT == "potential", "the protocol fixes the readout; change it here deliberately"


def calibrate(epochs: int) -> Dict[str, object]:
    """沿固定難度階梯 × lr 格點，找第一個讓中性臂落在中段的組合。"""
    base = dict(_downstream.TASKS["hard"])
    trials: List[Dict[str, object]] = []
    for pairs, noise_bits in LADDER:
        for lr in LR_GRID:
            task = dict(base)
            task.update(pairs=pairs, noise_bits=noise_bits, lr=lr)
            hits = []
            for seed in CALIBRATION_SEEDS:
                core = _downstream._train([1.0] * (pairs * epochs), seed, task, epochs)
                hits.append(_downstream._evaluate(core, task)["hit_rate"])
            mean_hit = statistics.fmean(hits)
            trials.append(
                {
                    "pairs": pairs,
                    "noise_bits": noise_bits,
                    "lr": lr,
                    "neutral_hit_rate": round(mean_hit, 3),
                }
            )
            if HIT_RANGE[0] <= mean_hit <= HIT_RANGE[1]:
                return {
                    "informative": True,
                    "pairs": pairs,
                    "noise_bits": noise_bits,
                    "lr": lr,
                    "neutral_hit_rate": round(mean_hit, 3),
                    "trials": trials,
                }
    return {"informative": False, "trials": trials}


def evaluate_cell(calibration: Dict[str, object], epochs: int) -> Dict[str, object]:
    task = dict(_downstream.TASKS["hard"])
    task.update(
        pairs=calibration["pairs"],
        noise_bits=calibration["noise_bits"],
        lr=calibration["lr"],
    )
    pairs = int(task["pairs"])  # type: ignore[arg-type]
    period = _downstream.natural_period()
    phase_gains = _downstream._schedule(period, pairs * epochs)

    rows: Dict[str, List[Dict[str, float]]] = {"neutral": [], "phase": [], "shuffled": []}
    import random

    for seed in SEEDS:
        shuffled = phase_gains[:]
        random.Random(seed * 7919).shuffle(shuffled)
        arms = {"neutral": [1.0] * (pairs * epochs), "phase": phase_gains, "shuffled": shuffled}
        for name, gains in arms.items():
            core = _downstream._train(gains, seed, task, epochs)
            rows[name].append(_downstream._evaluate(core, task))

    gains = {
        "neutral": 1.0,
        "phase": statistics.fmean(phase_gains),
        "shuffled": statistics.fmean(phase_gains),
    }
    matched = abs(gains["phase"] - gains["neutral"]) <= 0.05
    return {
        "pairs": calibration["pairs"],
        "noise_bits": calibration["noise_bits"],
        "lr": calibration["lr"],
        "epochs": epochs,
        "arms": {
            name: {
                "margin_mean": round(statistics.fmean(r["margin"] for r in rows[name]), 5),
                "hit_rate_mean": round(statistics.fmean(r["hit_rate"] for r in rows[name]), 3),
                "gain_mean": round(gains[name], 4),
            }
            for name in rows
        },
        "gain_matched": bool(matched),
        "verdict": _downstream._verdict(rows) if matched else "gain-not-matched",
    }


def overall_verdict(cells: Sequence[Dict[str, object]]) -> str:
    informative = [cell for cell in cells if cell["informative"]]
    if len(informative) < 2:
        return "insufficient-informative-regimes"
    verdicts = [cell["cell"]["verdict"] for cell in informative]  # type: ignore[index]
    if all(v == "phase-beats-matched-mean" for v in verdicts):
        return "mechanism-benefit-consistent"
    if all(
        v
        in (
            "no-downstream-difference",
            "margin-gain-without-hit-gain",
            "timing-does-not-matter-only-gain",
        )
        for v in verdicts
    ):
        return "no-mechanism-benefit-consistent"
    return "regime-dependent-no-claim"


def run() -> Dict[str, object]:
    cells: List[Dict[str, object]] = []
    for epochs in EPOCHS_MATRIX:
        calibration = calibrate(epochs)
        if not calibration["informative"]:
            cells.append({"epochs": epochs, "informative": False, "calibration": calibration})
            continue
        cell = evaluate_cell(calibration, epochs)
        cells.append(
            {"epochs": epochs, "informative": True, "calibration": calibration, "cell": cell}
        )

    return {
        "protocol": PROTOCOL_VERSION,
        "readout": READOUT,
        "ladder": [list(step) for step in LADDER],
        "epochs_matrix": list(EPOCHS_MATRIX),
        "lr_grid": list(LR_GRID),
        "hit_range": list(HIT_RANGE),
        "seeds": list(SEEDS),
        "cells": cells,
        "verdict": overall_verdict(cells),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    result = run()
    print(f"protocol: {result['protocol']}  readout {result['readout']}")
    for cell in result["cells"]:  # type: ignore[union-attr]
        cal = cell["calibration"]
        if not cell["informative"]:
            tops = ", ".join(
                f"{t['pairs']}/{t['noise_bits']}@lr{t['lr']}: {t['neutral_hit_rate']}"
                for t in cal["trials"]  # type: ignore[index]
            )
            print(f"epochs {cell['epochs']}: UNINFORMATIVE (neutral top-1 -> {tops})")
            continue
        body = cell["cell"]
        print(
            f"epochs {cell['epochs']}: pairs {body['pairs']} bits {body['noise_bits']} "
            f"lr {body['lr']} neutral top-1 {cal['neutral_hit_rate']}  "  # type: ignore[index]
            f"neutral {body['arms']['neutral']['margin_mean']:+.5f}/{body['arms']['neutral']['hit_rate_mean']}  "
            f"phase {body['arms']['phase']['margin_mean']:+.5f}/{body['arms']['phase']['hit_rate_mean']}  "
            f"shuffled {body['arms']['shuffled']['margin_mean']:+.5f}/{body['arms']['shuffled']['hit_rate_mean']}  "
            f"-> {body['verdict']}"
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
