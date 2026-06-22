"""Encode primitive parameters to/from embeddings."""

import numpy as np
from typing import Optional

from .primitive_types import DrawingInstructions


class PrimitiveEncoder:
    """Encodes DrawingInstructions to/from fixed-size embedding vectors.
    
    Uses linear projection to map between primitive parameter space
    and embedding space. Can be trained to learn meaningful mappings.
    """
    
    def __init__(self, embedding_dim: int = 64):
        self._embedding_dim = embedding_dim
        self._param_dim = 116  # Fixed by DrawingInstructions.to_vector()
        
        # Initialize random projection matrices
        rng = np.random.default_rng(42)
        scale = 1.0 / np.sqrt(self._param_dim)
        self._W_encode = rng.normal(0, scale, (embedding_dim, self._param_dim)).astype(np.float32)
        self._b_encode = np.zeros(embedding_dim, dtype=np.float32)
        
        self._W_decode = rng.normal(0, scale, (self._param_dim, embedding_dim)).astype(np.float32)
        self._b_decode = np.zeros(self._param_dim, dtype=np.float32)
        
        # Training state
        self._trained = False
    
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
    
    def decode(self, embedding: np.ndarray, 
               canvas_size: tuple = (128, 128)) -> DrawingInstructions:
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
    
    def train_step(self, instructions: DrawingInstructions, 
                   lr: float = 0.001) -> float:
        """Single training step to improve encode/decode fidelity.
        
        Uses reconstruction loss: minimize difference between
        original and decoded parameters.
        
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
        
        # Compute loss
        loss = np.mean((param_vec - reconstructed) ** 2)
        
        # Backward pass (simplified gradient descent)
        error = reconstructed - param_vec
        
        # Update decode weights
        grad_W_decode = np.outer(error, embedding)
        grad_b_decode = error
        self._W_decode -= lr * grad_W_decode
        self._b_decode -= lr * grad_b_decode
        
        # Update encode weights (through chain rule)
        grad_embedding = self._W_decode.T @ error
        grad_W_encode = np.outer(grad_embedding, param_vec)
        grad_b_encode = grad_embedding
        self._W_encode -= lr * grad_W_encode
        self._b_encode -= lr * grad_b_encode
        
        self._trained = True
        return float(loss)
    
    def train(self, instructions_list: list, epochs: int = 100, 
              lr: float = 0.001) -> dict:
        """Train encoder on a list of drawing instructions.
        
        Args:
            instructions_list: List of DrawingInstructions to train on
            epochs: Number of training epochs
            lr: Learning rate
            
        Returns:
            Dictionary with training history
        """
        losses = []
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            for instructions in instructions_list:
                loss = self.train_step(instructions, lr)
                epoch_loss += loss
            
            avg_loss = epoch_loss / len(instructions_list)
            losses.append(avg_loss)
        
        return {
            "final_loss": losses[-1] if losses else 0.0,
            "history": losses,
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
        with open(path, 'w') as f:
            json.dump(data, f)
    
    @classmethod
    def load(cls, path: str) -> 'PrimitiveEncoder':
        """Load encoder weights from file."""
        import json
        with open(path, 'r') as f:
            data = json.load(f)
        
        encoder = cls(embedding_dim=data["embedding_dim"])
        encoder._W_encode = np.array(data["W_encode"], dtype=np.float32)
        encoder._b_encode = np.array(data["b_encode"], dtype=np.float32)
        encoder._W_decode = np.array(data["W_decode"], dtype=np.float32)
        encoder._b_decode = np.array(data["b_decode"], dtype=np.float32)
        encoder._trained = True
        
        return encoder
