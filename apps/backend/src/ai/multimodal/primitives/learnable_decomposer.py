"""Learnable decomposer: neural network that outputs DrawingInstructions from CLIP embeddings.

Trained end-to-end: CLIP → decomposer → primitives → render → compare with target → update.

The renderer (PIL) is non-differentiable, so we use a straight-through estimator:
- Forward: decomposer outputs primitive params → render → compute pixel loss
- Backward: approximate gradient via param-space perturbation, backprop through decomposer
"""

import json
import logging
import os
from typing import Optional

import numpy as np

from .primitive_types import TOTAL_DIM, DrawingInstructions

logger = logging.getLogger(__name__)


class LearnableDecomposer:
    """Neural network that maps CLIP embeddings to DrawingInstructions.
    
    Architecture:
        CLIP (512) → FC(512, 256) → ReLU → FC(256, 263) → Sigmoid
        
    Output is 263-dim vector that decodes to DrawingInstructions:
        15 points + 10 lines + 5 planes + 4 circles + 3 arcs
    """
    
    def __init__(self, clip_dim: int = 512, hidden_dim: int = 256):
        self._clip_dim = clip_dim
        self._hidden_dim = hidden_dim
        self._out_dim = TOTAL_DIM  # 263
        
        rng = np.random.default_rng(42)
        
        # Layer 1: CLIP → hidden
        scale1 = np.sqrt(2.0 / clip_dim)
        self._W1 = rng.normal(0, scale1, (clip_dim, hidden_dim)).astype(np.float32)
        self._b1 = np.zeros(hidden_dim, dtype=np.float32)
        
        # Layer 2: hidden → output (263 dims)
        scale2 = np.sqrt(2.0 / hidden_dim)
        self._W2 = rng.normal(0, scale2, (hidden_dim, self._out_dim)).astype(np.float32)
        self._b2 = np.zeros(self._out_dim, dtype=np.float32)
        
        # Running mean of CLIP embeddings (for input normalization)
        self._clip_mean = np.zeros(clip_dim, dtype=np.float32)
        self._clip_std = np.ones(clip_dim, dtype=np.float32)
        self._n_seen = 0
    
    def forward(self, clip_emb: np.ndarray):
        """Forward pass with cached values for backprop.
        
        Returns:
            pred_vec: (263,) predicted primitive params in [0, 1]
            cache: dict with intermediate values for backprop
        """
        # Normalize input
        x = (clip_emb - self._clip_mean) / np.maximum(self._clip_std, 1e-8)
        
        # Layer 1: ReLU
        z1 = x @ self._W1 + self._b1
        h = np.maximum(0, z1)  # ReLU
        
        # Layer 2: Sigmoid
        z2 = h @ self._W2 + self._b2
        z2_clipped = np.clip(z2, -10, 10)
        sig = 1.0 / (1.0 + np.exp(-z2_clipped))
        
        cache = {"x": x, "z1": z1, "h": h, "z2": z2, "sig": sig}
        return sig, cache
    
    def decode_to_instructions(self, vec: np.ndarray,
                                canvas_size=(128, 128)) -> DrawingInstructions:
        """Convert 263-dim vector to DrawingInstructions."""
        return DrawingInstructions.from_vector(vec, canvas_size)
    
    def update_clip_stats(self, clip_emb: np.ndarray):
        """Update running mean/std of CLIP embeddings."""
        self._n_seen += 1
        alpha = 1.0 / self._n_seen
        self._clip_mean = (1 - alpha) * self._clip_mean + alpha * clip_emb
        self._clip_std = np.sqrt(
            (1 - alpha) * self._clip_std ** 2 +
            alpha * (clip_emb - self._clip_mean) ** 2
        )
    
    def compute_approx_gradient(self, pred_vec: np.ndarray, target_arr: np.ndarray,
                                 renderer, n_probe: int = 20) -> np.ndarray:
        """Approximate gradient of pixel loss w.r.t. primitive params.
        
        Uses finite differences on a random subset of parameters.
        This is the key trick to handle the non-differentiable renderer.
        """
        h, w = target_arr.shape[:2]
        base_rendered = np.array(renderer.render(
            self.decode_to_instructions(pred_vec)), dtype=np.float32) / 255.0
        base_loss = np.mean((base_rendered - target_arr) ** 2)
        
        grad = np.zeros_like(pred_vec)
        
        # Probe random dimensions
        probe_dims = np.random.choice(len(pred_vec), size=min(n_probe, len(pred_vec)), replace=False)
        eps = 0.02  # Small perturbation
        
        for dim in probe_dims:
            # Positive perturbation
            pred_plus = pred_vec.copy()
            pred_plus[dim] = min(1.0, pred_plus[dim] + eps)
            rendered_plus = np.array(renderer.render(
                self.decode_to_instructions(pred_plus)), dtype=np.float32) / 255.0
            loss_plus = np.mean((rendered_plus - target_arr) ** 2)
            
            # Negative perturbation
            pred_minus = pred_vec.copy()
            pred_minus[dim] = max(0.0, pred_minus[dim] - eps)
            rendered_minus = np.array(renderer.render(
                self.decode_to_instructions(pred_minus)), dtype=np.float32) / 255.0
            loss_minus = np.mean((rendered_minus - target_arr) ** 2)
            
            # Finite difference gradient
            grad[dim] = (loss_plus - loss_minus) / (2 * eps)
        
        return grad
    
    def train_step(self, clip_emb: np.ndarray, target_arr: np.ndarray,
                   renderer, lr: float = 0.005, n_probe: int = 20) -> float:
        """Single training step with rendering loss.
        
        Args:
            clip_emb: (512,) CLIP embedding
            target_arr: (H, W, 3) target image as float [0, 1]
            renderer: PrimitiveRenderer
            lr: Learning rate
            n_probe: Number of params to probe for gradient approximation
            
        Returns:
            Pixel MSE loss
        """
        # Forward: CLIP → primitive params
        pred_vec, cache = self.forward(clip_emb)
        
        # Compute loss
        rendered = np.array(renderer.render(
            self.decode_to_instructions(pred_vec)), dtype=np.float32) / 255.0
        loss = float(np.mean((rendered - target_arr) ** 2))
        
        if not np.isfinite(loss):
            return float('inf')
        
        # Approximate gradient in param space
        grad_params = self.compute_approx_gradient(pred_vec, target_arr, renderer, n_probe)
        
        # Backprop through decomposer: grad_params → grad_W2, grad_W2 → grad_W1
        # Through sigmoid: d(sig)/dz = sig * (1 - sig)
        d_z2 = grad_params * cache["sig"] * (1 - cache["sig"])
        
        # W2 gradient
        d_W2 = np.outer(cache["h"], d_z2)
        d_b2 = d_z2
        
        # Through ReLU
        d_h = d_z2 @ self._W2.T
        d_z1 = d_h * (cache["z1"] > 0).astype(np.float32)
        
        # W1 gradient
        d_W1 = np.outer(cache["x"], d_z1)
        d_b1 = d_z1
        
        # Gradient clipping
        for g in [d_W1, d_b1, d_W2, d_b2]:
            np.clip(g, -0.5, 0.5, out=g)
        
        # Update
        self._W1 -= lr * d_W1
        self._b1 -= lr * d_b1
        self._W2 -= lr * d_W2
        self._b2 -= lr * d_b2
        
        return loss
    
    def train(self, clip_embeddings: list, target_images: list,
              renderer, epochs: int = 50, lr: float = 0.005,
              n_probe: int = 15, batch_size: int = 4) -> dict:
        """Train decomposer end-to-end with rendering loss.
        
        Args:
            clip_embeddings: List of (512,) CLIP embeddings
            target_images: List of PIL Images (target)
            renderer: PrimitiveRenderer
            epochs: Training epochs
            lr: Learning rate
            n_probe: Params to probe per step for gradient approx
            batch_size: Images per batch
            
        Returns:
            Training history
        """
        n = len(clip_embeddings)
        losses = []
        
        # Convert targets
        target_arrs = [np.array(img, dtype=np.float32) / 255.0 for img in target_images]
        
        # Update CLIP stats
        for clip_emb in clip_embeddings:
            self.update_clip_stats(clip_emb)
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            indices = np.random.permutation(n)
            n_batches = 0
            
            for start in range(0, n, batch_size):
                batch_idx = indices[start:start + batch_size]
                batch_loss = 0.0
                
                for idx in batch_idx:
                    loss = self.train_step(
                        clip_embeddings[idx], target_arrs[idx],
                        renderer, lr=lr, n_probe=n_probe)
                    batch_loss += loss
                
                epoch_loss += batch_loss / len(batch_idx)
                n_batches += 1
            
            avg_loss = epoch_loss / max(n_batches, 1)
            losses.append(avg_loss)
            
            if epoch % 5 == 0:
                logger.info("Epoch %d/%d - loss: %.6f", epoch, epochs, avg_loss)
                print("  Epoch %d/%d - loss: %.6f" % (epoch, epochs, avg_loss), flush=True)
        
        return {
            "final_loss": losses[-1] if losses else 0.0,
            "best_loss": min(losses) if losses else 0.0,
            "history": losses,
        }
    
    def save(self, path: str):
        """Save weights."""
        data = {
            "clip_dim": self._clip_dim,
            "hidden_dim": self._hidden_dim,
            "out_dim": self._out_dim,
            "W1": self._W1.tolist(),
            "b1": self._b1.tolist(),
            "W2": self._W2.tolist(),
            "b2": self._b2.tolist(),
            "clip_mean": self._clip_mean.tolist(),
            "clip_std": self._clip_std.tolist(),
            "n_seen": self._n_seen,
        }
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)
    
    @classmethod
    def load(cls, path: str) -> "LearnableDecomposer":
        """Load weights."""
        with open(path) as f:
            data = json.load(f)
        d = cls(clip_dim=data["clip_dim"], hidden_dim=data["hidden_dim"])
        d._W1 = np.array(data["W1"], dtype=np.float32)
        d._b1 = np.array(data["b1"], dtype=np.float32)
        d._W2 = np.array(data["W2"], dtype=np.float32)
        d._b2 = np.array(data["b2"], dtype=np.float32)
        d._clip_mean = np.array(data["clip_mean"], dtype=np.float32)
        d._clip_std = np.array(data["clip_std"], dtype=np.float32)
        d._n_seen = data["n_seen"]
        return d
