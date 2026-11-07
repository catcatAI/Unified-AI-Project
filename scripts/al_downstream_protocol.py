#!/usr/bin/env python
"""固定評分協定 v3：相位調制到底有沒有用？（跨 regime × 任務族）

v2 只跑兩個 regime、一個任務族，結論是 `regime-dependent-no-claim`。v3 的改動是
**增加獨立維度**，不是再調參數：

* regime 矩陣擴成 epochs ∈ {1, 3, 5}；
* 任務族擴成兩個、干擾結構不同：
  - ``hard``：所有 cue 共用一個噪聲位，每 cue 有自己的 token；
  - ``many_to_one``：兩個 cue 共用同一個 target（干擾真的存在，但答案仍可學）。

協定（寫死在常數裡，不從命令列給）

1. **讀出**：膜電位（§20：脈衝次數在同權重下無鑑別力）；
2. **難度校準**：每個（任務族 × regime）沿固定階梯 × lr 格點，取第一個讓**中性臂**
   top-1 落在 [0.30, 0.70] 的組合；校準不到就標 ``uninformative``（天花板與地板都
   不算證據）；
3. **種子**：12 個固定；校準另用 3 個、**與評估種子互斥**（v5 起）；
4. **控制組**：``shuffled``——**同一組增益**打亂順序，分離「平均增益」與「時序」；
5. **判詞**：margin **與** top-1 必須同向；只升 margin 不算贏。

v4 只是**修儀器**：候選 label 由 pair 索引拼字串改成由任務的目標 label 集決定。
多對一任務裡一個 label 對應多個 pair，索引拼法會讓半數 pair 的 rivals 全空
（直接判 miss，命中率硬性截在 0.5），另一半把自己的 label 當對手。v3 的
``many_to_one`` 全部數字因此作廢，必須重跑。

整體判詞

* ``insufficient-informative-regimes``：可下結論的格 < 2；
* ``mechanism-benefit-consistent``：所有可下結論的格都是 `phase-beats-matched-mean`；
* ``no-mechanism-benefit-consistent``：所有格都沒贏過 neutral；
* ``mechanism-harm-consistent``：所有可下結論的格都是 `phase-loses-to-matched-mean`；
* ``regime-dependent-no-claim``：其餘（方向不一致）。
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
from typing import Dict, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

PROTOCOL_VERSION = "al-downstream-v5"
READOUT = "potential"
EPOCHS_MATRIX = (1, 3, 5)
LR_GRID = (0.005, 0.008, 0.01, 0.015, 0.02, 0.03, 0.05)
HIT_RANGE = (0.30, 0.70)
SEEDS = (11, 23, 37, 41, 53, 67, 79, 83, 97, 101, 113, 127)
# 校準種子必須與評估種子**互斥**：共用種子等於先看答案再出題，被校準到 [0.30, 0.70]
# 的中性臂會在評估時被同一批種子稍微優待（v4 及以前就是這樣）。
CALIBRATION_SEEDS = (211, 223, 241)

# 難度階梯：每個任務族由易到難，第一個校準得動的就採用。
FAMILIES: Dict[str, List[Dict[str, object]]] = {
    "hard": [
        {"pairs": 48, "noise_bits": 3, "shared": True},
        {"pairs": 96, "noise_bits": 2, "shared": True},
        {"pairs": 144, "noise_bits": 1, "shared": True},
    ],
    "many_to_one": [
        {"pairs": 48, "noise_bits": 3, "shared": True, "target_group": 24},
        {"pairs": 48, "noise_bits": 3, "shared": True, "target_group": 12},
        {"pairs": 96, "noise_bits": 2, "shared": True, "target_group": 24},
    ],
}

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
assert not set(CALIBRATION_SEEDS) & set(SEEDS), "calibration seeds must not leak into evaluation"


def _task(family: str, step: Dict[str, object], lr: float) -> Dict[str, object]:
    base = dict(_downstream.TASKS["hard"] if family == "hard" else _downstream.TASKS[family])
    base.update(step)
    base["lr"] = lr
    return base


def calibrate(family: str, epochs: int) -> Dict[str, object]:
    """沿該任務族的固定階梯 × lr 格點，找第一個讓中性臂落在中段的組合。"""
    trials: List[Dict[str, object]] = []
    for step in FAMILIES[family]:
        for lr in LR_GRID:
            task = _task(family, step, lr)
            pairs = int(task["pairs"])  # type: ignore[arg-type]
            hits = []
            for seed in CALIBRATION_SEEDS:
                core = _downstream._train([1.0] * (pairs * epochs), seed, task, epochs)
                hits.append(_downstream._evaluate(core, task)["hit_rate"])
            mean_hit = statistics.fmean(hits)
            entry = dict(step)
            entry.update(lr=lr, neutral_hit_rate=round(mean_hit, 3))
            trials.append(entry)
            if HIT_RANGE[0] <= mean_hit <= HIT_RANGE[1]:
                return {
                    "informative": True,
                    "step": dict(step),
                    "lr": lr,
                    "neutral_hit_rate": round(mean_hit, 3),
                    "trials": trials,
                }
    return {"informative": False, "trials": trials}


def evaluate_cell(family: str, calibration: Dict[str, object], epochs: int) -> Dict[str, object]:
    task = _task(family, calibration["step"], float(calibration["lr"]))  # type: ignore[arg-type]
    pairs = int(task["pairs"])  # type: ignore[arg-type]
    period = _downstream.natural_period()
    phase_gains = _downstream._schedule(period, pairs * epochs)

    rows: Dict[str, List[Dict[str, float]]] = {"neutral": [], "phase": [], "shuffled": []}
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
        "family": family,
        "task": {key: value for key, value in task.items() if key != "threshold"},
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


NO_BENEFIT = (
    "no-downstream-difference",
    "margin-gain-without-hit-gain",
    "timing-does-not-matter-only-gain",
    "phase-loses-to-matched-mean",
)
HARM = "phase-loses-to-matched-mean"


def overall_verdict(cells: Sequence[Dict[str, object]]) -> str:
    informative = [cell for cell in cells if cell["informative"]]
    if len(informative) < 2:
        return "insufficient-informative-regimes"
    verdicts = [cell["cell"]["verdict"] for cell in informative]  # type: ignore[index]
    if all(v == "phase-beats-matched-mean" for v in verdicts):
        return "mechanism-benefit-consistent"
    if all(v == HARM for v in verdicts):
        # 一致的負結果也是一種結論；不能只因為方向是負的就退回「沒差」。
        return "mechanism-harm-consistent"
    if all(v in NO_BENEFIT for v in verdicts):
        return "no-mechanism-benefit-consistent"
    return "regime-dependent-no-claim"


def run() -> Dict[str, object]:
    cells: List[Dict[str, object]] = []
    for family in FAMILIES:
        for epochs in EPOCHS_MATRIX:
            calibration = calibrate(family, epochs)
            if not calibration["informative"]:
                cells.append(
                    {
                        "family": family,
                        "epochs": epochs,
                        "informative": False,
                        "calibration": calibration,
                    }
                )
                continue
            cell = evaluate_cell(family, calibration, epochs)
            cells.append(
                {
                    "family": family,
                    "epochs": epochs,
                    "informative": True,
                    "calibration": calibration,
                    "cell": cell,
                }
            )

    return {
        "protocol": PROTOCOL_VERSION,
        "readout": READOUT,
        "epochs_matrix": list(EPOCHS_MATRIX),
        "lr_grid": list(LR_GRID),
        "hit_range": list(HIT_RANGE),
        "families": {name: steps for name, steps in FAMILIES.items()},
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
                f"{t.get('pairs')}@{t['lr']}: {t['neutral_hit_rate']}"
                for t in cal["trials"][-3:]  # type: ignore[index]
            )
            print(f"{cell['family']:<12} ep{cell['epochs']}: UNINFORMATIVE (…{tops})")
            continue
        body = cell["cell"]
        arms = body["arms"]
        print(
            f"{cell['family']:<12} ep{cell['epochs']}: lr {body['task'].get('lr')} "
            f"neutral top-1 {cal['neutral_hit_rate']}  "
            f"N {arms['neutral']['margin_mean']:+.5f}/{arms['neutral']['hit_rate_mean']}  "
            f"P {arms['phase']['margin_mean']:+.5f}/{arms['phase']['hit_rate_mean']}  "
            f"S {arms['shuffled']['margin_mean']:+.5f}/{arms['shuffled']['hit_rate_mean']}  "
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
