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
    python3 scripts/probe_state_cycles.py                 # the registered run
    python3 scripts/probe_state_cycles.py --seeds 0 --epochs 1 \
        --train-sessions 256 --eval-sessions 64           # smoke only
"""

from __future__ import annotations

import argparse
import json
import math
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
from ai.core.stateful_decoder import GRUCore  # noqa: E402

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


def generate_sessions(count: int, seed: int) -> List[Session]:
    """Deterministic session generator (registered in §37.2)."""
    rng = random.Random(seed)
    sessions: List[Session] = []
    for _ in range(count):
        key = rng.choice(KEYS)
        value = rng.choice(VALUES)
        if rng.random() < 0.5:
            total = rng.uniform(0.0, 200.0)
        else:
            total = rng.uniform(280.0, 400.0)
        weights = [rng.random() + 0.05 for _ in range(GAP_COUNT)]
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
    for index in range(GAP_COUNT - 1):
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
                [gaps_i[GAP_COUNT - 1] for gaps_i in gap_source],
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
) -> GRUCore:
    torch = model_torch()
    torch.manual_seed(seed)
    model = GRUCore(
        TOKEN_COUNT,
        hidden=hidden,
        emb=emb,
        chunk_seconds=chunk_seconds,
        seed=seed,
    )
    model.train()
    optimiser = torch.optim.Adam(model.parameters(), lr=lr)
    rng = random.Random(seed * 7919 + 13)
    order = list(range(len(sessions)))

    for _epoch in range(epochs):
        rng.shuffle(order)
        for start in range(0, len(order), batch_size):
            batch = [sessions[i] for i in order[start : start + batch_size]]
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
            for index in range(GAP_COUNT - 1):
                if arm == "core":
                    state = model.al_step(
                        _gap_tensor(batch, index, torch, device),
                        state,
                    )
                _, state = model.ai_step(talk, state)
            if arm == "core":
                state = model.al_step(
                    _gap_tensor(batch, GAP_COUNT - 1, torch, device),
                    state,
                )

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

            optimiser.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(list(model.parameters()), grad_clip)
            optimiser.step()
            model.invalidate_hash()

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
    registered = (
        args.epochs == REGISTERED["epochs"]
        and args.train_sessions == REGISTERED["train_sessions"]
        and args.eval_sessions == REGISTERED["eval_sessions"]
        and args.hidden == REGISTERED["hidden"]
        and args.emb == REGISTERED["emb"]
        and tuple(args.seeds) == tuple(REGISTERED["seeds"])
    )

    per_seed: List[Dict[str, Any]] = []
    provenance: List[Dict[str, Any]] = []
    started = time.time()

    for seed in args.seeds:
        train = generate_sessions(args.train_sessions, seed=1000 + seed)
        heldout = generate_sessions(args.eval_sessions, seed=2000 + seed)

        shared = dict(
            seed=seed,
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            grad_clip=REGISTERED["grad_clip"],
            hidden=args.hidden,
            emb=args.emb,
            chunk_seconds=REGISTERED["chunk_seconds"],
        )
        core = train_arm(train, arm="core", **shared)
        hand = train_arm(train, arm="hand", **shared)

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
                gap_override=[(30.0,) * GAP_COUNT for _ in heldout],
            ),
            "hand_state": evaluate(hand, heldout, arm="hand"),
            "hand_state_ablated": evaluate(hand, heldout, arm="hand", ablate=True),
            "hand_state_no_bucket": evaluate(hand, heldout, arm="hand", bucket_override=PAD),
        }
        metrics["t4_restart_delta"] = restart_delta(core, heldout[:200])
        metrics["semigroup_gap"] = semigroup_gap(core)
        metrics["zero_time_identity"] = float(zero_time_identity(core))
        hash_after = core.weights_hash()

        torch = model_torch()
        with torch.no_grad():
            token_probe = run_sessions(core, heldout[:32], arm="core")
        seen_tokens = [int(token) for token in token_probe["query_tokens"].flatten().tolist()]
        core_has_bucket = any(token in BUCKET_TOKENS for token in seen_tokens)

        provenance.append(
            {
                "seed": seed,
                "weights_hash_stable": hash_before == hash_after,
                "weights_hash": hash_before,
                "core_parameters": core.parameter_count(),
                "hand_parameters": hand.parameter_count(),
                "core_tokens_include_bucket": core_has_bucket,
                "core_query_tokens": sorted(set(seen_tokens)),
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

    report = {
        "registered": registered,
        "registration": "docs/06-project-management/CORE_GAP_ANALYSIS.md §37",
        "config": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "lr": args.lr,
            "hidden": args.hidden,
            "emb": args.emb,
            "chunk_seconds": REGISTERED["chunk_seconds"],
            "train_sessions": args.train_sessions,
            "eval_sessions": args.eval_sessions,
            "seeds": list(args.seeds),
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
    if not report["registered"]:
        print("\n⚠️  非登記參數：這不是 §37 的登記結果，只可當煙霧測試。\n")
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

    print("\n== 預登記判定 ==")
    for name, passed in report["checks"].items():
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
    print(f"\n  all_pass = {report['all_pass']}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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
        default=REPO_ROOT / "data" / "intelligence_reports" / "probe_state_cycles.json",
    )
    parser.add_argument("--json", action="store_true", help="print the full report as JSON")
    args = parser.parse_args(argv)

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
