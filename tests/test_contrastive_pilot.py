"""Contrastive pilot gate (R9): real updates, deterministic, learns.

Runs scripts/train_contrastive_pilot.py::main() (~0.3s): asserts exit 0,
i.e. final loss strictly below initial (no simulated arithmetic allowed).
Determinism is pinned by seed 42 + md5 W init inside the engine.
"""

import importlib.util
import os
import sys


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
    import sys

    import numpy as np

    if os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src") not in sys.path:
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


def _run_script(name, *args, timeout=120):
    import subprocess

    repo_root = os.path.join(os.path.dirname(__file__), "..")
    return subprocess.run(
        [sys.executable, os.path.join(repo_root, "scripts", name), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=repo_root,
    )


def test_multimodal_forwarder_runs_real():
    """R10: deprecated multimodal 試點轉發真實版，不再吐模擬算術。"""
    import sys

    p = _run_script("train_multimodal_pilot.py")
    assert p.returncode == 0, p.stderr[-500:]
    assert "真實 loss" in p.stdout
    assert "模擬 loss" not in p.stdout


def test_association_pilot_small_real():
    """R10: association 試點真訓練（Hebbian 成邊 + 回環），小量驗證。"""
    import sys

    p = _run_script(
        "train_pilot_association.py", "--count", "100", "--batch", "50", "--checkpoint", ""
    )
    assert p.returncode == 0, p.stderr[-500:]
    assert "Pilot done" in p.stdout
    assert "parsed=" in p.stdout
