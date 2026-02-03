
import sys
import os
from pathlib import Path

# Setup path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_memory_init():
    print("Testing HAMMemoryManager Initialization...")
    try:
        from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager
        manager = HAMMemoryManager()
        print("✅ HAMMemoryManager initialized successfully.")
        
        # Test vector store access
        print(f"VectorStore collection: {manager.vector_store.collection_name}")
        
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_memory_init()
