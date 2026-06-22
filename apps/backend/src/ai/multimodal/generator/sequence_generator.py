"""Sequence generator - predicts drawing instructions from CLIP embeddings.

Takes a 512-dim CLIP embedding and autoregressively produces a sequence
of 64-dim primitive embeddings, which PrimitiveEncoder decodes into
DrawingInstructions for PrimitiveRenderer to render.
"""

import json
import logging
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class SequenceGenerator:
    """Generates sequences of primitive embeddings from CLIP embeddings.
    
    Uses a simple RNN architecture that can run on CPU.
    
    Pipeline:
        CLIP 512-dim → [RNN] → sequence of 64-dim primitive embeddings
        → PrimitiveEncoder.decode() → DrawingInstructions → PIL Image
    """
    
    def __init__(self, input_dim: int = 512, hidden_dim: int = 128,
                 primitive_dim: int = 64, max_steps: int = 20):
        """Initialize sequence generator.
        
        Args:
            input_dim: CLIP embedding dimension (512)
            hidden_dim: RNN hidden state dimension
            primitive_dim: Output primitive embedding dimension (64)
            max_steps: Maximum number of primitives to generate
        """
        self._input_dim = input_dim
        self._hidden_dim = hidden_dim
        self._primitive_dim = primitive_dim
        self._max_steps = max_steps
        
        rng = np.random.default_rng(42)
        scale_ih = 1.0 / np.sqrt(input_dim)
        scale_hh = 1.0 / np.sqrt(hidden_dim)
        scale_ph = 1.0 / np.sqrt(primitive_dim)
        
        # Input → Hidden
        self._W_ih = (rng.normal(0, scale_ih, (hidden_dim, input_dim))).astype(np.float32)
        self._b_ih = np.zeros(hidden_dim, dtype=np.float32)
        
        # Primitive feedback → Hidden (for autoregressive step)
        self._W_ph = (rng.normal(0, scale_ph, (hidden_dim, primitive_dim))).astype(np.float32)
        self._b_ph = np.zeros(hidden_dim, dtype=np.float32)
        
        # Hidden → Hidden (recurrent)
        self._W_hh = (rng.normal(0, scale_hh, (hidden_dim, hidden_dim))).astype(np.float32)
        self._b_hh = np.zeros(hidden_dim, dtype=np.float32)
        
        # Hidden → Primitive output
        self._W_ho = (rng.normal(0, 1.0 / np.sqrt(hidden_dim),
                                 (primitive_dim, hidden_dim))).astype(np.float32)
        self._b_ho = np.zeros(primitive_dim, dtype=np.float32)
        
        # Stop token predictor (hidden → scalar logit)
        self._W_stop = (rng.normal(0, 1.0 / np.sqrt(hidden_dim),
                                   (hidden_dim,))).astype(np.float32)
        self._b_stop = np.zeros(1, dtype=np.float32)
        
        # Training state
        self._trained = False
    
    def generate(self, clip_embedding: np.ndarray,
                 temperature: float = 0.8) -> List[np.ndarray]:
        """Generate sequence of primitive embeddings from CLIP embedding.
        
        Args:
            clip_embedding: (input_dim,) CLIP embedding vector
            temperature: Sampling temperature (higher = more random)
            
        Returns:
            List of (primitive_dim,) primitive embedding vectors
        """
        if clip_embedding.shape != (self._input_dim,):
            raise ValueError(
                f"Expected clip_embedding shape ({self._input_dim},), "
                f"got {clip_embedding.shape}"
            )
        
        # Initialize hidden state from CLIP embedding
        h = np.tanh(self._W_ih @ clip_embedding + self._b_ih)
        
        primitives: List[np.ndarray] = []
        
        for _step in range(self._max_steps):
            # Generate primitive embedding
            prim_emb = self._W_ho @ h + self._b_ho
            
            # L2 normalize
            norm = np.linalg.norm(prim_emb)
            if norm > 0:
                prim_emb = prim_emb / norm
            
            # Check stop condition
            stop_logit = float(np.dot(self._W_stop, h) + self._b_stop[0])
            stop_prob = 1.0 / (1.0 + np.exp(-np.clip(stop_logit, -10, 10)))
            
            # Sample stop (at temperature)
            adjusted_logit = stop_logit / max(temperature, 0.01)
            stop_sample_prob = 1.0 / (1.0 + np.exp(-np.clip(adjusted_logit, -10, 10)))
            
            if np.random.random() < stop_sample_prob and _step > 0:
                break
            
            primitives.append(prim_emb)
            
            # Update hidden state: tanh(W_hh @ h + W_ph @ prim + b_hh)
            h = np.tanh(
                self._W_hh @ h + self._W_ph @ prim_emb + self._b_hh
            )
        
        return primitives
    
    def generate_deterministic(self, clip_embedding: np.ndarray) -> List[np.ndarray]:
        """Generate primitives greedily (no sampling).
        
        Useful for evaluation and testing.
        """
        if clip_embedding.shape != (self._input_dim,):
            raise ValueError(
                f"Expected clip_embedding shape ({self._input_dim},), "
                f"got {clip_embedding.shape}"
            )
        
        h = np.tanh(self._W_ih @ clip_embedding + self._b_ih)
        primitives: List[np.ndarray] = []
        
        for _step in range(self._max_steps):
            prim_emb = self._W_ho @ h + self._b_ho
            norm = np.linalg.norm(prim_emb)
            if norm > 0:
                prim_emb = prim_emb / norm
            
            stop_logit = float(np.dot(self._W_stop, h) + self._b_stop[0])
            
            if stop_logit > 0.0 and _step > 0:
                break
            
            primitives.append(prim_emb)
            h = np.tanh(
                self._W_hh @ h + self._W_ph @ prim_emb + self._b_hh
            )
        
        return primitives
    
    def train_step(self, clip_embedding: np.ndarray,
                   target_primitives: List[np.ndarray],
                   lr: float = 0.001) -> float:
        """Single training step with teacher forcing.
        
        Args:
            clip_embedding: (input_dim,) CLIP embedding
            target_primitives: List of (primitive_dim,) target embeddings
            lr: Learning rate
            
        Returns:
            MSE loss value
        """
        if clip_embedding.shape != (self._input_dim,):
            raise ValueError(f"Wrong clip_embedding shape: {clip_embedding.shape}")
        
        if len(target_primitives) == 0:
            return 0.0
        
        # Forward pass with teacher forcing
        h = np.tanh(self._W_ih @ clip_embedding + self._b_ih)
        
        predicted = []
        hidden_states = [h.copy()]
        
        for step in range(min(len(target_primitives), self._max_steps)):
            prim_emb = self._W_ho @ h + self._b_ho
            norm = np.linalg.norm(prim_emb)
            if norm > 0:
                prim_emb = prim_emb / norm
            
            predicted.append(prim_emb)
            
            # Teacher forcing: use target, not predicted
            target = target_primitives[step]
            h = np.tanh(
                self._W_hh @ h + self._W_ph @ target + self._b_hh
            )
            hidden_states.append(h.copy())
        
        # Compute loss
        n_steps = len(predicted)
        pred_matrix = np.stack(predicted)     # (n_steps, primitive_dim)
        targ_matrix = np.stack(target_primitives[:n_steps])  # (n_steps, primitive_dim)
        
        loss = float(np.mean((pred_matrix - targ_matrix) ** 2))
        
        # Backward pass (simplified gradient descent)
        error = pred_matrix - targ_matrix  # (n_steps, primitive_dim)
        
        # Gradient for W_ho and b_ho (from output error)
        for step in range(n_steps):
            grad_W_ho = np.outer(error[step], hidden_states[step])
            grad_b_ho = error[step]
            self._W_ho -= lr * grad_W_ho
            self._b_ho -= lr * grad_b_ho
        
        # Gradient for W_ih, W_ph, W_hh (through hidden states - truncated BPTT)
        for step in range(n_steps):
            # Gradient flowing back through tanh: dtanh/dx = 1 - tanh^2(x)
            h_state = hidden_states[step]
            dtanh = 1.0 - h_state ** 2
            
            # Error signal for hidden state
            h_error = self._W_ho.T @ error[step]
            h_grad = h_error * dtanh
            
            # Update W_ih (from input — only on first step)
            if step == 0:
                grad_W_ih = np.outer(h_grad, clip_embedding)
                self._W_ih -= lr * grad_W_ih
            
            # Update W_ph (from primitive feedback)
            grad_W_ph = np.outer(h_grad, target_primitives[step])
            self._W_ph -= lr * grad_W_ph
            
            # Update W_hh (from previous hidden state)
            if step > 0:
                prev_h = hidden_states[step - 1]
                grad_W_hh = np.outer(h_grad, prev_h)
                self._W_hh -= lr * grad_W_hh
        
        # Stop token gradient
        for step in range(n_steps):
            stop_target = 1.0 if step == n_steps - 1 else 0.0
            stop_logit = float(np.dot(self._W_stop, hidden_states[step]) + self._b_stop[0])
            stop_pred = 1.0 / (1.0 + np.exp(-np.clip(stop_logit, -10, 10)))
            stop_error = stop_pred - stop_target
            
            grad_W_stop = stop_error * hidden_states[step]
            self._W_stop -= lr * grad_W_stop
            self._b_stop -= lr * np.array([stop_error])
        
        self._trained = True
        return loss
    
    def train(self, clip_embeddings: List[np.ndarray],
              primitive_sequences: List[List[np.ndarray]],
              epochs: int = 50, lr: float = 0.001) -> dict:
        """Train on a dataset of (clip_embedding, primitive_sequence) pairs.
        
        Args:
            clip_embeddings: List of (input_dim,) CLIP embeddings
            primitive_sequences: List of primitive embedding sequences
            epochs: Number of training epochs
            lr: Learning rate
            
        Returns:
            Training history dict
        """
        if len(clip_embeddings) != len(primitive_sequences):
            raise ValueError("clip_embeddings and primitive_sequences must have same length")
        
        n_samples = len(clip_embeddings)
        losses = []
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            
            # Shuffle indices
            indices = np.random.permutation(n_samples)
            
            for idx in indices:
                loss = self.train_step(
                    clip_embeddings[idx],
                    primitive_sequences[idx],
                    lr=lr
                )
                epoch_loss += loss
            
            avg_loss = epoch_loss / max(n_samples, 1)
            losses.append(avg_loss)
            
            if epoch % 10 == 0:
                logger.info("Epoch %d/%d - loss: %.6f", epoch, epochs, avg_loss)
        
        return {
            "final_loss": losses[-1] if losses else 0.0,
            "history": losses,
            "epochs": epochs,
            "n_samples": n_samples,
        }
    
    @property
    def input_dim(self) -> int:
        return self._input_dim
    
    @property
    def hidden_dim(self) -> int:
        return self._hidden_dim
    
    @property
    def primitive_dim(self) -> int:
        return self._primitive_dim
    
    @property
    def max_steps(self) -> int:
        return self._max_steps
    
    @property
    def is_trained(self) -> bool:
        return self._trained
    
    def save(self, path: str):
        """Save generator weights to JSON file."""
        data = {
            "input_dim": self._input_dim,
            "hidden_dim": self._hidden_dim,
            "primitive_dim": self._primitive_dim,
            "max_steps": self._max_steps,
            "W_ih": self._W_ih.tolist(),
            "b_ih": self._b_ih.tolist(),
            "W_ph": self._W_ph.tolist(),
            "b_ph": self._b_ph.tolist(),
            "W_hh": self._W_hh.tolist(),
            "b_hh": self._b_hh.tolist(),
            "W_ho": self._W_ho.tolist(),
            "b_ho": self._b_ho.tolist(),
            "W_stop": self._W_stop.tolist(),
            "b_stop": self._b_stop.tolist(),
        }
        with open(path, 'w') as f:
            json.dump(data, f)
        logger.info("Saved SequenceGenerator to %s", path)
    
    @classmethod
    def load(cls, path: str) -> 'SequenceGenerator':
        """Load generator weights from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        gen = cls(
            input_dim=data["input_dim"],
            hidden_dim=data["hidden_dim"],
            primitive_dim=data["primitive_dim"],
            max_steps=data["max_steps"],
        )
        gen._W_ih = np.array(data["W_ih"], dtype=np.float32)
        gen._b_ih = np.array(data["b_ih"], dtype=np.float32)
        gen._W_ph = np.array(data["W_ph"], dtype=np.float32)
        gen._b_ph = np.array(data["b_ph"], dtype=np.float32)
        gen._W_hh = np.array(data["W_hh"], dtype=np.float32)
        gen._b_hh = np.array(data["b_hh"], dtype=np.float32)
        gen._W_ho = np.array(data["W_ho"], dtype=np.float32)
        gen._b_ho = np.array(data["b_ho"], dtype=np.float32)
        gen._W_stop = np.array(data["W_stop"], dtype=np.float32)
        gen._b_stop = np.array(data["b_stop"], dtype=np.float32)
        gen._trained = True
        
        logger.info("Loaded SequenceGenerator from %s", path)
        return gen
