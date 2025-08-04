# tests/core_ai/compression/test_alpha_deep_model.py

import unittest
import pytest
from dataclasses import asdict

# Add project root to path to allow absolute imports
import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.append(os.path.join(PROJECT_ROOT, 'apps', 'backend'))

from src.core_ai.compression.alpha_deep_model import AlphaDeepModel, DeepParameter, HAMGist, RelationalContext, Modalities

class TestAlphaDeepModel(unittest.TestCase):

    def setUp(self):
        """Set up a reusable model instance and sample data for tests."""
        self.model = AlphaDeepModel()
        self.sample_data = DeepParameter(
            source_memory_id="mem_test_001",
            timestamp="2025-08-04T05:00:00Z",
            base_gist=HAMGist(
                summary="Test summary.",
                keywords=["test", "summary"],
                original_length=20
            ),
            relational_context=RelationalContext(
                entities=["Entity A", "Entity B"],
                relationships=[{"subject": "Entity A", "verb": "is_related_to", "object": "Entity B"}]
            ),
            modalities=Modalities(
                text_confidence=0.99,
                audio_features={"pitch": 150.5},
                image_features=None
            )
        )

    def test_compress_decompress_cycle(self):
        """Test that data remains identical after a full compression-decompression cycle."""
        print("\n--- test_compress_decompress_cycle ---")
        original_dict = self.sample_data.to_dict()

        compressed = self.model.compress(self.sample_data)
        self.assertIsInstance(compressed, bytes)
        print(f"Compressed data length: {len(compressed)} bytes")

        decompressed = self.model.decompress(compressed)
        self.assertIsInstance(decompressed, dict)

        self.assertEqual(original_dict, decompressed)
        print("Successfully verified that decompressed data matches original data.")

    def test_compression_idempotency(self):
        """Test that compressing the same data twice yields the same result."""
        print("\n--- test_compression_idempotency ---")
        compressed1 = self.model.compress(self.sample_data)
        compressed2 = self.model.compress(self.sample_data)

        self.assertEqual(compressed1, compressed2)
        print("Successfully verified that compressing the same data is idempotent.")

    def test_invalid_input_type_raises_error(self):
        """Test that passing an invalid object type to compress raises a TypeError."""
        print("\n--- test_invalid_input_type_raises_error ---")
        invalid_data = 12345  # An integer is not a valid input type

        with self.assertRaises(TypeError):
            self.model.compress(invalid_data)
        print("Successfully caught TypeError for invalid input.")

    def test_partial_data_handling(self):
        """Test compression and decompression with partially incomplete data."""
        print("\n--- test_partial_data_handling ---")
        partial_data = DeepParameter(
            source_memory_id="mem_test_002",
            timestamp="2025-08-04T05:10:00Z",
            base_gist=HAMGist(summary="Partial data.", keywords=[], original_length=13),
            relational_context=RelationalContext(entities=[], relationships=[]),
            modalities=Modalities(text_confidence=0.90) # audio and image features are default None
        )
        original_dict = partial_data.to_dict()

        compressed = self.model.compress(partial_data)
        decompressed = self.model.decompress(compressed)

        self.assertEqual(original_dict, decompressed)
        print("Successfully verified that partially incomplete data is handled correctly.")

    def test_dict_input(self):
        """Test that the compress method can handle a dictionary input directly."""
        print("\n--- test_dict_input ---")
        original_dict = self.sample_data.to_dict()

        compressed = self.model.compress(original_dict)
        decompressed = self.model.decompress(compressed)

        self.assertEqual(original_dict, decompressed)
        print("Successfully verified that dictionary input is handled correctly.")

if __name__ == '__main__':
    unittest.main()
