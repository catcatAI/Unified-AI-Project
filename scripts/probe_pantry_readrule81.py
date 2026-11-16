#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§81: does removing the key-norm race let the read address the needed entry?

Why this exists
---------------
§80 read the model's own attention at the question turn on the frozen §77
treatment carrier and found a fixed slot: every one of the 200 held-out reads
put mass 1.0 on slot 2, the two-way forced choice was exactly 0.5000, and the
200 train twin pairs moved by 0.0 total variation.  The diagnosis it recorded
was a *norm race*: slot 2's key norm has median 9.8219 against slot 1's 2.8158,
and ``softmax(exp(log_read_scale) * k . q)`` with ``exp(log_read_scale) = 4``
and ``||q|| ~ 17`` reaches a logit gap of hundreds, so the comparison never
depends on direction.

That leaves two different failures, and they call for different repairs:

1. the store's keys do not contain what would be needed to tell the two roster
   entries apart, so no read rule could address them (the write side is the
   limit), or
2. the store's keys do contain it, but the read's arithmetic (norms and the
   learned temperature) swamps the comparison.

This stage asks only the second question, on the same frozen carrier, with no
retraining and **no fitted parameters**: recompute the same read under two
rules that remove the norm race and see whether the forced choice moves.

* ``model``  - ``softmax(exp(scale) * k . q)``: the model's own read (§80).
* ``cosine`` - ``softmax(exp(scale) * (k/||k||) . q)``: the key norm is removed,
  the learned temperature stays.
* ``cosine_unit`` - ``softmax((k/||k||) . (q/||q||))``: the query norm and the
  learned temperature are removed too, so the logits are plain cosines.

The read rule here is **ours, not the model's**: a pass says the stored content
is addressable, not that this carrier addresses it.  A failure says no read
rule of this shape can, which makes the write side the next registered change.

The ``model`` column is the anchor: it must reproduce §80's stored masses to
2e-9 and its 100/200 wins, or nothing is read.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_readrule81.py \\
        --report data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json \\
        --anchor data/pantry_stage/address80/k2.json \\
        --out data/pantry_stage/readrule81/k2.json

    ./.venv/bin/python scripts/probe_pantry_readrule81.py --check data/pantry_stage/readrule81/k2.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
ADDRESS80 = REPO_ROOT / "scripts" / "probe_pantry_address80.py"

# §81.4, written before the scored run.  The read has no fitted parameters, so
# there is no probe budget here; every constant is a decision rule.
ALPHA = 0.005
NULL_DRAWS = 400
NULL_SEED = 20261125
FORCED_FLOOR = 0.5
SW_MOVE_FLOOR = 0.01
ENTRY_COVERAGE = 0.99
ENTRY_COSINE = 0.999
REF_TOLERANCE = 2e-9
ROSTER_ITEMS = 2
READ_BATCH = 32
VARIANTS = ("model", "cosine", "cosine_unit")
STAGE = "§81 does removing the key-norm race let the read address the entry the question needs?"
BRANCH_ORDER = (
    "E0-instrument",
    "N1-norm-race-is-the-limit",
    "N2-saturation-is-the-limit",
    "N3-keys-do-not-address",
)


def _load(name: str, path: Path) -> Any:
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_address80() -> Any:
    """§80's module: the frozen read point, the labels and the audit."""
    module = _load("pantry_readrule81_address80", ADDRESS80)
    for name, expected in (
        ("ALPHA", ALPHA),
        ("NULL_DRAWS", NULL_DRAWS),
        ("NULL_SEED", NULL_SEED),
        ("FORCED_FLOOR", FORCED_FLOOR),
        ("ENTRY_COVERAGE", ENTRY_COVERAGE),
        ("ENTRY_COSINE", ENTRY_COSINE),
        ("ROSTER_ITEMS", ROSTER_ITEMS),
    ):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(
                f"§81 was registered against {name}={expected}, §80 now has {actual}; "
                "the two stages no longer share a criterion"
            )
    return module


# --------------------------------------------------------------------------- #
# the three read rules
# --------------------------------------------------------------------------- #
def rule_weights(torch: Any, keys: Any, query: Any, exp_scale: Any, variant: str) -> Any:
    """One attention distribution over the store's slots, under one read rule."""
    if variant == "model":
        scores = keys @ query
        return torch.softmax(exp_scale * scores, dim=-1)
    key_norm = keys.norm(dim=-1, keepdim=True).clamp_min(1e-12)
    if variant == "cosine":
        scores = (keys / key_norm) @ query
        return torch.softmax(exp_scale * scores, dim=-1)
    if variant == "cosine_unit":
        query_norm = query.norm().clamp_min(1e-12)
        scores = (keys / key_norm) @ (query / query_norm)
        return torch.softmax(scores, dim=-1)
    raise SystemExit(f"unknown read rule {variant!r}")


def weights_for(torch: Any, record: Dict[str, Any], exp_scale: Any, variant: str) -> Any:
    return rule_weights(torch, record["keys"], record["query"], exp_scale, variant)


# --------------------------------------------------------------------------- #
# the read: the store before the question turn, the question's last token
# --------------------------------------------------------------------------- #
def read_records(
    trainer: Any,
    probe: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    names: Sequence[str],
    colours: Sequence[str],
    pair: Any,
    *,
    batch: int = READ_BATCH,
) -> List[Dict[str, Any]]:
    """One record per session: the slots, the keys, the values, the query.

    The read point is §80's: the store at the boundary before the question turn,
    the question turn replayed from that boundary, the last token's ``h``.
    """
    torch = core._torch
    name_index = {name: i for i, name in enumerate(names)}
    colour_index = {colour: i for i, colour in enumerate(colours)}
    exp_scale = torch.exp(core.log_read_scale)
    records: List[Dict[str, Any]] = []
    core.eval()
    with torch.no_grad():
        for chunk in trainer._chunks(list(sessions), batch):
            turns: List[List[List[int]]] = []
            gaps: List[List[float]] = []
            for session in chunk:
                tokens, deltas = probe.turn_payload(trainer, session)
                turns.append(tokens)
                gaps.append(deltas)
            snapshots: List[Any] = []
            trainer.run_session(core, turns, gaps, boundaries=snapshots)
            for index, session in enumerate(chunk):
                q = len(turns[index]) - 1
                evidence = int(session["session_meta"]["evidence_turn"])
                if evidence != q - 1:
                    raise SystemExit(
                        f"{session['session_id']}: evidence turn {evidence} is not the turn "
                        f"before the question ({q - 1}); the read point is not the registered one"
                    )
                pairs = pair.roster_mapping(session)
                if len(pairs) != ROSTER_ITEMS:
                    raise SystemExit(
                        f"{session['session_id']}: {len(pairs)} roster items, "
                        f"registered {ROSTER_ITEMS}"
                    )
                keys = [str(key) for key, _ in pairs]
                seen = mod_seen_value(session)
                if keys.count(seen) != 1:
                    raise SystemExit(f"{session['session_id']}: {seen} is not one roster colour")
                item = keys.index(seen)
                before = snapshots[q - 1]
                state = core.init_state(len(chunk))
                state.tensors = {name: value for name, value in before.items()}
                delta = torch.as_tensor(
                    [gap[q] for gap in gaps],
                    dtype=before["h"].dtype,
                    device=before["h"].device,
                )
                hidden = core.al_step(delta, state).tensors["h"][index : index + 1]
                stacked = pair._replay_turn(trainer, core, turns[index][q], hidden)
                h_final = stacked[-1].reshape(-1)
                store_keys = before["k"][index].detach().clone()
                store_values = before["v"][index].detach().clone()
                query = core.query_proj(h_final.reshape(1, -1)).reshape(-1).detach().clone()
                slots = mod_roster_slots(
                    trainer,
                    turns[index],
                    int(session["session_meta"]["roster_turn"]),
                    int(core.slots),
                )
                records.append(
                    {
                        "session_id": session["session_id"],
                        "structure": str(
                            session["session_meta"].get("order_augmented_of")
                            or session["session_id"]
                        ),
                        "twin": bool(session["session_meta"].get("order_augmented_of")),
                        "item": int(item),
                        "slots": [int(slot) for slot in slots],
                        "keys": store_keys,
                        "values": store_values,
                        "query": query,
                        "h": h_final.detach().clone(),
                        "v_roster": torch.stack([store_values[slot].reshape(-1) for slot in slots])
                        .detach()
                        .clone(),
                        "key_norms": [round(float(store_keys[slot].norm()), 6) for slot in slots],
                        "query_norm": round(float(query.norm()), 6),
                        "name": name_index[str(pairs[item][1])],
                        "partner_name": name_index[str(pairs[1 - item][1])],
                        "colour": colour_index[str(pairs[item][0])],
                        "evidence_colour": colour_index[seen],
                    }
                )
    return records


def mod_seen_value(session: Dict[str, Any]) -> str:
    return ADDRESS.seen_value(session)


def mod_roster_slots(trainer: Any, turns: Any, roster: int, slots: int) -> List[int]:
    return ADDRESS.roster_slots(trainer, turns, roster, slots)


# --------------------------------------------------------------------------- #
# the scored cell: two-way forced choice under one rule
# --------------------------------------------------------------------------- #
def _summary(values: Sequence[float]) -> Dict[str, float]:
    ordered = sorted(values)
    count = len(ordered)
    if count == 0:
        return {"mean": 0.0, "sd": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0, "p99": 0.0}
    mean = sum(ordered) / count
    spread = math.sqrt(sum((value - mean) ** 2 for value in ordered) / count)

    def quantile(q: float) -> float:
        return ordered[min(count - 1, max(0, int(round(q * (count - 1)))))] if count else 0.0

    return {
        "mean": round(mean, 6),
        "sd": round(spread, 6),
        "min": round(ordered[0], 6),
        "max": round(ordered[-1], 6),
        "p95": round(quantile(0.95), 6),
        "p99": round(quantile(0.99), 6),
    }


def _masses(
    torch: Any, records: Sequence[Dict[str, Any]], exp_scale: Any, variant: str
) -> Tuple[Any, Any, Any]:
    first: List[float] = []
    second: List[float] = []
    for record in records:
        weights = weights_for(torch, record, exp_scale, variant)
        slots = list(record["slots"])
        first.append(float(weights[slots[0]]))
        second.append(float(weights[slots[1]]))
    items = torch.as_tensor([int(record["item"]) for record in records], dtype=torch.long)
    return (
        torch.as_tensor(first, dtype=torch.float32),
        torch.as_tensor(second, dtype=torch.float32),
        items,
    )


def address_block(
    torch: Any,
    split75: Any,
    composition: Any,
    records: Sequence[Dict[str, Any]],
    exp_scale: Any,
    variant: str,
    *,
    draws: int = NULL_DRAWS,
) -> Dict[str, Any]:
    """The two-way forced choice of attention mass under one read rule."""
    first, second, items = _masses(torch, records, exp_scale, variant)
    correct = torch.where(items == 0, first, second)
    partner = torch.where(items == 0, second, first)
    n = int(items.numel())
    wins = int((correct > partner).sum())

    def wins_for(labels: Any) -> int:
        mass = torch.where(labels == 0, first, second)
        other = torch.where(labels == 0, second, first)
        return int((mass > other).sum())

    null_wins: List[int] = []
    for draw in range(draws):
        shuffled = composition.permute_rows(torch, items, NULL_SEED + draw)
        null_wins.append(wins_for(shuffled))
    ge = sum(1 for value in null_wins if value >= wins)
    p_value = round((1 + ge) / (draws + 1), 6)

    hist: Dict[str, int] = {}
    argmax_on_roster = 0
    for record in records:
        weights = weights_for(torch, record, exp_scale, variant)
        slot = int(torch.argmax(weights))
        key = str(slot)
        hist[key] = hist.get(key, 0) + 1
        argmax_on_roster += int(slot in record["slots"])
    roster_mass = [
        float(weights_for(torch, record, exp_scale, variant)[list(record["slots"])].sum())
        for record in records
    ]
    return {
        "variant": variant,
        "n": n,
        "wins": wins,
        "forced": round(wins / max(n, 1), 6),
        "wilson": split75.wilson(wins, n),
        "p_value": p_value,
        "null": {
            "draws": int(draws),
            "seed": NULL_SEED,
            "ge": int(ge),
            "wins": _summary([float(value) for value in null_wins]),
        },
        "chance": {"forced": FORCED_FLOOR},
        "m0": [round(float(value), 9) for value in first.tolist()],
        "m1": [round(float(value), 9) for value in second.tolist()],
        "items": [int(value) for value in items.tolist()],
        "roster_mass": _summary(roster_mass),
        "argmax_hist": hist,
        "argmax_on_roster": round(argmax_on_roster / max(n, 1), 6),
    }


def query_block(
    torch: Any,
    split75: Any,
    composition: Any,
    records: Sequence[Dict[str, Any]],
    exp_scale: Any,
    variant: str,
    *,
    draws: int = NULL_DRAWS,
) -> Dict[str, Any]:
    """Descriptive: does the *query* carry the session-specific choice?

    The queries are re-paired across sessions (no refitting, the store's keys
    stay with their own session), so a rule that wins on the strength of the
    label balance alone keeps winning and a rule that needs this session's query
    drops to chance.
    """
    n = len(records)
    wins = 0
    for record in records:
        weights = weights_for(torch, record, exp_scale, variant)
        slots = list(record["slots"])
        mass = float(weights[slots[0]])
        other = float(weights[slots[1]])
        correct, partner = (mass, other) if int(record["item"]) == 0 else (other, mass)
        wins += int(correct > partner)
    order_source = torch.arange(n, dtype=torch.long)
    null_wins: List[int] = []
    for draw in range(draws):
        order = composition.permute_rows(torch, order_source, NULL_SEED + draw)
        count = 0
        for row, record in enumerate(records):
            donor = records[int(order[row])]
            weights = rule_weights(torch, record["keys"], donor["query"], exp_scale, variant)
            slots = list(record["slots"])
            mass = float(weights[slots[0]])
            other = float(weights[slots[1]])
            correct, partner = (mass, other) if int(record["item"]) == 0 else (other, mass)
            count += int(correct > partner)
        null_wins.append(count)
    ge = sum(1 for value in null_wins if value >= wins)
    return {
        "variant": variant,
        "n": n,
        "wins": wins,
        "forced": round(wins / max(n, 1), 6),
        "null": {
            "draws": int(draws),
            "seed": NULL_SEED,
            "ge": int(ge),
            "wins": _summary([float(value) for value in null_wins]),
        },
        "p_value": round((1 + ge) / (draws + 1), 6),
        "reading": "descriptive only: the queries are re-paired, the stores are not",
    }


def swap_block(
    torch: Any,
    records: Sequence[Dict[str, Any]],
    exp_scale: Any,
    variant: str,
) -> Dict[str, Any]:
    """Twin pairs: does the read move when the roster order is swapped?"""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        groups.setdefault(str(record["structure"]), []).append(record)
    distances: List[float] = []
    roster_distances: List[float] = []
    failures: List[Dict[str, Any]] = []
    for structure, group in sorted(groups.items()):
        if len(group) != 2:
            failures.append({"structure": structure, "problem": f"{len(group)} twins"})
            continue
        left, right = group
        if list(left["slots"]) != list(right["slots"]):
            failures.append({"structure": structure, "problem": "twins have different slots"})
            continue
        if int(left["item"]) == int(right["item"]):
            failures.append({"structure": structure, "problem": "twins have the same item"})
            continue
        first = weights_for(torch, left, exp_scale, variant)
        second = weights_for(torch, right, exp_scale, variant)
        distances.append(0.5 * float((first - second).abs().sum()))
        slots = list(left["slots"])
        roster_distances.append(
            0.5 * sum(abs(float(first[slot]) - float(second[slot])) for slot in slots)
        )
    summary = _summary(distances)
    return {
        "variant": variant,
        "pairs": len(distances),
        "structures": len(groups),
        "tw": summary,
        "roster_tw": _summary(roster_distances),
        "floor": SW_MOVE_FLOOR,
        "moves": bool(distances and summary["mean"] > SW_MOVE_FLOOR),
        "distances": [round(value, 9) for value in distances],
        "failures": failures[:10],
    }


# --------------------------------------------------------------------------- #
# the anchor: the model rule is §80's stored read
# --------------------------------------------------------------------------- #
def anchor_block(
    torch: Any,
    records: Sequence[Dict[str, Any]],
    exp_scale: Any,
    anchor: Dict[str, Any],
) -> Dict[str, Any]:
    """The model column must reproduce §80's stored masses and wins."""
    block = anchor["address"]
    stored_m0 = [float(value) for value in block["m0"]]
    stored_m1 = [float(value) for value in block["m1"]]
    stored_items = [int(value) for value in block["items"]]
    if not (len(stored_m0) == len(stored_m1) == len(stored_items) == len(records)):
        raise SystemExit(
            f"§80's anchor has {len(stored_m0)} reads, this run has {len(records)}; "
            "the anchor is not the same held-out set"
        )
    first, second, items = _masses(torch, records, exp_scale, "model")
    m0 = [round(float(value), 9) for value in first.tolist()]
    m1 = [round(float(value), 9) for value in second.tolist()]
    mismatch = 0
    worst = 0.0
    for left, right, stored_left, stored_right, item, stored_item in zip(
        m0, m1, stored_m0, stored_m1, items.tolist(), stored_items
    ):
        if int(item) != int(stored_item):
            mismatch += 1
            continue
        worst = max(worst, abs(left - stored_left), abs(right - stored_right))
        if abs(left - stored_left) > REF_TOLERANCE or abs(right - stored_right) > REF_TOLERANCE:
            mismatch += 1
    wins = 0
    for left, right, item in zip(m0, m1, items.tolist()):
        correct, partner = (left, right) if int(item) == 0 else (right, left)
        wins += int(correct > partner)
    return {
        "reads": len(records),
        "stored_wins": int(block["wins"]),
        "wins": wins,
        "max_abs_diff": worst,
        "tolerance": REF_TOLERANCE,
        "mismatches": mismatch,
        "reproduced": bool(mismatch == 0 and worst <= REF_TOLERANCE and wins == int(block["wins"])),
        "reading": (
            "the model rule on this run's extraction must give §80's stored masses (2e-9) "
            "and its win count"
        ),
    }


# --------------------------------------------------------------------------- #
# gates and the branch
# --------------------------------------------------------------------------- #
def gates(outcome: Dict[str, Any]) -> Dict[str, Any]:
    instrument = outcome["instrument"]
    anchor = instrument["anchor"]
    audit = instrument["read_audit"]
    coverage = min(float(audit["train"]["coverage"]), float(audit["heldout"]["coverage"]))
    i0 = {
        "pass": bool(
            instrument["carrier_unchanged"]
            and instrument["checkpoint_unchanged"]
            and instrument["mode_matches"]
            and instrument["corpus_digests_match"]
            and coverage >= ENTRY_COVERAGE
            and anchor["reproduced"]
        ),
        "carrier_unchanged": instrument["carrier_unchanged"],
        "checkpoint_unchanged": instrument["checkpoint_unchanged"],
        "mode_matches": instrument["mode_matches"],
        "corpus_digests_match": instrument["corpus_digests_match"],
        "read_coverage": coverage,
        "read_required_coverage": ENTRY_COVERAGE,
        "anchor_reproduced": anchor["reproduced"],
        "anchor_max_abs_diff": anchor["max_abs_diff"],
        "reading": (
            "the carrier, checkpoint and corpus are the frozen §77 ones, the roster writes are "
            "still the ones at the read boundary, and the model rule reproduces §80's stored "
            "masses"
        ),
    }
    cells: Dict[str, Any] = {}
    for variant in VARIANTS:
        block = outcome["address"][variant]
        wilson = block["wilson"]
        cells[variant] = {
            "pass": bool(float(wilson["low"]) > FORCED_FLOOR and float(block["p_value"]) < ALPHA),
            "n": block["n"],
            "wins": block["wins"],
            "forced": block["forced"],
            "wilson_low": float(wilson["low"]),
            "p_value": block["p_value"],
            "roster_mass": block["roster_mass"]["mean"],
            "argmax_on_roster": block["argmax_on_roster"],
            "floor": FORCED_FLOOR,
            "alpha": ALPHA,
            "reading": "the same reads scored under the rule named by the key",
        }
    return {"I0_instrument": i0, "cells": cells}


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """Fixed precedence, written before the run: E0 > N1 > N2 > N3."""
    if not gate["I0_instrument"]["pass"]:
        return {
            "id": "E0-instrument",
            "reading": (
                "the carrier, the corpus, the read-boundary audit or the §80 anchor moved; "
                "nothing is read"
            ),
            "next": "fix the instrument before asking what the read can address",
        }
    if gate["cells"]["cosine"]["pass"]:
        return {
            "id": "N1-norm-race-is-the-limit",
            "reading": (
                "with the key norm removed the same reads pass the two-way choice: the store's "
                "keys do separate the two roster entries, and the model's own read loses the "
                "comparison to the norm of one slot"
            ),
            "next": (
                "retrain the carrier with the normalised-key read at the same budget (10,000 "
                "steps, 168,150 parameters, same corpus) and re-read §80's cell plus §77's "
                "cells; no extra epochs, width or data"
            ),
        }
    if gate["cells"]["cosine_unit"]["pass"]:
        return {
            "id": "N2-saturation-is-the-limit",
            "reading": (
                "removing the key norm is not enough, but removing the query norm and the "
                "learned temperature as well makes the same reads pass: the comparison is "
                "saturated, not absent"
            ),
            "next": (
                "retrain with the cosine read (unit scale) at the same budget and re-read "
                "§80's cell; no extra epochs, width or data"
            ),
        }
    return {
        "id": "N3-keys-do-not-address",
        "reading": (
            "neither norm-free rule lifts the two-way choice above chance: at the read point "
            "the stored keys do not separate the entry the question needs, so no read rule of "
            "this shape can address it"
        ),
        "next": (
            "register the write-side change (the key carries the roster colour at the write "
            "point) at the same budget; the read rule is not where the remaining gap is"
        ),
    }


# --------------------------------------------------------------------------- #
# one run
# --------------------------------------------------------------------------- #
def run(
    report_path: Path,
    anchor_path: Path,
    *,
    device: str = "cpu",
    draws: int = NULL_DRAWS,
) -> Dict[str, Any]:
    started = time.time()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    anchor = json.loads(anchor_path.read_text(encoding="utf-8"))
    if anchor.get("stage") != ADDRESS.STAGE:
        raise SystemExit("the anchor is not a §80 report")
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§81 reads the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or 2)
    if k != ROSTER_ITEMS:
        raise SystemExit(f"§81 was registered at k={ROSTER_ITEMS}, this carrier has k={k}")
    seed = int(corpus_block.get("seed") or 0)
    if seed <= 0:
        raise SystemExit("the report does not record its corpus seed")

    pair = ADDRESS.load_pair79()
    composition = ADDRESS.load_composition()
    split75 = ADDRESS.load_split75()
    contents = ADDRESS.load_contents()
    probe = ADDRESS.load_readout()
    selection = contents.load_selection()
    trainer = selection.load_trainer()
    module = trainer._load_generator()

    corpus = trainer.load_corpus(
        minimal_binding=True,
        order_augmented=bool(corpus_block.get("minimal_order_augmented")),
        roster_size=k,
        seed=seed,
    )
    train = list(corpus["train"])
    held = list(corpus["heldout"])
    names = sorted(module.ACTORS)
    colours = sorted(module.COLOURS)

    checkpoint = Path(str(report.get("checkpoint")))
    hash_before = probe.checkpoint_sha256(checkpoint)
    core = probe.rebuild_core(trainer, report, device=device)
    weights_before = str(core.weights_hash() or "")
    config = report.get("config") or {}

    train_records = read_records(trainer, probe, core, train, names, colours, pair)
    held_records = read_records(trainer, probe, core, held, names, colours, pair)
    train_entries = pair.entry_records(trainer, probe, core, train, names, colours)
    held_entries = pair.entry_records(trainer, probe, core, held, names, colours)

    torch = core._torch
    exp_scale = torch.exp(core.log_read_scale)
    address = {
        variant: address_block(
            torch, split75, composition, held_records, exp_scale, variant, draws=draws
        )
        for variant in VARIANTS
    }
    swap = {variant: swap_block(torch, train_records, exp_scale, variant) for variant in VARIANTS}
    query = {
        variant: query_block(
            torch, split75, composition, held_records, exp_scale, variant, draws=draws
        )
        for variant in VARIANTS
    }
    instrument = {
        "carrier": str(report_path),
        "anchor_report": str(anchor_path),
        "checkpoint": str(checkpoint),
        "device": device,
        "write_mode": {
            "address": config.get("address"),
            "write_strength": config.get("write_strength"),
            "write_slots": config.get("write_slots"),
        },
        "registered": {"address": "item", "write_strength": "learned", "write_slots": 1},
        "mode_matches": bool(
            config.get("address") == "item"
            and config.get("write_strength") == "learned"
            and int(config.get("write_slots") or 1) == 1
        ),
        "weights_hash_before": weights_before,
        "weights_hash_after": str(core.weights_hash() or ""),
        "carrier_unchanged": str(core.weights_hash() or "") == weights_before,
        "checkpoint_sha256_before": hash_before,
        "checkpoint_sha256_after": probe.checkpoint_sha256(checkpoint),
        "checkpoint_unchanged": hash_before == probe.checkpoint_sha256(checkpoint),
        "corpus_digests_match": bool(
            (corpus.get("meta") or {}).get("train_digest") == corpus_block.get("train_digest")
            and (corpus.get("meta") or {}).get("heldout_digest")
            == corpus_block.get("heldout_digest")
        ),
        "read_audit": {
            "train": ADDRESS.read_audit(torch, train_records, train_entries),
            "heldout": ADDRESS.read_audit(torch, held_records, held_entries),
        },
        "anchor": anchor_block(torch, held_records, exp_scale, anchor),
    }

    outcome: Dict[str, Any] = {
        "stage": STAGE,
        "carrier_report": str(report_path),
        "anchor_report": str(anchor_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "corpus_seed": seed,
        "corpus": {
            "train_digest": corpus_block.get("train_digest"),
            "heldout_digest": corpus_block.get("heldout_digest"),
            "train_sessions": len(train),
            "heldout_sessions": len(held),
            "roster_items": ROSTER_ITEMS,
            "names": len(names),
            "colours": len(colours),
            "train_twins": sum(1 for record in train_records if record["twin"]),
            "heldout_twins": sum(1 for record in held_records if record["twin"]),
        },
        "read": {
            "point": "the store at the boundary before the question turn, last question token",
            "rules": {
                "model": "softmax(exp(scale) * k . q)  (the model's own read, §80)",
                "cosine": "softmax(exp(scale) * (k/||k||) . q)",
                "cosine_unit": "softmax((k/||k||) . (q/||q||))",
            },
            "scored_split": "heldout",
            "swap_split": "train (the corpus's own order-augmented twins; held-out has none)",
            "fitted_parameters": 0,
        },
        "decision": {
            "alpha": ALPHA,
            "forced_floor": FORCED_FLOOR,
            "null_draws": draws,
            "null_seed": NULL_SEED,
            "swap_move_floor": SW_MOVE_FLOOR,
            "anchor_tolerance": REF_TOLERANCE,
        },
        "reads": {"train": len(train_records), "heldout": len(held_records), "per_session": 1},
        "address": address,
        "swap": swap,
        "query": query,
        "instrument": instrument,
    }
    outcome["gates"] = gates(outcome)
    outcome["branch"] = branch(outcome["gates"])
    outcome["instrument_ok"] = bool(outcome["gates"]["I0_instrument"]["pass"])
    outcome["seconds"] = round(time.time() - started, 3)
    return outcome


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def _nested(data: Dict[str, Any], *path: str) -> Any:
    node: Any = data
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def check(path: Path) -> List[str]:
    """Re-derive every cell and the branch from the stored readings."""
    problems: List[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("stage") != STAGE:
        return ["this is not a §81 report"]
    decision = data.get("decision") or {}
    for name, expected in (
        ("alpha", ALPHA),
        ("forced_floor", FORCED_FLOOR),
        ("null_draws", NULL_DRAWS),
        ("null_seed", NULL_SEED),
        ("swap_move_floor", SW_MOVE_FLOOR),
        ("anchor_tolerance", REF_TOLERANCE),
    ):
        if decision.get(name) != expected:
            problems.append(f"decision.{name} is not the registered {expected!r}")
    reads = data.get("reads") or {}
    corpus = data.get("corpus") or {}
    if reads.get("train") != int(corpus.get("train_sessions") or 0):
        problems.append("the training read count is not one per session")
    if reads.get("heldout") != int(corpus.get("heldout_sessions") or 0):
        problems.append("the held-out read count is not one per session")

    instrument = data.get("instrument") or {}
    for split in ("train", "heldout"):
        audit = _nested(instrument, "read_audit", split) or {}
        if float(audit.get("coverage", 0.0)) < ENTRY_COVERAGE:
            problems.append(f"{split} read-boundary coverage is below {ENTRY_COVERAGE}")
    anchor = instrument.get("anchor") or {}
    if float(anchor.get("max_abs_diff", 1.0)) > REF_TOLERANCE:
        problems.append("the model rule does not reproduce §80's stored masses")
    if int(anchor.get("mismatches", 1)) != 0:
        problems.append("the model rule disagrees with §80's stored masses")

    for variant in VARIANTS:
        block = _nested(data, "address", variant) or {}
        n = int(block.get("n") or 0)
        m0 = block.get("m0") or []
        m1 = block.get("m1") or []
        items = block.get("items") or []
        if not (len(m0) == len(m1) == len(items) == n):
            problems.append(f"{variant}: the stored masses are not one pair per read")
            continue
        wins = 0
        for left, right, item in zip(m0, m1, items):
            correct, partner = (left, right) if int(item) == 0 else (right, left)
            wins += int(float(correct) > float(partner))
        if wins != int(block.get("wins") or -1):
            problems.append(f"{variant}: the forced-choice win count is not re-derivable")
        expected_forced = round(wins / max(n, 1), 6)
        if abs(float(block.get("forced", -1.0)) - expected_forced) > 1e-9:
            problems.append(f"{variant}: the forced rate is not wins/n")
        null = block.get("null") or {}
        expected_p = round((1 + int(null.get("ge") or 0)) / (int(null.get("draws") or 0) + 1), 6)
        if abs(float(block.get("p_value", -1.0)) - expected_p) > 1e-9:
            problems.append(f"{variant}: p_value is not the permutation convention")

    for variant in VARIANTS:
        swap = _nested(data, "swap", variant) or {}
        distances = swap.get("distances") or []
        if distances:
            expected_mean = round(sum(float(value) for value in distances) / len(distances), 6)
            got_mean = float((swap.get("tw") or {}).get("mean", -1.0))
            if abs(got_mean - expected_mean) > 1e-9:
                problems.append(f"{variant}: the swap distance is not the mean of its pairs")
            if int(swap.get("pairs") or 0) != len(distances):
                problems.append(f"{variant}: the swap pair count does not match its distances")
            if bool(swap.get("moves")) != bool(expected_mean > SW_MOVE_FLOOR):
                problems.append(f"{variant}: the swap verdict is not the registered floor")

    recomputed = gates(data)
    stored = data.get("gates") or {}
    if bool((stored.get("I0_instrument") or {}).get("pass")) != bool(
        recomputed["I0_instrument"]["pass"]
    ):
        problems.append("gate I0_instrument does not re-derive")
    for variant in VARIANTS:
        stored_cell = (stored.get("cells") or {}).get(variant) or {}
        if bool(stored_cell.get("pass")) != bool(recomputed["cells"][variant]["pass"]):
            problems.append(f"cell {variant} does not re-derive")
    expected_branch = branch(recomputed)
    stored_branch = data.get("branch") or {}
    if stored_branch.get("id") != expected_branch["id"]:
        problems.append("the branch does not re-derive from the gates")
    if stored_branch.get("id") not in BRANCH_ORDER:
        problems.append("the branch is not one of the registered four")
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="§81: what the read can address once norms are gone"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=REPO_ROOT / "data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json",
    )
    parser.add_argument(
        "--anchor", type=Path, default=REPO_ROOT / "data/pantry_stage/address80/k2.json"
    )
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--null-draws", type=int, default=NULL_DRAWS)
    parser.add_argument("--check", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.check is not None:
        problems = check(args.check)
        if problems:
            print("§81 check FAIL")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print("§81 check OK")
        return 0

    outcome = run(args.report, args.anchor, device=args.device, draws=int(args.null_draws))
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(outcome, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.json or args.out is None:
        print(json.dumps(outcome, indent=1, ensure_ascii=False, sort_keys=True))
    else:
        print(f"branch: {outcome['branch']['id']}")
        print(f"seconds: {outcome['seconds']}")
        print(f"report: {args.out}")
    return 0


ADDRESS = load_address80()

if __name__ == "__main__":
    raise SystemExit(main())
