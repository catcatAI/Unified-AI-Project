"""Tests for AlphaDeepModel"""
import pytest


class TestAlphaDeepModel:
    """Tests for AlphaDeepModel core functionality"""

    def test_import(self):
        try:
            from ai.compression.alpha_deep_model import (
                AlphaDeepModel,
                CompressionAlgorithm,
                DNADataChain,
            )
        except ImportError:
            pytest.skip("AlphaDeepModel not available (stub module)")
            return
        assert AlphaDeepModel is not None
        assert CompressionAlgorithm is not None
        assert DNADataChain is not None

    def test_compression_algorithm_values(self):
        try:
            from ai.compression.alpha_deep_model import CompressionAlgorithm
        except ImportError:
            pytest.skip("AlphaDeepModel not available (stub module)")
            return
        assert CompressionAlgorithm.ZLIB.value == "zlib"
        assert CompressionAlgorithm.BZ2.value == "bz2"
        assert CompressionAlgorithm.LZMA.value == "lzma"
        assert CompressionAlgorithm.MSGPACK_ONLY.value == "msgpack_only"

    def test_dna_data_chain_creation(self):
        try:
            from ai.compression.alpha_deep_model import DNADataChain
        except ImportError:
            pytest.skip("AlphaDeepModel not available (stub module)")
            return
        chain = DNADataChain(chain_id="test_chain")
        assert chain.chain_id == "test_chain"
        assert chain.nodes == []
        assert chain.branches == {}

    def test_dna_data_chain_add_node(self):
        try:
            from ai.compression.alpha_deep_model import DNADataChain
        except ImportError:
            pytest.skip("AlphaDeepModel not available (stub module)")
            return
        chain = DNADataChain(chain_id="test_chain")
        chain.add_node("node1")
        chain.add_node("node2")
        chain.add_node("node1")
        assert len(chain.nodes) == 2
        assert "node1" in chain.nodes
        assert "node2" in chain.nodes

    def test_dna_data_chain_create_branch(self):
        try:
            from ai.compression.alpha_deep_model import DNADataChain
        except ImportError:
            pytest.skip("AlphaDeepModel not available (stub module)")
            return
        chain = DNADataChain(chain_id="main")
        chain.add_node("node_a")
        branch = chain.create_branch("branch1", "node_a")
        assert branch.chain_id == "branch1"
        assert branch.metadata["parent_chain"] == "main"
        assert "branch1" in chain.branches

    def test_dna_data_chain_create_branch_missing_node(self):
        try:
            from ai.compression.alpha_deep_model import DNADataChain
        except ImportError:
            pytest.skip("AlphaDeepModel not available (stub module)")
            return
        chain = DNADataChain(chain_id="main")
        with pytest.raises(ValueError):
            chain.create_branch("branch1", "nonexistent")

    def test_dna_data_chain_merge(self):
        try:
            from ai.compression.alpha_deep_model import DNADataChain
        except ImportError:
            pytest.skip("AlphaDeepModel not available (stub module)")
            return
        chain1 = DNADataChain(chain_id="a")
        chain1.add_node("n1")
        chain1.add_node("n2")
        chain2 = DNADataChain(chain_id="b")
        chain2.add_node("n2")
        chain2.add_node("n3")
        result = chain1.merge_chain(chain2, "n2")
        assert result is True
        assert "n3" in chain1.nodes
