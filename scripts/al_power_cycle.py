#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [αβ] [B] [L3]
# =============================================================================
"""Power-cycle continuity, end to end: real file, real clock, real new process.

The ladder's r6 restarts a tracker inside one Python process, which proves the
serialisation but not the thing that matters: that a *new process*, starting
later, reads the state and continues from the elapsed wall-clock time instead of
resetting to the baseline or freezing at the last written value.

So this script does it with three processes:

    1. ``--write``  observe a level, persist, print the stored numbers
    2. (the parent sleeps ``--seconds``: a real gap, nothing alive in between)
    3. ``--read``   construct a fresh tracker from the same file, print what it reads

The parent compares the read value against the analytic continuation of the
stored state by the measured elapsed time, and reports the two forgeries in the
same units: ``hold`` (keep the last value, the diary-entry fake) and ``reset``
(jump back to the baseline, the amnesia fake).

Usage:
    ./.venv/bin/python scripts/al_power_cycle.py --seconds 3
    ./.venv/bin/python scripts/al_power_cycle.py --seconds 0.5 --json /tmp/pc.json
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "apps" / "backend" / "src"


def _child(mode: str, path: Path) -> Dict[str, object]:
    """One process lifetime: write or read, then exit."""
    sys.path.insert(0, str(SRC))
    from core.life import al_arousal as ar

    if mode == "write":
        tracker = ar.AffectTracker(path=path, clock=time.time, monotonic=time.monotonic)
        tracker.observe_level(0.9)
        return {
            "arousal": tracker.arousal(),
            "written_at": time.time(),
            "state": json.loads(path.read_text(encoding="utf-8")),
        }

    started = time.time()
    tracker = ar.AffectTracker(path=path, clock=time.time, monotonic=time.monotonic)
    value = tracker.arousal()
    verdict = tracker.clock_status()
    return {
        "arousal": value,
        "read_at": time.time(),
        "process_started_at": started,
        "clock_status": None if verdict is None else verdict.reason,
    }


def run(seconds: float, path: Optional[Path] = None) -> Dict[str, object]:
    path = path or Path(tempfile.mkdtemp(prefix="al_power_cycle_")) / "al_affect.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    first = _child("write", path)
    time.sleep(seconds)  # nothing is running: the state only exists on disk
    second = _child("read", path)
    # The gap is measured from the *persisted* timestamp, not from after the write
    # child exited: the reader's own start-up time is real elapsed time and the
    # analytic continuation has to include it, or the measurement blames the code
    # for the interpreter's import time.
    gap = second["read_at"] - float(first["state"]["at"])

    # Analytic continuation of what was written, by the measured gap.
    sys.path.insert(0, str(SRC))
    from core.life import al_arousal as ar

    stored = ar.AffectState(
        arousal=float(first["state"]["arousal"]),
        target=float(first["state"]["target"]),
        at=float(first["state"]["at"]),
    )
    truth = ar.advance(stored, stored.at + gap).arousal
    read = float(second["arousal"])
    held = float(first["arousal"])

    return {
        "gap_seconds": round(gap, 3),
        "stored": first["state"],
        "read_arousal": read,
        "analytic_arousal": truth,
        "error": abs(read - truth),
        "forgery_hold_error": abs(held - truth),
        "forgery_reset_error": abs(ar.AROUSAL_BASELINE - truth),
        "clock_status": second["clock_status"],
        "passed": abs(read - truth) < 1e-6 and not math.isnan(truth),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="AL power-cycle continuity (3 processes)")
    ap.add_argument("--seconds", type=float, default=3.0)
    ap.add_argument("--json", type=str, default="")
    args = ap.parse_args()

    result = run(args.seconds)
    print(f"gap              {result['gap_seconds']} s")
    print(
        f"stored           arousal={result['stored']['arousal']:.6f} at={result['stored']['at']:.3f}"
    )
    print(f"read after gap   {result['read_arousal']:.6f}")
    print(f"analytic truth   {result['analytic_arousal']:.6f}")
    print(f"error            {result['error']:.3e}")
    print(f"forgery hold     {result['forgery_hold_error']:.3e}  (keeps the last value)")
    print(f"forgery reset    {result['forgery_reset_error']:.3e}  (jumps to baseline)")
    print(f"clock status     {result['clock_status']}")
    print("passed" if result["passed"] else "FAILED")
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("report:", out)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--write", "--read"):
        mode = sys.argv[1][2:]
        target = Path(sys.argv[2])
        print(json.dumps(_child(mode, target)))
        raise SystemExit(0)
    raise SystemExit(main())
