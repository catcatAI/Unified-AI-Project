#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Pre-registered SNN vs GRU comparison on addition 0-99 (CORE_GAP §36).

The question this answers is narrow and decidable: at an **equal parameter
count and an equal number of optimiser steps**, on the one task where the
token-SNN has been measured to learn (§35.3), does replacing the LIF
recurrence with a GRU change the result? If a GRU of the same size also
fails, architecture is not the current gap. If it clearly wins, architecture
is a real variable and "just make it bigger" is not an answer.

Everything that could move the score after the fact is fixed *before* the
run (CORE_GAP_ANALYSIS.md §36, written first):

* task and split — ``a + b``, ``a, b in [0, 99]``; leak-guarded against the
  frozen test with ``problem_key`` (commutative for ``+``); ``Random(0)``
  shuffle, first 9,000 train, the rest held out;
* budget — 16 epochs x 141 batches = 2,256 steps, batch 64, Adam lr 5e-3
  constant, grad clip 1.0, no KD / scheduled sampling / tail weight;
* arms — SNN hidden 256 / 2048; GRU hidden size chosen by parameter matching
  (<= 2% error), never by score;
* metric — greedy exact match on **all** held-out pairs;
* decision — per size, paired by seed, mean difference with a 95% t interval
  (df = 4). If the interval contains 0 the result is "no detectable
  difference at this budget", not "equal".

The GRU arm is a *control*, not a candidate for production: it inherits
``TokenSNN``'s batching, masked cross-entropy, ``train_on`` loop and greedy
decoder, so the only thing that differs is the recurrence. It is defined here
rather than in ``ai/ed3n/token_snn.py`` on purpose — production code should
not carry a comparison arm.

Usage::

    python3 scripts/compare_snn_gru.py                     # the registered run
    python3 scripts/compare_snn_gru.py --epochs 1 --seeds 0 \
        --sizes small --train-limit 640 --eval-limit 100    # smoke only
"""

from __future__ import annotations

import argparse
import contextlib
import io
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

from ai.ed3n.token_snn import (  # noqa: E402
    CharVocab,
    TokenConfig,
    TokenSNN,
    resolve_device,
)
from arithmetic_task import parse_plain, problem_key  # noqa: E402
from train_token_snn import exact_match, fits  # noqa: E402
from train_token_snn_curriculum import eval_pool, leak_guard  # noqa: E402

REPORT_PATH = REPO_ROOT / "data" / "intelligence_reports" / "snn_vs_gru.json"
# Two-sided 95% Student-t critical value for df = 4 (5 paired seeds).
# Hard-coded so the decision rule cannot silently change with a scipy version.
T975_DF4 = 2.776
PREREGISTRATION = "docs/06-project-management/CORE_GAP_ANALYSIS.md §36"

# Pre-registered arm sizes. GRU hidden sizes are *not* listed here: they are
# derived by the matching rule below, so a change to the parameter count of
# either architecture cannot silently break the comparison.
SNN_SIZES: Dict[str, int] = {"small": 256, "large": 2048}


def _make_gru_net(torch: Any, pad_id: int) -> Any:
    """Define the control ``nn.Module`` lazily (keeps this file torch-free)."""
    nn = torch.nn

    class _GRUNet(nn.Module):
        def __init__(self, vocab_size: int, cfg: TokenConfig, d_hidden: int) -> None:
            super().__init__()
            self.cfg = cfg
            self.n_layers = 1
            self.embed = nn.Embedding(vocab_size, cfg.d_emb, padding_idx=pad_id)
            self.gru = nn.GRU(cfg.d_emb, int(d_hidden), batch_first=True)
            self.head = nn.Linear(int(d_hidden), vocab_size)

        # -- the four methods TokenSNN's training / decoding path needs ------
        def init_state(self, batch: int, device: Any = None) -> Any:
            # ``nn.GRU`` state is (layers, batch, hidden); follow the weights.
            return self.gru.weight_hh_l0.new_zeros(1, batch, self.gru.hidden_size)

        def advance_hidden(self, token_ids: Any, state: Any) -> Any:
            x = self.embed(token_ids.reshape(-1)).unsqueeze(1)
            out, state = self.gru(x, state)
            return out[:, 0], state

        def advance(self, token_ids: Any, state: Any) -> Any:
            out, state = self.advance_hidden(token_ids, state)
            return self.head(out), state

        def encode(self, ids: Any) -> Any:
            out, _ = self.gru(self.embed(ids))
            return out

        def forward(self, ids: Any) -> Any:
            return self.head(self.encode(ids))

    return _GRUNet


class GRUDecoder(TokenSNN):
    """``TokenSNN`` with the LIF recurrence swapped for a GRU (control arm).

    Everything outside the recurrence is inherited: ``encode_pair`` /
    ``make_batch`` (same ids, same padding mask), ``loss`` (same shifted,
    masked cross-entropy), ``train_on`` (same shuffle / Adam / clip / guard)
    and ``generate`` (same greedy loop). ``dynamics()`` is SNN-specific and
    will raise here on purpose — it must not be called on this arm.
    """

    def __init__(
        self,
        vocab: Any,
        config: Optional[TokenConfig] = None,
        device: str = "auto",
        d_hidden: int = 128,
    ) -> None:
        import torch

        self.torch = torch
        self.vocab = vocab
        self.config = config or TokenConfig()
        self.device = resolve_device(torch, device)
        net_cls = _make_gru_net(torch, vocab.pad_id)
        self.net = net_cls(len(vocab), self.config, int(d_hidden)).to(self.device)

    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.torch.save(
            {
                "kind": "gru",
                "d_hidden": int(self.net.gru.hidden_size),
                "vocab": self.vocab.to_dict(),
                "config": self.config.to_dict(),
                "state": self.net.state_dict(),
            },
            str(path),
        )

    @classmethod
    def load(
        cls, path: Path | str, map_location: str = "cpu", device: str = "auto"
    ) -> "GRUDecoder":
        import torch

        payload = torch.load(str(path), map_location=map_location, weights_only=True)
        if payload.get("kind") != "gru":
            raise ValueError(f"{path} is not a GRU control checkpoint")
        vocab = CharVocab.from_dict(payload["vocab"])
        model = cls(
            vocab,
            TokenConfig(**payload["config"]),
            device=device,
            d_hidden=int(payload["d_hidden"]),
        )
        model.net.load_state_dict(payload["state"])
        model.net.eval()
        return model


def count_params(model: TokenSNN) -> int:
    return sum(p.numel() for p in model.net.parameters())


def gru_param_count(vocab_size: int, cfg: TokenConfig, d_hidden: int) -> int:
    """Analytic parameter count of ``_GRUNet``: embed + GRU + head.

    Kept next to the module it mirrors (and checked against a constructed
    model by the contract tests) so the matching rule costs no allocation.
    """
    d = int(d_hidden)
    embed = vocab_size * cfg.d_emb
    gru = 3 * (cfg.d_emb * d + d * d + 2 * d)
    head = d * vocab_size + vocab_size
    return embed + gru + head


def match_gru_hidden(vocab_size: int, cfg: TokenConfig, target: int) -> Tuple[int, int]:
    """Nearest GRU hidden size to ``target`` parameters (pre-registered rule)."""
    centre = max(2, int(round(math.sqrt(target / 3.0))))
    best: Tuple[float, int, int] = (float("inf"), centre, 0)
    for d in range(max(2, centre - 256), centre + 257):
        n = gru_param_count(vocab_size, cfg, d)
        gap = abs(n - target)
        if gap < best[0]:
            best = (float(gap), d, n)
    return best[1], best[2]


def build_split(train_limit: int = 0, eval_limit: int = 0) -> Dict[str, Any]:
    """The frozen split from §36.1 (limits are smoke-test only).

    Split by ``problem_key``, not by row: ``+`` is commutative, so ``3 + 4``
    and ``4 + 3`` are the *same exercise*. A row split puts one order in
    training and the other in held-out for ~90% of held-out pairs, which
    measures recall of an operand pair rather than generalisation. Whole key
    groups move together, so both orders of an exercise stay on one side.
    """
    texts, _test_plus = eval_pool()
    pool = leak_guard(
        [(f"{a} + {b}", str(a + b)) for a in range(100) for b in range(100)],
        texts,
    )
    groups: Dict[Any, List[Tuple[str, str]]] = {}
    for prompt, answer in pool:
        key = problem_key(parse_plain(prompt))
        groups.setdefault(key, []).append((prompt, answer))
    keys = sorted(groups, key=lambda k: (str(k)))
    random.Random(0).shuffle(keys)
    train: List[Tuple[str, str]] = []
    held: List[Tuple[str, str]] = []
    for key in keys:
        group = groups[key]
        if len(train) + len(group) <= 9000:
            train.extend(group)
        else:
            held.extend(group)
    cfg = TokenConfig(d_emb=96, d_hidden=192, max_len=24)
    vocab = CharVocab.build(
        [p + "\n" + a for p, a in pool],
        min_count=cfg.min_count,
        max_vocab=cfg.max_vocab,
    )
    train = fits(train, vocab, cfg.max_len)
    held = fits(held, vocab, cfg.max_len)
    if train_limit > 0:
        train = train[:train_limit]
    if eval_limit > 0:
        held = held[:eval_limit]
    return {
        "cfg": cfg,
        "vocab": vocab,
        "train": train,
        "held": held,
        "pool": len(pool),
        "leaked": 10000 - len(pool),
    }


def _quiet_exact(model: TokenSNN, pairs: Sequence[Tuple[str, str]]) -> Dict[str, float]:
    """Same metric as every other run (``exact_match``), minus its progress line."""
    with contextlib.redirect_stdout(io.StringIO()):
        return exact_match(model, list(pairs), 0, seed=7)


def run_arm(
    name: str,
    kind: str,
    d_hidden: int,
    vocab: Any,
    cfg: TokenConfig,
    train: Sequence[Tuple[str, str]],
    held: Sequence[Tuple[str, str]],
    seed: int,
    epochs: int,
    batch: int,
    lr: float,
    device: str,
) -> Dict[str, Any]:
    import torch

    torch.manual_seed(seed)
    # ``cfg`` comes from the data builder (d_hidden is only a placeholder there);
    # the arm's size must come from the matched spec, so build a per-arm config.
    from dataclasses import replace

    arm_cfg = replace(cfg, d_hidden=int(d_hidden))
    if kind == "snn":
        model: TokenSNN = TokenSNN(vocab, arm_cfg, device=device)
    else:
        model = GRUDecoder(vocab, arm_cfg, device=device, d_hidden=d_hidden)
    params = count_params(model)
    started = time.time()
    history = model.train_on(
        list(train),
        epochs=epochs,
        batch_size=batch,
        lr=lr,
        seed=seed,
    )
    train_seconds = time.time() - started
    with contextlib.redirect_stdout(io.StringIO()):
        held_eval = _quiet_exact(model, held)
        train_eval = _quiet_exact(model, list(train[:200]))
        tf = model.tf_accuracy(list(held))
    per_epoch_steps = math.ceil(len(train) / batch)
    skipped = sum(int(row.get("skipped", 0)) for row in history)
    steps = len(history) * per_epoch_steps - skipped
    return {
        "arm": name,
        "kind": kind,
        "seed": seed,
        "d_hidden": d_hidden,
        "params": params,
        "epochs": len(history),
        "steps": steps,
        "skipped": skipped,
        "rolled_back": sum(1 for row in history if row.get("rolled_back")),
        "final_lr": history[-1]["lr"] if history else None,
        "train_seconds": round(train_seconds, 2),
        "held_exact": round(float(held_eval["exact"]), 6),
        "held_exact_full": round(float(held_eval["exact_full"]), 6),
        "held_tf": tf["tf_acc"],
        "train_exact_200": round(float(train_eval["exact"]), 6),
        "loss_history": [
            {"epoch": int(row["epoch"]), "loss": round(float(row["loss"]), 6)} for row in history
        ],
        "device": str(model.device),
    }


def paired_decision(snn: Sequence[float], gru: Sequence[float]) -> Dict[str, Any]:
    """Paired mean difference with a 95% t interval (df = len - 1)."""
    diffs = [float(a) - float(b) for a, b in zip(snn, gru)]
    n = len(diffs)
    if n == 0:
        return {"n": 0, "mean_diff": None, "ci_low": None, "ci_high": None, "verdict": "empty"}
    mean = sum(diffs) / n
    if n < 2:
        return {
            "n": n,
            "mean_diff": round(mean, 6),
            "ci_low": None,
            "ci_high": None,
            "verdict": "needs at least 2 seeds",
        }
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    half = T975_DF4 * math.sqrt(var / n) if n == 5 else None
    lo = None if half is None else mean - half
    hi = None if half is None else mean + half
    if lo is not None and lo > 0:
        verdict = "snn_better"
    elif hi is not None and hi < 0:
        verdict = "gru_better"
    elif lo is not None:
        verdict = "no_detectable_difference"
    else:
        verdict = "no_interval_for_n"
    return {
        "n": n,
        "mean_diff": round(mean, 6),
        "stdev_diff": round(math.sqrt(var), 6),
        "ci_low": None if lo is None else round(lo, 6),
        "ci_high": None if hi is None else round(hi, 6),
        "verdict": verdict,
    }


def summarise(runs: Sequence[Dict[str, Any]], sizes: Sequence[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for size in sizes:
        snn = [r for r in runs if r["arm"] == f"snn_{size}"]
        gru = [r for r in runs if r["arm"] == f"gru_{size}"]
        by_seed_gru = {r["seed"]: r["held_exact"] for r in gru}
        paired = [(r["seed"], r["held_exact"], by_seed_gru[r["seed"]]) for r in snn]
        paired.sort()
        decision = paired_decision([p[1] for p in paired], [p[2] for p in paired])
        snn_mean = sum(r["held_exact"] for r in snn) / len(snn) if snn else None
        gru_mean = sum(r["held_exact"] for r in gru) / len(gru) if gru else None
        best = max(x for x in (snn_mean, gru_mean) if x is not None) if snn and gru else None
        if best is not None and best < 0.10:
            # Pre-registered: a size where neither arm learns is inconclusive,
            # not a tie, and cannot be used to argue architecture is irrelevant.
            decision["verdict"] = "inconclusive_neither_learned"
        out[size] = {
            "snn_mean": None if snn_mean is None else round(snn_mean, 6),
            "gru_mean": None if gru_mean is None else round(gru_mean, 6),
            "paired": [
                {"seed": seed, "snn": round(a, 6), "gru": round(b, 6)} for seed, a, b in paired
            ],
            **decision,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--epochs", type=int, default=16)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=5e-3)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--sizes", nargs="+", default=["small", "large"], choices=sorted(SNN_SIZES))
    ap.add_argument("--out", default=str(REPORT_PATH))
    ap.add_argument(
        "--train-limit",
        type=int,
        default=0,
        help="smoke only: cap training rows (the registered run uses 0 = all 9,000)",
    )
    ap.add_argument(
        "--eval-limit",
        type=int,
        default=0,
        help="smoke only: cap held-out rows (the registered run uses 0 = all)",
    )
    args = ap.parse_args()

    if args.train_limit or args.eval_limit:
        print("SMOKE RUN: limits set; this is not the registered comparison.", flush=True)

    split = build_split(args.train_limit, args.eval_limit)
    cfg: TokenConfig = split["cfg"]
    vocab = split["vocab"]
    train = split["train"]
    held = split["held"]
    print(
        f"pool={split['pool']} leaked={split['leaked']} vocab={len(vocab)} "
        f"train={len(train)} held={len(held)}",
        flush=True,
    )

    import torch

    device = resolve_device(torch, args.device)
    steps_per_epoch = math.ceil(len(train) / args.batch)
    print(
        f"device={device} seed={args.seeds} epochs={args.epochs} "
        f"batch={args.batch} steps/epoch={steps_per_epoch} "
        f"total_steps={steps_per_epoch * args.epochs}",
        flush=True,
    )

    # Parameter matching is fixed before any score exists.
    arms: Dict[str, Dict[str, Any]] = {}
    for size in args.sizes:
        d_snn = SNN_SIZES[size]
        n_snn = _snn_param_count(len(vocab), cfg, d_snn)
        d_gru, n_gru = match_gru_hidden(len(vocab), cfg, n_snn)
        gap = abs(n_gru - n_snn) / max(1, n_snn)
        if gap > 0.02:
            raise SystemExit(f"{size}: GRU cannot be matched within 2% (gap {gap:.3%})")
        arms[f"snn_{size}"] = {
            "kind": "snn",
            "d_hidden": d_snn,
            "params": n_snn,
            "size": size,
        }
        arms[f"gru_{size}"] = {
            "kind": "gru",
            "d_hidden": d_gru,
            "params": n_gru,
            "size": size,
        }
        print(
            f"  {size}: snn d_hidden={d_snn} {n_snn:,} params  <->  "
            f"gru d_hidden={d_gru} {n_gru:,} params (gap {gap:.2%})",
            flush=True,
        )

    runs: List[Dict[str, Any]] = []
    started = time.time()
    for seed in args.seeds:
        for size in args.sizes:
            # Arm order is fixed per seed; interleaving seeds keeps any machine
            # drift spread across architectures instead of one of them.
            for arm_name in (f"snn_{size}", f"gru_{size}"):
                spec = arms[arm_name]
                print(
                    f"[{time.time() - started:7.1f}s] {arm_name} seed={seed} "
                    f"d={spec['d_hidden']}",
                    flush=True,
                )
                row = run_arm(
                    arm_name,
                    spec["kind"],
                    spec["d_hidden"],
                    vocab,
                    cfg,
                    train,
                    held,
                    seed,
                    args.epochs,
                    args.batch,
                    args.lr,
                    device,
                )
                if row["params"] != spec["params"]:
                    raise SystemExit(
                        f"{arm_name}: analytic params {spec['params']} != built "
                        f"model {row['params']}; the matching rule is wrong"
                    )
                runs.append(row)
                print(
                    f"    held_exact={row['held_exact']:.3f} "
                    f"held_tf={row['held_tf']:.3f} "
                    f"train_exact={row['train_exact_200']:.3f} "
                    f"final_loss={row['loss_history'][-1]['loss']:.3f} "
                    f"{row['train_seconds']:.1f}s",
                    flush=True,
                )

    decision = summarise(runs, args.sizes)
    report = {
        "experiment": "snn_vs_gru",
        "preregistration": PREREGISTRATION,
        "task": {
            "name": "addition_0_99",
            "prompt": "a + b, a,b in [0,99]",
            "train": len(train),
            "held_out": len(held),
            "pool": split["pool"],
            "leaked_against_frozen_test": split["leaked"],
            "shuffle_seed": 0,
        },
        "budget": {
            "epochs": args.epochs,
            "batch": args.batch,
            "steps_per_epoch": steps_per_epoch,
            "total_steps": steps_per_epoch * args.epochs,
            "lr": args.lr,
            "guard": True,
            "kd": False,
            "scheduled_sampling": False,
            "tail_weight": 1.0,
        },
        "vocab": {"size": len(vocab), "itos": list(vocab.itos)},
        "device": str(device),
        "arms": {
            name: {k: v for k, v in spec.items() if k != "size"} for name, spec in arms.items()
        },
        "runs": runs,
        "decision": decision,
        "seconds": round(time.time() - started, 1),
        "note": (
            "GRU is a control arm, not a production candidate. See "
            f"{PREREGISTRATION} for the fixed design and the decision rule."
        ),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\ndecision (paired by seed, 95% t interval df=4):", flush=True)
    for size, row in decision.items():
        print(
            f"  {size}: snn={row['snn_mean']} gru={row['gru_mean']} "
            f"diff={row['mean_diff']} ci=[{row['ci_low']}, {row['ci_high']}] "
            f"-> {row['verdict']}",
            flush=True,
        )
    print(f"wrote {out} in {report['seconds']}s", flush=True)
    return 0


def _snn_param_count(vocab_size: int, cfg: TokenConfig, d_hidden: int) -> int:
    """Analytic ``_SpikeNet`` count: embed + w_in + w_rec + head + norm + 2.

    ``layers=1`` is the pre-registered arm. Kept beside ``gru_param_count``
    so both sides of the match use the same arithmetic; the contract tests
    compare both against constructed models.
    """
    d = int(d_hidden)
    embed = vocab_size * cfg.d_emb
    w_in = cfg.d_emb * d + d
    w_rec = d * d
    head = d * vocab_size + vocab_size
    norm = 2 * d
    return embed + w_in + w_rec + head + norm + 2


if __name__ == "__main__":
    raise SystemExit(main())
