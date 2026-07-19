"""Generate training data for the sequence generator.

Creates (CLIP embedding, primitive_sequence) pairs from CIFAR-10 images
and synthetic text descriptions.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """Generates training data for SequenceGenerator.

    Uses CLIP to encode images and the PrimitiveLibrary to find
    closest primitive matches, creating (clip_embedding, primitive_sequence)
    training pairs.
    """

    def __init__(self, semantic_encoder=None, primitive_encoder=None, primitive_library=None):
        """Initialize training data generator.

        Args:
            semantic_encoder: SemanticVisualEncoder for CLIP encoding
            primitive_encoder: PrimitiveEncoder for embedding primitives
            primitive_library: PrimitiveLibrary for finding closest primitives
        """
        self._encoder = semantic_encoder
        self._prim_encoder = primitive_encoder
        self._library = primitive_library

    def generate_from_cifar10(
        self, cifar10_dir: str = "data/multimodal/cifar10", n_samples: int = 500, seed: int = 42
    ) -> Dict[str, List]:
        """Generate training pairs from CIFAR-10 images."""
        import json
        import os

        index_path = os.path.join(cifar10_dir, "index.json")
        if not os.path.exists(index_path):
            logger.warning("CIFAR-10 index not found at %s", index_path)
            return {"clip_embeddings": [], "primitive_sequences": []}

        with open(index_path, "r") as f:
            index = json.load(f)

        all_images = self._collect_cifar10_images(cifar10_dir, index)
        if not all_images:
            logger.warning("No CIFAR-10 images found")
            return {"clip_embeddings": [], "primitive_sequences": []}

        rng = np.random.default_rng(seed)
        if n_samples < len(all_images):
            indices = rng.choice(len(all_images), n_samples, replace=False)
            all_images = [all_images[i] for i in indices]

        logger.info("Generating training data from %d CIFAR-10 images", len(all_images))

        clip_embeddings = []
        primitive_sequences = []
        for img_info in all_images:
            result = self._process_single_image(img_info)
            if result is not None:
                clip_embeddings.append(result[0])
                primitive_sequences.append(result[1])

        logger.info("Generated %d training pairs", len(clip_embeddings))
        return {
            "clip_embeddings": clip_embeddings,
            "primitive_sequences": primitive_sequences,
        }

    def _collect_cifar10_images(self, cifar10_dir: str, index: dict) -> List[dict]:
        import os

        all_images = []
        for class_name, class_info in index.get("classes", {}).items():
            for img_entry in class_info.get("images", []):
                npy_path = os.path.join(cifar10_dir, img_entry["path"])
                if os.path.exists(npy_path):
                    all_images.append({"path": npy_path, "class": class_name})
        return all_images

    def _process_single_image(self, img_info: dict) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Process a single CIFAR-10 image into a (clip_embedding, primitive_sequence) pair."""
        try:
            from PIL import Image

            img_array = np.load(img_info["path"])
            if img_array.ndim != 3 or img_array.shape[2] != 3:
                return None
            img_pil = Image.fromarray(img_array.astype(np.uint8))
            img_pil = img_pil.resize((224, 224), Image.LANCZOS)
            if self._encoder is None:
                return None
            clip_vec = self._encoder.encode_from_pil(img_pil)
            if clip_vec is None:
                return None
            prim_emb = self._find_primitive_match(clip_vec)
            return (clip_vec, prim_emb)
        except Exception as e:
            logger.debug("Skipping %s: %s", img_info["path"], e)
            return None

    def _find_primitive_match(self, clip_vec: np.ndarray) -> np.ndarray:
        if self._library is not None and self._library.size > 0:
            similar = self._library.find_similar(clip_vec, top_k=1)
            if similar:
                prim_name, _ = similar[0]
                prim_emb = self._library.get_embedding(prim_name)
                if prim_emb is not None:
                    return prim_emb
                return self._project_clip(clip_vec)
            return np.zeros(128, dtype=np.float32)
        return self._project_clip(clip_vec)

    @staticmethod
    def _project_clip(clip_vec: np.ndarray) -> np.ndarray:
        d = 128
        proj = clip_vec[:d] if len(clip_vec) >= d else np.pad(clip_vec, (0, d - len(clip_vec)))
        return proj.astype(np.float32)

    def generate_synthetic_captions(
        self, n_per_primitive: int = 10, seed: int = 42
    ) -> Dict[str, List]:
        """Generate synthetic text→primitive training pairs.

        For each primitive in the library, generates text descriptions
        and encodes them with CLIP.

        Args:
            n_per_primitive: Number of text variations per primitive
            seed: Random seed

        Returns:
            Dict with 'clip_embeddings' and 'primitive_sequences'
        """
        if self._library is None or self._library.size == 0:
            logger.warning("No primitives in library")
            return {"clip_embeddings": [], "primitive_sequences": []}

        clip_embeddings = []
        primitive_sequences = []

        rng = np.random.default_rng(seed)

        # Color names for synthetic descriptions
        colors = [
            "red",
            "blue",
            "green",
            "yellow",
            "black",
            "white",
            "orange",
            "purple",
            "brown",
            "pink",
        ]
        shapes = ["circle", "square", "triangle", "dot", "line", "blob"]
        positions = [
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
            "center",
            "top",
            "bottom",
            "left",
            "right",
        ]

        for name in list(self._library._primitives.keys())[:50]:  # Limit to 50
            prim_emb = self._library.get_embedding(name)
            if prim_emb is None:
                continue

            # Generate text variations
            for _ in range(n_per_primitive):
                color = rng.choice(colors)
                shape = rng.choice(shapes)
                position = rng.choice(positions)

                text = f"a {color} {shape} at {position}"

                # Encode text with CLIP
                if self._encoder is not None:
                    text_embs = self._encoder.encode_text([text])
                    if text_embs is not None and len(text_embs) > 0:
                        clip_embeddings.append(text_embs[0])
                        primitive_sequences.append(prim_emb)

        logger.info("Generated %d synthetic caption pairs", len(clip_embeddings))

        return {
            "clip_embeddings": clip_embeddings,
            "primitive_sequences": primitive_sequences,
        }

    def generate_random_primitives(
        self, n_samples: int = 200, primitive_dim: int = 128, seed: int = 42
    ) -> Dict[str, List]:
        """Generate random primitive sequences for pre-training.

        Creates random (random_clip_vec, random_primitive) pairs to
        pre-train the sequence generator's basic dynamics.

        Args:
            n_samples: Number of random pairs
            primitive_dim: Dimension of primitive embeddings
            seed: Random seed

        Returns:
            Dict with 'clip_embeddings' and 'primitive_sequences'
        """
        rng = np.random.default_rng(seed)

        clip_embeddings = []
        primitive_sequences = []

        for _ in range(n_samples):
            # Random CLIP-like vector (512-dim, normalized)
            clip_vec = rng.normal(0, 1, 512).astype(np.float32)
            clip_vec = clip_vec / (np.linalg.norm(clip_vec) + 1e-8)
            clip_embeddings.append(clip_vec)

            # Random primitive sequence (1-5 primitives)
            n_prims = rng.integers(1, 6)
            seq = []
            for _ in range(n_prims):
                prim = rng.normal(0, 1, primitive_dim).astype(np.float32)
                prim = prim / (np.linalg.norm(prim) + 1e-8)
                seq.append(prim)
            primitive_sequences.append(seq)

        return {
            "clip_embeddings": clip_embeddings,
            "primitive_sequences": primitive_sequences,
        }
