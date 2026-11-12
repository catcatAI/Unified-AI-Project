#!/usr/bin/env python3
# ANGELA-MATRIX: L3 [βγδ] [A] [L2]
"""P5: drive the stateful core through real turns, in volume, and record them.

P4 measured three hand-run turns. Three turns prove the wiring; they cannot
show the carrier surviving a session. This probe replays the frozen standard set
through the *production* entry point (``_handle_chat_request`` — the same one
``trace_reply.py`` uses) with ``ANGELA_STATEFUL_CORE=1`` and writes one JSONL
record per turn.

What it measures — and what it does not:

- It measures that every turn was carried by the state object, that no turn was
  lost (``state_version`` strictly increases), and that refusals are zero.
- It does **not** measure capability. Nothing reads the state back into
  generation, so a clean run says nothing about the answers. The replies are
  produced by the same template/knowledge/routing layers as without the core,
  and that is recorded per turn (``state_source``) rather than assumed.
- The tokeniser is the ``hash-bucket`` placeholder, so the state's *content* has
  no linguistic meaning. Keeping the same shape as the P4 run (26 buckets,
  hidden 64, emb 32) is deliberate: the numbers stay comparable to §41.

The sandbox is shared with ``probe_native_dialogue`` (same lock, same data dir)
because two probes on one sandbox destroy each other's measurement.

Usage::

    ./.venv/bin/python scripts/probe_core_turns.py --turns 2000
    ./.venv/bin/python scripts/probe_core_turns.py --turns 40 --no-gate   # smoke

Exit code is 1 when the gate fails, so CI can hold the floor.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_SRC = REPO_ROOT / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

REPORT_DIR = REPO_ROOT / "data" / "core_turns"
DEFAULT_TURNS = 2000

# The floor per stratum. The standard set has five strata; only two of them are
# larger than 200 items, so the floor is "every item of the stratum, and at
# least 200 turns where the stratum can supply them". Raising this by repeating
# a small stratum would pad the count without adding a longer session, which is
# the thing this probe is for.
MIN_STRATUM_TURNS = 200

# The five kinds the standard set is built from. All five must be exercised:
# a run that only replayed the 492 questions would have a long session but would
# never touch a boundary item or a dialogue turn.
REQUIRED_STRATA = ("state", "multi", "claim", "qa", "dialogue")


def _load_script(name: str, filename: str) -> Any:
    """Import a sibling script (they are not a package)."""
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - broken install
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _build_checkpoint(directory: Path, *, arch: str = "ssm", token_count: int = 26) -> Path:
    """An untrained checkpoint — this probe measures the carrier, not the model.

    Untrained is stated in the report rather than hidden: a trained arm would
    make the ticks look meaningful without changing what is being measured.
    """
    from ai.core.stateful_decoder import GRUCore, SSMCore

    directory.mkdir(parents=True, exist_ok=True)
    core = (GRUCore if arch == "gru" else SSMCore)(
        token_count, hidden=64, emb=32, chunk_seconds=60.0, seed=0
    ).eval()
    core.save_weights(str(directory / "weights.pt"))
    return directory


def strata(items: Sequence[Any]) -> Dict[str, List[Any]]:
    """Group the standard set by ``kind`` — one session per stratum."""
    grouped: Dict[str, List[Any]] = defaultdict(list)
    for item in items:
        grouped[str(item.kind)].append(item)
    return dict(sorted(grouped.items()))


def arrange(kind_items: Dict[str, List[Any]], target: int, seed: int = 0) -> List[tuple]:
    """The turn order: whole passes over the set, each pass a fixed shuffle.

    Whole passes, not a truncated sample: cutting the last pass mid-way would
    drop turns from whichever strata happened to land at the tail, and a short
    stratum would then miss its floor for a reason that has nothing to do with
    the carrier. Passes are counted up, so the total lands at or above target.
    """
    import random

    order: List[tuple] = []
    turns_per_pass = sum(len(v) for v in kind_items.values())
    passes = max(1, -(-int(target) // max(1, turns_per_pass)))
    for pass_index in range(passes):
        batch: List[tuple] = []
        for kind, entries in kind_items.items():
            shuffled = list(entries)
            random.Random(f"{seed}:{pass_index}:{kind}").shuffle(shuffled)
            batch.extend((kind, item) for item in shuffled)
        random.Random(f"{seed}:{pass_index}").shuffle(batch)
        order.extend(batch)
    return order


def summarise(records: Sequence[Dict[str, Any]], target: int) -> Dict[str, Any]:
    """The gate. Every check here is a statement the run can fail."""
    by_stratum: Dict[str, int] = Counter(str(r["stratum"]) for r in records)
    by_session: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_session[str(record["session"])].append(record)

    sessions: Dict[str, Any] = {}
    versions_ok = True
    for label, rows in sorted(by_session.items()):
        versions = [int(r["state_version"]) for r in rows]
        refused = [r for r in rows if r.get("state_source") != "core"]
        monotonic = all(b > a for a, b in zip(versions, versions[1:]))
        versions_ok = versions_ok and monotonic and not refused
        sessions[label] = {
            "turns": len(rows),
            "refusals": len(refused),
            "versions_monotonic": monotonic,
            "first_version": versions[0],
            "last_version": versions[-1],
            "final_ticks": int(rows[-1]["ticks"]),
            "created_on_first_turn": bool(rows[0]["created"]),
            "state_path": rows[0]["state_path"],
        }

    strata_ok = {
        kind: count >= min(MIN_STRATUM_TURNS, standard_size(kind))
        for kind, count in by_stratum.items()
    }
    dts = sorted(float(r["dt_s"]) for r in records if float(r["dt_s"]) > 0)

    checks = {
        "turns": len(records) >= int(target),
        "no_refusals": all(v["refusals"] == 0 for v in sessions.values()),
        "versions_strictly_increase": versions_ok,
        "every_stratum_recorded": all(k in by_stratum for k in REQUIRED_STRATA)
        and all(strata_ok.values()),
        "every_turn_carried_by_the_core": all(
            str(r.get("state_source")) == "core" for r in records
        ),
    }
    return {
        "turns": len(records),
        "target": int(target),
        "by_stratum": dict(sorted(by_stratum.items())),
        "stratum_floor": {k: min(MIN_STRATUM_TURNS, standard_size(k)) for k in by_stratum},
        "sessions": sessions,
        "dt_s": {"count": len(dts), "median": _median(dts), "max": dts[-1] if dts else 0.0},
        "checks": checks,
        "all_pass": all(checks.values()),
    }


_STANDARD_SIZES: Dict[str, int] = {}


def standard_size(kind: str) -> int:
    """How many items of ``kind`` the standard set holds (cached)."""
    if not _STANDARD_SIZES:
        for kind_, entries in strata(_build_standard_set()).items():
            _STANDARD_SIZES[kind_] = len(entries)
    return _STANDARD_SIZES.get(kind, 0)


def _build_standard_set() -> List[Any]:
    from ai.response.human_speech import build_standard_set

    return build_standard_set()


def _median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    middle = len(values) // 2
    if len(values) % 2:
        return float(values[middle])
    return float((values[middle - 1] + values[middle]) / 2.0)


def _record(turn: int, kind: str, label: str, result: Dict[str, Any]) -> Dict[str, Any]:
    core = result.get("core_state") or {}
    return {
        "turn": turn,
        "stratum": kind,
        "session": label,
        "state_source": result.get("state_source"),
        "route": result.get("route"),
        "backend": result.get("backend"),
        "response_chars": len(str(result.get("response") or result.get("text") or "")),
        "created": bool(core.get("created")),
        "ticks": int(core.get("ticks") or 0),
        "state_version": int(core.get("state_version") or 0),
        "dt_s": float(core.get("dt_s") or 0.0),
        "arch": core.get("arch"),
        "tokenizer": core.get("tokenizer"),
        "weights_hash": core.get("weights_hash"),
        "state_path": core.get("state_path"),
    }


async def run(args: argparse.Namespace) -> int:
    probe = _load_script("probe_native_dialogue", "probe_native_dialogue.py")
    trace = _load_script("trace_reply", "trace_reply.py")

    probe.acquire_probe_lock()
    sandbox = probe.isolate_data_dir()
    if not args.keep_sandbox:
        shutil.rmtree(sandbox, ignore_errors=True)

    core_dir = Path(args.core_dir) if args.core_dir else sandbox / "core_state"
    if core_dir.exists():
        shutil.rmtree(core_dir, ignore_errors=True)
    _build_checkpoint(core_dir, arch=args.arch)

    os.environ["ANGELA_STATEFUL_CORE"] = "1"
    os.environ["ANGELA_STATEFUL_CORE_DIR"] = str(core_dir)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    jsonl_path = REPORT_DIR / f"turns_{stamp}.jsonl"
    summary_path = REPORT_DIR / f"turns_{stamp}.json"

    kinds = strata(_build_standard_set())
    order = arrange(kinds, args.turns, seed=args.seed)

    import services.llm.router as router_mod
    from api.routes.chat_routes import _handle_chat_request

    service = trace.build_native_service()
    await service.initialize()
    previous = getattr(router_mod, "_llm_service", None)
    router_mod._llm_service = service

    records: List[Dict[str, Any]] = []
    started = time.monotonic()
    try:
        with jsonl_path.open("w", encoding="utf-8") as sink:
            for index, (kind, item) in enumerate(order):
                label = f"core-turns-{kind}"
                result = await _handle_chat_request(
                    user_message=str(item.message),
                    user_name="core-turns",
                    history=[],
                    session_id=label,
                    origin="core-turns",
                )
                record = _record(index, kind, label, result or {})
                records.append(record)
                sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                sink.flush()
                if args.progress and (index + 1) % args.progress == 0:
                    elapsed = time.monotonic() - started
                    rate = (index + 1) / max(elapsed, 1e-9)
                    print(
                        f"  {index + 1}/{len(order)} turns  "
                        f"({rate:.1f}/s, {elapsed:.0f}s elapsed)",
                        flush=True,
                    )
    finally:
        router_mod._llm_service = previous

    elapsed = time.monotonic() - started
    summary = summarise(records, args.turns)
    summary.update(
        {
            "elapsed_s": round(elapsed, 1),
            "turns_per_s": round(len(records) / max(elapsed, 1e-9), 2),
            "core": {
                "directory": str(core_dir),
                "arch": args.arch,
                "checkpoint": "untrained",
                "tokenizer": "hash-bucket",
                "token_count": 26,
                "hidden": 64,
                "emb": 32,
            },
            "sandbox": str(sandbox),
            "jsonl": str(jsonl_path),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
    )
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"\nturns recorded : {summary['turns']} / {summary['target']} in {elapsed:.0f}s")
    print(f"by stratum     : {summary['by_stratum']}")
    for label, info in summary["sessions"].items():
        print(
            f"  {label:22s} turns={info['turns']:5d} "
            f"version {info['first_version']}→{info['last_version']} "
            f"ticks={info['final_ticks']:5d} refusals={info['refusals']}"
        )
    print(f"checks         : {json.dumps(summary['checks'], ensure_ascii=False)}")
    print(f"jsonl          : {jsonl_path}")
    print(f"summary        : {summary_path}")
    print(f"all_pass       : {summary['all_pass']}")

    if args.no_gate:
        return 0
    return 0 if summary["all_pass"] else 1


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", type=int, default=DEFAULT_TURNS)
    parser.add_argument("--arch", choices=["ssm", "gru"], default="ssm")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--core-dir", default="", help="reuse a checkpoint directory")
    parser.add_argument("--progress", type=int, default=200, help="print every N turns")
    parser.add_argument("--keep-sandbox", action="store_true")
    parser.add_argument("--no-gate", action="store_true", help="exit 0 even if a check fails")
    args = parser.parse_args(list(argv) if argv is not None else None)

    import asyncio

    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
