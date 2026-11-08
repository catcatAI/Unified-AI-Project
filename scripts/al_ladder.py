#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [αβγ] [B] [L3]
# =============================================================================
"""Time-ladder probe: what can the AL core do that a trained baseline cannot?

The open question after the 2026-11-06 review is not "is the core smart" but
"does *time acting on state* buy anything a model fed the same numbers would not
get". That question has a cheap, decisive form: put the AL rule and a trained
baseline on the same rungs, with the same inputs, and look at the held-out rung.

Everything here is measured against the production module
(``core.life.al_arousal``), not a reimplementation, so the numbers describe the
code that will ship. Three candidates, deliberately of different kind:

* ``al``       — the contract §5 operator, closed form. Zero training.
* ``mlp``      — numpy 2→16→16→2 trained on ``(v, target, dt) -> (v', target')``
                 with ``dt`` drawn only from the inner range. Same information,
                 same targets: the ceiling of "learn the trajectory". The point
                 of the inner/outer split is that a network can fit ``e^(-dt/tau)``
                 in-distribution and cannot extrapolate it, which is exactly the
                 claim (9.5 in the review) that a state system only buys
                 *efficiency and generalisation*, never new capability.
* ``forgery``  — last value plus noise, ignores elapsed time. The cheap fake the
                 review (section 10) says must be beaten before any claim counts.

Rungs, each with the error a candidate makes and whether the rung is *sensitive*
(the worst baseline is far from right, so passing is informative):

  r1 semigroup       advance(advance(s,t1),t2) == advance(s,t2)
  r2 sampling        one 600 s step == 600 x 1 s steps
  r3 fixed point     v == target, held 10 tau -> stays at target
  r4 inner dt        MAE on dt inside the MLP's training range
  r5 outer dt        MAE on dt the MLP never saw  <- the rung that matters
  r6 restart         persist, wait 300 s, reopen -> decays by elapsed time
  r7 clock attack    clock rolled back / jumped forward: does the system doubt it

r7 is a *mechanism* rung, not an accuracy rung: the honest reading today is that
the core freezes on a rollback and fully decays on a jump, with no suspicion
signal at all. It is scored as ``None`` (no estimate exists) rather than as a
pass, because "did not crash" is not "noticed".

Usage:
    ./.venv/bin/python scripts/al_ladder.py
    ./.venv/bin/python scripts/al_ladder.py --report data/intelligence_reports/al_ladder.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "backend" / "src"))

from core.life import al_arousal as ar  # noqa: E402

BASELINE = ar.AROUSAL_BASELINE
TAU_RISE = ar.DEFAULT_TAU_RISE_S
TAU_FALL = ar.DEFAULT_TAU_FALL_S
INNER_DT = (0.5, 60.0)
# Deliberately saturated-free: at 86400 s everything has relaxed to the baseline,
# so a constant predictor scores well and the rung stops discriminating. 90-600 s
# is 4.5-30 tau_rise and 0.3-2 tau_fall: the MLP never saw it, and it is not yet
# a settled state.
OUTER_DT = (90.0, 600.0)
# These are *exactness* rungs: the production rule is exact by construction, so
# "correct" means agreeing with it to float noise. A candidate 0.025 away (a
# constant that guesses the baseline) is wrong, not "close": letting a loose
# tolerance count as a pass is how a rung stops measuring anything.
SENSITIVE = 1e-03


# =============================================================================
# Candidates
# =============================================================================
class ALModel:
    """The production rule, called through the production function."""

    name = "al"
    trained = False

    def step(self, state: ar.AffectState, now: float) -> ar.AffectState:
        return ar.advance(state, now)


class CopyModel:
    """Identity control: predicts "nothing changed". Beats nothing, but is the
    floor that tells us whether a rung is measuring anything."""

    name = "copy"
    trained = False

    def step(self, state: ar.AffectState, now: float) -> ar.AffectState:
        return ar.AffectState(state.arousal, state.target, now)


class ConstModel:
    """Always the baseline. The cheapest predictor there is, and the one that
    exposes a rung which has saturated: at very long dt every candidate is
    approximately right, so a long-dt rung measures decay of information rather
    than anyone's model."""

    name = "const"
    trained = False

    def step(self, state: ar.AffectState, now: float) -> ar.AffectState:
        return ar.AffectState(BASELINE, BASELINE, now)


class ForgeryModel:
    """Table plus noise: remembers the last observed level, ignores elapsed time.

    This is the shape of the "Day N log" accounts in the review: the state is
    whatever was last written down, and the wall clock never enters."""

    name = "forgery"
    trained = False

    def __init__(self, seed: int = 7) -> None:
        self._rng = np.random.default_rng(seed)
        self._level = [BASELINE]

    def observe(self, level: float) -> None:
        self._level[0] = level

    def step(self, state: ar.AffectState, now: float) -> ar.AffectState:
        level = float(np.clip(self._level[0] + self._rng.normal(0.0, 0.02), 0.0, 1.0))
        return ar.AffectState(level, level, now)


class MLPModel:
    """``(v, target, log1p(dt)) -> (v', target')``, trained on the inner dt range.

    Same information as the AL rule (both get v, target and the elapsed time),
    same targets (generated from the AL rule), so the only difference is learned
    versus designed dynamics. Numpy only: no torch, no GPU, no seeding games.
    """

    name = "mlp"
    trained = True

    def __init__(self, hidden: int = 16, steps: int = 2500, lr: float = 0.05, seed: int = 1):
        rng = np.random.default_rng(seed)
        self._d_scale = math.log1p(INNER_DT[1])
        self._p: List[np.ndarray] = [
            rng.normal(0, 0.5, (3, hidden)),
            np.zeros(hidden),
            rng.normal(0, 0.5, (hidden, hidden)),
            np.zeros(hidden),
            rng.normal(0, 0.3, (hidden, 2)),
            np.zeros(2),
        ]
        x, y = self._dataset(4000, rng)
        self._train(x, y, steps=steps, lr=lr, rng=rng)

    # -- data ------------------------------------------------------------
    def _dataset(self, n: int, rng: np.random.Generator) -> Tuple[np.ndarray, np.ndarray]:
        v = rng.uniform(0.0, 1.0, n)
        target = rng.uniform(0.0, 1.0, n)
        dt = np.exp(rng.uniform(math.log(INNER_DT[0]), math.log(INNER_DT[1]), n))
        states = [ar.AffectState(float(a), float(b), 0.0) for a, b in zip(v, target)]
        nxt = [ar.advance(s, float(d)) for s, d in zip(states, dt)]
        x = np.stack([v, target, np.log1p(dt) / self._d_scale], axis=1)
        y = np.stack([[s.arousal for s in nxt], [s.target for s in nxt]], axis=1)
        return x, y

    # -- forward / backward ----------------------------------------------
    def _forward(self, x: np.ndarray) -> Tuple[np.ndarray, Tuple]:
        w1, b1, w2, b2, w3, b3 = self._p
        h1 = np.tanh(x @ w1 + b1)
        h2 = np.tanh(h1 @ w2 + b2)
        y = h2 @ w3 + b3
        return y, (x, h1, h2)

    def _train(self, x: np.ndarray, y: np.ndarray, *, steps: int, lr: float, rng) -> None:
        m = [np.zeros_like(p) for p in self._p]
        v = [np.zeros_like(p) for p in self._p]
        for i in range(steps):
            idx = rng.integers(0, len(x), 256)
            xb, yb = x[idx], y[idx]
            pred, (xb_, h1, h2) = self._forward(xb)
            g = 2.0 * (pred - yb) / len(xb)
            w1, b1, w2, b2, w3, b3 = self._p
            gw3 = h2.T @ g
            gb3 = g.sum(0)
            gh2 = (g @ w3.T) * (1 - h2**2)
            gw2 = h1.T @ gh2
            gb2 = gh2.sum(0)
            gh1 = (gh2 @ w2.T) * (1 - h1**2)
            gw1 = xb_.T @ gh1
            gb1 = gh1.sum(0)
            grads = [gw1, gb1, gw2, gb2, gw3, gb3]
            for k, grad in enumerate(grads):
                m[k] = 0.9 * m[k] + 0.1 * grad
                v[k] = 0.999 * v[k] + 0.001 * grad**2
                self._p[k] -= (
                    lr
                    * (m[k] / (1 - 0.9 ** (i + 1)))
                    / (np.sqrt(v[k] / (1 - 0.999 ** (i + 1))) + 1e-8)
                )

    # -- candidate interface ---------------------------------------------
    def step(self, state: ar.AffectState, now: float) -> ar.AffectState:
        dt = max(0.0, now - state.at)
        x = np.array([[state.arousal, state.target, math.log1p(dt) / self._d_scale]], dtype=float)
        y, _ = self._forward(x)
        return ar.AffectState(
            float(np.clip(y[0, 0], 0.0, 1.0)), float(np.clip(y[0, 1], 0.0, 1.0)), now
        )


# =============================================================================
# Rungs
# =============================================================================
def _states(n: int, rng: np.random.Generator) -> List[ar.AffectState]:
    return [
        ar.AffectState(float(a), float(b), 0.0)
        for a, b in zip(rng.uniform(0.05, 0.95, n), rng.uniform(0.05, 0.95, n))
    ]


def rung_semigroup(models, rng) -> Dict[str, float]:
    """advance twice vs advance once — the rule must not care how you slice time."""
    out = {}
    for m in models:
        err = 0.0
        for s in _states(200, rng):
            t1 = float(rng.uniform(1.0, 300.0))
            t2 = t1 + float(rng.uniform(1.0, 300.0))
            once = m.step(s, t2)
            twice = m.step(m.step(s, t1), t2)
            err = max(err, abs(once.arousal - twice.arousal))
        out[m.name] = err
    return out


def rung_sampling(models, rng) -> Dict[str, float]:
    """One long step vs 600 one-second steps: sampling rate is not a time base."""
    out = {}
    for m in models:
        err = 0.0
        for s in _states(50, rng):
            total = 600.0
            once = m.step(s, total)
            cur = s
            for i in range(1, 601):
                cur = m.step(cur, float(i))
            err = max(err, abs(once.arousal - cur.arousal))
        out[m.name] = err
    return out


def rung_attractor(models, rng) -> Dict[str, float]:
    """No events for a long time: does the *trajectory* relax onto the baseline?

    An earlier version of this rung held ``v == target == 0.8`` and called
    staying at 0.8 a fixed point; it is not one. A second version scored only the
    endpoint, and that was worse in a subtler way: a constant predictor that
    always answers 0.3 passes it (0 error, monotone by triviality). Endpoint-only
    scoring cannot tell a decay from a lucky constant.

    So the score is the mean absolute error along the curve (ten checkpoints out
    to 10 tau_fall) against the analytic trajectory, with the fraction of
    non-monotone steps as the second component. A constant fails the curve error
    immediately; a rule that wanders fails monotonicity.
    """
    out = {}
    for m in models:
        curve_err = 0.0
        non_monotone = 0
        steps = 0
        for start in (0.1, 0.5, 0.8, 1.0):
            s = ar.AffectState(start, start, 0.0)
            prev = start
            for k in range(1, 11):
                now = float(k) * TAU_FALL
                truth = ar.advance(s, now).arousal
                got = m.step(s, now).arousal
                curve_err += abs(got - truth)
                if abs(got - BASELINE) > abs(prev - BASELINE) + 1e-9:
                    non_monotone += 1
                steps += 1
                prev = got
        out[m.name] = max(curve_err / steps, non_monotone / steps)
    return out


def _dt_sweep(model, dt_lo: float, dt_hi: float, rng, n: int = 300) -> float:
    errs = []
    for s in _states(n, rng):
        dt = float(np.exp(rng.uniform(math.log(dt_lo), math.log(dt_hi))))
        truth = ar.advance(s, dt).arousal
        errs.append(abs(model.step(s, dt).arousal - truth))
    return float(np.mean(errs))


def rung_inner_dt(models, rng) -> Dict[str, float]:
    return {m.name: _dt_sweep(m, *INNER_DT, rng) for m in models}


def rung_outer_dt(models, rng) -> Dict[str, float]:
    return {m.name: _dt_sweep(m, *OUTER_DT, rng) for m in models}


def rung_restart(rng, tmp: Path) -> Dict[str, float]:
    """Persist, let 300 s pass while the process is gone, reopen.

    Measured for the four candidates that *can* be restarted: ``al`` via the real
    ``AffectTracker`` (which is the shipping path), ``forgery``/``copy`` as the
    last-value table. The MLP has no persistent state of its own; its "restart"
    is feeding it from the stored number, so it inherits the table's error and
    adds nothing — stated rather than silently omitted.
    """
    out: Dict[str, float] = {}
    level = 0.9
    elapsed = 300.0

    path = tmp / "affect.json"
    clock = [1000.0]
    tracker = ar.AffectTracker(path=path, clock=lambda: clock[0])
    tracker.observe_level(level)
    before = tracker.arousal()
    clock[0] += elapsed
    reborn = ar.AffectTracker(path=path, clock=lambda: clock[0])  # process restart
    truth = ar.advance(ar.AffectState(BASELINE, level, 1000.0), 1000.0 + elapsed).arousal
    out["al"] = abs(reborn.arousal() - truth)
    out["copy"] = abs(before - truth)  # keeps the last number: no decay
    out["forgery"] = abs(level - truth)  # same failure, plus noise on read
    return out


def rung_clock_attack(tmp: Path) -> Dict[str, Optional[float]]:
    """Forged clocks: does the system have an opinion *and* act on it?

    The mechanism is a second, unforgeable time source: ``time.monotonic`` moves
    forward by 1 s while the injected ``time.time`` is jumped. What is measured:

    - ``detect_backward`` / ``detect_forward``: fraction of forged samples flagged;
    - ``false_alarm``: fraction of honest samples flagged;
    - ``rollback_freeze``: state change on a backward jump (the value is held, which
      is now a *reported* hold rather than a silent one).

    A guard that flags everything would score 1.0 on detection and 1.0 on false
    alarms, so both are reported and the rung is only passed when both are right.
    """
    level = 0.9
    path = tmp / "attack.json"
    wall = [1_000_000.0]
    mono = [10_000.0]
    tracker = ar.AffectTracker(path=path, clock=lambda: wall[0], monotonic=lambda: mono[0])
    tracker.observe_level(level)

    honest = 0
    honest_total = 0
    for _ in range(20):  # one second each, in step
        wall[0] += 1.0
        mono[0] += 1.0
        tracker.arousal()
        verdict = tracker.clock_status()
        honest_total += 1
        honest += 1 if verdict is not None and verdict.suspicion else 0

    # A fresh tracker for the freeze measurement: `arousal()` is a pure read and
    # does not persist, so comparing a read taken at t with one taken after the
    # rollback compares two different stored states. Read, roll back, read again.
    freeze_tracker = ar.AffectTracker(
        path=tmp / "attack_freeze.json", clock=lambda: wall[0], monotonic=lambda: mono[0]
    )
    freeze_tracker.observe_level(level)
    before_rollback = freeze_tracker.arousal()

    wall[0] -= 1_000_000.0  # clock rolls back a week, monotonic does not
    mono[0] += 1.0
    rolled = freeze_tracker.arousal()
    backward_flag = freeze_tracker.clock_status()

    wall[0] += 2_000_000.0  # ...then jumps a week forward
    mono[0] += 1.0
    jumped = tracker.arousal()
    forward_flag = tracker.clock_status()

    return {
        "detect_backward": float(backward_flag.suspicion) if backward_flag else 0.0,
        "detect_forward": float(forward_flag.suspicion) if forward_flag else 0.0,
        "false_alarm": honest / honest_total if honest_total else 0.0,
        "rollback_freeze": abs(rolled - before_rollback),
        "forward_jump": abs(jumped - ar.advance(ar.AffectState(BASELINE, level, 0.0), 1e6).arousal),
    }


# =============================================================================
# Scorecard
# =============================================================================
def _verdict(al: float, worst_baseline: float, control: float) -> str:
    """Verdict with the control folded in.

    ``control`` is the identity model's error on the same rung. When the control
    passes, the rung is passed by doing nothing, so it cannot be evidence — that
    is the case for r1 and r2, where a closed form is invariant under reslicing
    time *and* so is the constant function. Those come back as
    ``sound-not-evidence``: worth having, but not something to quote.
    """
    if worst_baseline <= SENSITIVE:
        return "not-sensitive"
    if control <= SENSITIVE:
        return "sound-not-evidence"
    if al <= 0.1 * worst_baseline:
        return "al-wins"
    if al < worst_baseline:
        return "al-ahead"
    return "baseline-wins"


def run(tmp_root: Optional[Path] = None) -> Dict[str, object]:
    rng = np.random.default_rng(11)
    tmp = Path(tempfile.mkdtemp(prefix="al_ladder_", dir=str(tmp_root) if tmp_root else None))
    models = [ALModel(), MLPModel(), CopyModel(), ConstModel(), ForgeryModel()]

    rungs = {
        "r1_semigroup": rung_semigroup(models, rng),
        "r2_sampling": rung_sampling(models, rng),
        "r3_attractor": rung_attractor(models, rng),
        "r4_inner_dt": rung_inner_dt(models, rng),
        "r5_outer_dt": rung_outer_dt(models, rng),
        "r6_restart": rung_restart(rng, tmp),
        "r7_clock": rung_clock_attack(tmp),
    }

    table: Dict[str, Dict[str, object]] = {}
    for name, values in rungs.items():
        if name == "r7_clock":
            caught = float(values["detect_backward"]) + float(values["detect_forward"])
            false_alarms = float(values["false_alarm"])
            if caught == 0.0:
                verdict = "mechanism-missing"
            elif caught == 2.0 and false_alarms <= 0.05:
                verdict = "doubt-works"
            else:
                verdict = "doubt-weak"
            table[name] = {"values": values, "verdict": verdict}
            continue
        al = float(values["al"])
        worst = max(float(v) for k, v in values.items() if k != "al")
        control = float(values.get("copy", float("inf")))
        table[name] = {
            "values": {k: float(v) for k, v in values.items()},
            "worst_baseline": worst,
            "verdict": _verdict(al, worst, control),
        }

    wins = [k for k, v in table.items() if v["verdict"] == "al-wins"]
    sound = [k for k, v in table.items() if v["verdict"] == "sound-not-evidence"]
    sensitive = [k for k, v in table.items() if v["verdict"] != "not-sensitive"]
    return {
        "tau_rise_s": TAU_RISE,
        "tau_fall_s": TAU_FALL,
        "inner_dt": INNER_DT,
        "outer_dt": OUTER_DT,
        "rungs": table,
        "summary": {
            "rungs_measured": len(rungs),
            "rungs_sensitive": len(sensitive),
            "al_wins": wins,
            "sound_not_evidence": sound,
            "note": (
                "r1-r3 pass by construction (closed form) and are reported to show the "
                "rule is sound, not as evidence of life; r5 is the rung that separates a "
                "designed dynamic from a learned one; r7 has no estimate to score yet"
            ),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="AL temporal ladder probe")
    ap.add_argument("--report", type=str, default="")
    args = ap.parse_args()

    result = run()
    cols = ("al", "mlp", "copy", "const", "forgery")
    print(f"{'rung':<16}" + "".join(f"{c:>10}" for c in cols) + "  verdict")
    for name, row in result["rungs"].items():
        vals = row["values"]
        if name == "r7_clock":
            print(
                f"{name:<16}{'—':>10}{'—':>10}{'—':>10}{'—':>10}{'—':>10}  "
                f"{row['verdict']} (detect back/fwd="
                f"{vals['detect_backward']:.0f}/{vals['detect_forward']:.0f}, "
                f"false alarms={vals['false_alarm']:.0%})"
            )
            continue
        cells = "".join(
            f"{vals[k]:>10.2e}" if isinstance(vals.get(k), (int, float)) else f"{'--':>10}"
            for k in cols
        )
        print(f"{name:<16}{cells}  {row['verdict']}")
    print()
    print("al wins (control fails too):", ", ".join(result["summary"]["al_wins"]) or "(none)")
    print(
        "sound but no evidence (control also passes):",
        ", ".join(result["summary"]["sound_not_evidence"]) or "(none)",
    )
    if args.report:
        out = ROOT / args.report
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("report:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
