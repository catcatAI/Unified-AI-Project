#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§74: is the roster cell a reading of the roster, or a content-blind prior?

Why this exists
---------------
§73 changed only the write address and the held-out roster cell rose from 0.1400
to 0.3350 (k=2). It could not say what that number means: its W2 gate imported
§70's 0.95 readable floor - a floor §70 used for *the label the carrier was
trained to emit* - and applied it to a label the carrier was never trained to
emit, so W2 was false by construction (its own registered expectation was
0.4975). §73.17 therefore fixed the next step: define "admissible fit"
**relatively** before asking whether 0.3350 is transfer.

What this measures
------------------
Nothing is retrained. The §73 carriers, corpus, features and standardisation are
frozen and the observed in-sample / held-out numbers must reproduce §73's arms
bit for bit (``N0``). What is new is a **null distribution** for every reading,
and a third split that removes the exact pair from the fitting labels:

* ``Q1 relative fit``  - in-sample exact against ``null_draws`` refits on
  row-permuted labels: does the family fit *these* labels, or would arbitrary
  labels score the same? This is the relative replacement for §70's absolute
  ``CAPACITY_MAX`` and §73's absolute ``READABLE_FLOOR``.
* ``Q2 transfer``      - held-out exact against the same number of row
  permutations of the held-out labels, with the fitted probe held fixed: does
  the readout's answer depend on which roster the unseen session actually had?
* ``Q3 composition``   - **leave-roster-out inside the training split**: fit on
  every session whose roster is not ``R``, then read the sessions whose roster is
  ``R``. The pair itself was never a training label, so a pass cannot be a
  label-set lookup; the gate is on the mean *name overlap* (how many of the
  ``k`` roster names the top-``k`` set recovers), because "the pair" and "one of
  the two names" are different claims and only the first one is binding.

Reported, not gated: the overlap histogram on every split. It is what separates
"reads both names" from "reads one name" when exact is small, and it is a
descriptor rather than a threshold so that no new line is invented for it.

What this is not
----------------
Not a capability score (core score stays 0.00/10), not a re-run of §73's gates,
and not an independent replication: the criterion here is chosen with §73's
numbers in view, which is exactly what §73.17 asked for, so a pass is a
*criterion decision*. The replication on a fresh corpus is the next section's
job, not this one's. No threshold in §70/§72/§73 is moved.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_composition.py \\
        --report data/pantry_stage/turn73/k2_arm/pantry_deduction_20261115-125247.json \\
        --source data/pantry_stage/write73/k2.json \\
        --out data/pantry_stage/compose74/k2.json

    ./.venv/bin/python scripts/probe_pantry_composition.py --check data/pantry_stage/compose74/k2.json
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
BOUNDARIES = REPO_ROOT / "scripts" / "probe_pantry_boundaries.py"
FAMILIES = REPO_ROOT / "scripts" / "probe_pantry_families.py"

# §74.5, written before the scored run. ``NULL_DRAWS`` is chosen so the smallest
# attainable p-value (1 / (draws + 1)) is below ``ALPHA``; anything smaller would
# register a gate that cannot fire.
NULL_DRAWS = 400
NULL_SEED = 20261125
ALPHA = 0.005
# Q3 asks whether the *pair* is read: the mean overlap must reach three quarters
# of the ``k`` names, i.e. strictly more than "one name plus padding".
COMPOSED_OVERLAP_FRACTION = 0.75

FAMILIES_ORDER = ("linear_state", "linear_values", "nonlinear_quad")


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_boundaries() -> Any:
    return _load("pantry_readout_boundaries", BOUNDARIES)


def load_families() -> Any:
    """§70/§73's module: boundary features, the three families, the roster keys."""
    return _load("pantry_composition_families", FAMILIES)


# --------------------------------------------------------------------------- #
# scoring: exact set, and how many of the k names were recovered
# --------------------------------------------------------------------------- #
def score_set(logits: Any, targets: Any, k: int) -> Dict[str, Any]:
    """``exact`` is the registered gate metric; ``overlap`` is the descriptor.

    ``targets`` is a 0/1 matrix with exactly ``k`` ones per row (the roster is an
    order-free set of distinct names), so the per-row dot product is the number
    of true names the top-``k`` prediction recovered.
    """
    picked = logits.topk(k, dim=1).indices
    hit = logits.new_zeros(targets.shape)
    hit.scatter_(1, picked, 1.0)
    matched = (hit * targets).sum(dim=1)
    n = int(targets.shape[0])
    correct = int((matched == targets.sum(dim=1)).sum())
    overlap_sum = float(matched.sum())
    histogram: Dict[str, int] = {}
    for value in matched.tolist():
        histogram[str(int(value))] = histogram.get(str(int(value)), 0) + 1
    return {
        "n": n,
        "correct": correct,
        "exact": round(correct / max(n, 1), 4),
        "overlap_sum": overlap_sum,
        "overlap": round(overlap_sum / max(n, 1), 4),
        "overlap_histogram": dict(sorted(histogram.items(), key=lambda item: int(item[0]))),
    }


def chance_block(k: int, names: int) -> Dict[str, float]:
    """Exact chance ``1 / C(names, k)`` and the overlap a blind top-k gets."""
    total = math.comb(int(names), int(k))
    return {
        "exact": round(1.0 / total, 6),
        "overlap": round(float(k) * float(k) / float(names), 4),
    }


# --------------------------------------------------------------------------- #
# null machinery (all nulls are label permutations; only the fit differs)
# --------------------------------------------------------------------------- #
def permute_rows(torch: Any, labels: Any, seed: int) -> Any:
    generator = torch.Generator().manual_seed(int(seed))
    order = torch.randperm(int(labels.shape[0]), generator=generator)
    if not bool((torch.sort(order).values == torch.arange(int(labels.shape[0]))).all()):
        raise SystemExit("a label permutation was not a bijection")
    return labels[order]


def fit_and_predict(
    boundaries: Any,
    torch: Any,
    features: Any,
    labels: Any,
    *,
    out: int,
    slots: int,
    seed: int,
) -> Any:
    """The §70 probe, unchanged: one linear head, 2,000 steps, seeded init."""
    probe = boundaries.build_probe(torch, int(features.shape[1]), out, seed)
    boundaries.fit_probe(
        torch,
        probe,
        features,
        labels,
        kind="set",
        slots=slots,
        steps=boundaries.PROBE_STEPS,
        batch=boundaries.PROBE_BATCH,
        lr=boundaries.PROBE_LR,
        weight_decay=boundaries.PROBE_WEIGHT_DECAY,
        seed=seed,
    )
    return probe


def null_block(observed: Dict[str, Any], draws: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """p = (1 + #{null >= observed}) / (draws + 1); the permutation convention."""
    exacts = [float(row["exact"]) for row in draws]
    overlaps = [float(row["overlap"]) for row in draws]
    count = len(draws)

    def summary(values: Sequence[float], round_to: int = 6) -> Dict[str, float]:
        mean = sum(values) / max(len(values), 1)
        spread = math.sqrt(sum((value - mean) ** 2 for value in values) / max(len(values), 1))
        ordered = sorted(values)

        def quantile(q: float) -> float:
            index = min(len(ordered) - 1, max(0, int(round(q * (len(ordered) - 1)))))
            return ordered[index]

        return {
            "mean": round(mean, round_to),
            "sd": round(spread, round_to),
            "min": round(ordered[0], round_to) if ordered else 0.0,
            "max": round(ordered[-1], round_to) if ordered else 0.0,
            "p95": round(quantile(0.95), round_to),
            "p99": round(quantile(0.99), round_to),
        }

    ge = sum(1 for value in exacts if value >= float(observed["exact"]) - 1e-12)
    return {
        "draws": count,
        "seed": NULL_SEED,
        "exact": summary(exacts),
        "overlap": summary(overlaps, round_to=4),
        "ge": ge,
        "p_value": round((1 + ge) / (count + 1), 6),
    }


def in_sample_reading(
    boundaries: Any,
    torch: Any,
    features: Any,
    labels: Any,
    *,
    out: int,
    slots: int,
    draws: int,
) -> Dict[str, Any]:
    """Observed fit, then the same fit on row-permuted labels (refit each draw)."""
    probe = fit_and_predict(
        boundaries, torch, features, labels, out=out, slots=slots, seed=boundaries.PROBE_SEED
    )
    fitted_logits = boundaries.predict_probe(torch, probe, features)
    observed = score_set(fitted_logits, labels, slots)
    null_draws: List[Dict[str, Any]] = []
    for draw in range(draws):
        shuffled = permute_rows(torch, labels, NULL_SEED + draw)
        local = fit_and_predict(
            boundaries, torch, features, shuffled, out=out, slots=slots, seed=boundaries.PROBE_SEED
        )
        null_draws.append(
            score_set(boundaries.predict_probe(torch, local, features), shuffled, slots)
        )
    return {"observed": observed, "null": null_block(observed, null_draws)}


def transfer_reading(
    boundaries: Any,
    torch: Any,
    train_x: Any,
    train_y: Any,
    held_x: Any,
    held_y: Any,
    *,
    out: int,
    slots: int,
    draws: int,
) -> Dict[str, Any]:
    """One fit on the true training labels; the null permutes the held-out labels."""
    probe = fit_and_predict(
        boundaries, torch, train_x, train_y, out=out, slots=slots, seed=boundaries.PROBE_SEED
    )
    logits = boundaries.predict_probe(torch, probe, held_x)
    observed = score_set(logits, held_y, slots)
    null_draws = [
        score_set(logits, permute_rows(torch, held_y, NULL_SEED + draw), slots)
        for draw in range(draws)
    ]
    return {"observed": observed, "null": null_block(observed, null_draws)}


def leave_roster_out(
    boundaries: Any,
    torch: Any,
    features: Any,
    labels: Any,
    rosters: Sequence[Tuple[str, ...]],
    *,
    out: int,
    slots: int,
    draws: int,
) -> Dict[str, Any]:
    """Fit without roster ``R``, read ``R``'s sessions: the pair was never a label."""
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
        probe = fit_and_predict(
            boundaries,
            torch,
            features[train_index],
            labels[train_index],
            out=out,
            slots=slots,
            seed=boundaries.PROBE_SEED,
        )
        logits = boundaries.predict_probe(torch, probe, features[held_index])
        block = score_set(logits, labels[held_index], slots)
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
    observed = score_set(pooled_logits, pooled_labels, slots)
    null_draws = [
        score_set(pooled_logits, permute_rows(torch, pooled_labels, NULL_SEED + draw), slots)
        for draw in range(draws)
    ]
    sizes = [len(rows_) for rows_ in groups.values()]
    return {
        "observed": observed,
        "null": null_block(observed, null_draws),
        "rosters": len(groups),
        "fold_size": {
            "min": min(sizes),
            "max": max(sizes),
            "median": sorted(sizes)[len(sizes) // 2],
        },
        "per_fold": per_fold,
    }


# --------------------------------------------------------------------------- #
# gates, branch, mechanical re-check
# --------------------------------------------------------------------------- #
def gates(outcome: Dict[str, Any]) -> Dict[str, Any]:
    k = int(outcome["k"])
    readings = outcome["readings"]
    chance = outcome["probe"]["chance"]
    composed_floor = round(COMPOSED_OVERLAP_FRACTION * k, 4)

    q1 = {}
    q2 = {}
    q3 = {}
    for name in FAMILIES_ORDER:
        block = readings[name]
        observed = block["in_sample"]["observed"]
        q1[name] = {
            "pass": bool(block["in_sample"]["null"]["p_value"] < ALPHA),
            "observed": observed["exact"],
            "null_mean": block["in_sample"]["null"]["exact"]["mean"],
            "null_p99": block["in_sample"]["null"]["exact"]["p99"],
            "p_value": block["in_sample"]["null"]["p_value"],
            "alpha": ALPHA,
        }
        held = block["heldout"]
        q2[name] = {
            "pass": bool(
                held["null"]["p_value"] < ALPHA
                and held["observed"]["exact"] > float(chance["exact"])
            ),
            "observed": held["observed"]["exact"],
            "chance": chance["exact"],
            "p_value": held["null"]["p_value"],
            "alpha": ALPHA,
        }
        composed = block["leave_roster_out"]
        q3[name] = {
            "pass": bool(
                composed["observed"]["overlap"] >= composed_floor
                and composed["null"]["p_value"] < ALPHA
            ),
            "observed_overlap": composed["observed"]["overlap"],
            "overlap_floor": composed_floor,
            "observed_exact": composed["observed"]["exact"],
            "p_value": composed["null"]["p_value"],
            "alpha": ALPHA,
        }

    instrument = outcome["instrument"]
    reproduction = outcome["reproduction"]
    n0 = {
        "pass": bool(
            instrument["carrier_unchanged"]
            and instrument["checkpoint_unchanged"]
            and reproduction["equal"]
        ),
        "carrier_unchanged": instrument["carrier_unchanged"],
        "checkpoint_unchanged": instrument["checkpoint_unchanged"],
        "reproduction_equal": reproduction["equal"],
        "reading": (
            "the carrier and checkpoint bytes are unchanged and the observed in-sample / held-out "
            "cells reproduce the §73 report this run names"
        ),
    }
    return {
        "N0_instrument": n0,
        "Q1_relative_fit": {"arms": q1, "any": any(row["pass"] for row in q1.values())},
        "Q2_transfer": {"arms": q2, "any": any(row["pass"] for row in q2.values())},
        "Q3_composed_from_names": {
            "arms": q3,
            "any": any(row["pass"] for row in q3.values()),
        },
    }


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """Fixed precedence, written before the run: N0 > Q1 > Q2 > Q3."""
    if not gate["N0_instrument"]["pass"]:
        return {
            "id": "N0-instrument",
            "reading": "the carrier, the checkpoint or the §73 reproduction moved; nothing is read",
            "next": "fix the instrument before reading any cell of this stage",
        }
    fitted = [name for name, row in gate["Q1_relative_fit"]["arms"].items() if row["pass"]]
    if not fitted:
        return {
            "id": "Q1-no-relative-fit",
            "reading": (
                "no family fits the true roster labels better than its own permuted-label "
                "distribution, so the held-out cell is a readout artifact at this budget"
            ),
            "next": "the readout, not the write, is the subject: register a family that clears Q1 first",
        }
    transferred = [name for name in fitted if gate["Q2_transfer"]["arms"][name]["pass"]]
    if not transferred:
        return {
            "id": "Q2-fit-but-no-transfer",
            "reading": (
                "a family fits the training rosters but does not beat the held-out label "
                "permutation null, so the fit did not survive new sessions"
            ),
            "next": "the gap is in-distribution vs held-out, not composition",
        }
    composed = [
        name for name in transferred if gate["Q3_composed_from_names"]["arms"][name]["pass"]
    ]
    if composed:
        return {
            "id": "Q3-composed-from-names",
            "reading": (
                "the readout recovers most of a pair it never saw as a label (leave-roster-out), "
                "so the store's values carry the roster as a composition of names"
            ),
            "next": (
                "replicate on a fresh corpus seed before claiming binding, and only then ask what "
                "the write must contain"
            ),
        }
    return {
        "id": "Q2-transfer-below-the-composition-floor",
        "reading": (
            "the held-out cell beats its label-permutation null, but a pair that was never a "
            "fitting label does not reach the registered three-quarter overlap floor, so this "
            "stage does not call the reading binding. The leave-roster-out exact and overlap are "
            "reported beside their own null, so how far short it falls is visible without being "
            "labelled either way."
        ),
        "next": (
            "decide between 'composition is present but weak' and 'per-session identity memory' "
            "with the leave-roster-out null cell, and register the held-out seen/unseen-roster "
            "split before adding any other readout family"
        ),
    }


def instrument_problems(data: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    gate = data.get("gates") or {}
    n0 = gate.get("N0_instrument") or {}
    if n0.get("pass") is not True:
        problems.append("N0_instrument did not pass")
    instrument = data.get("instrument") or {}
    if instrument.get("carrier_unchanged") is not True:
        problems.append("the carrier weights changed")
    if instrument.get("checkpoint_unchanged") is not True:
        problems.append("checkpoint bytes changed")
    if (data.get("reproduction") or {}).get("equal") is not True:
        problems.append("the observed cells do not reproduce the §73 report")
    if data.get("instrument_ok") is not True and not problems:
        problems.append("instrument_ok is false without a listed problem")
    return problems


def check(path: Path) -> List[str]:
    """Re-derive every gate and the branch from the stored readings."""
    problems: List[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("stage") != "§74 which reading does the roster cell support":
        problems.append("this is not a §74 report")
        return problems

    if int(data.get("probe", {}).get("null_draws", -1)) != NULL_DRAWS:
        problems.append(f"null_draws is not the registered {NULL_DRAWS}")
    if float(data.get("probe", {}).get("alpha", -1.0)) != ALPHA:
        problems.append(f"alpha is not the registered {ALPHA}")

    chance = data["probe"]["chance"]
    for name in FAMILIES_ORDER:
        block = (data.get("readings") or {}).get(name)
        if not block:
            problems.append(f"reading {name} is missing")
            continue
        for split in ("in_sample", "heldout", "leave_roster_out"):
            part = block.get(split) or {}
            observed = part.get("observed") or {}
            null = part.get("null") or {}
            n = int(observed.get("n", 0))
            correct = int(observed.get("correct", -1))
            if n <= 0:
                problems.append(f"{name}.{split} has no rows")
                continue
            if observed.get("exact") != round(correct / n, 4):
                problems.append(f"{name}.{split} exact does not equal correct/n")
            if observed.get("overlap") != round(float(observed.get("overlap_sum", -1)) / n, 4):
                problems.append(f"{name}.{split} overlap does not equal overlap_sum/n")
            if int(null.get("draws", -1)) != NULL_DRAWS:
                problems.append(f"{name}.{split} did not draw {NULL_DRAWS} permutations")
            expected_p = round((1 + int(null.get("ge", -1))) / (NULL_DRAWS + 1), 6)
            if null.get("p_value") != expected_p:
                problems.append(f"{name}.{split} p_value does not follow from ge and draws")
            histogram = observed.get("overlap_histogram") or {}
            if sum(int(value) for value in histogram.values()) != n:
                problems.append(f"{name}.{split} overlap histogram does not sum to n")

    recomputed = gates(data)
    stored = data.get("gates") or {}
    if json.dumps(recomputed, sort_keys=True) != json.dumps(stored, sort_keys=True):
        problems.append("the stored gates do not follow from the stored readings")
    fork = branch(recomputed)
    if (data.get("branch") or {}).get("id") != fork["id"]:
        problems.append(
            f"the branch is stale: stored {(data.get('branch') or {}).get('id')}, recomputed {fork['id']}"
        )
    problems.extend(instrument_problems(data))
    return problems


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #
def run(
    contents: Any,
    report_path: Path,
    report: Dict[str, Any],
    *,
    source_path: Path,
    device: str = "cpu",
) -> Dict[str, Any]:
    boundaries = load_boundaries()
    families = load_families()
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§74 reads the §62/§63/§64 minimal-binding corpus, not this report")
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

    def standardised(name: str) -> Tuple[Any, Any]:
        train_x, held_x = contents.standardise(
            families.feature_view(name, train_views), families.feature_view(name, held_views)
        )
        return families.transform(name, train_x), families.transform(name, held_x)

    y_train = torch.as_tensor([list(row) for row in train_targets["roster"]], dtype=torch.float32)
    y_held = torch.as_tensor([list(row) for row in held_targets["roster"]], dtype=torch.float32)
    rosters = families.roster_keys(train)

    readings: Dict[str, Any] = {}
    for name in FAMILIES_ORDER:
        train_x, held_x = standardised(name)
        readings[name] = {
            "feature_dim": int(train_x.shape[1]),
            "in_sample": in_sample_reading(
                boundaries,
                torch,
                train_x,
                y_train,
                out=len(names),
                slots=k,
                draws=NULL_DRAWS,
            ),
            "heldout": transfer_reading(
                boundaries,
                torch,
                train_x,
                y_train,
                held_x,
                y_held,
                out=len(names),
                slots=k,
                draws=NULL_DRAWS,
            ),
            "leave_roster_out": leave_roster_out(
                boundaries,
                torch,
                train_x,
                y_train,
                rosters,
                out=len(names),
                slots=k,
                draws=NULL_DRAWS,
            ),
        }

    source = json.loads(source_path.read_text(encoding="utf-8"))
    expected = {
        name: {
            "in_sample": source["arms"][name]["in_sample"]["exact"],
            "heldout": source["arms"][name]["heldout"]["exact"],
        }
        for name in FAMILIES_ORDER
    }
    actual = {
        name: {
            "in_sample": readings[name]["in_sample"]["observed"]["exact"],
            "heldout": readings[name]["heldout"]["observed"]["exact"],
        }
        for name in FAMILIES_ORDER
    }

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
        "seconds": round(time.time() - started, 3),
    }
    outcome: Dict[str, Any] = {
        "stage": "§74 which reading does the roster cell support",
        "source_report": str(report_path),
        "source_cell": str(source_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "dimensions": {"colours": len(colours), "names": len(names)},
        "corpus": {
            "train_digest": (corpus.get("meta") or {}).get("train_digest"),
            "heldout_digest": (corpus.get("meta") or {}).get("heldout_digest"),
            "train_items": len(train),
            "heldout_items": len(heldout),
            "train_rosters": len(set(rosters)),
        },
        "probe": {
            "architecture": (
                "the §70 families, unchanged (one linear head on [h, read], on the store's values, "
                "or on [x, x*x]); every reading gets a row-permutation null of its own"
            ),
            "features": (
                "frozen carrier, torch.no_grad; state = [h, read] exactly as token_logits "
                "consumes it, values = v flattened over slots"
            ),
            "standardisation": "train-split per-dimension mean/std, applied to held-out rows",
            "steps": boundaries.PROBE_STEPS,
            "batch": boundaries.PROBE_BATCH,
            "lr": boundaries.PROBE_LR,
            "weight_decay": boundaries.PROBE_WEIGHT_DECAY,
            "seed": boundaries.PROBE_SEED,
            "null_draws": NULL_DRAWS,
            "null_seed": NULL_SEED,
            "alpha": ALPHA,
            "gate_metric": "roster row exact (top-k set)",
            "chance": chance_block(k, len(names)),
            "nulls": {
                "in_sample": "permute the training labels, refit, score on the same permuted labels",
                "heldout": "fit on true training labels, permute the held-out labels, score",
                "leave_roster_out": (
                    "fit without roster R, read R's rows, then permute the evaluated labels"
                ),
            },
            "composition_floor": {
                "overlap_fraction": COMPOSED_OVERLAP_FRACTION,
                "overlap": round(COMPOSED_OVERLAP_FRACTION * k, 4),
            },
        },
        "reproduction": {"expected": expected, "actual": actual, "equal": expected == actual},
        "readings": readings,
        "instrument": instrument,
    }
    outcome["gates"] = gates(outcome)
    outcome["branch"] = branch(outcome["gates"])
    outcome["instrument_ok"] = bool(outcome["gates"]["N0_instrument"]["pass"])
    return outcome


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default="", help="a finished pantry-deduction training report")
    parser.add_argument(
        "--source", default="", help="the §73 families JSON whose cells to reproduce"
    )
    parser.add_argument("--check", default="", help="re-derive a §74 JSON's verdict")
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

    if not args.report or not args.source:
        parser.error("both --report and --source are required (or --check)")
    report_path = Path(args.report)
    if not report_path.exists():
        raise SystemExit(f"missing report: {report_path}")
    source_path = Path(args.source)
    if not source_path.exists():
        raise SystemExit(f"missing source cell: {source_path}")
    contents = load_boundaries().load_contents()
    outcome = run(
        contents,
        report_path,
        json.loads(report_path.read_text(encoding="utf-8")),
        source_path=source_path,
        device=args.device,
    )

    print(f"report : {report_path}")
    print(f"k      : {outcome['k']}   rosters in train: {outcome['corpus']['train_rosters']}")
    print(
        f"chance : exact {outcome['probe']['chance']['exact']}  overlap {outcome['probe']['chance']['overlap']}"
    )
    print()
    header = f"  {'arm':16s} {'in':>7s} {'null':>7s} {'p':>8s}  {'held':>7s} {'null':>7s} {'p':>8s}  {'lro':>7s} {'ov':>6s} {'p':>8s}"
    print(header)
    for name in FAMILIES_ORDER:
        block = outcome["readings"][name]
        print(
            f"  {name:16s} "
            f"{block['in_sample']['observed']['exact']:7.4f} "
            f"{block['in_sample']['null']['exact']['mean']:7.4f} "
            f"{block['in_sample']['null']['p_value']:8.4f}  "
            f"{block['heldout']['observed']['exact']:7.4f} "
            f"{block['heldout']['null']['exact']['mean']:7.4f} "
            f"{block['heldout']['null']['p_value']:8.4f}  "
            f"{block['leave_roster_out']['observed']['exact']:7.4f} "
            f"{block['leave_roster_out']['observed']['overlap']:6.3f} "
            f"{block['leave_roster_out']['null']['p_value']:8.4f}"
        )
    print()
    for key, block in outcome["gates"].items():
        if "pass" in block:
            print(f"  {key:32s} {'PASS' if block['pass'] else 'FAIL'}")
        else:
            print(f"  {key:32s} {'PASS' if block['any'] else 'FAIL'}")
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
    problems = instrument_problems(outcome)
    for problem in problems:
        print(f"  FAIL  {problem}")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
