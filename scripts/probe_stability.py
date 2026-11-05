#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Measure whether long training erodes the recurrent structure.

The complaint that started this probe: past some point, more training stops
helping and eventually the run "blows up". The usual answer is capacity,
learning rate or overfitting. This probe tests a different one, which the
measurements support: **the structure that holds state is being optimised
away**, one small step at a time, and the loss barely notices because the task
can be served another way.

Three free quantities can each buy a lower loss without learning the task:

* ``theta`` — raise the threshold until the stack stops firing (bounded since
  CORE_GAP §三十);
* ``beta`` — lower the leak until the membrane forgets faster, i.e. replace
  integration by wire-through;
* ``w_rec`` — raise the recurrence gain until nothing has to be integrated at
  all.

The probe walks a small stack through many epochs on real rows and records, per
epoch, the loss on train and held-out rows together with those three quantities
and an **autonomous orbit**: prime the state with a real row, then cut the input
and let the recurrence run. A structure that holds state keeps firing in a
pattern of its own; a structure that has been eroded dies to silence.

Measured at 200 rows / 120 epochs (CORE_GAP §三十一): beta 0.900 -> 0.811,
sr(w_rec) 0.55 -> 1.58, orbit activity 0.54 -> 0.12, while train loss fell
0.85 -> 0.73 and validation loss turned up at epoch ~40 (0.825 -> 0.865). The
drift is monotone and happens *while the loss improves*, which is why no loss
curve can see it.

Two projections are offered to hold the band (both off by default, both
bit-identical to the historical forward when off):

    --leak-floor 0.9    memory horizon cannot shrink (1/(1-beta) >= 10 steps)
    --gain-cap 1.0      a perturbation may not grow per step

Usage:
    ./.venv/bin/python scripts/probe_stability.py
    ./.venv/bin/python scripts/probe_stability.py --epochs 120 --rows 200
    ./.venv/bin/python scripts/probe_stability.py --leak-floor 0.9 --gain-cap 1.0
    ./.venv/bin/python scripts/probe_stability.py --report out/stability.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

DEFAULT_DATA = (
    REPO_ROOT / "apps" / "backend" / "data" / "processed" / "ai_al_round7_3dp_train.jsonl"
)


def load_pairs(path: Path) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Rows from a jsonl corpus: last 300 held out, or the last 20% if fewer."""
    pairs = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            pairs.append((row["input"], row["output"]))
    if len(pairs) < 10:
        raise SystemExit(f"{path} has {len(pairs)} rows; need at least 10")
    if len(pairs) > 340:
        return pairs[:-300], pairs[-300:]
    cut = int(len(pairs) * 0.8)
    return pairs[:cut], pairs[cut:]


def spectral_radius(torch: Any, weight: Any, iters: int = 100, tol: float = 1e-4) -> float:
    """Largest |eigenvalue| of a square matrix, by power iteration."""
    with torch.no_grad():
        v = torch.randn(weight.shape[1], device=weight.device)
        v = v / (v.norm() + 1e-12)
        prev, radius = 0.0, 0.0
        for _ in range(iters):
            v = weight @ v
            radius = float(v.norm())
            if radius == 0.0:
                return 0.0
            v = v / radius
            if prev and abs(radius - prev) <= tol * radius:
                break
            prev = radius
    return radius


def orbit(
    torch: Any, model: Any, rows: Sequence[Tuple[str, str]], steps: int = 40
) -> Dict[str, Any]:
    """Autonomous dynamics: prime with a real row, then run with no input.

    ``end`` is the last-layer firing rate after ``steps``; ``dead_at`` is the
    first step where the layer is silent.

    Caveat, measured: with the input cut, the ``w_in`` biases are still there, so
    the membrane settles at ``b / (1 - beta)`` and keeps firing even when the
    recurrence is switched off entirely. The orbit is therefore a *diagnostic*
    of how much spontaneous drive the stack carries, not evidence that a learned
    attractor was preserved; ``summarise`` reads its verdict off beta and sr and
    only treats exact silence (``dead_at``) as decisive.
    """
    net = model.net
    cfg = model.config
    leak = torch.sigmoid(net.beta)
    theta = abs(net.threshold)
    ids, _mask, _cuts = model.make_batch(list(rows[:4]))
    ids = ids.to(model.device)
    mem = [net.embed.weight.new_zeros((ids.shape[0], cfg.d_hidden)) for _ in range(net.n_layers)]
    spk = [torch.zeros_like(m) for m in mem]
    with torch.no_grad():
        for step in range(ids.shape[1]):
            x = net.embed(ids[:, step])
            for layer in range(net.n_layers):
                drive = x if layer == 0 else spk[layer - 1]
                skip = net.w_skip[layer](x) if layer else 0.0
                mem[layer] = (
                    leak * mem[layer] + net.w_in[layer](drive) + net.w_rec[layer](spk[layer]) + skip
                )
                spk[layer] = (mem[layer] - theta >= 0).to(mem[layer].dtype)
        trail = []
        for _ in range(steps):
            for layer in range(net.n_layers):
                drive = (
                    torch.zeros((ids.shape[0], cfg.d_emb), device=model.device)
                    if layer == 0
                    else spk[layer - 1]
                )
                mem[layer] = (
                    leak * mem[layer] + net.w_in[layer](drive) + net.w_rec[layer](spk[layer])
                )
                spk[layer] = (mem[layer] - theta >= 0).to(mem[layer].dtype)
            trail.append(spk[-1].clone())
    rates = [float(torch.stack(trail)[t].mean()) for t in range(steps)]
    period = None
    for candidate in range(1, min(16, steps)):
        head = trail[candidate:]
        tail = trail[:-candidate]
        if all(torch.equal(a, b) for a, b in zip(head, tail)):
            period = candidate
            break
    return {
        "start": round(rates[0], 4),
        "end": round(rates[-1], 4),
        "dead_at": next((i for i, r in enumerate(rates) if r == 0.0), None),
        "period": period,
    }


def structure(torch: Any, model: Any, rows: Sequence[Tuple[str, str]]) -> Dict[str, Any]:
    """The three quantities that can be traded against learning, plus the orbit."""
    net = model.net
    beta = float(torch.sigmoid(net.beta.detach()))
    return {
        "beta": round(beta, 5),
        "horizon": round(1.0 / max(1e-6, 1.0 - beta), 3),
        "theta": round(float(abs(net.threshold.detach())), 5),
        "sr": [round(spectral_radius(torch, layer.weight), 4) for layer in net.w_rec],
        "orbit": orbit(torch, model, rows),
    }


def losses(
    torch: Any, model: Any, train: Sequence[Tuple[str, str]], val: Sequence[Tuple[str, str]]
) -> Dict[str, float]:
    out = {}
    with torch.no_grad():
        for tag, rows in (("train", train), ("val", val)):
            ids, mask, _cuts = model.make_batch(list(rows[:64]))
            out[tag] = round(float(model.loss(ids.to(model.device), mask.to(model.device))), 5)
    return out


def summarise(trajectory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """What the trajectory says: where the parameters went, and where val turned.

    The verdict is read off the three quantities, not off the orbit. Measured
    both ways (CORE_GAP §三十一): the autonomous orbit decays in *every* run,
    including one whose parameters were pinned in band, because learning to fire
    only on informative tokens also lowers spontaneous activity with no input.
    So the orbit is reported for diagnosis, and it is not used to claim the
    structure was preserved -- only exact silence would be decisive.
    """
    first, last = trajectory[0], trajectory[-1]
    best = min(trajectory, key=lambda row: row["val"])
    # only look *after* the best epoch: early epochs are above it on any curve
    turn = next(
        (
            row["epoch"]
            for row in trajectory
            if row["epoch"] > best["epoch"] and row["val"] > best["val"] + 0.01
        ),
        None,
    )
    tail = trajectory[-10:]
    sr_max = max(max(row["sr"]) for row in trajectory)
    drifted = bool(last["beta"] < first["beta"] - 0.02 or sr_max > 1.3)
    silent = any(row["orbit"]["dead_at"] is not None for row in trajectory)
    return {
        "epochs": len(trajectory),
        "beta": [first["beta"], last["beta"]],
        "horizon": [first["horizon"], last["horizon"]],
        "theta": [first["theta"], last["theta"]],
        "sr_last": last["sr"],
        "sr_max": round(sr_max, 4),
        "orbit_end": [first["orbit"]["end"], last["orbit"]["end"]],
        "orbit_silent": silent,
        "train": [first["train"], last["train"]],
        "val": [first["val"], last["val"]],
        "val_best": round(best["val"], 5),
        "val_best_epoch": best["epoch"],
        "val_tail_mean": round(sum(row["val"] for row in tail) / len(tail), 5),
        "val_regression": round(sum(row["val"] for row in tail) / len(tail) - best["val"], 5),
        "val_rose_above_best_at": turn,
        "verdict": "params-drifted" if drifted else "in-band",
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--rows", type=int, default=200, help="training rows (default 200)")
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--every", type=int, default=10, help="print every N epochs (default 10)")
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--d-emb", type=int, default=48)
    ap.add_argument("--d-hidden", type=int, default=96)
    ap.add_argument("--layers", type=int, default=2)
    ap.add_argument("--beta", type=float, default=0.9)
    ap.add_argument("--leak-floor", type=float, default=0.0)
    ap.add_argument("--gain-cap", type=float, default=0.0)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()

    import torch

    from ai.ed3n.token_snn import TokenConfig, TokenSNN, TokenVocab

    train, val = load_pairs(args.data)
    train = train[: args.rows]
    texts = [p + a for p, a in train + val]
    vocab = TokenVocab.build(texts, min_count=1, max_vocab=4000)
    torch.manual_seed(args.seed)
    model = TokenSNN(
        vocab,
        TokenConfig(
            d_emb=args.d_emb,
            d_hidden=args.d_hidden,
            layers=args.layers,
            max_len=200,
            beta=args.beta,
            leak_floor=args.leak_floor,
            gain_cap=args.gain_cap,
        ),
        device=args.device,
    )
    print(
        f"rows={len(train)}/{len(val)} vocab={len(vocab)} device={model.device} "
        f"leak_floor={args.leak_floor} gain_cap={args.gain_cap}"
    )
    trajectory: List[Dict[str, Any]] = []
    for epoch in range(1, args.epochs + 1):
        model.train_on(train, epochs=1, batch_size=args.batch, lr=args.lr, seed=args.seed + epoch)
        row: Dict[str, Any] = {"epoch": epoch}
        row.update(losses(torch, model, train, val))
        row.update(structure(torch, model, val))
        trajectory.append(row)
        if epoch % args.every == 0 or epoch == 1:
            orbit_now = row["orbit"]
            print(
                f"ep{epoch:<4} train={row['train']:.4f} val={row['val']:.4f} "
                f"beta={row['beta']:.4f} sr={row['sr']} theta={row['theta']:.3f} "
                f"orbit={orbit_now['start']:.3f}->{orbit_now['end']:.3f}"
                + ("  DEAD" if orbit_now["dead_at"] is not None else "")
            )
    summary = summarise(trajectory)
    print(
        f"\nbeta {summary['beta'][0]:.4f}->{summary['beta'][1]:.4f} "
        f"(horizon {summary['horizon'][0]:.1f}->{summary['horizon'][1]:.1f} steps) "
        f"sr {summary['sr_last']} orbit_end {summary['orbit_end'][0]:.3f}->{summary['orbit_end'][1]:.3f}"
    )
    print(
        f"train {summary['train'][0]:.4f}->{summary['train'][1]:.4f} "
        f"val {summary['val'][0]:.4f}->{summary['val'][1]:.4f} "
        f"(best {summary['val_best']:.4f} at ep{summary['val_best_epoch']}"
        + (
            f", rose above it at ep{summary['val_rose_above_best_at']})"
            if summary["val_rose_above_best_at"]
            else ")"
        )
    )
    print(
        f"tail val {summary['val_tail_mean']:.4f} vs best {summary['val_best']:.4f} "
        f"(regression {summary['val_regression']:+.4f}) -> {summary['verdict']}"
    )

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(
                {
                    "config": {k: v for k, v in vars(args).items() if not isinstance(v, Path)}
                    | {"data": str(args.data)},
                    "trajectory": trajectory,
                    "summary": summary,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
