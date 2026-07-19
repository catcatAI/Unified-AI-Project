"""Primitive library - stores and manages visual primitives."""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

from .primitive_types import DrawingInstructions

logger = logging.getLogger(__name__)


class PrimitiveLibrary:
    """Library of visual primitives for compositional image generation.

    Stores primitive parameters and their embeddings for retrieval
    and auto-expansion.
    """

    def __init__(self, embedding_dim: int = 64, max_primitives: int = 1000):
        self._embedding_dim = embedding_dim
        self._max_primitives = max_primitives
        self._primitives: Dict[str, Dict] = {}  # name -> {params, embedding}
        self._embeddings: Optional[np.ndarray] = None  # (N, embedding_dim)
        self._names: List[str] = []
        self._dirty = True  # Flag to rebuild embeddings array

    def add_primitive(self, name: str, params: DrawingInstructions, embedding: np.ndarray) -> bool:
        """Add a primitive to the library.

        Args:
            name: Unique name for the primitive
            params: DrawingInstructions for this primitive
            embedding: Embedding vector (embedding_dim,)

        Returns:
            True if added, False if library is full or name exists
        """
        if len(self._primitives) >= self._max_primitives:
            logger.warning(
                "PrimitiveLibrary full (%d/%d)", len(self._primitives), self._max_primitives
            )
            return False

        if name in self._primitives:
            logger.warning("Primitive '%s' already exists", name)
            return False

        if embedding.shape != (self._embedding_dim,):
            logger.warning(
                "Embedding shape mismatch: expected (%d,), got %s",
                self._embedding_dim,
                embedding.shape,
            )
            return False

        self._primitives[name] = {
            "params": params,
            "embedding": embedding.copy(),
        }
        self._names.append(name)
        self._dirty = True

        logger.info("Added primitive '%s' (total: %d)", name, len(self._primitives))
        return True

    def get_primitive(self, name: str) -> Optional[DrawingInstructions]:
        """Get primitive parameters by name."""
        prim = self._primitives.get(name)
        return prim["params"] if prim else None

    def get_embedding(self, name: str) -> Optional[np.ndarray]:
        """Get primitive embedding by name."""
        prim = self._primitives.get(name)
        return prim["embedding"].copy() if prim else None

    def find_similar(self, embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find similar primitives via cosine similarity.

        Args:
            embedding: Query embedding (embedding_dim,)
            top_k: Number of top results to return

        Returns:
            List of (name, similarity) tuples, sorted by similarity descending
        """
        if self._dirty:
            self._rebuild_embeddings()

        if self._embeddings is None or len(self._names) == 0:
            return []

        # Normalize embeddings
        query_norm = embedding / (np.linalg.norm(embedding) + 1e-8)
        lib_norm = self._embeddings / (
            np.linalg.norm(self._embeddings, axis=1, keepdims=True) + 1e-8
        )

        # Compute cosine similarities
        similarities = lib_norm @ query_norm

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            name = self._names[idx]
            sim = float(similarities[idx])
            results.append((name, sim))

        return results

    def auto_expand(
        self, embedding: np.ndarray, params: DrawingInstructions, threshold: float = 0.8
    ) -> Optional[str]:
        """Auto-expand library if new primitive is sufficiently different.

        Args:
            embedding: New primitive embedding
            params: New primitive parameters
            threshold: Minimum distance to existing primitives (0-1)

        Returns:
            Name of new primitive if added, None if too similar or library full
        """
        if len(self._primitives) == 0:
            # First primitive
            name = f"prim_{len(self._primitives):04d}"
            self.add_primitive(name, params, embedding)
            return name

        # Find most similar primitive
        similar = self.find_similar(embedding, top_k=1)
        if similar:
            _, similarity = similar[0]
            distance = 1.0 - similarity

            if distance < threshold:
                # Too similar, don't add
                return None

        # Add new primitive
        name = f"prim_{len(self._primitives):04d}"
        self.add_primitive(name, params, embedding)
        return name

    def _rebuild_embeddings(self):
        """Rebuild embeddings array from dictionary."""
        if not self._dirty:
            return

        if len(self._primitives) == 0:
            self._embeddings = None
            return

        embeddings = []
        for name in self._names:
            embeddings.append(self._primitives[name]["embedding"])

        self._embeddings = np.stack(embeddings)
        self._dirty = False

    @property
    def size(self) -> int:
        return len(self._primitives)

    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim

    def save(self, path: str):
        """Save library to file."""
        data = {"embedding_dim": self._embedding_dim, "primitives": {}}
        for name, prim in self._primitives.items():
            # Convert DrawingInstructions to dict
            params = prim["params"]
            data["primitives"][name] = {
                "params": {
                    "background_color": params.background_color,
                    "canvas_size": params.canvas_size,
                    "points": [(p.x, p.y, p.color, p.size) for p in params.points],
                    "lines": [
                        (l.start.x, l.start.y, l.end.x, l.end.y, l.width, l.color)
                        for l in params.lines
                    ],
                    "planes": [
                        (
                            [p.x for p in pl.points],
                            [p.y for p in pl.points],
                            pl.fill_color,
                            pl.outline_color,
                            pl.outline_width,
                        )
                        for pl in params.planes
                    ],
                },
                "embedding": prim["embedding"].tolist(),
            }

        import json

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info("Saved PrimitiveLibrary to %s (%d primitives)", path, len(self._primitives))

    @classmethod
    def load(cls, path: str) -> "PrimitiveLibrary":
        """Load library from file."""
        import json

        with open(path, "r") as f:
            data = json.load(f)

        lib = cls(embedding_dim=data["embedding_dim"])

        for name, prim_data in data["primitives"].items():
            params_dict = prim_data["params"]
            embedding = np.array(prim_data["embedding"], dtype=np.float32)

            # Reconstruct DrawingInstructions
            from .primitive_types import Line, Plane, Point

            points = [Point(x, y, color, size) for x, y, color, size in params_dict["points"]]

            lines = [
                Line(Point(sx, sy, (0, 0, 0), 0.0), Point(ex, ey, (0, 0, 0), 0.0), width, color)
                for sx, sy, ex, ey, width, color in params_dict["lines"]
            ]

            planes = [
                Plane(
                    [Point(x, y, (0, 0, 0), 0.0) for x, y in zip(xs, ys)],
                    fill_color,
                    outline_color,
                    outline_width,
                )
                for xs, ys, fill_color, outline_color, outline_width in params_dict["planes"]
            ]

            params = DrawingInstructions(
                points=points,
                lines=lines,
                planes=planes,
                background_color=tuple(params_dict["background_color"]),
                canvas_size=tuple(params_dict["canvas_size"]),
            )

            lib.add_primitive(name, params, embedding)

        logger.info("Loaded PrimitiveLibrary from %s (%d primitives)", path, lib.size)
        return lib
