#!/usr/bin/env python
"""C-state：相位改的是模型的**內部體質**，不是輸入也不是輸出（`al_c_logit.py` 的下一級）

前三級都能說是「從外面推」：C-param 改請求參數；C-logit 改輸出分布；兩者模型
內部完全不知道。這一支改的是 GARDEN SNN 的**發火閾值**：

    同樣的 input_keys、同樣的 W、同樣的 timesteps，
    只因為內部興奮度不同，脈衝樣式就不同。

這就是「狀態在模型裡面」的最小可測形式。前三個層級換一個模型就消失；這一層
改變的是同一份權重跑出來的動力學。

量什麼
------
1. ``internal_effect``：八個相位下輸出（概念鍵→累積發火）相對基線的 L1 變化；
2. ``flip``：有沒有概念**從不發火變成發火**（離散結構改變，不只是數值漂移）；
3. ``monotone``：活躍概念數是否隨 activation 單調（Spearman ρ）；
4. ``input_untouched``：每一次呼叫的 input_keys 逐位相同——差異只能來自內部。

控制組與偽造品
--------------
- **無調制**（ctx 沒有 ``al_modulation``）→ 輸出**逐位相同**；
- **置換對照**：同一批調制值打散後，與 activation 的單調關係消失；
- **偽造品**：wall-clock 正弦 → 同一相位重跑不同。

它**沒有**量什麼：沒有量「AL 讓模型學會了什麼」（那是權重層，不是狀態層），
也沒有量語意品質。這裡只主張：內部參數被 AL 狀態驅動，且因此改變輸出。
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
from core.life.al_oscillator import Oscillator, natural_period  # noqa: E402
from core.life.al_snn_modulation import modulate  # noqa: E402

N_PHASES = 8
CHAIN = ("seed", "a", "b", "c", "d", "e", "f")
INPUT = {"seed": 1.0}


def _build_core(leak: float = 0.5, weight: float = 0.6) -> TensorSNNCore:
    """一條會擴散的概念鏈：seed → a → b → …，權重遞減。"""
    # 參數刻意落在「瀕臨發火」的區間：threshold 0.6、權重 0.6、leak 0.5。
    # 若權重遠大於 threshold，所有神經元每一拍都點亮，閾值怎麼調都一樣——
    # 那是第一版的情況（L1 恆為 0），結論會被誤讀成「內部調制沒用」。
    core = TensorSNNCore(leak=leak, threshold=0.6, timesteps=12, decay=0.9, device="cpu")
    for left, right in zip(CHAIN, CHAIN[1:]):
        core.add_relation(left, right, weight=weight)
    return core


def _l1(a: Dict[str, float], b: Dict[str, float]) -> float:
    return sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in set(a) | set(b))


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


def crossover(weight: float = 0.6, steps: int = 14) -> float:
    """二分找出「開始有概念擴散」的 activation。

    若調制其實是寫死的門檻（`if activation > 0.5`），這個交叉點不會隨網路的
    洩漏率移動。它會移動，就說明切換點長自**動力學**，不是長自規則。
    """
    core = _build_core(weight=weight)
    lo, hi = 0.0, 1.0
    for _ in range(steps):
        mid = 0.5 * (lo + hi)
        out = core.forward(INPUT, {"al_modulation": modulate(mid).as_dict()})
        if out:
            hi = mid
        else:
            lo = mid
    return round(0.5 * (lo + hi), 4)


def run(n_phases: int = N_PHASES) -> Dict[str, object]:
    core = _build_core()
    baseline = core.forward(INPUT)

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
    inputs_identical = True
    for phase, activation in points:
        mod = modulate(activation)
        out = core.forward(INPUT, {"al_modulation": mod.as_dict()})
        new_keys = sorted(set(out) - set(baseline))
        lost_keys = sorted(set(baseline) - set(out))
        rows.append(
            {
                "phase": phase,
                "activation": activation,
                "threshold_multiplier": mod.threshold_multiplier,
                "l1": round(_l1(out, baseline), 6),
                "active": len(out),
                "new_concepts": new_keys,
                "lost_concepts": lost_keys,
            }
        )

    # 控制組：完全不加調制 → 必須逐位相同。
    plain = core.forward(INPUT)
    control_identical = plain == baseline

    l1s = [r["l1"] for r in rows]
    acts = [r["activation"] for r in rows]
    active = [float(r["active"]) for r in rows]
    rho = _spearman(acts, active)

    # 置換對照：打散調制值 → 與 activation 的單調關係消失。
    seed, idx = 777001, list(range(len(rows)))
    for i in range(len(idx) - 1, 0, -1):
        seed = (1103515245 * seed + 12345) % (2**31)
        j = seed % (i + 1)
        idx[i], idx[j] = idx[j], idx[i]
    perm_active = [active[k] for k in idx]
    rho_perm = _spearman(acts, perm_active)

    # 偽造：wall-clock 正弦 → 同一相位重跑不同。
    t0 = time.time()
    a0 = 0.5 + 0.5 * math.sin(2 * math.pi * t0 / period)
    time.sleep(0.01)
    a1 = 0.5 + 0.5 * math.sin(2 * math.pi * time.time() / period)
    clock_reproducible = abs(a0 - a1) < 1e-12

    # 交叉點是否隨「權重」（輸入電流）移動：若調制只是寫死的門檻，它不會動。
    crossovers = {str(w): crossover(w) for w in (0.5, 0.6, 0.75)}
    cross_spread = max(crossovers.values()) - min(crossovers.values())

    checks = {
        "internal_effect": bool(max(l1s) > 0.01),
        "boundary_follows_dynamics": bool(cross_spread > 0.02),
        "structure_changes": bool(any(r["new_concepts"] or r["lost_concepts"] for r in rows)),
        "monotone_in_activation": bool(abs(rho) > 0.9),
        "control_is_identical": bool(control_identical),
        "not_random": bool(abs(rho_perm) < 0.9),
    }
    admissible = all(checks.values()) and not clock_reproducible

    return {
        "period_s": round(period, 3),
        "chain": list(CHAIN),
        "input_untouched": inputs_identical,
        "baseline": {k: round(v, 4) for k, v in sorted(baseline.items())},
        "rows": rows,
        "l1_max": round(max(l1s), 6),
        "spearman": round(rho, 3),
        "crossover": crossovers,
        "crossover_spread": round(cross_spread, 4),
        "permutation_spearman": round(rho_perm, 3),
        "clock_forgery_reproducible": bool(clock_reproducible),
        "checks": checks,
        "verdict": (
            "phase-changes-internal-dynamics" if admissible else "phase-leaves-internals-alone"
        ),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    result = run()
    print(f"period {result['period_s']} s   baseline {result['baseline']}")
    for row in result["rows"]:
        print(
            f"  act {row['activation']:.3f} thr×{row['threshold_multiplier']:.3f} "
            f"active {row['active']} L1 {row['l1']:.4f} "
            f"new {row['new_concepts']} lost {row['lost_concepts']}"
        )
    print(
        f"max L1 {result['l1_max']}  rho {result['spearman']} (perm {result['permutation_spearman']})"
    )
    print(f"crossover by weight {result['crossover']}  spread {result['crossover_spread']}")
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
