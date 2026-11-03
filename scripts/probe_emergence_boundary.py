#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""MVE-1 emergence-boundary instrument: holdout set, shuffled control, gate.

CORE_GAP_ANALYSIS §十一.4 defined the minimum measurable emergence (MVE-1)
threshold — compositional-holdout free-running exact ≥5/200 with the shuffled
control ≤1/200 — but the instrument did not exist, so the next 0 could not be
told apart from an unmeasurable task. This script *is* that instrument.

Design decisions, each forced by evidence from rounds 1-3:

1. **Single gold, the rung named in the prompt (round-4 schema).** Rounds
   1-3 hid ``dt`` while the contract operator is
   ``S(t+1) = F(S(t), events, dt)`` (§5), so the target was
   under-determined by construction and grading accepted any of the four
   ladder rungs (family-exact — the archived round-3 baseline read under
   that criterion). Since round 4, ``generate_al_dataset.py --expose-dt``
   puts dt in the input line (``... intent=x dt=1.00 | text``), gold is the
   matching rung only and exact means *exact*: a 0 can no longer hide behind
   either an invisible input or a lucky family match. The four-rung family
   is still scored per row as the ``wrong_rung`` diagnostic — hits there
   mean the model was handed dt and ignored it.

2. **The response is given in the prompt.** Training rows read
   ``prompt + "\\n" + response + "\\n" + <al_out> block``; under teacher
   forcing the block is predicted *conditioned on the gold response*, and the
   contract's F does not consume response text. Prompting with the response
   isolates the AL transition (the project's own rule) from corpus verbatim
   recall (response_tf ≈ 26%, which would pin exact at 0 regardless of the
   AL side). The probe prompt is byte-for-byte the training prefix up to the
   block, so free-running the block is the same task the model trained on.

3. **Compositional cells = (intent × mode), carved on the training side.**
   dt is invisible to rounds 1-3, so an (intent × dt) holdout would not be
   well-posed there. (intent × mode) is: each primitive stays in training
   (every intent keeps its other two modes, every mode keeps other intents),
   while the cell itself never appears — passing requires composing the
   intent-target branch with the mode-carry branch on unseen rows. The carve
   lives in ``generate_al_dataset.py --holdout-cells`` (default off = byte-
   identical rebuilds). Until a training round carves the cells, readings are
   labelled *baseline* (rounds 1-3 trained on all cells).

4. **Rotation control.** Row i is graded against row i+1's gold (a
   derangement — no row ever keeps its own gold, so unlike a random shuffle
   there is no expected false hit). Same generations, wrong pairing: any hit
   means format/probability artefacts, not mapping. Gate: exact ≥5/200
   **and** rotation ≤1/200 — the registered numbers; with dt exposed the
   criterion is strictly harder than the family baseline rounds 1-3 read
   against, and the gate keys keep their names so the report schema stays
   comparable.

Rows come from a corpus slice no training round has used (default accepted
rows [10000, 50000) — the band that still carries every intent),
leak-checked against every ``ai_al_*train*/val*`` file, and filtered
with the exact window criterion (tokenize == vocab.encode atom count, so the
192-token budget is checked without a checkpoint).

Usage:
    scripts/probe_emergence_boundary.py --build
    scripts/probe_emergence_boundary.py --check
    scripts/probe_emergence_boundary.py --probe \
        --checkpoint data/checkpoints/ai_al_round3.pt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = REPO_ROOT / "scripts"
_SRC = REPO_ROOT / "apps" / "backend" / "src"
for _p in (str(_SCRIPTS), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import generate_al_dataset as gen  # noqa: E402  (paths set above)
import prepare_ai_al_training_data as prep  # noqa: E402
from ai.ed3n.token_snn import tokenize  # noqa: E402

PROCESSED = REPO_ROOT / "apps" / "backend" / "data" / "processed"
SET_OUT = PROCESSED / "mve1_emergence_boundary.json"
REPORT_OUT = REPO_ROOT / "data" / "intelligence_reports" / "mve1_emergence_boundary.json"

GATE_N = 200
GATE_EXACT_MIN = 5
GATE_CONTROL_MAX = 1
_FIELD_KEYS = ("v", "a", "d", "fatigue", "stress", "health")
_MARKER = "<al_out>"
# Reference cells use the three corpus-abundant intents: rarity (humor ≈ 0.2%
# of core_train) makes a reference set from them fragile, and the reference's
# job is only to show the task is doable at all on *seen* compositions.
_REFERENCE_INTENTS = ("unknown", "knowledge_query", "math_query")


# -- shared pieces (single code path with the data pipeline) ----------------


def _atoms(text: str) -> int:
    """Atom count; tokenize and vocab.encode are length-identical by contract."""
    return len(tokenize(text))


def pair_fits(prompt: str, block: str, max_len: int) -> bool:
    """The training window criterion, checked without a checkpoint.

    ``token_snn._encode`` builds ``[bos] + prompt + [\\n] + block + [eos]`` for
    the probe pair, and ``train_token_snn.fits`` counts the same total for the
    training pair (prompt + response + separator + block) — so 3 + atoms is
    the exact budget both sides obey.
    """
    return 3 + _atoms(prompt) + _atoms(block) <= max_len


def family_golds(
    state_in: Dict[str, object],
    intent: str,
    baseline: Dict[str, float],
    targets: Dict[str, Dict[str, float]],
    decimals: int = 2,
) -> List[str]:
    """The four legal targets for one input: one per dt rung (decision 1).

    ``decimals`` must match the input line's: a 3dp input graded against a 2dp
    gold carries 0.005 of the *grader's own* rounding as if it were model error.
    """
    target = targets.get(intent, baseline)
    mode = str(state_in["routing_mode"])
    golds: List[str] = []
    for dt in gen._DT_LADDER:
        out: Dict[str, object] = dict(gen.transition(state_in, target, dt))  # type: ignore[arg-type]
        out["routing_mode"] = mode  # carried: 10/10 pilot rows keep it
        golds.append(prep._state_line(out, intent, "out", decimals=decimals))
    return golds


def grade(got: str, golds: Sequence[str]) -> Tuple[bool, Optional[int]]:
    """Family-exact: the generated block must equal one rung's gold verbatim."""
    text = got.strip()
    for i, gold in enumerate(golds):
        if text == gold.strip():
            return True, i
    return False, None


def gate(family_hits: int, rotation_hits: int, holdout_n: int = GATE_N) -> Dict[str, object]:
    return {
        "n": holdout_n,
        "family_min": GATE_EXACT_MIN,
        "rotation_max": GATE_CONTROL_MAX,
        "family_hits": family_hits,
        "rotation_hits": rotation_hits,
        "pass": family_hits >= GATE_EXACT_MIN and rotation_hits <= GATE_CONTROL_MAX,
    }


def _set_label(entry: dict) -> str:
    return "holdout" if str(entry["sample_id"]).startswith("mve1h_") else "reference"


def rotation_index_map(rows: Sequence[dict]) -> List[int]:
    """Per-row rotation target, deranged *within* each set (never across)."""
    groups: Dict[str, List[int]] = {}
    for i, entry in enumerate(rows):
        groups.setdefault(_set_label(entry), []).append(i)
    rot = list(range(len(rows)))
    for idxs in groups.values():
        for j, i in enumerate(idxs):
            rot[i] = idxs[(j + 1) % len(idxs)]
    return rot


def _ref_mode(holdout_mode: str) -> str:
    return next(m for m in gen._MODES if m != holdout_mode)


def _parse_block(text: str) -> Dict[str, str]:
    """``{"v": "-0.16", ..., "mode": "...", "intent": "..."}`` from a block."""
    out: Dict[str, str] = {}
    for tok in str(text).split():
        if "=" in tok:
            key, value = tok.split("=", 1)
            out.setdefault(key, value)
    return out


def _pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    """Pearson r, or ``None`` when either series is constant.

    ``None`` is the honest answer for a collapsed block: a model that emits one
    fixed value has zero output variance, so there is no correlation to report
    (0.0 would wrongly read as "uncorrelated but varying").
    """
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return round(sxy / (sxx**0.5 * syy**0.5), 3)


def _body(text: str) -> str:
    """The state block only — everything after ``<al_out>``."""
    stripped = str(text).strip()
    if _MARKER in stripped:
        return stripped.split(_MARKER, 1)[1].strip()
    return stripped


def _mutate(prompt: str, field: str, value: str) -> str:
    """Rewrite one ``<al_in>`` field, leaving the rest byte-identical.

    Only the first line (the ``<al_in>`` header) is touched, so a perturbation
    cannot accidentally rewrite the block the model is about to predict.
    """
    head, sep, rest = str(prompt).partition("\n")
    pattern = rf"\b{re.escape(field)}=-?\d+\.?\d*"
    return re.sub(pattern, f"{field}={value}", head, count=1) + sep + rest


_AXIS_OF = {
    "v": "valence",
    "a": "arousal",
    "d": "dominance",
    "fatigue": "fatigue",
    "stress": "stress",
    "health": "health",
}
_GRID = 0.005  # gold is printed to 2dp; a prediction is "exact" within half a unit
# one-hot vocabulary for the affine ceiling; an intent outside this list is
# simply all-zeros (the fit then treats it as the intercept), which is honest
# for a row the ceiling has no column for.
_MODES_ORDER = tuple(gen._MODES)
_INTENTS_ORDER = ("greeting", "humor", "knowledge_query", "math_query", "unknown")


def _gold_correlation(rows: Sequence[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    """Ceiling for ``input_output_correlation``: gold's own input→output slope.

    Round 8 read ≤0.14 in every field and that number means nothing on its own:
    a contract whose output barely moves with the input would be reported as a
    model failure. Read against this, 0.76-0.83 is the value a correct model
    would reproduce, so the gap — not the distance from zero — is the reading.
    """
    xs: Dict[str, List[float]] = {f: [] for f in _FIELD_KEYS}
    ys: Dict[str, List[float]] = {f: [] for f in _FIELD_KEYS}
    for entry in rows:
        parsed = _parse_block(entry.get("gold", ""))
        state = entry.get("state_in") or {}
        for f in _FIELD_KEYS:
            if f not in parsed or _AXIS_OF[f] not in state:
                continue
            try:
                xs[f].append(float(state[_AXIS_OF[f]]))
                ys[f].append(float(parsed[f]))
            except (TypeError, ValueError):
                continue
    return {f: _pearson(xs[f], ys[f]) for f in _FIELD_KEYS}


def _affine_ceiling(rows: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Is the AL transition learnable at all? Fit the contract's own form, twice.

    ``generate_al_dataset.transition`` is ``out = t + (s - t)·exp(-dt/tau)``:
    linear in ``(s, t)`` *with a dt-dependent coefficient*. Rounding out 0/200
    is only evidence about the model if that form can be recovered from the
    rows at all, so this fits it directly — once per ``dt`` (the model is told
    dt) and once with dt as a plain additive feature (no interaction). The two
    numbers separate "the model cannot regress" from "the model never used dt",
    which ``dt_conditioning`` cannot report while no block is legal.

    Fit per rung over 5 folds and score out-of-fold predictions: 200 rows cannot
    spare a fixed half for fitting (15 columns per rung), and fitting on all of
    them would score the fit against itself. Exact means every field within
    0.005 of gold — the same unit the grader uses.
    """
    try:
        import numpy as np  # noqa: PLC0415  (optional: the probe works without it)
    except ImportError:
        return None
    feats: List[List[float]] = []
    targets: List[List[float]] = []
    dts: List[float] = []
    for entry in rows:
        parsed = _parse_block(entry.get("gold", ""))
        state = entry.get("state_in") or {}
        if any(f not in parsed for f in _FIELD_KEYS):
            continue
        try:
            state_values = [float(state[_AXIS_OF[f]]) for f in _FIELD_KEYS]
            dt = float(entry["dt"])
        except (KeyError, TypeError, ValueError):
            continue
        mode = str(entry.get("mode") or "")
        intent = str(entry.get("intent") or "")
        feats.append(
            state_values
            + [float(mode == m) for m in _MODES_ORDER]
            + [float(intent == i) for i in _INTENTS_ORDER]
        )
        targets.append([float(parsed[f]) for f in _FIELD_KEYS])
        dts.append(dt)
    if len(feats) < 8:
        return None
    x = np.array(feats, dtype=float)
    y = np.array(targets, dtype=float)
    dt_col = np.array(dts, dtype=float)
    lo = np.array([-1.0, -1.0, -1.0, 0.0, 0.0, 0.0])
    hi = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

    def _score(pred: Any) -> Dict[str, Any]:
        err = np.abs(y - np.clip(pred, lo, hi))
        r2 = {}
        for i, f in enumerate(_FIELD_KEYS):
            ss_res = float(((y[:, i] - np.clip(pred[:, i], lo[i], hi[i])) ** 2).sum())
            ss_tot = float(((y[:, i] - y[:, i].mean()) ** 2).sum())
            r2[f] = round(1.0 - ss_res / ss_tot, 4) if ss_tot > 0 else None
        return {
            "row_exact": round(float(np.mean(np.all(err <= _GRID, axis=1))), 4),
            "field_within": {
                f: round(float(np.mean(err[:, i] <= _GRID)), 4) for i, f in enumerate(_FIELD_KEYS)
            },
            "r2": r2,
        }

    one = np.ones((len(feats), 1))
    design_all = np.hstack([x, one])
    folds = 5
    fold_of = np.arange(len(feats)) % folds
    # dt-blind first: a rung with too few rows to fit 15 columns per rung would
    # otherwise leave its rows at zero and report a fabricated negative R², so
    # those rows fall back to the blind prediction and are counted as unfitted.
    design_blind = np.hstack([x, dt_col[:, None], one])
    pred_blind = np.zeros_like(y)
    for fold in range(folds):
        fit_rows = np.flatnonzero(fold_of != fold)
        eval_rows = np.flatnonzero(fold_of == fold)
        coef_blind, *_ = np.linalg.lstsq(design_blind[fit_rows], y[fit_rows], rcond=None)
        pred_blind[eval_rows] = design_blind[eval_rows] @ coef_blind

    pred_conditioned = pred_blind.copy()
    rungs_fitted = 0
    unfitted_rows = 0
    for rung in sorted(set(dts)):
        rung_rows = np.flatnonzero(dt_col == rung)
        # one coefficient set per rung needs more fit rows than columns,
        # otherwise the fold interpolates and the score would be a fiction
        if rung_rows.size - (rung_rows.size + folds - 1) // folds <= design_all.shape[1]:
            unfitted_rows += int(rung_rows.size)
            continue
        fitted = False
        for fold in range(folds):
            fit_rows = rung_rows[fold_of[rung_rows] != fold]
            eval_rows = rung_rows[fold_of[rung_rows] == fold]
            if not eval_rows.size or fit_rows.size <= design_all.shape[1]:
                continue
            coef, *_ = np.linalg.lstsq(design_all[fit_rows], y[fit_rows], rcond=None)
            pred_conditioned[eval_rows] = design_all[eval_rows] @ coef
            fitted = True
        rungs_fitted += int(fitted)

    return {
        "folds": folds,
        "rows": len(feats),
        "rungs_fitted": rungs_fitted,
        "rungs_unfitted_rows": unfitted_rows,
        "grid": _GRID,
        "dt_conditioned": _score(pred_conditioned),
        "dt_blind": _score(pred_blind),
    }


_TAU_GRID = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
# the contract table spells three fields out; the block uses the short names
_FIELD_LONG = {
    "v": "valence",
    "a": "arousal",
    "d": "dominance",
    "fatigue": "fatigue",
    "stress": "stress",
    "health": "health",
}
DEFAULT_TRAIN = PROCESSED / "ai_al_round7_train.jsonl"


def _parse_input_line(prompt: str) -> Dict[str, str]:
    """``<al_in>`` header only — the 2dp values the model actually sees."""
    return _parse_block(str(prompt).split("\n", 1)[0])


def _contract_train_rows(train_path: Path) -> List[Dict[str, Any]]:
    """Training pairs in the shape both constant estimators read."""
    rows: List[Dict[str, Any]] = []
    if not Path(train_path).is_file():
        return rows
    with Path(train_path).open(encoding="utf-8") as fh:
        for line in fh:
            try:
                row = json.loads(line)
                state = _parse_input_line(row["input"])
                gold = _parse_block(_body(row["output"]))
                rows.append(
                    {
                        "state": {f: float(state[f]) for f in _FIELD_KEYS},
                        "gold": {f: float(gold[f]) for f in _FIELD_KEYS},
                        "dt": float(state["dt"]),
                        "intent": str(state["intent"]),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return rows


def _learn_contract_constants(
    train_path: Path, tau: float, estimator: str = "median"
) -> Tuple[Dict[Tuple[str, str], float], int]:
    """``c[intent][field]`` from training pairs, plus row count.

    Two estimators, because they disagree in a measurable way. ``median`` inverts
    ``out = c + (in - c)·k`` per row (``c = (out - in·k)/(1-k)``) and takes the
    middle value: robust to a few bad rows, but it weighs a near-zero ``1-k`` row
    — whose implied constant is amplified noise — the same as an informative one.
    ``ls`` is the least-squares solve, which is the exact answer for this model.
    """
    rows = _contract_train_rows(train_path)
    if not rows:
        return {}, 0
    if estimator == "ls":
        return _solve_operator_constants(rows, tau), len(rows)
    implied: Dict[Tuple[str, str], List[float]] = {}
    for row in rows:
        k = pow(math.e, -row["dt"] / tau)
        if abs(1.0 - k) < 1e-6:
            continue
        for f in _FIELD_KEYS:
            implied.setdefault((row["intent"], f), []).append(
                (row["gold"][f] - row["state"][f] * k) / (1.0 - k)
            )
    constants = {}
    for key, values in implied.items():
        ordered = sorted(values)
        constants[key] = ordered[len(ordered) // 2]
    return constants, len(rows)


def _contract_form_ceiling(
    rows: Sequence[Dict[str, Any]], train_path: Path = DEFAULT_TRAIN
) -> Optional[Dict[str, Any]]:
    """The ceiling that matters: apply the contract's own operator.

    ``generate_al_dataset.build`` computes

        out[f] = c[intent][f] + (state[f] - c[intent][f]) · exp(-dt / tau)

    with ``tau = 1.0`` and ``c`` fitted to the 10 pilot rows. So the gold block
    is a 6-number lookup per intent plus one exponential — fully determined by
    tokens that are *in the prompt* except ``c``, which exists only in the data.
    This learns ``c`` from training pairs alone (median of the implied constant),
    picks ``tau`` on a grid using those pairs only, and then applies the operator
    to the graded rows. That is what ``0/200`` should be read against: the affine
    ceiling reports 0.50 because it fits one linear map per rung across intents,
    which cannot express ``c[intent]·(1 - k)``.

    Rows whose intent has no training pairs are counted separately: nothing in
    the prompt identifies that intent's constants, so they are not "hard", they
    are unpredicted by construction. The gate denominator still includes them.
    """
    train_path = Path(train_path)
    parsed_rows: List[Dict[str, Any]] = []
    for entry in rows:
        state = _parse_input_line(entry.get("prompt", ""))
        gold = _parse_block(entry.get("gold", ""))
        try:
            parsed_rows.append(
                {
                    "state": {f: float(state[f]) for f in _FIELD_KEYS},
                    "gold": {f: float(gold[f]) for f in _FIELD_KEYS},
                    "dt": float(state["dt"]),
                    "intent": str(state.get("intent") or ""),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    if not parsed_rows:
        return None

    best: Optional[Dict[str, Any]] = None
    comparison: Dict[str, Any] = {}
    for estimator in ("median", "ls"):
        for tau in _TAU_GRID:
            constants, train_used = _learn_contract_constants(train_path, tau, estimator)
            if not constants or not train_used:
                continue
            scored = _score_contract_rows(parsed_rows, constants, tau)
            score = scored.pop("row_exact_seen")
            if estimator not in comparison or score > comparison[estimator]["row_exact_seen"]:
                comparison[estimator] = {
                    "row_exact_seen": score,
                    "row_exact_all_intents": scored["row_exact_all_intents"],
                    "tau": tau,
                }
            if best is None or score > best["row_exact_seen"]:
                best = {
                    **scored,
                    "row_exact_seen": score,
                    "tau": tau,
                    "train_rows": train_used,
                    "estimator": estimator,
                }
    if best is not None:
        best["estimator_comparison"] = comparison
    return best


def _score_contract_rows(
    parsed_rows: Sequence[Dict[str, Any]],
    constants: Dict[Tuple[str, str], float],
    tau: float,
    targets: Optional[Dict[str, Dict[str, float]]] = None,
) -> Dict[str, Any]:
    """Apply the operator.

    ``targets`` is the contract's intent table (§5: the state relaxes toward the
    intent's target). Passing it is what lets an intent the *training file never
    covered* be answered at all — the target is a runtime lookup in production,
    not a learned weight, so leaving those rows out is a property of this probe,
    not of the contract. Both readings are returned.
    """
    seen_n = seen_exact = unseen_n = unseen_exact = 0
    seen_aware = unseen_aware = 0
    field_hits = {f: 0 for f in _FIELD_KEYS}
    for row in parsed_rows:
        intent = row["intent"]
        known = (intent, _FIELD_KEYS[0]) in constants
        if not known and not (targets and intent in targets):
            unseen_n += 1
            continue
        k = pow(math.e, -row["dt"] / tau)
        ok = True
        # the input line is printed at 2dp, so |Δin| ≤ 0.005 propagates as
        # 0.005·k. Grading against the bare grid therefore counts printing error
        # as model error; this second reading allows for it.
        aware = True
        for f in _FIELD_KEYS:
            c = constants[(intent, f)] if known else float(targets[intent][_FIELD_LONG[f]])
            pred = c + (row["state"][f] - c) * k
            err = abs(pred - row["gold"][f])
            hit = err <= _GRID
            field_hits[f] += int(hit)
            ok = ok and hit
            aware = aware and err <= _GRID * (1.0 + k)
        if known:
            seen_n += 1
            seen_exact += int(ok)
            seen_aware += int(aware)
        else:
            unseen_n += 1
            unseen_exact += int(ok)
            unseen_aware += int(aware)
    graded = seen_exact + unseen_exact
    graded_aware = seen_aware + unseen_aware
    return {
        "rows": len(parsed_rows),
        "seen_intent_rows": seen_n,
        "unseen_intent_rows": unseen_n,
        "row_exact_seen": round(seen_exact / seen_n, 4) if seen_n else 0.0,
        "row_exact_all_intents": round(graded / len(parsed_rows), 4),
        "row_exact_all_intents_rounding_aware": round(graded_aware / len(parsed_rows), 4),
        "row_exact_of_all": round(seen_exact / len(parsed_rows), 4),
        "field_within": {
            f: round(field_hits[f] / max(1, seen_n + unseen_exact), 4) for f in _FIELD_KEYS
        },
    }


def _contract_table() -> Optional[Tuple[Dict[str, Dict[str, float]], Dict[str, float]]]:
    """The pilot intent targets and the mean in-state baseline, if present."""
    try:
        import generate_al_dataset as gen

        baseline, targets, _rows = gen._pilot_tables()
    except (ImportError, SystemExit, FileNotFoundError, ValueError, KeyError):
        return None
    if not targets:
        return None
    return targets, baseline


def _structural_ceiling(
    parsed_rows: Sequence[Dict[str, Any]],
    targets: Dict[str, Dict[str, float]],
    baseline: Dict[str, float],
    tau: float,
) -> Dict[str, Any]:
    """Exact rows achievable with the *true* targets and exact arithmetic.

    The block is graded against a 2dp gold at ±0.005 while the input it must be
    computed from is itself printed at 2dp, so the inherited error is
    ``|Δin|·k ≤ 0.005·exp(-dt/tau)`` on top of gold's own rounding. For short dt
    that exceeds the tolerance on its own: some rows are unmatchable regardless
    of the model. This is the number any gate reading has to be divided by.
    """
    hits = 0
    hits_aware = 0
    by_dt: Dict[float, Dict[str, int]] = {}
    errors: List[float] = []
    for row in parsed_rows:
        target = targets.get(row["intent"], baseline)
        k = pow(math.e, -row["dt"] / tau)
        worst = 0.0
        for f in _FIELD_KEYS:
            c = float(target[_FIELD_LONG[f]])
            worst = max(worst, abs(c + (row["state"][f] - c) * k - row["gold"][f]))
        errors.append(worst)
        ok = worst <= _GRID
        aware = worst <= _GRID * (1.0 + k)
        hits += int(ok)
        hits_aware += int(aware)
        bucket = by_dt.setdefault(row["dt"], {"rows": 0, "exact": 0, "exact_rounding_aware": 0})
        bucket["rows"] += 1
        bucket["exact"] += int(ok)
        bucket["exact_rounding_aware"] += int(aware)
    n = len(parsed_rows)
    return {
        "rows": n,
        "exact": hits,
        "row_exact": round(hits / n, 4) if n else 0.0,
        "exact_rounding_aware": hits_aware,
        "row_exact_rounding_aware": round(hits_aware / n, 4) if n else 0.0,
        "by_dt": {str(a): b for a, b in sorted(by_dt.items())},
        "max_abs_error_median": round(sorted(errors)[n // 2], 4) if errors else 0.0,
        "max_abs_error_p90": round(sorted(errors)[min(n - 1, int(0.9 * n))], 4) if errors else 0.0,
        "reason": "input and gold are both printed at 2dp; error = |Δin|*exp(-dt/tau) "
        "is up to 0.005*k on top of gold's rounding",
    }


def _input_sensitivity(model: Any, rows: Sequence[Dict[str, Any]], max_len: int) -> Dict[str, Any]:
    """Does the block change when only one input field changes?

    Correlation can be 0 both for "ignores the input" and for "depends on it
    non-monotonically", so this asks the causal question directly: regenerate
    the same row with one ``<al_in>`` value replaced and see whether the block
    moves. Round 7 measured 12/24 for ``v`` and 14/24 for ``dt`` — the model does
    read the prefix, but the dependency is ragged.
    """
    v_changed = 0
    dt_changed = 0
    for entry in rows:
        budget = min(max_len, len(model.vocab.encode(entry["gold"])) + 8)
        base = _body(model.generate(entry["prompt"], max_new=budget))
        for field, value in (("v", "-0.90"), ("dt", "2.00")):
            mutated = _mutate(entry["prompt"], field, value)
            if mutated == entry["prompt"]:
                continue
            got = _body(model.generate(mutated, max_new=budget))
            if got != base:
                if field == "v":
                    v_changed += 1
                else:
                    dt_changed += 1
    n = len(rows)
    return {
        "n": n,
        "v_changed": v_changed,
        "dt_changed": dt_changed,
        "v_share": round(v_changed / max(1, n), 3),
        "dt_share": round(dt_changed / max(1, n), 3),
    }


def _training_norms() -> Tuple[Dict[str, int], set]:
    """Normalized input texts of every prepared AI+AL train/val file."""
    texts: set = set()
    files: Dict[str, int] = {}
    for path in sorted(PROCESSED.glob("ai_al_*train*.jsonl")) + sorted(
        PROCESSED.glob("ai_al_*val*.jsonl")
    ):
        count = 0
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                inp = str(row.get("input") or "")
                texts.add(gen._norm(inp.split("|", 1)[-1]))
                count += 1
        files[path.name] = count
    return files, texts


# -- build ------------------------------------------------------------------


def build(
    total: int = 200,
    seed: int = 11,
    skip: int = 10000,
    window: int = 40000,
    cells: Optional[Dict[str, str]] = None,
    ref_intents: Sequence[str] = _REFERENCE_INTENTS,
    max_len: int = 192,
    min_per_cell: int = 10,
    decimals: int = 2,
) -> Dict[str, object]:
    """Build the holdout set (+ reference) as one deterministic JSON payload.

    The default region — accepted core_train rows [10000, 50000) — is chosen
    from the corpus layout: rows ≥80000 are all ``unknown`` and rows <10000
    were consumed by rounds 1-4, while this band still carries every intent
    (humor/greeting ≈ 40 rows per 10k). The probe re-checks overlap against
    the train/val files at evaluation time and reports it, so a later round
    that marches into this region shows up instead of silently inflating a
    reading.
    """
    chosen = dict(cells if cells is not None else gen.MVE1_HOLDOUT_CELLS)
    if not chosen:
        raise SystemExit("no holdout cells requested")
    baseline, targets, pilot_rows = gen._pilot_tables()
    source = gen._load_ai_rows(window, skip=skip)
    buckets: Dict[str, List[dict]] = {}
    for row in source:
        intent = gen._intent_of(row["input"])
        if intent in chosen:
            buckets.setdefault(intent, []).append(row)

    rng = random.Random(seed)
    quota = total // len(chosen)
    remainder = total - quota * len(chosen)
    holdout: List[dict] = []
    reference: List[dict] = []
    want: Dict[str, Tuple[int, int]] = {}
    got: Dict[str, Tuple[int, int]] = {}

    for idx, intent in enumerate(sorted(chosen)):
        want_h = quota + (1 if idx < remainder else 0)
        want_r = quota if intent in ref_intents else 0
        want[intent] = (want_h, want_r)
        h_mode, r_mode = chosen[intent], _ref_mode(chosen[intent])
        h_done = r_done = 0
        for row in buckets.get(intent, []):
            if h_done >= want_h and r_done >= want_r:
                break
            take_holdout = h_done < want_h
            mode = h_mode if take_holdout else r_mode
            state_in: Dict[str, object] = gen._sample_state(rng)
            state_in["routing_mode"] = mode
            text, response = row["input"], row["output"]
            # the rung is fixed by position (cycles 0..3), so adding dt cannot
            # touch the rng stream and every cell gets a balanced rung spread
            # (cell quotas are multiples of 4, cells are appended in order)
            slot = len(holdout) if take_holdout else len(reference)
            rung = slot % len(gen._DT_LADDER)
            dt = gen._DT_LADDER[rung]
            prompt_in = (
                prep._state_line(state_in, intent, "in", dt=dt, decimals=decimals) + " | " + text
            )
            prompt = (prompt_in + "\n" + response).strip()
            family = family_golds(state_in, intent, baseline, targets, decimals=decimals)
            gold = family[rung]
            if not pair_fits(prompt, gold, max_len):
                continue
            entry = {
                "sample_id": f"mve1{'h' if take_holdout else 'r'}_{slot:04d}",
                "cell": f"{intent}:{mode}",
                "intent": intent,
                "mode": mode,
                "prompt": prompt,
                "text": text,
                "response": response,
                "state_in": state_in,
                "family": family,
                "dt": dt,
                "rung": rung,
                "gold": gold,
            }
            if take_holdout:
                holdout.append(entry)
                h_done += 1
            else:
                reference.append(entry)
                r_done += 1
        got[intent] = (h_done, r_done)

    # every holdout cell must meet its quota and the readability floor; a
    # shortfall is a build error (silent shrinkage would change the gate N)
    short = {
        i: {
            "want": want[i][0],
            "got": got.get(i, (0, 0))[0],
            "reference_got": got.get(i, (0, 0))[1],
        }
        for i in sorted(chosen)
        if got.get(i, (0, 0))[0] < max(want[i][0], min_per_cell)
    }
    if short:
        raise SystemExit(
            f"holdout cell underfilled (raise --window, lower --total, or drop the cell): {short}"
        )

    files, norms = _training_norms()
    overlaps = sum(1 for e in holdout + reference if gen._norm(e["text"]) in norms)
    if overlaps:
        raise SystemExit(f"{overlaps} instrument rows already appear in ai_al train/val files")

    return {
        "version": "1.1.0",
        "description": (
            "MVE-1 emergence-boundary instrument: (intent x mode) compositional-holdout "
            "rows with dt in the prompt and a single-rung gold, plus seen-composition "
            "reference rows. Grade free-running <al_out> blocks exact (the four-rung "
            "family is the wrong-rung diagnostic); gate >=5/200 with the rotation "
            "control <=1/200 (MEASUREMENT_MAP MVE-1)."
        ),
        "seed": seed,
        "total": len(holdout),
        "reference_total": len(reference),
        "provenance": {
            "ai_source": str(gen.AI_SRC.relative_to(REPO_ROOT)),
            "ai_source_sha256": hashlib.sha256(gen.AI_SRC.read_bytes()).hexdigest(),
            "skip": skip,
            "window": window,
            "max_len": max_len,
            "pilot_rows": pilot_rows,
            "dt_ladder": list(gen._DT_LADDER),
            "dt_in_prompt": True,
            "gold_rule": "single rung: dt rides the input line, gold = family[rung]",
            "cells": chosen,
            "reference_intents": [i for i in sorted(chosen) if i in ref_intents],
            "reference_rule": "reference cell mode = first mode in _MODES != holdout mode",
            "carve_flag": "generate_al_dataset.py --holdout-cells (default off)",
            "training_files_scanned": files,
            "overlap_with_training": overlaps,
        },
        "holdout": holdout,
        "reference": reference,
    }


# -- probe ------------------------------------------------------------------


def _select(payload: Dict[str, object], which: str) -> List[dict]:
    if which == "holdout":
        return list(payload["holdout"])  # type: ignore[arg-type]
    if which == "reference":
        return list(payload["reference"])  # type: ignore[arg-type]
    if which == "all":
        return list(payload["holdout"]) + list(payload["reference"])  # type: ignore[arg-type]
    raise ValueError(which)


def _training_cell_rows(cells: Dict[str, str]) -> Dict[str, int]:
    """Rows in prepared train/val files that fall in a holdout cell."""
    counts: Dict[str, int] = {}
    for path in sorted(PROCESSED.glob("ai_al_*train*.jsonl")) + sorted(
        PROCESSED.glob("ai_al_*val*.jsonl")
    ):
        hits = 0
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                match = re.search(r"mode=(\S+) intent=(\S+)", line)
                if match and cells.get(match.group(2)) == match.group(1):
                    hits += 1
        if hits:
            counts[path.name] = hits
    return counts


def probe(
    checkpoint: str = "",
    set_file: Path = SET_OUT,
    which: str = "all",
    device: str = "auto",
    report: Path = REPORT_OUT,
    limit: int = 0,
    sensitivity_rows: int = 0,
    model: Any = None,
) -> int:
    """Grade one model against the instrument set.

    ``model`` exists so a *non-SNN* control (``compare_al_baselines.py``) is
    graded by the exact same code path: anything with ``vocab``,
    ``config.max_len``, ``device`` and ``generate(prompt, max_new)`` qualifies.
    Without it a baseline would need a second copy of the scoring logic, and
    two implementations of one measurement are two measurements.
    """
    if model is None:
        from ai.ed3n.token_snn import TokenSNN

        model = TokenSNN.load(checkpoint, device=device)

    payload = json.loads(Path(set_file).read_text(encoding="utf-8"))
    rows = _select(payload, which)
    if limit:
        rows = rows[:limit]
    if not rows:
        print(f"no rows selected from {set_file} ({which})")
        return 1

    started = time.time()
    max_len = model.config.max_len

    # exact window check against the real config (atom counts == encode length)
    bad = [
        e["sample_id"]
        for e in rows
        if not pair_fits(e["prompt"], e["gold"], max_len)
        or len(model.vocab.encode(e["prompt"])) > max_len - 1
    ]
    if bad:
        print(f"window violation for {len(bad)} rows (rebuild the set): {bad[:5]}")
        return 2

    n = len(rows)
    rot_of = rotation_index_map(rows)
    is_holdout = [_set_label(e) == "holdout" for e in rows]
    hits: List[bool] = []
    rot_hits: List[bool] = []
    format_ok = 0
    marker_ok = 0
    field_hits = {f: 0 for f in _FIELD_KEYS}
    rows_by_rung = {str(d): 0 for d in gen._DT_LADDER}
    hits_by_rung = {str(d): 0 for d in gen._DT_LADDER}
    dt_conditioning = {"exact_rung": 0, "wrong_rung": 0, "no_match": 0}
    # How many *different* blocks the model produced at all. A model that emits
    # the same near-constant block every time scores high on format/marker while
    # having learned nothing about the transition — round 6 read format_ok 316
    # that way and only per-sample inspection showed the collapse.
    blocks: Dict[str, int] = {}
    # the block *body* only (everything after ``<al_out>``): a model can vary a
    # leading answer/digits a lot while its state block stays fixed, so the two
    # must be counted separately before calling an output "constant".
    bodies: Dict[str, int] = {}
    # input-state -> generated-state, per field. Diversity alone cannot tell
    # "varies with the input" from "varies randomly"; a correlation near 0 in
    # every field means the block is not conditioned on <al_in> at all.
    io_pairs: Dict[str, Tuple[List[float], List[float]]] = {f: ([], []) for f in _FIELD_KEYS}
    # ``mode`` and ``intent`` are pass-through by contract (target mode/intent ==
    # the input's), so they are *copyable*: a model that ignores <al_in> still
    # emits a legal one, and only this count tells the two apart. Round 7 read
    # correlation 0 in all six fields while printing legal blocks — the question
    # then is "cannot regress" vs "does not read the input at all".
    copy_ok: Dict[str, int] = {"mode": 0, "intent": 0}
    per_cell: Dict[str, Dict[str, int]] = {}
    parsed_all = [[_parse_block(g) for g in e["family"]] for e in rows]
    first_gots: List[str] = []

    for i, entry in enumerate(rows):
        budget = min(max_len, len(model.vocab.encode(entry["gold"])) + 8)
        got = model.generate(entry["prompt"], max_new=budget)
        hit, _ = grade(got, [entry["gold"]])
        fam_hit, _ = grade(got, entry["family"])
        rot_hit, _ = grade(got, [rows[rot_of[i]]["gold"]])
        hits.append(hit)
        rot_hits.append(rot_hit)
        rung_key = str(gen._DT_LADDER[entry["rung"]])
        rows_by_rung[rung_key] += 1
        if hit:
            hits_by_rung[rung_key] += 1
        # exact = the matching rung; wrong_rung = a different legal rung (the
        # model had dt and ignored it); no_match = no legal block at all
        if hit:
            dt_conditioning["exact_rung"] += 1
        elif fam_hit:
            dt_conditioning["wrong_rung"] += 1
        else:
            dt_conditioning["no_match"] += 1

        blocks[got.strip()] = blocks.get(got.strip(), 0) + 1
        bodies[_body(got)] = bodies.get(_body(got), 0) + 1
        fields = _parse_block(got)
        keys = set(fields)
        if set(_FIELD_KEYS) <= keys and "mode" in keys and "intent" in keys:
            format_ok += 1
        if _MARKER in got:
            marker_ok += 1
        if i < 3:
            first_gots.append(got)
        for f in _FIELD_KEYS:
            gold_values = {p.get(f) for p in parsed_all[i]}
            if fields.get(f) in gold_values:
                field_hits[f] += 1
        in_fields = _parse_block(entry["prompt"])
        for token_name in copy_ok:
            if in_fields.get(token_name) == fields.get(token_name):
                copy_ok[token_name] += 1
        for f in _FIELD_KEYS:
            try:
                src = float(in_fields[f])
                dst = float(fields[f])
            except (KeyError, TypeError, ValueError):
                continue
            io_pairs[f][0].append(src)
            io_pairs[f][1].append(dst)
        cell = entry["cell"]
        bucket = per_cell.setdefault(cell, {"hits": 0, "n": 0})
        bucket["n"] += 1
        bucket["hits"] += int(hit)
        if (i + 1) % 20 == 0:
            print(
                f"[{i + 1}/{n}] exact={sum(hits)} rotation={sum(rot_hits)}",
                flush=True,
            )

    # a few raw generations for diagnosis (stored during the run, not re-run)
    samples = [
        {
            "sample_id": e["sample_id"],
            "cell": e["cell"],
            "dt": e["dt"],
            "prompt_tail": e["prompt"][-90:],
            "generated": got,
            "gold": e["gold"],
        }
        for e, got in zip(rows[:3], first_gots)
    ]
    # which rung a hit used + a few raw samples for diagnosis
    files_seen, norms = _training_norms()
    text_overlap = sum(1 for e in rows if gen._norm(e["text"]) in norms)
    cell_rows = _training_cell_rows(dict(payload["provenance"]["cells"]))  # type: ignore[arg-type]

    def _subset(sel: List[bool]) -> Dict[str, int]:
        return {
            "n": sum(sel),
            "family_hits": sum(h for h, s in zip(hits, sel) if s),
            "rotation_hits": sum(h for h, s in zip(rot_hits, sel) if s),
        }

    holdout_stats = _subset(is_holdout)
    reference_stats = _subset([not s for s in is_holdout])
    # the registered gate is read from the holdout rows only; a run without
    # them (--set reference) reports gate=null instead of borrowing them
    gate_result = (
        gate(holdout_stats["family_hits"], holdout_stats["rotation_hits"], holdout_stats["n"])
        if holdout_stats["n"]
        else None
    )

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "checkpoint": str(checkpoint),
        "device": str(model.device),
        "set_file": str(set_file),
        "set": which,
        "n": n,
        "holdout": holdout_stats,
        "reference": reference_stats,
        "gate": gate_result,
        "format_ok": format_ok,
        "marker_ok": marker_ok,
        "field_hits": field_hits,
        "rows_by_rung": rows_by_rung,
        "hits_by_rung": hits_by_rung,
        "dt_conditioning": dt_conditioning,
        "output_diversity": {
            "distinct": len(blocks),
            "modal_share": round(max(blocks.values(), default=0) / max(1, n), 4),
            "modal": (max(blocks.items(), key=lambda kv: kv[1])[0][:160] if blocks else ""),
            "body_distinct": len(bodies),
            "body_modal_share": round(max(bodies.values(), default=0) / max(1, n), 4),
            "body_modal": (max(bodies.items(), key=lambda kv: kv[1])[0][:160] if bodies else ""),
        },
        "input_output_correlation": {f: _pearson(xs, ys) for f, (xs, ys) in io_pairs.items()},
        "gold_input_correlation": _gold_correlation(rows),
        "learnability": _affine_ceiling(rows),
        "contract_form_ceiling": _contract_form_ceiling(rows),
        "copy_accuracy": {k: round(v / max(1, n), 4) for k, v in copy_ok.items()},
        "input_sensitivity": (
            _input_sensitivity(model, rows[:sensitivity_rows], max_len)
            if sensitivity_rows
            else None
        ),
        "per_cell": per_cell,
        "training_cell_rows": cell_rows,
        "cells_carved_from_training": not cell_rows,
        "samples": samples,
        "instrument_text_overlap": {"count": text_overlap, "files": len(files_seen)},
        "elapsed_s": round(time.time() - started, 1),
    }
    report = Path(report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    gate_line = (
        f"gate pass={gate_result['pass']} (>= {GATE_EXACT_MIN}, <= {GATE_CONTROL_MAX})"
        if gate_result
        else "gate=null (no holdout rows in this run)"
    )
    print(
        f"\nset={which} n={n} "
        f"holdout={holdout_stats['family_hits']}/{holdout_stats['n']} "
        f"rotation={holdout_stats['rotation_hits']}/{holdout_stats['n']} "
        f"reference={reference_stats['family_hits']}/{reference_stats['n']} "
        f"format_ok={format_ok} carved={result['cells_carved_from_training']}\n"
        f"dt_conditioning={dt_conditioning} rows_by_rung={rows_by_rung}\n"
        f"{gate_line}\nwrote {report}"
    )
    return 0


# -- cli --------------------------------------------------------------------


# -- value head -------------------------------------------------------------
#
# CORE_GAP §十九/§二十 separated three claims that a single 0/200 conflated:
# (a) the inputs are invisible, (b) the representation cannot hold them, (c)
# the *text decoder* cannot emit them. §二十 ruled out (a) — every input is in
# the prompt and a learned operator reaches 0.508 — and the arithmetic ruled
# out (c) as an exactness problem: the block is ~40 atoms, so per-token
# accuracy p gives p**40 per row, and p would have to be 0.99. This mode tests
# (b) directly: freeze the network, take its hidden state at the block start
# (the position that predicts the first block atom) and fit a head over the
# closed 201-atom value grid, one distribution per field. If a head on the
# frozen state reaches the contract ceiling, the information is there and only
# the text interface is wrong; if it reads 0, the recurrent state dropped the
# inputs and no decoder can help.
#
# The head is trained on the *training file* rows and scored on the instrument
# rows with the grader's own unit: state values are printed at 2 dp, so atom
# equality and "within 0.005" are the same event (any other atom is >= 0.01
# away). A linear head is fitted alongside as the affine floor — the head that
# can only express ``c + w·h`` should reproduce the 0.503 ceiling measured in
# §十九, which turns that number into a check on the instrument.

_VALUE_GRID: Tuple[str, ...] = tuple(f"{i / 100:.2f}" for i in range(-100, 101))


def _value_targets(vocab: Any, block: str) -> Optional[List[int]]:
    """Six grid indices (``v a d fatigue stress health``) or ``None``."""
    parsed = _parse_block(block)
    out: List[int] = []
    for field in _FIELD_KEYS:
        raw = parsed.get(field)
        idx = _VALUE_GRID.index(raw) if raw in _VALUE_GRID else -1
        if idx < 0 or raw not in vocab.stoi:
            return None
        out.append(idx)
    return out


def _train_value_pairs(path: Path, limit: int = 24000) -> List[Tuple[str, str, str]]:
    """``(prompt, gold block, intent)`` from the training jsonl.

    The prompt is the training prefix up to the block — ``<al_in>`` line, the
    source text and the *gold* response — because that is what the model was
    trained to condition the block on (§probe docstring point 2).
    """
    pairs: List[Tuple[str, str, str]] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if limit and len(pairs) >= limit:
                break
            row = json.loads(line)
            output = str(row.get("output", ""))
            if _MARKER not in output:
                continue
            body, block = output.split(_MARKER, 1)
            intent = _parse_block(str(row.get("input", ""))).get("intent", "?")
            prompt = str(row["input"]).strip() + "\n" + body.strip()
            pairs.append((prompt, (_MARKER + block).strip(), intent))
    return pairs


_HEAD_POSITIONS = ("values_end", "input_line_end", "block_start")


def _position_index(model: Any, prompt: str, start: int, position: str, width: int) -> int:
    """Where in the sequence a head reads the state.

    ``input_line_end`` is the last atom of the ``<al_in>`` line — the state that
    has just read the six values. ``block_start`` is the first answer atom, i.e.
    the state the language model actually decodes from, ~100 atoms of response
    later. Reading both separates "the state never had it" from "the state lost
    it": a head that works at the first and fails at the second is a retention
    failure, not a decoder failure.
    """
    if position == "block_start":
        idx = start
    elif position == "values_end":
        # the six values, dt and intent sit left of the " | " that starts the
        # source text, so this is the state that has *just* read them
        idx = len(model.vocab.encode(str(prompt).split(" | ", 1)[0]))
    elif position == "input_line_end":
        # ids are [bos] + atoms(prompt), so the state after the L-th first-line
        # atom sits at index L (bos occupies 0)
        idx = len(model.vocab.encode(str(prompt).split("\n", 1)[0]))
    else:
        raise SystemExit(f"unknown head position {position!r}")
    return min(max(idx, 0), width - 1)


def _block_features(
    model: Any, pairs: Sequence[str], position: str = "block_start", batch: int = 32
) -> Any:
    """Pre-head hidden state at ``position`` for each prompt, as (N, d).

    The head's own input is captured with a forward hook, so the network is used
    exactly as trained (same forward, same readout, same normalisation) and
    nothing in ``token_snn`` grows a diagnostic-only API.
    """
    torch = model.torch
    # the head is called once per timestep, so the hook collects a list that has
    # to be stacked along time into (batch, steps, hidden)
    steps: List[Any] = []
    handle = model.net.head.register_forward_hook(lambda _m, inputs, _out: steps.append(inputs[0]))
    rows: List[Any] = []
    try:
        for i in range(0, len(pairs), batch):
            chunk = list(pairs[i : i + batch])
            encoded = [model._encode(p, _MARKER) for p in chunk]
            width = max(len(ids) for ids, _, _ in encoded)
            ids_t = torch.full(
                (len(chunk), width), model.vocab.pad_id, dtype=torch.long, device=model.device
            )
            for r, (ids, _start, _end) in enumerate(encoded):
                ids_t[r, : len(ids)] = torch.tensor(ids, dtype=torch.long, device=model.device)
            steps.clear()
            with torch.no_grad():
                model.net(ids_t)
            hidden = torch.stack(steps, dim=1)
            for r, (_ids, start, _end) in enumerate(encoded):
                idx = _position_index(model, chunk[r], start, position, hidden.shape[1])
                rows.append(hidden[r, idx].detach().float())
    finally:
        handle.remove()
    return torch.stack(rows)


def _fit_value_head(
    model: Any,
    x_train: Any,
    y_train: Any,
    x_eval: Any,
    hidden: int,
    steps: int = 3000,
    batch: int = 128,
    lr: float = 2e-3,
    seed: int = 7,
) -> Tuple[Any, Any]:
    """Fit one head over the frozen state; return (argmax, expectation).

    Exact-atom accuracy is the grader's unit but a coarse one: with 201 classes
    over [-1, 1] a head with 0.2 MAE still lands exactly about 2% of the time.
    The softmax expectation gives a continuous reading (MAE / R2) so "the state
    carries the value weakly" cannot be mistaken for "the state is empty".
    """
    torch = model.torch
    nn = torch.nn
    torch.manual_seed(seed)
    d_in = int(x_train.shape[1])
    n_cls = len(_VALUE_GRID)
    layers: List[Any] = [nn.LayerNorm(d_in)]
    if hidden:
        layers += [nn.Linear(d_in, hidden), nn.GELU(), nn.Dropout(0.1)]
    layers.append(nn.Linear(hidden or d_in, len(_FIELD_KEYS) * n_cls))
    head = nn.Sequential(*layers).to(model.device)
    opt = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=1e-4)
    n_train = x_train.shape[0]
    # Steps, not epochs: 40 epochs of 2611 rows at batch 512 is 240 updates,
    # which cannot move a 1206-logit head at all. The target is gathered as
    # y[idx].reshape(-1) — the earlier flat gather indexed rows by *row id*,
    # so the head learned "which row am I", read 0.05 nats and scored 0.
    for _step in range(steps):
        idx = torch.randint(0, n_train, (min(batch, n_train),), device=model.device)
        logits = head(x_train[idx]).reshape(-1, n_cls)
        loss = torch.nn.functional.cross_entropy(logits, y_train[idx].reshape(-1))
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    with torch.no_grad():
        logits = head(x_eval).reshape(-1, len(_FIELD_KEYS), n_cls)
        grid = torch.tensor(
            [(i - 100) / 100.0 for i in range(n_cls)], device=logits.device, dtype=logits.dtype
        )
        expected = (logits.softmax(dim=-1) * grid).sum(dim=-1)
        return logits.argmax(dim=-1), expected


def _score_value_preds(
    argmax: Any,
    expected: Any,
    targets: Any,
    labels: Sequence[Dict[str, object]],
) -> Dict[str, Any]:
    """Per-field, per-row and per-group accuracy, in continuous and exact units."""
    p = argmax.cpu().tolist()
    e = expected.cpu().tolist()
    t = targets.cpu().tolist()
    n_fields = len(_FIELD_KEYS)
    field_hits = [0] * n_fields
    row_hits = 0
    groups: Dict[str, List[int]] = {}
    for i, (row, gold) in enumerate(zip(p, t)):
        ok = [row[f] == gold[f] for f in range(n_fields)]
        for f, hit in enumerate(ok):
            field_hits[f] += int(hit)
        hit = all(ok)
        row_hits += int(hit)
        key = f"{labels[i]['set']}/{labels[i]['intent']}"
        groups.setdefault(key, [0, 0])
        groups[key][0] += int(hit)
        groups[key][1] += 1
    n = max(1, len(p))
    gold_vals = [[(row[f] - 100) / 100.0 for f in range(n_fields)] for row in t]
    out: Dict[str, Any] = {
        "n": len(p),
        "field_top1": {f: round(h / n, 4) for f, h in zip(_FIELD_KEYS, field_hits)},
        "row_exact": round(row_hits / n, 4),
        "row_hits": row_hits,
        "by_group": {k: {"hits": v[0], "n": v[1]} for k, v in sorted(groups.items())},
    }
    mae: Dict[str, float] = {}
    r2: Dict[str, float] = {}
    within_02: Dict[str, float] = {}
    for f, field in enumerate(_FIELD_KEYS):
        gold_f = [g[f] for g in gold_vals]
        pred_f = [row[f] for row in e]
        mae[field] = round(sum(abs(a - b) for a, b in zip(pred_f, gold_f)) / n, 4)
        mean_g = sum(gold_f) / n
        ss_tot = sum((g - mean_g) ** 2 for g in gold_f)
        ss_res = sum((a - b) ** 2 for a, b in zip(pred_f, gold_f))
        r2[field] = round(1 - ss_res / ss_tot, 4) if ss_tot > 1e-9 else 0.0
        within_02[field] = round(
            sum(1 for a, b in zip(pred_f, gold_f) if abs(a - b) <= 0.02) / n, 4
        )
    out["field_mae"] = mae
    out["field_r2"] = r2
    out["field_within_02"] = within_02
    return out


def _copy_baseline(rows: Sequence[dict]) -> Dict[str, Any]:
    """``out = in`` per field — the floor any head has to beat.

    The gold relaxes *towards* a per-intent constant, so the input values alone
    already explain much of the gold variance (0.74-0.84 correlation). A head
    reading R2 below this line is not using the inputs at all, however its
    exact-atom count reads.
    """
    mae: Dict[str, float] = {}
    r2: Dict[str, float] = {}
    n = max(1, len(rows))
    for field in _FIELD_KEYS:
        ins: List[float] = []
        golds: List[float] = []
        for entry in rows:
            raw_in = _parse_input_line(str(entry["prompt"])).get(field)
            raw_gold = _parse_block(str(entry["gold"])).get(field)
            if raw_in is None or raw_gold is None:
                continue
            ins.append(float(raw_in))
            golds.append(float(raw_gold))
        m = max(1, len(ins))
        mae[field] = round(sum(abs(a - b) for a, b in zip(ins, golds)) / m, 4)
        mean_g = sum(golds) / m
        ss_tot = sum((g - mean_g) ** 2 for g in golds)
        ss_res = sum((a - b) ** 2 for a, b in zip(ins, golds))
        r2[field] = round(1 - ss_res / ss_tot, 4) if ss_tot > 1e-9 else 0.0
    return {"n": n, "field_mae": mae, "field_r2": r2}


def _contract_feature_ridge(train_ok: Sequence[tuple], rows: Sequence[dict]) -> Dict[str, Any]:
    """Ridge on the six *parsed* input values + dt + intent, closed form.

    The control for the whole mode: it shows what a statistical estimator can do
    when it is handed the contract fields directly, with no recurrence in the
    way. If this reaches a good R2 but still no exact rows, then exactness — not
    information, not representation — is what the gate is asking for.
    """
    import torch

    intents = sorted({i for _p, _g, i in train_ok} | {str(e.get("intent", "?")) for e in rows})

    def feats(prompt: str) -> List[float]:
        parsed = _parse_input_line(prompt)
        vec = [float(parsed.get(k, 0.0)) for k in _FIELD_KEYS]
        vec.append(float(parsed.get("dt", 0.0)))
        vec.extend(1.0 if parsed.get("intent") == i else 0.0 for i in intents)
        return vec

    def gold_vecs(blocks: Sequence[str]) -> Any:
        return torch.tensor(
            [[float(_parse_block(b).get(k, 0.0)) for k in _FIELD_KEYS] for b in blocks],
            dtype=torch.float32,
        )

    x_train = torch.tensor([feats(p) for p, _g, _i in train_ok], dtype=torch.float32)
    x_eval = torch.tensor([feats(str(e["prompt"])) for e in rows], dtype=torch.float32)
    y_train = gold_vecs([g for _p, g, _i in train_ok])
    y_eval = gold_vecs([str(e["gold"]) for e in rows])
    xt = torch.cat([x_train, torch.ones(len(x_train), 1)], dim=1)
    lam = 0.01
    w = torch.linalg.solve(xt.T @ xt + lam * torch.eye(xt.shape[1]), xt.T @ y_train)
    pred = torch.cat([x_eval, torch.ones(len(x_eval), 1)], dim=1) @ w
    err = (pred - y_eval).abs()
    r2: Dict[str, float] = {}
    mae: Dict[str, float] = {}
    within: Dict[str, float] = {}
    for f, field in enumerate(_FIELD_KEYS):
        e = err[:, f]
        ss_res = float(((pred[:, f] - y_eval[:, f]) ** 2).sum())
        ss_tot = float(((y_eval[:, f] - y_eval[:, f].mean()) ** 2).sum())
        r2[field] = round(1 - ss_res / ss_tot, 4) if ss_tot > 1e-9 else 0.0
        mae[field] = round(float(e.mean()), 4)
        within[field] = round(float((e <= 0.02).float().mean()), 4)
    exact = (err <= 0.005).all(dim=1)
    return {
        "n_train": len(train_ok),
        "n_eval": len(rows),
        "features": [*_FIELD_KEYS, "dt", f"intent({len(intents)})"],
        "field_r2": r2,
        "field_mae": mae,
        "field_within_02": within,
        "row_exact": round(float(exact.float().mean()), 4),
        "row_hits": int(exact.sum()),
    }


def _contract_rows(rows: Sequence[dict]) -> List[Dict[str, Any]]:
    """``{state, gold, dt, intent}`` for every row that carries six values."""
    parsed: List[Dict[str, Any]] = []
    for entry in rows:
        state = _parse_input_line(str(entry.get("prompt", "")))
        gold = _parse_block(str(entry.get("gold", "")))
        try:
            parsed.append(
                {
                    "state": {f: float(state[f]) for f in _FIELD_KEYS},
                    "gold": {f: float(gold[f]) for f in _FIELD_KEYS},
                    "dt": float(state["dt"]),
                    "intent": str(state.get("intent") or ""),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return parsed


def _solve_operator_constants(
    parsed: Sequence[Dict[str, Any]], tau: float
) -> Dict[Tuple[str, str], float]:
    """Closed-form per-(intent, field) constants for a fixed tau.

    ``out = c + (in - c)·k`` is *linear in c*, so for a fixed tau the constants
    are a least-squares solve, not an optimisation: ``c = Σ a·b / Σ a²`` with
    ``a = 1-k`` and ``b = gold - k·in``. Weights ``1/(1+k²)`` are the inverse
    variance of that residual, because the input's own printing error arrives
    multiplied by k. Gradient descent reaches the same 19 numbers only up to its
    convergence floor — which is exactly the ~0.002 the head was missing rows by.
    """
    acc: Dict[Tuple[str, str], List[float]] = {}
    for row in parsed:
        k = math.exp(-row["dt"] / tau)
        w = 1.0 / (1.0 + k * k)
        a = 1.0 - k
        for f in _FIELD_KEYS:
            key = (row["intent"], f)
            num, den = acc.get(key, (0.0, 0.0))
            acc[key] = (
                num + w * a * (row["gold"][f] - k * row["state"][f]),
                den + w * a * a,
            )
    constants: Dict[Tuple[str, str], float] = {}
    for key, (num, den) in acc.items():
        if den > 1e-12:
            constants[key] = num / den
    return constants


def _operator_mse(
    parsed: Sequence[Dict[str, Any]], constants: Dict[Tuple[str, str], float], tau: float
) -> float:
    """Train-side error, used to pick tau. MSE, not exact: exact is quantised."""
    total = 0.0
    n = 0
    for row in parsed:
        known = (row["intent"], _FIELD_KEYS[0]) in constants
        if not known:
            continue
        k = math.exp(-row["dt"] / tau)
        for f in _FIELD_KEYS:
            c = constants[(row["intent"], f)]
            pred = c + (row["state"][f] - c) * k
            total += (pred - row["gold"][f]) ** 2
            n += 1
    return total / n if n else float("inf")


def _fit_operator_head(
    train_ok: Sequence[tuple],
    epochs: int = 800,
    lr: float = 0.05,
    seed: int = 0,
    solver: str = "ls",
) -> Optional[Dict[str, Any]]:
    """Learn the contract operator's 19 parameters by gradient descent.

    The value interface, not the text interface: the block is six numbers and
    the contract's own form is ``c[intent][f] + (in[f] - c[intent][f])·e^(-dt/tau)``
    (§5) — 18 per-intent constants plus one tau. Those 19 numbers are the only
    thing the data has to supply; the exponential and the rounding are exact
    arithmetic. Fitting them by GD (rather than the closed-form inversion the
    ``--ceiling`` mode uses) is what makes this a *learned* decoder instead of
    an analysis: 2611 rows train 19 parameters, where the token LM trains 1.24M
    parameters to emit the same block as 40 atoms.
    """
    try:
        import torch
    except ImportError:
        return None
    parsed = _contract_rows([{"prompt": p, "gold": g} for p, g, _i in train_ok])
    if not parsed:
        return None
    intents = sorted({r["intent"] for r in parsed if r["intent"]})
    index = {name: i for i, name in enumerate(intents)}
    rows = [r for r in parsed if r["intent"] in index]
    if not rows:
        return None
    if solver == "ls":
        # exact for a fixed tau, so tau is the only thing left to search
        best = None
        for tau in _TAU_GRID:
            constants = _solve_operator_constants(rows, tau)
            if not constants:
                continue
            mse = _operator_mse(rows, constants, tau)
            if best is None or mse < best[0]:
                best = (mse, tau, constants)
        if best is None:
            return None
        _mse, tau, table = best
        return {
            "constants": table,
            "tau": round(tau, 4),
            "intents": intents,
            "train_rows": len(rows),
            "solver": "ls",
            "train_mse": round(_mse, 6),
        }
    torch.manual_seed(seed)
    x = torch.tensor([[r["state"][f] for f in _FIELD_KEYS] for r in rows], dtype=torch.float32)
    y = torch.tensor([[r["gold"][f] for f in _FIELD_KEYS] for r in rows], dtype=torch.float32)
    dt = torch.tensor([r["dt"] for r in rows], dtype=torch.float32)
    who = torch.tensor([index[r["intent"]] for r in rows], dtype=torch.long)
    # warm start on the per-intent mean gold: the operator relaxes *towards* c,
    # so that mean is already the right neighbourhood and 19 parameters do not
    # have to find the scale of the data from zero
    c0 = torch.zeros(len(intents), len(_FIELD_KEYS))
    for i in range(len(intents)):
        mask = who == i
        if bool(mask.any()):
            c0[i] = y[mask].mean(dim=0)
    constants = c0.clone().requires_grad_(True)
    log_tau = torch.tensor(0.0, requires_grad=True)  # softplus(0) = 0.69
    opt = torch.optim.Adam([constants, log_tau], lr=lr)
    for _epoch in range(epochs):
        tau = torch.nn.functional.softplus(log_tau) + 1e-4
        k = torch.exp(-dt / tau).unsqueeze(1)
        pred = constants[who] + (x - constants[who]) * k
        loss = ((pred - y) ** 2).mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    tau = float(torch.nn.functional.softplus(log_tau).detach()) + 1e-4
    table = {
        (name, f): float(constants[i, j])
        for name, i in index.items()
        for j, f in enumerate(_FIELD_KEYS)
    }
    return {
        "constants": table,
        "tau": round(tau, 4),
        "intents": intents,
        "train_rows": len(rows),
        "solver": "gd",
    }


def _operator_head_report(
    model: Any,
    rows: Sequence[dict],
    train_path: Path,
    epochs: int = 800,
    solver: str = "ls",
) -> Dict[str, Any]:
    """Fit the operator on the training file and grade it on the instrument."""
    # The atom grid gates the *text* interface: a block whose values are off the
    # tokenizer's grid cannot be emitted at all. This head reads the six floats
    # directly, so gating it on the vocab would make a 3dp corpus unlearnable by
    # construction — the gate would be the reason, not the data. Counted, kept.
    pairs = _train_value_pairs(train_path)
    expressible = sum(1 for _p, g, _i in pairs if _value_targets(model.vocab, g) is not None)
    train_ok = pairs
    fitted = _fit_operator_head(train_ok, epochs=epochs, solver=solver)
    if fitted is None:
        raise SystemExit("operator head unavailable (torch missing or no training rows)")
    holdout = _contract_rows([e for e in rows if _set_label(e) == "holdout"])
    reference = _contract_rows([e for e in rows if _set_label(e) != "holdout"])
    scored_all = _contract_rows(rows)
    hold = _score_contract_rows(holdout, fitted["constants"], fitted["tau"])
    ref = _score_contract_rows(reference, fitted["constants"], fitted["tau"])
    # the contract's intent table is a runtime lookup (§5), not a learned weight,
    # so score the unseen-intent rows twice: learned only, and with the table
    table = _contract_table()
    # both solvers on the same rows and the same grader: the closed form is exact
    # for a fixed tau, GD stops wherever its convergence happens to land
    comparison: Dict[str, Any] = {}
    for name in ("ls", "gd"):
        other = (
            fitted if name == solver else _fit_operator_head(train_ok, epochs=epochs, solver=name)
        )
        if other is None:
            continue
        scored = _score_contract_rows(
            holdout, other["constants"], other["tau"], targets=table[0] if table else None
        )
        comparison[name] = {
            "tau": other["tau"],
            "hits": round(scored["row_exact_all_intents"] * scored["rows"]),
            "hits_rounding_aware": round(
                scored["row_exact_all_intents_rounding_aware"] * scored["rows"]
            ),
            "rows": scored["rows"],
        }
    hold_table = (
        _score_contract_rows(holdout, fitted["constants"], fitted["tau"], targets=table[0])
        if table
        else None
    )
    ref_table = (
        _score_contract_rows(reference, fitted["constants"], fitted["tau"], targets=table[0])
        if table
        else None
    )
    ceiling = _structural_ceiling(holdout, table[0], table[1], fitted["tau"]) if table else None
    ceiling_seen = (
        _structural_ceiling(
            [r for r in holdout if (r["intent"], _FIELD_KEYS[0]) in fitted["constants"]],
            table[0],
            table[1],
            fitted["tau"],
        )
        if table
        else None
    )
    hits = round(hold["row_exact_of_all"] * hold["rows"])
    hits_table = (
        round(hold_table["row_exact_all_intents"] * hold_table["rows"]) if hold_table else 0
    )
    hits_aware = (
        round(hold_table["row_exact_all_intents_rounding_aware"] * hold_table["rows"])
        if hold_table
        else 0
    )
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "interface": "value (six numbers per block), not text (40 atoms)",
        "params": 1 + 6 * len(fitted["intents"]),
        "tau": fitted["tau"],
        "intents": fitted["intents"],
        "train_rows": fitted["train_rows"],
        "constants": {f"{i}/{f}": round(v, 4) for (i, f), v in sorted(fitted["constants"].items())},
        "solver": fitted.get("solver", solver),
        "solver_comparison": comparison,
        "train_rows_atom_expressible": expressible,
        "holdout": hold,
        "holdout_with_contract_table": hold_table,
        "reference": ref,
        "reference_with_contract_table": ref_table,
        "structural_ceiling": ceiling,
        "structural_ceiling_seen_intents": ceiling_seen,
        "gate": gate(hits, 0, hold["rows"]),
        "gate_with_contract_table": gate(hits_table, 0, hold["rows"]),
        "gate_with_contract_table_rounding_aware": gate(hits_aware, 0, hold["rows"]),
        "checkpoint": str(getattr(model, "path", "")),
        "elapsed_note": f"scored {len(scored_all)} rows",
    }


def _value_head_report(
    model: Any,
    rows: Sequence[dict],
    train_path: Path,
    steps: int = 3000,
    train_limit: int = 24000,
) -> Dict[str, Any]:
    """Fit heads on the training file over the frozen state, then score the set."""
    pairs = _train_value_pairs(train_path, limit=train_limit)
    if not pairs:
        raise SystemExit(f"no training pairs with {_MARKER} in {train_path}")
    train_ok = [(p, g, i) for p, g, i in pairs if _value_targets(model.vocab, g) is not None]
    train_intents = {i for _p, _g, i in train_ok}
    eval_rows = [e for e in rows if _value_targets(model.vocab, str(e.get("gold", ""))) is not None]
    if not eval_rows:
        raise SystemExit("no instrument row carries six gradable values")

    torch = model.torch
    y_train = torch.tensor(
        [_value_targets(model.vocab, g) for _p, g, _i in train_ok],
        dtype=torch.long,
        device=model.device,
    )
    y_eval = torch.tensor(
        [_value_targets(model.vocab, str(e["gold"])) for e in eval_rows],
        dtype=torch.long,
        device=model.device,
    )
    y_gold_list = y_eval.tolist()
    labels = [
        {
            "set": _set_label(e),
            "intent": str(e.get("intent", "?")),
            "seen_intent": str(e.get("intent", "?")) in train_intents,
        }
        for e in eval_rows
    ]
    out: Dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "checkpoint": str(getattr(model, "path", "")),
        "device": str(model.device),
        "train_file": str(train_path),
        "train_rows": len(train_ok),
        "train_intents": sorted(train_intents),
        "eval_rows": len(eval_rows),
        "eval_seen_intent_rows": sum(1 for lab in labels if lab["seen_intent"]),
        "readout": "pre-head hidden state, read at each position below",
        "unit": "atom equality over the 201-value grid == grader +/-0.005 at 2dp",
        "contract_ceiling_reference": 0.508,
        "copy_baseline": _copy_baseline(eval_rows),
        "contract_feature_reference": _contract_feature_ridge(train_ok, eval_rows),
        "leak": round(float(torch.sigmoid(model.net.beta)), 4),
        "leak_memory_atoms": round(1.0 / max(1e-6, 1 - float(torch.sigmoid(model.net.beta))), 1),
    }
    prompts_train = [p for p, _g, _i in train_ok]
    prompts_eval = [str(e["prompt"]) for e in eval_rows]
    seen = [i for i, lab in enumerate(labels) if lab["seen_intent"]]
    positions: Dict[str, Any] = {}
    for position in _HEAD_POSITIONS:
        x_train = _block_features(model, prompts_train, position=position)
        x_eval = _block_features(model, prompts_eval, position=position)
        entry_out: Dict[str, Any] = {}
        argmax_by_head: Dict[str, Any] = {}
        for name, hidden in (("mlp", 256), ("linear", 0)):
            argmax, expected = _fit_value_head(
                model, x_train, y_train, x_eval, hidden=hidden, steps=steps
            )
            argmax_by_head[name] = argmax
            entry_out[name] = _score_value_preds(argmax, expected, y_eval, labels)
        if seen and len(seen) < len(labels):
            # the unattainable population (intents never in training) must not
            # be averaged into the reachable one: §二十 measured 80/200 rows
            entry_out["mlp_seen_only_row_exact"] = round(
                sum(1 for i in seen if argmax_by_head["mlp"][i].tolist() == y_gold_list[i])
                / len(seen),
                4,
            )
        positions[position] = entry_out
    out["positions"] = positions
    return out


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true", help="build the instrument set (default)")
    ap.add_argument("--check", action="store_true", help="rebuild in memory; fail if it differs")
    ap.add_argument("--probe", action="store_true", help="run a checkpoint against the set")
    ap.add_argument("--checkpoint", default="", help="TokenSNN checkpoint for --probe")
    ap.add_argument("--set", dest="which", choices=("holdout", "reference", "all"), default="all")
    ap.add_argument("--limit", type=int, default=0, help="probe only the first N rows (debug)")
    ap.add_argument(
        "--sensitivity-rows",
        type=int,
        default=0,
        help="perturb one <al_in> field on the first N rows and count block changes "
        "(3 generations per row; off by default)",
    )
    ap.add_argument("--device", default="auto", help="auto | xpu | cuda | cpu")
    ap.add_argument("--total", type=int, default=GATE_N, help="holdout rows (gate N)")
    ap.add_argument(
        "--decimals",
        type=int,
        default=2,
        help="decimal places in the instrument's <al_in>/<al_out> lines (default 2: the "
        "rounds the checkpoints trained on; 3 makes the +/-0.005 grader decidable)",
    )
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--skip", type=int, default=10000, help="corpus rows no round has used")
    ap.add_argument("--window", type=int, default=40000, help="rows scanned after --skip")
    ap.add_argument("--max-len", type=int, default=192, help="training window (TokenConfig)")
    ap.add_argument("--out", default=str(SET_OUT))
    ap.add_argument(
        "--report",
        default=None,
        help="report destination; default is one file per mode under data/intelligence_reports "
        "(mve1_operator_head.json, mve1_value_head.json, ...)",
    )
    ap.add_argument(
        "--ceiling",
        action="store_true",
        help="no checkpoint: print the contract-form ceiling (constants learned "
        "from the training pairs, operator applied to the set) and write it to "
        "data/intelligence_reports/mve1_contract_form_ceiling.json. This is the "
        "number 0/200 should be read against.",
    )
    ap.add_argument(
        "--value-head",
        action="store_true",
        help="fit a 201-atom head per field on the frozen network's hidden state at "
        "the block start (trained on --train, scored on the set) and write "
        'data/intelligence_reports/mve1_value_head.json. Separates "the state '
        'cannot hold the values" from "the text decoder cannot emit them".',
    )
    ap.add_argument("--head-steps", type=int, default=3000, help="optimiser steps per value head")
    ap.add_argument(
        "--operator-head",
        action="store_true",
        help="learn the contract operator's 18 constants + tau by gradient descent on "
        "--train and grade the block on the value interface (writes "
        "data/intelligence_reports/mve1_operator_head.json). This is the interface the "
        "measurements say is passable: ~19 parameters over exact arithmetic.",
    )
    ap.add_argument("--train-rows", type=int, default=24000, help="training rows for --value-head")
    ap.add_argument("--train", default=str(DEFAULT_TRAIN), help="pairs for --ceiling")
    args = ap.parse_args(argv)

    if args.ceiling:
        payload = json.loads(Path(args.out).read_text(encoding="utf-8"))
        ceiling = _contract_form_ceiling(_select(payload, args.which), Path(args.train))
        if ceiling is None:
            print(f"ceiling unavailable (missing rows or {args.train})")
            return 1
        payload = {"set": str(args.out), "train": str(args.train), **ceiling}
        out_path = (
            Path(args.report)
            if args.report
            else REPORT_OUT.parent / "mve1_contract_form_ceiling.json"
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0

    if args.probe:
        if not args.checkpoint:
            ap.error("--probe requires --checkpoint")
        return probe(
            args.checkpoint,
            set_file=Path(args.out),
            which=args.which,
            device=args.device,
            report=Path(args.report) if args.report else REPORT_OUT,
            limit=args.limit,
            sensitivity_rows=args.sensitivity_rows,
        )

    if args.operator_head:
        if not args.checkpoint:
            ap.error("--operator-head requires --checkpoint")
        from ai.ed3n.token_snn import TokenSNN

        payload = json.loads(Path(args.out).read_text(encoding="utf-8"))
        model = TokenSNN.load(args.checkpoint, device="cpu")
        model.path = args.checkpoint
        report = _operator_head_report(
            model, _select(payload, args.which), Path(args.train), epochs=args.head_steps
        )
        out_path = (
            Path(args.report) if args.report else REPORT_OUT.parent / "mve1_operator_head.json"
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: report[k] for k in ("tau", "params", "holdout", "gate")}, indent=2))
        print(f"wrote {out_path}")
        return 0

    if args.value_head:
        if not args.checkpoint:
            ap.error("--value-head requires --checkpoint")
        from ai.ed3n.token_snn import TokenSNN

        payload = json.loads(Path(args.out).read_text(encoding="utf-8"))
        model = TokenSNN.load(args.checkpoint, device=args.device)
        model.path = args.checkpoint
        rows = _select(payload, args.which)
        if args.limit:
            rows = rows[: args.limit]
        report = _value_head_report(
            model,
            rows,
            train_path=Path(args.train),
            steps=args.head_steps,
            train_limit=args.train_rows,
        )
        out_path = Path(args.report) if args.report else REPORT_OUT.parent / "mve1_value_head.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in report.items() if k != "by_group"}, indent=2))
        print(f"wrote {out_path}")
        return 0

    built = build(
        total=args.total,
        seed=args.seed,
        skip=args.skip,
        window=args.window,
        max_len=args.max_len,
        decimals=args.decimals,
    )
    body = json.dumps(built, indent=2, ensure_ascii=False) + "\n"
    out = Path(args.out)
    if args.check:
        if not out.exists():
            print(f"check failed: missing {out.name}")
            return 1
        if out.read_text(encoding="utf-8") != body:
            # The rows are the instrument. ``training_files_scanned`` is a
            # property of the data directory at build time, so a new round file
            # landing there must not turn an unchanged instrument into a failed
            # check — but it is still reported, because it is the leak scan.
            try:
                on_disk = json.loads(out.read_text(encoding="utf-8"))
            except ValueError:
                print(f"check failed: {out.name} is not valid JSON")
                return 1
            strip = lambda d: {  # noqa: E731
                **{k: v for k, v in d.items() if k != "provenance"},
                "provenance": {
                    k: v
                    for k, v in (d.get("provenance") or {}).items()
                    if k != "training_files_scanned"
                },
            }
            if strip(on_disk) != strip(built):
                print(f"check failed: {out.name} differs from a fresh build")
                return 1
            before = (on_disk.get("provenance") or {}).get("training_files_scanned")
            after = built["provenance"]["training_files_scanned"]
            print(
                f"check ok (rows identical): {built['total']} holdout + "
                f"{built['reference_total']} reference; leak scan now covers "
                f"{len(after)} files (was {len(before or {})}), "
                f"overlap {built['provenance']['overlap_with_training']}"
            )
            return 0
        print(f"check ok: {built['total']} holdout + {built['reference_total']} reference")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    print(
        f"holdout={built['total']} reference={built['reference_total']} "
        f"cells={sorted(built['provenance']['cells'])} "
        f"skip={built['provenance']['skip']} window={built['provenance']['window']}\n"
        f"wrote {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
