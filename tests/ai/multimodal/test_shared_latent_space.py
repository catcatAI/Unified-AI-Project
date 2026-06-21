import numpy as np
import pytest


@pytest.fixture
def latent_space():
    from ai.multimodal.shared_latent_space import SharedLatentSpace
    ls = SharedLatentSpace(latent_dim=64)
    ls.register_modality("vision", 128)
    ls.register_modality("audio", 32)
    ls.register_modality("text", 256)
    return ls


class TestSharedLatentSpace:

    def test_project_returns_latent_vector(self, latent_space):
        features = np.random.randn(128).astype(np.float32)
        latent = latent_space.project("vision", features)
        assert isinstance(latent, np.ndarray)
        assert latent.shape == (64,)
        assert latent.dtype == np.float32

    def test_projected_vector_is_not_zero(self, latent_space):
        features = np.random.randn(128).astype(np.float32)
        latent = latent_space.project("vision", features)
        norm = np.linalg.norm(latent)
        assert norm > 0

    def test_similarity_between_known_modalities(self, latent_space):
        v_feat = np.random.randn(128).astype(np.float32)
        a_feat = np.random.randn(32).astype(np.float32)
        latent_space.project("vision", v_feat)
        latent_space.project("audio", a_feat)
        sim = latent_space.similarity("vision", "audio")
        assert 0.0 <= sim <= 1.0

    def test_similarity_self_is_high(self, latent_space):
        feat = np.random.randn(128).astype(np.float32)
        latent_space.project("vision", feat)
        latent_space.project("vision", feat)
        sim = latent_space.similarity("vision", "vision")
        assert sim > 0.99

    def test_unknown_modality_returns_zeros(self, latent_space):
        latent = latent_space.project("unknown", np.random.randn(10).astype(np.float32))
        assert np.all(latent == 0.0)

    def test_similarity_unknown_modality_zero(self, latent_space):
        assert latent_space.similarity("vision", "unknown") == 0.0

    def test_register_modality_adds_projection(self, latent_space):
        assert "text" in latent_space.registered_modalities()
        assert len(latent_space.registered_modalities()) == 3

    def test_reset_clears_cache(self, latent_space):
        latent_space.project("vision", np.random.randn(128).astype(np.float32))
        assert latent_space.get_embedding("vision") is not None
        latent_space.reset()
        assert latent_space.get_embedding("vision") is None

    def test_get_embedding_after_project(self, latent_space):
        feat = np.random.randn(128).astype(np.float32)
        latent_space.project("vision", feat)
        emb = latent_space.get_embedding("vision")
        assert emb is not None
        assert emb.shape == (64,)
