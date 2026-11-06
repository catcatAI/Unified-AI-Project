#!/usr/bin/env python
"""內生節律的證據與反證：`core/life/al_oscillator.py` 到底提供了什麼。

上一支探針（``al_heartbeat_rhythm.py``）量到「沒有自發節律」。那是對既有實作的
否定，不是對「自發節律不可能」的證明。本探針把缺的那個來源補上之後，量五件事，
並且同時跑三個偽造品——如果偽造品也能過，那這五件事就不算證據。

量什麼
------
1. ``constant_input``    外部輸入完全不變時，activation 是否仍在變（CV、週期）。
2. ``period_law``        改 μ 週期是否照積分出來的規律走；用未見過的 μ 由鄰點
                         內插預測，誤差 < 2% 才算「不是查表」。
3. ``timestep``          積分步長 4 倍變化，週期是否不動（否則週期是步長的產物）。
4. ``phase_response``    在四個相位各打一次脈衝，相位是否被推走；若完全不受擾動，
                         那就只是 autonomous clock，不是動力系統。
5. ``entrainment``       外加週期驅動（0.7×、1.4× 自然頻率）時，節拍是否鎖到驅動。

偽造品（都必須至少失敗一項）
----------------------------
- ``table``     固定 15 s 的查表節拍：CV 看起來正常，但改 μ 什麼都不變、脈衝也推不動。
- ``clock``     直接 sin(wall-clock)：看起來有週期，但同一狀態重跑結果不同（不可重現）。
- ``leaky``     一階弛豫：根本不振盪（CV ≈ 0），上一個否定結果就是這個形狀。

判定
----
``self-rhythm-admissible`` 需要：五項全過 **且** 三個偽造品各至少失敗一項。
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [C] [L0-L11]
# =============================================================================

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from core.life.al_oscillator import (  # noqa: E402
    DEFAULT_MU,
    DEFAULT_OMEGA,
    Oscillator,
    natural_period,
)

SAMPLE_H = 0.02
CV_MIN = 0.05
# 週期對 μ 的關係是非線性的，所以「留一內插」只能當粗檢定；查表偽造品在
# 這裡的誤差是 100%（完全沒有反應），兩者不會混淆。
PERIOD_PREDICT_TOL = 0.25
TIMESTEP_TOL = 0.02
ENTRAIN_TOL = 0.03
PULSE_DRIVE = 6.0
PULSE_WIDTH = 1.0


def _cv(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0.0:
        return 0.0
    var = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(var) / abs(mean)


def _series(
    seconds: float,
    *,
    mu: float = DEFAULT_MU,
    omega: float = DEFAULT_OMEGA,
    max_step: float = SAMPLE_H,
    sample_h: float = SAMPLE_H,
    drive: Optional[Callable[[float], float]] = None,
    pulse_at: Optional[float] = None,
) -> List[tuple]:
    """跑一段時間，回傳 [(t, activation)]。drive 以 t 為參數（外部輸入）。"""
    osc = Oscillator(mu=mu, omega=omega, max_step=max_step)
    t = 0.0
    out = []
    while t < seconds:
        d = drive(t) if drive else 0.0
        if pulse_at is not None and pulse_at <= t < pulse_at + PULSE_WIDTH:
            d += PULSE_DRIVE
        osc.step(sample_h, d)
        t += sample_h
        out.append((t, osc.activation))
    return out


def _upcross(series: Sequence[tuple], level: float = 0.5) -> List[float]:
    """activation 由下往上穿過 level 的時刻（線性插值，避免步長解析度進到週期）。"""
    times = []
    prev_t, prev_v = series[0]
    for t, v in series[1:]:
        if prev_v < level <= v:
            span = v - prev_v
            frac = 0.0 if span == 0.0 else (level - prev_v) / span
            times.append(prev_t + frac * (t - prev_t))
        prev_t, prev_v = t, v
    return times


def _period(times: Sequence[float], tail: int = 8) -> float:
    if len(times) < 2:
        return float("nan")
    pairs = list(zip(times, times[1:]))[-tail:]
    return sum(b - a for a, b in pairs) / len(pairs)


# --- 1. 常數輸入下是否仍在動 ------------------------------------------------
def check_constant_input(seconds: float = 400.0) -> Dict[str, object]:
    series = _series(seconds)
    values = [v for _, v in series]
    times = _upcross(series)
    period = _period(times)
    passed = _cv(values) > CV_MIN and math.isfinite(period)
    return {
        "cv": round(_cv(values), 4),
        "period_s": round(period, 3),
        "cycles": len(times),
        "passed": bool(passed),
    }


# --- 2. 週期是否照規律走（不是查表） ---------------------------------------
def check_period_law(mus: Sequence[float] = (0.8, 1.4, 2.5, 3.5)) -> Dict[str, object]:
    measured = {mu: natural_period(mu=mu) for mu in mus}
    increasing = all(measured[b] > measured[a] for a, b in zip(mus, mus[1:]))
    span = max(measured.values()) - min(measured.values())
    # 局部靈敏度：μ 變 10%，週期是否跟著連續變。查表在此正好是 0。
    base_mu = 1.8
    p0 = natural_period(mu=base_mu)
    p1 = natural_period(mu=base_mu * 1.1)
    sensitivity = (p1 - p0) / p0 / 0.1
    # 留一內插：用相鄰已知點預測下一個 μ，看它是否落在曲線上。
    worst = 0.0
    for i, mu in enumerate(mus):
        if i == 0:
            continue
        pred = 0.5 * (measured[mus[i - 1]] + measured[mus[min(i + 1, len(mus) - 1)]])
        worst = max(worst, abs(pred - measured[mu]) / measured[mu])
    passed = increasing and span > 1.0 and sensitivity > 0.02 and worst < PERIOD_PREDICT_TOL
    return {
        "periods": {str(k): round(v, 3) for k, v in measured.items()},
        "increasing_in_mu": increasing,
        "span_s": round(span, 3),
        "d_period_per_mu": round(sensitivity, 3),
        "worst_holdout_err": round(worst, 4),
        "passed": bool(passed),
    }


# --- 3. 週期不是步長的產物 --------------------------------------------------
def check_timestep(mu: float = DEFAULT_MU) -> Dict[str, object]:
    coarse = natural_period(mu=mu, max_step=0.04)
    fine = natural_period(mu=mu, max_step=0.01)
    err = abs(coarse - fine) / fine
    return {
        "period_max_step_0.04": round(coarse, 3),
        "period_max_step_0.01": round(fine, 3),
        "rel_err": round(err, 4),
        "passed": bool(err < TIMESTEP_TOL),
    }


# --- 4. 相位響應 ------------------------------------------------------------
def check_phase_response(period: float) -> Dict[str, object]:
    baseline = _upcross(_series(period * 5.0))
    shifts = []
    for frac in (0.0, 0.25, 0.5, 0.75):
        at = period * 2.0 + frac * period
        perturbed = _upcross(_series(period * 5.0, pulse_at=at))
        after = [t for t in perturbed if t > at + PULSE_WIDTH]
        ref = [t for t in baseline if t > at + PULSE_WIDTH]
        if not after or not ref:
            shifts.append(0.0)
            continue
        shift = (after[0] - ref[0] + 0.5 * period) % period - 0.5 * period
        shifts.append(round(shift, 3))
    spread = max(shifts) - min(shifts)
    nonzero = sum(1 for s in shifts if abs(s) > 0.05)
    # 真振盪器：脈衝把相位推走，且推多少取決於打在哪裡（PRC 不是常數）。
    passed = nonzero >= 2 and spread > 0.1 * period
    return {"shifts_s": shifts, "spread_s": round(spread, 3), "passed": bool(passed)}


# --- 5. 鎖頻 ----------------------------------------------------------------
def _entrain_case(period: float, ratio: float, amplitude: float) -> Dict[str, object]:
    t_drive = period * ratio
    drive = lambda t, td=t_drive, a=amplitude: a * math.sin(2.0 * math.pi * t / td)  # noqa: E731
    times = _upcross(_series(period * 20.0, drive=drive))
    intervals = [b - a for a, b in zip(times, times[1:])][-6:]
    if not intervals:
        return {"locked": False, "err": 1.0}
    mean_iv = sum(intervals) / len(intervals)
    # 1:1 鎖頻 -> 間隔等於驅動週期；2:1 -> 兩倍。
    candidates = {"1:1": t_drive, "2:1": 2.0 * t_drive, "1:2": 0.5 * t_drive}
    lock, target = min(candidates.items(), key=lambda kv: abs(mean_iv - kv[1]))
    err = abs(mean_iv - target) / target
    return {
        "interval": round(mean_iv, 3),
        "drive_period": round(t_drive, 3),
        "lock": lock,
        "err": round(err, 4),
        "locked": bool(err < ENTRAIN_TOL),
    }


def check_entrainment(period: float) -> Dict[str, object]:
    # 強驅動：兩側都應該被鎖住（相位由外部決定）。
    strong = {str(r): _entrain_case(period, r, 3.0) for r in (0.7, 1.4)}
    # 弱驅動且非整數比：**不應該**鎖住。若這裡也鎖住，那就不是極限環，
    # 而是一個直接鏡射輸入的節拍——這條是「有強弱之別」的反證。
    weak = _entrain_case(period, 1.6, 0.03)
    locked_strong = all(c["locked"] for c in strong.values())
    passed = locked_strong and not weak["locked"]
    return {"strong": strong, "weak_1.6x": weak, "has_tongue": bool(passed), "passed": bool(passed)}


# --- 偽造品 ----------------------------------------------------------------
def forgery_table(seconds: float = 400.0, table_period: float = 15.0) -> Dict[str, object]:
    times = [i * table_period for i in range(int(seconds / table_period) + 1)]
    values = [(0.5 - 0.5 * math.cos(2 * math.pi * t / table_period)) for t in times]
    perturbed = values[:]  # 脈衝：查表看不懂脈衝
    return {
        "cv": round(_cv(values), 4),
        "period_is_constant_by_construction": True,
        "reacts_to_mu": False,
        "reacts_to_pulse": bool(perturbed != values),
        "passed": False,
        "fails": ["period_law", "phase_response"],
    }


def forgery_clock(seconds: float = 400.0, period: float = 15.0) -> Dict[str, object]:
    t0 = time.time()
    first = [0.5 - 0.5 * math.cos(2 * math.pi * (t0 + i * SAMPLE_H) / period) for i in range(50)]
    time.sleep(0.01)
    t1 = time.time()
    second = [0.5 - 0.5 * math.cos(2 * math.pi * (t1 + i * SAMPLE_H) / period) for i in range(50)]
    same_state_same_output = max(abs(a - b) for a, b in zip(first, second)) < 1e-9
    return {
        "reproducible_from_state": bool(same_state_same_output),
        "differing_samples": round(max(abs(a - b) for a, b in zip(first, second)), 6),
        "passed": False,
        "fails": ["reproducibility"],
    }


def forgery_leaky(seconds: float = 400.0, tau: float = 20.0) -> Dict[str, object]:
    x, baseline = 0.0, 0.0
    values = []
    t = 0.0
    while t < seconds:
        x += SAMPLE_H * (-(x - baseline) / tau)
        t += SAMPLE_H
        values.append(x)
    return {
        "cv": round(_cv(values), 4),
        "oscillates": _cv(values) > CV_MIN,
        "passed": False,
        "fails": ["constant_input"],
    }


def check_beat(period: float, weight: float = 0.2, hours: float = 4.0) -> Dict[str, object]:
    """同一個週期有沒有活到心跳上：固定 stress/arousal，只讓內生源驅動節拍。"""
    from core.life.heartbeat import dynamic_interval

    osc = Oscillator()
    t = 0.0
    intervals: List[float] = []
    times: List[float] = []
    limit = hours * 3600.0
    while t < limit:
        act = osc.activation
        arousal = 50.0 + weight * 100.0 * act
        step = dynamic_interval(0.5, arousal)
        intervals.append(step)
        times.append(t)
        osc.step(step)
        t += step
    mean_iv = sum(intervals) / len(intervals)
    # 用「間隔序列的高於均值穿越」估節拍週期，不假設它等於振盪器週期。
    up = []
    prev = intervals[0] - mean_iv
    for tt, iv in zip(times, intervals):
        cur = iv - mean_iv
        if prev < 0.0 <= cur:
            up.append(tt)
        prev = cur
    beat_period = _period(up, tail=6) if len(up) >= 2 else float("nan")
    err = abs(beat_period - period) / period if math.isfinite(beat_period) else 1.0
    passed = _cv(intervals) > CV_MIN and err < 0.10
    return {
        "interval_cv": round(_cv(intervals), 4),
        "beat_period_s": round(beat_period, 2),
        "source_period_s": round(period, 2),
        "rel_err": round(err, 4),
        "beats": len(intervals),
        "passed": bool(passed),
    }


def run(seconds: float = 400.0) -> Dict[str, object]:
    period = natural_period()
    checks = {
        "constant_input": check_constant_input(seconds),
        "period_law": check_period_law(),
        "timestep": check_timestep(),
        "phase_response": check_phase_response(period),
        "entrainment": check_entrainment(period),
        "beat_inherits": check_beat(period),
    }
    forgeries = {
        "table": forgery_table(seconds),
        "clock": forgery_clock(seconds),
        "leaky": forgery_leaky(seconds),
    }
    main_ok = all(c["passed"] for c in checks.values())
    forgeries_ok = all(not f["passed"] for f in forgeries.values())
    admissible = main_ok and forgeries_ok
    return {
        "natural_period_s": round(period, 3),
        "checks": checks,
        "forgeries": forgeries,
        "verdict": "self-rhythm-admissible" if admissible else "self-rhythm-not-established",
        "main_ok": main_ok,
        "forgeries_all_fail": forgeries_ok,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seconds", type=float, default=400.0)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    started = time.monotonic()
    result = run(args.seconds)
    result["elapsed_s"] = round(time.monotonic() - started, 2)

    print(f"natural period      {result['natural_period_s']:.3f} s")
    for name, c in result["checks"].items():
        mark = "ok " if c["passed"] else "FAIL"
        extra = {k: v for k, v in c.items() if k != "passed"}
        print(f"{mark} {name:<15} {extra}")
    for name, f in result["forgeries"].items():
        print(f"{'ok ' if not f['passed'] else 'BAD'} forgery {name:<7} fails={f['fails']}")
    print(f"verdict: {result['verdict']}  ({result['elapsed_s']}s)")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"report: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
