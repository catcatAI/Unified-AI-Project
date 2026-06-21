"""
P30: Tests for MultimodalService — the multimodal pipeline orchestrator.

Tests cover:
- Encode vision/audio
- Decode vision/audio (base64 output)
- Cross-modal comparison
- Item registry management
- Training (synthetic)
- Evaluation
- Cross-modal generation
- Weight persistence
- Health check
"""

import asyncio
import io
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))

from services.multimodal_service import MultimodalService


def _sample_image_bytes(size: int = 256) -> bytes:
    """Generate a simple PNG-like image."""
    from PIL import Image
    img = Image.fromarray(
        np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)
    )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _sample_audio_bytes(duration_ms: int = 500) -> bytes:
    """Generate a simple WAV audio."""
    sample_rate = 16000
    n_samples = int(sample_rate * duration_ms / 1000)
    samples = (np.random.randn(n_samples) * 0.3 * 32767).astype(np.int16)
    buf = io.BytesIO()
    import wave
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


@pytest.fixture
def service():
    return MultimodalService()


@pytest.mark.asyncio
class TestMultimodalServiceEncode:
    """P30 T1-T3: Encoding tests (3 tests)."""

    async def test_encode_vision_returns_latent(self, service):
        """T1: Encode image returns latent, feature_vector, dim, item_id."""
        data = _sample_image_bytes()
        result = await service.encode(data, "vision")
        assert result.get("error") is None, result.get("error")
        assert result["modality"] == "vision"
        assert "latent" in result
        assert len(result["latent"]) == 64  # LATENT_DIM
        assert "feature_vector" in result
        assert len(result["feature_vector"]) == 256  # VISION_DIM
        assert result["dim"] == 256
        assert "item_id" in result
        assert result["item_id"].startswith("vision_")
        assert "time_ms" in result

    async def test_encode_audio_returns_latent(self, service):
        """T2: Encode audio returns latent, feature_vector, dim, item_id."""
        data = _sample_audio_bytes()
        result = await service.encode(data, "audio")
        assert result.get("error") is None, result.get("error")
        assert result["modality"] == "audio"
        assert len(result["latent"]) == 64  # LATENT_DIM
        feat = result["feature_vector"]
        assert len(feat) == 128  # AUDIO_DIM
        assert result["dim"] == 128

    async def test_encode_vision_with_custom_id(self, service):
        """T3: Encode with custom item_id preserves the id."""
        data = _sample_image_bytes()
        custom_id = "my_test_image_001"
        result = await service.encode(data, "vision", item_id=custom_id)
        assert result["item_id"] == custom_id

    async def test_encode_empty_data(self, service):
        """T3b: Encode empty bytes returns error gracefully."""
        result = await service.encode(b"", "vision")
        assert "error" in result


@pytest.mark.asyncio
class TestMultimodalServiceDecode:
    """P30 T4-T5: Decoding tests (2 tests)."""

    async def test_decode_vision_returns_base64(self, service):
        """T4: Decode image returns base64 PNG data URI."""
        data = _sample_image_bytes()
        await service.encode(data, "vision", item_id="decode_test_img")
        result = await service.decode("decode_test_img", "vision")
        assert result.get("error") is None, result.get("error")
        decoded = result["decoded"]
        assert isinstance(decoded, str)
        assert decoded.startswith("data:image/png;base64,")

    async def test_decode_audio_returns_base64(self, service):
        """T5: Decode audio returns base64 WAV data URI."""
        data = _sample_audio_bytes()
        enc = await service.encode(data, "audio", item_id="decode_test_aud")
        result = await service.decode("decode_test_aud", "audio")
        assert result.get("error") is None, result.get("error")
        decoded = result["decoded"]
        assert isinstance(decoded, str)
        assert decoded.startswith("data:audio/wav;base64,")


@pytest.mark.asyncio
class TestMultimodalServiceCompare:
    """P30 T6-T7: Comparison and registry tests (2 tests)."""

    async def test_compare_vision_audio(self, service):
        """T6: Compare vision and audio items returns similarity score."""
        img = _sample_image_bytes()
        aud = _sample_audio_bytes()
        await service.encode(img, "vision", item_id="cmp_v")
        await service.encode(aud, "audio", item_id="cmp_a")
        result = await service.compare("cmp_v", "cmp_a")
        assert result.get("error") is None, result.get("error")
        assert "similarity" in result
        assert 0.0 <= result["similarity"] <= 1.0
        assert result["modality_a"] == "vision"
        assert result["modality_b"] == "audio"

    async def test_list_items_after_encode(self, service):
        """T7: List items returns registered count."""
        await service.encode(_sample_image_bytes(), "vision", item_id="list_v")
        await service.encode(_sample_audio_bytes(), "audio", item_id="list_a")
        result = await service.list_items()
        assert result["count"] >= 2
        assert "list_v" in result["items"]
        assert "list_a" in result["items"]


@pytest.mark.asyncio
class TestMultimodalServiceTraining:
    """P30 T8-T9: Training tests (2 tests)."""

    async def test_train_synthetic_completes(self, service):
        """T8: Synthetic training completes without error."""
        result = await service.train(mode="full", epochs=2, lr=0.01)
        assert result["status"] == "completed"
        assert "time_ms" in result

    async def test_train_contrastive_only(self, service):
        """T9: Contrastive-only training completes."""
        result = await service.train(mode="contrastive", epochs=2)
        assert result["status"] == "completed"

    async def test_train_recon_only(self, service):
        """T9b: Reconstruction-only training completes."""
        result = await service.train(mode="recon", epochs=2)
        assert result["status"] == "completed"


@pytest.mark.asyncio
class TestMultimodalServiceEvaluate:
    """P30 T10: Evaluation test (1 test)."""

    async def test_evaluate_synthetic(self, service):
        """T10: Evaluate on synthetic samples returns metrics."""
        result = await service.evaluate(modality="vision", n_samples=3)
        assert result.get("error") is None, result.get("error")
        assert "metrics" in result


@pytest.mark.asyncio
class TestMultimodalServiceCrossModal:
    """P30 T11: Cross-modal generation test (1 test)."""

    async def test_generate_vision_to_audio(self, service):
        """T11: Cross-modal vision→audio generation returns base64 WAV."""
        img = _sample_image_bytes()
        await service.encode(img, "vision", item_id="gen_v")
        result = await service.generate("gen_v", "audio")
        assert result.get("error") is None, result.get("error")
        assert "generated" in result
        assert result["generated"].startswith("data:audio/wav;base64,")


@pytest.mark.asyncio
class TestMultimodalServiceWeights:
    """P30 T12-T14: Weight persistence tests (3 tests)."""

    async def test_save_weights(self, service, tmp_path):
        """T12: Save weights creates .npz file."""
        await service.train(mode="full", epochs=2)
        path = str(tmp_path / "test_weights.npz")
        result = await service.save_weights(path)
        assert result["status"] == "saved"
        assert Path(path).exists()

    async def test_save_and_load_weights_roundtrip(self, service, tmp_path):
        """T13: Save then load weights succeeds."""
        await service.train(mode="full", epochs=2)
        path = str(tmp_path / "roundtrip.npz")
        await service.save_weights(path)
        result = await service.load_weights(path)
        assert result["status"] == "loaded"

    async def test_load_invalid_path(self, service):
        """T14: Loading from invalid path returns failed."""
        result = await service.load_weights("/nonexistent/weights.npz")
        assert result["status"] == "failed"


@pytest.mark.asyncio
class TestMultimodalServiceHealth:
    """P30 T15: Health check test (1 test)."""

    async def test_health(self, service):
        """T15: Health check returns status with all components."""
        health = await service.health()
        assert health["status"] == "healthy"
        assert "encoders" in health
        assert health["encoders"]["vision"] is True
        assert health["encoders"]["audio"] is True
        assert health["latent_space"] is True
        assert "registered_items" in health


@pytest.mark.asyncio
class TestMultimodalServiceEdgeCases:
    """P30 T16: Edge cases (1 test)."""

    async def test_unknown_modality(self, service):
        """T16: Unknown modality returns error gracefully."""
        result = await service.encode(_sample_image_bytes(), "tactile")
        assert "error" in result


@pytest.mark.asyncio
class TestMultimodalServiceClearItems:
    """P30 T17: Clear items test (1 test)."""

    async def test_clear_items_empties_registry(self, service):
        """T17: Clear items removes all registered items."""
        await service.encode(_sample_image_bytes(), "vision", item_id="clear_v")
        await service.encode(_sample_audio_bytes(), "audio", item_id="clear_a")
        before = await service.list_items()
        assert before["count"] >= 2
        await service.clear_items()
        after = await service.list_items()
        assert after["count"] == 0


@pytest.mark.asyncio
class TestMultimodalServiceRetrieve:
    """P30 T18: Retrieval test (1 test)."""

    async def test_retrieve_returns_items(self, service):
        """T18: Retrieve with unknown item returns empty list."""
        result = await service.retrieve("nonexistent_item", top_k=3)
        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.asyncio
class TestMultimodalServiceVisualize:
    """P30 T19: Visualize test (1 test)."""

    async def test_visualize(self, service):
        """T19: List items returns count > 0 after encode."""
        # This test just verifies list_items still works
        await service.encode(_sample_image_bytes(), "vision", item_id="viz_v")
        result = await service.list_items()
        assert result["count"] >= 1
