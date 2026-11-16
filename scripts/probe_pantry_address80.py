#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§80: does the store's own read address the entry the question needs?

Why this exists
---------------
§79 measured what **one entry** carries when it is read by a probe fitted per
entry: the entry carries its own name (0.9350 on held-out) and its own colour
(0.6200).  That is a property of the *write*, measured with a probe that is told
which entry to look at.  It says nothing about the read the model actually
performs at the question turn.

The model's own read is content-addressed:

    scores  = k . (W_q h)                      # one score per slot
    weights = softmax(exp(log_read_scale) * scores)
    r       = weights @ v

with ``h`` the state of the token being processed and ``k``/``v`` the store.  At
the question turn the state is the recurrence's compression of the whole
session, and the store is the boundary **before** that turn.  The question can
only be answered if this read puts its mass on the roster entry that pairs the
evidence colour with the culprit's name.

This stage measures exactly that on the frozen §77 **treatment** carrier:

* for every held-out session, take the store at the boundary before the question
  turn (the roster turn wrote slots 1 and 2, the evidence turn wrote slot 3),
  replay the question turn from that boundary, and take the last token's ``h``;
* compute the model's own attention over all 16 slots;
* the scored cell is a **two-way forced choice**: the attention mass on the
  roster entry whose colour matches the evidence (``correct``) must exceed the
  mass on the other roster entry (``partner``); chance 0.5;
* the mechanism control (``SW``) uses the corpus's own order-augmented twins
  (train only: held-out has no twins): same question, swapped roster order, so
  the needed entry moves from slot 1 to slot 2.  A read that follows the content
  moves with it; a read fixed to a slot does not.

What this is not
----------------
Not a capability score (core stays 0.00/10), not a retraining, not a threshold
change, not a new readout family, not a probe fitted on the answer.  ``A`` is
read off the model's own softmax, with no fitted parameters.

Why no decode cell on the culprit name
--------------------------------------
A cell of the form "decode the culprit's name from the roster side" would be
uninterpretable on this corpus: of 600 sessions there are only **378 distinct
full roster mappings** and **367 of those 378** have a single culprit (97.1 %),
so the mapping alone determines the answer for ~97 % of sessions.  A probe on
the roster-side value predicts the culprit at **0.9533** (train-only 5-fold)
while the same probe cannot recover the evidence colour (**0.1133** against
chance 0.125).  That route is mapping memory, not composition, so §80 registers
no such cell; the only scored cell is the attention's two-way choice.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_address80.py \\
        --report data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json \\
        --out data/pantry_stage/address80/k2.json

    ./.venv/bin/python scripts/probe_pantry_address80.py --check data/pantry_stage/address80/k2.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
PAIR79 = REPO_ROOT / "scripts" / "probe_pantry_pair79.py"
COMPOSITION = REPO_ROOT / "scripts" / "probe_pantry_composition.py"
SPLIT75 = REPO_ROOT / "scripts" / "probe_pantry_split75.py"
FAMILIES = REPO_ROOT / "scripts" / "probe_pantry_families.py"
BOUNDARIES = REPO_ROOT / "scripts" / "probe_pantry_boundaries.py"
CONTENTS = REPO_ROOT / "scripts" / "probe_pantry_contents.py"
READOUT = REPO_ROOT / "scripts" / "probe_pantry_readout.py"

# §80.4, written before the scored run.  Reused from §79 where the object is the
# same (one carrier, one readout budget, one null convention).
PROBE_STEPS = 2000
PROBE_BATCH = 64
PROBE_LR = 1e-3
PROBE_WEIGHT_DECAY = 1e-4
PROBE_SEED = 20261121
NULL_DRAWS = 400
NULL_SEED = 20261125
ALPHA = 0.005
FORCED_FLOOR = 0.50
SW_SLOT_FLOOR = 0.01
ENTRY_COVERAGE = 0.99
ENTRY_COSINE = 0.999
BRIDGE_TOLERANCE = 1e-9
ROSTER_ITEMS = 2
READ_BATCH = 32
# §77's stored treatment cells; the frozen carrier must reproduce them from this
# stage's own extraction (the same anchor §79 used).
REFERENCE = {
    "in_sample": {"exact": 0.72, "overlap": 1.72},
    "heldout": {"exact": 0.55, "overlap": 1.52},
    "leave_roster_out": {"exact": 0.43, "overlap": 1.4225},
}
STAGE = "§80 does the store's own read at the question turn address the entry the question needs?"
BRANCH_ORDER = (
    "E0-instrument",
    "H3-read-addresses",
    "H1-read-ignores-query",
    "H2-read-uses-query-but-wrong",
)


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_pair79() -> Any:
    """§79's module: the entry extraction, the alignment and the §77 bridge."""
    module = _load("pantry_address80_pair79", PAIR79)
    for name, expected in (
        ("PROBE_STEPS", PROBE_STEPS),
        ("PROBE_BATCH", PROBE_BATCH),
        ("PROBE_LR", PROBE_LR),
        ("PROBE_WEIGHT_DECAY", PROBE_WEIGHT_DECAY),
        ("PROBE_SEED", PROBE_SEED),
        ("NULL_DRAWS", NULL_DRAWS),
        ("NULL_SEED", NULL_SEED),
        ("ALPHA", ALPHA),
        ("FORCED_FLOOR", FORCED_FLOOR),
        ("ENTRY_COVERAGE", ENTRY_COVERAGE),
        ("ENTRY_COSINE", ENTRY_COSINE),
        ("BRIDGE_TOLERANCE", BRIDGE_TOLERANCE),
        ("ROSTER_ITEMS", ROSTER_ITEMS),
    ):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(
                f"§80 was registered against {name}={expected}, §79 now has {actual}; "
                "the two stages no longer share a criterion"
            )
    if tuple(module.REFERENCE) != tuple(REFERENCE):  # type: ignore[attr-defined]
        raise SystemExit("§80's §77 anchor is not the one §79 registers")
    return module


def load_composition() -> Any:
    module = _load("pantry_address80_composition", COMPOSITION)
    for name, expected in (("NULL_DRAWS", NULL_DRAWS), ("ALPHA", ALPHA), ("NULL_SEED", NULL_SEED)):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(
                f"§80 was registered against {name}={expected}, §74 now has {actual}; "
                "the stages no longer share a criterion"
            )
    return module


def load_split75() -> Any:
    module = _load("pantry_address80_split75", SPLIT75)
    for name, expected in (("NULL_DRAWS", NULL_DRAWS), ("ALPHA", ALPHA)):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(f"§80 was registered against {name}={expected}, §75 now has {actual}")
    return module


def load_families() -> Any:
    return _load("pantry_address80_families", FAMILIES)


def load_boundaries() -> Any:
    module = _load("pantry_address80_boundaries", BOUNDARIES)
    for name, expected in (
        ("PROBE_STEPS", PROBE_STEPS),
        ("PROBE_BATCH", PROBE_BATCH),
        ("PROBE_LR", PROBE_LR),
        ("PROBE_WEIGHT_DECAY", PROBE_WEIGHT_DECAY),
        ("PROBE_SEED", PROBE_SEED),
    ):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(
                f"§80 was registered against {name}={expected}, §69 now has {actual}; "
                "the probe is not the one this stage registered"
            )
    return module


def load_contents() -> Any:
    return _load("pantry_address80_contents", CONTENTS)


def load_readout() -> Any:
    return _load("pantry_address80_readout", READOUT)


# --------------------------------------------------------------------------- #
# the read: the model's own softmax at the question turn
# --------------------------------------------------------------------------- #
def seen_value(session: Dict[str, Any]) -> str:
    """The evidence turn's colour key, from the corpus's own ``seen`` assert."""
    evidence = int(session["session_meta"]["evidence_turn"])
    for item in session["turns"][evidence].get("asserts") or []:
        if item.get("kind") == "seen":
            return str(item["value"])
    raise SystemExit(f"{session['session_id']}: evidence turn has no 'seen' assert")


def roster_slots(
    trainer: Any, tokens: Sequence[Sequence[int]], roster: int, slots: int
) -> List[int]:
    """The roster items' slots: ``counter + i``, ``counter`` = items written before."""
    counter = sum(len(trainer.item_end_positions(tokens[turn])) for turn in range(roster))
    if counter + ROSTER_ITEMS > int(slots):
        raise SystemExit(
            f"the roster turn would write past the store: {counter}+{ROSTER_ITEMS} > {slots}"
        )
    return [counter + item for item in range(ROSTER_ITEMS)]


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
    """One record per session: the model's own attention at the question turn.

    The store is the boundary **before** the question turn (``snapshots[q-1]``,
    the state after the evidence turn).  The question turn's last token is
    replayed from that boundary exactly as ``run_session`` advances it, then the
    softmax over ``exp(log_read_scale) * k . query_proj(h)`` is the read.
    """
    torch = core._torch
    name_index = {name: i for i, name in enumerate(names)}
    colour_index = {colour: i for i, colour in enumerate(colours)}
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
                roster = int(session["session_meta"]["roster_turn"])
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
                seen = seen_value(session)
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
                store_keys = before["k"][index]
                store_values = before["v"][index]
                query = core.query_proj(h_final.reshape(1, -1)).reshape(-1)
                scores = store_keys @ query
                weights = torch.softmax(torch.exp(core.log_read_scale) * scores, dim=-1)
                slots = roster_slots(trainer, turns[index], roster, int(core.slots))
                record = {
                    "session_id": session["session_id"],
                    "structure": str(
                        session["session_meta"].get("order_augmented_of") or session["session_id"]
                    ),
                    "twin": bool(session["session_meta"].get("order_augmented_of")),
                    "item": int(item),
                    "slots": [int(slot) for slot in slots],
                    "weights": weights.detach().clone(),
                    "query": query.detach().clone(),
                    "h": h_final.detach().clone(),
                    "r": (weights @ store_values).reshape(-1).detach().clone(),
                    "v_roster": torch.stack([store_values[slot].reshape(-1) for slot in slots])
                    .detach()
                    .clone(),
                    "key_norms": [round(float(store_keys[slot].norm()), 6) for slot in slots],
                    "roster_mass": round(float(weights[slots].sum()), 6),
                    "argmax": int(torch.argmax(weights)),
                    "name": name_index[str(pairs[item][1])],
                    "partner_name": name_index[str(pairs[1 - item][1])],
                    "colour": colour_index[str(pairs[item][0])],
                    "evidence_colour": colour_index[seen],
                }
                records.append(record)
    return records


# --------------------------------------------------------------------------- #
# instrument: the roster writes are still the ones at the read boundary
# --------------------------------------------------------------------------- #
def _stat(values: Sequence[float]) -> Dict[str, float]:
    ordered = sorted(values)
    if not ordered:
        return {"min": 0.0, "median": 0.0, "max": 0.0}
    return {
        "min": round(ordered[0], 6),
        "median": round(ordered[len(ordered) // 2], 6),
        "max": round(ordered[-1], 6),
    }


def read_audit(
    torch: Any, records: Sequence[Dict[str, Any]], entries: Sequence[Dict[str, Any]]
) -> Dict[str, Any]:
    """Every roster slot read at the question turn still holds §79's entry."""
    cosine = torch.nn.functional.cosine_similarity
    by_session: Dict[str, Dict[int, Dict[str, Any]]] = {}
    for entry in entries:
        by_session.setdefault(str(entry["session_id"]), {})[int(entry["slot"])] = entry
    landed = 0
    cosines: List[float] = []
    failures: List[Dict[str, Any]] = []
    for record in records:
        problems: List[str] = []
        available = by_session.get(str(record["session_id"])) or {}
        slots = list(record["slots"])
        if len(set(slots)) != len(slots):
            problems.append("the two roster items share a slot")
        for index, slot in enumerate(slots):
            entry = available.get(int(slot))
            if entry is None:
                problems.append(f"no §79 entry at slot {slot}")
                continue
            value = record["v_roster"][index].reshape(1, -1)
            stored = entry["v"].reshape(1, -1)
            similarity = float(cosine(value, stored).squeeze())
            cosines.append(similarity)
            if similarity < ENTRY_COSINE:
                problems.append(f"slot {slot} value cosine {similarity:.6f}")
            if float(record["v_roster"][index].norm()) <= 0.0:
                problems.append(f"slot {slot} is empty at the read boundary")
        if problems:
            if len(failures) < 20:
                failures.append({"session_id": record["session_id"], "problems": problems})
        else:
            landed += 1
    sessions = len(records)
    return {
        "sessions": sessions,
        "landed": landed,
        "coverage": round(landed / sessions, 6) if sessions else 0.0,
        "required_coverage": ENTRY_COVERAGE,
        "required_cosine": ENTRY_COSINE,
        "cosine": _stat(cosines),
        "failures": failures,
        "pass": bool(sessions > 0 and landed / sessions >= ENTRY_COVERAGE),
    }


# --------------------------------------------------------------------------- #
# the scored cell: two-way forced choice of attention mass
# --------------------------------------------------------------------------- #
def _summary(values: Sequence[float]) -> Dict[str, float]:
    ordered = sorted(values)
    count = len(ordered)
    if count == 0:
        return {"mean": 0.0, "sd": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0, "p99": 0.0}
    mean = sum(ordered) / count
    spread = math.sqrt(sum((value - mean) ** 2 for value in ordered) / max(count, 1))

    def quantile(q: float) -> float:
        return ordered[min(count - 1, max(0, int(round(q * (count - 1)))))]

    return {
        "mean": round(mean, 6),
        "sd": round(spread, 6),
        "min": round(ordered[0], 6) if ordered else 0.0,
        "max": round(ordered[-1], 6) if ordered else 0.0,
        "p95": round(quantile(0.95), 6),
        "p99": round(quantile(0.99), 6),
    }


def _masses(torch: Any, records: Sequence[Dict[str, Any]]) -> Tuple[Any, Any, Any]:
    first = torch.as_tensor(
        [float(record["weights"][record["slots"][0]]) for record in records], dtype=torch.float32
    )
    second = torch.as_tensor(
        [float(record["weights"][record["slots"][1]]) for record in records], dtype=torch.float32
    )
    items = torch.as_tensor([int(record["item"]) for record in records], dtype=torch.long)
    return first, second, items


def address_block(
    torch: Any,
    split75: Any,
    composition: Any,
    records: Sequence[Dict[str, Any]],
    *,
    draws: int = NULL_DRAWS,
) -> Dict[str, Any]:
    """The model's own attention must put more mass on the needed roster entry."""
    first, second, items = _masses(torch, records)
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
    for record in records:
        key = str(int(record["argmax"]))
        hist[key] = hist.get(key, 0) + 1
    return {
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
            "forced": _summary([float(value) / max(n, 1) for value in null_wins]),
        },
        "chance": {"forced": FORCED_FLOOR},
        "m0": [round(float(value), 9) for value in first.tolist()],
        "m1": [round(float(value), 9) for value in second.tolist()],
        "items": [int(value) for value in items.tolist()],
        "roster_mass": _summary([float(record["roster_mass"]) for record in records]),
        "argmax_hist": hist,
        "argmax_on_roster": round(
            sum(1 for record in records if int(record["argmax"]) in record["slots"]) / max(n, 1), 6
        ),
        "key_norms": {
            "slot_first": _stat([float(record["key_norms"][0]) for record in records]),
            "slot_second": _stat([float(record["key_norms"][1]) for record in records]),
        },
        "reading": (
            "the model's own softmax at the question turn; no fitted parameters, no threshold"
        ),
    }


def swap_block(torch: Any, records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Twin pairs: same question, swapped roster order (so the needed slot flips).

    ``SW`` is the mean total-variation distance between the two twins' attention
    distributions.  A read fixed to a slot cannot move (0); a read that follows
    the needed entry has to move (near 1).
    """
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
        distance = 0.5 * float((left["weights"] - right["weights"]).abs().sum())
        distances.append(distance)
        slots = list(left["slots"])
        roster_distances.append(
            0.5
            * sum(
                abs(float(left["weights"][slot]) - float(right["weights"][slot])) for slot in slots
            )
        )
    summary = _summary(distances)
    return {
        "pairs": len(distances),
        "structures": len(groups),
        "tw": summary,
        "roster_tw": _summary(roster_distances),
        "floor": SW_SLOT_FLOOR,
        "slot_fixed": bool(distances and summary["mean"] <= SW_SLOT_FLOOR),
        "distances": [round(value, 9) for value in distances],
        "failures": failures[:10],
        "reading": (
            "mean total-variation distance between a session's attention and its twin's; the "
            "twins share the question and swap the roster order, so the needed slot flips"
        ),
    }


# --------------------------------------------------------------------------- #
# the query cell (descriptive only, no gate, no null)
# --------------------------------------------------------------------------- #
def query_probe(
    torch: Any,
    boundaries: Any,
    pair: Any,
    records: Sequence[Dict[str, Any]],
    out: int,
    *,
    folds: int = 5,
) -> Dict[str, Any]:
    """Train-only 5-fold: can a linear read of ``h_final`` name the evidence colour?"""
    features = torch.stack([record["h"] for record in records]).float()
    labels = torch.as_tensor([record["evidence_colour"] for record in records], dtype=torch.long)
    groups = sorted({str(record["structure"]) for record in records})
    bucket = {key: position % folds for position, key in enumerate(groups)}
    fold = [bucket[str(record["structure"])] for record in records]
    hits = 0
    per_fold: List[Dict[str, int]] = []
    for index in range(folds):
        train_rows = [row for row, value in enumerate(fold) if value != index]
        test_rows = [row for row, value in enumerate(fold) if value == index]
        train_index = torch.as_tensor(train_rows, dtype=torch.long)
        test_index = torch.as_tensor(test_rows, dtype=torch.long)
        mean = features[train_index].mean(dim=0, keepdim=True)
        std = features[train_index].std(dim=0, keepdim=True, unbiased=False).clamp_min(1e-6)
        logits = pair._probe_logits(
            torch,
            boundaries,
            (features[train_index] - mean) / std,
            labels[train_index],
            (features[test_index] - mean) / std,
            out,
            seed=PROBE_SEED,
        )
        correct = int((logits.argmax(dim=1) == labels[test_index]).sum())
        hits += correct
        per_fold.append({"n": len(test_rows), "correct": correct})
    return {
        "n": len(records),
        "correct": hits,
        "top1": round(hits / max(len(records), 1), 6),
        "chance": round(1.0 / out, 6),
        "folds": per_fold,
        "steps": PROBE_STEPS,
        "seed": PROBE_SEED,
        "reading": "descriptive only: a linear read of the question turn's last state",
    }


# --------------------------------------------------------------------------- #
# gates and the branch
# --------------------------------------------------------------------------- #
def gates(outcome: Dict[str, Any]) -> Dict[str, Any]:
    instrument = outcome["instrument"]
    audit = instrument["read_audit"]
    align = instrument["alignment"]
    bridge = instrument["bridge"]
    coverage = min(float(audit["train"]["coverage"]), float(audit["heldout"]["coverage"]))
    i0 = {
        "pass": bool(
            instrument["carrier_unchanged"]
            and instrument["checkpoint_unchanged"]
            and instrument["mode_matches"]
            and instrument["corpus_digests_match"]
            and align["pass"]
            and coverage >= ENTRY_COVERAGE
            and bridge["reproduced"]
        ),
        "carrier_unchanged": instrument["carrier_unchanged"],
        "checkpoint_unchanged": instrument["checkpoint_unchanged"],
        "mode_matches": instrument["mode_matches"],
        "corpus_digests_match": instrument["corpus_digests_match"],
        "alignment_pass": align["pass"],
        "read_coverage": coverage,
        "read_required_coverage": ENTRY_COVERAGE,
        "bridge_reproduced": bridge["reproduced"],
        "reading": (
            "the carrier, checkpoint and corpus are the frozen §77 ones, the item text matches "
            "its roster mapping, the roster writes are still the ones at the read boundary, and "
            "the §77 cells are reproduced from this extraction"
        ),
    }
    address = outcome["address"]
    wilson = address["wilson"]
    a_pass = bool(float(wilson["low"]) > FORCED_FLOOR and float(address["p_value"]) < ALPHA)
    swap = outcome["swap"]
    s_pass = bool(float(swap["tw"]["mean"]) <= SW_SLOT_FLOOR)
    return {
        "I0_instrument": i0,
        "A_address": {
            "pass": a_pass,
            "n": address["n"],
            "forced": address["forced"],
            "wilson_low": float(wilson["low"]),
            "p_value": address["p_value"],
            "floor": FORCED_FLOOR,
            "alpha": ALPHA,
            "reading": (
                "the model's own attention puts more mass on the roster entry that pairs the "
                "evidence colour with a name than on the other roster entry"
            ),
        },
        "S_swap": {
            "pass": s_pass,
            "swap": float(swap["tw"]["mean"]),
            "floor": SW_SLOT_FLOOR,
            "pairs": swap["pairs"],
            "reading": (
                "the twin pairs' attention moves with the needed entry (pass = it does not: a "
                "fixed-slot read)"
            ),
        },
        "reads": outcome["reads"],
    }


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """Fixed precedence, written before the run: E0 > H3 > H1 > H2."""
    if not gate["I0_instrument"]["pass"]:
        return {
            "id": "E0-instrument",
            "reading": (
                "the carrier, the corpus, the item labels, the read-boundary audit or the §77 "
                "reproduction moved; nothing is read"
            ),
            "next": "fix the instrument before asking what the read addresses",
        }
    if gate["A_address"]["pass"]:
        return {
            "id": "H3-read-addresses",
            "reading": (
                "on held-out sessions the model's own read puts more attention on the roster "
                "entry the question needs than on its partner: the store's read is addressed "
                "by the question, and §78's shortfall is downstream of the read"
            ),
            "next": (
                "register a read-to-answer cell (the read vector through the head) at the "
                "question turn, no new budget, and replicate on a second corpus seed"
            ),
        }
    if gate["S_swap"]["pass"]:
        return {
            "id": "H1-read-ignores-query",
            "reading": (
                "the read fails the two-way choice and does not move when the roster order is "
                "swapped: it is a fixed slot, not an address of the entry the question needs"
            ),
            "next": (
                "register a write-side change: make the read's key carry the roster colour at "
                "the write point, or register a query that states the evidence colour; no new "
                "budget, thresholds untouched"
            ),
        }
    return {
        "id": "H2-read-uses-query-but-wrong",
        "reading": (
            "the read fails the two-way choice but does move between twins: it addresses some "
            "store content, just not the roster entry the question needs"
        ),
        "next": (
            "measure which slot/content the read follows (key norm, recency, the evidence "
            "entry) before changing the read rule; no new budget"
        ),
    }


# --------------------------------------------------------------------------- #
# one run
# --------------------------------------------------------------------------- #
def run(
    report_path: Path,
    *,
    device: str = "cpu",
    draws: int = NULL_DRAWS,
) -> Dict[str, Any]:
    started = time.time()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§80 reads the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or 2)
    if k != ROSTER_ITEMS:
        raise SystemExit(f"§80 was registered at k={ROSTER_ITEMS}, this carrier has k={k}")
    seed = int(corpus_block.get("seed") or 0)
    if seed <= 0:
        raise SystemExit("the report does not record its corpus seed")

    pair = load_pair79()
    composition = load_composition()
    split75 = load_split75()
    families = load_families()
    boundaries = load_boundaries()
    contents = load_contents()
    probe = load_readout()
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
    display = dict(module.COLOURS)

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
    address = address_block(torch, split75, composition, held_records, draws=draws)
    swap = swap_block(torch, train_records)
    query = query_probe(torch, boundaries, pair, train_records, len(colours))
    bridge = pair.bridge_block(
        torch,
        trainer,
        contents,
        families,
        boundaries,
        composition,
        core,
        train,
        held,
        names,
        colours,
    )
    instrument = {
        "carrier": str(report_path),
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
        "corpus_digests_recorded": bool(
            corpus_block.get("train_digest") and corpus_block.get("heldout_digest")
        ),
        "corpus_digests_match": bool(
            (corpus.get("meta") or {}).get("train_digest") == corpus_block.get("train_digest")
            and (corpus.get("meta") or {}).get("heldout_digest")
            == corpus_block.get("heldout_digest")
        ),
        "alignment": {
            "train": pair.alignment(display, train),
            "heldout": pair.alignment(display, held),
        },
        "read_audit": {
            "train": read_audit(torch, train_records, train_entries),
            "heldout": read_audit(torch, held_records, held_entries),
        },
        "bridge": bridge,
    }
    instrument["alignment"]["pass"] = bool(
        instrument["alignment"]["train"]["pass"] and instrument["alignment"]["heldout"]["pass"]
    )

    outcome: Dict[str, Any] = {
        "stage": STAGE,
        "carrier_report": str(report_path),
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
            "train_structures": len({str(record["structure"]) for record in train_records}),
            "heldout_structures": len({str(record["structure"]) for record in held_records}),
            "train_twins": sum(1 for record in train_records if record["twin"]),
            "heldout_twins": sum(1 for record in held_records if record["twin"]),
        },
        "read": {
            "point": "the store at the boundary before the question turn, last question token",
            "question_turn": -1,
            "evidence_turn_offset": -2,
            "slots": "counter + i, counter = items written before the roster turn",
            "scored_split": "heldout",
            "swap_split": "train (the corpus's own order-augmented twins; held-out has none)",
        },
        "probe": {
            "steps": PROBE_STEPS,
            "batch": PROBE_BATCH,
            "lr": PROBE_LR,
            "weight_decay": PROBE_WEIGHT_DECAY,
            "seed": PROBE_SEED,
            "null_draws": draws,
            "null_seed": NULL_SEED,
            "alpha": ALPHA,
            "forced_floor": FORCED_FLOOR,
            "swap_floor": SW_SLOT_FLOOR,
            "gate_metric": "two-way forced choice of the model's own attention mass",
        },
        "reads": {
            "train": len(train_records),
            "heldout": len(held_records),
            "per_session": 1,
        },
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
    """Re-derive every gate and the branch from the stored readings."""
    problems: List[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("stage") != STAGE:
        return ["this is not a §80 report"]
    probe = data.get("probe") or {}
    for name, expected in (
        ("steps", PROBE_STEPS),
        ("seed", PROBE_SEED),
        ("null_draws", NULL_DRAWS),
        ("null_seed", NULL_SEED),
        ("alpha", ALPHA),
        ("forced_floor", FORCED_FLOOR),
        ("swap_floor", SW_SLOT_FLOOR),
    ):
        if probe.get(name) != expected:
            problems.append(f"probe.{name} is not the registered {expected!r}")
    reads = data.get("reads") or {}
    corpus = data.get("corpus") or {}
    if reads.get("train") != int(corpus.get("train_sessions") or 0):
        problems.append("the training read count is not one per session")
    if reads.get("heldout") != int(corpus.get("heldout_sessions") or 0):
        problems.append("the held-out read count is not one per session")

    instrument = data.get("instrument") or {}
    if (instrument.get("alignment") or {}).get("pass") is not True:
        problems.append("the item/label alignment did not pass")
    for split in ("train", "heldout"):
        audit = _nested(instrument, "read_audit", split) or {}
        if float(audit.get("coverage", 0.0)) < ENTRY_COVERAGE:
            problems.append(f"{split} read-boundary coverage is below {ENTRY_COVERAGE}")
    bridge = instrument.get("bridge") or {}
    actual = bridge.get("actual") or {}
    for which, expected in REFERENCE.items():
        got = actual.get(which) or {}
        for key, value in expected.items():
            if abs(float(got.get(key, -1.0)) - value) > BRIDGE_TOLERANCE:
                problems.append(f"the §77 bridge does not reproduce {which}.{key}")

    address = data.get("address") or {}
    n = int(address.get("n") or 0)
    m0 = address.get("m0") or []
    m1 = address.get("m1") or []
    items = address.get("items") or []
    if not (len(m0) == len(m1) == len(items) == n):
        problems.append("the stored masses are not one pair per read")
    else:
        wins = 0
        for left, right, item in zip(m0, m1, items):
            correct, partner = (left, right) if int(item) == 0 else (right, left)
            wins += int(float(correct) > float(partner))
        if wins != int(address.get("wins") or -1):
            problems.append("the forced-choice win count is not re-derivable")
        expected_forced = round(wins / max(n, 1), 6)
        if abs(float(address.get("forced", -1.0)) - expected_forced) > 1e-9:
            problems.append("the forced rate is not wins/n")
    null = address.get("null") or {}
    expected_p = round((1 + int(null.get("ge") or 0)) / (int(null.get("draws") or 0) + 1), 6)
    if abs(float(address.get("p_value", -1.0)) - expected_p) > 1e-9:
        problems.append("p_value is not the permutation convention")

    swap = data.get("swap") or {}
    distances = swap.get("distances") or []
    if distances:
        expected_mean = round(sum(float(value) for value in distances) / len(distances), 6)
        got_mean = float((swap.get("tw") or {}).get("mean", -1.0))
        if abs(got_mean - expected_mean) > 1e-9:
            problems.append("the swap distance is not the mean of its pairs")
        if int(swap.get("pairs") or 0) != len(distances):
            problems.append("the swap pair count does not match its distances")

    recomputed = gates(data)
    stored = data.get("gates") or {}
    for key in ("I0_instrument", "A_address", "S_swap"):
        if bool((stored.get(key) or {}).get("pass")) != bool(recomputed[key]["pass"]):
            problems.append(f"gate {key} does not re-derive")
    expected_branch = branch(recomputed)
    stored_branch = data.get("branch") or {}
    if stored_branch.get("id") != expected_branch["id"]:
        problems.append("the branch does not re-derive from the gates")
    if stored_branch.get("id") not in BRANCH_ORDER:
        problems.append("the branch is not one of the registered four")
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="§80: what the model's own read addresses")
    parser.add_argument(
        "--report",
        type=Path,
        default=REPO_ROOT / "data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json",
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
            print("§80 check FAIL")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print("§80 check OK")
        return 0

    outcome = run(args.report, device=args.device, draws=int(args.null_draws))
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


if __name__ == "__main__":
    raise SystemExit(main())
