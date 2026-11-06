#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [αβγ] [B] [L3]
# =============================================================================
"""Which rungs survive an *optimised* fake? Provenance and ablation for the AL layer.

The project already has an anti-pseudo-intelligence standard on the system layer:

* six score types, only 驗證分 / 實際分 count (``ai/meta/intelligence.py``);
* ``census_reply_provenance.py`` cross-tabulates every *correct* benchmark answer
  against its producer, and only ``correct ∧ computed|other`` counts as the
  system producing it — a lookup is correct and is not intelligence;
* strict scoring separates ``wrong`` from ``abstain`` instead of counting both
  the same way.

None of that discipline existed for the life layer. ``al_ladder.py`` measured
what the rule does; that is a capability table, not a provenance table, and a
capability is exactly what a forgery can imitate. This script supplies the
missing half, with two independent mechanisms:

**Forgery budget.** A fake is not "a template"; it is a series of fakes with
increasing budget, and the rung is only admissible if *all* of them fail:

* ``table_noise``  — remembers the last level, adds noise, never reads a clock.
                     The "Day N log" fake: state is what was last written down.
* ``call_clock``   — decays once per call regardless of elapsed time. Looks
                     right whenever the sampling is regular, which is why the
                     on-screen behaviour of such an account is convincing.
* ``imitate``      — an MLP trained on the AL rule's own trajectories, given the
                     same (v, target, dt). The strongest behavioural imitation
                     available at this budget: if a rung cannot separate the
                     rule from its learned copy, the rung is not evidence.
* ``clone``        — an independent reimplementation of the closed form. Not a
                     fake in motive — same mechanism — and included on purpose:
                     no behavioural test can separate it, so a claim that rests
                     only on behaviour is claiming what a reimplementation also
                     has. Reported separately as the behavioural ceiling.

**Mechanism ablation.** Each rung names the mechanism it is supposed to be
measuring, and the same rung is re-run with that mechanism removed:

* ``rule``        — remove the rule (identity) → r3, r4, r5 must break;
* ``persistence`` — remove the state file → r6 must break.

A rung whose error does not move when its mechanism is removed is measuring the
test's shape, not the mechanism. That is the check that would have caught the
endpoint-only attractor rung, which a constant passed.

Verdicts per rung:

* ``admissible``         — AL exact, control fails, every forgery fails, ablation
                           breaks it. This is the only state that can be quoted.
* ``control-passes``     — doing nothing also passes it (r1, r2 today).
* ``forgery-passes: X``  — a fake with a finite budget still passes; the rung
                           needs a harder variant before it means anything.
* ``mechanism-missing``  — the mechanism is not built (r7: no clock estimate).

Usage:
    ./.venv/bin/python scripts/al_forgery.py
    ./.venv/bin/python scripts/al_forgery.py --report data/intelligence_reports/al_forgery.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LADDER = ROOT / "scripts" / "al_ladder.py"


def _load_ladder():
    spec = importlib.util.spec_from_file_location("al_ladder_for_forgery", LADDER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["al_ladder_for_forgery"] = module
    spec.loader.exec_module(module)
    return module


ladder = _load_ladder()
ar = ladder.ar
TOL = ladder.SENSITIVE  # exactness: these rungs demand agreement with the rule


# =============================================================================
# Forgeries with a budget
# =============================================================================
class TableNoiseForgery(ladder.ForgeryModel):
    """Echo the current value plus noise, never read the clock.

    Stateless on purpose. An earlier version kept the level in an attribute and
    decayed it, which made it accumulate across the rung's 200 samples: after a
    few hundred calls the level sat at zero, both sides of the semigroup test
    read ~0, and the fake *passed* r1 with error 0.0. That is a test artefact,
    not a capability — a candidate whose error can go to zero by saturating must
    not be reused across samples without a reset. Echoing the given state has no
    such hidden channel.
    """

    name = "table_noise"
    budget = "last value + noise, no clock"

    def step(self, state: ar.AffectState, now: float) -> ar.AffectState:
        level = float(np.clip(state.arousal + self._rng.normal(0.0, 0.02), 0.0, 1.0))
        return ar.AffectState(level, level, now)


class CallClockForgery:
    """Decay per call, not per second — the "one diary entry per day" fake.

    It has a plausible-looking curve: each message moves the value toward the
    baseline, so a viewer who sees one message per day cannot tell. It fails the
    moment the sampling rate is not the schedule, which is precisely the variable
    the real rule is invariant to.
    """

    name = "call_clock"
    budget = "one decay step per call"

    def step(self, state: ar.AffectState, now: float) -> ar.AffectState:
        # One fixed step toward the baseline, independent of `now`. Derived from
        # the given state, not from an attribute: the same saturation artefact
        # that let the table fake pass r1 applies here.
        level = ladder.BASELINE + (state.arousal - ladder.BASELINE) * 0.9
        return ar.AffectState(level, level, now)


class ImitateForgery(ladder.MLPModel):
    """The trained imitation, under the name the matrix reports."""

    name = "imitate"
    budget = "training on the rule's own trajectories, with dt"


class CloneModel:
    """Not a fake: the same rule, independently written.

    Its purpose is to bound what behaviour can prove. It passes every rung, so a
    claim of the form "no baseline reproduces this behaviour" would be false —
    the honest claim is about *provenance and mechanism*, which is why the
    ablation column exists and why the project's score-type discipline matters.
    """

    name = "clone"
    budget = "same rule, different code"
    is_equivalent_mechanism = True

    def step(self, state: ar.AffectState, now: float) -> ar.AffectState:
        dt = now - state.at
        if not np.isfinite(dt) or dt <= 0.0:
            return state
        baseline, tr, tf = ladder.BASELINE, ladder.TAU_RISE, ladder.TAU_FALL
        d0 = state.target - baseline
        u0 = state.arousal - baseline
        ef = np.exp(-dt / tf)
        er = np.exp(-dt / tr)
        u = u0 * er + d0 * tf / (tf - tr) * (ef - er)
        return ar.AffectState(
            min(max(baseline + float(u), 0.0), 1.0),
            min(max(baseline + float(d0 * ef), 0.0), 1.0),
            now,
        )


# =============================================================================
# Ablations: remove the mechanism a rung claims to measure
# =============================================================================
def ablate_rule(models: List) -> Dict[str, float]:
    """Replace the rule with identity: r3-r5 must stop being exact."""
    return ladder.rung_inner_dt([ladder.CopyModel()], None)


def restart_without_persistence(tmp: Path) -> float:
    """Persist, then lose the file. If r6 still passes, it was never measuring
    persistence."""
    level = 0.9
    elapsed = 300.0
    path = tmp / "ablated.json"
    clock = [1000.0]
    tracker = ar.AffectTracker(path=path, clock=lambda: clock[0])
    tracker.observe_level(level)
    clock[0] += elapsed
    path.unlink()  # the mechanism, removed
    truth = ar.advance(ar.AffectState(ladder.BASELINE, level, 1000.0), 1000.0 + elapsed).arousal
    reborn = ar.AffectTracker(path=path, clock=lambda: clock[0])
    got = reborn.arousal()
    if got is None:  # unobserved after losing the file: D11, not a value
        return abs(truth - ladder.BASELINE)
    return abs(got - truth)


# =============================================================================
# Matrix
# =============================================================================
MECHANISM = {
    "r3_attractor": "rule",
    "r4_inner_dt": "rule",
    "r5_outer_dt": "rule",
    "r6_restart": "persistence",
}


def run(tmp_root: Optional[Path] = None) -> Dict[str, object]:
    rng = np.random.default_rng(29)
    tmp = Path(tempfile.mkdtemp(prefix="al_forgery_", dir=str(tmp_root) if tmp_root else None))

    al = ladder.ALModel()
    clone = CloneModel()
    controls = [ladder.CopyModel(), ladder.ConstModel()]
    imitate = ImitateForgery()  # stateless: built once, reused across rungs

    def forgery_set() -> List:
        """Fresh stateful fakes per rung — a fake that remembers last rung's
        levels is measuring the harness, not the rung."""
        return [TableNoiseForgery(), CallClockForgery(), imitate]

    rungs = {
        "r1_semigroup": ladder.rung_semigroup,
        "r2_sampling": ladder.rung_sampling,
        "r3_attractor": ladder.rung_attractor,
        "r4_inner_dt": ladder.rung_inner_dt,
        "r5_outer_dt": ladder.rung_outer_dt,
    }

    # The rule-backed rungs are ablated by replacing the rule with identity.
    # Computed before scoring: the verdict has to see the ablation, or every
    # rung comes back "unablated" and the gate proves nothing.
    ablated_by = {
        name: fn([ladder.CopyModel()], np.random.default_rng(7))["copy"]
        for name, fn in rungs.items()
        if name in ("r3_attractor", "r4_inner_dt", "r5_outer_dt")
    }

    rows: Dict[str, Dict[str, object]] = {}
    for name, fn in rungs.items():
        values = fn([al, clone] + controls, rng)
        fvals = {f.name: fn([f], np.random.default_rng(5))[f.name] for f in forgery_set()}
        rows[name] = _row(values, fvals, ablated=ablated_by.get(name))

    # r6 is the one rung with its own harness: it needs a process to die.
    restart = ladder.rung_restart(None, tmp)
    truth = ar.advance(ar.AffectState(ladder.BASELINE, 0.9, 1000.0), 1300.0).arousal
    rows["r6_restart"] = _row(
        {
            "al": restart["al"],
            "clone": 0.0,
            "copy": restart["copy"],
            "const": abs(ladder.BASELINE - truth),
        },
        {
            "table_noise": restart["forgery"],
            # Neither fake has state that survives a restart, so both fall back
            # to the number they last wrote down; stated, not omitted.
            "call_clock": abs(0.9 - truth),
            "imitate": abs(0.9 - truth),
        },
        ablated=restart_without_persistence(tmp),
    )

    clock = ladder.rung_clock_attack(tmp)
    caught = float(clock["detect_backward"]) + float(clock["detect_forward"])
    rows["r7_clock"] = {
        "values": clock,
        "verdict": (
            "doubt-works" if caught == 2.0 and float(clock["false_alarm"]) <= 0.05 else "doubt-weak"
        ),
    }

    admissible = [k for k, v in rows.items() if v["verdict"] == "admissible"]
    return {
        "tolerance": TOL,
        "forgeries": {
            f.name: getattr(f, "budget", "training budget: same (v, target, dt) traces")
            for f in forgery_set()
        },
        "clone_note": CloneModel.budget,
        "rungs": rows,
        "summary": {
            "admissible": admissible,
            "counts": _counts(rows),
            "note": (
                "admissible = AL exact AND the identity/constant controls fail AND every "
                "finite-budget forgery fails AND removing the named mechanism breaks the rung; "
                "the clone column is the behavioural ceiling and is not a forgery"
            ),
        },
    }


def _row(values: Dict[str, float], forgeries: Dict[str, float], ablated: Optional[float]):
    al = float(values["al"])
    controls = {k: float(v) for k, v in values.items() if k in ("copy", "const")}
    control_pass = [k for k, v in controls.items() if v <= TOL]
    forgery_pass = [k for k, v in forgeries.items() if v <= TOL]
    if al > TOL:
        verdict = "al-fails"
    elif control_pass:
        verdict = "control-passes"
    elif forgery_pass:
        verdict = "forgery-passes:" + ",".join(sorted(forgery_pass))
    elif ablated is not None and float(ablated) > TOL:
        verdict = "admissible"
    elif ablated is None:
        verdict = "unablated"
    else:
        verdict = "mechanism-not-load-bearing"
    return {
        "values": {k: round(float(v), 12) for k, v in values.items() if k != "al"} | {"al": al},
        "forgeries": {k: round(float(v), 12) for k, v in forgeries.items()},
        "controls_passing": control_pass,
        "forgeries_passing": forgery_pass,
        "ablated": None if ablated is None else round(float(ablated), 12),
        "verdict": verdict,
    }


def _counts(rows: Dict[str, Dict[str, object]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows.values():
        key = str(row["verdict"]).split(":")[0]
        counts[key] = counts.get(key, 0) + 1
    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description="AL anti-forgery gate")
    ap.add_argument("--report", type=str, default="")
    args = ap.parse_args()

    result = run()
    cols = ("al", "clone", "table_noise", "call_clock", "imitate")
    print(f"{'rung':<15}" + "".join(f"{c:>12}" for c in cols) + f"{'ablated':>10}  verdict")
    for name, row in result["rungs"].items():
        if name == "r7_clock":
            v = row["values"]
            print(
                f"{name:<15}{'—':>12}{'—':>12}{'—':>12}{'—':>12}{'—':>12}{'—':>10}  "
                f"{row['verdict']} (back/fwd={v['detect_backward']:.0f}/{v['detect_forward']:.0f}, "
                f"false alarms={v['false_alarm']:.0%})"
            )
            continue
        cells = {"al": row["values"]["al"], "clone": row["values"].get("clone")} | {
            k: v for k, v in row["forgeries"].items()
        }
        line = "".join(
            f"{cells.get(c, float('nan')):>12.2e}" if cells.get(c) is not None else f"{'--':>12}"
            for c in cols
        )
        abl = row["ablated"]
        abl_cell = f"{abl:>10.2e}" if abl is not None else f"{'-':>10}"
        print(f"{name:<15}{line}{abl_cell}  {row['verdict']}")
    print()
    print("admissible evidence:", ", ".join(result["summary"]["admissible"]) or "(none)")
    print("counts:", result["summary"]["counts"])
    if args.report:
        out = ROOT / args.report
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("report:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
