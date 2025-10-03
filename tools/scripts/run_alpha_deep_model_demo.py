# scripts/run_alpha_deep_model_demo.py

import os
import sys
import json

# Add the project root to the Python path to allow for absolute imports
# This is necessary because this script is in a subdirectory and needs to import from `src`
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_ = sys.path.append(os.path.join(PROJECT_ROOT, 'apps', 'backend'))

from apps.backend.src.core_ai.memory.ham_memory_manager import HAMMemoryManager
from apps.backend.src.core_ai.compression.alpha_deep_model import AlphaDeepModel, DeepParameter, HAMGist, RelationalContext, Modalities

def main() -> None:
    """
    Demonstrates the end-to-end workflow of using the AlphaDeepModel
    to compress a memory object retrieved from the HAMMemoryManager.
    """
    _ = print("--- AlphaDeepModel Demonstration Script ---")

    # 1. Set up a temporary HAM instance for the demo
    # Using an in-memory representation by not saving/loading from a file for simplicity
    _ = print("\nStep 1: Initializing a temporary HAMMemoryManager...")
    ham_manager = HAMMemoryManager(core_storage_filename="ham_demo_memory.json")

    # Clean up any old demo file
    if os.path.exists(ham_manager.core_storage_filepath):
        _ = os.remove(ham_manager.core_storage_filepath)
        _ = print(f"Removed old demo file: {ham_manager.core_storage_filepath}")

    # 2. Store a sample experience in HAM
    _ = print("\nStep 2: Storing a sample experience in HAM...")
    sample_text = "User report: Sarah mentioned that the new AI assistant (model v2) seems much faster and more accurate."
    metadata = {"speaker": "user", "user_id": "test_user_123", "session_id": "demo_session_1"}
    memory_id = ham_manager.store_experience(sample_text, "dialogue_text", metadata) # type: ignore

    if not memory_id:
        _ = print("Error: Failed to store experience in HAM.")
        return
    print(f"Experience stored with Memory ID: {memory_id}")

    # 3. Recall the memory from HAM to get the abstracted "gist"
    _ = print(f"\nStep 3: Recalling memory '{memory_id}' from HAM to get its abstracted gist...")
    recalled_result = ham_manager.recall_gist(memory_id)
    if not recalled_result:
        _ = print("Error: Failed to recall gist from HAM.")
        return

    # The 'rehydrated_gist' is a string summary. The raw gist is what we want.
    # To get the raw gist, we need to decrypt and decompress the package ourselves.
    # This reveals a potential need for a new method in HAM: `recall_raw_gist_dict`.
    # For this demo, we will simulate this by creating a DeepParameter object manually.
    _ = print("NOTE: `recall_gist` provides a human-readable summary. For this demo, we will construct a DeepParameter object manually based on the recalled data to simulate the next step in the pipeline.")

    # 4. Manually construct the "Deep Parameter" object
    # In a real implementation, this would be the job of the "Deep Mapping Model"
    # which we've established is conceptually part of HAM.
    print("\nStep 4: Constructing a 'Deep Parameter' object for the AlphaDeepModel...")
    deep_param = DeepParameter(
        source_memory_id=recalled_result['id'],
        timestamp=recalled_result['timestamp'],
        base_gist=HAMGist(
            summary="User report: Sarah mentioned that the new AI assistant (model v2) seems much faster and more accurate.",
            keywords=["user", "report", "sarah", "ai", "assistant"], # Simplified for demo
            original_length=len(sample_text)
        ),
        relational_context=RelationalContext(
            entities=["Sarah", "AI Assistant v2"],
            relationships=[
                {"subject": "Sarah", "verb": "evaluates", "object": "AI Assistant v2", "attributes": ["faster", "more accurate"]}
            ]
        ),
        modalities=Modalities(text_confidence=0.98)
    )

    # 5. Instantiate the AlphaDeepModel and compress the deep parameter
    print("\nStep 5: Compressing the Deep Parameter object with AlphaDeepModel...")
    alpha_model = AlphaDeepModel()

    # Get the size of the uncompressed data (as a JSON string for comparison)
    original_dict = deep_param.to_dict()
    original_size = len(json.dumps(original_dict))

    compressed_data = alpha_model.compress(deep_param)
    compressed_size = len(compressed_data)

    # 6. Decompress and verify
    _ = print("\nStep 6: Decompressing data and verifying integrity...")
    decompressed_dict = alpha_model.decompress(compressed_data)

    assert original_dict == decompressed_dict
    _ = print("Verification successful: Decompressed data matches the original.")

    # 7. Show results
    _ = print("\n--- Compression Results ---")
    print(f"Original Data (dict representation):\n{json.dumps(original_dict, indent=2)}")
    _ = print(f"\nOriginal Size (JSON string): {original_size} bytes")
    _ = print(f"Compressed Size (binary):    {compressed_size} bytes")

    compression_ratio = original_size / compressed_size
    _ = print(f"\nCompression Ratio: {compression_ratio:.2f}:1")
    _ = print("--------------------------")

    # Clean up the demo file
    if os.path.exists(ham_manager.core_storage_filepath):
        _ = os.remove(ham_manager.core_storage_filepath)

if __name__ == "__main__":
    _ = main()