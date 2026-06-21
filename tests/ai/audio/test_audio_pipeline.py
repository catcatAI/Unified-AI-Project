"""
P32: Tests for AudioPipeline and AudioQualityMonitor.

Tests cover:
- AudioPipeline.process() — full end-to-end pipeline
- AudioPipeline.encode_only() — encode bypass
- AudioPipeline.get_latent() — encode + project only
- AudioPipeline.batch_process() — batch processing
- AudioPipeline caching (LRU, clear, cache_size)
- AudioPipeline SNR computation
- AudioPipeline.get_stats()
- AudioQualityMonitor.record() + report()
- AudioQualityMonitor.quality_trend()
- AudioService.encode_with_pipeline()
- AudioService.batch_encode()

Total: 20 tests
"""

import io
import sys
import struct
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))

from ai.audio.audio_pipeline import AudioPipeline
from ai.audio.quality_monitor import AudioQualityMonitor


def _sample_wav_bytes(duration_samples: int = 8000, freq: float = 440.0,
                      sample_rate: int = 16000) -> bytes:
    """Generate a simple WAV file with a sine wave for testing."""
    t = np.arange(duration_samples, dtype=np.float32) / sample_rate
    signal = (np.sin(2 * np.pi * freq * t) * 0.5).astype(np.float32)
    int16 = (np.clip(signal, -1.0, 1.0) * 32767).astype(np.int16)
    data = int16.tobytes()

    buf = io.BytesIO()
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + len(data)))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))          # chunk size
    buf.write(struct.pack("<H", 1))            # PCM
    buf.write(struct.pack("<H", 1))            # mono
    buf.write(struct.pack("<I", sample_rate))
    buf.write(struct.pack("<I", sample_rate * 2))  # byte rate
    buf.write(struct.pack("<H", 2))            # block align
    buf.write(struct.pack("<H", 16))           # bits per sample
    buf.write(b"data")
    buf.write(struct.pack("<I", len(data)))
    buf.write(data)
    return buf.getvalue()


@pytest.fixture
def pipeline():
    return AudioPipeline()


@pytest.fixture
def monitor():
    return AudioQualityMonitor(max_history=100)


class TestAudioPipelineProcess:
    """P32 T1-T5: Core pipeline processing tests (5 tests)."""

    def test_process_returns_all_fields(self, pipeline):
        """T1: process() returns all expected fields."""
        data = _sample_wav_bytes()
        result = pipeline.process(data)
        assert "error" not in result or result["error"] is None, result.get("error")
        assert "feature_vector" in result
        assert len(result["feature_vector"]) == 128  # AUDIO_DIM
        assert "latent" in result
        assert len(result["latent"]) == 64  # LATENT_DIM
        assert "decoded_waveform" in result
        assert "snr" in result
        assert "time_ms" in result
        assert "audio_hash" in result

    def test_process_different_audio_gives_different_latent(self, pipeline):
        """T2: Different audio produces different latent vectors."""
        a1 = _sample_wav_bytes(freq=440.0)
        a2 = _sample_wav_bytes(freq=880.0)  # Different frequency
        r1 = pipeline.process(a1)
        r2 = pipeline.process(a2)
        assert r1["latent"] != r2["latent"]

    def test_process_caches_identical_audio(self, pipeline):
        """T3: Same audio returns cached result on second call."""
        data = _sample_wav_bytes()
        r1 = pipeline.process(data)
        assert not r1.get("cache_hit", False)
        r2 = pipeline.process(data)
        assert r2.get("cache_hit", False)

    def test_process_empty_data_returns_error(self, pipeline):
        """T4: Empty audio data returns gracefully."""
        result = pipeline.process(b"")
        assert "error" in result

    def test_process_invalid_data_returns_error(self, pipeline):
        """T4b: Invalid audio data returns gracefully."""
        result = pipeline.process(b"not_audio_data")
        assert "error" in result


class TestAudioPipelineUtility:
    """P32 T6-T9: Utility method tests (4 tests)."""

    def test_encode_only_returns_vector(self, pipeline):
        """T6: encode_only returns 128-dim feature vector."""
        data = _sample_wav_bytes()
        vec = pipeline.encode_only(data)
        assert len(vec) == 128

    def test_get_latent_returns_64_dim(self, pipeline):
        """T7: get_latent returns 64-dim latent."""
        data = _sample_wav_bytes()
        latent = pipeline.get_latent(data)
        assert len(latent) == 64

    def test_batch_process_returns_list(self, pipeline):
        """T8: batch_process returns list of results."""
        audios = [_sample_wav_bytes() for _ in range(3)]
        results = pipeline.batch_process(audios)
        assert len(results) == 3
        for r in results:
            assert "feature_vector" in r

    def test_detect_duration(self, pipeline):
        """T9: _detect_duration returns correct duration."""
        data = _sample_wav_bytes(duration_samples=8000)  # 0.5s at 16kHz
        duration = pipeline._detect_duration(data)
        assert abs(duration - 0.5) < 0.05


class TestAudioPipelineCache:
    """P32 T10-T12: Cache tests (3 tests)."""

    def test_cache_size_starts_at_zero(self, pipeline):
        """T10: Cache starts empty."""
        assert pipeline.cache_size() == 0

    def test_cache_size_increases_after_process(self, pipeline):
        """T11: Cache grows after processing audio."""
        pipeline.process(_sample_wav_bytes())
        assert pipeline.cache_size() == 1

    def test_clear_cache_empties(self, pipeline):
        """T12: Clear cache resets to zero."""
        pipeline.process(_sample_wav_bytes())
        pipeline.clear_cache()
        assert pipeline.cache_size() == 0


class TestAudioPipelineStats:
    """P32 T13-T14: Stats and SNR tests (2 tests)."""

    def test_get_stats_returns_fields(self, pipeline):
        """T13: get_stats returns all expected fields."""
        stats = pipeline.get_stats()
        assert "cache_size" in stats
        assert "sample_rate" in stats
        assert "audio_dim" in stats
        assert "latent_dim" in stats
        assert stats["sample_rate"] == 16000
        assert stats["audio_dim"] == 128
        assert stats["latent_dim"] == 64

    def test_snr_same_signal_is_high(self, pipeline):
        """T14: SNR of identical signals is high."""
        data = _sample_wav_bytes()
        # Use the waveform from the WAV itself for perfect match
        pcm = np.frombuffer(data[44:], dtype=np.int16).astype(np.float32) / 32767.0
        snr = pipeline._compute_snr(data, pcm[:len(pcm)])
        assert snr > 30.0  # Near-perfect match


class TestAudioQualityMonitor:
    """P32 T15-T18: QualityMonitor tests (4 tests)."""

    def test_report_empty_returns_zeros(self, monitor):
        """T15: Empty report returns zero metrics."""
        report = monitor.report()
        assert report["total_calls"] == 0
        assert report["avg_snr"] == 0.0

    def test_report_after_records(self, monitor):
        """T16: Report returns correct averages after recording."""
        for _ in range(10):
            monitor.record({
                "snr": 15.0,
                "time_ms": 50.0,
                "duration": 1.0,
                "cache_hit": False,
                "audio_hash": "abc",
            })
        report = monitor.report()
        assert report["total_calls"] == 10
        assert abs(report["avg_snr"] - 15.0) < 0.1

    def test_quality_trend_insufficient(self, monitor):
        """T17: Trend with < 4 records returns insufficient_data."""
        trend = monitor.quality_trend()
        assert trend["assessment"] == "insufficient_data"

    def test_quality_trend_stable(self, monitor):
        """T18: Trend with stable data returns stable."""
        for _ in range(20):
            monitor.record({
                "snr": 15.0,
                "time_ms": 50.0,
                "duration": 1.0,
                "cache_hit": False,
                "audio_hash": "abc",
            })
        trend = monitor.quality_trend(window=10)
        assert trend["assessment"] in ("stable", "improving")


class TestAudioServiceExtension:
    """P32 T19-T20: AudioService extension tests (2 tests)."""

    async def test_encode_with_pipeline_returns_full_result(self):
        """T19: encode_with_pipeline returns audio pipeline result."""
        from services.audio_service import AudioService
        svc = AudioService()
        data = _sample_wav_bytes()
        result = await svc.encode_with_pipeline(data)
        assert "error" not in result or result.get("error") is None
        assert "feature_vector" in result
        assert "latent" in result
        assert "snr" in result

    async def test_batch_encode_returns_list(self):
        """T20: batch_encode returns list of results."""
        from services.audio_service import AudioService
        svc = AudioService()
        audios = [_sample_wav_bytes() for _ in range(3)]
        results = await svc.batch_encode(audios)
        assert len(results) == 3
        for r in results:
            assert "feature_vector" in r or "error" in r
