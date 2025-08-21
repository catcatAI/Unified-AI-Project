# alpha_deep_model.py
import sys
import os

# Add the parent directory of core_ai to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import msgpack
import zlib
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from core_ai.symbolic_space.unified_symbolic_space import UnifiedSymbolicSpace

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

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass instance to a dictionary for serialization."""
        return asdict(self)

class AlphaDeepModel:
    """
    A model for performing high-compression on structured 'deep parameter' objects.
    """

    def __init__(self, symbolic_space_db: str = 'alpha_deep_model_symbolic_space.db'):
        """
        Initializes the AlphaDeepModel.
        """
        self.symbolic_space = UnifiedSymbolicSpace(symbolic_space_db)

    def learn(self, deep_parameter: DeepParameter, feedback: Optional[Dict[str, Any]] = None) -> None:
        """
        Placeholder for the learning mechanism.
        This method will be responsible for updating the model's internal state
        based on new DeepParameters and optional feedback.
        """
        print(f"Learning from deep parameter: {deep_parameter.source_memory_id}")
        if feedback:
            print(f"Received feedback: {feedback}")
        # Implement actual learning logic here
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

        # 3. Placeholder for adjusting model's internal parameters/weights based on feedback
        # This would involve more complex logic, potentially using the feedback to refine
        # future compression or learning strategies. For now, we focus on symbolic representation.
        print(f"Symbolic space updated for {deep_parameter.source_memory_id}")

    def compress(self, deep_parameter: Any) -> bytes:
        """
        Compresses a deep parameter object into a highly compressed binary format.
        The process involves converting the object to a dictionary, serializing it
        with MessagePack, and then compressing the result with zlib.

        Args:
            deep_parameter: The deep parameter object (e.g., a dataclass instance).

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

        # 2. Compress with zlib
        compressed_data = zlib.compress(packed_data)

        return compressed_data

    def decompress(self, compressed_data: bytes) -> Dict[str, Any]:
        """
        Decompresses a binary object back into a deep parameter dictionary.
        This reverses the compression process: decompress with zlib, then
        deserialize with MessagePack.

        Args:
            compressed_data: A byte string of the compressed data.

        Returns:
            A dictionary representing the deep parameter object.
        """
        # 1. Decompress with zlib
        packed_data = zlib.decompress(compressed_data)

        # 2. Deserialize with MessagePack
        param_dict = msgpack.unpackb(packed_data, raw=False)

        return param_dict

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
        action_feedback={"action": "respond", "success": True, "details": "User happy"}
    )

    # 2. Compress the data
    print(f"Original data object: {example_data}")
    original_dict = example_data.to_dict()
    print(f"\nOriginal data as dict: {original_dict}")

    compressed = model.compress(example_data)

    # 3. Decompress the data
    decompressed = model.decompress(compressed)

    # 4. Verify
    print(f"\nCompressed size: {len(compressed)} bytes")
    print(f"Decompressed data: {decompressed}")

    assert original_dict == decompressed
    print("\nCompression and decompression successful!")

    # Example of calling the new learn method
    model.learn(example_data, feedback=example_data.action_feedback)

    # Verify symbols and relationships in the symbolic space
    print("\n--- Symbolic Space Content ---")
    print(f"Symbol 'mem_000456': {model.symbolic_space.get_symbol('mem_000456')}")
    print(f"Symbol 'Sarah said she likes the new AI assistant.': {model.symbolic_space.get_symbol('Sarah said she likes the new AI assistant.')}")
    print(f"Relationships for 'Sarah': {model.symbolic_space.get_relationships('Sarah')}")
    print(f"Relationships for 'AI Assistant': {model.symbolic_space.get_relationships('AI Assistant')}")

    # Clean up test symbolic space database
    import os
    if os.path.exists('test_alpha_deep_model_symbolic_space.db'):
        os.remove('test_alpha_deep_model_symbolic_space.db')
        print("Cleaned up test_alpha_deep_model_symbolic_space.db")
