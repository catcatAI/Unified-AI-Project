#!/usr/bin/env python3
# ANGELA-MATRIX: L6 [βγδ] [B] [L2]
"""§84: does a read taken at the question boundary, and held, fit and address?

§83 retrained the read at the **evidence** boundary (one turn before the
question) and held it for the whole answer decode. The arm did not fit the
subset it trained on (``train_fit_subset`` 0.8325 < 0.90), so the held-out cell
was not a test of the read point (§83.16-§83.17). §83.19 separated the two
things that arm changed at once:

1. the read is **one fixed vector** for the whole decode, and
2. that vector is taken **before the question turn's write** exists.

§84 changes only the second: ``--read-at question`` takes the read at the
decode's **own** boundary (``snapshots[q]``, whose store already contains the
question turn's write) and holds it. Same ``W_q``, same ``head``, same store,
same budget - **zero new parameters**.

What this probe reads, on the same held-out 200 sessions:

* **control** - the frozen §77 carrier's read at the question boundary. This
  cell was not scored before: §80/§81 read the store *before* the question
  turn. It is reported as a descriptive baseline, not an anchored cell.
* **treatment** - the retrained carrier's read at the question boundary; that
  is the computation its answer decode used during training.
* the scored cell is §81's within-session two-way forced choice, ``model`` is
  the gate, ``cosine_unit`` descriptive.

Instrument: §82's ``boundary_query`` cell is re-extracted and anchored read for
read at 2e-9, exactly as §83 did, so a drift in the carrier, arithmetic or
extraction shows up before the treatment is read. In addition the **query
vectors** of the question read must equal §82's question-turn query read for
read: only the store changed, not the projection input.

No-regression: §79's ``k``/``v`` -> colour cells are refitted on the treatment
carrier and §82's gate applies.

Nothing here is a capability score. The core score stays **0.00/10** (§275).
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
PAIR79 = REPO_ROOT / "scripts" / "probe_pantry_pair79.py"
READRULE81 = REPO_ROOT / "scripts" / "probe_pantry_readrule81.py"
READRULE82 = REPO_ROOT / "scripts" / "probe_pantry_readrule82.py"
READRULE83 = REPO_ROOT / "scripts" / "probe_pantry_readrule83.py"

# §84.4, written before the scored run. Everything that is not the read point is
# §83's registered value, so the two treatment arms differ only in --read-at.
ALPHA = 0.005
NULL_DRAWS = 400
NULL_SEED = 20261125
FORCED_FLOOR = 0.5
ROSTER_ITEMS = 2
READ_BATCH = 32
REF_TOLERANCE = 2e-9
FIT_FLOOR = 0.90
CONTROL_STEPS = 10000
CONTROL_PARAMS = 168150
PRIMARY_RULE = "model"
RULES = ("model", "cosine_unit")
# §82's boundary_query anchor (the instrument, not the scored cell).
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
    "model": "softmax(exp(scale) * k . q)  (the carrier's own read, at the question boundary)",
    "cosine_unit": "softmax((k/||k||) . (q/||q||))  (no norm race, no learned temperature)",
}
STAGE = "§84 does a read taken at the question boundary, and held, fit and address?"
BRANCH_ORDER = (
    "E0-instrument",
    "Q0-fit-fails",
    "Q2-pass-but-regression",
    "Q1-read-at-question-works",
    "Q3-fits-but-no-gain",
)
PREDICTION = "Q3-fits-but-no-gain"
PREDICTION_ALTERNATIVE = "Q0-fit-fails"


# --------------------------------------------------------------------------- #
# the modules this probe reuses
# --------------------------------------------------------------------------- #
def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_pair79() -> Any:
    return _load("pantry_pair79_for84", PAIR79)


def load_readrule81() -> Any:
    return _load("pantry_readrule81_for84", READRULE81)


def load_readrule82() -> Any:
    return _load("pantry_readrule82_for84", READRULE82)


def load_readrule83() -> Any:
    return _load("pantry_readrule83_for84", READRULE83)


# --------------------------------------------------------------------------- #
# the read: the store *after* the question turn's write, that boundary's h
# --------------------------------------------------------------------------- #
def question_records(
    trainer: Any,
    probe: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    names: Sequence[str],
    colours: Sequence[str],
    pair: Any,
    rr81: Any,
    *,
    batch: int = READ_BATCH,
) -> List[Dict[str, Any]]:
    """One record per session: the store at ``snapshots[q]`` and that boundary's query.

    This is §80/§81's extraction moved one boundary later: §81 reads
    ``snapshots[q-1]`` and replays the question turn, which is the store *before*
    the question's write. §84's arm reads ``snapshots[q]`` - the state after
    ``end_turn`` wrote the question turn - with ``W_q`` of that same boundary's
    ``h``. Same keys, same values, same query projection; only the write the read
    sees is different.
    """
    torch = core._torch
    name_index = {name: i for i, name in enumerate(names)}
    colour_index = {colour: i for i, colour in enumerate(colours)}
    records: List[Dict[str, Any]] = []
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
                q = len(turns[index]) - 1
                evidence = int(session["session_meta"]["evidence_turn"])
                if evidence != q - 1:
                    raise SystemExit(
                        f"{session['session_id']}: evidence turn {evidence} is not the turn "
                        f"before the question ({q - 1}); the read point is not the registered one"
                    )
                pairs = pair.roster_mapping(session)
                if len(pairs) != ROSTER_ITEMS:
                    raise SystemExit(
                        f"{session['session_id']}: {len(pairs)} roster items, "
                        f"registered {ROSTER_ITEMS}"
                    )
                keys = [str(key) for key, _ in pairs]
                seen = rr81.mod_seen_value(session)
                if keys.count(seen) != 1:
                    raise SystemExit(f"{session['session_id']}: {seen} is not one roster colour")
                item = keys.index(seen)
                # The query is §82's computation unchanged: replay the question
                # turn from the boundary before it and take its last token. The
                # store is the *later* snapshot, i.e. after that turn's write.
                before = snapshots[q - 1]
                state = core.init_state(len(chunk))
                state.tensors = {name: value for name, value in before.items()}
                delta = torch.as_tensor(
                    [gap[q] for gap in gaps],
                    dtype=before["h"].dtype,
                    device=before["h"].device,
                )
                hidden = core.al_step(delta, state).tensors["h"][index : index + 1]
                stacked = pair._replay_turn(trainer, core, turns[index][q], hidden)
                h_final = stacked[-1].reshape(-1)
                after = snapshots[q]
                store_keys = after["k"][index].detach().clone()
                store_values = after["v"][index].detach().clone()
                query = core.query_proj(h_final.reshape(1, -1)).reshape(-1).detach().clone()
                slots = rr81.mod_roster_slots(
                    trainer,
                    turns[index],
                    int(session["session_meta"]["roster_turn"]),
                    int(core.slots),
                )
                records.append(
                    {
                        "session_id": session["session_id"],
                        "structure": str(
                            session["session_meta"].get("order_augmented_of")
                            or session["session_id"]
                        ),
                        "twin": bool(session["session_meta"].get("order_augmented_of")),
                        "item": int(item),
                        "slots": [int(slot) for slot in slots],
                        "keys": store_keys,
                        "values": store_values,
                        "query": query,
                        "h": h_final.detach().clone(),
                        "v_roster": torch.stack([store_values[slot].reshape(-1) for slot in slots])
                        .detach()
                        .clone(),
                        "key_norms": [round(float(store_keys[slot].norm()), 6) for slot in slots],
                        "query_norm": round(float(query.norm()), 6),
                        "name": name_index[str(pairs[item][1])],
                        "partner_name": name_index[str(pairs[1 - item][1])],
                        "colour": colour_index[str(pairs[item][0])],
                        "partner_colour": colour_index[str(pairs[1 - item][0])],
                        "evidence_colour": colour_index[seen],
                    }
                )
    return records


def query_identity(
    token_records: Sequence[Dict[str, Any]],
    question_records: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """The question read must use the same query vectors as §82's question cell.

    If the projection input moved, the arm would be changing two things (the
    store *and* the query); this says it did not.
    """
    by_id = {str(row["session_id"]): row for row in question_records}
    compared = 0
    mismatches = 0
    worst = 0.0
    for row in token_records:
        other = by_id.get(str(row["session_id"]))
        if other is None:
            mismatches += 1
            continue
        compared += 1
        left = row["query"].detach().cpu()
        right = other["query"].detach().cpu()
        worst = max(worst, float((left - right).abs().max()))
        if not bool((left == right).all()):
            mismatches += 1
    return {
        "compared": compared,
        "mismatches": mismatches,
        "max_abs_diff": worst,
        "tolerance": REF_TOLERANCE,
        "pass": bool(compared == len(question_records) and mismatches == 0),
        "reading": (
            "the question-boundary read uses §82's question-turn query vectors unchanged: only "
            "the store the read addresses moved"
        ),
    }


def _stack(torch: Any, records: Sequence[Dict[str, Any]], field: str) -> Any:
    return torch.stack([row[field] for row in records]).float()


def _labels(torch: Any, records: Sequence[Dict[str, Any]], field: str) -> Any:
    return torch.as_tensor([int(row[field]) for row in records], dtype=torch.long)


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
    rr83 = load_readrule83()
    if anchor82.get("stage") != rr82.STAGE:
        raise SystemExit("the control anchor is not a §82 report")

    control_config = control_report.get("config") or {}
    treatment_config = treatment_report.get("config") or {}
    corpus_block = control_report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§84 reads the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or 2)
    if k != ROSTER_ITEMS:
        raise SystemExit(f"§84 was registered at k={ROSTER_ITEMS}, this carrier has k={k}")
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

    def cells_for(core: Any, reads: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        torch = core._torch
        exp_scale = torch.exp(core.log_read_scale)
        return {
            variant: rr81.address_block(
                torch, split75, composition, reads, exp_scale, variant, draws=draws
            )
            for variant in RULES
        }

    # ---- control: the frozen §77 carrier, two extractions ------------------
    control_checkpoint = Path(str(control_report.get("checkpoint")))
    control_hash_before = probe.checkpoint_sha256(control_checkpoint)
    control_core = probe.rebuild_core(trainer, control_report, device=device)
    control_weights_before = str(control_core.weights_hash() or "")
    control_anchor_reads = rr82.read_records(
        trainer, probe, control_core, held, names, colours, pair, rr81, batch=READ_BATCH
    )
    control_boundary_cells = cells_for(
        control_core, [dict(row, query=row["query_boundary"]) for row in control_anchor_reads]
    )
    control_anchor = rr83.anchor_control(control_boundary_cells, anchor82)

    control_question_reads = question_records(
        trainer, probe, control_core, held, names, colours, pair, rr81, batch=READ_BATCH
    )
    control_query_identity = query_identity(control_anchor_reads, control_question_reads)
    control_cells = cells_for(control_core, control_question_reads)

    # ---- treatment: same architecture/budget, only the read point changed --
    treatment_checkpoint = Path(str(treatment_report.get("checkpoint")))
    treatment_hash_before = probe.checkpoint_sha256(treatment_checkpoint)
    treatment_core = probe.rebuild_core(trainer, treatment_report, device=device)
    treatment_weights_before = str(treatment_core.weights_hash() or "")
    treatment_question_reads = question_records(
        trainer, probe, treatment_core, held, names, colours, pair, rr81, batch=READ_BATCH
    )
    treatment_cells = cells_for(treatment_core, treatment_question_reads)

    # ---- no-regression: §79's entry cells, refitted on the treatment -------
    treatment_torch = treatment_core._torch
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
    treatment_is_read_rule = bool(control_read_at == "token" and treatment_read_at == "question")
    instrument = {
        "control": str(control_path),
        "treatment": str(treatment_path),
        "control_checkpoint": str(control_checkpoint),
        "treatment_checkpoint": str(treatment_checkpoint),
        "device": device,
        "read_at": {"control": control_read_at, "treatment": treatment_read_at},
        "registered_read_at": {"control": "token", "treatment": "question"},
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
        "query_identity": control_query_identity,
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
            "control": (
                "the frozen §77 carrier's W_q of the question-boundary h, over the store at that "
                "boundary (the question turn's write included); descriptive, not anchored"
            ),
            "treatment": (
                "the retrained carrier's same read; that is the computation its answer decode "
                "actually used during training (--read-at question)"
            ),
            "rules": {variant: RULES_TEXT[variant] for variant in RULES},
            "fitted_parameters": 0,
            "null": "label permutation without refitting (§80/§81 convention)",
            "store": "snapshots[q], after end_turn wrote the question turn",
        },
        "fit": rr83._fit_block(treatment_report),
        "control": {variant: control_cells[variant] for variant in RULES},
        "treatment": {variant: treatment_cells[variant] for variant in RULES},
        "no_regression": {"entry_key": entry_key, "entry_value": entry_value},
        "prediction": {
            "registered": PREDICTION,
            "alternative": PREDICTION_ALTERNATIVE,
            "confidence": "low",
            "reason": (
                "§83.19's hypothesis is that the fit floor came from *both* a fixed read and its "
                "position before the question write; adding the question write to the store is "
                "the one thing §84 changes, so a fit is the prediction, but §82 measured this "
                "query's trace at only 0.5450 and a fixed vector can still be too little to "
                "address the entry, so Q0 stays live"
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


# --------------------------------------------------------------------------- #
# gates and the branch
# --------------------------------------------------------------------------- #
def gates(outcome: Dict[str, Any]) -> Dict[str, Any]:
    rr83 = load_readrule83()
    instrument = outcome["instrument"]
    anchor = instrument["control_anchor"]
    identity = instrument["query_identity"]
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
            and identity["pass"]
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
        "query_identity_pass": identity["pass"],
        "query_identity_max_abs_diff": identity["max_abs_diff"],
        "reading": (
            "the control is the frozen §77 carrier and reproduces §82's boundary-query cell read "
            "for read; the treatment is the same architecture, initialisation, corpus and budget "
            "with only the read point changed, and its query vectors are §82's unchanged"
        ),
    }
    return {
        "I0_instrument": i0,
        "fit": outcome["fit"],
        "treatment": {
            variant: rr83._cell_block(outcome["treatment"][variant]) for variant in RULES
        },
        "no_regression": {
            "entry_key": rr83._entry_block(outcome["no_regression"]["entry_key"]),
            "entry_value": rr83._entry_block(outcome["no_regression"]["entry_value"]),
            "pass": bool(
                rr83._entry_block(outcome["no_regression"]["entry_key"])["pass"]
                and rr83._entry_block(outcome["no_regression"]["entry_value"])["pass"]
            ),
        },
    }


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """Fixed precedence, written before the run: E0 > Q0 > Q2 > Q1 > Q3."""
    if not gate["I0_instrument"]["pass"]:
        return {
            "id": "E0-instrument",
            "reading": (
                "the control carrier, checkpoint, corpus or budget moved, §82's boundary-query "
                "cell is not reproduced read for read, or the question read no longer uses "
                "§82's query vectors; nothing is read"
            ),
            "next": "fix the instrument before asking whether the read point is learnable",
        }
    if not gate["fit"]["pass"]:
        return {
            "id": "Q0-fit-fails",
            "reading": (
                "with the question turn's write inside the store the read addresses, the "
                "treatment still did not fit the subset it trained on: the fit floor is not "
                "specific to reading before the question write, and the common factor left is "
                "one fixed read vector per decode"
            ),
            "next": (
                "re-run the same registered arm (do not change the read rule or the budget) and "
                "report whether the loss floor reproduces before reading any cell"
            ),
        }
    primary = gate["treatment"][PRIMARY_RULE]
    if primary["pass"] and not gate["no_regression"]["pass"]:
        return {
            "id": "Q2-pass-but-regression",
            "reading": (
                "the fixed question-boundary read now addresses the roster entry the evidence "
                "colour needs, but §79's key/value-to-colour cells no longer pass: the retraining "
                "moved the write side, so the gain is not free"
            ),
            "next": (
                "register the write-side cells on this carrier and separate which of the two "
                "moved, at the same budget"
            ),
        }
    if primary["pass"]:
        return {
            "id": "Q1-read-at-question-works",
            "reading": (
                "at the same budget, parameters and store, holding the read taken at the question "
                "boundary makes that read address the roster entry the evidence colour needs, and "
                "§79's entry cells still pass: the read's position relative to the question write "
                "was what §83's fit floor was missing, and a fixed read is learnable"
            ),
            "next": (
                "read the end-to-end answer cell on this carrier (§80's held-out answer exact) "
                "and, if it moves with the read, register the same read point on the next corpus "
                "seed before calling it a rule"
            ),
        }
    return {
        "id": "Q3-fits-but-no-gain",
        "reading": (
            "the arm fitted with the question boundary's store and a fixed read, but the read "
            "still does not address the roster entry: fixing the read vector is not the fit "
            "floor's cause, and a trained fixed read does not by itself select the entry"
        ),
        "next": (
            "separate 'fixed for the decode' from 'taken once' with a read that is re-addressed "
            "at every decode token from the question boundary's store, at the same budget"
        ),
    }


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def check(path: Path) -> List[str]:
    """Re-derive every gate and the branch from the stored readings."""
    problems: List[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("stage") != STAGE:
        return ["this is not a §84 report"]
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

    split75 = load_readrule83().load_read75()
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

    instrument = data.get("instrument") or {}
    anchor = instrument.get("control_anchor") or {}
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

    identity = instrument.get("query_identity") or {}
    if bool(identity.get("pass")) != bool(
        int(identity.get("mismatches", 1)) == 0
        and float(identity.get("max_abs_diff", 1.0)) == 0.0
        and int(identity.get("compared") or 0) > 0
    ):
        problems.append("query identity does not re-derive")

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


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="§84: take the read at the question boundary and hold it"
    )
    parser.add_argument(
        "--control",
        type=Path,
        default=REPO_ROOT / "data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json",
    )
    parser.add_argument(
        "--treatment",
        type=Path,
        default=None,
        help="the --read-at question report under data/pantry_stage/readrule84/treatment/",
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
            print("§84 check FAIL")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print("§84 check OK")
        return 0

    if args.treatment is None:
        candidates = sorted((REPO_ROOT / "data/pantry_stage/readrule84/treatment").glob("*.json"))
        if not candidates:
            print("§84 needs a --read-at question report; none is staged yet")
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
