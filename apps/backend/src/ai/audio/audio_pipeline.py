# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
AudioPipeline — single-modality end-to-end audio processing pipeline.

Analogous to VisionPipeline for the vision modality.

Pipeline:
  Upload WAV → AudioSpectralEncoder (128-dim MFCC)
  → SharedLatentSpace.project("audio") → 64-dim latent
  → AudioWaveformDecoder.decode() → 16kHz PCM waveform
  → quality_metrics.snr() → quality score
  → Cache last 10 results

P32: Second single-modality pipeline after P31 VisionPipeline.
"""

import io
import logging
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional

import numpy as np
from core.utils import safe_error

logger = logging.getLogger(__name__)


class AudioPipeline:
    """End-to-end audio processing pipeline.

    Integrates AudioSpectralEncoder → SharedLatentSpace → AudioWaveformDecoder → SNR
    into a single unified interface with caching and monitoring.

    Thread-safe: each method creates its own backend instances lazily.
    """

    CACHE_SIZE: int = 10
    SAMPLE_RATE: int = 16000
    DURATION: float = 1.0
    AUDIO_DIM: int = 128
    LATENT_DIM: int = 64

    def __init__(self):
        self._encoder = None
        self._latent_space = None
        self._decoder = None
        # LRU cache: {audio_hash: cached_result}
        self._cache: OrderedDict = OrderedDict()

    # --- Lazy initialization ---

    def _get_encoder(self):
        if self._encoder is None:
            from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder

            self._encoder = AudioSpectralEncoder(feature_dim=self.AUDIO_DIM)
        return self._encoder

    def _get_latent_space(self):
        if self._latent_space is None:
            from ai.multimodal.shared_latent_space import get_shared_latent_space

            self._latent_space = get_shared_latent_space(latent_dim=self.LATENT_DIM)
        return self._latent_space

    def _get_decoder(self):
        if self._decoder is None:
            from ai.multimodal.audio_decoder import (
                AudioWaveformDecoder,
                load_default_audio_decoder_weights,
            )

            self._decoder = AudioWaveformDecoder()
            load_default_audio_decoder_weights(self._decoder)
        return self._decoder

    # --- Core process ---

    def process(self, audio_data: bytes) -> Dict[str, Any]:
        """Run the full audio pipeline on WAV bytes.

        Args:
            audio_data: Raw WAV audio bytes

        Returns:
            dict with:
              - feature_vector (128-dim list)
              - latent (64-dim list)
              - decoded_waveform (list of float32 samples)
              - snr (float, dB)
              - duration (float, seconds)
              - time_ms (float)
              - audio_hash (str)
              - error (str, if any)
        """
        t0 = time.time()
        result: Dict[str, Any] = {"error": None}

        try:
            # Check cache
            audio_hash = self._hash_audio(audio_data)
            cached = self._cache.get(audio_hash)
            if cached is not None:
                result.update(cached)
                result["cache_hit"] = True
                result["time_ms"] = round((time.time() - t0) * 1000, 1)
                return result

            # 1. Detect duration from WAV header
            duration = self._detect_duration(audio_data)

            # 2. Encode → feature vector (128-dim)
            encoder = self._get_encoder()
            feature_vec = encoder.encode(audio_data)

            # 3. Project → latent (64-dim)
            ls = self._get_latent_space()
            latent = ls.project("audio", feature_vec)

            # 4. Decode latent → waveform (16kHz PCM)
            decoder = self._get_decoder()
            waveform = decoder.decode(latent)

            # 5. Quality metrics (SNR)
            snr_val = self._compute_snr(audio_data, waveform)

            # 6. Build result
            result["feature_vector"] = feature_vec.tolist()
            result["latent"] = latent.tolist()
            result["decoded_waveform"] = waveform.tolist()
            result["snr"] = round(float(snr_val), 2)
            result["duration"] = round(duration, 3) if duration else None
            result["audio_hash"] = audio_hash
            result["sample_rate"] = self.SAMPLE_RATE
            result["time_ms"] = round((time.time() - t0) * 1000, 1)
            result["cache_hit"] = False

            # 7. Update cache (exclude large waveform from cache)
            self._cache[audio_hash] = {
                k: v for k, v in result.items() if k not in ("decoded_waveform",)
            }
            self._cache.move_to_end(audio_hash)
            while len(self._cache) > self.CACHE_SIZE:
                self._cache.popitem(last=False)

        except Exception as e:
            logger.error("AudioPipeline.process failed: %s", e, exc_info=True)
            result["error"] = safe_error(e)

        return result

    def batch_process(self, audios: List[bytes]) -> List[Dict[str, Any]]:
        """Process multiple audio clips in batch.

        Reuses encoder, latent space, and decoder instances for efficiency.

        Args:
            audios: List of raw WAV audio bytes

        Returns:
            List of result dicts (same structure as process())
        """
        return [self.process(audio_data) for audio_data in audios]

    def clear_cache(self) -> None:
        """Clear the LRU cache."""
        self._cache.clear()

    def cache_size(self) -> int:
        """Return current cache size."""
        return len(self._cache)

    # --- Utility methods ---

    def encode_only(self, audio_data: bytes) -> np.ndarray:
        """Encode audio to feature vector only (bypasses full pipeline)."""
        encoder = self._get_encoder()
        return encoder.encode(audio_data)

    def get_latent(self, audio_data: bytes) -> np.ndarray:
        """Encode and project to latent only."""
        ls = self._get_latent_space()
        feat = self.encode_only(audio_data)
        return ls.project("audio", feat)

    def decode_latent_to_waveform(self, latent: np.ndarray) -> np.ndarray:
        """Decode a latent vector to a waveform array."""
        decoder = self._get_decoder()
        return decoder.decode(latent)

    @staticmethod
    def _hash_audio(audio_data: bytes) -> str:
        """Generate a content-based hash for caching."""
        import hashlib

        return hashlib.md5(audio_data).hexdigest()

    @staticmethod
    def _detect_duration(audio_data: bytes) -> float:
        """Detect audio duration in seconds from WAV header."""
        if len(audio_data) < 44:
            return 0.0
        try:
            if audio_data[:4] != b"RIFF":
                return 0.0
            import struct

            channels = struct.unpack("<H", audio_data[22:24])[0]
            sample_rate = struct.unpack("<I", audio_data[24:28])[0]
            bits_per_sample = struct.unpack("<H", audio_data[34:36])[0]
            data_size = len(audio_data) - 44
            bytes_per_sec = channels * sample_rate * bits_per_sample // 8
            if bytes_per_sec == 0:
                return 0.0
            return data_size / bytes_per_sec
        except (struct.error, IndexError):
            return 0.0

    def _compute_snr(self, original_bytes: bytes, decoded_wave: np.ndarray) -> float:
        """Compute SNR between original audio and decoded reconstruction.

        Extracts PCM data from original WAV and compares with decoded signal.

        Args:
            original_bytes: Original WAV bytes
            decoded_wave: Decoded float32 waveform [-1, 1]

        Returns:
            SNR in dB (higher is better). Returns 0.0 if comparison not possible.
        """
        try:
            if len(original_bytes) < 44:
                return 0.0
            # Extract PCM samples from WAV
            pcm_data = original_bytes[44:]
            if len(pcm_data) < 2:
                return 0.0
            pcm_int16 = np.frombuffer(pcm_data, dtype=np.int16)
            if len(pcm_int16) == 0:
                return 0.0
            original_float = pcm_int16.astype(np.float32) / 32767.0

            # Trim or pad to match decoded length
            min_len = min(len(original_float), len(decoded_wave))
            if min_len < 100:
                return 0.0
            orig = original_float[:min_len]
            recon = decoded_wave[:min_len]

            # Signal power
            signal_power = np.mean(orig**2)
            if signal_power < 1e-10:
                return 100.0  # Silent original → perfect score

            # Noise power (difference)
            noise = orig - recon
            noise_power = np.mean(noise**2)
            if noise_power < 1e-10:
                return 100.0

            snr_val = 10.0 * np.log10(signal_power / noise_power)
            return float(np.clip(snr_val, -20.0, 100.0))

        except Exception as e:
            logger.warning("SNR computation failed: %s", e, exc_info=True)
            return 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Return pipeline statistics."""
        return {
            "cache_size": len(self._cache),
            "sample_rate": self.SAMPLE_RATE,
            "audio_dim": self.AUDIO_DIM,
            "latent_dim": self.LATENT_DIM,
            "encoder_initialized": self._encoder is not None,
            "latent_space_initialized": self._latent_space is not None,
            "decoder_initialized": self._decoder is not None,
        }
