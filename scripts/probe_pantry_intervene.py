#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§71: does the roster line *cause* the roster in the state? (intervention, no fitting)

Why this exists
---------------
§70 ended on **B3-roster-present-but-not-fittable** at k=2 (the roster leaves a
trace in the state at its own turn: same-roster held-out states are closer,
AUC 0.7699, p 0.001) and **B4-roster-absent-at-its-own-turn** at k=5 (24
same-roster pairs, so the test had no power). B3's next step and B4's next step
are the same experiment: stop asking fitted readouts, and **intervene on the
roster line itself**.

§70.11 recorded the limit that makes this necessary: the structure test cannot
tell "the state encodes the roster" from "the state encodes the turn's literal
text" - two sessions with the same roster also share their names as tokens. A
probe that only edits one name and then finds the edited state near genuine
sessions of the edited roster is consistent with both readings, because the
edited line *is* textually a genuine roster line.

So the intervention uses three matched edits of the same session, all with the
same token count (names are chosen same-length; colours are all two characters):

* ``swap``    - one name becomes a name of the same byte length that is not in
  the roster. The roster set changes; the line is textually a genuine roster
  line for the edited set.
* ``reverse`` - the clauses are reversed. Same names, same colours, same set,
  different order (this is the corpus's own order twin).
* ``colour``  - one clause's colour word changes to a colour not used in the
  line. Same names, same order, different text.

The two controls are the discriminators. If the state tracks **the roster set**,
``reverse`` and ``colour`` keep it in its own roster's neighbourhood (the set
did not change). If the state tracks **the literal text**, both move it away,
while ``swap`` still lands on genuine text of the edited roster.

What this measures (all capacity-free)
-------------------------------------
* ``movement``  - ``1 - cos(state_edited, state_original)`` at the roster
  boundary: did the edit change the state at all?
* ``lift``      - per row, the mean cosine to unedited reference states whose
  roster equals the **edited** roster minus the mean cosine to states whose
  roster equals the **original** roster. Under "the state carries no roster
  identity" these are exchangeable, so the null is a sign flip per row
  (1,000 draws, fixed seed). No parameters are fitted.
* ``retention`` - the same difference for ``reverse`` and ``colour``, where the
  edited roster *is* the original one: ``mean cos(own roster)`` for the edit
  minus ``mean cos(own roster)`` for the unedited state. A negative value means
  the edit pushed the state away from its own roster.

Why k=5 only reports movement
----------------------------
The neighbourhood test needs unedited reference sessions whose roster equals the
edited roster. There are ``C(12,5)=792`` rosters and 600 reference sessions, so
most edited rosters have no reference at all. That is registered here, before
the run, rather than discovered afterwards: the k=5 arm reports movement and
retention and **does not** claim a lift either way.

What this is not
----------------
Not a capability score (core stays 0.00/10), not a new objective, not more
training: the carrier is frozen and its weights hash and checkpoint sha256 are
recorded before and after. Not a claim that the trace is usable - only that the
line does or does not set it.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_intervene.py \\
        --report data/pantry_stage/ord_arm/pantry_deduction_20261115-015751.json \\
        --out data/pantry_stage/intervene71/k2.json
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

REPO_ROOT = Path(__file__).resolve().parents[1]
FAMILIES = REPO_ROOT / "scripts" / "probe_pantry_families.py"

ROSTER_PREFIX = "今天值班表上寫著："
SEPARATOR = "、"
SUFFIX = "。"

# §71.5, written before the scored run.
EDIT_MOVEMENT_FLOOR = 1e-3
LIFT_ALPHA = 0.001
LIFT_PERMUTATIONS = 1000
LIFT_SEED = 20261124
RETENTION_FLOOR = -0.01
MIN_LIFT_ROWS = 50


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_families() -> Any:
    """§70's module: the boundary extractor and the corpus/selection loaders."""
    return _load("pantry_intervene_families", FAMILIES)


# --------------------------------------------------------------------------- #
# the roster line: parse, render, and three matched edits
# --------------------------------------------------------------------------- #
def roster_turn(session: Dict[str, Any]) -> int:
    return int(session["session_meta"]["roster_turn"])


def clauses_of(session: Dict[str, Any]) -> List[Tuple[str, str]]:
    """``[("白色", "Hana"), ...]`` from the roster turn, or a refusal.

    Refusing rather than skipping is deliberate: a session whose line does not
    parse would silently drop out of the intervention, and the rate would then
    be computed on a subset nobody declared.
    """
    text = str(session["turns"][roster_turn(session)]["user_input"])
    if not text.startswith(ROSTER_PREFIX) or not text.endswith(SUFFIX):
        raise SystemExit(
            f"{session['session_id']}: roster line is not the registered template: {text!r}"
        )
    body = text[len(ROSTER_PREFIX) : -len(SUFFIX)]
    clauses: List[Tuple[str, str]] = []
    for clause in body.split(SEPARATOR):
        if "是 " not in clause:
            raise SystemExit(f"{session['session_id']}: roster clause has no '是 ': {clause!r}")
        head, name = clause.split("是 ", 1)
        clauses.append((head, name))
    if len(clauses) < 2:
        raise SystemExit(f"{session['session_id']}: roster line has fewer than two clauses")
    return clauses


def render_clauses(clauses: Sequence[Tuple[str, str]]) -> str:
    return ROSTER_PREFIX + SEPARATOR.join(f"{head}是 {name}" for head, name in clauses) + SUFFIX


def with_roster_line(session: Dict[str, Any], line: str) -> Dict[str, Any]:
    """A copy whose roster turn says ``line`` and whose other bytes are unchanged."""
    turns = [dict(turn) for turn in session["turns"]]
    turns[roster_turn(session)]["user_input"] = line
    return {**session, "turns": turns}


def _digest(text: str) -> int:
    return int.from_bytes(hashlib.blake2s(text.encode("utf-8"), digest_size=8).digest(), "big")


def edit_swap(
    session: Dict[str, Any], actors: Sequence[str]
) -> Tuple[Dict[str, Any], Tuple[str, ...]]:
    """Replace one name with a **same-byte-length** name that is not in the roster."""
    clauses = clauses_of(session)
    names = [name for _, name in clauses]
    seed = _digest(session["session_id"])
    index = seed % len(clauses)
    name = names[index]
    width = len(name.encode("utf-8"))
    candidates = sorted(
        actor for actor in actors if len(actor.encode("utf-8")) == width and actor not in names
    )
    if not candidates:
        raise SystemExit(
            f"{session['session_id']}: no same-length name outside {names} (width {width})"
        )
    replacement = candidates[(seed >> 8) % len(candidates)]
    edited = list(clauses)
    edited[index] = (clauses[index][0], replacement)
    target = tuple(sorted(names[:index] + [replacement] + names[index + 1 :]))
    return with_roster_line(session, render_clauses(edited)), target


def edit_reverse(session: Dict[str, Any]) -> Dict[str, Any]:
    return with_roster_line(session, render_clauses(list(reversed(clauses_of(session)))))


def edit_colour(session: Dict[str, Any], colours: Sequence[str]) -> Dict[str, Any]:
    """Change one clause's colour word to one the line does not already use."""
    clauses = clauses_of(session)
    used = {head for head, _ in clauses}
    available = sorted(
        colour for colour in colours if colour not in used and len(colour) == len(clauses[0][0])
    )
    if not available:
        raise SystemExit(f"{session['session_id']}: no unused colour of the same width")
    seed = _digest(session["session_id"] + "|colour")
    index = seed % len(clauses)
    edited = list(clauses)
    edited[index] = (available[(seed >> 8) % len(available)], clauses[index][1])
    return with_roster_line(session, render_clauses(edited))


def roster_key(session: Dict[str, Any]) -> Tuple[str, ...]:
    return tuple(sorted(str(name) for name in session["environment"]["actors"]))


def clause_key(session: Dict[str, Any]) -> Tuple[str, ...]:
    """The roster as the line states it: used to check ``swap`` really swapped."""
    return tuple(sorted(name for _, name in clauses_of(session)))


# --------------------------------------------------------------------------- #
# distances and the sign-flip null
# --------------------------------------------------------------------------- #
def cosine_rows(torch: Any, left: Any, right: Any) -> Any:
    unit = torch.nn.functional.normalize
    return unit(left.double(), dim=1) @ unit(right.double(), dim=1).T


def movement(torch: Any, edited: Any, original: Any) -> List[float]:
    similarity = torch.nn.functional.cosine_similarity(edited.double(), original.double(), dim=1)
    return [round(float(1.0 - value), 6) for value in similarity]


def sign_flip(differences: Sequence[float], *, permutations: int, seed: int) -> Dict[str, Any]:
    """One-sided sign-flip test for ``mean(difference) > 0``, no parameters."""
    import torch

    if not differences:
        return {
            "mean": float("nan"),
            "p_value": float("nan"),
            "n_rows": 0,
            "permutations": int(permutations),
            "seed": int(seed),
        }
    tensor = torch.as_tensor(list(differences), dtype=torch.float64)
    observed = float(tensor.mean())
    generator = torch.Generator().manual_seed(seed)
    hits = 0
    for _ in range(int(permutations)):
        signs = torch.randint(0, 2, (tensor.numel(),), generator=generator, dtype=torch.int64)
        signs = signs.to(torch.float64) * 2.0 - 1.0
        if float((tensor * signs).mean()) >= observed:
            hits += 1
    return {
        "mean": round(observed, 6),
        "p_value": round((1.0 + hits) / (1.0 + int(permutations)), 4),
        "n_rows": int(tensor.numel()),
        "permutations": int(permutations),
        "seed": int(seed),
        "differences": [round(value, 6) for value in differences],
    }


def neighbourhood(
    torch: Any,
    edited: Any,
    edited_keys: Sequence[Tuple[str, ...]],
    original_keys: Sequence[Tuple[str, ...]],
    reference: Any,
    reference_keys: Sequence[Tuple[str, ...]],
    reference_ids: Sequence[str],
    edited_ids: Sequence[str],
    *,
    permutations: int = LIFT_PERMUTATIONS,
    seed: int = LIFT_SEED,
) -> Dict[str, Any]:
    """Per row: cos(edited roster's unedited states) - cos(original roster's).

    Reference rows that belong to the edited session are excluded, so the
    comparison never includes the state the edit started from.
    """
    cosine = cosine_rows(torch, edited, reference)
    by_key: Dict[Tuple[str, ...], List[int]] = {}
    for index, key in enumerate(reference_keys):
        by_key.setdefault(key, []).append(index)
    differences: List[float] = []
    top1 = 0
    top1_rows = 0
    missing = 0
    for row in range(int(cosine.shape[0])):
        keep = [
            column
            for column in range(len(reference_ids))
            if reference_ids[column] != edited_ids[row]
        ]
        target = [column for column in by_key.get(edited_keys[row], []) if column in set(keep)]
        original = [column for column in by_key.get(original_keys[row], []) if column in set(keep)]
        if not target or not original:
            missing += 1
            continue
        values = cosine[row]
        differences.append(float(values[target].mean() - values[original].mean()))
        if keep:
            best = max(keep, key=lambda column: float(values[column]))
            top1_rows += 1
            if reference_keys[best] == edited_keys[row]:
                top1 += 1
    block = sign_flip(differences, permutations=permutations, seed=seed)
    block.update(
        {
            "rows_missing_reference": missing,
            "rows_compared": len(differences),
            "top1_edited_roster": top1,
            "top1_rows": top1_rows,
            "top1_rate": round(top1 / top1_rows, 4) if top1_rows else None,
            "distinct_reference_rosters": len(by_key),
            "chance": round(1.0 / len(by_key), 4) if by_key else None,
        }
    )
    return block


def retention(
    torch: Any,
    edited: Any,
    own_keys: Sequence[Tuple[str, ...]],
    reference: Any,
    reference_keys: Sequence[Tuple[str, ...]],
    reference_ids: Sequence[str],
    edited_ids: Sequence[str],
) -> Dict[str, Any]:
    """Mean cos to the state's own roster, per edited row (self excluded)."""
    cosine = cosine_rows(torch, edited, reference)
    by_key: Dict[Tuple[str, ...], List[int]] = {}
    for index, key in enumerate(reference_keys):
        by_key.setdefault(key, []).append(index)
    values: List[float] = []
    for row in range(int(cosine.shape[0])):
        columns = [
            column
            for column in by_key.get(own_keys[row], [])
            if reference_ids[column] != edited_ids[row]
        ]
        if columns:
            values.append(float(cosine[row][columns].mean()))
    return {
        "mean": round(sum(values) / len(values), 6) if values else None,
        "n_rows": len(values),
        "per_row": [round(value, 6) for value in values],
    }


def paired_difference(left: Dict[str, Any], right: Dict[str, Any]) -> List[float]:
    """``left.per_row - right.per_row`` for the rows both blocks measured."""
    if left["n_rows"] != right["n_rows"]:
        raise SystemExit(
            f"retention rows differ ({left['n_rows']} vs {right['n_rows']}): "
            "the edit changed which sessions could be compared"
        )
    return [round(a - b, 6) for a, b in zip(left["per_row"], right["per_row"])]


# --------------------------------------------------------------------------- #
# gates and the fork
# --------------------------------------------------------------------------- #
def gates(report: Dict[str, Any]) -> Dict[str, Any]:
    """§71.6, mechanically, from numbers the report already stores."""
    k = int(report["k"])
    edits = report["edits"]
    lift = report["lift"]
    movement_block = report["movement"]
    retention_block = report["retention"]
    instrument = report["instrument"]

    swap_moves = float(movement_block["swap"]["mean"]) > EDIT_MOVEMENT_FLOOR
    lift_defined = int(lift["rows_compared"]) >= MIN_LIFT_ROWS
    lift_passes = bool(
        lift_defined and float(lift["mean"]) > 0.0 and float(lift["p_value"]) <= LIFT_ALPHA
    )
    retention_ok = bool(
        float(retention_block["reverse"]["difference"]["mean"]) >= RETENTION_FLOOR
        and float(retention_block["colour"]["difference"]["mean"]) >= RETENTION_FLOOR
    )
    return {
        "J0_instrument": {
            "pass": bool(
                instrument["carrier_unchanged"]
                and instrument["checkpoint_unchanged"]
                and instrument["determinism_ok"]
                and instrument["texts_changed"]
                and instrument["token_counts_matched"]
            ),
            "carrier_unchanged": instrument["carrier_unchanged"],
            "checkpoint_unchanged": instrument["checkpoint_unchanged"],
            "determinism_ok": instrument["determinism_ok"],
            "texts_changed": instrument["texts_changed"],
            "token_counts_matched": instrument["token_counts_matched"],
            "reading": (
                "re-running the unedited session reproduces its state, all three edits change the "
                "bytes, and every edit keeps the roster turn's token count"
            ),
        },
        "J1_edit_moves_the_state": {
            "pass": bool(swap_moves),
            "swap_movement": movement_block["swap"]["mean"],
            "reverse_movement": movement_block["reverse"]["mean"],
            "colour_movement": movement_block["colour"]["mean"],
            "floor": EDIT_MOVEMENT_FLOOR,
            "reading": "an edit of the roster line changes the state at the roster boundary",
        },
        "J2_swap_lands_on_the_edited_roster": {
            "pass": lift_passes,
            "defined": lift_defined,
            "mean": lift["mean"],
            "p_value": lift["p_value"],
            "n_rows": lift["rows_compared"],
            "alpha": LIFT_ALPHA,
            "top1_rate": lift["top1_rate"],
            "top1_reference": "top-1 is descriptive; chance is 1 / distinct reference rosters",
            "top1_chance": lift["chance"],
            "reading": (
                "after one name changes, the state is closer to unedited states of the edited "
                "roster than to states of the original roster (sign-flip null, no fitting)"
            ),
        },
        "J3_order_and_colour_keep_the_roster": {
            "pass": bool(retention_ok),
            "reverse_difference": retention_block["reverse"]["difference"]["mean"],
            "colour_difference": retention_block["colour"]["difference"]["mean"],
            "floor": RETENTION_FLOOR,
            "reading": (
                "reversing the clauses and changing one colour do not push the state away from its "
                "own roster, so the trace is the name set rather than the literal line"
            ),
        },
        "J4_neighbourhood_power": {
            "k": k,
            "rows_compared": lift["rows_compared"],
            "rows_missing_reference": lift["rows_missing_reference"],
            "min_rows": MIN_LIFT_ROWS,
            "distinct_reference_rosters": lift["distinct_reference_rosters"],
            "reading": (
                "the neighbourhood question needs unedited states of the edited roster; at k=5 the "
                "roster space is too large for that and this arm only reports movement"
            ),
        },
    }


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """§71.7, mechanically, fixed precedence."""
    if not gate["J0_instrument"]["pass"]:
        return {
            "id": "J0-instrument",
            "reading": (
                "the unedited re-run did not reproduce its own state, an edit did not change the "
                "bytes, or an edit changed the roster turn's token count: no intervention reading "
                "can be taken"
            ),
            "next": "fix the edit plumbing (determinism, byte change, token count), then re-run",
        }
    if not gate["J1_edit_moves_the_state"]["pass"]:
        return {
            "id": "J3-state-ignores-the-turn-text",
            "reading": (
                "editing the roster line does not move the state at the roster boundary "
                f"(movement {gate['J1_edit_moves_the_state']['swap_movement']} vs floor "
                f"{gate['J1_edit_moves_the_state']['floor']}), so this boundary's state is not a "
                "function of the line - which also puts §70's structure result under suspicion"
            ),
            "next": (
                "re-examine what the structure test separated: if the state ignores the turn's "
                "text, the same-roster proximity must come from something else and must be named"
            ),
        }
    if not gate["J2_swap_lands_on_the_edited_roster"]["defined"]:
        return {
            "id": "J4-neighbourhood-underpowered",
            "reading": (
                f"the edit moves the state, but only {gate['J2_swap_lands_on_the_edited_roster']['n_rows']} "
                "rows have unedited reference states of the edited roster (need "
                f"{gate['J4_neighbourhood_power']['min_rows']}), so the 'which roster' question is "
                "not decidable at this k"
            ),
            "next": "keep the movement result; ask the roster question only at a k whose roster space fits the pool",
        }
    if (
        gate["J2_swap_lands_on_the_edited_roster"]["pass"]
        and gate["J3_order_and_colour_keep_the_roster"]["pass"]
    ):
        return {
            "id": "J1-roster-line-sets-the-roster",
            "reading": (
                "changing one name moves the state to the edited roster's neighbourhood "
                f"(lift {gate['J2_swap_lands_on_the_edited_roster']['mean']}, p "
                f"{gate['J2_swap_lands_on_the_edited_roster']['p_value']}), while reversing the "
                "clauses and changing a colour do not move it away from its own roster: the trace "
                "is the roster set, not the literal line"
            ),
            "next": (
                "the roster is addressable in the state at its own turn; ask why the readout "
                "cannot name it (address collision vs superposition) with a per-slot probe"
            ),
        }
    return {
        "id": "J2-the-trace-is-the-line-not-the-roster",
        "reading": (
            "the edit moves the state and lands near the edited roster's genuine lines "
            f"(lift {gate['J2_swap_lands_on_the_edited_roster']['mean']}, p "
            f"{gate['J2_swap_lands_on_the_edited_roster']['p_value']}), but reversing the clauses "
            f"({gate['J3_order_and_colour_keep_the_roster']['reverse_difference']}) or changing a "
            f"colour ({gate['J3_order_and_colour_keep_the_roster']['colour_difference']}) pushes it "
            "away from its own roster: §70.11's surface reading holds - the state tracks the line, "
            "not the set of names"
        ),
        "next": (
            "stop treating the roster boundary as a roster representation; probe the token states "
            "of the names inside the turn and what end_turn writes"
        ),
    }


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #
def _states(
    families: Any,
    trainer: Any,
    contents: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    index: int,
) -> Any:
    return families.boundary_features(trainer, contents, core, sessions, index)["state"]


def run(
    families: Any, report_path: Path, report: Dict[str, Any], *, device: str = "cpu"
) -> Dict[str, Any]:
    boundaries = families.load_boundaries()
    contents = boundaries.load_contents()
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§71 edits the §62/§63/§64 minimal-binding corpus, not this report")
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
    actors = sorted(module.ACTORS)
    colours = sorted(str(value) for value in module.COLOURS.values())

    checkpoint = Path(str(report.get("checkpoint")))
    hash_before = probe.checkpoint_sha256(checkpoint)
    core = probe.rebuild_core(trainer, report, device=device)
    weights_before = str(core.weights_hash() or "")
    torch = core._torch
    started = time.time()

    indexes = boundaries.shared_boundaries(train)
    boundaries.shared_boundaries(heldout)
    roster_index = indexes["roster"]

    references = train + heldout
    reference_states = _states(families, trainer, contents, core, references, roster_index)
    reference_keys = [roster_key(session) for session in references]
    reference_ids = [str(session["session_id"]) for session in references]

    original_states = _states(families, trainer, contents, core, heldout, roster_index)
    # Determinism: the same sessions through a second independent call.
    repeat_states = _states(families, trainer, contents, core, heldout, roster_index)
    determinism = float(
        torch.nn.functional.cosine_similarity(
            original_states.double(), repeat_states.double(), dim=1
        ).min()
    )

    swaps: List[Dict[str, Any]] = []
    reversed_sessions: List[Dict[str, Any]] = []
    colour_sessions: List[Dict[str, Any]] = []
    edited_keys: List[Tuple[str, ...]] = []
    original_keys: List[Tuple[str, ...]] = []
    texts_changed = True
    token_counts_matched = True
    for session in heldout:
        turn = roster_turn(session)
        original_line = str(session["turns"][turn]["user_input"])
        swapped, target = edit_swap(session, actors)
        if clause_key(swapped) != target:
            raise SystemExit(f"{session['session_id']}: swap did not produce the target roster")
        reversed_session = edit_reverse(session)
        colour_session = edit_colour(session, colours)
        for edited in (swapped, reversed_session, colour_session):
            if str(edited["turns"][turn]["user_input"]) == original_line:
                texts_changed = False
            if len(edited["turns"][turn]["user_input"].encode("utf-8")) != len(
                original_line.encode("utf-8")
            ):
                token_counts_matched = False
        swaps.append(swapped)
        edited_keys.append(target)
        original_keys.append(roster_key(session))
        reversed_sessions.append(reversed_session)
        colour_sessions.append(colour_session)

    swap_states = _states(families, trainer, contents, core, swaps, roster_index)
    reverse_states = _states(families, trainer, contents, core, reversed_sessions, roster_index)
    colour_states = _states(families, trainer, contents, core, colour_sessions, roster_index)
    edited_ids = [str(session["session_id"]) for session in heldout]

    movement_block = {
        "swap": {
            "mean": round(sum(movement(torch, swap_states, original_states)) / len(heldout), 6),
            "per_row": movement(torch, swap_states, original_states),
        },
        "reverse": {
            "mean": round(sum(movement(torch, reverse_states, original_states)) / len(heldout), 6),
            "per_row": movement(torch, reverse_states, original_states),
        },
        "colour": {
            "mean": round(sum(movement(torch, colour_states, original_states)) / len(heldout), 6),
            "per_row": movement(torch, colour_states, original_states),
        },
    }

    lift = neighbourhood(
        torch,
        swap_states,
        edited_keys,
        original_keys,
        reference_states,
        reference_keys,
        reference_ids,
        edited_ids,
    )

    reverse_own = retention(
        torch,
        reverse_states,
        original_keys,
        reference_states,
        reference_keys,
        reference_ids,
        edited_ids,
    )
    colour_own = retention(
        torch,
        colour_states,
        original_keys,
        reference_states,
        reference_keys,
        reference_ids,
        edited_ids,
    )
    original_own = retention(
        torch,
        original_states,
        original_keys,
        reference_states,
        reference_keys,
        reference_ids,
        edited_ids,
    )
    swap_own = retention(
        torch, swap_states, edited_keys, reference_states, reference_keys, reference_ids, edited_ids
    )
    retention_block = {
        "original": {"mean": original_own["mean"], "n_rows": original_own["n_rows"]},
        "swap": {"mean": swap_own["mean"], "n_rows": swap_own["n_rows"]},
        "reverse": {
            "mean": reverse_own["mean"],
            "difference": sign_flip(
                paired_difference(reverse_own, original_own),
                permutations=LIFT_PERMUTATIONS,
                seed=LIFT_SEED + 1,
            ),
        },
        "colour": {
            "mean": colour_own["mean"],
            "difference": sign_flip(
                paired_difference(colour_own, original_own),
                permutations=LIFT_PERMUTATIONS,
                seed=LIFT_SEED + 2,
            ),
        },
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
        "determinism_min_cosine": round(determinism, 8),
        "determinism_ok": bool(determinism >= 1.0 - 1e-6),
        "texts_changed": bool(texts_changed),
        "token_counts_matched": bool(token_counts_matched),
        "seconds": 0.0,
    }
    outcome: Dict[str, Any] = {
        "stage": "§71 does the roster line cause the roster in the state",
        "source_report": str(report_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "turns": indexes,
        "dimensions": {"colours": len(colours), "names": len(actors)},
        "corpus": {
            "train_digest": (corpus.get("meta") or {}).get("train_digest"),
            "heldout_digest": (corpus.get("meta") or {}).get("heldout_digest"),
            "train_items": len(train),
            "heldout_items": len(heldout),
            "reference_items": len(references),
            "reference_rosters": len(set(reference_keys)),
        },
        "edits": {
            "swap": "one name -> a same-byte-length name not in the roster",
            "reverse": "reverse the clause order (same names, same colours)",
            "colour": "one colour word -> a colour the line does not use (same width)",
            "invariants": (
                "only the roster turn's user_input changes; names are chosen same-length and "
                "colours are two characters, so the roster turn's token count is unchanged"
            ),
        },
        "probe": {
            "features": "frozen carrier state [h, read] at the roster boundary, torch.no_grad",
            "movement": "1 - cos(edited state, unedited state), per held-out row",
            "lift": (
                "per row: mean cos to unedited states of the edited roster minus mean cos to "
                "states of the original roster; sign-flip null, no fitted parameters"
            ),
            "retention": (
                "per row: mean cos to the state's own roster after an order/colour edit, minus the "
                "same mean for the unedited state"
            ),
            "edit_movement_floor": EDIT_MOVEMENT_FLOOR,
            "lift_alpha": LIFT_ALPHA,
            "lift_permutations": LIFT_PERMUTATIONS,
            "lift_seed": LIFT_SEED,
            "retention_floor": RETENTION_FLOOR,
            "min_lift_rows": MIN_LIFT_ROWS,
            "top1_reference": "top-1 is descriptive; chance is 1 / distinct reference rosters",
        },
        "movement": movement_block,
        "lift": lift,
        "retention": retention_block,
        "instrument": instrument,
    }
    outcome["gates"] = gates(outcome)
    outcome["branch"] = branch(outcome["gates"])
    instrument["seconds"] = round(time.time() - started, 2)
    outcome["instrument_ok"] = bool(
        outcome["gates"]["J0_instrument"]["pass"]
        and outcome["gates"]["J1_edit_moves_the_state"]["pass"]
    )
    return outcome


# --------------------------------------------------------------------------- #
# mechanical re-check
# --------------------------------------------------------------------------- #
def check(path: Path) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    problems: List[str] = []
    for name in ("swap", "reverse", "colour"):
        block = (data.get("movement") or {}).get(name) or {}
        if not isinstance(block.get("mean"), (int, float)):
            problems.append(f"movement.{name} has no mean")
        elif not isinstance(block.get("per_row"), list) or not block["per_row"]:
            problems.append(f"movement.{name} has no per-row values")
        else:
            recomputed = sum(block["per_row"]) / len(block["per_row"])
            if abs(recomputed - float(block["mean"])) > 1e-4:
                problems.append(f"movement.{name}.mean does not follow from its rows")
    lift = data.get("lift") or {}
    differences = lift.get("differences")
    if not isinstance(differences, list) or not differences:
        problems.append("lift has no per-row differences")
    else:
        block = sign_flip(
            differences,
            permutations=int(lift.get("permutations") or 0),
            seed=int(lift.get("seed") or 0),
        )
        if abs(block["p_value"] - float(lift.get("p_value"))) > 1e-9:
            problems.append(
                f"lift.p_value {lift.get('p_value')} does not follow from its own differences "
                f"({block['p_value']})"
            )
        if abs(block["mean"] - float(lift.get("mean"))) > 1e-5:
            problems.append("lift.mean does not follow from its own differences")
        if int(lift.get("rows_compared") or 0) != len(differences):
            problems.append("lift.rows_compared does not match the stored differences")
    for name in ("reverse", "colour"):
        block = ((data.get("retention") or {}).get(name) or {}).get("difference") or {}
        rows = block.get("differences")
        if not isinstance(rows, list) or not rows:
            problems.append(f"retention.{name} has no per-row differences")
            continue
        recomputed = sign_flip(
            rows,
            permutations=int(block.get("permutations") or 0),
            seed=int(block.get("seed") or 0),
        )
        if abs(recomputed["p_value"] - float(block.get("p_value"))) > 1e-9:
            problems.append(f"retention.{name}.p_value does not follow from its rows")
        if abs(recomputed["mean"] - float(block.get("mean"))) > 1e-5:
            problems.append(f"retention.{name}.mean does not follow from its rows")
    try:
        expected = gates(data)
    except (KeyError, TypeError, ZeroDivisionError) as error:
        problems.append(f"the stored numbers cannot be re-gated: {error}")
        return problems
    for key, block in expected.items():
        stored = (data.get("gates") or {}).get(key) or {}
        for flag in ("pass", "defined"):
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
    parser.add_argument("--check", default="", help="re-derive a stage-§71 JSON's verdict")
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
    print(
        f"corpus : {outcome['corpus']['train_items']} train + "
        f"{outcome['corpus']['heldout_items']} held-out, "
        f"{outcome['corpus']['reference_rosters']} reference rosters"
    )
    print()
    print(f"  {'edit':10s} {'movement':>10s}")
    for name, block in outcome["movement"].items():
        print(f"  {name:10s} {block['mean']:10.6f}")
    print()
    print(
        f"  lift   : mean {outcome['lift']['mean']}  p {outcome['lift']['p_value']}  "
        f"rows {outcome['lift']['rows_compared']}  "
        f"top1 {outcome['lift']['top1_rate']} (chance {outcome['lift']['chance']})"
    )
    for name in ("reverse", "colour"):
        block = outcome["retention"][name]["difference"]
        print(
            f"  {name:6s} retention: mean {block['mean']}  p {block['p_value']}  "
            f"rows {block['n_rows']}"
        )
    print()
    for key, block in outcome["gates"].items():
        flag = block.get("pass", block.get("defined"))
        print(f"  {key:44s} {'PASS' if flag else 'FAIL'}")
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
