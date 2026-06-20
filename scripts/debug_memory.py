
import sys
import os
import traceback
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

# Setup path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def test_memory_init():
    print("Testing HAMMemoryManager Initialization...")
    try:
        from ai.memory.ham_memory.ham_manager import HAMMemoryManager
        manager = HAMMemoryManager()
        print("✅ HAMMemoryManager initialized successfully.")
        
        # Test vector store access
        print(f"VectorStore collection: {manager.vector_store.collection_name}")
        
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_memory_init()
