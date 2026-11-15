#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§75: does the roster reading survive a roster the carrier never saw?

Why this exists
---------------
§74 left two questions, both named by its own branch (``Q2-transfer-below-the-
composition-floor``, §74.17):

1. **Is the held-out cell carried by rosters the carrier already saw?** §74's
   held-out split mixes two populations - sessions whose name pair also appears
   in the 400 training sessions, and sessions whose pair never does - and only
   the second one can show a *new* composition. This probe splits the 200
   held-out rows by exactly that question and reads the two cells separately,
   with one forward pass of the already-fitted probe (no refitting, no new
   training, no new readout family).
2. **Does the leave-roster-out signal replicate on another corpus?** §74's
   ``linear_values`` leave-roster-out was 0.2350 against a null mean of 0.0207
   and a registered floor of 1.5 overlap: the signal is real against its null
   and below the floor. A second corpus seed decides whether that shape is the
   corpus or the carrier.

What this measures
------------------
``--part seen`` (Part A, the §73 k=2 carrier, frozen)
   One linear probe per family (``linear_values``, ``linear_state``) fitted on
   all 400 training rows exactly as §74's held-out reading does, then a single
   forward pass over the 200 held-out rows. The rows are split by whether their
   roster key occurs among the 57 training rosters. Each cell is scored against
   its own 400-draw permutation null, permuting labels **within that cell**.
   Because the fit is byte-identical to §74's held-out reading, the pooled
   exact must reproduce §74's stored cell (``N0a``) - otherwise the split is
   not a split of the same measurement.

``--part fresh`` (Part B, a new corpus seed, retrained)
   The §73 training command with only ``--pantry-seed`` changed (same 400
   sessions, 200 epochs, 10,000 steps, 168,150 parameters, ``--address turn``,
   no extra epochs, width or data), then §74's three readings with the same
   400 draws, the same alpha and the same ``0.75k`` composition floor. The
   §73 reproduction gate cannot apply to a corpus that did not exist in §73,
   so ``N0b`` records that fact explicitly instead of pretending.

What this is not
----------------
Not a capability score (core score stays 0.00/10), not a claim of binding, and
not a principled test of "composition" - Part A has only the 24 held-out rows
whose roster is new, so a **pass** is evidence at that size while a **fail is
not evidence of absence**; both cells are reported with Wilson intervals so the
width is visible rather than hidden behind one number.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_split75.py \\
        --part seen \\
        --report data/pantry_stage/turn73/k2_arm/pantry_deduction_20261115-125247.json \\
        --reference data/pantry_stage/compose74/k2.json \\
        --out data/pantry_stage/split75/seen_k2.json

    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_split75.py \\
        --part fresh \\
        --report data/pantry_stage/seed75/k2_arm/pantry_deduction_*.json \\
        --out data/pantry_stage/split75/fresh_k2.json

    ./.venv/bin/python scripts/probe_pantry_split75.py --check data/pantry_stage/split75/seen_k2.json
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

# §75.4, written before either cell was scored. These are the §74 constants,
# repeated here so a change on either side is an assertion failure rather than a
# silent difference between two stages.
NULL_DRAWS = 400
NULL_SEED = 20261125
ALPHA = 0.005
COMPOSED_OVERLAP_FRACTION = 0.75
# Part A reads only the two families §74.17 named; the nonlinear arm is not
# re-read here (it had the worst composition cell, and adding it would turn a
# two-cell question into a family search).
SPLIT_FAMILIES = ("linear_state", "linear_values")
FRESH_FAMILIES = ("linear_state", "linear_values", "nonlinear_quad")
STAGE_SEEN = "§75a seen and unseen rosters on one frozen carrier"
STAGE_FRESH = "§75b does leave-roster-out replicate on a second corpus seed"


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_composition() -> Any:
    """§74's module: the null machinery and the three readings, one copy only."""
    module = _load("pantry_split75_composition", COMPOSITION)
    for name, expected in (
        ("NULL_DRAWS", NULL_DRAWS),
        ("ALPHA", ALPHA),
        ("COMPOSED_OVERLAP_FRACTION", COMPOSED_OVERLAP_FRACTION),
        ("NULL_SEED", NULL_SEED),
    ):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(
                f"§75 was registered against {name}={expected}, §74 now has {actual}; "
                "the stages no longer share a criterion"
            )
    return module


# --------------------------------------------------------------------------- #
# intervals: the cells here are small, so the width must be reported
# --------------------------------------------------------------------------- #
def wilson(correct: int, n: int, z: float = 1.96) -> Dict[str, float]:
    if n <= 0:
        return {"low": 0.0, "high": 0.0}
    phat = correct / n
    denominator = 1.0 + z * z / n
    centre = phat + z * z / (2 * n)
    spread = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))
    return {
        "low": round((centre - spread) / denominator, 4),
        "high": round((centre + spread) / denominator, 4),
    }


def with_interval(block: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(block)
    enriched["wilson"] = wilson(int(block.get("correct", 0)), int(block.get("n", 0)))
    return enriched


# --------------------------------------------------------------------------- #
# Part A: one forward pass, two cells
# --------------------------------------------------------------------------- #
def split_rows(
    held_rosters: Sequence[Tuple[str, ...]], train_rosters: Sequence[Tuple[str, ...]]
) -> Dict[str, Any]:
    """Seen = the pair appears in the training sessions' rosters; unseen = it does not."""
    known = {tuple(key) for key in train_rosters}
    seen: List[int] = []
    unseen: List[int] = []
    for row, key in enumerate(held_rosters):
        (seen if tuple(key) in known else unseen).append(row)
    if len(seen) + len(unseen) != len(held_rosters):
        raise SystemExit("the held-out split lost or duplicated rows")
    if set(seen) & set(unseen):
        raise SystemExit("the held-out split is not a partition")
    unseen_sizes: Dict[str, int] = {}
    for row in unseen:
        key = tuple(held_rosters[row])
        unseen_sizes["+".join(key)] = unseen_sizes.get("+".join(key), 0) + 1
    return {
        "rows": len(held_rosters),
        "seen": len(seen),
        "unseen": len(unseen),
        "seen_rows": seen,
        "unseen_rows": unseen,
        "train_rosters": len(known),
        "unseen_rosters": len(unseen_sizes),
        "unseen_roster_sizes": dict(sorted(unseen_sizes.items())),
    }


def subset_reading(
    composition: Any,
    torch: Any,
    logits: Any,
    labels: Any,
    rows: Sequence[int],
    *,
    slots: int,
    draws: int,
) -> Dict[str, Any]:
    """Score a held-out cell, then permute **that cell's** labels (400 draws)."""
    if not rows:
        raise SystemExit("an empty cell cannot be read")
    index = torch.as_tensor(list(rows), dtype=torch.long)
    cell_logits = logits[index]
    cell_labels = labels[index]
    observed = composition.score_set(cell_logits, cell_labels, slots)
    null_draws = [
        composition.score_set(
            cell_logits,
            composition.permute_rows(torch, cell_labels, NULL_SEED + draw),
            slots,
        )
        for draw in range(draws)
    ]
    return {
        "observed": with_interval(observed),
        "null": composition.null_block(observed, null_draws),
        "chance": composition.chance_block(slots, int(labels.shape[1])),
    }


def seen_gates(outcome: Dict[str, Any]) -> Dict[str, Any]:
    readings = outcome["readings"]
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
            "the carrier and checkpoint bytes are unchanged and the pooled held-out cell "
            "reproduces §74's stored reading, so the two cells are a split of that measurement"
        ),
    }

    def cell(cell_name: str) -> Dict[str, Any]:
        arms: Dict[str, Any] = {}
        for name in SPLIT_FAMILIES:
            part = readings[name][cell_name]
            observed = part["observed"]
            arms[name] = {
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
        return {"arms": arms, "any": any(row["pass"] for row in arms.values())}

    return {
        "N0a_instrument": n0,
        "S1_seen": cell("seen"),
        "S2_unseen": cell("unseen"),
    }


def seen_branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """Fixed precedence, written before the run: N0a > S2 > S1."""
    if not gate["N0a_instrument"]["pass"]:
        return {
            "id": "N0-instrument",
            "reading": "the carrier, the checkpoint or the reproduction moved; the split reads nothing",
            "next": "fix the instrument before reading either cell",
        }
    if gate["S2_unseen"]["any"]:
        returned = [name for name, row in gate["S2_unseen"]["arms"].items() if row["pass"]]
        return {
            "id": "U1-unseen-rosters-answer",
            "reading": (
                "at least one family answers held-out sessions whose name pair never appears in "
                f"the training corpus ({', '.join(returned)}), above its own within-cell null"
            ),
            "next": (
                "replicate on a second corpus seed (part fresh) before reading this as composition "
                "rather than one corpus's luck"
            ),
        }
    if gate["S1_seen"]["any"]:
        return {
            "id": "U2-seen-rosters-only",
            "reading": (
                "only the held-out rows whose pair also appears in training are above their own "
                "null, so the pooled held-out cell is carried by pairs the carrier already saw"
            ),
            "next": (
                "the next stage is a carrier that must answer an unseen pair, not a larger held-out "
                "pool: report the unseen cell's interval and do not read the pooled number alone"
            ),
        }
    return {
        "id": "U3-neither-cell-above-null",
        "reading": (
            "neither cell beats its own label-permutation null, so §74's pooled held-out cell does "
            "not survive being split"
        ),
        "next": "the readout, not the split, is the subject; no composition claim is available",
    }


def run_seen(
    composition: Any,
    boundaries: Any,
    families: Any,
    contents: Any,
    report_path: Path,
    report: Dict[str, Any],
    reference_path: Path,
    *,
    device: str = "cpu",
) -> Dict[str, Any]:
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§75 reads the §62/§63/§64 minimal-binding corpus, not this report")
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
    split = split_rows(families.roster_keys(heldout), families.roster_keys(train))

    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    readings: Dict[str, Any] = {}
    reproduction_actual: Dict[str, Any] = {}
    for name in SPLIT_FAMILIES:
        train_x, held_x = contents.standardise(
            families.feature_view(name, train_views), families.feature_view(name, held_views)
        )
        train_x = families.transform(name, train_x)
        held_x = families.transform(name, held_x)
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
        pooled = composition.score_set(held_logits, y_held, k)
        reproduction_actual[name] = pooled["exact"]
        readings[name] = {
            "feature_dim": int(train_x.shape[1]),
            "pooled": with_interval(pooled),
            "seen": subset_reading(
                composition,
                torch,
                held_logits,
                y_held,
                split["seen_rows"],
                slots=k,
                draws=NULL_DRAWS,
            ),
            "unseen": subset_reading(
                composition,
                torch,
                held_logits,
                y_held,
                split["unseen_rows"],
                slots=k,
                draws=NULL_DRAWS,
            ),
        }

    expected = {
        name: reference["readings"][name]["heldout"]["observed"]["exact"] for name in SPLIT_FAMILIES
    }
    reference_report = str((reference.get("source_report") or ""))
    hash_after = probe.checkpoint_sha256(checkpoint)
    weights_after = str(core.weights_hash() or "")
    outcome: Dict[str, Any] = {
        "stage": STAGE_SEEN,
        "source_report": str(report_path),
        "reference": str(reference_path),
        "reference_report": reference_report,
        "checkpoint": str(checkpoint),
        "k": k,
        "dimensions": {"colours": len(colours), "names": len(names)},
        "corpus": {
            "train_digest": (corpus.get("meta") or {}).get("train_digest"),
            "heldout_digest": (corpus.get("meta") or {}).get("heldout_digest"),
            "train_items": len(train),
            "heldout_items": len(heldout),
        },
        "split": {
            "rows": split["rows"],
            "seen": split["seen"],
            "unseen": split["unseen"],
            "train_rosters": split["train_rosters"],
            "unseen_rosters": split["unseen_rosters"],
            "unseen_roster_sizes": split["unseen_roster_sizes"],
        },
        "probe": {
            "architecture": (
                "§74's families, unchanged: one probe fitted on all 400 training rows with the true "
                "labels, one forward pass over the 200 held-out rows, then the rows are split by "
                "whether their roster key occurs in the training rosters"
            ),
            "features": "frozen carrier, torch.no_grad; state = [h, read], values = v flattened",
            "standardisation": "train-split per-dimension mean/std, applied to held-out rows",
            "steps": boundaries.PROBE_STEPS,
            "batch": boundaries.PROBE_BATCH,
            "lr": boundaries.PROBE_LR,
            "weight_decay": boundaries.PROBE_WEIGHT_DECAY,
            "seed": boundaries.PROBE_SEED,
            "null_draws": NULL_DRAWS,
            "null_seed": NULL_SEED,
            "alpha": ALPHA,
            "nulls": {
                "seen": "permute the labels of the seen rows only, 400 draws, probe fixed",
                "unseen": "permute the labels of the unseen rows only, 400 draws, probe fixed",
                "pooled": "not re-nulled here; it is the §74 held-out cell being reproduced",
            },
            "reading_rule": (
                "S1/S2 pass when p < alpha and exact > chance; the unseen cell has ~24 rows, so a "
                "pass is evidence at that size and a fail is not evidence of absence"
            ),
            "chance": composition.chance_block(k, len(names)),
        },
        "reproduction": {
            "expected": expected,
            "actual": reproduction_actual,
            "equal": expected == reproduction_actual,
        },
        "readings": readings,
        "instrument": {
            "device": device,
            "weights_hash_before": weights_before,
            "weights_hash_after": weights_after,
            "carrier_unchanged": weights_after == weights_before,
            "checkpoint_sha256_before": hash_before,
            "checkpoint_sha256_after": hash_after,
            "checkpoint_unchanged": hash_before == hash_after,
            "seconds": round(time.time() - started, 3),
        },
    }
    outcome["gates"] = seen_gates(outcome)
    outcome["branch"] = seen_branch(outcome["gates"])
    outcome["instrument_ok"] = bool(outcome["gates"]["N0a_instrument"]["pass"])
    return outcome


# --------------------------------------------------------------------------- #
# Part B: a second corpus seed, §74's readings
# --------------------------------------------------------------------------- #
def fresh_gates(composition: Any, outcome: Dict[str, Any]) -> Dict[str, Any]:
    """§74's Q1/Q2/Q3 arithmetic, with the instrument gate a new corpus allows."""
    gate = composition.gates(outcome)
    instrument = outcome["instrument"]
    corpus = outcome["corpus"]
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
            "the fresh carrier and checkpoint are unchanged across the run and the fresh corpus "
            "digests are recorded; §73's reproduction gate is recorded as not applicable because "
            "this corpus did not exist when §73 was scored"
        ),
    }
    gate["N0_instrument"] = n0
    return gate


def fresh_branch(gate: Dict[str, Any], composition: Any, outcome: Dict[str, Any]) -> Dict[str, str]:
    """Fixed precedence, written before the run: N0b > Q1 > Q2 > Q3 > replication."""
    if not gate["N0_instrument"]["pass"]:
        return {
            "id": "N0-instrument",
            "reading": "the fresh carrier, the checkpoint or the corpus record moved; nothing is read",
            "next": "fix the instrument before reading any cell of this stage",
        }
    fitted = [name for name, row in gate["Q1_relative_fit"]["arms"].items() if row["pass"]]
    if not fitted:
        return {
            "id": "Q1-no-relative-fit",
            "reading": "no family fits the fresh training rosters better than its own permutation null",
            "next": "the readout, not the corpus, is the subject; no composition claim is available",
        }
    transferred = [name for name in fitted if gate["Q2_transfer"]["arms"][name]["pass"]]
    if not transferred:
        return {
            "id": "Q2-fit-but-no-transfer",
            "reading": (
                "a family fits the fresh training rosters but does not beat the held-out label "
                "permutation null, so §74's transfer did not replicate on this corpus"
            ),
            "next": "the transfer is corpus-specific until a third seed says otherwise",
        }
    composed = [
        name for name in transferred if gate["Q3_composed_from_names"]["arms"][name]["pass"]
    ]
    if composed:
        return {
            "id": "Q3-composed-from-names-on-second-seed",
            "reading": (
                "the leave-roster-out overlap reaches the registered three-quarter floor on a corpus "
                "that did not exist in §74, so the composition signal is not one corpus's luck "
                f"({', '.join(composed)})"
            ),
            "next": (
                "a third seed and a second task before any binding claim; the floor is still a "
                "criterion, not a demonstration"
            ),
        }
    # Below the floor: is it below *with* the §74 shape, or flat against the null?
    weak = [
        name
        for name in transferred
        if gate["Q3_composed_from_names"]["arms"][name]["p_value"] < ALPHA
    ]
    if weak:
        return {
            "id": "Q3-below-floor-again",
            "reading": (
                "the leave-roster-out cell is above its own permutation null but below the "
                f"registered floor on this corpus too ({', '.join(weak)}), matching §74's shape"
            ),
            "next": (
                "composition is weak rather than absent on two seeds; the next registration should "
                "ask what in the write would raise it, not add epochs or width"
            ),
        }
    return {
        "id": "Q3-flat-on-second-seed",
        "reading": (
            "the leave-roster-out cell is not distinguishable from its label-permutation null on "
            "this corpus, so §74's leave-roster-out signal did not replicate"
        ),
        "next": "§74's signal is read as this corpus's, not the carrier's",
    }


def run_fresh(
    composition: Any,
    boundaries: Any,
    families: Any,
    contents: Any,
    report_path: Path,
    report: Dict[str, Any],
    *,
    device: str = "cpu",
) -> Dict[str, Any]:
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§75 reads the §62/§63/§64 minimal-binding corpus, not this report")
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

    readings: Dict[str, Any] = {}
    for name in FRESH_FAMILIES:
        train_x, held_x = contents.standardise(
            families.feature_view(name, train_views), families.feature_view(name, held_views)
        )
        train_x = families.transform(name, train_x)
        held_x = families.transform(name, held_x)
        readings[name] = {
            "feature_dim": int(train_x.shape[1]),
            "in_sample": composition.in_sample_reading(
                boundaries, torch, train_x, y_train, out=len(names), slots=k, draws=NULL_DRAWS
            ),
            "heldout": composition.transfer_reading(
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
            "leave_roster_out": composition.leave_roster_out(
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
        # §75 adds the interval to every cell; §74's cells are point estimates.
        for split_name in ("in_sample", "heldout", "leave_roster_out"):
            block = readings[name][split_name]
            block["observed"] = with_interval(block["observed"])

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
        "stage": STAGE_FRESH,
        "source_report": str(report_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "dimensions": {"colours": len(colours), "names": len(names)},
        "corpus_seed": corpus_block.get("seed"),
        "corpus": {
            "train_digest": (corpus.get("meta") or {}).get("train_digest"),
            "heldout_digest": (corpus.get("meta") or {}).get("heldout_digest"),
            "train_items": len(train),
            "heldout_items": len(heldout),
            "train_rosters": len(set(rosters)),
        },
        "probe": {
            "architecture": (
                "§74's readings verbatim (in_sample, heldout, leave_roster_out) on a carrier trained "
                "on a corpus seed that did not exist in §73/§74"
            ),
            "features": "frozen carrier, torch.no_grad; state = [h, read], values = v flattened",
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
            "chance": composition.chance_block(k, len(names)),
            "nulls": {
                "in_sample": "permute the training labels, refit, score on the same permuted labels",
                "heldout": "fit on true training labels, permute the held-out labels, score",
                "leave_roster_out": "fit without roster R, read R's rows, then permute the evaluated labels",
            },
            "composition_floor": {
                "overlap_fraction": COMPOSED_OVERLAP_FRACTION,
                "overlap": round(COMPOSED_OVERLAP_FRACTION * k, 4),
            },
        },
        "readings": readings,
        "reproduction": {
            "applicable": False,
            "equal": False,
            "reason": (
                "§73's cell belongs to the corpus seed this carrier did not train on, so reproducing "
                "it is impossible by construction; N0b records that instead of asserting it"
            ),
        },
        "instrument": instrument,
    }
    outcome["gates"] = fresh_gates(composition, outcome)
    outcome["branch"] = fresh_branch(outcome["gates"], composition, outcome)
    outcome["instrument_ok"] = bool(outcome["gates"]["N0_instrument"]["pass"])
    return outcome


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def _check_readings(problems: List[str], name: str, split: str, part: Dict[str, Any]) -> None:
    observed = part.get("observed") or {}
    null = part.get("null") or {}
    n = int(observed.get("n", 0))
    correct = int(observed.get("correct", -1))
    if n <= 0:
        problems.append(f"{name}.{split} has no rows")
        return
    if observed.get("exact") != round(correct / n, 4):
        problems.append(f"{name}.{split} exact does not equal correct/n")
    if observed.get("overlap") != round(float(observed.get("overlap_sum", -1)) / n, 4):
        problems.append(f"{name}.{split} overlap does not equal overlap_sum/n")
    if observed.get("wilson") != wilson(correct, n):
        problems.append(f"{name}.{split} wilson interval does not follow from correct/n")
    if int(null.get("draws", -1)) != NULL_DRAWS:
        problems.append(f"{name}.{split} did not draw {NULL_DRAWS} permutations")
    if null.get("p_value") != round((1 + int(null.get("ge", -1))) / (NULL_DRAWS + 1), 6):
        problems.append(f"{name}.{split} p_value does not follow from ge and draws")
    histogram = observed.get("overlap_histogram") or {}
    if sum(int(value) for value in histogram.values()) != n:
        problems.append(f"{name}.{split} overlap histogram does not sum to n")


def check(path: Path) -> List[str]:
    problems: List[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    stage = data.get("stage")
    if stage not in (STAGE_SEEN, STAGE_FRESH):
        return ["this is not a §75 report"]
    probe = data.get("probe") or {}
    if int(probe.get("null_draws", -1)) != NULL_DRAWS:
        problems.append(f"null_draws is not the registered {NULL_DRAWS}")
    if float(probe.get("alpha", -1.0)) != ALPHA:
        problems.append(f"alpha is not the registered {ALPHA}")
    if (
        float((probe.get("composition_floor") or {}).get("overlap_fraction", -1.0))
        != (COMPOSED_OVERLAP_FRACTION)
        and stage == STAGE_FRESH
    ):
        problems.append(f"the composition floor is not the registered {COMPOSED_OVERLAP_FRACTION}k")

    composition = load_composition()

    if stage == STAGE_SEEN:
        split = data.get("split") or {}
        if int(split.get("seen", -1)) + int(split.get("unseen", -1)) != int(split.get("rows", -2)):
            problems.append("the split does not add up to the held-out rows")
        if int(split.get("unseen", 0)) <= 0:
            problems.append("the unseen cell is empty")
        for name in SPLIT_FAMILIES:
            block = (data.get("readings") or {}).get(name)
            if not block:
                problems.append(f"reading {name} is missing")
                continue
            for cell in ("seen", "unseen"):
                part = block.get(cell) or {}
                _check_readings(problems, name, cell, part)
            pooled = block.get("pooled") or {}
            if int(pooled.get("n", 0)) != int(split.get("rows", -1)):
                problems.append(f"{name}.pooled is not the whole held-out split")
        recomputed = seen_gates(data)
        if json.dumps(recomputed, sort_keys=True) != json.dumps(
            data.get("gates") or {}, sort_keys=True
        ):
            problems.append("the stored gates do not follow from the stored readings")
        fork = seen_branch(recomputed)
        if (data.get("branch") or {}).get("id") != fork["id"]:
            problems.append(
                f"the branch is stale: stored {(data.get('branch') or {}).get('id')}, recomputed {fork['id']}"
            )
        instrument = data.get("instrument") or {}
        if instrument.get("carrier_unchanged") is not True:
            problems.append("the carrier weights changed")
        if instrument.get("checkpoint_unchanged") is not True:
            problems.append("checkpoint bytes changed")
        if (data.get("reproduction") or {}).get("equal") is not True:
            problems.append("the pooled cell does not reproduce the §74 reading")
    else:
        for name in FRESH_FAMILIES:
            block = (data.get("readings") or {}).get(name)
            if not block:
                problems.append(f"reading {name} is missing")
                continue
            for split_name in ("in_sample", "heldout", "leave_roster_out"):
                _check_readings(problems, name, split_name, block.get(split_name) or {})
        recomputed = fresh_gates(composition, data)
        stored = data.get("gates") or {}
        for key in ("Q1_relative_fit", "Q2_transfer", "Q3_composed_from_names"):
            if json.dumps(recomputed[key], sort_keys=True) != json.dumps(
                stored.get(key), sort_keys=True
            ):
                problems.append(f"the stored {key} does not follow from the stored readings")
        fork = fresh_branch(recomputed, composition, data)
        if (data.get("branch") or {}).get("id") != fork["id"]:
            problems.append(
                f"the branch is stale: stored {(data.get('branch') or {}).get('id')}, recomputed {fork['id']}"
            )
        instrument = data.get("instrument") or {}
        if instrument.get("carrier_unchanged") is not True:
            problems.append("the carrier weights changed")
        if instrument.get("checkpoint_unchanged") is not True:
            problems.append("checkpoint bytes changed")
        if not (data.get("corpus") or {}).get("train_digest"):
            problems.append("the fresh corpus digest is not recorded")
    return problems


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=("seen", "fresh"), default="", help="which half of §75")
    parser.add_argument("--report", default="", help="a finished pantry-deduction training report")
    parser.add_argument("--reference", default="", help="§74's JSON (part seen only)")
    parser.add_argument("--check", default="", help="re-derive a §75 JSON's verdict")
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

    if not args.part or not args.report:
        parser.error("--part and --report are required (or --check)")
    report_path = Path(args.report)
    if not report_path.exists():
        raise SystemExit(f"missing report: {report_path}")
    composition = load_composition()
    boundaries = composition.load_boundaries()
    families = composition.load_families()
    contents = boundaries.load_contents()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    print(f"report : {report_path}")
    if args.part == "seen":
        if not args.reference:
            parser.error("--part seen needs --reference (§74's JSON to reproduce)")
        reference_path = Path(args.reference)
        if not reference_path.exists():
            raise SystemExit(f"missing reference: {reference_path}")
        outcome = run_seen(
            composition,
            boundaries,
            families,
            contents,
            report_path,
            report,
            reference_path,
            device=args.device,
        )
        split = outcome["split"]
        print(
            f"split  : seen {split['seen']} / unseen {split['unseen']} of {split['rows']} held-out rows"
        )
        print(
            f"         train rosters {split['train_rosters']}, unseen rosters {split['unseen_rosters']}"
        )
        print()
        print(
            f"  {'arm':16s} {'cell':8s} {'n':>4s} {'exact':>7s} {'wilson':>15s} {'null':>7s} {'p':>8s}"
        )
        for name in SPLIT_FAMILIES:
            block = outcome["readings"][name]
            for cell in ("seen", "unseen"):
                observed = block[cell]["observed"]
                null = block[cell]["null"]
                interval = f"{observed['wilson']['low']:.3f}-{observed['wilson']['high']:.3f}"
                print(
                    f"  {name:16s} {cell:8s} {observed['n']:4d} {observed['exact']:7.4f} "
                    f"{interval:>15s} {null['exact']['mean']:7.4f} {null['p_value']:8.4f}"
                )
                print(
                    f"  {'':16s} {'':8s} overlap {observed['overlap']:.4f}  hist {observed['overlap_histogram']}"
                )
        print()
        for key, block in outcome["gates"].items():
            if "pass" in block:
                print(f"  {key:24s} {'PASS' if block['pass'] else 'FAIL'}")
            else:
                arms = ", ".join(
                    f"{a}={'PASS' if r['pass'] else 'FAIL'}" for a, r in block["arms"].items()
                )
                print(f"  {key:24s} {'PASS' if block['any'] else 'FAIL'}  ({arms})")
    else:
        outcome = run_fresh(
            composition, boundaries, families, contents, report_path, report, device=args.device
        )
        print(
            f"k      : {outcome['k']}   corpus seed: {outcome['corpus_seed']}   rosters: {outcome['corpus']['train_rosters']}"
        )
        print(
            f"chance : exact {outcome['probe']['chance']['exact']}  overlap {outcome['probe']['chance']['overlap']}"
        )
        print()
        header = (
            f"  {'arm':16s} {'in':>7s} {'null':>7s} {'p':>8s}  {'held':>7s} {'null':>7s} {'p':>8s}  "
            f"{'lro':>7s} {'ov':>6s} {'p':>8s}"
        )
        print(header)
        for name in FRESH_FAMILIES:
            block = outcome["readings"][name]
            print(
                f"  {name:16s} "
                f"{block['in_sample']['observed']['exact']:7.4f} {block['in_sample']['null']['exact']['mean']:7.4f} "
                f"{block['in_sample']['null']['p_value']:8.4f}  "
                f"{block['heldout']['observed']['exact']:7.4f} {block['heldout']['null']['exact']['mean']:7.4f} "
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
    return 0 if outcome["instrument_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
