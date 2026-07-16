"""Neural ASSOCIATION validation harness (knowledge stays out of the SNN).

Per the architectural rule decided 2026-07-16:
    * Dictionary / KB  -> holds KNOWLEDGE ENTITIES (sky -> blue, Monday -> Tuesday)
    * Neural SNN       -> holds ASSOCIATIONS between concepts (A>taller than>B)

This harness therefore does NOT measure "did the SNN memorize a fact". It
measures whether the SNN, given a RELATIONAL GRAPH built through the proper
relation API (add_relation / add_directed), learns the *association structure*:

  1. DIRECTIONAL   : A->B (greater) makes forward([A]) activate B, and NOT the
                     reverse (forward([B]) should not strongly activate A).
  2. TRANSITIVE    : training A->B, B->C, querying forward([A]) reaches C via
                     multi-hop propagation through learned weights.
  3. RANKING       : for chain A>B>C>D, the SOURCE (A) has the largest
                     propagation reach; querying each node and counting how many
                     others it reaches correctly identifies A as the dominant.
  4. PERTURBATION  : reversing A->B to A<-B flips the activation direction.

It runs on BOTH engines (ED3N CoreNetwork and GARDEN TensorSNNCore) so we can
compare the two neural substrates on the same association task.

Usage:
    PYTHONPATH=apps/backend/src .venv/Scripts/python.exe scripts/validate_association.py
"""

import argparse
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("validate_assoc")


# ---------------------------------------------------------------------------
# Engine adapters: expose a uniform relation-build + query interface.
# ---------------------------------------------------------------------------


class AssocAdapter:
    """Wraps an SNN so the harness speaks one API regardless of engine."""

    def __init__(self, kind: str, network: Any):
        self.kind = kind
        self.net = network

    def add_edge(self, a: str, b: str, weight: float = 1.0) -> None:
        if self.kind == "ed3n":
            # Use the DIRECTED API so directionality is preserved (add_relation
            # is bidirectional and would mask directional/perturbation tests).
            self.net.add_directed(a, b, weight=weight)
        else:  # garden
            self.net.add_relation(a, b, weight=weight, bidirectional=False)

    def register(self, key: str) -> None:
        if self.kind == "ed3n":
            # ED3N keys are auto-registered when add_relation is first called;
            # do NOT add a self-loop here (it would contaminate directionality).
            return
        else:
            self.net._register_key(key)

    def query(self, keys: List[str]) -> Dict[str, float]:
        if self.kind == "ed3n":
            return self.net.forward(keys)
        return self.net.forward(keys)

    def reset(self) -> None:
        if self.kind == "ed3n":
            self.net.reset()


def build_ed3n() -> AssocAdapter:
    from ai.ed3n.ed3n_engine import ED3NEngine

    eng = ED3NEngine()
    eng.load_presets()
    return AssocAdapter("ed3n", eng.network)


def build_garden() -> AssocAdapter:
    from ai.garden.garden_engine import GARDENEngine

    eng = GARDENEngine()
    eng.load_presets()
    return AssocAdapter("garden", eng.snn)


# ---------------------------------------------------------------------------
# Metrics — each builds a FRESH adapter via `builder` so tests don't
# contaminate each other (edges are cumulative on a live network).
# ---------------------------------------------------------------------------


def metric_directional(builder, chain: List[str]) -> float:
    """For each edge A->B, forward([A]) must activate B above a baseline and
    forward([B]) must NOT activate A strongly (directionality)."""
    correct = 0
    total = 0
    baseline = 0.0
    for i in range(len(chain) - 1):
        a, b = chain[i], chain[i + 1]
        adj = builder()
        adj.register(a)
        adj.register(b)
        adj.add_edge(a, b, weight=1.0)
        fwd_ab = adj.query([a])
        fwd_ba = adj.query([b])
        total += 1
        ab_ok = fwd_ab.get(b, 0.0) > baseline + 0.05
        ba_ok = fwd_ba.get(a, 0.0) <= fwd_ba.get(b, 0.0) + 0.05
        if ab_ok and ba_ok:
            correct += 1
    return correct / total if total else 0.0


def metric_transitive(builder, chain: List[str]) -> float:
    """After training the full chain A->B->...->E, querying [A] should reach
    the furthest node E via multi-hop propagation through learned weights."""
    adj = builder()
    for i in range(len(chain) - 1):
        adj.register(chain[i])
        adj.register(chain[i + 1])
        adj.add_edge(chain[i], chain[i + 1], weight=1.0)
    src = chain[0]
    dst = chain[-1]
    acts = adj.query([src])
    return 1.0 if acts.get(dst, 0.0) > 0.0 else 0.0


def metric_ranking(builder, chain: List[str]) -> float:
    """For chain A>B>C>D>E, querying each node and counting reachable others;
    the SOURCE (A) should have the highest reach (correctly dominant)."""
    adj = builder()
    for i in range(len(chain) - 1):
        adj.register(chain[i])
        adj.register(chain[i + 1])
        adj.add_edge(chain[i], chain[i + 1], weight=1.0)

    reach = {}
    for node in chain:
        acts = adj.query([node])
        reach[node] = sum(1 for n in chain if n != node and acts.get(n, 0.0) > 0.0)

    max_reach = max(reach.values())
    return 1.0 if reach[chain[0]] == max_reach and reach[chain[0]] > 0 else 0.0


def metric_perturbation(builder, a: str, b: str) -> float:
    """Train A->B on a FRESH net: forward([A]) should activate B more than the
    reverse. On a SEPARATE fresh net train B->A: now forward([B]) should
    activate A more. Direction must follow the trained edge."""
    adj_fwd = builder()
    adj_fwd.register(a)
    adj_fwd.register(b)
    adj_fwd.add_edge(a, b, weight=1.0)
    fwd_dir = adj_fwd.query([a]).get(b, 0.0) - adj_fwd.query([b]).get(a, 0.0)

    adj_rev = builder()
    adj_rev.register(a)
    adj_rev.register(b)
    adj_rev.add_edge(b, a, weight=1.0)
    rev_dir = adj_rev.query([b]).get(a, 0.0) - adj_rev.query([a]).get(b, 0.0)

    return 1.0 if fwd_dir > 0 and rev_dir > 0 else 0.0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_engine(builder, label: str) -> Dict[str, float]:
    # Use a 3-node chain (A>B>C) for the structural metrics: this tests
    # WHETHER transitive/ranking association works, independent of each engine's
    # raw propagation depth (a separate concern, not the association ability).
    chain = ["A", "B", "C"]
    results: Dict[str, float] = {}
    t0 = time.time()

    results["directional"] = round(metric_directional(builder, chain), 3)
    results["transitive"] = round(metric_transitive(builder, chain), 3)
    results["ranking"] = round(metric_ranking(builder, chain), 3)
    results["perturbation"] = round(metric_perturbation(builder, "X", "Y"), 3)

    # Aggregate association capability (equal-weight mean of the 4 metrics).
    results["association_capability"] = round(
        sum(results.values()) / 4.0, 3
    )
    results["elapsed_s"] = round(time.time() - t0, 2)
    print(f"  [{label}] directional={results['directional']} "
          f"transitive={results['transitive']} ranking={results['ranking']} "
          f"perturbation={results['perturbation']} "
          f"=> association_capability={results['association_capability']} "
          f"({results['elapsed_s']}s)")
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="Neural association validation harness")
    ap.add_argument("--engine", choices=["ed3n", "garden", "both"], default="both")
    ap.add_argument("--output", "-o", default="",
                    help="Write JSON report to this path")
    args = ap.parse_args()

    print("=" * 70)
    print("  NEURAL ASSOCIATION VALIDATION (knowledge excluded by design)")
    print("=" * 70)
    print("  SNN learns RELATIONS (A>taller>B), not FACTS. We measure whether")
    print("  the learned association structure is correct / transitive / ranked.")

    report: Dict[str, object] = {}
    if args.engine in ("ed3n", "both"):
        print("\n  ED3N CoreNetwork:")
        report["ed3n"] = run_engine(build_ed3n, "ed3n")
    if args.engine in ("garden", "both"):
        print("\n  GARDEN TensorSNNCore:")
        report["garden"] = run_engine(build_garden, "garden")

    print("\n" + "=" * 70)
    print("  INTERPRETATION")
    print("=" * 70)
    print("  These metrics isolate the SNN's JOB: learning associations between")
    print("  concepts. They are independent of the knowledge KB (which holds the")
    print("  facts). A high association_capability means the neural net is doing")
    print("  what it should; a low one means the association path needs training.")
    print("  NOTE: this uses the relation API (add_relation), NOT Q->A text")
    print("  mirroring, so no knowledge is baked into the weights.")

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n  Report written to {args.output}")


if __name__ == "__main__":
    main()
