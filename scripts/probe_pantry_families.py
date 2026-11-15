#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§70: which readout family reaches the roster? (same frozen carrier, same turn)

Why this exists
---------------
§69 ended on **B5-partial-facts-held**: the colour transfers at the turn that
states it (0.8900 / 0.9950) and the roster does not (0.2850 / 0.0050 against a
registered 0.50 effect floor). B5's next step was fixed in §69.7 and repeated in
§69.14: probe the failing fact **at its own turn** with a different readout
family - the store's values directly first, then a nonlinear readout - never more
steps, width or data.

What this measures
------------------
Same carriers (§64's k=2 and §65's k=5 checkpoints), same 400 declared / 200
held-out structures, same 2,000-step budget, same train-split standardisation.
Only the readout family changes, and every family is fitted on the training split
only:

* ``linear_state``  - §69's readout, recomputed here so all columns share one
  instrument and the reproduction is explicit;
* ``linear_values`` - a linear read on the store's **values** ``v`` at the roster
  boundary (the write itself, not the attention-weighted read);
* ``nonlinear_quad``- ``[x, x*x]`` then a linear head: a fixed-feature nonlinear
  family with no random projection to seed;
* ``structure``     - a **capacity-free** test: are two held-out states whose
  sessions carry the same roster set closer (cosine) than two states whose
  rosters differ? That question needs no fitted parameters at all, so it cannot
  be bought with readout capacity.

Why the fourth arm is in this stage
-----------------------------------
The train-split calibration in §70.4 (recorded before this file was committed)
showed the window between "fits the labels" and "cannot fit permuted labels" is
empty at 400 structures: every nonlinear family wide enough to fit the roster in
sample also fits permuted labels above the 0.50 instrument cap. So the two fitted
arms B5 named can be predicted to come back uninformative, and a stage that only
ran them would end with "cannot decide". The structure test decides the same
question without a fitted readout, and it is blind to the readout arms: it uses
no labels, only which sessions share a roster.

What this is not
----------------
Not a capability score (the core score stays 0.00/10), not a new objective, and
not a licence to add training: the carrier is frozen and ``weights_hash`` plus
the checkpoint sha256 are recorded before and after. A roster that separates the
geometry but not any admissible readout is a *readout/budget* finding, not a
claim that the carrier can represent it.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_families.py \\
        --report data/pantry_stage/ord_arm/pantry_deduction_20261115-015751.json \\
        --reference data/pantry_stage/bounds69/k2.json \\
        --out data/pantry_stage/readout70/k2.json
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

# §70.5, written before the scored run. Same floors as §69; only the structure
# test adds a number, and it is fixed here rather than chosen after the run.
READABLE_FLOOR = 0.95
TRANSFER_FLOOR = 0.50
CAPACITY_MAX = 0.50
STRUCTURE_AUC_FLOOR = 0.65
STRUCTURE_ALPHA = 0.001
STRUCTURE_PERMUTATIONS = 1000
STRUCTURE_SEED = 20261123

FAMILIES = ("linear_state", "linear_values", "nonlinear_quad")


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_boundaries() -> Any:
    """§69's module: the corpus, the boundaries, the probe fit and the gates."""
    return _load("pantry_readout_boundaries", BOUNDARIES)


# --------------------------------------------------------------------------- #
# features at one boundary, including the store's written values
# --------------------------------------------------------------------------- #
def boundary_features(
    trainer: Any,
    contents: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    index: int,
    *,
    batch: int = 64,
) -> Dict[str, Any]:
    """``state`` = [h, read], ``read`` alone, and the store's ``v`` flattened.

    ``values`` is the write itself: ``end_turn`` stores one ``value_proj(h)`` per
    turn, so this is what the store literally holds, not what the current ``h``
    happens to address. It is flattened over slots so a linear probe can ask
    whether any slot holds the roster.
    """
    torch = core._torch
    probe = contents.load_selection().load_probe()
    states: List[Any] = []
    reads: List[Any] = []
    values: List[Any] = []
    shape: Optional[List[int]] = None
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
            if "v" not in tensors:
                raise SystemExit(
                    "the state has no 'v' tensor: §70 needs the store (memory=True), "
                    "not the ablation arm"
                )
            read = core.read_vector(tensors)
            states.append(torch.cat([tensors["h"], read], dim=1).detach().cpu())
            reads.append(read.detach().cpu())
            values.append(tensors["v"].reshape(len(chunk), -1).detach().cpu())
            shape = [int(tensors["v"].shape[1]), int(tensors["v"].shape[2])]
    return {
        "state": torch.cat(states, dim=0),
        "read": torch.cat(reads, dim=0),
        "values": torch.cat(values, dim=0),
        "value_shape": shape,
    }


# --------------------------------------------------------------------------- #
# the nonlinear family (fixed before scoring)
# --------------------------------------------------------------------------- #
def quad(features: Any) -> Any:
    """``[x, x*x]``: elementwise nonlinearity, no random projection, no seed."""
    import torch

    return torch.cat([features, features * features], dim=1)


def transform(name: str, features: Any) -> Any:
    if name == "nonlinear_quad":
        return quad(features)
    return features


def feature_view(name: str, views: Dict[str, Any]) -> Any:
    """Which stored view a family reads: state for both state arms, values for v."""
    return views["values"] if name == "linear_values" else views["state"]


# --------------------------------------------------------------------------- #
# the capacity-free structure test
# --------------------------------------------------------------------------- #
def roster_keys(sessions: Sequence[Dict[str, Any]]) -> List[Tuple[str, ...]]:
    """The roster as an order-free set: the order twins must count as the same."""
    return [
        tuple(sorted(str(name) for name in session["environment"]["actors"]))
        for session in sessions
    ]


def pair_index(count: int) -> Tuple[Any, Any]:
    import torch

    return torch.triu_indices(count, count, offset=1)


def cosine_distances(features: Any) -> Any:
    import torch

    unit = torch.nn.functional.normalize(features.double(), dim=1)
    return (1.0 - unit @ unit.T).clamp_min(0.0)


def average_ranks(distance: Any) -> Any:
    """1-based average ranks, ties sharing their mean rank (AUC needs this)."""
    import torch

    unique, inverse = torch.unique(distance, return_inverse=True)
    counts = torch.bincount(inverse).double()
    ends = torch.cumsum(counts, dim=0)
    starts = ends - counts + 1.0
    mean_rank = (starts + ends) / 2.0
    return mean_rank[inverse]


def auc_from_ranks(ranksum: float, same_pairs: int, diff_pairs: int) -> float:
    """Mann-Whitney AUC: P(distance of a same pair < distance of a different pair)."""
    if same_pairs <= 0 or diff_pairs <= 0:
        return float("nan")
    numerator = ranksum - same_pairs * (same_pairs + 1) / 2.0
    return numerator / (same_pairs * diff_pairs)


def identical_pairs(ids: Sequence[int], left: Any, right: Any) -> Any:
    import torch

    table = torch.as_tensor(list(ids), dtype=torch.long)
    return (table[left] == table[right]).to(torch.bool)


def structure_test(
    torch: Any,
    features: Any,
    rosters: Sequence[Tuple[str, ...]],
    *,
    permutations: int = STRUCTURE_PERMUTATIONS,
    seed: int = STRUCTURE_SEED,
) -> Dict[str, Any]:
    """Do same-roster states sit closer together than different-roster states?

    No parameters are fitted, so this cannot be inflated by readout capacity. The
    null keeps the distance matrix fixed and permutes only which row carries which
    roster, which is the correct null for "the roster leaves no trace".
    """
    unique = {key: index for index, key in enumerate(sorted(set(rosters)))}
    ids = [unique[key] for key in rosters]
    count = len(ids)
    left, right = pair_index(count)
    distances = cosine_distances(features)[left, right]
    # Rank the similarity (-distance) ascending so a same-roster pair that is
    # nearer earns a *higher* rank: AUC = P(same pair nearer than a different one).
    ranks = average_ranks(-distances)
    same = identical_pairs(ids, left, right)
    same_pairs = int(same.sum())
    diff_pairs = int((~same).sum())
    ranksum = float(ranks[same].sum())
    observed = auc_from_ranks(ranksum, same_pairs, diff_pairs)

    generator = torch.Generator().manual_seed(seed)
    table = torch.as_tensor(ids, dtype=torch.long)
    null: List[float] = []
    for _ in range(int(permutations)):
        order = torch.randperm(count, generator=generator)
        mask = table[order[left]] == table[order[right]]
        drawn = int(mask.sum())
        if drawn <= 0 or drawn >= count * (count - 1) // 2:
            null.append(float("nan"))
            continue
        null.append(auc_from_ranks(float(ranks[mask].sum()), drawn, int(ranks.numel() - drawn)))
    finite = [value for value in null if not math.isnan(value)]
    if not finite:
        raise SystemExit("every permuted roster assignment produced a degenerate split")
    hits = sum(1 for value in finite if value >= observed)
    p_value = (1.0 + hits) / (1.0 + len(finite))
    return {
        "auc": round(observed, 4),
        "same_pairs": same_pairs,
        "diff_pairs": diff_pairs,
        "n_pairs": int(ranks.numel()),
        "n_rows": count,
        "distinct_rosters": len(unique),
        "same_ranksum": round(ranksum, 4),
        "permutations": int(permutations),
        "null_mean": round(sum(finite) / len(finite), 4),
        "null_upper": round(sorted(finite)[-1], 4),
        "p_value": round(p_value, 4),
        "null": [round(value, 6) for value in null],
        "seed": int(seed),
    }


def structure_gate(train: Dict[str, Any], heldout: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "auc": heldout["auc"],
        "p_value": heldout["p_value"],
        "auc_floor": STRUCTURE_AUC_FLOOR,
        "alpha": STRUCTURE_ALPHA,
        "same_pairs": heldout["same_pairs"],
        "diff_pairs": heldout["diff_pairs"],
        "distinct_rosters": heldout["distinct_rosters"],
        "train_auc": train["auc"],
        "transfers": bool(
            heldout["auc"] >= STRUCTURE_AUC_FLOOR
            and heldout["p_value"] <= STRUCTURE_ALPHA
            and heldout["same_pairs"] > 0
            and heldout["diff_pairs"] > 0
        ),
        "reading": (
            "two held-out states with the same roster are closer than two with different "
            "rosters; no parameters are fitted, so readout capacity cannot produce this"
        ),
    }


# --------------------------------------------------------------------------- #
# gates and the fork
# --------------------------------------------------------------------------- #
def gates(report: Dict[str, Any]) -> Dict[str, Any]:
    """§70.6, mechanically: every input is a number this file already stores."""
    boundaries = load_boundaries()
    k = int(report["k"])
    dims = report["dimensions"]
    chance = boundaries.chance_levels(int(dims["colours"]), int(dims["names"]), k)
    baseline = report["majority_baselines"]["roster"]
    arms = report["arms"]
    controls = report["positive_controls"]
    carrier_unchanged = bool(report["instrument"]["carrier_unchanged"])

    def control(name: str) -> Dict[str, Any]:
        block = controls[name]
        return {
            "in_sample": block["in_sample"]["exact"],
            "capacity": block["capacity"]["exact"],
            "pass": bool(
                block["in_sample"]["exact"] >= READABLE_FLOOR
                and block["capacity"]["exact"] <= CAPACITY_MAX
            ),
        }

    instrument = {name: control(name) for name in FAMILIES}
    reproduction = report["reproduction"]
    values_readable = bool(arms["linear_values"]["in_sample"]["exact"] >= READABLE_FLOOR)
    nonlinear_readable = bool(arms["nonlinear_quad"]["in_sample"]["exact"] >= READABLE_FLOOR)
    nonlinear_capacity_ok = bool(arms["nonlinear_quad"]["capacity"]["exact"] <= CAPACITY_MAX)
    return {
        "H0_instrument": {
            "pass": bool(all(instrument[name]["pass"] for name in FAMILIES) and carrier_unchanged),
            "controls": instrument,
            "carrier_unchanged": carrier_unchanged,
            "readable_floor": READABLE_FLOOR,
            "capacity_max": CAPACITY_MAX,
            "reading": (
                "every family fits the one label the carrier was trained to emit (the culprit "
                "at the answer boundary) and cannot fit row-permuted labels"
            ),
        },
        "H1_linear_state_reproduces_§69": {
            "pass": bool(reproduction["equal"]),
            "expected": reproduction["expected"],
            "actual": reproduction["actual"],
            "reading": "the linear-state arm is §69's cell, so the two stages share one instrument",
        },
        "H2_store_values_are_readable": {
            "readable": values_readable,
            "in_sample": arms["linear_values"]["in_sample"]["exact"],
            "capacity": arms["linear_values"]["capacity"]["exact"],
            "floor": READABLE_FLOOR,
            "reading": (
                "in-sample >= 0.95 is the precondition for a held-out failure to mean anything: "
                "a family that cannot fit the fact in sample cannot witness its absence"
            ),
        },
        "H3_nonlinear_is_admissible": {
            "readable": nonlinear_readable,
            "capacity_limited": not nonlinear_capacity_ok,
            "in_sample": arms["nonlinear_quad"]["in_sample"]["exact"],
            "capacity": arms["nonlinear_quad"]["capacity"]["exact"],
            "floor": READABLE_FLOOR,
            "capacity_max": CAPACITY_MAX,
            "reading": (
                "readable and not capacity_limited are both required before a nonlinear "
                "failure can be read as 'not encoded'"
            ),
        },
        "H4_roster_separates_the_geometry": structure_gate(
            report["structure"]["train"], report["structure"]["heldout"]
        ),
        "H5_store_values_transfer": boundaries.fact_gate(
            arms["linear_values"], baseline, chance["roster"]
        ),
        "H6_nonlinear_transfers": boundaries.fact_gate(
            arms["nonlinear_quad"], baseline, chance["roster"]
        ),
    }


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """§70.7, mechanically: which reading the gates select, in fixed precedence."""
    if not gate["H0_instrument"]["pass"]:
        return {
            "id": "B0-instrument",
            "reading": (
                "at least one family cannot fit the carrier's own label in sample "
                f"({json.dumps(gate['H0_instrument']['controls'])}) or the carrier moved: "
                "no roster reading can be taken from this run"
            ),
            "next": "fix the family/budget so every arm passes the control, then re-run",
        }
    if (
        gate["H2_store_values_are_readable"]["readable"]
        and gate["H5_store_values_transfer"]["transfers"]
    ):
        return {
            "id": "B1-store-values-hold-the-roster",
            "reading": (
                "a linear read on the store's own values transfers the roster "
                f"({gate['H5_store_values_transfer']['heldout_exact']}), so the write is where "
                "the roster lives and the read address is what §68/§69 failed on"
            ),
            "next": "probe why read_vector does not surface the values the store already holds",
        }
    if (
        gate["H3_nonlinear_is_admissible"]["readable"]
        and not gate["H3_nonlinear_is_admissible"]["capacity_limited"]
        and gate["H6_nonlinear_transfers"]["transfers"]
    ):
        return {
            "id": "B2-nonlinear-readout-holds-the-roster",
            "reading": (
                "the roster is in the state nonlinearly: the fixed-feature family fits in "
                f"sample ({gate['H3_nonlinear_is_admissible']['in_sample']}), cannot fit "
                f"permuted labels ({gate['H3_nonlinear_is_admissible']['capacity']}) and "
                f"transfers ({gate['H6_nonlinear_transfers']['heldout_exact']})"
            ),
            "next": "name the nonlinear feature the roster uses, then test it at the answer boundary",
        }
    if gate["H4_roster_separates_the_geometry"]["transfers"]:
        return {
            "id": "B3-roster-present-but-not-fittable",
            "reading": (
                "the roster leaves a trace in the state at its own turn (same-roster states "
                f"are closer: AUC {gate['H4_roster_separates_the_geometry']['auc']}, "
                f"p {gate['H4_roster_separates_the_geometry']['p_value']}), but no admissible "
                "fitted family names it: the store's values cannot fit it in sample "
                f"({gate['H2_store_values_are_readable']['in_sample']}) and the nonlinear "
                "family is capacity-limited or underfits "
                f"({gate['H3_nonlinear_is_admissible']['in_sample']} in sample, "
                f"capacity {gate['H3_nonlinear_is_admissible']['capacity']})"
            ),
            "next": (
                "stop asking fitted readouts at 400 structures; intervene on the roster line "
                "(swap a name on that turn only) and ask whether the state moves to the edited "
                "roster's neighbourhood"
            ),
        }
    return {
        "id": "B4-roster-absent-at-its-own-turn",
        "reading": (
            "the roster does not separate the state's geometry either "
            f"(AUC {gate['H4_roster_separates_the_geometry']['auc']}, "
            f"p {gate['H4_roster_separates_the_geometry']['p_value']}), so no readout family "
            "could have found it: the turn's state does not carry which names were named"
        ),
        "next": (
            "probe the roster turn itself (the token states of the names, and what end_turn "
            "writes) instead of adding readout families"
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
    reference_path: Optional[Path] = None,
    device: str = "cpu",
) -> Dict[str, Any]:
    boundaries = load_boundaries()
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§70 reads the §62/§63/§64 minimal-binding corpus, not this report")
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

    train_views = boundary_features(trainer, contents, core, train, indexes["roster"])
    held_views = boundary_features(trainer, contents, core, heldout, indexes["roster"])

    def standardised(name: str) -> Tuple[Any, Any]:
        train_x, held_x = contents.standardise(
            feature_view(name, train_views), feature_view(name, held_views)
        )
        return transform(name, train_x), transform(name, held_x)

    y_train = torch.as_tensor([list(row) for row in train_targets["roster"]], dtype=torch.float32)
    y_held = torch.as_tensor([list(row) for row in held_targets["roster"]], dtype=torch.float32)

    arms: Dict[str, Any] = {}
    for name in FAMILIES:
        train_x, held_x = standardised(name)
        fitted = boundaries.run_probe(
            torch,
            train_x,
            y_train,
            held_x,
            y_held,
            kind="set",
            out=len(names),
            slots=k,
            seed=boundaries.PROBE_SEED,
        )
        ceiling = boundaries.capacity_ceiling(
            torch, train_x, y_train, kind="set", out=len(names), slots=k
        )
        folded = boundaries.cross_validate(
            torch,
            train_x,
            y_train,
            train_targets["structure"],
            kind="set",
            out=len(names),
            slots=k,
            seed=boundaries.PROBE_SEED,
            folds=boundaries.FOLDS,
        )
        arms[name] = {**fitted, "capacity": ceiling, "in_distribution": folded}

    # Positive control per family: the culprit at the answer boundary, the one
    # label the carrier was trained to emit.
    answer_train = boundary_features(trainer, contents, core, train, indexes["answer"])
    y_culprit = torch.as_tensor(train_targets["culprit"], dtype=torch.long)
    controls: Dict[str, Any] = {}
    for name in FAMILIES:
        raw = answer_train["values"] if name == "linear_values" else answer_train["state"]
        train_x, _ = contents.standardise(raw, raw)
        train_x = transform(name, train_x)
        fitted = boundaries.run_probe(
            torch,
            train_x,
            y_culprit,
            train_x,
            y_culprit,
            kind="single",
            out=len(names),
            slots=0,
            seed=boundaries.PROBE_SEED,
        )
        ceiling = boundaries.capacity_ceiling(
            torch, train_x, y_culprit, kind="single", out=len(names), slots=0
        )
        controls[name] = {
            "in_sample": fitted["in_sample"],
            "heldout": fitted["heldout"],
            "capacity": ceiling,
        }

    # §70.2 registers the structure test on the **standardised** [h, read]:
    # cosine distance is scale-sensitive per dimension, so the metric must be the
    # one the registration names, not the raw state.
    state_train, state_held = standardised("linear_state")
    train_structure = structure_test(torch, state_train, roster_keys(train))
    held_structure = structure_test(torch, state_held, roster_keys(heldout))

    reproduction: Dict[str, Any] = {
        "reference": str(reference_path) if reference_path else None,
        "expected": None,
        "actual": None,
        "equal": False,
    }
    if reference_path is not None and reference_path.exists():
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        expected = reference["roster_boundary"]["roster"]
        actual = arms["linear_state"]
        reproduction["expected"] = {
            "in_sample": expected["in_sample"]["exact"],
            "capacity": expected["capacity"]["exact"],
            "in_distribution": expected["in_distribution"]["exact"],
            "heldout": expected["heldout"]["exact"],
        }
        reproduction["actual"] = {
            "in_sample": actual["in_sample"]["exact"],
            "capacity": actual["capacity"]["exact"],
            "in_distribution": actual["in_distribution"]["exact"],
            "heldout": actual["heldout"]["exact"],
        }
        reproduction["equal"] = reproduction["expected"] == reproduction["actual"]

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
        "stage": "§70 which readout family reaches the roster",
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
            "architecture": (
                "one readout per family at the roster boundary (linear on [h, read]; linear on "
                "the store's values; [x, x*x] then linear), each with its own permuted-label "
                "capacity control"
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
            "folds": boundaries.FOLDS,
            "readable_floor": READABLE_FLOOR,
            "transfer_floor": TRANSFER_FLOOR,
            "capacity_max": CAPACITY_MAX,
            "gate_metric": "roster row exact (top-k set); chance 1/C(names, k)",
            "structure": {
                "distance": "cosine on the standardised [h, read]",
                "statistic": "AUC = P(same-roster pair closer than different-roster pair)",
                "permutations": STRUCTURE_PERMUTATIONS,
                "seed": STRUCTURE_SEED,
                "auc_floor": STRUCTURE_AUC_FLOOR,
                "alpha": STRUCTURE_ALPHA,
            },
            "chance": boundaries.chance_levels(len(colours), len(names), k),
        },
        "turns": indexes,
        "value_shape": train_views["value_shape"],
        "arms": arms,
        "positive_controls": controls,
        "structure": {"train": train_structure, "heldout": held_structure},
        "majority_baselines": {
            "roster": boundaries.majority_baseline(train_targets["roster"], held_targets["roster"])
        },
        "reproduction": reproduction,
        "instrument": instrument,
    }
    outcome["gates"] = gates(outcome)
    outcome["branch"] = branch(outcome["gates"])
    instrument["seconds"] = round(time.time() - started, 2)
    outcome["instrument_ok"] = bool(
        outcome["gates"]["H0_instrument"]["pass"]
        and outcome["gates"]["H1_linear_state_reproduces_§69"]["pass"]
        and hash_before == hash_after
    )
    return outcome


# --------------------------------------------------------------------------- #
# mechanical re-check
# --------------------------------------------------------------------------- #
def check(path: Path) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    problems: List[str] = []
    gates_ = data.get("gates") or {}
    if not data.get("turns"):
        problems.append("the boundary turn indices are missing")
    for name in FAMILIES:
        arm = (data.get("arms") or {}).get(name)
        if not isinstance(arm, dict):
            problems.append(f"the {name} arm is missing")
            continue
        for half in ("in_sample", "heldout"):
            if not isinstance(arm.get(half, {}).get("exact"), (int, float)):
                problems.append(f"{name}.{half} has no exact rate")
        if not isinstance(arm.get("capacity"), dict):
            problems.append(f"{name} has no capacity control")
        elif arm["capacity"].get("permutation_is_bijection") is not True:
            problems.append(f"{name}'s capacity control is not a permutation")
        elif float(arm["capacity"].get("labels_changed") or 0.0) < 0.5:
            problems.append(f"{name}'s capacity control kept too many labels")
        if not isinstance(arm.get("in_distribution"), dict):
            problems.append(f"{name} has no in-distribution reference")
        control = (data.get("positive_controls") or {}).get(name)
        if not isinstance(control, dict) or not isinstance(
            control.get("in_sample", {}).get("exact"), (int, float)
        ):
            problems.append(f"{name} has no positive control")
    for split in ("train", "heldout"):
        block = (data.get("structure") or {}).get(split) or {}
        if not isinstance(block.get("auc"), (int, float)):
            problems.append(f"structure.{split} has no AUC")
            continue
        if not isinstance(block.get("null"), list) or not block["null"]:
            problems.append(f"structure.{split} has no permutation null")
            continue
        recomputed = auc_from_ranks(
            float(block["same_ranksum"]), int(block["same_pairs"]), int(block["diff_pairs"])
        )
        if abs(recomputed - float(block["auc"])) > 1e-3:
            problems.append(
                f"structure.{split}'s AUC {block['auc']} does not follow from its own rank sum"
            )
        finite = [
            value
            for value in block["null"]
            if isinstance(value, (int, float)) and not math.isnan(value)
        ]
        hits = sum(1 for value in finite if value >= float(block["auc"]))
        expected_p = (1.0 + hits) / (1.0 + len(finite))
        if abs(expected_p - float(block["p_value"])) > 1.5e-3:
            problems.append(
                f"structure.{split}'s p {block['p_value']} does not follow from its null "
                f"({expected_p})"
            )
    try:
        expected = gates(data)
    except (KeyError, TypeError, ZeroDivisionError) as error:
        problems.append(f"the stored numbers cannot be re-gated: {error}")
        return problems
    for key, block in expected.items():
        stored = gates_.get(key) or {}
        for flag in ("pass", "transfers", "readable", "capacity_limited"):
            if flag in block and stored.get(flag) != block[flag]:
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
    parser.add_argument("--reference", default="", help="§69's roster cell, for H1")
    parser.add_argument("--check", default="", help="re-derive a stage-§70 JSON's verdict")
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
    contents = load_boundaries().load_contents()
    report = json.loads(path.read_text(encoding="utf-8"))
    reference = Path(args.reference) if args.reference else None
    outcome = run(contents, path, report, reference_path=reference, device=args.device)

    print(f"report : {path}")
    print(f"k      : {outcome['k']}   turns: {outcome['turns']}")
    print(f"store  : {outcome['value_shape']} (slots x value_dim)")
    print()
    print(f"  {'arm':16s} {'in-sample':>10s} {'capacity':>9s} {'in-dist':>8s} {'held-out':>9s}")
    for name, block in outcome["arms"].items():
        print(
            f"  {name:16s} {block['in_sample']['exact']:10.4f} "
            f"{block['capacity']['exact']:9.4f} {block['in_distribution']['exact']:8.4f} "
            f"{block['heldout']['exact']:9.4f}"
        )
    print()
    for split in ("train", "heldout"):
        block = outcome["structure"][split]
        print(
            f"  structure {split:7s} AUC {block['auc']:.4f}  p {block['p_value']:.4f}  "
            f"same {block['same_pairs']} / diff {block['diff_pairs']}  "
            f"rosters {block['distinct_rosters']}"
        )
    print()
    for key, block in outcome["gates"].items():
        flag = block.get("transfers", block.get("pass", block.get("readable")))
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
