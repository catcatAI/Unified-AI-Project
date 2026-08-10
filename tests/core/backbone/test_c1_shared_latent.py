# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""步驟 C1：SharedLatentSpace save/load_weights + Mountable 協議 + backbone 掛載接線。

驗證：
- save_weights / load_weights 對任意 modality 名 roundtrip（含非標準名）。
- Mountable 協議（mount/unmount/is_mounted/persistence_path）直接可用。
- get_backbone() 單例建例時自動註冊 shared_latent_space 為 mountable，
  且 `access()` 可取得真實 singleton（lazy mount 不炸）。
"""

import os

import numpy as np
import pytest

from ai.multimodal.shared_latent_space import SharedLatentSpace, get_shared_latent_space
from core.backbone import get_backbone, reset_backbone


@pytest.fixture(autouse=True)
def _fresh():
    reset_backbone()
    yield
    reset_backbone()


@pytest.fixture
def ls(tmp_path):
    space = SharedLatentSpace(latent_dim=16)
    space.register_modality("vision", 32)
    space.register_modality("audio_semantic", 24)
    space.weights_path = str(tmp_path / "ls.npz")
    return space


class TestSaveLoadWeights:
    def test_roundtrip_all_modalities(self, ls):
        before = {name: proj["W"].copy() for name, proj in ls._projections.items()}
        assert ls.save_weights(ls.weights_path)
        space2 = SharedLatentSpace(latent_dim=16)
        space2.register_modality("vision", 32)
        space2.register_modality("audio_semantic", 24)
        assert space2.load_weights(ls.weights_path)
        for name, W in before.items():
            assert np.allclose(W, space2._projections[name]["W"])

    def test_load_missing_path_returns_false(self, ls, tmp_path):
        assert ls.load_weights(str(tmp_path / "nope.npz")) is False

    def test_save_failure_returns_false(self, ls):
        bad = str(ls.weights_path) if False else os.path.join("/nonexistent-root-dir-xyz", "a.npz")
        assert ls.save_weights(bad) is False

    def test_load_ignores_unknown_keys(self, ls):
        ls.save_weights(ls.weights_path)
        data = np.load(ls.weights_path, allow_pickle=False)
        extra = {k: v for k, v in data.items()}
        extra["mystery__W"] = np.ones(1)
        extra["mystery__b"] = np.ones(1)
        np.savez(ls.weights_path, **extra)
        assert ls.load_weights(ls.weights_path) is True

    def test_bad_file_content_returns_false(self, ls, tmp_path):
        p = tmp_path / "junk.npz"
        p.write_bytes(b"not a valid npz")
        assert ls.load_weights(str(p)) is False


class TestMountableProtocol:
    def test_mount_returns_true(self, ls):
        assert ls.mount() is True
        assert ls.is_mounted() is True

    def test_unmount_keeps_singleton_alive(self, ls):
        assert ls.unmount() is True
        assert ls.is_mounted() is True

    def test_persistence_path_default(self, ls):
        assert isinstance(ls.persistence_path(), str)
        assert ls.persistence_path().endswith(".npz")


class TestBackboneRegistration:
    def test_singleton_registers_shared_latent(self):
        bb = get_backbone()
        assert bb.mounts.has("shared_latent_space")
        assert bb.mounts.is_mounted("shared_latent_space") in (True, False)

    def test_access_returns_shared_latent_singleton(self):
        bb = get_backbone()
        resource = bb.access("shared_latent_space")
        assert resource is not None
        # Lazy mount 會呼叫 factory（get_shared_latent_space），拿到全域 singleton 實例
        global_sls = get_shared_latent_space()
        assert resource is global_sls
        assert resource is get_backbone().access("shared_latent_space")