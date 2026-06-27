"""Tests for primitive library."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
from ai.multimodal.primitives.primitive_library import PrimitiveLibrary
from ai.multimodal.primitives.primitive_types import DrawingInstructions, Line, Plane, Point


@pytest.fixture
def library():
    return PrimitiveLibrary(embedding_dim=64, max_primitives=100)


@pytest.fixture
def sample_embedding():
    emb = np.random.randn(64).astype(np.float32)
    return emb / np.linalg.norm(emb)


@pytest.fixture
def sample_instructions():
    return DrawingInstructions(
        points=[Point(0.5, 0.5, (255, 0, 0), 0.1)],
        background_color=(255, 255, 255)
    )


class TestPrimitiveLibrary:
    def test_add_primitive(self, library, sample_embedding, sample_instructions):
        result = library.add_primitive("test", sample_instructions, sample_embedding)
        assert result is True
        assert library.size == 1
    
    def test_add_primitive_duplicate_name(self, library, sample_embedding, sample_instructions):
        library.add_primitive("test", sample_instructions, sample_embedding)
        result = library.add_primitive("test", sample_instructions, sample_embedding)
        assert result is False
        assert library.size == 1
    
    def test_add_primitive_wrong_embedding_dim(self, library, sample_instructions):
        wrong_emb = np.random.randn(32).astype(np.float32)
        result = library.add_primitive("test", sample_instructions, wrong_emb)
        assert result is False
        assert library.size == 0
    
    def test_get_primitive(self, library, sample_embedding, sample_instructions):
        library.add_primitive("test", sample_instructions, sample_embedding)
        retrieved = library.get_primitive("test")
        assert retrieved is not None
        assert retrieved.background_color == sample_instructions.background_color
    
    def test_get_primitive_not_found(self, library):
        retrieved = library.get_primitive("nonexistent")
        assert retrieved is None
    
    def test_get_embedding(self, library, sample_embedding, sample_instructions):
        library.add_primitive("test", sample_instructions, sample_embedding)
        retrieved = library.get_embedding("test")
        assert retrieved is not None
        assert np.allclose(retrieved, sample_embedding)
    
    def test_find_similar(self, library, sample_instructions):
        # Add multiple primitives
        for i in range(5):
            emb = np.random.randn(64).astype(np.float32)
            emb = emb / np.linalg.norm(emb)
            library.add_primitive(f"prim_{i}", sample_instructions, emb)
        
        # Query with first primitive's embedding
        query_emb = library.get_embedding("prim_0")
        similar = library.find_similar(query_emb, top_k=3)
        
        assert len(similar) == 3
        assert similar[0][0] == "prim_0"  # Most similar should be itself
        assert similar[0][1] > 0.9  # Should be very similar
    
    def test_auto_expand_new_primitive(self, library, sample_instructions):
        emb1 = np.random.randn(64).astype(np.float32)
        emb1 = emb1 / np.linalg.norm(emb1)
        
        emb2 = np.random.randn(64).astype(np.float32)
        emb2 = emb2 / np.linalg.norm(emb2)
        
        # First primitive should always be added
        name1 = library.auto_expand(emb1, sample_instructions, threshold=0.5)
        assert name1 is not None
        assert library.size == 1
        
        # Second primitive with different embedding should be added
        name2 = library.auto_expand(emb2, sample_instructions, threshold=0.5)
        assert name2 is not None
        assert library.size == 2
    
    def test_auto_expand_too_similar(self, library, sample_instructions):
        emb = np.random.randn(64).astype(np.float32)
        emb = emb / np.linalg.norm(emb)
        
        # Add first primitive
        library.add_primitive("prim_0", sample_instructions, emb)
        
        # Try to add very similar primitive
        similar_emb = emb + np.random.randn(64).astype(np.float32) * 0.01
        similar_emb = similar_emb / np.linalg.norm(similar_emb)
        
        result = library.auto_expand(similar_emb, sample_instructions, threshold=0.5)
        assert result is None  # Should be rejected
        assert library.size == 1
    
    def test_save_and_load(self, library, sample_embedding, sample_instructions):
        # Add some primitives
        library.add_primitive("prim_0", sample_instructions, sample_embedding)
        
        # Save
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        
        library.save(temp_path)
        
        # Load
        loaded = PrimitiveLibrary.load(temp_path)
        assert loaded.size == 1
        assert loaded.get_primitive("prim_0") is not None
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_max_primitives(self):
        library = PrimitiveLibrary(embedding_dim=64, max_primitives=2)
        
        for i in range(5):
            emb = np.random.randn(64).astype(np.float32)
            emb = emb / np.linalg.norm(emb)
            instr = DrawingInstructions()
            library.add_primitive(f"prim_{i}", instr, emb)
        
        assert library.size == 2  # Should stop at max
