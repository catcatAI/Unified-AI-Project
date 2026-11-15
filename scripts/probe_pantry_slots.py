#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§72: what does ``end_turn`` actually write, and why can no readout name the roster?

Why this exists
---------------
§71 closed the *addressing* question: the roster line at its own turn changes the
state, and the change follows the **name set** (reversing the clauses or changing
an unused colour does not move the state out of its own roster's neighbourhood).
So the roster is *addressable* in the state. §70 had already shown that no
admissible fitted readout names it at 400 structures (B3: in-sample only).

§70.3 measured one half of the write mechanism on the training split: one
``value_proj(h)`` per turn, one share across all 16 slots, a constant write
address. This section asks the remaining question and makes it *mechanical*:

    is the failure a **collision** between slots, a **superposition** of many
    turns inside one slot, or neither?

What it measures (all on the same frozen carrier, no training)
--------------------------------------------------------------
At the roster boundary, for every held-out session, from one single pass:

* ``max_share``  - the largest softmax write weight (``slot_gate``), i.e. how
  concentrated the address is. 1.0 means one slot receives everything.
* ``active_slots`` - how many of the 16 slots hold a non-zero value after the
  turn (``||v_slot|| >= ACTIVE_SLOT_SHARE * max ||v_slot||``).
* ``rank1_residual`` - the second over the first singular value of the 16x64
  value matrix. A one-slot store is exactly rank 1.
* ``read_cos`` - cosine between the read vector and the strongest slot's value.
  1.0 means the read *is* that value up to scale.
* ``address_rank1`` - the same ratio for the 16 address scalars across sessions.
  A single global address is rank 1 across sessions.

Four linear readout arms at the same budget as §70/§71 (2,000 steps, same
standardisation, same permutation capacity control):

* ``values`` - the whole store flattened, the §70 ``linear_values`` arm verbatim
  (a within-run reproduction check);
* ``read``   - the pooled read only;
* ``state``  - ``[h, read]``, the §70 ``linear_state`` arm verbatim (the second
  within-run reproduction check);
* ``address`` - the 16 write weights only (does the *address* carry the roster?).

Why this is not another readout family
--------------------------------------
The arms are diagnostics of the *write*, not candidates for production. If the
store is one slot, then "try a different readout" is answered: there is nothing
else in the store to read, and the fix must be a different write (one address per
turn), which this section does **not** do - it only decides whether that is the
next experiment.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_slots.py \
        --report data/pantry_stage/ord_arm/pantry_deduction_20261115-015751.json \
        --out data/pantry_stage/slots72/k2.json
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
FAMILIES = REPO_ROOT / "scripts" / "probe_pantry_families.py"

# §72.5, written before the scored run. Readable/transfer/capacity are §70's
# numbers, unchanged, so the two sections are directly comparable.
READABLE_FLOOR = 0.95
TRANSFER_FLOOR = 0.50
CAPACITY_MAX = 0.50
ADDRESS_TRANSFER_MAX = 0.10
ONE_ADDRESS_FLOOR = 0.95
ACTIVE_SLOT_SHARE = 1e-3
RANK1_EPS = 1e-3
FRACTION_FLOOR = 0.95
READ_COS_FLOOR = 0.999
ARMS = ("values", "read", "state", "address")


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_families() -> Any:
    """§70's module: boundary features, the readout trainer, the capacity control."""
    return _load("pantry_slots_families", FAMILIES)


# --------------------------------------------------------------------------- #
# the write, measured from one state
# --------------------------------------------------------------------------- #
def write_weights(torch: Any, core: Any, hidden: Any) -> Any:
    """The exact softmax ``end_turn`` uses to pick slots, recomputed from ``h``."""
    with torch.no_grad():
        return torch.softmax(torch.exp(core.log_write_scale) * core.slot_gate(hidden), dim=-1)


def slot_block(torch: Any, core: Any, views: Dict[str, Any]) -> Dict[str, Any]:
    """Per-session address, slot occupancy, rank-1 residual and read alignment."""
    values = views["values"]
    count = int(values.shape[0])
    slots = int(core.slots)
    slot_dim = int(core.slot_dim)
    hidden_dim = int(views["state"].shape[1]) - int(core.value_dim)
    hidden = views["state"][:, :hidden_dim]
    grid = values.reshape(count, slots, slot_dim).double()

    weights = write_weights(torch, core, hidden).double()
    norms = grid.norm(dim=2)
    strongest = norms.max(dim=1).values.clamp_min(1e-12)
    active = (norms >= ACTIVE_SLOT_SHARE * strongest.unsqueeze(1)).sum(dim=1)
    singular = torch.linalg.svdvals(grid)
    residual = singular[:, 1] / singular[:, 0].clamp_min(1e-12)

    index = norms.argmax(dim=1)
    best = grid[torch.arange(count), index]
    read_cos = torch.nn.functional.cosine_similarity(views["read"].double(), best, dim=1)
    amplitude = singular[:, 0]
    address = torch.nn.functional.normalize(weights, dim=1) * amplitude.unsqueeze(1)

    def centred_rank(matrix: Any) -> float:
        centred = matrix - matrix.mean(dim=0, keepdim=True)
        spectrum = torch.linalg.svdvals(centred)
        return float(spectrum[1] / spectrum[0].clamp_min(1e-12))

    return {
        # The readings are computed in double for the rank numbers, but the two
        # views that feed a linear probe must keep the store's dtype: §70's
        # probe is float32, and mixing dtypes fails at the first matmul.
        "weights": weights.to(values.dtype),
        "address": address.to(values.dtype),
        "max_share": weights.max(dim=1).values,
        "effective_slots": 1.0 / (weights * weights).sum(dim=1),
        "active_slots": active,
        "rank1_residual": residual,
        "read_cos": read_cos,
        "address_rank1_residual": centred_rank(address),
    }


def summarise(torch: Any, block: Dict[str, Any]) -> Dict[str, Any]:
    def stat(name: str) -> Dict[str, float]:
        row = block[name].double()
        return {
            "mean": round(float(row.mean()), 6),
            "min": round(float(row.min()), 6),
            "max": round(float(row.max()), 6),
        }

    total = int(block["max_share"].numel())
    return {
        "sessions": total,
        "max_share": stat("max_share"),
        "effective_slots": stat("effective_slots"),
        "active_slots": {**stat("active_slots"), "counts": _counts(block["active_slots"])},
        "rank1_residual": stat("rank1_residual"),
        "read_cos": stat("read_cos"),
        "one_address_fraction": round(
            float((block["max_share"] >= ONE_ADDRESS_FLOOR).float().mean()), 4
        ),
        "single_slot_fraction": round(float((block["active_slots"] <= 1).float().mean()), 4),
        "rank1_fraction": round(float((block["rank1_residual"] <= RANK1_EPS).float().mean()), 4),
        "read_is_write_fraction": round(
            float((block["read_cos"] >= READ_COS_FLOOR).float().mean()), 4
        ),
        "address_rank1_residual": block["address_rank1_residual"],
    }


def _counts(row: Any) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for value in row.tolist():
        key = str(int(value))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


# --------------------------------------------------------------------------- #
# the readout arms (same budget as §70)
# --------------------------------------------------------------------------- #
def arm(
    boundaries: Any,
    torch: Any,
    train_x: Any,
    held_x: Any,
    y_train: Any,
    y_held: Any,
    structures: Sequence[str],
    *,
    names: int,
    slots: int,
) -> Dict[str, Any]:
    fitted = boundaries.run_probe(
        torch,
        train_x,
        y_train,
        held_x,
        y_held,
        kind="set",
        out=names,
        slots=slots,
        seed=boundaries.PROBE_SEED,
    )
    ceiling = boundaries.capacity_ceiling(
        torch, train_x, y_train, kind="set", out=names, slots=slots
    )
    folded = boundaries.cross_validate(
        torch,
        train_x,
        y_train,
        structures,
        kind="set",
        out=names,
        slots=slots,
        seed=boundaries.PROBE_SEED,
        folds=boundaries.FOLDS,
    )
    return {**fitted, "capacity": ceiling, "in_distribution": folded}


def feature_matrix(views: Dict[str, Any], name: str, block: Dict[str, Any]) -> Any:
    if name == "values":
        return views["values"]
    if name == "read":
        return views["read"]
    if name == "state":
        return views["state"]
    if name == "address":
        return block["address"]
    raise SystemExit(f"unknown view {name}")


# --------------------------------------------------------------------------- #
# gates and the fork
# --------------------------------------------------------------------------- #
def gates(report: Dict[str, Any]) -> Dict[str, Any]:
    """§72.6, mechanically, from numbers the report already stores."""
    held = report["mechanism"]["heldout"]
    arms = report["arms"]
    instrument = report["instrument"]

    one_address = float(held["one_address_fraction"]) >= FRACTION_FLOOR
    single_slot = float(held["single_slot_fraction"]) >= FRACTION_FLOOR
    rank1 = float(held["rank1_fraction"]) >= FRACTION_FLOOR
    read_is_write = float(held["read_is_write_fraction"]) >= FRACTION_FLOOR

    def transfers(name: str) -> bool:
        block = arms[name]
        return bool(
            float(block["heldout"]["exact"]) >= TRANSFER_FLOOR
            and float(block["capacity"]["exact"]) < CAPACITY_MAX
        )

    return {
        "S0_instrument": {
            "pass": bool(
                instrument["carrier_unchanged"]
                and instrument["checkpoint_unchanged"]
                and instrument["determinism_ok"]
                and instrument["features_finite"]
            ),
            "carrier_unchanged": instrument["carrier_unchanged"],
            "checkpoint_unchanged": instrument["checkpoint_unchanged"],
            "determinism_ok": instrument["determinism_ok"],
            "determinism_min_cosine": instrument["determinism_min_cosine"],
            "features_finite": instrument["features_finite"],
            "reading": (
                "the same sessions through the same frozen carrier reproduce their features, the "
                "carrier is unchanged, and every feature view is finite"
            ),
        },
        "S1_one_address": {
            "pass": bool(one_address),
            "one_address_fraction": held["one_address_fraction"],
            "max_share_mean": held["max_share"]["mean"],
            "effective_slots_mean": held["effective_slots"]["mean"],
            "floor": ONE_ADDRESS_FLOOR,
            "frac_floor": FRACTION_FLOOR,
            "reading": (
                "the softmax write gate is one-hot for nearly every session, so a turn writes to a "
                "single slot instead of distributing over the 16"
            ),
        },
        "S2_single_slot_store": {
            "pass": bool(single_slot and rank1),
            "single_slot_fraction": held["single_slot_fraction"],
            "rank1_fraction": held["rank1_fraction"],
            "rank1_residual": held["rank1_residual"],
            "active_slots": held["active_slots"]["counts"],
            "eps": RANK1_EPS,
            "reading": (
                "15 of the 16 slots are empty and the value matrix is rank 1, so the store is one "
                "vector - superposition is temporal (turn over turn in one slot), not across slots"
            ),
        },
        "S3_read_is_the_write": {
            "pass": bool(read_is_write),
            "read_is_write_fraction": held["read_is_write_fraction"],
            "read_cos": held["read_cos"],
            "floor": READ_COS_FLOOR,
            "reading": (
                "the pooled read is the strongest slot's value up to scale, so the read adds no "
                "dimension the stored value does not already have"
            ),
        },
        "S4_address_carries_no_roster": {
            # Registered as "address held-out <= ADDRESS_TRANSFER_MAX": a write
            # address that names the roster is a *high* transfer, so the gate is
            # read that way round rather than as "not transfers at all".
            "pass": bool(float(arms["address"]["heldout"]["exact"]) <= ADDRESS_TRANSFER_MAX),
            "heldout_exact": arms["address"]["heldout"]["exact"],
            "capacity": arms["address"]["capacity"]["exact"],
            "max": ADDRESS_TRANSFER_MAX,
            "reading": (
                "the 16 write weights name the roster no better than chance, so the address is not "
                "where the roster is written - it is a constant profile"
            ),
        },
        "S5_store_is_not_readable": {
            "pass": bool(not transfers("values") and not transfers("read")),
            "values_heldout": arms["values"]["heldout"]["exact"],
            "read_heldout": arms["read"]["heldout"]["exact"],
            "state_heldout": arms["state"]["heldout"]["exact"],
            "floor": TRANSFER_FLOOR,
            "capacity_max": CAPACITY_MAX,
            "reading": (
                "no admissible arm transfers: the same failure as §70, now with the write measured "
                "beside it"
            ),
        },
    }


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """§72.7, mechanically, fixed precedence."""
    if not gate["S0_instrument"]["pass"]:
        return {
            "id": "S0-instrument",
            "reading": "the carrier or the features moved: no write reading can be taken",
            "next": "fix the feature plumbing (determinism, finiteness, carrier hash), then re-run",
        }
    if not gate["S1_one_address"]["pass"]:
        return {
            "id": "S4-slots-are-distributed",
            "reading": (
                "the write is not one-hot, so the store does spread a turn over several slots - the "
                "§70.3 'constant address' reading does not hold on this split"
            ),
            "next": "re-measure what the address profile is (it is not a collision), then re-ask",
        }
    if not gate["S2_single_slot_store"]["pass"]:
        return {
            "id": "S4-two-addresses",
            "reading": (
                "the gate is one-hot but the store is not rank 1, so some sessions write a second "
                "slot: the collision reading holds only for the single-slot fraction, which is "
                "recorded beside it"
            ),
            "next": "split the sessions by active-slot count and re-probe the rank-1 ones only",
        }
    if not gate["S3_read_is_the_write"]["pass"]:
        return {
            "id": "S2-read-is-not-the-write",
            "reading": (
                "the store is one slot but the pooled read is not that slot's value, so the read "
                "path (query/key) is doing the losing, not the write"
            ),
            "next": "probe read_vector's query against the stored key",
        }
    if not gate["S4_address_carries_no_roster"]["pass"]:
        return {
            "id": "S3-address-codes-the-roster",
            "reading": (
                "the 16 write weights do name the roster, so the roster lives in the address even "
                "though the value does not"
            ),
            "next": "address the write per roster entry instead of per turn",
        }
    return {
        "id": "S1-single-address-temporal-superposition",
        "reading": (
            "every turn writes the same single slot, 15 slots stay empty, the read is that one "
            "value, and the address does not name the roster: the roster shares one 64-dim moving "
            "average with every earlier turn's text, so no readout family can separate it - the "
            "loss is the write, not the read"
        ),
        "next": (
            "change the write, not the readout: one address per turn (turn index as the address) on "
            "the same corpus, same steps, same parameters, then re-run §70's arms"
        ),
    }


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #
def run(
    families: Any, report_path: Path, report: Dict[str, Any], *, device: str = "cpu"
) -> Dict[str, Any]:
    boundaries = families.load_boundaries()
    contents = boundaries.load_contents()
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§72 reads the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or report["config"].get("roster_size") or 2)
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
    repeat_views = families.boundary_features(trainer, contents, core, heldout, indexes["roster"])
    determinism = float(
        torch.nn.functional.cosine_similarity(
            held_views["state"].double(), repeat_views["state"].double(), dim=1
        ).min()
    )

    train_block = slot_block(torch, core, train_views)
    held_block = slot_block(torch, core, held_views)
    finite = bool(
        torch.isfinite(held_views["state"]).all()
        and torch.isfinite(held_views["values"]).all()
        and torch.isfinite(held_block["address"]).all()
    )

    y_train = torch.as_tensor([list(row) for row in train_targets["roster"]], dtype=torch.float32)
    y_held = torch.as_tensor([list(row) for row in held_targets["roster"]], dtype=torch.float32)
    arms: Dict[str, Any] = {}
    for name in ARMS:
        train_x, held_x = contents.standardise(
            feature_matrix(train_views, name, train_block),
            feature_matrix(held_views, name, held_block),
        )
        arms[name] = arm(
            boundaries,
            torch,
            train_x,
            held_x,
            y_train,
            y_held,
            train_targets["structure"],
            names=len(names),
            slots=k,
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
        "determinism_min_cosine": round(determinism, 8),
        "determinism_ok": bool(determinism >= 1.0 - 1e-6),
        "features_finite": finite,
        "seconds": 0.0,
    }
    outcome: Dict[str, Any] = {
        "stage": "§72 what end_turn writes, and why no readout names the roster",
        "source_report": str(report_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "turns": indexes,
        "corpus": {
            "train_digest": (corpus.get("meta") or {}).get("train_digest"),
            "heldout_digest": (corpus.get("meta") or {}).get("heldout_digest"),
            "train_items": len(train),
            "heldout_items": len(heldout),
        },
        "probe": {
            "features": "frozen carrier state [h, read] and the store's v at the roster boundary",
            "write": "weights = softmax(exp(log_write_scale) * slot_gate(h)), recomputed from h",
            "active_slot": f"||v_slot|| >= {ACTIVE_SLOT_SHARE} * max ||v_slot||",
            "rank1": "second over first singular value of the 16x64 value matrix",
            "arms": list(ARMS),
            "readable_floor": READABLE_FLOOR,
            "transfer_floor": TRANSFER_FLOOR,
            "capacity_max": CAPACITY_MAX,
            "address_transfer_max": ADDRESS_TRANSFER_MAX,
            "one_address_floor": ONE_ADDRESS_FLOOR,
            "fraction_floor": FRACTION_FLOOR,
            "rank1_eps": RANK1_EPS,
            "read_cos_floor": READ_COS_FLOOR,
        },
        "mechanism": {
            "train": summarise(torch, train_block),
            "heldout": summarise(torch, held_block),
        },
        "arms": arms,
        "instrument": instrument,
    }
    outcome["gates"] = gates(outcome)
    outcome["branch"] = branch(outcome["gates"])
    instrument["seconds"] = round(time.time() - started, 2)
    outcome["instrument_ok"] = bool(outcome["gates"]["S0_instrument"]["pass"])
    return outcome


# --------------------------------------------------------------------------- #
# mechanical re-check
# --------------------------------------------------------------------------- #
def check(path: Path) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    problems: List[str] = []
    for split in ("train", "heldout"):
        block = (data.get("mechanism") or {}).get(split) or {}
        for key in (
            "one_address_fraction",
            "single_slot_fraction",
            "rank1_fraction",
            "read_is_write_fraction",
        ):
            value = block.get(key)
            if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
                problems.append(f"mechanism.{split}.{key} is not a fraction")
        for key in ("max_share", "rank1_residual", "read_cos"):
            row = block.get(key) or {}
            if not all(isinstance(row.get(part), (int, float)) for part in ("mean", "min", "max")):
                problems.append(f"mechanism.{split}.{key} is missing a summary")
    for name in ARMS:
        block = (data.get("arms") or {}).get(name) or {}
        for part in ("in_sample", "heldout", "capacity"):
            row = block.get(part) or {}
            if not isinstance(row.get("exact"), (int, float)):
                problems.append(f"arms.{name}.{part}.exact is missing")
            elif row.get("n") and not 0 <= int(row.get("correct", -1)) <= int(row["n"]):
                problems.append(f"arms.{name}.{part} correct/n is impossible")
    try:
        expected = gates(data)
    except (KeyError, TypeError, ZeroDivisionError) as error:
        problems.append(f"the stored numbers cannot be re-gated: {error}")
        return problems
    for key, block in expected.items():
        stored = (data.get("gates") or {}).get(key) or {}
        if stored.get("pass") != block["pass"]:
            problems.append(f"gate {key}.pass is stale")
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
    parser.add_argument("--check", default="", help="re-derive a stage-§72 JSON's verdict")
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
    report = json.loads(path.read_text(encoding="utf-8"))
    families = load_families()
    outcome = run(families, path, report, device=args.device)

    print(f"report : {path}")
    print(f"k      : {outcome['k']}   turns: {outcome['turns']}")
    print()
    for split in ("train", "heldout"):
        block = outcome["mechanism"][split]
        print(
            f"  {split:8s} one-address {block['one_address_fraction']:.4f} "
            f"single-slot {block['single_slot_fraction']:.4f} "
            f"rank1 {block['rank1_fraction']:.4f} read=write {block['read_is_write_fraction']:.4f}"
        )
        print(
            f"           max-share mean {block['max_share']['mean']:.6f}  "
            f"eff-slots {block['effective_slots']['mean']:.4f}  "
            f"rank1 residual max {block['rank1_residual']['max']:.2e}  "
            f"read cos min {block['read_cos']['min']:.6f}"
        )
        print(
            f"           active slots {block['active_slots']['counts']}  "
            f"address rank1 residual {block['address_rank1_residual']:.3e}"
        )
    print()
    print(f"  {'arm':10s} {'in':>8s} {'cap':>8s} {'indist':>8s} {'held':>8s}")
    for name in ARMS:
        block = outcome["arms"][name]
        print(
            f"  {name:10s} {block['in_sample']['exact']:8.4f} {block['capacity']['exact']:8.4f} "
            f"{block['in_distribution']['exact']:8.4f} {block['heldout']['exact']:8.4f} "
            f"({block['heldout']['correct']}/{block['heldout']['n']})"
        )
    print()
    for key, block in outcome["gates"].items():
        print(f"  {key:36s} {'PASS' if block['pass'] else 'FAIL'}")
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
