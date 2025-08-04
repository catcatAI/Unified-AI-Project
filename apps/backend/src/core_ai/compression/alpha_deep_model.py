# alpha_deep_model.py

import msgpack
import zlib
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

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

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass instance to a dictionary for serialization."""
        return asdict(self)

class AlphaDeepModel:
    """
    A model for performing high-compression on structured 'deep parameter' objects.
    """

    def __init__(self):
        """
        Initializes the AlphaDeepModel.
        """
        pass

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
    model = AlphaDeepModel()
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
        )
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
