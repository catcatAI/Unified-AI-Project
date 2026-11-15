#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§67: is the readout the missing piece? (frozen carrier, selection head only)

Why this exists
---------------
§66 read three levels at the answer boundary and returned R3b: ``h`` never carries
the session (cosine 1.0000 with the roster swapped, 0.9870/0.9999 even between
unrelated sessions), the store's values and the content-addressed read do move
with the roster (median cosine 0.8405/0.8553 at k=2, 0.9938/0.8105 at k=5), and
the head is shown that read vector - yet the roster-restricted argmax follows the
swapped mapping exactly 1/k of the time.

That result has two readings, and only one of them is a readout problem:

1. the state holds a value -> person binding and the autoregressive head never
   uses it (then a selection head should recover it, and it should transfer);
2. the read vector merely *varies* with the roster text (session memory) without
   identifying the culprit in a way that transfers (then no readout can turn it
   into held-out accuracy).

§66 measured variation, not answer identity, so it could not separate them. This
stage changes only the readout.

What this measures
------------------
The carrier is frozen: its ``weights_hash`` and the checkpoint's sha256 are
recorded before and after, and only a small head is trained, on the same 400
declared training items the carrier fitted:

    score(c) = v . tanh(W_h h + W_r read + W_e e_c + b)

with ``e_c`` the frozen mean byte embedding of candidate ``c``, and the softmax
taken over the session's own roster only, so an out-of-roster answer is
impossible by construction (recorded as a construction check, not a score).

Three arms, one architecture, identical parameter count and initialisation:

* ``read`` - ``[h, read, e_c]``: the registered readout;
* ``h``    - ``read`` zeroed at train and eval: the controller alone;
* ``cand`` - ``h`` and ``read`` zeroed: the candidate names alone (content-free).

plus one intervention that needs no training: ``permuted`` rotates each held-out
session's ``read`` onto its neighbour, so a head that still answers correctly is
not reading ``read`` at all.

What it is not
--------------
Not a capability score - the core score stays 0.00/10 whatever happens. Not a
claim that a selection head is the product: the roster is given by the session, so
this is a multiple-choice readout of a task whose answer is already one of the
named people. It decides one question: does the state hold a *transferable*
binding that a readout can use, or does §66's "the content is there" mean only
"the read vector varies with the roster"?

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_selection.py \\
        --report data/pantry_stage/ord_arm/pantry_deduction_20261115-015751.json \\
        --out data/pantry_stage/sel67/k2.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
TRAINER = REPO_ROOT / "scripts" / "train_pantry_deduction.py"
PROBE = REPO_ROOT / "scripts" / "probe_pantry_readout.py"

# §67.4, written before the run.
HEAD_HIDDEN = 64
HEAD_STEPS = 6000
HEAD_BATCH = 8
HEAD_LR = 1e-3
HEAD_WEIGHT_DECAY = 1e-4
HEAD_SEED = 20261118
EVAL_EVERY = 500
FIT_FLOOR = 0.90
ORDER_FLOOR = 0.80
ARMS = ("read", "h", "cand")
PREDICT_BATCH = 64


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_trainer() -> Any:
    return _load("pantry_selection_trainer", TRAINER)


def load_probe() -> Any:
    """Reuse §66's carrier rebuild so the two stages cannot drift apart."""
    return _load("pantry_selection_probe", PROBE)


# --------------------------------------------------------------------------- #
# features and the head
# --------------------------------------------------------------------------- #
def session_features(
    trainer: Any,
    probe: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    names: Sequence[str],
    *,
    batch: int = PREDICT_BATCH,
) -> Dict[str, Any]:
    """Frozen carrier features at the answer boundary, one row per session."""
    torch = core._torch
    hidden: List[Any] = []
    read: List[Any] = []
    rosters: List[List[int]] = []
    targets: List[int] = []
    culprits: List[str] = []
    core.eval()
    with torch.no_grad():
        for chunk in trainer._chunks(list(sessions), batch):
            turns: List[List[List[int]]] = []
            gaps: List[List[float]] = []
            for session in chunk:
                tokens, deltas = probe.turn_payload(trainer, session)
                turns.append(tokens)
                gaps.append(deltas)
            state, _ = trainer.run_session(core, turns, gaps)
            tensors = dict(state.tensors)
            hidden.append(tensors["h"].detach().cpu())
            read.append(core.read_vector(tensors).detach().cpu())
            for session in chunk:
                roster = list(session["environment"]["actors"])
                culprit = session["ground_truth_oracle"]["culprit"]
                rosters.append([names.index(name) for name in roster])
                targets.append(roster.index(culprit))
                culprits.append(culprit)
    return {
        "h": torch.cat(hidden, dim=0),
        "read": torch.cat(read, dim=0),
        "roster": torch.as_tensor(rosters, dtype=torch.long),
        "target": torch.as_tensor(targets, dtype=torch.long),
        "culprit": culprits,
    }


def name_vectors(core: Any, names: Sequence[str], trainer: Any) -> Any:
    """Each name as the frozen mean byte embedding the carrier already owns."""
    torch = core._torch
    table = core.embedding.weight.detach()
    rows = []
    for name in names:
        ids = [trainer.BYTE_OFFSET + byte for byte in name.encode("utf-8")]
        rows.append(table[torch.as_tensor(ids, dtype=torch.long)].mean(dim=0))
    return torch.stack(rows, dim=0)


def build_head(torch: Any, h_dim: int, r_dim: int, e_dim: int, hidden: int, seed: int) -> Any:
    """The selection head; every arm constructs it under the same seed."""
    nn = torch.nn

    class SelectionHead(nn.Module):
        """``[h, read, e_c] -> one score per roster candidate``."""

        def __init__(self) -> None:
            super().__init__()
            self.proj_h = nn.Linear(h_dim, hidden)
            self.proj_r = nn.Linear(r_dim, hidden)
            self.proj_e = nn.Linear(e_dim, hidden)
            self.score = nn.Linear(hidden, 1)

        def forward(self, state: Any, read: Any, candidates: Any) -> Any:
            combined = (
                self.proj_h(state).unsqueeze(1)
                + self.proj_r(read).unsqueeze(1)
                + self.proj_e(candidates)
            )
            return self.score(torch.tanh(combined)).squeeze(-1)

    torch.manual_seed(seed)
    return SelectionHead()


def parameter_count(head: Any) -> int:
    return int(sum(part.numel() for part in head.parameters()))


def _prepare(
    torch: Any,
    data: Dict[str, Any],
    names_vec: Any,
    rows: Any,
    use_h: bool,
    use_read: bool,
) -> Any:
    state = data["h"][rows]
    read = data["read"][rows]
    if not use_h:
        state = torch.zeros_like(state)
    if not use_read:
        read = torch.zeros_like(read)
    return state, read, names_vec[data["roster"][rows]]


def wilson(correct: int, total: int) -> Tuple[float, float]:
    """95% Wilson interval, the same form the trainer uses for its gates."""
    if total <= 0:
        return 0.0, 0.0
    z = 1.96
    p = correct / total
    denominator = 1.0 + z * z / total
    centre = (p + z * z / (2.0 * total)) / denominator
    margin = z * ((p * (1.0 - p) / total + z * z / (4.0 * total * total)) ** 0.5) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def summarise(predictions: Sequence[str], targets: Sequence[str]) -> Dict[str, Any]:
    total = len(targets)
    correct = sum(1 for name, target in zip(predictions, targets) if name == target)
    low, high = wilson(correct, total)
    counts: Dict[str, int] = {}
    for name in predictions:
        counts[name] = counts.get(name, 0) + 1
    top_name, top_count = ("", 0)
    if counts:
        top_name, top_count = max(counts.items(), key=lambda item: item[1])
    return {
        "n": total,
        "correct": correct,
        "exact": round(correct / total, 4) if total else 0.0,
        "wilson_lower": round(low, 4),
        "wilson_upper": round(high, 4),
        "distinct_predictions": len(counts),
        "top_prediction": top_name,
        "top_share": round(top_count / total, 4) if total else 0.0,
    }


# --------------------------------------------------------------------------- #
# training and reading one arm
# --------------------------------------------------------------------------- #
def fit_head(
    torch: Any,
    head: Any,
    data: Dict[str, Any],
    names_vec: Any,
    *,
    steps: int,
    batch: int,
    lr: float,
    weight_decay: float,
    seed: int,
    use_h: bool,
    use_read: bool,
    observer: Any = None,
    every: int = EVAL_EVERY,
) -> List[Dict[str, Any]]:
    """Fixed-budget fit; the reported head is the last step, never a best one."""
    functional = torch.nn.functional
    count = int(data["target"].shape[0])
    generator = torch.Generator().manual_seed(seed + 17)
    optimizer = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=weight_decay)
    curve: List[Dict[str, Any]] = []
    head.train()
    for step in range(1, steps + 1):
        rows = torch.randint(0, count, (batch,), generator=generator)
        state, read, candidates = _prepare(torch, data, names_vec, rows, use_h, use_read)
        loss = functional.cross_entropy(head(state, read, candidates), data["target"][rows])
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        if observer is not None and step % every == 0:
            curve.append(observer(step))
    return curve


def predict(
    torch: Any,
    head: Any,
    data: Dict[str, Any],
    names_vec: Any,
    names: Sequence[str],
    *,
    use_h: bool,
    use_read: bool,
    batch: int = PREDICT_BATCH,
) -> List[str]:
    """One roster argmax per row, returned as names."""
    head.eval()
    count = int(data["target"].shape[0])
    picked: List[str] = []
    with torch.no_grad():
        for start in range(0, count, batch):
            rows = torch.arange(start, min(start + batch, count))
            state, read, candidates = _prepare(torch, data, names_vec, rows, use_h, use_read)
            choice = torch.argmax(head(state, read, candidates), dim=1).tolist()
            for offset, position in enumerate(choice):
                picked.append(str(names[int(data["roster"][start + offset, position])]))
    return picked


def rotate_rows(torch: Any, tensor: Any) -> Any:
    """The permuted-read intervention: every row gets its neighbour's read."""
    shifts = torch.roll(torch.arange(int(tensor.shape[0])), shifts=-1)
    return tensor[shifts]


def mutation_share(tensor: Any) -> float:
    """How many rows the rotation actually moves (1.0 means a real rotation)."""
    count = int(tensor.shape[0])
    if count < 2:
        return 0.0
    moved = 0
    for row in range(count):
        if not bool((tensor[row] == tensor[(row + 1) % count]).all()):
            moved += 1
    return round(moved / count, 4)


def outside_roster(picks: Sequence[str], sessions: Sequence[Dict[str, Any]]) -> int:
    return sum(
        1 for name, session in zip(picks, sessions) if name not in session["environment"]["actors"]
    )


# --------------------------------------------------------------------------- #
# gates and the fork
# --------------------------------------------------------------------------- #
def gates(
    arms: Dict[str, Any],
    *,
    k: int,
    permuted: Dict[str, Any],
    outside: Dict[str, int],
) -> Dict[str, Any]:
    """§67.6, mechanically: fit, transfer, order invariance, attribution."""
    chance = 1.0 / k if k else 0.0
    read = arms["read"]
    baselines = [arms["h"]["heldout"], arms["cand"]["heldout"], permuted]
    ceiling = max(block["wilson_upper"] for block in baselines)
    return {
        "S1_fit": {
            "pass": read["fit"]["exact"] >= FIT_FLOOR,
            "value": read["fit"]["exact"],
            "floor": FIT_FLOOR,
        },
        "S2_transfer": {
            "pass": read["heldout"]["wilson_lower"] > chance,
            "value": read["heldout"]["wilson_lower"],
            "chance": round(chance, 4),
        },
        "S3_order": {
            "pass": read["order_same_person"] >= ORDER_FLOOR,
            "value": read["order_same_person"],
            "floor": ORDER_FLOOR,
        },
        "S4_attribution": {
            "pass": read["heldout"]["wilson_lower"] > ceiling,
            "read_lower": read["heldout"]["wilson_lower"],
            "baseline_ceiling": round(ceiling, 4),
            "baselines": {
                "h": arms["h"]["heldout"]["wilson_upper"],
                "cand": arms["cand"]["heldout"]["wilson_upper"],
                "permuted": permuted["wilson_upper"],
            },
        },
        # a construction check, not a hypothesis: the softmax is over the roster
        "R3_in_roster": {
            "pass": all(value == 0 for value in outside.values()),
            "outside_roster": dict(outside),
        },
    }


def branch(gate: Dict[str, Any]) -> Dict[str, str]:
    """§67.7, mechanically: which reading the four gates select."""
    if not gate["S1_fit"]["pass"]:
        return {
            "id": "R4a-head-cannot-fit",
            "reading": (
                "the frozen state does not let a selection head fit even the 400 items the carrier "
                f"fitted (fit {gate['S1_fit']['value']} < {FIT_FLOOR}): §66's 'the content is there' "
                "means only 'the read vector varies with the roster', not 'it identifies the culprit'"
            ),
            "next": (
                "probe what the read vector does encode (a linear readout of culprits versus roster "
                "slots on the same states), not more training and not another head"
            ),
        }
    if not gate["S2_transfer"]["pass"]:
        return {
            "id": "R4b-fits-not-transfers",
            "reading": (
                "the head fits the declared items but the held-out Wilson lower bound stays at or "
                f"below chance ({gate['S2_transfer']['value']} <= {gate['S2_transfer']['chance']}): "
                "the readout is not the missing piece - the state holds per-session memory, not a "
                "transferable value -> person binding"
            ),
            "next": (
                "measure what differs between the fitted and the held-out states (the §58 shape: "
                "in-sample 0.9725, held-out 0.1100), since no readout over the same state can "
                "produce transfer the state does not contain"
            ),
        }
    if not gate["S4_attribution"]["pass"]:
        return {
            "id": "R4c-uses-a-prior",
            "reading": (
                "the head transfers, but not above every baseline "
                f"({gate['S4_attribution']['read_lower']} <= "
                f"{gate['S4_attribution']['baseline_ceiling']}): what it learned is available "
                "without the read vector, so the gain is not attributable to it"
            ),
            "next": "audit which input the head uses before any claim about the state's binding",
        }
    if not gate["S3_order"]["pass"]:
        return {
            "id": "R4d-unstable-under-order",
            "reading": (
                "the head transfers and beats its baselines, but reordering the same roster moves "
                f"the answer ({gate['S3_order']['value']} < {ORDER_FLOOR}): the selection still "
                "keys on slot position rather than on the value -> person mapping"
            ),
            "next": "normalise the roster order inside the head (sort or set-pool) before scaling up",
        }
    return {
        "id": "R4e-readout-was-missing",
        "reading": (
            "the frozen state holds a transferable binding that a roster-restricted selection head "
            "recovers above chance and above every baseline, and it survives a roster reorder: the "
            "readout was the missing piece"
        ),
        "next": (
            "apply the same head to the full eleven-turn corpus (§49) and only then speak about "
            "capability; the core score still moves only when a frozen benchmark says so"
        ),
    }


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #
def _observe(
    torch: Any,
    head: Any,
    names_vec: Any,
    names: Sequence[str],
    train_data: Dict[str, Any],
    held_data: Dict[str, Any],
    *,
    use_h: bool,
    use_read: bool,
) -> Any:
    def observe(step: int) -> Dict[str, Any]:
        fit_picks = predict(
            torch, head, train_data, names_vec, names, use_h=use_h, use_read=use_read
        )
        held_picks = predict(
            torch, head, held_data, names_vec, names, use_h=use_h, use_read=use_read
        )
        return {
            "step": step,
            "fit_exact": summarise(fit_picks, train_data["culprit"])["exact"],
            "heldout_exact": summarise(held_picks, held_data["culprit"])["exact"],
        }

    return observe


def run(
    trainer: Any,
    probe: Any,
    report_path: Path,
    report: Dict[str, Any],
    *,
    device: str = "cpu",
    steps: int = HEAD_STEPS,
) -> Dict[str, Any]:
    corpus_block = report.get("corpus") or {}
    if not corpus_block.get("minimal_binding"):
        raise SystemExit("§67 reads the §62/§63/§64 minimal-binding corpus, not this report")
    k = int(corpus_block.get("minimal_roster_size") or 2)
    module = trainer._load_generator()
    corpus = trainer.load_corpus(
        minimal_binding=True,
        order_augmented=bool(corpus_block.get("minimal_order_augmented")),
        roster_size=k,
    )
    train = list(corpus["train"])
    heldout = list(corpus["heldout"])
    names = sorted(module.ACTORS)

    checkpoint = Path(str(report.get("checkpoint")))
    hash_before = probe.checkpoint_sha256(checkpoint)
    core = probe.rebuild_core(trainer, report, device=device)
    weights_before = str(core.weights_hash() or "")
    started = time.time()

    torch = core._torch
    names_vec = name_vectors(core, names, trainer)
    train_data = session_features(trainer, probe, core, train, names)
    held_data = session_features(trainer, probe, core, heldout, names)
    twin_data = session_features(
        trainer, probe, core, [module.minimal_twin(row) for row in heldout], names
    )
    reorder_data = session_features(
        trainer, probe, core, [module.minimal_order_twin(row) for row in heldout], names
    )

    arms: Dict[str, Any] = {}
    heads: Dict[str, Any] = {}
    for arm in ARMS:
        use_h = arm != "cand"
        use_read = arm == "read"
        head = build_head(
            torch,
            int(core.hidden),
            int(names_vec.shape[1]),
            int(core.emb),
            HEAD_HIDDEN,
            HEAD_SEED,
        )
        observer = _observe(
            torch, head, names_vec, names, train_data, held_data, use_h=use_h, use_read=use_read
        )
        curve = fit_head(
            torch,
            head,
            train_data,
            names_vec,
            steps=steps,
            batch=HEAD_BATCH,
            lr=HEAD_LR,
            weight_decay=HEAD_WEIGHT_DECAY,
            seed=HEAD_SEED,
            use_h=use_h,
            use_read=use_read,
            observer=observer,
        )
        fit_picks = predict(
            torch, head, train_data, names_vec, names, use_h=use_h, use_read=use_read
        )
        held_picks = predict(
            torch, head, held_data, names_vec, names, use_h=use_h, use_read=use_read
        )
        twin_picks = predict(
            torch, head, twin_data, names_vec, names, use_h=use_h, use_read=use_read
        )
        reorder_picks = predict(
            torch, head, reorder_data, names_vec, names, use_h=use_h, use_read=use_read
        )
        arms[arm] = {
            "fit": summarise(fit_picks, train_data["culprit"]),
            "heldout": summarise(held_picks, held_data["culprit"]),
            "twin": summarise(twin_picks, twin_data["culprit"]),
            "order_same_person": round(
                sum(
                    1 for name, target in zip(reorder_picks, held_data["culprit"]) if name == target
                )
                / len(held_data["culprit"]),
                4,
            ),
            "curve": curve,
            "parameters": parameter_count(head),
        }
        heads[arm] = head

    permuted_data = dict(held_data)
    permuted_data["read"] = rotate_rows(torch, held_data["read"])
    permuted_picks = predict(
        torch, heads["read"], permuted_data, names_vec, names, use_h=True, use_read=True
    )
    permuted = summarise(permuted_picks, held_data["culprit"])

    outside = {
        arm: outside_roster(
            predict(
                torch,
                heads[arm],
                held_data,
                names_vec,
                names,
                use_h=arm != "cand",
                use_read=arm == "read",
            ),
            heldout,
        )
        for arm in ARMS
    }
    gate = gates(arms, k=k, permuted=permuted, outside=outside)
    share = mutation_share(held_data["read"])
    hash_after = probe.checkpoint_sha256(checkpoint)
    instrument_ok = bool(
        gate["R3_in_roster"]["pass"] and share == 1.0 and hash_before == hash_after
    )
    weights_after = str(core.weights_hash() or "")
    elapsed = time.time() - started
    return {
        "stage": "§67 roster-restricted selection head",
        "source_report": str(report_path),
        "checkpoint": str(checkpoint),
        "k": k,
        "chance": round(1.0 / k, 4),
        "corpus": {
            "train_digest": (corpus.get("meta") or {}).get("train_digest"),
            "heldout_digest": (corpus.get("meta") or {}).get("heldout_digest"),
            "train_items": len(train),
            "heldout_items": len(heldout),
            "minimal_order_augmented": bool(corpus_block.get("minimal_order_augmented")),
        },
        "head": {
            "architecture": "v . tanh(W_h h + W_r read + W_e e_c + b)",
            "hidden": HEAD_HIDDEN,
            "steps": steps,
            "batch": HEAD_BATCH,
            "lr": HEAD_LR,
            "weight_decay": HEAD_WEIGHT_DECAY,
            "seed": HEAD_SEED,
            "selection": "the last step; no early stopping, no checkpoint choice",
            "parameters": parameter_count(heads["read"]),
        },
        "arms": arms,
        "permuted_read": permuted,
        "gates": gate,
        "branch": branch(gate),
        "r4_cost": {
            "device": device,
            "seconds": round(elapsed, 2),
            "weights_hash_before": weights_before,
            "weights_hash_after": weights_after,
            "carrier_unchanged": weights_after == weights_before,
            "checkpoint_sha256_before": hash_before,
            "checkpoint_sha256_after": hash_after,
            "checkpoint_unchanged": hash_before == hash_after,
            "read_permutation_share": share,
        },
        "instrument_ok": instrument_ok,
        "all_pass": instrument_ok,  # the gates are a finding, not a pass/fail
    }


# --------------------------------------------------------------------------- #
# mechanical re-check
# --------------------------------------------------------------------------- #
def check(path: Path) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    problems: List[str] = []
    gates_block = data.get("gates") or {}
    arms = data.get("arms") or {}

    for arm in ARMS:
        if arm not in arms:
            problems.append(f"arm {arm} is missing")
            continue
        fit = (arms[arm].get("fit") or {}).get("exact")
        held = (arms[arm].get("heldout") or {}).get("exact")
        if not isinstance(fit, (int, float)) or not isinstance(held, (int, float)):
            problems.append(f"arm {arm} has no fit/held-out exact")
        if len(arms[arm].get("curve") or []) < 2:
            problems.append(f"arm {arm} recorded fewer than two curve points")
        if (arms[arm].get("parameters") or 0) <= 0:
            problems.append(f"arm {arm} recorded no parameter count")

    try:
        expected = gates(
            arms,
            k=int(data.get("k") or 0),
            permuted=data.get("permuted_read") or {},
            outside=((gates_block.get("R3_in_roster") or {}).get("outside_roster") or {}),
        )
    except (KeyError, TypeError) as error:
        problems.append(f"the stored numbers cannot be re-gated: {error}")
        return problems

    for key, block in expected.items():
        stored = gates_block.get(key) or {}
        if stored.get("pass") != block["pass"]:
            problems.append(
                f"gate {key} is stale: stored {stored.get('pass')}, recomputed {block['pass']}"
            )

    fork = branch(expected)
    if (data.get("branch") or {}).get("id") != fork["id"]:
        problems.append(
            f"the branch is stale: stored {(data.get('branch') or {}).get('id')}, "
            f"recomputed {fork['id']}"
        )

    cost = data.get("r4_cost") or {}
    if cost.get("weights_hash_before") != cost.get("weights_hash_after"):
        problems.append("the carrier weights changed; the run trained more than the head")
    if cost.get("carrier_unchanged") is not True:
        problems.append("r4_cost.carrier_unchanged is not True")
    if cost.get("checkpoint_sha256_before") != cost.get("checkpoint_sha256_after"):
        problems.append("checkpoint bytes changed")
    if cost.get("checkpoint_unchanged") is not True:
        problems.append("r4_cost.checkpoint_unchanged is not True")
    if cost.get("read_permutation_share") != 1.0:
        problems.append("the read permutation was not a real rotation")
    if not data.get("instrument_ok"):
        problems.append("instrument_ok is false")
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default="", help="a finished pantry-deduction report")
    parser.add_argument("--check", default="", help="re-derive a stage-§67 JSON's verdict")
    parser.add_argument("--device", default="cpu", help="cpu is the registered device")
    parser.add_argument("--steps", type=int, default=HEAD_STEPS)
    parser.add_argument("--out", default="", help="write the JSON verdict here")
    args = parser.parse_args(argv)

    if args.check:
        problems = check(Path(args.check))
        print(f"file: {args.check}")
        for problem in problems:
            print(f"  FAIL  {problem}")
        print(f"check: {'OK' if not problems else 'FAILED'}")
        return 0 if not problems else 1

    if not args.report:
        parser.error("one of --report or --check is required")
    path = Path(args.report)
    if not path.exists():
        raise SystemExit(f"missing report: {path}")
    trainer = load_trainer()
    probe = load_probe()
    report = json.loads(path.read_text(encoding="utf-8"))
    outcome = run(trainer, probe, path, report, device=args.device, steps=args.steps)

    print(f"report   : {path}")
    print(f"k        : {outcome['k']}  chance {outcome['chance']}")
    print(f"head     : {outcome['head']['parameters']} params, {outcome['head']['steps']} steps")
    print()
    print(f"  {'arm':6s} {'fit':>7s} {'held-out':>9s} {'wilson':>16s} {'order':>7s}")
    for arm in ARMS:
        block = outcome["arms"][arm]
        held = block["heldout"]
        print(
            f"  {arm:6s} {block['fit']['exact']:7.4f} {held['exact']:9.4f} "
            f"{held['wilson_lower']:7.4f}-{held['wilson_upper']:7.4f} "
            f"{block['order_same_person']:7.4f}"
        )
    permuted = outcome["permuted_read"]
    print(
        f"  perm   {'':7s} {permuted['exact']:9.4f} "
        f"{permuted['wilson_lower']:7.4f}-{permuted['wilson_upper']:7.4f}"
    )
    print()
    for key, block in outcome["gates"].items():
        print(f"  {key:18s} {'PASS' if block['pass'] else 'FAIL'}")
    print()
    print(f"branch   : {outcome['branch']['id']}")
    print(f"reading  : {outcome['branch']['reading']}")
    print(f"next     : {outcome['branch']['next']}")
    print(f"cost     : {outcome['r4_cost']['seconds']}s on {outcome['r4_cost']['device']}")
    print(f"instrument_ok : {outcome['instrument_ok']}")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
        print(f"wrote    : {args.out}")
    return 0 if outcome["instrument_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
