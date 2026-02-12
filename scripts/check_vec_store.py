import json
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

def check_vector_store():
    store_path = Path("data/vector_store/default_collection.json")
    if not store_path.exists():
        print(f"VectorStore file not found: {store_path}")
        return

    with open(store_path, "r", encoding="utf-8") as f:
        memories = json.load(f)

    drive_memories = [m for m in memories if m.get("metadata", {}).get("source") == "google_drive"]
    
    print(f"Total memories: {len(memories)}")
    print(f"Google Drive memories: {len(drive_memories)}")
    
    for i, m in enumerate(drive_memories[:5]):
        print(f"\n[{i+1}] ID: {m['id']}")
        print(f"Name: {m['metadata'].get('file_name')}")
        print(f"Snippet: {m['document'][:100]}...")

if __name__ == "__main__":
    check_vector_store()
