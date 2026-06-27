"""Integration tests for primitives package."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
from ai.multimodal.primitives.primitive_library import PrimitiveLibrary
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.primitives.primitive_types import DrawingInstructions, Line, Plane, Point


class TestPrimitivesIntegration:
    """End-to-end integration tests for primitives system."""
    
    def test_full_pipeline(self):
        """Test complete pipeline: create → encode → store → retrieve → render."""
        # 1. Create drawing instructions
        instructions = DrawingInstructions(
            background_color=(240, 240, 240),
            points=[
                Point(0.3, 0.3, (255, 0, 0), 0.15),
                Point(0.7, 0.7, (0, 255, 0), 0.1),
            ],
            lines=[
                Line(
                    Point(0.3, 0.3, (0, 0, 0), 0.0),
                    Point(0.7, 0.7, (0, 0, 0), 0.0),
                    0.05,
                    (0, 0, 255)
                )
            ],
            planes=[
                Plane(
                    [
                        Point(0.1, 0.1, (0, 0, 0), 0.0),
                        Point(0.9, 0.1, (0, 0, 0), 0.0),
                        Point(0.9, 0.9, (0, 0, 0), 0.0),
                        Point(0.1, 0.9, (0, 0, 0), 0.0),
                    ],
                    (200, 200, 255),
                    (0, 0, 0),
                    0.02
                )
            ]
        )
        
        # 2. Initialize components
        renderer = PrimitiveRenderer(canvas_size=(128, 128))
        encoder = PrimitiveEncoder(embedding_dim=64)
        library = PrimitiveLibrary(embedding_dim=64, max_primitives=100)
        
        # 3. Encode to embedding
        embedding = encoder.encode(instructions)
        assert embedding.shape == (64,)
        assert np.linalg.norm(embedding) > 0.9  # Should be normalized
        
        # 4. Add to library
        success = library.add_primitive("test_prim", instructions, embedding)
        assert success is True
        assert library.size == 1
        
        # 5. Retrieve from library
        retrieved = library.get_primitive("test_prim")
        assert retrieved is not None
        assert retrieved.background_color == instructions.background_color
        
        # 6. Find similar
        similar = library.find_similar(embedding, top_k=1)
        assert len(similar) == 1
        assert similar[0][0] == "test_prim"
        assert similar[0][1] > 0.9
        
        # 7. Render to image
        img = renderer.render(instructions)
        assert img.size == (128, 128)
        assert img.mode == "RGB"
        
        # 8. Encode/decode roundtrip
        decoded = encoder.decode(embedding)
        assert isinstance(decoded, DrawingInstructions)
        
        # 9. Render decoded
        decoded_img = renderer.render(decoded)
        assert decoded_img.size == (128, 128)
        
        # 10. Save/load library
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        
        library.save(temp_path)
        loaded_library = PrimitiveLibrary.load(temp_path)
        assert loaded_library.size == 1
        assert loaded_library.get_primitive("test_prim") is not None
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_multiple_primitives_library(self):
        """Test library with multiple primitives."""
        library = PrimitiveLibrary(embedding_dim=64, max_primitives=50)
        encoder = PrimitiveEncoder(embedding_dim=64)
        renderer = PrimitiveRenderer(canvas_size=(128, 128))
        
        # Create 10 different primitives
        for i in range(10):
            instructions = DrawingInstructions(
                background_color=(255, 255, 255),
                points=[
                    Point(np.random.random(), np.random.random(),
                         (int(np.random.random() * 255),
                          int(np.random.random() * 255),
                          int(np.random.random() * 255)),
                         0.1)
                ]
            )
            
            embedding = encoder.encode(instructions)
            library.add_primitive(f"prim_{i:04d}", instructions, embedding)
        
        assert library.size == 10
        
        # Find similar to first primitive
        first_embedding = library.get_embedding("prim_0000")
        similar = library.find_similar(first_embedding, top_k=5)
        
        assert len(similar) == 5
        assert similar[0][0] == "prim_0000"  # Most similar should be itself
        
        # Test auto-expand
        new_embedding = np.random.randn(64).astype(np.float32)
        new_embedding = new_embedding / np.linalg.norm(new_embedding)
        new_instructions = DrawingInstructions(
            points=[Point(0.5, 0.5, (255, 0, 0), 0.1)]
        )
        
        new_name = library.auto_expand(new_embedding, new_instructions, threshold=0.5)
        assert new_name is not None
        assert library.size == 11
    
    def test_training_improves_encoder(self):
        """Test that training improves encoder reconstruction."""
        encoder = PrimitiveEncoder(embedding_dim=64)
        
        # Create training examples
        examples = []
        for _ in range(20):
            instructions = DrawingInstructions(
                background_color=(int(np.random.random() * 255),
                                 int(np.random.random() * 255),
                                 int(np.random.random() * 255)),
                points=[
                    Point(np.random.random(), np.random.random(),
                         (int(np.random.random() * 255),
                          int(np.random.random() * 255),
                          int(np.random.random() * 255)),
                         0.1)
                ]
            )
            examples.append(instructions)
        
        # Measure initial reconstruction error
        initial_errors = []
        for instr in examples:
            embedding = encoder.encode(instr)
            decoded = encoder.decode(embedding)
            error = np.mean((instr.to_vector() - decoded.to_vector()) ** 2)
            initial_errors.append(error)
        
        avg_initial_error = np.mean(initial_errors)
        
        # Train
        encoder.train(examples, epochs=100, lr=0.01)
        
        # Measure final reconstruction error
        final_errors = []
        for instr in examples:
            embedding = encoder.encode(instr)
            decoded = encoder.decode(embedding)
            error = np.mean((instr.to_vector() - decoded.to_vector()) ** 2)
            final_errors.append(error)
        
        avg_final_error = np.mean(final_errors)
        
        # Error should decrease
        assert avg_final_error < avg_initial_error
    
    def test_renderer_quality(self):
        """Test that renderer produces non-trivial images."""
        renderer = PrimitiveRenderer(canvas_size=(128, 128))
        
        # Create complex instructions
        instructions = DrawingInstructions(
            background_color=(100, 150, 200),
            points=[
                Point(0.2, 0.3, (255, 0, 0), 0.1),
                Point(0.8, 0.7, (0, 255, 0), 0.1),
                Point(0.5, 0.5, (0, 0, 255), 0.15),
            ],
            lines=[
                Line(
                    Point(0.1, 0.1, (0, 0, 0), 0.0),
                    Point(0.9, 0.9, (0, 0, 0), 0.0),
                    0.03,
                    (255, 255, 0)
                ),
                Line(
                    Point(0.9, 0.1, (0, 0, 0), 0.0),
                    Point(0.1, 0.9, (0, 0, 0), 0.0),
                    0.02,
                    (255, 0, 255)
                ),
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
                    0.01
                )
            ]
        )
        
        img = renderer.render(instructions)
        arr = np.array(img)
        
        # Check that image has variation (not all same color)
        unique_colors = len(np.unique(arr.reshape(-1, 3), axis=0))
        assert unique_colors > 5  # Should have several different colors
        
        # Check that image is not all black or all white
        mean_val = arr.mean()
        assert 10 < mean_val < 245
