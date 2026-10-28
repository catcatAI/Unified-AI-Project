#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""P5-4: latency of the three local role backends, sequentially and in parallel.

`/chat/group` runs roles one after another, so the user-visible cost is the sum
of the three. This script measures that, plus what concurrency would buy — the
number that decides whether a group turn needs parallel execution.

Usage:
    python scripts/bench_local_roles.py
    python scripts/bench_local_roles.py --parallel --runs 3
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

# Keep in sync with apps/backend/configs/system/roles.default.yaml + plan ports.
SLOTS = [
    {"slot": "llamacpp-local", "role": "main", "port": 8080},
    {"slot": "llamacpp-gemma", "role": "role_b", "port": 8082},
    {"slot": "llamacpp-qwen", "role": "role_c", "port": 8081},
]

PROMPT = "用一句話說明你現在扮演的角色。"
MAX_TOKENS = 40


def call(port: int, prompt: str = PROMPT, timeout: float = 120.0) -> Dict[str, object]:
    body = json.dumps(
        {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": MAX_TOKENS,
            "temperature": 0.2,
        }
    ).encode()
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    elapsed = time.perf_counter() - started
    usage = payload.get("usage") or {}
    tokens = int(usage.get("completion_tokens") or 0)
    return {
        "port": port,
        "seconds": elapsed,
        "tokens": tokens,
        "tokens_per_s": (tokens / elapsed) if elapsed > 0 and tokens else 0.0,
    }


def healthy(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
            return r.status == 200
    except (urllib.error.URLError, OSError):
        return False


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--parallel", action="store_true", help="also measure concurrent calls")
    args = parser.parse_args(argv)

    up = [slot for slot in SLOTS if healthy(slot["port"])]
    if len(up) < 3:
        print("not all three backends are up; start them with:")
        print("  python scripts/run_local_three_models.py start")
        print(f"healthy: {[s['slot'] for s in up]}")
        return 2

    sequential: List[float] = []
    print(f"{'role':8} {'slot':16} {'port':5} {'sec':>6} {'tok':>4} {'tok/s':>6}")
    rows = []
    for _ in range(max(1, args.runs)):
        round_rows = []
        for slot in up:
            result = call(int(slot["port"]))
            round_rows.append(result)
            rows.append(result)
            print(
                f"{slot['role']:8} {slot['slot']:16} {slot['port']:5} "
                f"{result['seconds']:6.2f} {result['tokens']:4d} {result['tokens_per_s']:6.1f}"
            )
        sequential.append(sum(r["seconds"] for r in round_rows))
        print(f"  → group turn (sequential): {sequential[-1]:.2f}s")

    print(
        f"\nsequential total: mean {statistics.mean(sequential):.2f}s over {len(sequential)} runs"
    )

    if args.parallel:
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=len(up)) as pool:
            futures = [pool.submit(call, int(slot["port"])) for slot in up]
            [f.result() for f in futures]
        wall = time.perf_counter() - started
        print(
            f"parallel wall clock: {wall:.2f}s (vs {statistics.mean(sequential):.2f}s sequential)"
        )
        print(f"speed-up: {statistics.mean(sequential) / wall:.1f}x")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
