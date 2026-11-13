#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [A] [L3]
# LAYER: learning
# =============================================================================
"""Stage P: pantry deduction on the stage-L byte carrier (§49).

What this measures
------------------
Stage L (§47/§48) left a byte-level ``GRUCore`` that reads and writes text. Stage
P asks the next question, and it is falsifiable on its own: read eleven turns of
testimony and produce the person whose value falls inside the theft window.

The corpus is built so that no single turn holds the answer:

* every turn that names people names *everybody* (a roll call or a roster);
* evidence turns carry a value (a badge id or a colour) and name nobody;
* the first evidence row is wrong and is retracted in a later correction;
* the final question names only the item.

So the answer needs value -> roster -> person under a time filter, plus dropping
the retracted row. ``derive()`` in the generator is the solver, and it - not a
human - decides every target: the full session, the pre-correction prefix
(singleton on 98/200 sessions) and each ablation are all scored against it.

Why the gates are what they are
-------------------------------
No external anchor applies to a synthetic task, so the bar is computed from the
corpus itself: the model's 95% Wilson lower bound must clear the strongest
surface baseline's 95% upper bound (0.2500; chance is 0.1591). A format-only
control - same text, same steps, answers replaced by a random other actor - must
stay at chance, because §48.3 measured testimony at 0.248 BPC (format is nearly
free and a high score alone would prove nothing).

Deliberate limits
-----------------
* this is not language understanding and not a general reasoning claim;
* it changes no score: core stays 0.00/10;
* the stateful path stays opt-in and is not wired into production;
* a failing run does not prove "the core cannot reason", only that this carrier,
  this budget and this task did not do it.

Usage (registered command is in CORE_GAP_ANALYSIS.md §49.10)::

    ./.venv/bin/python scripts/train_pantry_deduction.py --smoke --device cpu
    ./.venv/bin/python scripts/train_pantry_deduction.py --control rand --out data/pantry_stage
    ./.venv/bin/python scripts/train_pantry_deduction.py --out data/pantry_stage
    ./.venv/bin/python scripts/train_pantry_deduction.py --check data/pantry_stage/<report>.json

Stage Q (§50) adds two flags and changes nothing by default. ``--aux-loss``
(λ, default 0.0 = stage P) adds ``λ · mean_k CE(head(h_k) → answer)`` over the
earlier turn boundaries, so each turn is only one turn away from the loss instead
of 11−k (§49.16 measured ~3 orders of magnitude lost per turn). Evaluation never
uses the auxiliary readout. ``--overfit N`` is Q1's instrument calibration: the
first N training sessions, marked ``overfit: true``, ignored when looking for the
format control::

    ./.venv/bin/python scripts/train_pantry_deduction.py --overfit 32 --epochs 100 \\
        --aux-loss 1.0 --device cpu --out data/pantry_stage/q_overfit
    ./.venv/bin/python scripts/train_pantry_deduction.py --aux-loss 1.0 --out data/pantry_stage/q
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

TASK_VERSION = "pantry-deduction-v1"

# §49.4 - the representation is L's, not a new one.
PAD_ID = 0
BOS_ID = 1
EOS_ID = 2
BYTE_OFFSET = 3
VOCAB_SIZE = BYTE_OFFSET + 256  # 259
HIDDEN = 128
EMB = 64
CHUNK_SECONDS = 60.0
NEWLINE = 10

# §49.5 - fixed before the run. A different value is a different registration.
SEED = 20261118
LEARNING_RATE = 5e-4
BATCH = 8
EPOCHS = 20
MAX_ANSWER_BYTES = 8

# §49.3 - the corpus is the same generator call as stage L.
PANTRY_SCRIPT = "scripts/gen_pantry_ecosystem.py"
PANTRY_SEED = 20261113
PANTRY_SESSIONS = 1000
HELDOUT_FRACTION = 0.2
TRAIN_SESSIONS = 800
HOLDOUT_SESSIONS = 200
TRAIN_BYTES = 1_014_924
HOLDOUT_BYTES = 254_050
TRAIN_DIGEST = "cbbe5265b2f065b15c170116d277c20eb508d822929e6f8865e59c19997d0179"
HOLDOUT_DIGEST = "2ef82f705aedbf957be04ad375021e383520e52d141d3c4e335393137871ba6a"

# §49.1 - the start point is L's checkpoint, pinned by hash.
#
# The hash is the *trained* weights (what the file contains). L's report field
# named ``weights_hash`` is the seed's initialisation instead: it was recorded
# before ``train()`` (§48.7 erratum), and L's L5 gate never compared it. Both
# values are pinned here so the difference cannot be papered over later.
L_CHECKPOINT = "data/text_stage/text_stage_20261113-212446.pt"
L_WEIGHTS_HASH = "sha256:77cb6af3cf2a9df9d3e26142ab2092720d99e8b74423f73d250ff942945ea825"
L_INIT_HASH = "sha256:a7843b34ef1dba6502f07645a0138dd2e3dc1d9af1eb010ccc0aca7c293d6c4b"
L_CHECKPOINT_SHA256 = "e2a6580ec06b1a8afe886adc5b955d9e7a10bba8996b782383f86b16370efdd4"
L_PARAMS = 124_611

# §49.6 - thresholds, with the quantity each one comes from.
FIT_SESSIONS = 200
FIT_FLOOR = 0.25
SURFACE_BASELINE_UPPER = 0.25
CHANCE_MARGIN = 0.10
GAP_MIN = 0.25
FLIP_MIN = 0.50
TOP_SHARE_MAX = 0.35

# §50 - stage Q changes one thing (an auxiliary readout at each turn boundary)
# and adds one calibration arm (overfit). Neither number is a capability claim:
# 0.0 is stage P's behaviour, and OVERFIT_FLOOR is an instrument check on 32
# training sessions, never a generalisation rate.
AUX_LAMBDA_DEFAULT = 0.0
AUX_MODE_DEFAULT = "all"
OVERFIT_FLOOR = 0.90

SAMPLE_ROWS = 3

VARIANTS = ("full", "reset", "no_correction", "no_roster", "no_bounds", "skip_al")
WINDOW_TAGS = {"window_lower_bound", "window_upper_bound"}


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_head() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            check=False,
            timeout=30,
        )
        return out.stdout.decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _chunks(rows: Sequence[Any], size: int) -> List[Sequence[Any]]:
    return [rows[start : start + size] for start in range(0, len(rows), size)]


def wilson(successes: int, total: int, z: float = 1.96) -> Tuple[float, float]:
    """95% Wilson interval; degenerate counts are reported honestly, not hidden."""
    if total <= 0:
        return 0.0, 1.0
    p = successes / total
    denominator = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    spread = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total))
    return (centre - spread) / denominator, (centre + spread) / denominator


def _round(value: Optional[float], digits: int = 4) -> Optional[float]:
    return None if value is None else round(float(value), digits)


def _find_control_report(
    folder: Path, aux_lambda: Optional[float] = None, aux_mode: Optional[str] = None
) -> Optional[Path]:
    """The newest finished F-rand report in ``folder``, ignoring smoke/overfit runs.

    §49.10 requires the control to finish first. Picking the newest scored run
    of the right arm is enough here: this is a single-task driver, not a queue,
    and the digest check in :func:`run` refuses a control measured on a
    different held-out corpus.

    §50.4 additionally requires the control to use the *same* auxiliary loss, so
    ``aux_lambda`` filters by it; otherwise a stage-P control (λ=0) could quietly
    stand in for a stage-Q arm and Q7 would compare two different trainings.
    §51.4 extends that to ``aux_mode``: "supervise every boundary" and
    "supervise only resolvable boundaries" are different objectives, and a
    control trained under one cannot validate the other.
    """
    if not folder.is_dir():
        return None
    candidates = []
    for path in folder.glob("pantry_deduction_*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if payload.get("control_arm") != "rand" or payload.get("smoke"):
            continue
        if payload.get("overfit"):
            continue
        if payload.get("task_version") != TASK_VERSION:
            continue
        if aux_lambda is not None:
            recorded = float((payload.get("config") or {}).get("aux_lambda") or 0.0)
            if abs(recorded - float(aux_lambda)) > 1e-12:
                continue
        if aux_mode is not None:
            recorded_mode = str((payload.get("config") or {}).get("aux_mode") or AUX_MODE_DEFAULT)
            if recorded_mode != aux_mode:
                continue
        candidates.append(path)
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.stat().st_mtime)


# --------------------------------------------------------------------------- #
# corpus
# --------------------------------------------------------------------------- #
def _load_generator() -> Any:
    spec = importlib.util.spec_from_file_location("pantry_for_stage_p", REPO_ROOT / PANTRY_SCRIPT)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {PANTRY_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["pantry_for_stage_p"] = module
    spec.loader.exec_module(module)
    return module


def render_session(session: Dict[str, Any]) -> bytes:
    """Exactly the stage-L rendering: turns joined by newlines, trailing newline."""
    return ("\n".join(turn["user_input"] for turn in session["turns"]) + "\n").encode("utf-8")


def turn_tokens(session: Dict[str, Any]) -> List[List[int]]:
    """Per-turn token ids; each turn keeps its own terminator.

    Concatenating these reproduces :func:`render_session` byte for byte, which is
    what lets the model be fed turn by turn without changing the text.
    """
    out: List[List[int]] = []
    for turn in session["turns"]:
        payload = (turn["user_input"] + "\n").encode("utf-8")
        out.append([BYTE_OFFSET + byte for byte in payload])
    return out


def turn_gaps(session: Dict[str, Any]) -> List[float]:
    return [float(turn["dt_s"]) for turn in session["turns"]]


def drop_indices(session: Dict[str, Any], variant: str) -> set:
    """Which turns the variant removes (registered in §49.9, never tuned)."""
    meta = session["session_meta"]
    if variant == "no_correction":
        return {int(meta["correction_turn"])}
    if variant == "no_roster":
        return {int(meta["roster_turn"])}
    if variant == "no_bounds":
        return {
            int(turn["turn_id"])
            for turn in session["turns"]
            if WINDOW_TAGS & set(turn.get("expected_internal_focus") or ())
        }
    return set()


def solver_candidates(module: Any, session: Dict[str, Any], dropped: set) -> List[str]:
    """What ``derive()`` concludes from the turns that are actually shown."""
    asserts = [
        (turn["turn_id"], item)
        for turn in session["turns"]
        if int(turn["turn_id"]) not in dropped
        for item in turn.get("asserts", [])
    ]
    return module.derive(asserts, session["environment"]["actors"])


def load_corpus(*, sessions: int = PANTRY_SESSIONS, seed: int = PANTRY_SEED) -> Dict[str, Any]:
    """Generate the registered corpus, run the data gates, and pin the digests."""
    module = _load_generator()
    synthesizer = module.PantryEcosystemSynthesizer(
        seed=seed, sessions=sessions, heldout_fraction=HELDOUT_FRACTION
    )
    splits = synthesizer.generate()
    problems = module.PantryEcosystemSynthesizer.validate(splits)
    if problems:
        head = "; ".join(problems[:5])
        raise SystemExit(f"the corpus fails its own gates ({len(problems)}): {head}")

    train = list(splits["train"])
    heldout = list(splits["heldout"])
    train_bytes = b"".join(render_session(row) for row in train)
    heldout_bytes = b"".join(render_session(row) for row in heldout)
    return {
        "module": module,
        "train": train,
        "heldout": heldout,
        "meta": {
            "source": PANTRY_SCRIPT,
            "generated": True,
            "seed": seed,
            "sessions": sessions,
            "heldout_fraction": HELDOUT_FRACTION,
            "train_sessions": len(train),
            "heldout_sessions": len(heldout),
            "train_bytes": len(train_bytes),
            "heldout_bytes": len(heldout_bytes),
            "train_digest": _digest(train_bytes),
            "heldout_digest": _digest(heldout_bytes),
            "registered_sizes_match": (
                len(train) == TRAIN_SESSIONS and len(heldout) == HOLDOUT_SESSIONS
            ),
            "registered_digests_match": (
                _digest(train_bytes) == TRAIN_DIGEST and _digest(heldout_bytes) == HOLDOUT_DIGEST
            ),
        },
    }


def leak_report(sessions: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """The answer must not be readable from the question, and no oracle leaks in."""
    problems: List[str] = []
    for session in sessions:
        sid = session["session_id"]
        text = render_session(session).decode("utf-8", "replace")
        oracle = session["ground_truth_oracle"]
        if oracle["evidence_tag"] in text:
            problems.append(f"{sid}: evidence_tag appears in the text")
        if "ground_truth_oracle" in text:
            problems.append(f"{sid}: oracle key appears in the text")
        question = session["turns"][-1]["user_input"]
        if oracle["culprit"] in question:
            problems.append(f"{sid}: the answer name appears in the final question")
        # rendered text must be exactly the turns' user_input and nothing else
        rebuilt = "\n".join(turn["user_input"] for turn in session["turns"]) + "\n"
        if rebuilt != text:
            problems.append(f"{sid}: rendered text is not the turns")
    return {"clean": not problems, "problems": problems[:10], "checked": len(sessions)}


# --------------------------------------------------------------------------- #
# model plumbing
# --------------------------------------------------------------------------- #
def build_core(*, hidden: int = HIDDEN, emb: int = EMB, device: str, seed: int = SEED) -> Any:
    from ai.core.stateful_decoder import GRUCore

    return GRUCore(
        VOCAB_SIZE,
        hidden=hidden,
        emb=emb,
        chunk_seconds=CHUNK_SECONDS,
        seed=seed,
        device=device,
    )


def resolve_device(requested: str) -> str:
    from core.system.config.compute_device import resolve_torch_device

    if requested == "auto":
        return resolve_torch_device()
    return requested


def load_stage_l(core: Any, path: Path) -> str:
    """Load L's checkpoint and refuse to start from anything else (§49.1)."""
    if not path.exists():
        raise SystemExit(f"missing the stage-L checkpoint: {path}")
    file_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if file_digest != L_CHECKPOINT_SHA256:
        raise SystemExit(
            f"stage-L checkpoint file sha256 {file_digest[:12]}… != registered "
            f"{L_CHECKPOINT_SHA256[:12]}…; the start point is not the artifact §49.1 names"
        )
    core.load_weights(str(path), strict_config=True)
    digest = core.weights_hash()
    if digest != L_WEIGHTS_HASH:
        raise SystemExit(
            f"stage-L checkpoint hash {digest} != registered {L_WEIGHTS_HASH}; "
            "the start point is not the one §49.1 names"
        )
    if digest == L_INIT_HASH:  # pragma: no cover - only if the pin is wrong
        raise SystemExit("the start point is the initialisation, not a trained carrier")
    if core.parameter_count() != L_PARAMS:
        raise SystemExit(f"stage-L checkpoint has {core.parameter_count()} params != {L_PARAMS}")
    return digest


def _run_turn(core: Any, rows: Sequence[Sequence[int]], hidden: Any) -> Any:
    """Feed one turn per sample and keep the state at each sample's own length.

    Right-padding is only used to batch the arithmetic: the gathered state is the
    one computed from that sample's real tokens, so the pad never enters the
    state (``tests/test_pantry_deduction.py`` checks this against ``ai_step``).
    """
    torch = core._torch
    lengths = [len(row) for row in rows]
    if not rows or min(lengths) <= 0:
        raise ValueError("empty turn")
    width = max(lengths)
    pad = torch.zeros((len(rows), width), dtype=torch.long, device=hidden.device)
    for index, row in enumerate(rows):
        pad[index, : len(row)] = torch.as_tensor(row, dtype=torch.long, device=hidden.device)
    states = []
    for position in range(width):
        hidden = core.cell(core.embedding(pad[:, position]), hidden)
        states.append(hidden)
    stacked = torch.stack(states, dim=1)
    picks = torch.as_tensor([n - 1 for n in lengths], device=hidden.device).reshape(-1, 1, 1)
    return stacked.gather(1, picks.expand(-1, 1, stacked.shape[-1])).reshape(len(rows), -1)


def run_session(
    core: Any,
    batch_turns: Sequence[Sequence[Sequence[int]]],
    batch_gaps: Sequence[Sequence[float]],
    state: Any = None,
    *,
    reset_before_last: bool = False,
    boundaries: Optional[List[Any]] = None,
) -> Tuple[Any, Any]:
    """Run whole sessions; ``al_step`` happens *between* turns, never after.

    ``boundaries`` is the §50.2 hook: when a list is passed, each turn's hidden
    state is appended to it (the graph is kept, so training can read out from
    every turn). When it is ``None`` nothing changes - stage P's run is bitwise
    the same computation.
    """
    torch = core._torch
    batch = len(batch_turns)
    turns = len(batch_turns[0])
    if any(len(row) != turns for row in batch_turns):
        raise ValueError("all samples in a batch must have the same number of turns")
    state = state if state is not None else core.init_state(batch)
    hidden = state.tensors["h"]
    for index in range(turns):
        if index > 0:
            if reset_before_last and index == turns - 1:
                hidden = torch.zeros_like(hidden)
            else:
                state.tensors["h"] = hidden
                dt = torch.as_tensor(
                    [row[index] for row in batch_gaps], dtype=hidden.dtype, device=hidden.device
                )
                state = core.al_step(dt, state)
                hidden = state.tensors["h"]
        hidden = _run_turn(core, [row[index] for row in batch_turns], hidden)
        # one ai_step per turn, so state_version/ticks mean what they mean in
        # the contract (al_step bumps for chunks; this bumps for the turn)
        state.tensors["h"] = hidden
        state.bump()
        if boundaries is not None:
            boundaries.append(hidden)
    return state, hidden


def _answer_loss(core: Any, hidden: Any, answers: Sequence[Sequence[int]]) -> Any:
    import torch.nn.functional as functional

    torch = core._torch
    longest = max(len(answer) for answer in answers)
    logits = []
    current = hidden
    for position in range(longest):
        logits.append(core.head(current))
        tokens = [answer[position] if position < len(answer) else PAD_ID for answer in answers]
        if position < longest - 1:
            feed = torch.as_tensor(tokens, dtype=torch.long, device=current.device)
            current = core.cell(core.embedding(feed), current)
    stacked = torch.stack(logits, dim=1)
    targets = torch.full((len(answers), longest), -100, dtype=torch.long, device=stacked.device)
    for index, answer in enumerate(answers):
        targets[index, : len(answer)] = torch.as_tensor(
            answer, dtype=torch.long, device=stacked.device
        )
    return functional.cross_entropy(
        stacked.reshape(-1, VOCAB_SIZE), targets.reshape(-1), ignore_index=-100
    )


def _training_loss(
    core: Any,
    boundaries: Sequence[Any],
    answers: Sequence[Sequence[int]],
    aux_lambda: float,
    prefix_answers: Optional[Sequence[Sequence[Optional[Sequence[int]]]]] = None,
) -> Tuple[Any, Any, Optional[Any]]:
    """The registered §50.2 objective: main CE plus the mean CE at earlier turns.

    Each auxiliary term starts *at that boundary*, so turn k's evidence is one
    turn away from the answer loss rather than 11−k (§49.16). With λ=0 no extra
    term is computed at all, which is what keeps stage P bitwise unchanged.

    ``prefix_answers`` (stage R, §51.2) changes *what* the earlier boundaries are
    asked, never how many: entry ``[sample][k]`` is that boundary's own unique
    ``derive()`` answer, or ``None`` where the prefix has no unique answer. The
    auxiliary term then averages only over the (boundary, sample) pairs that
    have an answer, so the model is never asked to answer a question that is not
    yet answerable - the failure §50.13 measured in stage Q's arm.
    """
    main = _answer_loss(core, boundaries[-1], answers)
    earlier = list(boundaries[:-1])
    if aux_lambda <= 0.0 or not earlier:
        return main, main, None
    if prefix_answers is None:
        auxiliary = sum(_answer_loss(core, hidden, answers) for hidden in earlier) / len(earlier)
        return main + aux_lambda * auxiliary, main, auxiliary

    terms = []
    for index, hidden in enumerate(earlier):
        rows = [prefix_answers[sample][index] for sample in range(len(answers))]
        keep = [position for position, answer in enumerate(rows) if answer is not None]
        if not keep:
            continue
        picked = [rows[position] for position in keep]
        index_tensor = hidden.new_tensor(keep).long()
        terms.append(_answer_loss(core, hidden.index_select(0, index_tensor), picked))
    if not terms:
        return main, main, None
    auxiliary = sum(terms) / len(terms)
    return main + aux_lambda * auxiliary, main, auxiliary


def generate_bytes(core: Any, hidden: Any, limit: int = MAX_ANSWER_BYTES) -> List[bytes]:
    """Greedy decode: stop at a newline, a special token, or ``limit`` bytes."""
    batch = int(hidden.shape[0])
    produced: List[List[int]] = [[] for _ in range(batch)]
    finished = [False] * batch
    current = hidden
    for _ in range(limit):
        tokens = core.head(current).argmax(dim=-1)
        for index in range(batch):
            if finished[index]:
                continue
            token = int(tokens[index])
            if token < BYTE_OFFSET or token == EOS_ID:
                finished[index] = True
                continue
            byte = token - BYTE_OFFSET
            if byte == NEWLINE:
                finished[index] = True
                continue
            produced[index].append(byte)
        if all(finished):
            break
        current = core.cell(core.embedding(tokens), current)
    return [bytes(item) for item in produced]


def rank_actor(core: Any, hidden: Any, candidates: Sequence[str]) -> str:
    """Sequence log-likelihood of each name (plus terminator); argmax wins."""
    import torch.nn.functional as functional

    torch = core._torch
    best_name = ""
    best_score = -math.inf
    for name in candidates:
        ids = [BYTE_OFFSET + byte for byte in (name + "\n").encode("utf-8")]
        current = hidden
        total = 0.0
        for token in ids:
            logits = core.head(current)
            total += float(functional.log_softmax(logits, dim=-1)[0, token])
            feed = torch.as_tensor([token], dtype=torch.long, device=current.device)
            current = core.cell(core.embedding(feed), current)
        if total > best_score:
            best_score = total
            best_name = name
    return best_name


# --------------------------------------------------------------------------- #
# training
# --------------------------------------------------------------------------- #
def answer_ids(session: Dict[str, Any], _seed: int = 0) -> List[int]:
    payload = (session["ground_truth_oracle"]["culprit"] + "\n").encode("utf-8")
    return [BYTE_OFFSET + byte for byte in payload]


def random_answer_ids(session: Dict[str, Any], seed: int) -> List[int]:
    """Format-only control: a real actor, never the culprit (§49.6 G8)."""
    actors = list(session["environment"]["actors"])
    culprit = session["ground_truth_oracle"]["culprit"]
    rng = random.Random(f"{seed}:{session['session_meta']['index']}:rand")
    choice = rng.choice([name for name in actors if name != culprit])
    return [BYTE_OFFSET + byte for byte in (choice + "\n").encode("utf-8")]


def build_samples(
    sessions: Sequence[Dict[str, Any]],
    *,
    seed: int,
    control: Optional[str],
    prefix_module: Any = None,
) -> List[Dict[str, Any]]:
    """Turn sessions into training rows.

    ``prefix_module`` (stage R, §51.2) additionally records, for every earlier
    turn boundary, that boundary's own ``derive()`` answer - ``None`` where the
    prefix does not yet determine one. It costs nothing at λ=0 and is ignored
    there, so stage P/Q reports stay reproducible from this function.
    """
    picker = random_answer_ids if control == "rand" else answer_ids
    rows = []
    for session in sessions:
        row = {
            "turns": turn_tokens(session),
            "gaps": turn_gaps(session),
            "answer": picker(session, seed),
            "index": int(session["session_meta"]["index"]),
            "session": session,
        }
        if prefix_module is not None:
            boundaries = len(session["turns"]) - 1
            if control == "rand":
                # the format-only arm must not see the real answer even as an
                # auxiliary target, or the control would leak what it controls
                row["prefix_answers"] = [row["answer"]] * boundaries
            else:
                row["prefix_answers"] = []
                for upto in range(boundaries):
                    candidates = prefix_candidates(prefix_module, session, upto)
                    if len(candidates) != 1:
                        row["prefix_answers"].append(None)
                        continue
                    payload = (candidates[0] + "\n").encode("utf-8")
                    row["prefix_answers"].append([BYTE_OFFSET + byte for byte in payload])
        rows.append(row)
    return rows


def train(
    core: Any,
    samples: Sequence[Dict[str, Any]],
    *,
    epochs: int,
    batch: int,
    lr: float,
    seed: int,
    aux_lambda: float = AUX_LAMBDA_DEFAULT,
    aux_mode: str = AUX_MODE_DEFAULT,
) -> List[Dict[str, Any]]:
    torch = core._torch
    optimiser = torch.optim.Adam(list(core.parameters()), lr=lr)
    history: List[Dict[str, Any]] = []
    started = time.time()
    for epoch in range(1, epochs + 1):
        order = list(range(len(samples)))
        random.Random(f"{seed}:{epoch}").shuffle(order)
        running = 0.0
        running_main = 0.0
        running_aux = 0.0
        seen = 0
        for start in range(0, len(order), batch):
            rows = [samples[index] for index in order[start : start + batch]]
            boundaries: Optional[List[Any]] = [] if aux_lambda > 0.0 else None
            state, hidden = run_session(
                core,
                [row["turns"] for row in rows],
                [row["gaps"] for row in rows],
                boundaries=boundaries,
            )
            total, main_loss, aux_loss = _training_loss(
                core,
                boundaries if boundaries is not None else [hidden],
                [row["answer"] for row in rows],
                aux_lambda,
                (
                    [row["prefix_answers"] for row in rows]
                    if aux_mode == "resolvable" and boundaries is not None
                    else None
                ),
            )
            optimiser.zero_grad(set_to_none=True)
            total.backward()
            torch.nn.utils.clip_grad_norm_(list(core.parameters()), 1.0)
            optimiser.step()
            core.invalidate_hash()
            running += float(total.detach().cpu())
            running_main += float(main_loss.detach().cpu())
            if aux_loss is not None:
                running_aux += float(aux_loss.detach().cpu())
            seen += 1
        history.append(
            {
                "epoch": epoch,
                "batches": seen,
                "mean_loss": round(running / max(1, seen), 4),
                "mean_main_loss": round(running_main / max(1, seen), 4),
                "mean_aux_loss": (
                    round(running_aux / max(1, seen), 4) if aux_lambda > 0.0 else None
                ),
                "aux_lambda": aux_lambda,
                "seconds": round(time.time() - started, 1),
            }
        )
        print(
            f"  epoch {epoch}/{epochs}  batches={seen}  "
            f"loss={history[-1]['mean_loss']:.4f}  "
            f"main={history[-1]['mean_main_loss']:.4f}  "
            f"aux={history[-1]['mean_aux_loss']}  elapsed={history[-1]['seconds']:.0f}s",
            flush=True,
        )
    return history


# --------------------------------------------------------------------------- #
# evaluation
# --------------------------------------------------------------------------- #
def _decoded(data: bytes) -> str:
    return data.decode("utf-8", "replace").strip()


def evaluate(
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    variant: str,
    *,
    module: Any,
    batch: int = 32,
) -> List[Dict[str, Any]]:
    """One record per session: prediction, ranking, and the solver's target."""
    torch = core._torch
    records: List[Dict[str, Any]] = []
    core.eval()
    with torch.no_grad():
        for chunk in _chunks(list(sessions), batch):
            turns: List[List[List[int]]] = []
            gaps: List[List[float]] = []
            targets: List[Optional[str]] = []
            for session in chunk:
                dropped = drop_indices(session, variant)
                kept = [turn for turn in session["turns"] if int(turn["turn_id"]) not in dropped]
                turns.append(
                    [
                        [BYTE_OFFSET + byte for byte in (turn["user_input"] + "\n").encode("utf-8")]
                        for turn in kept
                    ]
                )
                gaps.append([float(turn["dt_s"]) for turn in kept])
                if variant == "skip_al":
                    gaps[-1] = [0.0 for _ in gaps[-1]]
                candidates = solver_candidates(module, session, dropped)
                targets.append(candidates[0] if len(candidates) == 1 else None)

            if not turns or min(len(row) for row in turns) == 0:
                raise SystemExit(f"variant {variant} removed every turn of a session")
            if len({len(row) for row in turns}) != 1:
                raise SystemExit(f"variant {variant} left sessions with different turn counts")

            reset = variant == "reset"
            state, hidden = run_session(core, turns, gaps, reset_before_last=reset)
            produced = generate_bytes(core, hidden)
            for index, session in enumerate(chunk):
                ranked = rank_actor(
                    core, hidden[index : index + 1], session["environment"]["actors"]
                )
                prediction = _decoded(produced[index])
                records.append(
                    {
                        "session_id": session["session_id"],
                        "chain": session["session_meta"]["chain"],
                        "actors": len(session["environment"]["actors"]),
                        "target": targets[index],
                        "prediction": prediction,
                        "ranking": ranked,
                        "generated_bytes": produced[index].hex(),
                    }
                )
    return records


def summarise(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Exact/ranking rates over the records that have a solver-derived target."""
    targeted = [row for row in records if row["target"]]
    total = len(targeted)
    correct = sum(1 for row in targeted if row["prediction"] == row["target"])
    ranked = sum(1 for row in targeted if row["ranking"] == row["target"])
    chance = sum(1.0 / row["actors"] for row in targeted) / total if total else 0.0
    low, high = wilson(correct, total)
    rank_low, rank_high = wilson(ranked, total)
    counts: Dict[str, int] = {}
    for row in records:
        counts[row["prediction"]] = counts.get(row["prediction"], 0) + 1
    top_name, top_count = ("", 0)
    if counts:
        top_name, top_count = max(counts.items(), key=lambda item: item[1])
    per_chain: Dict[str, Dict[str, Any]] = {}
    for row in targeted:
        bucket = per_chain.setdefault(
            row["chain"], {"n": 0, "correct": 0, "ranked": 0, "chance": 0.0}
        )
        bucket["n"] += 1
        bucket["correct"] += int(row["prediction"] == row["target"])
        bucket["ranked"] += int(row["ranking"] == row["target"])
        bucket["chance"] += 1.0 / row["actors"]
    for bucket in per_chain.values():
        bucket["exact"] = _round(bucket["correct"] / bucket["n"]) if bucket["n"] else None
        bucket["ranking"] = _round(bucket["ranked"] / bucket["n"]) if bucket["n"] else None
        bucket["chance"] = _round(bucket["chance"] / bucket["n"]) if bucket["n"] else None
    return {
        "n": total,
        "correct": correct,
        "exact": _round(correct / total) if total else None,
        "chance": _round(chance),
        "wilson_lower": _round(low),
        "wilson_upper": _round(high),
        "ranking_correct": ranked,
        "ranking_exact": _round(ranked / total) if total else None,
        "ranking_lower": _round(rank_low),
        "ranking_upper": _round(rank_high),
        "distinct_predictions": len(counts),
        "top_prediction": top_name,
        "top_share": _round(top_count / len(records)) if records else None,
        "per_chain": per_chain,
        "samples": [
            {
                "session": row["session_id"],
                "target": row["target"],
                "prediction": row["prediction"],
                "ranking": row["ranking"],
            }
            for row in records[:SAMPLE_ROWS]
        ],
    }


def agreement(
    records: Sequence[Dict[str, Any]], reference: Sequence[Dict[str, Any]]
) -> Dict[str, Any]:
    """How often an ablation answers the same name as the full session."""
    other = {row["session_id"]: row["prediction"] for row in reference}
    rows = [row for row in records if row["session_id"] in other]
    same = sum(1 for row in rows if row["prediction"] == other[row["session_id"]])
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row["prediction"]] = counts.get(row["prediction"], 0) + 1
    top = max(counts.items(), key=lambda item: item[1])[1] if counts else 0
    return {
        "n": len(rows),
        "same_as_full": same,
        "same_rate": _round(same / len(rows)) if rows else None,
        "top_share": _round(top / len(rows)) if rows else None,
    }


def flip_summary(full: Sequence[Dict[str, Any]], pre: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """On sessions where the pre-correction prefix has one answer, does it flip?

    ``flip_rate`` is the strong reading of §49.6 G6: the pre-correction state
    answers the trap *and* the full state answers the culprit. ``changed_rate``
    (any different name) is reported beside it as a diagnostic, because a model
    that is simply wrong twice would otherwise look like it retracted.
    """
    pre_map = {row["session_id"]: row for row in pre}
    pairs = []
    for row in full:
        other = pre_map.get(row["session_id"])
        if other is None or not other["target"] or not row["target"]:
            continue
        pairs.append(
            {
                "session": row["session_id"],
                "chain": row["chain"],
                "pre_target": other["target"],
                "pre_prediction": other["prediction"],
                "full_target": row["target"],
                "full_prediction": row["prediction"],
                "changed": other["prediction"] != row["prediction"],
                "pre_right": other["prediction"] == other["target"],
                "full_right": row["prediction"] == row["target"],
            }
        )
    changed = sum(1 for pair in pairs if pair["changed"])
    both_right = sum(1 for pair in pairs if pair["pre_right"] and pair["full_right"])
    full_right = sum(1 for pair in pairs if pair["full_right"])
    pre_right = sum(1 for pair in pairs if pair["pre_right"])
    low, high = wilson(both_right, len(pairs))
    return {
        "n": len(pairs),
        "changed": changed,
        "changed_rate": _round(changed / len(pairs)) if pairs else None,
        "flipped": both_right,
        "flip_rate": _round(both_right / len(pairs)) if pairs else None,
        "flip_lower": _round(low),
        "flip_upper": _round(high),
        "pre_correct_on_subset": pre_right,
        "full_correct_on_subset": full_right,
        "full_exact_on_subset": _round(full_right / len(pairs)) if pairs else None,
        "examples": pairs[:SAMPLE_ROWS],
    }


# --------------------------------------------------------------------------- #
# the auxiliary readout (§50.6) - a diagnostic, never a gate
# --------------------------------------------------------------------------- #
def prefix_candidates(module: Any, session: Dict[str, Any], upto: int) -> List[str]:
    """What ``derive()`` concludes from the turns up to and including ``upto``.

    Used to decide where a per-turn readout is even scoreable: on an ambiguous
    prefix there is no single right answer, so scoring it would measure luck.
    """
    dropped = {int(turn["turn_id"]) for turn in session["turns"] if int(turn["turn_id"]) > upto}
    return solver_candidates(module, session, dropped)


def readout_profile(
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    *,
    module: Any,
    batch: int = 32,
) -> Dict[str, Any]:
    """Decode the answer at every turn boundary (§50.6).

    §50.2 trains a readout at each boundary, so the model can be asked "who is
    it?" before the last turn. That is useful as a diagnostic - it says how early
    an answer exists - but it is not a score and not a gate: only prefixes the
    solver already resolves to one person are counted, and ``n=0`` means the
    prefix is ambiguous rather than that the model was wrong.
    """
    torch = core._torch
    turns_total = len(sessions[0]["turns"])
    totals = [0] * turns_total
    correct = [0] * turns_total
    core.eval()
    with torch.no_grad():
        for chunk in _chunks(list(sessions), batch):
            boundaries: List[Any] = []
            run_session(
                core,
                [turn_tokens(session) for session in chunk],
                [turn_gaps(session) for session in chunk],
                boundaries=boundaries,
            )
            for turn in range(turns_total):
                targets = [prefix_candidates(module, session, turn) for session in chunk]
                produced = generate_bytes(core, boundaries[turn])
                for index, candidates in enumerate(targets):
                    if len(candidates) != 1:
                        continue
                    totals[turn] += 1
                    correct[turn] += int(_decoded(produced[index]) == candidates[0])
    return {
        "sessions": len(sessions),
        "turns": [
            {
                "turn": turn,
                "n": totals[turn],
                "correct": correct[turn],
                "exact": _round(correct[turn] / totals[turn]) if totals[turn] else None,
            }
            for turn in range(turns_total)
        ],
        "note": (
            "diagnostic only (§50.6): scored where the solver already has a unique "
            "answer on that prefix; n=0 means the prefix is ambiguous, not that the "
            "model answered wrongly"
        ),
    }


# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #
def _aux_lambda_of(report: Dict[str, Any]) -> float:
    """0.0 is stage P; anything else is stage Q's objective (§50.2)."""
    return float((report.get("config") or {}).get("aux_lambda") or 0.0)


def _aux_gate_values(report: Dict[str, Any]) -> Dict[str, Any]:
    """§50.4's Q1-Q9 (and §51.4's R1-R9), recomputed from the recorded numbers.

    The numbers are stage P's where the registration says they are: Q2 = G3,
    Q3-Q8 = G4-G9, Q9 extends G10 with the auxiliary loss and the per-turn
    readout. Q1 exists only on the overfit calibration report, and on that report
    Q2-Q8 are ``None`` on purpose - 32 memorised sessions are not a score, and a
    ``None`` gate is ignored by :func:`verdict` instead of quietly passing.
    Q10 (``--check``) cannot live inside the report it verifies; it is run after
    the fact and recorded in the result section.
    """
    results = report.get("results") or {}
    full = results.get("full") or {}
    reset = results.get("reset") or {}
    fit = results.get("train_fit") or {}
    flip = results.get("flip") or {}
    control = report.get("control") or {}
    cost = report.get("cost") or {}
    history = (report.get("training") or {}).get("history") or []
    readout = (report.get("diagnostics") or {}).get("readout") or {}
    overfit = bool(report.get("overfit"))

    chance = full.get("chance")
    ceiling = None if chance is None else chance + CHANCE_MARGIN
    control_exact = control.get("exact")
    control_ranking = control.get("ranking_exact")

    checks: Dict[str, Any] = {}
    checks["Q1_overfit_calibration"] = (
        None if not overfit else (fit.get("exact") is not None and fit["exact"] >= OVERFIT_FLOOR)
    )
    if overfit:
        for name in (
            "Q2_instrument_fits_train",
            "Q3_heldout_exact_beats_surface",
            "Q4_heldout_ranking_beats_surface",
            "Q5_retraction_flips_the_answer",
            "Q6_answer_lives_in_the_state",
            "Q7_format_control_at_chance",
            "Q8_not_a_constant_answer",
        ):
            checks[name] = None
    else:
        checks["Q2_instrument_fits_train"] = (
            fit.get("exact") is not None and fit["exact"] > FIT_FLOOR
        )
        checks["Q3_heldout_exact_beats_surface"] = (
            full.get("wilson_lower") is not None and full["wilson_lower"] > SURFACE_BASELINE_UPPER
        )
        checks["Q4_heldout_ranking_beats_surface"] = (
            full.get("ranking_lower") is not None and full["ranking_lower"] > SURFACE_BASELINE_UPPER
        )
        checks["Q5_retraction_flips_the_answer"] = (
            flip.get("flip_rate") is not None
            and flip["flip_rate"] >= FLIP_MIN
            and flip.get("full_exact_on_subset") is not None
            and flip["full_exact_on_subset"] >= SURFACE_BASELINE_UPPER
        )
        checks["Q6_answer_lives_in_the_state"] = (
            full.get("exact") is not None
            and reset.get("exact") is not None
            and ceiling is not None
            and (full["exact"] - reset["exact"]) >= GAP_MIN
            and reset["exact"] <= ceiling
        )
        checks["Q7_format_control_at_chance"] = (
            control_exact is not None
            and control_ranking is not None
            and ceiling is not None
            and control_exact <= ceiling
            and control_ranking <= ceiling
        )
        checks["Q8_not_a_constant_answer"] = (
            full.get("top_share") is not None and full["top_share"] <= TOP_SHARE_MAX
        )
    checks["Q9_cost_and_auxiliary_recorded"] = (
        all(cost.get(key) not in (None, 0) for key in ("params", "train_seconds", "device"))
        and _aux_lambda_of(report) > 0.0
        and bool(history)
        and all(row.get("mean_aux_loss") is not None for row in history)
        and bool(readout.get("turns"))
    )
    # stage R (§51) keeps the same nine conditions and only renames them, and
    # stage S (§52) does the same under its own letter, so a report cannot claim
    # one stage's name while being graded by another stage's rules
    prefix = (report.get("config") or {}).get("gate_prefix")
    if prefix is None:
        prefix = "R" if (report.get("config") or {}).get("aux_mode") == "resolvable" else "Q"
    prefix = str(prefix)
    if len(prefix) != 1 or not prefix.isalpha() or prefix != prefix.upper():
        raise SystemExit(f"gate_prefix must be a single A-Z letter, got {prefix!r}")
    checks = {(prefix + name[1:]): value for name, value in checks.items()}
    return checks


def gate_values(report: Dict[str, Any]) -> Dict[str, Any]:
    """Recompute stage P's G1-G10 from the recorded numbers; never read the stored verdict."""
    if _aux_lambda_of(report) > 0.0:
        return _aux_gate_values(report)
    corpus = report.get("corpus") or {}
    start = report.get("start") or {}
    results = report.get("results") or {}
    full = results.get("full") or {}
    reset = results.get("reset") or {}
    fit = results.get("train_fit") or {}
    flip = results.get("flip") or {}
    control = report.get("control") or {}
    cost = report.get("cost") or {}

    chance = full.get("chance")
    ceiling = None if chance is None else chance + CHANCE_MARGIN
    control_exact = control.get("exact")
    control_ranking = control.get("ranking_exact")

    return {
        "G1_start_is_stage_l": (
            start.get("weights_hash") == L_WEIGHTS_HASH
            and start.get("checkpoint_sha256") == L_CHECKPOINT_SHA256
            and start.get("params") == L_PARAMS
            and bool(start.get("checkpoint"))
        ),
        "G2_corpus_is_registered": bool(corpus.get("registered_sizes_match"))
        and bool(corpus.get("registered_digests_match"))
        and corpus.get("train_digest") == TRAIN_DIGEST
        and corpus.get("heldout_digest") == HOLDOUT_DIGEST,
        "G3_instrument_fits_train": (fit.get("exact") is not None and fit.get("exact") > FIT_FLOOR),
        "G4_heldout_exact_beats_surface": (
            full.get("wilson_lower") is not None and full["wilson_lower"] > SURFACE_BASELINE_UPPER
        ),
        "G5_heldout_ranking_beats_surface": (
            full.get("ranking_lower") is not None and full["ranking_lower"] > SURFACE_BASELINE_UPPER
        ),
        "G6_retraction_flips_the_answer": (
            flip.get("flip_rate") is not None
            and flip["flip_rate"] >= FLIP_MIN
            and flip.get("full_exact_on_subset") is not None
            and flip["full_exact_on_subset"] >= SURFACE_BASELINE_UPPER
        ),
        "G7_answer_lives_in_the_state": (
            full.get("exact") is not None
            and reset.get("exact") is not None
            and ceiling is not None
            and (full["exact"] - reset["exact"]) >= GAP_MIN
            and reset["exact"] <= ceiling
        ),
        "G8_format_control_at_chance": (
            control_exact is not None
            and control_ranking is not None
            and ceiling is not None
            and control_exact <= ceiling
            and control_ranking <= ceiling
        ),
        "G9_not_a_constant_answer": (
            full.get("top_share") is not None and full["top_share"] <= TOP_SHARE_MAX
        ),
        "G10_cost_recorded": all(
            cost.get(key) not in (None, 0) for key in ("params", "train_seconds", "device")
        ),
    }


def verdict(checks: Dict[str, Any]) -> bool:
    """Only booleans are gates; diagnostics may live beside them (see §46.11)."""
    booleans = [value for value in checks.values() if isinstance(value, bool)]
    return bool(booleans) and all(booleans)


# --------------------------------------------------------------------------- #
# check
# --------------------------------------------------------------------------- #
def check_report(path: Path) -> List[str]:
    """Re-verify a finished run without retraining (§49.10)."""
    problems: List[str] = []
    if not path.exists():
        return [f"{path} does not exist"]
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("task_version") != TASK_VERSION:
        problems.append(f"task_version {report.get('task_version')!r} != {TASK_VERSION!r}")

    # the corpus is regenerated, so G2 is not taken on trust
    corpus = load_corpus(
        sessions=int((report.get("corpus") or {}).get("sessions", PANTRY_SESSIONS)),
        seed=int((report.get("corpus") or {}).get("seed", PANTRY_SEED)),
    )
    if corpus["meta"]["train_digest"] != (report.get("corpus") or {}).get("train_digest"):
        problems.append("the regenerated train corpus does not match the report")
    if corpus["meta"]["heldout_digest"] != (report.get("corpus") or {}).get("heldout_digest"):
        problems.append("the regenerated held-out corpus does not match the report")

    results = report.get("results") or {}
    for name, block in results.items():
        if not isinstance(block, dict) or "n" not in block:
            continue
        if block.get("n") and block.get("correct") is not None and block.get("exact") is not None:
            expected = block["correct"] / block["n"]
            if abs(float(block["exact"]) - expected) > 1e-3:
                problems.append(f"results.{name}.exact does not equal correct/n")

    # the entry lock is re-verified even though it is not a Q gate (§50.4 has no
    # start/corpus row; run() refuses to start otherwise, and this is the tail
    # that proves the report came from that start)
    start = report.get("start") or {}
    if start.get("weights_hash") != L_WEIGHTS_HASH:
        problems.append("the recorded start weights_hash is not the registered stage-L carrier")
    if start.get("checkpoint_sha256") != L_CHECKPOINT_SHA256:
        problems.append("the recorded start checkpoint sha256 is not the registered stage-L file")

    # §50.4 Q9: if the auxiliary loss was on, every epoch must have both parts
    aux_lambda = _aux_lambda_of(report)
    if aux_lambda > 0.0:
        for row in (report.get("training") or {}).get("history") or []:
            main = row.get("mean_main_loss")
            aux = row.get("mean_aux_loss")
            if main is None or aux is None or "mean_loss" not in row:
                problems.append("the auxiliary run does not record main and auxiliary loss")
                break
            expected = float(main) + aux_lambda * float(aux)
            if abs(float(row["mean_loss"]) - expected) > 1e-3:
                problems.append(f"epoch {row.get('epoch')}: total loss is not main + lambda*aux")
                break

    recorded = report.get("gates") or {}
    recomputed = gate_values(report)
    for name, value in recomputed.items():
        if recorded.get(name) != value:
            problems.append(f"{name}: recorded {recorded.get(name)!r} but recomputes to {value!r}")

    checkpoint = report.get("checkpoint")
    config = report.get("config") or {}
    if not checkpoint or not Path(checkpoint).exists():
        problems.append("checkpoint is missing, so the weights hash cannot be re-verified")
    else:
        try:
            core = build_core(
                hidden=int(config.get("hidden", HIDDEN)),
                emb=int(config.get("emb", EMB)),
                device="cpu",
            )
            core.load_weights(checkpoint, strict_config=True)
            if core.config().get("model_kind") != "gru":
                problems.append("checkpoint model_kind is not 'gru'")
            if core.token_count != VOCAB_SIZE:
                problems.append(f"checkpoint token_count {core.token_count} != {VOCAB_SIZE}")
            if core.weights_hash() != report.get("weights_hash"):
                problems.append("checkpoint weights_hash does not match the report")
            state = core.init_state(1)
            if state.schema_version != 1:
                problems.append(f"state schema_version {state.schema_version} != 1")
        except Exception as exc:  # a check must report, not crash
            problems.append(f"checkpoint reload failed: {exc}")

    leak = report.get("leak_check") or {}
    if leak.get("clean") is not True:
        problems.append("the leak check was not clean when recorded")
    if not report.get("all_pass") and report.get("all_pass") is not False:
        problems.append("all_pass is not a boolean")
    return problems


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #
def run(args: argparse.Namespace, stamp: str) -> Dict[str, Any]:
    import torch  # fail early with a clear message

    device = resolve_device(args.device)
    started = time.time()

    corpus = load_corpus(sessions=args.sessions, seed=args.pantry_seed)
    meta = corpus["meta"]
    if not meta["registered_sizes_match"] or not meta["registered_digests_match"]:
        raise SystemExit(
            "the generated corpus is not the registered one "
            f"({meta['train_bytes']}/{meta['heldout_bytes']} bytes, "
            f"{meta['train_digest'][:12]}/{meta['heldout_digest'][:12]}); "
            "§49.3 would no longer describe this run"
        )

    train_sessions = corpus["train"]
    heldout = corpus["heldout"]
    if args.limit:
        train_sessions = train_sessions[: args.limit]
    if args.overfit:
        if args.overfit > len(train_sessions):
            raise SystemExit(
                f"--overfit {args.overfit} asks for more sessions than the {len(train_sessions)} "
                "available; Q1 is defined on the first N training sessions (§50.4)"
            )
        train_sessions = train_sessions[: args.overfit]
    if args.eval_limit:
        heldout = heldout[: args.eval_limit]

    control_block: Optional[Dict[str, Any]] = None
    if args.control != "rand" and not args.smoke and not args.overfit:
        control_path = _find_control_report(
            Path(args.out), aux_lambda=args.aux_loss, aux_mode=args.aux_mode
        )
        if control_path is None:
            raise SystemExit(
                f"no F-rand control report under {args.out} trained with the same auxiliary "
                "loss; the format-only arm must finish before the scored arm starts "
                "(§49.6 G8, §50.4 Q7). Run `--control rand` with the same --aux-loss first; "
                "refusing to score without it"
            )
        payload = json.loads(control_path.read_text(encoding="utf-8"))
        if payload.get("control_arm") != "rand":
            raise SystemExit(
                f"{control_path} is not the F-rand control (control_arm="
                f"{payload.get('control_arm')!r}); the format control cannot be computed"
            )
        if payload.get("corpus", {}).get("heldout_digest") != HOLDOUT_DIGEST:
            raise SystemExit(
                f"{control_path} was scored on a different held-out corpus; "
                "the format control would compare two different tests"
            )
        control_lambda = float((payload.get("config") or {}).get("aux_lambda") or 0.0)
        if abs(control_lambda - args.aux_loss) > 1e-12:
            raise SystemExit(
                f"{control_path} used aux_lambda={control_lambda}, this run uses "
                f"{args.aux_loss}; §50.4 requires the control to share the auxiliary loss"
            )
        full = (payload.get("results") or {}).get("full") or {}
        control_block = {
            "path": str(control_path),
            "exact": full.get("exact"),
            "ranking_exact": full.get("ranking_exact"),
            "chance": full.get("chance"),
            "top_share": full.get("top_share"),
            "aux_lambda": control_lambda,
            "all_pass": payload.get("all_pass"),
        }

    core = build_core(hidden=args.hidden, emb=args.emb, device=device, seed=args.seed)
    start_hash = load_stage_l(core, Path(args.start))

    arm = "rand" if args.control == "rand" else "answer"
    module = corpus["module"]
    samples = build_samples(
        train_sessions,
        seed=args.seed,
        control=args.control,
        prefix_module=module if args.aux_mode == "resolvable" else None,
    )
    print(
        f"stage P: device={device} params={core.parameter_count()} "
        f"train={len(samples)} holdout={len(heldout)} arm={arm}"
        + (f" aux_lambda={args.aux_loss}" if args.aux_loss > 0.0 else "")
        + (f" aux_mode={args.aux_mode}" if args.aux_loss > 0.0 else ""),
        flush=True,
    )
    history = train(
        core,
        samples,
        epochs=args.epochs,
        batch=args.batch,
        lr=args.lr,
        seed=args.seed,
        aux_lambda=args.aux_loss,
        aux_mode=args.aux_mode,
    )

    raw = {
        name: evaluate(core, heldout, name, module=module)
        for name in ("full", "reset", "no_correction", "no_roster", "no_bounds", "skip_al")
    }
    results: Dict[str, Any] = {name: summarise(records) for name, records in raw.items()}
    results["no_roster"]["agreement_with_full"] = agreement(raw["no_roster"], raw["full"])
    results["no_bounds"]["agreement_with_full"] = agreement(raw["no_bounds"], raw["full"])
    results["flip"] = flip_summary(raw["full"], raw["no_correction"])

    fit_rows = train_sessions[: min(FIT_SESSIONS, len(train_sessions))]
    results["train_fit"] = summarise(evaluate(core, fit_rows, "full", module=module))

    # §50.6: where does an answer exist along the testimony? Diagnostic only.
    diagnostics: Dict[str, Any] = {}
    if args.aux_loss > 0.0:
        diagnostics["readout"] = readout_profile(core, heldout, module=module)

    # the data contract behind "the answer is not in the question"
    leak = leak_report(heldout)

    checkpoint = Path(args.out) / f"pantry_deduction_{stamp}.pt"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    core.save_weights(str(checkpoint))

    report: Dict[str, Any] = {
        "task_version": TASK_VERSION,
        "git_head": _git_head(),
        "device": device,
        "config": {
            "token_count": VOCAB_SIZE,
            "hidden": args.hidden,
            "emb": args.emb,
            "chunk_seconds": CHUNK_SECONDS,
            "lr": args.lr,
            "batch": args.batch,
            "epochs": args.epochs,
            "seed": args.seed,
            "max_answer_bytes": MAX_ANSWER_BYTES,
            "arm": arm,
            "aux_lambda": args.aux_loss,
            "aux_mode": args.aux_mode,
            "gate_prefix": args.gate_prefix,
            "overfit_sessions": args.overfit,
        },
        "corpus": {
            **meta,
            "train_sessions_used": len(train_sessions),
            "heldout_sessions_used": len(heldout),
        },
        "start": {
            "checkpoint": str(args.start),
            "weights_hash": start_hash,
            "init_weights_hash": L_INIT_HASH,
            "checkpoint_sha256": L_CHECKPOINT_SHA256,
            "params": core.parameter_count(),
            "stage_l_report": "data/text_stage/text_stage_20261113-212446.json",
        },
        "params": core.parameter_count(),
        "weights_hash": core.weights_hash(),
        "training": {
            "epochs_run": len(history),
            "steps": sum(row["batches"] for row in history),
            "seconds": round(time.time() - started, 1),
            "history": history,
        },
        "results": results,
        "control": control_block,
        "diagnostics": diagnostics,
        "leak_check": leak,
        "checkpoint": str(checkpoint),
        "overfit": bool(args.overfit),
        "cost": {
            "params": core.parameter_count(),
            "train_seconds": round(time.time() - started, 1),
            "device": device,
        },
    }
    report["gates"] = gate_values(report)
    report["all_pass"] = verdict(report["gates"])
    report["wall_seconds"] = round(time.time() - started, 1)
    if args.smoke:
        report["smoke"] = True
        report["control_arm"] = "smoke"
    else:
        report["control_arm"] = arm

    out_path = Path(args.out) / f"pantry_deduction_{stamp}.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"report": report, "path": out_path}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage P: pantry deduction on the stage-L byte carrier (§49)"
    )
    parser.add_argument("--out", default="data/pantry_stage")
    parser.add_argument("--check", metavar="REPORT.json", help="re-verify a finished run")
    parser.add_argument("--start", default=L_CHECKPOINT, help="stage-L checkpoint to start from")
    parser.add_argument(
        "--control",
        choices=["rand"],
        default=None,
        help="train the format-only control instead of the scored arm (G8)",
    )
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--pantry-seed", type=int, default=PANTRY_SEED)
    parser.add_argument("--sessions", type=int, default=PANTRY_SESSIONS)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--batch", type=int, default=BATCH)
    parser.add_argument("--lr", type=float, default=LEARNING_RATE)
    parser.add_argument("--hidden", type=int, default=HIDDEN)
    parser.add_argument("--emb", type=int, default=EMB)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--limit", type=int, default=0, help="smoke: training sessions")
    parser.add_argument("--eval-limit", type=int, default=0, help="smoke: held-out sessions")
    parser.add_argument("--smoke", action="store_true", help="tiny run on CPU, no score")
    parser.add_argument(
        "--aux-loss",
        type=float,
        default=AUX_LAMBDA_DEFAULT,
        help="§50.2 auxiliary readout weight; 0.0 is stage P's objective",
    )
    parser.add_argument(
        "--aux-mode",
        default=AUX_MODE_DEFAULT,
        choices=("all", "resolvable"),
        help=(
            "what the earlier boundaries are asked (§50.2 'all' vs §51.2 'resolvable': "
            "only where the prefix already has a unique derive() answer)"
        ),
    )
    parser.add_argument(
        "--gate-prefix",
        default=None,
        metavar="LETTER",
        help=(
            "grade this report's conditions under LETTER1-LETTER9 instead of Q/R "
            "(a stage labels its own variable; --check recomputes the same prefix)"
        ),
    )
    parser.add_argument(
        "--overfit",
        type=int,
        default=0,
        help="§50.4 Q1 calibration: first N training sessions only, marked overfit",
    )
    args = parser.parse_args(argv)
    if args.aux_loss < 0.0:
        parser.error("--aux-loss must be >= 0; 0.0 is stage P and is never negative")
    if args.aux_mode == "resolvable" and args.aux_loss <= 0.0:
        parser.error("--aux-mode resolvable only matters with --aux-loss > 0")
    if args.gate_prefix is not None and (
        len(args.gate_prefix) != 1
        or not args.gate_prefix.isalpha()
        or args.gate_prefix != args.gate_prefix.upper()
    ):
        parser.error("--gate-prefix must be a single A-Z letter")
    if args.overfit < 0:
        parser.error("--overfit must be >= 0")

    if args.smoke:
        if args.device == "auto":
            args.device = "cpu"
        args.epochs = min(args.epochs, 1)
        args.limit = args.limit or 4
        args.eval_limit = args.eval_limit or 8
        args.batch = min(args.batch, 4)
        args.control = args.control or "rand"
        if args.out == "data/pantry_stage":
            # a smoke report must never be picked up as the F-rand control
            args.out = "data/pantry_stage/smoke"

    if args.check:
        problems = check_report(Path(args.check))
        if problems:
            print(f"FAILED {args.check}")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print(f"OK {args.check}")
        return 0

    stamp = time.strftime("%Y%m%d-%H%M%S")
    outcome = run(args, stamp)
    report = outcome["report"]
    print()
    print(f"task      : {TASK_VERSION}  device={report['device']}  params={report['params']}")
    print(f"arm       : {report['config']['arm']}")
    if report["config"].get("aux_lambda"):
        print(f"aux loss  : lambda={report['config']['aux_lambda']} (training only)")
    if report.get("overfit"):
        print(
            f"overfit   : {report['config']['overfit_sessions']} train sessions "
            "(calibration arm, not a score)"
        )
    print(
        f"corpus    : train {report['corpus']['train_bytes']} B / "
        f"holdout {report['corpus']['heldout_bytes']} B"
    )
    print()
    print(f"  {'variant':16s} {'n':>4s} {'exact':>7s} {'rank':>7s} {'chance':>7s}")
    for name in VARIANTS:
        block = report["results"][name]
        exact = "-" if block.get("exact") is None else f"{block['exact']:.4f}"
        rank = "-" if block.get("ranking_exact") is None else f"{block['ranking_exact']:.4f}"
        chance = "-" if block.get("chance") is None else f"{block['chance']:.4f}"
        print(f"  {name:16s} {block['n']:4d} {exact:>7s} {rank:>7s} {chance:>7s}")
    flip = report["results"]["flip"]
    print(
        f"  flip: n={flip['n']} both_right={flip['flip_rate']} "
        f"lower={flip['flip_lower']} changed={flip['changed_rate']} "
        f"full_exact={flip['full_exact_on_subset']}"
    )
    print()
    readout = (report.get("diagnostics") or {}).get("readout")
    if readout:
        cells = " ".join(
            f"{row['turn']}:"
            + ("-" if row["exact"] is None else f"{row['exact']:.3f}")
            + f"(n={row['n']})"
            for row in readout["turns"]
        )
        print(f"  readout (diag, held-out): {cells}")
    print("  gates")
    for name, value in report["gates"].items():
        label = "n/a " if value is None else ("PASS" if value else "FAIL")
        print(f"    {label}  {name}")
    print()
    print(f"all_pass : {report['all_pass']}")
    print(f"report    : {outcome['path']}")
    print(f"checkpoint: {report['checkpoint']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
