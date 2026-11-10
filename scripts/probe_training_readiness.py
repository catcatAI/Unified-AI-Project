#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Is the core *ready to accept training*? Measure, do not assume.

This probe exists because "train it longer" is the wrong reflex when the thing
being trained may already be degenerate. It checks the five things that decide
whether a training run can mean anything, and it refuses to call the rig ready
when one of them is broken.

What it measures (and what a failure means)
-------------------------------------------
A. **Data** — the corpus the run would learn from.
   - manifest hashes still match the written files;
   - zero benchmark leaks (the score must not be bought by training on it);
   - how many rows teach *nothing* because truncation cut the answer away
     (those rows cost the same compute and contribute no target);
   - contradictory supervision: one input, several different answers;
   - how much of the validation answer mass is ``<unk>``.

B. **Mechanics** — whether the graph can learn at all. Run on a *reduced*
   config (the point is the mechanism, not the score): every parameter group
   receives a finite non-zero gradient, the spiking stack fires inside the
   surrogate's gradient band, 24 rows can be overfit, a fixed seed reproduces
   bit-identically, and eval/train agree when there is no dropout.

C. **Objective** — whether more training or a better teacher is the lever.
   - an interpolated bigram floor on the same answer positions (what a
     one-token-context model achieves);
   - the student's last reported loss against that floor;
   - the teacher's atom-level cross-entropy against the same floor — if the
     teacher is not clearly better, distillation would teach noise;
   - the teacher's probability on tokens that agree with the gold atom, i.e.
     whether pulling toward the teacher also pulls toward the answer.

D. **Distillation plumbing** — whether soft targets survive the tokeniser
   mismatch. The mapper (``ai.ed3n.kd_targets``) is measured on real positions:
   how much of the teacher's top-k mass lands on a student atom, whether the KD
   loss produces gradients, and whether 24 rows can be overfit on it.

E. **Checkpoint dynamics** — the failure that motivated this probe: the 108M
   model ended with ``theta`` pinned at its cap (1.9995 of 2.0), the leak
   collapsed 0.9 -> 0.54 and only 0.18% of pre-activations sat near threshold,
   i.e. the spiking nonlinearity had almost no gradient while the loss looked
   fine. A checkpoint in that state is not a base to continue from.

Exit codes: 0 all pass, 1 any FAIL, 2 nothing failed but something is BLOCKED
(a prerequisite such as the teacher model is missing).

Usage
    python scripts/probe_training_readiness.py
    python scripts/probe_training_readiness.py --json /tmp/readiness.json
    python scripts/probe_training_readiness.py --skip-teacher   # offline
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import prepare_core_training_data as prep  # noqa: E402  (sibling script)

PROCESSED = REPO_ROOT / "apps" / "backend" / "data" / "processed"
TRAIN = PROCESSED / "core_train.jsonl"
VAL = PROCESSED / "core_val.jsonl"
MANIFEST = PROCESSED / "core_train_manifest.json"
TEACHER = REPO_ROOT / "data" / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
STUDENT_REPORT = REPO_ROOT / "data" / "intelligence_reports" / "token_snn_108m.json"
STUDENT_CKPT = REPO_ROOT / "apps" / "backend" / "data" / "models" / "token_snn_108m.pt"

MAX_LEN = 192  # the 108M run's budget; A3/E measure against it


# ---------------------------------------------------------------------------
# result plumbing — every check prints its number, so a PASS is auditable
# ---------------------------------------------------------------------------
class Report:
    def __init__(self) -> None:
        self.rows: List[Dict[str, Any]] = []

    def add(
        self,
        check: str,
        status: str,
        value: Any = None,
        threshold: Any = None,
        note: str = "",
    ) -> None:
        assert status in ("PASS", "FAIL", "BLOCKED", "INFO"), status
        self.rows.append(
            {"check": check, "status": status, "value": value, "threshold": threshold, "note": note}
        )
        shown = "" if value is None else f"{value}"
        mark = {"PASS": "✅", "FAIL": "❌", "BLOCKED": "⛔", "INFO": "·"}[status]
        extra = f"  (threshold {threshold})" if threshold is not None else ""
        print(f"  {mark} [{status:7s}] {check}: {shown}{extra}", flush=True)
        if note:
            print(f"        {note}", flush=True)

    def counts(self) -> Dict[str, int]:
        return dict(collections.Counter(r["status"] for r in self.rows))

    def verdict(self) -> int:
        counts = self.counts()
        if counts.get("FAIL"):
            return 1
        if counts.get("BLOCKED"):
            return 2
        return 0


def _rows(path: Path, limit: int = 0) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        out.append(json.loads(line))
        if limit and len(out) >= limit:
            break
    return out


def _atom_ids(vocab: Any, text: str) -> List[int]:
    return vocab.encode(text)


def _fit_encoder(vocab: Any, max_len: int) -> Any:
    """Bind the *real* ``TokenSNN._encode`` to a config-only shim.

    Re-implementing the truncation arithmetic here would let this probe and the
    trainer disagree — which is the class of defect the probe is supposed to
    catch. Importing ``TokenSNN`` does not import torch (it is imported in
    ``__init__``), so this stays cheap and measures the shipping code path.
    """
    from ai.ed3n.token_snn import TokenConfig, TokenSNN

    class _Shim:
        pass

    shim = _Shim()
    shim.vocab = vocab
    shim.config = TokenConfig(max_len=max_len)
    return lambda prompt, answer: TokenSNN._encode(shim, prompt, answer)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# A. data
# ---------------------------------------------------------------------------
def check_data(
    rep: Report,
    train: List[Dict[str, str]],
    val: List[Dict[str, str]],
    min_count: int,
    max_vocab: int,
) -> Dict[str, Any]:
    print("\nA. data", flush=True)
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        mismatched = []
        for name in ("core_train.jsonl", "core_val.jsonl"):
            path = PROCESSED / name
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != manifest.get("files", {}).get(name):
                mismatched.append(name)
        rep.add(
            "data.manifest_hashes",
            "PASS" if not mismatched else "FAIL",
            value="match" if not mismatched else ",".join(mismatched),
            note="the files were not edited by hand after preparation",
        )
    else:
        rep.add("data.manifest_hashes", "BLOCKED", value="no manifest", note=str(MANIFEST))

    bench = prep._benchmark_texts()
    shingles: set = set()
    for question in bench:
        shingles |= prep._shingles(question)
    leaks = 0
    for row in train + val:
        if prep._is_leak(prep._norm(row["input"]), bench, shingles):
            leaks += 1
    rep.add(
        "data.benchmark_leak",
        "PASS" if leaks == 0 else "FAIL",
        value=leaks,
        threshold=0,
        note=f"{len(bench)} frozen questions, whole-question + 8-gram shingles",
    )

    from ai.ed3n.token_snn import TokenVocab

    vocab = TokenVocab.build(
        [r["input"] + "\n" + r["output"] for r in train],
        min_count=min_count,
        max_vocab=max_vocab,
    )
    encode = _fit_encoder(vocab, MAX_LEN)
    lost = truncated = 0
    unk = atoms = 0
    for row in train:
        ids, start, _cut = encode(row["input"], row["output"])
        if len(ids) - start <= 1:
            lost += 1
        if len(ids) >= MAX_LEN and ids[-1] != vocab.eos_id:
            truncated += 1
    for row in val:
        ids, start, _cut = encode(row["input"], row["output"])
        if len(ids) - start <= 1:
            continue
        atom_ids = ids[start:-1]
        unk += sum(1 for t in atom_ids if t == vocab.unk_id)
        atoms += len(atom_ids)
    rep.add(
        "data.rows_teaching_nothing",
        "FAIL" if lost else "PASS",
        value=lost,
        threshold=0,
        note=f"answer entirely cut by max_len={MAX_LEN}; those rows cost a batch and yield no target",
    )
    rep.add(
        "data.rows_truncated",
        "INFO",
        value=f"{truncated} ({truncated / max(1, len(train)):.2%})",
        note="answer cut mid-way (still yields targets, but the last tokens are unseen)",
    )
    rep.add(
        "data.val_unk_share",
        "INFO" if unk / max(1, atoms) < 0.05 else "FAIL",
        value=f"{unk / max(1, atoms):.2%}",
        threshold="<5%",
        note="validation answer atoms the vocab cannot express",
    )

    by_input: Dict[str, set] = collections.defaultdict(set)
    for row in train:
        by_input[prep._norm(row["input"])].add(prep._norm(row["output"]))
    contradictions = sum(1 for answers in by_input.values() if len(answers) > 1)
    share = contradictions / max(1, len(by_input))
    rep.add(
        "data.contradictory_inputs",
        "PASS" if share <= 0.02 else "FAIL",
        value=f"{contradictions} ({share:.2%})",
        threshold="<=2%",
        note="one input with several answers: the model is asked to average them",
    )
    return {"vocab": vocab, "encode": encode, "train_fit_rows": len(train) - lost}


# ---------------------------------------------------------------------------
# C. objective information (baselines + teacher)
# ---------------------------------------------------------------------------
def _interpolated_bigram_floor(
    train: Sequence[Dict[str, str]],
    val_rows: Sequence[Sequence[int]],
) -> Tuple[float, float]:
    """(best λ, CE) for ``λ·P_ml(t|prev) + (1-λ)·P_uni(t)`` on answer atoms.

    Add-1 smoothing over a 32k vocabulary would make the baseline absurdly bad
    (each unseen bigram costs ~log(V) nats), which would make any model look
    good. Interpolation with the unigram is the standard floor, and the best λ
    is reported so the floor is the *strongest* one-token-context model, not a
    straw man.
    """
    unigram: collections.Counter = collections.Counter()
    bigram: collections.Counter = collections.Counter()
    prev_count: collections.Counter = collections.Counter()
    for row in train:
        prev: Optional[int] = None
        for t in row:
            unigram[t] += 1
            bigram[(prev, t)] += 1
            prev_count[prev] += 1
            prev = t
    total = sum(unigram.values())
    vocab_size = max(1, len(unigram))

    def p_uni(t: int) -> float:
        return (unigram[t] + 0.1) / (total + 0.1 * vocab_size)

    best = (0.0, float("inf"))
    for lam in (0.3, 0.5, 0.7, 0.9, 0.97):
        nll = 0.0
        n = 0
        for atoms in val_rows:
            prev = None
            for t in atoms:
                p = lam * (bigram[(prev, t)] + 0.1) / (prev_count[prev] + 0.1 * vocab_size) + (
                    1 - lam
                ) * p_uni(t)
                nll -= math.log(p)
                n += 1
                prev = t
        ce = nll / max(1, n)
        if ce < best[1]:
            best = (lam, ce)
    return best


def check_baselines(
    rep: Report,
    train_atom_rows: List[List[int]],
    val_atom_rows: List[List[int]],
    student_report: Path,
) -> Dict[str, float]:
    print("\nC. objective information", flush=True)
    if not val_atom_rows:
        rep.add("baseline.bigram", "BLOCKED", value="no fit rows")
        return {}
    lam, floor = _interpolated_bigram_floor(train_atom_rows, val_atom_rows)
    rep.add(
        "baseline.bigram_floor",
        "INFO",
        value=f"{floor:.3f} nats",
        note=f"interpolated bigram, best λ={lam} chosen on this split (strongest 1-token floor)",
    )
    student_loss = None
    if student_report.exists():
        payload = json.loads(student_report.read_text(encoding="utf-8"))
        student_loss = payload.get("best_loss")
    if student_loss is None:
        rep.add("baseline.student_train_loss", "BLOCKED", value="no student loss")
    else:
        # This is the *training* loss against a *validation* floor: useful
        # context, not a verdict — the like-for-like measurement is E's
        # ``ckpt.val_ce_vs_floor``, computed on the same rows as the floor.
        rep.add(
            "baseline.student_train_loss",
            "INFO",
            value=f"train loss {student_loss:.3f} vs val floor {floor:.3f}",
            note="reported for context only; E measures the checkpoint on the same "
            "validation rows as the floor, and that is the check that gates",
        )
    return {"floor": floor, "student_loss": float(student_loss or 0.0)}


def _open_teacher() -> Tuple[Optional[Any], str]:
    """Open the GGUF teacher once; ``(teacher, reason_if_unavailable)``.

    Both the teacher measurement and the distillation domain must go through the
    same :class:`ai.ed3n.kd_teacher.KdTeacher`, because the tokenisers differ and
    the alignment rule is the thing most likely to drift. A second hand-rolled
    copy in this script is how the 0.316 agreement was produced.
    """
    if not TEACHER.exists():
        return None, f"teacher missing: {TEACHER}"
    try:
        from ai.ed3n.kd_teacher import KdTeacher

        return KdTeacher(str(TEACHER), n_ctx=512, n_threads=6), ""
    except Exception as exc:  # noqa: BLE001 — optional dependency
        return None, f"llama_cpp unavailable: {exc}"


def check_teacher(
    rep: Report,
    train_rows: List[Dict[str, str]],
    val_rows: List[Dict[str, str]],
    vocab: Any,
    floor: float,
    sample: int,
    skip: bool,
) -> Optional[Any]:
    """Teacher CE at atom granularity, plus its agreement with the gold atom."""
    if skip:
        rep.add("teacher.atom_ce", "BLOCKED", value="--skip-teacher")
        rep.add("teacher.gold_agreement", "BLOCKED", value="--skip-teacher")
        return None
    teacher, why = _open_teacher()
    if teacher is None:
        rep.add("teacher.atom_ce", "BLOCKED", value=why)
        rep.add("teacher.gold_agreement", "BLOCKED", value=why)
        return None

    rnd = random.Random(7)
    picks = list(val_rows)
    rnd.shuffle(picks)
    picks = picks[:sample]
    nll = 0.0
    atoms = 0
    aligned = 0
    seen = 0
    agree: List[float] = []
    for row in picks:
        walk, scores, spans = teacher.align(row["input"], row["output"])
        if scores is None:
            continue
        lp = teacher.token_logprobs(teacher.tokenize(row["input"] + "\n" + row["output"]))
        row_aligned = []
        for atom in walk:
            atom_lp = teacher.atom_logprob(lp, spans, atom.start, atom.end)
            if atom_lp is None:
                continue
            nll -= atom_lp
            atoms += 1
            seen += 1
            if atom.token_index is None:
                continue
            aligned += 1
            row_aligned.append(atom)
        agree.extend(teacher.agreement(row_aligned, scores))
    if not atoms:
        rep.add("teacher.atom_ce", "BLOCKED", value="no scorable atoms")
        return teacher
    ce = nll / atoms
    rep.add(
        "teacher.atom_ce",
        "PASS" if ce < floor - 0.5 else "FAIL",
        value=f"{ce:.3f} nats over {atoms} atoms",
        threshold=f"< floor {floor:.3f} - 0.5",
        note="if the teacher is not clearly better than the bigram floor, distilling it "
        "teaches the student noise, not knowledge",
    )
    rep.add(
        "teacher.boundary_alignment",
        "INFO",
        value=f"{aligned}/{seen} atoms ({aligned / max(1, seen):.1%})",
        note="answer atoms that begin exactly where a teacher token begins; only these can "
        "carry a distillation target",
    )
    if not agree:
        rep.add("teacher.gold_agreement", "BLOCKED", value="no aligned atoms")
        return teacher
    mean_agree = sum(agree) / len(agree)
    rep.add(
        "teacher.gold_agreement",
        "PASS" if mean_agree >= 0.5 else "FAIL",
        value=f"{mean_agree:.3f} over {len(agree)} aligned atoms",
        threshold=">=0.5",
        note="teacher mass on tokens that agree with the corpus answer at that boundary; "
        "low means the soft target pulls away from the gold continuation",
    )
    return teacher


# ---------------------------------------------------------------------------
# B. mechanics (reduced config — the mechanism, not the score)
# ---------------------------------------------------------------------------
def _small_model(vocab: Any, seed: int = 0, max_len: int = 64) -> Any:
    import torch
    from ai.ed3n.token_snn import TokenConfig, TokenSNN

    torch.manual_seed(seed)
    cfg = TokenConfig(d_emb=64, d_hidden=128, max_len=max_len, readout="membrane")
    return TokenSNN(vocab, cfg, device="cpu")


def check_mechanics(rep: Report, vocab: Any, pairs: List[Tuple[str, str]]) -> Dict[str, Any]:
    print("\nB. mechanics (reduced config: d_emb=64 d_hidden=128 max_len=64)", flush=True)
    import torch

    model = _small_model(vocab)
    batch = pairs[:8]
    ids, mask, _ = model.make_batch(batch)
    loss = model.loss(ids, mask)
    loss.backward()
    # Group by the *first* component of each real parameter name
    # ("w_rec.0.weight" -> "w_rec"). Iterating the parameters instead of a
    # hard-coded list means a group with no parameters (``w_skip`` is an
    # ``nn.Identity`` at layers=1) is absent rather than a false zero-gradient
    # failure, and a newly added module cannot be forgotten.
    norms: Dict[str, float] = {}
    counts: Dict[str, int] = {}
    for pname, param in model.net.named_parameters():
        group = pname.split(".", 1)[0]
        counts[group] = counts.get(group, 0) + int(param.numel())
        if param.grad is None:
            norms.setdefault(group, float("nan"))
            continue
        norms[group] = norms.get(group, 0.0) + float(param.grad.detach().pow(2).sum())
    norms = {k: math.sqrt(v) for k, v in norms.items()}
    missing = [k for k, v in norms.items() if not math.isfinite(v) or v == 0.0]
    rep.add(
        "mech.gradient_reaches_every_group",
        "PASS" if not missing else "FAIL",
        value=", ".join(f"{k}={v:.3e}" for k, v in sorted(norms.items())),
        threshold="all > 0 and finite",
        note=(
            ""
            if not missing
            else f"no gradient: {', '.join(missing)} (training would not touch it)"
        ),
    )
    rep.add(
        "mech.parameter_allocation",
        "INFO",
        value=", ".join(
            f"{k}={counts[k] / max(1, sum(counts.values())):.1%}" for k in sorted(counts)
        ),
        note=f"{sum(counts.values()):,} parameters; the head and embedding dominate, the "
        "recurrent matrix is the part that carries context",
    )

    dyn = model.dynamics(batch, n=4)
    layer = dyn["per_layer"][0]
    rep.add(
        "mech.dynamics_alive",
        "PASS" if 0.01 < layer["spike_rate"] < 0.99 and layer["sensitive"] > 0.01 else "FAIL",
        value=f"rate={layer['spike_rate']} sensitive={layer['sensitive']} near={layer['near_threshold']}",
        threshold="0.01<rate<0.99, sensitive>0.01",
        note="outside the surrogate's +-2 band the unit fires but receives no gradient",
    )

    # Overfit a fixed 24-row batch: the cheapest proof that the optimiser, the
    # graph and the head can move in the right direction at all.
    over = pairs[:24]
    model = _small_model(vocab, seed=1)
    opt = torch.optim.Adam(model.net.parameters(), lr=3e-3)
    first = last = None
    for step in range(40):
        opt.zero_grad()
        ids_o, mask_o, _ = model.make_batch(over)
        step_loss = model.loss(ids_o, mask_o)
        step_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.net.parameters(), 1.0)
        opt.step()
        if step == 0:
            first = float(step_loss.detach())
        last = float(step_loss.detach())
    ratio = last / max(1e-9, first)
    rep.add(
        "mech.can_overfit_24_rows",
        "PASS" if ratio <= 0.6 else "FAIL",
        value=f"{first:.3f} -> {last:.3f} (x{ratio:.3f})",
        threshold="<= 0.6x after 40 steps",
        note="a model that cannot overfit 24 rows will not generalise from 138k",
    )

    a = _small_model(vocab, seed=2)
    b = _small_model(vocab, seed=2)
    losses = []
    for model_ in (a, b):
        ids_d, mask_d, _ = model_.make_batch(over[:4])
        losses.append(float(model_.loss(ids_d, mask_d).detach()))
    rep.add(
        "mech.seed_is_deterministic",
        "PASS" if abs(losses[0] - losses[1]) <= 1e-6 else "FAIL",
        value=f"{losses[0]:.8f} vs {losses[1]:.8f}",
        threshold="|diff| <= 1e-6",
        note="without this a run's difference cannot be attributed to the change",
    )

    # Mode-dependence check on a fresh model: this stack has no dropout, so
    # eval() and train() must return the same loss. Using a *fresh* model keeps
    # the number independent of the overfit test above.
    mode_model = _small_model(vocab, seed=4)
    ids_m, mask_m, _ = mode_model.make_batch(over[:4])
    mode_model.net.eval()
    eval_loss = float(mode_model.loss(ids_m, mask_m).detach())
    mode_model.net.train()
    train_loss = float(mode_model.loss(ids_m, mask_m).detach())
    rep.add(
        "mech.train_eval_agree",
        "PASS" if abs(eval_loss - train_loss) <= 1e-5 else "FAIL",
        value=f"eval {eval_loss:.6f} vs train {train_loss:.6f}",
        threshold="|diff| <= 1e-5",
        note="no dropout in this model, so a difference means mode-dependent code",
    )
    return {"grad_norms": norms, "dynamics": dyn}


# ---------------------------------------------------------------------------
# D. distillation plumbing
# ---------------------------------------------------------------------------
def check_kd(
    rep: Report,
    teacher: Optional[Any],
    vocab: Any,
    rows: List[Dict[str, str]],
    pairs: List[Tuple[str, str]],
    student: Optional[Any] = None,
) -> None:
    print("\nD. distillation plumbing", flush=True)
    if teacher is None:
        rep.add("kd.targets", "BLOCKED", value="teacher unavailable")
        return
    import torch
    from ai.ed3n.kd_targets import AtomPrefixIndex

    atoms = AtomPrefixIndex(
        (vocab.stoi[a], a)
        for a in vocab.itos
        if a not in ("<pad>", "<bos>", "<eos>", "<unk>") and a
    )
    # max_len must match the run being prepared; a 64-atom budget would cut most
    # answers and make the coverage number look like a mapper problem.
    model = _small_model(vocab, seed=3, max_len=MAX_LEN)
    ref = student if student is not None else model
    ids_vocab = student.vocab if student is not None else vocab
    if student is not None:
        # Compare ``itos`` (what an id *means*), not ``to_dict()``: the stored
        # checkpoint records only the atom list, so the metadata keys (kind,
        # numeric_atoms) differ for reasons that cannot change an id.
        mismatch = next(
            (i for i, (a, b) in enumerate(zip(student.vocab.itos, vocab.itos)) if a != b),
            None,
        )
        same = mismatch is None and len(student.vocab) == len(vocab)
        rep.add(
            "kd.vocab_matches_checkpoint",
            "PASS" if same else "FAIL",
            value=f"checkpoint {len(student.vocab)} atoms vs data {len(vocab)}"
            + ("" if same else f", first difference at {mismatch}"),
            note="a rebuilt vocabulary must be identical, or atom ids from the corpus and "
            "from the checkpoint mean different things",
        )

    # Build (row, student ids, per-atom targets). The student position that
    # predicts answer atom k is ``start + k - 1`` — *not* the teacher's token
    # index. Mixing the two indexes silently trains atom k on the teacher's
    # distribution for a different character position.
    kd_rows: List[Dict[str, Any]] = []
    mapped: List[float] = []
    topk: List[float] = []
    q_gold: List[float] = []
    total_atoms = 0
    for row in rows[:8]:
        walk, scores, _spans = teacher.align(row["input"], row["output"])
        if scores is None:
            continue
        ids_s, start, _ = ref._encode(row["input"], row["output"])
        targets: List[Tuple[int, Any, int]] = []
        total_atoms += len(walk)
        for atom_index, tgt in teacher.targets(walk, scores, atoms, top_k=64):
            pos = start + atom_index - 1
            if pos < 0 or pos + 1 >= len(ids_s):
                continue
            mapped.append(tgt.mapped_mass)
            topk.append(tgt.topk_mass)
            gold_id = int(ids_vocab.stoi.get(walk[atom_index].text, -1))
            hit = tgt.atom_ids == gold_id if gold_id >= 0 else None
            q_gold.append(float(tgt.probs[hit].sum()) if hit is not None else 0.0)
            targets.append((pos, tgt, gold_id))
        kd_rows.append({"ids": ids_s, "targets": targets})

    # One canonical loss path: build a KdCache over exactly these rows and let
    # the trainer's own ``batch_loss`` produce the term. A separate local
    # implementation is how the subset-softmax variant survived unnoticed.
    from ai.ed3n.kd_cache import KdCache

    kd_cache = KdCache.build(
        (
            (entry["ids"], 0, [(pos, tgt) for pos, tgt, _gid in entry["targets"]])
            for entry in kd_rows
        ),
        ids_vocab.itos,
    )

    if not mapped:
        rep.add("kd.targets", "BLOCKED", value="no mappable positions")
        return
    mean_mapped = sum(mapped) / len(mapped)
    rep.add(
        "kd.target_mass_mapped",
        "PASS" if mean_mapped >= 0.5 else "FAIL",
        value=f"{mean_mapped:.3f} of top-64 mass (top-64 holds {sum(topk) / len(topk):.3f} of all mass)",
        threshold=">=0.5",
        note="how much of the teacher's preference survives the tokeniser mismatch; "
        "below 0.5 the 'soft' target is a hard label in disguise",
    )
    covered = len(mapped) / max(1, total_atoms)
    rep.add(
        "kd.answer_coverage",
        "PASS" if covered >= 0.5 else "FAIL",
        value=f"{len(mapped)}/{total_atoms} answer atoms ({covered:.1%})",
        threshold=">=50%",
        note="atoms that get a soft target at all; the rest keep their hard label",
    )
    mean_q = sum(q_gold) / len(q_gold)
    present = sum(1 for q in q_gold if q > 0.0) / len(q_gold)
    rep.add(
        "kd.gold_in_target_share",
        "PASS" if present >= 0.95 else "FAIL",
        value=f"{present:.1%} of targets contain the gold atom",
        threshold=">=95%",
        note="the restricted KL pulls a missing atom toward zero mass, so a target "
        "without the gold atom actively un-teaches the answer",
    )
    rep.add(
        "kd.gold_mass",
        "INFO",
        value=f"{mean_q:.4f} mean target mass on the gold atom",
        note="the teacher's own CE implies ~exp(-CE); a much lower value means the "
        "projection, not the teacher, is deciding what the student learns",
    )

    if student is not None:
        # The decisive, non-arbitrary comparison: at the very positions distillation
        # would train, does the teacher put more mass on the correct atom than the
        # student already does? If not, distilling pulls the student away from the
        # answer, whatever the aggregate loss says.
        p_student: List[float] = []
        with torch.no_grad():
            for entry in kd_rows:
                ids_t = torch.as_tensor([entry["ids"]], dtype=torch.long, device=student.device)
                logits = student.net(ids_t)[0]
                soft = torch.softmax(logits.float(), dim=-1)
                for pos, _tgt, gid in entry["targets"]:
                    if gid < 0 or pos < 0 or pos >= soft.shape[0]:
                        continue
                    p_student.append(float(soft[pos, gid]))
        if p_student:
            mean_p = sum(p_student) / len(p_student)
            rep.add(
                "kd.teacher_beats_student_on_gold",
                "PASS" if mean_q > mean_p else "FAIL",
                value=f"teacher q(gold)={mean_q:.4f} vs student p(gold)={mean_p:.4f} "
                f"over {len(p_student)} positions",
                threshold="teacher > student",
                note="relative, not a self-set absolute bar: distillation only helps if the "
                "teacher knows the answer better than the student at that position",
            )

    def kd_loss() -> Any:
        """The training objective itself — same code the trainer runs.

        Delegated to :meth:`ai.ed3n.kd_cache.KdCache.batch_loss` instead of a
        second copy here: a local copy is how the subset-softmax form survived
        long enough to be quoted in the docs. That form renormalised over the
        target atoms, so the term could fall while the model predicted nothing;
        ``batch_loss`` keeps the full softmax and only the *mapped* part of the
        teacher's mass (``q`` sums to 1 over the atoms the projection retained).
        """
        terms = []
        for index, entry in enumerate(kd_rows):
            ids_s = torch.as_tensor([entry["ids"]], dtype=torch.long, device=model.device)
            hidden = model.net.encode(ids_s)[:, :-1, :]
            term = kd_cache.batch_loss(model.net, hidden, [index])
            if term is not None:
                terms.append(term)
        if not terms:
            return sum(p.sum() for p in model.net.parameters()) * 0.0
        return torch.stack(terms).mean()

    loss = kd_loss()
    loss.backward()
    w_rec_grad = math.sqrt(
        sum(
            float(p.grad.detach().pow(2).sum())
            for name, p in model.net.named_parameters()
            if name.startswith("w_rec") and p.grad is not None
        )
    )
    embed_grad = math.sqrt(
        sum(
            float(p.grad.detach().pow(2).sum())
            for name, p in model.net.named_parameters()
            if name.startswith("embed") and p.grad is not None
        )
    )
    rep.add(
        "kd.loss_is_differentiable",
        "PASS" if loss.requires_grad and w_rec_grad > 0 and embed_grad > 0 else "FAIL",
        value=f"loss={float(loss.detach()):.3f} grad(embed)={embed_grad:.3e} grad(w_rec)={w_rec_grad:.3e}",
        note="the KD target must train the recurrent stack, not only the head",
    )

    opt = torch.optim.Adam(model.net.parameters(), lr=3e-3)
    first = last = None
    for step in range(30):
        opt.zero_grad()
        step_loss = kd_loss()
        step_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.net.parameters(), 1.0)
        opt.step()
        if step == 0:
            first = float(step_loss.detach())
        last = float(step_loss.detach())
    ratio = last / max(1e-9, first)
    rep.add(
        "kd.can_learn",
        "PASS" if ratio <= 0.6 else "FAIL",
        value=f"{first:.3f} -> {last:.3f} (x{ratio:.3f})",
        threshold="<= 0.6x after 30 steps",
        note="the plumbing computes a target the optimizer can actually reduce",
    )


# ---------------------------------------------------------------------------
# E. checkpoint dynamics
# ---------------------------------------------------------------------------
def _load_student(ckpt: Path) -> Optional[Any]:
    """Load the checkpoint once; D and E both need the real student."""
    if not ckpt.exists():
        return None
    from ai.ed3n.token_snn import TokenSNN

    return TokenSNN.load(ckpt, map_location="cpu", device="auto")


def _model_ce(model: Any, rows: Sequence[Dict[str, str]]) -> Tuple[Optional[float], int]:
    """Cross-entropy of the checkpoint on answer atoms (same span as the floor)."""
    import torch

    total = 0.0
    n = 0
    model.net.eval()
    with torch.no_grad():
        for row in rows:
            ids, start, _ = model._encode(row["input"], row["output"])
            if len(ids) - start <= 1:
                continue
            t = torch.as_tensor([ids], dtype=torch.long, device=model.device)
            logits = model.net(t)[0]
            logp = torch.log_softmax(logits.float(), dim=-1)
            for i in range(start, len(ids) - 1):
                total -= float(logp[i - 1, ids[i]])
                n += 1
    return (total / n if n else None), n


def check_checkpoint(
    rep: Report,
    model: Optional[Any],
    rows: List[Dict[str, str]],
    val_rows: Sequence[Dict[str, str]],
    floor: float,
) -> None:
    print("\nE. checkpoint dynamics", flush=True)
    if model is None:
        rep.add("ckpt.dynamics", "BLOCKED", value="no checkpoint", note=str(STUDENT_CKPT))
        return
    cfg = model.config
    pairs = [(r["input"], r["output"]) for r in rows[:2]]
    dyn = model.dynamics(pairs, n=2)
    layer = dyn["per_layer"][0]
    # ``beta`` and ``threshold`` are top-level in dynamics(); only the per-layer
    # firing statistics are per layer. Reading layer["threshold"] raised KeyError.
    pin_ratio = abs(dyn["threshold"]) / max(1e-9, cfg.theta_max) if cfg.theta_max else 0.0
    rep.add(
        "ckpt.threshold_headroom",
        "INFO",
        value=f"theta={dyn['threshold']} / cap={cfg.theta_max} ({pin_ratio:.3f})",
        note="a bounded threshold is *expected* to sit at its cap: the objective always "
        "prefers a sparser stack, and a higher cap is how the 108M run collapsed. This "
        "is why the gate is the gradient band below, not the distance to the cap",
    )
    rep.add(
        "ckpt.leak_not_collapsed",
        "PASS" if dyn["beta"] >= 0.6 else "FAIL",
        value=f"beta={dyn['beta']} configured {cfg.beta}",
        threshold=">= 0.6",
        note="memory horizon 1/(1-beta); 0.54 keeps ~2 tokens, i.e. no recurrence",
    )
    rep.add(
        "ckpt.gradient_band",
        "PASS" if layer["near_threshold"] >= 0.005 and layer["sensitive"] >= 0.05 else "FAIL",
        value=f"near_threshold={layer['near_threshold']} sensitive={layer['sensitive']} "
        f"spike_rate={layer['spike_rate']}",
        threshold="near>=0.005, sensitive>=0.05",
        note="pre-activations outside +-2 carry no surrogate gradient; outside +-0.1 ~none",
    )
    rep.add(
        "ckpt.verdict",
        "PASS" if dyn["verdict"] == "alive" else "FAIL",
        value=dyn["verdict"],
        note="dynamics()'s own verdict (it is a weaker test than the three above)",
    )

    if floor == float("inf") or not val_rows:
        rep.add("ckpt.val_ce_vs_floor", "BLOCKED", value="no floor / no rows")
        return
    import random as _random

    rnd = _random.Random(3)
    sample = list(val_rows)
    rnd.shuffle(sample)
    ce, atoms = _model_ce(model, sample[:400])
    if ce is None:
        rep.add("ckpt.val_ce_vs_floor", "BLOCKED", value="no scorable val atoms")
        return
    gap = floor - ce
    rep.add(
        "ckpt.val_ce_vs_floor",
        "PASS" if gap > 0.1 else "FAIL",
        value=f"checkpoint {ce:.3f} vs bigram floor {floor:.3f} (gap {gap:+.3f}) over {atoms} atoms",
        threshold="gap > 0.1 nats",
        note="the like-for-like number: below 0.1 the checkpoint is indistinguishable from a "
        "previous-token lookup, i.e. its recurrence is not carrying context",
    )


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="is the core ready to accept training?")
    ap.add_argument("--json", default="", help="write the full report here")
    ap.add_argument("--train-rows", type=int, default=0, help="0 = all")
    ap.add_argument("--teacher-rows", type=int, default=40)
    ap.add_argument("--skip-teacher", action="store_true")
    ap.add_argument("--skip-checkpoint", action="store_true")
    ap.add_argument("--student-report", default=str(STUDENT_REPORT))
    ap.add_argument("--checkpoint", default=str(STUDENT_CKPT), help="checkpoint to measure in E")
    args = ap.parse_args()

    started = time.time()
    rep = Report()
    print("Training readiness probe — measuring the rig, not the score", flush=True)
    if not TRAIN.exists() or not VAL.exists():
        print(f"missing data: {TRAIN} / {VAL}")
        return 1
    train = _rows(TRAIN, args.train_rows)
    val = _rows(VAL)

    from ai.ed3n.token_snn import TokenVocab

    # Build the vocabulary exactly as ``train_token_snn.py`` does. That script
    # hard-codes ``min_count=1`` ("rare words must stay composable") and only
    # takes ``max_vocab`` from the config; reading ``min_count`` from the
    # checkpoint's config record (2) produced a 31,081-atom vocabulary whose
    # atom ids meant something else entirely. Measured: min_count=1 on the
    # train split reproduces the checkpoint's 32,773 atoms *exactly*.
    run_config: Dict[str, Any] = {}
    if STUDENT_REPORT.exists():
        run_config = json.loads(STUDENT_REPORT.read_text(encoding="utf-8")).get("config", {})
    min_count = 1
    max_vocab = int(run_config.get("max_vocab", 32768))
    print(f"vocab: min_count={min_count} (trainer default) max_vocab={max_vocab}")

    info = check_data(rep, train, val, min_count, max_vocab)
    vocab = info["vocab"]
    encode = info["encode"]

    def atom_rows(rows: Sequence[Dict[str, str]]) -> List[List[int]]:
        out = []
        for row in rows:
            ids, start, _ = encode(row["input"], row["output"])
            if len(ids) - start > 1:
                out.append(ids[start:-1])
        return out

    sample_train = train[: min(len(train), 60000)]
    baselines = check_baselines(
        rep, atom_rows(sample_train), atom_rows(val), Path(args.student_report)
    )

    pairs = [(r["input"], r["output"]) for r in train[:64]]
    check_mechanics(rep, vocab, pairs)

    teacher = check_teacher(
        rep,
        train,
        val,
        vocab,
        baselines.get("floor", float("inf")),
        args.teacher_rows,
        args.skip_teacher,
    )
    student = None if args.skip_checkpoint else _load_student(Path(args.checkpoint))
    check_kd(rep, teacher, vocab, val[:8], pairs, student=student)
    check_checkpoint(rep, student, val[:8], val, baselines.get("floor", float("inf")))

    counts = rep.counts()
    elapsed = time.time() - started
    print("\n" + "=" * 72)
    print(f"readiness: {counts} in {elapsed:.0f}s")
    verdict = rep.verdict()
    if verdict == 1:
        print("❌ NOT READY — a check failed above; training now would measure the defect.")
    elif verdict == 2:
        print("⛔ INCOMPLETE — nothing failed, but a prerequisite is missing (see BLOCKED).")
    else:
        print("✅ READY — the data is clean, the graph trains, and the teacher is informative.")
    print("=" * 72)
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(
            json.dumps(
                {"checks": rep.rows, "counts": counts, "seconds": round(elapsed, 1)},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"wrote {args.json}")
    return verdict


if __name__ == "__main__":
    raise SystemExit(main())
