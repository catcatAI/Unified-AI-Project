#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L5] [βγ] [A] [L4]
# =============================================================================
"""A computed ceiling for one process's GPU use, from the kernel's own counters.

There is no per-process GPU utilisation limit on Intel Arc through torch, so a
ceiling has to be *computed* and enforced. The Xe driver publishes the two
numbers that make the computation exact, per client, in ``/proc/<pid>/fdinfo``:

* ``drm-cycles-<engine>`` - GPU cycles this client consumed;
* ``drm-total-cycles-<engine>`` - GPU cycles elapsed (same value in every fd).

Their ratio over an interval **is** the utilisation - the quantity ``gputop``
prints as a percentage - so no clock rate or wall-clock estimate is needed.
``drm-total-cycles`` advances at the GPU's 19.2 MHz crystal rate whether the
client runs or not, which is what makes it usable as a clock.

How the ceiling is enforced
---------------------------
The obvious controller - pause the process, watch the ratio fall, resume - does
**not** work on this driver, and the failure was measured rather than assumed:
while a process is ``SIGSTOP``ped the driver keeps crediting it with ~92% of
the elapsed cycles even though the GPU is free (a second burner launched
alongside the paused one ran at full speed, 0.034 s vs 0.035 s baseline). A
controller that waits for the counter to fall would therefore wait forever.

So the pause length is **computed once, at the moment of pausing**, from the
work actually measured in the current run phase:

    pause_until_total = window_start_total + ceil(busy_cycles / target)

After which ``busy_cycles / elapsed_cycles == target`` exactly, by
construction. The window is rebased when the process resumes, so the phantom
cycles credited during a pause never bias the next measurement, and the work
counted for reporting is only the work credited while the process was allowed
to run (measured at each pause point).

Usage (limit a process already running):

    python3 scripts/gpu_limit.py --pid 1234 --target 0.5 --seconds 60

Usage (launch and limit):

    python3 scripts/gpu_limit.py --run --target 0.5 --seconds 60 -- burn.py
"""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# The compute engine on Xe is ``ccs``; the others are kept so the reader works
# on i915 too (``rcs`` there), and a client only fills the engines it uses.
ENGINES = ("rcs", "bcs", "ccs", "vcs", "vecs")

# ``drm-total-cycles`` is the GPU's 19.2 MHz crystal counter. Only used to turn
# a computed cycle budget into a wall-clock estimate for logging; the decision
# itself never uses wall time.
CRYSTAL_HZ = 19_200_000


def read_counters(fdinfo_dir: Path) -> Tuple[int, int]:
    """``(busy_cycles, total_cycles)`` for one process, from its DRM fdinfo.

    ``busy`` is summed across the process's DRM file descriptions (each tracks
    its own submissions); ``total`` is the GPU's elapsed-cycle counter, which is
    the same value in every fd, so it is taken as the maximum instead of summed.
    """
    busy = 0
    total = 0
    for entry in fdinfo_dir.glob("*"):
        try:
            text = entry.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        per_busy = 0
        per_total = 0
        seen = False
        for line in text.splitlines():
            key, _, raw = line.partition(":")
            key = key.strip()
            if not key.startswith("drm-"):
                continue
            value = raw.strip()
            if not value.isdigit():
                continue
            if key.startswith("drm-cycles-"):
                engine = key[len("drm-cycles-") :]
                if engine in ENGINES:
                    per_busy += int(value)
                    seen = True
            elif key.startswith("drm-total-cycles-"):
                engine = key[len("drm-total-cycles-") :]
                if engine in ENGINES:
                    per_total = max(per_total, int(value))
                    seen = True
        if not seen:
            continue
        busy += per_busy
        total = max(total, per_total)
    return busy, total


def resident_vram_mib(fdinfo_dir: Path) -> float:
    """VRAM this client currently holds, in MiB (0 when the driver omits it)."""
    total = 0
    for entry in fdinfo_dir.glob("*"):
        try:
            text = entry.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            key, _, raw = line.partition(":")
            if key.strip() == "drm-resident-vram" and raw.strip().isdigit():
                total += int(raw.strip())
    return total / (1024 * 1024)


def duty(busy: int, total: int) -> float:
    return float(busy) / float(total) if total > 0 else 0.0


def window_duty(busy: int, total: int, base_busy: int, base_total: int) -> float:
    elapsed = total - base_total
    return float(busy - base_busy) / float(elapsed) if elapsed > 0 else 0.0


def over_budget(busy: int, total: int, base_busy: int, base_total: int, target: float) -> bool:
    """Is the window's measured duty above the ceiling?"""
    elapsed = total - base_total
    if elapsed <= 0:
        return False
    return (busy - base_busy) > target * elapsed


def resume_total(busy: int, base_busy: int, base_total: int, target: float) -> int:
    """The ``total`` at which the window duty returns to exactly ``target``."""
    if target <= 0.0:
        raise ValueError("target must be > 0")
    return base_total + int(math.ceil((busy - base_busy) / target))


def cycles_to_seconds(cycles: int) -> float:
    return float(cycles) / float(CRYSTAL_HZ)


class Limiter:
    """Hold one process at or below ``target`` GPU duty by computed pausing."""

    def __init__(
        self,
        pid: int,
        *,
        target: float = 0.5,
        poll_seconds: float = 0.02,
        counters_timeout: float = 30.0,
    ) -> None:
        if not 0.0 < target <= 1.0:
            raise ValueError("target must be in (0, 1]")
        if poll_seconds <= 0:
            raise ValueError("poll must be > 0")
        if counters_timeout <= 0:
            raise ValueError("counters_timeout must be > 0")
        self.pid = int(pid)
        self.target = float(target)
        self.poll_seconds = float(poll_seconds)
        self.counters_timeout = float(counters_timeout)
        self.paused = False
        # work credited while the process was allowed to run, in cycles
        self.acc_busy = 0
        # one record per run phase (ended by a pause or by the end of the run)
        self.phases: List[Dict[str, Any]] = []
        self.start_busy = 0
        self.start_total = 0
        self.peak_resident_vram_mib = 0.0
        self._base_busy = 0
        self._base_total = 0
        self._resume_at: Optional[int] = None

    # -- counters -----------------------------------------------------------
    def sample(self) -> Tuple[int, int]:
        return read_counters(Path(f"/proc/{self.pid}/fdinfo"))

    def seed(self, busy: int, total: int, now: float) -> None:
        """Open the first measurement window at ``(busy, total)``.

        ``now`` is accepted for callers that want to stamp their own log; the
        controller itself never uses wall time.
        """
        del now
        self._base_busy = busy
        self._base_total = total
        self.start_busy = busy
        self.start_total = total
        self.acc_busy = 0
        self._resume_at = None

    def _alive(self) -> bool:
        """Is the process still there and not a zombie (a zombie has no fds)."""
        try:
            stat = Path(f"/proc/{self.pid}/stat").read_text(encoding="utf-8")
        except OSError:
            return False
        return stat.rsplit(")", 1)[-1].split()[:1] != ["Z"]

    def _wait_for_counters(self, timeout: float = 0.0) -> Optional[Tuple[int, int]]:
        """Block until the client has opened a DRM node, or it goes away.

        A freshly launched process has no ``drm-*`` counters until its GPU
        driver is initialised (torch takes seconds). Seeding before that would
        make the first window span the whole GPU uptime and the ceiling would
        never trigger.
        """
        deadline = time.monotonic() + (timeout or self.counters_timeout)
        while True:
            try:
                busy, total = self.sample()
            except (FileNotFoundError, ProcessLookupError):
                return None
            if total > 0:
                return busy, total
            if not self._alive() or time.monotonic() >= deadline:
                return None
            time.sleep(min(self.poll_seconds, 0.05))

    # -- the one decision ---------------------------------------------------
    def step(self, busy: int, total: int, now: float) -> str:
        """``run`` / ``pause`` / ``resume`` for this sample."""
        del now
        if self.paused:
            if self._resume_at is not None and total >= self._resume_at:
                self._base_busy = busy
                self._base_total = total
                self._resume_at = None
                return "resume"
            return "pause"
        if over_budget(busy, total, self._base_busy, self._base_total, self.target):
            used = busy - self._base_busy
            self.acc_busy += used
            self._resume_at = resume_total(busy, self._base_busy, self._base_total, self.target)
            self.phases.append(
                {
                    "start_total": self._base_total,
                    "busy_cycles": used,
                    "elapsed_cycles": total - self._base_total,
                    "pause_until_total": self._resume_at,
                    "pause_seconds": round(cycles_to_seconds(self._resume_at - total), 3),
                }
            )
            # keep ``acc_busy`` counting work up to ``_base_busy`` so the final
            # segment can be added without double counting
            self._base_busy = busy
            self._base_total = total
            return "pause"
        return "run"

    def _signal(self, stop: bool) -> None:
        os.kill(self.pid, signal.SIGSTOP if stop else signal.SIGCONT)

    def run(self, *, seconds: Optional[float] = None) -> Dict[str, Any]:
        got = self._wait_for_counters()
        if got is None:
            return {
                "pid": self.pid,
                "target": self.target,
                "start_busy_cycles": 0,
                "start_total_cycles": 0,
                "end_busy_cycles": 0,
                "end_total_cycles": 0,
                "acc_busy_cycles": 0,
                "elapsed_cycles": 0,
                "measured_duty": 0.0,
                "driver_reported_duty": 0.0,
                "peak_resident_vram_mib": 0.0,
                "pauses": 0,
                "phases": [],
                "counters_seen": False,
            }
        busy, total = got
        self.seed(busy, total, time.monotonic())
        start_busy, start_total = busy, total
        deadline = None if seconds is None else time.monotonic() + float(seconds)
        last = (busy, total)
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                break
            if not self._alive():
                break
            try:
                busy, total = self.sample()
            except (FileNotFoundError, ProcessLookupError):
                break
            if total < last[1]:
                # a zombie reports zeros; never let that rewind the clock
                break
            last = (busy, total)
            try:
                self.peak_resident_vram_mib = max(
                    self.peak_resident_vram_mib,
                    resident_vram_mib(Path(f"/proc/{self.pid}/fdinfo")),
                )
            except (FileNotFoundError, ProcessLookupError):
                pass
            decision = self.step(busy, total, time.monotonic())
            if decision == "pause" and not self.paused:
                try:
                    self._signal(True)
                except ProcessLookupError:
                    break
                self.paused = True
            elif decision == "resume" and self.paused:
                try:
                    self._signal(False)
                except ProcessLookupError:
                    break
                self.paused = False
            # never sleep past the computed resume point: the crystal counter
            # is a clock, so the remaining pause is known in seconds
            wait = self.poll_seconds
            if self.paused and self._resume_at is not None:
                remaining = cycles_to_seconds(self._resume_at - total)
                wait = min(self.poll_seconds, remaining) if remaining > 0 else 0.0
            time.sleep(wait)

        if self.paused:
            try:
                self._signal(False)
            except ProcessLookupError:
                pass
            self.paused = False
        end_busy, end_total = last
        try:
            tail_busy, tail_total = self.sample()
            if tail_total >= end_total:
                end_busy, end_total = tail_busy, tail_total
        except (FileNotFoundError, ProcessLookupError):
            pass
        # work done in the last (unpaused) segment
        self.acc_busy += end_busy - self._base_busy
        self.phases.append(
            {
                "start_total": self._base_total,
                "busy_cycles": end_busy - self._base_busy,
                "elapsed_cycles": end_total - self._base_total,
                "pause_until_total": None,
                "pause_seconds": 0.0,
            }
        )
        elapsed = end_total - start_total
        return {
            "pid": self.pid,
            "target": self.target,
            "start_busy_cycles": start_busy,
            "start_total_cycles": start_total,
            "end_busy_cycles": end_busy,
            "end_total_cycles": end_total,
            "acc_busy_cycles": self.acc_busy,
            "elapsed_cycles": elapsed,
            "measured_duty": round(duty(self.acc_busy, elapsed), 6),
            "driver_reported_duty": round(duty(end_busy - start_busy, elapsed), 6),
            "peak_resident_vram_mib": round(self.peak_resident_vram_mib, 1),
            "pauses": len(self.phases) - 1,
            "phases": self.phases[:50],
            "counters_seen": True,
        }


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, default=0, help="limit this process")
    parser.add_argument("--target", type=float, default=0.5, help="GPU duty ceiling (0, 1]")
    parser.add_argument("--poll", type=float, default=0.02, help="sample period, seconds")
    parser.add_argument("--seconds", type=float, default=0.0, help="stop limiting after N seconds")
    parser.add_argument("--out", default="", help="write the report here")
    parser.add_argument(
        "--run",
        action="store_true",
        help="launch the command after -- and limit that child instead of --pid",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    if args.run:
        command = args.command
        if command[:1] == ["--"]:
            command = command[1:]
        if not command:
            parser.error("--run needs a command after --")
        child = subprocess.Popen(command)
        limiter = Limiter(child.pid, target=args.target, poll_seconds=args.poll)
        try:
            report = limiter.run(seconds=args.seconds or None)
            child.wait()
        except KeyboardInterrupt:
            limiter._signal(False)
            child.kill()
            raise SystemExit(130)
        report["exit_code"] = child.returncode
        report["command"] = command
    else:
        if args.pid <= 0:
            parser.error("--pid is required unless --run is used")
        limiter = Limiter(args.pid, target=args.target, poll_seconds=args.poll)
        report = limiter.run(seconds=args.seconds or None)

    print(json.dumps(report, indent=2))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    ok = report["measured_duty"] <= args.target
    print(
        f"measured_duty={report['measured_duty']:.4f} target={args.target:.2f} "
        f"{'OK' if ok else 'OVER'}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
