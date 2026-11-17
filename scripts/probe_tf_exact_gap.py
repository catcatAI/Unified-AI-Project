#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""§88: is the teacher-forced -> exact gap decoding, or the distribution?

§275/§276 leave one cheap question. A token-SNN can have a per-token accuracy
well above zero and a free-running exact rate at zero. Two causes need opposite
fixes, so telling them apart is worth more than another training run:

* **decoding** — fed the gold prefix the model picks the right token, fed its own
  prefix it drifts; fix the decoder (teacher forcing, scheduled sampling, search);
* **distribution** — even with the gold prefix the right token is outside the
  model's top few; the mapping is not learned, and no decoder recovers it.

The instrument is a per-row partition, not a threshold:

* ``O``  — every answer position (including the final EOS) is the argmax under
  the **gold** prefix (the best case any teacher-forced decoder could reach);
* ``T5`` — the gold token is inside the **top 5** at every position, i.e. a
  beam/top-5 search *could* in principle keep it (it is not a guarantee);
* ``G``  — greedy decoding from the prompt produces the whole answer **and**
  stops with EOS (``prefix_curve`` at k=0).

Rows then split by the closed form registered in §88 amendment #2. Causality
gives ``O => G`` (the gold-prefix argmax path *is* the greedy path until the
first divergence), so "the gold prefix fixes it" (``O and not G``) is
structurally empty and cannot be a bucket. With ``S(k) = T_k - G`` and
``M(k) = N - T_k``: ``S`` is search-recoverable (decoding), ``M`` is outside
the top k everywhere (distribution), and ``N - G = S(k) + M(k)``. The verdict
is the majority of the failures at k=5, with 0.5 as the only number and Wilson
intervals printed beside it; k=3/10/20/50 are reported descriptively.

Four forward-only arms, registered in §88.3 of
``docs/06-project-management/CORE_GAP_ANALYSIS.md``:

* ``distill_holdout`` — ``token_snn_distill.pt`` on the frozen 248-row hold-out
  (same corpus, never trained on). Q1, the primary arm.
* ``core_holdout`` — ``token_snn_core149k.pt`` on the same rows. Q3: the 0/248
  headline is a cross-corpus measurement, and this arm is the cross arm.
* ``distill_train`` / ``core_train`` — the first 248 rows each checkpoint was
  trained on. Q2: the only place where exposure bias is actually testable,
  because per-token accuracy there is high.

No training, no optimizer, no weight update; every checkpoint is reloaded fresh
and hashed before and after. ``--check`` re-runs the primary arm end to end and
recomputes every aggregate from the stored rows, because a report is a claim
until it has been turned back into a measurement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from ai.ed3n.token_snn import TokenSNN  # noqa: E402
from train_token_snn import exact_match, fits, read_pairs  # noqa: E402

DATA = REPO_ROOT / "apps" / "backend" / "data"
MODELS = DATA / "models"
PROCESSED = DATA / "processed"
OUT_DIR = REPO_ROOT / "data" / "tf_gap88"
REPORT = OUT_DIR / "report.json"

DISTILL_CKPT = MODELS / "token_snn_distill.pt"
CORE_CKPT = MODELS / "token_snn_core149k.pt"
HOLDOUT = PROCESSED / "distill_val_holdout.jsonl"
DISTILL_TRAIN = PROCESSED / "distill_train.jsonl"
CORE_TRAIN = PROCESSED / "core_train.jsonl"

#: Registered in §88.3: 248 rows per arm.
ROWS = 248
#: Registered in §88.4: rank containment is measured at these k. Only k=5
#: decides; the rest are reported so the reader can see the sensitivity.
TOP_K: Tuple[int, ...] = (3, 5, 10, 20, 50)
#: Registered in §88.4, corrected by amendment #2: 0.0 is greedy (G) and 1.0 is
#: the EOS prediction under the full gold prefix (`eos_argmax`), not O.
CURVE_FRACTIONS: Tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0)
#: Registered in §88.9: stop rather than run past half an hour.
MAX_SECONDS = 1800.0

ARMS: Tuple[str, ...] = ("distill_holdout", "core_holdout", "distill_train", "core_train")
ARM_SPECS: Dict[str, Dict[str, Any]] = {
    "distill_holdout": {
        "checkpoint": DISTILL_CKPT,
        "split": "holdout",
        "question": "Q1",
        "label": "distill on the frozen hold-out (same corpus, never trained on)",
    },
    "core_holdout": {
        "checkpoint": CORE_CKPT,
        "split": "holdout",
        "question": "Q3",
        "label": "core149k on the same hold-out (cross-corpus contrast)",
    },
    "distill_train": {
        "checkpoint": DISTILL_CKPT,
        "split": "distill_train",
        "question": "Q2",
        "label": "distill on the first 248 rows it trained on",
    },
    "core_train": {
        "checkpoint": CORE_CKPT,
        "split": "core_train",
        "question": "Q2-replication",
        "label": "core149k on the first 248 representable rows it trained on",
    },
}

PRIMARY = "distill_holdout"


# -- small helpers ----------------------------------------------------------
def display_path(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(Path(path).resolve())


def resolve_path(text: str) -> Path:
    path = Path(text)
    return path if path.is_absolute() else (REPO_ROOT / path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def pairs_digest(pairs: Sequence[Tuple[str, str]]) -> str:
    payload = json.dumps([[q, a] for q, a in pairs], ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def wilson(hits: int, total: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score interval; used so a 0/248 is not reported as a point."""
    if total <= 0:
        return (0.0, 0.0)
    p = hits / total
    denom = 1.0 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return (round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4))


def _params(model: TokenSNN) -> int:
    return int(sum(p.numel() for p in model.net.parameters()))


def _pairs_for(name: str, model: TokenSNN) -> List[Tuple[str, str]]:
    """The registered rows for an arm, in file order.

    ``core_train`` additionally requires the prompt and the answer to survive
    the vocabulary round-trip; that filter depends on the vocabulary only, not
    on any model output, so it cannot cherry-pick rows the model does well on.
    """
    spec = ARM_SPECS[name]
    if spec["split"] == "holdout":
        pairs = read_pairs(HOLDOUT)
    elif spec["split"] == "distill_train":
        pairs = read_pairs(DISTILL_TRAIN)
    elif spec["split"] == "core_train":
        pairs = fits(read_pairs(CORE_TRAIN), model.vocab, model.config.max_len)
        pairs = [
            (q, a)
            for q, a in pairs
            if model.vocab.decode(model.vocab.encode(q)) == q.strip()
            and model.vocab.decode(model.vocab.encode(a)) == a.strip()
        ]
    else:  # pragma: no cover - the table is closed
        raise ValueError(f"unknown split {spec['split']!r}")
    return list(pairs[:ROWS])


# -- measurement ------------------------------------------------------------
def _gold_pass(model: TokenSNN, prompt: str, answer: str) -> Dict[str, Any]:
    """One batched forward over prompt + gold answer + EOS.

    Returns the quantities that need the gold prefix: per-position correctness,
    the rank of the gold token, its log-probability, and whether the answer was
    truncated by ``max_len``.
    """
    torch = model.torch
    ids, a_start, _ = model._encode(prompt, answer)
    tensor = torch.tensor([ids], dtype=torch.long, device=model.device)
    with torch.no_grad():
        logits = model.net(tensor)[0]
    gold = ids[a_start:]
    correct: List[bool] = []
    ranks: List[int] = []
    logps: List[float] = []
    for j, gid in enumerate(gold):
        row = logits[a_start + j - 1]
        best = int(torch.argmax(row).item())
        correct.append(best == gid)
        ranks.append(1 + int((row > row[gid]).sum().item()))
        logps.append(float(torch.log_softmax(row, dim=-1)[gid].item()))
    untruncated = ids[-1] == model.vocab.eos_id
    return {
        "ids": ids,
        "a_start": a_start,
        "gold": gold,
        "correct": correct,
        "ranks": ranks,
        "logps": logps,
        "truncated": not untruncated,
    }


def _feed(model: TokenSNN, state: Any, ids: Sequence[int]) -> Tuple[Any, Any]:
    torch = model.torch
    logits = None
    for token in ids:
        logits, state = model.net.advance(
            torch.tensor([[int(token)]], dtype=torch.long, device=model.device), state
        )
    return logits, state


def _continue_exact(
    model: TokenSNN, prefix: Sequence[int], gold_body: Sequence[int], k: int
) -> Tuple[List[int], bool]:
    """Force ``k`` gold tokens, then require ``gold[k:] + [EOS]`` exactly.

    The EOS tail is what makes k = len(gold) meaningful: without it the
    remainder is empty and the endpoint would succeed for every row.
    """
    torch = model.torch
    state = model.net.init_state(1, device=model.device)
    logits, state = _feed(model, state, list(prefix) + list(gold_body[:k]))
    want = list(gold_body[k:]) + [model.vocab.eos_id]
    out: List[int] = []
    for _ in range(len(want)):
        nxt = int(torch.argmax(logits[0]).item())
        out.append(nxt)
        if nxt == model.vocab.eos_id:
            break
        if nxt == model.vocab.pad_id or nxt == model.vocab.bos_id:
            break
        logits, state = model.net.advance(
            torch.tensor([[nxt]], dtype=torch.long, device=model.device), state
        )
    return out, out == want


def measure_row(model: TokenSNN, prompt: str, answer: str) -> Dict[str, Any]:
    """Everything §88.4 registered, for one row. Forward only."""
    gold = _gold_pass(model, prompt, answer)
    gold_ids = list(gold["gold"])
    body = gold_ids[:-1] if gold_ids and gold_ids[-1] == model.vocab.eos_id else gold_ids
    prefix = gold["ids"][: gold["a_start"]]

    curve: Dict[str, bool] = {}
    greedy: List[int] = []
    for fraction in CURVE_FRACTIONS:
        k = int(math.floor(fraction * len(body)))
        produced, ok = _continue_exact(model, prefix, body, k)
        curve[str(fraction)] = bool(ok)
        if fraction == 0.0:
            greedy = produced

    gold_text = model.vocab.decode(body)
    greedy_text = model.vocab.decode(greedy)
    first_div = -1
    wanted = body + [model.vocab.eos_id]
    for index, token in enumerate(greedy):
        if index >= len(wanted) or token != wanted[index]:
            first_div = index
            break
    if first_div == -1 and len(greedy) != len(wanted):
        # A short greedy output diverged by stopping early: the divergence is
        # the missing token, not "no divergence".
        first_div = len(greedy)

    return {
        "prompt_sha": hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16],
        "gold_len": len(body),
        "gold_unk": sum(1 for token in body if token == model.vocab.unk_id),
        "gold_text": gold_text,
        "truncated": gold["truncated"],
        "argmax_exact": all(gold["correct"]),
        "eos_argmax": bool(gold["correct"][-1]) if gold["correct"] else False,
        "tf_hits": int(sum(gold["correct"])),
        "token_tf": (sum(gold["correct"]) / len(gold["correct"])) if gold["correct"] else 0.0,
        "ranks": gold["ranks"],
        "rank_median": (
            float(sorted(gold["ranks"])[len(gold["ranks"]) // 2]) if gold["ranks"] else 0.0
        ),
        "gold_logprob": (sum(gold["logps"]) / len(gold["logps"])) if gold["logps"] else 0.0,
        "topk_all": {str(k): all(rank <= k for rank in gold["ranks"]) for k in TOP_K},
        "exact_g": bool(curve["0.0"]),
        "exact_model": greedy_text.strip() == gold_text.strip(),
        "exact_raw": greedy_text.strip() == answer.strip(),
        "first_div": first_div,
        "greedy_len": len(greedy),
        "greedy_sha": hashlib.sha256(
            "\u0000".join(str(t) for t in greedy).encode("utf-8")
        ).hexdigest()[:16],
        "prefix_curve": curve,
    }


def _verdict_from_counts(decoding_rows: int, distribution_rows: int) -> str:
    """§88.5 after amendment #2: the closed form ``S(k) = T_k - G``, ``M(k) = N - T_k``.

    ``D`` is structurally zero (``O => G``), so the decoding-recoverable rows are
    exactly the rows whose gold token stays inside the top ``k`` at every
    position but whose greedy output is not the answer. The only decision number
    is still the majority of the failures.
    """
    failures = decoding_rows + distribution_rows
    if failures <= 0:
        return "no-gap"
    decoding = decoding_rows / failures
    distribution = distribution_rows / failures
    if decoding >= 0.5 and distribution < 0.5:
        return "gap=decoding"
    if distribution > 0.5:
        return "gap=distribution"
    return "gap=mixed"


def _aggregate(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(rows)
    g = sum(1 for row in rows if row["exact_g"])
    o = sum(1 for row in rows if row["argmax_exact"])
    top = {str(k): sum(1 for row in rows if row["topk_all"][str(k)]) for k in TOP_K}
    # O => G by causality: the gold-prefix argmax path *is* the greedy path
    # until the first divergence, so both "gold prefix fixes it" (O and not G)
    # and "greedy luck" (G and not O) are structurally empty. They are computed
    # and reported as consistency checks, not as decision buckets.
    d = sum(1 for row in rows if row["argmax_exact"] and not row["exact_g"])
    x = sum(1 for row in rows if not row["argmax_exact"] and row["exact_g"])
    failures = n - g
    s = top["5"] - g
    m = n - top["5"]
    sensitivity: Dict[str, Any] = {}
    for k in TOP_K:
        decoding_rows = top[str(k)] - g
        distribution_rows = n - top[str(k)]
        sensitivity[str(k)] = {
            "topk_rows": top[str(k)],
            "S": decoding_rows,
            "M": distribution_rows,
            "share_decoding": round(decoding_rows / failures, 4) if failures else 0.0,
            "share_distribution": round(distribution_rows / failures, 4) if failures else 0.0,
            "verdict": _verdict_from_counts(decoding_rows, distribution_rows),
        }
    return {
        "rows": n,
        "greedy_exact": g,
        "greedy_exact_rate": round(g / max(1, n), 4),
        "greedy_exact_ci": wilson(g, n),
        "exact_raw": sum(1 for row in rows if row["exact_raw"]),
        "exact_model": sum(1 for row in rows if row["exact_model"]),
        "argmax_exact": o,
        "eos_argmax": sum(1 for row in rows if row["eos_argmax"]),
        "topk_all": top,
        "S_top5_search_could": s,
        "M_distribution": m,
        "k_sensitivity": sensitivity,
        "D_gold_prefix_fixes": d,
        "X_greedy_luck": x,
        "failures": failures,
        "share_decoding": round(s / failures, 4) if failures else 0.0,
        "share_distribution": round(m / failures, 4) if failures else 0.0,
        "share_decoding_ci": wilson(s, failures),
        "share_distribution_ci": wilson(m, failures),
        "partition_sums_to_failures": d + s + m == failures,
        "mean_gold_len": round(sum(row["gold_len"] for row in rows) / max(1, n), 2),
        "mean_row_tf": round(sum(row["token_tf"] for row in rows) / max(1, n), 4),
        "token_tf_weighted": round(
            sum(row["tf_hits"] for row in rows) / max(1, sum(len(row["ranks"]) for row in rows)),
            4,
        ),
        # By causality O => G: the greedy path *is* the gold path until it first
        # diverges, so the "gold prefix fixes it" bucket is structurally empty.
        # It is kept as a consistency check, not as a decision bucket.
        "theorem_gold_path_equals_greedy": d == 0 and x == 0,
        "mean_gold_logprob": round(sum(row["gold_logprob"] for row in rows) / max(1, n), 4),
        "truncated": sum(1 for row in rows if row["truncated"]),
        "raw_vs_model_disagree": sum(1 for row in rows if row["exact_raw"] != row["exact_model"]),
        "distinct_greedy": len({row["greedy_sha"] for row in rows}),
        "first_div_at_zero": sum(1 for row in rows if row["first_div"] == 0),
        "first_div_median": _median([row["first_div"] for row in rows if row["first_div"] >= 0]),
        "curve": {
            str(f): round(sum(1 for row in rows if row["prefix_curve"][str(f)]) / max(1, n), 4)
            for f in CURVE_FRACTIONS
        },
    }


def _median(values: Sequence[int]) -> float:
    ordered = sorted(values)
    if not ordered:
        return -1.0
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def verdict(aggregate: Dict[str, Any]) -> str:
    """§88.5: the only decision number is a majority of the failures."""
    return _verdict_from_counts(
        int(aggregate["S_top5_search_could"]), int(aggregate["M_distribution"])
    )


# -- run / check ------------------------------------------------------------
def _rows_equal(left: Sequence[Dict[str, Any]], right: Sequence[Dict[str, Any]]) -> bool:
    if len(left) != len(right):
        return False
    for a, b in zip(left, right):
        if set(a) != set(b):
            return False
        for key in a:
            if isinstance(a[key], float) and isinstance(b[key], float):
                if abs(a[key] - b[key]) > 1e-6:
                    return False
            elif a[key] != b[key]:
                return False
    return True


def run(args: argparse.Namespace) -> Dict[str, Any]:
    import torch

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    hashes_before: Dict[str, str] = {}
    arms: Dict[str, Any] = {}
    truncated_by_arm: Dict[str, int] = {}
    training_flags: Dict[str, bool] = {}

    for name in args.arms:
        spec = ARM_SPECS[name]
        checkpoint = Path(spec["checkpoint"])
        hashes_before[name] = sha256_file(checkpoint)
        model = TokenSNN.load(checkpoint, device="cpu")
        pairs = _pairs_for(name, model)
        digest = pairs_digest(pairs)
        print(f"{name}: {len(pairs)} rows from {display_path(checkpoint)}", flush=True)
        rows: List[Dict[str, Any]] = []
        arm_started = time.time()
        for index, (prompt, answer) in enumerate(pairs, 1):
            rows.append(measure_row(model, prompt, answer))
            if index % 50 == 0:
                print(f"    {index}/{len(pairs)} ({time.time() - arm_started:.0f}s)", flush=True)
            if time.time() - started > MAX_SECONDS:
                raise SystemExit(
                    f"stopped after {time.time() - started:.0f}s > {MAX_SECONDS:.0f}s; "
                    "this run is aborted and must not be scored"
                )

        determinism = None
        if name == PRIMARY and len(pairs) > 1:
            repeat = pairs[: min(32, len(pairs))]
            again = [measure_row(model, q, a) for q, a in repeat]
            determinism = {
                "compared": len(repeat),
                "identical": _rows_equal(rows[: len(repeat)], again),
            }

        cross = None
        if name == PRIMARY:
            with redirect_stdout(StringIO()):
                production = exact_match(model, pairs, 0, seed=3)
            ours = sum(1 for row in rows if row["exact_raw"])
            tf = model.tf_accuracy(pairs)
            positions = sum(len(row["ranks"]) for row in rows)
            hits = sum(row["tf_hits"] for row in rows)
            production_hits = int(round(tf["tf_acc"] * tf["tokens"]))
            cross = {
                "exact_match_hits": int(round(production["exact"] * production["n"])),
                "our_exact_raw": ours,
                "exact_match_n": production["n"],
                "tf_accuracy": tf["tf_acc"],
                "tf_tokens": tf["tokens"],
                "production_tf_hits": production_hits,
                "our_tf_hits": hits,
                "our_tf_tokens": positions,
                "our_token_tf": round(hits / max(1, positions), 6),
                # train_token_snn.tf_accuracy rounds its rate to 4 decimals, so
                # the only exact comparison is the hit count; the rate is
                # compared at the rounding width that the producer uses.
                "tf_delta": abs(hits / max(1, positions) - tf["tf_acc"]),
            }

        aggregate = _aggregate(rows)
        truncated_by_arm[name] = aggregate["truncated"]
        training_flags[name] = bool(model.net.training)
        arms[name] = {
            "spec": spec["label"],
            "question": spec["question"],
            "checkpoint": display_path(checkpoint),
            "sha256": hashes_before[name],
            "params": _params(model),
            "vocab_size": len(model.vocab),
            "config": model.config.to_dict(),
            "rows_digest": digest,
            "rows": rows,
            "aggregate": aggregate,
            "verdict": verdict(aggregate),
            "determinism": determinism,
            "production_cross_check": cross,
            "seconds": round(time.time() - arm_started, 1),
        }
        print(
            f"    {name}: G={aggregate['greedy_exact']}/{aggregate['rows']} "
            f"O={aggregate['argmax_exact']} T5={aggregate['topk_all']['5']} "
            f"D={aggregate['D_gold_prefix_fixes']} "
            f"S={aggregate['S_top5_search_could']} M={aggregate['M_distribution']} "
            f"-> {arms[name]['verdict']}",
            flush=True,
        )
        del model

    hashes_after = {name: sha256_file(Path(ARM_SPECS[name]["checkpoint"])) for name in args.arms}
    overlap = len(set(read_pairs(HOLDOUT)) & set(read_pairs(DISTILL_TRAIN)))

    primary = arms.get(PRIMARY)
    primary_digest_ok = None
    if primary is not None:
        primary_model = TokenSNN.load(Path(ARM_SPECS[PRIMARY]["checkpoint"]), device="cpu")
        primary_pairs = _pairs_for(PRIMARY, primary_model)
        del primary_model
        primary_digest_ok = pairs_digest(primary_pairs) == primary["rows_digest"]
    # Amendment #2: with `gold[k:] + [EOS]`, k = len(gold) leaves exactly one
    # token to predict (EOS), so the f=1.0 endpoint is `eos_argmax` — the
    # batched gold forward's last position — not the full gold path (O).
    endpoint_ok = all(
        row["exact_g"] == row["prefix_curve"]["0.0"]
        and row["eos_argmax"] == row["prefix_curve"]["1.0"]
        for arm in arms.values()
        for row in arm["rows"]
    )

    items: List[Dict[str, Any]] = [
        {
            "id": "I0-1",
            "name": "checkpoints unchanged (sha256 before == after)",
            "value": {"before": hashes_before, "after": hashes_after},
            "passes": hashes_before == hashes_after,
        },
        {
            "id": "I0-2",
            "name": "no training: net.training is False after every arm",
            "value": training_flags,
            "passes": not any(training_flags.values()),
        },
        {
            "id": "I0-3",
            "name": "the registered rows, and hold-out does not overlap distill_train",
            "value": {
                "rows": {name: len(arm["rows"]) for name, arm in arms.items()},
                "digests": {name: arm["rows_digest"] for name, arm in arms.items()},
                "holdout_and_distill_train": overlap,
                "primary_digest_recomputed_ok": primary_digest_ok,
            },
            "passes": all(len(arm["rows"]) == ROWS for arm in arms.values())
            and overlap == 0
            and primary_digest_ok,
        },
        {
            "id": "I0-4",
            "name": "determinism: the first 32 primary rows repeated identically",
            "value": (primary or {}).get("determinism"),
            "passes": bool((primary or {}).get("determinism", {}).get("identical")),
        },
        {
            "id": "I0-5",
            "name": "greedy decoding matches train_token_snn.exact_match",
            "value": (primary or {}).get("production_cross_check"),
            "passes": bool(
                (primary or {}).get("production_cross_check", {}).get("exact_match_hits")
                == (primary or {}).get("production_cross_check", {}).get("our_exact_raw")
                and (primary or {}).get("production_cross_check") is not None
            ),
        },
        {
            "id": "I0-6",
            "name": "the gold-prefix forward matches TokenSNN.tf_accuracy",
            "value": (primary or {}).get("production_cross_check"),
            "passes": bool(
                (primary or {}).get("production_cross_check")
                and primary["production_cross_check"]["tf_tokens"]
                == primary["production_cross_check"]["our_tf_tokens"]
                and primary["production_cross_check"]["production_tf_hits"]
                == primary["production_cross_check"]["our_tf_hits"]
                # the producer stores the rate rounded to 4 decimals
                and primary["production_cross_check"]["tf_delta"] <= 5e-5
            ),
        },
        {
            "id": "I0-7",
            "name": "no truncated rows (over 5% voids the arm)",
            "value": truncated_by_arm,
            "passes": all(count <= 0.05 * ROWS for count in truncated_by_arm.values()),
        },
        {
            "id": "I0-8",
            "name": "prefix-curve endpoints agree with G (f=0) and eos_argmax (f=1)",
            "value": {
                name: {
                    "curve0_vs_g": sum(
                        1 for row in arm["rows"] if row["prefix_curve"]["0.0"] == row["exact_g"]
                    ),
                    "curve1_vs_eos": sum(
                        1 for row in arm["rows"] if row["prefix_curve"]["1.0"] == row["eos_argmax"]
                    ),
                }
                for name, arm in arms.items()
            },
            "passes": bool(endpoint_ok),
        },
    ]
    i0 = {"items": items, "all_pass": all(item["passes"] for item in items)}

    q1 = arms["distill_holdout"]["verdict"] if "distill_holdout" in arms else None
    q2 = arms["distill_train"]["verdict"] if "distill_train" in arms else None
    q2_rep = arms["core_train"]["verdict"] if "core_train" in arms else None
    if "core_train" in arms and "core_holdout" in arms:
        core_train_g = arms["core_train"]["aggregate"]["greedy_exact_ci"]
        core_holdout_g = arms["core_holdout"]["aggregate"]["greedy_exact_ci"]
        disjoint = core_train_g[0] > core_holdout_g[1] or core_holdout_g[0] > core_train_g[1]
    else:
        core_train_g = (
            arms["core_train"]["aggregate"]["greedy_exact_ci"] if "core_train" in arms else None
        )
        core_holdout_g = (
            arms["core_holdout"]["aggregate"]["greedy_exact_ci"] if "core_holdout" in arms else None
        )
        disjoint = None

    predictions = {
        "Q1_expected": "gap=distribution",
        "Q1_actual": q1 if q1 is not None else "not-run",
        "Q1_met": (q1 == "gap=distribution") if q1 is not None else None,
        "Q2_expected": "gap=decoding",
        "Q2_actual": q2 if q2 is not None else "not-run",
        "Q2_met": (q2 == "gap=decoding") if q2 is not None else None,
        "Q2_replication_actual": q2_rep if q2_rep is not None else "not-run",
        "Q3_expected": "core_train and core_holdout exact intervals do not overlap",
        "Q3_intervals": {
            "core_train": core_train_g,
            "core_holdout": core_holdout_g,
        },
        "Q3_met": bool(disjoint) if disjoint is not None else None,
    }

    return {
        "stage": "probe_tf_exact_gap",
        "registration": "docs/06-project-management/CORE_GAP_ANALYSIS.md §88",
        "registered_run": (
            list(args.arms) == list(ARMS) and primary is not None and len(primary["rows"]) == ROWS
        ),
        "protocol": {
            "rows_per_arm": ROWS,
            "top_k": list(TOP_K),
            "curve_fractions": list(CURVE_FRACTIONS),
            "primary": PRIMARY,
            "checkpoints": {
                name: {
                    "path": display_path(Path(spec["checkpoint"])),
                    "sha256": hashes_before[name],
                }
                for name, spec in ARM_SPECS.items()
                if name in args.arms
            },
            "splits": {
                "holdout": display_path(HOLDOUT),
                "distill_train": display_path(DISTILL_TRAIN),
                "core_train": display_path(CORE_TRAIN),
            },
            "verdict_rule": (
                "amendment #2: O => G, so D = O&!G == 0 and X = !O&G == 0; "
                "S(k) = T_k - G; M(k) = N - T_k; failures = N - G = S(k) + M(k); "
                "k=5 decides: decoding if S/failures>=0.5 and M/failures<0.5; "
                "distribution if M/failures>0.5; else mixed; no-gap if failures==0; "
                "k=3/10/20/50 are reported descriptively only"
            ),
        },
        "arms": arms,
        "i0": i0,
        "predictions": predictions,
        "seconds": round(time.time() - started, 1),
    }


def _canonical(value: Any) -> Any:
    """Tuple -> list, so an aggregate compared to itself after a JSON round-trip
    is equal. ``wilson`` returns tuples and the report stores JSON arrays."""
    return json.loads(json.dumps(value, sort_keys=True))


def check(report_path: Path) -> Tuple[bool, str]:
    """Recompute every aggregate and re-run the primary arm end to end."""
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if report.get("stage") != "probe_tf_exact_gap":
        return False, "not a probe_tf_exact_gap report"
    errors: List[str] = []

    for name, arm in report.get("arms", {}).items():
        path = resolve_path(arm["checkpoint"])
        if not path.is_file():
            errors.append(f"{name}: missing checkpoint {arm['checkpoint']}")
            continue
        if sha256_file(path) != arm["sha256"]:
            errors.append(f"{name}: checkpoint changed since the report was written")
            continue
        recomputed = _aggregate(arm["rows"])
        if _canonical(recomputed) != _canonical(arm["aggregate"]):
            errors.append(f"{name}: aggregate does not recompute from its own rows")
        if verdict(recomputed) != arm["verdict"]:
            errors.append(f"{name}: verdict {verdict(recomputed)} != reported {arm['verdict']}")
        if (
            recomputed["D_gold_prefix_fixes"]
            + recomputed["S_top5_search_could"]
            + recomputed["M_distribution"]
            != recomputed["failures"]
        ):
            errors.append(f"{name}: the four-cell partition does not sum to the failures")

    primary_name = report["protocol"]["primary"]
    primary = report["arms"][primary_name]
    model = TokenSNN.load(resolve_path(primary["checkpoint"]), device="cpu")
    pairs = _pairs_for(primary_name, model)
    if pairs_digest(pairs) != primary["rows_digest"]:
        errors.append("primary: the registered rows changed since the report was written")
    fresh = [measure_row(model, prompt, answer) for prompt, answer in pairs]
    if not _rows_equal(fresh, primary["rows"]):
        errors.append("primary: re-running the arm does not reproduce its per-row records")
    if model.net.training:
        errors.append("primary: the model is in training mode after a forward-only pass")

    if not report.get("i0", {}).get("all_pass"):
        failed = [
            item["id"] for item in report.get("i0", {}).get("items", []) if not item["passes"]
        ]
        errors.append(f"the report's own I0 block failed: {', '.join(failed) or 'missing'}")

    if errors:
        return False, "; ".join(errors[:5])
    return True, (
        f"probe_tf_exact_gap check OK ({len(report['arms'])} arms recomputed, "
        f"primary re-run row-for-row, I0 all pass)"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--arms",
        default=",".join(ARMS),
        help="comma-separated subset (a subset marks the report as not the registered run)",
    )
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument(
        "--check",
        type=Path,
        metavar="REPORT",
        help="recompute every aggregate and re-run the primary arm from its checkpoint",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    names = [name.strip() for name in str(args.arms).split(",") if name.strip()]
    unknown = [name for name in names if name not in ARM_SPECS]
    if unknown:
        parser.error(f"unknown arm(s): {', '.join(unknown)}; known: {', '.join(ARMS)}")
    args.arms = names

    if args.check:
        ok, message = check(args.check)
        print(message if ok else f"FAIL: {message}")
        return 0 if ok else 1

    report = run(args)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    print("\n" + "=" * 78)
    print(f"{'arm':18s} {'G':>7s} {'O':>5s} {'T5':>5s} {'D':>4s} {'S':>4s} {'M':>4s}  verdict")
    for name, arm in report["arms"].items():
        agg = arm["aggregate"]
        print(
            f"{name:18s} {agg['greedy_exact']:3d}/{agg['rows']:<3d} "
            f"{agg['argmax_exact']:5d} {agg['topk_all']['5']:5d} "
            f"{agg['D_gold_prefix_fixes']:4d} {agg['S_top5_search_could']:4d} "
            f"{agg['M_distribution']:4d}  {arm['verdict']}"
        )
    preds = report["predictions"]

    def _met(flag: Any) -> str:
        if flag is None:
            return "not-run"
        return "met" if flag else "MISSED"

    print(
        f"Q1 predicted {preds['Q1_expected']}, got {preds['Q1_actual']} ({_met(preds['Q1_met'])})"
    )
    print(
        f"Q2 predicted {preds['Q2_expected']}, got {preds['Q2_actual']} ({_met(preds['Q2_met'])}); "
        f"core_train replication: {preds['Q2_replication_actual']}"
    )
    print(f"Q3 intervals {preds['Q3_intervals']} ({_met(preds['Q3_met'])})")
    for name, arm in report["arms"].items():
        sensitivity = arm["aggregate"]["k_sensitivity"]
        print(f"{name} k-sensitivity (k=5 decides):")
        for k in sorted(sensitivity, key=int):
            row = sensitivity[k]
            print(
                f"    k={k:>2s} T={row['topk_rows']:3d} "
                f"S={row['S']:3d} M={row['M']:3d} "
                f"share_decoding={row['share_decoding']:.3f} "
                f"share_distribution={row['share_distribution']:.3f} "
                f"{row['verdict']}{'  <- decides' if k == '5' else ''}"
            )
    print(f"i0: {'ALL PASS' if report['i0']['all_pass'] else 'FAILED'}")
    print(f"seconds: {report['seconds']:.1f}")
    print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
