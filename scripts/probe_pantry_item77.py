#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§77: does the *content* written per turn limit composition - per item vs turn end?

Why this exists
---------------
§76 changed how *wide* one turn's write is (one slot vs four chunks of the same
value) and the leave-roster-out cell did not move (``W2``): the resolution of a
single write is not the limit. §76.19 named the next subject, and this stage is
its one treatment:

* **control** - ``address="turn"``: turn ``k`` writes once, from the ``h`` at the
  turn's last token, into slot ``k``. §73's write.
* **treatment** - ``address="item"``: every list item writes once, from the ``h``
  at *that item's* last character, into the session's next slot. A roster turn
  with two items is two writes, so the two names no longer share one rank-1
  summary.

The token stream, the recurrence, the parameters, the corpus, the initial
weights and the budget are identical; the only arm difference is ``--address``.
The treatment is a write **plan** (which positions, which slots), not a second
forward pass.

Two things were measured before this stage was registered (§77.2):

1. Hashing an item's bytes into a slot (the literal "content-addressed" reading)
   collides: FNV-1a over 16 slots loses slots in 209/400 training and 101/200
   held-out sessions. The read is already content-addressed, so the slot index
   only has to avoid overwrites; the treatment uses the session's item counter.
2. On §76's trained control carrier the treatment really changes the store:
   active slots at the roster boundary 2 -> 3 in every held-out session,
   rank-1 residual 0.3278 -> 0.4552, the two item values are not the same vector
   (cosine mean 0.2251), and both item writes land (gate >= 0.1185).

What is gated
-------------
``M_slots`` (the write the arm was registered with is the write the store shows)
and ``M_landed`` (each write's stored vector is ``sigmoid(write_gate(h))`` times
``value_proj(h)``: the item write for the treatment, the turn-end write for the
control). Then §74's three readings (in-sample / held-out / leave-roster-out),
§75's seen/unseen split and the registered unseen floor.

What this is not
----------------
Not a capability score (core score stays 0.00/10), not a binding claim, and not a
search over write rules: the treatment was fixed before the run.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_item77.py \\
        --control data/pantry_stage/item77/control/pantry_deduction_*.json \\
        --treatment data/pantry_stage/item77/item/pantry_deduction_*.json \\
        --out data/pantry_stage/item77/k2.json

    ./.venv/bin/python scripts/probe_pantry_item77.py --check data/pantry_stage/item77/k2.json
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

# §77.4, written before either arm was trained. The null, alpha and floor are
# §74's; the rest are this stage's.
NULL_DRAWS = 400
NULL_SEED = 20261125
ALPHA = 0.005
COMPOSED_OVERLAP_FRACTION = 0.75
CONTRAST_MARGIN = 0.05
FIT_COMPARABILITY = 0.15
UNSEEN_FLOOR = 0.125
ITEM_SEPARATOR = "、"
EXPECTED_ITEMS_PER_SESSION = 5
# Both arms write two turns before the roster boundary; the control writes once
# per turn (2 slots) and the treatment writes once per item (1 + 2 = 3 slots).
MECHANISM_MAX = {"control": 3, "treatment": 3}
MECHANISM_COVERAGE = 0.99
MECHANISM_COSINE = 0.999
ARMS = ("control", "treatment")
FAMILIES = ("linear_state", "linear_values", "nonlinear_quad")
REGISTERED = {
    "control": {"address": "turn", "write_strength": "learned", "write_slots": 1},
    "treatment": {"address": "item", "write_strength": "learned", "write_slots": 1},
}
STAGE = "§77 the content written per turn: one write per list item"


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
    module = _load("pantry_item77_composition", COMPOSITION)
    for name, expected in (
        ("NULL_DRAWS", NULL_DRAWS),
        ("ALPHA", ALPHA),
        ("COMPOSED_OVERLAP_FRACTION", COMPOSED_OVERLAP_FRACTION),
        ("NULL_SEED", NULL_SEED),
    ):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(
                f"§77 was registered against {name}={expected}, §74 now has {actual}; "
                "the stages no longer share a criterion"
            )
    return module


def load_split75() -> Any:
    """§75's module: the split and the within-cell null, one copy only."""
    module = _load("pantry_item77_split75", SPLIT75)
    for name, expected in (("NULL_DRAWS", NULL_DRAWS), ("ALPHA", ALPHA)):
        actual = getattr(module, name)
        if actual != expected:
            raise SystemExit(f"§77 was registered against {name}={expected}, §75 now has {actual}")
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


def exact_fraction(store: Dict[str, Any], value: int) -> float:
    counts = (store.get("active_slots") or {}).get("counts") or {}
    total = sum(int(v) for v in counts.values())
    if total <= 0:
        return 0.0
    return round(int(counts.get(str(value), 0)) / total, 6)


def items_per_session(trainer: Any, probe: Any, session: Dict[str, Any]) -> int:
    """How many list items one session splits into (§77.4's 5).

    The session's turns are dicts; the tokens the write plan indexes are the ones
    ``turn_payload`` builds (``user_input + "\\n"``), not the dicts themselves.
    """
    tokens, _ = probe.turn_payload(trainer, session)
    return sum(len(trainer.item_end_positions(turn)) for turn in tokens)


# --------------------------------------------------------------------------- #
# the mechanism: did each write land, and where
# --------------------------------------------------------------------------- #
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


def landing(
    trainer: Any,
    probe: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    *,
    arm: str,
    batch: int = 64,
) -> Dict[str, Any]:
    """``M_landed``: the stored vector is the write the rule says it is.

    Treatment: every roster item sits in its own non-empty slot, and that slot's
    content is ``sigmoid(write_gate(h_item)) * value_proj(h_item)`` (the slot was
    fresh before the write, so the moving average is the write itself).
    Control: the turn-end write landed the same way, from the turn's last token.

    No fitted parameter is involved: the h trajectory is replayed from the
    boundary state before the roster turn, and the expected vector is the core's
    own projections.
    """
    torch = core._torch
    cosine = torch.nn.functional.cosine_similarity
    landed = 0
    total = 0
    failures: List[Dict[str, Any]] = []
    min_cosine = 1.0
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
                meta = session["session_meta"]
                roster = int(meta["roster_turn"])
                if roster >= len(snapshots):
                    raise SystemExit("the roster boundary does not exist in this corpus")
                before = snapshots[roster - 1] if roster > 0 else core.init_state(1).tensors
                hidden = before["h"][index : index + 1]
                if roster > 0:
                    # run_session advances the controller between turns; the
                    # replay has to start from the same h the write saw.
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
                values = store["v"][index]
                problems: List[str] = []
                cosines: List[float] = []
                if arm == "control":
                    position = len(stacked) - 1
                    slot = roster % int(core.slots)
                    expected = torch.sigmoid(core.write_gate(stacked[position])) * core.value_proj(
                        stacked[position]
                    )
                    observed = values[slot].reshape(1, -1)
                    value = float(cosine(observed, expected).squeeze())
                    cosines.append(value)
                    if float(values[slot].norm()) <= 0.0:
                        problems.append(f"slot {slot} is empty")
                    if value < MECHANISM_COSINE:
                        problems.append(f"slot {slot} cosine {value:.6f}")
                else:
                    positions = trainer.item_end_positions(turns[index][roster])
                    counter = sum(
                        len(trainer.item_end_positions(turns[index][turn]))
                        for turn in range(roster)
                    )
                    slots = [(counter + item) % int(core.slots) for item in range(len(positions))]
                    if len(set(slots)) != len(slots):
                        problems.append(f"roster items reuse a slot: {slots}")
                    for position, slot in zip(positions, slots):
                        expected = torch.sigmoid(
                            core.write_gate(stacked[position])
                        ) * core.value_proj(stacked[position])
                        observed = values[slot].reshape(1, -1)
                        value = float(cosine(observed, expected).squeeze())
                        cosines.append(value)
                        if float(values[slot].norm()) <= 0.0:
                            problems.append(f"slot {slot} is empty")
                        if value < MECHANISM_COSINE:
                            problems.append(f"slot {slot} cosine {value:.6f}")
                    if len(positions) < 2:
                        problems.append(f"the roster turn has {len(positions)} items")
                total += 1
                if cosines:
                    min_cosine = min(min_cosine, min(cosines))
                if problems:
                    if len(failures) < 20:
                        failures.append({"session_id": session["session_id"], "problems": problems})
                else:
                    landed += 1
    return {
        "arm": arm,
        "sessions": total,
        "landed": landed,
        "coverage": round(landed / total, 6) if total else 0.0,
        "required_coverage": MECHANISM_COVERAGE,
        "required_cosine": MECHANISM_COSINE,
        "min_cosine": round(min_cosine, 6),
        "failures": failures,
    }


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
        raise SystemExit("§77 reads the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or 2)
    seed = int(corpus_block.get("seed") or 0)
    if seed <= 0:
        raise SystemExit("the report does not record its corpus seed; §77 cannot read it")

    selection = contents.load_selection()
    trainer = selection.load_trainer()
    probe = selection.load_probe()
    module = trainer._load_generator()
    # §77 reads the seed the carrier was trained on. §76's probe did not, which
    # is recorded as a §77 finding: its readings were computed on the default
    # seed (20261113) while the carrier had been trained on 20261127.
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
        for which in ("in_sample", "heldout", "leave_roster_out"):
            block = readings[name][which]
            block["observed"] = split75.with_interval(block["observed"])

    store = families.store_shape(torch, held_views["values"], held_views["value_shape"])
    landing_block = landing(trainer, probe, core, heldout, arm=arm)
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
        "registered": dict(REGISTERED[arm]),
        "mode_matches": bool(
            config.get("address") == REGISTERED[arm]["address"]
            and config.get("write_strength") == REGISTERED[arm]["write_strength"]
            and int(config.get("write_slots") or 1) == REGISTERED[arm]["write_slots"]
        ),
        "weights_hash_before": weights_before,
        "weights_hash_after": weights_after,
        "carrier_unchanged": weights_after == weights_before,
        "checkpoint_sha256_before": hash_before,
        "checkpoint_sha256_after": hash_after,
        "checkpoint_unchanged": hash_before == hash_after,
        "seconds": round(time.time() - started, 3),
    }
    meta = corpus.get("meta") or {}
    corpus_recomputed = {
        "train_digest": meta.get("train_digest"),
        "heldout_digest": meta.get("heldout_digest"),
        "seed": seed,
    }
    corpus_digests_match = bool(
        corpus_recomputed["train_digest"] == corpus_block.get("train_digest")
        and corpus_recomputed["heldout_digest"] == corpus_block.get("heldout_digest")
    )
    outcome: Dict[str, Any] = {
        "stage": STAGE,
        "arm": arm,
        "source_report": str(report_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "corpus_seed": seed,
        "dimensions": {"colours": len(colours), "names": len(names)},
        "corpus": {
            "train_digest": corpus_recomputed["train_digest"],
            "heldout_digest": corpus_recomputed["heldout_digest"],
            "recorded_train_digest": corpus_block.get("train_digest"),
            "recorded_heldout_digest": corpus_block.get("heldout_digest"),
            "digests_match": corpus_digests_match,
            "train_items": len(train),
            "heldout_items": len(heldout),
            "train_rosters": len(set(rosters)),
            "items_per_session": (items_per_session(trainer, probe, train[0]) if train else 0),
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
        "store": store,
        "landing": landing_block,
        "reproduction": {
            "applicable": False,
            "equal": False,
            "reason": (
                "both arms are retrained in this stage, so the A/B does not rest on an earlier "
                "run; §76's stored control cells are not a reproduction target either, because "
                "§76's probe read the default corpus seed while its carrier was trained on "
                "20261127 (§77.2 records the defect)"
            ),
        },
        "readings": readings,
        "instrument": instrument,
    }
    outcome["gates"] = arm_gates(composition, outcome, k=k)
    outcome["instrument_ok"] = bool(
        outcome["gates"]["N0_instrument"]["pass"]
        and outcome["gates"]["M_slots"]["pass"]
        and outcome["gates"]["M_landed"]["pass"]
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
    landing_block = outcome["landing"]
    median = slot_median(store)
    limit = MECHANISM_MAX[outcome["arm"]]
    exact3 = exact_fraction(store, 3)
    n0 = {
        "pass": bool(
            instrument["carrier_unchanged"]
            and instrument["checkpoint_unchanged"]
            and instrument["mode_matches"]
            and corpus.get("train_digest")
            and corpus.get("heldout_digest")
            and corpus.get("digests_match")
        ),
        "carrier_unchanged": instrument["carrier_unchanged"],
        "checkpoint_unchanged": instrument["checkpoint_unchanged"],
        "mode_matches": instrument["mode_matches"],
        "corpus_digests_recorded": bool(
            corpus.get("train_digest") and corpus.get("heldout_digest")
        ),
        "corpus_digests_match": corpus.get("digests_match"),
        "reading": (
            "the carrier and checkpoint are unchanged, the report's write mode is the one "
            "this arm registered, and the corpus the probe re-derived is the corpus the "
            "carrier was trained on (digests equal)"
        ),
    }
    mechanism = {
        "pass": bool(
            median <= limit
            if outcome["arm"] == "control"
            else (median >= limit and exact3 >= MECHANISM_COVERAGE)
        ),
        "arm": outcome["arm"],
        "active_slots_median": median,
        "exact_three_fraction": exact3,
        "required_coverage": MECHANISM_COVERAGE,
        "expected": (
            f"median <= {limit} (one write per turn; two turns before the roster boundary)"
            if outcome["arm"] == "control"
            else (
                f"median >= {limit} and >= {MECHANISM_COVERAGE:.0%} with exactly 3 "
                "(one write per item: 1 item + 2 roster items)"
            )
        ),
        "counts": store.get("active_slots", {}).get("counts"),
        "rank1_residual_mean": store.get("rank1_residual", {}).get("mean"),
        "reading": (
            "the write the arm was registered with is the write the store shows; if this "
            "fails the A/B never happened"
        ),
    }
    landed = {
        "pass": bool(
            landing_block["sessions"] > 0
            and landing_block["landed"] / landing_block["sessions"] >= MECHANISM_COVERAGE
        ),
        "arm": outcome["arm"],
        "sessions": landing_block["sessions"],
        "landed": landing_block["landed"],
        "coverage": landing_block["coverage"],
        "required_coverage": MECHANISM_COVERAGE,
        "min_cosine": landing_block["min_cosine"],
        "required_cosine": MECHANISM_COSINE,
        "reading": (
            "each write's stored vector is sigmoid(write_gate(h)) * value_proj(h) at the "
            "position the plan names, and the treatment's two roster items occupy "
            "different non-empty slots; recomputed from the carrier, no fitted parameter"
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
    gates["M_slots"] = mechanism
    gates["M_landed"] = landed
    gates["S1_seen"] = block("seen")
    gates["S2_unseen"] = block("unseen")
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
            "the treatment's own gates. The descriptors are the same deltas on every cell; "
            "§77 registered the expectation that linear_values moves more than linear_state "
            "- reported, not gated"
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
        and control["gates"]["M_slots"]["pass"]
        and treatment["gates"]["M_slots"]["pass"]
        and control["gates"]["M_landed"]["pass"]
        and treatment["gates"]["M_landed"]["pass"]
    ):
        return {
            "id": "N0-instrument",
            "reading": (
                "an arm's carrier, checkpoint, write mode or corpus record moved, or a write "
                "did not land where the rule says it lands; the A/B never happened"
            ),
            "next": "fix the instrument before reading either arm",
        }
    if not gates["Q1_relative_fit"]["any"]:
        return {
            "id": "P3-treatment-no-fit",
            "reading": (
                "the item-addressed arm does not fit its own training rosters above the "
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
            "id": "P1-item-content-was-the-limit",
            "reading": (
                "with one write per list item the leave-roster-out cell reaches the "
                "registered floor and the unseen-roster cell clears 3/24, so which state a "
                f"turn writes was part of the loss ({', '.join(composed)})"
            ),
            "next": (
                "still not binding: the next registration is a third seed and a name-indexed "
                "read, and neither may be claimed from this stage"
            ),
        }
    if not gates["Q2_transfer"]["any"]:
        return {
            "id": "P6-treatment-no-transfer",
            "reading": (
                "the item-addressed arm fits but does not beat the held-out label "
                "permutation null, so splitting the turn's write broke transfer"
            ),
            "next": "the write rule, not the readout, is the subject; one more content rule only",
        }
    if contrast_block["readable"] and contrast_block["gain_arms"]:
        return {
            "id": "P4-partial-gain-from-item-content",
            "reading": (
                "one write per item raises leave-roster-out by at least the registered "
                "margin but not to the floor, so the write's content matters without being "
                f"sufficient ({', '.join(contrast_block['gain_arms'])})"
            ),
            "next": (
                "ask what an item is still missing (the value -> name pair as one entry), "
                "not more epochs or width"
            ),
        }
    if contrast_block["readable"] and contrast_block["loss_arms"]:
        return {
            "id": "P5-item-content-hurt",
            "reading": (
                "one write per item is worse than the turn-end write, so the turn's last h "
                "was the better addressable unit "
                f"({', '.join(contrast_block['loss_arms'])})"
            ),
            "next": (
                "the item's own h is not the loss; the next stage reads what the turn-end h "
                "carries that an item's h does not"
            ),
        }
    return {
        "id": "P2-both-width-and-content-were-not-the-limit",
        "reading": (
            "one write per item is not further from the control than the registered margin "
            "on leave-roster-out, so neither the width nor the content of a write is what "
            "limits composition"
        ),
        "next": (
            "the limit is downstream of the store's contents; the next registration changes "
            "the readout end, not more epochs, width or data"
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
        "M_slots",
        "M_landed",
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
    if outcome["instrument"]["mode_matches"] is not True:
        problems.append(f"{arm}: the report's write mode is not the registered one")
    if outcome["store"]["active_slots"]["counts"] != recomputed["M_slots"]["counts"]:
        problems.append(f"{arm}: the store counts do not match the stored block")
    declared = outcome["instrument"]["write_mode"]
    registered = REGISTERED[arm]
    if declared.get("address") != registered["address"]:
        problems.append(
            f"{arm}: address is {declared.get('address')!r}, registered "
            f"{registered['address']!r}"
        )
    if int(declared.get("write_slots") or 1) != registered["write_slots"]:
        problems.append(f"{arm}: write_slots is not the registered one")
    if outcome["corpus"].get("digests_match") is not True:
        problems.append(f"{arm}: the probe re-derived a different corpus than the report")
    held = outcome["landing"]
    if int(held["sessions"]) > 0:
        expected = round(int(held["landed"]) / int(held["sessions"]), 6)
        if held["coverage"] != expected:
            problems.append(f"{arm}: landing coverage does not equal landed/sessions")
    if arm == "treatment":
        expected_items = EXPECTED_ITEMS_PER_SESSION
        if int(outcome["corpus"].get("items_per_session") or 0) != expected_items:
            problems.append(
                f"{arm}: the corpus has {outcome['corpus'].get('items_per_session')} items "
                f"per session, registered {expected_items}"
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
        return ["this is not a §77 report"]
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
    if str(probe.get("item_separator")) != ITEM_SEPARATOR:
        problems.append(f"the item separator is not the registered {ITEM_SEPARATOR!r}")
    if int(probe.get("expected_items_per_session", -1)) != EXPECTED_ITEMS_PER_SESSION:
        problems.append(f"items per session is not the registered {EXPECTED_ITEMS_PER_SESSION}")
    if float(probe.get("mechanism_coverage", -1.0)) != MECHANISM_COVERAGE:
        problems.append("the mechanism coverage is not the registered one")
    if float(probe.get("mechanism_cosine", -1.0)) != MECHANISM_COSINE:
        problems.append("the mechanism cosine is not the registered one")
    for arm in ARMS:
        block = (data.get("arms") or {}).get(arm)
        if not block:
            problems.append(f"the {arm} arm is missing")
            continue
        _check_arm(problems, block)
    if "arms" not in data or any(arm not in (data.get("arms") or {}) for arm in ARMS):
        return problems
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
    parser.add_argument("--control", default="", help="the turn-addressed report")
    parser.add_argument("--treatment", default="", help="the item-addressed report")
    parser.add_argument("--check", default="", help="re-derive a §77 JSON's verdict")
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
            "item_separator": ITEM_SEPARATOR,
            "expected_items_per_session": EXPECTED_ITEMS_PER_SESSION,
            "mechanism_max": MECHANISM_MAX,
            "mechanism_coverage": MECHANISM_COVERAGE,
            "mechanism_cosine": MECHANISM_COSINE,
            "composition_floor": {
                "overlap_fraction": COMPOSED_OVERLAP_FRACTION,
                "overlap": round(COMPOSED_OVERLAP_FRACTION * arms["control"]["k"], 4),
            },
            "readings": "§74's three, then §75's seen/unseen split of the held-out cell",
            "arms": {
                "control": "address=turn, write_slots=1 (§73's write, retrained)",
                "treatment": "address=item: one write per list item, session slot counter",
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
            f"exactly-3 {block['gates']['M_slots']['exact_three_fraction']:.4f}  "
            f"landed {block['landing']['landed']}/{block['landing']['sessions']}  "
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
            "M_slots",
            "M_landed",
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
