import asyncio
import os
import hashlib
from pathlib import Path
import sys

# Add project root to sys.path to allow imports from 'apps'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager
from apps.backend.src.integrations.document_parser import DocumentParser

# Temporary file containing all concatenated activity content
ACTIVITY_CONTENT_FILE = Path(project_root) / "temp_my_activity_content.txt"

def compute_content_hash(file_path: Path) -> str:
    """Compute MD5 hash of file content."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

async def ingest_activity_content():
    print(f"Starting ingestion of {ACTIVITY_CONTENT_FILE}...")
    
    # Initialize HAMMemoryManager (needs to be done in an async context or with a running event loop)
    # This might require some setup similar to SystemManager if HAMMemoryManager depends on it
    # For a standalone script, we'll try direct instantiation
    ham_memory_manager = HAMMemoryManager()
    
    document_parser = DocumentParser()
    
    if not ACTIVITY_CONTENT_FILE.exists():
        print(f"Error: Activity content file not found at {ACTIVITY_CONTENT_FILE}")
        return

    try:
        # Read and parse the concatenated content
        mime_type = "text/plain" # Assuming it's a plain text file
        full_content = document_parser.parse_document(str(ACTIVITY_CONTENT_FILE), mime_type)
        
        content_hash = compute_content_hash(ACTIVITY_CONTENT_FILE)
        
        # Store in HAMMemoryManager
        experience = {
            "content": full_content,
            "metadata": {
                "source": "local_activity_log",
                "path": str(ACTIVITY_CONTENT_FILE),
                "file_name": ACTIVITY_CONTENT_FILE.name,
                "mime_type": mime_type,
                "content_hash": content_hash,
                "description": "Concatenated content from '我的活動' directory"
            }
        }
        
        print(f"Storing content in HAMMemoryManager. Hash: {content_hash}")
        memory_id = await ham_memory_manager.store_experience(experience)
        print(f"Successfully memorized content. Memory ID: {memory_id}")
        
    except Exception as e:
        print(f"An error occurred during ingestion: {e}")

if __name__ == "__main__":
    asyncio.run(ingest_activity_content())
