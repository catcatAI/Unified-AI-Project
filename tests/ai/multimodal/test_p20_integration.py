import numpy as np
import pytest
from PIL import Image
import io
import wave


@pytest.fixture
def sample_image_bytes():
    img = Image.new("RGB", (64, 64), color=(128, 64, 32))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_audio_bytes():
    n_samples = 8000
    samples = (np.sin(2 * np.pi * 440 * np.arange(n_samples) / 16000) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


class TestServiceDecode:

    @pytest.fixture
    def service(self):
        from ai.multimodal.similarity_service import MultimodalSimilarityService
        return MultimodalSimilarityService()

    async def test_decode_to_image_after_encode(self, service, sample_image_bytes):
        vec = await service.encode_vision(sample_image_bytes, "img1")
        assert vec is not None
        pil = service.decode_to_image("img1")
        assert pil is not None
        assert pil.size == (128, 128)
        assert pil.mode == "RGB"

    async def test_decode_to_image_unknown_returns_none(self, service):
        assert service.decode_to_image("unknown") is None

    async def test_decode_to_image_wrong_modality(self, service, sample_audio_bytes):
        await service.encode_audio(sample_audio_bytes, "aud1")
        assert service.decode_to_image("aud1") is None

    async def test_decode_to_audio_after_encode(self, service, sample_audio_bytes):
        vec = await service.encode_audio(sample_audio_bytes, "aud1")
        assert vec is not None
        wav = service.decode_to_audio("aud1")
        assert wav is not None
        assert len(wav) == 16000
        assert all(isinstance(v, float) for v in wav[:10])

    async def test_decode_to_audio_unknown_returns_none(self, service):
        assert service.decode_to_audio("unknown") is None

    async def test_decode_to_audio_wrong_modality(self, service, sample_image_bytes):
        await service.encode_vision(sample_image_bytes, "img1")
        assert service.decode_to_audio("img1") is None


class TestVisualEncoderConv2d:

    @pytest.fixture
    def encoder(self):
        from ai.multimodal.visual_encoder import VisualEncoder
        return VisualEncoder()

    def test_vectorized_conv2d_matches_manual(self, encoder):
        import numpy as np
        img = np.random.default_rng(42).normal(0, 1, (128, 128)).astype(np.float32)

        filters = encoder._build_filters()
        k = filters[0]
        k_h, k_w = k.shape
        s = 4
        h_out = (128 - k_h) // s + 1
        w_out = (128 - k_w) // s + 1

        manual = np.zeros((h_out, w_out), dtype=np.float32)
        for y in range(0, h_out * s, s):
            for x in range(0, w_out * s, s):
                manual[y // s, x // s] = np.sum(img[y:y + k_h, x:x + k_w] * k)

        windows = np.lib.stride_tricks.sliding_window_view(img, (k_h, k_w))[::s, ::s]
        vectorized = np.tensordot(windows, k, axes=2)

        assert np.allclose(manual, vectorized, atol=1e-5)

    def test_cnn_features_returns_correct_shape(self, encoder, sample_image_bytes):
        vec = encoder.encode(sample_image_bytes)
        assert len(vec) == 256


class TestMultimodalBridge:

    @pytest.fixture
    def bridge(self):
        from ai.multimodal.multimodal_bridge import MultimodalBridge
        return MultimodalBridge()

    def test_encode_image_bytes(self, bridge, sample_image_bytes):
        vec = bridge.encode_image_bytes(sample_image_bytes)
        assert vec is not None
        assert len(vec) == 256

    def test_encode_audio_bytes(self, bridge, sample_audio_bytes):
        vec = bridge.encode_audio_bytes(sample_audio_bytes)
        assert vec is not None
        assert len(vec) == 128

    def test_encode_image_to_latent(self, bridge, sample_image_bytes):
        latent = bridge.encode_image_to_latent(sample_image_bytes)
        assert latent is not None
        assert len(latent) == 64

    def test_encode_audio_to_latent(self, bridge, sample_audio_bytes):
        latent = bridge.encode_audio_to_latent(sample_audio_bytes)
        assert latent is not None
        assert len(latent) == 64

    def test_decode_latent_to_image(self, bridge, sample_image_bytes):
        latent = bridge.encode_image_to_latent(sample_image_bytes)
        assert latent is not None
        pil = bridge.decode_latent_to_image(latent)
        assert pil is not None
        assert pil.size == (128, 128)

    def test_decode_latent_to_waveform(self, bridge, sample_audio_bytes):
        latent = bridge.encode_audio_to_latent(sample_audio_bytes)
        assert latent is not None
        wav = bridge.decode_latent_to_waveform(latent)
        assert wav is not None
        assert len(wav) == 16000

    def test_decode_latent_wrong_dim_returns_none(self, bridge):
        assert bridge.decode_latent_to_image([0.0] * 10) is None
        assert bridge.decode_latent_to_waveform([0.0] * 10) is None

    def test_similarity(self, bridge):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        sim = bridge.similarity(a, b)
        assert abs(sim - 0.5) < 1e-5  # orthogonal → cos=0 → mapped to 0.5

    def test_similarity_self_is_one(self, bridge):
        a = [1.0, 2.0, 3.0]
        sim = bridge.similarity(a, a)
        assert abs(sim - 1.0) < 1e-5

    def test_cross_similarity(self, bridge, sample_image_bytes, sample_audio_bytes):
        sim = bridge.cross_similarity(sample_image_bytes, sample_audio_bytes)
        assert 0.0 <= sim <= 1.0

    def test_to_dictionary_entry(self, bridge, sample_image_bytes):
        entry = bridge.to_dictionary_entry(sample_image_bytes, label="test_image")
        assert "key" in entry
        assert "value" in entry
        assert "vector" in entry
        assert entry["value"] == "test_image"
        assert len(entry["vector"]) == 64

    def test_empty_bytes_returns_empty_entry(self, bridge):
        entry = bridge.to_dictionary_entry(b"")
        assert entry["key"] == ""
        assert entry["vector"] == []

    def test_latent_to_entry(self, bridge):
        latent = [0.1] * 64
        entry = bridge.latent_to_entry(latent, label="test")
        assert entry["key"].startswith("mm_latent_")
        assert entry["value"] == "test"
        assert entry["vector"] == latent
