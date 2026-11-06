#!/usr/bin/env python
"""C-logit：相位有沒有改變**模型自己的機率分布**？（`al_c_param.py` 的下一級）

C-param 改的是請求參數（temperature/max_tokens）：換一個模型，耦合就消失，
因為 AL 的狀態從來沒有碰到模型的輸出。這一支改的是模型在解碼時的 logits，
所以問題變成可量測的：

    同一個 prompt、同一個 temperature，只換相位，
    模型對「高喚醒詞」與「低喚醒詞」的機率會不會交換？

方法
----
1. 用**真的**本地模型（`data/models/*.gguf`，llama.cpp）對同一個 prompt 跑
   一次 forward，用 `logits_processor` 攔下最後一個位置的 logits（151,936 維）。
2. 用 `core/life/al_logit_bias.phase_bias` 由相位算出兩組語意詞彙的偏移，
   套用在攔下來的 logits 上。
3. 量三件事：詞彙內的機率差 `p(energy) − p(calm)`、相對基線的 KL、以及
   機率差是否隨 activation 單調（Pearson r）。

控制組（缺一不可）
------------------
- **中點不動**：activation = 0.5 → 偏移全為 0 → logits **逐位相同**（KL 恰好 0）。
- **置換**：把相位與 activation 打散 → 機率差仍有變異，但不再隨相位走。
- **偽造品**：activation 由 wall-clock 正弦產生 → 同一相位重跑得到不同偏移。

它**沒有**量什麼
----------------
沒有量「取樣出來的句子變成什麼」。logits 是分布，句子是分布的樣本；從分布
差異推句子差異需要多次取樣與檢定。這裡量的是分布本身，而且分布是模型的直接
輸出，不是推論。
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

from core.life.al_logit_bias import DEFAULT_STRENGTH, LogitBias, apply_to, phase_bias  # noqa: E402
from core.life.al_oscillator import Oscillator, natural_period  # noqa: E402

DEFAULT_MODEL = REPO_ROOT / "data" / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
PROMPT = "The room felt"
ENERGY_WORDS = (" excited", " tense", " urgent")
CALM_WORDS = (" calm", " quiet", " still")
N_PHASES = 8
KL_MIN = 0.01
R_MIN = 0.90


def _softmax(values: Sequence[float]) -> List[float]:
    top = max(values)
    exps = [math.exp(v - top) for v in values]
    total = sum(exps)
    return [e / total for e in exps]


def _kl(p: Sequence[float], q: Sequence[float], eps: float = 1e-12) -> float:
    return sum(pi * math.log((pi + eps) / (qi + eps)) for pi, qi in zip(p, q) if pi > 0.0)


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    vy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return cov / (vx * vy) if vx > 0 and vy > 0 else 0.0


class _Recorder:
    """攔下最後一個位置的 logits；套用偏移後交回去，讓模型照用它解碼。"""

    def __init__(self) -> None:
        self.logits: Optional[List[float]] = None
        self.bias: Optional[LogitBias] = None

    def __call__(self, input_ids, scores):
        import numpy as np

        # 必須**回傳新的陣列**：就地改 `scores` 不會被取用（第一版同時犯了兩個
        # 錯——改複本又回傳原陣列，且記錄的是偏移前的值，KL 於是恰好 0）。
        array = np.array(scores, copy=True)
        flat = array[-1] if array.ndim == 2 else array
        if self.bias is not None:
            for token_id, delta in self.bias.biases.items():
                if 0 <= token_id < flat.shape[0]:
                    flat[token_id] += delta
        if self.logits is None:
            # 記錄**套用後**的值：要量的是模型的分布，不是偏移前的中間量。
            self.logits = [float(x) for x in flat]
        return array


def _capture(llm, bias: Optional[LogitBias]) -> List[float]:
    rec = _Recorder()
    rec.bias = bias
    llm(PROMPT, max_tokens=1, logits_processor=[rec])
    if rec.logits is None:
        raise RuntimeError("logits_processor was never called")
    return rec.logits


def run(model_path: Path = DEFAULT_MODEL, n_phases: int = N_PHASES) -> Dict[str, object]:
    from llama_cpp import Llama

    llm = Llama(
        model_path=str(model_path),
        n_ctx=128,
        n_gpu_layers=0,
        verbose=False,
    )
    energy_ids = sorted({int(llm.tokenize(w.encode())[0]) for w in ENERGY_WORDS})
    calm_ids = sorted({int(llm.tokenize(w.encode())[0]) for w in CALM_WORDS})

    baseline_logits = _capture(llm, None)
    baseline_probs = _softmax(baseline_logits)

    def mass(probs: Sequence[float]) -> Dict[str, float]:
        return {
            "energy": sum(probs[i] for i in energy_ids),
            "calm": sum(probs[i] for i in calm_ids),
        }

    # 八個相位（真的振盪器）
    period = natural_period()
    osc = Oscillator()
    osc.step(period * 3.0)
    points: List[tuple] = []
    for i in range(n_phases):
        target = (i + 0.5) / n_phases
        for _ in range(int(period / 0.05) + 200):
            osc.step(0.05)
            if abs(osc.phase - target) < 0.01:
                break
        points.append((round(osc.phase, 4), round(osc.activation, 6)))

    rows = []
    for phase, activation in points:
        bias = phase_bias(activation, energy_ids, calm_ids)
        logits = _capture(llm, bias)
        probs = _softmax(logits)
        m = mass(probs)
        rows.append(
            {
                "phase": phase,
                "activation": activation,
                "p_energy": round(m["energy"], 6),
                "p_calm": round(m["calm"], 6),
                "delta": round(m["energy"] - m["calm"], 6),
                "kl": round(_kl(probs, baseline_probs), 6),
            }
        )

    base_mass = mass(baseline_probs)
    deltas = [r["delta"] for r in rows]
    activations = [r["activation"] for r in rows]
    kls = [r["kl"] for r in rows]

    # 控制組：中點（偏移全 0）→ logits 逐位相同。
    neutral = phase_bias(0.5, energy_ids, calm_ids)
    neutral_logits = _capture(llm, neutral)
    bit_identical = neutral_logits == baseline_logits

    # 置換：同樣的 activation 分佈，但與相位無關。
    seed, idx = 20261107, list(range(len(rows)))
    for i in range(len(idx) - 1, 0, -1):
        seed = (1103515245 * seed + 12345) % (2**31)
        j = seed % (i + 1)
        idx[i], idx[j] = idx[j], idx[i]
    perm_deltas = [deltas[k] for k in idx]
    r = _pearson(activations, deltas)
    r_perm = _pearson(activations, perm_deltas)

    # 偽造：wall-clock 正弦 → 同一相位重跑不同偏移。
    t0 = time.time()
    a0 = 0.5 + 0.5 * math.sin(2 * math.pi * t0 / period)
    time.sleep(0.01)
    a1 = 0.5 + 0.5 * math.sin(2 * math.pi * time.time() / period)
    clock_reproducible = abs(a0 - a1) < 1e-12

    checks = {
        "distribution_moved": bool(max(kls) >= KL_MIN),
        "flips_with_phase": bool(min(deltas) < 0.0 < max(deltas)),
        "monotone_in_activation": bool(r > R_MIN),
        "neutral_is_bit_identical": bool(bit_identical),
        "not_random": bool(abs(r_perm) < 0.5),
    }
    admissible = all(checks.values()) and not clock_reproducible

    return {
        "model": model_path.name,
        "prompt": PROMPT,
        "vocab": len(baseline_logits),
        "energy_tokens": energy_ids,
        "calm_tokens": calm_ids,
        "strength": DEFAULT_STRENGTH,
        "baseline": {
            "p_energy": round(base_mass["energy"], 6),
            "p_calm": round(base_mass["calm"], 6),
        },
        "rows": rows,
        "kl_range": [round(min(kls), 6), round(max(kls), 6)],
        "correlation": round(r, 4),
        "permutation_correlation": round(r_perm, 4),
        "clock_forgery_reproducible": bool(clock_reproducible),
        "checks": checks,
        "verdict": "phase-reaches-logits" if admissible else "phase-does-not-reach-logits",
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    result = run(args.model)
    print(f"model {result['model']}  vocab {result['vocab']}")
    print(
        f"baseline p_energy={result['baseline']['p_energy']} p_calm={result['baseline']['p_calm']}"
    )
    for row in result["rows"]:
        print(
            f"  phase {row['phase']:.3f} act {row['activation']:.3f} "
            f"p_e {row['p_energy']:.4f} p_c {row['p_calm']:.4f} "
            f"delta {row['delta']:+.4f} kl {row['kl']:.4f}"
        )
    print(
        f"KL range {result['kl_range']}  r {result['correlation']} (perm {result['permutation_correlation']})"
    )
    for name, ok in result["checks"].items():
        print(f"{'ok ' if ok else 'FAIL'} {name}")
    print(f"verdict: {result['verdict']}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"report: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
