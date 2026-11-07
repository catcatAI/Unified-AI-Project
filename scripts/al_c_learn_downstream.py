#!/usr/bin/env python
"""下游問題（第三版）：**這樣學有比較好嗎？**——用連續讀出，三臂增益匹配

前兩版失敗在儀器（§18.2、§19）。§20 量到：把讀出換成膜電位，排名就出現了
（脈衝次數讀出在同樣的權重上完全排不出來）。這一支用那個讀出回答原本的問題。

三臂，**平均增益匹配**，只差在「何時給多少增益」：

* ``neutral``：每次 1.0；
* ``phase``：真振盪器走一整個週期，逐樣本取 ``learning_gain()``；
* ``shuffled``：**同一組增益**、打亂順序（同一個種子）。

``shuffled`` 是關鍵控制組：如果 ``phase`` 只是贏在平均增益，打亂後也會贏；只有
「時機」真的有意義時，``phase`` 才該贏過 ``shuffled``。

量的是 held-out 名次：給 cue，``potential`` 讀出下正確 target 的**分數差**
（margin，連續值，不受脈衝量化影響）與 top-1 命中率。

判詞

* ``phase-beats-matched-mean``：``phase`` 在多數種子上同時贏過 ``neutral`` 與
  ``shuffled``，且差距大於種子間散佈；
* ``timing-does-not-matter-only-gain``：``phase`` 贏 ``neutral`` 但贏不過 ``shuffled``
  ——好處來自平均增益，不是時機；
* ``no-downstream-difference``：其餘。
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
from core.life.al_learning_gate import learning_gain  # noqa: E402
from core.life.al_oscillator import Oscillator, natural_period  # noqa: E402

READOUT_SCRIPT = Path(__file__).with_name("garden_readout_variants.py")


def _load_readouts():
    spec = importlib.util.spec_from_file_location("garden_readout_variants", READOUT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {READOUT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_readouts = _load_readouts()

N_PAIRS = 16
NOISE_BITS = 3
EPOCHS = 1
LEARNING_RATE = 0.05
TARGET_STRENGTH = 0.35
THRESHOLD = 0.25
TOP_K_RATIO = 0.5
SEEDS = (11, 23, 37, 41, 53, 67)


def _pairs() -> List[Tuple[List[str], str]]:
    return [
        ([f"cue{i:02d}"] + [f"n{i % NOISE_BITS}"] * NOISE_BITS, f"t{i:02d}") for i in range(N_PAIRS)
    ]


def _schedule(period: float, n: int) -> List[float]:
    """真振盪器走一整個週期，逐樣本取增益。"""
    osc = Oscillator()
    osc.step(period * 3.0)
    gains: List[float] = []
    dt = period / n
    for _ in range(n):
        osc.step(dt)
        gains.append(learning_gain(osc.activation).gain)
    return gains


def _train(gains: Sequence[float], seed: int) -> TensorSNNCore:
    core = TensorSNNCore(threshold=THRESHOLD, timesteps=_readouts.TIMESTEPS)
    rng = random.Random(seed)
    pairs = _pairs()
    for _ in range(EPOCHS):
        order = pairs[:]
        rng.shuffle(order)
        for (inputs, target), gain in zip(order, gains):
            core.hebbian_update(
                {key: 1.0 for key in inputs},
                {target: 1.0},
                lr=LEARNING_RATE,
                target_strength=TARGET_STRENGTH,
                plasticity=gain,
            )
    return core


def _evaluate(core: TensorSNNCore) -> Dict[str, float]:
    hits, margins = 0, []
    for i, (inputs, target) in enumerate(_pairs()):
        out = _readouts._forward(core, {key: 1.0 for key in inputs}, "potential")
        correct = out.get(target)
        rivals = [out.get(f"t{j:02d}") for j in range(N_PAIRS) if j != i]
        rivals = [value for value in rivals if value is not None]
        if correct is None or not rivals:
            margins.append(0.0)
            continue
        best = max(rivals)
        margins.append(correct - best)
        if correct > best:
            hits += 1
    return {"hit_rate": hits / N_PAIRS, "margin": statistics.fmean(margins)}


def _verdict(rows: Dict[str, List[Dict[str, float]]]) -> str:
    phase = [row["margin"] for row in rows["phase"]]
    neutral = [row["margin"] for row in rows["neutral"]]
    shuffled = [row["margin"] for row in rows["shuffled"]]
    beats_both = sum(1 for p, n, s in zip(phase, neutral, shuffled) if p > n and p > s)
    spread = statistics.pstdev(neutral)
    gain = statistics.fmean(phase) - statistics.fmean(neutral)
    beats_shuffled = statistics.fmean(phase) - statistics.fmean(shuffled)
    if beats_both > len(phase) / 2 and gain > spread and beats_shuffled > spread:
        return "phase-beats-matched-mean"
    if gain > spread and beats_shuffled <= spread:
        return "timing-does-not-matter-only-gain"
    return "no-downstream-difference"


def run(seeds: Sequence[int] = SEEDS) -> Dict[str, object]:
    period = natural_period()
    n_samples = N_PAIRS * EPOCHS
    phase_gains = _schedule(period, n_samples)

    rows: Dict[str, List[Dict[str, float]]] = {"neutral": [], "phase": [], "shuffled": []}
    gain_means: Dict[str, float] = {}
    for seed in seeds:
        shuffled = phase_gains[:]
        random.Random(seed * 7919).shuffle(shuffled)
        arms = {"neutral": [1.0] * n_samples, "phase": phase_gains, "shuffled": shuffled}
        for name, gains in arms.items():
            rows[name].append(_evaluate(_train(gains, seed)))
            gain_means.setdefault(name, statistics.fmean(gains))

    summary = {
        name: {
            "margin_mean": round(statistics.fmean(r["margin"] for r in rows[name]), 5),
            "hit_rate_mean": round(statistics.fmean(r["hit_rate"] for r in rows[name]), 3),
            "gain_mean": round(gain_means[name], 4),
        }
        for name in rows
    }
    matched = abs(gain_means["phase"] - gain_means["neutral"]) <= 0.05

    return {
        "period_s": round(period, 3),
        "threshold": THRESHOLD,
        "epochs": EPOCHS,
        "seeds": list(seeds),
        "arms": summary,
        "gain_matched": bool(matched),
        "per_seed_margin": {name: [round(r["margin"], 5) for r in rows[name]] for name in rows},
        "verdict": _verdict(rows) if matched else "gain-not-matched",
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    result = run()
    for name, arm in result["arms"].items():  # type: ignore[union-attr]
        print(
            f"{name:<9} margin {arm['margin_mean']:+.5f}  hit {arm['hit_rate_mean']:.3f}  "
            f"gain {arm['gain_mean']:.3f}"
        )
    print(f"per-seed margin {result['per_seed_margin']}")
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
