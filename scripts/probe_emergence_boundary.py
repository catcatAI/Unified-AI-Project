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
import random
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

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
) -> List[str]:
    """The four legal targets for one input: one per dt rung (decision 1)."""
    target = targets.get(intent, baseline)
    mode = str(state_in["routing_mode"])
    golds: List[str] = []
    for dt in gen._DT_LADDER:
        out: Dict[str, object] = dict(gen.transition(state_in, target, dt))  # type: ignore[arg-type]
        out["routing_mode"] = mode  # carried: 10/10 pilot rows keep it
        golds.append(prep._state_line(out, intent, "out"))
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
            prompt_in = prep._state_line(state_in, intent, "in", dt=dt) + " | " + text
            prompt = (prompt_in + "\n" + response).strip()
            family = family_golds(state_in, intent, baseline, targets)
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
    checkpoint: str,
    set_file: Path = SET_OUT,
    which: str = "all",
    device: str = "auto",
    report: Path = REPORT_OUT,
    limit: int = 0,
) -> int:
    from ai.ed3n.token_snn import TokenSNN

    payload = json.loads(Path(set_file).read_text(encoding="utf-8"))
    rows = _select(payload, which)
    if limit:
        rows = rows[:limit]
    if not rows:
        print(f"no rows selected from {set_file} ({which})")
        return 1

    started = time.time()
    model = TokenSNN.load(checkpoint, device=device)
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


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true", help="build the instrument set (default)")
    ap.add_argument("--check", action="store_true", help="rebuild in memory; fail if it differs")
    ap.add_argument("--probe", action="store_true", help="run a checkpoint against the set")
    ap.add_argument("--checkpoint", default="", help="TokenSNN checkpoint for --probe")
    ap.add_argument("--set", dest="which", choices=("holdout", "reference", "all"), default="all")
    ap.add_argument("--limit", type=int, default=0, help="probe only the first N rows (debug)")
    ap.add_argument("--device", default="auto", help="auto | xpu | cuda | cpu")
    ap.add_argument("--total", type=int, default=GATE_N, help="holdout rows (gate N)")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--skip", type=int, default=10000, help="corpus rows no round has used")
    ap.add_argument("--window", type=int, default=40000, help="rows scanned after --skip")
    ap.add_argument("--max-len", type=int, default=192, help="training window (TokenConfig)")
    ap.add_argument("--out", default=str(SET_OUT))
    ap.add_argument("--report", default=str(REPORT_OUT))
    args = ap.parse_args(argv)

    if args.probe:
        if not args.checkpoint:
            ap.error("--probe requires --checkpoint")
        return probe(
            args.checkpoint,
            set_file=Path(args.out),
            which=args.which,
            device=args.device,
            report=Path(args.report),
            limit=args.limit,
        )

    built = build(
        total=args.total,
        seed=args.seed,
        skip=args.skip,
        window=args.window,
        max_len=args.max_len,
    )
    body = json.dumps(built, indent=2, ensure_ascii=False) + "\n"
    out = Path(args.out)
    if args.check:
        if not out.exists():
            print(f"check failed: missing {out.name}")
            return 1
        if out.read_text(encoding="utf-8") != body:
            print(f"check failed: {out.name} differs from a fresh build")
            return 1
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
