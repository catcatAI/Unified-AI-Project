"""Quality metrics for multimodal decoder outputs — SSIM (image) and SNR (audio).

P24: Pure numpy metrics for evaluating generation quality.
"""

from typing import Dict, Tuple

import numpy as np


def ssim(
    img_a: np.ndarray, img_b: np.ndarray, k1: float = 0.01, k2: float = 0.03, L: float = 255.0
) -> float:
    """Structural Similarity Index between two uint8 RGB images.

    Computes per-channel SSIM and averages. Uses pixel-wise mean/variance
    for simplicity, matching the structural quality of generated images.
    Works on uint8 arrays of the same shape.
    """
    if img_a.shape != img_b.shape:
        return 0.0

    a = img_a.astype(np.float32)
    b = img_b.astype(np.float32)

    c1 = (k1 * L) ** 2
    c2 = (k2 * L) ** 2

    scores = []
    for c in range(3):
        channel_a = a[:, :, c]
        channel_b = b[:, :, c]
        mu_a = np.mean(channel_a)
        mu_b = np.mean(channel_b)
        sigma_a = np.var(channel_a)
        sigma_b = np.var(channel_b)
        sigma_ab = np.mean((channel_a - mu_a) * (channel_b - mu_b))

        numerator = (2 * mu_a * mu_b + c1) * (2 * sigma_ab + c2)
        denominator = (mu_a**2 + mu_b**2 + c1) * (sigma_a + sigma_b + c2)
        scores.append(float(numerator / max(denominator, 1e-8)))
    return float(np.mean(scores))


def snr(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """Signal-to-Noise Ratio in dB between two float32 arrays."""
    signal = np.mean(original**2)
    noise = np.mean((original - reconstructed) ** 2)
    if noise < 1e-12 or signal < 1e-12:
        return 60.0 if noise < 1e-12 else 0.0
    return float(10.0 * np.log10(signal / noise))


def psnr(original: np.ndarray, reconstructed: np.ndarray, peak: float = 255.0) -> float:
    """Peak Signal-to-Noise Ratio in dB."""
    mse = float(np.mean((original.astype(np.float32) - reconstructed.astype(np.float32)) ** 2))
    if mse < 1e-12:
        return 60.0
    return float(10.0 * np.log10(peak**2 / mse))


def quality_report(
    decoded_img: np.ndarray,
    reference_img: np.ndarray,
    decoded_waveform: np.ndarray,
    reference_waveform: np.ndarray,
) -> Dict[str, float]:
    """Generate a comprehensive quality report for multimodal decoder outputs.

    Args:
        decoded_img: Generated 128×128×3 uint8 image
        reference_img: Reference 128×128×3 uint8 image
        decoded_waveform: Generated 1D float32 waveform
        reference_waveform: Reference 1D float32 waveform

    Returns:
        Dict with 'ssim', 'image_psnr', 'audio_snr' keys
    """
    return {
        "ssim": ssim(decoded_img, reference_img),
        "image_psnr": psnr(decoded_img, reference_img),
        "audio_snr": snr(reference_waveform, decoded_waveform),
    }
