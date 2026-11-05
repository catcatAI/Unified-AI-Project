#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""A mixed (multi-approach) decoder for the MVE-1 boundary, with the mix measured.

Four ways to produce the six numbers of a state block, of deliberately different
kind, so their failures are not the same failure:

* ``operator``  — contract §5 arithmetic ``c + (in - c)·e^(-dt/tau)`` with the
  per-intent constants solved in closed form. Parametric, 19 numbers, exact when
  the intent was trained on.
* ``table``     — the contract's own intent→target table (§5 runtime lookup).
  Not learned at all: it is the knowledge source the engine already carries, and
  it is the only component that can answer an intent never seen in training.
* ``knn``       — non-parametric: invert the operator on the nearest training
  row's own (state, gold, dt) to get its implied constant, then apply it here.
  No assumption that an intent has one constant.
* ``copy``      — identity, the control: predicts the input unchanged. If a
  component cannot beat this, it is not doing anything.

The point of the mix is not to win rows the operator already wins — at 3dp the
operator wins every row, and a mix cannot beat 200/200. The point is to find out
**which component is load-bearing at which precision**, which the plain accuracy
number hides. So the router is fitted on the training file only, and what it
picks per intent is reported as the mix ratio before anything is graded on the
instrument set:

    --plan   fit the router, print the per-intent choice and its in-sample
             support (leave-one-out for knn, so it cannot match itself)
    --run    same router, then grade on the instrument's holdout + reference

Both write the fitted hybrid as JSON, so the "model" is a file and not a claim.

Usage:
    ./.venv/bin/python scripts/hybrid_boundary.py --plan
    ./.venv/bin/python scripts/hybrid_boundary.py --run --set all \\
        --out data/checkpoints/hybrid_boundary_3dp.json \\
        --report data/intelligence_reports/hybrid_boundary_3dp.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import probe_emergence_boundary as probe  # noqa: E402

PROCESSED = REPO_ROOT / "apps" / "backend" / "data" / "processed"
REPORTS = REPO_ROOT / "data" / "intelligence_reports"
CHECKPOINTS = REPO_ROOT / "data" / "checkpoints"

FIELD_KEYS = probe._FIELD_KEYS
FIELD_LONG = probe._FIELD_LONG

#: Cost class, cheapest first. The router breaks accuracy ties by this order, so
#: the mix does not spend a nearest-neighbour search where a dict lookup answers.
COST_ORDER = ("table", "operator", "knn", "copy")


def _rel(path: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _parse_rows(entries: Sequence[dict]) -> List[Dict[str, Any]]:
    return probe._contract_rows(entries)


def _pred_operator(
    row: Dict[str, Any], constants: Dict[Tuple[str, str], float], tau: float
) -> Optional[Dict[str, float]]:
    known = all((row["intent"], f) in constants for f in FIELD_KEYS)
    if not known:
        return None
    k = math.exp(-row["dt"] / tau)
    return {
        f: constants[(row["intent"], f)] + (row["state"][f] - constants[(row["intent"], f)]) * k
        for f in FIELD_KEYS
    }


def _pred_table(
    row: Dict[str, Any], table: Optional[Dict[str, Dict[str, float]]], tau: float
) -> Optional[Dict[str, float]]:
    if not table or row["intent"] not in table:
        return None
    k = math.exp(-row["dt"] / tau)
    target = table[row["intent"]]
    return {
        f: target[FIELD_LONG[f]] + (row["state"][f] - target[FIELD_LONG[f]]) * k for f in FIELD_KEYS
    }


class KnnIndex:
    """Nearest training rows in the six-value state space, implied-constant form."""

    def __init__(self, rows: Sequence[Dict[str, Any]], k: int = 5) -> None:
        self.rows = list(rows)
        self.k = k

    def _dist(self, a: Dict[str, float], b: Dict[str, float]) -> float:
        return math.sqrt(sum((a[f] - b[f]) ** 2 for f in FIELD_KEYS))

    def nearest(self, row: Dict[str, Any], exclude: Optional[Dict[str, Any]] = None):
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for cand in self.rows:
            if exclude is not None and cand is exclude:
                continue
            scored.append((self._dist(row["state"], cand["state"]), cand))
        if not scored:
            return []
        scored.sort(key=lambda pair: pair[0])
        return scored[: self.k]

    def predict(
        self, row: Dict[str, Any], tau: float, exclude: Optional[Dict[str, Any]] = None
    ) -> Optional[Tuple[Dict[str, float], float]]:
        """Weighted implied constant from the k nearest rows, plus the distance."""
        near = self.nearest(row, exclude=exclude)
        if not near:
            return None
        k_dt = math.exp(-row["dt"] / tau)
        weights: Dict[str, List[Tuple[float, float]]] = {f: [] for f in FIELD_KEYS}
        for dist, cand in near:
            k_c = math.exp(-cand["dt"] / tau)
            if abs(1.0 - k_c) < 1e-6:
                continue
            w = 1.0 / (1e-3 + dist)
            for f in FIELD_KEYS:
                implied = (cand["gold"][f] - cand["state"][f] * k_c) / (1.0 - k_c)
                weights[f].append((w, implied))
        pred: Dict[str, float] = {}
        for f in FIELD_KEYS:
            total = sum(w for w, _ in weights[f])
            pred[f] = sum(w * v for w, v in weights[f]) / total if total else row["state"][f]
        return {f: pred[f] + (row["state"][f] - pred[f]) * k_dt for f in FIELD_KEYS}, near[0][0]


def _pred_copy(row: Dict[str, Any]) -> Dict[str, float]:
    return {f: row["state"][f] for f in FIELD_KEYS}


def _hits(
    rows: Sequence[Dict[str, Any]],
    predict: Callable[[Dict[str, Any]], Optional[Dict[str, float]]],
    tol: float = 0.005,
    tau: float = 1.0,
) -> Dict[str, Any]:
    """Strict and rounding-aware exact match over all six fields.

    Two numbers, because at 2dp the strict one is decided by the printer: a gold
    printed to two places is already up to 0.005 from the value it stands for, so
    a strict grader charges the model for the instrument's rounding. The aware
    bound is 0.005·(1+k), the same rule the probe scores with.
    """
    hits = aware = answered = 0
    for row in rows:
        pred = predict(row)
        if pred is None:
            continue
        answered += 1
        slack = tol * (1.0 + math.exp(-row["dt"] / tau))
        if all(abs(pred[f] - row["gold"][f]) <= slack for f in FIELD_KEYS):
            aware += 1
        if all(abs(pred[f] - row["gold"][f]) <= tol for f in FIELD_KEYS):
            hits += 1
    return {
        "rows": len(rows),
        "answered": answered,
        "hits": hits,
        "hits_rounding_aware": aware,
        "coverage": round(answered / len(rows), 3) if rows else 0.0,
        "exact_of_answered": round(hits / answered, 3) if answered else 0.0,
        "exact_of_answered_rounding_aware": round(aware / answered, 3) if answered else 0.0,
        "exact_of_all": round(hits / len(rows), 3) if rows else 0.0,
    }


def _fit_constants(rows: Sequence[Dict[str, Any]]) -> Tuple[Dict[Tuple[str, str], float], float]:
    """Pick tau on training MSE, constants closed-form; no torch needed."""
    best: Optional[Tuple[float, Dict[Tuple[str, str], float]]] = None
    for tau in probe._TAU_GRID:
        constants = probe._solve_operator_constants(rows, tau)
        if not constants:
            continue
        mse = probe._operator_mse(rows, constants, tau)
        if best is None or mse < best[0]:
            best = (mse, constants, tau)  # type: ignore[assignment]
    mse, constants, tau = best  # type: ignore[misc]
    return constants, tau


def _router_plan(
    train_rows: Sequence[Dict[str, Any]],
    constants: Dict[Tuple[str, str], float],
    table: Optional[Dict[str, Dict[str, float]]],
    tau: float,
    components: Sequence[str] = COST_ORDER,
) -> Dict[str, Any]:
    """Per-intent component choice, decided on the training file only.

    ``knn`` is scored leave-one-out: a nearest-neighbour component that is
    allowed to find the query row itself scores 100% and means nothing.
    """
    index = KnnIndex(train_rows)
    by_intent: Dict[str, List[Dict[str, Any]]] = {}
    for row in train_rows:
        by_intent.setdefault(row["intent"], []).append(row)

    def score(intent: str, name: str) -> Dict[str, Any]:
        rows = by_intent[intent]
        if name == "operator":
            return _hits(rows, lambda r: _pred_operator(r, constants, tau), tau=tau)
        if name == "table":
            return _hits(rows, lambda r: _pred_table(r, table, tau), tau=tau)
        if name == "copy":
            return _hits(rows, _pred_copy, tau=tau)
        knn = index

        def pred(r: Dict[str, Any]) -> Optional[Dict[str, float]]:
            got = knn.predict(r, tau, exclude=r)
            return got[0] if got else None

        return _hits(rows, pred, tau=tau)

    plan: Dict[str, Any] = {"per_intent": {}, "components": list(components)}
    for intent in sorted(by_intent):
        stats = {name: score(intent, name) for name in components}
        usable = [n for n in components if stats[n]["coverage"] > 0 and n != "copy"]
        # accuracy first, then cost; a component that only ties the control is
        # not chosen, because it adds a dependency for no row
        best = None
        for name in components:
            if name == "copy" or name not in usable:
                continue
            key = (stats[name]["exact_of_answered"], -components.index(name))
            if best is None or key > best[0]:
                best = (key, name)
        chosen = best[1] if best else "copy"
        control = stats["copy"]["exact_of_answered"]
        if stats.get(chosen, {}).get("exact_of_answered", 0.0) <= control + 0.02:
            chosen = "copy"
        plan["per_intent"][intent] = {
            "chosen": chosen,
            "rows": len(by_intent[intent]),
            "candidates": stats,
            "control_exact": control,
        }
    counts: Dict[str, int] = {}
    for intent, entry in plan["per_intent"].items():
        counts[entry["chosen"]] = counts.get(entry["chosen"], 0) + entry["rows"]
    total = sum(counts.values()) or 1
    plan["ratio"] = {name: round(n / total, 3) for name, n in sorted(counts.items())}
    plan["rows_by_component"] = dict(sorted(counts.items()))
    return plan


def _router(plan: Dict[str, Any]) -> Callable[[str], str]:
    """Per-intent choice; an intent the router never saw gets the cost default.

    Defaulting an unknown intent to ``copy`` would hand the row to the control
    and call the resulting miss a coverage gap. The default is the cheapest
    component that can *answer* something it has not trained on — the table.
    """
    default = COST_ORDER[0]
    return lambda intent: plan["per_intent"].get(intent, {}).get("chosen", default)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--train", default=str(PROCESSED / "ai_al_round7_train.jsonl"))
    ap.add_argument("--set", default=str(PROCESSED / "mve1_emergence_boundary_3dp.json"))
    ap.add_argument("--which", default="all", choices=["holdout", "reference", "all"])
    ap.add_argument("--plan", action="store_true", help="fit the router and print the mix")
    ap.add_argument("--run", action="store_true", help="also grade on the instrument set")
    ap.add_argument(
        "--with-knn",
        action="store_true",
        help="keep the nearest-neighbour component (measured 0.019 at 3dp, 0.003 at "
        "2dp against 1.000/0.512 for table+operator; off by default)",
    )
    ap.add_argument(
        "--predict",
        default="",
        help="run the fitted decoder on one <al_in> line and print the block "
        "(empty = skip; use --checkpoint to load a saved hybrid instead of refitting)",
    )
    ap.add_argument("--checkpoint", default="", help="load a saved hybrid JSON for --predict")
    ap.add_argument(
        "--response-from",
        default="",
        help="write the *response* half of the line with this token checkpoint and the "
        "block with the fitted operator. The two halves are separate problems: the "
        "block is a linear relaxation (out = target + (in - target) * exp(-dt/tau)), "
        "which the operator solves exactly, while the response is free text. Asking "
        "one SNN for both is what pinned free-running exactness at 0/20.",
    )
    ap.add_argument("--out", default=str(CHECKPOINTS / "hybrid_boundary.json"))
    ap.add_argument("--report", default=str(REPORTS / "hybrid_boundary.json"))
    args = ap.parse_args(argv)
    if not (args.plan or args.run or args.predict):
        args.plan = True
    components = tuple(n for n in COST_ORDER if n != "knn" or args.with_knn)

    started = time.time()
    table_pair = probe._contract_table()
    table = table_pair[0] if table_pair else None
    index: Optional[KnnIndex] = None
    plan: Dict[str, Any] = {"per_intent": {}, "ratio": {}, "components": list(components)}

    saved = None
    if args.checkpoint and Path(args.checkpoint).is_file():
        saved = json.loads(Path(args.checkpoint).read_text(encoding="utf-8"))
        tau = float(saved["tau"])
        constants = {
            (key.rsplit("/", 1)[0], key.rsplit("/", 1)[1]): float(value)
            for key, value in saved["constants"].items()
        }
        plan["per_intent"] = {i: {"chosen": c} for i, c in saved.get("router", {}).items()}
        plan["ratio"] = saved.get("mix_ratio", {})
        chosen_of = _router(plan)
        print(f"loaded {args.checkpoint}: tau={tau} intents={sorted(plan['per_intent'])}")
        print(f"mix ratio: {plan['ratio']}")
        if args.run:
            raise SystemExit("--checkpoint is for --predict; --run refits on the training file")
    else:
        train_pairs = probe._train_value_pairs(Path(args.train))
        train_rows = _parse_rows([{"prompt": p, "gold": g} for p, g, _i in train_pairs])
        if not train_rows:
            raise SystemExit(f"no training rows in {args.train}")
        constants, tau = _fit_constants(train_rows)
        index = KnnIndex(train_rows)
        plan = _router_plan(train_rows, constants, table, tau, components=components)
        chosen_of = _router(plan)
        print(f"train rows={len(train_rows)} intents={len(plan['per_intent'])} tau={tau}")
        print(f"mix ratio: {plan['ratio']}")
        for intent, entry in sorted(plan["per_intent"].items()):
            stats = entry["candidates"]
            line = " ".join(
                f"{name}={stats[name]['exact_of_answered']:.2f}"
                f"/{stats[name]['exact_of_answered_rounding_aware']:.2f}"
                for name in components
                if name in stats
            )
            print(f"  {intent:<18} n={entry['rows']:<5} -> {entry['chosen']:<9} [{line}]")

    def component_pred(name: str, row: Dict[str, Any]) -> Optional[Dict[str, float]]:
        if name == "table":
            return _pred_table(row, table, tau)
        if name == "operator":
            return _pred_operator(row, constants, tau)
        if name == "knn":
            if index is None:
                return None
            got = index.predict(row, tau)
            return got[0] if got else None
        return _pred_copy(row)

    def cascade(row: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Router first; then the rest in cost order as a fallback.

        The router is the *declared* mix. A cascade on top of it is what makes
        the thing robust: if the chosen component has nothing to say about a row
        (a constant missing, a table entry absent), the next cheapest one gets
        the row instead of the row being dropped — which is how a component's
        coverage turns into a failure rate that nobody intended.
        """
        order = [chosen_of(row["intent"])] + [
            n for n in COST_ORDER if n != chosen_of(row["intent"])
        ]
        for name in order:
            pred = component_pred(name, row)
            if pred is not None:
                return pred
        return None

    if args.predict:
        line = args.predict
        state = probe._parse_input_line(line)
        row: Dict[str, Any] = {
            "state": {f: float(state[f]) for f in FIELD_KEYS},
            "dt": float(state["dt"]),
            "intent": str(state.get("intent") or ""),
            "gold": {},
        }
        pred = cascade(row)
        if pred is None:
            print("no component could answer")
        else:
            block = "<al_out> " + " ".join(f"{f}={pred[f]:.3f}" for f in FIELD_KEYS)
            block += f" mode={state.get('mode', 'neutral')} intent={row['intent']}"
            print(f"intent={row['intent']} dt={row['dt']} via={chosen_of(row['intent'])}")
            if args.response_from:
                from ai.ed3n.token_snn import TokenSNN

                model = TokenSNN.load(args.response_from, map_location="cpu")
                prompt = line.split("|", 1)[-1].strip()
                # the model may keep writing into the block; the block is the
                # operator's, so the response stops where <al_out> starts
                text = model.generate(prompt, max_new=48).split("<al_out>")[0].strip()
                print("<response> " + text)
            print(block)
            constants_here = {
                f: constants[(row["intent"], f)]
                for f in FIELD_KEYS
                if (row["intent"], f) in constants
            }
            if constants_here:
                print("constants: " + " ".join(f"{f}={constants_here[f]:.4f}" for f in FIELD_KEYS))

    report: Dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "interface": "value (six numbers), not text",
        "train": _rel(args.train) if not saved else saved.get("train", ""),
        "set": _rel(args.set),
        "tau": tau,
        "constants": {f"{i}/{f}": round(v, 5) for (i, f), v in sorted(constants.items())},
        "table_intents": sorted(table) if table else [],
        "plan": plan,
    }

    if args.run:
        payload = json.loads(Path(args.set).read_text(encoding="utf-8"))
        entries = probe._select(payload, args.which)
        rows = _parse_rows(entries)
        holdout = [r for r in rows if _is_holdout(entries, r)]
        print(f"\ninstrument rows={len(rows)} (holdout {len(holdout)})")

        alone = {
            name: _hits(rows, lambda r, n=name: component_pred(n, r), tau=tau)
            for name in COST_ORDER
        }
        routed = _hits(rows, cascade, tau=tau)
        # leave-one-out on the instrument set: how much each component is missed
        ablation: Dict[str, Any] = {}
        for name in components:
            if name == "copy":
                continue

            def pred_wo(row: Dict[str, Any], skip: str = name) -> Optional[Dict[str, float]]:
                """The same cascade with one component taken out of the order."""
                first = chosen_of(row["intent"])
                order = [first] + [n for n in components if n != first and n != "copy"]
                order = [n for n in order if n != skip] + ["copy"]
                for candidate in order:
                    got = component_pred(candidate, row)
                    if got is not None:
                        return got
                return None

            ablation[name] = _hits(rows, pred_wo, tau=tau)

        coverage: Dict[str, int] = {}
        for row in rows:
            chosen = chosen_of(row["intent"])
            coverage[chosen] = coverage.get(chosen, 0) + 1

        report.update(
            {
                "instrument": {
                    "rows": len(rows),
                    "holdout_rows": len(holdout),
                    "alone": alone,
                    "hybrid": routed,
                    "ablation_without": ablation,
                    "coverage_by_component": coverage,
                    "ratio_on_instrument": {
                        k: round(v / len(rows), 3) for k, v in sorted(coverage.items())
                    },
                }
            }
        )
        print("\ncomponent alone (hits / all rows, coverage):")
        for name in components:
            s = alone[name]
            print(
                f"  {name:<9} {s['hits']:>4}/{s['rows']:<4} exact={s['exact_of_all']:.3f} "
                f"coverage={s['coverage']:.3f}"
            )
        print(
            f"  {'hybrid':<9} {routed['hits']:>4}/{routed['rows']:<4} "
            f"exact={routed['exact_of_all']:.3f} coverage={routed['coverage']:.3f}"
        )
        print("\nablation (hybrid without X):")
        for name, s in ablation.items():
            print(f"  -{name:<8} {s['hits']:>4}/{s['rows']:<4} exact={s['exact_of_all']:.3f}")

    report["elapsed_seconds"] = round(time.time() - started, 1)

    # a --predict run must not litter the checkpoint directory with a model it
    # did not fit; it only writes when an output path was actually asked for
    if args.predict and args.out == str(CHECKPOINTS / "hybrid_boundary.json"):
        print("(predict-only run: nothing written)")
        return 0

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "kind": "hybrid-boundary-decoder",
                "tau": tau,
                "constants": {f"{i}/{f}": v for (i, f), v in sorted(constants.items())},
                "router": {k: v["chosen"] for k, v in plan["per_intent"].items()},
                "mix_ratio": plan["ratio"],
                "note": "table comes from the contract at runtime; only constants/router are fitted",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    rep = Path(args.report)
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nwrote {out}\nwrote {rep}")
    return 0


def _is_holdout(entries: Sequence[dict], row: Dict[str, Any]) -> bool:
    for entry in entries:
        state = probe._parse_input_line(str(entry.get("prompt", "")))
        if (
            state.get("intent") == row["intent"]
            and abs(float(state.get("dt", -1)) - row["dt"]) < 1e-9
        ):
            return probe._set_label(entry) == "holdout"
    return False


if __name__ == "__main__":
    raise SystemExit(main())
