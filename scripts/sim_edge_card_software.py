#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Host-proxy software simulation for the edge card budget.

Loads the card's target model (google gemma-4-E2B QAT Q4_0 GGUF from the
local Hugging Face cache) with llama.cpp on THIS machine's CPU and re-derives
every headline budget in hardware/edge_card/edge_card_spec.yaml with real
measured numbers:

  envelope  measured GGUF size + KV + OS vs the 8/16 GB module floors
  decode    measured host tok/s, projected to the Orin NX via the
            file-streaming bound 102.4 GB/s * eta / file_bytes
            (eta = weight-streaming efficiency, the L1 unknown)
  prefill   measured host pp tok/s + the Orin INT8 analytic bound
  load      measured file size over the spec's Gen4 x1 payload math

Honesty: this is an x86 CPU proxy run, NOT L1. L1 (the numbers the spec
commits to) still requires an Orin NX devkit. The script exits non-zero if
any hard invariant (envelope fit, decode bound vs target, load vs target)
fails, so it can double as a regression gate.

Usage:  .venv/bin/python scripts/sim_edge_card_software.py [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import yaml
from llama_cpp import Llama

REPO = Path(__file__).resolve().parents[1]
SPEC_PATH = REPO / "hardware/edge_card/edge_card_spec.yaml"
HF_HUB = Path.home() / ".cache/huggingface/hub"

PROMPT = ("Write a short story about a robot learning to paint. " * 14).strip()
MEASURE_TOKENS = 192


def find_gguf() -> Path:
    """Locate the gemma-4 E2B Q4_0 GGUF in the local HF cache (real-name snapshot, not blobs)."""
    candidates = [
        p
        for p in HF_HUB.glob("models--google--gemma-4*E2B*/snapshots/*/*.gguf")
        if "q4" in p.name.lower()
    ]
    if not candidates:
        raise FileNotFoundError(f"no gemma-4 E2B q4_0 gguf under {HF_HUB}")
    return candidates[0]


def stream_bandwidth_gbs(threads: int = 6, per_thread_mb: int = 256, iters: int = 16) -> float:
    """Multi-threaded read bandwidth: each thread streams its own src->dst copies (GIL released)."""
    n = per_thread_mb * 1024 * 1024 // 8
    srcs = [np.ones(n, dtype=np.float64) for _ in range(threads)]
    dsts = [np.empty_like(a) for a in srcs]

    def work(i: int) -> float:
        for _ in range(iters):
            np.copyto(dsts[i], srcs[i])
        return float(dsts[i][0])

    with ThreadPoolExecutor(max_workers=threads) as pool:
        t0 = time.perf_counter()
        list(pool.map(work, range(threads)))
        dt = time.perf_counter() - t0
    read_bytes = threads * iters * srcs[0].nbytes
    return read_bytes / dt / 1e9


def measure_llama(gguf: Path, n_threads: int, samples: int) -> dict:
    """Per-token wall timestamps from the streaming API isolate prefill from decode.

    prefill = time of the first token; decode = median of interior inter-token
    deltas (drops the first delta, which carries setup, and the last, which can
    carry end-of-generation buffering). Repeated `samples` times, medians over.
    """
    llm = Llama(model_path=str(gguf), n_ctx=512, n_threads=n_threads, verbose=False)
    for _ in range(2):  # warmup: fault in weight pages, settle allocator
        list(llm(PROMPT, max_tokens=8, temperature=0.0, seed=42, stream=True))
    prefill_times, deltas, prompt_tokens = [], [], 0
    for _ in range(samples):
        t0 = time.perf_counter()
        times: list[float] = []
        for _chunk in llm(PROMPT, max_tokens=MEASURE_TOKENS, temperature=0.0, seed=42, stream=True):
            times.append(time.perf_counter() - t0)
        if len(times) < 8:
            raise RuntimeError(f"stream ended early ({len(times)} tokens)")
        usage = llm.tokenize(PROMPT.encode("utf-8"), add_bos=True)
        prompt_tokens = len(usage)
        prefill_times.append(times[0])
        run_deltas = [times[i + 1] - times[i] for i in range(len(times) - 1)]
        deltas.extend(run_deltas[1:-1])
    if not deltas or min(deltas) <= 0:
        raise RuntimeError("no positive decode deltas measured")
    median_delta = statistics.median(deltas)
    prefill_s = statistics.median(prefill_times)
    return {
        "n_threads": n_threads,
        "prompt_tokens": prompt_tokens,
        "prefill_s": round(prefill_s, 3),
        "prefill_tok_s": round(prompt_tokens / prefill_s, 1),
        "decode_tok_s": round(1.0 / median_delta, 2),
        "decode_tokens_sampled": len(deltas),
        "samples": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None, help="write machine-readable results")
    parser.add_argument("--threads", type=int, default=6, help="physical cores on the i5-12400F")
    parser.add_argument("--samples", type=int, default=2, help="differential timing repeats")
    args = parser.parse_args()

    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    gguf = find_gguf()
    file_bytes = gguf.stat().st_size
    file_gb = file_bytes / 1e9

    eta_min, eta_max = spec["performance_budget"]["decode_assumptions"]["stream_efficiency_range"]
    target_decode = spec["performance_budget"]["decode_tok_s"]["target_e2b_q4_0_min"]
    target_prefill = spec["performance_budget"]["prefill_tok_s"]["target_e2b_min"]
    target_load = spec["performance_budget"]["host_link"]["cold_load_e2b_q4_0_from_host_s_max"]
    payload_gbs = spec["host_interface"]["payload_gbs_each_direction"]
    kv_gb = spec["model_target"]["working_set_gb"]["kv_cache_budget_gb"]["value"]
    os_gb = spec["model_target"]["working_set_gb"]["os_reserve_gb"]
    module_gb = spec["memory"]["module_lpddr5_gb"]
    floor_gb = 8
    bandwidth = spec["performance_budget"]["decode_assumptions"]["memory_bandwidth_gbs"]

    # ---- measured host numbers -------------------------------------------------
    host_bw_gbs = stream_bandwidth_gbs(threads=args.threads)
    llama = measure_llama(gguf, n_threads=args.threads, samples=args.samples)

    # ---- projections to the card ----------------------------------------------
    envelope_gb = file_gb + kv_gb + os_gb
    decode_bound = [
        round(bandwidth * eta_min / file_gb, 1),
        round(bandwidth * eta_max / file_gb, 1),
    ]
    eta_needed = round(target_decode * file_gb / bandwidth, 3)
    ratio_projected = round(llama["decode_tok_s"] * bandwidth / host_bw_gbs, 1)
    load_from_host_s = round(file_gb / payload_gbs, 2)
    load_from_nvme_s = round(file_gb / 1.6, 2)
    prefill_ideal = round(2 * 2.3e9 * 1000 / (50e12 * 0.4), 3)  # s/1K tokens at 0.4 MFU
    prefill_ideal_tps = round(1000 / prefill_ideal)

    # ---- verdicts ---------------------------------------------------------------
    verdicts = [
        {
            "item": "envelope_measured_vs_floor",
            "value": round(envelope_gb, 2),
            "unit": "GB",
            "target": f"<= {floor_gb} GB floor SKU",
            "pass": envelope_gb <= floor_gb,
        },
        {
            "item": "envelope_measured_vs_baseline",
            "value": round(envelope_gb, 2),
            "unit": "GB",
            "target": f"<= {module_gb} GB baseline",
            "pass": envelope_gb <= module_gb,
        },
        {
            "item": "decode_file_stream_bound_low",
            "value": decode_bound[0],
            "unit": "tok/s",
            "target": f">= {target_decode} (at eta={eta_min})",
            "pass": decode_bound[0] >= target_decode,
        },
        {
            "item": "decode_host_ratio_projected",
            "value": ratio_projected,
            "unit": "tok/s",
            "target": f"reference for {target_decode} (cpu-bound caveat)",
            "pass": None,
        },
        {
            "item": "prefill_host_measured",
            "value": llama["prefill_tok_s"],
            "unit": "tok/s",
            "target": f"informational; Orin analytic ideal {prefill_ideal_tps} vs >= {target_prefill}",
            "pass": None,
        },
        {
            "item": "load_from_host_s",
            "value": load_from_host_s,
            "unit": "s",
            "target": f"<= {target_load} s",
            "pass": load_from_host_s <= target_load,
        },
        {
            "item": "load_from_oncard_nvme_s",
            "value": load_from_nvme_s,
            "unit": "s",
            "target": "informational (1.6 GB/s assumed bus)",
            "pass": None,
        },
    ]

    results = {
        "sim_kind": "host_proxy_not_l1",
        "gguf": str(gguf),
        "file_gb": round(file_gb, 3),
        "host_bandwidth_gbs": round(host_bw_gbs, 1),
        "llama": llama,
        "projections": {
            "decode_file_stream_bound": decode_bound,
            "eta_needed_for_target": eta_needed,
            "decode_host_ratio_projected": ratio_projected,
            "envelope_gb": round(envelope_gb, 2),
            "load_from_host_s": load_from_host_s,
            "prefill_ideal_s_per_1k": prefill_ideal,
        },
        "verdicts": verdicts,
    }

    print("=" * 72)
    print("EDGE CARD HOST-PROXY SIMULATION (NOT L1 - x86 CPU, not Orin NX)")
    print("=" * 72)
    print(f"model           : {gguf.name} ({file_gb:.3f} GB)")
    print(f"host bandwidth  : {host_bw_gbs:.1f} GB/s (mt-copy read, {args.threads} threads)")
    print(
        f"prefill         : {llama['prefill_tok_s']:.1f} tok/s "
        f"({llama['prompt_tokens']} tokens, {llama['prefill_s']:.2f} s, n_threads={llama['n_threads']})"
    )
    print(f"decode          : {llama['decode_tok_s']:.2f} tok/s (host CPU)")
    print(f"orin bound      : {decode_bound} tok/s (102.4 GB/s x eta[{eta_min},{eta_max}] / file)")
    print(f"eta needed      : {eta_needed}  (target {target_decode} tok/s on file streaming)")
    print(f"ratio projected : {ratio_projected} tok/s (host tok/s scaled by 102.4/host_bw)")
    print(f"envelope        : {file_gb:.2f} + {kv_gb} KV + {os_gb} OS = {envelope_gb:.2f} GB")
    print(f"load time       : {load_from_host_s} s over Gen4 x1 ({payload_gbs} GB/s)")
    print("-" * 72)
    hard_fail = False
    for v in verdicts:
        if v["pass"] is None:
            mark = "INFO"
        elif v["pass"]:
            mark = "PASS"
        else:
            mark = "FAIL"
            hard_fail = True
        print(f"[{mark}] {v['item']:<32} {v['value']} {v['unit']:<6} {v['target']}")
    print("=" * 72)

    if args.json:
        args.json.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"json -> {args.json}")
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
