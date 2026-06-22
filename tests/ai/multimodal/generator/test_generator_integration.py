"""Integration test for full compositional image generation pipeline."""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from ai.multimodal.generator.sequence_generator import SequenceGenerator
from ai.multimodal.generator.image_generator import ImageGenerator
from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer


class TestFullPipeline:
    """Test end-to-end pipeline: text → CLIP → generator → encoder → renderer → image."""

    def test_text_to_image_pipeline(self):
        """Full pipeline produces an image from text."""
        gen = ImageGenerator()
        img = gen.generate_from_text("a red circle at center")
        assert img is not None
        assert img.size == (128, 128)

    def test_pipeline_with_training(self):
        """Pipeline works after training the generator."""
        gen = ImageGenerator()
        
        # Create small training set
        n = 10
        clip_embs = [np.random.randn(512).astype(np.float32) for _ in range(n)]
        sequences = [[np.random.randn(64).astype(np.float32) for _ in range(2)]
                     for _ in range(n)]
        
        # Train
        result = gen._generator.train(clip_embs, sequences, epochs=20, lr=0.01)
        assert result["final_loss"] < result["history"][0]
        
        # Generate
        img = gen.generate_from_text("a blue square")
        assert img is not None
        img_bytes = img.tobytes()
        assert len(img_bytes) > 0

    def test_encoder_renderer_roundtrip(self):
        """PrimitiveEncoder encode → decode → render produces valid image."""
        encoder = PrimitiveEncoder()
        renderer = PrimitiveRenderer()
        
        from ai.multimodal.primitives.primitive_types import DrawingInstructions, Point
        
        instructions = DrawingInstructions(
            points=[Point(0.3, 0.4, (255, 0, 0), 0.1),
                    Point(0.7, 0.6, (0, 0, 255), 0.08)],
            background_color=(200, 200, 200),
        )
        
        # Encode
        embedding = encoder.encode(instructions)
        assert embedding.shape == (64,)
        
        # Decode
        decoded = encoder.decode(embedding)
        assert decoded is not None
        
        # Render
        img = renderer.render(decoded)
        assert img is not None
        assert img.size == (128, 128)

    def test_generator_encoder_renderer_pipeline(self):
        """SequenceGenerator → PrimitiveEncoder → PrimitiveRenderer pipeline."""
        generator = SequenceGenerator()
        encoder = PrimitiveEncoder()
        renderer = PrimitiveRenderer()
        
        clip_emb = np.random.randn(512).astype(np.float32)
        
        # Generate primitive sequence
        primitives = generator.generate(clip_emb)
        assert len(primitives) > 0
        
        # Decode first primitive
        instructions = encoder.decode(primitives[0])
        assert instructions is not None
        
        # Render
        img = renderer.render(instructions)
        assert img is not None
        assert img.size == (128, 128)
        
        # Image should not be all white (has some content)
        arr = np.array(img)
        assert arr.mean() < 250  # Not pure white

    def test_multiple_generations_produce_different_images(self):
        """Different texts should produce different images."""
        gen = ImageGenerator()
        
        img1 = gen.generate_from_text("red")
        img2 = gen.generate_from_text("blue")
        
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # They should differ (different random seeds from different text)
        assert not np.array_equal(arr1, arr2)
