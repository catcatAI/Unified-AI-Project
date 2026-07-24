"""Three-column honest validation harness for ED3N / GARDEN.

The point of this harness is to answer the question:
    "If we remove the deterministic engines, does the neural network still
     work on its own?"

We measure three columns over the SAME in-repo datasets:

  HYBRID  (normal)        : deterministic stages (calculator / KB / symbolic
                            reasoner / relational-chain) + SNN all enabled.
  DETERMINISTIC-ONLY      : SNN forward + decode disabled; only the
                            deterministic engines may answer.
  SNN-ONLY                : all deterministic stages disabled; only the
                            SNN (neural) path may answer.

Then we report, per dataset and engine:
  - the three accuracies,
  - DETERMINISTIC-CARRY = HYBRID - SNN-ONLY  (how much the system relies on
    deterministic engines — this is the honest "neural contribution delta"),
  - and note that SNN-ONLY is also handicapped because knowledge lives in the
    deterministic KB, not in SNN weights (a known architectural limitation,
    not a model-capability verdict).

Usage:
    PYTHONPATH=apps/backend/src .venv/Scripts/python.exe scripts/validate_three_column.py
"""

import argparse
import csv
import json
import logging
import os
import re
import time
from typing import Callable, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("validate")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "apps", "backend", "data", "raw_datasets")

# ---------------------------------------------------------------------------
# Dataset loaders (in-repo only — no external download, offline-capable)
# ---------------------------------------------------------------------------


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_datasets() -> Dict[str, List[Tuple[str, str]]]:
    """Return {domain: [(input, expected_output), ...]} from in-repo files."""
    out: Dict[str, List[Tuple[str, str]]] = {}

    # Reasoning (relational chains) — the big one (11k).
    rp = os.path.join(DATA_DIR, "reasoning_train.json")
    if os.path.exists(rp):
        data = _load_json(rp)
        out["reasoning"] = [(d["input"], d["output"]) for d in data]

    # Arithmetic test (2k).
    cp = os.path.join(DATA_DIR, "arithmetic_test_dataset.csv")
    if os.path.exists(cp):
        rows=[]
        with open(cp, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows.append((row["problem"], row["answer"]))
        out["math"] = rows

    # Logic test (200).
    lp = os.path.join(DATA_DIR, "logic_test.json")
    if os.path.exists(lp):
        data = _load_json(lp)
        out["logic"] = [
            (d["proposition"], str(d["answer"]).lower()) for d in data
        ]

    return out


# ---------------------------------------------------------------------------
# Answer scoring
# ---------------------------------------------------------------------------


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def score(output: Optional[str], expected: str) -> bool:
    if not output:
        return False
    o = _normalize(output)
    e = _normalize(expected)
    if not e:
        return False
        # Contains-match: expected substring must appear in output.
    return e in o


# ---------------------------------------------------------------------------
# Column modes -> monkeypatch functions
# ---------------------------------------------------------------------------

def _stub_return_none(self, *args, **kwargs):
    return None


def apply_mode(engine, mode: str, engine_kind: str) -> None:
    """Disable stages according to the column mode.

    mode in {"hybrid", "deterministic", "snn"}.
    """
    if mode == "hybrid":
        return

    if engine_kind == "ed3n":
        if mode == "snn":
            # Disable all deterministic stages -> force neural path.
            for name in (
                "_stage_reflex",
                "_stage_math",
                "_stage_reasoning",
                "_stage_knowledge",
                "_stage_chain_reasoning",
            ):
                setattr(engine, name, _stub_return_none)
        elif mode == "deterministic":
            # Disable the neural forward + decode so deterministic answers win.
            engine._stage_network_forward = lambda *a, **k: None
            engine._stage_anchored_decode = _stub_return_none
            # Cycling/validate also lean on the network; neutralize them.
            engine._stage_cycling = _stub_return_none
            engine._stage_validate = _stub_return_none
    else:  # garden
        if mode == "snn":
            for name in (
                "_try_math_eval",
                "_try_reasoning",
                "_try_chain_reasoning",
                "_try_knowledge",
            ):
                if hasattr(engine, name):
                    setattr(engine, name, _stub_return_none)
                    # Reflex is a method on the engine itself.
            engine.reflex.match = lambda text: None
        elif mode == "deterministic":
            # Disable the SNN + anchored decode; keep deterministic stages.
            engine._single_step_process = lambda *a, **k: None
            engine.snn.forward = lambda *a, **k: None


def run_column(engine, mode: str, engine_kind: str,
               cases: List[Tuple[str, str]]) -> Tuple[int, int, float]:
    apply_mode(engine, mode, engine_kind)
    passed=0
    total = len(cases)
    t0 = time.time()
    for inp, expected in cases:
        try:
            out = engine.process(inp)
        except Exception as e:
            logger.debug("process error in %s/%s: %s", engine_kind, mode, e)
            out=""
        if score(out, expected):
            passed += 1
    elapsed = time.time() - t0
    return passed, total, (passed / total if total else 0.0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description="Three-column validation harness")
    ap.add_argument("--engine", choices=["ed3n", "garden", "both"], default="both")
    ap.add_argument("--sample", type=int, default=150,
                    help="Max cases sampled per domain (default 150; statistical "
                         "margin <8%%). Use --full to run every case.")
    ap.add_argument("--full", action="store_true",
                    help="Run the entire in-repo dataset (can be slow: 11k "
                         "reasoning cases x 3 columns).")
    ap.add_argument("--output", "-o", default="",
                    help="Write JSON report to this path")
    args = ap.parse_args()

    datasets = load_datasets()
    if not args.full:
        for k in datasets:
            if len(datasets[k]) > args.sample:
                # Deterministic stratified-ish sample: take evenly spaced cases.
                step = len(datasets[k]) // args.sample
                datasets[k] = datasets[k][::step][: args.sample]

    print("=" * 70)
    print("  THREE-COLUMN VALIDATION HARNESS (in-repo datasets, offline)")
    print("=" * 70)
    for dom, cases in datasets.items():
        print(f"  {dom:12s}: {len(cases)} cases")

    CKPT_DIR = os.path.join(ROOT, "data", "checkpoints")

    engines_to_run=[]
    if args.engine in ("ed3n", "both"):
        from ai.ed3n.ed3n_engine import ED3NEngine

        e = ED3NEngine()
        ed3n_ckpt = os.path.join(CKPT_DIR, "ed3n_full.json")
        if os.path.exists(ed3n_ckpt):
            e.load(ed3n_ckpt)
            logger.info("Loaded trained ED3N from %s", ed3n_ckpt)
        else:
            e.load_presets()
            logger.info("No trained ED3N checkpoint; using presets")
        try:
            e.process("warmup 1 + 1")
        except Exception as exc:
            logger.debug("Warmup failed (benign): %s", exc)
        engines_to_run.append(("ed3n", e))
    if args.engine in ("garden", "both"):
        from ai.garden.garden_engine import GARDENEngine

        e = GARDENEngine()
        garden_ckpt = os.path.join(CKPT_DIR, "garden_checkpoint")
        if os.path.isdir(garden_ckpt):
            e.load(garden_ckpt)
            logger.info("Loaded trained GARDEN from %s", garden_ckpt)
        else:
            e.load_presets()
            logger.info("No trained GARDEN checkpoint; using presets")
        try:
            e.process("warmup 1 + 1")
        except Exception as exc:
            logger.debug("Warmup failed (benign): %s", exc)
        engines_to_run.append(("garden", e))

    report: Dict[str, object] = {"datasets": {k: len(v) for k, v in datasets.items()},
                                 "engines": {}}

    for kind, engine in engines_to_run:
        print(f"\n{'=' * 70}")
        print(f"  ENGINE: {kind}")
        print(f"{'=' * 70}")
        eng_report: Dict[str, object] = {}
        header = f"  {'domain':12s} | {'HYBRID':>7s} | {'DET-ONLY':>8s} | {'SNN-ONLY':>8s} | {'DET-CARRY':>9s}"
        print(header)
        print("  " + "-" * 62)
        dom_summary: Dict[str, Dict[str, float]] = {}
        for dom, cases in datasets.items():
            # Save original methods, apply mode, run, restore.
            # This avoids re-loading sentence-transformers 9 times.
            originals = {}
            if kind == "ed3n":
                patch_names = ["_stage_reflex", "_stage_math", "_stage_reasoning",
                               "_stage_knowledge", "_stage_chain_reasoning",
                               "_stage_network_forward", "_stage_anchored_decode",
                               "_stage_cycling", "_stage_validate"]
            else:
                patch_names = ["_try_math_eval", "_try_reasoning", "_try_chain_reasoning",
                               "_try_knowledge", "_single_step_process"]
            for name in patch_names:
                if hasattr(engine, name):
                    originals[name] = getattr(engine, name)

            # Save reflex.match for garden
            if kind == "garden":
                originals["reflex_match"] = engine.reflex.match

            hp, ht, ha = run_column(engine, "hybrid", kind, cases)
            # Restore before next column
            for name, val in originals.items():
                if name == "reflex_match":
                    engine.reflex.match = val
                else:
                    setattr(engine, name, val)

            dp, dt, da = run_column(engine, "deterministic", kind, cases)
            for name, val in originals.items():
                if name == "reflex_match":
                    engine.reflex.match = val
                else:
                    setattr(engine, name, val)

            sp, st, sa = run_column(engine, "snn", kind, cases)
            for name, val in originals.items():
                if name == "reflex_match":
                    engine.reflex.match = val
                else:
                    setattr(engine, name, val)

            carry = ha - sa  # how much hybrid beats pure-SNN
            dom_summary[dom] = {
                "hybrid": round(ha * 100, 2),
                "deterministic": round(da * 100, 2),
                "snn_only": round(sa * 100, 2),
                "det_carry": round(carry * 100, 2),
                "n": len(cases),
            }
            print(f"  {dom:12s} | {hp:5d}/{ht:<2d} | {dp:5d}/{dt:<2d} | {sp:5d}/{st:<2d} | {carry*100:7.1f}%")

        eng_report["domains"] = dom_summary
        report["engines"][kind] = eng_report

        # Aggregate over all domains (weighted by case count).
        tot = sum(d["n"] for d in dom_summary.values())
        agg={"hybrid": 0.0, "deterministic": 0.0, "snn_only": 0.0}
        for d in dom_summary.values():
            w = d["n"] / tot
            agg["hybrid"] += d["hybrid"] * w
            agg["deterministic"] += d["deterministic"] * w
            agg["snn_only"] += d["snn_only"] * w
        agg["det_carry"] = agg["hybrid"] - agg["snn_only"]
        eng_report["aggregate"] = {k: round(v, 2) for k, v in agg.items()}
        print("  " + "-" * 62)
        print(f"  AGGREGATE (weighted) | HYBRID {agg['hybrid']:.1f}% | "
              f"DET-ONLY {agg['deterministic']:.1f}% | SNN-ONLY {agg['snn_only']:.1f}% | "
              f"DET-CARRY {agg['det_carry']:.1f}%")

    print("\n" + "=" * 70)
    print("  INTERPRETATION")
    print("=" * 70)
    print("  DET-CARRY = HYBRID - SNN-ONLY = how much the system depends on")
    print("  deterministic engines (calculator / KB / symbolic reasoner / chain).")
    print("  SNN-ONLY is ALSO handicapped: knowledge lives in the deterministic")
    print("  KB, not in SNN weights — a known architectural limit, not a verdict")
    print("  on SNN capacity. A low SNN-ONLY means 'knowledge was never trained")
    print("  into the neural weights', which is the real next-step finding.")

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n  Report written to {args.output}")


if __name__ == "__main__":
    main()
