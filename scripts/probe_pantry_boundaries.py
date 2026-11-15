#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§69: where do the facts live? (same frozen carrier, same readout, three boundaries)

Why this exists
---------------
§68 asked what the frozen state carries at the **answer** boundary and returned
N3-facts-not-linearly-readable: a linear probe could not expose the observed
colour or the roster names there, so "the state does not hold these facts" was
left unsupported - the failure might be the boundary, not the state. §68.9 named
the next measurement and this is it: probe the same facts at the turns where they
are *stated*.

What this measures
------------------
Same carriers (§64's k=2 and §65's k=5 checkpoints), same 400 declared / 200
held-out structures, same readout (one ``nn.Linear`` on the standardised
``read`` vector, 2,000 steps, train-split statistics), same grading (held-out
exact >= 0.50 **and** Wilson lower bound above both chance and the majority
baseline). Only the boundary moves:

* ``roster``  - right after the turn that names the roster;
* ``evidence``- right after the turn where the witness names the colour;
* ``answer``  - after the final question (the §68 boundary, recomputed here so
  all three columns share one instrument).

Three facts, each probed where it can exist:

| fact | asserted at | pushed through the probe at |
| --- | --- | --- |
| ``roster`` (top-k name set) | roster turn | roster, evidence, answer |
| ``colour`` (8-way argmax) | evidence turn | evidence, answer |
| ``pairing`` (colour per roster slot) | roster turn | roster, evidence, answer |
| ``culprit`` (12-way argmax) | nowhere (it must be deduced) | answer only |

``colour`` is not probed at the roster boundary because it is not yet
identifiable from the input there - the witness has not spoken, and scoring an
unknowable fact would only add a chance-level row that could be misread.

``pairing`` is the fact §68 did not measure: the roster line states
``colour -> name`` for every slot, so the *relation* is asserted at the roster
turn even though the *answer* requires combining it with the witness's colour.
It is graded as an exact tuple (every slot's colour must be right), so chance is
``1 / 8**k`` - 1/64 at k=2 and 1/32768 at k=5.

What this is not
----------------
Not a capability score (the core score stays 0.00/10), and not a new objective:
the carrier is frozen, ``weights_hash`` and the checkpoint sha256 are recorded
before and after, and every probe is fitted on the declared training split only.
A fact that transfers at its own boundary and not at the answer boundary is a
*retention* finding, not a claim that the carrier cannot represent it.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_boundaries.py \\
        --report data/pantry_stage/ord_arm/pantry_deduction_20261115-015751.json \\
        --out data/pantry_stage/bounds69/k2.json
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
CONTENTS = REPO_ROOT / "scripts" / "probe_pantry_contents.py"

# §69.4, written before the scored run.
PROBE_STEPS = 2000
PROBE_BATCH = 64
PROBE_LR = 1e-3
PROBE_WEIGHT_DECAY = 1e-4
PROBE_SEED = 20261121
CAPACITY_SEED = 20261121
FOLDS = 5
READABLE_FLOOR = 0.95
TRANSFER_FLOOR = 0.50
CAPACITY_MAX = 0.50


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_contents() -> Any:
    """§68's module: standardisation, probe construction and the Wilson interval."""
    return _load("pantry_boundaries_contents", CONTENTS)


# --------------------------------------------------------------------------- #
# sessions and their three boundaries
# --------------------------------------------------------------------------- #
def boundary_turns(session: Dict[str, Any]) -> Dict[str, int]:
    """The turn index each boundary sits *after*: roster, evidence, answer."""
    meta = session["session_meta"]
    turns = session["turns"]
    return {
        "roster": int(meta["roster_turn"]),
        "evidence": int(meta["evidence_turn"]),
        "answer": len(turns) - 1,
    }


def shared_boundaries(sessions: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    """One index per boundary, or a refusal: features are stacked across rows."""
    first = boundary_turns(sessions[0])
    for session in sessions:
        if boundary_turns(session) != first:
            raise SystemExit(
                f"{session['session_id']}: boundary turns {boundary_turns(session)} "
                f"differ from {sessions[0]['session_id']}'s {first}"
            )
    return first


def roster_names(session: Dict[str, Any]) -> List[str]:
    """The roster in the order the session states it."""
    return [str(name) for name in session["environment"]["actors"]]


def pairing_of(session: Dict[str, Any]) -> Dict[str, str]:
    """``name -> colour`` from the roster turn's own assert (not from the oracle)."""
    turn = int(session["session_meta"]["roster_turn"])
    for assert_ in session["turns"][turn]["asserts"]:
        if assert_.get("kind") == "roster":
            return {str(name): str(colour) for colour, name in dict(assert_["value"]).items()}
    raise SystemExit(f"{session['session_id']}: no 'roster' assert on turn {turn}")


def targets(
    sessions: Sequence[Dict[str, Any]],
    names: Sequence[str],
    colours: Sequence[str],
    contents: Any,
) -> Dict[str, List[Any]]:
    """Roster multi-hot, live colour, per-slot colours and the culprit, per row.

    ``roster`` is a multi-hot over **all** names because the readout scores an
    exact top-k set (the same definition §68 used); ``pairing`` is in roster
    order, so slot ``s`` always refers to the ``s``-th name of
    ``environment.actors`` and the tuple target cannot silently reorder itself
    between training and scoring.
    """
    rosters: List[List[int]] = []
    colour_index: List[int] = []
    pairing: List[List[int]] = []
    culprit_index: List[int] = []
    structures: List[str] = []
    for session in sessions:
        roster = roster_names(session)
        mapping = pairing_of(session)
        rosters.append([1 if name in roster else 0 for name in names])
        colour_index.append(colours.index(contents.live_value(session)))
        pairing.append([colours.index(mapping[name]) for name in roster])
        culprit_index.append(names.index(session["ground_truth_oracle"]["culprit"]))
        structures.append(contents.structure_of(session))
    return {
        "roster": rosters,
        "colour": colour_index,
        "pairing": pairing,
        "culprit": culprit_index,
        "structure": structures,
    }


# --------------------------------------------------------------------------- #
# features at one boundary
# --------------------------------------------------------------------------- #
def boundary_reads(
    trainer: Any,
    contents: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    index: int,
    *,
    batch: int = 64,
) -> Dict[str, Any]:
    """Two views of the state after turn ``index``, one row per session, frozen.

    ``state`` is ``[h, read]`` - exactly what the carrier's output head is fed
    (``token_logits`` concatenates them), so a probe on it asks "can the vector
    the model actually classifies from expose this fact". ``read`` alone is
    kept as the comparability column: §68 probed only ``read``, and keeping it
    means the two stages can be compared without re-running §68's instrument.
    """
    torch = core._torch
    probe = contents.load_selection().load_probe()
    states: List[Any] = []
    reads: List[Any] = []
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
            if index >= len(snapshots):
                raise SystemExit(
                    f"boundary {index} does not exist: the run produced {len(snapshots)} turns"
                )
            state = snapshots[index]
            tensors = dict(state) if isinstance(state, dict) else {"h": state}
            read = core.read_vector(tensors)
            states.append(torch.cat([tensors["h"], read], dim=1).detach().cpu())
            reads.append(read.detach().cpu())
    return {"state": torch.cat(states, dim=0), "read": torch.cat(reads, dim=0)}


# --------------------------------------------------------------------------- #
# the readouts
# --------------------------------------------------------------------------- #
def build_probe(torch: Any, dim: int, out: int, seed: int) -> Any:
    """Seeded init, so two runs of the same file agree bit for bit."""
    torch.manual_seed(seed)
    return torch.nn.Linear(dim, out)


def fit_probe(
    torch: Any,
    probe: Any,
    features: Any,
    labels: Any,
    *,
    kind: str,
    slots: int,
    steps: int,
    batch: int,
    lr: float,
    weight_decay: float,
    seed: int,
) -> None:
    functional = torch.nn.functional
    count = int(features.shape[0])
    generator = torch.Generator().manual_seed(seed + 23)
    optimizer = torch.optim.AdamW(probe.parameters(), lr=lr, weight_decay=weight_decay)
    probe.train()
    for _ in range(steps):
        rows = torch.randint(0, count, (batch,), generator=generator)
        logits = probe(features[rows])
        if kind == "set":
            loss = functional.binary_cross_entropy_with_logits(logits, labels[rows].float())
        elif kind == "tuple":
            flat = logits.reshape(-1, int(logits.shape[1]) // slots)
            loss = functional.cross_entropy(flat, labels[rows].reshape(-1))
        else:
            loss = functional.cross_entropy(logits, labels[rows])
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()


def predict_probe(torch: Any, probe: Any, features: Any) -> Any:
    probe.eval()
    with torch.no_grad():
        return probe(features)


def score_predictions(logits: Any, targets_: Any, *, kind: str, k: int = 0) -> Dict[str, Any]:
    """Argmax, top-k exact set, or a tuple scored both per slot and as a whole.

    The tuple target is the one place two readings disagree, so both are kept:
    ``exact`` is the strict "every slot right" rate (chance ``1 / 8**k``) and
    ``slot_exact`` is the per-slot rate (chance ``1/8``). §69 gates the mapping
    on ``slot_exact`` because an exact 5-tuple is a 1/32768 event that would
    read as "absent" even when most slots are decoded; the strict rate stays in
    the JSON as the secondary.
    """
    if kind == "set":
        picked = logits.new_zeros(targets_.shape)
        picked.scatter_(1, logits.topk(k, dim=1).indices, 1.0)
        exact = int((picked == targets_).all(dim=1).sum())
        return {"n": int(targets_.shape[0]), "correct": exact}
    if kind == "tuple":
        slots = int(targets_.shape[1])
        per_slot = int(logits.shape[1]) // slots
        if per_slot * slots != int(logits.shape[1]):
            raise SystemExit(
                f"a {int(logits.shape[1])}-wide tuple readout cannot be split into {slots} slots"
            )
        picked = logits.reshape(-1, slots, per_slot).argmax(dim=2)
        hits = picked == targets_
        return {
            "n": int(targets_.shape[0]),
            "correct": int(hits.all(dim=1).sum()),
            "slot_n": int(targets_.numel()),
            "slot_correct": int(hits.sum()),
        }
    exact = int((logits.argmax(dim=1) == targets_).sum())
    return {"n": int(targets_.shape[0]), "correct": exact}


def _scored(block: Dict[str, Any]) -> Dict[str, Any]:
    scored = {**block, "exact": round(block["correct"] / max(block["n"], 1), 4)}
    if "slot_n" in block:
        scored["slot_exact"] = round(block["slot_correct"] / max(block["slot_n"], 1), 4)
    return scored


def run_probe(
    torch: Any,
    train_x: Any,
    train_y: Any,
    test_x: Any,
    test_y: Any,
    *,
    kind: str,
    out: int,
    slots: int = 0,
    seed: int,
    steps: int = PROBE_STEPS,
) -> Dict[str, Any]:
    width = out * slots if kind == "tuple" else out
    probe = build_probe(torch, int(train_x.shape[1]), width, seed)
    fit_probe(
        torch,
        probe,
        train_x,
        train_y,
        kind=kind,
        slots=slots,
        steps=steps,
        batch=PROBE_BATCH,
        lr=PROBE_LR,
        weight_decay=PROBE_WEIGHT_DECAY,
        seed=seed,
    )
    seen = score_predictions(
        predict_probe(torch, probe, train_x),
        train_y.long() if kind != "set" else train_y,
        kind=kind,
        k=slots,
    )
    unseen = score_predictions(
        predict_probe(torch, probe, test_x),
        test_y.long() if kind != "set" else test_y,
        kind=kind,
        k=slots,
    )
    return {"in_sample": _scored(seen), "heldout": _scored(unseen)}


def capacity_ceiling(
    torch: Any,
    features: Any,
    labels: Any,
    *,
    kind: str,
    out: int,
    slots: int = 0,
    steps: int = PROBE_STEPS,
) -> Dict[str, Any]:
    """The same probe on row-permuted labels: what arbitrary labels score here."""
    generator = torch.Generator().manual_seed(CAPACITY_SEED)
    permutation = torch.randperm(int(labels.shape[0]), generator=generator)
    if not bool((torch.sort(permutation).values == torch.arange(int(labels.shape[0]))).all()):
        raise SystemExit("the capacity permutation is not a bijection")
    shuffled = labels[permutation]
    width = out * slots if kind == "tuple" else out
    probe = build_probe(torch, int(features.shape[1]), width, PROBE_SEED)
    fit_probe(
        torch,
        probe,
        features,
        shuffled,
        kind=kind,
        slots=slots,
        steps=steps,
        batch=PROBE_BATCH,
        lr=PROBE_LR,
        weight_decay=PROBE_WEIGHT_DECAY,
        seed=PROBE_SEED,
    )
    block = score_predictions(
        predict_probe(torch, probe, features),
        shuffled.long() if kind != "set" else shuffled,
        kind=kind,
        k=slots,
    )
    changed = int((shuffled != labels).reshape(int(labels.shape[0]), -1).any(dim=1).sum())
    return {
        **_scored(block),
        "labels_changed": round(changed / max(int(labels.shape[0]), 1), 4),
        "permutation_is_bijection": True,
        "seed": CAPACITY_SEED,
    }


def fold_of(structure: str, keys: Sequence[str], folds: int) -> int:
    return keys.index(structure) % folds


def cross_validate(
    torch: Any,
    features: Any,
    labels: Any,
    structures: Sequence[str],
    *,
    kind: str,
    out: int,
    slots: int = 0,
    seed: int,
    folds: int = FOLDS,
    steps: int = PROBE_STEPS,
) -> Dict[str, Any]:
    """Leave-structure-out inside the training split: the in-distribution reference."""
    keys = sorted(set(structures))
    correct = 0
    total = 0
    slot_correct = 0
    slot_total = 0
    per_fold: List[float] = []
    for fold in range(folds):
        test_rows = [row for row, key in enumerate(structures) if fold_of(key, keys, folds) == fold]
        train_rows = [
            row for row, key in enumerate(structures) if fold_of(key, keys, folds) != fold
        ]
        if not test_rows or not train_rows:
            continue
        index_train = torch.as_tensor(train_rows, dtype=torch.long)
        index_test = torch.as_tensor(test_rows, dtype=torch.long)
        width = out * slots if kind == "tuple" else out
        probe = build_probe(torch, int(features.shape[1]), width, seed + fold)
        local_labels = labels[index_train]
        fit_probe(
            torch,
            probe,
            features[index_train],
            local_labels,
            kind=kind,
            slots=slots,
            steps=steps,
            batch=PROBE_BATCH,
            lr=PROBE_LR,
            weight_decay=PROBE_WEIGHT_DECAY,
            seed=seed + fold,
        )
        block = score_predictions(
            predict_probe(torch, probe, features[index_test]),
            labels[index_test].long() if kind != "set" else labels[index_test],
            kind=kind,
            k=slots,
        )
        correct += block["correct"]
        total += block["n"]
        slot_correct += int(block.get("slot_correct", 0))
        slot_total += int(block.get("slot_n", 0))
        per_fold.append(round(block["correct"] / max(block["n"], 1), 4))
    folded = {
        "exact": round(correct / max(total, 1), 4),
        "correct": correct,
        "n": total,
        "folds": per_fold,
    }
    if slot_total:
        folded["slot_exact"] = round(slot_correct / max(slot_total, 1), 4)
        folded["slot_correct"] = slot_correct
        folded["slot_n"] = slot_total
    return folded


# --------------------------------------------------------------------------- #
# chance levels and the majority baseline
# --------------------------------------------------------------------------- #
def chance_levels(colours_total: int, names_total: int, k: int) -> Dict[str, float]:
    """A uniform pick from each answer space; the tuple has a per-slot level too."""
    if colours_total <= 0 or names_total <= 0 or k <= 0 or k > names_total:
        raise SystemExit(
            f"invalid dimensions for a chance level: {colours_total}/{names_total}/{k}"
        )
    return {
        "colour": 1.0 / colours_total,
        "roster": 1.0 / math.comb(names_total, k),
        "pairing": 1.0 / (colours_total**k),
        "pairing_slot": 1.0 / colours_total,
        "culprit": 1.0 / names_total,
    }


def as_key(value: Any) -> Tuple[Any, ...]:
    """A hashable answer: tuples/sequences become tuples, scalars stay scalars."""
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return value


def majority_answer(values: Sequence[Any]) -> Any:
    counts: Dict[Any, int] = {}
    for value in values:
        key = as_key(value)
        counts[key] = counts.get(key, 0) + 1
    return max(counts.items(), key=lambda item: item[1])[0]


def majority_baseline(train_values: Sequence[Any], test_values: Sequence[Any]) -> Dict[str, Any]:
    """What a content-free rule scores: the most frequent answer in the train split.

    For tuple targets the row answer is a tuple and the per-slot answer is one
    colour; both baselines are stored so the slot gate can be compared against
    a rule that predicts the commonest colour in every slot.
    """
    top = majority_answer(train_values)
    hits = sum(1 for value in test_values if as_key(value) == top)
    baseline = {
        "prediction": list(top) if isinstance(top, tuple) else top,
        "correct": hits,
        "n": len(test_values),
        "exact": round(hits / max(len(test_values), 1), 4),
    }
    if isinstance(top, tuple):
        flat_train = [item for row in train_values for item in row]
        flat_test = [item for row in test_values for item in row]
        top_slot = majority_answer(flat_train)
        slot_hits = sum(1 for value in flat_test if value == top_slot)
        baseline["slot_prediction"] = top_slot
        baseline["slot_correct"] = slot_hits
        baseline["slot_n"] = len(flat_test)
        baseline["slot_exact"] = round(slot_hits / max(len(flat_test), 1), 4)
    return baseline


def wilson(correct: int, total: int) -> Tuple[float, float]:
    if total <= 0:
        return 0.0, 0.0
    z = 1.96
    p = correct / total
    denominator = 1.0 + z * z / total
    centre = (p + z * z / (2.0 * total)) / denominator
    margin = z * ((p * (1.0 - p) / total + z * z / (4.0 * total * total)) ** 0.5) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


# --------------------------------------------------------------------------- #
# gates and the fork
# --------------------------------------------------------------------------- #
def fact_gate(
    block: Dict[str, Any],
    baseline: Dict[str, Any],
    chance: float,
    *,
    metric: str = "exact",
) -> Dict[str, Any]:
    """One fact at one boundary: does it transfer to unseen structures?

    ``metric="slot"`` reads the tuple's per-slot accuracy; every other fact uses
    the row-exact rate. ``in_sample`` and ``capacity`` are stored next to the
    transfer verdict because they say whether a failure is informative at all
    (a probe that fits row-permuted labels just as well cannot witness absence).
    """
    if metric == "slot":
        in_sample = block["in_sample"]["slot_exact"]
        capacity = block["capacity"]["slot_exact"]
        heldout = block["heldout"]["slot_exact"]
        correct = block["heldout"]["slot_correct"]
        total = block["heldout"]["slot_n"]
        observed = baseline["slot_exact"]
    else:
        in_sample = block["in_sample"]["exact"]
        capacity = block["capacity"]["exact"]
        heldout = block["heldout"]["exact"]
        correct = block["heldout"]["correct"]
        total = block["heldout"]["n"]
        observed = baseline["exact"]
    low, high = wilson(correct, total)
    floor = max(chance, float(observed))
    capacity_limited = capacity > CAPACITY_MAX
    return {
        "metric": metric,
        "in_sample": in_sample,
        "capacity": capacity,
        "capacity_limited": capacity_limited,
        "heldout_exact": heldout,
        "wilson_lower": round(low, 4),
        "wilson_upper": round(high, 4),
        "chance": round(chance, 4),
        "baseline": round(float(observed), 4),
        "floor": round(floor, 4),
        "transfers": bool(heldout >= TRANSFER_FLOOR and low > floor),
    }


def gates(report: Dict[str, Any]) -> Dict[str, Any]:
    """§69.6, mechanically: every input is a number this file already stores."""
    k = int(report["k"])
    dims = report["dimensions"]
    chance = chance_levels(int(dims["colours"]), int(dims["names"]), k)
    baselines = report["majority_baselines"]
    carrier_unchanged = bool(report["instrument"]["carrier_unchanged"])

    colour_evidence = fact_gate(
        report["evidence_boundary"]["colour"],
        baselines["evidence_boundary.colour"],
        chance["colour"],
    )
    colour_answer = fact_gate(
        report["answer_boundary"]["colour"],
        baselines["answer_boundary.colour"],
        chance["colour"],
    )
    roster_roster = fact_gate(
        report["roster_boundary"]["roster"],
        baselines["roster_boundary.roster"],
        chance["roster"],
    )
    roster_answer = fact_gate(
        report["answer_boundary"]["roster"],
        baselines["answer_boundary.roster"],
        chance["roster"],
    )
    pairing_roster = fact_gate(
        report["roster_boundary"]["pairing"],
        baselines["roster_boundary.pairing"],
        chance["pairing_slot"],
        metric="slot",
    )
    pairing_answer = fact_gate(
        report["answer_boundary"]["pairing"],
        baselines["answer_boundary.pairing"],
        chance["pairing_slot"],
        metric="slot",
    )

    control = report["answer_boundary"]["culprit"]
    control_pass = bool(
        control["in_sample"]["exact"] >= READABLE_FLOOR
        and control["capacity"]["exact"] <= CAPACITY_MAX
        and carrier_unchanged
    )
    culprit_low, culprit_high = wilson(control["heldout"]["correct"], control["heldout"]["n"])
    return {
        "G0_positive_control": {
            "pass": control_pass,
            "in_sample": control["in_sample"]["exact"],
            "capacity": control["capacity"]["exact"],
            "floor": READABLE_FLOOR,
            "capacity_max": CAPACITY_MAX,
            "carrier_unchanged": carrier_unchanged,
            "reading": "the frozen readout can fit the one label the carrier was trained to emit",
        },
        "G1_colour_transfers_at_evidence": colour_evidence,
        "G2_colour_transfers_at_answer": colour_answer,
        "G3_roster_transfers_at_its_turn": roster_roster,
        "G4_roster_transfers_at_answer": roster_answer,
        "G5_pairing_slot_transfers_at_its_turn": pairing_roster,
        "G6_pairing_slot_transfers_at_answer": pairing_answer,
        "G7_culprit_at_answer": {
            "transfers": bool(culprit_low > (1.0 / k)),
            "heldout_exact": control["heldout"]["exact"],
            "wilson_lower": round(culprit_low, 4),
            "wilson_upper": round(culprit_high, 4),
            "roster_ceiling": round(1.0 / k, 4),
            "uniform_chance": round(chance["culprit"], 4),
            "reading": "a free linear probe at the answer must not beat the roster ceiling (§67/§68)",
        },
    }


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """§69.7, mechanically: which reading the gates select, in fixed precedence."""
    if not gate["G0_positive_control"]["pass"]:
        return {
            "id": "B0-instrument",
            "reading": (
                "the readout cannot even fit the culprit in sample ("
                f"{gate['G0_positive_control']['in_sample']} at floor "
                f"{gate['G0_positive_control']['floor']}, capacity "
                f"{gate['G0_positive_control']['capacity']} at cap "
                f"{gate['G0_positive_control']['capacity_max']}) or the carrier moved: "
                "no fact can be read from this run"
            ),
            "next": "fix the readout budget/feature view and re-run; read no fact from this run",
        }
    if gate["G7_culprit_at_answer"]["transfers"]:
        return {
            "id": "B1-contradiction-with-§67",
            "reading": (
                "a free linear probe on the head's own input transfers the culprit at the answer "
                f"boundary (Wilson lower {gate['G7_culprit_at_answer']['wilson_lower']} > 1/k "
                f"{gate['G7_culprit_at_answer']['roster_ceiling']}), which §67's roster-limited "
                "head and §68's read-only probe did not: audit the difference before anything else"
            ),
            "next": "audit this probe against §67's head and §68's read column, not the corpus",
        }
    if (
        gate["G2_colour_transfers_at_answer"]["transfers"]
        or gate["G4_roster_transfers_at_answer"]["transfers"]
    ):
        return {
            "id": "B2-answer-boundary-contradicts-§68",
            "reading": (
                "at the answer boundary the state *does* transfer a fact that §68 recorded as "
                "absent (colour "
                f"{gate['G2_colour_transfers_at_answer']['heldout_exact']}, roster "
                f"{gate['G4_roster_transfers_at_answer']['heldout_exact']}), so the difference "
                "is the feature view ([h, read] vs read alone), not the boundary"
            ),
            "next": (
                "re-run §68's read-only column beside this one and audit which half of the "
                "head's input carries it"
            ),
        }
    facts_here = (
        gate["G1_colour_transfers_at_evidence"]["transfers"]
        or gate["G3_roster_transfers_at_its_turn"]["transfers"]
    )
    mapping_here = gate["G5_pairing_slot_transfers_at_its_turn"]["transfers"]
    if (
        gate["G1_colour_transfers_at_evidence"]["transfers"]
        and gate["G3_roster_transfers_at_its_turn"]["transfers"]
        and mapping_here
    ):
        return {
            "id": "B3-held-at-their-turn-lost-by-the-answer",
            "reading": (
                "both facts and the colour-per-slot mapping transfer at the turns that state "
                f"them (colour {gate['G1_colour_transfers_at_evidence']['heldout_exact']}, "
                f"roster {gate['G3_roster_transfers_at_its_turn']['heldout_exact']}, pairing "
                f"{gate['G5_pairing_slot_transfers_at_its_turn']['heldout_exact']}) and none "
                "transfers at the answer boundary: this is retention, not representation"
            ),
            "next": (
                "bisect the turns between the evidence boundary and the answer (the question "
                "turn, the al_step gap), not re-probe the answer boundary"
            ),
        }
    if (
        gate["G1_colour_transfers_at_evidence"]["transfers"]
        and gate["G3_roster_transfers_at_its_turn"]["transfers"]
    ):
        return {
            "id": "B4-facts-held-mapping-missing",
            "reading": (
                "both facts transfer at their own turns but the colour-per-slot mapping does "
                f"not at either boundary (per-slot {gate['G5_pairing_slot_transfers_at_its_turn']['heldout_exact']} "
                f"at the roster turn, {gate['G6_pairing_slot_transfers_at_answer']['heldout_exact']} "
                "at the answer): the state holds the parts, not the relation"
            ),
            "next": (
                "probe the store's per-turn writes (is any slot keyed by the colour text) or "
                "register a relational target, not more steps"
            ),
        }
    if facts_here:
        return {
            "id": "B5-partial-facts-held",
            "reading": (
                "one fact transfers at its own turn and one does not (colour "
                f"{gate['G1_colour_transfers_at_evidence']['transfers']} at the evidence turn, "
                f"roster {gate['G3_roster_transfers_at_its_turn']['transfers']} at the roster "
                "turn), so the failure has a named location rather than a single verdict"
            ),
            "next": (
                "probe the fact that failed with a different readout family at its own turn "
                "(nonlinear, or the store values directly) before any new objective"
            ),
        }
    return {
        "id": "B6-facts-not-transferable-anywhere",
        "reading": (
            "neither fact transfers at the turn that states it (colour "
            f"{gate['G1_colour_transfers_at_evidence']['heldout_exact']}, roster "
            f"{gate['G3_roster_transfers_at_its_turn']['heldout_exact']}) while the positive "
            "control passes: the linear readout does not expose these facts even where they are "
            "written, so the boundary is not the only problem"
        ),
        "next": (
            "probe that turn's store write directly (the values, not the read) before any new "
            "objective or more training"
        ),
    }


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #
def run(
    contents: Any,
    report_path: Path,
    report: Dict[str, Any],
    *,
    device: str = "cpu",
    steps: int = PROBE_STEPS,
    folds: int = FOLDS,
) -> Dict[str, Any]:
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§69 reads the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or 2)
    selection = contents.load_selection()
    trainer = selection.load_trainer()
    probe = selection.load_probe()
    module = trainer._load_generator()
    corpus = trainer.load_corpus(
        minimal_binding=True,
        order_augmented=bool(corpus_block.get("minimal_order_augmented")),
        roster_size=k,
    )
    train = list(corpus["train"])
    heldout = list(corpus["heldout"])
    names = sorted(module.ACTORS)
    colours = sorted(module.COLOURS)

    checkpoint = Path(str(report.get("checkpoint")))
    hash_before = probe.checkpoint_sha256(checkpoint)
    core = probe.rebuild_core(trainer, report, device=device)
    weights_before = str(core.weights_hash() or "")
    started = time.time()

    torch = core._torch
    indexes = shared_boundaries(train)
    shared_boundaries(heldout)
    train_targets = targets(train, names, colours, contents)
    held_targets = targets(heldout, names, colours, contents)

    tasks: Dict[str, Dict[str, Any]] = {
        "roster": {"roster": ("set", len(names), k), "pairing": ("tuple", len(colours), k)},
        "evidence": {
            "colour": ("single", len(colours), 0),
            "roster": ("set", len(names), k),
            "pairing": ("tuple", len(colours), k),
        },
        "answer": {
            "colour": ("single", len(colours), 0),
            "roster": ("set", len(names), k),
            "pairing": ("tuple", len(colours), k),
            "culprit": ("single", len(names), 0),
        },
    }

    blocks: Dict[str, Dict[str, Any]] = {}
    baselines: Dict[str, Any] = {}
    for boundary, jobs in tasks.items():
        views = {}
        for column, key in (("state", "state"), ("read", "read")):
            train_view, held_view = contents.standardise(
                boundary_reads(trainer, contents, core, train, indexes[boundary])[key],
                boundary_reads(trainer, contents, core, heldout, indexes[boundary])[key],
            )
            views[column] = (train_view, held_view)
        blocks[boundary] = {}
        for name, (kind, out, slots) in jobs.items():

            def as_labels(values: Sequence[Any]) -> Any:
                if kind == "set":
                    return torch.as_tensor([list(row) for row in values], dtype=torch.float32)
                if kind == "tuple":
                    return torch.as_tensor([list(row) for row in values], dtype=torch.long)
                return torch.as_tensor(list(values), dtype=torch.long)

            y_train, y_held = as_labels(train_targets[name]), as_labels(held_targets[name])
            cells = {}
            for column in ("state", "read"):
                x_train, x_held = views[column]
                fitted = run_probe(
                    torch,
                    x_train,
                    y_train,
                    x_held,
                    y_held,
                    kind=kind,
                    out=out,
                    slots=slots,
                    seed=PROBE_SEED,
                    steps=steps,
                )
                ceiling = capacity_ceiling(
                    torch, x_train, y_train, kind=kind, out=out, slots=slots, steps=steps
                )
                fold_block = cross_validate(
                    torch,
                    x_train,
                    y_train,
                    train_targets["structure"],
                    kind=kind,
                    out=out,
                    slots=slots,
                    seed=PROBE_SEED,
                    folds=folds,
                    steps=steps,
                )
                cells[column] = {
                    **fitted,
                    "capacity": ceiling,
                    "in_distribution": fold_block,
                }
            blocks[boundary][name] = {**cells["state"], "read_only": cells["read"]}
            baselines[f"{boundary}_boundary.{name}"] = majority_baseline(
                train_targets[name], held_targets[name]
            )

    hash_after = probe.checkpoint_sha256(checkpoint)
    weights_after = str(core.weights_hash() or "")

    instrument = {
        "device": device,
        "weights_hash_before": weights_before,
        "weights_hash_after": weights_after,
        "carrier_unchanged": weights_after == weights_before,
        "checkpoint_sha256_before": hash_before,
        "checkpoint_sha256_after": hash_after,
        "checkpoint_unchanged": hash_before == hash_after,
        "seconds": 0.0,
    }
    outcome: Dict[str, Any] = {
        "stage": "§69 where the facts live",
        "source_report": str(report_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "dimensions": {"colours": len(colours), "names": len(names)},
        "corpus": {
            "train_digest": (corpus.get("meta") or {}).get("train_digest"),
            "heldout_digest": (corpus.get("meta") or {}).get("heldout_digest"),
            "train_items": len(train),
            "heldout_items": len(heldout),
            "train_structures": len(set(train_targets["structure"])),
            "heldout_structures": len(set(held_targets["structure"])),
        },
        "probe": {
            "architecture": "one nn.Linear per boundary, fitted twice (state view, read view)",
            "features": (
                "state = [h, read] after turn k, exactly what the carrier's output head is fed; "
                "read = the read vector alone, §68's comparability column; frozen carrier, "
                "torch.no_grad"
            ),
            "standardisation": "train-split per-dimension mean/std, applied to held-out rows",
            "steps": steps,
            "batch": PROBE_BATCH,
            "lr": PROBE_LR,
            "weight_decay": PROBE_WEIGHT_DECAY,
            "seed": PROBE_SEED,
            "folds": folds,
            "readable_floor": READABLE_FLOOR,
            "transfer_floor": TRANSFER_FLOOR,
            "capacity_max": CAPACITY_MAX,
            "gate_metric": {
                "colour": "row exact (8-way argmax)",
                "roster": "row exact (top-k set)",
                "pairing": "per-slot accuracy; strict tuple rate kept as secondary",
                "culprit": "row exact (12-way argmax), positive control only",
            },
            "chance": chance_levels(len(colours), len(names), k),
        },
        "turns": indexes,
        "roster_boundary": blocks["roster"],
        "evidence_boundary": blocks["evidence"],
        "answer_boundary": blocks["answer"],
        "majority_baselines": baselines,
        "instrument": instrument,
    }
    outcome["gates"] = gates(outcome)
    outcome["branch"] = branch(outcome["gates"])
    instrument["seconds"] = round(time.time() - started, 2)
    outcome["instrument_ok"] = bool(
        outcome["gates"]["G0_positive_control"]["pass"] and hash_before == hash_after
    )
    return outcome


# --------------------------------------------------------------------------- #
# mechanical re-check
# --------------------------------------------------------------------------- #
def check(path: Path) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    problems: List[str] = []
    for boundary, jobs in (
        ("roster_boundary", ("roster", "pairing")),
        ("evidence_boundary", ("colour", "roster", "pairing")),
        ("answer_boundary", ("colour", "roster", "pairing", "culprit")),
    ):
        block = data.get(boundary) or {}
        for name in jobs:
            if name not in block:
                problems.append(f"{boundary} has no {name} readout")
                continue
            part = block[name]
            if not part.get("in_sample") or not part.get("heldout"):
                problems.append(f"{boundary}.{name} has no in-sample/held-out block")
                continue
            if not isinstance(part["heldout"].get("exact"), (int, float)):
                problems.append(f"{boundary}.{name} has no held-out exact")
            if name == "pairing":
                for half in ("in_sample", "heldout"):
                    if not isinstance(part[half].get("slot_exact"), (int, float)):
                        problems.append(f"{boundary}.{name}.{half} has no per-slot rate")
                    if not isinstance(part[half].get("slot_n"), int):
                        problems.append(f"{boundary}.{name}.{half} has no per-slot count")
            capacity = part.get("capacity")
            if not isinstance(capacity, dict):
                problems.append(f"{boundary}.{name} has no capacity control")
            elif capacity.get("permutation_is_bijection") is not True:
                problems.append(f"{boundary}.{name}'s capacity control is not a permutation")
            elif float(capacity.get("labels_changed") or 0.0) < 0.5:
                problems.append(f"{boundary}.{name}'s capacity control kept too many labels")
            elif name == "pairing" and not isinstance(capacity.get("slot_exact"), (int, float)):
                problems.append(f"{boundary}.{name}'s capacity has no per-slot rate")
            if not isinstance(part.get("in_distribution"), dict):
                problems.append(f"{boundary}.{name} has no in-distribution reference")
            read_only = part.get("read_only")
            if not isinstance(read_only, dict):
                problems.append(f"{boundary}.{name} has no read-only comparability column")
            else:
                if not read_only.get("in_sample") or not read_only.get("heldout"):
                    problems.append(f"{boundary}.{name}.read_only has no scored halves")
                elif not isinstance(read_only["heldout"].get("exact"), (int, float)):
                    problems.append(f"{boundary}.{name}.read_only has no held-out exact")
                read_capacity = read_only.get("capacity")
                if not isinstance(read_capacity, dict) or (
                    read_capacity.get("permutation_is_bijection") is not True
                ):
                    problems.append(
                        f"{boundary}.{name}.read_only's capacity control is not a permutation"
                    )
    if not data.get("turns"):
        problems.append("the boundary turn indices are missing")
    if not data.get("majority_baselines"):
        problems.append("the majority baselines are missing")

    try:
        expected = gates(data)
    except (KeyError, TypeError, ZeroDivisionError) as error:
        problems.append(f"the stored numbers cannot be re-gated: {error}")
        return problems

    stored = data.get("gates") or {}
    for key, block in expected.items():
        for flag in ("pass", "transfers", "readable", "capacity_limited"):
            if flag in block and (stored.get(key) or {}).get(flag) != block[flag]:
                problems.append(f"gate {key}.{flag} is stale")
    fork = branch(expected)
    if (data.get("branch") or {}).get("id") != fork["id"]:
        problems.append(
            f"the branch is stale: stored {(data.get('branch') or {}).get('id')}, "
            f"recomputed {fork['id']}"
        )
    instrument = data.get("instrument") or {}
    if instrument.get("carrier_unchanged") is not True:
        problems.append("the carrier weights changed")
    if instrument.get("checkpoint_unchanged") is not True:
        problems.append("checkpoint bytes changed")
    if not data.get("instrument_ok"):
        problems.append("instrument_ok is false")
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default="", help="a finished pantry-deduction report")
    parser.add_argument("--check", default="", help="re-derive a stage-§69 JSON's verdict")
    parser.add_argument("--device", default="cpu", help="cpu is the registered device")
    parser.add_argument("--out", default="", help="write the JSON verdict here")
    args = parser.parse_args(argv)

    if args.check:
        path = Path(args.check)
        if not path.exists():
            print(f"file: {args.check}")
            print("  FAIL  the file does not exist")
            print("check: FAILED")
            return 1
        problems = check(path)
        print(f"file: {args.check}")
        for problem in problems:
            print(f"  FAIL  {problem}")
        print(f"check: {'OK' if not problems else 'FAILED'}")
        return 0 if not problems else 1

    if not args.report:
        parser.error("one of --report or --check is required")
    path = Path(args.report)
    if not path.exists():
        raise SystemExit(f"missing report: {path}")
    contents = load_contents()
    report = json.loads(path.read_text(encoding="utf-8"))
    outcome = run(contents, path, report, device=args.device)

    chance = outcome["probe"]["chance"]
    print(f"report : {path}")
    print(f"k      : {outcome['k']}   turns: {outcome['turns']}")
    print(f"probe  : {outcome['probe']['architecture']}, {outcome['probe']['steps']} steps")
    for boundary in ("roster_boundary", "evidence_boundary", "answer_boundary"):
        print()
        print(f"  {boundary}")
        print(
            f"  {'target':8s} {'in-sample':>10s} {'capacity':>9s} {'in-dist':>8s} "
            f"{'held-out':>9s} {'wilson':>16s} {'chance':>8s}"
        )
        for name, block in outcome[boundary].items():
            low, high = wilson(block["heldout"]["correct"], block["heldout"]["n"])
            print(
                f"  {name:8s} {block['in_sample']['exact']:10.4f} "
                f"{block['capacity']['exact']:9.4f} {block['in_distribution']['exact']:8.4f} "
                f"{block['heldout']['exact']:9.4f} {low:7.4f}-{high:7.4f} "
                f"{chance[name]:8.4f}"
            )
            if "slot_exact" in block["in_sample"]:
                slot_low, slot_high = wilson(
                    block["heldout"]["slot_correct"], block["heldout"]["slot_n"]
                )
                print(
                    f"  {'  (slot)':8s} {block['in_sample']['slot_exact']:10.4f} "
                    f"{block['capacity']['slot_exact']:9.4f} "
                    f"{block['in_distribution']['slot_exact']:8.4f} "
                    f"{block['heldout']['slot_exact']:9.4f} "
                    f"{slot_low:7.4f}-{slot_high:7.4f} {chance['pairing_slot']:8.4f}"
                )
            read = block["read_only"]
            read_low, read_high = wilson(read["heldout"]["correct"], read["heldout"]["n"])
            print(
                f"  {'  (read)':8s} {read['in_sample']['exact']:10.4f} "
                f"{read['capacity']['exact']:9.4f} {read['in_distribution']['exact']:8.4f} "
                f"{read['heldout']['exact']:9.4f} {read_low:7.4f}-{read_high:7.4f}"
            )
    print()
    for key, block in outcome["gates"].items():
        flag = block.get("transfers", block.get("pass"))
        print(f"  {key:38s} {'PASS' if flag else 'FAIL'}")
    print()
    print(f"branch  : {outcome['branch']['id']}")
    print(f"reading : {outcome['branch']['reading']}")
    print(f"next    : {outcome['branch']['next']}")
    print(f"cost    : {outcome['instrument']['seconds']}s on {outcome['instrument']['device']}")
    print(f"instrument_ok : {outcome['instrument_ok']}")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
        print(f"wrote   : {args.out}")
    return 0 if outcome["instrument_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
