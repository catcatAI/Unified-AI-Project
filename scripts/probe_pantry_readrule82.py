#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§82: is the missing colour on the key side, on the query side, or neither?

Why this exists
---------------
§81 removed the key-norm race and the learned temperature (``cosine_unit``) and
the read *still* preferred slot 2 in 200/200 held-out reads: the forced choice was
exactly the label balance, and all 400 label permutations tied it.  So no read
rule of that shape addresses the frozen keys.

But §81 cannot say *which* side is missing the colour, because the twins only
swap the roster order and the question text is byte-identical: "the keys do not
carry the colour" and "the query does not carry it" produce the same 100/200.

This stage separates them at the same frozen read point, with no retraining:

* ``entry_key``       - can a linear probe on the stored key tell which colour
  that entry holds (own vs the partner's colour, within a session)?
* ``entry_value``     - the same probe on the stored value.  This is the anchor:
  §79 measured 0.6200 (248/400), so the harness must reproduce it exactly.
* ``query``           - can a linear probe on the question-turn query ``W_q h``
  tell which colour the session needs (needed vs partner, plus an 8-way
  descriptor)?
* ``boundary_query``  - and does the **boundary** use of the same read address?
  ``q_b = W_q h_b`` at the boundary before the question turn, scored with §81's
  own forced choice under ``model`` and ``cosine_unit``.  Zero fitted parameters,
  because the query is still the carrier's own projection and the keys are the
  carrier's own keys.  This is the candidate repair: if the colour is in the
  boundary state, its query can select the roster entry without new parameters.

The question is narrow: the read at the question turn needs the *evidence*
colour; the roster entries' keys already carry their own colours (§79: k
0.7375).  If the query carries the needed colour, the read rule is the limit.
If it does not, the question turn never has the colour, and changing the read
cannot help.

Conventions (all inherited, none retuned)
-----------------------------------------
* fitted cells: fit on the **train** split, score the forced choice on the
  **held-out** split, label-permutation null refits per draw (§79's convention,
  400 refits);
* ``boundary_query``: unfitted, so its null permutes the labels without
  refitting (§80/§81's convention);
* forced choice floor 0.5, Wilson lower bound must clear it, ``p < 0.005``.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_readrule82.py \\
        --report data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json \\
        --anchor79 data/pantry_stage/pair79/k2.json \\
        --anchor81 data/pantry_stage/readrule81/k2.json \\
        --out data/pantry_stage/readrule82/k2.json

    ./.venv/bin/python scripts/probe_pantry_readrule82.py --check data/pantry_stage/readrule82/k2.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
PAIR79 = REPO_ROOT / "scripts" / "probe_pantry_pair79.py"
READRULE81 = REPO_ROOT / "scripts" / "probe_pantry_readrule81.py"

# §82.4, written before the scored run.
ALPHA = 0.005
NULL_DRAWS = 400
NULL_SEED = 20261125
FORCED_FLOOR = 0.5
ENTRY_COVERAGE = 0.99
ENTRY_COSINE = 0.999
ROSTER_ITEMS = 2
READ_BATCH = 32
REF_TOLERANCE = 2e-9
PROBE_STEPS = 2000
PROBE_BATCH = 64
PROBE_LR = 1e-3
PROBE_WEIGHT_DECAY = 1e-4
PROBE_SEED = 20261121
ANCHOR79_FORCED = 0.62
ANCHOR79_WINS = 248
ANCHOR79_N = 400
ANCHOR81_WINS = 100
BOUNDARY_RULES = ("model", "cosine_unit")
RULES = {
    "model": "softmax(exp(scale) * k . q_b)  (the model's own read, on the boundary query)",
    "cosine_unit": "softmax((k/||k||) . (q_b/||q_b||))  (no norm race, no learned temperature)",
}
STAGE = "§82 is the missing colour on the key side, the query side, or neither?"
BRANCH_ORDER = (
    "E0-instrument",
    "C1-state-addresses",
    "C4-write-side-keys-lack-colour",
    "C2-both-sides-carry-colour",
    "C3-query-missing",
)
PREDICTION = "C3-query-missing"
PREDICTION_ALTERNATIVE = "C1-state-addresses"


def _load(name: str, path: Path) -> Any:
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_pair79() -> Any:
    """§79: the entry extraction, the probe harness and the anchor cell."""
    module = _load("pantry_readrule82_pair79", PAIR79)
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
        ("ROSTER_ITEMS", ROSTER_ITEMS),
    ):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(
                f"§82 was registered against {name}={expected}, §79 now has {actual}; "
                "the two stages no longer share a criterion"
            )
    return module


def load_readrule81() -> Any:
    """§81: the frozen read rules, the forced choice and the anchor."""
    module = _load("pantry_readrule82_readrule81", READRULE81)
    for name, expected in (
        ("ALPHA", ALPHA),
        ("NULL_DRAWS", NULL_DRAWS),
        ("NULL_SEED", NULL_SEED),
        ("FORCED_FLOOR", FORCED_FLOOR),
        ("ENTRY_COVERAGE", ENTRY_COVERAGE),
        ("ENTRY_COSINE", ENTRY_COSINE),
        ("ROSTER_ITEMS", ROSTER_ITEMS),
        ("REF_TOLERANCE", REF_TOLERANCE),
    ):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(
                f"§82 was registered against {name}={expected}, §81 now has {actual}; "
                "the two stages no longer share a criterion"
            )
    return module


# --------------------------------------------------------------------------- #
# the read record: §81's point, plus the boundary query
# --------------------------------------------------------------------------- #
def read_records(
    trainer: Any,
    probe: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    names: Sequence[str],
    colours: Sequence[str],
    pair: Any,
    rr81: Any,
    *,
    batch: int = READ_BATCH,
) -> List[Dict[str, Any]]:
    """One record per session: the store, the question-turn ``h``, both queries.

    This is §81's extraction unchanged (so its model masses can be anchored),
    plus ``query_boundary``: the carrier's own query projection on the **boundary**
    hidden state, i.e. the query that was available one turn earlier.
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
                seen = rr81.mod_seen_value(session)
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
                query_boundary = (
                    core.query_proj(before["h"][index : index + 1]).reshape(-1).detach().clone()
                )
                slots = rr81.mod_roster_slots(
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
                        "query_boundary": query_boundary,
                        "h": h_final.detach().clone(),
                        "v_roster": torch.stack([store_values[slot].reshape(-1) for slot in slots])
                        .detach()
                        .clone(),
                        "key_norms": [round(float(store_keys[slot].norm()), 6) for slot in slots],
                        "query_norm": round(float(query.norm()), 6),
                        "name": name_index[str(pairs[item][1])],
                        "partner_name": name_index[str(pairs[1 - item][1])],
                        "colour": colour_index[str(pairs[item][0])],
                        "partner_colour": colour_index[str(pairs[1 - item][0])],
                        "evidence_colour": colour_index[seen],
                    }
                )
    return records


def _stack(torch: Any, records: Sequence[Dict[str, Any]], field: str) -> Any:
    return torch.stack([row[field] for row in records]).float()


def _labels(torch: Any, records: Sequence[Dict[str, Any]], field: str) -> Any:
    return torch.as_tensor([int(row[field]) for row in records], dtype=torch.long)


# --------------------------------------------------------------------------- #
# the probe cells
# --------------------------------------------------------------------------- #
def observed_block(
    torch: Any,
    pair: Any,
    split75: Any,
    boundaries: Any,
    train_x: Any,
    train_y: Any,
    eval_x: Any,
    own: Any,
    partner: Any,
    out: int,
) -> Dict[str, Any]:
    """One fitted cell without the null (the §79 anchor only, not a new claim)."""
    mean = train_x.mean(dim=0, keepdim=True)
    std = train_x.std(dim=0, keepdim=True, unbiased=False).clamp_min(1e-6)
    logits = pair._probe_logits(
        torch,
        boundaries,
        (train_x - mean) / std,
        train_y,
        (eval_x - mean) / std,
        out,
        seed=PROBE_SEED,
    )
    observed = pair.forced_block(torch, split75, logits, own, partner)
    return {
        "observed": observed,
        "chance": {"forced": FORCED_FLOOR, "top1": round(1.0 / out, 6)},
        "fitted_null": False,
        "reading": "§79's value-to-colour cell: the anchor, not a new claim",
    }


def probe_block(
    torch: Any,
    pair: Any,
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
    """§79's fitted cell with its refit-per-draw label null."""
    return pair.readout_block(
        torch,
        boundaries,
        composition,
        split75,
        train_x,
        train_y,
        eval_x,
        own,
        partner,
        out,
        draws=draws,
    )


def probe_pass(block: Dict[str, Any], *, alpha: float = ALPHA) -> bool:
    """The registered gate for a fitted cell: Wilson low clears chance, null does not."""
    observed = block.get("observed") or {}
    wilson = observed.get("wilson") or {}
    return bool(
        float(wilson.get("low", 0.0)) > FORCED_FLOOR and float(block.get("p_value", 1.0)) < alpha
    )


def read_pass(block: Dict[str, Any], *, alpha: float = ALPHA) -> bool:
    """The registered gate for an unfitted read: same shape, no refit."""
    wilson = block.get("wilson") or {}
    return bool(
        float(wilson.get("low", 0.0)) > FORCED_FLOOR and float(block.get("p_value", 1.0)) < alpha
    )


# --------------------------------------------------------------------------- #
# gates and the branch
# --------------------------------------------------------------------------- #
def gates(outcome: Dict[str, Any]) -> Dict[str, Any]:
    instrument = outcome["instrument"]
    audit = instrument["entry_audit"]
    coverage = min(float(audit["train"]["coverage"]), float(audit["heldout"]["coverage"]))
    read_audit = instrument["read_audit"]
    read_coverage = min(
        float(read_audit["train"]["coverage"]), float(read_audit["heldout"]["coverage"])
    )
    anchor79 = instrument["anchor79"]
    anchor81 = instrument["anchor81"]
    i0 = {
        "pass": bool(
            instrument["carrier_unchanged"]
            and instrument["checkpoint_unchanged"]
            and instrument["mode_matches"]
            and instrument["corpus_digests_match"]
            and instrument["alignment"]["pass"]
            and coverage >= ENTRY_COVERAGE
            and read_coverage >= ENTRY_COVERAGE
            and anchor79["reproduced"]
            and anchor81["reproduced"]
        ),
        "carrier_unchanged": instrument["carrier_unchanged"],
        "checkpoint_unchanged": instrument["checkpoint_unchanged"],
        "mode_matches": instrument["mode_matches"],
        "corpus_digests_match": instrument["corpus_digests_match"],
        "alignment_pass": instrument["alignment"]["pass"],
        "entry_coverage": coverage,
        "read_coverage": read_coverage,
        "entry_required_coverage": ENTRY_COVERAGE,
        "anchor79_reproduced": anchor79["reproduced"],
        "anchor79_forced": anchor79["forced"],
        "anchor79_wins": anchor79["wins"],
        "anchor81_reproduced": anchor81["reproduced"],
        "anchor81_wins": anchor81["wins"],
        "anchor81_max_abs_diff": anchor81["max_abs_diff"],
        "reading": (
            "the carrier, checkpoint and corpus are the frozen §77 ones, the entry writes are the "
            "ones at the read point, §79's value-to-colour cell is reproduced and §81's model "
            "masses are reproduced"
        ),
    }
    entry_key = outcome["cells"]["entry_key"]
    query = outcome["cells"]["query"]
    boundary = {
        variant: read_pass(outcome["cells"]["boundary_query"][variant])
        for variant in BOUNDARY_RULES
    }
    return {
        "I0_instrument": i0,
        "cells": {
            "entry_key": {
                "pass": probe_pass(entry_key),
                "forced": entry_key["observed"]["forced"],
                "wins": entry_key["observed"]["forced_correct"],
                "n": entry_key["observed"]["n"],
                "wilson_low": float(entry_key["observed"]["wilson"]["low"]),
                "p_value": entry_key["p_value"],
                "top1": entry_key["observed"]["top1"],
                "chance": FORCED_FLOOR,
                "eight_way_chance": float(entry_key["chance"]["top1"]),
            },
            "query": {
                "pass": probe_pass(query),
                "forced": query["observed"]["forced"],
                "wins": query["observed"]["forced_correct"],
                "n": query["observed"]["n"],
                "wilson_low": float(query["observed"]["wilson"]["low"]),
                "p_value": query["p_value"],
                "top1": query["observed"]["top1"],
                "chance": FORCED_FLOOR,
                "eight_way_chance": float(query["chance"]["top1"]),
            },
            "boundary_query": {
                variant: {
                    "pass": bool(boundary[variant]),
                    "wins": outcome["cells"]["boundary_query"][variant]["wins"],
                    "n": outcome["cells"]["boundary_query"][variant]["n"],
                    "forced": outcome["cells"]["boundary_query"][variant]["forced"],
                    "wilson_low": float(
                        outcome["cells"]["boundary_query"][variant]["wilson"]["low"]
                    ),
                    "p_value": outcome["cells"]["boundary_query"][variant]["p_value"],
                    "roster_mass": outcome["cells"]["boundary_query"][variant]["roster_mass"][
                        "mean"
                    ],
                    "argmax_on_roster": outcome["cells"]["boundary_query"][variant][
                        "argmax_on_roster"
                    ],
                    "chance": FORCED_FLOOR,
                }
                for variant in BOUNDARY_RULES
            },
        },
    }


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """Fixed precedence, written before the run: E0 > C1 > C4 > C2 > C3."""
    if not gate["I0_instrument"]["pass"]:
        return {
            "id": "E0-instrument",
            "reading": (
                "the carrier, corpus, entry audit, §79's value-to-colour cell or §81's masses "
                "moved; nothing is read"
            ),
            "next": "fix the instrument before asking which side lost the colour",
        }
    boundary = gate["cells"]["boundary_query"]
    if boundary["model"]["pass"] or boundary["cosine_unit"]["pass"]:
        return {
            "id": "C1-state-addresses",
            "reading": (
                "the boundary query (W_q of the state before the question turn) selects the roster "
                "entry the evidence colour needs, under at least one registered rule: the colour is "
                "in the boundary state and the stored keys can be addressed by it, so what loses it "
                "is the question-turn read point, not the store"
            ),
            "next": (
                "retrain with the read taken at the boundary query (same 10,000 steps, 168,150 "
                "parameters, same corpus; no extra epochs, width or data) and re-read §80's cell "
                "plus §81's three columns"
            ),
        }
    if not gate["cells"]["entry_key"]["pass"]:
        return {
            "id": "C4-write-side-keys-lack-colour",
            "reading": (
                "the stored keys do not carry the roster colour (own vs partner, within a session), "
                "so no query could address them; the information is missing on the write side"
            ),
            "next": (
                "register the write-side change (the key carries the roster colour at the write "
                "point) at the same budget, then re-read §80's cell"
            ),
        }
    if gate["cells"]["query"]["pass"]:
        return {
            "id": "C2-both-sides-carry-colour",
            "reading": (
                "both the stored keys and the question-turn query carry the colour, and the boundary "
                "query does not address: the remaining limit is the read's own projection/geometry, "
                "not the information"
            ),
            "next": (
                "register a read that uses the readable directions (a learned metric over the same "
                "keys and query) at the same budget, then re-read §80's cell"
            ),
        }
    return {
        "id": "C3-query-missing",
        "reading": (
            "the stored keys do carry the colour, the question-turn query does not, and the "
            "boundary query does not address either: the colour never reaches the read's query, so "
            "no read rule over these keys and queries can be guided by it"
        ),
        "next": (
            "change where the query comes from so it can see the evidence colour (the state that "
            "carries it is the boundary one, §69's 0.8900), same budget; the keys and the read "
            "arithmetic are already ruled out"
        ),
    }


# --------------------------------------------------------------------------- #
# one run
# --------------------------------------------------------------------------- #
def run(
    report_path: Path,
    anchor79_path: Path,
    anchor81_path: Path,
    *,
    device: str = "cpu",
    draws: int = NULL_DRAWS,
) -> Dict[str, Any]:
    started = time.time()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    anchor79 = json.loads(anchor79_path.read_text(encoding="utf-8"))
    anchor81 = json.loads(anchor81_path.read_text(encoding="utf-8"))
    pair = load_pair79()
    rr81 = load_readrule81()
    if anchor79.get("stage") != pair.STAGE:
        raise SystemExit("the §79 anchor is not a §79 report")
    if anchor81.get("stage") != rr81.STAGE:
        raise SystemExit("the §81 anchor is not a §81 report")
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§82 reads the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or 2)
    if k != ROSTER_ITEMS:
        raise SystemExit(f"§82 was registered at k={ROSTER_ITEMS}, this carrier has k={k}")
    seed = int(corpus_block.get("seed") or 0)
    if seed <= 0:
        raise SystemExit("the report does not record its corpus seed")

    contents = pair.load_contents()
    composition = pair.load_composition()
    split75 = pair.load_split75()
    boundaries = pair.load_boundaries()
    probe = pair.load_readout()
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

    # the entry cells: §79's extraction, at the same boundary
    train_entries = pair.entry_records(trainer, probe, core, train, names, colours)
    held_entries = pair.entry_records(trainer, probe, core, held, names, colours)

    # the read records: §81's point, plus the boundary query
    train_reads = read_records(trainer, probe, core, train, names, colours, pair, rr81)
    held_reads = read_records(trainer, probe, core, held, names, colours, pair, rr81)
    torch = core._torch
    exp_scale = torch.exp(core.log_read_scale)

    train_entry_x = {f: _stack(torch, train_entries, f) for f in ("k", "v")}
    held_entry_x = {f: _stack(torch, held_entries, f) for f in ("k", "v")}
    entry_train_y = _labels(torch, train_entries, "colour")
    entry_own = _labels(torch, held_entries, "colour")
    entry_partner = _labels(torch, held_entries, "partner_colour")

    query_train_x = _stack(torch, train_reads, "query")
    query_held_x = _stack(torch, held_reads, "query")
    query_train_y = _labels(torch, train_reads, "colour")
    query_own = _labels(torch, held_reads, "colour")
    query_partner = _labels(torch, held_reads, "partner_colour")
    if any(int(row["colour"]) != int(row["evidence_colour"]) for row in train_reads + held_reads):
        raise SystemExit("the target entry's colour is not the evidence colour")

    out = len(colours)
    entry_value = observed_block(
        torch,
        pair,
        split75,
        boundaries,
        train_entry_x["v"],
        entry_train_y,
        held_entry_x["v"],
        entry_own,
        entry_partner,
        out,
    )
    entry_key = probe_block(
        torch,
        pair,
        boundaries,
        composition,
        split75,
        train_entry_x["k"],
        entry_train_y,
        held_entry_x["k"],
        entry_own,
        entry_partner,
        out,
        draws=draws,
    )
    query = probe_block(
        torch,
        pair,
        boundaries,
        composition,
        split75,
        query_train_x,
        query_train_y,
        query_held_x,
        query_own,
        query_partner,
        out,
        draws=draws,
    )

    boundary_records = [dict(row, query=row["query_boundary"]) for row in held_reads]
    boundary_query = {
        variant: rr81.address_block(
            torch, split75, composition, boundary_records, exp_scale, variant, draws=draws
        )
        for variant in BOUNDARY_RULES
    }

    # the anchors: §79's observed value-to-colour cell, and §81's model masses
    stored79 = anchor79.get("readouts", {}).get("v", {}).get("colour", {}).get("observed", {})
    observed79 = entry_value["observed"]
    anchor79_block = {
        "stored_forced": float(stored79.get("forced", -1.0)),
        "stored_wins": int(stored79.get("forced_correct", -1)),
        "stored_n": int(stored79.get("n", -1)),
        "forced": observed79["forced"],
        "wins": observed79["forced_correct"],
        "n": observed79["n"],
        "reproduced": bool(
            abs(float(observed79["forced"]) - float(stored79.get("forced", -1.0))) <= 1e-6
            and int(observed79["forced_correct"]) == int(stored79.get("forced_correct", -2))
            and int(observed79["n"]) == int(stored79.get("n", -1))
        ),
        "reading": "§79 measured the same value-to-colour cell: 0.6200 (248/400)",
    }
    anchor81_block = rr81.anchor_block(
        torch, held_reads, exp_scale, {"address": anchor81["address"]["model"]}
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
        "corpus_digests_match": bool(
            (corpus.get("meta") or {}).get("train_digest") == corpus_block.get("train_digest")
            and (corpus.get("meta") or {}).get("heldout_digest")
            == corpus_block.get("heldout_digest")
        ),
        "alignment": {
            "train": pair.alignment(display, train),
            "heldout": pair.alignment(display, held),
        },
        "entry_audit": {
            "train": pair.audit_block(train_entries),
            "heldout": pair.audit_block(held_entries),
        },
        "read_audit": {
            "train": rr81.ADDRESS.read_audit(torch, train_reads, train_entries),
            "heldout": rr81.ADDRESS.read_audit(torch, held_reads, held_entries),
        },
        "anchor79": anchor79_block,
        "anchor81": anchor81_block,
    }
    instrument["alignment"]["pass"] = bool(
        instrument["alignment"]["train"]["pass"] and instrument["alignment"]["heldout"]["pass"]
    )

    outcome: Dict[str, Any] = {
        "stage": STAGE,
        "carrier_report": str(report_path),
        "anchor79_report": str(anchor79_path),
        "anchor81_report": str(anchor81_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "corpus_seed": seed,
        "corpus": {
            "train_digest": corpus_block.get("train_digest"),
            "heldout_digest": corpus_block.get("heldout_digest"),
            "train_sessions": len(train),
            "heldout_sessions": len(held),
            "train_entries": len(train_entries),
            "heldout_entries": len(held_entries),
            "roster_items": ROSTER_ITEMS,
            "names": len(names),
            "colours": len(colours),
            "train_twins": sum(1 for record in train_reads if record["twin"]),
            "heldout_twins": sum(1 for record in held_reads if record["twin"]),
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
            "fit_split": "train",
            "scored_split": "heldout",
            "gate_metric": "within-session two-way forced choice (needed vs the other entry's colour)",
        },
        "reads": {
            "point": "the store at the boundary before the question turn, last question token",
            "boundary_query": "W_q of the boundary hidden state (the query one turn earlier)",
            "rules": {variant: RULES[variant] for variant in BOUNDARY_RULES},
            "fitted_parameters_boundary": 0,
            "null": "label permutation without refitting (§80/§81 convention)",
        },
        "cells": {
            "entry_key": entry_key,
            "entry_value": entry_value,
            "query": query,
            "boundary_query": boundary_query,
        },
        "prediction": {
            "registered": PREDICTION,
            "alternative": PREDICTION_ALTERNATIVE,
            "confidence": "low",
            "reason": (
                "§79 puts the colour in the keys (0.7375) and §80.2(d) puts it below chance in "
                "the question-turn h (0.105), which is the C3 shape; C1 is the live alternative "
                "because §69 reads the colour at the evidence boundary (0.8900)"
            ),
        },
        "decision": {
            "alpha": ALPHA,
            "forced_floor": FORCED_FLOOR,
            "null_draws": draws,
            "null_seed": NULL_SEED,
            "anchor_tolerance": REF_TOLERANCE,
            "anchor79_forced": ANCHOR79_FORCED,
            "anchor79_wins": ANCHOR79_WINS,
            "anchor79_n": ANCHOR79_N,
            "anchor81_wins": ANCHOR81_WINS,
        },
        "instrument": instrument,
    }
    outcome["gates"] = gates(outcome)
    outcome["branch"] = branch(outcome["gates"])
    outcome["prediction_hit"] = bool(outcome["branch"]["id"] == PREDICTION)
    outcome["instrument_ok"] = bool(outcome["gates"]["I0_instrument"]["pass"])
    outcome["seconds"] = round(time.time() - started, 3)
    return outcome


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def check(path: Path) -> List[str]:
    """Re-derive every gate and the branch from the stored readings."""
    problems: List[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("stage") != STAGE:
        return ["this is not a §82 report"]
    decision = data.get("decision") or {}
    for name, expected in (
        ("alpha", ALPHA),
        ("forced_floor", FORCED_FLOOR),
        ("null_draws", NULL_DRAWS),
        ("null_seed", NULL_SEED),
        ("anchor_tolerance", REF_TOLERANCE),
        ("anchor79_forced", ANCHOR79_FORCED),
        ("anchor79_wins", ANCHOR79_WINS),
        ("anchor79_n", ANCHOR79_N),
        ("anchor81_wins", ANCHOR81_WINS),
    ):
        if decision.get(name) != expected:
            problems.append(f"decision.{name} is not the registered {expected!r}")

    cells = data.get("cells") or {}
    for name in ("entry_key", "query"):
        block = cells.get(name) or {}
        observed = block.get("observed") or {}
        n = int(observed.get("n") or 0)
        if n <= 0:
            problems.append(f"{name}: no observed reads")
            continue
        wins = int(observed.get("forced_correct") or 0)
        if abs(float(observed.get("forced", -1.0)) - round(wins / n, 6)) > 1e-9:
            problems.append(f"{name}: the forced rate is not wins/n")
        null = block.get("null") or {}
        expected_p = round((1 + int(null.get("ge") or 0)) / (int(null.get("draws") or 0) + 1), 6)
        if abs(float(block.get("p_value", -1.0)) - expected_p) > 1e-9:
            problems.append(f"{name}: p_value is not the permutation convention")

    stored_cell = cells.get("entry_value") or {}
    if not (stored_cell.get("observed") or {}).get("n"):
        problems.append("entry_value: no observed reads")

    for variant in BOUNDARY_RULES:
        block = (cells.get("boundary_query") or {}).get(variant) or {}
        n = int(block.get("n") or 0)
        m0 = block.get("m0") or []
        m1 = block.get("m1") or []
        items = block.get("items") or []
        if not (len(m0) == len(m1) == len(items) == n) or n <= 0:
            problems.append(f"boundary_query[{variant}]: the masses are not one pair per read")
            continue
        wins = 0
        for left, right, item in zip(m0, m1, items):
            correct, partner = (left, right) if int(item) == 0 else (right, left)
            wins += int(float(correct) > float(partner))
        if wins != int(block.get("wins") or -1):
            problems.append(f"boundary_query[{variant}]: the win count is not re-derivable")
        if abs(float(block.get("forced", -1.0)) - round(wins / n, 6)) > 1e-9:
            problems.append(f"boundary_query[{variant}]: the forced rate is not wins/n")
        null = block.get("null") or {}
        expected_p = round((1 + int(null.get("ge") or 0)) / (int(null.get("draws") or 0) + 1), 6)
        if abs(float(block.get("p_value", -1.0)) - expected_p) > 1e-9:
            problems.append(f"boundary_query[{variant}]: p_value is not the permutation convention")

    anchor79 = (data.get("instrument") or {}).get("anchor79") or {}
    if not anchor79.get("reproduced"):
        problems.append("§79's value-to-colour cell is not reproduced")
    anchor81 = (data.get("instrument") or {}).get("anchor81") or {}
    if not anchor81.get("reproduced"):
        problems.append("§81's model masses are not reproduced")
    if int(anchor81.get("mismatches", 1)) != 0:
        problems.append("§81's model masses disagree")
    if float(anchor81.get("max_abs_diff", 1.0)) > REF_TOLERANCE:
        problems.append("§81's model masses exceed the tolerance")

    recomputed = gates(data)
    stored = data.get("gates") or {}
    if bool((stored.get("I0_instrument") or {}).get("pass")) != bool(
        recomputed["I0_instrument"]["pass"]
    ):
        problems.append("gate I0_instrument does not re-derive")
    for name in ("entry_key", "query"):
        stored_cell = (stored.get("cells") or {}).get(name) or {}
        if bool(stored_cell.get("pass")) != bool(recomputed["cells"][name]["pass"]):
            problems.append(f"cell {name} does not re-derive")
    for variant in BOUNDARY_RULES:
        stored_cell = ((stored.get("cells") or {}).get("boundary_query") or {}).get(variant) or {}
        if bool(stored_cell.get("pass")) != bool(
            recomputed["cells"]["boundary_query"][variant]["pass"]
        ):
            problems.append(f"cell boundary_query[{variant}] does not re-derive")
    expected_branch = branch(recomputed)
    stored_branch = data.get("branch") or {}
    if stored_branch.get("id") != expected_branch["id"]:
        problems.append("the branch does not re-derive from the gates")
    if stored_branch.get("id") not in BRANCH_ORDER:
        problems.append("the branch is not one of the registered five")
    if bool(data.get("prediction_hit")) != bool(stored_branch.get("id") == PREDICTION):
        problems.append("prediction_hit does not re-derive from the branch")
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="§82: which side lost the colour")
    parser.add_argument(
        "--report",
        type=Path,
        default=REPO_ROOT / "data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json",
    )
    parser.add_argument(
        "--anchor79", type=Path, default=REPO_ROOT / "data/pantry_stage/pair79/k2.json"
    )
    parser.add_argument(
        "--anchor81", type=Path, default=REPO_ROOT / "data/pantry_stage/readrule81/k2.json"
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
            print("§82 check FAIL")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print("§82 check OK")
        return 0

    outcome = run(
        args.report, args.anchor79, args.anchor81, device=args.device, draws=int(args.null_draws)
    )
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
