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
    
    def __init__(self, semantic_encoder=None, primitive_encoder=None,
                 primitive_library=None):
        """Initialize training data generator.
        
        Args:
            semantic_encoder: SemanticVisualEncoder for CLIP encoding
            primitive_encoder: PrimitiveEncoder for embedding primitives
            primitive_library: PrimitiveLibrary for finding closest primitives
        """
        self._encoder = semantic_encoder
        self._prim_encoder = primitive_encoder
        self._library = primitive_library
    
    def generate_from_cifar10(self, cifar10_dir: str = "data/multimodal/cifar10",
                              n_samples: int = 500,
                              seed: int = 42) -> Dict[str, List]:
        """Generate training pairs from CIFAR-10 images.
        
        For each image:
        1. Load the 32x32 numpy array
        2. Encode with CLIP → 512-dim embedding
        3. Find closest primitive in library → primitive embedding
        
        Args:
            cifar10_dir: Path to CIFAR-10 data directory
            n_samples: Number of samples to use
            seed: Random seed
            
        Returns:
            Dict with 'clip_embeddings' and 'primitive_sequences'
        """
        import os
        import json
        
        index_path = os.path.join(cifar10_dir, "index.json")
        if not os.path.exists(index_path):
            logger.warning("CIFAR-10 index not found at %s", index_path)
            return {"clip_embeddings": [], "primitive_sequences": []}
        
        with open(index_path, 'r') as f:
            index = json.load(f)
        
        # Collect all image paths
        all_images = []
        for class_name, class_info in index.get("classes", {}).items():
            for img_entry in class_info.get("images", []):
                npy_path = os.path.join(cifar10_dir, img_entry["path"])
                if os.path.exists(npy_path):
                    all_images.append({
                        "path": npy_path,
                        "class": class_name,
                    })
        
        if not all_images:
            logger.warning("No CIFAR-10 images found")
            return {"clip_embeddings": [], "primitive_sequences": []}
        
        # Sample subset
        rng = np.random.default_rng(seed)
        if n_samples < len(all_images):
            indices = rng.choice(len(all_images), n_samples, replace=False)
            all_images = [all_images[i] for i in indices]
        
        logger.info("Generating training data from %d CIFAR-10 images", len(all_images))
        
        clip_embeddings = []
        primitive_sequences = []
        
        for img_info in all_images:
            try:
                # Load image
                img_array = np.load(img_info["path"])
                
                # Convert to PIL for CLIP
                from PIL import Image
                if img_array.ndim == 3 and img_array.shape[2] == 3:
                    img_pil = Image.fromarray(img_array.astype(np.uint8))
                    # Resize to 224x224 for CLIP
                    img_pil = img_pil.resize((224, 224), Image.LANCZOS)
                    
                    # Encode with CLIP
                    if self._encoder is not None:
                        clip_vec = self._encoder.encode_from_pil(img_pil)
                        if clip_vec is not None:
                            clip_embeddings.append(clip_vec)
                            
                            # Find closest primitive embedding in library
                            if self._library is not None and self._library.size > 0:
                                similar = self._library.find_similar(clip_vec, top_k=1)
                                if similar:
                                    prim_name, _ = similar[0]
                                    prim_emb = self._library.get_embedding(prim_name)
                                    if prim_emb is not None:
                                        primitive_sequences.append(prim_emb)
                                    else:
                                        primitive_sequences.append(clip_vec[:64]
                                            if len(clip_vec) >= 64
                                            else np.pad(clip_vec, (0, 64 - len(clip_vec))))
                                else:
                                    # No match — use zero embedding
                                    primitive_sequences.append(np.zeros(64, dtype=np.float32))
                            else:
                                # No library — project CLIP to 64-dim as proxy
                                proj = clip_vec[:64] if len(clip_vec) >= 64 \
                                    else np.pad(clip_vec, (0, 64 - len(clip_vec)))
                                primitive_sequences.append(proj.astype(np.float32))
            except Exception as e:
                logger.debug("Skipping %s: %s", img_info["path"], e)
                continue
        
        logger.info("Generated %d training pairs", len(clip_embeddings))
        
        return {
            "clip_embeddings": clip_embeddings,
            "primitive_sequences": primitive_sequences,
        }
    
    def generate_synthetic_captions(self, n_per_primitive: int = 10,
                                    seed: int = 42) -> Dict[str, List]:
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
        colors = ["red", "blue", "green", "yellow", "black", "white",
                  "orange", "purple", "brown", "pink"]
        shapes = ["circle", "square", "triangle", "dot", "line", "blob"]
        positions = ["top-left", "top-right", "bottom-left", "bottom-right",
                     "center", "top", "bottom", "left", "right"]
        
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
    
    def generate_random_primitives(self, n_samples: int = 200,
                                   primitive_dim: int = 64,
                                   seed: int = 42) -> Dict[str, List]:
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
