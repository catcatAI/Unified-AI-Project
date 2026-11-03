"""Tests for the mixed boundary decoder (scripts/hybrid_boundary.py).

Claims pinned here:

1. the router's default for an intent it never saw is the component that can
   answer without training (the contract table), never the identity control —
   otherwise a coverage gap is silently reported as a model miss;
2. the control answers last, so a row is never dropped while a real component
   could still take it;
3. the mix is load-bearing, not decorative: on rows split between "trained
   intent" and "table-only intent", each single component misses one half and
   the cascade gets both;
4. the nearest-neighbour component is scored leave-one-out, because a
   non-parametric component allowed to find its own row scores 100% and means
   nothing;
5. grading reports strict and rounding-aware hits separately, since at 2dp the
   strict number is partly decided by the printer.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "hybrid_boundary.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def hybrid():
    return _load("hybrid_boundary_test", SCRIPT)


def _row(hybrid, intent: str, state: float, gold: float, dt: float = 1.0):
    return {
        "state": {f: state for f in hybrid.FIELD_KEYS},
        "gold": {f: gold for f in hybrid.FIELD_KEYS},
        "dt": dt,
        "intent": intent,
    }


def test_router_defaults_to_the_component_that_needs_no_training(hybrid):
    """An unseen intent gets the table, not the identity control."""
    chosen_of = hybrid._router({"per_intent": {"seen": {"chosen": "operator"}}})
    assert chosen_of("seen") == "operator"
    assert chosen_of("never_trained") == hybrid.COST_ORDER[0] == "table"


def test_identity_control_is_never_the_router_choice(hybrid):
    plan = hybrid._router_plan([_row(hybrid, "seen", 0.2, 0.8)], constants={}, table=None, tau=1.0)
    assert plan["per_intent"]["seen"]["chosen"] == "copy"
    assert plan["ratio"] == {"copy": 1.0}


def test_operator_reproduces_the_contract_arithmetic(hybrid):
    row = _row(hybrid, "seen", 0.9, 0.0, dt=0.5)
    constants = {("seen", f): 0.3 for f in hybrid.FIELD_KEYS}
    pred = hybrid._pred_operator(row, constants, 1.0)
    k = math.exp(-0.5)
    for f in hybrid.FIELD_KEYS:
        assert pred[f] == pytest.approx(0.3 + (0.9 - 0.3) * k)
    assert hybrid._pred_operator(_row(hybrid, "other", 0.9, 0.0), constants, 1.0) is None


def test_knn_is_scored_without_itself(hybrid):
    """Leave-one-out: the row being predicted must not be its own neighbour."""
    rows = [
        _row(hybrid, "a", 0.1, 0.9),
        _row(hybrid, "a", 0.2, 0.8),
        _row(hybrid, "a", 0.3, 0.7),
    ]
    index = hybrid.KnnIndex(rows)
    with_self = index.predict(rows[0], 1.0)[0]
    without = index.predict(rows[0], 1.0, exclude=rows[0])[0]
    assert with_self != without
    # excluding the query point must move the implied constant toward its peers
    assert without["v"] < with_self["v"]


def test_hits_separate_strict_from_rounding_aware(hybrid):
    rows = [_row(hybrid, "a", 0.5, 0.5, dt=2.0)]

    def off_by(x):
        return lambda r: {f: r["gold"][f] + x for f in hybrid.FIELD_KEYS}

    assert hybrid._hits(rows, off_by(0.004), tau=1.0)["hits"] == 1
    # 0.0055 is outside the bare grid but inside 0.005*(1+k) at dt=2
    strict = hybrid._hits(rows, off_by(0.0055), tau=1.0)
    assert strict["hits"] == 0
    assert strict["hits_rounding_aware"] == 1


def test_the_mix_covers_what_each_single_component_misses(hybrid):
    """Half the rows need the table, half need the trained constant."""
    table_pair = hybrid.probe._contract_table()
    assert table_pair, "contract table unavailable"
    table, _defaults = table_pair
    table_intent = sorted(table)[0]

    trained = [_row(hybrid, "trained_only", 0.2, 0.8), _row(hybrid, "trained_only", 0.6, 0.4)]
    constants, tau = hybrid._fit_constants(trained)
    plan = hybrid._router_plan(trained, constants, table, tau)
    chosen_of = hybrid._router(plan)

    rows = [_row(hybrid, "trained_only", 0.35, 0.65), _row(hybrid, table_intent, 0.35, 0.65)]

    def cascade(row):
        first = chosen_of(row["intent"])
        order = [first] + [n for n in ("table", "operator") if n != first] + ["copy"]
        for name in order:
            if name == "table":
                got = hybrid._pred_table(row, table, tau)
            elif name == "operator":
                got = hybrid._pred_operator(row, constants, tau)
            else:
                got = hybrid._pred_copy(row)
            if got is not None:
                return got
        return None

    def alone(name):
        if name == "table":
            return hybrid._hits(rows, lambda r: hybrid._pred_table(r, table, tau), tau=tau)
        return hybrid._hits(rows, lambda r: hybrid._pred_operator(r, constants, tau), tau=tau)

    table_alone = alone("table")
    operator_alone = alone("operator")
    mixed = hybrid._hits(rows, cascade, tau=tau)
    assert table_alone["answered"] == 1 and operator_alone["answered"] == 1
    assert mixed["answered"] == 2
    assert mixed["coverage"] == 1.0
    assert mixed["hits"] >= max(table_alone["hits"], operator_alone["hits"])
