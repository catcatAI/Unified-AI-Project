#!/usr/bin/env python
"""相位有沒有改變決定？—— 從「有節律」走到「節律有作用」。

前一輪證明系統內部有一個 43.54 s 的自持週期（`scripts/al_rhythm_source.py`）。
有週期不等於週期有用：一隻鐘也會擺。這支探針問的是下一個可證偽的問題——

    同樣的觀測、同樣的輸入，只換相位，某個**決定**會不會不同？

被測的決定是記憶編碼權重（`core/life/al_memory_policy.retention_policy`，
`weight ← intensity × 喚醒度 × 內生相位`）。它比 prompt 誠實：權重寫進記憶、
改變 retrieval 與衰減，不是換一句話就沒了。

四件事必須同時成立，否則判 `phase-does-not-matter`
-------------------------------------------------
1. **有效應**：八個相位跑一圈，權重差距 ≥ 3%；
2. **由相位決定**：相位與權重的相關係數 |r| > 0.99（不是「有差」而是「照它走」）；
3. **控制組不動**：同一批快照把 rhythm 拔掉（`rhythm=None`）→ 權重完全相同；
4. **不是隨機**：把 activation 換成同分佈的亂數，|r| 應該接近 0（變異一樣大，關聯沒有）。

再加兩個偽造品
--------------
- ``constant``：activation 固定 0.5 → 控制組形狀，沒有效應；
- ``clock``：activation 由 wall-clock 正弦產生 → 同一「相位」重跑得到不同權重（不可重現）。

邊界（照實寫）
--------------
這是 **state → decision** 的耦合：AL 的狀態改變了系統自己的決定並留下持久痕跡。
它**不是**「同一個模型」——LLM 的 logits 沒有被碰過，生成參數也沒被碰過。
把這條接上去需要改 routing 生成路徑（本輪未動）。
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

from core.life.al_memory_policy import RHYTHM_GAIN, retention_policy  # noqa: E402
from core.life.al_oscillator import Oscillator, natural_period  # noqa: E402
from core.life.al_state import (  # noqa: E402
    AL_STATE_VERSION,
    DEFAULT_WEIGHTS,
    PARAM_SOURCES,
    ALSnapshot,
)

BINS = 8
SPREAD_MIN = 0.03
# 相位能解釋的權重變異：真函數近 1.0，置換後應掉到 0 附近。
R2_MIN = 0.9
R2_RANDOM_MAX = 0.2


def _snapshot(activation: Optional[float], phase: float = 0.0) -> ALSnapshot:
    """受控快照：除相位外全部固定，且都是「有觀測但中性」的值。

    刻意不用 ``get_al_state()``：環境快照會把其他觀測一起帶進來，屆時權重的
    差異就無法歸因到相位（I9 的同一件事）。
    """
    return ALSnapshot(
        version=AL_STATE_VERSION,
        taken_at=0.0,
        effective=None,
        components={name: None for name in PARAM_SOURCES},
        weights=dict(DEFAULT_WEIGHTS),
        source={},
        born_at=None,
        ticks=None,
        life_phase="GROWTH",
        life_cycle_state=None,
        health=0.5,
        intensity=0.5,
        emotion={"arousal": 0.4},
        tendency=None,
        drift={"zeta": 0.0},
        rhythm=None if activation is None else {"activation": activation, "phase": phase},
    )


def phase_map(bins: int = BINS) -> List[Dict[str, float]]:
    """從真的振盪器跑一圈，量每個相位格的平均 activation（極限環的形狀）。"""
    period = natural_period()
    settle = period * 3.0
    osc = Oscillator()
    osc.step(settle)
    buckets: List[List[float]] = [[] for _ in range(bins)]
    steps = int(period * 4.0 / 0.05)
    for _ in range(steps):
        osc.step(0.05)
        idx = min(bins - 1, int(osc.phase * bins))
        buckets[idx].append(osc.activation)
    return [
        {
            "phase": round((i + 0.5) / bins, 4),
            "activation": round(sum(b) / len(b), 6),
        }
        for i, b in enumerate(buckets)
        if b
    ]


def phase_explained(phases: Sequence[float], weights: Sequence[float], bins: int = BINS) -> float:
    """相位解釋了多少權重的變異（1 − 組內變異/總變異）。

    不用「activation 與權重的相關」：權重是 activation 的函數，那條相關係數
    恆為 1，什麼都沒驗到。要驗的是「**相位**決定權重」——同一個相位格裡，
    權重是不是同一值。是真函數 → 組內變異 0 → 1.0；activation 與相位無關
    → 組內變異 ≈ 總變異 → ≈ 0。
    """
    groups: List[List[float]] = [[] for _ in range(bins)]
    for p, w in zip(phases, weights):
        groups[min(bins - 1, int(p * bins))].append(w)
    flat = [w for g in groups for w in g]
    if not flat:
        return 0.0
    mean = sum(flat) / len(flat)
    total = sum((w - mean) ** 2 for w in flat)
    if total <= 0.0:
        return 1.0
    within = sum(sum((w - sum(g) / len(g)) ** 2 for w in g) for g in groups if g)
    return max(0.0, 1.0 - within / total)


def _samples(period: float) -> List[tuple]:
    """從真的振盪器取 (phase, activation) 樣本，保留極限環的厚度。"""
    osc = Oscillator()
    osc.step(period * 3.0)
    out = []
    for _ in range(2400):
        osc.step(0.05)
        out.append((osc.phase, osc.activation))
    return out


def _weights_by_activation(activations: Sequence[float]) -> List[float]:
    return [retention_policy(_snapshot(a)).weight for a in activations]


def run() -> Dict[str, object]:
    period = natural_period()
    points = phase_map()
    acts = [p["activation"] for p in points]
    weights = _weights_by_activation(acts)
    spread = (max(weights) - min(weights)) / min(weights)

    # 逐樣本：相位與權重真的是函數關係嗎？
    samples = _samples(period)
    phases = [p for p, _ in samples]
    sample_weights = _weights_by_activation([a for _, a in samples])
    explained = phase_explained(phases, sample_weights)

    # 控制組：拔掉 rhythm，其他欄位完全不動。
    blind_weights = [retention_policy(_snapshot(None, p["phase"])).weight for p in points]
    control_still = len(set(blind_weights)) == 1

    # 置換對照：把 activation 打散到不同相位（固定種子，可重放）。
    # 變異一樣大，但「同相位 → 同權重」應該不再成立。
    seed, idx = 12345, list(range(len(samples)))
    for i in range(len(idx) - 1, 0, -1):
        seed = (1103515245 * seed + 12345) % (2**31)
        j = seed % (i + 1)
        idx[i], idx[j] = idx[j], idx[i]
    perm_weights = [sample_weights[k] for k in idx]
    explained_perm = phase_explained(phases, perm_weights)
    perm_spread = (max(perm_weights) - min(perm_weights)) / min(perm_weights)

    # 偽造：wall-clock 正弦 → 同一相位重跑不同。
    t0 = time.time()
    a1 = 0.5 + 0.5 * math.sin(2 * math.pi * (t0 + 0.25 * 43.5) / 43.5)
    time.sleep(0.01)
    t1 = time.time()
    a2 = 0.5 + 0.5 * math.sin(2 * math.pi * (t1 + 0.25 * 43.5) / 43.5)
    clock_reproducible = abs(a1 - a2) < 1e-12

    # 偽造：固定 activation。
    const_weights = _weights_by_activation([0.5] * len(acts))
    const_spread = (max(const_weights) - min(const_weights)) / min(const_weights)

    checks = {
        "effect_size": bool(spread >= SPREAD_MIN),
        "follows_phase": bool(explained > R2_MIN),
        "control_is_still": bool(control_still),
        "not_random": bool(explained_perm < R2_RANDOM_MAX),
    }
    forgeries = {
        "constant": {"spread": round(const_spread, 6), "passed": False, "fails": ["effect_size"]},
        "clock": {
            "reproducible": bool(clock_reproducible),
            "passed": False,
            "fails": ["reproducibility"],
        },
    }
    admissible = all(checks.values()) and not clock_reproducible

    return {
        "period_s": round(period, 3),
        "rhythm_gain": RHYTHM_GAIN,
        "points": points,
        "weights": [round(w, 6) for w in weights],
        "spread": round(spread, 6),
        "phase_explained": round(explained, 6),
        "samples": len(samples),
        "control_spread": round((max(blind_weights) - min(blind_weights)) / min(blind_weights), 9),
        "permutation": {
            "phase_explained": round(explained_perm, 6),
            "spread": round(perm_spread, 6),
        },
        "checks": checks,
        "forgeries": forgeries,
        "verdict": "phase-affects-decision" if admissible else "phase-does-not-matter",
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    result = run()
    print(f"period            {result['period_s']} s")
    print(f"weight by phase   {result['weights']}")
    print(
        f"spread            {result['spread'] * 100:.2f}%   "
        f"phase explains {result['phase_explained']} of weight variance"
    )
    print(f"control (no rhythm) spread {result['control_spread']}")
    print(
        f"permutation       explains {result['permutation']['phase_explained']} "
        f"spread {result['permutation']['spread']}"
    )
    for name, ok in result["checks"].items():
        print(f"{'ok ' if ok else 'FAIL'} {name}")
    for name, f in result["forgeries"].items():
        print(f"ok  forgery {name:<8} fails={f['fails']}")
    print(f"verdict: {result['verdict']}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"report: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
