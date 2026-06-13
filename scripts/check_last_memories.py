import json
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def check_last_memories():
    store_path = PROJECT_ROOT / "data" / "vector_store" / "default_collection.json"
    if not store_path.exists():
        print(f"VectorStore file not found: {store_path}")
        return

    with open(store_path, "r", encoding="utf-8") as f:
        memories = json.load(f)

    print(f"Total memories: {len(memories)}")
    
    for i, m in enumerate(memories[-5:]):
        doc = m.get('document', '')
        print(f"\n[Index {len(memories)-5+i}] ID: {m.get('id', 'N/A')}")
        print(f"Metadata: {m.get('metadata', {})}")
        print(f"Snippet: {doc[:50]}...")

if __name__ == "__main__":
    check_last_memories()
