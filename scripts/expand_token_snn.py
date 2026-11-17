#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""Widen a trained token-SNN in place, preserving what it already computes.

The question this answers is "must a bigger run start from random weights?".
It does not have to.  Every hidden unit of the parent is duplicated ``factor``
times, and the three places that touch the hidden axis are laid out so the
child's output is the parent's output:

* ``w_in`` rows - a new unit receives exactly what the unit it copies received;
* ``w_rec`` - old units keep their old recurrent row and receive **zero** from
  the new copies; a new copy receives the old row (and zero from other copies),
  so its membrane follows the copied unit step for step;
* ``head`` columns - each copy carries ``1/factor`` of the parent's column, so
  the copies sum to the parent's contribution;
* ``out_norm`` - the entries are duplicated, so the empirical mean and
  (biased) variance over the layer are unchanged.

The result is a child that is arithmetically equal to the parent up to float32
summation order (measured on the 2.5M distilled checkpoint: max |Δlogit| =
3.8e-06 on a logit scale of 65, relative 5.9e-08).  ``--noise`` then perturbs
only the new copies' incoming rows, which breaks the copy symmetry so training
can use the added capacity.  With noise=0 the check is a hard instrument gate;
with noise>0 the drift is reported and bounded rather than required to be zero.

This is not a capability claim, and it does not decide whether the added
capacity helps: the child starts from whatever plateau the parent reached.
That comparison needs its own pre-registered experiment (warm start versus the
same width from scratch, at equal tokens seen).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from ai.ed3n.token_snn import TokenConfig, TokenSNN  # noqa: E402

#: Relative drift allowed when noise == 0.  A pure widening is the parent plus
#: float32 summation order, not an approximation.
TOLERANCE_EXACT = 1e-5
#: Relative drift allowed when the copies are perturbed (measured 1.4e-04 at
#: noise=1e-3 on the 2.5M checkpoint; the bound is two orders above that).
TOLERANCE_NOISY = 1e-2


def weights_digest(state: Dict[str, Any]) -> str:
    """sha256 over sorted state entries, independent of dict order."""
    h = hashlib.sha256()
    for key in sorted(state):
        tensor = state[key].detach().cpu().contiguous()
        h.update(key.encode("utf-8"))
        h.update(str(tuple(tensor.shape)).encode("utf-8"))
        h.update(tensor.float().numpy().tobytes())
    return "sha256:" + h.hexdigest()


def expand_state_dict(
    state: Dict[str, Any],
    config: TokenConfig,
    vocab_size: int,
    factor: int,
) -> Dict[str, Any]:
    """Return a widened state dict (pure function; no torch modules built)."""
    import torch

    if factor < 2:
        raise ValueError(f"factor must be >= 2, got {factor}")
    hidden = int(config.d_hidden)
    emb = int(config.d_emb)
    layers = max(1, int(config.layers))
    hidden_new = hidden * factor
    copy_of = torch.arange(hidden_new) % hidden

    out: Dict[str, Any] = {"embed.weight": state["embed.weight"].clone()}
    for layer in range(layers):
        w_in = state[f"w_in.{layer}.weight"]
        if layer == 0:
            out[f"w_in.{layer}.weight"] = w_in[copy_of].clone()
        else:
            # Layer > 0 is driven by the previous layer's spikes, so the input
            # axis also grew: the old block is copied, the new-column block is
            # zero (old units must not hear the copies).
            widened = torch.zeros(hidden_new, hidden_new, dtype=w_in.dtype)
            widened[:hidden, :hidden] = w_in
            widened[hidden:, :hidden] = w_in[copy_of[hidden:]]
            out[f"w_in.{layer}.weight"] = widened
        out[f"w_in.{layer}.bias"] = state[f"w_in.{layer}.bias"][copy_of].clone()

        rec = state[f"w_rec.{layer}.weight"]
        widened = torch.zeros(hidden_new, hidden_new, dtype=rec.dtype)
        widened[:hidden, :hidden] = rec
        widened[hidden:, :hidden] = rec[copy_of[hidden:]]
        out[f"w_rec.{layer}.weight"] = widened

        if layer > 0:
            out[f"w_skip.{layer}.weight"] = state[f"w_skip.{layer}.weight"][copy_of].clone()
            out[f"w_skip.{layer}.bias"] = state[f"w_skip.{layer}.bias"][copy_of].clone()

    out["head.weight"] = (state["head.weight"][:, copy_of] / float(factor)).clone()
    out["head.bias"] = state["head.bias"].clone()
    out["out_norm.weight"] = state["out_norm.weight"][copy_of].clone()
    out["out_norm.bias"] = state["out_norm.bias"][copy_of].clone()
    out["beta"] = state["beta"].clone()
    out["threshold"] = state["threshold"].clone()
    return out


def expand_model(
    model: TokenSNN,
    factor: int,
    noise: float = 0.0,
    seed: int = 0,
) -> TokenSNN:
    """Build the widened child of ``model`` (same vocab, same everything else)."""
    import torch

    parent_config = model.config
    state = expand_state_dict(model.net.state_dict(), parent_config, len(model.vocab), factor)
    child_config = TokenConfig(**parent_config.to_dict())
    child_config.d_hidden = int(parent_config.d_hidden) * int(factor)
    child = TokenSNN(model.vocab, child_config, device="cpu")
    child.net.load_state_dict(state)
    if noise:
        generator = torch.Generator().manual_seed(int(seed))
        hidden = int(parent_config.d_hidden)
        with torch.no_grad():
            for layer in range(max(1, int(parent_config.layers))):
                weight = child.net.state_dict()[f"w_in.{layer}.weight"]
                # Only the new rows are perturbed: the parent's units keep the
                # function the parent had.  The scale is relative to this
                # layer's own weight spread, not a fixed absolute number.
                std = float(weight.std())
                weight[hidden:] += (
                    torch.randn(weight[hidden:].shape, generator=generator) * std * float(noise)
                )
    child.net.eval()
    return child


def probe_ids(vocab_size: int, seed: int, batch: int, seq: int) -> Any:
    """A fixed probe batch, derived only from the report's recorded constants."""
    import torch

    generator = torch.Generator().manual_seed(int(seed))
    return torch.randint(0, int(vocab_size), (int(batch), int(seq)), generator=generator)


def preservation(model: TokenSNN, child: TokenSNN, ids: Any) -> Dict[str, Any]:
    """How far the child's logits are from the parent's on the probe batch."""
    import torch

    with torch.no_grad():
        base = model.net(ids)
        out = child.net(ids)
    diff = (base - out).abs()
    max_abs = float(diff.max())
    scale = max(1e-9, float(base.abs().max()))
    return {
        "max_abs_diff": max_abs,
        "mean_abs_diff": float(diff.mean()),
        "max_abs_logit": float(base.abs().max()),
        "relative": max_abs / scale,
        "shapes_equal": tuple(base.shape) == tuple(out.shape),
    }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _config_summary(model: TokenSNN) -> Dict[str, Any]:
    return {
        "params": int(sum(p.numel() for p in model.net.parameters())),
        "config": model.config.to_dict(),
        "vocab": len(model.vocab),
        "vocab_digest": hashlib.sha256(
            json.dumps(model.vocab.to_dict(), sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


def run(
    checkpoint: Path,
    out: Path,
    factor: int,
    noise: float,
    seed: int,
    batch: int,
    seq: int,
    device: str,
) -> Dict[str, Any]:
    started = time.time()
    parent = TokenSNN.load(checkpoint, device="cpu")
    ids = probe_ids(len(parent.vocab), seed, batch, seq)
    child = expand_model(parent, factor=factor, noise=noise, seed=seed)
    measured = preservation(parent, child, ids)
    child.save(out)
    tolerance = TOLERANCE_NOISY if noise else TOLERANCE_EXACT
    passed = bool(measured["shapes_equal"] and measured["relative"] <= tolerance)

    return {
        "stage": "expand_token_snn",
        "factor": int(factor),
        "noise": float(noise),
        "seed": int(seed),
        "parent": {
            "path": str(checkpoint),
            "sha256": _sha256_file(checkpoint),
            **_config_summary(parent),
        },
        "child": {
            "path": str(out),
            "sha256": _sha256_file(out),
            **_config_summary(child),
        },
        "state_digest": {
            "parent": weights_digest(parent.net.state_dict()),
            "child": weights_digest(child.net.state_dict()),
        },
        "probe": {
            "seed": int(seed),
            "batch": int(batch),
            "seq": int(seq),
            "reads": "logits from net(ids), both models in eval mode on CPU",
        },
        "preservation": {
            **measured,
            "tolerance": tolerance,
            "pass": passed,
        },
        "device": device,
        "seconds": round(time.time() - started, 3),
    }


def check(report_path: Path) -> Tuple[bool, str]:
    """Recompute the instrument from the report's own files and constants."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("stage") != "expand_token_snn":
        return False, "not an expand_token_snn report"
    parent_path = Path(report["parent"]["path"])
    child_path = Path(report["child"]["path"])
    if not parent_path.is_file() or not child_path.is_file():
        return False, "parent or child checkpoint is missing"
    parent = TokenSNN.load(parent_path, device="cpu")
    child = TokenSNN.load(child_path, device="cpu")
    if parent.vocab.to_dict() != child.vocab.to_dict():
        return False, "vocab changed between parent and child"
    expected_hidden = int(parent.config.d_hidden) * int(report["factor"])
    if int(child.config.d_hidden) != expected_hidden:
        return False, (
            f"child d_hidden {child.config.d_hidden} != "
            f"parent {parent.config.d_hidden} x {report['factor']}"
        )
    probe = report["probe"]
    ids = probe_ids(len(parent.vocab), probe["seed"], probe["batch"], probe["seq"])
    measured = preservation(parent, child, ids)
    tolerance = TOLERANCE_NOISY if float(report["noise"]) else TOLERANCE_EXACT
    ok = bool(measured["shapes_equal"] and measured["relative"] <= tolerance)
    if not ok:
        return False, (
            f"preservation drifted: relative {measured['relative']:.3e} > " f"{tolerance:.1e}"
        )
    if report["child"]["sha256"] != _sha256_file(child_path):
        return False, "child sha256 changed since the report was written"
    if report["parent"]["sha256"] != _sha256_file(parent_path):
        return False, "parent sha256 changed since the report was written"
    return True, "expand_token_snn check OK"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, help="trained parent checkpoint")
    parser.add_argument("--out", type=Path, help="where to write the widened child")
    parser.add_argument(
        "--factor",
        type=int,
        default=4,
        help="width multiplier; d_hidden becomes parent_hidden x factor (>= 2)",
    )
    parser.add_argument(
        "--noise",
        type=float,
        default=0.0,
        help="relative perturbation of the new copies' input rows (0 preserves "
        "the parent exactly; training should use a small value such as 1e-3)",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--probe-batch", type=int, default=2)
    parser.add_argument("--probe-seq", type=int, default=16)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--check",
        type=Path,
        metavar="REPORT",
        help="recompute the instrument of an existing report and exit",
    )
    args = parser.parse_args()

    if args.check:
        ok, message = check(args.check)
        print(message if ok else f"FAIL: {message}")
        return 0 if ok else 1
    if args.checkpoint is None or args.out is None:
        parser.error("--checkpoint and --out are required (or use --check)")

    report = run(
        checkpoint=args.checkpoint,
        out=args.out,
        factor=args.factor,
        noise=args.noise,
        seed=args.seed,
        batch=args.probe_batch,
        seq=args.probe_seq,
        device=args.device,
    )
    text = json.dumps(report, indent=1, sort_keys=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")
    print(text)
    if not report["preservation"]["pass"]:
        print("FAIL: preservation gate did not pass", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
