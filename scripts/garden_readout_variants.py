#!/usr/bin/env python
"""三種讀出的比較：換讀出能不能讓下游任務問得出來？（改生產前先量）

§19 量到：脈衝次數讀出只有 17 段解析度，掃閾值時正確率在 0 與 1 之間跳。這裡問
下一個問題——**換一種讀出**（連續膜電位、首發脈衝時間）會不會讓候選之間出現
真正的名次。

三種讀出，同一批權重、同一個輸入：

* ``spike_count``：`forward` 目前的做法（脈衝次數 ÷ timesteps）；
* ``potential``：每個時間步更新後的膜電位累加（未發火者也留值）；
* ``first_spike``：第一次發火的時間（越早越強，取負值方便排名）。

判詞

* ``continuous-readout-resolves-and-ranks``：連續讀出破除了同分，且正確率高於
  基線；
* ``continuous-breaks-ties-but-no-graded-signal``：同分破了，但正確目標沒有排到
  前面——問題不在讀出，而在**權重本身沒有分級訊號**；
* ``continuous-readout-also-degenerate``：換讀出也沒差（仍然全部同分）。
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
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from ai.garden import snn_core  # noqa: E402
from ai.garden.snn_core import TensorSNNCore  # noqa: E402

N_PAIRS = 16
NOISE_BITS = 3
EPOCHS = 2
LEARNING_RATE = 0.1
TARGET_STRENGTH = 0.35
TIMESTEPS = 16
# 閾值決定「誰發火」：太低全部發（沒有資訊），太高全部不發（也沒有資訊）。
# 掃描才看得到讀出之間真正的差異。
THRESHOLDS = (0.05, 0.1, 0.15, 0.2, 0.25, 0.3)
TOP_K_RATIO = 0.5
SEED = 11


def _pairs() -> List[Tuple[List[str], str]]:
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


def _direct(core: TensorSNNCore, input_keys: Dict[str, float]) -> Dict[str, float]:
    """一步讀出：``W · a``，完全不做脈衝動力學。

    ``potential`` 讀出是 16 個時間步的膜電位累積，等於在無向權重圖上做擴散：權重一強，
    幾個時間步之後整個連通分量都被填到同一個值，所有 target 的電位相等，top-1 一律判
    miss。實測 structured 任務 ep1 是 1.000，ep3 起變 0.000，而**同一批權重**用一步讀出
    在 ep1/3/5 都是 1.000——所以塌的是讀出，不是權重。
    """
    V = core.vocab_size
    if not input_keys or core._W is None or V == 0:
        return {}
    W = core._W[:V, :V]
    a = core._init_activations(input_keys, None)
    if float(a.sum()) == 0.0:
        return {}
    values = W @ a if W.ndim == 2 else a * W
    result: Dict[str, float] = {}
    for idx in snn_core._nonzero_indices(values).tolist():
        key = core._idx_to_key[idx] if isinstance(core._idx_to_key, list) else core._idx_to_key[idx]
        result[key] = float(values[idx])
    return result


def _forward(core: TensorSNNCore, input_keys: Dict[str, float], readout: str) -> Dict[str, float]:
    """與 `forward` 同一個 LIF 迴圈，只換最後的讀出（候選，不動生產程式碼）。"""
    if readout == "direct":
        return _direct(core, input_keys)
    V = core.vocab_size
    if not input_keys or core._W is None or V == 0:
        return {}
    W = core._W[:V, :V]
    a = core._init_activations(input_keys, None)
    if a.sum() == 0.0:
        return {}

    threshold = max(0.01, core.base_threshold)
    potential = core._new_zeros(V)
    cumulative = core._new_zeros(V)
    membrane = core._new_zeros(V)
    first = core._new_zeros(V)
    seen = core._new_zeros(V)
    max_active = max(1, int(V * TOP_K_RATIO))

    for t in range(core.timesteps):
        potential, spikes, _ = core._compute_timestep(a, W, potential, t, threshold, max_active)
        membrane = membrane + potential
        spike_idx = snn_core._nonzero_indices(spikes).tolist()
        for idx in spike_idx:
            if float(seen[idx]) == 0.0:
                first[idx] = -float(t)  # 越早發火越大
                seen[idx] = 1.0
        a = spikes * (core.decay**t)
        cumulative += spikes

    values = {"spike_count": cumulative, "potential": membrane, "first_spike": first}[readout]
    result: Dict[str, float] = {}
    for idx in snn_core._nonzero_indices(values).tolist():
        result[core._idx_to_key[idx]] = float(values[idx]) / (
            core.timesteps if readout == "spike_count" else 1.0
        )
    return result


def _rank(readout: str, weights: Dict[str, Any]) -> Dict[str, float]:
    hits, ties = 0, 0
    for i, (inputs, target) in enumerate(_pairs()):
        out = weights[readout]({key: 1.0 for key in inputs})
        correct = out.get(target)
        if correct is None:
            continue
        rivals = [out.get(f"t{j:02d}") for j in range(N_PAIRS) if j != i]
        rivals = [r for r in rivals if r is not None]
        best = max(rivals) if rivals else float("-inf")
        if correct > best:
            hits += 1
        elif correct == best:
            ties += 1
    return {"hit_rate": round(hits / N_PAIRS, 3), "tie_rate": round(ties / N_PAIRS, 3)}


def _verdict(sweep: Sequence[Dict[str, Any]]) -> str:
    """逐閾值比較：連續讀出是否在基線失敗的地方排得出來。"""
    rescued = False
    broke_ties = False
    for row in sweep:
        baseline = row["panels"]["spike_count"]
        continuous = [row["panels"]["potential"], row["panels"]["first_spike"]]
        if any(p["tie_rate"] < baseline["tie_rate"] for p in continuous):
            broke_ties = True
        if max(p["hit_rate"] for p in continuous) > baseline["hit_rate"] + 0.25:
            rescued = True
    if rescued:
        return "continuous-readout-rescues-ranking"
    if broke_ties:
        return "continuous-breaks-ties-but-no-better-ranking"
    return "continuous-readout-also-degenerate"


def run() -> Dict[str, object]:
    sweep: List[Dict[str, Any]] = []
    spread = 0.0
    for threshold in THRESHOLDS:
        core = _train(threshold)
        closures = {
            "spike_count": lambda keys: core.forward(keys, top_k_ratio=TOP_K_RATIO),
            "potential": lambda keys: _forward(core, keys, "potential"),
            "first_spike": lambda keys: _forward(core, keys, "first_spike"),
        }
        sweep.append(
            {
                "threshold": threshold,
                "panels": {name: _rank(name, closures) for name in closures},
            }
        )
        if threshold == THRESHOLDS[-1]:
            # 權重層：Oja 的 target_strength 把每一列壓到同一個高度時，
            # 任何讀出都沒有東西可排。記下來當解釋。
            V = core.vocab_size
            row_sums = [
                float(core._W[idx, :V].sum())
                for i in range(N_PAIRS)
                for idx in [core._key_to_idx.get(f"t{i:02d}")]
                if idx is not None
            ]
            spread = round(max(row_sums) - min(row_sums), 6) if row_sums else 0.0

    return {
        "pairs": N_PAIRS,
        "timesteps": TIMESTEPS,
        "thresholds": list(THRESHOLDS),
        "sweep": sweep,
        "target_row_sum_spread": spread,
        "verdict": _verdict(sweep),
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    result = run()
    for row in result["sweep"]:  # type: ignore[union-attr]
        panels = row["panels"]
        print(
            f"threshold {row['threshold']:<5} "
            f"spike {panels['spike_count']['hit_rate']:<5} "
            f"potential {panels['potential']['hit_rate']:<5} "
            f"first_spike {panels['first_spike']['hit_rate']}"
        )
    print(f"target row-sum spread: {result['target_row_sum_spread']}")
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
