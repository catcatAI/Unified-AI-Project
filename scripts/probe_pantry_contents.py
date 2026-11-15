#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§68: what does the state carry? (frozen carrier, linear readouts at the answer boundary)

Why this exists
---------------
§67 trained a roster-restricted selection head on the frozen carrier. It fitted the
400 declared items to 1.0000 and scored 0.4850 / 0.2300 on 200 unseen structures -
at chance for a k-way choice, and no better than an arm that sees only the
candidate names. The mechanical branch was R4b-fits-not-transfers.

That leaves one question, which §67.9 already named: what differs between the
states the head can fit and the states it cannot? Two readings survive, and they
are not the same claim:

1. the state carries the *facts* of a session (the observed colour, the roster
   names) but not the *pairing* between them (which name wears that colour), so a
   readout that reports a fact would succeed where a readout that looks up the
   answer fails;
2. the state carries only a *session key* (enough to tell session A from session B,
   nothing that transfers), so no readout can do better than §67 did.

This stage separates them without changing the carrier and without asking any
readout to answer the deduction a third time.

What this measures
------------------
Four readouts on the same frozen features at the **answer boundary** (the final
``read`` vector, the same vector §66/§67 examined), all with the same protocol:
fit on the 400 declared items, score on the 200 held-out structures; reference =
5-fold by *structure* inside the training split, so no fold ever sees the other
roster order of a test structure.

* ``colour``  - 8-way argmax over the colour the witness named (``COLOURS`` has 8);
* ``roster``  - 12 logits, decoded as a **top-k set** (the roster has exactly k
  members), graded as an exact set; chance is ``1 / C(12, k)``;
* ``culprit`` - 12-way argmax over the name the corpus declares correct (the
  §58/§67 control);
* ``shift``   - the §67 ``read`` head retrained on the *same* 400 items with every
  label moved to the next roster position. If it still fits 1.0000, §67's
  in-sample fit was capacity, not evidence that the state holds the mapping.

Every probe is a single ``nn.Linear`` on the standardised ``read`` vector (no
nonlinearity, no hidden layer). Two instrument lessons are built in, both
measured on the **training split only** before this stage was registered:

* the raw ``read`` vector has norm ~37, and 99.9% of its variance lies in eight
  singular directions. A fresh ``nn.Linear`` on raw features starts saturated, so
  the probe sees standardised features (train-split mean/std, the same statistics
  applied to held-out rows - no leakage);
* on that ~8-dimensional manifold a linear probe **cannot** fit arbitrary 8-way
  labels of 400 rows (measured ceiling 0.2175 for colour, 0.0500 for a top-2 set,
  0.1600 for 12-way name labels). So each target carries a ``capacity`` number:
  the same probe, same steps, same seed, on *row-permuted* labels. A low in-sample
  fit is only evidence when it sits above that ceiling, and the branch below is
  written to say so instead of calling it a fact about the state.

Transfer is judged with an effect size, not just "above chance":
``held-out exact >= 0.50`` **and** the Wilson lower bound above both the uniform
chance level and the majority-answer baseline. Anything weaker is recorded as not
transferring, because §68 asks whether a fact could be *composed* into the pairing,
and a 5% set recovery cannot.

What it is not
--------------
Not a capability score (the core score stays 0.00/10). Not a claim that the
carrier should be replaced: a probe finding "facts but no pairing" says what the
*state* holds at one boundary, and says nothing about whether a different
objective could make the pairing appear - that would need its own registered stage.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_contents.py \\
        --report data/pantry_stage/ord_arm/pantry_deduction_20261115-015751.json \\
        --out data/pantry_stage/contents68/k2.json
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
SELECTION = REPO_ROOT / "scripts" / "train_pantry_selection.py"

# §68.4, written before the scored run.
PROBE_STEPS = 2000
PROBE_BATCH = 64
PROBE_LR = 1e-3
PROBE_WEIGHT_DECAY = 1e-4
PROBE_SEED = 20261119
CAPACITY_SEED = 20261119
FOLDS = 5
READABLE_FLOOR = 0.95
TRANSFER_FLOOR = 0.50
SHIFT_FLOOR = 0.90


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_selection() -> Any:
    """§67's module: the head, the budget and the summaries are reused verbatim."""
    return _load("pantry_contents_selection", SELECTION)


# --------------------------------------------------------------------------- #
# targets and chance levels
# --------------------------------------------------------------------------- #
def structure_of(session: Dict[str, Any]) -> str:
    """The structure a row belongs to; both roster orders share one key."""
    return str(session["session_meta"].get("order_augmented_of") or session["session_id"])


def live_value(session: Dict[str, Any]) -> str:
    """The colour the witness named, read from the evidence turn's own assert."""
    turn = int(session["session_meta"]["evidence_turn"])
    for assert_ in session["turns"][turn]["asserts"]:
        if assert_.get("kind") == "seen":
            return str(assert_["value"])
    raise SystemExit(f"{session['session_id']}: no 'seen' assert on turn {turn}")


def targets(
    sessions: Sequence[Dict[str, Any]],
    names: Sequence[str],
    colours: Sequence[str],
) -> Dict[str, List[Any]]:
    """Colour index, roster multi-hot, culprit index and the structure key."""
    colour_index: List[int] = []
    roster_flags: List[List[int]] = []
    culprit_index: List[int] = []
    structures: List[str] = []
    for session in sessions:
        colour_index.append(colours.index(live_value(session)))
        roster = list(session["environment"]["actors"])
        roster_flags.append([1 if name in roster else 0 for name in names])
        culprit_index.append(names.index(session["ground_truth_oracle"]["culprit"]))
        structures.append(structure_of(session))
    return {
        "colour": colour_index,
        "roster": roster_flags,
        "culprit": culprit_index,
        "structure": structures,
    }


def chance_levels(colours_total: int, names_total: int, k: int) -> Dict[str, float]:
    """What a content-free answer scores: a uniform pick from the answer space."""
    if colours_total <= 0 or names_total <= 0 or k <= 0 or k > names_total:
        raise SystemExit(
            f"invalid dimensions for a chance level: {colours_total}/{names_total}/{k}"
        )
    return {
        "colour": 1.0 / colours_total,
        "culprit": 1.0 / names_total,
        "roster": 1.0 / math.comb(names_total, k),
    }


def majority_baselines(
    train: Dict[str, List[Any]],
    test: Dict[str, List[Any]],
    names: Sequence[str],
    colours: Sequence[str],
) -> Dict[str, Any]:
    """What a content-free rule scores: the most frequent answer in the train split."""
    colour_counts: Dict[int, int] = {}
    for value in train["colour"]:
        colour_counts[value] = colour_counts.get(value, 0) + 1
    top_colour = max(colour_counts.items(), key=lambda item: item[1])[0]
    colour_hits = sum(1 for value in test["colour"] if value == top_colour)

    name_counts: Dict[int, int] = {}
    for value in train["culprit"]:
        name_counts[value] = name_counts.get(value, 0) + 1
    top_name = max(name_counts.items(), key=lambda item: item[1])[0]
    culprit_hits = sum(1 for value in test["culprit"] if value == top_name)

    pair_counts: Dict[Tuple[int, ...], int] = {}
    for flags in train["roster"]:
        pair = tuple(index for index, flag in enumerate(flags) if flag)
        pair_counts[pair] = pair_counts.get(pair, 0) + 1
    top_pair = max(pair_counts.items(), key=lambda item: item[1])[0]
    roster_hits = sum(
        1
        for flags in test["roster"]
        if tuple(index for index, flag in enumerate(flags) if flag) == top_pair
    )
    return {
        "colour": {
            "prediction": str(colours[top_colour]),
            "correct": colour_hits,
            "n": len(test["colour"]),
            "exact": round(colour_hits / max(len(test["colour"]), 1), 4),
        },
        "roster": {
            "prediction": [names[index] for index in top_pair],
            "correct": roster_hits,
            "n": len(test["roster"]),
            "exact": round(roster_hits / max(len(test["roster"]), 1), 4),
        },
        "culprit": {
            "prediction": names[top_name],
            "correct": culprit_hits,
            "n": len(test["culprit"]),
            "exact": round(culprit_hits / max(len(test["culprit"]), 1), 4),
        },
    }


# --------------------------------------------------------------------------- #
# features and the probes
# --------------------------------------------------------------------------- #
def standardise(train_x: Any, *others: Any) -> Tuple[Any, ...]:
    """Train-split mean/std, applied unchanged to every other split."""
    mean = train_x.mean(dim=0, keepdim=True)
    std = train_x.std(dim=0, keepdim=True, unbiased=False).clamp_min(1e-6)
    return tuple((part - mean) / std for part in (train_x, *others))


def build_probe(torch: Any, dim: int, out: int, seed: int) -> Any:
    torch.manual_seed(seed)
    return torch.nn.Linear(dim, out)


def fit_probe(
    torch: Any,
    probe: Any,
    features: Any,
    labels: Any,
    *,
    kind: str,
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
            loss = functional.binary_cross_entropy_with_logits(logits, labels[rows])
        else:
            loss = functional.cross_entropy(logits, labels[rows])
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()


def predict_probe(torch: Any, probe: Any, features: Any) -> Any:
    probe.eval()
    with torch.no_grad():
        return probe(features)


def score_predictions(
    torch: Any, logits: Any, targets_: Any, *, kind: str, k: int = 0
) -> Dict[str, Any]:
    """Argmax for a single label, top-k exact set for a roster."""
    if kind == "set":
        picked = torch.zeros_like(targets_)
        picked.scatter_(1, logits.topk(k, dim=1).indices, 1.0)
        exact = int((picked == targets_).all(dim=1).sum())
    else:
        exact = int((torch.argmax(logits, dim=1) == targets_).sum())
    return {"n": int(targets_.shape[0]), "correct": exact}


def _scored(block: Dict[str, Any]) -> Dict[str, Any]:
    return {**block, "exact": round(block["correct"] / max(block["n"], 1), 4)}


def run_probe(
    torch: Any,
    train_x: Any,
    train_y: Any,
    test_x: Any,
    test_y: Any,
    *,
    kind: str,
    out: int,
    seed: int,
    k: int = 0,
    steps: int = PROBE_STEPS,
) -> Dict[str, Any]:
    """Fit on the declared items, report those rows and the held-out rows."""
    probe = build_probe(torch, int(train_x.shape[1]), out, seed)
    fit_probe(
        torch,
        probe,
        train_x,
        train_y,
        kind=kind,
        steps=steps,
        batch=PROBE_BATCH,
        lr=PROBE_LR,
        weight_decay=PROBE_WEIGHT_DECAY,
        seed=seed,
    )
    seen = score_predictions(torch, predict_probe(torch, probe, train_x), train_y, kind=kind, k=k)
    unseen = score_predictions(torch, predict_probe(torch, probe, test_x), test_y, kind=kind, k=k)
    return {"in_sample": _scored(seen), "heldout": _scored(unseen)}


def capacity_ceiling(
    torch: Any,
    features: Any,
    labels: Any,
    *,
    kind: str,
    out: int,
    k: int = 0,
    steps: int = PROBE_STEPS,
) -> Dict[str, Any]:
    """The same probe on row-permuted labels: what *arbitrary* labels score here."""
    generator = torch.Generator().manual_seed(CAPACITY_SEED)
    permutation = torch.randperm(int(labels.shape[0]), generator=generator)
    in_order = torch.sort(permutation).values == torch.arange(int(labels.shape[0]))
    if not bool(in_order.all()):  # pragma: no cover - torch contract
        raise SystemExit("the capacity permutation is not a bijection")
    shuffled = labels[permutation]
    probe = build_probe(torch, int(features.shape[1]), out, PROBE_SEED)
    fit_probe(
        torch,
        probe,
        features,
        shuffled,
        kind=kind,
        steps=steps,
        batch=PROBE_BATCH,
        lr=PROBE_LR,
        weight_decay=PROBE_WEIGHT_DECAY,
        seed=PROBE_SEED,
    )
    block = score_predictions(
        torch, predict_probe(torch, probe, features), shuffled, kind=kind, k=k
    )
    changed = (
        int((shuffled != labels).any(dim=1).sum())
        if labels.dim() > 1
        else int((shuffled != labels).sum())
    )
    return {
        **_scored(block),
        "labels_changed": round(changed / max(int(labels.shape[0]), 1), 4),
        "permutation_is_bijection": True,
        "seed": CAPACITY_SEED,
    }


def fold_of(structure: str, keys: Sequence[str], folds: int) -> int:
    """A stable fold index; both roster orders of one structure share a key."""
    return keys.index(structure) % folds


def cross_validate(
    torch: Any,
    features: Any,
    labels: Any,
    structures: Sequence[str],
    *,
    kind: str,
    out: int,
    seed: int,
    k: int = 0,
    folds: int = FOLDS,
    steps: int = PROBE_STEPS,
) -> Dict[str, Any]:
    """Leave-structure-out inside the training split: the in-distribution reference."""
    keys = sorted(set(structures))
    correct = 0
    total = 0
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
        probe = build_probe(torch, int(features.shape[1]), out, seed + fold)
        fit_probe(
            torch,
            probe,
            features[index_train],
            labels[index_train],
            kind=kind,
            steps=steps,
            batch=PROBE_BATCH,
            lr=PROBE_LR,
            weight_decay=PROBE_WEIGHT_DECAY,
            seed=seed + fold,
        )
        block = score_predictions(
            torch,
            predict_probe(torch, probe, features[index_test]),
            labels[index_test],
            kind=kind,
            k=k,
        )
        correct += block["correct"]
        total += block["n"]
        per_fold.append(round(block["correct"] / max(block["n"], 1), 4))
    return {
        "exact": round(correct / max(total, 1), 4),
        "correct": correct,
        "n": total,
        "folds": per_fold,
    }


# --------------------------------------------------------------------------- #
# the shift control
# --------------------------------------------------------------------------- #
def shift_labels(target: Any, width: int) -> Any:
    """Every label moves to the next roster position; no row keeps its label."""
    if width < 2:
        raise SystemExit("the label shift needs at least two roster positions")
    return (target + 1) % width


def shifted_culprits(
    data: Dict[str, Any],
    shifted_target: Any,
    names: Sequence[str],
    width: int,
) -> Tuple[List[str], float]:
    """The name each shifted position points at, plus the share that stays in roster."""
    picks: List[str] = []
    in_roster = 0
    for row in range(int(shifted_target.shape[0])):
        position = int(shifted_target[row])
        roster = [int(index) for index in data["roster"][row].tolist()]
        name = str(names[roster[position]])
        picks.append(name)
        if 0 <= position < len(roster) and name in {names[index] for index in roster}:
            in_roster += 1
    count = int(shifted_target.shape[0])
    return picks, round(in_roster / max(count, 1), 4)


def shift_control(
    selection: Any,
    torch: Any,
    data: Dict[str, Any],
    held: Dict[str, Any],
    names_vec: Any,
    names: Sequence[str],
    width: int,
) -> Dict[str, Any]:
    """§67's ``read`` head on the same features with every label shifted."""
    shifted = dict(data)
    shifted["target"] = shift_labels(data["target"], width)
    shifted["culprit"], in_roster = shifted_culprits(data, shifted["target"], names, width)
    count = int(data["target"].shape[0])
    changed = sum(
        1 for row in range(count) if int(shifted["target"][row]) != int(data["target"][row])
    )

    head = selection.build_head(
        torch,
        int(data["h"].shape[1]),
        int(data["read"].shape[1]),
        int(names_vec.shape[1]),
        selection.HEAD_HIDDEN,
        selection.HEAD_SEED,
    )
    curve: List[Dict[str, Any]] = []

    def observe(step: int) -> Dict[str, Any]:
        point = {
            "step": step,
            "fit_exact": selection.summarise(
                selection.predict(
                    torch, head, shifted, names_vec, names, use_h=True, use_read=True
                ),
                shifted["culprit"],
            )["exact"],
            "same_rows_true_exact": selection.summarise(
                selection.predict(torch, head, data, names_vec, names, use_h=True, use_read=True),
                data["culprit"],
            )["exact"],
        }
        curve.append(point)
        return point

    selection.fit_head(
        torch,
        head,
        shifted,
        names_vec,
        steps=selection.HEAD_STEPS,
        batch=selection.HEAD_BATCH,
        lr=selection.HEAD_LR,
        weight_decay=selection.HEAD_WEIGHT_DECAY,
        seed=selection.HEAD_SEED,
        use_h=True,
        use_read=True,
        observer=observe,
    )
    fit_picks = selection.predict(torch, head, shifted, names_vec, names, use_h=True, use_read=True)
    same_picks = selection.predict(torch, head, data, names_vec, names, use_h=True, use_read=True)
    held_picks = selection.predict(torch, head, held, names_vec, names, use_h=True, use_read=True)
    return {
        "fit": selection.summarise(fit_picks, shifted["culprit"]),
        "same_rows_true_labels": selection.summarise(same_picks, data["culprit"]),
        "heldout_true_labels": selection.summarise(held_picks, held["culprit"]),
        "steps": selection.HEAD_STEPS,
        "seed": selection.HEAD_SEED,
        "labels_changed": round(changed / max(count, 1), 4),
        "labels_in_row_roster": in_roster,
        "why_not_random_permutation": (
            "at k=2 a random permutation of the position labels leaves about half the rows on "
            "their original label, which would confound this control; the cyclic shift changes "
            "every row's label and still names a member of that row's own roster"
        ),
        "curve": curve,
    }


# --------------------------------------------------------------------------- #
# gates and the fork
# --------------------------------------------------------------------------- #
def wilson(correct: int, total: int) -> Tuple[float, float]:
    """95% Wilson interval, the same form §67 uses."""
    if total <= 0:
        return 0.0, 0.0
    z = 1.96
    p = correct / total
    denominator = 1.0 + z * z / total
    centre = (p + z * z / (2.0 * total)) / denominator
    margin = z * ((p * (1.0 - p) / total + z * z / (4.0 * total * total)) ** 0.5) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def fact_gate(report: Dict[str, Any], key: str, chance: float) -> Dict[str, Any]:
    """One fact: is it readable in sample, and does it transfer to unseen structures?"""
    block = report[key]
    low, high = wilson(block["heldout"]["correct"], block["heldout"]["n"])
    floor = max(chance, float(report["majority_baselines"][key]["exact"]))
    return {
        "readable": block["in_sample"]["exact"] >= READABLE_FLOOR,
        "in_sample": block["in_sample"]["exact"],
        "in_sample_above_capacity": (
            block["in_sample"]["exact"] > float(block["capacity"]["exact"])
        ),
        "capacity": block["capacity"]["exact"],
        "heldout_exact": block["heldout"]["exact"],
        "wilson_lower": round(low, 4),
        "wilson_upper": round(high, 4),
        "chance": round(chance, 4),
        "floor": round(floor, 4),
        "transfers": bool(block["heldout"]["exact"] >= TRANSFER_FLOOR and low > floor),
    }


def gates(report: Dict[str, Any]) -> Dict[str, Any]:
    """§68.6, mechanically: every input is a number this file already stores."""
    k = int(report["k"])
    dimensions = report["dimensions"]
    chance = chance_levels(int(dimensions["colours"]), int(dimensions["names"]), k)
    in_sample = report["culprit"]["in_sample"]["exact"]
    carrier_unchanged = bool(report["instrument"]["carrier_unchanged"])
    culprit_low, culprit_high = wilson(
        report["culprit"]["heldout"]["correct"], report["culprit"]["heldout"]["n"]
    )
    roster_ceiling = 1.0 / k
    return {
        "G1_readout_can_fit": {
            "pass": in_sample >= READABLE_FLOOR and carrier_unchanged,
            "in_sample": in_sample,
            "floor": READABLE_FLOOR,
            "capacity": report["culprit"]["capacity"]["exact"],
            "carrier_unchanged": carrier_unchanged,
        },
        "G2_shift_fits": {
            "pass": (
                report["shift"]["fit"]["exact"] >= SHIFT_FLOOR
                and report["shift"]["labels_changed"] == 1.0
                and report["shift"]["labels_in_row_roster"] == 1.0
            ),
            "value": report["shift"]["fit"]["exact"],
            "floor": SHIFT_FLOOR,
            "labels_changed": report["shift"]["labels_changed"],
            "labels_in_row_roster": report["shift"]["labels_in_row_roster"],
        },
        "G3_colour": fact_gate(report, "colour", chance["colour"]),
        "G4_roster": fact_gate(report, "roster", chance["roster"]),
        "G5_culprit_control": {
            "transfers": culprit_low > roster_ceiling,
            "wilson_lower": round(culprit_low, 4),
            "wilson_upper": round(culprit_high, 4),
            "heldout_exact": report["culprit"]["heldout"]["exact"],
            "roster_ceiling": round(roster_ceiling, 4),
            "uniform_chance": round(chance["culprit"], 4),
        },
    }


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """§68.7, mechanically: which reading the gates select."""
    if not gate["G1_readout_can_fit"]["pass"]:
        return {
            "id": "N0-instrument",
            "reading": (
                "the linear readout cannot fit the declared items (culprit in-sample "
                f"{gate['G1_readout_can_fit']['in_sample']} < {READABLE_FLOOR}) or the carrier "
                "moved: the held-out numbers cannot be interpreted"
            ),
            "next": "fix the readout; read no fact from this run",
        }
    if gate["G5_culprit_control"]["transfers"]:
        return {
            "id": "N5-contradiction",
            "reading": (
                "the unrestricted linear probe on `read` alone transfers the culprit "
                f"(Wilson lower {gate['G5_culprit_control']['wilson_lower']} > the roster ceiling "
                f"{gate['G5_culprit_control']['roster_ceiling']}), which §67 did not observe with a "
                "roster-restricted MLP: the two readouts differ (linear vs MLP, free vs "
                "restricted) and the difference has to be audited before any other reading"
            ),
            "next": "audit the difference between the §67 head and this probe, not the corpus",
        }
    if not gate["G2_shift_fits"]["pass"]:
        return {
            "id": "N4-fit-needs-true-labels",
            "reading": (
                "the §67 head does not fit the same items with shifted labels "
                f"({gate['G2_shift_fits']['value']} < {SHIFT_FLOOR}): its in-sample 1.0000 was "
                "label-dependent, so the state holds something about the true mapping that does "
                "not transfer, rather than a bare session key"
            ),
            "next": "probe the relation itself (colour -> name) at the roster and answer boundaries",
        }
    colour = gate["G3_colour"]
    roster = gate["G4_roster"]
    if colour["transfers"] and roster["transfers"]:
        return {
            "id": "N1-facts-without-pairing",
            "reading": (
                "the state carries both facts on unseen structures - the observed colour "
                f"({colour['heldout_exact']}) and the roster names ({roster['heldout_exact']}) - "
                "while the culprit stays at chance: the missing piece is the *composition* of the "
                "two, not the facts themselves"
            ),
            "next": (
                "register an objective that rewards the composition on unseen structures (and only "
                "then ask whether the pairing appears), not more steps on the same objective"
            ),
        }
    if colour["transfers"] or roster["transfers"]:
        return {
            "id": "N2-partial-facts",
            "reading": (
                "exactly one of the two facts transfers (colour "
                f"{colour['transfers']}, roster {roster['transfers']}) while the culprit stays at "
                "chance: part of the session is in the state and part is not, so the failure has a "
                "nameable location"
            ),
            "next": "probe the missing fact at the turn where it is stated, before any new objective",
        }
    if not (colour["readable"] and roster["readable"]):
        return {
            "id": "N3-facts-not-linearly-readable",
            "reading": (
                "neither fact transfers, and at least one is not even linearly readable in sample "
                f"(colour {colour['in_sample']} vs its arbitrary-label ceiling {colour['capacity']}; "
                f"roster {roster['in_sample']} vs {roster['capacity']}): at the answer boundary the "
                "read vector does not expose the input facts to a linear probe, so 'the state does "
                "not hold them' is not yet supported - the failure may be the boundary, not the state"
            ),
            "next": (
                "probe the same facts at the turns where they are stated (roster turn, evidence "
                "turn) before concluding anything about what the store holds"
            ),
        }
    return {
        "id": "N6-session-key-only",
        "reading": (
            "both facts are linearly readable in sample "
            f"(colour {colour['in_sample']}, roster {roster['in_sample']}) and neither transfers, "
            "and the culprit does not either: the state is a session key - enough to tell one "
            "session from another, nothing that carries across structures"
        ),
        "next": (
            "probe the per-turn store writes at the roster and evidence boundaries (does any slot "
            "hold the colour at all), not another readout on the same vectors"
        ),
    }


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #
def run(
    selection: Any,
    report_path: Path,
    report: Dict[str, Any],
    *,
    device: str = "cpu",
) -> Dict[str, Any]:
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§68 reads the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or 2)
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
    names_vec = selection.name_vectors(core, names, trainer)
    train_features = selection.session_features(trainer, probe, core, train, names)
    held_features = selection.session_features(trainer, probe, core, heldout, names)
    train_targets = targets(train, names, colours)
    held_targets = targets(heldout, names, colours)

    x_train, x_held = standardise(train_features["read"], held_features["read"])
    colour_out = len(colours)
    name_out = len(names)

    def as_int(values: Sequence[int]) -> Any:
        return torch.as_tensor(list(values), dtype=torch.long)

    def as_flags(values: Sequence[Sequence[int]]) -> Any:
        return torch.as_tensor([list(row) for row in values], dtype=torch.float32)

    y_colour, y_colour_held = as_int(train_targets["colour"]), as_int(held_targets["colour"])
    y_roster, y_roster_held = as_flags(train_targets["roster"]), as_flags(held_targets["roster"])
    y_culprit, y_culprit_held = as_int(train_targets["culprit"]), as_int(held_targets["culprit"])

    colour = run_probe(
        torch,
        x_train,
        y_colour,
        x_held,
        y_colour_held,
        kind="single",
        out=colour_out,
        seed=PROBE_SEED,
    )
    roster = run_probe(
        torch,
        x_train,
        y_roster,
        x_held,
        y_roster_held,
        kind="set",
        out=name_out,
        k=k,
        seed=PROBE_SEED,
    )
    culprit = run_probe(
        torch,
        x_train,
        y_culprit,
        x_held,
        y_culprit_held,
        kind="single",
        out=name_out,
        seed=PROBE_SEED,
    )
    colour_capacity = capacity_ceiling(torch, x_train, y_colour, kind="single", out=colour_out)
    roster_capacity = capacity_ceiling(torch, x_train, y_roster, kind="set", out=name_out, k=k)
    culprit_capacity = capacity_ceiling(torch, x_train, y_culprit, kind="single", out=name_out)
    colour_folds = cross_validate(
        torch,
        x_train,
        y_colour,
        train_targets["structure"],
        kind="single",
        out=colour_out,
        seed=PROBE_SEED,
    )
    roster_folds = cross_validate(
        torch,
        x_train,
        y_roster,
        train_targets["structure"],
        kind="set",
        out=name_out,
        k=k,
        seed=PROBE_SEED,
    )
    culprit_folds = cross_validate(
        torch,
        x_train,
        y_culprit,
        train_targets["structure"],
        kind="single",
        out=name_out,
        seed=PROBE_SEED,
    )
    baselines = majority_baselines(train_targets, held_targets, names, colours)
    shift = shift_control(selection, torch, train_features, held_features, names_vec, names, k)
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
        "stage": "§68 what the state carries",
        "source_report": str(report_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "dimensions": {"colours": colour_out, "names": name_out},
        "corpus": {
            "train_digest": (corpus.get("meta") or {}).get("train_digest"),
            "heldout_digest": (corpus.get("meta") or {}).get("heldout_digest"),
            "train_items": len(train),
            "heldout_items": len(heldout),
            "train_structures": len(set(train_targets["structure"])),
            "heldout_structures": len(set(held_targets["structure"])),
        },
        "probe": {
            "architecture": "one nn.Linear on the standardised read vector",
            "features": "read_vector(final state), frozen carrier, torch.no_grad",
            "standardisation": "train-split per-dimension mean/std, applied to held-out rows",
            "roster_readout": "top-k of the 12 logits, graded as an exact set",
            "steps": PROBE_STEPS,
            "batch": PROBE_BATCH,
            "lr": PROBE_LR,
            "weight_decay": PROBE_WEIGHT_DECAY,
            "seed": PROBE_SEED,
            "folds": FOLDS,
            "readable_floor": READABLE_FLOOR,
            "transfer_floor": TRANSFER_FLOOR,
            "chance": chance_levels(colour_out, name_out, k),
        },
        "colour": {**colour, "capacity": colour_capacity, "in_distribution": colour_folds},
        "roster": {**roster, "capacity": roster_capacity, "in_distribution": roster_folds},
        "culprit": {**culprit, "capacity": culprit_capacity, "in_distribution": culprit_folds},
        "majority_baselines": baselines,
        "shift": shift,
        "instrument": instrument,
    }
    outcome["gates"] = gates(outcome)
    outcome["branch"] = branch(outcome["gates"])
    instrument["seconds"] = round(time.time() - started, 2)
    outcome["instrument_ok"] = bool(
        outcome["gates"]["G1_readout_can_fit"]["pass"] and hash_before == hash_after
    )
    return outcome


# --------------------------------------------------------------------------- #
# mechanical re-check
# --------------------------------------------------------------------------- #
def check(path: Path) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    problems: List[str] = []
    for key in ("colour", "roster", "culprit"):
        block = data.get(key) or {}
        if not block.get("heldout") or not block.get("in_sample"):
            problems.append(f"{key} has no in-sample/held-out block")
            continue
        if not isinstance(block["heldout"].get("exact"), (int, float)):
            problems.append(f"{key} has no held-out exact")
        if not isinstance(block.get("capacity"), dict):
            problems.append(f"{key} has no capacity control")
        elif block["capacity"].get("permutation_is_bijection") is not True:
            problems.append(f"{key}'s capacity control is not a permutation")
        elif float(block["capacity"].get("labels_changed") or 0.0) < 0.5:
            problems.append(f"{key}'s capacity control kept too many original labels")
        if not isinstance(block.get("in_distribution"), dict):
            problems.append(f"{key} has no in-distribution reference")
    shift = data.get("shift") or {}
    if not shift.get("fit") or not shift.get("same_rows_true_labels"):
        problems.append("the shift control is missing")
    elif shift.get("labels_changed") != 1.0:
        problems.append(f"the shift did not move every label ({shift.get('labels_changed')})")
    elif shift.get("labels_in_row_roster") != 1.0:
        problems.append("a shifted label left its row's roster")
    if not data.get("majority_baselines"):
        problems.append("the majority baselines are missing")

    try:
        expected = gates(data)
    except (KeyError, TypeError, ZeroDivisionError) as error:
        problems.append(f"the stored numbers cannot be re-gated: {error}")
        return problems

    stored = data.get("gates") or {}
    for key, block in expected.items():
        flag = "transfers" if key in ("G5_culprit_control",) else "pass"
        if key in ("G3_colour", "G4_roster"):
            for sub in ("readable", "transfers", "in_sample_above_capacity"):
                if (stored.get(key) or {}).get(sub) != block.get(sub):
                    problems.append(f"gate {key}.{sub} is stale")
            continue
        if (stored.get(key) or {}).get(flag) != block.get(flag):
            problems.append(
                f"gate {key} is stale: stored {(stored.get(key) or {}).get(flag)}, "
                f"recomputed {block.get(flag)}"
            )

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
    parser.add_argument("--check", default="", help="re-derive a stage-§68 JSON's verdict")
    parser.add_argument("--device", default="cpu", help="cpu is the registered device")
    parser.add_argument("--out", default="", help="write the JSON verdict here")
    args = parser.parse_args(argv)

    if args.check:
        problems = check(Path(args.check))
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
    selection = load_selection()
    report = json.loads(path.read_text(encoding="utf-8"))
    outcome = run(selection, path, report, device=args.device)

    chance = outcome["probe"]["chance"]
    print(f"report   : {path}")
    print(f"k        : {outcome['k']}  (roster chance 1/{round(1.0 / chance['roster'])})")
    print(f"probe    : {outcome['probe']['architecture']}, {outcome['probe']['steps']} steps")
    print()
    print(
        f"  {'target':8s} {'in-sample':>10s} {'capacity':>9s} {'in-dist':>8s} "
        f"{'held-out':>9s} {'wilson':>16s} {'chance':>7s}"
    )
    for key in ("colour", "roster", "culprit"):
        block = outcome[key]
        low, high = wilson(block["heldout"]["correct"], block["heldout"]["n"])
        print(
            f"  {key:8s} {block['in_sample']['exact']:10.4f} {block['capacity']['exact']:9.4f} "
            f"{block['in_distribution']['exact']:8.4f} {block['heldout']['exact']:9.4f} "
            f"{low:7.4f}-{high:7.4f} {chance[key]:7.4f}"
        )
    print()
    print(
        f"  majority baselines: colour {outcome['majority_baselines']['colour']['exact']:.4f}  "
        f"roster {outcome['majority_baselines']['roster']['exact']:.4f}  "
        f"culprit {outcome['majority_baselines']['culprit']['exact']:.4f}"
    )
    shifted = outcome["shift"]
    print(
        f"  shift control   : fit {shifted['fit']['exact']:.4f} on shifted labels "
        f"(changed {shifted['labels_changed']:.2f}), same rows true labels "
        f"{shifted['same_rows_true_labels']['exact']:.4f}, held-out "
        f"{shifted['heldout_true_labels']['exact']:.4f}"
    )
    print()
    for key, block in outcome["gates"].items():
        if key in ("G3_colour", "G4_roster"):
            print(f"  {key:24s} readable={block['readable']} transfers={block['transfers']}")
            continue
        flag = block.get("transfers", block.get("pass"))
        print(f"  {key:24s} {'PASS' if flag else 'FAIL'}")
    print()
    print(f"branch   : {outcome['branch']['id']}")
    print(f"reading  : {outcome['branch']['reading']}")
    print(f"next     : {outcome['branch']['next']}")
    print(f"cost     : {outcome['instrument']['seconds']}s on {outcome['instrument']['device']}")
    print(f"instrument_ok : {outcome['instrument_ok']}")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
        print(f"wrote    : {args.out}")
    return 0 if outcome["instrument_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
