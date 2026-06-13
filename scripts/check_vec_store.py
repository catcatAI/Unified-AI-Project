import json
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def check_vector_store():
    store_path = PROJECT_ROOT / "data" / "vector_store" / "default_collection.json"
    if not store_path.exists():
        print(f"VectorStore file not found: {store_path}")
        return

    with open(store_path, "r", encoding="utf-8") as f:
        memories = json.load(f)

    drive_memories = [m for m in memories if m.get("metadata", {}).get("source") == "google_drive"]
    
    print(f"Total memories: {len(memories)}")
    print(f"Google Drive memories: {len(drive_memories)}")
    
    for i, m in enumerate(drive_memories[:5]):
        metadata = m.get('metadata', {})
        doc = m.get('document', '')
        print(f"\n[{i+1}] ID: {m.get('id', 'N/A')}")
        print(f"Name: {metadata.get('file_name', 'N/A')}")
        print(f"Snippet: {doc[:100]}...")

if __name__ == "__main__":
    check_vector_store()
