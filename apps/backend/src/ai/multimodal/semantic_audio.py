"""
Semantic Audio Encoder — Whisper encoder-based semantic feature extraction (P42).

Uses HuggingFace transformers' WhisperModel to extract encoder hidden states
as semantic audio features. Falls back gracefully to None when torch/transformers
is unavailable.

Feature pipeline:
  1. Whisper encoder → mean-pooled hidden states → semantic vector (512-dim)
  2. Falls back to None when no torch/transformers available

This runs IN PARALLEL with AudioSpectralEncoder (128-dim MFCC/spectral features).
The DualEncoderRouter combines both outputs.
"""

import io
import logging
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Lazy-load torch and Whisper with guarded imports
_WHISPER_AVAILABLE = False
_WHISPER_MODEL = None
_WHISPER_PROCESSOR = None
_WHISPER_FEATURE_EXTRACTOR = None


def _lazy_init_whisper():
    """Try to load Whisper model and processor. Returns (model, processor) or (None, None)."""
    global _WHISPER_AVAILABLE, _WHISPER_MODEL, _WHISPER_PROCESSOR, _WHISPER_FEATURE_EXTRACTOR
    if _WHISPER_AVAILABLE:
        return _WHISPER_MODEL, _WHISPER_PROCESSOR, _WHISPER_FEATURE_EXTRACTOR
    try:
        import torch
        import transformers
        from transformers import WhisperFeatureExtractor, WhisperModel, WhisperProcessor

        model_name = "openai/whisper-tiny"  # Smallest Whisper for speed
        _WHISPER_MODEL = WhisperModel.from_pretrained(model_name)
        _WHISPER_PROCESSOR = WhisperProcessor.from_pretrained(model_name)
        _WHISPER_FEATURE_EXTRACTOR = WhisperFeatureExtractor.from_pretrained(model_name)
        _WHISPER_MODEL.eval()
        if torch.cuda.is_available():
            _WHISPER_MODEL = _WHISPER_MODEL.cuda()
        _WHISPER_AVAILABLE = True
        logger.info("SemanticAudioEncoder: Whisper loaded (%s)", model_name)
    except Exception as e:
        logger.warning("SemanticAudioEncoder: Whisper load failed: %s", e)
        _WHISPER_AVAILABLE = False
        _WHISPER_MODEL = None
        _WHISPER_PROCESSOR = None
        _WHISPER_FEATURE_EXTRACTOR = None
    return _WHISPER_MODEL, _WHISPER_PROCESSOR, _WHISPER_FEATURE_EXTRACTOR


class SemanticAudioEncoder:
    """Encodes audio into semantic vectors using Whisper encoder.

    Parallel to AudioSpectralEncoder (128-dim MFCC/spectral features).
    Semantic vectors capture high-level audio content (speech content,
    environmental sounds, music characteristics).

    Features:
    - torch-guarded lazy initialization
    - Whisper tiny encoder mean-pooled hidden states → semantic vector
    - Graceful fallback: is_available = False when no torch/transformers
    - Singleton model instance
    - Supports WAV and raw PCM input
    """

    FEATURE_DIM: int = 384  # Whisper tiny encoder dim
    SAMPLE_RATE: int = 16000

    def __init__(self):
        self._model, self._processor, self._feature_extractor = None, None, None

    @property
    def is_available(self) -> bool:
        """Whether the Whisper backend is available."""
        model, _, _ = self._get_backend()
        return model is not None

    def _get_backend(self) -> Tuple[Optional[object], Optional[object], Optional[object]]:
        """Get or lazy-init Whisper backend."""
        if self._model is None:
            self._model, self._processor, self._feature_extractor = _lazy_init_whisper()
        return self._model, self._processor, self._feature_extractor

    def encode(self, audio_data: bytes) -> Optional[np.ndarray]:
        """Encode audio bytes into a semantic vector using Whisper encoder.

        Args:
            audio_data: Raw audio bytes (WAV or raw PCM)

        Returns:
            Float32 numpy array of FEATURE_DIM dims, or None if unavailable/error.
        """
        model, processor, feat_extractor = self._get_backend()
        if model is None or processor is None:
            return None
        try:
            import torch

            samples = self._decode_audio(audio_data)
            if len(samples) < 160:  # Minimum 10ms
                return None

            # Truncate to 30s max (Whisper limit)
            if len(samples) > self.SAMPLE_RATE * 30:
                samples = samples[:self.SAMPLE_RATE * 30]

            # Extract log-mel spectrogram features
            if feat_extractor is not None:
                inputs = feat_extractor(samples, sampling_rate=self.SAMPLE_RATE,
                                        return_tensors="pt")
            else:
                # Fallback: use processor
                inputs = processor(samples, sampling_rate=self.SAMPLE_RATE,
                                   return_tensors="pt")

            with torch.no_grad():
                encoder_outputs = model.encoder(**inputs)
                # Mean pool over time dimension
                hidden = encoder_outputs.last_hidden_state  # (1, seq_len, 384)
                pooled = hidden.mean(dim=1)  # (1, 384)

            vec = pooled.cpu().numpy().flatten().astype(np.float32)
            # L2 normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
        except Exception as e:
            logger.debug("SemanticAudioEncoder encode failed: %s", e)
            return None

    def _decode_audio(self, audio_data: bytes) -> np.ndarray:
        """Decode audio bytes to float samples [-1, 1]."""
        if not audio_data:
            return np.array([], dtype=np.float32)
        # WAV format detection
        if audio_data[:4] == b"RIFF":
            return self._decode_wav(audio_data)
        # Assume raw PCM 16-bit
        try:
            samples = np.frombuffer(
                audio_data[:len(audio_data) - len(audio_data) % 2],
                dtype=np.int16
            ).astype(np.float32) / 32768.0
            return samples
        except Exception as e:
            logger.debug("Failed to decode raw PCM audio: %s", e)
            return np.array([], dtype=np.float32)

    def _decode_wav(self, data: bytes) -> np.ndarray:
        """Decode WAV file bytes to float samples."""
        try:
            import wave
            with io.BytesIO(data) as buf:
                with wave.open(buf, "rb") as wf:
                    frames = wf.readframes(wf.getnframes())
                    sampwidth = wf.getsampwidth()
                    nchannels = wf.getnchannels()
            if sampwidth == 2:
                dtype = np.int16
            elif sampwidth == 1:
                dtype = np.uint8
            else:
                return np.array([], dtype=np.float32)
            samples = np.frombuffer(frames, dtype=dtype).astype(np.float32)
            if sampwidth == 2:
                samples /= 32768.0
            elif sampwidth == 1:
                samples = (samples - 128.0) / 128.0
            if nchannels > 1:
                samples = samples.reshape(-1, nchannels).mean(axis=1)
            return samples
        except Exception as e:
            logger.debug("Failed to decode WAV audio: %s", e)
            return np.array([], dtype=np.float32)
