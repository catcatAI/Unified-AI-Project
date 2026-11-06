#!/usr/bin/env python
"""C-param：相位有沒有進到**生成請求**？（`scripts/al_phase_effect.py` 的下一級）

上一支探針證明相位改變了系統自己的決定（記憶權重），但那條路徑沒有碰到生成。
這一支問：同一個 prompt 送出去時，請求參數會不會因為相位而不同？

被測路徑是**生產程式碼**：`ChatService.generate_text` 呼叫
`core.life.al_generation_params.modulate(temperature, max_tokens, snapshot)`，
而 snapshot 來自 `al_state.get_al_state()` 的 `rhythm` 欄位。

三件要分開講清楚
----------------
1. **接線是真的**：探針不信實作，它把 `ChatService` 的 LLM 服務換成記錄器，
   實際呼叫 `generate_text`，看最後送出去的 `temperature` / `max_tokens`。
2. **歸因是乾淨的**：快照是注入的（只有相位不同），所以差異只能來自相位；
   拔掉 `rhythm` 必須得到逐位相同的原值。
3. **不是隨機**：相位換成亂數、或換成 wall-clock 正弦（偽造品），要嘛關聯消失、
   要嘛不可重現。

它**沒有**量什麼（照實寫）
--------------------------
沒有量真實模型上的解碼差異。這裡只有參數層的證據（ΔT、Δtokens）與一段算術
示範（固定 logit 下 softmax 的變化）。要量生成內容的差異需要跑真模型，且必須
先排除取樣本身造成的變異——那是下一個實驗，不是這一個。
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [C] [L0-L11]
# =============================================================================

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from core.life import al_state  # noqa: E402
from core.life.al_generation_params import (  # noqa: E402
    TEMPERATURE_SWING,
    modulate,
)
from core.life.al_oscillator import Oscillator, natural_period  # noqa: E402

BASE_TEMPERATURE = 0.7
BASE_TOKENS = 512
DT_MIN = 0.05
SEED = 424242


def _phases(period: float, n: int = 8) -> List[tuple]:
    """取 n 個相位對應的 activation（真的振盪器，不是公式）。"""
    osc = Oscillator()
    osc.step(period * 3.0)
    out = []
    for i in range(n):
        target = (i + 0.5) / n
        # 走到目標相位（最多一個週期）
        for _ in range(int(period / 0.05) + 200):
            osc.step(0.05)
            if abs(osc.phase - target) < 0.01:
                break
        out.append((round(osc.phase, 4), round(osc.activation, 6)))
    return out


def _live_call(activation: float) -> Dict[str, float]:
    """實際跑 `ChatService.generate_text`，攔下它送給 LLM 服務的參數。

    用 `__new__` 繞過重量級初始化：這支探針要驗的是那一行接線，不是整個服務。
    """
    from services.chat_service import ChatService

    svc = ChatService.__new__(ChatService)
    captured: Dict[str, float] = {}

    class _Recorder:
        async def generate_text(self, **kwargs):
            captured.update(kwargs)
            return "ok"

    svc._llm_service = _Recorder()

    snapshot = al_state.get_al_state()
    injected = al_state.ALSnapshot(
        **{
            **{k: getattr(snapshot, k) for k in snapshot.__dataclass_fields__},
            "rhythm": None if activation is None else {"activation": activation, "phase": 0.0},
        }
    )
    original = al_state.get_al_state
    al_state.get_al_state = lambda: injected  # type: ignore[assignment]
    try:
        asyncio.run(
            svc.generate_text("probe", temperature=BASE_TEMPERATURE, max_tokens=BASE_TOKENS)
        )
    finally:
        al_state.get_al_state = original  # type: ignore[assignment]
    return captured


class _Snap:
    """最小快照替身：只有 ``rhythm``，`modulate` 也只讀它。"""

    def __init__(self, activation: Optional[float]) -> None:
        self.rhythm = None if activation is None else {"activation": activation, "phase": 0.0}


def _phase_explained(phases: Sequence[float], values: Sequence[float], bins: int = 8) -> float:
    """1 − 組內變異/總變異：相位格內的值是否一致。"""
    groups: List[List[float]] = [[] for _ in range(bins)]
    for p, v in zip(phases, values):
        groups[min(bins - 1, int(p * bins))].append(v)
    flat = [v for g in groups for v in g]
    if not flat:
        return 0.0
    mean = sum(flat) / len(flat)
    total = sum((v - mean) ** 2 for v in flat)
    if total <= 0.0:
        return 1.0
    within = sum(sum((v - sum(g) / len(g)) ** 2 for v in g) for g in groups if g)
    return max(0.0, 1.0 - within / total)


def _softmax_top(logits: Sequence[float], temperature: float) -> float:
    """固定 logits 下，最高機率 token 的機率。只是算術示範，不是模型量測。"""
    scaled = [z / max(temperature, 1e-6) for z in logits]
    top = max(scaled)
    exps = [math.exp(z - top) for z in scaled]
    return max(exps) / sum(exps)


def run() -> Dict[str, object]:
    period = natural_period()
    points = _phases(period)

    live = [_live_call(a) for _, a in points]
    temps = [round(float(p.get("temperature", float("nan"))), 4) for p in live]
    tokens = [int(p.get("max_tokens", -1)) for p in live]
    spread = (max(temps) - min(temps)) / BASE_TEMPERATURE

    # 控制組：快照沒有 rhythm → 必須逐位等於原值。
    control = _live_call(None)
    control_still = (
        float(control.get("temperature", -1.0)) == BASE_TEMPERATURE
        and int(control.get("max_tokens", -1)) == BASE_TOKENS
    )

    # 逐樣本：相位對溫度的解釋力（同相位 → 同溫度，是真的函數關係）。
    osc = Oscillator()
    osc.step(period * 3.0)
    sample_phases, sample_acts = [], []
    for _ in range(2400):
        osc.step(0.05)
        sample_phases.append(osc.phase)
        sample_acts.append(osc.activation)
    sample_temps = [
        modulate(BASE_TEMPERATURE, BASE_TOKENS, _Snap(a)).temperature for a in sample_acts
    ]
    explained = _phase_explained(sample_phases, sample_temps)

    # 置換對照：activation 與相位無關 → 變異一樣大，但相位不再解釋它。
    seed, idx = SEED, list(range(len(sample_acts)))
    for i in range(len(idx) - 1, 0, -1):
        seed = (1103515245 * seed + 12345) % (2**31)
        j = seed % (i + 1)
        idx[i], idx[j] = idx[j], idx[i]
    perm_temps = [sample_temps[k] for k in idx]
    explained_perm = _phase_explained(sample_phases, perm_temps)
    perm_spread = (max(perm_temps) - min(perm_temps)) / BASE_TEMPERATURE

    # 偽造：wall-clock 正弦 → 同一相位重跑得到不同參數。
    t0 = time.time()
    a0 = 0.5 + 0.5 * math.sin(2 * math.pi * t0 / period)
    time.sleep(0.01)
    a1 = 0.5 + 0.5 * math.sin(2 * math.pi * time.time() / period)
    clock_reproducible = abs(a0 - a1) < 1e-12

    # 算術示範：固定 logit 差距 2.0，最高機率 token 的機率在兩端溫度下的差。
    hot = _softmax_top([2.0, 0.0], max(temps))
    cold = _softmax_top([2.0, 0.0], min(temps))

    checks = {
        "reaches_the_request": bool(all(t == t for t in temps) and len(set(tokens)) > 1),
        "effect_is_visible": bool(spread >= 0.10 and (max(temps) - min(temps)) >= 0.10),
        "control_is_still": bool(control_still),
        "phase_explains_params": bool(explained > 0.9 and explained_perm < 0.2),
    }
    admissible = all(checks.values()) and not clock_reproducible

    return {
        "period_s": round(period, 3),
        "swing_setting": TEMPERATURE_SWING,
        "points": [{"phase": p, "activation": a} for p, a in points],
        "temperature": temps,
        "max_tokens": tokens,
        "spread": round(spread, 4),
        "control": {
            "temperature": control.get("temperature"),
            "max_tokens": control.get("max_tokens"),
        },
        "phase_explained": round(explained, 6),
        "permutation": {
            "phase_explained": round(explained_perm, 6),
            "spread": round(perm_spread, 4),
        },
        "clock_forgery_reproducible": bool(clock_reproducible),
        "softmax_demo": {"hot": round(hot, 4), "cold": round(cold, 4), "logits": [2.0, 0.0]},
        "checks": checks,
        "verdict": "generation-params-modulated" if admissible else "generation-params-untouched",
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    result = run()
    print(f"period {result['period_s']} s")
    print(f"temperature  {result['temperature']}")
    print(f"max_tokens   {result['max_tokens']}")
    print(f"spread       {result['spread'] * 100:.1f}% of {BASE_TEMPERATURE}")
    print(f"control      {result['control']}")
    print(
        f"phase explains {result['phase_explained']} of the temperature variance "
        f"(permuted {result['permutation']['phase_explained']})"
    )
    print(f"softmax demo {result['softmax_demo']}")
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
