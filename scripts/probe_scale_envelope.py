#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Measure the capacity/scale envelope of the token-SNN decoder on this box.

The scaling question ("can the AI+AL boundary model be made bigger?") is a
hardware question before it is a modelling one, and this machine answers it with
two numbers that are not the ones people expect:

* VRAM is 9.9 GiB on the Arc B570, but it is **shared with whatever the user is
  running** — a game holds most of it, so the trainer's budget is a slice;
* host RAM is 7 GB total with a couple of GB free, and the trainer holds the pair
  list, the vocab and a batch of token ids *before* the first forward pass. This
  is the binding constraint, and it is invisible to device-memory thinking.

So the probe measures what one real step costs — peak device bytes and peak host
RSS — for a grid of (d_emb, d_hidden, layers, batch, max_len) on the row shape
the round actually trains on, and reports each against a budget. A config fits
only if both peaks stay under budget; the largest fitting config is the envelope.

Every config runs in **its own process**. That is not caution, it is the
measurement: the host high-water mark is monotonic per process, so several
configs in one process would report the first one's peak for all the rest — the
first version of this probe did exactly that and printed 2 TB of RSS.

Usage:
    ./.venv/bin/python scripts/probe_scale_envelope.py
    ./.venv/bin/python scripts/probe_scale_envelope.py --report out.json
    ./.venv/bin/python scripts/probe_scale_envelope.py --vram-budget 2.0
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

PROCESSED = REPO_ROOT / "apps" / "backend" / "data" / "processed"
MIB = 1024.0 * 1024.0

#: The round-9 operating point, kept as the reference row: everything else is
#: read as "×N of the shape that already ran for 21 minutes".
GRID: List[Dict[str, int]] = [
    {"d_emb": 96, "d_hidden": 1024, "layers": 1, "batch": 32, "max_len": 384},
    {"d_emb": 128, "d_hidden": 1536, "layers": 1, "batch": 32, "max_len": 384},
    {"d_emb": 128, "d_hidden": 2048, "layers": 2, "batch": 32, "max_len": 384},
    {"d_emb": 192, "d_hidden": 2048, "layers": 2, "batch": 48, "max_len": 512},
    {"d_emb": 256, "d_hidden": 3072, "layers": 2, "batch": 48, "max_len": 512},
    {"d_emb": 256, "d_hidden": 4096, "layers": 3, "batch": 64, "max_len": 512},
    {"d_emb": 384, "d_hidden": 5120, "layers": 3, "batch": 64, "max_len": 768},
]


def _pairs(path: Path, limit: int) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            pairs.append((str(row.get("input", "")), str(row.get("output", ""))))
            if limit and len(pairs) >= limit:
                break
    return pairs


def _host_mib() -> Tuple[float, float]:
    """(resident, high-water) MiB, read from /proc/self/status on Linux."""
    resident = high_water = 0.0
    try:
        with open("/proc/self/status", encoding="ascii") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    resident = float(line.split()[1]) / 1024.0
                elif line.startswith("VmHWM:"):
                    high_water = float(line.split()[1]) / 1024.0
    except OSError:  # not Linux: best effort
        import resource

        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        resident = high_water = peak / 1024.0
    return round(resident, 1), round(high_water, 1)


def _device_free(kind: str) -> Tuple[Optional[float], Optional[float]]:
    try:
        import torch

        if kind == "xpu":
            free, total = torch.xpu.mem_get_info()
            return round(free / MIB, 1), round(total / MIB, 1)
        if kind == "cuda":
            free, total = torch.cuda.mem_get_info()
            return round(free / MIB, 1), round(total / MIB, 1)
    except Exception:
        return None, None
    return None, None


def _sync(torch: Any, kind: str) -> None:
    if kind == "xpu":
        torch.xpu.synchronize()
    elif kind == "cuda":
        torch.cuda.synchronize()


def _measure(cfg: Dict[str, int], pairs: List[Tuple[str, str]], device: str, steps: int):
    """One warmup + ``steps`` real training steps at the target shape."""
    import torch

    from ai.ed3n.token_snn import TokenConfig, TokenSNN, TokenVocab, resolve_device

    torch.manual_seed(0)
    kind = resolve_device(torch, device)
    vocab = TokenVocab.build(
        [p for pair in pairs for p in pair], min_count=2, max_vocab=12000, numeric_atoms=True
    )
    config = TokenConfig(
        d_emb=cfg["d_emb"],
        d_hidden=cfg["d_hidden"],
        layers=cfg["layers"],
        timesteps=1,
        max_len=cfg["max_len"],
    )
    model = TokenSNN(vocab, config, device=kind)
    net = model.net
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    batch = min(cfg["batch"], len(pairs))
    # The runtime floor: torch + the XPU oneAPI stack already hold ~2 GiB of
    # host RSS before a parameter does any work (the device context, the L0/ze
    # loader and the shared-memory mappings all count in RSS). That floor, not
    # the model, is what makes "two torch jobs at once" impossible on a 7 GB
    # box, so it is measured *after* the first device allocation and reported
    # apart from the model's own growth.
    _ = torch.zeros(1, device=kind)
    _sync(torch, kind)
    floor_mib = _host_mib()[1]
    dev_free_before, dev_total = _device_free(kind)
    host_before, _ = _host_mib()

    def one_step(i: int) -> Tuple[Any, Tuple[Any, Any]]:
        start = (i * batch) % max(1, len(pairs) - batch)
        ids, mask, _starts, weights = model.make_batch_weighted(
            pairs[start : start + batch], tail_weight=1.0
        )
        opt.zero_grad(set_to_none=True)
        loss = model.loss(ids, mask, weights)
        loss.backward()
        opt.step()
        return loss, (ids, mask)

    loss_value = float(one_step(0)[0].detach())
    _sync(torch, kind)
    started = time.time()
    device_peaks: List[float] = []
    for step in range(steps):
        loss_value = float(one_step(step % 7)[0].detach())
        _sync(torch, kind)
        if kind == "xpu":
            device_peaks.append(torch.xpu.max_memory_allocated() / MIB)
        elif kind == "cuda":
            device_peaks.append(torch.cuda.max_memory_allocated() / MIB)
        else:
            device_peaks.append(0.0)
    elapsed = time.time() - started
    resident, high_water = _host_mib()
    params = sum(p.numel() for p in net.parameters())
    dev_free_after, _ = _device_free(kind)
    return {
        "config": dict(cfg),
        "device": kind,
        "params": params,
        "params_mib_fp32": round(params * 4 / MIB, 1),
        "peak_device_mib": round(max(device_peaks), 1),
        "device_total_mib": dev_total,
        "device_free_before_mib": dev_free_before,
        "device_free_after_mib": dev_free_after,
        "host_rss_after_mib": resident,
        "host_rss_peak_mib": high_water,
        "host_runtime_floor_mib": floor_mib,
        "host_rss_delta_mib": round(max(0.0, high_water - floor_mib), 1),
        "host_rss_after_mib": resident,
        "sec_per_step": round(elapsed / max(1, steps), 3),
        "loss": round(loss_value, 4),
    }


def _run_child(idx: int, args: argparse.Namespace) -> Dict[str, Any]:
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--only",
        str(idx),
        "--train",
        args.train,
        "--limit",
        str(args.limit),
        "--steps",
        str(args.steps),
        "--device",
        args.device,
    ]
    started = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    wall = time.time() - started
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith("{"):
            row = json.loads(line)
            row["wall_seconds"] = round(wall, 1)
            row["returncode"] = proc.returncode
            return row
    return {
        "config": dict(GRID[idx]),
        "error": (proc.stderr.strip().splitlines() or ["no output"])[-1][:200],
        "returncode": proc.returncode,
        "wall_seconds": round(wall, 1),
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--train", default=str(PROCESSED / "ai_al_round7_train.jsonl"))
    ap.add_argument("--limit", type=int, default=600, help="rows to encode (peak is per step)")
    ap.add_argument("--steps", type=int, default=3, help="timed steps per config")
    ap.add_argument(
        "--vram-budget",
        type=float,
        default=3.0,
        help="GiB the trainer may hold; the rest of the 9.9 GiB is the user's",
    )
    ap.add_argument(
        "--host-budget", type=float, default=1.6, help="GiB of host RSS for the trainer"
    )
    ap.add_argument("--device", default="auto")
    ap.add_argument("--report", default="")
    ap.add_argument(
        "--host-total-gib", type=float, default=7.0, help="physical RAM, for the headroom line"
    )
    ap.add_argument("--only", type=int, default=-1, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    if args.only >= 0:
        cfg = GRID[args.only]
        pairs = _pairs(Path(args.train), args.limit)
        try:
            print(json.dumps(_measure(cfg, pairs, args.device, max(1, args.steps))))
        except RuntimeError as exc:  # OOM is a result, not a crash
            print(json.dumps({"config": dict(cfg), "error": str(exc)[:200]}))
        return 0

    vram_budget = args.vram_budget * 1024.0
    host_budget = args.host_budget * 1024.0
    print(
        f"grid={len(GRID)} rows≈{args.limit} budget: device {args.vram_budget:.1f} GiB, host {args.host_budget:.1f} GiB"
    )
    header = (
        f"{'d_emb':>6} {'d_hid':>6} {'L':>2} {'bs':>3} {'len':>4} "
        f"{'params':>9} {'devMiB':>7} {'hostMiB':>8} {'s/step':>7} {'wall':>6}  verdict"
    )
    print(header)
    print("-" * len(header))

    rows: List[Dict[str, Any]] = []
    for idx, cfg in enumerate(GRID):
        row = _run_child(idx, args)
        if "peak_device_mib" not in row:
            print(
                f"{cfg['d_emb']:>6} {cfg['d_hidden']:>6} {cfg['layers']:>2} "
                f"{cfg['batch']:>3} {cfg['max_len']:>4}   error: {row.get('error', '?')[:70]}"
            )
            row["fits"] = False
            rows.append(row)
            continue
        row["fits_device"] = row["peak_device_mib"] <= vram_budget
        row["fits_host"] = row["host_rss_peak_mib"] <= host_budget * 1024.0
        row["fits"] = row["fits_device"] and row["fits_host"]
        verdict = "fit" if row["fits"] else ("host!" if row["fits_device"] else "vram!")
        print(
            f"{cfg['d_emb']:>6} {cfg['d_hidden']:>6} {cfg['layers']:>2} "
            f"{cfg['batch']:>3} {cfg['max_len']:>4} {row['params'] / 1e6:>8.2f}M "
            f"{row['peak_device_mib']:>7.0f} {row['host_rss_delta_mib']:>8.0f} "
            f"{row['sec_per_step']:>7.3f} {row['wall_seconds']:>6.0f}  {verdict}"
        )
        rows.append(row)

    fit_rows = [r for r in rows if r.get("fits")]
    base = next((r for r in rows if r.get("config") == GRID[0] and "params" in r), None)
    summary: Dict[str, Any] = {
        "budget_gib": {"device": args.vram_budget, "host": args.host_budget},
        "device_total_mib": next(
            (r.get("device_total_mib") for r in rows if r.get("device_total_mib")), None
        ),
        "baseline_round9": base,
        "configs": rows,
        "largest_fit": (fit_rows[-1]["config"] if fit_rows else None),
        "largest_fit_params": (fit_rows[-1]["params"] if fit_rows else None),
    }
    if fit_rows and base and base.get("sec_per_step"):
        summary["params_scale_vs_round9"] = round(
            fit_rows[-1]["params"] / max(1, base["params"]), 2
        )
        summary["step_cost_scale_vs_round9"] = round(
            fit_rows[-1]["sec_per_step"] / max(1e-9, base["sec_per_step"]), 2
        )
        summary["round9_epoch_cost_s"] = base["sec_per_step"] * 2633 / 32
    if fit_rows:
        print(
            f"\nlargest fit: {summary['largest_fit']} → "
            f"{summary['largest_fit_params'] / 1e6:.2f}M params "
            f"({summary.get('params_scale_vs_round9')}x round-9 params, "
            f"{summary.get('step_cost_scale_vs_round9')}x step cost)"
        )
    else:
        print("\nno fit: even the round-9 shape is over budget")
    if rows and rows[0].get("host_runtime_floor_mib"):
        floor = rows[0]["host_runtime_floor_mib"]
        worst = max((r.get("host_rss_peak_mib", 0.0) for r in rows), default=0.0)
        headroom = args.host_total_gib * 1024.0 - worst
        summary["host_floor_mib"] = floor
        summary["host_peak_worst_mib"] = worst
        summary["host_headroom_mib"] = round(headroom, 1)
        print(
            f"host: runtime floor {floor:.0f} MiB, worst config peak {worst:.0f} MiB, "
            f"headroom {headroom:.0f} MiB of {args.host_total_gib:.1f} GiB"
        )
        # Host cost is a *fixed* per-process charge: compare the cheapest and
        # dearest configs. If they are within a few hundred MiB of each other,
        # capacity is not what the host budget constrains — concurrency is.
        peaks = [r["host_rss_peak_mib"] for r in rows if r.get("host_rss_peak_mib")]
        if peaks:
            spread = max(peaks) - min(peaks)
            summary["host_peak_spread_mib"] = round(spread, 1)
            print(
                f"  host peak spread across the whole grid: {spread:.0f} MiB "
                f"({'fixed per-process cost — capacity is not host-bound' if spread < 400 else 'grows with config'})"
            )
        if headroom < 700:
            print("  → a second training job does not fit; runs must stay serial")
    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    raise SystemExit(main())
