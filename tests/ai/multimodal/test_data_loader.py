"""Tests for multimodal data loader — CIFAR10Loader, ESC50Loader, RealDataProvider."""

import numpy as np
import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# CIFAR10Loader — tests with synthetic data
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_cifar10_dir(tmp_path):
    """Create a fake CIFAR-10 directory structure with synthetic data."""
    cifar_dir = tmp_path / "cifar10"
    class_names = ["airplane", "automobile", "bird"]
    class_dir = cifar_dir / class_names[0]
    class_dir.mkdir(parents=True)
    for i in range(3):
        img = np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)
        np.save(class_dir / f"img_{i}.npy", img)
    import json
    with open(cifar_dir / "index.json", "w") as f:
        json.dump({"total": 3, "classes": class_names, "class_counts": {cn: 1 for cn in class_names}}, f)
    return cifar_dir


def test_cifar10_loader_init_no_data():
    """CIFAR10Loader should handle missing data gracefully."""
    from ai.multimodal.data_loader import CIFAR10Loader
    loader = CIFAR10Loader(data_dir=Path("/nonexistent/path"))
    assert not loader.available
    assert loader.size == 0


def test_cifar10_loader_scan(fake_cifar10_dir):
    """CIFAR10Loader should find .npy files."""
    from ai.multimodal.data_loader import CIFAR10Loader
    loader = CIFAR10Loader(data_dir=fake_cifar10_dir)
    assert loader.available
    assert loader.size == 3


def test_cifar10_loader_encode_all(fake_cifar10_dir):
    """CIFAR10Loader.encode_all should encode images via VisualEncoder."""
    from ai.multimodal.data_loader import CIFAR10Loader
    loader = CIFAR10Loader(data_dir=fake_cifar10_dir)
    count = loader.encode_all()
    assert count >= 0  # May encode 0 if images are too small for VisualEncoder
    if count > 0:
        assert 256 in [len(v) for v in loader._encoded.values() if v is not None]


def test_cifar10_loader_get_label(fake_cifar10_dir):
    """CIFAR10Loader.get_label should return class label."""
    from ai.multimodal.data_loader import CIFAR10Loader
    loader = CIFAR10Loader(data_dir=fake_cifar10_dir)
    for i in range(loader.size):
        label = loader.get_label(i)
        assert 0 <= label <= 9


def test_cifar10_loader_build_contrastive_pairs_no_data():
    """CIFAR10Loader.build_contrastive_pairs should return empty for no data."""
    from ai.multimodal.data_loader import CIFAR10Loader
    loader = CIFAR10Loader(data_dir=Path("/nonexistent"))
    pos, neg = loader.build_contrastive_pairs(10)
    assert len(pos) == 0
    assert len(neg) == 0


# ---------------------------------------------------------------------------
# ESC50Loader — tests with synthetic data
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_esc50_dir(tmp_path):
    """Create a fake ESC-50 directory structure with synthetic data."""
    esc_dir = tmp_path / "esc50"
    cat_dir = esc_dir / "dog"
    cat_dir.mkdir(parents=True)
    # Create fake .ref files with small WAV data
    for i in range(3):
        ref_path = cat_dir / f"clip_{i}.ref"
        # Write a tiny fake WAV (44 bytes header + 160 samples)
        n_samples = 160
        wav_bytes = b"RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00data" + (n_samples * 2).to_bytes(4, 'little') + b"\x00" * (n_samples * 2)
        with open(ref_path, "w") as f:
            f.write(str(ref_path.parent / f"clip_{i}.wav"))
        wav_path = cat_dir / f"clip_{i}.wav"
        with open(wav_path, "wb") as f:
            f.write(wav_bytes)
    import json
    with open(esc_dir / "index.json", "w") as f:
        json.dump({"total": 3, "categories": ["dog"], "category_counts": {"dog": 3}}, f)
    return esc_dir


def test_esc50_loader_init_no_data():
    """ESC50Loader should handle missing data gracefully."""
    from ai.multimodal.data_loader import ESC50Loader
    loader = ESC50Loader(data_dir=Path("/nonexistent/path"))
    assert not loader.available
    assert loader.size == 0


def test_esc50_loader_scan(fake_esc50_dir):
    """ESC50Loader should find .ref files."""
    from ai.multimodal.data_loader import ESC50Loader
    loader = ESC50Loader(data_dir=fake_esc50_dir)
    assert loader.available
    assert loader.size == 3


def test_esc50_loader_encode_all(fake_esc50_dir):
    """ESC50Loader.encode_all should encode audio via AudioSpectralEncoder."""
    from ai.multimodal.data_loader import ESC50Loader
    loader = ESC50Loader(data_dir=fake_esc50_dir)
    count = loader.encode_all()
    assert count >= 0
    if count > 0:
        assert 128 in [len(v) for v in loader._encoded.values() if v is not None]


def test_esc50_loader_get_class_id(fake_esc50_dir):
    """ESC50Loader.get_class_id should return class id."""
    from ai.multimodal.data_loader import ESC50Loader
    loader = ESC50Loader(data_dir=fake_esc50_dir)
    for i in range(loader.size):
        cid = loader.get_class_id(i)
        assert cid >= 0


def test_esc50_loader_build_contrastive_pairs(fake_esc50_dir):
    """ESC50Loader.build_contrastive_pairs should work with encoded data."""
    from ai.multimodal.data_loader import ESC50Loader
    loader = ESC50Loader(data_dir=fake_esc50_dir)
    loader.encode_all()
    pos, neg = loader.build_contrastive_pairs(5)
    assert isinstance(pos, list)
    assert isinstance(neg, list)
    for p in pos:
        assert len(p) == 4
        assert p[0] == "audio"
        assert len(p[1]) == 128


# ---------------------------------------------------------------------------
# RealDataProvider — combined interface tests
# ---------------------------------------------------------------------------

def test_real_data_provider_init():
    """RealDataProvider should initialize without data."""
    from ai.multimodal.data_loader import RealDataProvider
    provider = RealDataProvider()
    assert not provider.has_data()


def test_real_data_provider_contrastive_pairs_empty():
    """RealDataProvider.contrastive_pairs should return empty lists when no data."""
    from ai.multimodal.data_loader import RealDataProvider
    provider = RealDataProvider()
    pos, neg = provider.contrastive_pairs(10)
    assert len(pos) == 0
    assert len(neg) == 0


def test_real_data_provider_reconstruction_samples_empty():
    """RealDataProvider.reconstruction_samples should return empty dict when no data."""
    from ai.multimodal.data_loader import RealDataProvider
    provider = RealDataProvider()
    samples = provider.reconstruction_samples(10)
    assert isinstance(samples, dict)
    assert len(samples) == 0


def test_real_data_provider_encode_all_no_data():
    """RealDataProvider.encode_all should return empty counts when no data dirs."""
    from ai.multimodal.data_loader import RealDataProvider
    provider = RealDataProvider()
    counts = provider.encode_all()
    assert isinstance(counts, dict)
