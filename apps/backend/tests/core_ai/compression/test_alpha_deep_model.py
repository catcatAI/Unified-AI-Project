# tests/core_ai/compression/test_alpha_deep_model.py

import unittest
import pytest
from dataclasses import asdict

# Add project root to path to allow absolute imports
import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.append(os.path.join(PROJECT_ROOT, 'apps', 'backend'))

from src.core_ai.compression.alpha_deep_model import AlphaDeepModel, DeepParameter, HAMGist, RelationalContext, Modalities, CompressionAlgorithm

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
            ),
            dna_chain_id="test_chain_001"
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

    def test_different_compression_algorithms(self):
        """Test compression and decompression with different algorithms."""
        print("\n--- test_different_compression_algorithms ---")
        original_dict = self.sample_data.to_dict()
        
        algorithms = [CompressionAlgorithm.ZLIB, CompressionAlgorithm.BZ2, CompressionAlgorithm.LZMA, CompressionAlgorithm.MSGPACK_ONLY]
        
        for algorithm in algorithms:
            with self.subTest(algorithm=algorithm):
                compressed = self.model.compress(self.sample_data, algorithm)
                self.assertIsInstance(compressed, bytes)
                
                decompressed = self.model.decompress(compressed, algorithm)
                self.assertIsInstance(decompressed, dict)
                
                self.assertEqual(original_dict, decompressed)
                print(f"Successfully verified {algorithm.value} compression/decompression cycle.")

    def test_dna_chain_functionality(self):
        """Test DNA data chain functionality."""
        print("\n--- test_dna_chain_functionality ---")
        
        # Test creating a DNA chain
        chain = self.model.create_dna_chain("test_chain")
        self.assertIsNotNone(chain)
        
        # Test adding nodes to the chain
        chain.add_node("mem_test_001")
        chain.add_node("mem_test_002")
        self.assertIn("mem_test_001", chain.nodes)
        self.assertIn("mem_test_002", chain.nodes)
        
        # Test getting a chain
        retrieved_chain = self.model.get_dna_chain("test_chain")
        self.assertEqual(chain, retrieved_chain)
        
        # Test creating a branch
        branch = chain.create_branch("test_branch", "mem_test_001")
        self.assertIn("test_branch", chain.branches)
        self.assertEqual(branch, chain.branches["test_branch"])
        
        print("Successfully verified DNA data chain functionality.")

    def test_learning_mechanism(self):
        """Test the enhanced learning mechanism."""
        print("\n--- test_learning_mechanism ---")
        
        # Test learning without feedback
        self.model.learn(self.sample_data)
        
        # Verify symbol was created
        symbol = self.model.symbolic_space.get_symbol(self.sample_data.source_memory_id)
        self.assertIsNotNone(symbol)
        
        # Test learning with feedback
        feedback = {"accuracy": 0.95, "response_time": 0.5}
        self.model.learn(self.sample_data, feedback)
        
        # Verify feedback was processed
        feedback_symbol = self.model.symbolic_space.get_symbol(f"feedback_{self.sample_data.source_memory_id}")
        self.assertIsNotNone(feedback_symbol)
        
        print("Successfully verified learning mechanism.")

    def test_compression_stats(self):
        """Test compression statistics tracking."""
        print("\n--- test_compression_stats ---")
        
        # Perform some compressions
        self.model.compress(self.sample_data, CompressionAlgorithm.ZLIB)
        self.model.compress(self.sample_data, CompressionAlgorithm.BZ2)
        self.model.compress(self.sample_data, CompressionAlgorithm.ZLIB)
        
        # Check stats
        stats = self.model.get_compression_stats()
        self.assertIn("zlib", stats)
        self.assertIn("bz2", stats)
        self.assertEqual(stats["zlib"]["total_compressions"], 2)
        self.assertEqual(stats["bz2"]["total_compressions"], 1)
        
        print("Successfully verified compression statistics tracking.")

if __name__ == '__main__':
    unittest.main()