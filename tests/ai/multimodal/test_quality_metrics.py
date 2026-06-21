"""Tests for quality_metrics — SSIM, PSNR, SNR."""

import numpy as np
import pytest


@pytest.fixture
def ref_image():
    return np.random.default_rng(42).integers(0, 256, (128, 128, 3), dtype=np.uint8)


@pytest.fixture
def identical_image(ref_image):
    return ref_image.copy()


@pytest.fixture
def different_image():
    return np.random.default_rng(99).integers(0, 256, (128, 128, 3), dtype=np.uint8)


@pytest.fixture
def audio_ref():
    return np.sin(2 * np.pi * 440 * np.arange(16000, dtype=np.float32) / 16000)


class TestSSIM:

    def test_identical_returns_one(self, ref_image, identical_image):
        from ai.multimodal.quality_metrics import ssim
        assert ssim(ref_image, identical_image) == pytest.approx(1.0, abs=0.01)

    def test_different_less_than_one(self, ref_image, different_image):
        from ai.multimodal.quality_metrics import ssim
        score = ssim(ref_image, different_image)
        assert score < 0.99

    def test_shape_mismatch_returns_zero(self, ref_image):
        from ai.multimodal.quality_metrics import ssim
        wrong = np.zeros((64, 64, 3), dtype=np.uint8)
        assert ssim(ref_image, wrong) == 0.0

    def test_range_zero_to_one(self):
        from ai.multimodal.quality_metrics import ssim
        a = np.random.default_rng(1).integers(0, 256, (128, 128, 3), dtype=np.uint8)
        b = np.random.default_rng(2).integers(0, 256, (128, 128, 3), dtype=np.uint8)
        score = ssim(a, b)
        assert 0.0 <= score <= 1.0


class TestPSNR:

    def test_identical_returns_high(self, ref_image, identical_image):
        from ai.multimodal.quality_metrics import psnr
        score = psnr(ref_image, identical_image)
        assert score > 50.0

    def test_different_lower(self, ref_image, different_image):
        from ai.multimodal.quality_metrics import psnr
        score = psnr(ref_image, different_image)
        assert score < 20.0


class TestSNR:

    def test_identical_returns_high(self, audio_ref):
        from ai.multimodal.quality_metrics import snr
        score = snr(audio_ref, audio_ref)
        assert score > 50.0

    def test_silent_is_zero(self, audio_ref):
        from ai.multimodal.quality_metrics import snr
        score = snr(audio_ref, np.zeros_like(audio_ref))
        assert score == pytest.approx(0.0, abs=0.1)


class TestQualityReport:

    def test_report_contains_keys(self, ref_image, different_image, audio_ref):
        from ai.multimodal.quality_metrics import quality_report
        report = quality_report(
            ref_image, different_image,
            audio_ref, np.zeros_like(audio_ref),
        )
        assert "ssim" in report
        assert "image_psnr" in report
        assert "audio_snr" in report

    def test_report_identical_is_perfect(self, ref_image, identical_image, audio_ref):
        from ai.multimodal.quality_metrics import quality_report
        report = quality_report(
            ref_image, identical_image,
            audio_ref, audio_ref,
        )
        assert report["ssim"] > 0.99
        assert report["image_psnr"] > 50.0
        assert report["audio_snr"] > 50.0