"""Contrastive pilot gate (R9): real updates, deterministic, learns.

Runs scripts/train_contrastive_pilot.py::main() (~0.3s): asserts exit 0,
i.e. final loss strictly below initial (no simulated arithmetic allowed).
Determinism is pinned by seed 42 + md5 W init inside the engine.
"""

import importlib.util
import os


def load_pilot():
    path = os.path.join(os.path.dirname(__file__), "..", "scripts", "train_contrastive_pilot.py")
    spec = importlib.util.spec_from_file_location("train_contrastive_pilot", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pilot_learns_and_exits_zero():
    mod = load_pilot()
    assert mod.main() == 0


def test_pilot_deterministic_history():
    import numpy as np

    import sys

    sys.path.insert(
        0,
        os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"),
    )
    from ai.multimodal.shared_latent_space import SharedLatentSpace

    histories = []
    for _ in range(2):
        np.random.seed(42)
        pos, neg = [], []
        for _ in range(100):
            base = np.random.randn(64).astype(np.float32)
            pos.append(
                (
                    base + np.random.randn(64).astype(np.float32) * 0.5,
                    base + np.random.randn(64).astype(np.float32) * 0.5,
                )
            )
            neg.append(
                (
                    np.random.randn(64).astype(np.float32),
                    np.random.randn(64).astype(np.float32),
                )
            )
        sls = SharedLatentSpace()
        sls.register_modality("vision", 64)
        sls.register_semantic_modality("vision", 64)
        histories.append(
            sls.semantic_contrastive_train(
                pos, neg, modality="vision_semantic", epochs=3, lr=0.05, margin=0.5
            )["history"]
        )
    assert histories[0] == histories[1]
    assert histories[0][-1] < histories[0][0]
