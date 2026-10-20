# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import time
from typing import Any, Dict

import numpy as np

logger = logging.getLogger(__name__)


def _hz_to_mel(hz: float) -> float:
    """Hz → mel (the standard 2595 log10 formula)."""
    value: float = float(2595.0 * np.log10(1.0 + float(hz) / 700.0))
    return value


def _mel_to_hz(mel: np.ndarray) -> np.ndarray:
    """mel → Hz."""
    return 700.0 * (10.0 ** (np.asarray(mel, dtype=np.float64) / 2595.0) - 1.0)


class AudioProcessing:
    """
    Audio processing module for Angela AI.
    Handles Voice Activity Detection (VAD) and feature extraction.
    """

    def __init__(self, sample_rate: int = 16000, energy_threshold: float = 0.01):
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        logger.info(
            f"AudioProcessing initialized (SR: {sample_rate}, Threshold: {energy_threshold})"
        )

    def detect_voice_activity(self, audio_chunk: bytes) -> bool:
        """
        Simple energy-based VAD.

        Args:
            audio_chunk: Raw bytes (assumed 16-bit PCM)

        Returns:
            True if voice is detected, False otherwise.
        """
        if not audio_chunk:
            return False

        try:
            # Convert bytes to numpy array (assumes 16-bit PCM)
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0

            # Calculate root mean square (RMS) energy
            energy = float(np.sqrt(np.mean(np.square(audio_data))))

            is_active = energy > self.energy_threshold
            if is_active:
                logger.debug(f"[AudioProcessing] VAD Active: Energy={energy:.4f}")

            return is_active
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"VAD Error: {e}", exc_info=True)
            return False

    def extract_features(self, audio_chunk: bytes) -> Dict[str, Any]:
        """Extract spectral features: energy, pitch, brightness, MFCC.

        The old implementation returned energy + peak only, and said so
        ("Placeholder for spectral features like MFCC"). With nothing but
        energy the encoders could not tell a bright voice from a dark one, nor
        a high pitch from a low one — every non-silent clip collapsed into
        "loud". These are the features the audio path actually needs, and
        they are computed with numpy only (no new dependency).

        Returns (all values are 0..1 unless noted):
          energy            RMS energy
          peak              peak amplitude
          zcr               zero-crossing rate
          pitch_hz          dominant frequency (0 when the clip is silent)
          pitch_norm        dominant frequency mapped into 0..1 (0..1 kHz)
          brightness        spectral centroid, normalised by the Nyquist rate
          rolloff           85 % roll-off frequency, normalised
          flux              spectral flux (frame-to-frame change)
          mfcc              13 mel-frequency cepstral coefficients
        """
        if not audio_chunk:
            return {
                "energy": 0.0,
                "peak": 0.0,
                "zcr": 0.0,
                "pitch_hz": 0.0,
                "pitch_norm": 0.0,
                "brightness": 0.0,
                "rolloff": 0.0,
                "flux": 0.0,
                "mfcc": [],
                "timestamp": time.time(),
            }

        audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        energy = float(np.sqrt(np.mean(np.square(audio_data))))
        peak = float(np.max(np.abs(audio_data)))
        features: Dict[str, Any] = {
            "energy": energy,
            "peak": peak,
            "zcr": 0.0,
            "pitch_hz": 0.0,
            "pitch_norm": 0.0,
            "brightness": 0.0,
            "rolloff": 0.0,
            "flux": 0.0,
            "mfcc": [],
            "timestamp": time.time(),
        }
        if audio_data.size < self._FRAME_SIZE or energy <= 0.0:
            return features

        try:
            spectrum, freqs = self._spectrum(audio_data)
            power = spectrum**2
            total = float(power.sum())
            if total <= 0.0:
                return features

            # Brightness: where the energy sits in the spectrum.
            centroid = float((power * freqs).sum() / total)
            nyquist = self.sample_rate / 2.0
            features["brightness"] = float(min(1.0, centroid / nyquist))

            # Roll-off: the frequency below which 85 % of the energy lies.
            cumulative = np.cumsum(power) / total
            rolloff_idx = int(np.searchsorted(cumulative, 0.85))
            rolloff_idx = min(rolloff_idx, len(freqs) - 1)
            features["rolloff"] = float(min(1.0, freqs[rolloff_idx] / nyquist))

            # Dominant frequency (a cheap pitch proxy).
            dominant = float(freqs[int(np.argmax(spectrum))])
            features["pitch_hz"] = dominant
            features["pitch_norm"] = float(min(1.0, dominant / 1000.0))

            # Zero-crossing rate: a cheap voiced/unvoiced proxy.
            signs = np.sign(audio_data)
            crossings = int(np.count_nonzero(signs[1:] != signs[:-1]))
            features["zcr"] = float(crossings / max(1, audio_data.size - 1))

            # Spectral flux: how much the spectrum changes frame to frame.
            features["flux"] = self._spectral_flux(audio_data)

            # MFCC: log-mel energies → cepstral coefficients.
            features["mfcc"] = self._mfcc(spectrum, freqs)
        except Exception as exc:  # pragma: no cover - numerical degradation
            logger.debug("Spectral feature extraction failed: %s", exc)
        return features

    # ------------------------------------------------------------------
    # Spectral helpers
    # ------------------------------------------------------------------
    _FRAME_SIZE = 512
    _HOP_SIZE = 256
    _MEL_BANDS = 26
    _MFCC_COEFFS = 13

    def _frames(self, audio_data: np.ndarray) -> np.ndarray:
        """Split the signal into overlapping frames (zero-padded at the end)."""
        size = self._FRAME_SIZE
        hop = self._HOP_SIZE
        if audio_data.size < size:
            padded = np.zeros(size, dtype=np.float32)
            padded[: audio_data.size] = audio_data
            return padded[np.newaxis, :]
        count = 1 + (audio_data.size - size) // hop
        indices = np.arange(size)[np.newaxis, :] + hop * np.arange(count)[:, np.newaxis]
        frames: np.ndarray = audio_data[indices]
        return frames

    def _spectrum(self, audio_data: np.ndarray):
        """The averaged power spectrum and its frequency axis."""
        frames = self._frames(audio_data)
        window = np.hanning(frames.shape[1]).astype(np.float32)
        spectrum = np.abs(np.fft.rfft(frames * window, axis=1)).mean(axis=0)
        freqs = np.fft.rfftfreq(frames.shape[1], d=1.0 / self.sample_rate)
        return spectrum, freqs

    def _spectral_flux(self, audio_data: np.ndarray) -> float:
        """Frame-to-frame spectral change, normalised to 0..1."""
        frames = self._frames(audio_data)
        window = np.hanning(frames.shape[1]).astype(np.float32)
        mags = np.abs(np.fft.rfft(frames * window, axis=1))
        if mags.shape[0] < 2:
            return 0.0
        diff = np.diff(mags, axis=0)
        flux = float(np.sum(np.maximum(diff, 0.0)) / max(1.0, float(mags.sum())))
        return float(min(1.0, flux))

    def _mel_filterbank(self, freqs: np.ndarray) -> np.ndarray:
        """A simple triangular mel filterbank over the frequency axis."""
        bands = self._MEL_BANDS
        nyquist = self.sample_rate / 2.0
        mel_max = _hz_to_mel(nyquist)
        points = mel_max * np.linspace(0.0, 1.0, bands + 2)
        hz = _mel_to_hz(points)
        filterbank = np.zeros((bands, len(freqs)), dtype=np.float32)
        for band in range(bands):
            left, center, right = hz[band], hz[band + 1], hz[band + 2]
            if center <= 0:
                continue
            lower = (freqs - left) / max(1e-9, center - left)
            upper = (right - freqs) / max(1e-9, right - center)
            filterbank[band] = np.clip(np.minimum(lower, upper), 0.0, None)
        return filterbank

    def _mfcc(self, spectrum: np.ndarray, freqs: np.ndarray) -> list:
        """13 mel-frequency cepstral coefficients (DCT-II of the log-mel)."""
        filterbank = self._mel_filterbank(freqs)
        energies = filterbank @ (spectrum**2)
        log_energies = np.log(energies + 1e-10)
        coeffs = self._dct2(log_energies)
        return [float(c) for c in coeffs[: self._MFCC_COEFFS]]

    @staticmethod
    def _dct2(values: np.ndarray) -> np.ndarray:
        """DCT-II (orthonormal-ish) of a 1-D array."""
        n = len(values)
        if n == 0:
            return np.zeros(0, dtype=np.float64)
        k = np.arange(n)[:, np.newaxis]
        i = np.arange(n)[np.newaxis, :]
        matrix = np.cos(np.pi * k * (2 * i + 1) / (2 * n))
        result: np.ndarray = matrix @ values / np.sqrt(n)
        return result
