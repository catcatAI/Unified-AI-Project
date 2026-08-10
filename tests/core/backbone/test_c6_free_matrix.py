# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""後續計畫 §1：自由矩陣深化 — version/created_at + free_matrices()。

驗證：
- SharedLatentSpace(version=…) / created_at 建例可設。
- save_weights 存 __version / __created_at；load_weights 讀回。
- backbone.register_free_matrix + free_matrices() 列出（含版本/維度/modalities）。
- 多實例隔離：不同 key 的不同矩陣不互相污染。
"""

import numpy as np
import pytest

from ai.multimodal.shared_latent_space import SharedLatentSpace
from core.backbone import get_backbone, reset_backbone


@pytest.fixture(autouse=True)
def _fresh():
    reset_backbone()
    yield
    reset_backbone()


class TestVersionMetadata:
    def test_defaults(self):
        space = SharedLatentSpace()
        assert space.version == 1
        assert space.created_at

    def test_custom_version(self):
        space = SharedLatentSpace(version=7)
        assert space.version == 7

    def test_created_at_roundtrips_through_weights(self, tmp_path):
        space = SharedLatentSpace(version=3)
        space.register_modality("vision", 16)
        path = str(tmp_path / "sls.npz")
        assert space.save_weights(path)

        space2 = SharedLatentSpace(version=1)
        space2.register_modality("vision", 16)
        assert space2.load_weights(path)
        assert space2.version == 3
        assert space2.created_at

    def test_weights_without_meta_still_ok(self, tmp_path):
        # 舊格式 npz（無 __version）載入不該崩，version 維持預設
        rng = np.random.default_rng(0)
        w = rng.normal(size=(64, 4)).astype(np.float32)
        np.savez(tmp_path / "old.npz", vision__W=w, vision__b=np.zeros(64, dtype=np.float32))
        space = SharedLatentSpace(version=9)
        space.register_modality("vision", 4)
        assert space.load_weights(str(tmp_path / "old.npz"))
        assert space.version == 9


class TestFreeMatrices:
    def test_register_and_list(self):
        bb = get_backbone()
        space = SharedLatentSpace(version=2)
        space.register_modality("vision", 16)
        space.register_modality("audio", 8)
        bb.register_free_matrix("game_matrix", space)

        mats = bb.free_matrices()
        # 可能還含 shared_latent_space（get_backbone 自動註冊）
        game = next((m for m in mats if m["key"] == "game_matrix"), None)
        assert game is not None
        assert game["is_free_matrix"] is True
        assert game["version"] == 2
        assert set(game["modalities"]) == {"vision", "audio"}
        assert game["latent_dim"] == 64

    def test_default_shared_latent_registered(self):
        bb = get_backbone()
        mats = bb.free_matrices()
        assert any(m["key"] == "shared_latent_space" for m in mats)
        entry = next(m for m in mats if m["key"] == "shared_latent_space")
        assert entry["is_free_matrix"] is True

    def test_isolation_between_keyed_matrices(self):
        bb = get_backbone()
        a = SharedLatentSpace()
        b = SharedLatentSpace(version=5)
        bb.register_free_matrix("m_a", a)
        bb.register_free_matrix("m_b", b)
        mats = {m["key"]: m for m in bb.free_matrices()}
        assert mats["m_a"]["version"] == 1
        assert mats["m_b"]["version"] == 5
        # 兩者不相通
        assert a is not b

    def test_register_free_matrix_is_mountable(self):
        bb = get_backbone()
        space = SharedLatentSpace(version=11)
        bb.register_free_matrix("keyed", space)
        assert bb.mount("keyed")
        assert bb.mounts.is_mounted("keyed")
        assert bb.access("keyed") is space
