#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Balance sweep for the edge card: compute x context x memory x PCIe.

The card is a Jetson Orin NX module carrier: compute (dense INT8 TOPS),
LPDDR5 bandwidth and capacity live inside the purchased module, so the real
balance knobs are module SKU, nvpmodel power mode, the TOPS counting
convention, and the context length. This script sweeps those knobs through
the SAME structural engine as sim_edge_card_cycle.py and answers, with
numbers:

  * which (mode, ctx) combinations reach the spec decode target (15 tok/s),
  * how much LPDDR5 utilization each point produces, and the arithmetic
    intensity point where memory WOULD bind (~222 ops/ns at 32K - far above
    any Orin NX mode, which is why memory sits idle by physics, not by
    misconfiguration),
  * what PCIe Gen4 x1 is actually for: the load path (fully utilized,
    1.7-2.1 s of a 5 s budget) - decode carries only 8 B/token, so decode
    utilization is a category error, not a design miss.

A cross-check pins the baseline point (nx16_25w_c2 @32K) to the cycle
runner's measured 5.93 tok/s, so this tool cannot silently drift.

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
    workload_totals,
)

GGUF_DEFAULT = (
    Path.home()
    / ".cache/huggingface/hub/models--google--gemma-4-E2B-it-qat-q4_0-gguf"
    / "snapshots/675cff42a74c774d6cb76f76d8eacb49b48c9b93"
    / "gemma-4-E2B_q4_0-it.gguf"
)

# module modes: dense INT8 TOPS straight from edge_card_spec.yaml
# (option_sku = 8GB/35, primary = 16GB/50 @25W, super = 16GB/78 @40W);
# c2 = conservative 2 ops/MAC reading, c1 = ops reading of the same number.
REAL_MODES: dict[str, tuple[float, int, str]] = {
    "nx8_25w_c2": (35.0, 2, "Orin-NX-8GB dense35@25W, 2ops/MAC"),
    "nx16_25w_c2": (50.0, 2, "Orin-NX-16GB dense50@25W, 2ops/MAC (spec baseline)"),
    "nx8_25w_c1": (35.0, 1, "Orin-NX-8GB dense35@25W, ops reading"),
    "nx16_25w_c1": (50.0, 1, "Orin-NX-16GB dense50@25W, ops reading"),
    "nx16_40w_c2": (78.0, 2, "Orin-NX-16GB MAXN-SUPER dense78@40W, 2ops/MAC"),
    "nx16_40w_c1": (78.0, 1, "Orin-NX-16GB MAXN-SUPER dense78@40W, ops reading"),
}
CTXS = (8192, 16384, 32768)


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

    points: list[dict] = []
    print(f"\n{'mode':14s} {'ctx':>6s} {'tok/s':>7s} {'mac':>6s} {'mem':>6s} {'pcie':>8s}  verdict")
    for mode, (tops, conv, _label) in REAL_MODES.items():
        cfg = make_cfg(tops, conv)
        for ctx in CTXS:
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
