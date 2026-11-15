#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§76: is composition limited by the *resolution* of the per-turn write?

Why this exists
---------------
§75 measured two things and named the next question. The pooled held-out cell is
carried by rosters the carrier already saw (``U2-seen-rosters-only``), and on a
second corpus seed the leave-roster-out (LRO) signal sits above its own
permutation null but far below the registered floor (``Q3-below-floor-again``).
§75.17 then named the subject: the **write** - what the store must contain for a
pair it has never seen together - not another readout family, not more epochs,
width or data.

Two things were measured before this stage was registered, and they decide the
treatment:

1. The learned write gate is **saturated**: on §73's trained k=2 carrier,
   ``sigmoid(write_gate(h))`` is 0.9964-0.9987 at every turn of every session
   (train and held-out). So forcing it to 1.0 is not a treatment at all - it
   changes the written magnitude by less than 0.4% - and that candidate was
   dropped. ``write_strength="force"`` remains in the core as a documented dead
   end, not as an arm.
2. At the roster boundary the store has received **two** turns (the sessions are
   four turns long), so ``active_slots = 2`` in §73 is structural, not a learned
   "keeps 2 of 11". What is not structural is that **14 of the 16 slots are
   empty**: the whole turn - its roster, its evidence, its values - is one
   64-dimensional vector in one slot.

So the question this stage asks is about the write's **resolution**:

* **control** - ``address="turn"``, ``write_slots=1``: §73's write. Turn ``k``
  writes the whole ``key_proj(h)`` / ``value_proj(h)`` into slot ``k``.
* **treatment** - ``address="turn"``, ``write_slots=4``: chunk ``j`` of the same
  two projections goes into slot ``k * 4 + j``, with zeros outside its own
  block. The parameter count is identical (the projections are the same linear
  maps; only the scatter differs), the corpus is identical, the initial weights
  are identical, and the parameter budget is identical.

The read is not modified. Because each chunk-slot holds zeros outside its own
block, a query's dot product sees only that chunk, so ``read_vector``
content-addresses **chunks** of a turn instead of the whole turn: the read can
weight "the name part" and "the culprit part" of the same turn differently. A
test pins the invariant that makes this a write-only change: the four chunks sum
to exactly the one-slot value the control would have written.

What this measures
------------------
For each arm, with §74's readings and §75's split:

* ``Q1``/``Q2``/``Q3`` - in-sample, held-out, and leave-roster-out against 400
  label permutations, the same alpha and the same ``0.75k`` floor §74 registered;
* ``S1``/``S2`` - the held-out cell split by whether the roster key occurs among
  the training rosters, each cell permuted within itself;
* ``store`` - ``active_slots`` on the held-out boundary (no fitted parameters).
  That is the mechanism check: 2 slots for the control (one per turn written so
  far) and 8 for the treatment (four per turn), otherwise the write was not
  changed and nothing is read.

The contrast is registered too, with a margin fixed before the run: at least
``CONTRAST_MARGIN`` (0.05 = 20 of 400 pairs) on LRO exact, in either direction,
only counts while the two arms' in-sample readings are within
``FIT_COMPARABILITY`` (0.15) of each other. Otherwise the fit difference is a
co-factor and the branch uses the treatment's own gates.

The flattened ``values`` view is the same 128 numbers in a different arrangement
of the same 1024 dimensions, so ``linear_values`` is a built-in descriptor: it
must move much less than ``linear_state``, and both deltas are recorded. That is
reported, not gated - the two arms are separately trained, so the descriptor
reads fit, not content.

What this is not
----------------
Not a capability score (core score stays 0.00/10), not a binding claim, and not
a search over write rules: exactly one treatment is registered, chosen because
14 of 16 slots are empty at the boundary, not because it is one of many
candidates.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_write76.py \\
        --control data/pantry_stage/write76/control/pantry_deduction_*.json \\
        --treatment data/pantry_stage/write76/slots4/pantry_deduction_*.json \\
        --out data/pantry_stage/write76/k2.json

    ./.venv/bin/python scripts/probe_pantry_write76.py --check data/pantry_stage/write76/k2.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOSITION = REPO_ROOT / "scripts" / "probe_pantry_composition.py"
SPLIT75 = REPO_ROOT / "scripts" / "probe_pantry_split75.py"

# §76.4, written before either arm was trained. The null, alpha and floor are
# §74's; the rest are this stage's.
NULL_DRAWS = 400
NULL_SEED = 20261125
ALPHA = 0.005
COMPOSED_OVERLAP_FRACTION = 0.75
# The contrast and the unseen floor. 0.05 on 400 pairs is 20 whole pairs; 3/24 is
# the value §75.15 showed would have cleared its stored null at p=0.002494.
CONTRAST_MARGIN = 0.05
FIT_COMPARABILITY = 0.15
UNSEEN_FLOOR = 0.125
ARMS = ("control", "treatment")
FAMILIES = ("linear_state", "linear_values", "nonlinear_quad")
# Sessions are four turns; the roster boundary sits after two of them. A write of
# one slot per turn therefore shows 2 active slots, and four show 8. The control
# allows 3 for a stray; the treatment must reach 8 or the write did not change.
SLOTS_PER_TURN = {"control": 1, "treatment": 4}
MECHANISM_MAX = {"control": 3, "treatment": 8}
STAGE = "§76 the per-turn write's resolution, at equal budget"


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_composition() -> Any:
    """§74's module: one copy of the null machinery and the three readings."""
    module = _load("pantry_write76_composition", COMPOSITION)
    for name, expected in (
        ("NULL_DRAWS", NULL_DRAWS),
        ("ALPHA", ALPHA),
        ("COMPOSED_OVERLAP_FRACTION", COMPOSED_OVERLAP_FRACTION),
        ("NULL_SEED", NULL_SEED),
    ):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(
                f"§76 was registered against {name}={expected}, §74 now has {actual}; "
                "the stages no longer share a criterion"
            )
    return module


def load_split75() -> Any:
    """§75's module: the split and the within-cell null, one copy only."""
    module = _load("pantry_write76_split75", SPLIT75)
    for name, expected in (("NULL_DRAWS", NULL_DRAWS), ("ALPHA", ALPHA)):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(f"§76 was registered against {name}={expected}, §75 now has {actual}")
    return module


def slot_median(store: Dict[str, Any]) -> float:
    counts = (store.get("active_slots") or {}).get("counts") or {}
    total = sum(int(v) for v in counts.values())
    if total <= 0:
        return 0.0
    ordered: List[int] = []
    for key, value in counts.items():
        ordered.extend([int(key)] * int(value))
    ordered.sort()
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2.0


# --------------------------------------------------------------------------- #
# one arm
# --------------------------------------------------------------------------- #
def run_arm(
    composition: Any,
    split75: Any,
    boundaries: Any,
    families: Any,
    contents: Any,
    report_path: Path,
    report: Dict[str, Any],
    *,
    arm: str,
    device: str = "cpu",
) -> Dict[str, Any]:
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm!r}")
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§76 reads the §62/§63/§64 minimal-binding corpus, not this report")
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
    indexes = boundaries.shared_boundaries(train)
    boundaries.shared_boundaries(heldout)
    train_targets = boundaries.targets(train, names, colours, contents)
    held_targets = boundaries.targets(heldout, names, colours, contents)
    train_views = families.boundary_features(trainer, contents, core, train, indexes["roster"])
    held_views = families.boundary_features(trainer, contents, core, heldout, indexes["roster"])

    y_train = torch.as_tensor([list(row) for row in train_targets["roster"]], dtype=torch.float32)
    y_held = torch.as_tensor([list(row) for row in held_targets["roster"]], dtype=torch.float32)
    rosters = families.roster_keys(train)
    split = split75.split_rows(families.roster_keys(heldout), rosters)

    readings: Dict[str, Any] = {}
    for name in FAMILIES:
        train_x, held_x = contents.standardise(
            families.feature_view(name, train_views), families.feature_view(name, held_views)
        )
        train_x = families.transform(name, train_x)
        held_x = families.transform(name, held_x)
        in_sample = composition.in_sample_reading(
            boundaries, torch, train_x, y_train, out=len(names), slots=k, draws=NULL_DRAWS
        )
        heldout_cell = composition.transfer_reading(
            boundaries,
            torch,
            train_x,
            y_train,
            held_x,
            y_held,
            out=len(names),
            slots=k,
            draws=NULL_DRAWS,
        )
        lro = composition.leave_roster_out(
            boundaries,
            torch,
            train_x,
            y_train,
            rosters,
            out=len(names),
            slots=k,
            draws=NULL_DRAWS,
        )
        # §75's subset cells score the held-out logits the same fitted probe makes.
        # The fit is the seeded §74 fit, so this is that fit's own prediction.
        fitted = composition.fit_and_predict(
            boundaries,
            torch,
            train_x,
            y_train,
            out=len(names),
            slots=k,
            seed=boundaries.PROBE_SEED,
        )
        held_logits = boundaries.predict_probe(torch, fitted, held_x)
        readings[name] = {
            "feature_dim": int(train_x.shape[1]),
            "in_sample": in_sample,
            "heldout": heldout_cell,
            "leave_roster_out": lro,
            "seen": split75.subset_reading(
                composition,
                torch,
                held_logits,
                y_held,
                split["seen_rows"],
                slots=k,
                draws=NULL_DRAWS,
            ),
            "unseen": split75.subset_reading(
                composition,
                torch,
                held_logits,
                y_held,
                split["unseen_rows"],
                slots=k,
                draws=NULL_DRAWS,
            ),
        }
        # §74's three cells are point estimates; §75 adds the interval. The two
        # subset cells already carry theirs.
        for which in ("in_sample", "heldout", "leave_roster_out"):
            block = readings[name][which]
            block["observed"] = split75.with_interval(block["observed"])

    store = families.store_shape(torch, held_views["values"], held_views["value_shape"])
    hash_after = probe.checkpoint_sha256(checkpoint)
    weights_after = str(core.weights_hash() or "")
    config = report.get("config") or {}
    instrument = {
        "arm": arm,
        "device": device,
        "write_mode": {
            "address": config.get("address"),
            "write_strength": config.get("write_strength"),
            "write_slots": config.get("write_slots"),
        },
        "weights_hash_before": weights_before,
        "weights_hash_after": weights_after,
        "carrier_unchanged": weights_after == weights_before,
        "checkpoint_sha256_before": hash_before,
        "checkpoint_sha256_after": hash_after,
        "checkpoint_unchanged": hash_before == hash_after,
        "seconds": round(time.time() - started, 3),
    }
    outcome: Dict[str, Any] = {
        "stage": STAGE,
        "arm": arm,
        "source_report": str(report_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "corpus_seed": corpus_block.get("seed"),
        "dimensions": {"colours": len(colours), "names": len(names)},
        "corpus": {
            "train_digest": (corpus.get("meta") or {}).get("train_digest"),
            "heldout_digest": (corpus.get("meta") or {}).get("heldout_digest"),
            "train_items": len(train),
            "heldout_items": len(heldout),
            "train_rosters": len(set(rosters)),
        },
        "split": {
            "rows": split["rows"],
            "seen": split["seen"],
            "unseen": split["unseen"],
            "train_rosters": split["train_rosters"],
            "unseen_rosters": split["unseen_rosters"],
        },
        "training": {
            "final_loss": (
                ((report.get("training") or {}).get("history") or [{}])[-1].get("mean_loss")
            ),
            "seconds": (report.get("training") or {}).get("seconds"),
            "steps": (report.get("training") or {}).get("steps"),
            "params": report.get("params"),
        },
        "probe": {
            "readings": "§74's in_sample / heldout / leave_roster_out, then §75's seen/unseen cells",
            "null_draws": NULL_DRAWS,
            "null_seed": NULL_SEED,
            "alpha": ALPHA,
            "gate_metric": "roster row exact (top-k set)",
            "chance": composition.chance_block(k, len(names)),
        },
        "reproduction": {
            "applicable": False,
            "equal": False,
            "reason": (
                "this stage retrains both arms on a corpus seed that neither §73 nor §75 "
                "scored, so there is no earlier cell to reproduce; N0_instrument records "
                "that instead of asserting it"
            ),
        },
        "store": store,
        "readings": readings,
        "instrument": instrument,
    }
    outcome["gates"] = arm_gates(composition, outcome, k=k)
    outcome["instrument_ok"] = bool(
        outcome["gates"]["N0_instrument"]["pass"] and outcome["gates"]["W_mechanism"]["pass"]
    )
    return outcome


# --------------------------------------------------------------------------- #
# gates and the branch
# --------------------------------------------------------------------------- #
def arm_gates(
    composition: Any, outcome: Dict[str, Any], *, k: Optional[int] = None
) -> Dict[str, Any]:
    k = int(k if k is not None else outcome["k"])
    base = composition.gates(outcome)
    instrument = outcome["instrument"]
    corpus = outcome["corpus"]
    store = outcome["store"]
    median = slot_median(store)
    limit = MECHANISM_MAX[outcome["arm"]]
    per_turn = SLOTS_PER_TURN[outcome["arm"]]
    n0 = {
        "pass": bool(
            instrument["carrier_unchanged"]
            and instrument["checkpoint_unchanged"]
            and corpus.get("train_digest")
            and corpus.get("heldout_digest")
        ),
        "carrier_unchanged": instrument["carrier_unchanged"],
        "checkpoint_unchanged": instrument["checkpoint_unchanged"],
        "corpus_digests_recorded": bool(
            corpus.get("train_digest") and corpus.get("heldout_digest")
        ),
        "reproduction_applicable": False,
        "reading": (
            "the carrier and checkpoint are unchanged across the run and the corpus digests "
            "are recorded; §73's reproduction gate cannot apply to a corpus it never scored"
        ),
    }
    mechanism = {
        "pass": bool(median <= limit) if outcome["arm"] == "control" else bool(median >= limit),
        "arm": outcome["arm"],
        "slots_per_turn": per_turn,
        "active_slots_median": median,
        "expected": (
            f"<= {limit} (one slot per turn; two turns before the roster boundary)"
            if outcome["arm"] == "control"
            else f">= {limit} (four slots per turn; two turns before the roster boundary)"
        ),
        "counts": store.get("active_slots", {}).get("counts"),
        "rank1_residual_mean": store.get("rank1_residual", {}).get("mean"),
        "reading": (
            "the write width the arm was registered with is the write width the store shows; "
            "if this fails the A/B never happened"
        ),
    }

    def cell(name: str, which: str) -> Dict[str, Any]:
        part = outcome["readings"][name][which]
        observed = part["observed"]
        return {
            "pass": bool(
                part["null"]["p_value"] < ALPHA
                and observed["exact"] > float(part["chance"]["exact"])
            ),
            "n": observed["n"],
            "exact": observed["exact"],
            "overlap": observed["overlap"],
            "wilson": observed["wilson"],
            "null_mean": part["null"]["exact"]["mean"],
            "null_max": part["null"]["exact"]["max"],
            "p_value": part["null"]["p_value"],
            "alpha": ALPHA,
            "chance": part["chance"]["exact"],
        }

    def block(which: str) -> Dict[str, Any]:
        arms = {name: cell(name, which) for name in FAMILIES}
        return {"arms": arms, "any": any(row["pass"] for row in arms.values())}

    gates = dict(base)
    gates["N0_instrument"] = n0
    gates["W_mechanism"] = mechanism
    gates["S1_seen"] = block("seen")
    gates["S2_unseen"] = block("unseen")
    # registered unseen floor: 3/24 cleared §75's stored null at p=0.002494
    gates["U_unseen_floor"] = {
        "arms": {
            name: {
                "pass": bool(
                    outcome["readings"][name]["unseen"]["observed"]["exact"] >= UNSEEN_FLOOR
                    and outcome["readings"][name]["unseen"]["null"]["p_value"] < ALPHA
                ),
                "exact": outcome["readings"][name]["unseen"]["observed"]["exact"],
                "floor": UNSEEN_FLOOR,
                "n": outcome["readings"][name]["unseen"]["observed"]["n"],
                "p_value": outcome["readings"][name]["unseen"]["null"]["p_value"],
            }
            for name in FAMILIES
        },
        "any": any(
            outcome["readings"][name]["unseen"]["observed"]["exact"] >= UNSEEN_FLOOR
            and outcome["readings"][name]["unseen"]["null"]["p_value"] < ALPHA
            for name in FAMILIES
        ),
    }
    return gates


def contrast(control: Dict[str, Any], treatment: Dict[str, Any]) -> Dict[str, Any]:
    rows: Dict[str, Any] = {}
    for name in FAMILIES:
        c = control["readings"][name]["leave_roster_out"]
        t = treatment["readings"][name]["leave_roster_out"]
        delta = round(float(t["observed"]["exact"]) - float(c["observed"]["exact"]), 4)
        fit_gap = abs(
            float(treatment["readings"][name]["in_sample"]["observed"]["exact"])
            - float(control["readings"][name]["in_sample"]["observed"]["exact"])
        )
        both_above_null = bool(c["null"]["p_value"] < ALPHA and t["null"]["p_value"] < ALPHA)
        rows[name] = {
            "control_exact": c["observed"]["exact"],
            "treatment_exact": t["observed"]["exact"],
            "delta": delta,
            "fit_gap": round(fit_gap, 4),
            "fit_comparable": bool(fit_gap <= FIT_COMPARABILITY),
            "both_above_null": both_above_null,
            "gain": bool(delta >= CONTRAST_MARGIN and both_above_null),
            "loss": bool(-delta >= CONTRAST_MARGIN and both_above_null),
        }
    readable = all(row["fit_comparable"] for row in rows.values())
    descriptors = {}
    for name in FAMILIES:
        for which in ("in_sample", "heldout", "leave_roster_out"):
            descriptors[f"{name}.{which}"] = round(
                float(treatment["readings"][name][which]["observed"]["exact"])
                - float(control["readings"][name][which]["observed"]["exact"]),
                4,
            )
    return {
        "margin": CONTRAST_MARGIN,
        "fit_comparability": FIT_COMPARABILITY,
        "readable": bool(readable),
        "gain_arms": [name for name, row in rows.items() if row["gain"]],
        "loss_arms": [name for name, row in rows.items() if row["loss"]],
        "rows": rows,
        "descriptors": descriptors,
        "reading": (
            "a >= 0.05 LRO change counts only while the two arms' in-sample readings are "
            "within 0.15; otherwise the fit difference is a co-factor and the branch uses "
            "the treatment's own gates. The descriptors are the same deltas on every cell - "
            "linear_values must move much less than linear_state, because it is the same "
            "numbers in a different arrangement; reported, not gated"
        ),
    }


def branch(
    control: Dict[str, Any], treatment: Dict[str, Any], contrast_block: Dict[str, Any]
) -> Dict[str, str]:
    """Fixed precedence, written before the run: N0 > Q1 > Q3+U > Q2 > contrast."""
    gates = treatment["gates"]
    if not (
        control["gates"]["N0_instrument"]["pass"]
        and treatment["gates"]["N0_instrument"]["pass"]
        and control["gates"]["W_mechanism"]["pass"]
        and treatment["gates"]["W_mechanism"]["pass"]
    ):
        return {
            "id": "N0-instrument",
            "reading": (
                "an arm's carrier, checkpoint or corpus record moved, or the store does not "
                "show the write width it was registered with; the A/B never happened"
            ),
            "next": "fix the instrument before reading either arm",
        }
    if not gates["Q1_relative_fit"]["any"]:
        return {
            "id": "W3-treatment-no-fit",
            "reading": (
                "the four-slot arm does not fit its own training rosters above the "
                "permutation null, so nothing can be read on top of it"
            ),
            "next": (
                "stop: the fit failure forbids more epochs, width or data (§75.7); the "
                "subject is the write rule again, not the budget"
            ),
        }
    composed = [
        name
        for name in contrast_block["rows"]
        if gates["Q2_transfer"]["arms"][name]["pass"]
        and gates["Q3_composed_from_names"]["arms"][name]["pass"]
    ]
    if composed and gates["U_unseen_floor"]["any"]:
        return {
            "id": "W1-the-write-resolution-was-the-limit",
            "reading": (
                "with four slots per turn the leave-roster-out cell reaches the registered "
                "floor and the unseen-roster cell clears 3/24, so how much of a turn one "
                f"write could hold was part of the loss ({', '.join(composed)})"
            ),
            "next": (
                "still not binding: the next registration is a third seed and a "
                "content-addressed write, and neither may be claimed from this stage"
            ),
        }
    if not gates["Q2_transfer"]["any"]:
        return {
            "id": "W6-treatment-no-transfer",
            "reading": (
                "the four-slot arm fits but does not beat the held-out label permutation "
                "null, so spending the empty slots broke transfer"
            ),
            "next": "the write rule, not the readout, is the subject; one more write rule only",
        }
    if contrast_block["readable"] and contrast_block["gain_arms"]:
        return {
            "id": "W4-partial-gain-from-resolution",
            "reading": (
                "four slots per turn raises leave-roster-out by at least the registered "
                "margin but not to the floor, so the write's resolution matters without "
                f"being sufficient ({', '.join(contrast_block['gain_arms'])})"
            ),
            "next": (
                "ask what the chunks still lack (per-name writes, not more epochs or "
                "width); do not raise the floor"
            ),
        }
    if contrast_block["readable"] and contrast_block["loss_arms"]:
        return {
            "id": "W5-resolution-hurt",
            "reading": (
                "four slots per turn is worse than the one-slot write, so the whole-turn "
                "value was the better addressable unit "
                f"({', '.join(contrast_block['loss_arms'])})"
            ),
            "next": (
                "the write's resolution is not the loss; the next stage reads what a "
                "whole-turn value carries that chunks do not"
            ),
        }
    return {
        "id": "W2-the-write-was-not-the-limit",
        "reading": (
            "four slots per turn is not further from the control than the registered "
            "margin on leave-roster-out, so how much of a turn one write holds is not what "
            "limits composition"
        ),
        "next": (
            "the limit is downstream of the store's contents; the next registration is a "
            "content-addressed (per-name) write, not more epochs, width or data"
        ),
    }


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def _check_arm(problems: List[str], outcome: Dict[str, Any]) -> None:
    arm = outcome.get("arm")
    if arm not in ARMS:
        problems.append(f"unknown arm {arm!r}")
        return
    for name in FAMILIES:
        block = outcome["readings"][name]
        for which in ("in_sample", "heldout", "leave_roster_out", "seen", "unseen"):
            part = block[which]
            observed = part["observed"]
            n = int(observed["n"])
            correct = int(observed["correct"])
            if n <= 0:
                problems.append(f"{arm}.{name}.{which} has no rows")
                continue
            if observed["exact"] != round(correct / n, 4):
                problems.append(f"{arm}.{name}.{which} exact does not equal correct/n")
            if observed["overlap"] != round(float(observed["overlap_sum"]) / n, 4):
                problems.append(f"{arm}.{name}.{which} overlap does not equal overlap_sum/n")
            null = part["null"]
            if int(null["draws"]) != NULL_DRAWS:
                problems.append(f"{arm}.{name}.{which} did not draw {NULL_DRAWS} permutations")
            if null["p_value"] != round((1 + int(null["ge"])) / (NULL_DRAWS + 1), 6):
                problems.append(f"{arm}.{name}.{which} p_value does not follow from ge/draws")
    recomputed = arm_gates_from_stored(outcome)
    for key in (
        "N0_instrument",
        "W_mechanism",
        "Q1_relative_fit",
        "Q2_transfer",
        "Q3_composed_from_names",
        "S1_seen",
        "S2_unseen",
        "U_unseen_floor",
    ):
        if json.dumps(recomputed[key], sort_keys=True) != json.dumps(
            outcome["gates"].get(key), sort_keys=True
        ):
            problems.append(f"{arm}.{key} does not re-derive from the stored readings")
    if outcome["instrument"]["carrier_unchanged"] is not True:
        problems.append(f"{arm}: carrier weights changed")
    if outcome["instrument"]["checkpoint_unchanged"] is not True:
        problems.append(f"{arm}: checkpoint bytes changed")
    if outcome["store"]["active_slots"]["counts"] != recomputed["W_mechanism"]["counts"]:
        problems.append(f"{arm}: the store counts do not match the stored block")
    declared = outcome["instrument"]["write_mode"].get("write_slots")
    if declared != SLOTS_PER_TURN[arm]:
        problems.append(
            f"{arm}: the report's write_slots is {declared!r}, registered {SLOTS_PER_TURN[arm]}"
        )


def arm_gates_from_stored(outcome: Dict[str, Any]) -> Dict[str, Any]:
    """Re-derive the gates from a stored arm without loading any carrier."""
    composition = load_composition()
    return arm_gates(composition, outcome, k=int(outcome.get("k") or 2))


def check(path: Path) -> List[str]:
    problems: List[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"not JSON: {exc}"]
    if data.get("stage") != STAGE:
        return ["this is not a §76 report"]
    probe = data.get("probe") or {}
    if int(probe.get("null_draws", -1)) != NULL_DRAWS:
        problems.append(f"null_draws is not the registered {NULL_DRAWS}")
    if float(probe.get("alpha", -1.0)) != ALPHA:
        problems.append(f"alpha is not the registered {ALPHA}")
    if float(probe.get("contrast_margin", -1.0)) != CONTRAST_MARGIN:
        problems.append("the contrast margin is not the registered one")
    if float((probe.get("composition_floor") or {}).get("overlap_fraction", -1.0)) != (
        COMPOSED_OVERLAP_FRACTION
    ):
        problems.append("the composition floor is not the registered one")
    for arm in ARMS:
        block = (data.get("arms") or {}).get(arm)
        if not block:
            problems.append(f"the {arm} arm is missing")
            continue
        _check_arm(problems, block)
    derived = contrast(data["arms"]["control"], data["arms"]["treatment"])
    if json.dumps(derived, sort_keys=True) != json.dumps(
        data.get("contrast") or {}, sort_keys=True
    ):
        problems.append("the contrast does not follow from the stored arms")
    fork = branch(data["arms"]["control"], data["arms"]["treatment"], derived)
    if (data.get("branch") or {}).get("id") != fork["id"]:
        problems.append(
            f"the branch is stale: stored {(data.get('branch') or {}).get('id')}, "
            f"recomputed {fork['id']}"
        )
    return problems


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", default="", help="the one-slot report")
    parser.add_argument("--treatment", default="", help="the four-slot report")
    parser.add_argument("--check", default="", help="re-derive a §76 JSON's verdict")
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

    if not args.control or not args.treatment:
        parser.error("--control and --treatment are required (or --check)")
    composition = load_composition()
    split75 = load_split75()
    boundaries = composition.load_boundaries()
    families = composition.load_families()
    contents = boundaries.load_contents()

    arms: Dict[str, Any] = {}
    for arm, raw in (("control", args.control), ("treatment", args.treatment)):
        report_path = Path(raw)
        if not report_path.exists():
            raise SystemExit(f"missing report: {report_path}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        arms[arm] = run_arm(
            composition,
            split75,
            boundaries,
            families,
            contents,
            report_path,
            report,
            arm=arm,
            device=args.device,
        )

    contrast_block = contrast(arms["control"], arms["treatment"])
    outcome: Dict[str, Any] = {
        "stage": STAGE,
        "probe": {
            "null_draws": NULL_DRAWS,
            "null_seed": NULL_SEED,
            "alpha": ALPHA,
            "contrast_margin": CONTRAST_MARGIN,
            "fit_comparability": FIT_COMPARABILITY,
            "unseen_floor": UNSEEN_FLOOR,
            "composition_floor": {
                "overlap_fraction": COMPOSED_OVERLAP_FRACTION,
                "overlap": round(COMPOSED_OVERLAP_FRACTION * arms["control"]["k"], 4),
            },
            "slots_per_turn": SLOTS_PER_TURN,
            "mechanism_max": MECHANISM_MAX,
            "readings": "§74's three, then §75's seen/unseen split of the held-out cell",
            "arms": {
                "control": "address=turn, write_slots=1 (§73's write, new corpus seed)",
                "treatment": "address=turn, write_slots=4 (chunk j into slot turn*4+j)",
            },
        },
        "arms": arms,
        "contrast": contrast_block,
    }
    outcome["branch"] = branch(arms["control"], arms["treatment"], contrast_block)
    outcome["instrument_ok"] = bool(
        arms["control"]["instrument_ok"] and arms["treatment"]["instrument_ok"]
    )

    for arm in ARMS:
        block = arms[arm]
        print(f"== {arm}  ({block['instrument']['write_mode']})")
        print(
            f"   corpus {block['corpus_seed']}  rosters {block['corpus']['train_rosters']}  "
            f"split {block['split']['seen']}/{block['split']['unseen']}  "
            f"active slots median {slot_median(block['store'])}  "
            f"loss {block['training']['final_loss']}"
        )
        for name in FAMILIES:
            r = block["readings"][name]
            print(
                f"   {name:16s} in {r['in_sample']['observed']['exact']:7.4f} "
                f"held {r['heldout']['observed']['exact']:7.4f} "
                f"lro {r['leave_roster_out']['observed']['exact']:7.4f} "
                f"ov {r['leave_roster_out']['observed']['overlap']:5.3f} "
                f"p {r['leave_roster_out']['null']['p_value']:.6f}  "
                f"seen {r['seen']['observed']['exact']:7.4f} "
                f"unseen {r['unseen']['observed']['exact']:7.4f}"
            )
        for key in (
            "N0_instrument",
            "W_mechanism",
            "Q1_relative_fit",
            "Q2_transfer",
            "Q3_composed_from_names",
            "S1_seen",
            "S2_unseen",
            "U_unseen_floor",
        ):
            gate = block["gates"][key]
            verdict = "PASS" if gate.get("pass", gate.get("any")) else "FAIL"
            print(f"   {key:26s} {verdict}")
    print()
    print(
        f"contrast readable: {contrast_block['readable']}"
        f"  gain {contrast_block['gain_arms']}  loss {contrast_block['loss_arms']}"
    )
    for name, row in contrast_block["rows"].items():
        print(
            f"   {name:16s} control {row['control_exact']:7.4f} treatment "
            f"{row['treatment_exact']:7.4f} delta {row['delta']:+.4f} "
            f"fit gap {row['fit_gap']:.4f}"
        )
    print()
    print(f"branch  : {outcome['branch']['id']}")
    print(f"reading : {outcome['branch']['reading']}")
    print(f"next    : {outcome['branch']['next']}")
    print(f"instrument_ok : {outcome['instrument_ok']}")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
        print(f"wrote   : {args.out}")
    return 0 if outcome["instrument_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
