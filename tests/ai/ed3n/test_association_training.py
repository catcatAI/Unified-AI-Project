# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [C] [L0]
# =============================================================================
"""
Regression tests for training-domain routing and SNN association training.

Verifies:
- The ``association`` domain is owned by the ED3N SNN (not GARDEN, which trains
  associations=False and would discard relational signal).
- ``association`` is included in the ED3N SNN training domains so relational
  samples actually build association edges in the neural graph (preserving
  max association, not just knowledge-in-dict).
"""

import asyncio

import pytest

from ai.core.training_coordinator import DOMAIN_OWNERSHIP, TrainingCoordinator
from ai.ed3n.core_network import CoreNetwork, RelationType
from ai.ed3n.ed3n_engine import ED3NEngine
from ai.ed3n.ed3n_trainer import ED3NTrainer
from ai.ed3n.training_types import TrainingBatch, TrainingExample


def test_association_domain_routes_to_ed3n():
    coord = TrainingCoordinator()
    assert "association" in DOMAIN_OWNERSHIP
    assert DOMAIN_OWNERSHIP["association"] == "ed3n"
    assert asyncio.run(coord.assign_domain("association")) == "ed3n"


def test_association_samples_train_snn_edges():
    """A relational chain (A>taller>B, B>taller>C) must build association edges
    in the SNN, proving the association domain populates the neural graph."""
    eng = ED3NEngine()
    eng.load_presets()
    before = eng.network._conn_count
    samples = [
        {"input": "Alice is taller than Bob.", "output": "Bob is shorter than Alice.", "domain": "association"},
        {"input": "Bob is taller than Carol.", "output": "Carol is shorter than Bob.", "domain": "association"},
        {"input": "Carol is taller than Dave.", "output": "Dave is shorter than Carol.", "domain": "association"},
    ]
    examples = []
    for s in samples:
        ik = list(set(eng.dictionary.encode(s["input"].lower())))
        ok_ = list(set(eng.dictionary.encode(s["output"].lower())))
        if not ik or not ok_:
            continue
        pairs = [(a, "mapping", b) for a in ik for b in ok_]
        examples.append(TrainingExample(
            input_text=s["input"], expected_output=s["output"],
            input_keys=ik, output_keys=ok_, relation_pairs=pairs,
            confidence=0.8, metadata={"domain": "association"}))
    trainer = ED3NTrainer(eng)
    trainer.train_step(TrainingBatch(examples=examples, batch_id="assoc"))
    assert eng.network._conn_count > before, "association samples must add SNN edges"
