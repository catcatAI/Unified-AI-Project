#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [αβ] [B] [L3]
# =============================================================================
"""Is the heartbeat's rhythm generated, or inherited from its inputs?

The 2026-11-06 review guessed that the heartbeat interval fed by stress/arousal
(mutually connected) *might* produce a rhythm, and listed "measure the interval
series" as the way to find out. This measures it, on the shipping formula
(``core.life.heartbeat.dynamic_interval``, extracted unchanged from the loop):

* **constant inputs** — the interval series is flat. A pure function of a
  constant is a constant, so there is no self-generated oscillation, and any CV
  above zero has to come from the input.
* **inherited rhythm** — drive arousal with a sine: the interval follows, with
  high lag-1 autocorrelation. That is a filtered copy of the input, not a beat of
  its own.
* **feedback** — the formula has no state, so today's interval cannot influence
  tomorrow's arousal *through this path*. Measured as: same inputs, same
  interval, regardless of the interval history.

The honest verdict is therefore "no rhythm here yet", and the reason is
structural rather than a tuning problem: a memoryless map cannot oscillate. If a
rhythm is wanted, it has to come from a source that has its own dynamics (the
bio integrator, or arousal with its rise/fall pair), and then the measurement is
whether that source's period survives to the beat.

That source now exists (``core/life/al_oscillator.py``, wired into the beat via
``heartbeat.effective_arousal``), and ``scripts/al_rhythm_source.py`` measures
whether the period survives. This script keeps measuring the **mapping alone**,
which is still memoryless: the verdict below is about ``dynamic_interval``, not
about the beat, and it is supposed to stay "inherited" forever.

Usage:
    ./.venv/bin/python scripts/al_heartbeat_rhythm.py
    ./.venv/bin/python scripts/al_heartbeat_rhythm.py --json data/intelligence_reports/al_heartbeat_rhythm.json
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "backend" / "src"))

from core.life.heartbeat import dynamic_interval  # noqa: E402  (pure function)


def _series(arousals: Sequence[float], stress: float = 0.5) -> List[float]:
    return [dynamic_interval(stress, a) for a in arousals]


def _cv(series: Sequence[float]) -> float:
    mean = statistics.fmean(series)
    return 0.0 if mean == 0 else statistics.pstdev(series) / mean


def _lag1(series: Sequence[float]) -> float:
    if len(series) < 3:
        return 0.0
    x = list(series[:-1])
    y = list(series[1:])
    mx, my = statistics.fmean(x), statistics.fmean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return 0.0 if den == 0 else num / den


def run(n: int = 240) -> Dict[str, object]:
    constant = _series([50.0] * n)

    sine = [50.0 + 25.0 * math.sin(2 * math.pi * i / 40) for i in range(n)]
    inherited = _series(sine)

    # Feedback probe: same arousal trajectory, but the interval history is
    # deliberately different (the formula never sees it, so the output must be
    # identical). This is the "no memory" check, not a simulation of the loop.
    a_traj = [40.0 + 10.0 * math.cos(2 * math.pi * i / 30) for i in range(60)]
    forward = _series(a_traj)
    backward = _series(list(reversed(a_traj)))
    history_independent = forward == list(reversed(backward))

    stats = {
        "constant": {"cv": _cv(constant), "lag1": _lag1(constant), "interval": constant[0]},
        "inherited_sine": {
            "cv": _cv(inherited),
            "lag1": _lag1(inherited),
            "interval_range": [min(inherited), max(inherited)],
        },
        "history_independent": history_independent,
    }

    verdict = "no-self-rhythm"
    if stats["constant"]["cv"] > 1e-9:
        verdict = "self-rhythm"  # a memoryless map cannot do this; would be a bug
    elif stats["inherited_sine"]["cv"] > 1e-9 and history_independent:
        verdict = "rhythm-inherited-from-input"

    return {
        "samples": n,
        "statistics": stats,
        "verdict": verdict,
        "within_bounds": all(5.0 <= v <= 60.0 for v in constant + inherited),
        "note": (
            "a memoryless map cannot oscillate; measured CV=0 under constant inputs "
            "and high autocorrelation under a sine input means the beat is a filtered "
            "copy of its source, so any rhythm claim must name the source's dynamics"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="heartbeat rhythm probe")
    ap.add_argument("--json", type=str, default="")
    args = ap.parse_args()

    result = run()
    s = result["statistics"]
    print(
        f"constant input      interval={s['constant']['interval']:.3f}s  CV={s['constant']['cv']:.2e}  lag1={s['constant']['lag1']:.2f}"
    )
    print(
        f"sinusoidal arousal  range={s['inherited_sine']['interval_range'][0]:.2f}–"
        f"{s['inherited_sine']['interval_range'][1]:.2f}s  CV={s['inherited_sine']['cv']:.3f}  "
        f"lag1={s['inherited_sine']['lag1']:.3f}"
    )
    print(f"history independent {s['history_independent']}")
    print(f"within 5–60 s       {result['within_bounds']}")
    print("verdict:", result["verdict"])
    if args.json:
        out = ROOT / args.json
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("report:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
