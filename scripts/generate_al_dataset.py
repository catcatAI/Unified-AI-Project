#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""Generate an AL batch at scale from the ready-made AI corpus.

Round 1 of the AI+AL loop: the AI side is abundant (``core_train.jsonl``,
already leak-checked when it was built), the AL side is what needs preparing.
A later batch takes a *fresh slice* of the corpus with ``--skip`` (round 1
used rows 0-4000; re-sampling the same rows with a new seed would only
resample the state values — same questions, wasted training).
This script attaches an AL state transition to each AI pair and writes a file
in the *pilot* shape, so ``prepare_ai_al_training_data.py --src`` can split,
leak-check and emit the trainable jsonl without a second code path.

The transition is the contract's operator, not an invention::

    v <- target + (v - target) * exp(-dt / tau)      al-engine-contract.md §5

* ``target``  = the pilot's ``al_state_out`` for the same intent, or the
  pilot's mean in-state (the baseline) when the intent is not one of the 10
  pilot rows. The whole target table is *fitted to those 10 rows*.
* ``tau``     = 1.0 ticks for every field: all 7 pilot fields are ``fast``
  under §3.1 (emotion PAD, fatigue, stress, health).
* ``dt``      = sampled from a fixed ladder (deterministic under ``--seed``).
* ``routing_mode`` is carried over: **all 10 pilot rows keep their mode across
  the interaction**, so the generator never invents a mode switch.

Limits, stated so they are not mistaken for capability:

* the target table comes from 10 hand-written rows — it is a data-prep
  placeholder for the AL engine's event-driven targets, not AL dynamics;
* intent labelling uses keyword rules, a placeholder for the production
  ``ai/core/query_classifier.py``;
* these rows teach the *mapping* (state, text) -> (response, state'), they are
  not evidence that the AL state model is right.

Usage:
    python scripts/generate_al_dataset.py
    python scripts/generate_al_dataset.py --rows 4000 --seed 7
    python scripts/generate_al_dataset.py --check
    python scripts/generate_al_dataset.py --holdout-cells unknown:conservative,knowledge_query:neutral
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
AI_SRC = REPO_ROOT / "apps" / "backend" / "data" / "processed" / "core_train.jsonl"
PILOT = REPO_ROOT / "apps" / "backend" / "data" / "processed" / "ai_al_pilot_dataset.json"
OUT = REPO_ROOT / "apps" / "backend" / "data" / "processed" / "ai_al_round1_dataset.json"
BENCH = REPO_ROOT / "benchmarks" / "data" / "native_bench_v1.json"

_PUNCT = re.compile(r"[^\w\s]+", re.UNICODE)
_FIELDS = ("valence", "arousal", "dominance", "fatigue", "stress", "health")
_RANGE = {
    "valence": (-1.0, 1.0),
    "arousal": (-1.0, 1.0),
    "dominance": (-1.0, 1.0),
    "fatigue": (0.0, 1.0),
    "stress": (0.0, 1.0),
    "health": (0.0, 1.0),
}
_TAU = 1.0  # every pilot field is `fast` (contract §3.1); one tau, no invention
_DT_LADDER = (0.25, 0.5, 1.0, 2.0)
# Pilot mode counts (4 exploratory / 4 neutral / 2 conservative), used as
# sampling weights for the *in* state only; the *out* mode is carried over.
_MODES = ("exploratory", "neutral", "conservative")
_MODE_WEIGHTS = (4, 4, 2)

# MVE-1 compositional-holdout cells (probe_emergence_boundary.py): one
# (intent, mode) cell per intent. Carved with --holdout-cells — each intent
# keeps two modes in training and every mode keeps the other intents, so a
# model that passes rows from these cells is composing the intent-target
# branch with the mode-carry branch instead of retrieving a seen pairing.
# farewell is absent on purpose: only 16 rows corpus-wide cannot fill a cell.
MVE1_HOLDOUT_CELLS: Dict[str, str] = {
    "unknown": "conservative",
    "knowledge_query": "neutral",
    "math_query": "exploratory",
    "humor": "conservative",
    "greeting": "neutral",
}


def _parse_holdout_cells(spec: str) -> Dict[str, str]:
    """``"intent:mode,intent:mode"`` -> dict; an empty spec -> ``{}``."""
    cells: Dict[str, str] = {}
    for part in (p.strip() for p in spec.split(",")):
        if not part:
            continue
        intent, sep, mode = part.partition(":")
        if not sep or not intent or mode not in _MODES:
            raise SystemExit(f"bad --holdout-cells entry {part!r} (want intent:mode)")
        cells[intent] = mode
    return cells


# Keyword rules — a placeholder for the production query_classifier.
_INTENT_KEYWORDS = (
    ("humor", ("joke", "funny", "笑話")),
    ("math_query", ("calculate", "compute", "how much", "equals", "算出", "等於")),
    ("greeting", ("hello", "good morning", "good evening", "你好", "您好")),
    ("farewell", ("goodbye", "see you", "再見", "拜拜")),
    (
        "knowledge_query",
        ("why ", "explain", "describe", "what is", "what are", "為什麼", "是什麼"),
    ),
)


def _norm(text: str) -> str:
    return " ".join(_PUNCT.sub(" ", str(text or "")).lower().split())


def _intent_of(text: str) -> str:
    low = str(text or "").lower()
    for intent, keys in _INTENT_KEYWORDS:
        if any(k in low for k in keys):
            return intent
    return "unknown"


def _benchmark_norms() -> set[str]:
    if not BENCH.exists():
        return set()
    data = json.loads(BENCH.read_text(encoding="utf-8"))
    out = set()
    for suite in (data.get("suites") or {}).values():
        for item in suite.get("items") or []:
            if item.get("q"):
                out.add(_norm(item["q"]))
    return out


def _pilot_tables() -> Tuple[Dict[str, float], Dict[str, Dict[str, float]], int]:
    """Baseline (mean in-state), per-intent targets (pilot out-state), rows."""
    data = json.loads(PILOT.read_text(encoding="utf-8"))
    rows = data.get("examples") or []
    if not rows:
        raise SystemExit(f"{PILOT} has no examples — nothing to fit the target table from")
    sums = {f: 0.0 for f in _FIELDS}
    targets: Dict[str, Dict[str, float]] = {}
    for ex in rows:
        for f in _FIELDS:
            sums[f] += float(ex["al_state_in"][f])
        targets[str(ex.get("intent") or "unknown")] = {
            f: float(ex["al_state_out"][f]) for f in _FIELDS
        }
    baseline = {f: sums[f] / len(rows) for f in _FIELDS}
    return baseline, targets, len(rows)


def transition(
    state: Dict[str, float],
    target: Dict[str, float],
    dt: float,
    tau: float = _TAU,
) -> Dict[str, float]:
    """Contract §5 operator: exponential relaxation toward the target."""
    k = math.exp(-dt / tau)
    out: Dict[str, float] = {}
    for f in _FIELDS:
        v = target[f] + (state[f] - target[f]) * k
        lo, hi = _RANGE[f]
        out[f] = round(min(hi, max(lo, v)), 4)
    return out


def _sample_state(rng: random.Random) -> Dict[str, float]:
    return {f: round(rng.uniform(*_RANGE[f]), 4) for f in _FIELDS}


def _load_ai_rows(limit: int, skip: int = 0) -> List[dict]:
    if not AI_SRC.exists():
        raise SystemExit(f"missing {AI_SRC} — run scripts/prepare_core_training_data.py first")
    rows: List[dict] = []
    seen: set[str] = set()
    bench = _benchmark_norms()
    leaked = 0
    skipped = 0
    with AI_SRC.open(encoding="utf-8") as fh:
        for line in fh:
            if limit and len(rows) >= limit:
                break
            row = json.loads(line)
            text = str(row.get("input") or "").strip()
            answer = str(row.get("output") or "").strip()
            if not text or not answer:
                continue
            key = _norm(text)
            if key in bench:  # gate 1: never carry a benchmark question in
                leaked += 1
                continue
            if key in seen:  # gate 2: no duplicates
                continue
            seen.add(key)
            if skipped < skip:  # gate 3: a later batch starts after earlier slices
                skipped += 1
                continue
            rows.append({"input": text, "output": answer})
    _load_ai_rows.leaked = leaked  # reported by build()
    return rows


def build(
    rows: int,
    seed: int,
    skip: int = 0,
    id_prefix: str = "r1_",
    holdout_cells: Optional[Dict[str, str]] = None,
) -> Dict[str, object]:
    baseline, targets, pilot_rows = _pilot_tables()
    source = _load_ai_rows(rows, skip=skip)
    rng = random.Random(seed)
    examples: List[dict] = []
    carved = 0
    for i, row in enumerate(source, start=1):
        intent = _intent_of(row["input"])
        state_in = _sample_state(rng)
        # mode is sampled for the *in* state only; the *out* mode is carried
        # over, because all 10 pilot rows keep their mode across the interaction
        mode = rng.choices(_MODES, _MODE_WEIGHTS)[0]
        # dt is drawn *before* the carve check so the rng stream — and every
        # row after a dropped one — is identical with or without the carve.
        dt = _DT_LADDER[rng.randrange(len(_DT_LADDER))]
        if holdout_cells and holdout_cells.get(intent) == mode:
            # MVE-1 carve: drop the held-out (intent, mode) cell.
            carved += 1
            continue
        state_in["routing_mode"] = mode
        target = targets.get(intent, baseline)
        state_out = transition(state_in, target, dt)
        examples.append(
            {
                "sample_id": f"{id_prefix}{i:06d}",
                "input_text": row["input"],
                "expected_response": row["output"],
                "al_state_in": state_in,
                "al_state_out": {**state_out, "routing_mode": mode},
                "intent": intent,
                "confidence": 0.9,
            }
        )
    return {
        "version": "1.1.0",
        "description": (
            (
                "Round-1 AI+AL dataset: AI corpus pairs with an AL state transition "
                "computed by the contract §5 operator (targets fitted to the 10 pilot rows)."
                if id_prefix == "r1_" and not skip
                else f"AI+AL batch {id_prefix.rstrip('_')} (AI corpus rows after the first "
                f"{skip} accepted) with an AL state transition computed by the contract "
                "§5 operator (targets fitted to the 10 pilot rows)."
            )
        ),
        "seed": seed,
        "total_samples": len(examples),
        "schema": {
            "input_text": "str (from core_train.jsonl)",
            "expected_response": "str (from core_train.jsonl)",
            "al_state_in": "sampled PAD + fatigue/stress/health + routing_mode",
            "al_state_out": "contract §5 operator toward the intent target",
            "intent": "keyword rules (placeholder for query_classifier)",
        },
        "provenance": {
            "ai_source": str(AI_SRC.relative_to(REPO_ROOT)),
            "ai_source_sha256": hashlib.sha256(AI_SRC.read_bytes()).hexdigest(),
            "pilot": str(PILOT.relative_to(REPO_ROOT)),
            "pilot_rows": pilot_rows,
            "benchmark_leaked": getattr(_load_ai_rows, "leaked", 0),
            "tau": _TAU,
            "dt_ladder": list(_DT_LADDER),
            "mode_rule": "routing_mode_out = routing_mode_in (10/10 pilot rows)",
            "target_rule": "pilot al_state_out for the intent, else pilot mean in-state",
            # Recorded only when non-default: a default-args rebuild must stay
            # byte-identical, or `--check` would fail on the round-1 file.
            **({"skip": skip} if skip else {}),
            **({"id_prefix": id_prefix} if id_prefix != "r1_" else {}),
            # Recorded only when carving: a default build must stay
            # byte-identical or `--check` would fail on the round files.
            **(
                {"holdout_cells": dict(holdout_cells), "holdout_carved": carved}
                if holdout_cells
                else {}
            ),
        },
        "examples": examples,
    }


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rows", type=int, default=4000, help="AI pairs to convert (default 4000)")
    ap.add_argument("--seed", type=int, default=7, help="sampling seed (default 7)")
    ap.add_argument(
        "--skip",
        type=int,
        default=0,
        help="drop the first N accepted AI rows so a later batch takes a fresh "
        "slice (round 1 used 0-4000; a new seed alone repeats the same questions)",
    )
    ap.add_argument(
        "--id-prefix",
        default="r1_",
        help="sample_id prefix (default r1_; use r2_ for the next batch — it also "
        "feeds the deterministic split in prepare_ai_al_training_data.py)",
    )
    ap.add_argument(
        "--holdout-cells",
        default="",
        help="comma-separated intent:mode cells to EXCLUDE from this batch "
        "(MVE-1 compositional holdout; cells declared in MVE1_HOLDOUT_CELLS). "
        "Default off: a default build must stay byte-identical for --check",
    )
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument(
        "--check",
        action="store_true",
        help="rebuild in memory and fail if the file on disk differs (no writes)",
    )
    args = ap.parse_args(argv)
    holdout = _parse_holdout_cells(args.holdout_cells)

    built = build(
        args.rows,
        args.seed,
        skip=args.skip,
        id_prefix=args.id_prefix,
        holdout_cells=holdout or None,
    )
    body = json.dumps(built, indent=2, ensure_ascii=False) + "\n"
    out = Path(args.out)

    if args.check:
        if not out.exists():
            print(f"check failed: missing {out.name}")
            return 1
        if out.read_text(encoding="utf-8") != body:
            print(f"check failed: {out.name} differs from a fresh build")
            return 1
        print(f"check ok: {built['total_samples']} examples")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    p = built["provenance"]
    carve = f" carved={p['holdout_carved']} of {len(p['holdout_cells'])} cells" if holdout else ""
    print(
        f"examples={built['total_samples']} leaked={p['benchmark_leaked']} "
        f"pilot_rows={p['pilot_rows']} seed={args.seed} "
        f"skip={args.skip} prefix={args.id_prefix}{carve}\nwrote {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
