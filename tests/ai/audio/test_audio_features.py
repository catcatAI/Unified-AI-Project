"""
ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
The audio features must be real spectral features.

``AudioProcessing.extract_features`` used to return energy + peak only and
called itself a "Placeholder for spectral features like MFCC". With nothing
but energy the audio encoder could not tell a bright voice from a dark one,
or a high pitch from a low one — every non-silent clip collapsed into
"loud".

These tests pin the extractor against synthetic signals with a known
frequency, so a regression (a broken FFT, a mis-scaled mel filterbank) fails
here instead of silently degrading the audio path.
"""

import numpy as np
import pytest
from ai.audio.audio_processing import AudioProcessing


def _tone(freq: float, seconds: float = 1.0, sample_rate: int = 16000, amp: float = 0.5) -> bytes:
    t = np.arange(int(seconds * sample_rate)) / sample_rate
    signal = (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    return (signal * 32767).astype(np.int16).tobytes()


def _noise(seconds: float = 1.0, sample_rate: int = 16000, amp: float = 0.05) -> bytes:
    rng = np.random.RandomState(0)
    signal = (rng.randn(int(seconds * sample_rate)) * amp).astype(np.float32)
    return (signal * 32767).astype(np.int16).tobytes()


class TestSpectralFeatures:
    def test_empty_input_is_handled(self):
        features = AudioProcessing().extract_features(b"")
        assert features["energy"] == 0.0
        assert features["mfcc"] == []

    def test_a_short_clip_does_not_crash(self):
        features = AudioProcessing().extract_features(_tone(440.0, seconds=0.005))
        assert "energy" in features
        assert "mfcc" in features

    def test_the_dominant_frequency_is_found(self):
        ap = AudioProcessing()
        for freq in (220.0, 440.0, 1200.0):
            features = ap.extract_features(_tone(freq))
            assert (
                abs(features["pitch_hz"] - freq) < freq * 0.1
            ), f"expected ~{freq} Hz, measured {features['pitch_hz']:.1f} Hz"

    def test_a_higher_tone_is_brighter_and_crosses_more_often(self):
        ap = AudioProcessing()
        low = ap.extract_features(_tone(220.0))
        high = ap.extract_features(_tone(1200.0))
        assert high["brightness"] > low["brightness"]
        assert high["zcr"] > low["zcr"]

    def test_noise_is_the_brightest_and_moves_the_most(self):
        ap = AudioProcessing()
        tone = ap.extract_features(_tone(440.0))
        noise = ap.extract_features(_noise())
        assert noise["brightness"] > tone["brightness"]
        assert noise["flux"] > tone["flux"]

    def test_the_mfcc_has_thirteen_coefficients(self):
        features = AudioProcessing().extract_features(_tone(440.0))
        assert len(features["mfcc"]) == 13

    def test_energy_and_peak_stay_meaningful(self):
        ap = AudioProcessing()
        loud = ap.extract_features(_tone(440.0, amp=0.8))
        quiet = ap.extract_features(_tone(440.0, amp=0.05))
        assert loud["energy"] > quiet["energy"]
        assert loud["peak"] > quiet["peak"]
