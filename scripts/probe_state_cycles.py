#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""T1–T6 for the single-core state contract, on a controlled synthetic task.

The pre-registration is written first, in ``CORE_GAP_ANALYSIS.md`` §37: task,
data sizes, model, optimiser, epochs, metrics, and the pass thresholds are all
fixed before this script is run.  Nothing here may be tuned after seeing a
number — a run that changes the design is a **new** pre-registration, not an
edit to this one.

What the task isolates
----------------------
Every session teaches one ``<key> <value>`` pair, then lets time pass
(``al_step(dt)``), then asks two questions:

* a **time question** — has the teach expired? (only ``dt`` can answer it)
* a **content question** — which value was taught? (only the state can answer it)

The context at question time contains no earlier turn, so a stateless model is
at chance; the only channels are the recurrent state (core arm) and, in the
hand-state control arm, an explicit bucket token.  That is what makes T1
(state ablation) and T2 (hand-state) distinguishable instead of decorative.

Why a synthetic task
--------------------
A language-level version of this test does not exist yet: the production core
is at 0.00/10 and has no multi-turn training data.  This probe answers the
narrow question the contract needs answered first — *does the model use the
state at all* — with a task small enough that a failure is a design signal, not
a capacity story.  It says nothing about language ability and must not be
reported as intelligence.

Usage
-----
    python3 scripts/probe_state_cycles.py                 # registered round 1 (S37)
    python3 scripts/probe_state_cycles.py --round 2       # registered round 2 (S38,
                                                          # equal step counts)
    python3 scripts/probe_state_cycles.py --round 3       # registered round 3 (S39,
                                                          # L_al semigroup loss)
    python3 scripts/probe_state_cycles.py --round 4       # registered round 4 (S40,
                                                          # SSM arm)
    python3 scripts/probe_state_cycles.py --cost          # §40.6 cost only (idle
                                                          # machine; scores nothing)
    python3 scripts/probe_state_cycles.py --seeds 0 --epochs 1 \
        --train-sessions 256 --eval-sessions 64           # smoke only
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from ai.core.core_state import CoreState  # noqa: E402
from ai.core.core_step import chunk_dt  # noqa: E402
from ai.core.stateful_decoder import GRUCore, SSMCore  # noqa: E402

# -- vocabulary (fixed; changing it invalidates §37) -------------------------
PAD = 0
REMEMBER = 1
TALK = 2
Q_TIME = 3
Q_KEY = 4
VALID = 5
EXPIRED = 6
UNKNOWN = 7
BUCKET_SHORT = 8
BUCKET_LONG = 9
KEYS: Tuple[int, ...] = tuple(range(10, 18))
VALUES: Tuple[int, ...] = tuple(range(18, 26))
TOKEN_COUNT = 26

GAP_COUNT = 4
EXPIRY_S = 240.0
BUCKET_TOKENS = (BUCKET_SHORT, BUCKET_LONG)

# Round 2 removes the "count the chunks" shortcut: with 8 equal gaps every
# session is advanced by exactly 8 chunks, so only the dt *magnitude* can carry
# the elapsed time.  Same task, vocabulary and thresholds as round 1.
# The semigroup measurement set is fixed for every round so the L_al arm and
# its control are compared on identical pairs (§39.3).
SEMIGROUP_TRAIN_PAIR: Tuple[float, float] = (25.0, 25.0)
SEMIGROUP_HELDOUT_PAIRS: Tuple[Tuple[float, float], ...] = ((30.0, 30.0), (20.0, 40.0))
L_AL_MAX_DELTA = 1e-2

ROUNDS = {
    1: {"gap_count": 4, "gap_mode": "random"},
    2: {"gap_count": 8, "gap_mode": "equal"},
    3: {
        "gap_count": 8,
        "gap_mode": "equal",
        "l_al_weight": 0.5,
        "l_al_train": SEMIGROUP_TRAIN_PAIR,
        "l_al_eval": SEMIGROUP_HELDOUT_PAIRS,
    },
    # Same task, data and answer thresholds as round 2; only the recurrence
    # changes.  The semigroup is gated here because the diagonal decay makes it
    # exact by construction (an architectural property, not a learned one).
    4: {
        "gap_count": 8,
        "gap_mode": "equal",
        "arch": "ssm",
        "semigroup_gate": True,
    },
}

# Registered defaults (§37.3). A deviating run prints a banner and is not the
# registered result.
REGISTERED = {
    "epochs": 30,
    "batch_size": 64,
    "lr": 5e-3,
    "grad_clip": 1.0,
    "hidden": 64,
    "emb": 32,
    "chunk_seconds": 60.0,
    "train_sessions": 4000,
    "eval_sessions": 1000,
    "seeds": (0, 1, 2, 3, 4),
}

# Pre-registered pass thresholds (§37.5).
THRESHOLDS = {
    "t3_time": 0.90,
    "t3_key": 0.85,
    "t3_half": 0.85,
    "t1_time": 0.65,
    "t1_key_valid": 0.30,
    "t1_drop": 0.30,
    "t4_max_prob_diff": 1e-5,
    "t5_no_al_time": 0.65,
    "t5_no_al_drop": 0.30,
    "t5_shuffled_overall": 0.70,
    "t5_fake_clock_expired": 0.30,
    "t2_time": 0.90,
    "t2_ablation_delta": 0.05,
    "t2_bucket_drop": 0.30,
}
T975_DF4 = 2.776


@dataclass(frozen=True)
class Session:
    key: int
    value: int
    gaps: Tuple[float, ...]
    expired: bool

    @property
    def time_target(self) -> int:
        return EXPIRED if self.expired else VALID

    @property
    def key_target(self) -> int:
        return UNKNOWN if self.expired else self.value


def generate_sessions(
    count: int, seed: int, *, gap_count: int = GAP_COUNT, gap_mode: str = "random"
) -> List[Session]:
    """Deterministic session generator (§37.2 round 1, §38.2 round 2).

    ``gap_mode="random"``: unequal gaps, some above 60 s (round 1).
    ``gap_mode="equal"``: ``gap_count`` equal gaps, each ≤ 50 s for the
    registered bands, so every session takes exactly ``gap_count`` chunks and
    the chunk count stops being a time signal (round 2).
    """
    if gap_count <= 0:
        raise ValueError("gap_count must be > 0")
    if gap_mode not in {"random", "equal"}:
        raise ValueError(f"unknown gap_mode {gap_mode!r}")
    rng = random.Random(seed)
    sessions: List[Session] = []
    for _ in range(count):
        key = rng.choice(KEYS)
        value = rng.choice(VALUES)
        if rng.random() < 0.5:
            total = rng.uniform(0.0, 200.0)
        else:
            total = rng.uniform(280.0, 400.0)
        if gap_mode == "equal":
            gaps = tuple(total / gap_count for _ in range(gap_count))
        else:
            weights = [rng.random() + 0.05 for _ in range(gap_count)]
            norm = sum(weights)
            gaps = tuple(total * weight / norm for weight in weights)
        sessions.append(Session(key=key, value=value, gaps=gaps, expired=total > EXPIRY_S))
    return sessions


# -- tensor helpers ----------------------------------------------------------


def _tensor(sessions: Sequence[Session], field: str, torch: Any, device: str) -> Any:
    return torch.tensor([getattr(session, field) for session in sessions], device=device)


def _gap_tensor(sessions: Sequence[Session], index: int, torch: Any, device: str) -> Any:
    return torch.tensor(
        [session.gaps[index] for session in sessions], dtype=torch.float32, device=device
    )


def _bucket_tokens(sessions: Sequence[Session], arm: str, torch: Any, device: str) -> Any:
    if arm == "hand":
        tokens = [BUCKET_LONG if session.expired else BUCKET_SHORT for session in sessions]
    else:
        tokens = [PAD for _ in sessions]
    return torch.tensor(tokens, device=device)


# -- one forward pass over a batch of sessions -------------------------------


def run_sessions(
    model: GRUCore,
    sessions: Sequence[Session],
    *,
    arm: str,
    gaps: Optional[Sequence[Tuple[float, ...]]] = None,
    skip_al: bool = False,
    ablate: bool = False,
    bucket_override: Optional[int] = None,
    keep_prefix_state: bool = False,
) -> Dict[str, Any]:
    """Run teach → gaps/fillers → time question → content question.

    Returns predictions, probabilities, the final state, and (optionally) the
    state right before the questions, which is what the restart test saves.
    """
    torch = model._torch
    device = model.device
    batch = len(sessions)
    gap_count = len(sessions[0].gaps)
    gap_source = gaps if gaps is not None else [session.gaps for session in sessions]

    state = model.init_state(batch, session_id="probe")
    teach = torch.stack(
        [
            torch.full((batch,), REMEMBER, device=device),
            _tensor(sessions, "key", torch, device),
            _tensor(sessions, "value", torch, device),
        ],
        dim=1,
    )
    talk = torch.full((batch, 1), TALK, device=device)

    _, state = model.ai_step(teach, state)
    for index in range(gap_count - 1):
        if arm == "core" and not skip_al:
            state = model.al_step(
                torch.tensor(
                    [gaps_i[index] for gaps_i in gap_source],
                    dtype=torch.float32,
                    device=device,
                ),
                state,
            )
        _, state = model.ai_step(talk, state)
    if arm == "core" and not skip_al:
        state = model.al_step(
            torch.tensor(
                [gaps_i[gap_count - 1] for gaps_i in gap_source],
                dtype=torch.float32,
                device=device,
            ),
            state,
        )

    prefix_state: Optional[CoreState] = None
    if keep_prefix_state:
        prefix_state = model.export_state(state)

    if ablate:
        state.tensors["h"] = torch.zeros_like(state.tensors["h"])

    if bucket_override is not None:
        bucket = torch.full((batch,), bucket_override, device=device)
    else:
        bucket = _bucket_tokens(sessions, arm, torch, device)

    time_tokens = torch.stack([bucket, torch.full_like(bucket, Q_TIME)], dim=1)
    time_logits, state = model.ai_step(time_tokens, state)
    key_logits, state = model.ai_step(
        torch.stack([bucket, torch.full_like(bucket, Q_KEY)], dim=1), state
    )

    time_probs = torch.softmax(time_logits[:, -1, :], dim=-1)
    return {
        "time_pred": torch.argmax(time_logits[:, -1, :], dim=-1),
        "key_pred": torch.argmax(key_logits[:, -1, :], dim=-1),
        "time_probs": time_probs,
        "state": state,
        "prefix_state": prefix_state,
        "query_tokens": time_tokens.detach().to("cpu"),
    }


def build_core(
    arch: str,
    *,
    seed: int,
    hidden: int,
    emb: int,
    chunk_seconds: float,
) -> Any:
    """Construct one arm; the only place that knows the registered model sizes."""
    torch = model_torch()
    torch.manual_seed(seed)
    if arch == "gru":
        return GRUCore(
            TOKEN_COUNT,
            hidden=hidden,
            emb=emb,
            chunk_seconds=chunk_seconds,
            seed=seed,
        )
    if arch == "ssm":
        return SSMCore(
            TOKEN_COUNT,
            hidden=hidden,
            emb=emb,
            chunk_seconds=chunk_seconds,
            seed=seed,
        )
    raise ValueError(f"unknown arch {arch!r}")


def _train_step(
    model: Any,
    optimiser: Any,
    batch: Sequence[Session],
    *,
    arm: str,
    grad_clip: float,
    l_al_weight: float = 0.0,
    l_al_train: Tuple[float, float] = (25.0, 25.0),
) -> None:
    """One registered-shaped optimiser step (teach → gaps → two queries).

    Kept as its own function so the cost measurement times **this** work rather
    than a look-alike: ``train_arm`` and ``run_cost`` call the same body.
    """
    torch = model_torch()
    gap_count = len(batch[0].gaps)
    state = model.init_state(len(batch), session_id="train")
    device = model.device
    teach = torch.stack(
        [
            torch.full((len(batch),), REMEMBER, device=device),
            _tensor(batch, "key", torch, device),
            _tensor(batch, "value", torch, device),
        ],
        dim=1,
    )
    talk = torch.full((len(batch), 1), TALK, device=device)
    _, state = model.ai_step(teach, state)
    for index in range(gap_count - 1):
        if arm == "core":
            state = model.al_step(
                _gap_tensor(batch, index, torch, device),
                state,
            )
        _, state = model.ai_step(talk, state)
    if arm == "core":
        state = model.al_step(
            _gap_tensor(batch, gap_count - 1, torch, device),
            state,
        )

    l_al_value = None
    if l_al_weight > 0.0 and arm == "core":
        # §39.2: the same h advanced as dt1+dt2 vs dt2(dt1(h)).
        # Only the training pair is taught; the held-out pairs are
        # measured, never optimised.
        hidden0 = state.tensors["h"]
        sequential = model.init_state(len(batch), session_id="l_al_seq")
        sequential.tensors["h"] = hidden0
        model.al_step(l_al_train[0], sequential)
        model.al_step(l_al_train[1], sequential)
        joined = model.init_state(len(batch), session_id="l_al_join")
        joined.tensors["h"] = hidden0
        model.al_step(l_al_train[0] + l_al_train[1], joined)
        l_al_value = ((sequential.tensors["h"] - joined.tensors["h"]) ** 2).mean()

    bucket = _bucket_tokens(batch, arm, torch, device)
    time_logits, state = model.ai_step(
        torch.stack([bucket, torch.full_like(bucket, Q_TIME)], dim=1), state
    )
    key_logits, state = model.ai_step(
        torch.stack([bucket, torch.full_like(bucket, Q_KEY)], dim=1), state
    )

    time_target = _tensor(batch, "time_target", torch, device)
    key_target = _tensor(batch, "key_target", torch, device)
    loss = torch.nn.functional.cross_entropy(
        time_logits[:, -1, :], time_target
    ) + torch.nn.functional.cross_entropy(key_logits[:, -1, :], key_target)
    if l_al_value is not None:
        loss = loss + l_al_weight * l_al_value

    optimiser.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(list(model.parameters()), grad_clip)
    optimiser.step()
    model.invalidate_hash()
    if l_al_value is not None:
        model.last_l_al_value = float(l_al_value.detach())


def train_arm(
    sessions: Sequence[Session],
    *,
    arm: str,
    seed: int,
    epochs: int,
    batch_size: int,
    lr: float,
    grad_clip: float,
    hidden: int,
    emb: int,
    chunk_seconds: float,
    l_al_weight: float = 0.0,
    l_al_train: Tuple[float, float] = (25.0, 25.0),
    arch: str = "gru",
) -> Any:
    torch = model_torch()
    model = build_core(arch, seed=seed, hidden=hidden, emb=emb, chunk_seconds=chunk_seconds)
    model.train()
    optimiser = torch.optim.Adam(model.parameters(), lr=lr)
    rng = random.Random(seed * 7919 + 13)
    order = list(range(len(sessions)))

    for _epoch in range(epochs):
        rng.shuffle(order)
        for start in range(0, len(order), batch_size):
            batch = [sessions[i] for i in order[start : start + batch_size]]
            _train_step(
                model,
                optimiser,
                batch,
                arm=arm,
                grad_clip=grad_clip,
                l_al_weight=l_al_weight,
                l_al_train=l_al_train,
            )

    model.eval()
    return model


def model_torch() -> Any:
    import torch

    return torch


# -- metrics -----------------------------------------------------------------


def _accuracy(pred: Any, target: Any, mask: Any) -> float:
    selected = pred[mask]
    if int(selected.numel()) == 0:
        return float("nan")
    return float((selected == target[mask]).float().mean())


def evaluate(
    model: GRUCore,
    sessions: Sequence[Session],
    *,
    arm: str,
    skip_al: bool = False,
    ablate: bool = False,
    gap_override: Optional[Sequence[Tuple[float, ...]]] = None,
    bucket_override: Optional[int] = None,
) -> Dict[str, float]:
    torch = model_torch()
    expired = torch.tensor([session.expired for session in sessions], device=model.device)
    valid = ~expired
    with torch.no_grad():
        out = run_sessions(
            model,
            sessions,
            arm=arm,
            gaps=gap_override,
            skip_al=skip_al,
            ablate=ablate,
            bucket_override=bucket_override,
        )
    time_pred = out["time_pred"]
    key_pred = out["key_pred"]
    time_target = _tensor(sessions, "time_target", torch, model.device)
    key_target = _tensor(sessions, "key_target", torch, model.device)
    both = (time_pred == time_target) & (key_pred == key_target)
    return {
        "time_acc": _accuracy(time_pred, time_target, torch.ones_like(expired)),
        "time_acc_valid": _accuracy(time_pred, time_target, valid),
        "time_acc_expired": _accuracy(time_pred, time_target, expired),
        "key_acc": _accuracy(key_pred, key_target, torch.ones_like(expired)),
        "key_acc_valid": _accuracy(key_pred, key_target, valid),
        "key_acc_expired": _accuracy(key_pred, key_target, expired),
        "overall": float(both.float().mean()),
    }


# -- T4 / T6 / semigroup -----------------------------------------------------


def restart_delta(model: GRUCore, sessions: Sequence[Session]) -> float:
    """Save→load the pre-question state, then compare time-question probabilities."""
    torch = model_torch()
    with torch.no_grad():
        first = run_sessions(model, sessions, arm="core", keep_prefix_state=True)
        prefix = first["prefix_state"]
        assert prefix is not None

        with tempfile.TemporaryDirectory() as tmp:
            exported = model.export_state(prefix)
            exported.save(tmp)
            loaded = CoreState.load(tmp, expected_weights_hash=model.weights_hash())
            restored = model.attach_state(loaded)
            # Recompute the two question steps from the restored state.
            batch = len(sessions)
            device = model.device
            bucket = _bucket_tokens(sessions, "core", torch, device)
            time_logits, _ = model.ai_step(
                torch.stack([bucket, torch.full_like(bucket, Q_TIME)], dim=1), restored
            )
            restored_probs = torch.softmax(time_logits[:, -1, :], dim=-1)

    return float((restored_probs - first["time_probs"]).abs().max())


def semigroup_gap(model: GRUCore) -> float:
    """Report-only: h after al_step(30)+al_step(30) vs al_step(60)."""
    torch = model_torch()
    sessions = generate_sessions(4, seed=99)
    with torch.no_grad():
        left = model.init_state(len(sessions), session_id="semigroup")
        left = model.al_step(30.0, left)
        left = model.al_step(30.0, left)
        right = model.init_state(len(sessions), session_id="semigroup")
        right = model.al_step(60.0, right)
    return float((left.tensors["h"] - right.tensors["h"]).abs().max())


def l_al_penalty(model: GRUCore, hidden0: Any, dt1: float, dt2: float) -> Any:
    """``mean((h(dt2 after dt1) - h(dt1+dt2))^2)`` for one state tensor (§39.2).

    Kept as a named function so a test can pin the two properties the claim
    depends on: zero time is exactly zero penalty, and the gradient actually
    reaches the recurrence (otherwise ``L_al`` would be decorative).
    """
    sequential = model.init_state(int(hidden0.shape[0]), session_id="l_al_seq")
    sequential.tensors["h"] = hidden0
    model.al_step(dt1, sequential)
    model.al_step(dt2, sequential)
    joined = model.init_state(int(hidden0.shape[0]), session_id="l_al_join")
    joined.tensors["h"] = hidden0
    model.al_step(dt1 + dt2, joined)
    return ((sequential.tensors["h"] - joined.tensors["h"]) ** 2).mean()


def semigroup_eval(
    model: GRUCore,
    sessions: Sequence[Session],
    pairs: Sequence[Tuple[float, float]],
) -> Dict[str, float]:
    """Max |h(dt2 then dt1) - h(dt1+dt2)| on the pre-question states.

    The states are the ones the model actually visits (held-out sessions);
    ``pairs`` are fixed in the pre-registration, and only the first pair is
    ever trained on.  No gradients: a held-out pair that is optimised is not
    a held-out pair.
    """
    torch = model_torch()
    results: Dict[str, float] = {}
    with torch.no_grad():
        out = run_sessions(model, sessions, arm="core", keep_prefix_state=True)
        prefix = out["prefix_state"]
        assert prefix is not None
        base = torch.as_tensor(prefix.tensors["h"], dtype=torch.float32, device=model.device)
        for dt1, dt2 in pairs:
            sequential = model.init_state(len(sessions), session_id="semigroup_eval")
            sequential.tensors["h"] = base.clone()
            model.al_step(dt1, sequential)
            model.al_step(dt2, sequential)
            joined = model.init_state(len(sessions), session_id="semigroup_eval")
            joined.tensors["h"] = base.clone()
            model.al_step(dt1 + dt2, joined)
            delta = (sequential.tensors["h"] - joined.tensors["h"]).abs().max()
            results[f"{dt1:g}+{dt2:g}"] = float(delta)
    return results


def zero_time_identity(model: GRUCore) -> bool:
    torch = model_torch()
    with torch.no_grad():
        state = model.init_state(3, session_id="zero")
        before = state.tensors["h"].clone()
        ticks = state.ticks
        version = state.state_version
        model.al_step(0.0, state)
        same = torch.equal(before, state.tensors["h"])
    return bool(same and ticks == state.ticks and version == state.state_version)


# -- reporting ---------------------------------------------------------------


def _mean(values: Sequence[float]) -> float:
    usable = [value for value in values if not math.isnan(value)]
    return sum(usable) / len(usable) if usable else float("nan")


def _ci_half(values: Sequence[float]) -> float:
    usable = [value for value in values if not math.isnan(value)]
    if len(usable) < 2:
        return float("nan")
    mean = _mean(usable)
    variance = sum((value - mean) ** 2 for value in usable) / (len(usable) - 1)
    return T975_DF4 * math.sqrt(variance / len(usable))


def run(args: argparse.Namespace) -> Dict[str, Any]:
    round_config = ROUNDS[args.round]
    gap_count = int(round_config["gap_count"])
    gap_mode = str(round_config["gap_mode"])
    arch = str(round_config.get("arch", "gru"))
    l_al_weight = float(round_config.get("l_al_weight", 0.0))
    if args.l_al_weight is not None:
        l_al_weight = float(args.l_al_weight)
    l_al_train = tuple(round_config.get("l_al_train", SEMIGROUP_TRAIN_PAIR))
    l_al_eval = tuple(round_config.get("l_al_eval", ()))
    fake_dt = 120.0 / gap_count  # same chunk count as a real session, only dt differs

    registered = (
        args.epochs == REGISTERED["epochs"]
        and args.train_sessions == REGISTERED["train_sessions"]
        and args.eval_sessions == REGISTERED["eval_sessions"]
        and args.hidden == REGISTERED["hidden"]
        and args.emb == REGISTERED["emb"]
        and l_al_weight == float(round_config.get("l_al_weight", 0.0))
        and arch == str(round_config.get("arch", "gru"))
        and tuple(args.seeds) == tuple(REGISTERED["seeds"])
    )

    per_seed: List[Dict[str, Any]] = []
    provenance: List[Dict[str, Any]] = []
    started = time.time()

    # Measure (do not assume) whether the chunk count leaks time.  In round 2
    # every session must take the same number of chunks, so only dt magnitude
    # can carry the gap.
    probe_sessions = generate_sessions(
        args.eval_sessions, seed=2000 + args.seeds[0], gap_count=gap_count, gap_mode=gap_mode
    )
    chunk_totals = sorted(
        {
            sum(len(chunk_dt(gap, REGISTERED["chunk_seconds"])) for gap in session.gaps)
            for session in probe_sessions
        }
    )

    for seed in args.seeds:
        train = generate_sessions(
            args.train_sessions, seed=1000 + seed, gap_count=gap_count, gap_mode=gap_mode
        )
        heldout = generate_sessions(
            args.eval_sessions, seed=2000 + seed, gap_count=gap_count, gap_mode=gap_mode
        )

        shared = dict(
            seed=seed,
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            grad_clip=REGISTERED["grad_clip"],
            hidden=args.hidden,
            emb=args.emb,
            chunk_seconds=REGISTERED["chunk_seconds"],
            l_al_weight=l_al_weight,
            l_al_train=l_al_train,
        )
        core = train_arm(train, arm="core", arch=arch, **shared)
        # The hand-state control is always the GRU arm: it exists to show that
        # the same T1 does *not* detect a state that lives in the context.
        hand = train_arm(train, arm="hand", arch="gru", **shared)

        hash_before = core.weights_hash()
        rng = random.Random(seed * 104729 + 7)
        shuffled = list(heldout)
        rng.shuffle(shuffled)
        shuffled_gaps = [session.gaps for session in shuffled]

        metrics = {
            "persistent": evaluate(core, heldout, arm="core"),
            "ablated": evaluate(core, heldout, arm="core", ablate=True),
            "no_al": evaluate(core, heldout, arm="core", skip_al=True),
            "shuffled": evaluate(core, heldout, arm="core", gap_override=shuffled_gaps),
            "fake_clock": evaluate(
                core,
                heldout,
                arm="core",
                gap_override=[(fake_dt,) * gap_count for _ in heldout],
            ),
            "hand_state": evaluate(hand, heldout, arm="hand"),
            "hand_state_ablated": evaluate(hand, heldout, arm="hand", ablate=True),
            "hand_state_no_bucket": evaluate(hand, heldout, arm="hand", bucket_override=PAD),
        }
        metrics["t4_restart_delta"] = restart_delta(core, heldout[:200])
        metrics["semigroup_gap"] = semigroup_gap(core)
        # Measured for every round (no gradients), so the L_al arm and its
        # control are compared on the same held-out states and pairs.
        pairs = (SEMIGROUP_TRAIN_PAIR, *SEMIGROUP_HELDOUT_PAIRS)
        metrics["semigroup_eval"] = semigroup_eval(core, heldout, pairs)
        if l_al_weight > 0.0:
            metrics["l_al_train_last_batch"] = float(getattr(core, "last_l_al_value", float("nan")))
        metrics["zero_time_identity"] = float(zero_time_identity(core))
        hash_after = core.weights_hash()

        torch = model_torch()
        with torch.no_grad():
            token_probe = run_sessions(core, heldout[:32], arm="core")
        seen_tokens = [int(token) for token in token_probe["query_tokens"].flatten().tolist()]
        core_has_bucket = any(token in BUCKET_TOKENS for token in seen_tokens)

        tau_stats = None
        if hasattr(core, "tau"):
            tau = core.tau().detach().to("cpu")
            tau_stats = {
                "min": float(tau.min()),
                "median": float(tau.median()),
                "max": float(tau.max()),
            }

        provenance.append(
            {
                "seed": seed,
                "weights_hash_stable": hash_before == hash_after,
                "weights_hash": hash_before,
                "core_parameters": core.parameter_count(),
                "hand_parameters": hand.parameter_count(),
                "core_tokens_include_bucket": core_has_bucket,
                "core_query_tokens": sorted(set(seen_tokens)),
                "tau_seconds": tau_stats,
            }
        )
        per_seed.append(metrics)
        print(
            f"seed {seed}: persistent time={metrics['persistent']['time_acc']:.3f} "
            f"key={metrics['persistent']['key_acc']:.3f} "
            f"overall={metrics['persistent']['overall']:.3f} | "
            f"ablated time={metrics['ablated']['time_acc']:.3f} | "
            f"no_al time={metrics['no_al']['time_acc']:.3f} | "
            f"restart Δ={metrics['t4_restart_delta']:.2e}",
            flush=True,
        )

    def values(condition: str, metric: str) -> List[float]:
        return [seed_metrics[condition][metric] for seed_metrics in per_seed]

    summary = {
        f"{condition}.{metric}": {
            "mean": _mean(values(condition, metric)),
            "ci": _ci_half(values(condition, metric)),
        }
        for condition in (
            "persistent",
            "ablated",
            "no_al",
            "shuffled",
            "fake_clock",
            "hand_state",
            "hand_state_ablated",
            "hand_state_no_bucket",
        )
        for metric in (
            "time_acc",
            "time_acc_valid",
            "time_acc_expired",
            "key_acc",
            "key_acc_valid",
            "key_acc_expired",
            "overall",
        )
    }
    for scalar in ("t4_restart_delta", "semigroup_gap", "zero_time_identity"):
        summary[scalar] = {
            "mean": _mean([seed_metrics[scalar] for seed_metrics in per_seed]),
            "ci": _ci_half([seed_metrics[scalar] for seed_metrics in per_seed]),
        }

    def mean_of(condition: str, metric: str) -> float:
        return summary[f"{condition}.{metric}"]["mean"]

    drop_time = mean_of("persistent", "time_acc") - mean_of("ablated", "time_acc")
    no_al_drop = mean_of("persistent", "time_acc") - mean_of("no_al", "time_acc")
    hand_drop = mean_of("hand_state", "time_acc") - mean_of("hand_state_no_bucket", "time_acc")
    hand_ablation = abs(
        mean_of("hand_state", "time_acc") - mean_of("hand_state_ablated", "time_acc")
    )

    checks = {
        "T3_time": mean_of("persistent", "time_acc") >= THRESHOLDS["t3_time"],
        "T3_key": mean_of("persistent", "key_acc") >= THRESHOLDS["t3_key"],
        "T3_halves": min(
            mean_of("persistent", "time_acc_valid"),
            mean_of("persistent", "time_acc_expired"),
            mean_of("persistent", "key_acc_valid"),
            mean_of("persistent", "key_acc_expired"),
        )
        >= THRESHOLDS["t3_half"],
        "T1_time": mean_of("ablated", "time_acc") <= THRESHOLDS["t1_time"],
        "T1_key_valid": mean_of("ablated", "key_acc_valid") <= THRESHOLDS["t1_key_valid"],
        "T1_drop": drop_time >= THRESHOLDS["t1_drop"],
        "T4_restart": _mean([m["t4_restart_delta"] for m in per_seed])
        <= THRESHOLDS["t4_max_prob_diff"],
        "T5_no_al": mean_of("no_al", "time_acc") <= THRESHOLDS["t5_no_al_time"],
        "T5_no_al_drop": no_al_drop >= THRESHOLDS["t5_no_al_drop"],
        "T5_shuffled": mean_of("shuffled", "overall") <= THRESHOLDS["t5_shuffled_overall"],
        "T5_fake_clock": mean_of("fake_clock", "time_acc_expired")
        <= THRESHOLDS["t5_fake_clock_expired"],
        "T2_hand_time": mean_of("hand_state", "time_acc") >= THRESHOLDS["t2_time"],
        "T2_hand_ablation": hand_ablation <= THRESHOLDS["t2_ablation_delta"],
        "T2_hand_bucket_drop": hand_drop >= THRESHOLDS["t2_bucket_drop"],
        "T6_provenance": all(
            item["weights_hash_stable"]
            and item["core_parameters"] > 0
            and not item["core_tokens_include_bucket"]
            for item in provenance
        ),
        "T6_no_bucket_tokens": not any(item["core_tokens_include_bucket"] for item in provenance),
        "zero_time_identity": summary["zero_time_identity"]["mean"] == 1.0,
    }
    if gap_mode == "equal":
        checks["equal_step_counts"] = chunk_totals == [gap_count]

    semigroup_report: Dict[str, Dict[str, Any]] = {}
    for pair in (SEMIGROUP_TRAIN_PAIR, *SEMIGROUP_HELDOUT_PAIRS):
        key = f"{pair[0]:g}+{pair[1]:g}"
        values = [seed_metrics["semigroup_eval"][key] for seed_metrics in per_seed]
        semigroup_report[key] = {
            "mean": _mean(values),
            "max": max(values),
            "per_seed": values,
        }

    if round_config.get("semigroup_gate"):
        for key, entry in semigroup_report.items():
            checks[f"SEMIGROUP_{key}"] = entry["max"] <= L_AL_MAX_DELTA

    l_al_report: Dict[str, Any] = {}
    if l_al_weight > 0.0:
        for key, entry in semigroup_report.items():
            checks[f"L_AL_{key}"] = entry["max"] <= L_AL_MAX_DELTA
        l_al_report = {
            "weight": l_al_weight,
            "train_pair": list(l_al_train),
            "eval_pairs": [list(pair) for pair in l_al_eval],
            "max_delta_allowed": L_AL_MAX_DELTA,
            "delta": semigroup_report,
            "train_loss_last_batch": {
                "mean": _mean(
                    [
                        seed_metrics.get("l_al_train_last_batch", float("nan"))
                        for seed_metrics in per_seed
                    ]
                )
            },
            "note": (
                "Only the train pair is optimised; the eval pairs are measured "
                "on held-out session states."
            ),
        }

    report = {
        "registered": registered,
        "round": args.round,
        "registration": (
            "docs/06-project-management/CORE_GAP_ANALYSIS.md §37"
            if args.round == 1
            else "docs/06-project-management/CORE_GAP_ANALYSIS.md §38"
        ),
        "config": {
            "round": args.round,
            "gap_count": gap_count,
            "gap_mode": gap_mode,
            "step_counts": {
                "distinct_totals": chunk_totals,
                "min": chunk_totals[0] if chunk_totals else None,
                "max": chunk_totals[-1] if chunk_totals else None,
            },
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "lr": args.lr,
            "hidden": args.hidden,
            "emb": args.emb,
            "chunk_seconds": REGISTERED["chunk_seconds"],
            "train_sessions": args.train_sessions,
            "eval_sessions": args.eval_sessions,
            "seeds": list(args.seeds),
            "arch": arch,
            "token_count": TOKEN_COUNT,
            "expiry_seconds": EXPIRY_S,
        },
        "thresholds": THRESHOLDS,
        "summary": summary,
        "derived": {
            "t1_time_drop": drop_time,
            "t5_no_al_time_drop": no_al_drop,
            "t2_hand_bucket_drop": hand_drop,
            "t2_hand_ablation_delta": hand_ablation,
        },
        "checks": checks,
        "semigroup_delta": semigroup_report,
        "l_al": l_al_report,
        "all_pass": all(checks.values()),
        "provenance": provenance,
        "per_seed": per_seed,
        "wall_seconds": time.time() - started,
        "note": (
            "Synthetic mechanism test only. It does not change the core score "
            "(0.00/10) and does not claim language ability."
        ),
    }
    return report


def print_report(report: Dict[str, Any]) -> None:
    section = {1: "§37", 2: "§38", 3: "§39", 4: "§40"}.get(report.get("round", 1), "§?")
    if not report["registered"]:
        print(f"\n⚠️  非登記參數：這不是 {section} 的登記結果，只可當煙霧測試。\n")
    step_counts = report["config"]["step_counts"]["distinct_totals"]
    print(f"\n== round {report.get('round', 1)}；每 session 的 chunk 總數 {step_counts} ==")
    summary = report["summary"]
    print("\n== 主臂／對照（5 種子平均）==")
    rows = [
        ("persistent", "time_acc"),
        ("persistent", "time_acc_expired"),
        ("persistent", "key_acc"),
        ("persistent", "overall"),
        ("ablated", "time_acc"),
        ("ablated", "key_acc"),
        ("no_al", "time_acc"),
        ("shuffled", "overall"),
        ("fake_clock", "time_acc_expired"),
        ("hand_state", "time_acc"),
        ("hand_state_ablated", "time_acc"),
        ("hand_state_no_bucket", "time_acc"),
    ]
    for condition, metric in rows:
        entry = summary[f"{condition}.{metric}"]
        print(f"  {condition:22s} {metric:18s} {entry['mean']:.4f} ± {entry['ci']:.4f}")
    print(f"  T4 restart Δ {summary['t4_restart_delta']['mean']:.2e}")
    print(f"  semigroup Δ (report only) {summary['semigroup_gap']['mean']:.4f}")
    if report.get("semigroup_delta"):
        for key, entry in report["semigroup_delta"].items():
            print(f"  semigroup {key:10s} max|Δh| {entry['max']:.4e}")

    print("\n== 預登記判定 ==")
    for name, passed in report["checks"].items():
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
    print(f"\n  all_pass = {report['all_pass']}")


# -- cost measurement (§40.6) -------------------------------------------------

COST = {
    "batch_size": 64,
    "gap_count": 8,
    "warmup": 5,
    "reps": 30,
    "alternations": 3,
    "seed": 4242,
}


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return 0.5 * (ordered[middle - 1] + ordered[middle])


def _time_phase(call: Any, *, warmup: int, reps: int) -> Dict[str, float]:
    """Warm up, then time ``reps`` calls; return median/min/max in seconds."""
    for _ in range(warmup):
        call()
    samples = []
    for _ in range(reps):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    samples.sort()
    return {"median": _median(samples), "min": samples[0], "max": samples[-1]}


def _checkpoint_bytes(model: Any) -> int:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "weights.pt"
        model.save_weights(str(path))
        return int(path.stat().st_size)


def _aggregate(entries: Sequence[Dict[str, float]]) -> Dict[str, Any]:
    return {
        "median_ms": 1e3 * _median([entry["median"] for entry in entries]),
        "min_ms": 1e3 * min(entry["min"] for entry in entries),
        "max_ms": 1e3 * max(entry["max"] for entry in entries),
        "alternations": len(entries),
    }


def run_cost(args: argparse.Namespace) -> Dict[str, Any]:
    """Time the two arms on the same work, alternating the order.

    §38's 99.4 s and §40's 74.0 s are **not** comparable (one of them ran while
    the full test suite was running). This measures one forward pass and one
    optimiser step on an idle process, alternating GRU/SSM so a drift in machine
    load lands on both arms rather than on one, and repeats the alternation.

    What it does **not** measure: process RSS (shared with torch, not
    attributable per arm), GPU, or end-to-end latency. Checkpoint bytes and
    parameter counts are facts about the weights, not throughput claims.
    """
    torch = model_torch()
    load_start = os.getloadavg() if hasattr(os, "getloadavg") else (float("nan"),) * 3
    batch = generate_sessions(
        COST["batch_size"],
        seed=COST["seed"],
        gap_count=COST["gap_count"],
        gap_mode="equal",
    )
    arms = ("gru", "ssm")
    models = {
        arch: build_core(
            arch,
            seed=COST["seed"],
            hidden=args.hidden,
            emb=args.emb,
            chunk_seconds=REGISTERED["chunk_seconds"],
        )
        for arch in arms
    }
    optimisers = {arch: torch.optim.Adam(models[arch].parameters(), lr=args.lr) for arch in arms}

    timings: Dict[str, Dict[str, List[Dict[str, float]]]] = {
        arch: {"forward": [], "train_step": []} for arch in arms
    }
    for alternation in range(COST["alternations"]):
        order = arms if alternation % 2 == 0 else tuple(reversed(arms))
        for arch in order:
            model = models[arch]
            optimiser = optimisers[arch]

            model.eval()

            def _forward(model=model):
                with torch.no_grad():
                    run_sessions(model, batch, arm="core")

            model.train()

            def _step(model=model, optimiser=optimiser):
                _train_step(model, optimiser, batch, arm="core", grad_clip=REGISTERED["grad_clip"])

            forward = _time_phase(_forward, warmup=COST["warmup"], reps=COST["reps"])
            step = _time_phase(_step, warmup=COST["warmup"], reps=COST["reps"])

            timings[arch]["forward"].append(forward)
            timings[arch]["train_step"].append(step)
            print(
                f"  {arch} #{alternation}: forward {forward['median'] * 1e3:.2f} ms | "
                f"train step {step['median'] * 1e3:.2f} ms",
                flush=True,
            )

    arms_report = {}
    for arch in arms:
        model = models[arch]
        arms_report[arch] = {
            "parameters": model.parameter_count(),
            "checkpoint_bytes": _checkpoint_bytes(model),
            "state_bytes_per_batch": int(COST["batch_size"]) * int(model.hidden) * 4,
            "forward": _aggregate(timings[arch]["forward"]),
            "train_step": _aggregate(timings[arch]["train_step"]),
        }

    ratio = {
        "parameters": arms_report["ssm"]["parameters"] / arms_report["gru"]["parameters"],
        "checkpoint_bytes": (
            arms_report["ssm"]["checkpoint_bytes"] / arms_report["gru"]["checkpoint_bytes"]
        ),
        "forward": (
            arms_report["ssm"]["forward"]["median_ms"] / arms_report["gru"]["forward"]["median_ms"]
        ),
        "train_step": (
            arms_report["ssm"]["train_step"]["median_ms"]
            / arms_report["gru"]["train_step"]["median_ms"]
        ),
    }

    return {
        "kind": "cost",
        "registered": False,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "cost": dict(COST),
        "config": {
            "hidden": args.hidden,
            "emb": args.emb,
            "chunk_seconds": REGISTERED["chunk_seconds"],
            "token_count": TOKEN_COUNT,
            "lr": args.lr,
            "grad_clip": REGISTERED["grad_clip"],
            "torch_threads": int(torch.get_num_threads()),
            "torch_version": torch.__version__,
            "cpu_count": os.cpu_count(),
            "load_avg_start": [round(value, 2) for value in load_start],
            "load_avg_end": [
                round(value, 2)
                for value in (os.getloadavg() if hasattr(os, "getloadavg") else (float("nan"),) * 3)
            ],
        },
        "arms": arms_report,
        "ratio": ratio,
        "caveats": [
            "single process, CPU only, PyTorch eager; no GPU / no inductor",
            "the machine is a desktop, not a dedicated benchmark host: desktop apps and "
            "one unrelated background process keep the load average above 1, so read the "
            "medians and the alternating order, not the absolute milliseconds",
            "process RSS is shared and is not attributed per arm",
            "state_bytes_per_batch counts the hidden state only (no allocator overhead)",
            "a smaller parameter count is not by itself 'cheaper' until both arms "
            "are wired into the same production call path (P4)",
        ],
    }


def print_cost_report(report: Dict[str, Any]) -> None:
    config = report["config"]
    print(
        f"\n== 成本量測（同一進程、交替順序；沒有其它量測在跑）== "
        f"threads={config['torch_threads']} cpus={config['cpu_count']} "
        f"load={config['load_avg_start']}→{config['load_avg_end']}"
    )
    for arch, entry in report["arms"].items():
        print(
            f"  {arch:4s} params {entry['parameters']:6d} | "
            f"ckpt {entry['checkpoint_bytes'] / 1024:7.1f} KiB | "
            f"forward {entry['forward']['median_ms']:7.2f} ms "
            f"[{entry['forward']['min_ms']:.2f}–{entry['forward']['max_ms']:.2f}] | "
            f"train {entry['train_step']['median_ms']:7.2f} ms "
            f"[{entry['train_step']['min_ms']:.2f}–{entry['train_step']['max_ms']:.2f}]"
        )
    ratio = report["ratio"]
    print(
        f"  SSM/GRU  params {ratio['parameters']:.3f} | ckpt {ratio['checkpoint_bytes']:.3f} | "
        f"forward {ratio['forward']:.3f} | train {ratio['train_step']:.3f}"
    )
    print("  注意：這不是能力，也不是端到端延遲；P4 接上生產前不宣稱「成本可接受」。")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--round",
        type=int,
        choices=sorted(ROUNDS),
        default=1,
        help="1 = registered §37 (unequal gaps); 2 = registered §38 (equal step counts)",
    )
    parser.add_argument(
        "--l-al-weight",
        type=float,
        default=None,
        help="override the round's registered L_al weight (smoke runs only)",
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=list(REGISTERED["seeds"]))
    parser.add_argument("--epochs", type=int, default=REGISTERED["epochs"])
    parser.add_argument("--batch-size", type=int, default=REGISTERED["batch_size"])
    parser.add_argument("--lr", type=float, default=REGISTERED["lr"])
    parser.add_argument("--hidden", type=int, default=REGISTERED["hidden"])
    parser.add_argument("--emb", type=int, default=REGISTERED["emb"])
    parser.add_argument("--train-sessions", type=int, default=REGISTERED["train_sessions"])
    parser.add_argument("--eval-sessions", type=int, default=REGISTERED["eval_sessions"])
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
    )
    parser.add_argument("--json", action="store_true", help="print the full report as JSON")
    parser.add_argument(
        "--cost",
        action="store_true",
        help="measure the cost of both arms (§40.6); trains nothing, scores nothing",
    )
    args = parser.parse_args(argv)

    if args.cost:
        report = run_cost(args)
        print_cost_report(report)
        out = args.out or (
            REPO_ROOT / "data" / "intelligence_reports" / "probe_state_cycles_cost.json"
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nreport: {out}")
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    if args.out is None:
        name = {
            1: "probe_state_cycles.json",
            2: "probe_state_cycles_round2.json",
            3: "probe_state_cycles_round3.json",
            4: "probe_state_cycles_round4.json",
        }[args.round]
        args.out = REPO_ROOT / "data" / "intelligence_reports" / name

    report = run(args)
    print_report(report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nreport: {args.out}")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["all_pass"] or not report["registered"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
