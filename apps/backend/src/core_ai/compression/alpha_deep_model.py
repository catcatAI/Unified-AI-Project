# alpha_deep_model.py
import sys
import os

# Add the parent directory of core_ai to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import msgpack
import zlib
import bz2
import lzma
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from core_ai.symbolic_space.unified_symbolic_space import UnifiedSymbolicSpace

class CompressionAlgorithm(Enum):
    """Compression algorithms supported by the model."""
    ZLIB = "zlib"
    BZ2 = "bz2"
    LZMA = "lzma"
    MSGPACK_ONLY = "msgpack_only"

@dataclass
class HAMGist:
    """Represents the basic abstracted gist from HAM."""
    summary: str
    keywords: List[str]
    original_length: int

@dataclass
class RelationalContext:
    """Represents the structured relationships between entities."""
    entities: List[str]
    relationships: List[Dict[str, Any]] # e.g., {"subject": "A", "verb": "likes", "object": "B"}

@dataclass
class Modalities:
    """Represents data from different modalities, designed for extensibility."""
    text_confidence: float
    audio_features: Optional[Dict[str, Any]] = None
    image_features: Optional[Dict[str, Any]] = None

@dataclass
class DeepParameter:
    """The main input structure for the AlphaDeepModel, combining various contexts."""
    source_memory_id: str
    timestamp: str
    base_gist: HAMGist
    relational_context: RelationalContext
    modalities: Modalities
    action_feedback: Optional[Dict[str, Any]] = None # New field for feedback loop
    dna_chain_id: Optional[str] = None  # DNA衍生数据链ID

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass instance to a dictionary for serialization."""
        return asdict(self)

class DNADataChain:
    """DNA衍生数据链结构，用于组织相关记忆"""
    
    def __init__(self, chain_id: str):
        self.chain_id = chain_id
        self.nodes: List[str] = []  # Memory IDs in the chain
        self.branches: Dict[str, 'DNADataChain'] = {}  # Branches from this chain
        self.metadata: Dict[str, Any] = {}
    
    def add_node(self, memory_id: str):
        """Add a memory node to the chain."""
        if memory_id not in self.nodes:
            self.nodes.append(memory_id)
    
    def create_branch(self, branch_id: str, from_node: str) -> 'DNADataChain':
        """Create a branch from a specific node."""
        if from_node not in self.nodes:
            raise ValueError(f"Node {from_node} not found in chain")
        
        branch = DNADataChain(branch_id)
        branch.metadata['parent_chain'] = self.chain_id
        branch.metadata['branch_point'] = from_node
        self.branches[branch_id] = branch
        return branch
    
    def merge_chain(self, other_chain: 'DNADataChain', at_node: str) -> bool:
        """Merge another chain at a specific node."""
        if at_node not in self.nodes:
            return False
        
        # Add nodes from other chain
        for node in other_chain.nodes:
            if node not in self.nodes:
                self.nodes.append(node)
        
        # Merge branches
        self.branches.update(other_chain.branches)
        return True

class AlphaDeepModel:
    """
    A model for performing high-compression on structured 'deep parameter' objects.
    Enhanced with DNA衍生数据链技术和更高效的压缩算法.
    """

    def __init__(self, symbolic_space_db: str = 'alpha_deep_model_symbolic_space.db'):
        """
        Initializes the AlphaDeepModel.
        """
        self.symbolic_space = UnifiedSymbolicSpace(symbolic_space_db)
        self.dna_chains: Dict[str, DNADataChain] = {}  # DNA数据链存储
        self.compression_stats: Dict[str, Dict[str, Any]] = {}  # 压缩统计信息

    def learn(self, deep_parameter: DeepParameter, feedback: Optional[Dict[str, Any]] = None) -> None:
        """
        Enhanced learning mechanism that updates the model's internal state
        based on new DeepParameters and optional feedback.
        """
        print(f"Learning from deep parameter: {deep_parameter.source_memory_id}")
        if feedback:
            print(f"Received feedback: {feedback}")
        
        # 1. Update symbolic space based on deep_parameter
        # Ensure the main memory symbol exists or create it
        memory_symbol = self.symbolic_space.get_symbol(deep_parameter.source_memory_id)
        if not memory_symbol:
            self.symbolic_space.add_symbol(deep_parameter.source_memory_id, 'Memory', {'timestamp': deep_parameter.timestamp})
        else:
            self.symbolic_space.update_symbol(deep_parameter.source_memory_id, properties={'timestamp': deep_parameter.timestamp})

        # Add or update gist as a symbol and relate it to the memory
        gist_symbol_name = deep_parameter.base_gist.summary
        self.symbolic_space.add_symbol(gist_symbol_name, 'Gist', {'keywords': deep_parameter.base_gist.keywords, 'original_length': deep_parameter.base_gist.original_length})
        self.symbolic_space.add_relationship(deep_parameter.source_memory_id, gist_symbol_name, 'contains_gist')

        # Process relational context
        for entity in deep_parameter.relational_context.entities:
            self.symbolic_space.add_symbol(entity, 'Entity') # Ensure entity exists
        for rel in deep_parameter.relational_context.relationships:
            # Ensure subject and object symbols exist before adding relationship
            self.symbolic_space.add_symbol(rel['subject'], 'Unknown') # Type can be refined later
            self.symbolic_space.add_symbol(rel['object'], 'Unknown') # Type can be refined later
            self.symbolic_space.add_relationship(rel['subject'], rel['object'], rel['verb'], rel)

        # Process modalities (e.g., add as properties to the memory symbol or create new symbols)
        self.symbolic_space.update_symbol(deep_parameter.source_memory_id, properties={'modalities': asdict(deep_parameter.modalities)})

        # 2. Incorporate action feedback into the symbolic space
        if deep_parameter.action_feedback:
            feedback_id = f"feedback_{deep_parameter.source_memory_id}"
            self.symbolic_space.add_symbol(feedback_id, 'ActionFeedback', deep_parameter.action_feedback)
            self.symbolic_space.add_relationship(deep_parameter.source_memory_id, feedback_id, 'has_feedback')

        # 3. Create or update DNA data chain
        if deep_parameter.dna_chain_id:
            if deep_parameter.dna_chain_id not in self.dna_chains:
                self.dna_chains[deep_parameter.dna_chain_id] = DNADataChain(deep_parameter.dna_chain_id)
            self.dna_chains[deep_parameter.dna_chain_id].add_node(deep_parameter.source_memory_id)
        
        # 4. Update learning based on feedback
        if feedback:
            # Adjust model parameters based on feedback
            self._adjust_model_parameters(deep_parameter, feedback)
        
        print(f"Symbolic space updated for {deep_parameter.source_memory_id}")

    def _adjust_model_parameters(self, deep_parameter: DeepParameter, feedback: Dict[str, Any]):
        """Adjust model parameters based on feedback."""
        # This is a placeholder for more complex parameter adjustment logic
        # In a real implementation, this would adjust compression or learning strategies
        feedback_symbol = f"feedback_{deep_parameter.source_memory_id}"
        current_symbol = self.symbolic_space.get_symbol(feedback_symbol)
        if current_symbol:
            current_props = current_symbol.get('properties', {})
            current_props.update(feedback)
            self.symbolic_space.update_symbol(feedback_symbol, properties=current_props)

    def compress(self, deep_parameter: Any, algorithm: CompressionAlgorithm = CompressionAlgorithm.ZLIB) -> bytes:
        """
        Compresses a deep parameter object into a highly compressed binary format.
        Supports multiple compression algorithms for optimal performance.

        Args:
            deep_parameter: The deep parameter object (e.g., a dataclass instance).
            algorithm: The compression algorithm to use.

        Returns:
            A byte string representing the compressed data.
        """
        if hasattr(deep_parameter, 'to_dict'):
            param_dict = deep_parameter.to_dict()
        elif isinstance(deep_parameter, dict):
            param_dict = deep_parameter
        else:
            raise TypeError("Input `deep_parameter` must be a dict or a class with a to_dict() method.")

        # 1. Serialize with MessagePack
        packed_data = msgpack.packb(param_dict, use_bin_type=True)
        original_size = len(packed_data)

        # 2. Compress with selected algorithm
        if algorithm == CompressionAlgorithm.ZLIB:
            compressed_data = zlib.compress(packed_data)
        elif algorithm == CompressionAlgorithm.BZ2:
            compressed_data = bz2.compress(packed_data)
        elif algorithm == CompressionAlgorithm.LZMA:
            compressed_data = lzma.compress(packed_data)
        elif algorithm == CompressionAlgorithm.MSGPACK_ONLY:
            compressed_data = packed_data
        else:
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")

        # 3. Update compression stats
        compressed_size = len(compressed_data)
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
        
        if not hasattr(self, 'compression_stats'):
            self.compression_stats = {}
            
        self.compression_stats[algorithm.value] = {
            'total_compressions': self.compression_stats.get(algorithm.value, {}).get('total_compressions', 0) + 1,
            'total_original_size': self.compression_stats.get(algorithm.value, {}).get('total_original_size', 0) + original_size,
            'total_compressed_size': self.compression_stats.get(algorithm.value, {}).get('total_compressed_size', 0) + compressed_size,
            'last_compression_ratio': compression_ratio
        }

        return compressed_data

    def decompress(self, compressed_data: bytes, algorithm: CompressionAlgorithm = CompressionAlgorithm.ZLIB) -> Dict[str, Any]:
        """
        Decompresses a binary object back into a deep parameter dictionary.
        This reverses the compression process.

        Args:
            compressed_data: A byte string of the compressed data.
            algorithm: The compression algorithm used.

        Returns:
            A dictionary representing the deep parameter object.
        """
        # 1. Decompress with selected algorithm
        if algorithm == CompressionAlgorithm.ZLIB:
            packed_data = zlib.decompress(compressed_data)
        elif algorithm == CompressionAlgorithm.BZ2:
            packed_data = bz2.decompress(compressed_data)
        elif algorithm == CompressionAlgorithm.LZMA:
            packed_data = lzma.decompress(compressed_data)
        elif algorithm == CompressionAlgorithm.MSGPACK_ONLY:
            packed_data = compressed_data
        else:
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")

        # 2. Deserialize with MessagePack
        param_dict = msgpack.unpackb(packed_data, raw=False)

        return param_dict

    def get_compression_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get compression statistics for all algorithms used."""
        return self.compression_stats

    def create_dna_chain(self, chain_id: str) -> DNADataChain:
        """Create a new DNA data chain."""
        if chain_id not in self.dna_chains:
            self.dna_chains[chain_id] = DNADataChain(chain_id)
        return self.dna_chains[chain_id]

    def get_dna_chain(self, chain_id: str) -> Optional[DNADataChain]:
        """Get a DNA data chain by ID."""
        return self.dna_chains.get(chain_id)

if __name__ == '__main__':
    # Example Usage demonstrating the new data structures

    # 1. Create an instance of the model and example data using the new dataclasses
    # Initialize AlphaDeepModel with a specific symbolic space database
    model = AlphaDeepModel('test_alpha_deep_model_symbolic_space.db')
    example_data = DeepParameter(
        source_memory_id="mem_000456",
        timestamp="2025-08-04T04:00:00Z",
        base_gist=HAMGist(
            summary="Sarah said she likes the new AI assistant.",
            keywords=["sarah", "likes", "ai", "assistant"],
            original_length=42
        ),
        relational_context=RelationalContext(
            entities=["Sarah", "AI Assistant"],
            relationships=[{"subject": "Sarah", "verb": "likes", "object": "AI Assistant", "confidence": 0.9}]
        ),
        modalities=Modalities(
            text_confidence=0.95
        ),
        action_feedback={"action": "respond", "success": True, "details": "User happy"},
        dna_chain_id="chain_001"
    )

    # 2. Compress the data with different algorithms
    print(f"Original data object: {example_data}")
    original_dict = example_data.to_dict()
    print(f"\nOriginal data as dict: {original_dict}")

    # Test different compression algorithms
    algorithms = [CompressionAlgorithm.ZLIB, CompressionAlgorithm.BZ2, CompressionAlgorithm.LZMA]
    for algorithm in algorithms:
        compressed = model.compress(example_data, algorithm)
        print(f"\nCompressed size with {algorithm.value}: {len(compressed)} bytes")
        
        decompressed = model.decompress(compressed, algorithm)
        assert original_dict == decompressed
        print(f"Decompression with {algorithm.value} successful!")

    # 3. Test DNA data chain functionality
    print("\n--- DNA Data Chain Functionality ---")
    chain = model.create_dna_chain("test_chain")
    chain.add_node("mem_000456")
    chain.add_node("mem_000457")
    
    # Create a branch
    branch = chain.create_branch("branch_001", "mem_000456")
    branch.add_node("mem_000458")
    
    print(f"Main chain nodes: {chain.nodes}")
    print(f"Branch nodes: {branch.nodes}")
    print(f"Branches: {list(chain.branches.keys())}")

    # 4. Verify learning mechanism
    print("\n--- Learning Mechanism ---")
    model.learn(example_data, feedback={"accuracy": 0.95, "response_time": 0.5})

    # Verify symbols and relationships in the symbolic space
    print("\n--- Symbolic Space Content ---")
    print(f"Symbol 'mem_000456': {model.symbolic_space.get_symbol('mem_000456')}")
    print(f"Symbol 'Sarah said she likes the new AI assistant.': {model.symbolic_space.get_symbol('Sarah said she likes the new AI assistant.')}")
    print(f"Relationships for 'Sarah': {model.symbolic_space.get_relationships('Sarah')}")
    print(f"Relationships for 'AI Assistant': {model.symbolic_space.get_relationships('AI Assistant')}")

    # Show compression stats
    print("\n--- Compression Statistics ---")
    stats = model.get_compression_stats()
    for algo, stat in stats.items():
        avg_ratio = stat['total_original_size'] / stat['total_compressed_size'] if stat['total_compressed_size'] > 0 else 0
        print(f"{algo}: {stat['total_compressions']} compressions, "
              f"avg ratio: {avg_ratio:.2f}:1")

    # Clean up test symbolic space database
    import os
    if os.path.exists('test_alpha_deep_model_symbolic_space.db'):
        os.remove('test_alpha_deep_model_symbolic_space.db')
        print("Cleaned up test_alpha_deep_model_symbolic_space.db")