#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§78: at matched readout fit, does the per-item store still read better?

Why this exists
---------------
§77 asked whether the *content* one write carries limits composition: control
wrote once per turn from the turn's last token, treatment wrote once per list
item from that item's last character. The mechanism passed (2 -> 3 active slots,
rank-1 residual 0.3278 -> 0.5148, 200/200 writes landed) but the contrast was
unreadable: the treatment's ``linear_values`` in-sample fit was 0.7200 against
the control's 0.4175, a gap of 0.3025 > ``FIT_COMPARABILITY`` 0.15. §77 could
therefore not say whether the +0.2800 leave-roster-out delta was the write or
the fit.

This stage makes that comparison readable without loosening the rule. Both
carriers are frozen (§77's trained reports) and only the readout's step budget
moves:

* the *same* ``linear_values`` family, head, seed, batch and learning rate;
* a registered ladder of in-sample step budgets (250 .. 8000);
* the comparison is read at the **highest common in-sample fit**: the pair
  (control rung, treatment rung) whose in-sample fits are within
  ``FIT_MATCH_TOLERANCE`` (0.05, three times tighter than §77's 0.15) and whose
  rungs are *admissible* (the permuted-label capacity at that rung is below
  §70's 0.50 instrument cap);
* the ladder runs first and the matching uses **in-sample fit only** - no
  held-out or leave-roster-out number is computed before the pair is chosen.

Two families were already comparable at §77's 2000 steps (``linear_state`` gap
0.0375, ``nonlinear_quad`` gap 0.0075) and their readable cells showed no gain
above the 0.05 margin; ``linear_values`` is the family that made the whole
contrast unreadable, so it is the one this stage fits.

What is gated
-------------
``N0`` (frozen carriers, corpus digests, and an exact reproduction of §77's
2000-step ``linear_values`` cells), ``L`` (the ladder really sweeps: in-sample
fit is non-decreasing and spans at least 0.10), ``W1`` (a matched admissible
pair exists) and ``W2`` (both arms' matched cells are gated by their own
permutation nulls). The branch then reads the leave-roster-out overlap delta
(**primary, in the same currency as the 1.5 floor**) and the exact delta
(descriptive).

What this is not
----------------
Not a capability score (core score stays 0.00/10), not a structural
decomposition of "fit" (matching by capacity is matching on the training-set
fit, nothing more), and not a licence for more epochs, width or data: the
carriers are frozen and every rung's capacity is recorded.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_fit78.py \\
        --control data/pantry_stage/item77/control/pantry_deduction_20261116-183446.json \\
        --treatment data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json \\
        --reference data/pantry_stage/item77/k2.json \\
        --device cpu --out data/pantry_stage/fit78/k2.json

    ./.venv/bin/python scripts/probe_pantry_fit78.py --check data/pantry_stage/fit78/k2.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
ITEM77 = REPO_ROOT / "scripts" / "probe_pantry_item77.py"

# §78.4, written before the scored run. 2000 is §77's registered point (the
# anchor); the ladder brackets it by powers of two so the fit curve is not
# sampled only where §77 happened to sit.
STEPS_LADDER = (250, 500, 1000, 2000, 4000, 8000)
ANCHOR_STEPS = 2000
FAMILY = "linear_values"
# Three times tighter than §77's FIT_COMPARABILITY 0.15; the same "20 rows on
# 400" scale as CONTRAST_MARGIN.
FIT_MATCH_TOLERANCE = 0.05
CONTRAST_MARGIN = 0.05
LADDER_SPAN_MIN = 0.10
COMPOSED_OVERLAP_FRACTION = 0.75
CAPACITY_MAX = 0.50
MONOTONE_TOLERANCE = 1e-6
NULL_DRAWS = 400
NULL_SEED = 20261125
ALPHA = 0.005
ARMS = ("control", "treatment")
STAGE = "§78 at matched readout fit: does the per-item store still read better?"


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_item77() -> Any:
    """§77's module: the corpus loader, the feature views, the registered arms."""
    module = _load("pantry_fit78_item77", ITEM77)
    for name, expected in (
        ("NULL_DRAWS", NULL_DRAWS),
        ("ALPHA", ALPHA),
        ("COMPOSED_OVERLAP_FRACTION", COMPOSED_OVERLAP_FRACTION),
        ("NULL_SEED", NULL_SEED),
    ):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(f"§77's {name} is {actual!r}, §78 registers {expected!r}")
    return module


# --------------------------------------------------------------------------- #
# the readout at a registered step budget
# --------------------------------------------------------------------------- #
def fit_at(
    boundaries: Any,
    torch: Any,
    features: Any,
    labels: Any,
    *,
    out: int,
    slots: int,
    steps: int,
) -> Any:
    """§70's probe, unchanged except that the step budget is a parameter.

    Everything else (seeded init, batch, learning rate, weight decay, the
    optimiser's own generator) is §74's, so the 2000-step cell is the same
    arithmetic §77 stored.
    """
    probe = boundaries.build_probe(torch, int(features.shape[1]), out, boundaries.PROBE_SEED)
    boundaries.fit_probe(
        torch,
        probe,
        features,
        labels,
        kind="set",
        slots=slots,
        steps=int(steps),
        batch=boundaries.PROBE_BATCH,
        lr=boundaries.PROBE_LR,
        weight_decay=boundaries.PROBE_WEIGHT_DECAY,
        seed=boundaries.PROBE_SEED,
    )
    return probe


def in_sample_reading(
    composition: Any,
    boundaries: Any,
    torch: Any,
    features: Any,
    labels: Any,
    *,
    out: int,
    slots: int,
    steps: int,
    draws: int,
) -> Dict[str, Any]:
    """§74's ``in_sample_reading`` with the step budget threaded through."""
    probe = fit_at(boundaries, torch, features, labels, out=out, slots=slots, steps=steps)
    observed = composition.score_set(
        boundaries.predict_probe(torch, probe, features), labels, slots
    )
    null_draws: List[Dict[str, Any]] = []
    for draw in range(draws):
        shuffled = composition.permute_rows(torch, labels, NULL_SEED + draw)
        local = fit_at(boundaries, torch, features, shuffled, out=out, slots=slots, steps=steps)
        null_draws.append(
            composition.score_set(boundaries.predict_probe(torch, local, features), shuffled, slots)
        )
    return {"observed": observed, "null": composition.null_block(observed, null_draws)}


def transfer_reading(
    composition: Any,
    boundaries: Any,
    torch: Any,
    train_x: Any,
    train_y: Any,
    held_x: Any,
    held_y: Any,
    *,
    out: int,
    slots: int,
    steps: int,
    draws: int,
) -> Dict[str, Any]:
    """§74's ``transfer_reading`` with the step budget threaded through."""
    probe = fit_at(boundaries, torch, train_x, train_y, out=out, slots=slots, steps=steps)
    logits = boundaries.predict_probe(torch, probe, held_x)
    observed = composition.score_set(logits, held_y, slots)
    null_draws = [
        composition.score_set(
            logits, composition.permute_rows(torch, held_y, NULL_SEED + draw), slots
        )
        for draw in range(draws)
    ]
    return {"observed": observed, "null": composition.null_block(observed, null_draws)}


def leave_roster_out(
    composition: Any,
    boundaries: Any,
    torch: Any,
    features: Any,
    labels: Any,
    rosters: Sequence[Tuple[str, ...]],
    *,
    out: int,
    slots: int,
    steps: int,
    draws: int,
) -> Dict[str, Any]:
    """§74's ``leave_roster_out`` with the step budget threaded through."""
    groups: Dict[Tuple[str, ...], List[int]] = {}
    for row, key in enumerate(rosters):
        groups.setdefault(tuple(key), []).append(row)
    predictions: List[Any] = []
    order: List[int] = []
    per_fold: List[Dict[str, Any]] = []
    for key in sorted(groups):
        held_rows = groups[key]
        held_set = set(held_rows)
        train_rows = [row for row in range(int(labels.shape[0])) if row not in held_set]
        if not train_rows or not held_rows:
            continue
        train_index = torch.as_tensor(train_rows, dtype=torch.long)
        held_index = torch.as_tensor(held_rows, dtype=torch.long)
        probe = fit_at(
            boundaries,
            torch,
            features[train_index],
            labels[train_index],
            out=out,
            slots=slots,
            steps=steps,
        )
        logits = boundaries.predict_probe(torch, probe, features[held_index])
        block = composition.score_set(logits, labels[held_index], slots)
        per_fold.append(
            {
                "roster": list(key),
                "n": block["n"],
                "correct": block["correct"],
                "overlap": block["overlap"],
            }
        )
        predictions.append(logits)
        order.extend(held_rows)
    if not predictions:
        raise SystemExit("leave-roster-out had nothing to evaluate")

    index = torch.as_tensor(order, dtype=torch.long)
    pooled_logits = torch.cat(predictions, dim=0)
    pooled_labels = labels[index]
    observed = composition.score_set(pooled_logits, pooled_labels, slots)
    null_draws = [
        composition.score_set(
            pooled_logits, composition.permute_rows(torch, pooled_labels, NULL_SEED + draw), slots
        )
        for draw in range(draws)
    ]
    sizes = [len(rows_) for rows_ in groups.values()]
    return {
        "observed": observed,
        "null": composition.null_block(observed, null_draws),
        "rosters": len(groups),
        "fold_size": {
            "min": min(sizes),
            "max": max(sizes),
            "median": sorted(sizes)[len(sizes) // 2],
        },
        "per_fold": per_fold,
    }


# --------------------------------------------------------------------------- #
# the fit ladder (phase A: in-sample only)
# --------------------------------------------------------------------------- #
def fit_ladder(
    boundaries: Any,
    composition: Any,
    torch: Any,
    train_x: Any,
    train_y: Any,
    *,
    out: int,
    slots: int,
    steps_list: Sequence[int] = STEPS_LADDER,
) -> List[Dict[str, Any]]:
    """One fit per rung: the in-sample cell and the permuted-label capacity.

    Phase A deliberately reads **no** held-out or leave-roster-out number: the
    matching pair must be chosen from training-side fit alone, or the choice
    would be made with the thing it is supposed to control.
    """
    rows: List[Dict[str, Any]] = []
    for steps in steps_list:
        probe = fit_at(boundaries, torch, train_x, train_y, out=out, slots=slots, steps=steps)
        block = composition.score_set(
            boundaries.predict_probe(torch, probe, train_x), train_y, slots
        )
        ceiling = boundaries.capacity_ceiling(
            torch, train_x, train_y, kind="set", out=out, slots=slots, steps=int(steps)
        )
        rows.append(
            {
                "steps": int(steps),
                "in_sample_correct": int(block["correct"]),
                "in_sample_n": int(block["n"]),
                "in_sample_exact": float(block["exact"]),
                "capacity_correct": int(ceiling["correct"]),
                "capacity_exact": float(ceiling["exact"]),
                "admissible": bool(float(ceiling["exact"]) < CAPACITY_MAX),
            }
        )
    return rows


def ladder_effective(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    fits = [float(row["in_sample_exact"]) for row in rows]
    monotone = all(
        fits[index] + MONOTONE_TOLERANCE >= fits[index - 1] for index in range(1, len(fits))
    )
    span = round(max(fits) - min(fits), 6) if fits else 0.0
    return {
        "pass": bool(monotone and span >= LADDER_SPAN_MIN),
        "monotone": bool(monotone),
        "span": span,
        "span_floor": LADDER_SPAN_MIN,
        "fits": fits,
    }


# --------------------------------------------------------------------------- #
# the matching rule (chosen from phase A only)
# --------------------------------------------------------------------------- #
def match_pair(
    control: Sequence[Dict[str, Any]],
    treatment: Sequence[Dict[str, Any]],
    *,
    tolerance: float = FIT_MATCH_TOLERANCE,
) -> Dict[str, Any]:
    """Highest common in-sample fit among admissible rungs.

    Ties are broken by the smaller gap, then by the smaller total step budget,
    so the rule is a total order on the registered ladder. A pair is admissible
    only when neither rung fits permuted labels at or above §70's cap: a rung
    that can memorise arbitrary labels cannot support a comparison at all.
    """
    best: Optional[Tuple[Tuple[float, float, int], Dict[str, Any], Dict[str, Any]]] = None
    for left in control:
        if not left["admissible"]:
            continue
        for right in treatment:
            if not right["admissible"]:
                continue
            gap = abs(float(left["in_sample_exact"]) - float(right["in_sample_exact"]))
            if gap > tolerance + 1e-12:
                continue
            level = min(float(left["in_sample_exact"]), float(right["in_sample_exact"]))
            key = (level, -gap, -(int(left["steps"]) + int(right["steps"])))
            if best is None or key > best[0]:
                best = (key, left, right)
    if best is None:
        ceiling = max(
            (float(row["in_sample_exact"]) for row in control if row["admissible"]), default=0.0
        )
        admissible_steps = [int(row["steps"]) for row in control if row["admissible"]]
        return {
            "found": False,
            "tolerance": tolerance,
            "control_ceiling": round(ceiling, 4),
            "control_admissible_steps": admissible_steps,
            "reason": (
                "no admissible pair is within the registered tolerance: the control's best "
                "admissible in-sample fit is below the treatment's fit at every admissible rung"
            ),
        }
    _, left, right = best
    gap = abs(float(left["in_sample_exact"]) - float(right["in_sample_exact"]))
    return {
        "found": True,
        "control_steps": int(left["steps"]),
        "treatment_steps": int(right["steps"]),
        "control_fit": float(left["in_sample_exact"]),
        "treatment_fit": float(right["in_sample_exact"]),
        "gap": round(gap, 4),
        "level": round(min(float(left["in_sample_exact"]), float(right["in_sample_exact"])), 4),
        "tolerance": tolerance,
    }


# --------------------------------------------------------------------------- #
# phase B: the full cell at a rung
# --------------------------------------------------------------------------- #
def full_cell(
    item77: Any,
    boundaries: Any,
    composition: Any,
    split75: Any,
    torch: Any,
    train_x: Any,
    train_y: Any,
    held_x: Any,
    held_y: Any,
    rosters: Sequence[Tuple[str, ...]],
    split: Dict[str, Any],
    *,
    out: int,
    slots: int,
    steps: int,
    draws: int = NULL_DRAWS,
) -> Dict[str, Any]:
    in_sample = in_sample_reading(
        composition,
        boundaries,
        torch,
        train_x,
        train_y,
        out=out,
        slots=slots,
        steps=steps,
        draws=draws,
    )
    heldout = transfer_reading(
        composition,
        boundaries,
        torch,
        train_x,
        train_y,
        held_x,
        held_y,
        out=out,
        slots=slots,
        steps=steps,
        draws=draws,
    )
    lro = leave_roster_out(
        composition,
        boundaries,
        torch,
        train_x,
        train_y,
        rosters,
        out=out,
        slots=slots,
        steps=steps,
        draws=draws,
    )
    fitted = fit_at(boundaries, torch, train_x, train_y, out=out, slots=slots, steps=steps)
    held_logits = boundaries.predict_probe(torch, fitted, held_x)
    seen = split75.subset_reading(
        composition, torch, held_logits, held_y, split["seen_rows"], slots=slots, draws=draws
    )
    unseen = split75.subset_reading(
        composition, torch, held_logits, held_y, split["unseen_rows"], slots=slots, draws=draws
    )
    cell = {
        "steps": int(steps),
        "in_sample": in_sample,
        "heldout": heldout,
        "leave_roster_out": lro,
        "seen": seen,
        "unseen": unseen,
    }
    for which in ("in_sample", "heldout", "leave_roster_out"):
        cell[which]["observed"] = split75.with_interval(cell[which]["observed"])
    return cell


# --------------------------------------------------------------------------- #
# one arm: corpus, frozen carrier, features, ladder
# --------------------------------------------------------------------------- #
def run_arm(
    item77: Any,
    families: Any,
    boundaries: Any,
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
        raise SystemExit("§78 reads the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or 2)
    seed = int(corpus_block.get("seed") or 0)
    if seed <= 0:
        raise SystemExit("the report does not record its corpus seed; §78 cannot read it")

    selection = contents.load_selection()
    trainer = selection.load_trainer()
    probe = selection.load_probe()
    module = trainer._load_generator()
    corpus = trainer.load_corpus(
        minimal_binding=True,
        order_augmented=bool(corpus_block.get("minimal_order_augmented")),
        roster_size=k,
        seed=seed,
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
    train_x, held_x = contents.standardise(
        families.feature_view(FAMILY, train_views), families.feature_view(FAMILY, held_views)
    )
    # Identity for ``linear_values`` (only ``nonlinear_quad`` expands), kept here
    # so this arm builds its features exactly the way §77's did.
    train_x = families.transform(FAMILY, train_x)
    held_x = families.transform(FAMILY, held_x)
    y_train = torch.as_tensor([list(row) for row in train_targets["roster"]], dtype=torch.float32)
    y_held = torch.as_tensor([list(row) for row in held_targets["roster"]], dtype=torch.float32)
    rosters = families.roster_keys(train)
    split75 = item77.load_split75()
    split = split75.split_rows(families.roster_keys(heldout), rosters)

    composition = item77.load_composition()
    ladder = fit_ladder(boundaries, composition, torch, train_x, y_train, out=len(names), slots=k)

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
        "registered": dict(item77.REGISTERED[arm]),
        "mode_matches": bool(
            config.get("address") == item77.REGISTERED[arm]["address"]
            and config.get("write_strength") == item77.REGISTERED[arm]["write_strength"]
            and int(config.get("write_slots") or 1) == item77.REGISTERED[arm]["write_slots"]
        ),
        "weights_hash_before": weights_before,
        "weights_hash_after": weights_after,
        "carrier_unchanged": weights_after == weights_before,
        "checkpoint_sha256_before": hash_before,
        "checkpoint_sha256_after": hash_after,
        "checkpoint_unchanged": hash_before == hash_after,
        "ladder_seconds": round(time.time() - started, 3),
    }
    meta = corpus.get("meta") or {}
    corpus_recomputed = {
        "train_digest": meta.get("train_digest"),
        "heldout_digest": meta.get("heldout_digest"),
        "seed": seed,
    }
    digests_match = bool(
        corpus_recomputed["train_digest"] == corpus_block.get("train_digest")
        and corpus_recomputed["heldout_digest"] == corpus_block.get("heldout_digest")
    )
    return {
        "arm": arm,
        "source_report": str(report_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "dimensions": {"colours": len(colours), "names": len(names)},
        "corpus": {
            "train_digest": corpus_recomputed["train_digest"],
            "heldout_digest": corpus_recomputed["heldout_digest"],
            "recorded_train_digest": corpus_block.get("train_digest"),
            "recorded_heldout_digest": corpus_block.get("heldout_digest"),
            "digests_match": digests_match,
            "seed": seed,
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
        "instrument": instrument,
        "ladder": ladder,
        "torch": torch,
        "features": {
            "train_x": train_x,
            "held_x": held_x,
            "y_train": y_train,
            "y_held": y_held,
            "rosters": rosters,
            "split": split,
        },
    }


# --------------------------------------------------------------------------- #
# anchor reproduction (§77's stored 2000-step cells)
# --------------------------------------------------------------------------- #
def anchor_reference(reference_path: Path) -> Dict[str, Any]:
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    if reference.get("stage") != "§77 the content written per turn: one write per list item":
        raise SystemExit("the reference is not §77's stored report")
    copied: Dict[str, Any] = {}
    for arm in ARMS:
        readings = (reference.get("arms") or {}).get(arm, {}).get("readings") or {}
        block = readings.get(FAMILY)
        if not block:
            raise SystemExit(f"the reference has no {FAMILY} cell for the {arm} arm")
        copied[arm] = {
            "in_sample": float(block["in_sample"]["observed"]["exact"]),
            "heldout": float(block["heldout"]["observed"]["exact"]),
            "lro_exact": float(block["leave_roster_out"]["observed"]["exact"]),
            "lro_overlap": float(block["leave_roster_out"]["observed"]["overlap"]),
        }
    return {"path": str(reference_path), "cells": copied}


def reproduction(cells: Dict[str, Any], reference: Dict[str, Any]) -> Dict[str, Any]:
    compared: Dict[str, Any] = {}
    equal = True
    for arm in ARMS:
        cell = (cells.get(arm) or {}).get(str(ANCHOR_STEPS))
        expected = reference["cells"][arm]
        if cell is None:
            equal = False
            compared[arm] = {"equal": False, "reason": "the anchor cell was not computed"}
            continue
        actual = {
            "in_sample": float(cell["in_sample"]["observed"]["exact"]),
            "heldout": float(cell["heldout"]["observed"]["exact"]),
            "lro_exact": float(cell["leave_roster_out"]["observed"]["exact"]),
            "lro_overlap": float(cell["leave_roster_out"]["observed"]["overlap"]),
        }
        same = all(abs(actual[key] - float(expected[key])) < 1e-9 for key in expected)
        equal = equal and same
        compared[arm] = {"expected": expected, "actual": actual, "equal": bool(same)}
    return {"equal": bool(equal), "cells": compared}


# --------------------------------------------------------------------------- #
# gates and branch
# --------------------------------------------------------------------------- #
def cell_delta(cells: Dict[str, Any], match: Dict[str, Any], *, k: int) -> Dict[str, Any]:
    control = cells["control"][str(match["control_steps"])]
    treatment = cells["treatment"][str(match["treatment_steps"])]
    control_overlap = float(control["leave_roster_out"]["observed"]["overlap"])
    treatment_overlap = float(treatment["leave_roster_out"]["observed"]["overlap"])
    control_exact = float(control["leave_roster_out"]["observed"]["exact"])
    treatment_exact = float(treatment["leave_roster_out"]["observed"]["exact"])
    floor = round(COMPOSED_OVERLAP_FRACTION * k, 4)
    return {
        "control_overlap": control_overlap,
        "treatment_overlap": treatment_overlap,
        "overlap_delta": round(treatment_overlap - control_overlap, 4),
        "control_exact": control_exact,
        "treatment_exact": treatment_exact,
        "exact_delta": round(treatment_exact - control_exact, 4),
        "gain": bool(treatment_overlap - control_overlap >= CONTRAST_MARGIN),
        "above_floor": bool(treatment_overlap >= floor),
        "floor": floor,
    }


def _gated(cell: Dict[str, Any], chance: Dict[str, float]) -> Dict[str, Any]:
    fit = cell["in_sample"]
    held = cell["heldout"]
    lro = cell["leave_roster_out"]
    return {
        "pass": bool(
            float(fit["null"]["p_value"]) < ALPHA
            and float(held["null"]["p_value"]) < ALPHA
            and float(held["observed"]["exact"]) > float(chance["exact"])
            and float(lro["null"]["p_value"]) < ALPHA
        ),
        "fit_p": float(fit["null"]["p_value"]),
        "heldout_p": float(held["null"]["p_value"]),
        "heldout_exact": float(held["observed"]["exact"]),
        "chance": float(chance["exact"]),
        "lro_p": float(lro["null"]["p_value"]),
    }


def gates(outcome: Dict[str, Any]) -> Dict[str, Any]:
    k = int(outcome["k"])
    chance = (outcome["probe"] or {}).get("chance") or {}
    ladder = outcome.get("ladder") or {}
    match = outcome.get("match") or {}
    cells = outcome.get("cells") or {}
    # A report can be tampered with or hand-edited, so every read here tolerates
    # a missing block: ``check()`` must report the inconsistency, not crash on it.
    instrument = {arm: (ladder.get(arm) or {}).get("instrument") or {} for arm in ARMS}
    corpus = {arm: (ladder.get(arm) or {}).get("corpus") or {} for arm in ARMS}

    n0 = {
        "pass": bool(
            all(
                instrument[arm].get(key) is True
                for arm in ARMS
                for key in ("carrier_unchanged", "checkpoint_unchanged", "mode_matches")
            )
            and all(corpus[arm].get("digests_match") is True for arm in ARMS)
            and bool((outcome.get("anchor") or {}).get("reproduction", {}).get("equal"))
        ),
        "carriers_unchanged": all(instrument[arm].get("carrier_unchanged") is True for arm in ARMS),
        "checkpoints_unchanged": all(
            instrument[arm].get("checkpoint_unchanged") is True for arm in ARMS
        ),
        "modes_match": all(instrument[arm].get("mode_matches") is True for arm in ARMS),
        "digests_match": all(corpus[arm].get("digests_match") is True for arm in ARMS),
        "anchor_reproduced": bool(
            (outcome.get("anchor") or {}).get("reproduction", {}).get("equal")
        ),
    }
    effective = {arm: ladder_effective((ladder.get(arm) or {}).get("ladder") or []) for arm in ARMS}
    l_gate = {
        "pass": bool(all(block["pass"] for block in effective.values())),
        "arms": effective,
        "span_floor": LADDER_SPAN_MIN,
        "monotone_tolerance": MONOTONE_TOLERANCE,
    }
    w1 = {
        "pass": bool(match.get("found")),
        "tolerance": FIT_MATCH_TOLERANCE,
        "match": match,
    }
    matched: Dict[str, Dict[str, Any]] = {}
    if match.get("found"):
        for arm in ARMS:
            part = (cells.get(arm) or {}).get(str(match.get(f"{arm}_steps")))
            if part is None:
                matched = {}
                break
            matched[arm] = part
    if matched:
        delta = cell_delta(cells, match, k=k)
        gated = {arm: _gated(block, chance) for arm, block in matched.items()}
        w2 = {
            "pass": bool(all(block["pass"] for block in gated.values())),
            "arms": gated,
            "alpha": ALPHA,
        }
    else:
        delta = None
        w2 = {
            "pass": False,
            "arms": {},
            "alpha": ALPHA,
            "reason": (
                "no matched pair, so no cell to gate"
                if not match.get("found")
                else "the matched rung's cell is missing, so there is nothing to gate"
            ),
        }
    return {
        "N0_instrument": n0,
        "L_ladder_effective": l_gate,
        "W1_match_found": w1,
        "W2_matched_cells_gated": w2,
        "delta": delta,
        "CONTRAST_MARGIN": CONTRAST_MARGIN,
        "COMPOSED_OVERLAP_FRACTION": COMPOSED_OVERLAP_FRACTION,
        "FIT_MATCH_TOLERANCE": FIT_MATCH_TOLERANCE,
        "LADDER_SPAN_MIN": LADDER_SPAN_MIN,
        "ALPHA": ALPHA,
        "CAPACITY_MAX": CAPACITY_MAX,
        "STEPS_LADDER": list(STEPS_LADDER),
        "ANCHOR_STEPS": ANCHOR_STEPS,
        "FAMILY": FAMILY,
    }


BRANCH_ORDER = (
    "F0-instrument",
    "F1-fit-not-matchable",
    "F5-ungated-at-matched-fit",
    "F2-gain-above-floor-at-matched-fit",
    "F3-gain-below-floor-at-matched-fit",
    "F4-fit-explains-the-delta",
)


def branch(gate: Dict[str, Any]) -> Dict[str, Any]:
    """Fixed precedence; the first matching row wins."""
    if not gate["N0_instrument"]["pass"] or not gate["L_ladder_effective"]["pass"]:
        return {
            "id": "F0-instrument",
            "reading": "the frozen carriers, the corpus or the ladder is wrong; no cell is read",
            "next": (
                "fix the instrument (hashes, digests, the 2000-step reproduction, the ladder's "
                "monotonicity), then re-run; do not read W1 or the delta"
            ),
        }
    if not gate["W1_match_found"]["pass"]:
        return {
            "id": "F1-fit-not-matchable",
            "reading": (
                "no admissible rung of the control reaches the treatment's in-sample fit within "
                "the registered tolerance: the fit gap is a property of the two feature sets, not "
                "of readout capacity, so this family cannot compare them at equal fit"
            ),
            "next": (
                "a readout that removes the treatment's extra fit by construction (a fixed "
                "rank-1/SVD projection of the value matrix), not more steps"
            ),
        }
    if not gate["W2_matched_cells_gated"]["pass"]:
        return {
            "id": "F5-ungated-at-matched-fit",
            "reading": (
                "a matched admissible pair exists, but at least one arm's matched cell is not "
                "gated by its own permutation nulls, so its delta is not readable"
            ),
            "next": "read the matched cell's nulls before reading any delta; do not widen the ladder after the fact",
        }
    delta = gate["delta"]
    if delta["gain"] and delta["above_floor"]:
        return {
            "id": "F2-gain-above-floor-at-matched-fit",
            "reading": (
                "at equal in-sample fit the per-item store reads a higher leave-roster-out "
                "overlap, and the treatment crosses the composition floor: the §77 delta "
                "survives fit matching"
            ),
            "next": (
                "still not a binding claim: replicate on a second corpus seed and a name-indexed "
                "readout, without adding budget"
            ),
        }
    if delta["gain"]:
        return {
            "id": "F3-gain-below-floor-at-matched-fit",
            "reading": (
                "at equal in-sample fit the per-item store reads a higher overlap, but it stays "
                "below the registered composition floor: the write helps and is still not enough"
            ),
            "next": "ask what one item still lacks (value-to-name pairing in the same entry), without adding budget",
        }
    return {
        "id": "F4-fit-explains-the-delta",
        "reading": (
            "at equal in-sample fit the per-item store does not read a higher overlap: §77's "
            "+0.2800 was co-variation with the treatment's easier fit, not a composition gain"
        ),
        "next": (
            "the readout end: a slot-addressed readout (score each slot against a candidate name "
            "instead of pooling the flattened store), not another write rule and not more budget"
        ),
    }


# --------------------------------------------------------------------------- #
# mechanical re-check
# --------------------------------------------------------------------------- #
def _check_cell(problems: List[str], arm: str, steps: str, cell: Dict[str, Any]) -> None:
    for which in ("in_sample", "heldout", "leave_roster_out", "seen", "unseen"):
        part = cell[which]
        observed = part["observed"]
        n = int(observed["n"])
        correct = int(observed["correct"])
        if n <= 0:
            problems.append(f"{arm}@{steps}.{which} has no rows")
            continue
        if observed["exact"] != round(correct / n, 4):
            problems.append(f"{arm}@{steps}.{which} exact does not equal correct/n")
        if observed["overlap"] != round(float(observed["overlap_sum"]) / n, 4):
            problems.append(f"{arm}@{steps}.{which} overlap does not equal overlap_sum/n")
        null = part["null"]
        if int(null["draws"]) != NULL_DRAWS:
            problems.append(f"{arm}@{steps}.{which} did not draw {NULL_DRAWS} permutations")
        if null["p_value"] != round((1 + int(null["ge"])) / (NULL_DRAWS + 1), 6):
            problems.append(f"{arm}@{steps}.{which} p_value does not follow from ge/draws")


def check(path: Path) -> List[str]:
    problems: List[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"not JSON: {exc}"]
    if data.get("stage") != STAGE:
        return ["this is not a §78 report"]
    probe = data.get("probe") or {}
    for key, expected in (
        ("null_draws", NULL_DRAWS),
        ("alpha", ALPHA),
        ("contrast_margin", CONTRAST_MARGIN),
        ("fit_match_tolerance", FIT_MATCH_TOLERANCE),
        ("ladder_span_floor", LADDER_SPAN_MIN),
        ("anchor_steps", ANCHOR_STEPS),
        ("family", FAMILY),
        ("capacity_max", CAPACITY_MAX),
        ("steps_ladder", list(STEPS_LADDER)),
        ("composition_overlap_fraction", COMPOSED_OVERLAP_FRACTION),
    ):
        if probe.get(key) != expected:
            problems.append(f"probe.{key} is {probe.get(key)!r}, registered {expected!r}")
    ladder = data.get("ladder") or {}
    for arm in ARMS:
        block = ladder.get(arm)
        if not block:
            problems.append(f"the {arm} ladder is missing")
            continue
        rows = block.get("ladder") or []
        if [int(row.get("steps", -1)) for row in rows] != list(STEPS_LADDER):
            problems.append(f"{arm}: the ladder is not the registered step list")
            continue
        for row in rows:
            if int(row["in_sample_n"]) <= 0:
                problems.append(f"{arm}: rung {row['steps']} has no rows")
                continue
            if row["in_sample_exact"] != round(
                int(row["in_sample_correct"]) / int(row["in_sample_n"]), 4
            ):
                problems.append(f"{arm}: rung {row['steps']} in-sample exact is not correct/n")
            if float(row["capacity_exact"]) != round(
                int(row["capacity_correct"]) / int(row["in_sample_n"]), 4
            ):
                problems.append(f"{arm}: rung {row['steps']} capacity is not correct/n")
            if bool(row["admissible"]) != bool(float(row["capacity_exact"]) < CAPACITY_MAX):
                problems.append(f"{arm}: rung {row['steps']} admissibility is not recomputed")
        effective = ladder_effective(rows)
        if json.dumps(effective, sort_keys=True) != json.dumps(
            block.get("effective") or {}, sort_keys=True
        ):
            problems.append(f"{arm}: the ladder's effective block does not re-derive")
        instrument = block.get("instrument") or {}
        for key in ("carrier_unchanged", "checkpoint_unchanged", "mode_matches"):
            if instrument.get(key) is not True:
                problems.append(f"{arm}: {key} is not true")
        if (block.get("corpus") or {}).get("digests_match") is not True:
            problems.append(f"{arm}: the probe re-derived a different corpus than the report")

    derived_match = match_pair(
        (ladder.get("control") or {}).get("ladder") or [],
        (ladder.get("treatment") or {}).get("ladder") or [],
    )
    if json.dumps(derived_match, sort_keys=True) != json.dumps(
        data.get("match") or {}, sort_keys=True
    ):
        problems.append("the match does not follow from the stored ladders")

    cells = data.get("cells") or {}
    needed = {ANCHOR_STEPS}
    match = data.get("match") or {}
    if match.get("found"):
        needed.add(int(match["control_steps"]))
        needed.add(int(match["treatment_steps"]))
    for arm in ARMS:
        block = cells.get(arm) or {}
        for steps in sorted(needed):
            cell = block.get(str(steps))
            if not cell:
                problems.append(f"the {arm} cell at {steps} steps is missing")
                continue
            if int(cell.get("steps", -1)) != steps:
                problems.append(f"{arm}@{steps}: the cell's step field disagrees")
            _check_cell(problems, arm, str(steps), cell)

    anchor = data.get("anchor") or {}
    reference = anchor.get("reference") or {}
    if not reference.get("cells"):
        problems.append("the anchor reference cells are missing")
    else:
        derived_repro = reproduction(cells, reference)
        if json.dumps(derived_repro, sort_keys=True) != json.dumps(
            anchor.get("reproduction") or {}, sort_keys=True
        ):
            problems.append("the anchor reproduction does not re-derive")

    derived_gates = gates(data)
    if json.dumps(derived_gates, sort_keys=True) != json.dumps(
        data.get("gates") or {}, sort_keys=True
    ):
        problems.append("the gates do not re-derive from the stored blocks")
    derived_branch = branch(derived_gates)
    if (data.get("branch") or {}).get("id") != derived_branch["id"]:
        problems.append(
            f"the branch is stale: stored {(data.get('branch') or {}).get('id')}, "
            f"recomputed {derived_branch['id']}"
        )
    if data.get("branch", {}).get("id") not in BRANCH_ORDER:
        problems.append("the branch id is not one of the registered six")
    return problems


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="§78: matched-fit readout of §77's frozen stores")
    parser.add_argument("--control", type=Path, help="§77's control report")
    parser.add_argument("--treatment", type=Path, help="§77's treatment report")
    parser.add_argument("--reference", type=Path, help="§77's stored k2.json (anchor cells)")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args(argv)

    if args.check:
        problems = check(args.check)
        print(f"file: {args.check}")
        for problem in problems:
            print(f"  FAIL  {problem}")
        print("check:", "OK" if not problems else "FAILED")
        return 0 if not problems else 1

    if not (args.control and args.treatment and args.reference and args.out):
        parser.error("a scored run needs --control, --treatment, --reference and --out")

    item77 = load_item77()
    composition = item77.load_composition()
    split75 = item77.load_split75()
    boundaries = composition.load_boundaries()
    families = composition.load_families()
    contents = boundaries.load_contents()

    started = time.time()
    reports = {
        "control": json.loads(args.control.read_text(encoding="utf-8")),
        "treatment": json.loads(args.treatment.read_text(encoding="utf-8")),
    }
    arms: Dict[str, Any] = {}
    for arm in ARMS:
        arms[arm] = run_arm(
            item77,
            families,
            boundaries,
            contents,
            args.control if arm == "control" else args.treatment,
            reports[arm],
            arm=arm,
            device=args.device,
        )
        print(
            f"== {arm} ladder  "
            + " ".join(
                f"{row['steps']}:{row['in_sample_exact']:.4f}"
                f"({'ok' if row['admissible'] else 'cap'})"
                for row in arms[arm]["ladder"]
            )
        )

    match = match_pair(arms["control"]["ladder"], arms["treatment"]["ladder"])
    print(f"== match: {json.dumps(match, sort_keys=True)}")

    # Phase B: full cells at the anchor (for §77's reproduction) and, when one
    # exists, at the matched pair. The pair was chosen from in-sample fit only.
    wanted = {ANCHOR_STEPS}
    if match.get("found"):
        wanted.add(int(match["control_steps"]))
        wanted.add(int(match["treatment_steps"]))
    cells: Dict[str, Any] = {arm: {} for arm in ARMS}
    for arm in ARMS:
        features = arms[arm]["features"]
        for steps in sorted(wanted):
            cell = full_cell(
                item77,
                boundaries,
                composition,
                split75,
                arms[arm]["torch"],
                features["train_x"],
                features["y_train"],
                features["held_x"],
                features["y_held"],
                features["rosters"],
                features["split"],
                out=int(arms[arm]["dimensions"]["names"]),
                slots=int(arms[arm]["k"]),
                steps=steps,
            )
            cells[arm][str(steps)] = cell
            print(
                f"== {arm}@{steps}: fit {cell['in_sample']['observed']['exact']:.4f}  "
                f"held {cell['heldout']['observed']['exact']:.4f}  "
                f"lro exact {cell['leave_roster_out']['observed']['exact']:.4f}  "
                f"overlap {cell['leave_roster_out']['observed']['overlap']:.4f}"
            )

    reference = anchor_reference(args.reference)
    anchor = {
        "steps": ANCHOR_STEPS,
        "reference": reference,
        "reproduction": reproduction(cells, reference),
    }
    outcome: Dict[str, Any] = {
        "stage": STAGE,
        "probe": {
            "family": FAMILY,
            "steps_ladder": list(STEPS_LADDER),
            "anchor_steps": ANCHOR_STEPS,
            "null_draws": NULL_DRAWS,
            "null_seed": NULL_SEED,
            "alpha": ALPHA,
            "contrast_margin": CONTRAST_MARGIN,
            "fit_match_tolerance": FIT_MATCH_TOLERANCE,
            "ladder_span_floor": LADDER_SPAN_MIN,
            "composition_overlap_fraction": COMPOSED_OVERLAP_FRACTION,
            "capacity_max": CAPACITY_MAX,
            "gate_metric": "roster row exact (top-k set); delta on leave-roster-out overlap",
            "chance": composition.chance_block(
                int(arms["control"]["k"]), int(arms["control"]["dimensions"]["names"])
            ),
        },
        "k": int(arms["control"]["k"]),
        "ladder": {
            arm: {
                "source_report": arms[arm]["source_report"],
                "checkpoint": arms[arm]["checkpoint"],
                "corpus": arms[arm]["corpus"],
                "split": arms[arm]["split"],
                "instrument": arms[arm]["instrument"],
                "ladder": arms[arm]["ladder"],
                "effective": ladder_effective(arms[arm]["ladder"]),
            }
            for arm in ARMS
        },
        "match": match,
        "cells": cells,
        "anchor": anchor,
        "seconds": round(time.time() - started, 3),
    }
    outcome["gates"] = gates(outcome)
    outcome["branch"] = branch(outcome["gates"])
    outcome["instrument_ok"] = bool(
        outcome["gates"]["N0_instrument"]["pass"]
        and outcome["gates"]["L_ladder_effective"]["pass"]
        and outcome["gates"]["W1_match_found"]["pass"]
        and outcome["gates"]["W2_matched_cells_gated"]["pass"]
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(outcome, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"report : {args.out}")
    print(f"branch : {outcome['branch']['id']}")
    print(f"instrument_ok: {outcome['instrument_ok']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
