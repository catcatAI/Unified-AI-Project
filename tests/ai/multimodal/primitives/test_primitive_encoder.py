"""Tests for primitive encoder."""

import numpy as np
import pytest
import tempfile
from pathlib import Path

from ai.multimodal.primitives.primitive_types import (
    Point, Line, Plane, DrawingInstructions
)
from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder


@pytest.fixture
def encoder():
    return PrimitiveEncoder(embedding_dim=64)


@pytest.fixture
def sample_instructions():
    return DrawingInstructions(
        background_color=(128, 128, 128),
        points=[
            Point(0.25, 0.25, (255, 0, 0), 0.1),
            Point(0.75, 0.75, (0, 255, 0), 0.1),
        ],
        lines=[
            Line(
                Point(0.1, 0.5, (0, 0, 0), 0.0),
                Point(0.9, 0.5, (0, 0, 0), 0.0),
                0.05,
                (0, 0, 255)
            )
        ],
        planes=[
            Plane(
                [
                    Point(0.3, 0.3, (0, 0, 0), 0.0),
                    Point(0.7, 0.3, (0, 0, 0), 0.0),
                    Point(0.7, 0.7, (0, 0, 0), 0.0),
                    Point(0.3, 0.7, (0, 0, 0), 0.0),
                ],
                (255, 255, 0),
                (0, 0, 0),
                0.02
            )
        ]
    )


class TestPrimitiveEncoder:
    def test_encode_returns_embedding(self, encoder, sample_instructions):
        embedding = encoder.encode(sample_instructions)
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (64,)
        assert embedding.dtype == np.float32
    
    def test_encode_normalized(self, encoder, sample_instructions):
        embedding = encoder.encode(sample_instructions)
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-6
    
    def test_decode_returns_instructions(self, encoder, sample_instructions):
        embedding = encoder.encode(sample_instructions)
        decoded = encoder.decode(embedding)
        assert isinstance(decoded, DrawingInstructions)
        # Background color should be in valid range
        assert all(0 <= c <= 255 for c in decoded.background_color)
    
    def test_encode_decode_roundtrip_after_training(self, encoder, sample_instructions):
        # Train encoder to improve reconstruction
        encoder.train([sample_instructions] * 10, epochs=50, lr=0.01)
        
        embedding = encoder.encode(sample_instructions)
        decoded = encoder.decode(embedding)
        
        # After training, reconstruction should be better
        # Check that background color is closer to original
        orig_vec = sample_instructions.to_vector()
        decoded_vec = decoded.to_vector()
        mse = np.mean((orig_vec - decoded_vec) ** 2)
        
        # MSE should be reasonably small after training
        assert mse < 0.1
    
    def test_train_step_reduces_loss(self, encoder, sample_instructions):
        # Get initial reconstruction
        initial_embedding = encoder.encode(sample_instructions)
        initial_decoded = encoder.decode(initial_embedding)
        initial_loss = np.mean((sample_instructions.to_vector() - 
                               initial_decoded.to_vector()) ** 2)
        
        # Train for one step
        loss = encoder.train_step(sample_instructions, lr=0.01)
        
        # Get new reconstruction
        new_embedding = encoder.encode(sample_instructions)
        new_decoded = encoder.decode(new_embedding)
        new_loss = np.mean((sample_instructions.to_vector() - 
                           new_decoded.to_vector()) ** 2)
        
        # Loss should decrease
        assert new_loss <= initial_loss + 1e-6
    
    def test_train_reduces_loss(self, encoder):
        # Create multiple training examples
        examples = []
        for i in range(10):
            instructions = DrawingInstructions(
                points=[Point(np.random.random(), np.random.random(),
                             (int(np.random.random() * 255),
                              int(np.random.random() * 255),
                              int(np.random.random() * 255)),
                             0.1)]
            )
            examples.append(instructions)
        
        # Train
        result = encoder.train(examples, epochs=50, lr=0.01)
        
        # Check that loss decreased
        assert result["final_loss"] < result["history"][0]
    
    def test_save_and_load(self, encoder, sample_instructions):
        # Train encoder
        encoder.train([sample_instructions], epochs=10)
        
        # Save
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        
        encoder.save(temp_path)
        
        # Load
        loaded = PrimitiveEncoder.load(temp_path)
        assert loaded.is_trained
        assert loaded.embedding_dim == encoder.embedding_dim
        
        # Check that loaded encoder produces similar results
        embedding1 = encoder.encode(sample_instructions)
        embedding2 = loaded.encode(sample_instructions)
        assert np.allclose(embedding1, embedding2, atol=1e-5)
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_different_instructions_different_embeddings(self, encoder):
        instr1 = DrawingInstructions(
            points=[Point(0.2, 0.2, (255, 0, 0), 0.1)]
        )
        instr2 = DrawingInstructions(
            points=[Point(0.8, 0.8, (0, 255, 0), 0.1)]
        )
        
        emb1 = encoder.encode(instr1)
        emb2 = encoder.encode(instr2)
        
        assert not np.allclose(emb1, emb2)
