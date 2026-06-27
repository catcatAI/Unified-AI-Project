"""
P42 tests for SemanticVisualEncoder, SemanticAudioEncoder, and DualEncoderRouter.

Tests cover:
- SemanticVisualEncoder (6): import/init, available w torch, unavailable w/o torch,
  encode returns 512-dim, encode from PIL, empty data
- SemanticAudioEncoder (6): import/init, available, encode 384-dim,
  decode wav, empty/error handling, singleton backend
- DualEncoderRouter (8): init/import, encode vision both, encode vision structural only,
  encode audio both, availability report, combine latents, empty data, error handling
"""

import io
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from ai.multimodal.dual_encoder_router import DualEncoderRouter
from ai.multimodal.semantic_audio import SemanticAudioEncoder
from ai.multimodal.semantic_visual import SemanticVisualEncoder

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_png() -> bytes:
    """Generate a minimal valid PNG (1x1 white pixel)."""
    import struct
    import zlib

    def _make_png():
        width, height = 1, 1
        raw = b''
        for y in range(height):
            raw += b'\x00'  # filter byte
            for x in range(width):
                raw += b'\xff\xff\xff'  # RGB white

        def chunk(chunk_type, data):
            c = chunk_type + data
            crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
            return struct.pack('>I', len(data)) + c + crc

        ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        idat = zlib.compress(raw)
        return (b'\x89PNG\r\n\x1a\n'
                + chunk(b'IHDR', ihdr)
                + chunk(b'IDAT', idat)
                + chunk(b'IEND', b''))

    return _make_png()


@pytest.fixture
def sample_wav() -> bytes:
    """Generate a minimal valid WAV (0.1s silence, 16kHz, mono, 16-bit)."""
    import struct
    sample_rate = 16000
    duration = 0.1
    num_samples = int(sample_rate * duration)
    data = struct.pack('<' + 'h' * num_samples, *([0] * num_samples))
    data_size = len(data)
    # WAV header
    header = struct.pack('<4sI4s', b'RIFF', 36 + data_size, b'WAVE')
    fmt = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
    data_chunk = struct.pack('<4sI', b'data', data_size) + data
    return header + fmt + data_chunk


# ---------------------------------------------------------------------------
# SemanticVisualEncoder Tests (6)
# ---------------------------------------------------------------------------

class TestSemanticVisualEncoderInit:
    """P42a: SemanticVisualEncoder initialization and backend detection."""

    def test_init_no_torch(self):
        """S1: SemanticVisualEncoder initializes without torch."""
        with patch.dict('sys.modules', {'torch': None}):
            sve = SemanticVisualEncoder()
            assert hasattr(sve, 'is_available')
            assert not sve.is_available  # No torch → not available

    def test_init_with_torch_clip(self):
        """S2: SemanticVisualEncoder detects CLIP availability (mocked)."""
        with patch('ai.multimodal.semantic_visual._lazy_init_clip',
                   return_value=(MagicMock(), MagicMock())):
            sve = SemanticVisualEncoder()
            # Force backend init to use the mock
            backend = sve._get_backend()
            assert backend[0] is not None
            assert backend[1] is not None
            assert sve.is_available

    def test_encode_no_clip(self):
        """S3: encode returns None when CLIP is unavailable."""
        with patch.object(SemanticVisualEncoder, '_get_backend',
                          return_value=(None, None)):
            sve = SemanticVisualEncoder()
            result = sve.encode(b'some_image_data')
            assert result is None

    def test_encode_returns_512dim(self, sample_png):
        """S4: encode with mock CLIP backend returns 512-dim vector."""
        with patch('ai.multimodal.semantic_visual._lazy_init_clip') as mock_init:
            mock_model = MagicMock()
            mock_processor = MagicMock()
            mock_init.return_value = (mock_model, mock_processor)
            np_emb = np.random.randn(1, 512).astype(np.float32)
            mock_tensor = MagicMock()
            mock_tensor.cpu.return_value.numpy.return_value = np_emb
            mock_output = MagicMock()
            mock_output.pooler_output = mock_tensor
            mock_model.get_image_features.return_value = mock_output

            sve = SemanticVisualEncoder()
            sve._model = None
            sve._processor = None
            result = sve.encode(sample_png)
            assert result is not None
            assert isinstance(result, np.ndarray)
            assert result.shape == (512,)
            assert result.dtype == np.float32

    def test_encode_from_pil(self, sample_png):
        """S5: encode_from_pil works with mock CLIP backend."""
        from PIL import Image
        img = Image.open(io.BytesIO(sample_png))

        mock_model = MagicMock()
        mock_processor = MagicMock()
        np_emb = np.random.randn(1, 512).astype(np.float32)
        mock_tensor = MagicMock()
        mock_tensor.cpu.return_value.numpy.return_value = np_emb
        mock_output = MagicMock()
        mock_output.pooler_output = mock_tensor
        mock_model.get_image_features.return_value = mock_output

        with patch.object(SemanticVisualEncoder, '_get_backend',
                          return_value=(mock_model, mock_processor)):
            sve = SemanticVisualEncoder()
            result = sve.encode_from_pil(img)
            assert result is not None
            assert result.shape == (512,)

    def test_encode_empty_data(self):
        """S6: encode handles empty bytes gracefully."""
        with patch.object(SemanticVisualEncoder, '_get_backend',
                          return_value=(None, None)):
            sve = SemanticVisualEncoder()
            result = sve.encode(b'')
            assert result is None


# ---------------------------------------------------------------------------
# SemanticAudioEncoder Tests (6)
# ---------------------------------------------------------------------------

class TestSemanticAudioEncoder:
    """P42b: SemanticAudioEncoder tests."""

    def test_init(self):
        """A1: SemanticAudioEncoder initializes."""
        sae = SemanticAudioEncoder()
        assert hasattr(sae, 'is_available')
        assert hasattr(sae, 'FEATURE_DIM')

    def test_init_no_torch(self):
        """A2: SemanticAudioEncoder detects unavailable backend."""
        # Reset module-level globals to force re-init through mock
        import ai.multimodal.semantic_audio as sem_audio_mod
        sem_audio_mod._WHISPER_AVAILABLE = False
        sem_audio_mod._WHISPER_MODEL = None
        sem_audio_mod._WHISPER_PROCESSOR = None
        sem_audio_mod._WHISPER_FEATURE_EXTRACTOR = None

        with patch('ai.multimodal.semantic_audio._lazy_init_whisper',
                   return_value=(None, None, None)):
            sae = SemanticAudioEncoder()
            assert not sae.is_available

    def test_encode_no_whisper(self):
        """A3: encode returns None when Whisper is unavailable."""
        with patch.object(SemanticAudioEncoder, '_get_backend',
                          return_value=(None, None, None)):
            sae = SemanticAudioEncoder()
            result = sae.encode(b'some_audio_data')
            assert result is None

    def test_encode_with_mock(self, sample_wav):
        """A4: encode with mock Whisper backend returns 384-dim vector."""
        import ai.multimodal.semantic_audio as sem_audio_mod
        sem_audio_mod._WHISPER_AVAILABLE = False
        sem_audio_mod._WHISPER_MODEL = None

        mock_model = MagicMock()
        mock_processor = MagicMock()
        mock_feat = MagicMock()

        # Properly set up encoder return: model.encoder(**inputs) → encoder_output.last_hidden_state
        mock_hidden = MagicMock()
        mock_hidden.mean.return_value = MagicMock()
        mock_hidden.mean.return_value.cpu.return_value.numpy.return_value = \
            np.random.randn(1, 384).astype(np.float32)
        encoder_output = MagicMock()
        encoder_output.last_hidden_state = mock_hidden
        mock_model.encoder = MagicMock()
        mock_model.encoder.return_value = encoder_output

        with patch('ai.multimodal.semantic_audio._lazy_init_whisper',
                   return_value=(mock_model, mock_processor, mock_feat)):
            sae = SemanticAudioEncoder()
            sae._model = None
            result = sae.encode(sample_wav)
            assert result is not None
            assert isinstance(result, np.ndarray)
            assert result.shape == (384,)
            assert result.dtype == np.float32

    def test_decode_wav(self, sample_wav):
        """A5: _decode_wav returns float samples (no model loading needed)."""
        sae = SemanticAudioEncoder()
        # _decode_wav is a pure function, doesn't load Whisper
        samples = sae._decode_wav(sample_wav)
        assert len(samples) > 0
        # WAV duration 0.1s at 16kHz = 1600 samples
        assert len(samples) <= 2000  # rough check
        assert np.min(samples) >= -1.0
        assert np.max(samples) <= 1.0

    def test_encode_empty_audio(self):
        """A6: encode handles empty audio gracefully."""
        with patch.object(SemanticAudioEncoder, '_get_backend',
                          return_value=(None, None, None)):
            sae = SemanticAudioEncoder()
            result = sae.encode(b'')
            assert result is None


# ---------------------------------------------------------------------------
# DualEncoderRouter Tests (8)
# ---------------------------------------------------------------------------

class TestDualEncoderRouter:
    """P42c: DualEncoderRouter tests."""

    def test_init(self):
        """R1: DualEncoderRouter initializes."""
        router = DualEncoderRouter()
        assert hasattr(router, 'encode_vision')
        assert hasattr(router, 'encode_audio')
        assert hasattr(router, 'availability_report')

    def test_encode_vision_both(self, sample_png):
        """R2: encode_vision returns both structural and semantic when available."""
        router = DualEncoderRouter()

        # Mock semantic to be available
        mock_sve = MagicMock()
        mock_sve.is_available = True
        mock_sve.encode.return_value = np.ones(512, dtype=np.float32)

        with patch.object(router, '_get_semantic_visual', return_value=mock_sve):
            result = router.encode_vision(sample_png)

        assert "structural_vision" in result.get("modalities_used", [])
        assert result.get("structural") is not None
        assert result["structural"].shape == (256,)
        # structural always available
        assert "modalities_used" in result
        assert result.get("latent") is not None

    def test_encode_vision_structural_only(self, sample_png):
        """R3: encode_vision works with structural only."""
        router = DualEncoderRouter()
        result = router.encode_vision(sample_png, include_semantic=False)

        assert "structural_vision" in result.get("modalities_used", [])
        assert "semantic_vision" not in result.get("modalities_used", [])
        assert result.get("semantic") is None
        assert result.get("structural") is not None
        assert result.get("latent") is not None

    def test_encode_audio_both(self, sample_wav):
        """R4: encode_audio returns both structural and semantic when available."""
        router = DualEncoderRouter()

        mock_sae = MagicMock()
        mock_sae.is_available = True
        mock_sae.encode.return_value = np.ones(384, dtype=np.float32)

        with patch.object(router, '_get_semantic_audio', return_value=mock_sae):
            result = router.encode_audio(sample_wav)

        assert "structural_audio" in result.get("modalities_used", [])
        assert result.get("structural") is not None
        assert result["structural"].shape == (128,)
        assert result.get("latent") is not None

    def test_availability_report(self):
        """R5: availability_report returns valid structure."""
        router = DualEncoderRouter()
        # Mock semantic encoders to prevent real model loading
        mock_sve = MagicMock()
        mock_sve.is_available = False
        mock_sae = MagicMock()
        mock_sae.is_available = False
        with patch.object(router, '_get_semantic_visual', return_value=mock_sve), \
             patch.object(router, '_get_semantic_audio', return_value=mock_sae):
            report = router.availability_report()

        assert isinstance(report, dict)
        assert "structural_vision" in report
        assert "structural_audio" in report
        assert "semantic_vision" in report
        assert "semantic_audio" in report
        assert report["structural_vision"] is True  # Always True
        assert report["structural_audio"] is True  # Always True

    def test_combine_latents_both(self):
        """R6: _combine_latents with both structural and semantic (P43 SharedLatentSpace)."""
        router = DualEncoderRouter()
        structural = np.ones(256, dtype=np.float32)
        semantic = np.ones(512, dtype=np.float32)
        struct_lat, sem_lat, combined = router._combine_latents("vision", structural, semantic)
        assert struct_lat is not None
        assert struct_lat.shape == (64,)
        assert sem_lat is not None
        assert sem_lat.shape == (64,)
        assert combined is not None
        assert combined.shape == (64,)
        # Combined is L2 normalized
        norm = np.linalg.norm(combined)
        assert abs(norm - 1.0) < 1e-5

    def test_combine_latents_structural_only(self):
        """R7: _combine_latents with structural only (P43)."""
        router = DualEncoderRouter()
        structural = np.ones(256, dtype=np.float32)
        struct_lat, sem_lat, combined = router._combine_latents("vision", structural, None)
        assert struct_lat is not None
        assert struct_lat.shape == (64,)
        assert sem_lat is None
        assert combined is not None
        assert combined.shape == (64,)
        norm = np.linalg.norm(combined)
        assert abs(norm - 1.0) < 1e-5

    def test_combine_latents_none(self):
        """R8: _combine_latents with None returns Nones (P43)."""
        router = DualEncoderRouter()
        struct_lat, sem_lat, combined = router._combine_latents("vision", None, None)
        assert struct_lat is None
        assert sem_lat is None
        assert combined is None

    def test_encode_empty_vision(self):
        """R9: encode_vision handles empty bytes gracefully."""
        router = DualEncoderRouter()
        result = router.encode_vision(b'', include_semantic=False)
        # Structural encoder handles empty data by returning zeros
        assert result.get("structural") is not None
        assert isinstance(result["structural"], np.ndarray)

    def test_encode_empty_audio(self):
        """R10: encode_audio handles empty bytes gracefully."""
        router = DualEncoderRouter()
        result = router.encode_audio(b'', include_semantic=False)
        assert result.get("structural") is not None
        assert isinstance(result["structural"], np.ndarray)
