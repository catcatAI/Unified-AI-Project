#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Structural cycle simulation runner for the edge card.

Drives ai.hardware.edge_card_sim.Engine hop by hop over the REAL gemma-4-E2B
QAT Q4_0 GGUF (tensor table straight from the file), through staged
checkpoints - 16, 100, 1000, 10000 hops - then to full decode tokens in
steady state. The run is valid only if, at every checkpoint:

  * every hop passed every invariant (ceilings, SRAM bounds, dependency
    ordering, progress / no livelock),
  * a replaying engine stepped to the same hop count produces the same
    digest (bit-identical determinism),
and at token boundaries:

  * the workload totals were consumed EXACTLY (bytes / MACs / pcie), and
    the model output token was emitted over PCIe.

It also prints the CardConfig frequency/bit-width table, dual-resource
utilization (memory vs MAC array vs PCIe), and compares the measured
decode rate against hardware/edge_card/edge_card_spec.yaml's
performance_budget.decode_tok_s targets - honestly: a compute-bound
result refutes a bandwidth-derived target and is reported as such, never
rounded up.

Usage:
  .venv/bin/python scripts/sim_edge_card_cycle.py [--json out.json]
  exit code 0 = all hard gates passed; 1 = violation/mismatch; 2 = setup error
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="edge card structural cycle simulation")
    p.add_argument("--gguf", type=Path, default=GGUF_DEFAULT, help="GGUF model file")
    p.add_argument("--spec", type=Path, default=SPEC_PATH, help="edge card spec YAML")
    p.add_argument("--checkpoints", default="16,100,1000,10000", help="hop checkpoints")
    p.add_argument("--tokens", type=int, default=5, help="decode tokens after checkpoints")
    p.add_argument("--trace", type=int, default=64, help="record the first N hops")
    p.add_argument("--json", type=Path, default=None, help="write machine-readable result")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.gguf.is_file():
        print(f"ERROR: GGUF not found: {args.gguf}", file=sys.stderr)
        return 2
    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    raw_ctx = str(spec["model_target"]["primary"]["context_card_default"]).strip()
    ctx = int(raw_ctx[:-1]) * 1024 if raw_ctx.upper().endswith("K") else int(raw_ctx)
    target_tok_s = float(spec["performance_budget"]["decode_tok_s"]["target_e2b_q4_0_min"])
    derived = spec["performance_budget"]["decode_tok_s"]["derived_e2b_q4_0_range"]
    checkpoints = [int(x) for x in args.checkpoints.split(",") if x.strip()]
    max_cp = max(checkpoints)

    print("=" * 78)
    print("edge card structural cycle simulation")
    print("=" * 78)
    t0 = time.time()
    structure = read_gguf_structure(args.gguf)
    kv = structure["kv"]
    print(
        f"gguf       : {args.gguf.name} ({structure['file_size']:,} B, "
        f"{len(structure['tensors'])} tensors, read {time.time() - t0:.2f}s)"
    )
    print(
        f"model      : {kv.get('general.architecture')} "
        f"{kv.get('gemma4.block_count')}L ctx_default={ctx}"
    )

    cfg = CardConfig()
    print("\nCardConfig (bit widths / clocks):")
    for name, width, rate in cfg.frequency_table():
        print(f"  {name:14s} {width:34s} {rate}")

    token0 = workload_totals(build_decode_workload(structure, cfg, ctx, 0, 0))
    print(
        f"\ntoken 0 @ctx={ctx}: items={token0['items']} "
        f"reads={token0['reads'] / 1e9:.3f} GB writes={token0['writes']} B "
        f"macs={token0['ops'] / 1e9:.3f} G pcie={token0['pcie']} B"
    )

    eng = Engine(structure, cfg, ctx_start=ctx, trace_first=args.trace)
    ref = Engine(structure, cfg, ctx_start=ctx)  # replay/determinism twin
    mix: Counter[str] = Counter()
    failures: list[str] = []
    report: dict = {"checkpoints": [], "gguf": str(args.gguf), "ctx": ctx}

    # ---- staged hop checkpoints with replay comparison ----
    reached = 0
    for cp in checkpoints:
        while eng.hops < cp:
            mix[eng.step()] += 1
        ref.run_hops(cp - reached)
        reached = cp
        d_eng, d_ref = eng.digest(), ref.digest()
        ok = d_eng == d_ref and not eng.violations
        if d_eng != d_ref:
            failures.append(f"checkpoint {cp}: digest mismatch {d_eng} != {d_ref}")
        if eng.violations:
            failures.append(f"checkpoint {cp}: {len(eng.violations)} violations")
        cp_rec = {
            "hops": eng.hops,
            "t_ns": round(eng.t, 3),
            "tokens": eng.tokens_done,
            "digest": d_eng,
            "replay_equal": d_eng == d_ref,
            "violations": len(eng.violations),
            "sram": int(eng.sram),
            "mem_idx": eng.mem_idx,
            "comp_idx": eng.comp_idx,
        }
        report["checkpoints"].append(cp_rec)
        print(
            f"\n[checkpoint {cp:>6} hops] t={eng.t:.3f} ns tokens={eng.tokens_done} "
            f"sram={int(eng.sram):,} mem={eng.mem_idx} comp={eng.comp_idx}"
        )
        print(
            f"  digest={d_eng} replay_equal={d_eng == d_ref} " f"violations={len(eng.violations)}"
        )
        for h in eng.trace[: min(cp, args.trace)] if cp <= 64 else eng.trace[:16]:
            print(f"    hop {h.hop:>4}: t={h.t_ns:>12.4f} {h.event}")

    # ---- continue through full decode tokens to steady state ----
    guard = 0
    while eng.tokens_done < args.tokens:
        mix[eng.step()] += 1
        guard += 1
        if guard > 10_000_000:
            failures.append("runaway: 10M hops without token completion")
            break
    ref.run_hops(eng.hops - reached)

    # ---- hard gates ----
    if eng.violations:
        failures.append(
            f"{len(eng.violations)} invariant violations " f"(first: {eng.violations[0]})"
        )
    if eng.digest() != ref.digest():
        failures.append(f"final digest mismatch: {eng.digest()} != {ref.digest()}")

    expected = {"mem_r": 0.0, "mem_w": 0.0, "macs": 0.0, "pcie": 0.0}
    for tk in range(eng.tokens_done):
        tt = workload_totals(
            build_decode_workload(structure, cfg, ctx + tk, tk, tk * token0["items"])
        )
        expected["mem_r"] += tt["reads"]
        expected["mem_w"] += tt["writes"]
        expected["macs"] += tt["ops"]
        expected["pcie"] += tt["pcie"]
    for k, exp in expected.items():
        got = eng.done_cum[k]
        if got != exp:  # integer retire counters: exact by construction
            failures.append(f"workload exactness {k}: consumed {got} != expected {exp}")

    # ---- results ----
    span = max(eng.t, 1e-9)
    util = {
        "mem_service": (eng.cum["mem_r"] + eng.cum["mem_w"])
        / (cfg.mem_service_bytes_per_ns * span),
        "mac_array": eng.cum["macs"] / (cfg.mac_per_ns * span),
        "pcie": eng.cum["pcie"] / (cfg.pcie_bytes_per_ns * span),
    }
    bottleneck = max(util, key=util.get)
    per_token = eng.per_token_ms
    tok_s = [1e3 / ms for ms in per_token]
    steady = tok_s[len(tok_s) // 2 :] or tok_s
    mean_tok_s = sum(steady) / len(steady)

    print(
        f"\n[final] hops={eng.hops} tokens={eng.tokens_done} t={eng.t / 1e6:.3f} ms "
        f"digest={eng.digest()}"
    )
    print(f"  event mix: {dict(mix.most_common(8))}")
    print(
        "  dual-resource utilization: "
        + ", ".join(f"{k}={v:.3f}" for k, v in util.items())
        + f"  -> bottleneck={bottleneck}"
    )
    print(
        "  per-token: " + ", ".join(f"{ms:.2f}ms({ts:.1f}t/s)" for ms, ts in zip(per_token, tok_s))
    )
    print(
        f"  steady-state decode: {mean_tok_s:.2f} tok/s "
        f"(mac_convention={cfg.mac_convention} -> {cfg.mac_per_ns:.0f} MAC/ns)"
    )
    print("  exactness: done_cum=" + ", ".join(f"{k}={v:.0f}" for k, v in eng.done_cum.items()))

    # ---- spec comparison (honest: never rounded up) ----
    gate = spec.get("cycle_simulation", {}).get("gate", {})
    gate_min = float(gate["min_tok_s"]) if "min_tok_s" in gate else None
    meets_target = mean_tok_s >= target_tok_s
    print("\nspec comparison:")
    print(
        f"  performance_budget.decode_tok_s.target_e2b_q4_0_min = {target_tok_s} tok/s "
        f"-> {'MET' if meets_target else 'NOT MET'} at {mean_tok_s:.2f} tok/s"
    )
    print(
        f"  bandwidth-derived range {derived} tok/s (assumes free compute) -> "
        f"simulation bottleneck is {bottleneck} "
        f"({'compute-bound: bandwidth range does not apply' if bottleneck == 'mac_array' else 'bandwidth-bound'})"
    )

    # what the silicon would need for the target (used by spec cycle_simulation)
    attn_ops = sum(
        i.ops
        for i in build_decode_workload(structure, cfg, ctx, 0, 0)
        if i.name.startswith("kv_rd")
    )
    weight_ops = token0["ops"] - attn_ops
    print(
        f"  ops/token @ctx={ctx}: total={token0['ops'] / 1e9:.3f} G "
        f"(weights={weight_ops / 1e9:.3f} G + attention={attn_ops / 1e9:.3f} G)"
    )
    print(
        f"  {target_tok_s:.0f} tok/s needs >= {token0['ops'] * target_tok_s / 1e9:.1f} GMAC/s "
        f"at ctx={ctx}; weights-only floor (ctx->0) = "
        f"{weight_ops * target_tok_s / 1e9:.1f} GMAC/s "
        f"(= {2 * weight_ops * target_tok_s / 1e9:.0f} dense TOPS @2ops/MAC)"
    )

    # retired 1-op reading (fact-refuted: TOPS count 2 ops/MAC per NVIDIA's
    # own INT8:FP16 ratio) - kept only so the gap between readings is visible
    from dataclasses import replace

    cfg1 = replace(cfg, mac_convention=1)
    eng1 = Engine(structure, cfg1, ctx_start=ctx)
    eng1.run_until_tokens(min(args.tokens, 3))
    sens_tok_s = 1e3 / (sum(eng1.per_token_ms) / len(eng1.per_token_ms))
    print(
        f"  sensitivity mac_convention=1 ({cfg1.mac_per_ns:.0f} MAC/ns): "
        f"{sens_tok_s:.2f} tok/s "
        f"-> {'MET' if sens_tok_s >= target_tok_s else 'NOT MET'} vs {target_tok_s:.0f}, "
        f"violations={len(eng1.violations)}"
    )
    report["sensitivity_mac_conv1_tok_s"] = round(sens_tok_s, 3)
    report["needed_gmac_s_for_target"] = round(token0["ops"] * target_tok_s / 1e9, 2)
    report["weights_floor_gmac_s_for_target"] = round(weight_ops * target_tok_s / 1e9, 2)

    if gate_min is not None:
        if mean_tok_s < gate_min:
            failures.append(f"cycle_simulation gate: {mean_tok_s:.2f} < min_tok_s {gate_min}")
        print(
            f"  cycle_simulation.gate.min_tok_s = {gate_min} -> "
            f"{'OK' if mean_tok_s >= gate_min else 'FAIL'}"
        )

    report.update(
        {
            "tokens": eng.tokens_done,
            "hops": eng.hops,
            "t_end_ns": eng.t,
            "per_token_ms": [round(x, 4) for x in per_token],
            "steady_tok_s": round(mean_tok_s, 3),
            "utilization": {k: round(v, 4) for k, v in util.items()},
            "bottleneck": bottleneck,
            "target_tok_s": target_tok_s,
            "target_met": meets_target,
            "done_cum": {k: round(v, 3) for k, v in eng.done_cum.items()},
            "event_mix": dict(mix),
            "violations": eng.violations[:20],
            "failures": failures,
            "ok": not failures,
            "wall_s": round(time.time() - t0, 2),
        }
    )
    if args.json:
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\njson report: {args.json}")

    if failures:
        print(f"\nVERDICT: FAIL ({len(failures)})")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(
        f"\nVERDICT: PASS - {eng.hops} hops, {eng.tokens_done} tokens, "
        f"0 violations, replay identical, workload exact ({time.time() - t0:.1f}s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
