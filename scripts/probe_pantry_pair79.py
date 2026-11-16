#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§79: what one item's entry carries - the value -> name pair inside one write.

Why this exists
---------------
§78 matched the readout's in-sample fit across §77's two frozen carriers and
still found the per-item store ahead (leave-roster-out overlap +0.1775) but
below the registered composition floor (1.2650 < 1.5).  Its verdict named the
next question without answering it (§78.20): the write stores
``sigmoid(write_gate(h_item)) * value_proj(h_item)`` per item, but *whether the
entry carries the item's own name* was never measured - only inferred from a
readout that pools the whole store.

This stage measures it directly, on the frozen §77 **treatment** carrier, with
no retraining and no new budget:

* for every roster item, the entry is the stored value ``v`` at the item's own
  slot (and, as a diagnostic, the stored key ``k`` and the write state ``h``);
* a linear probe is fit on the **training** sessions' entries to name the
  entry's own name (12-way) and its own colour (8-way, the roster's value);
* the scored cell is the **held-out** sessions' entries, with a within-session
  two-way forced choice: the entry's own name must score above the name paired
  with the *other* item of the same session (chance 0.5).

The positive control is the colour: if the name is readable but the colour is
not, the entry kept the owner and dropped the key; if the colour is readable
and the name is not, the entry kept the key and dropped the owner.  That is the
difference between "the write binds the pair" and "the write binds one half".

What this is not
----------------
Not a capability score (core stays 0.00/10), not a new readout family, not a
retraining, not a threshold change.  The carrier, the corpus, the probe seed,
the step budget and the null are §69/§74/§77's; the only new object is the
per-entry label, taken from the roster assert the corpus already states.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_pair79.py \\
        --report data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json \\
        --out data/pantry_stage/pair79/k2.json

    ./.venv/bin/python scripts/probe_pantry_pair79.py --check data/pantry_stage/pair79/k2.json
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
COMPOSITION = REPO_ROOT / "scripts" / "probe_pantry_composition.py"
SPLIT75 = REPO_ROOT / "scripts" / "probe_pantry_split75.py"
FAMILIES = REPO_ROOT / "scripts" / "probe_pantry_families.py"
BOUNDARIES = REPO_ROOT / "scripts" / "probe_pantry_boundaries.py"
CONTENTS = REPO_ROOT / "scripts" / "probe_pantry_contents.py"
READOUT = REPO_ROOT / "scripts" / "probe_pantry_readout.py"

# §79.4, written before the scored run.
FEATURES = ("v", "k", "h")
PRIMARY_FEATURE = "v"
PROBE_STEPS = 2000
PROBE_BATCH = 64
PROBE_LR = 1e-3
PROBE_WEIGHT_DECAY = 1e-4
PROBE_SEED = 20261121
NULL_DRAWS = 400
NULL_SEED = 20261125
ALPHA = 0.005
FORCED_FLOOR = 0.50
ENTRY_COVERAGE = 0.99
ENTRY_COSINE = 0.999
BRIDGE_TOLERANCE = 1e-9
ROSTER_ITEMS = 2
# §77's stored treatment cells (`data/pantry_stage/item77/k2.json`); the frozen
# carrier must reproduce them from this stage's own extraction.
REFERENCE = {
    "in_sample": {"exact": 0.72, "overlap": 1.72},
    "heldout": {"exact": 0.55, "overlap": 1.52},
    "leave_roster_out": {"exact": 0.43, "overlap": 1.4225},
}
STAGE = "§79 what one item's entry carries: the value-to-name pair inside one write"
BRANCH_ORDER = (
    "E0-instrument",
    "D1-entry-carries-owner",
    "D4-owner-only",
    "D2-key-only",
    "D3-entry-lacks-owner",
)
TARGETS = ("name", "colour")


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_composition() -> Any:
    """§74's module: one copy of the null permutation and the set reading."""
    module = _load("pantry_pair79_composition", COMPOSITION)
    for name, expected in (("NULL_DRAWS", NULL_DRAWS), ("ALPHA", ALPHA), ("NULL_SEED", NULL_SEED)):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(
                f"§79 was registered against {name}={expected}, §74 now has {actual}; "
                "the stages no longer share a criterion"
            )
    return module


def load_split75() -> Any:
    """§75's module: the Wilson interval used by every later stage."""
    module = _load("pantry_pair79_split75", SPLIT75)
    for name, expected in (("NULL_DRAWS", NULL_DRAWS), ("ALPHA", ALPHA)):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(f"§79 was registered against {name}={expected}, §75 now has {actual}")
    return module


def load_families() -> Any:
    return _load("pantry_pair79_families", FAMILIES)


def load_boundaries() -> Any:
    module = _load("pantry_pair79_boundaries", BOUNDARIES)
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
                f"§79 was registered against {name}={expected}, §69 now has {actual}; "
                "the probe is not the one this stage registered"
            )
    return module


def load_contents() -> Any:
    return _load("pantry_pair79_contents", CONTENTS)


def load_readout() -> Any:
    return _load("pantry_pair79_readout", READOUT)


# --------------------------------------------------------------------------- #
# the corpus: one item, one entry, one label
# --------------------------------------------------------------------------- #
def roster_mapping(session: Dict[str, Any]) -> List[Tuple[str, str]]:
    """The roster turn's ``value -> name`` pairs in the order the text states them."""
    turn = int(session["session_meta"]["roster_turn"])
    for item in session["turns"][turn]["asserts"]:
        if item.get("kind") == "roster":
            return [(str(key), str(name)) for key, name in item["value"].items()]
    raise SystemExit(f"{session['session_id']}: roster turn has no roster assert")


def _replay_turn(trainer: Any, core: Any, tokens: Sequence[int], hidden: Any) -> List[Any]:
    """The turn's per-token states, computed the way ``_run_turn`` computes them."""
    torch = core._torch
    states: List[Any] = []
    h = hidden
    for token in tokens:
        feed = torch.as_tensor([int(token)], dtype=torch.long, device=h.device)
        h = core.cell(core.embedding(feed), h)
        states.append(h)
    return states


def entry_records(
    trainer: Any,
    probe: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    names: Sequence[str],
    colours: Sequence[str],
    *,
    batch: int = 64,
) -> List[Dict[str, Any]]:
    """One record per roster item: its own write state, its stored entry, its labels.

    The store is replayed exactly as ``run_session`` wrote it: ``snapshots`` are
    the boundaries after each turn (write included), and the roster turn's
    per-token states are recomputed from the boundary before it, because the
    item plan indexes *that* turn's states.
    """
    torch = core._torch
    cosine = torch.nn.functional.cosine_similarity
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
                roster = int(session["session_meta"]["roster_turn"])
                pairs = roster_mapping(session)
                if len(pairs) != ROSTER_ITEMS:
                    raise SystemExit(
                        f"{session['session_id']}: {len(pairs)} roster items, "
                        f"registered {ROSTER_ITEMS}"
                    )
                before = snapshots[roster - 1] if roster > 0 else core.init_state(1).tensors
                state = core.init_state(len(chunk))
                state.tensors = {name: value for name, value in before.items()}
                delta = torch.as_tensor(
                    [gap[roster] for gap in gaps],
                    dtype=before["h"].dtype,
                    device=before["h"].device,
                )
                hidden = core.al_step(delta, state).tensors["h"][index : index + 1]
                stacked = _replay_turn(trainer, core, turns[index][roster], hidden)
                store = snapshots[roster]
                positions = trainer.item_end_positions(turns[index][roster])
                if len(positions) != ROSTER_ITEMS:
                    raise SystemExit(f"{session['session_id']}: {len(positions)} item positions")
                counter = sum(
                    len(trainer.item_end_positions(turns[index][turn])) for turn in range(roster)
                )
                slots = [(counter + item) % int(core.slots) for item in range(ROSTER_ITEMS)]
                if len(set(slots)) != len(slots):
                    raise SystemExit(f"{session['session_id']}: roster items reuse a slot")
                for item, (position, slot) in enumerate(zip(positions, slots)):
                    state_item = stacked[position]
                    strength = torch.sigmoid(core.write_gate(state_item))
                    expected_value = strength * core.value_proj(state_item)
                    expected_key = strength * core.key_proj(state_item)
                    stored_value = store["v"][index, slot].reshape(1, -1)
                    stored_key = store["k"][index, slot].reshape(1, -1)
                    records.append(
                        {
                            "session_id": session["session_id"],
                            "structure": str(
                                session["session_meta"].get("order_augmented_of")
                                or session["session_id"]
                            ),
                            "position": item,
                            "slot": int(slot),
                            "gate": round(float(strength.reshape(-1)[0]), 6),
                            "norm_v": round(float(stored_value.norm()), 6),
                            "cos_v": round(
                                float(cosine(stored_value, expected_value).squeeze()), 6
                            ),
                            "cos_k": round(float(cosine(stored_key, expected_key).squeeze()), 6),
                            "h": state_item.reshape(-1).detach().clone(),
                            "v": stored_value.reshape(-1).detach().clone(),
                            "k": stored_key.reshape(-1).detach().clone(),
                            "name": name_index[str(pairs[item][1])],
                            "colour": colour_index[str(pairs[item][0])],
                            "partner": name_index[str(pairs[1 - item][1])],
                            "partner_colour": colour_index[str(pairs[1 - item][0])],
                        }
                    )
    return records


def alignment(display: Dict[str, str], sessions: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """The item text really names the mapped value and person, in the same order.

    This is the label-side instrument: if the i-th item's text does not contain
    the i-th mapping's display word and name, the item -> label correspondence is
    wrong and every readout below would be uninterpretable.
    """
    bad: List[Dict[str, Any]] = []
    total = 0
    for session in sessions:
        roster = int(session["session_meta"]["roster_turn"])
        pairs = roster_mapping(session)
        text = str(session["turns"][roster]["user_input"])
        body = text.split("：", 1)[1] if "：" in text else text
        parts = [part for part in body.replace("。", "").split("、") if part]
        total += 1
        if len(parts) != len(pairs):
            bad.append(
                {"session_id": session["session_id"], "problem": "item count", "parts": len(parts)}
            )
            continue
        for part, (key, name) in zip(parts, pairs):
            word = display.get(key, key)
            if word not in part or name not in part:
                bad.append(
                    {
                        "session_id": session["session_id"],
                        "problem": "text",
                        "item": part,
                        "value": key,
                        "name": name,
                    }
                )
    return {
        "sessions": total,
        "bad": len(bad),
        "pass": bool(total > 0 and not bad),
        "failures": bad[:10],
    }


def audit_block(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """``M_landed``-style: every entry is the write the rule says it is."""
    if not records:
        return {"entries": 0, "coverage": 0.0, "pass": False}
    by_session: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        by_session.setdefault(str(record["session_id"]), []).append(record)
    landed = 0
    failures: List[Dict[str, Any]] = []
    for session_id, entries in by_session.items():
        problems = []
        if len(entries) != ROSTER_ITEMS:
            problems.append(f"{len(entries)} entries, registered {ROSTER_ITEMS}")
        if len({entry["slot"] for entry in entries}) != len(entries):
            problems.append("entries reuse a slot")
        for entry in entries:
            if entry["norm_v"] <= 0.0:
                problems.append(f"slot {entry['slot']} is empty")
            if entry["cos_v"] < ENTRY_COSINE:
                problems.append(f"slot {entry['slot']} value cosine {entry['cos_v']:.6f}")
            if entry["cos_k"] < ENTRY_COSINE:
                problems.append(f"slot {entry['slot']} key cosine {entry['cos_k']:.6f}")
        if problems:
            if len(failures) < 20:
                failures.append({"session_id": session_id, "problems": problems})
        else:
            landed += 1

    def stat(values: Sequence[float]) -> Dict[str, float]:
        ordered = sorted(values)
        return {
            "min": round(ordered[0], 6),
            "median": round(ordered[len(ordered) // 2], 6),
            "max": round(ordered[-1], 6),
        }

    sessions = len(by_session)
    return {
        "entries": len(records),
        "sessions": sessions,
        "landed": landed,
        "coverage": round(landed / sessions, 6),
        "required_coverage": ENTRY_COVERAGE,
        "required_cosine": ENTRY_COSINE,
        "value_cosine": stat([entry["cos_v"] for entry in records]),
        "key_cosine": stat([entry["cos_k"] for entry in records]),
        "gate": stat([entry["gate"] for entry in records]),
        "value_norm": stat([entry["norm_v"] for entry in records]),
        "failures": failures,
        "pass": bool(sessions > 0 and landed / sessions >= ENTRY_COVERAGE),
    }


# --------------------------------------------------------------------------- #
# one readout: fit on training entries, force a choice on held-out entries
# --------------------------------------------------------------------------- #
def _probe_logits(
    torch: Any,
    boundaries: Any,
    train_x: Any,
    train_y: Any,
    eval_x: Any,
    out: int,
    *,
    seed: int,
) -> Any:
    probe = boundaries.build_probe(torch, int(train_x.shape[1]), int(out), seed)
    boundaries.fit_probe(
        torch,
        probe,
        train_x,
        train_y,
        kind="label",
        slots=0,
        steps=PROBE_STEPS,
        batch=PROBE_BATCH,
        lr=PROBE_LR,
        weight_decay=PROBE_WEIGHT_DECAY,
        seed=seed,
    )
    return boundaries.predict_probe(torch, probe, eval_x)


def permutation_p(ge: int, draws: int) -> float:
    """The §74 convention: ``(1 + #{null >= observed}) / (draws + 1)``."""
    return round((1 + int(ge)) / (int(draws) + 1), 6)


def forced_block(torch: Any, split75: Any, logits: Any, own: Any, partner: Any) -> Dict[str, Any]:
    """The entry's own label must beat the label paired with the other item."""
    n = int(own.numel())
    rows = torch.arange(n, device=own.device)
    forced_correct = int((logits[rows, own] > logits[rows, partner]).sum())
    top1_correct = int((logits.argmax(dim=1) == own).sum())
    top2 = logits.topk(2, dim=1).indices
    own_top2 = int((top2 == own.view(-1, 1)).any(dim=1).sum())
    partner_top2 = int((top2 == partner.view(-1, 1)).any(dim=1).sum())
    return {
        "n": n,
        "forced_correct": forced_correct,
        "forced": round(forced_correct / max(n, 1), 6),
        "wilson": split75.wilson(forced_correct, n),
        "top1_correct": top1_correct,
        "top1": round(top1_correct / max(n, 1), 6),
        "own_top2": round(own_top2 / max(n, 1), 6),
        "partner_top2": round(partner_top2 / max(n, 1), 6),
    }


def _summary(values: Sequence[float]) -> Dict[str, float]:
    ordered = sorted(values)
    count = len(ordered)
    mean = sum(ordered) / max(count, 1)
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


def readout_block(
    torch: Any,
    boundaries: Any,
    composition: Any,
    split75: Any,
    train_x: Any,
    train_y: Any,
    eval_x: Any,
    own: Any,
    partner: Any,
    out: int,
    *,
    draws: int = NULL_DRAWS,
) -> Dict[str, Any]:
    """One target on one feature: the observed fit plus the label-permutation null."""
    mean = train_x.mean(dim=0, keepdim=True)
    std = train_x.std(dim=0, keepdim=True, unbiased=False).clamp_min(1e-6)
    fit_x = (train_x - mean) / std
    eval_z = (eval_x - mean) / std
    logits = _probe_logits(torch, boundaries, fit_x, train_y, eval_z, out, seed=PROBE_SEED)
    observed = forced_block(torch, split75, logits, own, partner)
    null_forced: List[float] = []
    null_top1: List[float] = []
    for draw in range(draws):
        shuffled = composition.permute_rows(torch, train_y, NULL_SEED + draw)
        local = _probe_logits(torch, boundaries, fit_x, shuffled, eval_z, out, seed=PROBE_SEED)
        block = forced_block(torch, split75, local, own, partner)
        null_forced.append(float(block["forced"]))
        null_top1.append(float(block["top1"]))
    ge = sum(1 for value in null_forced if value >= float(observed["forced"]) - 1e-12)
    p_value = permutation_p(ge, draws)
    return {
        "observed": observed,
        "null": {
            "draws": int(draws),
            "seed": NULL_SEED,
            "ge": int(ge),
            "forced": _summary(null_forced),
            "top1": _summary(null_top1),
        },
        "p_value": round(p_value, 6),
        "chance": {"forced": FORCED_FLOOR, "top1": round(1.0 / out, 6)},
    }


def position_block(
    torch: Any,
    boundaries: Any,
    train_x: Any,
    train_position: Any,
    eval_x: Any,
    eval_position: Any,
) -> Dict[str, Any]:
    """Descriptive only: does the entry know whether it is the first or second item?"""
    mean = train_x.mean(dim=0, keepdim=True)
    std = train_x.std(dim=0, keepdim=True, unbiased=False).clamp_min(1e-6)
    logits = _probe_logits(
        torch,
        boundaries,
        (train_x - mean) / std,
        train_position,
        (eval_x - mean) / std,
        2,
        seed=PROBE_SEED,
    )
    correct = int((logits.argmax(dim=1) == eval_position).sum())
    return {
        "n": int(eval_position.numel()),
        "correct": correct,
        "top1": round(correct / max(int(eval_position.numel()), 1), 6),
        "chance": 0.5,
        "reading": "descriptor, no gate: the terminator differs (、 vs 。), so this is expected",
    }


def readout_pass(block: Dict[str, Any], *, alpha: float = ALPHA) -> bool:
    """The registered gate: the Wilson lower bound clears chance, and so does the null."""
    observed = block.get("observed") or {}
    wilson = observed.get("wilson") or {}
    return bool(
        float(wilson.get("low", 0.0)) > FORCED_FLOOR and float(block.get("p_value", 1.0)) < alpha
    )


# --------------------------------------------------------------------------- #
# the bridge: the same extraction must reproduce §77's cells
# --------------------------------------------------------------------------- #
def bridge_block(
    torch: Any,
    trainer: Any,
    contents: Any,
    families: Any,
    boundaries: Any,
    composition: Any,
    core: Any,
    train: Sequence[Dict[str, Any]],
    held: Sequence[Dict[str, Any]],
    names: Sequence[str],
    colours: Sequence[str],
) -> Dict[str, Any]:
    """§77's ``linear_values`` observed cells, recomputed from this stage's reads."""
    indexes = boundaries.shared_boundaries(list(train))
    boundaries.shared_boundaries(list(held))
    train_views = families.boundary_features(trainer, contents, core, train, indexes["roster"])
    held_views = families.boundary_features(trainer, contents, core, held, indexes["roster"])
    train_x, held_x = contents.standardise(
        families.feature_view("linear_values", train_views),
        families.feature_view("linear_values", held_views),
    )
    train_x = families.transform("linear_values", train_x)
    held_x = families.transform("linear_values", held_x)
    train_targets = boundaries.targets(train, names, colours, contents)
    held_targets = boundaries.targets(held, names, colours, contents)
    y_train = torch.as_tensor([list(row) for row in train_targets["roster"]], dtype=torch.float32)
    y_held = torch.as_tensor([list(row) for row in held_targets["roster"]], dtype=torch.float32)
    fitted = composition.fit_and_predict(
        boundaries, torch, train_x, y_train, out=len(names), slots=2, seed=boundaries.PROBE_SEED
    )
    in_sample = composition.score_set(boundaries.predict_probe(torch, fitted, train_x), y_train, 2)
    heldout = composition.score_set(boundaries.predict_probe(torch, fitted, held_x), y_held, 2)

    rosters = families.roster_keys(list(train))
    groups: Dict[Tuple[str, ...], List[int]] = {}
    for row, key in enumerate(rosters):
        groups.setdefault(tuple(key), []).append(row)
    predictions: List[Any] = []
    order: List[int] = []
    for key in sorted(groups):
        held_rows = groups[key]
        kept = set(held_rows)
        train_rows = [row for row in range(len(rosters)) if row not in kept]
        train_index = torch.as_tensor(train_rows, dtype=torch.long)
        held_index = torch.as_tensor(held_rows, dtype=torch.long)
        fold = composition.fit_and_predict(
            boundaries,
            torch,
            train_x[train_index],
            y_train[train_index],
            out=len(names),
            slots=2,
            seed=boundaries.PROBE_SEED,
        )
        predictions.append(boundaries.predict_probe(torch, fold, train_x[held_index]))
        order.extend(held_rows)
    pooled = torch.cat(predictions, dim=0)
    labels = y_train[torch.as_tensor(order, dtype=torch.long)]
    leave_roster_out = composition.score_set(pooled, labels, 2)

    def cells(block: Dict[str, Any]) -> Dict[str, float]:
        return {"exact": float(block["exact"]), "overlap": float(block["overlap"])}

    actual = {
        "in_sample": cells(in_sample),
        "heldout": cells(heldout),
        "leave_roster_out": cells(leave_roster_out),
    }
    equal = {
        name: bool(
            abs(actual[name]["exact"] - REFERENCE[name]["exact"]) <= BRIDGE_TOLERANCE
            and abs(actual[name]["overlap"] - REFERENCE[name]["overlap"]) <= BRIDGE_TOLERANCE
        )
        for name in REFERENCE
    }
    return {
        "reference": REFERENCE,
        "actual": actual,
        "equal": equal,
        "reproduced": bool(all(equal.values())),
        "tolerance": BRIDGE_TOLERANCE,
        "reading": (
            "the frozen carrier's §77 linear_values cells, recomputed with this stage's own "
            "extraction; if they move, the per-entry reads are not reading the frozen store"
        ),
    }


# --------------------------------------------------------------------------- #
# gates and the branch
# --------------------------------------------------------------------------- #
def gates(outcome: Dict[str, Any]) -> Dict[str, Any]:
    instrument = outcome["instrument"]
    entry = instrument["entry_audit"]
    align = instrument["alignment"]
    bridge = instrument["bridge"]
    entry_coverage = min(float(entry["train"]["coverage"]), float(entry["heldout"]["coverage"]))
    i0 = {
        "pass": bool(
            instrument["carrier_unchanged"]
            and instrument["checkpoint_unchanged"]
            and instrument["mode_matches"]
            and instrument["corpus_digests_match"]
            and align["pass"]
            and entry_coverage >= ENTRY_COVERAGE
            and bridge["reproduced"]
        ),
        "carrier_unchanged": instrument["carrier_unchanged"],
        "checkpoint_unchanged": instrument["checkpoint_unchanged"],
        "mode_matches": instrument["mode_matches"],
        "corpus_digests_match": instrument["corpus_digests_match"],
        "alignment_pass": align["pass"],
        "entry_coverage": entry_coverage,
        "entry_required_coverage": ENTRY_COVERAGE,
        "bridge_reproduced": bridge["reproduced"],
        "reading": (
            "the carrier, checkpoint and corpus are the frozen §77 ones, the item text matches "
            "its roster mapping, every entry is the registered write, and the §77 cells are "
            "reproduced from this extraction"
        ),
    }
    readouts = outcome["readouts"]
    primary = readouts[PRIMARY_FEATURE]
    name = {
        "pass": readout_pass(primary["name"]),
        "feature": PRIMARY_FEATURE,
        "forced": primary["name"]["observed"]["forced"],
        "wilson_low": primary["name"]["observed"]["wilson"]["low"],
        "p_value": primary["name"]["p_value"],
        "n": primary["name"]["observed"]["n"],
        "floor": FORCED_FLOOR,
        "alpha": ALPHA,
        "reading": (
            "the stored value's own name beats the name paired with the other item of the "
            "same session, on held-out entries"
        ),
    }
    colour = {
        "pass": readout_pass(primary["colour"]),
        "feature": PRIMARY_FEATURE,
        "forced": primary["colour"]["observed"]["forced"],
        "wilson_low": primary["colour"]["observed"]["wilson"]["low"],
        "p_value": primary["colour"]["p_value"],
        "n": primary["colour"]["observed"]["n"],
        "floor": FORCED_FLOOR,
        "alpha": ALPHA,
        "reading": (
            "the stored value's own colour beats the colour paired with the other item of the "
            "same session, on held-out entries; the positive control for the pairing"
        ),
    }
    return {
        "I0_instrument": i0,
        "P_name": name,
        "P_colour": colour,
        "entry_counts": outcome["entries"],
    }


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """Fixed precedence, written before the run: E0 > D1 > D4 > D2 > D3."""
    if not gate["I0_instrument"]["pass"]:
        return {
            "id": "E0-instrument",
            "reading": (
                "the carrier, the corpus, the item labels, the entry audit or the §77 "
                "reproduction moved; nothing is read"
            ),
            "next": "fix the instrument before asking what the entry carries",
        }
    name = gate["P_name"]["pass"]
    colour = gate["P_colour"]["pass"]
    if name and colour:
        return {
            "id": "D1-entry-carries-owner",
            "reading": (
                "one entry carries its own name and its own colour on held-out sessions: the "
                "write does bind the pair, so §78's shortfall is in the readout/aggregation, "
                "not in what the entry holds"
            ),
            "next": (
                "register a slot-addressed readout that pairs each entry's key with its own "
                "value (no new budget), and replicate on a second corpus seed before any "
                "binding claim"
            ),
        }
    if name and not colour:
        return {
            "id": "D4-owner-only",
            "reading": (
                "one entry carries its own name but not its own colour: the owner survives the "
                "write, the value half of the pair does not"
            ),
            "next": (
                "ask whether the write gate or the value projection drops the earlier token; "
                "no new budget"
            ),
        }
    if colour and not name:
        return {
            "id": "D2-key-only",
            "reading": (
                "one entry carries its own colour but not its own name: the key survives the "
                "write, the owner does not"
            ),
            "next": (
                "the missing half is the owner, not the value; register a write-side probe of "
                "the item's last token, no new budget"
            ),
        }
    return {
        "id": "D3-entry-lacks-owner",
        "reading": (
            "one entry carries neither its own name nor its own colour on held-out sessions: "
            "the write does not bind the pair at all"
        ),
        "next": (
            "the write side is the subject: register a probe of what the entry does carry "
            "(position/terminator) before changing the write rule"
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
        raise SystemExit("§79 reads the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or 2)
    if k != ROSTER_ITEMS:
        raise SystemExit(f"§79 was registered at k={ROSTER_ITEMS}, this carrier has k={k}")
    seed = int(corpus_block.get("seed") or 0)
    if seed <= 0:
        raise SystemExit("the report does not record its corpus seed")

    contents = load_contents()
    composition = load_composition()
    split75 = load_split75()
    families = load_families()
    boundaries = load_boundaries()
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

    train_records = entry_records(trainer, probe, core, train, names, colours)
    held_records = entry_records(trainer, probe, core, held, names, colours)

    torch = core._torch
    train_x = {
        feature: torch.stack([row[feature] for row in train_records]).float()
        for feature in FEATURES
    }
    held_x = {
        feature: torch.stack([row[feature] for row in held_records]).float() for feature in FEATURES
    }
    labels = {
        "name": torch.as_tensor([row["name"] for row in held_records], dtype=torch.long),
        "colour": torch.as_tensor([row["colour"] for row in held_records], dtype=torch.long),
    }
    partner = {
        "name": torch.as_tensor([row["partner"] for row in held_records], dtype=torch.long),
        "colour": torch.as_tensor(
            [row["partner_colour"] for row in held_records], dtype=torch.long
        ),
    }
    train_labels = {
        "name": torch.as_tensor([row["name"] for row in train_records], dtype=torch.long),
        "colour": torch.as_tensor([row["colour"] for row in train_records], dtype=torch.long),
    }
    train_position = torch.as_tensor([row["position"] for row in train_records], dtype=torch.long)
    held_position = torch.as_tensor([row["position"] for row in held_records], dtype=torch.long)

    readouts: Dict[str, Any] = {}
    for feature in FEATURES:
        readouts[feature] = {}
        for target in TARGETS:
            out = len(names) if target == "name" else len(colours)
            readouts[feature][target] = readout_block(
                torch,
                boundaries,
                composition,
                split75,
                train_x[feature],
                train_labels[target],
                held_x[feature],
                labels[target],
                partner[target],
                out,
                draws=draws,
            )
        readouts[feature]["position"] = position_block(
            torch,
            boundaries,
            train_x[feature],
            train_position,
            held_x[feature],
            held_position,
        )

    bridge = bridge_block(
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
    train_audit = audit_block(train_records)
    held_audit = audit_block(held_records)
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
            "train": alignment(display, train),
            "heldout": alignment(display, held),
        },
        "entry_audit": {"train": train_audit, "heldout": held_audit},
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
        },
        "probe": {
            "features": list(FEATURES),
            "primary_feature": PRIMARY_FEATURE,
            "targets": list(TARGETS),
            "name_out": len(names),
            "colour_out": len(colours),
            "steps": PROBE_STEPS,
            "batch": PROBE_BATCH,
            "lr": PROBE_LR,
            "weight_decay": PROBE_WEIGHT_DECAY,
            "seed": PROBE_SEED,
            "null_draws": draws,
            "null_seed": NULL_SEED,
            "alpha": ALPHA,
            "forced_floor": FORCED_FLOOR,
            "gate_metric": "within-session two-way forced choice (own vs the other item's label)",
        },
        "entries": {
            "train": len(train_records),
            "heldout": len(held_records),
            "per_session": ROSTER_ITEMS,
            "train_positions": {
                "first": sum(1 for row in train_records if row["position"] == 0),
                "second": sum(1 for row in train_records if row["position"] == 1),
            },
            "heldout_positions": {
                "first": sum(1 for row in held_records if row["position"] == 0),
                "second": sum(1 for row in held_records if row["position"] == 1),
            },
        },
        "readouts": readouts,
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
        return ["this is not a §79 report"]
    probe = data.get("probe") or {}
    for name, expected in (
        ("features", list(FEATURES)),
        ("primary_feature", PRIMARY_FEATURE),
        ("steps", PROBE_STEPS),
        ("null_draws", NULL_DRAWS),
        ("null_seed", NULL_SEED),
        ("alpha", ALPHA),
        ("forced_floor", FORCED_FLOOR),
    ):
        if probe.get(name) != expected:
            problems.append(f"probe.{name} is not the registered {expected!r}")
    entries = data.get("entries") or {}
    corpus = data.get("corpus") or {}
    if entries.get("train") != ROSTER_ITEMS * int(corpus.get("train_sessions") or 0):
        problems.append("the training entry count is not two per session")
    if entries.get("heldout") != ROSTER_ITEMS * int(corpus.get("heldout_sessions") or 0):
        problems.append("the held-out entry count is not two per session")

    instrument = data.get("instrument") or {}
    align = instrument.get("alignment") or {}
    if align.get("pass") is not True:
        problems.append("the item/label alignment did not pass")
    for split in ("train", "heldout"):
        audit = _nested(instrument, "entry_audit", split) or {}
        if float(audit.get("coverage", 0.0)) < ENTRY_COVERAGE:
            problems.append(f"{split} entry coverage is below {ENTRY_COVERAGE}")
    bridge = instrument.get("bridge") or {}
    actual = bridge.get("actual") or {}
    for which, expected in REFERENCE.items():
        got = actual.get(which) or {}
        for key, value in expected.items():
            if abs(float(got.get(key, -1.0)) - value) > BRIDGE_TOLERANCE:
                problems.append(f"the §77 bridge does not reproduce {which}.{key}")

    readouts = data.get("readouts") or {}
    for feature in FEATURES:
        for target in TARGETS:
            block = _nested(readouts, feature, target)
            if not block:
                problems.append(f"the {feature}.{target} readout is missing")
                continue
            observed = block.get("observed") or {}
            n = int(observed.get("n") or 0)
            expected_forced = round(int(observed.get("forced_correct") or 0) / max(n, 1), 6)
            if abs(float(observed.get("forced", -1.0)) - expected_forced) > 1e-9:
                problems.append(f"{feature}.{target} forced rate is not correct/n")
            expected_top1 = round(int(observed.get("top1_correct") or 0) / max(n, 1), 6)
            if abs(float(observed.get("top1", -1.0)) - expected_top1) > 1e-9:
                problems.append(f"{feature}.{target} top-1 is not correct/n")
            null = block.get("null") or {}
            expected_p = permutation_p(int(null.get("ge") or 0), int(null.get("draws") or 0))
            if abs(float(block.get("p_value", -1.0)) - expected_p) > 1e-9:
                problems.append(f"{feature}.{target} p_value is not the permutation convention")

    recomputed = gates(data)
    stored = data.get("gates") or {}
    for key in ("I0_instrument", "P_name", "P_colour"):
        if bool((stored.get(key) or {}).get("pass")) != bool(recomputed[key]["pass"]):
            problems.append(f"gate {key} does not re-derive")
    expected_branch = branch(recomputed)
    stored_branch = data.get("branch") or {}
    if stored_branch.get("id") != expected_branch["id"]:
        problems.append("the branch does not re-derive from the gates")
    if stored_branch.get("id") not in BRANCH_ORDER:
        problems.append("the branch is not one of the registered five")
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="§79: what one item's entry carries")
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
            print("§79 check FAIL")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print("§79 check OK")
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
