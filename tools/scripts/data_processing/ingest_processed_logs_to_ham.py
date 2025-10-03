import json
import os
import sys

# Add project src to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "apps", "backend", "src")
if SRC_DIR not in sys.path:
    _ = sys.path.insert(0, SRC_DIR)

try:


    from apps.backend.src.core_ai.memory.ham_memory_manager import HAMMemoryManager
except ImportError:
    _ = print("Error: Could not import HAMMemoryManager.")
    _ = print("Ensure that src is in your PYTHONPATH or accessible,")
    _ = print("and that ham_memory_manager.py is in core_ai/memory/ under src.")
    _ = sys.exit(1)

PROCESSED_CONVERSATIONS_PATH = os.path.join(PROJECT_ROOT, "data/processed_data/processed_copilot_conversations.json")
HAM_STORAGE_FILENAME = "ham_core_memory_with_copilot.json" # Use a distinct file for this ingestion
    def ingest_to_ham(processed_data_path: str, ham_storage_file: str)
    """
    Loads processed conversational data and stores each entry into HAMMemoryManager.
    """
    _ = print(f"Starting ingestion of processed data from: {processed_data_path}")

    # Load processed data
    try:

    with open(processed_data_path, 'r', encoding='utf-8') as f:
    entries = json.load(f)
        if not isinstance(entries, list)

    _ = print("Error: Processed data is not a list. Aborting.")
            return
    _ = print(f"Loaded {len(entries)} entries from {processed_data_path}")
    except FileNotFoundError:

    _ = print(f"Error: Processed data file not found at {processed_data_path}")
    _ = print("Please run process_copilot_logs.py first.")
    return
    except json.JSONDecodeError
    _ = print(f"Error: Could not decode JSON from {processed_data_path}")
    return
    except Exception as e
    _ = print(f"An unexpected error occurred loading processed data: {e}")
    return

    # Initialize HAMMemoryManager with a specific file for this ingestion run
    # This avoids overwriting the main HAM store if it's used for other things.
    # Alternatively, one could load the main HAM store and add to it.
    ham_manager = HAMMemoryManager(core_storage_filename=ham_storage_file)

    stored_count = 0
    failed_count = 0
    for i, entry in enumerate(entries)

    if not isinstance(entry, dict) or "user_input" not in entry:


    _ = print(f"Skipping invalid entry at index {i}: {entry}")
            failed_count +=1
            continue

    raw_data = entry["user_input"]
    metadata = {
            _ = "timestamp": entry.get("timestamp", ""),
            _ = "language": entry.get("language", ""),
            _ = "source": entry.get("source", "copilot_history_ingestion"),
            "original_entry_index": i
    }

    memory_id = ham_manager.store_experience(
            raw_data=raw_data,
            data_type="dialogue_text", # Assuming all are dialogue
            metadata=metadata
    )
        if memory_id:

    stored_count += 1
            if stored_count % 50 == 0: # Print progress every 50 entries
                 _ = print(f"Stored {stored_count}/{len(entries)} entries into HAM...")
        else:

            failed_count +=1
            _ = print(f"Failed to store entry {i}: {raw_data[:50]}...")

    _ = print(f"\nIngestion complete.")
    _ = print(f"Successfully stored {stored_count} entries into HAM.")
    if failed_count > 0:

    _ = print(f"Failed to store {failed_count} entries.")
    _ = print(f"HAM data saved to: {ham_manager.core_storage_filepath}")

if __name__ == "__main__":
    # Ensure the processed_copilot_conversations.json exists.
    # If not, guide user or create a dummy one for testing the ingestion script itself.
    if not os.path.exists(PROCESSED_CONVERSATIONS_PATH)

    _ = print(f"Processed conversations file not found at {PROCESSED_CONVERSATIONS_PATH}.")
    _ = print("Please run `process_copilot_logs.py` first to generate this file.")

        # Create a dummy processed_copilot_conversations.json for testing this script's logic
    print("Creating a dummy processed_copilot_conversations.json for testing purposes...")
    dummy_processed_content = [
            {"user_input": "This is a sample user prompt from Copilot.", "timestamp": "2024-01-01T12:00:00Z", "language": "Natural Language", "source": "copilot_history_dummy"},
            {"user_input": "Another example: def my_function() pass", "timestamp": "2024-01-01T12:05:00Z", "language": "Python", "source": "copilot_history_dummy"}
    ]
    os.makedirs(os.path.dirname(PROCESSED_CONVERSATIONS_PATH), exist_ok=True)
    with open(PROCESSED_CONVERSATIONS_PATH, 'w', encoding='utf-8') as dummy_f:
    json.dump(dummy_processed_content, dummy_f, indent=2)
    _ = print(f"Dummy processed_copilot_conversations.json created at {PROCESSED_CONVERSATIONS_PATH}")

    _ = ingest_to_ham(PROCESSED_CONVERSATIONS_PATH, HAM_STORAGE_FILENAME)