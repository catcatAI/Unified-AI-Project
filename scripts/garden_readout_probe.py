#!/usr/bin/env python
"""GARDEN 讀出端的解析度：**為什麼下游實驗量不出名次**（儀器診斷）

§18.2 的下游實驗（neutral／phase／shuffled 三臂）失敗在儀器：候選之間 100% 同分。
這一支把「為什麼」量出來，並且**不修改生產程式碼**——先是假設，再有量測。

兩個候選解釋，分開量：

1. **幅度被丟掉**：`forward` 的稀疏路徑對整個 weight row 求和，所以同一組鍵
   confidence 1.0 與 0.1 送出一樣的電流。這一項可以直接量：兩次 `forward` 的
   輸出是否逐位相同。
2. **讀出被量化**：輸出是「脈衝次數 ÷ timesteps」，只有 `timesteps + 1` 種可能值。
   如果候選之間只差一點權重，它們要嘛一起發火、要嘛一起不發火——掃描閾值就會看到
   正確率在 0 與 1 之間跳，沒有中間值。

判詞

* ``readout-quantised-no-headroom``：整個閾值掃描只有 0 或 1，且幅度確實被丟掉。
  這是「量不到」，不是「沒有差別」——下游要另找讀出方式（或改讀出）。
* ``readout-has-headroom``：掃描出現中間值，代表這個任務本來就分得出名次，
  量不到就不是儀器的問題。
"""

# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L0-L11]
# =============================================================================

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from ai.garden.snn_core import TensorSNNCore  # noqa: E402

N_PAIRS = 16
NOISE_BITS = 3
EPOCHS = 2
LEARNING_RATE = 0.1
TARGET_STRENGTH = 0.35
TIMESTEPS = 16
TOP_K_RATIO = 0.5
SEED = 11
THRESHOLDS = (0.03, 0.05, 0.08, 0.1, 0.12, 0.15, 0.18, 0.2, 0.25)


def _pairs() -> List[Tuple[List[str], str]]:
    """共享雜訊鍵 → 候選之間真的有干擾，不是各玩各的完美檢索。"""
    return [
        ([f"cue{i:02d}"] + [f"n{i % NOISE_BITS}"] * NOISE_BITS, f"t{i:02d}") for i in range(N_PAIRS)
    ]


def _train(threshold: float) -> TensorSNNCore:
    core = TensorSNNCore(threshold=threshold, timesteps=TIMESTEPS)
    rng = random.Random(SEED)
    pairs = _pairs()
    for _ in range(EPOCHS):
        order = pairs[:]
        rng.shuffle(order)
        for inputs, target in order:
            core.hebbian_update(
                {key: 1.0 for key in inputs},
                {target: 1.0},
                lr=LEARNING_RATE,
                target_strength=TARGET_STRENGTH,
            )
    return core


def _rank(core: TensorSNNCore) -> Dict[str, float]:
    hits, ties = 0, 0
    for i, (inputs, target) in enumerate(_pairs()):
        out = core.forward({key: 1.0 for key in inputs}, top_k_ratio=TOP_K_RATIO)
        correct = out.get(target, 0.0)
        rivals = [out.get(f"t{j:02d}", 0.0) for j in range(N_PAIRS) if j != i]
        best = max(rivals) if rivals else 0.0
        if correct > best:
            hits += 1
        elif correct == best:
            ties += 1
    return {"hit_rate": round(hits / N_PAIRS, 3), "tie_rate": round(ties / N_PAIRS, 3)}


def _magnitude_dropped(core: TensorSNNCore) -> Dict[str, object]:
    """同一組鍵，只把周邊鍵的 confidence 從 1.0 降到 0.1。"""
    keys = ["cue00"] + ["n0"] * NOISE_BITS
    loud = core.forward({key: 1.0 for key in keys}, top_k_ratio=TOP_K_RATIO)
    quiet = core.forward({keys[0]: 1.0, **{key: 0.1 for key in keys[1:]}}, top_k_ratio=TOP_K_RATIO)
    delta = sum(abs(loud.get(k, 0.0) - quiet.get(k, 0.0)) for k in set(loud) | set(quiet))
    return {"identical": loud == quiet, "max_delta": round(delta, 6)}


def _verdict(sweep: Sequence[Dict[str, float]], dropped: bool, empty: bool) -> str:
    if empty:
        return "no-output-above-threshold"
    settled = all(panel["hit_rate"] in (0.0, 1.0) for panel in sweep)
    if dropped and settled:
        return "readout-quantised-no-headroom"
    return "readout-has-headroom"


def run() -> Dict[str, object]:
    sweep = []
    for threshold in THRESHOLDS:
        core = _train(threshold)
        panel = _rank(core)
        panel["threshold"] = threshold
        sweep.append(panel)

    # 幅度這一項在任一閾值都量得出來（權重相同、只換 confidence）。
    dropped = bool(_magnitude_dropped(_train(0.1))["identical"])
    empty = all(panel["hit_rate"] == 0.0 and panel["tie_rate"] == 1.0 for panel in sweep)
    intermediate = [p for p in sweep if 0.0 < p["hit_rate"] < 1.0]

    return {
        "pairs": N_PAIRS,
        "noise_bits": NOISE_BITS,
        "timesteps": TIMESTEPS,
        "thresholds": list(THRESHOLDS),
        "sweep": sweep,
        "magnitude_dropped": dropped,
        "distinct_output_values": TIMESTEPS + 1,
        "intermediate_thresholds": [p["threshold"] for p in intermediate],
        "verdict": _verdict(sweep, dropped, empty),
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    result = run()
    print(f"output values possible: {result['distinct_output_values']} (spikes / timesteps)")
    print(f"magnitude dropped by forward: {result['magnitude_dropped']}")
    for panel in result["sweep"]:  # type: ignore[union-attr]
        print(
            f"  threshold {panel['threshold']:<5} hit {panel['hit_rate']:<5} "
            f"tie {panel['tie_rate']}"
        )
    print(f"intermediate thresholds: {result['intermediate_thresholds']}")
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
