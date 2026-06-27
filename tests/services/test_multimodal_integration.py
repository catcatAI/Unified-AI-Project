"""
End-to-end integration tests for the complete multimodal pipeline.

Tests the full flow: encode → decode → compare → retrieve → generate → evaluate,
verifying that the complete pipeline works correctly end-to-end.

P38: Maintenance & Testing Extension.

ANGELA-MATRIX: [L6] [αβγδ] [C] [L5]
"""

import asyncio
import io
import time
from typing import Any, Dict

import numpy as np
import pytest

# =============================================================================
# Fixtures: real MultimodalService (not mocked)
# =============================================================================


@pytest.fixture(scope="module")
def svc():
    """Create a real MultimodalService for end-to-end testing."""
    from services.multimodal_service import MultimodalService

    service = MultimodalService()
    # Ensure encoders are initialized
    _ = service._get_visual_encoder()
    _ = service._get_audio_encoder()
    _ = service._get_latent_space()
    return service


@pytest.fixture
def sample_image_bytes():
    """Generate a small test image (32x32 RGB PNG)."""
    from PIL import Image

    img = Image.new("RGB", (32, 32), color=(73, 109, 137))
    # Add some variation
    pixels = img.load()
    for x in range(32):
        for y in range(32):
            pixels[x, y] = (x * 8 % 256, y * 8 % 256, (x + y) * 4 % 256)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_audio_bytes():
    """Generate a small test audio (0.5s 16kHz WAV with a tone)."""
    sample_rate = 16000
    duration = 0.5
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = np.sin(2 * np.pi * 440 * t, dtype=np.float32) * 0.5
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        int16 = (tone * 32767).astype(np.int16)
        wf.writeframes(int16.tobytes())
    return buf.getvalue()


# =============================================================================
# Integration Tests
# =============================================================================


class TestMultimodalIntegration:
    """Complete end-to-end multimodal pipeline integration tests."""

    @pytest.mark.asyncio
    async def test_encode_vision_then_audio(self, svc, sample_image_bytes, sample_audio_bytes):
        """P30-P32: Encode both vision and audio, verify results have all fields."""
        # Encode vision
        vis_result = await svc.encode(sample_image_bytes, "vision")
        assert vis_result.get("error") is None
        assert "item_id" in vis_result
        assert "latent" in vis_result
        assert vis_result["modality"] == "vision"
        assert vis_result["dim"] == 256
        vision_id = vis_result["item_id"]

        # Encode audio
        aud_result = await svc.encode(sample_audio_bytes, "audio")
        assert aud_result.get("error") is None
        assert "item_id" in aud_result
        assert "latent" in aud_result
        assert aud_result["modality"] == "audio"
        assert aud_result["dim"] == 128
        audio_id = aud_result["item_id"]

        assert vision_id != audio_id, "Vision and audio should get different IDs"
        return vision_id, audio_id

    @pytest.mark.asyncio
    async def test_decode_vision_to_pil(self, svc, sample_image_bytes):
        """P30-P32: Encode then decode vision, verify decoded is valid."""
        result = await svc.encode(sample_image_bytes, "vision")
        assert result.get("error") is None
        item_id = result["item_id"]

        decoded = await svc.decode(item_id, "vision", output_format="pil")
        assert decoded.get("error") is None
        from PIL import Image
        assert isinstance(decoded.get("decoded"), Image.Image)

    @pytest.mark.asyncio
    async def test_compare_vision_audio(self, svc, sample_image_bytes, sample_audio_bytes):
        """P30-P33: Encode both modalities, then compare for similarity."""
        vis = await svc.encode(sample_image_bytes, "vision")
        aud = await svc.encode(sample_audio_bytes, "audio")
        assert vis.get("error") is None
        assert aud.get("error") is None

        comp = await svc.compare(vis["item_id"], aud["item_id"])
        assert comp.get("error") is None
        assert "similarity" in comp
        assert 0.0 <= comp["similarity"] <= 1.0
        assert comp["modality_a"] == "vision"
        assert comp["modality_b"] == "audio"

    @pytest.mark.asyncio
    async def test_retrieve_after_encode(self, svc, sample_image_bytes):
        """P30-P36: Encode, then retrieve similar items."""
        vis = await svc.encode(sample_image_bytes, "vision")
        assert vis.get("error") is None

        retrieved = await svc.retrieve(vis["item_id"], top_k=3)
        assert isinstance(retrieved, list)

    @pytest.mark.asyncio
    async def test_generate_vision_to_audio(self, svc, sample_image_bytes):
        """P30-P33: Encode vision, then generate audio from vision latent."""
        vis = await svc.encode(sample_image_bytes, "vision")
        assert vis.get("error") is None

        gen = await svc.generate(vis["item_id"], "audio")
        assert gen.get("error") is None
        assert "generated" in gen
        assert gen["generated"].startswith("data:audio/wav;base64,")

    @pytest.mark.asyncio
    async def test_evaluate_with_item(self, svc, sample_image_bytes):
        """P30-P37: Encode, then evaluate quality of the encoded item."""
        vis = await svc.encode(sample_image_bytes, "vision")
        assert vis.get("error") is None

        eval_result = await svc.evaluate(vis["item_id"], "vision")
        assert eval_result.get("error") is None
        metrics = eval_result.get("metrics", {})
        assert isinstance(metrics, dict)

    @pytest.mark.asyncio
    async def test_encode_with_retry(self, svc, sample_image_bytes):
        """P37: Encode with retry works on first try."""
        result = await svc.encode_with_retry(sample_image_bytes, "vision")
        assert result.get("error") is None
        assert result["recovery"]["attempts"] == 1
        assert result["recovery"]["retried"] is False

    @pytest.mark.asyncio
    async def test_save_load_checkpoint(self, svc, tmp_path):
        """P37: Save and load checkpoint works."""
        import os

        # Temporarily override checkpoint dir
        cp_dir = str(tmp_path / "cp_test")
        sp = svc._get_state_persistence()
        orig_dir = sp._checkpoint_dir
        sp._checkpoint_dir = cp_dir

        try:
            saved = await svc.save_checkpoint("e2e_test")
            assert saved["status"] == "saved"

            loaded = await svc.load_checkpoint("e2e_test")
            assert loaded["status"] == "loaded"
        finally:
            sp._checkpoint_dir = orig_dir

    @pytest.mark.asyncio
    async def test_full_pipeline(self, svc, sample_image_bytes, sample_audio_bytes):
        """P30-P37: Full pipeline — encode → decode → compare → retrieve → generate → evaluate."""
        # Step 1: Encode vision
        vis = await svc.encode(sample_image_bytes, "vision")
        assert vis.get("error") is None
        vid_id = vis["item_id"]

        # Step 2: Encode audio
        aud = await svc.encode(sample_audio_bytes, "audio")
        assert aud.get("error") is None
        aud_id = aud["item_id"]

        # Step 3: Decode vision
        decoded = await svc.decode(vid_id, "vision")
        assert decoded.get("error") is None
        assert "decoded" in decoded

        # Step 4: Compare
        comp = await svc.compare(vid_id, aud_id)
        assert comp.get("error") is None

        # Step 5: Retrieve
        retrieved = await svc.retrieve(vid_id, top_k=5)
        assert isinstance(retrieved, list)

        # Step 6: Generate cross-modal
        gen = await svc.generate(vid_id, "audio")
        assert gen.get("error") is None

        # Step 7: Evaluate
        eval_result = await svc.evaluate(vid_id, "vision")
        assert eval_result.get("error") is None

        # All steps completed
        assert True

    @pytest.mark.asyncio
    async def test_recovery_state_accessible(self, svc):
        """P37: Recovery state accessible and properly initialized."""
        state = await svc.get_recovery_state()
        assert "retry_counts" in state
        assert "crisis_levels" in state

    @pytest.mark.asyncio
    async def test_decoders_work(self, svc):
        """P18: Both visual and audio decoders initialized and produce output."""
        # Visual decoder
        vd = svc._get_visual_decoder()
        test_latent = np.random.randn(64).astype(np.float32)
        img = vd.decode(test_latent)
        assert img is not None
        assert img.shape == (128, 128, 3)

        # Audio decoder
        ad = svc._get_audio_decoder()
        wav = ad.decode(test_latent)
        assert wav is not None
        assert len(wav) > 0
