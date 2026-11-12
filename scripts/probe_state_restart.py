#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L2] [βγδ] [A] [L3+]
# =============================================================================
"""Cross-process restart of the single core (contract T4, `CORE_GAP_ANALYSIS` §40.6).

T4 was measured **inside one process** (`CoreState.save` → `load` →
`attach_state`). Production restarts the process, so the real question is
whether *weights + state files* are enough on their own: a fresh interpreter,
no shared memory, no prompt text, no clock value carried across.

The probe runs itself twice:

* ``--phase capture``: build the arm, play one registered-shaped turn
  (teach → 8 × 50 s gaps → query), then save the weights, the exported state,
  the query tokens and the reference probabilities.
* ``--phase resume``: a **new process** loads the weights and the state file
  (passing ``expected_weights_hash``), attaches the state, replays only the
  query, and compares.

Pass conditions (written before the run):

1. max |p_resume − p_capture| ≤ **1e-5** (T4's bar);
2. ``weights_hash``, ``ticks``, ``last_dt_s`` and ``state_version`` survive;
3. the comparison is **not vacuous**: a fresh (zeroed) state run through the
   same query gives probabilities that differ by more than 1e-2, so (1) is
   comparing a real state, not two empty ones. This is why the capture phase
   trains the core first — an untrained GRU answers from the query tokens
   alone, and the guard would fail for a reason that has nothing to do with
   restarting;
4. refusals still work in the new process — a state from the *other* arm and
   a state whose tensor bytes were edited are both rejected. Without (4) a
   silent reset would look exactly like a successful resume in (1).

Nothing is written into the measured environment: the work directory defaults
to a fresh temporary directory and is deleted afterwards.

Usage
-----
    python3 scripts/probe_state_restart.py                # both arms, all checks
    python3 scripts/probe_state_restart.py --json         # + full report
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from ai.core.core_state import CoreState, CoreStateError  # noqa: E402

# Fixed, written before the run: the point is the state file, not a score.
REGISTERED = {
    "hidden": 64,
    "emb": 32,
    "chunk_seconds": 60.0,
    "seed": 0,
    "batch": 4,
    "gaps": (50.0,) * 8,
    "token_count": 26,
    "max_prob_delta": 1e-5,
    "min_reset_delta": 1e-2,
    # A trained core is the production shape: an untrained GRU's query output
    # is dominated by the input tokens, so a zeroed state looks the same and
    # the T4 comparison would be vacuous. Budget matches the round-2 data
    # order of magnitude (2,000 sessions, 10 epochs), not the 30-epoch score.
    "train_sessions": 2000,
    "train_epochs": 10,
}

TEACH: Tuple[int, int, int] = (1, 2, 3)
TALK: Tuple[int, ...] = (4,)
QUERY: Tuple[int, ...] = (5, 6)

WEIGHTS = "weights.pt"
STATE_DIR = "state"
REFERENCE = "reference.npz"
META = "meta.json"
RESULT = "result.json"


def _torch() -> Any:
    import torch

    return torch


def _load_cycles_module() -> Any:
    """Import ``scripts/probe_state_cycles.py`` by path (it is not a package)."""
    import importlib.util

    path = Path(__file__).with_name("probe_state_cycles.py")
    spec = importlib.util.spec_from_file_location("probe_state_cycles", path)
    if spec is None or spec.loader is None:  # pragma: no cover - import guard
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    # Register before exec: the module defines a frozen dataclass, and
    # dataclasses resolves annotations through sys.modules[cls.__module__].
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_core(arch: str) -> Any:
    from ai.core.stateful_decoder import GRUCore, SSMCore

    options = {
        "hidden": REGISTERED["hidden"],
        "emb": REGISTERED["emb"],
        "chunk_seconds": REGISTERED["chunk_seconds"],
        "seed": REGISTERED["seed"],
    }
    if arch == "gru":
        return GRUCore(REGISTERED["token_count"], **options)
    if arch == "ssm":
        return SSMCore(REGISTERED["token_count"], **options)
    raise ValueError(f"unknown arch {arch!r}")


def _tokens(ids: Sequence[int]) -> Any:
    torch = _torch()
    return torch.tensor([list(ids)] * int(REGISTERED["batch"]))


def play_turn(model: Any) -> Any:
    """One registered turn; returns ``(state_before_query, probs, ticks)``.

    The saved state is the one *before* the query — otherwise the resumed
    process would apply the query a second time and the comparison would be
    between two different states, which is how a probe can "pass" for the wrong
    reason.
    """
    torch = _torch()
    batch = int(REGISTERED["batch"])
    state = model.init_state(batch, user_id="restart", session_id="restart")
    with torch.no_grad():
        _, state = model.ai_step(_tokens(TEACH), state)
        for gap in REGISTERED["gaps"][:-1]:
            state = model.al_step(gap, state)
            _, state = model.ai_step(_tokens(TALK), state)
        state = model.al_step(REGISTERED["gaps"][-1], state)

        before_query = model.export_state(state)
        ticks_before_query = int(state.ticks)
        logits, _ = model.ai_step(_tokens(QUERY), state)
    probs = torch.softmax(logits[:, -1, :], dim=-1)
    return before_query, probs, ticks_before_query


def phase_capture(
    arch: str,
    work: Path,
    *,
    train_sessions: int | None = None,
    train_epochs: int | None = None,
) -> int:
    import numpy as np

    work.mkdir(parents=True, exist_ok=True)
    cycles = _load_cycles_module()
    budget_sessions = int(
        REGISTERED["train_sessions"] if train_sessions is None else train_sessions
    )
    budget_epochs = int(REGISTERED["train_epochs"] if train_epochs is None else train_epochs)
    sessions = cycles.generate_sessions(
        budget_sessions,
        seed=1234,
        gap_count=len(REGISTERED["gaps"]),
        gap_mode="equal",
    )
    model = cycles.train_arm(
        sessions,
        arm="core",
        arch=arch,
        seed=int(REGISTERED["seed"]),
        epochs=budget_epochs,
        batch_size=64,
        lr=5e-3,
        grad_clip=1.0,
        hidden=int(REGISTERED["hidden"]),
        emb=int(REGISTERED["emb"]),
        chunk_seconds=float(REGISTERED["chunk_seconds"]),
    )
    model.eval()
    state, probs, ticks = play_turn(model)

    model.save_weights(str(work / WEIGHTS))
    state.save(work / STATE_DIR)
    np.savez(work / REFERENCE, probs=probs.detach().to("cpu").numpy())

    meta = {
        "arch": arch,
        "weights_hash": model.weights_hash(),
        "ticks": ticks,
        "last_dt_s": float(state.last_dt_s),
        "state_version": int(state.state_version),
        "model_kind": state.model_kind,
        "query": list(QUERY),
        "batch": int(REGISTERED["batch"]),
        "process": "capture",
        "pid": int(os.getpid()),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (work / META).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"capture[{arch}]: ticks={meta['ticks']} hash={meta['weights_hash'][:19]}…")
    return 0


def phase_resume(arch: str, work: Path) -> int:
    import numpy as np

    torch = _torch()
    meta = json.loads((work / META).read_text(encoding="utf-8"))
    model = build_core(arch)
    # The weights come from the file, not from the seed: a resume that only
    # works because both processes re-derived the same random init is not a
    # resume.
    model.load_weights(str(work / WEIGHTS))
    model.eval()

    checks: Dict[str, bool] = {}
    checks["weights_hash_survives"] = model.weights_hash() == meta["weights_hash"]

    state = CoreState.load(work / STATE_DIR, expected_weights_hash=model.weights_hash())
    checks["model_kind_survives"] = state.model_kind == meta["model_kind"]
    checks["ticks_survive"] = int(state.ticks) == int(meta["ticks"])
    checks["last_dt_s_survives"] = abs(float(state.last_dt_s) - float(meta["last_dt_s"])) <= 1e-9
    checks["state_version_survives"] = int(state.state_version) == int(meta["state_version"])

    attached = model.attach_state(state)
    with torch.no_grad():
        logits, _ = model.ai_step(_tokens(meta["query"]), attached)
    probs = torch.softmax(logits[:, -1, :], dim=-1).detach().to("cpu").numpy()

    reference = np.load(work / REFERENCE)["probs"]
    delta = float(np.abs(probs - reference).max())
    checks["prob_delta_le_1e-5"] = delta <= float(REGISTERED["max_prob_delta"])

    # Sensitivity: if a zeroed state answered the same way, T4 would be
    # comparing two empty states and any resume would "pass".
    fresh = model.attach_state(model.init_state(int(REGISTERED["batch"])))
    with torch.no_grad():
        fresh_logits, _ = model.ai_step(_tokens(meta["query"]), fresh)
    fresh_probs = torch.softmax(fresh_logits[:, -1, :], dim=-1).detach().to("cpu").numpy()
    reset_delta = float(np.abs(fresh_probs - reference).max())
    checks["reset_state_is_measurably_different"] = reset_delta >= float(
        REGISTERED["min_reset_delta"]
    )

    result = {
        "arch": arch,
        "checks": checks,
        "max_prob_delta": delta,
        "reset_prob_delta": reset_delta,
        "ticks": int(state.ticks),
        "weights_hash": model.weights_hash(),
        "process": "resume",
        "pid": int(os.getpid()),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (work / RESULT).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"resume[{arch}]: max|Δp|={delta:.3e} ticks={result['ticks']}")
    return 0


def _negative_checks(arch: str, other: str, work: Path) -> Dict[str, bool]:
    """Cross-arm and tampered state must be refused, not silently reset."""
    checks: Dict[str, bool] = {}

    other_model = build_core(other).eval()
    try:
        CoreState.load(work / STATE_DIR, expected_weights_hash=other_model.weights_hash())
    except CoreStateError:
        checks["refuses_state_from_the_other_arm"] = True
    else:
        checks["refuses_state_from_the_other_arm"] = False

    same = build_core(arch)
    same.load_weights(str(work / WEIGHTS))
    loaded = CoreState.load(work / STATE_DIR, expected_weights_hash=same.weights_hash())
    try:
        other_model.attach_state(loaded)
    except CoreStateError:
        checks["attach_refuses_the_wrong_arm"] = True
    else:
        checks["attach_refuses_the_wrong_arm"] = False

    tampered = Path(tempfile.mkdtemp(dir=str(work)))
    shutil.copytree(work / STATE_DIR, tampered / STATE_DIR)
    tensors = sorted((tampered / STATE_DIR).glob("*.npz"))
    try:
        payload = bytearray(tensors[0].read_bytes())
        payload[len(payload) // 2] ^= 0xFF
        tensors[0].write_bytes(bytes(payload))
        CoreState.load(tampered / STATE_DIR)
    except CoreStateError:
        checks["refuses_tampered_state"] = True
    except Exception:  # pragma: no cover - a wrong exception type is a failure
        checks["refuses_tampered_state"] = False
    else:
        checks["refuses_tampered_state"] = False
    shutil.rmtree(tampered, ignore_errors=True)

    return checks


def run(
    work_root: Path,
    arms: Sequence[str],
    *,
    train_sessions: int | None = None,
    train_epochs: int | None = None,
) -> Dict[str, Any]:
    script = str(Path(__file__).resolve())
    work_root.mkdir(parents=True, exist_ok=True)
    dirs = {arch: work_root / arch for arch in arms}
    budget = [
        "--train-sessions",
        str(int(REGISTERED["train_sessions"] if train_sessions is None else train_sessions)),
        "--train-epochs",
        str(int(REGISTERED["train_epochs"] if train_epochs is None else train_epochs)),
    ]

    for arch in arms:
        subprocess.run(
            [
                sys.executable,
                script,
                "--phase",
                "capture",
                "--arch",
                arch,
                "--work",
                str(dirs[arch]),
                *budget,
            ],
            check=True,
        )

    results: Dict[str, Any] = {}
    for arch in arms:
        subprocess.run(
            [
                sys.executable,
                script,
                "--phase",
                "resume",
                "--arch",
                arch,
                "--work",
                str(dirs[arch]),
            ],
            check=True,
        )
        results[arch] = json.loads((dirs[arch] / RESULT).read_text(encoding="utf-8"))

    other = {"gru": "ssm", "ssm": "gru"}
    for arch in arms:
        results[arch]["checks"].update(_negative_checks(arch, other[arch], dirs[arch]))
        results[arch]["all_pass"] = all(results[arch]["checks"].values())

    return {
        "kind": "restart",
        "registered": False,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "config": {
            **REGISTERED,
            "train_sessions": int(
                REGISTERED["train_sessions"] if train_sessions is None else train_sessions
            ),
            "train_epochs": int(
                REGISTERED["train_epochs"] if train_epochs is None else train_epochs
            ),
        },
        "arms": results,
        "all_pass": all(entry["all_pass"] for entry in results.values()),
        "caveats": [
            "same machine, CPU, same torch build; this tests process boundary + files, "
            "not a reboot or a different machine",
            "the probe plays one turn; a longer session is the production shape (P4)",
        ],
    }


def print_report(report: Dict[str, Any]) -> None:
    print("\n== 跨進程 restart（新解釋器，只靠 weights + state 檔）==")
    for arch, entry in report["arms"].items():
        print(
            f"  {arch}: max|Δp|={entry['max_prob_delta']:.3e} "
            f"(zeroed state would differ by {entry['reset_prob_delta']:.3e}) "
            f"ticks={entry['ticks']}"
        )
        for name, passed in entry["checks"].items():
            print(f"    {'PASS' if passed else 'FAIL'}  {name}")
    print(f"\n  all_pass = {report['all_pass']}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("capture", "resume"), default=None)
    parser.add_argument("--arch", choices=("gru", "ssm"), default="gru")
    parser.add_argument("--work", type=Path, default=None)
    parser.add_argument("--arms", nargs="+", default=["gru", "ssm"], choices=("gru", "ssm"))
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--train-sessions",
        type=int,
        default=None,
        help="capture budget; a smoke value is not the registered search",
    )
    parser.add_argument("--train-epochs", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.phase is not None:
        if args.work is None:
            parser.error("--phase requires --work")
        if args.phase == "capture":
            return phase_capture(
                args.arch,
                args.work,
                train_sessions=args.train_sessions,
                train_epochs=args.train_epochs,
            )
        return phase_resume(args.arch, args.work)

    work_root = args.work or Path(tempfile.mkdtemp(prefix="core-restart-"))
    try:
        report = run(
            work_root,
            args.arms,
            train_sessions=args.train_sessions,
            train_epochs=args.train_epochs,
        )
    finally:
        if args.work is None:
            shutil.rmtree(work_root, ignore_errors=True)

    print_report(report)
    out = args.out or (REPO_ROOT / "data" / "intelligence_reports" / "probe_state_restart.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nreport: {out}")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
