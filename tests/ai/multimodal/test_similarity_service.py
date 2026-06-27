import io
import wave

import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def vision_service():
    from services.vision_service import VisionService
    svc = VisionService()
    return svc


@pytest.fixture
def audio_service():
    from services.audio_service import AudioService
    svc = AudioService()
    return svc


def _sample_image_bytes():
    img = Image.new("RGB", (64, 64), color=(128, 64, 32))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _sample_audio_wav():
    n_samples = 8000
    samples = (np.sin(2 * np.pi * 440 * np.arange(n_samples) / 16000) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


class TestVisionServiceEncode:

    async def test_encode_image_returns_list(self, vision_service):
        result = await vision_service.encode_image(_sample_image_bytes())
        assert isinstance(result, list)
        assert len(result) == 256
        assert all(isinstance(v, float) for v in result)

    async def test_encode_image_empty_returns_empty(self, vision_service):
        result = await vision_service.encode_image(b"")
        assert result == []

    async def test_encode_image_zero_vector_on_bad_data(self, vision_service):
        result = await vision_service.encode_image(b"\x00\x00")
        assert isinstance(result, list)
        assert len(result) == 256


class TestAudioServiceEncode:

    async def test_encode_audio_returns_list(self, audio_service):
        result = await audio_service.encode_audio(_sample_audio_wav())
        assert isinstance(result, list)
        assert len(result) == 128
        assert all(isinstance(v, float) for v in result)

    async def test_encode_audio_empty_returns_empty(self, audio_service):
        result = await audio_service.encode_audio(b"")
        assert result == []

    async def test_encode_audio_zero_vector_on_bad_data(self, audio_service):
        result = await audio_service.encode_audio(b"\x00\x00")
        assert isinstance(result, list)
        assert len(result) == 128


class TestMultimodalSimilarityService:

    @pytest.fixture
    def sim_service(self):
        from ai.multimodal.similarity_service import MultimodalSimilarityService
        return MultimodalSimilarityService()

    async def test_encode_and_compare(self, sim_service):
        img_vec = await sim_service.encode_vision(_sample_image_bytes(), "img1")
        assert img_vec is not None
        assert len(img_vec) == 256

        aud_vec = await sim_service.encode_audio(_sample_audio_wav(), "aud1")
        assert aud_vec is not None
        assert len(aud_vec) == 128

        assert sim_service.registered_item_count() == 2
        sim = sim_service.compare("img1", "aud1")
        assert 0.0 <= sim <= 1.0

    async def test_same_modality_high_similarity(self, sim_service):
        await sim_service.encode_vision(_sample_image_bytes(), "img_a")
        await sim_service.encode_vision(_sample_image_bytes(), "img_b")
        sim = sim_service.compare("img_a", "img_b")
        assert sim > 0.5

    async def test_unknown_item_returns_zero(self, sim_service):
        assert sim_service.compare("nonexistent", "img1") == 0.0

    async def test_get_embedding(self, sim_service):
        await sim_service.encode_vision(_sample_image_bytes(), "img1")
        emb = sim_service.get_embedding("img1")
        assert emb is not None
        assert len(emb) == 64

    async def test_get_embedding_unknown(self, sim_service):
        assert sim_service.get_embedding("unknown") is None

    async def test_reset(self, sim_service):
        await sim_service.encode_vision(_sample_image_bytes(), "img1")
        assert sim_service.registered_item_count() == 1
        sim_service.reset()
        assert sim_service.registered_item_count() == 0

    async def test_encode_invalid_vision_returns_none(self, sim_service):
        result = await sim_service.encode_vision(b"", "bad_img")
        assert result is None


class TestMultimodalSimilarityServiceQuality:

    @pytest.fixture
    def sim_service(self):
        from ai.multimodal.similarity_service import MultimodalSimilarityService
        return MultimodalSimilarityService()

    async def test_evaluate_image_generation_returns_ssim(self, sim_service):
        img_bytes = _sample_image_bytes()
        await sim_service.encode_vision(img_bytes, "quality_img")
        report = sim_service.evaluate_image_generation(img_bytes, "quality_img")
        assert report is not None
        assert "ssim" in report
        assert 0.0 <= report["ssim"] <= 1.0

    async def test_evaluate_audio_generation_returns_snr(self, sim_service):
        aud_bytes = _sample_audio_wav()
        await sim_service.encode_audio(aud_bytes, "quality_aud")
        report = sim_service.evaluate_audio_generation(aud_bytes, "quality_aud")
        assert report is not None
        assert "snr" in report
        assert not np.isnan(report["snr"])

    async def test_evaluate_unknown_item_returns_none(self, sim_service):
        assert sim_service.evaluate_image_generation(b"", "unknown") is None
        assert sim_service.evaluate_audio_generation(b"", "unknown") is None

    async def test_full_quality_report_contains_modalities(self, sim_service):
        img_bytes = _sample_image_bytes()
        aud_bytes = _sample_audio_wav()
        await sim_service.encode_vision(img_bytes, "full_img")
        await sim_service.encode_audio(aud_bytes, "full_aud")
        report = sim_service.full_quality_report(
            image_data=img_bytes, audio_data=aud_bytes,
            image_item="full_img", audio_item="full_aud"
        )
        assert "image" in report
        assert "audio" in report
        assert "ssim" in report["image"]
        assert "snr" in report["audio"]
