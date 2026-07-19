"""Encode primitive parameters to/from embeddings."""

from typing import Optional

import numpy as np

from .primitive_types import DrawingInstructions


class PrimitiveEncoder:
    """Encodes DrawingInstructions to/from fixed-size embedding vectors.

    Uses linear projection to map between primitive parameter space
    and embedding space. Can be trained to learn meaningful mappings.
    """

    def __init__(self, embedding_dim: int = 128):
        self._embedding_dim = embedding_dim
        from .primitive_types import TOTAL_DIM

        self._param_dim = TOTAL_DIM  # 263

        rng = np.random.default_rng(42)

        # He initialization for better gradient flow
        scale_enc = np.sqrt(2.0 / self._param_dim)
        scale_dec = np.sqrt(2.0 / embedding_dim)

        self._W_encode = rng.normal(0, scale_enc, (embedding_dim, self._param_dim)).astype(
            np.float32
        )
        self._b_encode = np.zeros(embedding_dim, dtype=np.float32)

        self._W_decode = rng.normal(0, scale_dec, (self._param_dim, embedding_dim)).astype(
            np.float32
        )
        self._b_decode = np.zeros(self._param_dim, dtype=np.float32)

        # Training state
        self._trained = False
        self._best_loss = float("inf")

    def encode(self, instructions: DrawingInstructions) -> np.ndarray:
        """Encode drawing instructions to embedding vector.

        Args:
            instructions: DrawingInstructions to encode

        Returns:
            Embedding vector of shape (embedding_dim,)
        """
        param_vec = instructions.to_vector()
        embedding = self._W_encode @ param_vec + self._b_encode

        # L2 normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.astype(np.float32)

    def decode(self, embedding: np.ndarray, canvas_size: tuple = (128, 128)) -> DrawingInstructions:
        """Decode embedding back to drawing instructions.

        Args:
            embedding: Embedding vector of shape (embedding_dim,)
            canvas_size: Target canvas size for the instructions

        Returns:
            Reconstructed DrawingInstructions
        """
        # Project back to parameter space
        param_vec = self._W_decode @ embedding + self._b_decode

        # Clamp values to valid ranges
        param_vec = np.clip(param_vec, 0.0, 1.0)

        # Convert to DrawingInstructions
        return DrawingInstructions.from_vector(param_vec, canvas_size)

    def train_step(self, instructions: DrawingInstructions, lr: float = 0.001) -> float:
        """Single training step to improve encode/decode fidelity.

        Uses reconstruction loss with gradient clipping.

        Args:
            instructions: Training example
            lr: Learning rate

        Returns:
            Reconstruction loss (MSE)
        """
        # Forward pass
        param_vec = instructions.to_vector()
        embedding = self._W_encode @ param_vec + self._b_encode
        reconstructed = self._W_decode @ embedding + self._b_decode

        # Clamp to prevent overflow
        reconstructed = np.clip(reconstructed, -10.0, 10.0)

        # Compute loss
        loss = np.mean((param_vec - reconstructed) ** 2)

        if not np.isfinite(loss):
            return float("inf")

        # Backward pass with gradient clipping
        error = reconstructed - param_vec
        error = np.clip(error, -1.0, 1.0)  # Clip error too

        # Update decode weights
        grad_W_decode = np.outer(error, embedding)
        grad_b_decode = error

        # Gradient clipping by norm
        grad_norm = np.sqrt(np.sum(grad_W_decode**2) + np.sum(grad_b_decode**2))
        if grad_norm > 5.0:
            scale = 5.0 / grad_norm
            grad_W_decode *= scale
            grad_b_decode *= scale

        self._W_decode -= lr * grad_W_decode
        self._b_decode -= lr * grad_b_decode

        # Update encode weights (through chain rule)
        grad_embedding = self._W_decode.T @ error
        grad_embedding = np.clip(grad_embedding, -1.0, 1.0)
        grad_W_encode = np.outer(grad_embedding, param_vec)
        grad_b_encode = grad_embedding

        grad_norm2 = np.sqrt(np.sum(grad_W_encode**2) + np.sum(grad_b_encode**2))
        if grad_norm2 > 5.0:
            scale = 5.0 / grad_norm2
            grad_W_encode *= scale
            grad_b_encode *= scale

        self._W_encode -= lr * grad_W_encode
        self._b_encode -= lr * grad_b_encode

        self._trained = True
        return float(loss)

    def train(self, instructions_list: list, epochs: int = 100, lr: float = 0.001) -> dict:
        """Train encoder on a list of drawing instructions.

        Uses autoencoder reconstruction loss with early stopping.
        Initializes decode bias to mean of training vectors for faster convergence.

        Args:
            instructions_list: List of DrawingInstructions to train on
            epochs: Number of training epochs
            lr: Learning rate

        Returns:
            Dictionary with training history
        """
        if not instructions_list:
            return {"final_loss": 0.0, "best_loss": 0.0, "history": [], "epochs_trained": 0}

        # Initialize decode bias to mean of training vectors (key fix!)
        all_vecs = np.array([inst.to_vector() for inst in instructions_list])
        mean_vec = all_vecs.mean(axis=0)
        self._b_decode = mean_vec.copy()

        losses = []
        best_W_enc = self._W_encode.copy()
        best_b_enc = self._b_encode.copy()
        best_W_dec = self._W_decode.copy()
        best_b_dec = self._b_decode.copy()
        best_loss = float("inf")
        patience = max(10, epochs // 5)
        no_improve = 0

        for epoch in range(epochs):
            epoch_loss = 0.0
            for instructions in instructions_list:
                loss = self.train_step(instructions, lr)
                if np.isfinite(loss):
                    epoch_loss += loss

            avg_loss = epoch_loss / max(len(instructions_list), 1)
            losses.append(avg_loss)

            # Early stopping
            if avg_loss < best_loss:
                best_loss = avg_loss
                best_W_enc = self._W_encode.copy()
                best_b_enc = self._b_encode.copy()
                best_W_dec = self._W_decode.copy()
                best_b_dec = self._b_decode.copy()
                no_improve = 0
            else:
                no_improve += 1
                if no_improve >= patience:
                    break

        # Restore best weights
        self._W_encode = best_W_enc
        self._b_encode = best_b_enc
        self._W_decode = best_W_dec
        self._b_decode = best_b_dec
        self._best_loss = best_loss

        return {
            "final_loss": losses[-1] if losses else 0.0,
            "best_loss": best_loss,
            "history": losses,
            "epochs_trained": len(losses),
        }

    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim

    @property
    def is_trained(self) -> bool:
        return self._trained

    def save(self, path: str):
        """Save encoder weights to file."""
        data = {
            "embedding_dim": self._embedding_dim,
            "param_dim": self._param_dim,
            "W_encode": self._W_encode.tolist(),
            "b_encode": self._b_encode.tolist(),
            "W_decode": self._W_decode.tolist(),
            "b_decode": self._b_decode.tolist(),
        }
        import json

        with open(path, "w") as f:
            json.dump(data, f)

    @classmethod
    def load(cls, path: str) -> "PrimitiveEncoder":
        """Load encoder weights from file."""
        import json

        with open(path, "r") as f:
            data = json.load(f)

        encoder = cls(embedding_dim=data["embedding_dim"])
        encoder._W_encode = np.array(data["W_encode"], dtype=np.float32)
        encoder._b_encode = np.array(data["b_encode"], dtype=np.float32)
        encoder._W_decode = np.array(data["W_decode"], dtype=np.float32)
        encoder._b_decode = np.array(data["b_decode"], dtype=np.float32)
        encoder._trained = True

        return encoder
