#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Balance sweep for the edge card: compute x context x memory x PCIe.

The card is a Jetson Orin NX module carrier: compute (GPU Tensor Core dense
INT8 TOPS - the decode-usable share, DLA excluded), LPDDR5 bandwidth and
capacity live inside the purchased module, so the real balance knobs are
module SKU, nvpmodel power mode, and the context length. This script sweeps
those knobs through
the SAME structural engine as sim_edge_card_cycle.py and answers, with
numbers:

  * which (mode, ctx) combinations reach the spec decode target (15 tok/s),
    including the 15W low-power profile (derived from the spec's own ~30%
    derate note) and the 16GB SKU's reserved 128K context capability,
  * how much LPDDR5 utilization each point produces, and the arithmetic
    intensity point where memory WOULD bind (~222 ops/ns at 32K - far above
    any Orin NX mode, which is why memory sits idle by physics, not by
    misconfiguration),
  * what PCIe Gen4 x1 / the M.2 NVMe are actually for: every cold-load path
    (host payload, host achievable DMA, on-card NVMe, hypothetical faster
    device) against the 5 s budget - decode carries only 8 B/token, so
    decode utilization is a category error, not a design miss.

A cross-check pins the baseline point (nx16_25w_c2 @32K) to the cycle
runner's measured tok/s (spec cycle_simulation.measured), so this tool
cannot silently drift.

Usage:
  .venv/bin/python scripts/sim_edge_card_sweep.py [--json out.json]
  exit 0 = sweep ran + baseline cross-check held; 2 = setup error; 1 = drift
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SPEC_PATH = REPO / "hardware/edge_card/edge_card_spec.yaml"
sys.path.insert(0, str(REPO / "apps/backend/src"))

from ai.hardware.edge_card_sim import (  # noqa: E402
    CardConfig,
    Engine,
    build_decode_workload,
    read_gguf_structure,
    run_prefload,
    workload_totals,
)

GGUF_DEFAULT = (
    Path.home()
    / ".cache/huggingface/hub/models--google--gemma-4-E2B-it-qat-q4_0-gguf"
    / "snapshots/675cff42a74c774d6cb76f76d8eacb49b48c9b93"
    / "gemma-4-E2B_q4_0-it.gguf"
)

# decode-usable GPU Tensor Core dense INT8 TOPS, MAC=2 confirmed
# (module totals minus DLA - DLA is CNN-only and cannot decode; the old
# c1/1-op reading rows are retired: NVIDIA's INT8 dense is exactly 2x its
# FP16 dense on the same cores). nx16: GPU 30 dense @918MHz (25W),
# 38 @1173MHz (MAXN SUPER); nx8: same GPU at 765MHz default = 25 dense;
# 15W profile = 25W x 0.7 derived from power_and_thermal.low_power_profile's
# own "~30% derate" note - label says derived. ctxs: the 8GB SKU stops at
# 32K (128K capability is reserved to the 16GB SKU per model_target).
REAL_MODES: dict[str, dict] = {
    "nx8_25w_c2": {
        "tops": 25.0,
        "conv": 2,
        "ctxs": (8192, 16384, 32768),
        "label": "Orin-NX-8GB GPU dense25@25W (765MHz), 2ops/MAC",
    },
    "nx16_25w_c2": {
        "tops": 30.0,
        "conv": 2,
        "ctxs": (8192, 16384, 32768, 131072),
        "label": "Orin-NX-16GB GPU dense30@25W (module50-DLA20), 2ops/MAC (spec baseline)",
    },
    "nx16_15w_c2": {
        "tops": 21.0,
        "conv": 2,
        "ctxs": (8192, 16384, 32768, 131072),
        "label": "Orin-NX-16GB 15W profile (derived 21 GPU dense), 2ops/MAC",
    },
    "nx16_40w_c2": {
        "tops": 38.0,
        "conv": 2,
        "ctxs": (8192, 16384, 32768, 131072),
        "label": "Orin-NX-16GB GPU dense38@MAXN-SUPER (1173MHz), 2ops/MAC",
    },
}


def make_cfg(tops: float, conv: int) -> CardConfig:
    return dataclasses.replace(CardConfig(), int8_dense_tops=float(tops), mac_convention=conv)


def run_point(
    structure: dict, cfg: CardConfig, ctx: int, tokens: int
) -> dict[str, float | int | list]:
    """Run tokens decode steps and report the steady (last) token + utilization."""
    eng = Engine(structure, cfg, ctx_start=ctx, trace_first=0)
    eng.run_until_tokens(tokens)
    span = max(eng.t, 1e-9)
    last_ms = eng.per_token_ms[-1]
    return {
        "ctx": ctx,
        "tokens": eng.tokens_done,
        "hops": eng.hops,
        "tok_s": 1000.0 / last_ms,
        "mac_util": eng.cum["macs"] / (cfg.mac_per_ns * span),
        "mem_util": (eng.cum["mem_r"] + eng.cum["mem_w"]) / (cfg.mem_service_bytes_per_ns * span),
        "pcie_util": eng.cum["pcie"] / (cfg.pcie_bytes_per_ns * span),
        "violations": list(eng.violations),
    }


def memory_bind_point(structure: dict, cfg: CardConfig, ctx: int) -> dict[str, float]:
    """ops/ns at which the memory roofline would bind for this workload."""
    tt = workload_totals(build_decode_workload(structure, cfg, ctx, 0, 0))
    ops_per_byte = tt["ops"] / tt["reads"]
    bind = cfg.mem_service_bytes_per_ns * ops_per_byte
    return {
        "ops_ns": bind,
        "ops_per_byte": ops_per_byte,
        "mem_service_B_ns": cfg.mem_service_bytes_per_ns,
        "tok_s_at_bind": bind * 1e9 / tt["ops"],
    }


def pcie_analytics(structure: dict) -> dict[str, float | bool]:
    """Load path (where PCIe is genuinely used) + decode floor (where it is not)."""
    file_b = structure["file_size"]
    payload = CardConfig().pcie_bytes_per_ns  # 1.969231 B/ns Gen4 x1 payload
    achievable = 1.6  # spec host_interface.achievable_dma_gbs_each_direction_min
    budget_s = 5.0  # performance_budget.host_link.cold_load_e2b_q4_0_from_host_s_max
    load_s = file_b / payload / 1e9  # B / (B/ns) -> ns -> s
    load_ach_s = file_b / achievable / 1e9  # 1.6 GB/s == 1.6 B/ns numerically
    decode_bps = 8 * 15  # 8 B/token at the 15 tok/s target
    return {
        "file_bytes": file_b,
        "load_s_at_payload": load_s,
        "load_s_at_achievable_dma": load_ach_s,
        "load_budget_s": budget_s,
        "load_pass": max(load_s, load_ach_s) <= budget_s,
        "load_util_at_payload": 1.0,
        "decode_bytes_per_s_at_15": decode_bps,
        "decode_util_at_15": decode_bps / (payload * 1e9),
    }


def load_paths(structure: dict, cfg: CardConfig) -> dict[str, float | bool]:
    """Every cold-load path the component review asks about, vs the 5s budget.

    host payload  = Gen4 x1 theoretical payload rate (1.969 B/ns)
    host achievable = spec floor 1.6 GB/s (>=85% TLP efficiency)
    nvme spec     = engine run_prefload: M.2 device rate min(1.6, LPDDR5 write)
    nvme hypothetical = faster device class at 2.4 GB/s, still bounded by
    the module's own memory write - shows the ceiling storage upgrades can
    ever reach (LPDDR5 write at 87 B/ns never binds, so the device rate IS
    the limit until it exceeds ~87).
    """
    file_b = structure["file_size"]
    budget_s = 5.0
    host_payload_s = file_b / cfg.pcie_bytes_per_ns / 1e9
    host_ach_s = file_b / 1.6 / 1e9
    nvme_s = run_prefload(structure, cfg, file_b) / 1e9
    nvme_fast_s = file_b / min(2.4, cfg.mem_service_bytes_per_ns) / 1e9
    worst = max(host_payload_s, host_ach_s, nvme_s, nvme_fast_s)
    return {
        "file_bytes": file_b,
        "host_pcie_payload_s": host_payload_s,
        "host_pcie_achievable_s": host_ach_s,
        "nvme_spec_1_6_s": nvme_s,
        "nvme_hypothetical_2_4_s": nvme_fast_s,
        "budget_s": budget_s,
        "worst_case_s": worst,
        "margin_s": budget_s - worst,
        "all_pass": worst <= budget_s,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="edge card balance sweep")
    p.add_argument("--gguf", type=Path, default=GGUF_DEFAULT, help="GGUF model file")
    p.add_argument("--spec", type=Path, default=SPEC_PATH, help="edge card spec YAML")
    p.add_argument("--tokens", type=int, default=2, help="decode tokens per point")
    p.add_argument("--json", type=Path, default=None, help="write machine-readable result")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.gguf.is_file():
        print(f"ERROR: GGUF not found: {args.gguf}", file=sys.stderr)
        return 2
    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    baseline = float(
        spec["cycle_simulation"]["measured"]["decode_tok_s"]
        if "cycle_simulation" in spec
        else spec["performance_budget"]["decode_tok_s"]["derived_e2b_q4_0_range"][0]
    )
    target = float(spec["performance_budget"]["decode_tok_s"]["target_e2b_q4_0_min"])

    print("=" * 78)
    print("edge card balance sweep (module SKU x TOPS reading x context)")
    print("=" * 78)
    t0 = time.time()
    structure = read_gguf_structure(args.gguf)
    base_cfg = CardConfig()
    bind = memory_bind_point(structure, base_cfg, 32768)
    pcie = pcie_analytics(structure)
    loads = load_paths(structure, base_cfg)
    print(f"gguf: {structure['file_size']:,} B, {len(structure['tensors'])} tensors")
    print(
        f"memory bind point @32K: {bind['ops_ns']:.1f} ops/ns "
        f"({bind['ops_per_byte']:.3f} ops/B x {bind['mem_service_B_ns']:.2f} B/ns) "
        f"-> ~{bind['tok_s_at_bind']:.0f} tok/s class module would saturate LPDDR5"
    )
    print(
        f"pcie load: {pcie['load_s_at_payload']:.2f}s payload / "
        f"{pcie['load_s_at_achievable_dma']:.2f}s @achievable 1.6 GB/s "
        f"vs budget {pcie['load_budget_s']:.0f}s -> "
        f"{'PASS' if pcie['load_pass'] else 'FAIL'} (this is where x1 is utilized)"
    )
    print(
        "load paths (component review): "
        + ", ".join(
            f"{k}={loads[k]:.2f}s"
            for k in (
                "host_pcie_payload_s",
                "host_pcie_achievable_s",
                "nvme_spec_1_6_s",
                "nvme_hypothetical_2_4_s",
            )
        )
        + f" vs {loads['budget_s']:.0f}s budget -> "
        f"{'PASS' if loads['all_pass'] else 'FAIL'} "
        f"(worst {loads['worst_case_s']:.2f}s, margin {loads['margin_s']:.2f}s)"
    )

    points: list[dict] = []
    print(f"\n{'mode':14s} {'ctx':>6s} {'tok/s':>7s} {'mac':>6s} {'mem':>6s} {'pcie':>8s}  verdict")
    for mode, mode_spec in REAL_MODES.items():
        cfg = make_cfg(mode_spec["tops"], mode_spec["conv"])
        for ctx in mode_spec["ctxs"]:
            r = run_point(structure, cfg, ctx, args.tokens)
            r["mode"] = mode
            r["class"] = "real_module"
            r["mac_rate_ops_ns"] = cfg.mac_per_ns
            points.append(r)
            verdict = "MEETS" if r["tok_s"] >= target else "below"
            if r["violations"]:
                verdict = f"VIOLATION({len(r['violations'])})"
            print(
                f"{mode:14s} {ctx:>6d} {r['tok_s']:>7.2f} {r['mac_util']:>6.1%} "
                f"{r['mem_util']:>6.1%} {r['pcie_util']:>8.1e}  {verdict}"
            )
    # hypothetical module-class points: what WOULD utilize the LPDDR5
    # (100/150 = mid probes, bind = analytic memory bind point, 2xbind =
    # asymptote probe: tok/s approaches the pure-bandwidth roofline ~53)
    for hyp in (100.0, 150.0, round(bind["ops_ns"], 1), round(2 * bind["ops_ns"], 1)):
        cfg = make_cfg(hyp, 1)
        r = run_point(structure, cfg, 32768, args.tokens)
        r["mode"] = f"hw_{hyp:g}"
        r["class"] = "hypothetical_not_purchasable"
        r["mac_rate_ops_ns"] = cfg.mac_per_ns
        points.append(r)
        print(
            f"{r['mode']:14s} {32768:>6d} {r['tok_s']:>7.2f} {r['mac_util']:>6.1%} "
            f"{r['mem_util']:>6.1%} {r['pcie_util']:>8.1e}  (memory-use probe)"
        )

    # baseline cross-check: nx16_25w_c2 @32K must match the cycle runner
    base = next(p for p in points if p["mode"] == "nx16_25w_c2" and p["ctx"] == 32768)
    drift = abs(base["tok_s"] - baseline) / baseline
    cross_ok = drift <= 0.02
    print(
        f"\nbaseline cross-check: {base['tok_s']:.2f} vs cycle-runner {baseline:.2f} "
        f"-> {'OK' if cross_ok else 'DRIFT ' + f'{drift:.1%}'}"
    )
    meets = sorted(
        {p["mode"] for p in points if p["class"] == "real_module" and p["tok_s"] >= target}
    )
    meets_32k = sorted(
        {
            p["mode"]
            for p in points
            if p["class"] == "real_module" and p["ctx"] == 32768 and p["tok_s"] >= target
        }
    )
    print(f"modes reaching {target:g} tok/s at 32K: {meets_32k or 'NONE'}")
    print(f"modes reaching {target:g} tok/s anywhere in sweep: {meets or 'NONE'}")

    report = {
        "target_tok_s": target,
        "points": points,
        "memory_bind_point_32k": bind,
        "pcie": pcie,
        "load_paths": loads,
        "meets_target_modes_any_ctx": meets,
        "meets_target_modes_32k": meets_32k,
        "baseline_cross_check": {
            "measured": base["tok_s"],
            "expected": baseline,
            "ok": cross_ok,
        },
        "elapsed_s": time.time() - t0,
    }
    if args.json:
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"json report: {args.json}")
    print(f"VERDICT: {'PASS' if cross_ok else 'FAIL - baseline drift'} ({time.time() - t0:.1f}s)")
    return 0 if cross_ok else 1


if __name__ == "__main__":
    sys.exit(main())
