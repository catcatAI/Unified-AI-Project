#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§66: where does the roster binding go? (readout/state probe, no new training)

Why this exists
---------------
§65 closed the capacity question: at k=2/3/4/5 the arm fits its 400 declared
items (0.9750/0.9725/0.9750) and still answers held-out at or below that rung's
own chance (0.1900/0.0950/0.1300 vs 1/3, 1/4, 1/5). The reading that moves with
k is the roster's hold on the output: answers landing inside the roster fall
0.555 -> 0.550 -> 0.500 -> 0.450 against content-free expectations of
0.167 -> 0.250 -> 0.333 -> 0.417, so its lead over guessing falls 0.388 ->
0.033, and in-roster accuracy never beats chance. "The roster is too small" is
excluded; the remaining question is *where* the binding is lost.

This probe changes only the roster text of a held-out session and reads the
state at three levels, on checkpoints that are already trained:

* ``h`` - the controller state at the roster turn and at the answer turn;
* ``read`` - ``core.read_vector`` at those same boundaries (the store's
  content-addressed read, i.e. what the output head is actually shown);
* ``store`` - the key/value slots at the answer boundary, so "it was never
  written" can be told apart from "it was written and not read";
* the score each corpus name gets at the answer boundary, then the argmax over
  the session's own roster.

Three edits, applied to the same held-out sessions:

* ``identity`` - no edit (re-run; R1 must reproduce the report's ``results.full``
  exactly, otherwise the corpus/checkpoint pairing is wrong);
* ``twin`` - §62's name swap: the roster's mapping flips, so the correct answer
  becomes the other person; the evidence value is unchanged;
* ``reorder`` - §64's order twin: the same mapping, entries listed in reverse,
  so the correct answer does not move;
* ``mismatch`` - a reference distribution: session *i*'s answer boundary against
  session *i+1*'s (a different roster, different evidence, different everything).
  It gives the "unrelated" cosine so "the roster barely moves the state" can be
  read against something measured rather than assumed.

What it is not
--------------
Not a capability score. No training, no threshold on accuracy, no held-out
tuning. The state differences are diagnostics; the only behavioural number that
can decide between the readings is whether the head follows the swapped mapping.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_readout.py \\
        --report data/pantry_stage/ord_arm/pantry_deduction_20261115-015751.json \\
        --out data/pantry_stage/probe66/k2.json
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
TRAINER = REPO_ROOT / "scripts" / "train_pantry_deduction.py"

# §66.4, written before the run.
READ_COS_STATIC = 0.99
STORE_WRITTEN = 0.01
FOLLOWS_MAPPING = 0.50
READ_COS_CUTS = (0.90, 0.95, 0.99, 0.999)
PROBE_BATCH = 32

# The keys R1 compares; they are every field `summarise` produces for `results.full`.
R1_KEYS = (
    "n",
    "correct",
    "exact",
    "chance",
    "wilson_lower",
    "wilson_upper",
    "in_roster",
    "in_roster_exact",
    "in_roster_chance",
    "ranking_correct",
    "ranking_exact",
    "distinct_predictions",
    "top_prediction",
    "top_share",
)


def load_trainer() -> Any:
    """Import the trainer by path so the probe cannot drift from its encoding."""
    spec = importlib.util.spec_from_file_location("pantry_readout_trainer", TRAINER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["pantry_readout_trainer"] = module
    spec.loader.exec_module(module)
    return module


def checkpoint_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rebuild_core(trainer: Any, report: Dict[str, Any], *, device: str = "cpu") -> Any:
    """Rebuild the exact core a report names and verify the checkpoint hash."""
    config = report.get("config") or {}
    core = trainer.build_core(
        hidden=int(config.get("hidden", trainer.HIDDEN)),
        emb=int(config.get("emb", trainer.EMB)),
        device=device,
        kind=str(config.get("core") or "gru"),
        memory=bool(config.get("memory", True)),
        address=str(config.get("address") or "gate"),
        # §76: the write strength is shape-invisible, so a forced-write carrier
        # must be rebuilt with it or the strict guard rejects the checkpoint.
        write_strength=str(config.get("write_strength") or "learned"),
        # §76: the write width is shape-invisible too (same projections, a different
        # scatter), so a multi-slot carrier must be rebuilt with it.
        write_slots=int(config.get("write_slots") or 1),
    )
    checkpoint = report.get("checkpoint")
    if not checkpoint or not Path(checkpoint).exists():
        raise SystemExit("the report's checkpoint is missing; nothing to probe")
    core.load_weights(checkpoint, strict_config=True)
    if core.weights_hash() != report.get("weights_hash"):
        raise SystemExit("checkpoint weights_hash does not match the report")
    return core


# --------------------------------------------------------------------------- #
# reading one variant
# --------------------------------------------------------------------------- #
def turn_payload(trainer: Any, session: Dict[str, Any]) -> Tuple[List[List[int]], List[float]]:
    """The tokens and gaps ``evaluate`` feeds the core for variant ``full``."""
    dropped = trainer.drop_indices(session, "full")
    kept = [turn for turn in session["turns"] if int(turn["turn_id"]) not in dropped]
    tokens = [
        [trainer.BYTE_OFFSET + byte for byte in (turn["user_input"] + "\n").encode("utf-8")]
        for turn in kept
    ]
    gaps = [float(turn["dt_s"]) for turn in kept]
    return tokens, gaps


def score_names(trainer: Any, core: Any, boundary: Any, names: Sequence[str]) -> Any:
    """``[B, len(names)]`` sequence log-likelihoods, exactly ``rank_actor``'s loop.

    ``rank_actor`` returns only the argmax; the probe needs every candidate's
    score so it can measure how far the scores moved, not just whether the
    winner changed.
    """
    import torch.nn.functional as functional

    torch = core._torch
    view = trainer._decode_view(boundary)
    batch = int(view["h"].shape[0])
    device = view["h"].device
    totals = []
    for name in names:
        cursor = view
        acc = torch.zeros(batch, dtype=torch.float32, device=device)
        for token in trainer.candidates_tokens(name):
            logits = core.token_logits(cursor)
            acc = acc + functional.log_softmax(logits, dim=-1)[:, int(token)].float()
            feed = torch.full((batch,), int(token), dtype=torch.long, device=device)
            cursor = core.consume(feed, cursor)
        totals.append(acc)
    return torch.stack(totals, dim=1)


def read_variant(
    trainer: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    names: Sequence[str],
    *,
    batch: int = PROBE_BATCH,
) -> Dict[str, Any]:
    """One batched forward per chunk; every per-session state is kept.

    The roster turn is read from ``session_meta["roster_turn"]`` rather than
    hardcoded, and a chunk that disagrees on it is an error: the boundary list
    is indexed by turn, so a mixed chunk would silently compare the wrong turn.
    """
    torch = core._torch
    hidden_final: List[np.ndarray] = []
    read_final: List[np.ndarray] = []
    hidden_roster: List[np.ndarray] = []
    read_roster: List[np.ndarray] = []
    store_key: List[np.ndarray] = []
    store_value: List[np.ndarray] = []
    scores: List[np.ndarray] = []
    predictions: List[str] = []
    core.eval()
    with torch.no_grad():
        for chunk in trainer._chunks(list(sessions), batch):
            roster_turns = {int(session["session_meta"]["roster_turn"]) for session in chunk}
            if len(roster_turns) != 1:
                raise SystemExit(f"a chunk mixes roster turns {sorted(roster_turns)}")
            roster_turn = roster_turns.pop()
            turns: List[List[List[int]]] = []
            gaps: List[List[float]] = []
            for session in chunk:
                tokens, deltas = turn_payload(trainer, session)
                turns.append(tokens)
                gaps.append(deltas)
            boundaries: List[Any] = []
            state, _ = trainer.run_session(core, turns, gaps, boundaries=boundaries)
            final = dict(state.tensors)
            roster = trainer._decode_view(boundaries[roster_turn])
            produced = trainer.generate_bytes(core, final)
            scored = score_names(trainer, core, final, names)
            hidden_final.append(final["h"].cpu().numpy())
            read_final.append(core.read_vector(final).cpu().numpy())
            hidden_roster.append(roster["h"].cpu().numpy())
            read_roster.append(core.read_vector(roster).cpu().numpy())
            if "v" in final and "k" in final:
                slots = int(final["v"].shape[1])
                store_key.append(final["k"].cpu().numpy().reshape(len(chunk), -1))
                store_value.append(final["v"].cpu().numpy().reshape(len(chunk), -1))
            else:
                store_key.append(np.zeros((len(chunk), 0), dtype=np.float32))
                store_value.append(np.zeros((len(chunk), 0), dtype=np.float32))
            scores.append(scored.cpu().numpy())
            predictions.extend(trainer._decoded(item) for item in produced)
    return {
        "prediction": predictions,
        "scores": np.concatenate(scores, axis=0),
        "h_final": np.concatenate(hidden_final, axis=0),
        "read_final": np.concatenate(read_final, axis=0),
        "h_roster": np.concatenate(hidden_roster, axis=0),
        "read_roster": np.concatenate(read_roster, axis=0),
        "store_k": np.concatenate(store_key, axis=0),
        "store_v": np.concatenate(store_value, axis=0),
    }


# --------------------------------------------------------------------------- #
# arithmetic
# --------------------------------------------------------------------------- #
def _cos_rows(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    numerator = (left * right).sum(axis=1)
    denominator = np.linalg.norm(left, axis=1) * np.linalg.norm(right, axis=1)
    return numerator / np.maximum(denominator, 1e-12)


def _rel_rows(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """``||a - b|| / ||a||`` over the whole per-row vector (slots flattened)."""
    numerator = np.linalg.norm(left - right, axis=1)
    denominator = np.linalg.norm(left, axis=1)
    return numerator / np.maximum(denominator, 1e-12)


def _distribution(values: np.ndarray) -> Dict[str, float]:
    values = np.asarray(values, dtype=np.float64)
    return {
        "mean": round(float(values.mean()), 4),
        "min": round(float(values.min()), 4),
        "p25": round(float(np.percentile(values, 25)), 4),
        "median": round(float(np.median(values)), 4),
        "p75": round(float(np.percentile(values, 75)), 4),
        "max": round(float(values.max()), 4),
    }


def _rate(flags: Sequence[bool]) -> float:
    return round(float(sum(1 for flag in flags if flag)) / len(flags), 4) if flags else 0.0


def roster_indices(sessions: Sequence[Dict[str, Any]], names: Sequence[str]) -> List[List[int]]:
    return [
        [names.index(name) for name in session["environment"]["actors"]] for session in sessions
    ]


def pick_all(
    scores: np.ndarray,
    indices: Sequence[List[int]],
    names: Sequence[str],
) -> Tuple[List[str], List[int]]:
    """Per-row argmax over that row's own roster -> (names, positions).

    ``indices`` are positions into the corpus-wide ``names``; the returned name
    must be ``names[index[position]]``, not the position itself. Getting that
    wrong makes every name comparison trivially false, which is why the probe
    cross-checks its identity accuracy against the report's ``ranking_exact``.
    """
    chosen_names: List[str] = []
    chosen_positions: List[int] = []
    for row, index in enumerate(indices):
        position = int(np.argmax(scores[row, index]))
        chosen_positions.append(position)
        chosen_names.append(str(names[index[position]]))
    return chosen_names, chosen_positions


def compare_variant(
    identity: Dict[str, Any],
    variant: Dict[str, Any],
    sessions: Sequence[Dict[str, Any]],
    names: Sequence[str],
    indices: Sequence[List[int]],
    *,
    label: str,
) -> Dict[str, Any]:
    """State movement plus score movement, for one edit against ``identity``."""
    variant_names, variant_positions = pick_all(variant["scores"], indices, names)
    _, identity_positions = pick_all(identity["scores"], indices, names)
    deltas = []
    for row, index in enumerate(indices):
        deltas.append(
            float(np.mean(np.abs(variant["scores"][row, index] - identity["scores"][row, index])))
        )
    targets = [session["ground_truth_oracle"]["culprit"] for session in sessions]
    last_entries = [session["environment"]["actors"][-1] for session in sessions]
    payload: Dict[str, Any] = {
        "label": label,
        "n": len(sessions),
        "h_cos_final": _distribution(_cos_rows(identity["h_final"], variant["h_final"])),
        "read_cos_final": _distribution(_cos_rows(identity["read_final"], variant["read_final"])),
        "h_cos_roster": _distribution(_cos_rows(identity["h_roster"], variant["h_roster"])),
        "read_cos_roster": _distribution(
            _cos_rows(identity["read_roster"], variant["read_roster"])
        ),
        "h_rel_final": _distribution(_rel_rows(identity["h_final"], variant["h_final"])),
        "read_rel_final": _distribution(_rel_rows(identity["read_final"], variant["read_final"])),
        "store_k_rel_final": (
            _distribution(_rel_rows(identity["store_k"], variant["store_k"]))
            if identity["store_k"].shape[1]
            else None
        ),
        "store_v_rel_final": (
            _distribution(_rel_rows(identity["store_v"], variant["store_v"]))
            if identity["store_v"].shape[1]
            else None
        ),
        "same_prediction": _rate(
            [left == right for left, right in zip(identity["prediction"], variant["prediction"])]
        ),
        "same_roster_argmax": _rate(
            [left == right for left, right in zip(identity_positions, variant_positions)]
        ),
        "argmax_flip_rate": _rate(
            [left != right for left, right in zip(identity_positions, variant_positions)]
        ),
        "mean_abs_delta_roster": round(float(np.mean(deltas)), 4),
        "accuracy": _rate([name == target for name, target in zip(variant_names, targets)]),
        "follows_last_entry": _rate(
            [name == last for name, last in zip(variant_names, last_entries)]
        ),
    }
    return payload


def summarise_mismatch(
    identity: Dict[str, Any],
    sessions: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Reference distribution: session *i*'s answer boundary against *i+1*'s."""
    count = len(sessions)
    shift = np.roll(np.arange(count), -1)
    return {
        "label": "mismatch",
        "n": count,
        "note": "session i's answer boundary against session i+1's (unrelated sessions)",
        "h_cos_final": _distribution(_cos_rows(identity["h_final"][shift], identity["h_final"])),
        "read_cos_final": _distribution(
            _cos_rows(identity["read_final"][shift], identity["read_final"])
        ),
        "store_v_rel_final": (
            _distribution(_rel_rows(identity["store_v"][shift], identity["store_v"]))
            if identity["store_v"].shape[1]
            else None
        ),
    }


def _sensitivity(read_cos: np.ndarray) -> Dict[str, Any]:
    """How robust the 0.99 cut is: how many sessions sit below each cut."""
    below = {str(cut): int(np.sum(read_cos < cut)) for cut in READ_COS_CUTS}
    return {"n": int(len(read_cos)), "below_cut": below}


# --------------------------------------------------------------------------- #
# R1 / R2 / R4
# --------------------------------------------------------------------------- #
def compare_r1(summary: Dict[str, Any], report_full: Dict[str, Any]) -> Dict[str, Any]:
    mismatches = {
        key: {"probe": summary.get(key), "report": report_full.get(key)}
        for key in R1_KEYS
        if summary.get(key) != report_full.get(key)
    }
    return {"matches": not mismatches, "mismatches": mismatches}


def verify_edits(
    module: Any,
    sessions: Sequence[Dict[str, Any]],
    twins: Sequence[Dict[str, Any]],
    reorders: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """R2: each edit must change exactly the roster turn and move the answer as intended."""
    violations: List[str] = []
    for session, twin, reorder in zip(sessions, twins, reorders):
        roster_turn = int(session["session_meta"]["roster_turn"])
        culprit = session["ground_truth_oracle"]["culprit"]
        actors = list(session["environment"]["actors"])
        for label, edited in (("twin", twin), ("reorder", reorder)):
            if len(edited["turns"]) != len(session["turns"]):
                violations.append(f"{session['session_id']} {label}: turn count changed")
                continue
            changed = [
                index
                for index, (before, after) in enumerate(zip(session["turns"], edited["turns"]))
                if before["user_input"] != after["user_input"]
                or before.get("asserts") != after.get("asserts")
            ]
            if changed != [roster_turn]:
                violations.append(
                    f"{session['session_id']} {label}: changed turns {changed}, "
                    f"expected [{roster_turn}]"
                )
            derived = module.derive(module._all_asserts(edited), edited["environment"]["actors"])
            if label == "twin":
                if derived != [twin["ground_truth_oracle"]["culprit"]]:
                    violations.append(
                        f"{session['session_id']} twin: derive() {derived} is not the twin culprit"
                    )
                if twin["ground_truth_oracle"]["culprit"] == culprit:
                    violations.append(f"{session['session_id']} twin: the answer did not flip")
                if edited["environment"]["actors"] != actors:
                    violations.append(
                        f"{session['session_id']} twin: the roster membership changed"
                    )
            else:
                if derived != [culprit]:
                    violations.append(
                        f"{session['session_id']} reorder: derive() {derived} is not the culprit"
                    )
                if edited["ground_truth_oracle"]["culprit"] != culprit:
                    violations.append(f"{session['session_id']} reorder: the answer moved")
    return {"checked": len(sessions), "violations": violations}


# --------------------------------------------------------------------------- #
# the fork
# --------------------------------------------------------------------------- #
def branch(*, k: int, twin: Dict[str, Any], reorder: Dict[str, Any]) -> Dict[str, str]:
    """§66.9, mechanically: which branch the measured state differences select."""
    static = (
        twin["read_cos_final"]["median"] >= READ_COS_STATIC
        and reorder["read_cos_final"]["median"] >= READ_COS_STATIC
    )
    if static:
        written = (twin.get("store_v_rel_final") or {}).get("median", 0.0) >= STORE_WRITTEN
        if written:
            return {
                "id": "R3a-stored-not-read",
                "reading": (
                    "the roster edit changes the store's values at the answer boundary but the "
                    "read vector there is essentially unchanged (median cosine >= 0.99): the "
                    "roster is written and not addressed when the answer is produced"
                ),
                "next": (
                    "the query/read path - make the answer turn address the turn that carried the "
                    "roster (per-turn read or an explicit turn tag), not more training"
                ),
            }
        return {
            "id": "R3a-not-stored",
            "reading": (
                "neither the read vector nor the store's values move at the answer boundary "
                f"(store relative change < {STORE_WRITTEN}): the roster turn never reaches the "
                "carrier that the answer is read from"
            ),
            "next": (
                "the write path - the store's write gate/slot allocation for the roster turn, "
                "not more training"
            ),
        }
    if twin["moved_to_twin_target"] < FOLLOWS_MAPPING:
        return {
            "id": "R3b-head-ignores",
            "reading": (
                "the read vector moves with the roster (median cosine < 0.99) but the head's "
                f"choice follows the swapped mapping in fewer than {FOLLOWS_MAPPING:.0%} of "
                "sessions: the content is in the state and the output does not use it"
            ),
            "next": (
                "the readout - a roster-restricted selection head over the read vector, trained "
                "on the state, not more sessions, steps or width"
            ),
        }
    return {
        "id": "R3c-follows-but-wrong",
        "reading": (
            "the read vector moves and the head follows the swapped mapping in at least "
            f"{FOLLOWS_MAPPING:.0%} of sessions, yet held-out accuracy stays at or below chance: "
            "the selection is used but read in the wrong direction or with the wrong "
            "normalisation (a slot/order artefact, not a missing binding)"
        ),
        "next": (
            "audit the sign/order normalisation of the selection against the roster's own order "
            "before any further training"
        ),
    }


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #
def run(
    trainer: Any,
    report_path: Path,
    report: Dict[str, Any],
    *,
    device: str = "cpu",
    batch: int = PROBE_BATCH,
) -> Dict[str, Any]:
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§66 probes the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or 2)
    module = trainer._load_generator()
    corpus = trainer.load_corpus(
        minimal_binding=True,
        order_augmented=bool(corpus_block.get("minimal_order_augmented")),
        roster_size=k,
    )
    heldout = list(corpus["heldout"])
    names = sorted(module.ACTORS)
    indices = roster_indices(heldout, names)

    checkpoint = Path(str(report.get("checkpoint")))
    hash_before = checkpoint_sha256(checkpoint)
    started = time.time()
    core = rebuild_core(trainer, report, device=device)
    weights_before = str(core.weights_hash() or "")

    # R1: the production path, re-run unchanged.
    identity_records = trainer.evaluate(core, heldout, "full", module=module)
    identity_summary = trainer.summarise(identity_records)
    r1 = compare_r1(identity_summary, report.get("results", {}).get("full") or {})
    r1["identity_summary"] = identity_summary
    r1["report_full"] = report.get("results", {}).get("full") or {}

    # R2: the edits are surgical.
    twins = [module.minimal_twin(session) for session in heldout]
    reorders = [module.minimal_order_twin(session) for session in heldout]
    r2 = verify_edits(module, heldout, twins, reorders)

    # The three reads.
    identity = read_variant(trainer, core, heldout, names, batch=batch)
    twin_read = read_variant(trainer, core, twins, names, batch=batch)
    reorder_read = read_variant(trainer, core, reorders, names, batch=batch)

    twin_culprits = [session["ground_truth_oracle"]["culprit"] for session in twins]
    twin_names, _ = pick_all(twin_read["scores"], indices, names)
    identity_names, _ = pick_all(identity["scores"], indices, names)
    reorder_names, _ = pick_all(reorder_read["scores"], indices, names)

    twin = compare_variant(identity, twin_read, heldout, names, indices, label="twin")
    twin["moved_to_twin_target"] = _rate(
        [name == target for name, target in zip(twin_names, twin_culprits)]
    )
    twin["stayed_on_original"] = _rate(
        [
            name == session["ground_truth_oracle"]["culprit"]
            for name, session in zip(twin_names, heldout)
        ]
    )
    reorder = compare_variant(identity, reorder_read, heldout, names, indices, label="reorder")
    reorder["kept_original_target"] = _rate(
        [
            name == session["ground_truth_oracle"]["culprit"]
            for name, session in zip(reorder_names, heldout)
        ]
    )
    reorder["follows_reversed_last_entry"] = _rate(
        [
            name == session["environment"]["actors"][0]
            for name, session in zip(reorder_names, heldout)
        ]
    )
    identity_block = compare_variant(identity, identity, heldout, names, indices, label="identity")
    identity_block["accuracy_over_roster"] = _rate(
        [
            name == session["ground_truth_oracle"]["culprit"]
            for name, session in zip(identity_names, heldout)
        ]
    )
    identity_block["prediction_accuracy"] = _rate(
        [row["prediction"] == row["target"] for row in identity_records if row["target"]]
    )
    mismatch = summarise_mismatch(identity, heldout)

    # R1's second half: the probe's own roster argmax must reproduce the report's
    # `rank_actor` accuracy, or the probe is not reading the production readout.
    report_ranking = report.get("results", {}).get("full", {}).get("ranking_exact")
    identity_block["roster_argmax_matches_report"] = {
        "probe": identity_block["accuracy"],
        "report": report_ranking,
        "matches": identity_block["accuracy"] == report_ranking,
    }
    r1["roster_argmax_matches_report"] = identity_block["roster_argmax_matches_report"]
    r1["matches"] = bool(r1["matches"] and r1["roster_argmax_matches_report"]["matches"])

    fork = branch(k=k, twin=twin, reorder=reorder)
    elapsed = time.time() - started
    weights_after = str(core.weights_hash() or "")
    hash_after = checkpoint_sha256(checkpoint)
    instrument_ok = bool(r1["matches"] and not r2["violations"] and hash_after == hash_before)

    return {
        "probe": "§66 readout/state probe",
        "source_report": str(report_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "names": names,
        "r1_identity_reproduces_the_report": r1,
        "r2_edits_are_surgical": r2,
        "readout": {
            "identity": identity_block,
            "twin": twin,
            "reorder": reorder,
            "mismatch": mismatch,
            "sensitivity": {
                "twin_read_cos_final": _sensitivity(
                    _cos_rows(identity["read_final"], twin_read["read_final"])
                ),
                "reorder_read_cos_final": _sensitivity(
                    _cos_rows(identity["read_final"], reorder_read["read_final"])
                ),
            },
        },
        "fork": fork,
        "r4_cost": {
            "device": device,
            "sessions": len(heldout),
            "variants": 3,
            "seconds": round(elapsed, 2),
            "params": int((report.get("cost") or {}).get("params") or 0),
            "weights_hash_before": weights_before,
            "weights_hash_after": weights_after,
            "checkpoint_sha256_before": hash_before,
            "checkpoint_sha256_after": hash_after,
            "checkpoint_unchanged": hash_after == hash_before,
        },
        "instrument_ok": instrument_ok,
        "all_pass": instrument_ok,  # the fork is a finding, not a pass/fail
    }


# --------------------------------------------------------------------------- #
# mechanical re-check
# --------------------------------------------------------------------------- #
def check(path: Path) -> List[str]:
    """Re-derive §66's verdict from the stored numbers; no model needed."""
    data = json.loads(path.read_text(encoding="utf-8"))
    problems: List[str] = []

    r1 = data.get("r1_identity_reproduces_the_report") or {}
    summary = r1.get("identity_summary") or {}
    report_full = r1.get("report_full") or {}
    mismatches = {
        key: {"probe": summary.get(key), "report": report_full.get(key)}
        for key in R1_KEYS
        if summary.get(key) != report_full.get(key)
    }
    if mismatches:
        problems.append(f"R1 no longer matches the report: {mismatches}")
    if bool(r1.get("matches")) != (not mismatches):
        problems.append("R1.matches disagrees with its own stored summaries")

    cross = r1.get("roster_argmax_matches_report") or {}
    if cross.get("probe") != cross.get("report"):
        problems.append(
            "the probe's roster argmax no longer reproduces the report's ranking_exact: "
            f"{cross.get('probe')} vs {cross.get('report')}"
        )
    if cross.get("matches") is not True:
        problems.append("R1.roster_argmax_matches_report is not True")

    violations = (data.get("r2_edits_are_surgical") or {}).get("violations") or []
    if violations:
        problems.append(f"R2 violations recorded: {violations}")
    if not (data.get("r2_edits_are_surgical") or {}).get("checked"):
        problems.append("R2 recorded no checked sessions")

    cost = data.get("r4_cost") or {}
    if cost.get("weights_hash_before") != cost.get("weights_hash_after"):
        problems.append("R4 weights_hash changed; the probe wrote to the model")
    if cost.get("checkpoint_sha256_before") != cost.get("checkpoint_sha256_after"):
        problems.append("R4 checkpoint bytes changed")
    if cost.get("checkpoint_unchanged") is not True:
        problems.append("R4 checkpoint_unchanged is not True")

    readout = data.get("readout") or {}
    expected = branch(
        k=int(data.get("k") or 0),
        twin=readout.get("twin") or {},
        reorder=readout.get("reorder") or {},
    )
    stored = (data.get("fork") or {}).get("id")
    if expected["id"] != stored:
        problems.append(f"the fork is stale: stored {stored}, recomputed {expected['id']}")

    identity = readout.get("identity") or {}
    if identity.get("same_prediction") != 1.0:
        problems.append("the identity re-read disagrees with itself")
    if (data.get("readout") or {}).get("mismatch", {}).get("n") != cost.get("sessions"):
        problems.append("the mismatch reference covers a different session count")
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default="", help="a finished pantry-deduction report")
    parser.add_argument("--check", default="", help="re-derive a probe JSON's verdict")
    parser.add_argument("--device", default="cpu", help="cpu is the registered device")
    parser.add_argument("--batch", type=int, default=PROBE_BATCH)
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
    trainer = load_trainer()
    report = json.loads(path.read_text(encoding="utf-8"))
    outcome = run(trainer, path, report, device=args.device, batch=args.batch)

    print(f"report   : {path}")
    print(f"k        : {outcome['k']}  checkpoint {Path(outcome['checkpoint']).name}")
    print(
        f"R1       : {'OK' if outcome['r1_identity_reproduces_the_report']['matches'] else 'MISMATCH'}"
    )
    print(f"R2       : {len(outcome['r2_edits_are_surgical']['violations'])} violations")
    print()
    print(
        f"  {'variant':9s} {'read_cos(final)':>16s} {'store_v_rel':>12s} {'same_pred':>9s} {'flip':>7s}"
    )
    for label in ("twin", "reorder"):
        block = outcome["readout"][label]
        store = block.get("store_v_rel_final") or {}
        print(
            f"  {label:9s} {block['read_cos_final']['median']:16.4f} "
            f"{store.get('median', 0.0):12.4f} {block['same_prediction']:9.4f} "
            f"{block['argmax_flip_rate']:7.4f}"
        )
    print(f"  {'mismatch':9s} {outcome['readout']['mismatch']['read_cos_final']['median']:16.4f}")
    print()
    print(f"fork     : {outcome['fork']['id']}")
    print(f"reading  : {outcome['fork']['reading']}")
    print(f"next     : {outcome['fork']['next']}")
    print(f"cost     : {outcome['r4_cost']['seconds']}s on {outcome['r4_cost']['device']}")
    print(f"instrument_ok : {outcome['instrument_ok']}")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
        print(f"wrote    : {args.out}")
    return 0 if outcome["instrument_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
