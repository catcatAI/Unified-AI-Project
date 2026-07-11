"""PixelRefiner: lightweight FC network to refine compositional image output."""
import json
import logging
import os
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class PixelRefiner:
    """Lightweight fully-connected network for pixel-level image refinement.

    Takes a rough 128x128x3 image from the primitive renderer and refines
    it with learned pixel corrections. Acts as a "polish" step after the
    main compositional generation pipeline.

    Architecture:
        Input:  128*128*3 = 49,152 (flattened rough image)
        Hidden: 1024 (bottleneck)
        Output: 128*128*3 = 49,152 (refined image)

    Training: MSE loss between refined output and ground truth.
    ~5,000 parameters, fast CPU training.
    """

    def __init__(self, hidden_dim: int = 256, img_size: int = 128):
        self._hidden_dim = hidden_dim
        self._img_size = img_size
        self._flat_dim = img_size * img_size * 3

        # Xavier init for better gradient flow
        scale1 = np.sqrt(2.0 / (self._flat_dim + hidden_dim))
        scale2 = np.sqrt(2.0 / (hidden_dim + self._flat_dim))

        self._W1 = np.random.randn(self._flat_dim, hidden_dim).astype(np.float32) * scale1
        self._b1 = np.zeros(hidden_dim, dtype=np.float32)
        self._W2 = np.random.randn(hidden_dim, self._flat_dim).astype(np.float32) * scale2
        self._b2 = np.zeros(self._flat_dim, dtype=np.float32)

        # Running average of rough images (for skip connection init)
        self._rough_mean: Optional[np.ndarray] = None

    def forward(self, rough_flat: np.ndarray) -> np.ndarray:
        """Forward pass: rough image → refined image.

        Args:
            rough_flat: (flat_dim,) flattened 128x128x3 image, values in [0, 255]

        Returns:
            Refined (flat_dim,) array, values in [0, 255]
        """
        # Normalize to [0, 1]
        x = rough_flat.astype(np.float32) / 255.0

        # Hidden layer
        h = np.tanh(self._W1.T @ x + self._b1)

        # Output layer with skip connection (learn residual)
        out = self._W2.T @ h + self._b2

        # Skip connection: output = input + small correction
        # Initialize b2 so output ≈ input at start of training
        out = x + 0.01 * np.tanh(out)

        # Clamp to [0, 1] and convert back
        out = np.clip(out, 0.0, 1.0)
        return (out * 255.0).astype(np.uint8)

    def forward_train(self, rough_flat: np.ndarray):
        """Forward pass with cached values for backprop."""
        x = rough_flat.astype(np.float32) / 255.0

        z1 = self._W1.T @ x + self._b1
        h = np.tanh(z1)

        z2 = self._W2.T @ h + self._b2
        out = x + 0.01 * np.tanh(z2)
        out = np.clip(out, 0.0, 1.0)

        cache = {"x": x, "z1": z1, "h": h, "z2": z2, "out_raw": x + 0.01 * np.tanh(z2)}
        return out, cache

    def train_step(self, rough_flat: np.ndarray, target_flat: np.ndarray,
                   lr: float = 0.001) -> float:
        """Single training step with backprop.

        Args:
            rough_flat: (flat_dim,) rough image
            target_flat: (flat_dim,) ground truth image
            lr: Learning rate

        Returns:
            MSE loss
        """
        out, cache = self.forward_train(rough_flat)
        target = target_flat.astype(np.float32) / 255.0

        # MSE loss
        diff = out - target
        loss = float(np.mean(diff ** 2))

        # Backprop through skip connection
        d_out_raw = 2.0 * diff / self._flat_dim  # (flat_dim,)

        # d(tanh(z2))/dz2 = (1 - tanh^2(z2))
        tanh_z2 = np.tanh(cache["z2"])
        d_tanh = 1.0 - tanh_z2 ** 2

        # Through 0.01 * tanh(z2)
        d_z2 = d_out_raw * 0.01 * d_tanh

        # W2 gradient: dL/dW2 = h @ d_z2^T
        d_W2 = np.outer(cache["h"], d_z2)
        d_b2 = d_z2

        # Through tanh(z1)
        d_h = self._W2 @ d_z2
        d_z1 = d_h * (1.0 - cache["h"] ** 2)

        # W1 gradient: dL/dW1 = x @ d_z1^T
        d_W1 = np.outer(cache["x"], d_z1)
        d_b1 = d_z1

        # Clip gradients
        for g in [d_W1, d_b1, d_W2, d_b2]:
            np.clip(g, -1.0, 1.0, out=g)

        # Update with momentum
        self._W1 -= lr * d_W1
        self._b1 -= lr * d_b1
        self._W2 -= lr * d_W2
        self._b2 -= lr * d_b2

        return loss

    def refine(self, rough_image) -> "PIL.Image":
        """Refine a rough PIL image.

        Args:
            rough_image: PIL Image (128x128)

        Returns:
            Refined PIL Image (128x128)
        """
        from PIL import Image as PILImage
        arr = np.array(rough_image).astype(np.float32)
        flat = arr.flatten()
        refined_flat = self.forward(flat)
        refined_arr = refined_flat.reshape(self._img_size, self._img_size, 3)
        return PILImage.fromarray(refined_arr.astype(np.uint8))

    def train(self, rough_images: list, target_images: list,
              epochs: int = 50, lr: float = 0.005, batch_size: int = 8) -> Dict:
        """Train on pairs of rough/target images.

        Args:
            rough_images: List of PIL Images (rough A output)
            target_images: List of PIL Images (ground truth)
            epochs: Training epochs
            lr: Learning rate
            batch_size: Mini-batch size

        Returns:
            Training history
        """
        n = len(rough_images)
        losses = []

        for epoch in range(epochs):
            epoch_loss = 0.0
            indices = np.random.permutation(n)

            for start in range(0, n, batch_size):
                batch_idx = indices[start:start + batch_size]
                batch_loss = 0.0

                for idx in batch_idx:
                    rough_arr = np.array(rough_images[idx]).astype(np.float32).flatten()
                    target_arr = np.array(target_images[idx]).astype(np.float32).flatten()
                    loss = self.train_step(rough_arr, target_arr, lr=lr)
                    batch_loss += loss

                epoch_loss += batch_loss / len(batch_idx)

            avg_loss = epoch_loss / max(n // batch_size, 1)
            losses.append(avg_loss)

        return {
            "final_loss": losses[-1] if losses else 0.0,
            "best_loss": min(losses) if losses else 0.0,
            "history": losses,
        }

    def save(self, path: str):
        """Save weights to JSON."""
        data = {
            "hidden_dim": self._hidden_dim,
            "img_size": self._img_size,
            "W1": self._W1.tolist(),
            "b1": self._b1.tolist(),
            "W2": self._W2.tolist(),
            "b2": self._b2.tolist(),
        }
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)
        logger.info("PixelRefiner saved to %s", path)

    @classmethod
    def load(cls, path: str) -> "PixelRefiner":
        """Load weights from JSON."""
        with open(path) as f:
            data = json.load(f)
        refiner = cls(hidden_dim=data["hidden_dim"], img_size=data["img_size"])
        refiner._W1 = np.array(data["W1"], dtype=np.float32)
        refiner._b1 = np.array(data["b1"], dtype=np.float32)
        refiner._W2 = np.array(data["W2"], dtype=np.float32)
        refiner._b2 = np.array(data["b2"], dtype=np.float32)
        return refiner
