"""
Multilingual multimodal tests — verify cross-modal operations work with
multilingual encodings and cultural context.

Tests that MultimodalService, CulturalContextModule, and related components
handle Chinese, English, Japanese, and Korean text alongside image/audio data.

P38: Maintenance & Testing Extension.

ANGELA-MATRIX: [L6] [αβγδ] [C] [L5]
"""

import io
from typing import Any, Dict

import numpy as np
import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def svc():
    """Create a real MultimodalService."""
    from services.multimodal_service import MultimodalService

    service = MultimodalService()
    _ = service._get_visual_encoder()
    _ = service._get_audio_encoder()
    _ = service._get_latent_space()
    return service


@pytest.fixture
def sample_image_bytes():
    """Generate a small test image."""
    from PIL import Image

    img = Image.new("RGB", (32, 32), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_audio_bytes():
    """Generate a short test audio."""
    sample_rate = 16000
    duration = 0.3
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
# Multilingual Tests
# =============================================================================


class TestMultilingualMultimodal:
    """Multilingual multimodal operations."""

    @pytest.mark.asyncio
    async def test_encode_with_chinese_item_id(self, svc, sample_image_bytes):
        """Encode with Chinese (CJK) item_id works."""
        cn_id = "\u4e2d\u6587_test_001"  # 中文_test_001
        result = await svc.encode(sample_image_bytes, "vision", item_id=cn_id)
        assert result.get("error") is None
        assert result["item_id"] == cn_id

        # Retrieve the item
        item = await svc.get_item(cn_id)
        assert item is not None
        assert item["modality"] == "vision"

    @pytest.mark.asyncio
    async def test_encode_with_japanese_item_id(self, svc, sample_image_bytes):
        """Encode with Japanese (CJK) item_id works."""
        jp_id = "\u65e5\u672c\u8a9e_test_002"  # 日本語_test_002
        result = await svc.encode(sample_image_bytes, "vision", item_id=jp_id)
        assert result.get("error") is None
        assert result["item_id"] == jp_id

    @pytest.mark.asyncio
    async def test_encode_with_korean_item_id(self, svc, sample_image_bytes):
        """Encode with Korean (Hangul) item_id works."""
        kr_id = "\ud55c\uad6d\uc5b4_test_003"  # 한국어_test_003
        result = await svc.encode(sample_image_bytes, "vision", item_id=kr_id)
        assert result.get("error") is None
        assert result["item_id"] == kr_id

    @pytest.mark.asyncio
    async def test_multilingual_items_list(self, svc, sample_image_bytes):
        """List items after adding multilingual IDs works."""
        ids = [
            "english_001",
            "\u4e2d\u6587_002",
            "\u65e5\u672c\u8a9e_003",
            "\ud55c\uad6d\uc5b4_004",
        ]
        for iid in ids:
            await svc.encode(sample_image_bytes, "vision", item_id=iid)

        items = await svc.list_items()
        items_dict = items.get("items", {})
        # At least our 4 multilingual items should be present
        found = sum(1 for iid in ids if iid in items_dict)
        assert found >= 3, f"Only {found}/4 multilingual IDs found in items list"

    @pytest.mark.asyncio
    async def test_cross_modal_compare_multilingual(self, svc, sample_image_bytes,
                                                    sample_audio_bytes):
        """Compare registered items with multilingual IDs works."""
        cn_id = "\u4e2d\u6587_img"
        kr_id = "\ud55c\uad6d\uc5b4_aud"

        img = await svc.encode(sample_image_bytes, "vision", item_id=cn_id)
        aud = await svc.encode(sample_audio_bytes, "audio", item_id=kr_id)

        assert img.get("error") is None
        assert aud.get("error") is None

        comp = await svc.compare(cn_id, kr_id)
        assert comp.get("error") is None
        assert 0.0 <= comp["similarity"] <= 1.0

    @pytest.mark.asyncio
    async def test_encode_with_unicode_audio(self, svc, sample_audio_bytes):
        """Unicode item_id works for audio modality."""
        ue_id = "\u97f3\u58f0_001"  # 声音_001
        result = await svc.encode(sample_audio_bytes, "audio", item_id=ue_id)
        assert result.get("error") is None
        assert result["modality"] == "audio"
        assert result["item_id"] == ue_id

    @pytest.mark.asyncio
    async def test_cultural_context_detection(self):
        """CulturalContextModule detects CJK and Korean scripts.

        NOTE: enrich_context(context: dict, user_message: str, language_code: str)
        — first arg is the context dict, second is the user message string.
        """
        from ai.context.cultural_context import CulturalContextModule

        ccm = CulturalContextModule()

        # Chinese — enrich_context(context_dict, user_message_string)
        ctx = {}
        enriched = ccm.enrich_context(ctx, "\u4f60\u597d")  # 你好
        assert enriched.get("cultural_context", {}).get("region") == "east_asian"

        # English
        ctx2 = {}
        enriched2 = ccm.enrich_context(ctx2, "hello")
        assert enriched2.get("cultural_context", {}).get("region") == "western"

        # Korean
        ctx3 = {}
        enriched3 = ccm.enrich_context(ctx3, "\uc548\ub155\ud558\uc138\uc694")  # 안녕하세요
        assert enriched3.get("cultural_context", {}).get("region") == "east_asian"

        # Japanese
        ctx4 = {}
        enriched4 = ccm.enrich_context(ctx4, "\u3053\u3093\u306b\u3061\u306f")  # こんにちは
        assert enriched4.get("cultural_context", {}).get("region") == "east_asian"

    @pytest.mark.asyncio
    async def test_clear_items_after_multilingual(self, svc):
        """Clear items works after multilingual encodes."""
        await svc.clear_items()
        items = await svc.list_items()
        assert items["count"] == 0
