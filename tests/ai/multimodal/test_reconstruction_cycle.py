import numpy as np
import pytest


@pytest.fixture
def latent_space():
    from ai.multimodal.shared_latent_space import SharedLatentSpace
    ls = SharedLatentSpace(latent_dim=64)
    ls.register_modality("vision", 256)
    ls.register_modality("audio", 128)
    return ls


@pytest.fixture
def visual_decoder():
    from ai.multimodal.visual_decoder import VisualDecoder
    return VisualDecoder()


@pytest.fixture
def audio_decoder():
    from ai.multimodal.audio_decoder import AudioWaveformDecoder
    return AudioWaveformDecoder()


@pytest.fixture
def vision_features():
    rng = np.random.default_rng(42)
    return rng.normal(0, 1, 256).astype(np.float32)


@pytest.fixture
def audio_features():
    rng = np.random.default_rng(42)
    return rng.normal(0, 1, 128).astype(np.float32)


class TestReconstructionCycle:

    @pytest.fixture
    def cycle(self, latent_space, visual_decoder, audio_decoder):
        from ai.multimodal.reconstruction_cycle import ReconstructionCycle
        return ReconstructionCycle(latent_space, visual_decoder, audio_decoder)

    def test_init(self, cycle):
        assert cycle._visual_decoder is not None
        assert cycle._audio_decoder is not None

    def test_train_step_reduces_loss(self, cycle, vision_features):
        loss_before = cycle.train_step("vision", vision_features, lr=0.0001)
        loss_after = cycle.train_step("vision", vision_features, lr=0.001)
        assert loss_after <= loss_before

    def test_train_epochs_reduce_loss(self, cycle, vision_features):
        result = cycle.train("vision", [vision_features] * 3, epochs=10, lr=0.005)
        assert "final_loss" in result
        assert "history" in result
        assert len(result["history"]) == 10
        assert result["final_loss"] <= result["history"][0] * 0.99

    def test_reconstruct_returns_same_shape(self, cycle, vision_features):
        f_hat = cycle.reconstruct("vision", vision_features)
        assert f_hat.shape == vision_features.shape
        assert f_hat.dtype == np.float32

    def test_reconstruction_error_decreases(self, cycle, vision_features):
        err_before = cycle.reconstruction_error("vision", vision_features)
        for _ in range(50):
            cycle.train_step("vision", vision_features, lr=0.01)
        err_after = cycle.reconstruction_error("vision", vision_features)
        assert err_after <= err_before * 0.95

    def test_unknown_modality_returns_zero_loss(self, cycle):
        loss = cycle.train_step("unknown", np.zeros(10), lr=0.1)
        assert loss == 0.0

    def test_audio_reconstruction(self, cycle, audio_features):
        err_before = cycle.reconstruction_error("audio", audio_features)
        for _ in range(50):
            cycle.train_step("audio", audio_features, lr=0.01)
        err_after = cycle.reconstruction_error("audio", audio_features)
        assert err_after <= err_before * 0.95


class TestCrossModalSynthesizer:

    @pytest.fixture
    def synthesizer(self, latent_space, visual_decoder, audio_decoder):
        from ai.multimodal.reconstruction_cycle import CrossModalSynthesizer
        return CrossModalSynthesizer(latent_space, visual_decoder, audio_decoder)

    def test_blend_latents_returns_64dim(self, synthesizer, vision_features, audio_features):
        blended = synthesizer.blend_latents([
            ("vision", vision_features),
            ("audio", audio_features),
        ])
        assert len(blended) == 64
        assert blended.dtype == np.float32

    def test_blend_latents_equal_weights(self, synthesizer, vision_features, audio_features):
        blended = synthesizer.blend_latents([
            ("vision", vision_features),
            ("audio", audio_features),
        ], weights=[0.5, 0.5])
        z_v = synthesizer._ls.project("vision", vision_features)
        z_a = synthesizer._ls.project("audio", audio_features)
        expected = 0.5 * z_v + 0.5 * z_a
        assert np.allclose(blended, expected)

    def test_generate_image_from_latent(self, synthesizer, vision_features):
        z = synthesizer._ls.project("vision", vision_features)
        img = synthesizer.generate_image(z)
        assert img.shape == (128, 128, 3)
        assert img.dtype == np.uint8

    def test_generate_audio_from_latent(self, synthesizer, audio_features):
        z = synthesizer._ls.project("audio", audio_features)
        wav = synthesizer.generate_audio(z)
        assert len(wav) > 0
        assert wav.dtype == np.float32

    def test_cross_generate_vision_to_audio(self, synthesizer, vision_features):
        result = synthesizer.cross_generate("vision", vision_features, "audio")
        assert len(result) > 0
        assert result.dtype == np.float32

    def test_cross_generate_audio_to_vision(self, synthesizer, audio_features):
        result = synthesizer.cross_generate("audio", audio_features, "image")
        assert result.shape == (128, 128, 3)
        assert result.dtype == np.uint8

    def test_empty_modalities_returns_zeros(self, synthesizer):
        blended = synthesizer.blend_latents([])
        assert np.all(blended == 0.0)

    def test_generate_image_no_decoder_returns_zeros(self):
        from ai.multimodal.reconstruction_cycle import CrossModalSynthesizer
        from ai.multimodal.shared_latent_space import SharedLatentSpace
        ls = SharedLatentSpace(latent_dim=64)
        syn = CrossModalSynthesizer(ls)
        img = syn.generate_image(np.zeros(64))
        assert np.all(img == 0)
