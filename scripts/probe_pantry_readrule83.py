#!/usr/bin/env python3
# ANGELA-MATRIX: L6 [βγδ] [B] [L2]
"""§83: does retraining with the read at the evidence boundary make it address?

§82 separated the two sides: the stored keys carry the roster colour (0.7375), the
question-turn query does not (0.5450), and the zero-parameter move - the same
``W_q`` applied to the boundary state - still does not address (100/200 on
``model``, 101/200 on ``cosine_unit``). §82.20 registered the next step: **retrain
the projection with the read taken at the evidence boundary** and carried through
the answer decode.

This probe compares two arms on the same held-out 200 sessions:

* **control** - the frozen §77 carrier (``address="item"``, 168,150 parameters).
  Its boundary-query cell is §82's ``boundary_query`` column; it is re-extracted
  here and each read's masses are compared with §82's report (2e-9), so a drift in
  the instrument shows up before the treatment is read.
* **treatment** - the same architecture retrained from the same initialisation, on
  the same corpus, at the same budget (10,000 steps, 168,150 parameters) with
  ``--read-at boundary``. During training every answer decode carries the read
  taken at the boundary one turn earlier, so the scored cell *is* the computation
  that was trained. Same ``W_q``, same ``head``, same store: **zero new
  parameters**.

The scored cell is §81's two-way forced choice: of the two roster entries, does
the query put more attention on the one whose colour is the evidence colour? The
``model`` rule (the carrier's own softmax at its own learned temperature) is the
registered gate; ``cosine_unit`` is descriptive.

No-regression: §79's ``k``/``v`` -> colour cells are refitted on the treatment
carrier (train) and scored held-out, and §82's gate is applied to both.

Nothing here is a capability score. The core score stays **0.00/10** (§275).
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
PAIR79 = REPO_ROOT / "scripts" / "probe_pantry_pair79.py"
READRULE81 = REPO_ROOT / "scripts" / "probe_pantry_readrule81.py"
READRULE82 = REPO_ROOT / "scripts" / "probe_pantry_readrule82.py"

# §83.4, written before the scored run.
ALPHA = 0.005
NULL_DRAWS = 400
NULL_SEED = 20261125
FORCED_FLOOR = 0.5
ROSTER_ITEMS = 2
READ_BATCH = 32
REF_TOLERANCE = 2e-9
PROBE_STEPS = 2000
PROBE_BATCH = 64
PROBE_LR = 1e-3
PROBE_WEIGHT_DECAY = 1e-4
PROBE_SEED = 20261121
# §55's GENERAL_FIT_FLOOR / STORE_FLOOR: the treatment must fit the subset it was
# trained on before its held-out cell is read.
FIT_FLOOR = 0.90
CONTROL_STEPS = 10000
CONTROL_PARAMS = 168150
PRIMARY_RULE = "model"
RULES = ("model", "cosine_unit")
CONTROL_WINS = {"model": 100, "cosine_unit": 101}
BUDGET_KEYS = (
    "hidden",
    "emb",
    "core",
    "memory",
    "address",
    "write_strength",
    "write_slots",
    "aux_lambda",
    "aux_mode",
    "gate_prefix",
    "train_subset",
    "minimal_binding",
    "order_augmented",
    "roster_size",
    "seed",
    "epochs",
    "batch",
    "lr",
)
RULES_TEXT = {
    "model": "softmax(exp(scale) * k . q_b)  (the carrier's own read, on the boundary query)",
    "cosine_unit": "softmax((k/||k||) . (q_b/||q_b||))  (no norm race, no learned temperature)",
}
STAGE = "§83 does the read point, retrained at the same budget, make the read address?"
BRANCH_ORDER = (
    "E0-instrument",
    "T0-fit-fails",
    "T2-pass-but-regression",
    "T1-read-at-boundary-works",
    "T3-no-gain",
)
PREDICTION = "T1-read-at-boundary-works"
PREDICTION_ALTERNATIVE = "T3-no-gain"


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_pair79() -> Any:
    return _load("pantry_pair79_for83", PAIR79)


def load_readrule81() -> Any:
    return _load("pantry_readrule81_for83", READRULE81)


def load_readrule82() -> Any:
    return _load("pantry_readrule82_for83", READRULE82)


# --------------------------------------------------------------------------- #
# the control anchor: §82's per-read masses, reproduced
# --------------------------------------------------------------------------- #
def anchor_control(cells: Dict[str, Dict[str, Any]], anchor82: Dict[str, Any]) -> Dict[str, Any]:
    """Every control read must reproduce §82's masses and the registered wins.

    This is stricter than an audit: the masses are the projection, the store and
    the softmax together, so any drift in the extraction or in arithmetic moves
    them. A win count alone could coincide; a per-read 2e-9 match cannot.
    """
    stored = (anchor82.get("cells") or {}).get("boundary_query") or {}
    report: Dict[str, Any] = {}
    for variant in RULES:
        block = cells[variant]
        reference = stored.get(variant) or {}
        stored_m0 = [float(value) for value in reference.get("m0") or []]
        stored_m1 = [float(value) for value in reference.get("m1") or []]
        stored_items = [int(value) for value in reference.get("items") or []]
        n = int(block["n"])
        if not (len(stored_m0) == len(stored_m1) == len(stored_items) == n):
            raise SystemExit(
                f"§82's {variant} anchor has {len(stored_m0)} reads, this run has {n}; "
                "the anchor is not the same held-out set"
            )
        mismatch = 0
        worst = 0.0
        for ours, theirs in ((block["m0"], stored_m0), (block["m1"], stored_m1)):
            for left, right in zip(ours, theirs):
                worst = max(worst, abs(float(left) - float(right)))
                if abs(float(left) - float(right)) > REF_TOLERANCE:
                    mismatch += 1
        for ours, theirs in zip(block["items"], stored_items):
            if int(ours) != int(theirs):
                mismatch += 1
        wins = int(block["wins"])
        stored_wins = int(reference.get("wins", -1))
        report[variant] = {
            "reads": n,
            "stored_wins": stored_wins,
            "wins": wins,
            "registered_wins": CONTROL_WINS[variant],
            "stored_roster_mass_mean": float((reference.get("roster_mass") or {}).get("mean", -1)),
            "roster_mass_mean": float((block.get("roster_mass") or {}).get("mean", -1)),
            "max_abs_diff": worst,
            "mismatches": mismatch,
            "tolerance": REF_TOLERANCE,
            "reproduced": bool(wins == stored_wins == CONTROL_WINS[variant] and mismatch == 0),
        }
    report["pass"] = all(report[variant]["reproduced"] for variant in RULES)
    report["reading"] = (
        "the frozen §77 carrier re-extracted in this process reproduces §82's boundary-query "
        "cell read for read: 100/200 on model, 101/200 on cosine_unit, masses within 2e-9"
    )
    return report


# --------------------------------------------------------------------------- #
# gates and the branch
# --------------------------------------------------------------------------- #
def _fit_block(report: Dict[str, Any]) -> Dict[str, Any]:
    results = report.get("results") or {}
    fit = results.get("train_fit_subset") or results.get("train_fit") or {}
    exact = fit.get("exact")
    gates = report.get("gates") or {}
    if "G1_fits_the_subset" in gates and bool(gates["G1_fits_the_subset"]) != bool(
        exact is not None and float(exact) >= FIT_FLOOR
    ):
        raise SystemExit("the report's G1 and the registered fit floor disagree")
    return {
        "train_fit_subset_exact": exact,
        "train_fit_subset_n": fit.get("n"),
        "floor": FIT_FLOOR,
        "report_gate": gates.get("G1_fits_the_subset"),
        "pass": bool(exact is not None and float(exact) >= FIT_FLOOR),
        "reading": (
            "the treatment must fit the sessions it trained on before its held-out read is "
            "read; a miss says the arm did not learn at this budget, not that the read rule failed"
        ),
    }


def _cell_block(block: Dict[str, Any]) -> Dict[str, Any]:
    wilson = block.get("wilson") or {}
    return {
        "pass": bool(
            float(wilson.get("low", 0.0)) > FORCED_FLOOR and float(block["p_value"]) < ALPHA
        ),
        "wins": int(block["wins"]),
        "n": int(block["n"]),
        "forced": float(block["forced"]),
        "wilson_low": float(wilson.get("low", 0.0)),
        "wilson_high": float(wilson.get("high", 0.0)),
        "p_value": float(block["p_value"]),
        "roster_mass": float((block.get("roster_mass") or {}).get("mean", 0.0)),
        "argmax_on_roster": float(block.get("argmax_on_roster", 0.0)),
        "null_ge": int((block.get("null") or {}).get("ge", 0)),
        "chance": FORCED_FLOOR,
    }


def _entry_block(block: Dict[str, Any]) -> Dict[str, Any]:
    observed = block.get("observed") or {}
    wilson = observed.get("wilson") or {}
    return {
        "pass": bool(
            float(wilson.get("low", 0.0)) > FORCED_FLOOR and float(block["p_value"]) < ALPHA
        ),
        "wins": int(observed.get("forced_correct", -1)),
        "n": int(observed.get("n", 0)),
        "forced": float(observed.get("forced", -1.0)),
        "wilson_low": float(wilson.get("low", 0.0)),
        "p_value": float(block["p_value"]),
        "top1": float(observed.get("top1", 0.0)),
        "eight_way_chance": float((block.get("chance") or {}).get("top1", 0.0)),
        "null_ge": int((block.get("null") or {}).get("ge", 0)),
        "chance": FORCED_FLOOR,
    }


def gates(outcome: Dict[str, Any]) -> Dict[str, Any]:
    instrument = outcome["instrument"]
    anchor = instrument["control_anchor"]
    i0 = {
        "pass": bool(
            instrument["control_unchanged"]
            and instrument["control_checkpoint_unchanged"]
            and instrument["same_corpus"]
            and instrument["same_budget"]
            and instrument["same_start"]
            and instrument["treatment_is_the_read_rule"]
            and instrument["alignment"]["pass"]
            and anchor["pass"]
        ),
        "control_unchanged": instrument["control_unchanged"],
        "control_checkpoint_unchanged": instrument["control_checkpoint_unchanged"],
        "same_corpus": instrument["same_corpus"],
        "same_budget": instrument["same_budget"],
        "budget_differences": instrument["budget"]["differences"],
        "same_start": instrument["same_start"],
        "start_differences": instrument["start"]["differences"],
        "treatment_is_the_read_rule": instrument["treatment_is_the_read_rule"],
        "alignment_pass": instrument["alignment"]["pass"],
        "control_anchor_reproduced": anchor["pass"],
        "control_anchor_wins": {variant: anchor[variant]["wins"] for variant in RULES},
        "control_anchor_max_abs_diff": max(anchor[variant]["max_abs_diff"] for variant in RULES),
        "reading": (
            "the control is the frozen §77 carrier and reproduces §82's boundary-query cell read "
            "for read; the treatment is the same architecture, initialisation, corpus and budget "
            "with only the read point changed"
        ),
    }
    return {
        "I0_instrument": i0,
        "fit": outcome["fit"],
        "treatment": {variant: _cell_block(outcome["treatment"][variant]) for variant in RULES},
        "no_regression": {
            "entry_key": _entry_block(outcome["no_regression"]["entry_key"]),
            "entry_value": _entry_block(outcome["no_regression"]["entry_value"]),
            "pass": bool(
                _entry_block(outcome["no_regression"]["entry_key"])["pass"]
                and _entry_block(outcome["no_regression"]["entry_value"])["pass"]
            ),
        },
    }


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """Fixed precedence, written before the run: E0 > T0 > T2 > T1 > T3."""
    if not gate["I0_instrument"]["pass"]:
        return {
            "id": "E0-instrument",
            "reading": (
                "the control carrier, checkpoint, corpus or budget moved, or §82's boundary-query "
                "cell is not reproduced read for read; nothing is read"
            ),
            "next": "fix the instrument before asking whether the read point is learnable",
        }
    if not gate["fit"]["pass"]:
        return {
            "id": "T0-fit-fails",
            "reading": (
                "the treatment did not fit the training subset at this budget, so its held-out "
                "read is not a test of the read point"
            ),
            "next": (
                "re-run the same registered arm (do not change the read rule or the budget) and "
                "report why it did not fit before reading any cell"
            ),
        }
    primary = gate["treatment"][PRIMARY_RULE]
    if primary["pass"] and not gate["no_regression"]["pass"]:
        return {
            "id": "T2-pass-but-regression",
            "reading": (
                "the boundary read now addresses the roster entry the evidence colour needs, but "
                "§79's key/value-to-colour cells no longer pass: the retraining moved the write "
                "side, so the gain is not free"
            ),
            "next": (
                "register the write-side cells on this carrier and separate which of the two "
                "moved, at the same budget"
            ),
        }
    if primary["pass"]:
        return {
            "id": "T1-read-at-boundary-works",
            "reading": (
                "at the same budget, the same parameters and the same store, training the read "
                "at the evidence boundary makes that read address the roster entry the evidence "
                "colour needs, and §79's entry cells still pass: the question-turn read point was "
                "what the frozen carrier could not learn around, and the boundary read is "
                "learnable"
            ),
            "next": (
                "read the end-to-end answer cell on this carrier (§80's held-out answer exact) "
                "and, if it moves with the read, register the same read point on the next corpus "
                "seed before calling it a rule"
            ),
        }
    return {
        "id": "T3-no-gain",
        "reading": (
            "moved to the boundary and retrained at the same budget, the read still does not "
            "address the roster entry: the limit is not only where the query is taken, and the "
            "same store/head cannot be trained to use the boundary state at 10,000 steps"
        ),
        "next": (
            "register a change that gives the read a reason to separate the entries at the write "
            "point (the keys already carry the colour, §79) rather than moving the query again"
        ),
    }


# --------------------------------------------------------------------------- #
# one run
# --------------------------------------------------------------------------- #
def run(
    control_path: Path,
    treatment_path: Path,
    anchor82_path: Path,
    *,
    device: str = "cpu",
    draws: int = NULL_DRAWS,
) -> Dict[str, Any]:
    started = time.time()
    control_report = json.loads(control_path.read_text(encoding="utf-8"))
    treatment_report = json.loads(treatment_path.read_text(encoding="utf-8"))
    anchor82 = json.loads(anchor82_path.read_text(encoding="utf-8"))

    pair = load_pair79()
    rr81 = load_readrule81()
    rr82 = load_readrule82()
    if anchor82.get("stage") != rr82.STAGE:
        raise SystemExit("the control anchor is not a §82 report")

    control_config = control_report.get("config") or {}
    treatment_config = treatment_report.get("config") or {}
    corpus_block = control_report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§83 reads the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or 2)
    if k != ROSTER_ITEMS:
        raise SystemExit(f"§83 was registered at k={ROSTER_ITEMS}, this carrier has k={k}")
    seed = int(corpus_block.get("seed") or 0)
    if seed <= 0:
        raise SystemExit("the report does not record its corpus seed")

    contents = pair.load_contents()
    composition = pair.load_composition()
    split75 = pair.load_split75()
    boundaries = pair.load_boundaries()
    probe = pair.load_readout()
    selection = contents.load_selection()
    trainer = selection.load_trainer()
    module = trainer._load_generator()

    corpus = trainer.load_corpus(
        minimal_binding=True,
        order_augmented=bool(corpus_block.get("minimal_order_augmented")),
        roster_size=k,
        seed=seed,
    )
    train = list(corpus["train"])
    held = list(corpus["heldout"])
    names = sorted(module.ACTORS)
    colours = sorted(module.COLOURS)
    display = dict(module.COLOURS)

    # ---- control: the frozen §77 carrier, re-extracted read for read -------
    control_checkpoint = Path(str(control_report.get("checkpoint")))
    control_hash_before = probe.checkpoint_sha256(control_checkpoint)
    control_core = probe.rebuild_core(trainer, control_report, device=device)
    control_weights_before = str(control_core.weights_hash() or "")
    control_reads = rr82.read_records(
        trainer, probe, control_core, held, names, colours, pair, rr81, batch=READ_BATCH
    )
    torch = control_core._torch
    control_exp_scale = torch.exp(control_core.log_read_scale)
    control_records = [dict(row, query=row["query_boundary"]) for row in control_reads]
    control_cells = {
        variant: rr81.address_block(
            torch, split75, composition, control_records, control_exp_scale, variant, draws=draws
        )
        for variant in RULES
    }
    control_anchor = anchor_control(control_cells, anchor82)

    # ---- treatment: same architecture/budget, only the read point changed --
    treatment_checkpoint = Path(str(treatment_report.get("checkpoint")))
    treatment_hash_before = probe.checkpoint_sha256(treatment_checkpoint)
    treatment_core = probe.rebuild_core(trainer, treatment_report, device=device)
    treatment_weights_before = str(treatment_core.weights_hash() or "")
    treatment_reads = rr82.read_records(
        trainer, probe, treatment_core, held, names, colours, pair, rr81, batch=READ_BATCH
    )
    treatment_torch = treatment_core._torch
    treatment_exp_scale = treatment_torch.exp(treatment_core.log_read_scale)
    treatment_records = [dict(row, query=row["query_boundary"]) for row in treatment_reads]
    treatment_cells = {
        variant: rr81.address_block(
            treatment_torch,
            split75,
            composition,
            treatment_records,
            treatment_exp_scale,
            variant,
            draws=draws,
        )
        for variant in RULES
    }

    # ---- no-regression: §79's entry cells, refitted on the treatment -------
    train_entries = pair.entry_records(trainer, probe, treatment_core, train, names, colours)
    held_entries = pair.entry_records(trainer, probe, treatment_core, held, names, colours)
    entry_key = rr82.probe_block(
        treatment_torch,
        pair,
        boundaries,
        composition,
        split75,
        _stack(treatment_torch, train_entries, "k"),
        _labels(treatment_torch, train_entries, "colour"),
        _stack(treatment_torch, held_entries, "k"),
        _labels(treatment_torch, held_entries, "colour"),
        _labels(treatment_torch, held_entries, "partner_colour"),
        len(colours),
        draws=draws,
    )
    entry_value = rr82.probe_block(
        treatment_torch,
        pair,
        boundaries,
        composition,
        split75,
        _stack(treatment_torch, train_entries, "v"),
        _labels(treatment_torch, train_entries, "colour"),
        _stack(treatment_torch, held_entries, "v"),
        _labels(treatment_torch, held_entries, "colour"),
        _labels(treatment_torch, held_entries, "partner_colour"),
        len(colours),
        draws=draws,
    )

    # ---- instrument -------------------------------------------------------
    control_read_at = str(control_config.get("read_at") or "token")
    treatment_read_at = str(treatment_config.get("read_at") or "token")
    budget_differences = [
        key for key in BUDGET_KEYS if control_config.get(key) != treatment_config.get(key)
    ]
    same_corpus = bool(
        (control_report.get("corpus") or {}).get("train_digest")
        == (treatment_report.get("corpus") or {}).get("train_digest")
        and (control_report.get("corpus") or {}).get("heldout_digest")
        == (treatment_report.get("corpus") or {}).get("heldout_digest")
        and (corpus.get("meta") or {}).get("train_digest") == corpus_block.get("train_digest")
        and (corpus.get("meta") or {}).get("heldout_digest") == corpus_block.get("heldout_digest")
    )
    same_budget = bool(
        not budget_differences
        and int(control_report.get("params") or 0) == CONTROL_PARAMS
        and int(treatment_report.get("params") or 0) == CONTROL_PARAMS
        and int((control_report.get("training") or {}).get("steps") or 0) == CONTROL_STEPS
        and int((treatment_report.get("training") or {}).get("steps") or 0) == CONTROL_STEPS
    )
    control_start = control_report.get("start") or {}
    treatment_start = treatment_report.get("start") or {}
    start_keys = ("checkpoint", "weights_hash", "init_weights_hash", "params")
    start_differences = [
        key for key in start_keys if control_start.get(key) != treatment_start.get(key)
    ]
    same_start = bool(not start_differences and control_start.get("params") == CONTROL_PARAMS)
    treatment_is_read_rule = bool(control_read_at == "token" and treatment_read_at == "boundary")
    instrument = {
        "control": str(control_path),
        "treatment": str(treatment_path),
        "control_checkpoint": str(control_checkpoint),
        "treatment_checkpoint": str(treatment_checkpoint),
        "device": device,
        "read_at": {"control": control_read_at, "treatment": treatment_read_at},
        "registered_read_at": {"control": "token", "treatment": "boundary"},
        "treatment_is_the_read_rule": treatment_is_read_rule,
        "budget": {
            "keys": list(BUDGET_KEYS),
            "differences": budget_differences,
            "params": {
                "control": int(control_report.get("params") or 0),
                "treatment": int(treatment_report.get("params") or 0),
                "registered": CONTROL_PARAMS,
            },
            "steps": {
                "control": int((control_report.get("training") or {}).get("steps") or 0),
                "treatment": int((treatment_report.get("training") or {}).get("steps") or 0),
                "registered": CONTROL_STEPS,
            },
        },
        "same_budget": same_budget,
        "start": {
            "keys": list(start_keys),
            "differences": start_differences,
            "control": {key: control_start.get(key) for key in start_keys},
            "treatment": {key: treatment_start.get(key) for key in start_keys},
        },
        "same_start": same_start,
        "corpus": {
            "seed": seed,
            "control_train_digest": (control_report.get("corpus") or {}).get("train_digest"),
            "treatment_train_digest": (treatment_report.get("corpus") or {}).get("train_digest"),
            "control_heldout_digest": (control_report.get("corpus") or {}).get("heldout_digest"),
            "treatment_heldout_digest": (treatment_report.get("corpus") or {}).get(
                "heldout_digest"
            ),
        },
        "same_corpus": same_corpus,
        "control_weights_hash_before": control_weights_before,
        "control_weights_hash_after": str(control_core.weights_hash() or ""),
        "control_unchanged": str(control_core.weights_hash() or "") == control_weights_before,
        "control_checkpoint_sha256_before": control_hash_before,
        "control_checkpoint_sha256_after": probe.checkpoint_sha256(control_checkpoint),
        "control_checkpoint_unchanged": control_hash_before
        == probe.checkpoint_sha256(control_checkpoint),
        "treatment_weights_hash_before": treatment_weights_before,
        "treatment_weights_hash_after": str(treatment_core.weights_hash() or ""),
        "treatment_unchanged": str(treatment_core.weights_hash() or "") == treatment_weights_before,
        "treatment_checkpoint_sha256_before": treatment_hash_before,
        "treatment_checkpoint_sha256_after": probe.checkpoint_sha256(treatment_checkpoint),
        "treatment_checkpoint_unchanged": treatment_hash_before
        == probe.checkpoint_sha256(treatment_checkpoint),
        "alignment": {
            "train": pair.alignment(display, train),
            "heldout": pair.alignment(display, held),
        },
        "control_anchor": control_anchor,
    }
    instrument["alignment"]["pass"] = bool(
        instrument["alignment"]["train"]["pass"] and instrument["alignment"]["heldout"]["pass"]
    )

    outcome: Dict[str, Any] = {
        "stage": STAGE,
        "control_report": str(control_path),
        "treatment_report": str(treatment_path),
        "anchor82_report": str(anchor82_path),
        "k": k,
        "corpus_seed": seed,
        "corpus": {
            "train_digest": corpus_block.get("train_digest"),
            "heldout_digest": corpus_block.get("heldout_digest"),
            "train_sessions": len(train),
            "heldout_sessions": len(held),
            "roster_items": ROSTER_ITEMS,
            "names": len(names),
            "colours": len(colours),
            "train_twins": sum(
                1 for record in train if record.get("session_meta", {}).get("order_augmented_of")
            ),
            "heldout_twins": sum(
                1 for record in held if record.get("session_meta", {}).get("order_augmented_of")
            ),
        },
        "probe": {
            "steps": PROBE_STEPS,
            "batch": PROBE_BATCH,
            "lr": PROBE_LR,
            "weight_decay": PROBE_WEIGHT_DECAY,
            "seed": PROBE_SEED,
            "null_draws": draws,
            "null_seed": NULL_SEED,
            "alpha": ALPHA,
            "forced_floor": FORCED_FLOOR,
            "fit_split": "train",
            "scored_split": "heldout",
            "gate_metric": (
                "within-session two-way forced choice: the roster entry the evidence colour "
                "needs vs the other entry"
            ),
        },
        "reads": {
            "control": "the frozen §77 carrier's W_q on the boundary hidden state",
            "treatment": (
                "the retrained carrier's W_q on the boundary hidden state; that is the read its "
                "answer decode actually used during training (--read-at boundary)"
            ),
            "rules": {variant: RULES_TEXT[variant] for variant in RULES},
            "fitted_parameters": 0,
            "null": "label permutation without refitting (§80/§81 convention)",
        },
        "fit": _fit_block(treatment_report),
        "control": {variant: control_cells[variant] for variant in RULES},
        "treatment": {variant: treatment_cells[variant] for variant in RULES},
        "no_regression": {"entry_key": entry_key, "entry_value": entry_value},
        "prediction": {
            "registered": PREDICTION,
            "alternative": PREDICTION_ALTERNATIVE,
            "confidence": "low",
            "reason": (
                "§82 removed the zero-parameter move (the frozen boundary query is 100/200) and "
                "put the colour in the keys (0.7375) and in the boundary state (§69's 0.8900), so "
                "the main loss now depends directly on this read selecting the right entry - a "
                "gradient the frozen carrier never had; T3 is live because the same budget left "
                "the frozen read at chance"
            ),
        },
        "decision": {
            "alpha": ALPHA,
            "forced_floor": FORCED_FLOOR,
            "null_draws": draws,
            "null_seed": NULL_SEED,
            "anchor_tolerance": REF_TOLERANCE,
            "primary_rule": PRIMARY_RULE,
            "control_wins": dict(CONTROL_WINS),
            "fit_floor": FIT_FLOOR,
            "control_steps": CONTROL_STEPS,
            "control_params": CONTROL_PARAMS,
        },
        "instrument": instrument,
    }
    outcome["gates"] = gates(outcome)
    outcome["branch"] = branch(outcome["gates"])
    outcome["prediction_hit"] = bool(outcome["branch"]["id"] == PREDICTION)
    outcome["instrument_ok"] = bool(outcome["gates"]["I0_instrument"]["pass"])
    outcome["seconds"] = round(time.time() - started, 3)
    return outcome


def _stack(torch: Any, records: Sequence[Dict[str, Any]], field: str) -> Any:
    return torch.stack([row[field] for row in records]).float()


def _labels(torch: Any, records: Sequence[Dict[str, Any]], field: str) -> Any:
    return torch.as_tensor([int(row[field]) for row in records], dtype=torch.long)


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def check(path: Path) -> List[str]:
    """Re-derive every gate and the branch from the stored readings."""
    problems: List[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("stage") != STAGE:
        return ["this is not a §83 report"]
    decision = data.get("decision") or {}
    for name, expected in (
        ("alpha", ALPHA),
        ("forced_floor", FORCED_FLOOR),
        ("null_draws", NULL_DRAWS),
        ("null_seed", NULL_SEED),
        ("anchor_tolerance", REF_TOLERANCE),
        ("primary_rule", PRIMARY_RULE),
        ("fit_floor", FIT_FLOOR),
        ("control_steps", CONTROL_STEPS),
        ("control_params", CONTROL_PARAMS),
    ):
        if decision.get(name) != expected:
            problems.append(f"decision.{name} is not the registered {expected!r}")
    if decision.get("control_wins") != CONTROL_WINS:
        problems.append("decision.control_wins is not the registered control anchor")

    split75 = load_read75()
    for name in ("control", "treatment"):
        cells = data.get(name) or {}
        for variant in RULES:
            block = cells.get(variant) or {}
            n = int(block.get("n") or 0)
            m0 = block.get("m0") or []
            m1 = block.get("m1") or []
            items = block.get("items") or []
            if not (len(m0) == len(m1) == len(items) == n) or n <= 0:
                problems.append(f"{name}[{variant}]: the masses are not one pair per read")
                continue
            wins = 0
            for left, right, item in zip(m0, m1, items):
                correct, partner = (left, right) if int(item) == 0 else (right, left)
                wins += int(float(correct) > float(partner))
            if wins != int(block.get("wins") or -1):
                problems.append(f"{name}[{variant}]: the win count is not re-derivable")
            if abs(float(block.get("forced", -1.0)) - round(wins / n, 6)) > 1e-9:
                problems.append(f"{name}[{variant}]: the forced rate is not wins/n")
            if split75.wilson(wins, n)["low"] != float((block.get("wilson") or {}).get("low")):
                problems.append(f"{name}[{variant}]: the Wilson bound is not re-derivable")
            null = block.get("null") or {}
            expected_p = round(
                (1 + int(null.get("ge") or 0)) / (int(null.get("draws") or 0) + 1), 6
            )
            if abs(float(block.get("p_value", -1.0)) - expected_p) > 1e-9:
                problems.append(f"{name}[{variant}]: p_value is not the permutation convention")

    for name in ("entry_key", "entry_value"):
        block = (data.get("no_regression") or {}).get(name) or {}
        observed = block.get("observed") or {}
        n = int(observed.get("n") or 0)
        if n <= 0:
            problems.append(f"no_regression.{name}: no observed reads")
            continue
        wins = int(observed.get("forced_correct") or 0)
        if abs(float(observed.get("forced", -1.0)) - round(wins / n, 6)) > 1e-9:
            problems.append(f"no_regression.{name}: the forced rate is not wins/n")
        null = block.get("null") or {}
        expected_p = round((1 + int(null.get("ge") or 0)) / (int(null.get("draws") or 0) + 1), 6)
        if abs(float(block.get("p_value", -1.0)) - expected_p) > 1e-9:
            problems.append(f"no_regression.{name}: p_value is not the permutation convention")

    anchor = (data.get("instrument") or {}).get("control_anchor") or {}
    if not anchor.get("pass"):
        problems.append("§82's boundary-query cell is not reproduced")
    for variant in RULES:
        block = anchor.get(variant) or {}
        if int(block.get("mismatches", 1)) != 0:
            problems.append(f"§82's {variant} masses disagree")
        if float(block.get("max_abs_diff", 1.0)) > REF_TOLERANCE:
            problems.append(f"§82's {variant} masses exceed the tolerance")
        if int(block.get("wins", -1)) != CONTROL_WINS[variant]:
            problems.append(f"§82's {variant} win count is not reproduced")

    fit = data.get("fit") or {}
    exact = fit.get("train_fit_subset_exact")
    if bool(fit.get("pass")) != bool(exact is not None and float(exact) >= FIT_FLOOR):
        problems.append("the fit gate does not re-derive")

    recomputed = gates(data)
    stored = data.get("gates") or {}
    if bool((stored.get("I0_instrument") or {}).get("pass")) != bool(
        recomputed["I0_instrument"]["pass"]
    ):
        problems.append("gate I0_instrument does not re-derive")
    if bool((stored.get("fit") or {}).get("pass")) != bool(recomputed["fit"]["pass"]):
        problems.append("gate fit does not re-derive")
    for variant in RULES:
        stored_cell = (stored.get("treatment") or {}).get(variant) or {}
        if bool(stored_cell.get("pass")) != bool(recomputed["treatment"][variant]["pass"]):
            problems.append(f"treatment[{variant}] does not re-derive")
    for name in ("entry_key", "entry_value"):
        stored_cell = (stored.get("no_regression") or {}).get(name) or {}
        if bool(stored_cell.get("pass")) != bool(recomputed["no_regression"][name]["pass"]):
            problems.append(f"no_regression.{name} does not re-derive")
    if bool((stored.get("no_regression") or {}).get("pass")) != bool(
        recomputed["no_regression"]["pass"]
    ):
        problems.append("no_regression does not re-derive")

    expected_branch = branch(recomputed)
    stored_branch = data.get("branch") or {}
    if stored_branch.get("id") != expected_branch["id"]:
        problems.append("the branch does not re-derive from the gates")
    if stored_branch.get("id") not in BRANCH_ORDER:
        problems.append("the branch is not one of the registered five")
    if bool(data.get("prediction_hit")) != bool(stored_branch.get("id") == PREDICTION):
        problems.append("prediction_hit does not re-derive from the branch")
    return problems


def load_read75() -> Any:
    """§75 owns the Wilson helper; loading it keeps the re-check on one definition."""
    path = REPO_ROOT / "scripts" / "probe_pantry_split75.py"
    spec = importlib.util.spec_from_file_location("pantry_split75_for83", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["pantry_split75_for83"] = module
    spec.loader.exec_module(module)
    return module


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="§83: retrain the read at the evidence boundary")
    parser.add_argument(
        "--control",
        type=Path,
        default=REPO_ROOT / "data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json",
    )
    parser.add_argument(
        "--treatment",
        type=Path,
        default=None,
        help="the --read-at boundary report under data/pantry_stage/readrule83/treatment/",
    )
    parser.add_argument(
        "--anchor82",
        type=Path,
        default=REPO_ROOT / "data/pantry_stage/readrule82/k2.json",
    )
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--null-draws", type=int, default=NULL_DRAWS)
    parser.add_argument("--check", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.check is not None:
        problems = check(args.check)
        if problems:
            print("§83 check FAIL")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print("§83 check OK")
        return 0

    if args.treatment is None:
        candidates = sorted((REPO_ROOT / "data/pantry_stage/readrule83/treatment").glob("*.json"))
        if not candidates:
            print("§83 needs a --read-at boundary report; none is staged yet")
            return 1
        args.treatment = candidates[-1]

    outcome = run(
        args.control,
        args.treatment,
        args.anchor82,
        device=args.device,
        draws=int(args.null_draws),
    )
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(outcome, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.json or args.out is None:
        print(json.dumps(outcome, indent=1, ensure_ascii=False, sort_keys=True))
    else:
        print(f"branch: {outcome['branch']['id']}")
        print(f"seconds: {outcome['seconds']}")
        print(f"report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
