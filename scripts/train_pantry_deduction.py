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

Stage G (§56) is the question §55.6's branch names: the same 400 reviews/session,
but 200 distinct training sessions instead of 32, graded on the 200 held-out
sessions. ``--train-sessions N`` declares the subset, ``--gate-prefix G`` grades
it by G1-G4, and ``--stage-g`` computes the paired verdict::

    ./.venv/bin/python scripts/train_pantry_deduction.py --train-sessions 200 \\
        --epochs 400 --core turnstore --aux-loss 1.0 --aux-mode resolvable \\
        --gate-prefix G --device cpu --out data/pantry_stage/g_store
    ./.venv/bin/python scripts/train_pantry_deduction.py --train-sessions 200 \\
        --epochs 400 --aux-loss 1.0 --aux-mode resolvable \\
        --gate-prefix G --device cpu --out data/pantry_stage/g_gru
    ./.venv/bin/python scripts/train_pantry_deduction.py --stage-g <store>.json <gru>.json
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

# §55's per-turn store and §59's per-token cache are both derived from L and both
# take the ``--no-memory`` ablation; keeping one tuple means a new arm cannot be
# half-wired (accepted by the CLI but refused by the derivation, or vice versa).
STORE_ARMS = ("turnstore", "tokencache")
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

# §55 - stage T compares an architecture arm against the same budget. The GRU
# control is the registered n32_4x report (12/32 at 1,600 steps = 400
# updates/session); putting the number here means the ablation is graded against
# the run that exists, not against a recollection of it.
STORE_FLOOR = 0.90
ABLATION_CEILING = 0.65
ABLATION_GAP = 0.25
ABLATION_TOLERANCE = 0.15
GRU_CONTROL_EXACT = 0.375

# §56 - stage G is the question §55.6's branch names: with the same 400
# reviews/session, does an arm trained on *many* sessions answer answer tuples
# the corpus never gave it? The fit floor is the one the store already had to
# clear (0.90); the chance line is the report's own per-session chance (a roster
# of 5-8 names, not 1/12), and the store-vs-GRU line is a paired test on the
# same held-out sessions, so neither number is chosen here.
GENERAL_FIT_FLOOR = STORE_FLOOR
GENERAL_ALPHA = 0.05

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
def build_core(
    *,
    hidden: int = HIDDEN,
    emb: int = EMB,
    device: str,
    seed: int = SEED,
    kind: str = "gru",
    memory: bool = True,
) -> Any:
    """The registered carriers: ``gru`` (L/P…), ``turnstore`` (§55), ``tokencache`` (§59)."""
    if kind == "tokencache":
        from ai.core.stateful_decoder import TokenCacheCore

        return TokenCacheCore(
            VOCAB_SIZE,
            hidden=hidden,
            emb=emb,
            chunk_seconds=CHUNK_SECONDS,
            seed=seed,
            device=device,
            memory=memory,
        )
    if kind == "turnstore":
        from ai.core.stateful_decoder import TurnStoreCore

        return TurnStoreCore(
            VOCAB_SIZE,
            hidden=hidden,
            emb=emb,
            chunk_seconds=CHUNK_SECONDS,
            seed=seed,
            device=device,
            memory=memory,
        )
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


def widen_from_stage_l(core: Any, path: Path, *, source_hidden: int) -> str:
    """Zero-extend L's weights into ``core``'s width, keeping L's function at 0 steps.

    §52.4's width rung cannot load L into a wider model - ``strict_config``
    refuses different shapes, and a fresh wide init would silently change the
    carrier. This copies L's block and zero-connects the new units:

    * embedding / ``dt_proj`` / biases: copied (their shapes do not depend on H);
    * ``cell.weight_ih``: L's rows copied per gate, new rows keep the seed's init;
    * ``cell.weight_hh``: old rows x old columns = L, old rows x new columns = 0,
      so the old units' dynamics are exactly L's (they never see the new units);
    * ``head.weight``: L's columns copied, new columns zero (so the logits are
      L's until training writes to the new block).

    The widened model is therefore *behaviourally* L at step 0 while carrying
    extra capacity, which is what makes the width rung a width rung rather than
    a different experiment. Returns the widened weights hash.
    """
    torch = core._torch
    file_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if file_digest != L_CHECKPOINT_SHA256:
        raise SystemExit(
            f"stage-L checkpoint file sha256 {file_digest[:12]}… != registered "
            f"{L_CHECKPOINT_SHA256[:12]}…; the widened start is not derived from §49.1's file"
        )
    payload = torch.load(str(path), map_location="cpu", weights_only=True)
    config = payload.get("config") or {}
    if int(config.get("hidden") or 0) != source_hidden:
        raise SystemExit(
            f"source checkpoint hidden={config.get('hidden')!r} != expected {source_hidden}"
        )
    if int(config.get("emb") or 0) != core.emb:
        raise SystemExit(
            f"widening keeps emb fixed: source {config.get('emb')!r} != model {core.emb}"
        )
    if core.hidden <= source_hidden:
        raise SystemExit(f"--widen-to {core.hidden} is not wider than L's {source_hidden}")

    old, new = source_hidden, core.hidden
    source = payload["state_dict"]
    live = {
        "embedding": core.embedding.state_dict(),
        "cell": core.cell.state_dict(),
        "dt_proj": core.dt_proj.state_dict(),
        "head": core.head.state_dict(),
    }
    with torch.no_grad():
        live["embedding"]["weight"].copy_(source["embedding"]["weight"])
        live["dt_proj"]["weight"].copy_(source["dt_proj"]["weight"])
        live["dt_proj"]["bias"].copy_(source["dt_proj"]["bias"])
        for gate in range(3):  # GRUCell order: reset, update, candidate
            dst, src = gate * new, gate * old
            for name in ("weight_ih", "bias_ih", "bias_hh"):
                live["cell"][name][dst : dst + old].copy_(source["cell"][name][src : src + old])
            hidden_weights = live["cell"]["weight_hh"]
            hidden_weights[dst : dst + old, :old].copy_(
                source["cell"]["weight_hh"][src : src + old, :old]
            )
            hidden_weights[dst : dst + old, old:].zero_()
        live["head"]["weight"][:, :old].copy_(source["head"]["weight"])
        live["head"]["weight"][:, old:].zero_()
        live["head"]["bias"].copy_(source["head"]["bias"])
    core.invalidate_hash()
    return core.weights_hash()


def start_from_stage_l(core: Any, path: Path, *, source_hidden: int) -> str:
    """Copy L's blocks into a store arm so the start point is still L (§55.3).

    ``load_weights(strict_config=True)`` refuses a ``gru`` checkpoint in a
    ``turnstore`` model (the model kind differs), and a fresh init would silently
    change the start. This copies everything the two arms share and leaves the
    new projections at their seed init:

    * embedding / dt_proj / cell are copied wholesale (their shapes are L's);
    * ``head.weight[:, :H]`` and ``head.bias`` are copied, the new ``D`` columns
      are zero - so ``head([h, 0])`` is L's ``head(h)`` and the first token's
      logits are L's until the first read.

    The file must be the registered artifact (sha256), not merely a checkpoint
    with matching shapes: §49.1 pins the start, and a derivation of something
    else is a different experiment.
    """
    if getattr(core, "model_kind", "") not in STORE_ARMS:
        raise SystemExit(
            f"start_from_stage_l is for the store arms {sorted(STORE_ARMS)}, "
            f"not {core.model_kind!r}"
        )
    if not path.exists():
        raise SystemExit(f"missing the stage-L checkpoint: {path}")
    file_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if file_digest != L_CHECKPOINT_SHA256:
        raise SystemExit(
            f"stage-L checkpoint file sha256 {file_digest[:12]}… != registered "
            f"{L_CHECKPOINT_SHA256[:12]}…; the start point is not the artifact §49.1 names"
        )
    import torch

    payload = torch.load(str(path), map_location="cpu", weights_only=True)
    config = payload.get("config") or {}
    if config.get("model_kind") != "gru":
        raise SystemExit(f"{path} is not the GRU carrier (model_kind={config.get('model_kind')!r})")
    if int(config.get("hidden", -1)) != source_hidden:
        raise SystemExit(
            f"stage-L hidden {config.get('hidden')!r} != the registered {source_hidden}"
        )
    if int(config.get("emb", -1)) != core.emb:
        raise SystemExit(f"stage-L emb {config.get('emb')!r} != this model's {core.emb}")
    if int(config.get("token_count", -1)) != core.token_count:
        raise SystemExit(f"stage-L token_count {config.get('token_count')!r} != {core.token_count}")

    source = payload["state_dict"]
    with torch.no_grad():
        core.embedding.weight.copy_(source["embedding"]["weight"])
        for name in ("weight_ih", "weight_hh", "bias_ih", "bias_hh"):
            getattr(core.cell, name).copy_(source["cell"][name])
        core.dt_proj.weight.copy_(source["dt_proj"]["weight"])
        core.dt_proj.bias.copy_(source["dt_proj"]["bias"])
        core.head.weight[:, :source_hidden].copy_(source["head"]["weight"])
        core.head.weight[:, source_hidden:].zero_()
        core.head.bias.copy_(source["head"]["bias"])
    core.invalidate_hash()
    return core.weights_hash()


def start_is_stage_l(start: Dict[str, Any]) -> bool:
    """True when the recorded start is L, or a behaviour-preserving derivation of L."""
    if start.get("checkpoint_sha256") != L_CHECKPOINT_SHA256 or not start.get("checkpoint"):
        return False
    widened = start.get("widened_from_hidden")
    if widened is not None:
        return (
            int(widened) == HIDDEN
            and start.get("source_weights_hash") == L_WEIGHTS_HASH
            and int(start.get("hidden") or 0) > HIDDEN
            and int(start.get("params") or 0) > L_PARAMS
        )
    if start.get("derived_from") in STORE_ARMS:
        return (
            start.get("source_weights_hash") == L_WEIGHTS_HASH
            and int(start.get("hidden") or 0) == HIDDEN
            and int(start.get("params") or 0) > L_PARAMS
        )
    return start.get("weights_hash") == L_WEIGHTS_HASH and start.get("params") == L_PARAMS


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


def _run_turn(core: Any, rows: Sequence[Sequence[int]], hidden: Any) -> Tuple[Any, Any, Any]:
    """Feed one turn per sample; return ``(state at real length, all states, valid)``.

    Right-padding is only used to batch the arithmetic: the gathered state is the
    one computed from that sample's real tokens, so the pad never enters the
    state (``tests/test_pantry_deduction.py`` checks this against ``ai_step``).

    ``stacked`` is every position's state ``[B, width, H]`` and ``valid`` is the
    real-length mask ``[B, width]``: §59's token cache needs both (a token entry
    per position, and padding excluded from the read) and it must be written from
    the same computation, not from a second pass.
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
    final = stacked.gather(1, picks.expand(-1, 1, stacked.shape[-1])).reshape(len(rows), -1)
    positions = torch.arange(width, device=hidden.device).unsqueeze(0)
    valid = positions < torch.as_tensor(lengths, device=hidden.device).unsqueeze(1)
    return final, stacked, valid


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

    ``boundaries`` is the §50.2 hook: when a list is passed, each turn's state is
    appended to it (the graph is kept, so training can read out from every turn).
    When it is ``None`` nothing changes - stage P's run is bitwise the same
    computation. A boundary is the ``h`` tensor for one-tensor cores (so existing
    probes keep their type) and the whole tensor mapping for a core with a store,
    because its answer depends on more than ``h``.

    The §55 turn-end write happens here, after the turn's tokens and before the
    snapshot: a boundary is the state *after* turn k, including what turn k wrote.
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
                # the reset arm asks what the last turn says on its own; a store
                # left over from earlier turns would answer for them
                state.tensors = {
                    name: torch.zeros_like(value) for name, value in state.tensors.items()
                }
                hidden = state.tensors["h"]
            else:
                state.tensors["h"] = hidden
                dt = torch.as_tensor(
                    [row[index] for row in batch_gaps], dtype=hidden.dtype, device=hidden.device
                )
                state = core.al_step(dt, state)
                hidden = state.tensors["h"]
        hidden, stacked, valid = _run_turn(core, [row[index] for row in batch_turns], hidden)
        # one ai_step per turn, so state_version/ticks mean what they mean in
        # the contract (al_step bumps for chunks; this bumps for the turn)
        state.tensors["h"] = hidden
        # §59: a token-level arm writes its cache from the same stacked states
        # the turn was computed from, with padding marked invalid. The write is
        # functional, so an earlier boundary's cache is never rewritten.
        state.tensors = core.cache_write(state.tensors, stacked, valid)
        state.bump()
        state.tensors = core.end_turn(state.tensors)
        hidden = state.tensors["h"]
        if boundaries is not None:
            snapshot = dict(state.tensors)
            boundaries.append(snapshot["h"] if len(snapshot) == 1 else snapshot)
    return state, hidden


def _decode_view(record: Any) -> Dict[str, Any]:
    """Normalise a boundary/hidden into a tensor mapping (h only, or h + store)."""
    if isinstance(record, dict):
        return dict(record)
    return {"h": record}


def _select(record: Any, index: Any) -> Dict[str, Any]:
    """Pick rows from a boundary - a store boundary has to move with its ``h``."""
    return {name: value.index_select(0, index) for name, value in _decode_view(record).items()}


def _slice(record: Any, start: int, stop: int) -> Dict[str, Any]:
    return {name: value[start:stop] for name, value in _decode_view(record).items()}


def _answer_loss(core: Any, record: Any, answers: Sequence[Sequence[int]]) -> Any:
    import torch.nn.functional as functional

    torch = core._torch
    longest = max(len(answer) for answer in answers)
    view = _decode_view(record)
    logits = []
    for position in range(longest):
        logits.append(core.token_logits(view))
        tokens = [answer[position] if position < len(answer) else PAD_ID for answer in answers]
        if position < longest - 1:
            feed = torch.as_tensor(tokens, dtype=torch.long, device=view["h"].device)
            view = core.consume(feed, view)
    stacked = torch.stack(logits, dim=1)
    targets = torch.full((len(answers), longest), -100, dtype=torch.long, device=stacked.device)
    for index, answer in enumerate(answers):
        targets[index, : len(answer)] = torch.as_tensor(
            answer, dtype=torch.long, device=stacked.device
        )
    return functional.cross_entropy(
        stacked.reshape(-1, VOCAB_SIZE), targets.reshape(-1), ignore_index=-100
    )


def candidates_tokens(name: str) -> List[int]:
    """A candidate name as the exact bytes the answer loss would score."""
    return [BYTE_OFFSET + byte for byte in (name + "\n").encode("utf-8")]


def _candidate_region_loss(
    core: Any,
    boundary: Any,
    names: Sequence[Sequence[str]],
    answers: Sequence[Sequence[int]],
) -> Any:
    """§60: per-sample CE over only the names consistent with this prefix.

    ``names[s]`` is sample ``s``'s candidate set and ``answers[s]`` the culprit's
    token ids (which the corpus's ``derive()`` guarantees is a member). Scoring
    uses the same teacher-forced decode the answer loss uses, so the model sees
    exactly the bytes it would have to emit; the softmax is taken over the
    candidates instead of the whole byte vocabulary.

    Returns one cross-entropy per sample (reduction ``none``), because the caller
    weights each (sample, boundary) pair by ``1/|candidates|``.
    """
    import torch.nn.functional as functional

    torch = core._torch
    view = _decode_view(boundary)
    device = view["h"].device

    pairs: List[Tuple[int, List[int]]] = []
    for index, sample_names in enumerate(names):
        for name in sample_names:
            pairs.append((index, candidates_tokens(name)))
    if not pairs:
        return torch.zeros(0, device=device)

    picked = {
        key: value.index_select(
            0, torch.as_tensor([sample for sample, _ in pairs], dtype=torch.long, device=device)
        )
        for key, value in view.items()
    }
    longest = max(len(tokens) for _, tokens in pairs)
    totals = torch.zeros(len(pairs), dtype=view["h"].dtype, device=device)
    cursor = picked
    for position in range(longest):
        logits = core.token_logits(cursor)
        log_probs = functional.log_softmax(logits, dim=-1)
        targets = []
        masks = []
        for _, tokens in pairs:
            targets.append(tokens[position] if position < len(tokens) else 0)
            masks.append(1.0 if position < len(tokens) else 0.0)
        target_tensor = torch.as_tensor(targets, dtype=torch.long, device=device)
        mask = torch.as_tensor(masks, dtype=view["h"].dtype, device=device)
        totals = totals + log_probs.gather(1, target_tensor.unsqueeze(1)).squeeze(1) * mask
        cursor = core.consume(target_tensor, cursor)

    # regroup the flattened log-probabilities into one row per sample, in the
    # same candidate order, and drop the rows that are not real candidates
    scores = torch.full(
        (len(names), max(len(sample_names) for sample_names in names)),
        float("-inf"),
        dtype=view["h"].dtype,
        device=device,
    )
    slot = 0
    targets = []
    for index, sample_names in enumerate(names):
        answer = list(answers[index])
        chosen = None
        for position, name in enumerate(sample_names):
            scores[index, position] = totals[slot]
            if candidates_tokens(name) == answer:
                chosen = position
            slot += 1
        if chosen is None:
            raise SystemExit(
                "the culprit is not in the candidate set; the corpus's derive() and the "
                "answer disagree, so the region loss would be scored against a wrong target"
            )
        targets.append(chosen)
    return functional.cross_entropy(
        scores,
        torch.as_tensor(targets, dtype=torch.long, device=device),
        reduction="none",
    )


def region_stats(samples: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """W4's cost record: how many boundaries are scored and how wide they are."""
    scored = 0
    skipped = 0
    pairs = 0
    widths: List[int] = []
    for row in samples:
        for candidates in row.get("candidate_sets") or []:
            if candidates is None:
                skipped += 1
                continue
            scored += 1
            pairs += len(candidates)
            widths.append(len(candidates))
    return {
        "boundaries_scored": scored,
        "boundaries_skipped": skipped,
        "candidate_pairs_per_epoch": pairs,
        "mean_width": _round(sum(widths) / len(widths)) if widths else None,
        "max_width": max(widths) if widths else None,
    }


def _training_loss(
    core: Any,
    boundaries: Sequence[Any],
    answers: Sequence[Sequence[int]],
    aux_lambda: float,
    prefix_answers: Optional[Sequence[Sequence[Optional[Sequence[int]]]]] = None,
    candidate_sets: Optional[Sequence[Sequence[Optional[Sequence[str]]]]] = None,
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
    if candidate_sets is not None:
        auxiliary = _weighted_region_auxiliary(core, earlier, answers, candidate_sets)
        if auxiliary is None:
            return main, main, None
        return main + aux_lambda * auxiliary, main, auxiliary
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
        index_tensor = _decode_view(hidden)["h"].new_tensor(keep).long()
        terms.append(_answer_loss(core, _select(hidden, index_tensor), picked))
    if not terms:
        return main, main, None
    auxiliary = sum(terms) / len(terms)
    return main + aux_lambda * auxiliary, main, auxiliary


def _weighted_region_auxiliary(
    core: Any,
    earlier: Sequence[Any],
    answers: Sequence[Sequence[int]],
    candidate_sets: Sequence[Sequence[Optional[Sequence[str]]]],
) -> Optional[Any]:
    """§60.2: ``Σ w·CE / Σ w`` over boundaries restricted to their roster.

    ``w = 1/|C|`` because a narrower roster is a more determinate question: a
    boundary with two names left says almost as much as the final readout, while
    one with eight says little. Weighting by the count instead would let the
    earliest, least-informative boundaries dominate.

    Boundaries with ``|C| < 2`` are skipped: there is only one name on the
    table, so the cross-entropy is zero no matter what the model does and its
    gradient is exactly zero - scoring it would only add a constant to the
    denominator and dilute the boundaries that carry information.
    """
    torch = core._torch
    numerator: Optional[Any] = None
    denominator = 0.0
    for index, boundary in enumerate(earlier):
        rows = [candidate_sets[sample][index] for sample in range(len(answers))]
        # a single candidate has no choice to make: CE is exactly 0 and so is
        # its gradient, so it must not enter the denominator either
        keep = [position for position, names in enumerate(rows) if names and len(names) >= 2]
        if not keep:
            continue
        picked = [list(rows[position]) for position in keep]
        index_tensor = _decode_view(boundary)["h"].new_tensor(keep).long()
        targets = [answers[position] for position in keep]
        losses = _candidate_region_loss(core, _select(boundary, index_tensor), picked, targets)
        weights = torch.as_tensor(
            [1.0 / len(names) for names in picked], dtype=losses.dtype, device=losses.device
        )
        term = (losses * weights).sum()
        numerator = term if numerator is None else numerator + term
        denominator += float(sum(1.0 / len(names) for names in picked))
    if numerator is None or denominator <= 0.0:
        return None
    return numerator / denominator


def generate_bytes(core: Any, record: Any, limit: int = MAX_ANSWER_BYTES) -> List[bytes]:
    """Greedy decode: stop at a newline, a special token, or ``limit`` bytes.

    ``record`` is a boundary (``h`` tensor) or a tensor mapping; a core with a
    store reads it at every step, so the answer can depend on all of it.
    """
    view = _decode_view(record)
    batch = int(view["h"].shape[0])
    produced: List[List[int]] = [[] for _ in range(batch)]
    finished = [False] * batch
    for _ in range(limit):
        tokens = core.token_logits(view).argmax(dim=-1)
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
        view = core.consume(tokens, view)
    return [bytes(item) for item in produced]


def rank_actor(core: Any, record: Any, candidates: Sequence[str]) -> str:
    """Sequence log-likelihood of each name (plus terminator); argmax wins."""
    import torch.nn.functional as functional

    torch = core._torch
    best_name = ""
    best_score = -math.inf
    for name in candidates:
        ids = [BYTE_OFFSET + byte for byte in (name + "\n").encode("utf-8")]
        view = _decode_view(record)
        total = 0.0
        for token in ids:
            logits = core.token_logits(view)
            total += float(functional.log_softmax(logits, dim=-1)[0, token])
            feed = torch.as_tensor([token], dtype=torch.long, device=view["h"].device)
            view = core.consume(feed, view)
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


def cache_report(sessions: Sequence[Dict[str, Any]], *, slots: int) -> Dict[str, Any]:
    """§59.4's B4: what the token cache holds and what it had to drop.

    The cache keeps the **first** ``slots`` tokens of a session (§59.2), so a
    session longer than that silently loses its tail. That is a design choice,
    not a measurement, and it is only honest if the report says how much was
    lost: the roster is turn 2-3, so the expectation is "almost nothing", and a
    run where it is not almost nothing is not testing the registering question.
    """
    lengths = [sum(len(turn) for turn in turn_tokens(session)) for session in sessions]
    total = sum(lengths)
    dropped = sum(max(0, length - slots) for length in lengths)
    return {
        "slots": int(slots),
        "sessions": len(lengths),
        "mean_tokens": _round(total / len(lengths)) if lengths else None,
        "max_tokens": max(lengths) if lengths else None,
        "sessions_truncated": sum(1 for length in lengths if length > slots),
        "tokens_total": total,
        "tokens_dropped": dropped,
        "tokens_dropped_share": _round(dropped / total) if total else None,
    }


def build_samples(
    sessions: Sequence[Dict[str, Any]],
    *,
    seed: int,
    control: Optional[str],
    prefix_module: Any = None,
    region_module: Any = None,
) -> List[Dict[str, Any]]:
    """Turn sessions into training rows.

    ``prefix_module`` (stage R, §51.2) additionally records, for every earlier
    turn boundary, that boundary's own ``derive()`` answer - ``None`` where the
    prefix does not yet determine one. It costs nothing at λ=0 and is ignored
    there, so stage P/Q reports stay reproducible from this function.

    ``region_module`` (§60) records the *whole* candidate set at each boundary
    instead of only the unique answer, because the weighted region loss scores
    the correct name against the others still consistent with that prefix.
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
        if region_module is not None:
            # §60: what the earlier boundaries are allowed to answer. The answer
            # is still decided by the testimony; this only says which names are
            # on the table at that boundary (it is the roster, which the input
            # states). `None` entries are boundaries with fewer than two
            # candidates - there is nothing to discriminate, so they are skipped.
            row["candidate_sets"] = []
            for upto in range(len(session["turns"]) - 1):
                candidates = prefix_candidates(region_module, session, upto)
                row["candidate_sets"].append(list(candidates) if len(candidates) >= 2 else None)
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
                boundaries if boundaries is not None else [dict(state.tensors)],
                [row["answer"] for row in rows],
                aux_lambda,
                (
                    [row["prefix_answers"] for row in rows]
                    if aux_mode == "resolvable" and boundaries is not None
                    else None
                ),
                (
                    [row["candidate_sets"] for row in rows]
                    if aux_mode == "weighted-region" and boundaries is not None
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
            final = dict(state.tensors)
            produced = generate_bytes(core, final)
            for index, session in enumerate(chunk):
                actors = list(session["environment"]["actors"])
                ranked = rank_actor(core, _slice(final, index, index + 1), actors)
                prediction = _decoded(produced[index])
                records.append(
                    {
                        "session_id": session["session_id"],
                        "chain": session["session_meta"]["chain"],
                        "actors": len(actors),
                        # §56/§57/§59's diagnostic: does the answer even come
                        # from this session's roster, or is it a globally
                        # frequent name? `summarise` turns this into a rate and
                        # compares it with the content-free expectation.
                        "roster": actors,
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
    roster_of = {row["session_id"]: row.get("roster") or [] for row in records}
    names = {name for roster in roster_of.values() for name in roster}
    in_roster = sum(1 for row in targeted if row["prediction"] in roster_of[row["session_id"]])
    # "content-free": answering from the corpus-wide name distribution without
    # reading the session, i.e. P(name in this roster) under a uniform choice
    # over the names the corpus uses
    roster_chance = (
        sum(len(roster_of[row["session_id"]]) / len(names) for row in targeted) / total
        if total and names
        else 0.0
    )
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
        "in_roster": in_roster,
        "in_roster_exact": _round(in_roster / total) if total else None,
        "in_roster_chance": _round(roster_chance),
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


def _gate_prefix_of(report: Dict[str, Any]) -> str:
    """The letter a report is graded under; stages default to Q or R."""
    prefix = (report.get("config") or {}).get("gate_prefix")
    if prefix is None:
        prefix = "R" if (report.get("config") or {}).get("aux_mode") == "resolvable" else "Q"
    prefix = str(prefix)
    if len(prefix) != 1 or not prefix.isalpha() or prefix != prefix.upper():
        raise SystemExit(f"gate_prefix must be a single A-Z letter, got {prefix!r}")
    return prefix


def _stage_t_gate_values(report: Dict[str, Any]) -> Dict[str, Any]:
    """§55.4's T1-T4 for *one* arm; T2 needs the pair and is ``None`` here.

    T1 is the store arm's own calibration at the registered budget, T3 is the
    ablation's distance from the GRU control, T4 is cost. T2 (store minus
    ablation) cannot be computed from one report, so it stays ``None`` and
    ``--stage-t`` computes it from the pair; ``verdict`` ignores ``None``, so no
    single report can claim the pair's result. A GRU report under ``--gate-prefix
    T`` is not a T arm: only T4 applies.
    """
    config = report.get("config") or {}
    fit = (report.get("results") or {}).get("train_fit") or {}
    cost = report.get("cost") or {}
    overfit = bool(report.get("overfit"))
    memory = config.get("memory")
    exact = fit.get("exact")
    store_arm = overfit and memory is True
    ablation = overfit and memory is False

    return {
        "T1_store_fits_at_budget": (
            (exact is not None and exact >= STORE_FLOOR) if store_arm else None
        ),
        "T2_store_minus_ablation": None,
        "T3_ablation_matches_gru": (
            (abs(float(exact) - GRU_CONTROL_EXACT) <= ABLATION_TOLERANCE)
            if (ablation and exact is not None)
            else None
        ),
        "T4_cost_recorded": all(
            cost.get(key) not in (None, 0) for key in ("params", "train_seconds", "device")
        ),
    }


def stage_t_comparison(store: Dict[str, Any], ablation: Dict[str, Any]) -> Dict[str, Any]:
    """§55.4's pair verdict, computed from the two reports (never from a memory).

    Refuses to compare arms that are not the registered pair: same corpus
    digests, same seed/lr/batch/epochs, same L derivation, one store arm and one
    ablation. Without those checks the "gap" could be a difference in the test.
    """
    problems: List[str] = []
    for label, report in (("store", store), ("ablation", ablation)):
        if _gate_prefix_of(report) != "T":
            problems.append(f"the {label} report is not graded under T")
        if not report.get("overfit"):
            problems.append(f"the {label} report is not the overfit calibration")
    configs = [(store.get("config") or {}), (ablation.get("config") or {})]
    if configs[0].get("memory") is not True:
        problems.append("the first report is not the store arm (memory != True)")
    if configs[1].get("memory") is not False:
        problems.append("the second report is not the ablation (memory != False)")
    for key in ("seed", "lr", "batch", "epochs", "token_count", "hidden", "emb"):
        if configs[0].get(key) != configs[1].get(key):
            problems.append(f"the two arms differ in {key}")
    if (store.get("corpus") or {}).get("train_digest") != (ablation.get("corpus") or {}).get(
        "train_digest"
    ):
        problems.append("the two arms used different training corpora")
    if (store.get("start") or {}).get("source_weights_hash") != (ablation.get("start") or {}).get(
        "source_weights_hash"
    ):
        problems.append("the two arms started from different derivations of L")
    if problems:
        raise SystemExit("; ".join(problems))

    store_exact = ((store.get("results") or {}).get("train_fit") or {}).get("exact")
    ablation_exact = ((ablation.get("results") or {}).get("train_fit") or {}).get("exact")
    if store_exact is None or ablation_exact is None:
        raise SystemExit("a train_fit exact rate is missing; the pair cannot be graded")

    checks = {
        "T1_store_fits_at_budget": float(store_exact) >= STORE_FLOOR,
        "T2_store_minus_ablation": (
            float(ablation_exact) <= ABLATION_CEILING
            and (float(store_exact) - float(ablation_exact)) >= ABLATION_GAP
        ),
        "T3_ablation_matches_gru": (
            abs(float(ablation_exact) - GRU_CONTROL_EXACT) <= ABLATION_TOLERANCE
        ),
        "T4_cost_recorded": all(
            (report.get("cost") or {}).get(key) not in (None, 0)
            for report in (store, ablation)
            for key in ("params", "train_seconds", "device")
        ),
    }
    return {
        "store_exact": store_exact,
        "ablation_exact": ablation_exact,
        "gap": round(float(store_exact) - float(ablation_exact), 4),
        "gru_control_exact": GRU_CONTROL_EXACT,
        "checks": checks,
        "all_pass": all(checks.values()),
        "branch": stage_t_branch(checks),
    }


def stage_t_branch(checks: Dict[str, bool]) -> str:
    """§55.6, mechanically: what the next experiment is allowed to be."""
    if not checks["T3_ablation_matches_gru"]:
        return (
            "T3 fails: the ablation is not the same function as the GRU control, "
            "so T1/T2 are not read; fix the wiring first"
        )
    if checks["T1_store_fits_at_budget"] and checks["T2_store_minus_ablation"]:
        return (
            "T1+T2 pass: the store shortens the credit path; next is held-out "
            "generalisation at the same budget, not a score"
        )
    if checks["T1_store_fits_at_budget"] and not checks["T2_store_minus_ablation"]:
        return (
            "T1 passes but T2 does not: the fit is not attributable to the store; "
            "next is the parameter-matched GRU control, no architecture claim"
        )
    if not checks["T1_store_fits_at_budget"] and checks["T2_store_minus_ablation"]:
        return (
            "T1 fails but T2 passes: the store helps but not enough; next is "
            "per-turn regional losses, not more epochs or width"
        )
    return (
        "T1 and T2 fail: this wiring does not shorten the path; next is "
        "truncated BPTT or whole-turn attention, never more epochs or width"
    )


def _stage_g_gate_values(report: Dict[str, Any]) -> Dict[str, Any]:
    """§56.4's G1-G4 for *one* arm; G3 needs the pair and is ``None`` here.

    G1 is "the arm fitted the sessions it was trained on" - without it the
    held-out number is capped by underfitting and is not read. G2 is "held-out
    beats the report's own per-session chance" (a roster of 5-8 names), with the
    Wilson lower bound doing the reading, not the point estimate. G3 compares the
    two arms on the *same* held-out sessions and is computed by ``--stage-g``;
    ``None`` is ignored by :func:`verdict`, so one report cannot claim it.
    """
    results = report.get("results") or {}
    # §57: "fits the subset" means the sessions it was trained on. A report whose
    # declared subset is larger than §49.6's 200-session cap carries
    # ``train_fit_subset`` for exactly that set; older reports (and every arm at
    # or below the cap) keep using ``train_fit``.
    fit = results.get("train_fit_subset") or results.get("train_fit") or {}
    full = results.get("full") or {}
    cost = report.get("cost") or {}
    exact = fit.get("exact")
    chance = full.get("chance")
    return {
        "G1_fits_the_subset": (exact is not None and exact >= GENERAL_FIT_FLOOR),
        "G2_heldout_beats_chance": (
            full.get("wilson_lower") is not None
            and chance is not None
            and float(full["wilson_lower"]) > float(chance)
        ),
        "G3_store_beats_gru_on_heldout": None,
        "G4_cost_recorded": all(
            cost.get(key) not in (None, 0) for key in ("params", "train_seconds", "device")
        )
        and _cache_cost_recorded(report),
    }


def _cache_cost_recorded(report: Dict[str, Any]) -> bool:
    """B4's extra requirement: a cache arm must say what the cache dropped.

    Arms without a cache (everything before §59) have nothing to record, so this
    is ``True`` for them - the existing G4 cells stay exactly as measured. A
    ``tokencache`` arm cannot pass B4 without ``cost.cache``.
    """
    core_kind = (report.get("config") or {}).get("core")
    if core_kind != "tokencache":
        return True
    cache = (report.get("cost") or {}).get("cache") or {}
    if not cache:
        return False
    return all(
        (block or {}).get("tokens_dropped") is not None and (block or {}).get("slots")
        for block in cache.values()
    )


def mcnemar_one_sided(wins: int, losses: int) -> Optional[float]:
    """Exact one-sided sign test over the *discordant* pairs (no normal approx).

    ``wins`` is "the store is right and the GRU is wrong"; ``losses`` the
    reverse. Sessions both arms answer the same way carry no information about
    which one is better, so they are not in the denominator.
    """
    total = int(wins) + int(losses)
    if total <= 0:
        return None
    tail = sum(math.comb(total, k) for k in range(int(wins), total + 1))
    return tail / (2.0**total)


def _heldout_predictions(report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Re-run a report's checkpoint on the held-out corpus and return its records.

    The pair verdict must not trust the ``samples`` block (it keeps three rows),
    so both arms are re-evaluated from the checkpoint the report names; the
    weights hash is checked first, so a report and a checkpoint cannot be mixed.
    """
    config = report.get("config") or {}
    corpus_block = report.get("corpus") or {}
    corpus = load_corpus(
        sessions=int(corpus_block.get("sessions", PANTRY_SESSIONS)),
        seed=int(corpus_block.get("seed", PANTRY_SEED)),
    )
    kind = str(config.get("core") or "gru")
    core = build_core(
        hidden=int(config.get("hidden", HIDDEN)),
        emb=int(config.get("emb", EMB)),
        device="cpu",
        kind=kind,
        memory=bool(config.get("memory", True)),
    )
    checkpoint = report.get("checkpoint")
    if not checkpoint or not Path(checkpoint).exists():
        raise SystemExit("a report's checkpoint is missing; the pair cannot be re-evaluated")
    core.load_weights(checkpoint, strict_config=True)
    if kind != "gru" and core.config().get("model_kind") != kind:
        raise SystemExit(f"checkpoint model_kind is not {kind!r}")
    if core.weights_hash() != report.get("weights_hash"):
        raise SystemExit("checkpoint weights_hash does not match the report it is graded with")
    records = evaluate(core, corpus["heldout"], "full", module=corpus["module"])
    return {row["session_id"]: row for row in records}


def _start_source(report: Dict[str, Any]) -> Optional[str]:
    """Which weights a report's start actually is.

    A ``turnstore`` arm records ``source_weights_hash`` (the L it was copied
    from) because its own ``weights_hash`` is the derived model; a plain ``gru``
    arm records only ``weights_hash``, which *is* L's hash after loading. Both
    fields name the same thing here, so the pair check reads whichever exists
    instead of comparing two different keys and calling it a difference.
    """
    start = report.get("start") or {}
    return start.get("source_weights_hash") or start.get("weights_hash")


def stage_g_comparison(store: Dict[str, Any], gru: Dict[str, Any]) -> Dict[str, Any]:
    """§56.4's pair verdict: does the store generalise where the GRU does not?

    Both arms must be the registered pair (same corpus digests, same subset,
    same seed/lr/batch/epochs, same L derivation, one ``turnstore`` with the
    store on and one plain ``gru``), and the held-out answers are re-derived
    from the checkpoints. G3 is an exact sign test on the sessions where the two
    arms disagree, so "the store is better" cannot come from a shifted base rate.
    """
    problems: List[str] = []
    for label, report in (("store", store), ("gru", gru)):
        if _gate_prefix_of(report) != "G":
            problems.append(f"the {label} report is not graded under G")
        if report.get("overfit"):
            problems.append(f"the {label} report is an overfit calibration, not a subset arm")
    configs = [(store.get("config") or {}), (gru.get("config") or {})]
    if configs[0].get("core") != "turnstore" or configs[0].get("memory") is not True:
        problems.append("the first report is not the store arm (turnstore with memory on)")
    if configs[1].get("core") != "gru":
        problems.append("the second report is not the plain GRU arm")
    for key in (
        "seed",
        "lr",
        "batch",
        "epochs",
        "token_count",
        "hidden",
        "emb",
        "aux_lambda",
        "aux_mode",
        "train_subset",
    ):
        if configs[0].get(key) != configs[1].get(key):
            problems.append(f"the two arms differ in {key}")
    for key in ("train_digest", "heldout_digest"):
        if (store.get("corpus") or {}).get(key) != (gru.get("corpus") or {}).get(key):
            problems.append(f"the two arms used a different {key}")
    if (store.get("corpus") or {}).get("train_sessions_used") != (gru.get("corpus") or {}).get(
        "train_sessions_used"
    ):
        problems.append("the two arms used different numbers of training sessions")
    if _start_source(store) != _start_source(gru):
        problems.append("the two arms started from different derivations of L")
    for key in ("checkpoint_sha256", "init_weights_hash"):
        if (store.get("start") or {}).get(key) != (gru.get("start") or {}).get(key):
            problems.append(f"the two arms disagree on start.{key}")
    if problems:
        raise SystemExit("; ".join(problems))

    store_records = _heldout_predictions(store)
    gru_records = _heldout_predictions(gru)
    if set(store_records) != set(gru_records):
        raise SystemExit("the two arms were graded on different held-out sessions")

    shared = sorted(store_records)
    targeted = [sid for sid in shared if store_records[sid].get("target")]
    store_hits = sum(
        1 for sid in targeted if store_records[sid]["prediction"] == store_records[sid]["target"]
    )
    gru_hits = sum(
        1 for sid in targeted if gru_records[sid]["prediction"] == gru_records[sid]["target"]
    )
    wins = sum(
        1
        for sid in targeted
        if store_records[sid]["prediction"] == store_records[sid]["target"]
        and gru_records[sid]["prediction"] != gru_records[sid]["target"]
    )
    losses = sum(
        1
        for sid in targeted
        if store_records[sid]["prediction"] != store_records[sid]["target"]
        and gru_records[sid]["prediction"] == gru_records[sid]["target"]
    )
    p_value = mcnemar_one_sided(wins, losses)

    store_fit = ((store.get("results") or {}).get("train_fit") or {}).get("exact")
    gru_fit = ((gru.get("results") or {}).get("train_fit") or {}).get("exact")
    if store_fit is None or gru_fit is None:
        raise SystemExit("a train_fit exact rate is missing; the pair cannot be graded")
    store_chance = ((store.get("results") or {}).get("full") or {}).get("chance")
    gru_chance = ((gru.get("results") or {}).get("full") or {}).get("chance")
    if store_chance != gru_chance:
        raise SystemExit("the two arms were scored against different chance rates")

    store_gates = _stage_g_gate_values(store)
    gru_gates = _stage_g_gate_values(gru)
    checks = {
        # G1 is the arm whose held-out is read: the GRU's fit is recorded beside
        # it, because "the GRU did not fit either" changes the reading of G3 but
        # does not make the store's own fit untrue.
        "G1_fits_the_subset": store_gates["G1_fits_the_subset"],
        "G2_heldout_beats_chance": store_gates["G2_heldout_beats_chance"],
        "G3_store_beats_gru_on_heldout": (
            None
            if not store_gates["G1_fits_the_subset"]
            else bool(wins > losses and p_value is not None and p_value < GENERAL_ALPHA)
        ),
        "G4_cost_recorded": (store_gates["G4_cost_recorded"] and gru_gates["G4_cost_recorded"]),
    }
    return {
        "store_fit": store_fit,
        "gru_fit": gru_fit,
        "store_heldout_exact": _round(store_hits / len(targeted)) if targeted else None,
        "gru_heldout_exact": _round(gru_hits / len(targeted)) if targeted else None,
        "n": len(targeted),
        "chance": store_chance,
        "wins": wins,
        "losses": losses,
        "p_value": _round(p_value),
        "checks": checks,
        "all_pass": verdict(checks),
        "branch": stage_g_branch(checks, gru_fit=gru_fit),
    }


def stage_g_branch(checks: Dict[str, Any], gru_fit: Optional[float] = None) -> str:
    """§56.6, mechanically: what the next experiment is allowed to be."""
    if not checks["G1_fits_the_subset"]:
        return (
            "G1 fails: at 400 reviews/session the store does not fit 200 distinct sessions, "
            "so held-out is not read; next is per-turn regional losses (§55.6's T1-fail rule), "
            "never more epochs or width"
        )
    if not checks["G2_heldout_beats_chance"]:
        return (
            "G1 passes but G2 fails: fitting survives more sessions, generalisation does not; "
            "next is the memorisation diagnosis (where the prediction comes from), not more epochs"
        )
    if not checks["G3_store_beats_gru_on_heldout"]:
        note = (
            " (the GRU did not fit the subset either, so its chance-level held-out is not a "
            "generalisation failure to compare against)"
            if gru_fit is not None and gru_fit < GENERAL_FIT_FLOOR
            else ""
        )
        return (
            "G1+G2 pass but G3 does not: the arm generalises, the store is not shown to be why; "
            "next is the store's ablation at the same subset (memory=False), not more epochs" + note
        )
    return (
        "G1+G2+G3 pass: the store generalises at the same per-session budget; next is the same "
        "protocol on the remaining training sessions (data scaling), registered, not a score"
    )


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
    prefix = _gate_prefix_of(report)
    checks = {(prefix + name[1:]): value for name, value in checks.items()}
    return checks


def gate_values(report: Dict[str, Any]) -> Dict[str, Any]:
    """Recompute stage P's G1-G10 from the recorded numbers; never read the stored verdict."""
    if _gate_prefix_of(report) == "T":
        # §55's arms are graded by T1-T4, not by stage Q's nine conditions
        return _stage_t_gate_values(report)
    if _gate_prefix_of(report) == "G":
        # §56's arms are graded by G1-G4: fit, held-out above chance, pair, cost
        return _stage_g_gate_values(report)
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
        "G1_start_is_stage_l": start_is_stage_l(start),
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
def updates_per_session(steps: int, batch: int, sessions: int) -> float:
    """Rehearsals per session: a step touches ``min(batch, N)`` of the N rows.

    §54: holding *steps* fixed while N grows divides rehearsal by N, so two arms
    with the same step budget are not the same optimisation effort. Kept as a
    named function so the report and the tests cannot compute it differently.
    """
    if sessions <= 0:
        return 0.0
    return round(steps * min(batch, sessions) / sessions, 4)


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
    if not start_is_stage_l(start):
        problems.append(
            "the recorded start is neither the registered stage-L carrier nor a "
            "behaviour-preserving derivation of it"
        )

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
            kind = str(config.get("core") or "gru")
            core = build_core(
                hidden=int(config.get("hidden", HIDDEN)),
                emb=int(config.get("emb", EMB)),
                device="cpu",
                kind=kind,
                memory=bool(config.get("memory", True)),
            )
            core.load_weights(checkpoint, strict_config=True)
            if core.config().get("model_kind") != kind:
                problems.append(f"checkpoint model_kind is not {kind!r}")
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
    if args.train_sessions:
        if args.train_sessions > len(train_sessions):
            raise SystemExit(
                f"--train-sessions {args.train_sessions} asks for more sessions than the "
                f"{len(train_sessions)} available in the registered training split"
            )
        train_sessions = train_sessions[: args.train_sessions]

    control_block: Optional[Dict[str, Any]] = None
    # §56: a stage-G arm is a mechanism comparison on held-out sessions; its
    # gates do not include Q7 (the format-only control), and the attribution it
    # does read (G3) is paired on the same text, so a format model cannot create
    # it. Training an F-rand arm on the same subset would double the cost for a
    # gate that is not part of §56.4.
    needs_control = args.control != "rand" and not args.smoke and not args.overfit
    if args.gate_prefix == "G":
        needs_control = False
    if needs_control:
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

    if args.widen_to:
        core = build_core(hidden=args.widen_to, emb=args.emb, device=device, seed=args.seed)
        start_hash = widen_from_stage_l(core, Path(args.start), source_hidden=HIDDEN)
        widened = {
            "widened_from_hidden": HIDDEN,
            "source_weights_hash": L_WEIGHTS_HASH,
            "hidden": core.hidden,
        }
    elif args.core in STORE_ARMS:
        core = build_core(
            hidden=args.hidden,
            emb=args.emb,
            device=device,
            seed=args.seed,
            kind=args.core,
            memory=not args.no_memory,
        )
        start_hash = start_from_stage_l(core, Path(args.start), source_hidden=HIDDEN)
        widened = {
            "derived_from": args.core,
            "source_weights_hash": L_WEIGHTS_HASH,
            "hidden": core.hidden,
            "memory": core.memory,
        }
    else:
        core = build_core(hidden=args.hidden, emb=args.emb, device=device, seed=args.seed)
        start_hash = load_stage_l(core, Path(args.start))
        widened = {}

    arm = "rand" if args.control == "rand" else "answer"
    module = corpus["module"]
    samples = build_samples(
        train_sessions,
        seed=args.seed,
        control=args.control,
        prefix_module=module if args.aux_mode == "resolvable" else None,
        region_module=module if args.aux_mode == "weighted-region" else None,
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
    if len(train_sessions) > FIT_SESSIONS:
        # §49.6 capped the fit readout at 200 sessions for stage-P cost, but §56's
        # G1 (and §57's H1) is "the arm fits the sessions it was *trained on*". On
        # a 400-session subset those are different sets, so the declared subset is
        # measured too and the gate reads it; the capped number stays for the
        # stage-P comparison it was introduced for.
        results["train_fit_subset"] = summarise(
            evaluate(core, train_sessions, "full", module=module)
        )

    # §50.6: where does an answer exist along the testimony? Diagnostic only.
    diagnostics: Dict[str, Any] = {}
    if args.aux_loss > 0.0:
        diagnostics["readout"] = readout_profile(core, heldout, module=module)

    # the data contract behind "the answer is not in the question"
    leak = leak_report(heldout)

    # §59.4 B4: a token cache keeps only its first `slots` tokens
    slots = int(getattr(core, "slots", 0) or 0)
    cache_costs: Dict[str, Any] = {}
    if slots:
        cache_costs["heldout"] = cache_report(heldout, slots=slots)
        cache_costs["train_subset"] = cache_report(train_sessions, slots=slots)

    checkpoint = Path(args.out) / f"pantry_deduction_{stamp}.pt"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    core.save_weights(str(checkpoint))

    report: Dict[str, Any] = {
        "task_version": TASK_VERSION,
        "git_head": _git_head(),
        "device": device,
        "config": {
            "token_count": VOCAB_SIZE,
            "hidden": core.hidden,
            "emb": args.emb,
            "chunk_seconds": CHUNK_SECONDS,
            "lr": args.lr,
            "batch": args.batch,
            "epochs": args.epochs,
            "seed": args.seed,
            "max_answer_bytes": MAX_ANSWER_BYTES,
            "arm": arm,
            "core": args.core,
            "memory": None if args.core == "gru" else not args.no_memory,
            "aux_lambda": args.aux_loss,
            "aux_mode": args.aux_mode,
            "gate_prefix": args.gate_prefix,
            "overfit_sessions": args.overfit,
            "train_subset": args.train_sessions or None,
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
            **widened,
        },
        "params": core.parameter_count(),
        "weights_hash": core.weights_hash(),
        "training": {
            "epochs_run": len(history),
            "steps": sum(row["batches"] for row in history),
            # §54: "fixed steps" is not "fixed rehearsal". With batch 8, a step
            # touches min(batch, N) of the N sessions, so updates per session is
            # steps * min(batch, N) / N and falls as 1/N when the budget is held
            # fixed. Recorded so a capacity comparison can never mix the two
            # again.
            "updates_per_session": updates_per_session(
                sum(row["batches"] for row in history), args.batch, len(train_sessions)
            ),
            "seconds": round(time.time() - started, 1),
            "history": history,
            **(
                {"aux_region": region_stats(samples)}
                if args.aux_mode == "weighted-region" and args.aux_loss > 0.0
                else {}
            ),
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
            **({"cache": cache_costs} if cache_costs else {}),
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
    parser.add_argument(
        "--core",
        choices=("gru", "turnstore", "tokencache"),
        default="gru",
        help=(
            "§55 stage T: 'turnstore' is the per-turn store arm (same recurrence, "
            "one write per turn, read into the head); §59 stage B: 'tokencache' "
            "writes one entry per token and reads it into the head; 'gru' is every "
            "earlier stage"
        ),
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help=(
            "§55 T2/T3 ablation: keep every parameter, set the read to 0 and write "
            "nothing (only meaningful with --core turnstore)"
        ),
    )
    parser.add_argument(
        "--stage-t",
        nargs=2,
        metavar=("STORE", "ABLATION"),
        help="§55.4/§55.6: grade the pair from two finished reports and print the branch",
    )
    parser.add_argument(
        "--stage-g",
        nargs=2,
        metavar=("STORE", "GRU"),
        help="§56.4/§56.6: grade the held-out pair from two finished reports and print the branch",
    )
    parser.add_argument(
        "--train-sessions",
        type=int,
        default=0,
        metavar="N",
        help=(
            "§56: train on the first N of the registered 800 training sessions (a declared "
            "subset, not an overfit calibration); graded under --gate-prefix G"
        ),
    )
    parser.add_argument(
        "--widen-to",
        type=int,
        default=0,
        metavar="HIDDEN",
        help=(
            "§52.4 width rung: build HIDDEN-wide and zero-extend L's weights into it "
            "(behavioural identity at step 0; --hidden is ignored)"
        ),
    )
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
        choices=("all", "resolvable", "weighted-region"),
        help=(
            "what the earlier boundaries are asked (§50.2 'all' vs §51.2 'resolvable': "
            "only where the prefix already has a unique derive() answer; §60 "
            "'weighted-region': only names still consistent with that prefix, weighted "
            "by 1/|candidates|)"
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
    if args.aux_mode != "all" and args.aux_loss <= 0.0:
        parser.error(f"--aux-mode {args.aux_mode} only matters with --aux-loss > 0")
    if args.aux_mode == "weighted-region":
        # §60 registers this as an objective on the per-turn store; the other
        # cores were measured under different objectives and changing two things
        # at once would not attribute the result to the region loss.
        if args.core != "turnstore":
            parser.error(
                "§60 registers --aux-mode weighted-region on --core turnstore; "
                "another carrier is a different experiment"
            )
        if args.control == "rand":
            parser.error(
                "--aux-mode weighted-region needs the real culprit: the format control "
                "trains a random name that is not necessarily in the roster, so the "
                "region loss would have no valid target"
            )
    if args.gate_prefix is not None and (
        len(args.gate_prefix) != 1
        or not args.gate_prefix.isalpha()
        or args.gate_prefix != args.gate_prefix.upper()
    ):
        parser.error("--gate-prefix must be a single A-Z letter")
    if args.overfit < 0:
        parser.error("--overfit must be >= 0")
    if args.train_sessions < 0:
        parser.error("--train-sessions must be >= 0")
    if args.train_sessions and args.overfit:
        parser.error(
            "--train-sessions is §56's declared subset; --overfit is §50.4's calibration. "
            "The two subsets have different gates and cannot be the same run"
        )
    if args.train_sessions and args.limit:
        parser.error("--train-sessions and --limit both subset the training split; pass one")
    if args.train_sessions and args.smoke:
        parser.error("--train-sessions is not a smoke flag")
    if args.train_sessions and args.gate_prefix != "G":
        parser.error(
            "a --train-sessions arm is capped by its subset and must be graded under "
            "--gate-prefix G (§56), not by a stage that assumes all 800 sessions"
        )
    if args.no_memory and args.core not in STORE_ARMS:
        parser.error(
            "--no-memory is the store-arm ablation; pass --core " + " or ".join(sorted(STORE_ARMS))
        )
    if args.widen_to and args.core != "gru":
        parser.error("--widen-to is §52.4's GRU width rung; it does not combine with --core")
    if args.core != "gru" and (args.hidden != HIDDEN or args.emb != EMB):
        parser.error(
            f"§55/§59 fix hidden={HIDDEN} and emb={EMB} for the store arms; "
            "varying them is a different experiment"
        )
    if args.widen_to:
        if args.widen_to <= HIDDEN:
            parser.error(
                f"--widen-to must be > {HIDDEN} (L's width); a narrower model is not a width rung"
            )
        if args.hidden != HIDDEN:
            parser.error("--widen-to replaces --hidden; pass one of the two, not both")
        if args.emb != EMB:
            parser.error(f"--widen-to keeps emb fixed at {EMB}; varying both is not §52.4's rung")

    if args.smoke:
        if args.device == "auto":
            args.device = "cpu"
        args.epochs = min(args.epochs, 1)
        args.limit = args.limit or 4
        args.eval_limit = args.eval_limit or 8
        args.batch = min(args.batch, 4)
        # §60's objective needs the real culprit (a control's random name is not
        # necessarily in the roster), so a weighted-region smoke stays on the
        # scored arm's target; it is still marked `smoke` and never a control.
        if args.aux_mode == "weighted-region":
            args.control = None
        else:
            args.control = args.control or "rand"
        if args.out == "data/pantry_stage":
            # a smoke report must never be picked up as the F-rand control
            args.out = "data/pantry_stage/smoke"

    if args.stage_t:
        store_path, ablation_path = (Path(part) for part in args.stage_t)
        try:
            outcome = stage_t_comparison(
                json.loads(store_path.read_text(encoding="utf-8")),
                json.loads(ablation_path.read_text(encoding="utf-8")),
            )
        except SystemExit as exc:
            print(f"FAILED --stage-t: {exc}")
            return 1
        print(f"store    : {store_path}  train exact {outcome['store_exact']:.4f}")
        print(f"ablation : {ablation_path}  train exact {outcome['ablation_exact']:.4f}")
        print(f"gap      : {outcome['gap']:.4f}  (GRU control {outcome['gru_control_exact']:.4f})")
        for name, value in outcome["checks"].items():
            print(f"  {'PASS' if value else 'FAIL'}  {name}")
        print(f"all_pass : {outcome['all_pass']}")
        print(f"branch   : {outcome['branch']}")
        return 0 if outcome["all_pass"] else 1

    if args.stage_g:
        store_path, gru_path = (Path(part) for part in args.stage_g)
        try:
            outcome = stage_g_comparison(
                json.loads(store_path.read_text(encoding="utf-8")),
                json.loads(gru_path.read_text(encoding="utf-8")),
            )
        except SystemExit as exc:
            print(f"FAILED --stage-g: {exc}")
            return 1
        print(
            f"store : {store_path}  fit {outcome['store_fit']:.4f}  "
            f"held-out {outcome['store_heldout_exact']:.4f}"
        )
        print(
            f"gru   : {gru_path}  fit {outcome['gru_fit']:.4f}  "
            f"held-out {outcome['gru_heldout_exact']:.4f}"
        )
        print(
            f"pairs : n={outcome['n']}  chance={outcome['chance']:.4f}  "
            f"store-only {outcome['wins']}  gru-only {outcome['losses']}  "
            f"p={outcome['p_value']}"
        )
        for name, value in outcome["checks"].items():
            label = "n/a " if value is None else ("PASS" if value else "FAIL")
            print(f"  {label}  {name}")
        print(f"all_pass : {outcome['all_pass']}")
        print(f"branch   : {outcome['branch']}")
        return 0 if outcome["all_pass"] else 1

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
    if report["config"].get("train_subset"):
        print(
            f"subset    : {report['config']['train_subset']} of the registered training "
            "sessions (§56); held-out is the 200 unseen answer tuples"
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
