# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L3]
# =============================================================================
"""Multimodal data loader — loads real datasets and encodes via existing encoders.

P28: Connects ESC-50 (audio events) and CIFAR-10 (images) to the training
pipeline. Each dataset yields pre-encoded features that can be used for
contrastive training (same-class = positive, different-class = negative)
and reconstruction training (encode → decode → compare).

Datasets are expected under data/multimodal/{cifar10, esc50}/.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder
from ai.multimodal.visual_encoder import VisualEncoder

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent  # project root
DATA_DIR = ROOT / "data" / "multimodal"


# ---------------------------------------------------------------------------
# CIFAR-10
# ---------------------------------------------------------------------------


class CIFAR10Loader:
    """Loads CIFAR-10 images and encodes them via VisualEncoder.

    Directory structure (expected after scripts/download_datasets.py cifar10):
        data/multimodal/cifar10/{class_name}/*.npy
        data/multimodal/cifar10/index.json
    """

    CLASS_NAMES = [
        "airplane",
        "automobile",
        "bird",
        "cat",
        "deer",
        "dog",
        "frog",
        "horse",
        "ship",
        "truck",
    ]

    def __init__(
        self, data_dir: Optional[Path] = None, visual_encoder: Optional[VisualEncoder] = None
    ):
        self._data_dir = Path(data_dir or DATA_DIR / "cifar10")
        self._encoder = visual_encoder or VisualEncoder()
        self._samples: List[Tuple[int, str]] = []  # (label, filepath)
        self._encoded: Dict[int, Optional[np.ndarray]] = {}  # index -> features
        self._class_indices: Dict[int, List[int]] = {}  # label -> [indices]
        self._available = False
        self._scan()

    def _scan(self) -> None:
        """Scan directory for .npy files and build index."""
        idx_path = self._data_dir / "index.json"
        if not idx_path.exists():
            logger.warning("CIFAR-10 not found at %s", self._data_dir)
            return

        with open(idx_path, "r") as f:
            idx = json.load(f)

        self._samples = []
        self._class_indices = {}
        for label, class_name in enumerate(self.CLASS_NAMES):
            class_dir = self._data_dir / class_name
            if not class_dir.exists():
                continue
            npy_files = sorted(class_dir.glob("*.npy"))
            for npy_path in npy_files:
                idx_val = len(self._samples)
                self._samples.append((label, str(npy_path)))
                self._class_indices.setdefault(label, []).append(idx_val)

        self._available = len(self._samples) > 0
        if self._available:
            logger.info(
                "CIFAR-10: %d images available (%d classes)",
                len(self._samples),
                len(self.CLASS_NAMES),
            )
        else:
            logger.warning("CIFAR-10: no images found in %s", self._data_dir)

    @property
    def available(self) -> bool:
        return self._available

    @property
    def size(self) -> int:
        return len(self._samples)

    def encode_all(self, max_images: int = 0, checkpoint_interval: int = 5000) -> int:
        """Encode all images via VisualEncoder with checkpoint persistence.

        Args:
            max_images: Maximum images to encode (0 = all available).
            checkpoint_interval: Save checkpoint every N images.

        Saves incremental checkpoints every `checkpoint_interval` images,
        and resumes from checkpoint if available.

        Returns count of successfully encoded images.
        """
        checkpoint_path = self._data_dir / "_encoded_checkpoint.npz"

        # Resume from checkpoint if it exists
        if checkpoint_path.exists():
            try:
                ckpt = np.load(checkpoint_path, allow_pickle=True)
                saved_indices = ckpt.get("indices", [])
                saved_features = ckpt.get("features", [])
                if len(saved_indices) > 0:
                    self._encoded = dict(zip(saved_indices, saved_features))
                    # Ensure features are float32 (checkpoint may store object arrays)
                    for idx in self._encoded:
                        if self._encoded[idx] is not None:
                            self._encoded[idx] = np.asarray(self._encoded[idx], dtype=np.float32)
                    logger.info(
                        "CIFAR-10: resumed from checkpoint (%d images already encoded)",
                        len(self._encoded),
                    )
            except Exception as e:
                logger.warning("CIFAR-10: checkpoint load failed: %s", e)
                self._encoded = {}
        else:
            self._encoded = {}

        count = len(self._encoded)
        total = min(len(self._samples), max_images) if max_images > 0 else len(self._samples)
        if count >= total:
            logger.info("CIFAR-10: all %d images already encoded", count)
            return count

        for i in range(count, len(self._samples)):
            if len(self._encoded) >= total:
                break
            if i in self._encoded:
                continue
            try:
                label, path = self._samples[i]
                img_data = np.load(path).astype(np.uint8)
                from PIL import Image

                features = self._encoder.encode_from_pil(Image.fromarray(img_data))
                if features is not None and (
                    isinstance(features, np.ndarray) and features.sum() != 0
                ):
                    self._encoded[i] = np.asarray(features, dtype=np.float32)
                    count += 1
            except Exception as e:
                logger.debug("CIFAR-10 encode failed at index %d: %s", i, e)
            if (
                (i + 1) % checkpoint_interval == 0
                or (i + 1) == len(self._samples)
                or count >= total
            ):
                try:
                    indices = np.array(list(self._encoded.keys()), dtype=object)
                    feats = np.array(list(self._encoded.values()), dtype=object)
                    np.savez(checkpoint_path, indices=indices, features=feats)
                except Exception as e:
                    logger.warning("CIFAR-10: checkpoint save failed at %d: %s", i + 1, e)
                if (i + 1) % checkpoint_interval == 0:
                    logger.info(
                        "  Encoded %d/%d CIFAR-10 images (checkpoint saved)",
                        i + 1,
                        len(self._samples),
                    )

        if count == len(self._samples):
            try:
                checkpoint_path.unlink(missing_ok=True)
            except Exception:
                logger.debug("Failed to remove checkpoint file", exc_info=True)
            logger.info("CIFAR-10: encoded all %d images", count)
        else:
            logger.info("CIFAR-10: encoded %d/%d images", count, len(self._samples))
        return count

    def get_features(self, index: int) -> Optional[np.ndarray]:
        """Return encoded features for a specific image index."""
        return self._encoded.get(index)

    def get_label(self, index: int) -> int:
        """Return class label for a specific image index."""
        return self._samples[index][0]

    def build_contrastive_pairs(
        self, n_pairs: int = 100, same_prob: float = 0.5, seed: int = 42
    ) -> Tuple[List, List]:
        """Build positive/negative contrastive pairs from class labels.

        Positive pairs: two images of the same class.
        Negative pairs: two images of different classes.

        Returns (pos_pairs, neg_pairs) where each element is
        ("vision", feat_a, "vision", feat_b).
        """
        rng = np.random.RandomState(seed)
        pos_pairs: List = []
        neg_pairs: List = []

        encoded_indices = list(self._encoded.keys())
        if len(encoded_indices) < 2:
            return pos_pairs, neg_pairs

        for _ in range(n_pairs):
            if rng.rand() < same_prob and len(self._class_indices) > 0:
                # Positive pair: same class
                label = rng.choice(list(self._class_indices.keys()))
                candidates = [i for i in self._class_indices[label] if i in self._encoded]
                if len(candidates) >= 2:
                    a, b = rng.choice(candidates, 2, replace=False)
                    feat_a = self._encoded[a]
                    feat_b = self._encoded[b]
                    if feat_a is not None and feat_b is not None:
                        pos_pairs.append(("vision", feat_a, "vision", feat_b))
            else:
                # Negative pair: different classes
                if len(encoded_indices) >= 2:
                    a, b = rng.choice(encoded_indices, 2, replace=False)
                    if self.get_label(a) != self.get_label(b):
                        feat_a = self._encoded[a]
                        feat_b = self._encoded[b]
                        if feat_a is not None and feat_b is not None:
                            neg_pairs.append(("vision", feat_a, "vision", feat_b))

        return pos_pairs, neg_pairs

    def build_reconstruction_samples(self, n_samples: int = 50, seed: int = 42) -> List[np.ndarray]:
        """Sample encoded features for reconstruction training.

        Returns list of feature vectors.
        """
        rng = np.random.RandomState(seed)
        encoded_indices = list(self._encoded.keys())
        if len(encoded_indices) == 0:
            return []
        chosen = rng.choice(encoded_indices, min(n_samples, len(encoded_indices)), replace=False)
        return [self._encoded[i] for i in chosen if self._encoded[i] is not None]


# ---------------------------------------------------------------------------
# ESC-50
# ---------------------------------------------------------------------------


class ESC50Loader:
    """Loads ESC-50 audio clips and encodes them via AudioSpectralEncoder.

    Directory structure (after scripts/download_datasets.py esc50):
        data/multimodal/esc50/{category}/*.ref
        data/multimodal/esc50/index.json

    Each .ref file contains the path to the original WAV file.
    """

    def __init__(
        self, data_dir: Optional[Path] = None, audio_encoder: Optional[AudioSpectralEncoder] = None
    ):
        self._data_dir = Path(data_dir or DATA_DIR / "esc50")
        self._encoder = audio_encoder or AudioSpectralEncoder()
        self._samples: List[Tuple[int, str, str]] = []  # (class_id, category, ref_path)
        self._encoded: Dict[int, Optional[np.ndarray]] = {}
        self._class_indices: Dict[int, List[int]] = {}
        self._available = False
        self._scan()

    def _scan(self) -> None:
        idx_path = self._data_dir / "index.json"
        if not idx_path.exists():
            logger.warning("ESC-50 not found at %s", self._data_dir)
            return

        with open(idx_path, "r") as f:
            idx = json.load(f)

        self._samples = []
        self._class_indices = {}
        for class_id, category in enumerate(idx.get("categories", [])):
            cat_key = category.replace(" ", "_")
            cat_dir = self._data_dir / cat_key
            if not cat_dir.exists():
                continue
            ref_files = sorted(cat_dir.glob("*.ref"))
            for ref_path in ref_files:
                idx_val = len(self._samples)
                self._samples.append((class_id, category, str(ref_path)))
                self._class_indices.setdefault(class_id, []).append(idx_val)

        self._available = len(self._samples) > 0
        if self._available:
            logger.info(
                "ESC-50: %d clips indexed (%d classes)",
                len(self._samples),
                len(idx.get("categories", [])),
            )
        else:
            logger.warning("ESC-50: no clips found in %s", self._data_dir)

    @property
    def available(self) -> bool:
        return self._available

    @property
    def size(self) -> int:
        return len(self._samples)

    def encode_all(self, max_images: int = 0) -> int:
        """Encode all audio clips via AudioSpectralEncoder.

        Reads each WAV file, encodes spectrally.
        Args:
            max_images: Max clips to encode (0 = all).
        Returns count of successfully encoded clips.
        """
        limit = max_images if max_images > 0 else len(self._samples)
        count = 0
        for i, (class_id, category, ref_path_str) in enumerate(self._samples):
            if count >= limit:
                break
            try:
                ref_path = Path(ref_path_str)
                if not ref_path.exists():
                    continue
                with open(ref_path, "rb") as f:
                    wav_bytes = f.read()
                features = self._encoder.encode(wav_bytes)
                if features.sum() != 0:
                    self._encoded[i] = features
                    count += 1
            except Exception as e:
                logger.debug("ESC-50 encode failed at index %d: %s", i, e)
            if (i + 1) % 500 == 0:
                logger.info("  Encoded %d/%d ESC-50 clips", i + 1, len(self._samples))
        logger.info("ESC-50: encoded %d/%d clips", count, len(self._samples))
        return count

    def get_features(self, index: int) -> Optional[np.ndarray]:
        return self._encoded.get(index)

    def get_class_id(self, index: int) -> int:
        return self._samples[index][0]

    def build_contrastive_pairs(
        self, n_pairs: int = 100, same_prob: float = 0.5, seed: int = 42
    ) -> Tuple[List, List]:
        """Build contrastive pairs from class labels (same class = positive)."""
        rng = np.random.RandomState(seed)
        pos_pairs: List = []
        neg_pairs: List = []
        encoded_indices = list(self._encoded.keys())
        if len(encoded_indices) < 2:
            return pos_pairs, neg_pairs

        for _ in range(n_pairs):
            if rng.rand() < same_prob and self._class_indices:
                cid = rng.choice(list(self._class_indices.keys()))
                candidates = [i for i in self._class_indices[cid] if i in self._encoded]
                if len(candidates) >= 2:
                    a, b = rng.choice(candidates, 2, replace=False)
                    fa, fb = self._encoded[a], self._encoded[b]
                    if fa is not None and fb is not None:
                        pos_pairs.append(("audio", fa, "audio", fb))
            else:
                if len(encoded_indices) >= 2:
                    a, b = rng.choice(encoded_indices, 2, replace=False)
                    if self.get_class_id(a) != self.get_class_id(b):
                        fa, fb = self._encoded[a], self._encoded[b]
                        if fa is not None and fb is not None:
                            neg_pairs.append(("audio", fa, "audio", fb))
        return pos_pairs, neg_pairs

    def build_reconstruction_samples(self, n_samples: int = 50, seed: int = 42) -> List[np.ndarray]:
        rng = np.random.RandomState(seed)
        encoded_indices = list(self._encoded.keys())
        if not encoded_indices:
            return []
        chosen = rng.choice(encoded_indices, min(n_samples, len(encoded_indices)), replace=False)
        return [self._encoded[i] for i in chosen if self._encoded[i] is not None]


# ---------------------------------------------------------------------------
# Combined real data provider
# ---------------------------------------------------------------------------


class RealDataProvider:
    """Combines CIFAR-10 and ESC-50 into a unified interface for the training pipeline.

    Provides:
    - contrastive_pairs(): pos/neg pairs from both modalities
    - reconstruction_samples(): encoded features for decoder training
    """

    def __init__(self, encoders: Optional[Dict[str, object]] = None):
        self.cifar10 = CIFAR10Loader()
        self.esc50 = ESC50Loader()
        self._encoders = encoders or {}

    def has_data(self) -> bool:
        """Returns True if at least one dataset is available with encoded features."""
        return len(self.cifar10._encoded) > 0 or len(self.esc50._encoded) > 0

    def encode_all(self, max_images: int = 0) -> Dict[str, int]:
        """Encode all data from available datasets.

        Args:
            max_images: Max images to encode per dataset (0 = all).

        Returns dict with counts per dataset.
        """
        results = {}
        if self.cifar10.available:
            results["cifar10"] = self.cifar10.encode_all(max_images=max_images)
        if self.esc50.available:
            results["esc50"] = self.esc50.encode_all(max_images=max_images)
        return results

    def contrastive_pairs(
        self, n_per_modality: int = 50, same_prob: float = 0.5, seed: int = 42
    ) -> Tuple[List, List]:
        """Build contrastive pairs from real data."""
        pos_pairs: List = []
        neg_pairs: List = []

        # CIFAR-10 pairs
        vp, vn = self.cifar10.build_contrastive_pairs(n_per_modality, same_prob, seed)
        pos_pairs.extend(vp)
        neg_pairs.extend(vn)

        # ESC-50 pairs
        ap, an = self.esc50.build_contrastive_pairs(n_per_modality, same_prob, seed + 1)
        pos_pairs.extend(ap)
        neg_pairs.extend(an)

        return pos_pairs, neg_pairs

    def reconstruction_samples(
        self, n_per_modality: int = 30, seed: int = 42
    ) -> Dict[str, List[np.ndarray]]:
        """Build reconstruction samples from real data."""
        result: Dict[str, List[np.ndarray]] = {}
        rng = np.random.RandomState(seed)
        vision_samples = self.cifar10.build_reconstruction_samples(n_per_modality, seed)
        if vision_samples:
            result["vision"] = vision_samples
        audio_samples = self.esc50.build_reconstruction_samples(n_per_modality, seed + 1)
        if audio_samples:
            result["audio"] = audio_samples
        return result
