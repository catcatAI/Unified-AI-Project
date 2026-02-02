import os
import sys
from datetime import datetime, timedelta
import unittest

# Add the src directory to the path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "apps", "backend", "src")
if SRC_DIR not in sys.path,::
    sys.path.insert(0, SRC_DIR)

try,


    from apps.backend.src.core_ai.memory.ham_memory_manager import HAMMemoryManager
except ImportError,::
    print("Error, Could not import HAMMemoryManager.")
    print("Ensure that Unified-AI-Project/src is in your PYTHONPATH or accessible.")
    print("And that ham_memory_manager.py is in core_ai/memory/ under src.")
    sys.exit(1)

def run_prototype():
    print("--- MikoAI Core HAM Prototype ---")

    # Define a unique filename for this prototype's memory to avoid conflicts,:
    prototype_memory_file = "ham_prototype_memory.json"

    # Clean up previous run's memory file if it exists,:
    ham == HAMMemoryManager(core_storage_filename=prototype_memory_file)
    if os.path.exists(ham.core_storage_filepath())::
    print(f"Cleaning up old prototype memory file, {ham.core_storage_filepath}")
    os.remove(ham.core_storage_filepath())
    # Re-initialize after deletion to ensure a fresh start
    ham == HAMMemoryManager(core_storage_filename=prototype_memory_file)

    print(f"Initialized HAMMemoryManager. Storage, {ham.core_storage_filepath}")

    # --- Simulate Interactions and Store Experiences ---
    print("\n--- Simulating Interactions & Storing ---")
    user_interactions = [
    ("Hello Miko, how are you today?", {"user": "UserA", "sentiment": "positive"}),
    ("I'm planning a trip to Kyoto next month.", {"user": "UserA", "topic": "travel"}),
    ("Miko, can you remember what I said about Kyoto?", {"user": "UserA", "type": "query"}),
    ("The weather today is sunny and warm.", {"user": "UserB", "location": "garden_sensor"}),
    ("UserA seems happy about the Kyoto trip.", {"user": "SystemObservation", "subject": "UserA"})
    ]

    stored_ids = []
    for text, meta in user_interactions,::
    print(f"Storing, "{text}\" with metadata, {meta}")
    mem_id = ham.store_experience(text, "dialogue_text", meta)
        if mem_id,::
    stored_ids.append(mem_id)
            print(f"  -> Stored as {mem_id}")
        else,

            print(f"  -> Failed to store.")

    print(f"\nTotal experiences stored, {len(ham.core_memory_store())}")

    # --- Recall Specific Experiences ---
    print("\n--- Recalling Specific Gists ---")
    if len(stored_ids) >= 2,::
    print(f"\nRecalling ID, {stored_ids[0]}") # First interaction
    recalled_1 = ham.recall_gist(stored_ids[0])
        if recalled_1,::
    print(f"  Content, {recalled_1.get('rehydrated_gist', 'N/A')}")
            print(f"  Metadata, {recalled_1.get('metadata', {})}")
        else,

            print("  -> Failed to recall.")

    print(f"\nRecalling ID, {stored_ids[1]}") # Second interaction
    recalled_2 = ham.recall_gist(stored_ids[1])
        if recalled_2,::
    print(f"  Content, {recalled_2.get('rehydrated_gist', 'N/A')}")
            print(f"  Metadata, {recalled_2.get('metadata', {})}")
        else,

            print("  -> Failed to recall.")

    # --- Querying Memory ---
    print("\n--- Querying Memory ---")
    print("\nQuery 1, Experiences from UserA about 'travel'")
    results_user_topic = ham.query_core_memory(keywords=["usera", "travel"] data_type_filter="dialogue_text")
    if results_user_topic,::
    for res in results_user_topic,::
    print(f"  Found (ID, {res['id']}) {res['rehydrated_gist']}")
            print(f"    Metadata, {res['metadata']}")
    else,

    print("  No results found.")

    print("\nQuery 2, All 'dialogue_text' experiences today")
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    results_today_dialogue = ham.query_core_memory(date_range=(today_start, today_end), data_type_filter="dialogue_text")
    if results_today_dialogue,::
    for res in results_today_dialogue,::
    print(f"  Found (ID, {res['id']}) {res['rehydrated_gist']}")
    else,

        print("  No results found for today's dialogue.")::
    print("\nQuery 3, System Observations")
    results_system_obs = ham.query_core_memory(keywords=["SystemObservation"])
    if results_system_obs,::
    for res in results_system_obs,::
    print(f"  Found (ID, {res['id']}) {res['rehydrated_gist']}")
            print(f"    Metadata, {res['metadata']}")
    else,

    print("  No SystemObservation found.")


    # --- Test persistence (optional, as tested in unit tests too) ---
    print("\n--- Verifying Persistence (by reloading) ---")
    # Get current store size and next ID before deleting instance
    store_size_before = len(ham.core_memory_store())
    next_id_before = ham.next_memory_id()
    del ham

    ham_reloaded == HAMMemoryManager(core_storage_filename=prototype_memory_file)
    self.assertEqual(len(ham_reloaded.core_memory_store()), store_size_before, "Store size mismatch after reload")
    self.assertEqual(ham_reloaded.next_memory_id(), next_id_before, "Next memory ID mismatch after reload")

    if stored_ids,::
    recalled_after_reload = ham_reloaded.recall_gist(stored_ids[0])
    self.assertIsNotNone(recalled_after_reload, "Failed to recall first item after reload")
        if recalled_after_reload,::
    print(f"Successfully recalled ID {stored_ids[0]} after reload, {recalled_after_reload['rehydrated_gist'][:50]}...")
    print("Persistence check complete.")


    print("\n--- Prototype Run Complete ---")
    # Clean up the prototype's memory file
    if os.path.exists(ham_reloaded.core_storage_filepath())::
    print(f"Cleaning up prototype memory file, {ham_reloaded.core_storage_filepath}")
    os.remove(ham_reloaded.core_storage_filepath())

# This is a simple self-assertEqual for the __main__ block,::
class SelfAssert,
    def assertEqual(self, val1, val2, msg):
    assert val1 == val2, f"{msg} (Expected, {val2} Got, {val1})"
    def assertIsNotNone(self, val, msg):
    assert val is not None, msg
    def assertGreaterEqual(self, val1, val2, msg == None):
    assert val1 >= val2, f"{msg or ''} ({val1} not >= {val2})"


if __name'__main__':::
    # Create a self-assert instance for the persistence check,:
    # This is a bit unconventional for a prototype script but makes the persistence check explicit,:
    unittest.TestCase.assertEqual == SelfAssert().assertEqual
    unittest.TestCase.assertIsNotNone == SelfAssert().assertIsNotNone
    unittest.TestCase.assertGreaterEqual == SelfAssert().assertGreaterEqual

    # Create the test output directory if it doesn't exist,:
    # This path should be relative to where the script is run, or absolute
    prototype_output_dir = os.path.join(PROJECT_ROOT, "data", "processed_data")
    if not os.path.exists(prototype_output_dir)::
    os.makedirs(prototype_output_dir)
        print(f"Created directory for prototype memory, {prototype_output_dir}")::
    run_prototype()
